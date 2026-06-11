from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    estimated_token_count: int
    created_at: datetime


class SearchDocumentRead(BaseModel):
    id: str
    title: str
    original_filename: str
    content_type: str
    status: DocumentStatus


class ChunkSearchResultRead(BaseModel):
    rank: int
    score: float
    chunk: DocumentChunkRead
    document: SearchDocumentRead


class ChunkSearchResponseRead(BaseModel):
    query: str
    total: int
    results: list[ChunkSearchResultRead]
