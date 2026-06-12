import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.config import settings

DEFAULT_ANSWER_PROVIDER = "deterministic-evidence"
DETERMINISTIC_ANSWER_MODEL = "evidence-preview-template-v1"
MAX_EXCERPT_CHARS = 600


class UnsupportedAnswerProviderError(ValueError):
    """Raised when chat answer generation is configured for an unknown provider."""


class AnswerProviderType(StrEnum):
    DETERMINISTIC = "deterministic"
    FREE_TIER_API = "free-tier-api"
    LOCAL_MODEL = "local-model"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AnswerProviderStatus:
    provider_name: str
    provider_type: str
    display_name: str
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
class AnswerResult:
    content: str
    provider: str
    model: str


class AnswerProvider(Protocol):
    provider_name: str
    model_name: str

    def generate(self, request: AnswerRequest) -> AnswerResult:
        """Generate assistant answer text from retrieved evidence."""


def excerpt_text(text: str, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


class DeterministicEvidenceAnswerProvider:
    provider_name = DEFAULT_ANSWER_PROVIDER
    model_name = DETERMINISTIC_ANSWER_MODEL

    def generate(self, request: AnswerRequest) -> AnswerResult:
        question = request.question.strip()
        if not request.evidence:
            return AnswerResult(
                provider=self.provider_name,
                model=self.model_name,
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
        return AnswerResult(
            provider=self.provider_name,
            model=self.model_name,
            content="\n".join(lines),
        )


def get_answer_provider(provider_name: str | None = None) -> AnswerProvider:
    configured_name = provider_name if provider_name is not None else settings.answer_provider
    normalized_name = configured_name.strip().lower()
    if normalized_name == DEFAULT_ANSWER_PROVIDER:
        return DeterministicEvidenceAnswerProvider()

    raise UnsupportedAnswerProviderError(
        f"Unsupported answer provider '{configured_name}'. "
        f"Supported providers: {DEFAULT_ANSWER_PROVIDER}."
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

    return AnswerProviderStatus(
        provider_name=configured_name,
        provider_type=AnswerProviderType.UNKNOWN.value,
        display_name=configured_name or "Unconfigured answer provider",
        is_default=False,
        is_available=False,
        requires_api_key=False,
        requires_network=False,
        requires_model_download=False,
        supports_streaming=False,
        status_message=(
            f"Unsupported answer provider '{configured_name}'. "
            f"Supported providers: {DEFAULT_ANSWER_PROVIDER}."
        ),
    )
