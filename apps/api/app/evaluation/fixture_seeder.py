from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.ingestion_job import IngestionJobStatus
from app.services.chunking_service import chunk_document
from app.services.document_service import (
    _sha256_file,
    create_document_from_local_path,
    delete_document,
)
from app.services.ingestion_service import run_ingestion


class EvalFixtureSeedError(RuntimeError):
    """Raised when a local evaluation fixture cannot be prepared."""


@dataclass(frozen=True)
class SeededEvalFixture:
    document_id: str
    original_filename: str
    storage_path: str
    created: bool
    reset: bool
    ingestion_status: str
    chunk_count: int


def _matching_documents(
    db: Session,
    fixture_path: Path,
    *,
    include_stale_filename_matches: bool = False,
) -> list[Document]:
    fixture_hash = _sha256_file(fixture_path)
    criteria = (
        or_(Document.sha256 == fixture_hash, Document.original_filename == fixture_path.name)
        if include_stale_filename_matches
        else (Document.sha256 == fixture_hash)
    )
    statement = (
        select(Document)
        .where(
            criteria,
            Document.original_filename == fixture_path.name,
        )
        .order_by(Document.created_at.asc())
    )
    return list(db.scalars(statement).all())


def seed_eval_fixture(
    db: Session,
    fixture_path: Path,
    *,
    reset: bool = False,
) -> SeededEvalFixture:
    path = fixture_path.resolve()
    if not path.exists() or not path.is_file():
        raise EvalFixtureSeedError(f"Fixture file not found: {path}")

    if reset:
        existing_documents = _matching_documents(
            db,
            path,
            include_stale_filename_matches=True,
        )
        for document in existing_documents:
            delete_document(db, document)
        existing_documents = []
    else:
        existing_documents = _matching_documents(db, path)

    if existing_documents:
        document = existing_documents[0]
        created = False
    else:
        document = create_document_from_local_path(db, path)
        created = True

    ingestion_job = run_ingestion(db, document)
    db.refresh(document)
    if ingestion_job.status != IngestionJobStatus.COMPLETED:
        message = ingestion_job.error_message or "Ingestion did not complete."
        raise EvalFixtureSeedError(f"Failed to ingest {path.name}: {message}")

    chunks = chunk_document(db, document)
    db.refresh(document)

    return SeededEvalFixture(
        document_id=document.id,
        original_filename=document.original_filename,
        storage_path=document.storage_path,
        created=created,
        reset=reset,
        ingestion_status=ingestion_job.status.value,
        chunk_count=len(chunks),
    )
