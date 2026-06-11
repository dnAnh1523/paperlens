from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus
from app.models.ingestion_job import IngestionJobStatus


class IngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    status: IngestionJobStatus
    stage: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class IngestionTextPreviewRead(BaseModel):
    document_id: str
    text: str
    total_characters: int
    preview_characters: int


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    sha256: str
    storage_path: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentDetailRead(DocumentRead):
    ingestion_jobs: list[IngestionJobRead] = []
