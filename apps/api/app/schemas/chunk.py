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
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_kind: str | None = None
    source_path: str | None = None
    estimated_token_count: int
    created_at: datetime


class ChunkContextDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentChunkContextRead(BaseModel):
    document: ChunkContextDocumentRead
    selected_chunk: DocumentChunkRead
    previous_chunks: list[DocumentChunkRead]
    next_chunks: list[DocumentChunkRead]


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
    mode: str = "auto"
    backend: str = "like"
    results: list[ChunkSearchResultRead]


class RetrievalStatusRead(BaseModel):
    fts5_available: bool
    default_mode: str
    active_mode: str
