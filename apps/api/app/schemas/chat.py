from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=256)


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    message_id: str
    document_id: str
    chunk_id: str
    rank: int
    score: float
    excerpt: str
    full_chunk_text_snapshot: str | None = None
    document_title_snapshot: str | None = None
    document_filename_snapshot: str | None = None
    chunk_index_snapshot: int | None = None
    char_start_snapshot: int | None = None
    char_end_snapshot: int | None = None
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    estimated_token_count_snapshot: int | None = None


class AnswerProvenanceRead(BaseModel):
    provider_name: str
    provider_type: Literal[
        "deterministic",
        "free-tier-api",
        "local-model",
        "openai-compatible",
        "unknown",
    ]
    model_name: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime
    answer_provenance: AnswerProvenanceRead | None = None
    evidence: list[MessageEvidenceRead] = Field(default_factory=list)


class ChatTurnRead(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead


class EvidenceSourceDocumentRead(BaseModel):
    id: str
    title: str
    original_filename: str


class EvidenceSourceChunkRead(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int | None
    text: str
    char_start: int | None
    char_end: int | None
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    estimated_token_count: int | None = None


class MessageEvidenceSourceRead(BaseModel):
    source_status: Literal["live", "snapshot"]
    is_stale: bool
    note: str | None = None
    evidence: MessageEvidenceRead
    document: EvidenceSourceDocumentRead
    selected_chunk: EvidenceSourceChunkRead
    previous_chunks: list[EvidenceSourceChunkRead] = Field(default_factory=list)
    next_chunks: list[EvidenceSourceChunkRead] = Field(default_factory=list)
