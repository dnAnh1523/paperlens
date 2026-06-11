from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_upload_list_and_read_document() -> None:
    client = TestClient(app)
    response = client.post(
        "/documents",
        files={"file": ("paper.txt", b"PaperLens test paper", "text/plain")},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["original_filename"] == "paper.txt"
    assert created["status"] == "ready"
    assert Path(created["storage_path"]).exists()

    list_response = client.get("/documents")
    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json())

    detail_response = client.get(f"/documents/{created['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == created["id"]
    assert len(detail["ingestion_jobs"]) == 1
    assert detail["ingestion_jobs"][0]["stage"] == "completed"


def test_upload_rejects_unsupported_content_type() -> None:
    client = TestClient(app)
    response = client.post(
        "/documents",
        files={"file": ("archive.zip", b"not allowed", "application/zip")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
