import re
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


@dataclass(frozen=True)
class ChunkSearchResult:
    rank: int
    score: float
    chunk: DocumentChunk
    document: Document


def tokenize_query(query: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", query) if token.strip()]


def _score_chunk(text: str, terms: list[str], query: str) -> float:
    lowered_text = text.lower()
    score = sum(lowered_text.count(term) for term in terms)
    phrase = query.strip().lower()
    if phrase and len(phrase.split()) > 1:
        score += lowered_text.count(phrase) * 2
    return float(score)


def search_chunks(db: Session, query: str, limit: int) -> list[ChunkSearchResult]:
    terms = tokenize_query(query)
    if not terms:
        return []

    like_filters = [func.lower(DocumentChunk.text).like(f"%{term}%") for term in terms]
    statement = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(or_(*like_filters))
        .order_by(DocumentChunk.created_at.desc())
    )
    rows = db.execute(statement).all()

    scored: list[tuple[float, DocumentChunk, Document]] = []
    for chunk, document in rows:
        score = _score_chunk(chunk.text, terms, query)
        if score > 0:
            scored.append((score, chunk, document))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[2].title.lower(),
            item[1].chunk_index,
            item[1].chunk_id,
        )
    )
    return [
        ChunkSearchResult(rank=index + 1, score=score, chunk=chunk, document=document)
        for index, (score, chunk, document) in enumerate(scored[:limit])
    ]
