import json

import pytest
import httpx

from app.generation.answer_service import (
    AnswerRequest,
    DeterministicEvidenceAnswerProvider,
    EvidenceInput,
    OpenAICompatibleAnswerProvider,
    OpenAICompatibleProviderConfig,
    UnsupportedAnswerProviderError,
    get_answer_provider,
)


def _evidence_input() -> EvidenceInput:
    return EvidenceInput(
        rank=1,
        score=2.5,
        document_id="doc-1",
        document_title="Local Evidence Notes",
        document_filename="local-evidence-notes.txt",
        chunk_id="chunk-1",
        chunk_index=0,
        text="PaperLens keeps deterministic evidence previews grounded in retrieved chunks.",
        page_number=None,
    )


def test_deterministic_provider_returns_stable_output() -> None:
    provider = DeterministicEvidenceAnswerProvider()
    request = AnswerRequest(question="How does PaperLens answer?", evidence=[_evidence_input()])

    first = provider.generate(request)
    second = provider.generate(request)

    assert first == second
    assert first.provider == "deterministic-evidence"
    assert first.model == "evidence-preview-template-v1"
    assert first.provenance is not None
    assert first.provenance.provider_name == "deterministic-evidence"
    assert first.provenance.provider_type == "deterministic"
    assert first.provenance.model_name == "evidence-preview-template-v1"
    assert first.provenance.fallback_used is False
    assert first.provenance.fallback_reason is None
    assert "Evidence preview" in first.content
    assert "No external LLM" in first.content
    assert "chunk_id=chunk-1" in first.content


def test_deterministic_provider_no_evidence_message_is_clear() -> None:
    provider = DeterministicEvidenceAnswerProvider()
    result = provider.generate(AnswerRequest(question="missing topic", evidence=[]))

    assert "no relevant evidence was found" in result.content
    assert "local lexical search did not match any indexed chunks" in result.content


def test_answer_provider_factory_returns_default_provider() -> None:
    provider = get_answer_provider("deterministic-evidence")

    assert isinstance(provider, DeterministicEvidenceAnswerProvider)


def test_answer_provider_factory_returns_openai_compatible_provider() -> None:
    provider = get_answer_provider("openai-compatible")

    assert isinstance(provider, OpenAICompatibleAnswerProvider)


def test_answer_provider_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(UnsupportedAnswerProviderError, match="Unsupported answer provider"):
        get_answer_provider("free-tier-future-provider")


def test_openai_compatible_provider_missing_config_falls_back_to_deterministic_preview() -> None:
    provider = OpenAICompatibleAnswerProvider(
        OpenAICompatibleProviderConfig(
            base_url=None,
            api_key=None,
            model=None,
            timeout_seconds=5,
            max_tokens=200,
            temperature=0,
        )
    )

    result = provider.generate(
        AnswerRequest(question="How does it answer?", evidence=[_evidence_input()])
    )

    assert result.provider == "openai-compatible"
    assert result.model == "unconfigured"
    assert result.provenance is not None
    assert result.provenance.provider_name == "openai-compatible"
    assert result.provenance.provider_type == "openai-compatible"
    assert result.provenance.model_name == "unconfigured"
    assert result.provenance.fallback_used is True
    assert result.provenance.fallback_reason == (
        "llm_base_url is required for the OpenAI-compatible answer provider."
    )
    assert "OpenAI-compatible answer provider is unavailable" in result.content
    assert "llm_base_url is required" in result.content
    assert "Falling back to the deterministic evidence preview" in result.content
    assert "No external LLM was called" in result.content


def test_openai_compatible_provider_builds_chat_completions_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("Authorization")
        captured["payload"] = request.read()
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "Use Evidence 1 only."}}]},
        )

    config = OpenAICompatibleProviderConfig(
        base_url="https://provider.example.test/v1",
        api_key="test-secret",
        model="free-model",
        timeout_seconds=5,
        max_tokens=321,
        temperature=0.2,
        requires_api_key=True,
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleAnswerProvider(config=config, client=client)
        result = provider.generate(
            AnswerRequest(question="What is the evidence?", evidence=[_evidence_input()])
        )

    raw_payload = captured["payload"]
    assert isinstance(raw_payload, bytes)
    payload = json.loads(raw_payload)
    assert captured["url"] == "https://provider.example.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-secret"
    assert payload["model"] == "free-model"
    assert payload["max_tokens"] == 321
    assert payload["temperature"] == 0.2
    assert payload["stream"] is False
    assert payload["messages"][0]["role"] == "system"
    assert "Answer only from the evidence snippets" in payload["messages"][0]["content"]
    assert payload["messages"][1]["role"] == "user"
    assert "Evidence 1" in payload["messages"][1]["content"]
    assert "chunk_id=chunk-1" in payload["messages"][1]["content"]
    assert "Evidence-grounded answer draft" in result.content
    assert "Use Evidence 1 only." in result.content
    assert "test-secret" not in result.content
    assert result.provenance is not None
    assert result.provenance.provider_name == "openai-compatible"
    assert result.provenance.provider_type == "openai-compatible"
    assert result.provenance.model_name == "free-model"
    assert result.provenance.fallback_used is False
    assert result.provenance.fallback_reason is None


@pytest.mark.parametrize(
    ("status_code", "expected_text"),
    [
        (429, "rate limit"),
        (500, "HTTP 500"),
    ],
)
def test_openai_compatible_provider_handles_provider_errors_gracefully(
    status_code: int,
    expected_text: str,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status_code, json={"error": {"message": "provider error"}})

    config = OpenAICompatibleProviderConfig(
        base_url="https://provider.example.test/v1",
        api_key=None,
        model="free-model",
        timeout_seconds=5,
        max_tokens=200,
        temperature=0,
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleAnswerProvider(config=config, client=client)
        result = provider.generate(
            AnswerRequest(question="What is the evidence?", evidence=[_evidence_input()])
        )

    assert expected_text in result.content
    assert "Falling back to the deterministic evidence preview" in result.content
    assert "provider error" not in result.content
    assert result.provenance is not None
    assert result.provenance.fallback_used is True
    assert expected_text in (result.provenance.fallback_reason or "")


def test_openai_compatible_provider_handles_timeout_gracefully() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    config = OpenAICompatibleProviderConfig(
        base_url="https://provider.example.test/v1",
        api_key=None,
        model="free-model",
        timeout_seconds=5,
        max_tokens=200,
        temperature=0,
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleAnswerProvider(config=config, client=client)
        result = provider.generate(
            AnswerRequest(question="What is the evidence?", evidence=[_evidence_input()])
        )

    assert "request timed out" in result.content
    assert "Falling back to the deterministic evidence preview" in result.content
    assert result.provenance is not None
    assert result.provenance.fallback_used is True
    assert result.provenance.fallback_reason == "The provider request timed out."


def test_openai_compatible_provider_handles_invalid_response_gracefully() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json={"choices": []})

    config = OpenAICompatibleProviderConfig(
        base_url="https://provider.example.test/v1",
        api_key=None,
        model="free-model",
        timeout_seconds=5,
        max_tokens=200,
        temperature=0,
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleAnswerProvider(config=config, client=client)
        result = provider.generate(
            AnswerRequest(question="What is the evidence?", evidence=[_evidence_input()])
        )

    assert "invalid response" in result.content
    assert "Falling back to the deterministic evidence preview" in result.content
    assert result.provenance is not None
    assert result.provenance.fallback_used is True
    assert result.provenance.fallback_reason == "The provider returned an invalid response."
