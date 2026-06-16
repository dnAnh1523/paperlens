import json
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.embeddings.providers import FakeHashEmbeddingProvider
from app.main import app
from app.models.chunk_embedding import ChunkEmbedding
from app.services.embedding_service import deserialize_vector


def _term(prefix: str) -> str:
    return f"{prefix}{uuid4().hex}"


def _long_text(unique_term: str) -> str:
    return "\n\n".join(
        (
            f"Paragraph {index} contains embedding test term {unique_term}. "
            "PaperLens keeps lexical retrieval separate from local fake vector indexing. "
            "This sentence adds enough text to create deterministic chunks."
        )
        for index in range(16)
    )


def _upload_text(client: TestClient, filename: str, text: str) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={"file": (filename, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def _create_chunked_document(client: TestClient, term: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    document = _upload_text(client, f"{term}.txt", _long_text(term))
    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200
    chunks = chunk_response.json()
    assert len(chunks) >= 1
    return document, chunks


def _embedding_rows(document_id: str) -> list[ChunkEmbedding]:
    with SessionLocal() as db:
        statement = (
            select(ChunkEmbedding)
            .where(ChunkEmbedding.document_id == document_id)
            .order_by(ChunkEmbedding.chunk_id.asc())
        )
        return list(db.scalars(statement).all())


def test_fake_hash_embedding_provider_is_deterministic() -> None:
    provider = FakeHashEmbeddingProvider(dimension=8)

    first = provider.embed_texts(["alpha evidence", "beta evidence"])
    second = provider.embed_texts(["alpha evidence", "beta evidence"])

    assert provider.provider_name == "local-hash"
    assert provider.model_name == "fake-hash-v1"
    assert first == second
    assert len(first) == 2
    assert len(first[0]) == 8
    assert first[0] != first[1]


def test_index_embeddings_for_document_chunks() -> None:
    client = TestClient(app)
    term = _term("embedindexalpha")
    document, chunks = _create_chunked_document(client, term)

    response = client.post(f"/documents/{document['id']}/embeddings", params={"dimension": 16})

    assert response.status_code == 200
    status = response.json()
    assert status["document_id"] == document["id"]
    assert status["provider"] == "local-hash"
    assert status["model"] == "fake-hash-v1"
    assert status["dimension"] == 16
    assert status["chunk_count"] == len(chunks)
    assert status["embedding_count"] == len(chunks)
    assert status["is_indexed"] is True
    assert status["latest_created_at"]

    rows = _embedding_rows(str(document["id"]))
    assert len(rows) == len(chunks)
    stored_vector = deserialize_vector(rows[0].vector)
    assert len(stored_vector) == 16
    assert json.loads(rows[0].vector) == stored_vector


def test_reindexing_embeddings_replaces_existing_rows_without_duplicates() -> None:
    client = TestClient(app)
    term = _term("embedrerunbeta")
    document, chunks = _create_chunked_document(client, term)

    first_response = client.post(f"/documents/{document['id']}/embeddings", params={"dimension": 12})
    assert first_response.status_code == 200
    first_ids = {row.chunk_embedding_id for row in _embedding_rows(str(document["id"]))}

    second_response = client.post(f"/documents/{document['id']}/embeddings", params={"dimension": 12})
    assert second_response.status_code == 200
    second_ids = {row.chunk_embedding_id for row in _embedding_rows(str(document["id"]))}

    assert second_response.json()["embedding_count"] == len(chunks)
    assert len(second_ids) == len(chunks)
    assert first_ids.isdisjoint(second_ids)


def test_embedding_status_endpoint_reports_index_state() -> None:
    client = TestClient(app)
    term = _term("embedstatusgamma")
    document, chunks = _create_chunked_document(client, term)

    initial_response = client.get(f"/documents/{document['id']}/embeddings/status", params={"dimension": 10})
    assert initial_response.status_code == 200
    initial_status = initial_response.json()
    assert initial_status["chunk_count"] == len(chunks)
    assert initial_status["embedding_count"] == 0
    assert initial_status["is_indexed"] is False
    assert initial_status["latest_created_at"] is None

    index_response = client.post(f"/documents/{document['id']}/embeddings", params={"dimension": 10})
    assert index_response.status_code == 200

    indexed_response = client.get(f"/documents/{document['id']}/embeddings/status", params={"dimension": 10})
    assert indexed_response.status_code == 200
    indexed_status = indexed_response.json()
    assert indexed_status["chunk_count"] == len(chunks)
    assert indexed_status["embedding_count"] == len(chunks)
    assert indexed_status["is_indexed"] is True


def test_embedding_index_without_chunks_returns_conflict() -> None:
    client = TestClient(app)
    document = _upload_text(client, "embedding-no-chunks.txt", "Text is ingested but not chunked yet.")

    response = client.post(f"/documents/{document['id']}/embeddings")

    assert response.status_code == 409
    assert "Run chunking before indexing embeddings" in response.json()["detail"]


def test_lexical_search_and_chat_remain_unaffected_by_embedding_index() -> None:
    client = TestClient(app)
    term = _term("embedlexicaldelta")
    document, _chunks = _create_chunked_document(client, term)

    embedding_response = client.post(f"/documents/{document['id']}/embeddings", params={"dimension": 8})
    assert embedding_response.status_code == 200

    search_response = client.get("/search", params={"query": term, "limit": 5})
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["total"] >= 1
    assert search_payload["results"][0]["document"]["id"] == document["id"]
    assert term in search_payload["results"][0]["chunk"]["text"]

    conversation = client.post("/conversations").json()
    chat_response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
    )
    assert chat_response.status_code == 200
    assistant = chat_response.json()["assistant_message"]
    assert assistant["evidence"]
    assert assistant["evidence"][0]["document_id"] == document["id"]
