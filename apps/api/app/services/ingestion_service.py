from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.artifacts import (
    clear_document_artifacts,
    read_extracted_text,
    write_extracted_text,
    write_metadata,
    write_page_texts,
)
from app.ingestion.extractors import ExtractionError, UnsupportedExtractionError, extract_text
from app.models.document import Document, DocumentStatus
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.services.chunking_service import delete_chunks_for_document


def get_latest_ingestion_job(db: Session, document_id: str) -> IngestionJob | None:
    statement = (
        select(IngestionJob)
        .where(IngestionJob.document_id == document_id)
        .order_by(IngestionJob.created_at.desc())
        .limit(1)
    )
    return db.scalars(statement).first()


def ensure_ingestion_job(db: Session, document: Document) -> IngestionJob:
    job = get_latest_ingestion_job(db, document.id)
    if job is not None:
        return job

    job = IngestionJob(
        id=str(uuid4()),
        document_id=document.id,
        status=IngestionJobStatus.PENDING,
        stage="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_ingestion(db: Session, document: Document) -> IngestionJob:
    job = ensure_ingestion_job(db, document)
    started_at = datetime.now(timezone.utc)

    delete_chunks_for_document(db, document.id)
    clear_document_artifacts(document.id)
    job.status = IngestionJobStatus.RUNNING
    job.stage = "extracting"
    job.error_message = None
    job.started_at = started_at
    job.finished_at = None
    document.status = DocumentStatus.PROCESSING
    db.add_all([document, job])
    db.commit()

    try:
        result = extract_text(document)
        text_path = write_extracted_text(document.id, result.text)
        page_text_paths = (
            write_page_texts(document.id, result.page_texts) if result.page_texts else []
        )
        finished_at = datetime.now(timezone.utc)
        write_metadata(
            document.id,
            {
                "document_id": document.id,
                "source_path": document.storage_path,
                "content_type": document.content_type,
                "extractor": result.extractor_name,
                "extracted_text_path": str(text_path),
                "page_text_paths": [str(path) for path in page_text_paths],
                "character_count": len(result.text),
                "extracted_at": finished_at.isoformat(),
                **result.metadata,
            },
        )
        job.status = IngestionJobStatus.COMPLETED
        job.stage = "completed"
        job.error_message = None
        job.finished_at = finished_at
        document.status = DocumentStatus.READY
    except UnsupportedExtractionError as exc:
        job.status = IngestionJobStatus.FAILED
        job.stage = "unsupported"
        job.error_message = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        document.status = DocumentStatus.FAILED
    except ExtractionError as exc:
        page_text_paths = write_page_texts(document.id, exc.page_texts) if exc.page_texts else []
        if exc.metadata:
            finished_at = datetime.now(timezone.utc)
            write_metadata(
                document.id,
                {
                    "document_id": document.id,
                    "source_path": document.storage_path,
                    "content_type": document.content_type,
                    "extractor": exc.metadata.get("extractor", "unknown"),
                    "page_text_paths": [str(path) for path in page_text_paths],
                    "character_count": 0,
                    "extracted_at": finished_at.isoformat(),
                    "status": "failed",
                    "error_message": str(exc),
                    **exc.metadata,
                },
            )
        job.status = IngestionJobStatus.FAILED
        job.stage = "failed"
        job.error_message = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        document.status = DocumentStatus.FAILED
    except Exception as exc:
        job.status = IngestionJobStatus.FAILED
        job.stage = "failed"
        job.error_message = f"Ingestion failed: {exc}"
        job.finished_at = datetime.now(timezone.utc)
        document.status = DocumentStatus.FAILED

    db.add_all([document, job])
    db.commit()
    db.refresh(job)
    db.refresh(document)
    return job


def get_text_preview(document_id: str, max_chars: int) -> tuple[str, int] | None:
    extracted_text = read_extracted_text(document_id)
    if extracted_text is None:
        return None
    return extracted_text[:max_chars], len(extracted_text)
