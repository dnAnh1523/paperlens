from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.generation.answer_service import (
    AnswerRequest,
    AnswerResult,
    UnsupportedAnswerProviderError,
)
from app.main import app
from app.models.conversation import Conversation, Message, MessageEvidence
from app.services.chat_service import post_user_message


def _term(prefix: str) -> str:
    return f"{prefix}{uuid4().hex}"


def _unique_text(term: str) -> str:
    return (
        f"{term} appears in the local evidence corpus. "
        "PaperLens stores retrieved chunks before drafting chat evidence. "
        "This local test document has enough context for a deterministic citation."
    )


def _text_layer_pdf(pages: list[str]) -> bytes:
    import fitz

    pdf = fitz.open()
    for text in pages:
        page = pdf.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=11)
    try:
        return pdf.tobytes()
    finally:
        pdf.close()


def _create_chunked_document(client: TestClient, term: str) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={"file": (f"{term}.txt", _unique_text(term).encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    document = response.json()

    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200
    assert len(chunk_response.json()) >= 1
    return document


def _create_chunked_pdf_document(client: TestClient, term: str) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={
            "file": (
                f"{term}.pdf",
                _text_layer_pdf(
                    [
                        "Page one contains background context.",
                        f"Page two contains chat evidence term {term}.",
                    ]
                ),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    document = response.json()

    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200
    assert len(chunk_response.json()) >= 2
    return document


def test_create_conversation() -> None:
    client = TestClient(app)
    response = client.post("/conversations", json={"title": "Milestone 5 chat"})

    assert response.status_code == 201
    conversation = response.json()
    assert conversation["conversation_id"]
    assert conversation["title"] == "Milestone 5 chat"
    assert conversation["created_at"]
    assert conversation["updated_at"]


def test_list_conversations() -> None:
    client = TestClient(app)
    title = "List conversations m5 unique"
    create_response = client.post("/conversations", json={"title": title})
    assert create_response.status_code == 201

    list_response = client.get("/conversations")
    assert list_response.status_code == 200
    assert any(item["title"] == title for item in list_response.json())


def test_post_message_creates_user_assistant_and_evidence() -> None:
    client = TestClient(app)
    term = _term("chatneedlealpha")
    document = _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
        params={"limit": 3},
    )

    assert response.status_code == 200
    turn = response.json()
    assert turn["user_message"]["role"] == "user"
    assert turn["assistant_message"]["role"] == "assistant"
    assert "Evidence preview" in turn["assistant_message"]["content"]
    assert "No external LLM" in turn["assistant_message"]["content"]
    assert len(turn["assistant_message"]["evidence"]) >= 1
    evidence = turn["assistant_message"]["evidence"][0]
    assert evidence["document_id"] == document["id"]
    assert evidence["chunk_id"]
    assert evidence["rank"] == 1
    assert evidence["score"] > 0
    assert term in evidence["excerpt"]
    assert term in evidence["full_chunk_text_snapshot"]
    assert evidence["document_title_snapshot"] == document["title"]
    assert evidence["document_filename_snapshot"] == document["original_filename"]
    assert evidence["chunk_index_snapshot"] == 0
    assert evidence["char_start_snapshot"] is not None
    assert evidence["char_end_snapshot"] is not None
    assert evidence["estimated_token_count_snapshot"] is not None
    assert evidence["page_number"] is None


def test_post_user_message_uses_answer_provider_interface() -> None:
    class RecordingAnswerProvider:
        provider_name = "recording-test"
        model_name = "recording-test-v1"

        def __init__(self) -> None:
            self.request: AnswerRequest | None = None

        def generate(self, request: AnswerRequest) -> AnswerResult:
            self.request = request
            return AnswerResult(
                provider=self.provider_name,
                model=self.model_name,
                content=f"Provider response with {len(request.evidence)} evidence rows.",
            )

    client = TestClient(app)
    term = _term("chatprovider")
    document = _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()
    provider = RecordingAnswerProvider()

    with SessionLocal() as db:
        stored_conversation = db.get(Conversation, conversation["conversation_id"])
        assert stored_conversation is not None

        turn = post_user_message(
            db,
            conversation=stored_conversation,
            content=term,
            evidence_limit=3,
            answer_provider=provider,
        )

    assert provider.request is not None
    assert provider.request.question == term
    assert provider.request.evidence
    assert provider.request.evidence[0].document_id == document["id"]
    assert turn.assistant_message.content.startswith("Provider response with")
    assert turn.assistant_message.evidence
    assert turn.assistant_message.evidence[0].document_id == document["id"]


def test_post_message_evidence_includes_pdf_page_metadata() -> None:
    client = TestClient(app)
    term = _term("chatpdfpagegamma")
    document = _create_chunked_pdf_document(client, term)
    conversation = client.post("/conversations").json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
        params={"limit": 3},
    )

    assert response.status_code == 200
    assistant = response.json()["assistant_message"]
    assert "page=2" in assistant["content"]
    assert len(assistant["evidence"]) >= 1
    evidence = assistant["evidence"][0]
    assert evidence["document_id"] == document["id"]
    assert evidence["page_number"] == 2
    assert evidence["page_start"] is not None
    assert evidence["page_end"] is not None
    assert evidence["chunk_index_snapshot"] == 1
    assert term in evidence["full_chunk_text_snapshot"]


def test_evidence_source_endpoint_returns_live_context() -> None:
    client = TestClient(app)
    term = _term("chatsourcelive")
    _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()

    post_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
    )
    assert post_response.status_code == 200
    assistant = post_response.json()["assistant_message"]
    evidence = assistant["evidence"][0]

    source_response = client.get(
        f"/conversations/{conversation['conversation_id']}/messages/"
        f"{assistant['message_id']}/evidence/{evidence['evidence_id']}/source"
    )

    assert source_response.status_code == 200
    source = source_response.json()
    assert source["source_status"] == "live"
    assert source["is_stale"] is False
    assert source["note"] is None
    assert source["selected_chunk"]["chunk_id"] == evidence["chunk_id"]
    assert term in source["selected_chunk"]["text"]


def test_evidence_source_falls_back_to_snapshot_after_rechunking() -> None:
    client = TestClient(app)
    term = _term("chatsourcerechunk")
    document = _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()

    post_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
    )
    assert post_response.status_code == 200
    assistant = post_response.json()["assistant_message"]
    evidence = assistant["evidence"][0]

    rechunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert rechunk_response.status_code == 200
    assert evidence["chunk_id"] not in {chunk["chunk_id"] for chunk in rechunk_response.json()}

    source_response = client.get(
        f"/conversations/{conversation['conversation_id']}/messages/"
        f"{assistant['message_id']}/evidence/{evidence['evidence_id']}/source"
    )

    assert source_response.status_code == 200
    source = source_response.json()
    assert source["source_status"] == "snapshot"
    assert source["is_stale"] is True
    assert "chunk was regenerated or deleted" in source["note"]
    assert source["selected_chunk"]["chunk_id"] == evidence["chunk_id"]
    assert source["selected_chunk"]["text"] == evidence["full_chunk_text_snapshot"]
    assert source["document"]["original_filename"] == evidence["document_filename_snapshot"]


def test_evidence_source_falls_back_to_snapshot_after_document_delete() -> None:
    client = TestClient(app)
    term = _term("chatsourcedelete")
    document = _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()

    post_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
    )
    assert post_response.status_code == 200
    assistant = post_response.json()["assistant_message"]
    evidence = assistant["evidence"][0]

    delete_response = client.delete(f"/documents/{document['id']}")
    assert delete_response.status_code == 204

    source_response = client.get(
        f"/conversations/{conversation['conversation_id']}/messages/"
        f"{assistant['message_id']}/evidence/{evidence['evidence_id']}/source"
    )

    assert source_response.status_code == 200
    source = source_response.json()
    assert source["source_status"] == "snapshot"
    assert source["is_stale"] is True
    assert source["document"]["title"] == evidence["document_title_snapshot"]
    assert term in source["selected_chunk"]["text"]


def test_no_evidence_case_creates_clear_assistant_message() -> None:
    client = TestClient(app)
    conversation = client.post("/conversations", json={"title": "No evidence chat"}).json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": "unmatchedquerym5nothing"},
    )

    assert response.status_code == 200
    assistant = response.json()["assistant_message"]
    assert assistant["role"] == "assistant"
    assert assistant["evidence"] == []
    assert "no relevant evidence was found" in assistant["content"]


def test_unsupported_answer_provider_returns_clear_api_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_unsupported_provider():
        raise UnsupportedAnswerProviderError(
            "Unsupported answer provider 'future-provider'. "
            "Supported providers: deterministic-evidence."
        )

    monkeypatch.setattr(
        "app.services.chat_service.get_answer_provider",
        raise_unsupported_provider,
    )
    client = TestClient(app)
    conversation = client.post("/conversations").json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": "hello"},
    )

    assert response.status_code == 500
    assert "Unsupported answer provider" in response.json()["detail"]


def test_reading_message_history_returns_user_and_assistant_messages() -> None:
    client = TestClient(app)
    term = _term("chatneedlehistory")
    _create_chunked_document(client, term)
    conversation = client.post("/conversations", json={"title": "History chat"}).json()

    post_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
    )
    assert post_response.status_code == 200

    history_response = client.get(f"/conversations/{conversation['conversation_id']}/messages")
    assert history_response.status_code == 200
    messages = history_response.json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["evidence"]


def test_delete_conversation_cascades_messages_and_evidence() -> None:
    client = TestClient(app)
    term = _term("chatneedledelete")
    _create_chunked_document(client, term)
    conversation = client.post("/conversations", json={"title": "Delete chat"}).json()
    conversation_id = conversation["conversation_id"]

    post_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": term},
    )
    assert post_response.status_code == 200
    turn = post_response.json()
    user_message_id = turn["user_message"]["message_id"]
    assistant_message_id = turn["assistant_message"]["message_id"]
    evidence_id = turn["assistant_message"]["evidence"][0]["evidence_id"]

    delete_response = client.delete(f"/conversations/{conversation_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/conversations/{conversation_id}/messages").status_code == 404

    with SessionLocal() as db:
        assert db.get(Conversation, conversation_id) is None
        assert db.get(Message, user_message_id) is None
        assert db.get(Message, assistant_message_id) is None
        assert db.get(MessageEvidence, evidence_id) is None
