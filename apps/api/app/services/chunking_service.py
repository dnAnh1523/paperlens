import re
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ingestion.artifacts import read_extracted_text, write_chunks_artifact
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

TARGET_CHARS = 1500
OVERLAP_CHARS = 200


class ChunkingError(Exception):
    """Raised when extracted text cannot be chunked."""


class MissingExtractedTextError(ChunkingError):
    """Raised when the ingestion text artifact is missing."""


@dataclass(frozen=True)
class ChunkCandidate:
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    estimated_token_count: int


def estimate_token_count(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _trim_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _choose_chunk_end(text: str, start: int, target_end: int) -> int:
    if target_end >= len(text):
        return len(text)

    min_end = start + max(TARGET_CHARS // 2, 1)
    paragraph_match_end = -1
    for match in re.finditer(r"\n\s*\n", text[start:target_end]):
        absolute_end = start + match.end()
        if absolute_end >= min_end:
            paragraph_match_end = absolute_end

    if paragraph_match_end >= min_end:
        return paragraph_match_end

    for delimiter in (". ", "\n", " "):
        delimiter_index = text.rfind(delimiter, min_end, target_end)
        if delimiter_index >= min_end:
            return delimiter_index + len(delimiter)

    return target_end


def split_text_into_chunks(
    text: str,
    target_chars: int = TARGET_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
) -> list[ChunkCandidate]:
    if not text.strip():
        return []

    chunks: list[ChunkCandidate] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        target_end = min(start + target_chars, text_length)
        end = _choose_chunk_end(text, start, target_end)
        chunk_start, chunk_end = _trim_bounds(text, start, end)

        if chunk_start < chunk_end:
            chunk_text = text[chunk_start:chunk_end]
            chunks.append(
                ChunkCandidate(
                    chunk_index=len(chunks),
                    text=chunk_text,
                    char_start=chunk_start,
                    char_end=chunk_end,
                    estimated_token_count=estimate_token_count(chunk_text),
                )
            )

        if end >= text_length:
            break

        next_start = max(end - overlap_chars, start + 1)
        start = min(next_start, text_length)

    return chunks


def delete_chunks_for_document(db: Session, document_id: str) -> None:
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    db.commit()


def chunk_document(db: Session, document: Document) -> list[DocumentChunk]:
    extracted_text = read_extracted_text(document.id)
    if extracted_text is None:
        raise MissingExtractedTextError("Extracted text artifact not found. Run ingestion first.")

    candidates = split_text_into_chunks(extracted_text)
    delete_chunks_for_document(db, document.id)

    chunks = [
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=document.id,
            chunk_index=candidate.chunk_index,
            text=candidate.text,
            char_start=candidate.char_start,
            char_end=candidate.char_end,
            estimated_token_count=candidate.estimated_token_count,
        )
        for candidate in candidates
    ]
    db.add_all(chunks)
    db.commit()

    for chunk in chunks:
        db.refresh(chunk)

    write_chunks_artifact(
        document.id,
        [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "estimated_token_count": chunk.estimated_token_count,
                "created_at": chunk.created_at.isoformat(),
            }
            for chunk in chunks
        ],
    )
    return chunks


def list_document_chunks(db: Session, document_id: str, offset: int, limit: int) -> list[DocumentChunk]:
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_document_chunk(db: Session, document_id: str, chunk_id: str) -> DocumentChunk | None:
    statement = select(DocumentChunk).where(
        DocumentChunk.document_id == document_id,
        DocumentChunk.chunk_id == chunk_id,
    )
    return db.scalars(statement).first()
