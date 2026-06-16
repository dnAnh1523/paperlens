from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
import httpx

from app.db.session import SessionLocal
from app.generation.answer_service import (
    AnswerRequest,
    AnswerResult,
    OpenAICompatibleAnswerProvider,
    OpenAICompatibleProviderConfig,
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

    pdf: Any = fitz.open()
    for text in pages:
        page = pdf.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=11)
    try:
        return cast(bytes, pdf.tobytes())
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
    return cast(dict[str, object], document)


def _create_chunked_text_document(client: TestClient, filename: str, text: str) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={"file": (filename, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    document = response.json()

    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200
    assert len(chunk_response.json()) >= 1
    return cast(dict[str, object], document)


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
    return cast(dict[str, object], document)


def test_create_conversation() -> None:
    client = TestClient(app)
    response = client.post("/conversations", json={"title": "Milestone 5 chat"})

    assert response.status_code == 201
    conversation = response.json()
    assert conversation["conversation_id"]
    assert conversation["title"] == "Milestone 5 chat"
    assert conversation["created_at"]
    assert conversation["updated_at"]
    assert conversation["scoped_document_id"] is None
    assert conversation["scoped_document"] is None


def test_create_scoped_conversation_exposes_document_metadata() -> None:
    client = TestClient(app)
    term = _term("chatscopedcreate")
    document = _create_chunked_document(client, term)

    response = client.post(
        "/conversations",
        json={"title": "Scoped paper chat", "scoped_document_id": document["id"]},
    )

    assert response.status_code == 201
    conversation = response.json()
    assert conversation["title"] == "Scoped paper chat"
    assert conversation["scoped_document_id"] == document["id"]
    assert conversation["scoped_document"] == {
        "id": document["id"],
        "title": document["title"],
        "original_filename": document["original_filename"],
    }


def test_create_scoped_conversation_rejects_missing_document() -> None:
    client = TestClient(app)

    response = client.post(
        "/conversations",
        json={"scoped_document_id": "missing-document-id"},
    )

    assert response.status_code == 404
    assert "Scoped document not found" in response.json()["detail"]


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
    assert turn["assistant_message"]["answer_provenance"] == {
        "provider_name": "deterministic-evidence",
        "provider_type": "deterministic",
        "model_name": "evidence-preview-template-v1",
        "fallback_used": False,
        "fallback_reason": None,
    }
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


def test_scoped_conversation_retrieves_only_scoped_document() -> None:
    client = TestClient(app)
    scoped_term = _term("chatscopedinside")
    other_term = _term("chatscopedoutside")
    scoped_document = _create_chunked_document(client, scoped_term)
    other_document = _create_chunked_document(client, other_term)
    conversation = client.post(
        "/conversations",
        json={"title": "Scoped chat", "scoped_document_id": scoped_document["id"]},
    ).json()

    other_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": other_term},
    )

    assert other_response.status_code == 200
    other_assistant = other_response.json()["assistant_message"]
    assert other_assistant["evidence"] == []
    assert "no relevant evidence was found" in other_assistant["content"]

    scoped_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": scoped_term},
    )

    assert scoped_response.status_code == 200
    scoped_assistant = scoped_response.json()["assistant_message"]
    assert scoped_assistant["evidence"]
    assert {item["document_id"] for item in scoped_assistant["evidence"]} == {scoped_document["id"]}
    assert other_document["id"] not in {item["document_id"] for item in scoped_assistant["evidence"]}


def test_scoped_conversation_with_overlapping_terms_excludes_other_document() -> None:
    client = TestClient(app)
    shared_term = _term("scopedshared")
    alpha_marker = _term("alphascoped")
    beta_marker = _term("betascoped")
    alpha_document = _create_chunked_text_document(
        client,
        f"{alpha_marker}.txt",
        (
            f"The shared calibration study uses marker {shared_term}. "
            f"The selected document reports alpha-only evidence {alpha_marker} "
            "and a twelve-minute calibration window."
        ),
    )
    beta_document = _create_chunked_text_document(
        client,
        f"{beta_marker}.txt",
        (
            f"The shared calibration study uses marker {shared_term}. "
            f"The unrelated document reports beta-only evidence {beta_marker} "
            "and a thirty-minute stabilization window."
        ),
    )
    conversation = client.post(
        "/conversations",
        json={"title": "Scoped overlap", "scoped_document_id": alpha_document["id"]},
    ).json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": shared_term},
        params={"limit": 5},
    )

    assert response.status_code == 200
    evidence = response.json()["assistant_message"]["evidence"]
    assert evidence
    assert {item["document_id"] for item in evidence} == {alpha_document["id"]}
    assert beta_document["id"] not in {item["document_id"] for item in evidence}
    assert all(beta_marker not in item["excerpt"] for item in evidence)


def test_unscoped_conversation_still_retrieves_across_documents() -> None:
    client = TestClient(app)
    scoped_term = _term("chatunscopedinside")
    other_term = _term("chatunscopedoutside")
    _create_chunked_document(client, scoped_term)
    other_document = _create_chunked_document(client, other_term)
    conversation = client.post("/conversations").json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": other_term},
    )

    assert response.status_code == 200
    assistant = response.json()["assistant_message"]
    assert assistant["evidence"]
    assert assistant["evidence"][0]["document_id"] == other_document["id"]


def test_unscoped_conversation_with_overlapping_terms_can_return_multiple_documents() -> None:
    client = TestClient(app)
    shared_term = _term("unscopedshared")
    first_marker = _term("firstglobal")
    second_marker = _term("secondglobal")
    first_document = _create_chunked_text_document(
        client,
        f"{first_marker}.txt",
        f"The global retrieval corpus includes shared marker {shared_term} and first marker {first_marker}.",
    )
    second_document = _create_chunked_text_document(
        client,
        f"{second_marker}.txt",
        f"The global retrieval corpus includes shared marker {shared_term} and second marker {second_marker}.",
    )
    conversation = client.post("/conversations").json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": shared_term},
        params={"limit": 5},
    )

    assert response.status_code == 200
    evidence_document_ids = {
        item["document_id"] for item in response.json()["assistant_message"]["evidence"]
    }
    assert {first_document["id"], second_document["id"]}.issubset(evidence_document_ids)


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
    assert turn.assistant_message.answer_provenance == {
        "provider_name": "recording-test",
        "provider_type": "unknown",
        "model_name": "recording-test-v1",
        "fallback_used": False,
        "fallback_reason": None,
    }
    assert turn.assistant_message.evidence
    assert turn.assistant_message.evidence[0].document_id == document["id"]


def test_post_user_message_can_use_mocked_openai_compatible_provider() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "The answer is grounded in Evidence 1."}}]},
        )

    client = TestClient(app)
    term = _term("chatopenaiadapter")
    document = _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()
    config = OpenAICompatibleProviderConfig(
        base_url="https://provider.example.test/v1",
        api_key=None,
        model="free-model",
        timeout_seconds=5,
        max_tokens=200,
        temperature=0,
    )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        provider = OpenAICompatibleAnswerProvider(config=config, client=http_client)
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

    assert "Evidence-grounded answer draft" in turn.assistant_message.content
    assert "Evidence 1" in turn.assistant_message.content
    assert turn.assistant_message.answer_provenance == {
        "provider_name": "openai-compatible",
        "provider_type": "openai-compatible",
        "model_name": "free-model",
        "fallback_used": False,
        "fallback_reason": None,
    }
    assert turn.assistant_message.evidence
    assert turn.assistant_message.evidence[0].document_id == document["id"]


def test_post_user_message_records_openai_compatible_fallback_provenance() -> None:
    client = TestClient(app)
    term = _term("chatopenallback")
    _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()
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

    assert "Falling back to the deterministic evidence preview" in turn.assistant_message.content
    assert turn.assistant_message.answer_provenance == {
        "provider_name": "openai-compatible",
        "provider_type": "openai-compatible",
        "model_name": "unconfigured",
        "fallback_used": True,
        "fallback_reason": "llm_base_url is required for the OpenAI-compatible answer provider.",
    }


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
    assert assistant["answer_provenance"]["provider_name"] == "deterministic-evidence"
    assert assistant["answer_provenance"]["fallback_used"] is False


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
    assert messages[0]["answer_provenance"] is None
    assert messages[1]["answer_provenance"]["provider_name"] == "deterministic-evidence"
    assert messages[1]["evidence"]


def test_update_user_message_regenerates_turn_in_place() -> None:
    client = TestClient(app)
    old_term = _term("chateditold")
    new_term = _term("chateditnew")
    later_term = _term("chateditlater")
    old_document = _create_chunked_document(client, old_term)
    new_document = _create_chunked_document(client, new_term)
    _create_chunked_document(client, later_term)
    conversation = client.post("/conversations", json={"title": "Editable chat"}).json()
    conversation_id = conversation["conversation_id"]

    first_turn_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": old_term},
    )
    assert first_turn_response.status_code == 200
    first_turn = first_turn_response.json()
    user_message_id = first_turn["user_message"]["message_id"]
    old_assistant_message_id = first_turn["assistant_message"]["message_id"]
    old_evidence_id = first_turn["assistant_message"]["evidence"][0]["evidence_id"]

    later_turn_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": later_term},
    )
    assert later_turn_response.status_code == 200
    later_turn = later_turn_response.json()

    update_response = client.patch(
        f"/conversations/{conversation_id}/messages/{user_message_id}",
        json={"content": new_term},
    )

    assert update_response.status_code == 200
    updated_turn = update_response.json()
    assert updated_turn["user_message"]["message_id"] == user_message_id
    assert updated_turn["user_message"]["content"] == new_term
    assert updated_turn["assistant_message"]["message_id"] != old_assistant_message_id
    assert updated_turn["assistant_message"]["evidence"]
    assert {item["document_id"] for item in updated_turn["assistant_message"]["evidence"]} == {
        new_document["id"]
    }
    assert old_document["id"] not in {
        item["document_id"] for item in updated_turn["assistant_message"]["evidence"]
    }

    history_response = client.get(f"/conversations/{conversation_id}/messages")
    assert history_response.status_code == 200
    messages = history_response.json()
    assert [message["role"] for message in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[0]["message_id"] == user_message_id
    assert messages[0]["content"] == new_term
    assert messages[1]["message_id"] == updated_turn["assistant_message"]["message_id"]
    assert messages[2]["message_id"] == later_turn["user_message"]["message_id"]

    with SessionLocal() as db:
        assert db.get(Message, old_assistant_message_id) is None
        assert db.get(MessageEvidence, old_evidence_id) is None


def test_update_message_rejects_assistant_message() -> None:
    client = TestClient(app)
    term = _term("chateditassistant")
    _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()
    conversation_id = conversation["conversation_id"]
    post_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": term},
    )
    assert post_response.status_code == 200
    assistant_message_id = post_response.json()["assistant_message"]["message_id"]

    update_response = client.patch(
        f"/conversations/{conversation_id}/messages/{assistant_message_id}",
        json={"content": "do not edit assistant messages"},
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "User message not found"


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


def test_workspace_isolation() -> None:
    client = TestClient(app)
    term1 = _term("workspaceisolated1")
    term2 = _term("workspaceisolated2")
    doc1 = _create_chunked_document(client, term1)
    doc2 = _create_chunked_document(client, term2)

    # Create workspace with only doc1
    ws = client.post("/conversations", json={"title": "WS 1", "source_document_ids": [doc1["id"]]}).json()
    assert ws["source_document_ids"] == [doc1["id"]]

    # Query term2 (doc2) inside WS 1 -> should return 0 chunks since doc2 is isolated from WS 1
    resp = client.post(f"/conversations/{ws['conversation_id']}/messages", json={"content": term2})
    assert resp.status_code == 200
    assert resp.json()["assistant_message"]["evidence"] == []

    # Query term1 (doc1) inside WS 1 -> should retrieve from doc1
    resp = client.post(f"/conversations/{ws['conversation_id']}/messages", json={"content": term1})
    assert resp.status_code == 200
    assert len(resp.json()["assistant_message"]["evidence"]) >= 1
    assert resp.json()["assistant_message"]["evidence"][0]["document_id"] == doc1["id"]

    # PATCH workspace to assign doc2 as well
    patch_resp = client.patch(f"/conversations/{ws['conversation_id']}", json={"source_document_ids": [doc1["id"], doc2["id"]]})
    assert patch_resp.status_code == 200
    assert set(patch_resp.json()["source_document_ids"]) == {doc1["id"], doc2["id"]}

    # Query term2 (doc2) inside WS 1 -> now it should retrieve from doc2
    resp = client.post(f"/conversations/{ws['conversation_id']}/messages", json={"content": term2})
    assert resp.status_code == 200
    assert len(resp.json()["assistant_message"]["evidence"]) >= 1
    assert resp.json()["assistant_message"]["evidence"][0]["document_id"] == doc2["id"]
