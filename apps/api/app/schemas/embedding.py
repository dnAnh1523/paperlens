from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChunkEmbeddingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_embedding_id: str
    chunk_id: str
    document_id: str
    provider: str
    model: str
    dimension: int
    created_at: datetime


class DocumentEmbeddingStatusRead(BaseModel):
    document_id: str
    provider: str
    model: str
    dimension: int
    chunk_count: int
    embedding_count: int
    is_indexed: bool
    latest_created_at: datetime | None = None
