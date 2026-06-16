import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx
from app.config import settings

DEFAULT_ANSWER_PROVIDER = "deterministic-evidence"
OPENAI_COMPATIBLE_ANSWER_PROVIDER = "openai-compatible"
DETERMINISTIC_ANSWER_MODEL = "evidence-preview-template-v1"
MAX_EXCERPT_CHARS = 600


class UnsupportedAnswerProviderError(ValueError):
    """Raised when chat answer generation is configured for an unknown provider."""


class AnswerProviderType(StrEnum):
    DETERMINISTIC = "deterministic"
    FREE_TIER_API = "free-tier-api"
    LOCAL_MODEL = "local-model"
    OPENAI_COMPATIBLE = "openai-compatible"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AnswerProviderStatus:
    provider_name: str
    provider_type: str
    display_name: str
    model_name: str | None
    base_url_host: str | None
    is_default: bool
    is_available: bool
    requires_api_key: bool
    requires_network: bool
    requires_model_download: bool
    supports_streaming: bool
    status_message: str


@dataclass(frozen=True)
class EvidenceInput:
    rank: int
    score: float
    document_id: str
    document_title: str
    document_filename: str
    chunk_id: str
    chunk_index: int
    text: str
    page_number: int | None = None


@dataclass(frozen=True)
class AnswerRequest:
    question: str
    evidence: list[EvidenceInput]


@dataclass(frozen=True)
class AnswerProvenance:
    provider_name: str
    provider_type: str
    model_name: str | None
    fallback_used: bool = False
    fallback_reason: str | None = None


@dataclass(frozen=True)
class AnswerResult:
    content: str
    provider: str
    model: str
    provenance: AnswerProvenance | None = None


class AnswerProvider(Protocol):
    provider_name: str

    @property
    def model_name(self) -> str:
        """Provider model identifier used for diagnostics and answer metadata."""

    def generate(self, request: AnswerRequest) -> AnswerResult:
        """Generate assistant answer text from retrieved evidence."""


@dataclass(frozen=True)
class OpenAICompatibleProviderConfig:
    base_url: str | None
    api_key: str | None
    model: str | None
    timeout_seconds: float
    max_tokens: int
    temperature: float
    requires_api_key: bool = False


def excerpt_text(text: str, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


def _answer_result(
    *,
    provider_name: str,
    provider_type: str,
    model_name: str,
    content: str,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
) -> AnswerResult:
    return AnswerResult(
        provider=provider_name,
        model=model_name,
        content=content,
        provenance=AnswerProvenance(
            provider_name=provider_name,
            provider_type=provider_type,
            model_name=model_name,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        ),
    )


class DeterministicEvidenceAnswerProvider:
    provider_name = DEFAULT_ANSWER_PROVIDER
    model_name = DETERMINISTIC_ANSWER_MODEL

    def generate(self, request: AnswerRequest) -> AnswerResult:
        question = request.question.strip()
        if not request.evidence:
            return _answer_result(
                provider_name=self.provider_name,
                provider_type=AnswerProviderType.DETERMINISTIC.value,
                model_name=self.model_name,
                content=(
                    "Evidence preview: no relevant evidence was found for this question.\n\n"
                    "PaperLens has stored your question, but the local lexical search did not "
                    "match any indexed chunks. Try chunking ingested documents first or use "
                    "terms that appear in the uploaded sources."
                ),
            )

        lines = [
            "Evidence preview: this deterministic draft is grounded only in retrieved local chunks.",
            "",
            f"Question: {question}",
            "",
            "Retrieved evidence:",
        ]
        for evidence in request.evidence:
            page_label = (
                f", page={evidence.page_number}" if evidence.page_number is not None else ""
            )
            lines.append(
                f"{evidence.rank}. {evidence.document_title} "
                f"(document_id={evidence.document_id}, chunk_id={evidence.chunk_id}, "
                f"chunk_index={evidence.chunk_index}{page_label}, score={evidence.score:g})"
            )
            lines.append(f"   {excerpt_text(evidence.text, max_chars=260)}")
        lines.append("")
        lines.append("No external LLM was called for this response.")
        return _answer_result(
            provider_name=self.provider_name,
            provider_type=AnswerProviderType.DETERMINISTIC.value,
            model_name=self.model_name,
            content="\n".join(lines),
        )


def _supported_provider_names() -> str:
    return f"{DEFAULT_ANSWER_PROVIDER}, {OPENAI_COMPATIBLE_ANSWER_PROVIDER}"


def _openai_config_from_settings() -> OpenAICompatibleProviderConfig:
    return OpenAICompatibleProviderConfig(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        requires_api_key=settings.llm_requires_api_key,
    )


def _safe_base_url_host(base_url: str | None) -> str | None:
    if not base_url:
        return None
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.port is not None:
        return f"{parsed.hostname}:{parsed.port}"
    return parsed.hostname


def _openai_config_error(config: OpenAICompatibleProviderConfig) -> str | None:
    if not config.base_url or not config.base_url.strip():
        return "llm_base_url is required for the OpenAI-compatible answer provider."
    if _safe_base_url_host(config.base_url) is None:
        return "llm_base_url must be a valid HTTP(S) URL for the OpenAI-compatible answer provider."
    if not config.model or not config.model.strip():
        return "llm_model is required for the OpenAI-compatible answer provider."
    if config.requires_api_key and not config.api_key:
        return "llm_api_key is required because llm_requires_api_key is enabled."
    return None


def _evidence_block(evidence: EvidenceInput) -> str:
    page_label = f", page={evidence.page_number}" if evidence.page_number is not None else ""
    return (
        f"[Evidence {evidence.rank}] document_title={evidence.document_title}; "
        f"document_filename={evidence.document_filename}; document_id={evidence.document_id}; "
        f"chunk_id={evidence.chunk_id}; chunk_index={evidence.chunk_index}{page_label}; "
        f"score={evidence.score:g}\n"
        f"{excerpt_text(evidence.text, max_chars=1200)}"
    )


def _build_openai_messages(request: AnswerRequest) -> list[dict[str, str]]:
    evidence_text = "\n\n".join(_evidence_block(evidence) for evidence in request.evidence)
    return [
        {
            "role": "system",
            "content": (
                "You are PaperLens, an evidence-grounded assistant for scientific and technical "
                "documents. Answer only from the evidence snippets provided by PaperLens. If the "
                "evidence is insufficient, say that no relevant evidence was found. Do not invent "
                "facts, documents, chunks, pages, or citations. If you cite evidence, use only the "
                "provided Evidence numbers. PaperLens evidence rows remain the authoritative "
                "citations for this response."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{request.question.strip()}\n\n"
                f"Retrieved evidence snippets:\n{evidence_text}"
            ),
        },
    ]


def _deterministic_fallback_content(request: AnswerRequest, reason: str) -> str:
    deterministic = DeterministicEvidenceAnswerProvider().generate(request)
    return (
        "Evidence preview: OpenAI-compatible answer provider is unavailable. "
        f"{reason}\n\n"
        "Falling back to the deterministic evidence preview.\n\n"
        f"{deterministic.content}"
    )


def _openai_fallback_result(
    request: AnswerRequest,
    model_name: str,
    reason: str,
) -> AnswerResult:
    return _answer_result(
        provider_name=OPENAI_COMPATIBLE_ANSWER_PROVIDER,
        provider_type=AnswerProviderType.OPENAI_COMPATIBLE.value,
        model_name=model_name,
        fallback_used=True,
        fallback_reason=reason,
        content=_deterministic_fallback_content(request, reason),
    )


class OpenAICompatibleAnswerProvider:
    provider_name = OPENAI_COMPATIBLE_ANSWER_PROVIDER

    def __init__(
        self,
        config: OpenAICompatibleProviderConfig | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config or _openai_config_from_settings()
        self._client = client

    @property
    def model_name(self) -> str:
        return self.config.model or "unconfigured"

    def _request_payload(self, request: AnswerRequest) -> dict[str, Any]:
        return {
            "model": self.config.model,
            "messages": _build_openai_messages(request),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _chat_completions_url(self) -> str:
        base_url = self.config.base_url or ""
        return f"{base_url.rstrip('/')}/chat/completions"

    def _post_payload(self, payload: dict[str, Any]) -> httpx.Response:
        if self._client is not None:
            return self._client.post(
                self._chat_completions_url(),
                json=payload,
                headers=self._headers(),
                timeout=self.config.timeout_seconds,
            )

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            return client.post(
                self._chat_completions_url(),
                json=payload,
                headers=self._headers(),
            )

    def generate(self, request: AnswerRequest) -> AnswerResult:
        if not request.evidence:
            return _openai_fallback_result(
                request,
                self.model_name,
                "No retrieved evidence was available for provider-backed synthesis.",
            )

        config_error = _openai_config_error(self.config)
        if config_error is not None:
            return _openai_fallback_result(
                request,
                self.model_name,
                config_error,
            )

        try:
            response = self._post_payload(self._request_payload(request))
        except httpx.TimeoutException:
            return _openai_fallback_result(
                request,
                self.model_name,
                "The provider request timed out.",
            )
        except httpx.RequestError:
            return _openai_fallback_result(
                request,
                self.model_name,
                "The provider network request failed.",
            )

        if response.status_code == 429:
            return _openai_fallback_result(
                request,
                self.model_name,
                "The provider reported a rate limit.",
            )
        if response.status_code >= 400:
            return _openai_fallback_result(
                request,
                self.model_name,
                f"The provider returned HTTP {response.status_code}.",
            )

        try:
            payload = response.json()
            choices = payload.get("choices") if isinstance(payload, dict) else None
            first_choice = choices[0] if isinstance(choices, list) and choices else None
            message = first_choice.get("message") if isinstance(first_choice, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
        except ValueError:
            content = None

        if not isinstance(content, str) or not content.strip():
            return _openai_fallback_result(
                request,
                self.model_name,
                "The provider returned an invalid response.",
            )

        return _answer_result(
            provider_name=self.provider_name,
            provider_type=AnswerProviderType.OPENAI_COMPATIBLE.value,
            model_name=self.model_name,
            content=(
                "Evidence-grounded answer draft from OpenAI-compatible provider:\n\n"
                f"{content.strip()}\n\n"
                "PaperLens evidence cards remain the authoritative citations for this response."
            ),
        )


def get_answer_provider(provider_name: str | None = None) -> AnswerProvider:
    configured_name = provider_name if provider_name is not None else settings.answer_provider
    normalized_name = configured_name.strip().lower()
    if normalized_name == DEFAULT_ANSWER_PROVIDER:
        return DeterministicEvidenceAnswerProvider()
    if normalized_name == OPENAI_COMPATIBLE_ANSWER_PROVIDER:
        return OpenAICompatibleAnswerProvider()

    raise UnsupportedAnswerProviderError(
        f"Unsupported answer provider '{configured_name}'. "
        f"Supported providers: {_supported_provider_names()}."
    )


def get_answer_provider_status(provider_name: str | None = None) -> AnswerProviderStatus:
    configured_name = provider_name if provider_name is not None else settings.answer_provider
    normalized_name = configured_name.strip().lower()
    is_default = normalized_name == DEFAULT_ANSWER_PROVIDER

    if normalized_name == DEFAULT_ANSWER_PROVIDER:
        return AnswerProviderStatus(
            provider_name=DEFAULT_ANSWER_PROVIDER,
            provider_type=AnswerProviderType.DETERMINISTIC.value,
            display_name="Deterministic evidence preview",
            model_name=DETERMINISTIC_ANSWER_MODEL,
            base_url_host=None,
            is_default=is_default,
            is_available=True,
            requires_api_key=False,
            requires_network=False,
            requires_model_download=False,
            supports_streaming=False,
            status_message=(
                "Default local deterministic provider is available. It creates evidence-preview "
                "answers from retrieved chunks and does not call an LLM."
            ),
        )

    if normalized_name == OPENAI_COMPATIBLE_ANSWER_PROVIDER:
        config = _openai_config_from_settings()
        config_error = _openai_config_error(config)
        host = _safe_base_url_host(config.base_url)
        is_available = config_error is None
        return AnswerProviderStatus(
            provider_name=OPENAI_COMPATIBLE_ANSWER_PROVIDER,
            provider_type=AnswerProviderType.OPENAI_COMPATIBLE.value,
            display_name="OpenAI-compatible chat completions",
            model_name=config.model,
            base_url_host=host,
            is_default=False,
            is_available=is_available,
            requires_api_key=config.requires_api_key,
            requires_network=True,
            requires_model_download=False,
            supports_streaming=False,
            status_message=(
                "OpenAI-compatible provider is configured. Availability depends on the endpoint, "
                "network, quota, and credentials at request time."
                if is_available
                else config_error or "OpenAI-compatible provider is unavailable."
            ),
        )

    return AnswerProviderStatus(
        provider_name=configured_name,
        provider_type=AnswerProviderType.UNKNOWN.value,
        display_name=configured_name or "Unconfigured answer provider",
        model_name=None,
        base_url_host=None,
        is_default=False,
        is_available=False,
        requires_api_key=False,
        requires_network=False,
        requires_model_download=False,
        supports_streaming=False,
        status_message=(
            f"Unsupported answer provider '{configured_name}'. "
            f"Supported providers: {_supported_provider_names()}."
        ),
    )
