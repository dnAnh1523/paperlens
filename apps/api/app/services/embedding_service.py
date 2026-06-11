import json
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.embeddings.providers import EmbeddingProvider, FakeHashEmbeddingProvider
from app.models.chunk_embedding import ChunkEmbedding
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

DEFAULT_EMBEDDING_DIMENSION = 64
MAX_EMBEDDING_DIMENSION = 1024


class EmbeddingIndexError(Exception):
    """Raised when chunks cannot be embedded."""


class NoChunksForEmbeddingError(EmbeddingIndexError):
    """Raised when a document has no chunks to index."""


@dataclass(frozen=True)
class DocumentEmbeddingStatus:
    document_id: str
    provider: str
    model: str
    dimension: int
    chunk_count: int
    embedding_count: int
    is_indexed: bool
    latest_created_at: datetime | None


def create_default_embedding_provider(dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> EmbeddingProvider:
    return FakeHashEmbeddingProvider(dimension=dimension)


def serialize_vector(vector: list[float]) -> str:
    return json.dumps(vector, separators=(",", ":"))


def deserialize_vector(vector: str) -> list[float]:
    loaded = json.loads(vector)
    if not isinstance(loaded, list):
        raise ValueError("Stored embedding vector is not a JSON array.")
    return [float(value) for value in loaded]


def _document_chunks(db: Session, document_id: str) -> list[DocumentChunk]:
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(db.scalars(statement).all())


def _delete_embeddings_for_provider(
    db: Session,
    document_id: str,
    provider: EmbeddingProvider,
) -> None:
    db.execute(
        delete(ChunkEmbedding).where(
            ChunkEmbedding.document_id == document_id,
            ChunkEmbedding.provider == provider.provider_name,
            ChunkEmbedding.model == provider.model_name,
        )
    )


def index_document_embeddings(
    db: Session,
    document: Document,
    provider: EmbeddingProvider | None = None,
) -> DocumentEmbeddingStatus:
    embedding_provider = provider or create_default_embedding_provider()
    chunks = _document_chunks(db, document.id)
    if not chunks:
        raise NoChunksForEmbeddingError("No chunks found for document. Run chunking before indexing embeddings.")

    _delete_embeddings_for_provider(db, document.id, embedding_provider)
    vectors = embedding_provider.embed_texts([chunk.text for chunk in chunks])
    if len(vectors) != len(chunks):
        raise EmbeddingIndexError("Embedding provider returned a different number of vectors than input texts.")

    embeddings: list[ChunkEmbedding] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        if len(vector) != embedding_provider.dimension:
            raise EmbeddingIndexError("Embedding provider returned a vector with the wrong dimension.")
        embeddings.append(
            ChunkEmbedding(
                chunk_embedding_id=str(uuid4()),
                chunk_id=chunk.chunk_id,
                document_id=document.id,
                provider=embedding_provider.provider_name,
                model=embedding_provider.model_name,
                dimension=embedding_provider.dimension,
                vector=serialize_vector(vector),
            )
        )

    db.add_all(embeddings)
    db.commit()
    return get_document_embedding_status(db, document.id, embedding_provider)


def get_document_embedding_status(
    db: Session,
    document_id: str,
    provider: EmbeddingProvider | None = None,
) -> DocumentEmbeddingStatus:
    embedding_provider = provider or create_default_embedding_provider()
    chunk_count = db.scalar(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    embedding_count = db.scalar(
        select(func.count())
        .select_from(ChunkEmbedding)
        .where(
            ChunkEmbedding.document_id == document_id,
            ChunkEmbedding.provider == embedding_provider.provider_name,
            ChunkEmbedding.model == embedding_provider.model_name,
            ChunkEmbedding.dimension == embedding_provider.dimension,
        )
    )
    latest_created_at = db.scalar(
        select(ChunkEmbedding.created_at)
        .where(
            ChunkEmbedding.document_id == document_id,
            ChunkEmbedding.provider == embedding_provider.provider_name,
            ChunkEmbedding.model == embedding_provider.model_name,
            ChunkEmbedding.dimension == embedding_provider.dimension,
        )
        .order_by(ChunkEmbedding.created_at.desc())
        .limit(1)
    )

    safe_chunk_count = int(chunk_count or 0)
    safe_embedding_count = int(embedding_count or 0)
    return DocumentEmbeddingStatus(
        document_id=document_id,
        provider=embedding_provider.provider_name,
        model=embedding_provider.model_name,
        dimension=embedding_provider.dimension,
        chunk_count=safe_chunk_count,
        embedding_count=safe_embedding_count,
        is_indexed=safe_chunk_count > 0 and safe_embedding_count == safe_chunk_count,
        latest_created_at=latest_created_at,
    )
