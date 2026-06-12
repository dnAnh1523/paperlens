import pytest

from app.generation.answer_service import (
    AnswerRequest,
    DeterministicEvidenceAnswerProvider,
    EvidenceInput,
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


def test_answer_provider_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(UnsupportedAnswerProviderError, match="Unsupported answer provider"):
        get_answer_provider("free-tier-future-provider")
