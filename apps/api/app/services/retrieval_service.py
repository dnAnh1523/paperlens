import re
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class RetrievalMode(StrEnum):
    AUTO = "auto"
    LIKE = "like"
    FTS5 = "fts5"


class RetrievalBackendUnavailableError(Exception):
    """Raised when an explicitly requested retrieval backend is unavailable."""


DEFAULT_RETRIEVAL_MODE = RetrievalMode.AUTO
FTS_TABLE_NAME = "document_chunk_fts"


@dataclass(frozen=True)
class ChunkSearchResult:
    rank: int
    score: float
    chunk: DocumentChunk
    document: Document
    backend: str = RetrievalMode.LIKE.value


@dataclass(frozen=True)
class RetrievalBackendStatus:
    fts5_available: bool
    default_mode: str
    active_mode: str


def tokenize_query(query: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", query) if token.strip()]


def _score_chunk(text: str, terms: list[str], query: str) -> float:
    lowered_text = text.lower()
    score = sum(lowered_text.count(term) for term in terms)
    phrase = query.strip().lower()
    if phrase and len(phrase.split()) > 1:
        score += lowered_text.count(phrase) * 2
    return float(score)


def normalize_retrieval_mode(mode: str | RetrievalMode | None) -> RetrievalMode:
    if mode is None:
        return DEFAULT_RETRIEVAL_MODE
    if isinstance(mode, RetrievalMode):
        return mode
    try:
        return RetrievalMode(mode.lower())
    except ValueError as exc:
        raise ValueError("Retrieval mode must be one of: auto, like, fts5.") from exc


def is_fts5_available(db: Session) -> bool:
    try:
        db.execute(text("CREATE VIRTUAL TABLE temp.paperlens_fts5_probe USING fts5(content)"))
        db.execute(text("DROP TABLE temp.paperlens_fts5_probe"))
        return True
    except DatabaseError:
        db.rollback()
        return False


def ensure_fts_index(db: Session) -> bool:
    if not is_fts5_available(db):
        return False
    db.execute(
        text(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE_NAME}
            USING fts5(chunk_id UNINDEXED, document_id UNINDEXED, text)
            """
        )
    )
    db.commit()
    return True


def rebuild_fts_index(db: Session) -> bool:
    if not ensure_fts_index(db):
        return False
    db.execute(text(f"DELETE FROM {FTS_TABLE_NAME}"))
    chunks = list(
        db.scalars(
            select(DocumentChunk).order_by(
                DocumentChunk.document_id.asc(),
                DocumentChunk.chunk_index.asc(),
            )
        ).all()
    )
    for chunk in chunks:
        db.execute(
            text(
                f"""
                INSERT INTO {FTS_TABLE_NAME} (chunk_id, document_id, text)
                VALUES (:chunk_id, :document_id, :chunk_text)
                """
            ),
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_text": chunk.text,
            },
        )
    db.commit()
    return True


def ensure_fts_index_current(db: Session) -> bool:
    if not ensure_fts_index(db):
        return False
    chunk_count = int(db.scalar(select(func.count()).select_from(DocumentChunk)) or 0)
    fts_count = int(db.scalar(text(f"SELECT count(*) FROM {FTS_TABLE_NAME}")) or 0)
    if fts_count != chunk_count:
        return rebuild_fts_index(db)
    return True


def get_retrieval_backend_status(
    db: Session,
    mode: str | RetrievalMode | None = None,
) -> RetrievalBackendStatus:
    requested_mode = normalize_retrieval_mode(mode)
    fts5_available = is_fts5_available(db)
    active_mode = (
        RetrievalMode.FTS5
        if requested_mode == RetrievalMode.FTS5
        or (requested_mode == RetrievalMode.AUTO and fts5_available)
        else RetrievalMode.LIKE
    )
    return RetrievalBackendStatus(
        fts5_available=fts5_available,
        default_mode=DEFAULT_RETRIEVAL_MODE.value,
        active_mode=active_mode.value,
    )


def delete_fts_rows_for_document(db: Session, document_id: str) -> None:
    if not ensure_fts_index(db):
        return
    db.execute(
        text(f"DELETE FROM {FTS_TABLE_NAME} WHERE document_id = :document_id"),
        {"document_id": document_id},
    )
    db.commit()


def index_document_chunks_fts(db: Session, document_id: str) -> None:
    if not ensure_fts_index(db):
        return
    db.execute(
        text(f"DELETE FROM {FTS_TABLE_NAME} WHERE document_id = :document_id"),
        {"document_id": document_id},
    )
    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        ).all()
    )
    for chunk in chunks:
        db.execute(
            text(
                f"""
                INSERT INTO {FTS_TABLE_NAME} (chunk_id, document_id, text)
                VALUES (:chunk_id, :document_id, :chunk_text)
                """
            ),
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_text": chunk.text,
            },
        )
    db.commit()


def _search_chunks_like(
    db: Session,
    query: str,
    limit: int,
    backend: str = RetrievalMode.LIKE.value,
) -> list[ChunkSearchResult]:
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
        ChunkSearchResult(
            rank=index + 1,
            score=score,
            chunk=chunk,
            document=document,
            backend=backend,
        )
        for index, (score, chunk, document) in enumerate(scored[:limit])
    ]


def _fts_query_from_terms(terms: list[str]) -> str:
    return " OR ".join(f'"{term}"' for term in terms)


def _search_chunks_fts5(db: Session, query: str, limit: int) -> list[ChunkSearchResult]:
    terms = tokenize_query(query)
    if not terms:
        return []
    if not ensure_fts_index_current(db):
        raise RetrievalBackendUnavailableError("SQLite FTS5 is not available in this environment.")

    fts_query = _fts_query_from_terms(terms)
    rows = db.execute(
        text(
            f"""
            SELECT chunk_id, bm25({FTS_TABLE_NAME}) AS distance
            FROM {FTS_TABLE_NAME}
            WHERE {FTS_TABLE_NAME} MATCH :query
            ORDER BY distance ASC
            LIMIT :limit
            """
        ),
        {"query": fts_query, "limit": limit},
    ).all()

    if not rows:
        return []

    distance_by_chunk_id = {row.chunk_id: float(row.distance) for row in rows}
    order_by_chunk_id = {row.chunk_id: index for index, row in enumerate(rows)}
    statement = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.chunk_id.in_(distance_by_chunk_id))
    )
    chunk_rows = db.execute(statement).all()
    chunk_rows.sort(key=lambda row: order_by_chunk_id[row[0].chunk_id])

    results: list[ChunkSearchResult] = []
    for index, (chunk, document) in enumerate(chunk_rows, start=1):
        distance = distance_by_chunk_id[chunk.chunk_id]
        lexical_score = _score_chunk(chunk.text, terms, query)
        score = max(lexical_score, 0.0) + (1.0 / (1.0 + max(distance, 0.0)))
        results.append(
            ChunkSearchResult(
                rank=index,
                score=score,
                chunk=chunk,
                document=document,
                backend=RetrievalMode.FTS5.value,
            )
        )
    return results


def search_chunks(
    db: Session,
    query: str,
    limit: int,
    mode: str | RetrievalMode | None = None,
) -> list[ChunkSearchResult]:
    requested_mode = normalize_retrieval_mode(mode)
    if requested_mode == RetrievalMode.LIKE:
        return _search_chunks_like(db, query=query, limit=limit)
    if requested_mode == RetrievalMode.FTS5:
        return _search_chunks_fts5(db, query=query, limit=limit)

    if is_fts5_available(db):
        try:
            return _search_chunks_fts5(db, query=query, limit=limit)
        except RetrievalBackendUnavailableError:
            return _search_chunks_like(
                db,
                query=query,
                limit=limit,
                backend=RetrievalMode.LIKE.value,
            )
    return _search_chunks_like(db, query=query, limit=limit, backend=RetrievalMode.LIKE.value)
