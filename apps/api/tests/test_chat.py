from fastapi.testclient import TestClient
from uuid import uuid4

from app.db.session import SessionLocal
from app.main import app
from app.models.conversation import Conversation, Message, MessageEvidence


def _term(prefix: str) -> str:
    return f"{prefix}{uuid4().hex}"


def _unique_text(term: str) -> str:
    return (
        f"{term} appears in the local evidence corpus. "
        "PaperLens stores retrieved chunks before drafting chat evidence. "
        "This local test document has enough context for a deterministic citation."
    )


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
