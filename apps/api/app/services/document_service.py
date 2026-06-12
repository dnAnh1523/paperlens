import hashlib
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.artifacts import clear_document_artifacts
from app.models.document import Document, DocumentStatus
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.services.ingestion_service import run_ingestion
from app.services.retrieval_service import delete_fts_rows_for_document

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
    "text/markdown",
    "text/csv",
}

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _safe_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip().replace(" ", "_")
    return cleaned or "uploaded_file"


def _document_title(filename: str) -> str:
    title = Path(filename).stem.strip()
    return title or filename


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_document_from_upload(db: Session, upload: UploadFile) -> Document:
    if not upload.filename:
        raise ValueError("Uploaded file must have a filename.")

    content_type = upload.content_type or "application/octet-stream"
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValueError(f"Unsupported file type: {content_type}")

    document_id = str(uuid4())
    safe_filename = _safe_filename(upload.filename)
    document_dir = settings.storage_path / "documents" / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    stored_file_path = document_dir / safe_filename

    total_bytes = 0
    with stored_file_path.open("wb") as output:
        while chunk := upload.file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_BYTES:
                output.close()
                stored_file_path.unlink(missing_ok=True)
                raise ValueError("Uploaded file exceeds the 50 MB limit.")
            output.write(chunk)

    sha256 = _sha256_file(stored_file_path)

    document = Document(
        id=document_id,
        title=_document_title(upload.filename),
        original_filename=upload.filename,
        content_type=content_type,
        file_size_bytes=total_bytes,
        sha256=sha256,
        storage_path=str(stored_file_path),
        status=DocumentStatus.PENDING,
    )
    job = IngestionJob(
        id=str(uuid4()),
        document_id=document_id,
        status=IngestionJobStatus.PENDING,
        stage="queued",
    )
    document.ingestion_jobs.append(job)

    db.add(document)
    db.commit()
    db.refresh(document)
    run_ingestion(db, document)
    db.refresh(document)
    return document


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())).all())


def get_document(db: Session, document_id: str) -> Document | None:
    return db.get(Document, document_id)


def delete_document(db: Session, document: Document) -> None:
    storage_path = Path(document.storage_path)
    document_dir = storage_path.parent
    document_id = document.id
    delete_fts_rows_for_document(db, document_id)
    db.delete(document)
    db.commit()
    if document_dir.exists() and document_dir.is_dir():
        shutil.rmtree(document_dir, ignore_errors=True)
    clear_document_artifacts(document_id)
