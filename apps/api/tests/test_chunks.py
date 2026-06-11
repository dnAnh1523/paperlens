from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


def _term(prefix: str) -> str:
    return f"{prefix}{uuid4().hex}"


def _upload_text(client: TestClient, filename: str, text: str) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={"file": (filename, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "ready"
    return created


def _long_text(unique_term: str) -> str:
    paragraphs = [
        (
            f"Paragraph {index} explains PaperLens chunking with {unique_term}. "
            "It keeps source offsets, stores local SQLite rows, and supports lexical search. "
            "This sentence adds enough length for deterministic chunk boundaries."
        )
        for index in range(24)
    ]
    return "\n\n".join(paragraphs)


def test_chunking_success_for_ingested_text_and_markdown() -> None:
    client = TestClient(app)

    text_document = _upload_text(client, "chunk-source.txt", _long_text(_term("chunktextalpha")))
    markdown_response = client.post(
        "/documents",
        files={
            "file": (
                "chunk-source.md",
                _long_text(_term("chunkmarkdownbeta")).encode("utf-8"),
                "text/markdown",
            )
        },
    )
    assert markdown_response.status_code == 201
    markdown_document = markdown_response.json()

    for document in (text_document, markdown_document):
        response = client.post(f"/documents/{document['id']}/chunks")
        assert response.status_code == 200
        chunks = response.json()
        assert len(chunks) >= 2
        assert chunks[0]["document_id"] == document["id"]
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["char_start"] >= 0
        assert chunks[0]["char_end"] > chunks[0]["char_start"]
        assert chunks[0]["estimated_token_count"] > 0
        assert chunks[0]["text"]


def test_list_chunks_for_document_with_pagination() -> None:
    client = TestClient(app)
    document = _upload_text(client, "list-chunks.txt", _long_text(_term("chunklistgamma")))
    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200

    list_response = client.get(
        f"/documents/{document['id']}/chunks",
        params={"offset": 0, "limit": 1},
    )
    assert list_response.status_code == 200
    chunks = list_response.json()
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0


def test_get_single_chunk() -> None:
    client = TestClient(app)
    document = _upload_text(client, "single-chunk.txt", _long_text(_term("chunksingledelta")))
    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200
    created_chunk = chunk_response.json()[0]

    get_response = client.get(f"/documents/{document['id']}/chunks/{created_chunk['chunk_id']}")
    assert get_response.status_code == 200
    chunk = get_response.json()
    assert chunk["chunk_id"] == created_chunk["chunk_id"]
    assert chunk["text"] == created_chunk["text"]


def test_rerun_chunking_replaces_old_chunks_without_duplicates() -> None:
    client = TestClient(app)
    document = _upload_text(client, "rerun-chunks.txt", _long_text(_term("chunkrerunepsilon")))

    first_response = client.post(f"/documents/{document['id']}/chunks")
    assert first_response.status_code == 200
    first_chunks = first_response.json()

    second_response = client.post(f"/documents/{document['id']}/chunks")
    assert second_response.status_code == 200
    second_chunks = second_response.json()

    list_response = client.get(f"/documents/{document['id']}/chunks", params={"limit": 100})
    assert list_response.status_code == 200
    listed_chunks = list_response.json()
    assert len(listed_chunks) == len(first_chunks) == len(second_chunks)
    assert sorted(chunk["chunk_index"] for chunk in listed_chunks) == list(range(len(listed_chunks)))


def test_search_chunks_by_query() -> None:
    client = TestClient(app)
    term = _term("retrievalneedleomega")
    document = _upload_text(client, "search-chunks.txt", _long_text(term))
    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200

    search_response = client.get("/search", params={"query": term, "limit": 5})
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["query"] == term
    assert payload["total"] >= 1
    assert payload["results"][0]["score"] > 0
    assert payload["results"][0]["document"]["id"] == document["id"]
    assert term in payload["results"][0]["chunk"]["text"]


def test_chunking_missing_extracted_text_returns_conflict() -> None:
    client = TestClient(app)
    response = client.post(
        "/documents",
        files={"file": ("missing-text.png", b"image bytes", "image/png")},
    )
    assert response.status_code == 201
    document = response.json()
    assert document["status"] == "failed"

    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 409
    assert "Extracted text artifact not found" in chunk_response.json()["detail"]
