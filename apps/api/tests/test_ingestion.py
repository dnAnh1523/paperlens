import json
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


def test_text_layer_pdf_ingestion_writes_page_artifacts_and_metadata() -> None:
    client = TestClient(app)
    pdf_bytes = _text_layer_pdf(
        [
            "Alpha PDF evidence uses E = mc^2 and 1.23e-4 notation.",
            "Beta PDF evidence references Table 2 and local retrieval.",
        ]
    )

    created = _upload(client, "text-layer.pdf", pdf_bytes, "application/pdf")
    document_id = str(created["id"])

    assert created["status"] == "ready"
    artifact_dir = document_artifact_dir(document_id)
    extracted_text = (artifact_dir / "extracted_text.txt").read_text(encoding="utf-8")
    assert "--- Page 1 ---" in extracted_text
    assert "--- Page 2 ---" in extracted_text
    assert "Alpha PDF evidence uses E = mc^2 and 1.23e-4 notation." in extracted_text
    assert "Beta PDF evidence references Table 2 and local retrieval." in extracted_text

    page_one_text = (artifact_dir / "pages" / "page_001.txt").read_text(encoding="utf-8")
    page_two_text = (artifact_dir / "pages" / "page_002.txt").read_text(encoding="utf-8")
    assert "Alpha PDF evidence" in page_one_text
    assert "Beta PDF evidence" in page_two_text

    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["extractor"] == "pdf-text"
    assert metadata["extraction_method"] == "pymupdf.get_text(text)"
    assert metadata["page_count"] == 2
    assert metadata["extracted_page_count"] == 2
    assert metadata["pages_with_text"] == [1, 2]
    assert metadata["pages_without_text"] == []
    assert metadata["warnings"] == []
    assert len(metadata["page_text_paths"]) == 2

    chunk_response = client.post(f"/documents/{document_id}/chunks")
    assert chunk_response.status_code == 200
    chunks = chunk_response.json()
    assert len(chunks) >= 1
    assert "Alpha PDF evidence" in chunks[0]["text"]

    preview_response = client.get(
        f"/documents/{document_id}/ingestion/text-preview",
        params={"max_chars": 500},
    )
    assert preview_response.status_code == 200
    assert "Page 1" in preview_response.json()["text"]


def test_no_text_pdf_ingestion_fails_with_clear_metadata() -> None:
    client = TestClient(app)
    pdf_bytes = _text_layer_pdf([""])

    created = _upload(client, "scanned-placeholder.pdf", pdf_bytes, "application/pdf")
    document_id = str(created["id"])

    assert created["status"] == "failed"
    status_response = client.get(f"/documents/{document_id}/ingestion")
    assert status_response.status_code == 200
    job = status_response.json()
    assert job["status"] == "failed"
    assert job["stage"] == "failed"
    assert "No extractable PDF text layer" in job["error_message"]

    artifact_dir = document_artifact_dir(document_id)
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["page_count"] == 1
    assert metadata["extracted_page_count"] == 0
    assert metadata["pages_with_text"] == []
    assert metadata["pages_without_text"] == [1]
    assert any("OCR" in warning for warning in metadata["warnings"])
    assert (artifact_dir / "pages" / "page_001.txt").exists()
    assert not (artifact_dir / "extracted_text.txt").exists()

    preview_response = client.get(f"/documents/{document_id}/ingestion/text-preview")
    assert preview_response.status_code == 404


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
