from pathlib import Path

from fastapi.testclient import TestClient

from app.ingestion.artifacts import document_artifact_dir
from app.main import app


def _upload(
    client: TestClient,
    filename: str,
    content: bytes,
    content_type: str,
) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == 201
    return response.json()


def test_text_and_markdown_ingestion_success() -> None:
    client = TestClient(app)
    cases = [
        ("notes.txt", b"Plain text evidence", "text/plain", "Plain text evidence"),
        ("paper.md", b"# Heading\n\nMarkdown evidence", "text/markdown", "Markdown evidence"),
    ]

    for filename, content, content_type, expected_text in cases:
        created = _upload(client, filename, content, content_type)
        document_id = str(created["id"])

        assert created["status"] == "ready"
        artifact_path = document_artifact_dir(document_id) / "extracted_text.txt"
        assert artifact_path.exists()
        assert expected_text in artifact_path.read_text(encoding="utf-8")

        preview_response = client.get(
            f"/documents/{document_id}/ingestion/text-preview",
            params={"max_chars": 100},
        )
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert expected_text in preview["text"]
        assert preview["total_characters"] >= len(expected_text)


def test_unsupported_extraction_marks_ingestion_failed() -> None:
    client = TestClient(app)
    created = _upload(client, "figure.png", b"not an extracted text format", "image/png")
    document_id = str(created["id"])

    assert created["status"] == "failed"

    status_response = client.get(f"/documents/{document_id}/ingestion")
    assert status_response.status_code == 200
    job = status_response.json()
    assert job["status"] == "failed"
    assert job["stage"] == "unsupported"
    assert "No text extractor" in job["error_message"]

    preview_response = client.get(f"/documents/{document_id}/ingestion/text-preview")
    assert preview_response.status_code == 404


def test_ingestion_status_endpoint_returns_latest_job() -> None:
    client = TestClient(app)
    created = _upload(client, "status.txt", b"Status endpoint text", "text/plain")
    document_id = str(created["id"])

    response = client.get(f"/documents/{document_id}/ingestion")
    assert response.status_code == 200
    job = response.json()
    assert job["document_id"] == document_id
    assert job["status"] == "completed"
    assert job["stage"] == "completed"
    assert job["started_at"] is not None
    assert job["finished_at"] is not None


def test_retry_ingestion_endpoint_reruns_extraction() -> None:
    client = TestClient(app)
    created = _upload(client, "retry.txt", b"Retry endpoint text", "text/plain")
    document_id = str(created["id"])

    response = client.post(f"/documents/{document_id}/ingestion")
    assert response.status_code == 200
    job = response.json()
    assert job["document_id"] == document_id
    assert job["status"] == "completed"
    assert job["stage"] == "completed"

    preview_path = Path(document_artifact_dir(document_id) / "extracted_text.txt")
    assert "Retry endpoint text" in preview_path.read_text(encoding="utf-8")
