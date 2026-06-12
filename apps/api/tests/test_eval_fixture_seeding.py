from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.evaluation.fixture_seeder import seed_eval_fixture
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.services.retrieval_service import search_chunks


def _write_fixture(tmp_path: Path, unique_term: str) -> Path:
    fixture_path = tmp_path / f"{unique_term}.txt"
    fixture_path.write_text(
        "\n\n".join(
            [
                "PaperLens fixture seeding creates a local document record.",
                (
                    f"The deterministic seed term is {unique_term}. "
                    "The fixture is ingested, chunked, and available to lexical retrieval."
                ),
                "This test fixture uses SQLite metadata and local storage only.",
            ]
        ),
        encoding="utf-8",
    )
    return fixture_path


def _unique_term(prefix: str) -> str:
    return f"{prefix}{uuid4().hex}"


def _documents_for_filename(filename: str) -> list[Document]:
    with SessionLocal() as db:
        return list(
            db.scalars(select(Document).where(Document.original_filename == filename)).all()
        )


def test_seed_eval_fixture_creates_ingests_chunks_and_is_searchable(tmp_path: Path) -> None:
    unique_term = _unique_term("seedcreate")
    fixture_path = _write_fixture(tmp_path, unique_term)

    with SessionLocal() as db:
        result = seed_eval_fixture(db, fixture_path, reset=True)
        document = db.get(Document, result.document_id)
        chunks = list(
            db.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == result.document_id)
            ).all()
        )
        search_results = search_chunks(db, unique_term, limit=5, mode="like")

    assert result.created is True
    assert result.reset is True
    assert result.ingestion_status == "completed"
    assert result.chunk_count >= 1
    assert document is not None
    assert document.status == DocumentStatus.READY
    assert document.original_filename == fixture_path.name
    assert chunks
    assert any(match.document.id == result.document_id for match in search_results)


def test_seed_eval_fixture_reuses_existing_document_without_reset(tmp_path: Path) -> None:
    unique_term = _unique_term("seedreuse")
    fixture_path = _write_fixture(tmp_path, unique_term)

    with SessionLocal() as db:
        first = seed_eval_fixture(db, fixture_path, reset=True)
        second = seed_eval_fixture(db, fixture_path)
        chunk_count = len(
            db.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == second.document_id)
            ).all()
        )

    matching_documents = _documents_for_filename(fixture_path.name)

    assert second.created is False
    assert second.reset is False
    assert second.document_id == first.document_id
    assert second.chunk_count == chunk_count
    assert len(matching_documents) == 1


def test_seed_eval_fixture_reset_replaces_matching_document(tmp_path: Path) -> None:
    unique_term = _unique_term("seedreset")
    fixture_path = _write_fixture(tmp_path, unique_term)

    with SessionLocal() as db:
        first = seed_eval_fixture(db, fixture_path, reset=True)
        fixture_path.write_text(
            f"Updated fixture text for the same filename with term {_unique_term('seedresetnew')}.",
            encoding="utf-8",
        )
        second = seed_eval_fixture(db, fixture_path, reset=True)

    matching_documents = _documents_for_filename(fixture_path.name)

    assert first.document_id != second.document_id
    assert second.created is True
    assert second.reset is True
    assert len(matching_documents) == 1
    assert matching_documents[0].id == second.document_id
