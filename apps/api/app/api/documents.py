from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.ingestion_job import IngestionJob
from app.schemas.chunk import (
    ChunkContextDocumentRead,
    DocumentChunkContextRead,
    DocumentChunkRead,
)
from app.schemas.document import (
    DocumentDetailRead,
    DocumentRead,
    IngestionJobRead,
    IngestionTextPreviewRead,
)
from app.services.document_service import (
    create_document_from_upload,
    delete_document,
    get_document,
    list_documents,
)
from app.services.chunking_service import (
    MissingExtractedTextError,
    chunk_document,
    get_document_chunk_context,
    get_document_chunk,
    list_document_chunks,
)
from app.services.ingestion_service import (
    get_latest_ingestion_job,
    get_text_preview,
    run_ingestion,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    try:
        return create_document_from_upload(db, file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentRead])
def read_documents(db: Session = Depends(get_db)) -> list[Document]:
    return list_documents(db)


@router.get("/{document_id}", response_model=DocumentDetailRead)
def read_document(document_id: str, db: Session = Depends(get_db)) -> Document:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/{document_id}/chunks", response_model=list[DocumentChunkRead])
def create_document_chunks(document_id: str, db: Session = Depends(get_db)) -> list[DocumentChunk]:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        return chunk_document(db, document)
    except MissingExtractedTextError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
def read_document_chunks(
    document_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[DocumentChunk]:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return list_document_chunks(db, document_id=document_id, offset=offset, limit=limit)


@router.get("/{document_id}/chunks/{chunk_id}/context", response_model=DocumentChunkContextRead)
def read_document_chunk_context(
    document_id: str,
    chunk_id: str,
    before: int = Query(default=1, ge=0, le=5),
    after: int = Query(default=1, ge=0, le=5),
    db: Session = Depends(get_db),
) -> DocumentChunkContextRead:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    context = get_document_chunk_context(
        db,
        document_id=document_id,
        chunk_id=chunk_id,
        before=before,
        after=after,
    )
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

    return DocumentChunkContextRead(
        document=ChunkContextDocumentRead.model_validate(document),
        selected_chunk=DocumentChunkRead.model_validate(context.selected_chunk),
        previous_chunks=[
            DocumentChunkRead.model_validate(chunk) for chunk in context.previous_chunks
        ],
        next_chunks=[DocumentChunkRead.model_validate(chunk) for chunk in context.next_chunks],
    )


@router.get("/{document_id}/chunks/{chunk_id}", response_model=DocumentChunkRead)
def read_document_chunk(
    document_id: str,
    chunk_id: str,
    db: Session = Depends(get_db),
) -> DocumentChunk:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunk = get_document_chunk(db, document_id=document_id, chunk_id=chunk_id)
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return chunk


@router.get("/{document_id}/ingestion", response_model=IngestionJobRead)
def read_document_ingestion(document_id: str, db: Session = Depends(get_db)) -> IngestionJob:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    job = get_latest_ingestion_job(db, document_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    return job


@router.post("/{document_id}/ingestion", response_model=IngestionJobRead)
def retry_document_ingestion(document_id: str, db: Session = Depends(get_db)) -> IngestionJob:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return run_ingestion(db, document)


@router.get("/{document_id}/ingestion/text-preview", response_model=IngestionTextPreviewRead)
def read_document_text_preview(
    document_id: str,
    max_chars: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
) -> IngestionTextPreviewRead:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    preview = get_text_preview(document_id, max_chars=max_chars)
    if preview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extracted text artifact not found",
        )
    text, total_characters = preview
    return IngestionTextPreviewRead(
        document_id=document_id,
        text=text,
        total_characters=total_characters,
        preview_characters=len(text),
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(document_id: str, db: Session = Depends(get_db)) -> None:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    delete_document(db, document)
