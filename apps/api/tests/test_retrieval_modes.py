from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import SessionLocal
from app.evaluation import eval_runner
from app.evaluation.eval_runner import (
    EvalCase,
    EvalDataset,
    format_comparison_report,
    run_retrieval_eval,
    run_retrieval_eval_comparison,
)
from app.main import app
from app.services.retrieval_service import (
    FTS_TABLE_NAME,
    RetrievalBackendUnavailableError,
    RetrievalBackendStatus,
    is_fts5_available,
)


def _term(prefix: str) -> str:
    return f"{prefix}{uuid4().hex}"


def _long_text(unique_term: str) -> str:
    return "\n\n".join(
        (
            f"Paragraph {index} includes retrieval mode term {unique_term}. "
            "PaperLens stores chunks in SQLite and can search them locally. "
            "This sentence gives the chunker enough content for deterministic tests."
        )
        for index in range(18)
    )


def _upload_text(client: TestClient, filename: str, text: str) -> dict[str, object]:
    response = client.post(
        "/documents",
        files={"file": (filename, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def _create_chunked_document(client: TestClient, term: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    document = _upload_text(client, f"{term}.txt", _long_text(term))
    chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert chunk_response.status_code == 200
    chunks = chunk_response.json()
    assert chunks
    return document, chunks


def _fts_row_count(document_id: str) -> int:
    with SessionLocal() as db:
        if not is_fts5_available(db):
            pytest.skip("SQLite FTS5 is not available in this environment.")
        return int(
            db.scalar(
                text(f"SELECT count(*) FROM {FTS_TABLE_NAME} WHERE document_id = :document_id"),
                {"document_id": document_id},
            )
            or 0
        )


def test_fts5_availability_detection_returns_boolean() -> None:
    with SessionLocal() as db:
        assert isinstance(is_fts5_available(db), bool)


def test_search_status_endpoint_reports_backend() -> None:
    client = TestClient(app)

    response = client.get("/search/status")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["fts5_available"], bool)
    assert payload["default_mode"] == "auto"
    assert payload["active_mode"] in {"like", "fts5"}


def test_search_endpoint_like_mode_still_works() -> None:
    client = TestClient(app)
    term = _term("retrievallike")
    document, _chunks = _create_chunked_document(client, term)

    response = client.get("/search", params={"query": term, "limit": 5, "mode": "like"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "like"
    assert payload["backend"] == "like"
    assert payload["total"] >= 1
    assert payload["results"][0]["document"]["id"] == document["id"]
    assert term in payload["results"][0]["chunk"]["text"]


def test_search_endpoint_auto_mode_works() -> None:
    client = TestClient(app)
    term = _term("retrievalauto")
    document, _chunks = _create_chunked_document(client, term)

    response = client.get("/search", params={"query": term, "limit": 5, "mode": "auto"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "auto"
    assert payload["backend"] in {"like", "fts5"}
    assert payload["total"] >= 1
    assert payload["results"][0]["document"]["id"] == document["id"]


def test_search_endpoint_fts5_mode_matches_when_available() -> None:
    client = TestClient(app)
    term = _term("retrievalfts")
    document, _chunks = _create_chunked_document(client, term)

    with SessionLocal() as db:
        available = is_fts5_available(db)

    response = client.get("/search", params={"query": term, "limit": 5, "mode": "fts5"})
    if not available:
        assert response.status_code == 409
        assert "FTS5 is not available" in response.json()["detail"]
        return

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "fts5"
    assert payload["total"] >= 1
    assert payload["results"][0]["document"]["id"] == document["id"]


def test_chunking_updates_fts_index_without_duplicates_when_available() -> None:
    client = TestClient(app)
    term = _term("retrievalftsindex")
    document, chunks = _create_chunked_document(client, term)

    assert _fts_row_count(str(document["id"])) == len(chunks)

    second_chunk_response = client.post(f"/documents/{document['id']}/chunks")
    assert second_chunk_response.status_code == 200
    second_chunks = second_chunk_response.json()
    assert _fts_row_count(str(document["id"])) == len(second_chunks)


def test_document_deletion_removes_fts_search_results_when_available() -> None:
    client = TestClient(app)
    term = _term("retrievaldelete")
    document, _chunks = _create_chunked_document(client, term)
    if _fts_row_count(str(document["id"])) == 0:
        pytest.skip("SQLite FTS5 is not available in this environment.")

    before_delete = client.get("/search", params={"query": term, "mode": "fts5"})
    assert before_delete.status_code == 200
    assert before_delete.json()["total"] >= 1

    delete_response = client.delete(f"/documents/{document['id']}")
    assert delete_response.status_code == 204

    after_delete = client.get("/search", params={"query": term, "mode": "fts5"})
    assert after_delete.status_code == 200
    assert after_delete.json()["total"] == 0


def test_chat_uses_default_retrieval_mode_and_still_creates_evidence() -> None:
    client = TestClient(app)
    term = _term("retrievalchat")
    document, _chunks = _create_chunked_document(client, term)
    conversation = client.post("/conversations").json()

    response = client.post(
        f"/conversations/{conversation['conversation_id']}/messages",
        json={"content": term},
    )

    assert response.status_code == 200
    assistant = response.json()["assistant_message"]
    assert assistant["evidence"]
    assert assistant["evidence"][0]["document_id"] == document["id"]


def test_eval_runner_accepts_retrieval_mode() -> None:
    client = TestClient(app)
    term = _term("retrievaleval")
    document, _chunks = _create_chunked_document(client, term)
    dataset = EvalDataset(
        name="retrieval_mode_unit",
        description=None,
        default_k=5,
        cases=[
            EvalCase(
                case_id="mode",
                question=term,
                expected_terms=[term],
                expected_answer_terms=[],
                expected_document_filename=str(document["original_filename"]),
            )
        ],
    )

    with SessionLocal() as db:
        report = run_retrieval_eval(db, dataset, mode="like")

    assert report.summary.retrieval_mode == "like"
    assert report.summary.retrieval_backend == "like"
    assert report.summary.hits == 1


def test_eval_runner_comparison_report_data_structure() -> None:
    client = TestClient(app)
    term = _term("retrievalcompare")
    document, _chunks = _create_chunked_document(client, term)
    dataset = EvalDataset(
        name="retrieval_compare_unit",
        description=None,
        default_k=5,
        cases=[
            EvalCase(
                case_id="compare",
                question=term,
                expected_terms=[term],
                expected_answer_terms=[],
                expected_document_filename=str(document["original_filename"]),
            )
        ],
    )

    with SessionLocal() as db:
        report = run_retrieval_eval_comparison(db, dataset)

    mode_results = {mode_result.mode: mode_result for mode_result in report.modes}
    assert set(mode_results) == {"like", "fts5", "auto"}
    assert report.dataset_name == "retrieval_compare_unit"
    assert report.total_cases == 1
    assert mode_results["like"].available is True
    assert mode_results["like"].backend == "like"
    assert mode_results["like"].report is not None
    assert mode_results["like"].report.summary.hits == 1
    assert mode_results["auto"].available is True
    assert mode_results["auto"].report is not None

    if report.fts5_available:
        assert mode_results["fts5"].available is True
        assert mode_results["fts5"].backend == "fts5"
        assert mode_results["fts5"].report is not None
    else:
        assert mode_results["fts5"].available is False
        assert mode_results["fts5"].error

    formatted = format_comparison_report(report)
    assert "Mode summary:" in formatted
    assert "Per-question summary:" in formatted
    assert "like:" in formatted
    assert "auto:" in formatted


def test_eval_runner_comparison_marks_fts5_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_backend_status(_db, mode="auto") -> RetrievalBackendStatus:
        return RetrievalBackendStatus(
            fts5_available=False,
            default_mode="auto",
            active_mode="like",
        )

    monkeypatch.setattr(eval_runner, "get_retrieval_backend_status", fake_backend_status)
    dataset = EvalDataset(name="unavailable_compare", description=None, default_k=1, cases=[])

    with SessionLocal() as db:
        report = run_retrieval_eval_comparison(db, dataset)

    mode_results = {mode_result.mode: mode_result for mode_result in report.modes}
    assert report.fts5_available is False
    assert mode_results["like"].available is True
    assert mode_results["auto"].available is True
    assert mode_results["fts5"].available is False
    assert mode_results["fts5"].report is None
    assert "FTS5 is not available" in str(mode_results["fts5"].error)


def test_eval_runner_fts5_mode_fails_clearly_when_unavailable() -> None:
    with SessionLocal() as db:
        available = is_fts5_available(db)
        dataset = EvalDataset(name="empty", description=None, default_k=1, cases=[])
        if available:
            report = run_retrieval_eval(db, dataset, mode="fts5")
            assert report.summary.retrieval_backend == "fts5"
            return

        with pytest.raises(RetrievalBackendUnavailableError, match="FTS5 is not available"):
            run_retrieval_eval(db, dataset, mode="fts5")


def test_zero_budget_forbidden_dependencies_and_config_are_not_required() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    api_root = repo_root / "apps" / "api"
    checked_files = [
        api_root / "pyproject.toml",
        api_root / "app" / "config.py",
        api_root / "paperlens_api.egg-info" / "requires.txt",
        api_root / "paperlens_api.egg-info" / "PKG-INFO",
    ]
    forbidden = [
        "openai",
        "anthropic",
        "cohere",
        "gemini",
        "mistral",
        "pinecone",
        "weaviate",
        "qdrant-client",
        "chromadb",
        "torch",
        "transformers",
        "sentence-transformers",
        "huggingface_hub",
        "langchain",
        "llama-index",
        "llama_index",
    ]

    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in checked_files if path.exists()
    ).casefold()
    for term in forbidden:
        assert term.casefold() not in combined
