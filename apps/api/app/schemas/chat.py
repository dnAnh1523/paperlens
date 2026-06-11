from datetime import datetime

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


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime
    evidence: list[MessageEvidenceRead] = Field(default_factory=list)


class ChatTurnRead(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead
