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


def test_update_document_title() -> None:
    client = TestClient(app)
    response = client.post(
        "/documents",
        files={"file": ("paper.txt", b"PaperLens test paper", "text/plain")},
    )
    assert response.status_code == 201
    created = response.json()

    update_response = client.patch(
        f"/documents/{created['id']}",
        json={"title": "Renamed source"},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert updated["title"] == "Renamed source"
    assert updated["original_filename"] == "paper.txt"


def test_update_document_title_rejects_blank_title() -> None:
    client = TestClient(app)
    response = client.post(
        "/documents",
        files={"file": ("paper.txt", b"PaperLens test paper", "text/plain")},
    )
    assert response.status_code == 201
    created = response.json()

    update_response = client.patch(
        f"/documents/{created['id']}",
        json={"title": "   "},
    )

    assert update_response.status_code == 400
    assert "cannot be empty" in update_response.json()["detail"]


def test_document_workspace_isolation() -> None:
    client = TestClient(app)

    # 1. Create two workspaces
    ws_a = client.post("/conversations", json={"title": "Workspace A"}).json()
    ws_b = client.post("/conversations", json={"title": "Workspace B"}).json()
    ws_a_id = ws_a["conversation_id"]
    ws_b_id = ws_b["conversation_id"]

    # 2. Upload document to Workspace A
    resp_a = client.post(
        "/documents",
        params={"conversation_id": ws_a_id},
        files={"file": ("doc_a.txt", b"Content A", "text/plain")},
    )
    assert resp_a.status_code == 201
    doc_a = resp_a.json()
    assert doc_a["conversation_id"] == ws_a_id

    # 3. Upload document to Workspace B
    resp_b = client.post(
        "/documents",
        params={"conversation_id": ws_b_id},
        files={"file": ("doc_b.txt", b"Content B", "text/plain")},
    )
    assert resp_b.status_code == 201
    doc_b = resp_b.json()
    assert doc_b["conversation_id"] == ws_b_id

    # 4. List documents for Workspace A
    list_a = client.get("/documents", params={"conversation_id": ws_a_id}).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == doc_a["id"]
    assert list_a[0]["original_filename"] == "doc_a.txt"

    # 5. List documents for Workspace B
    list_b = client.get("/documents", params={"conversation_id": ws_b_id}).json()
    assert len(list_b) == 1
    assert list_b[0]["id"] == doc_b["id"]
    assert list_b[0]["original_filename"] == "doc_b.txt"

