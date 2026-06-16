from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document import Document


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    scoped_document_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    _source_document_ids: Mapped[str | None] = mapped_column(
        "source_document_ids",
        Text,
        nullable=True,
    )

    @property
    def source_document_ids(self) -> list[str] | None:
        import json
        from typing import cast
        if self._source_document_ids is None:
            if self.scoped_document_id:
                return [self.scoped_document_id]
            return None
        try:
            return cast(list[str], json.loads(self._source_document_ids))
        except Exception:
            return []

    @source_document_ids.setter
    def source_document_ids(self, val: list[str] | None) -> None:
        import json
        if val is None:
            self._source_document_ids = None
        else:
            self._source_document_ids = json.dumps(val)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    scoped_document: Mapped["Document | None"] = relationship("Document", foreign_keys=[scoped_document_id])


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    answer_provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_provider_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_model_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    answer_fallback_used: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    answer_fallback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    evidence: Mapped[list["MessageEvidence"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )

    @property
    def answer_provenance(self) -> dict[str, object] | None:
        if self.answer_provider_name is None:
            return None
        return {
            "provider_name": self.answer_provider_name,
            "provider_type": self.answer_provider_type or "unknown",
            "model_name": self.answer_model_name,
            "fallback_used": bool(self.answer_fallback_used),
            "fallback_reason": self.answer_fallback_reason,
        }


class MessageEvidence(Base):
    __tablename__ = "message_evidence"

    evidence_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    chunk_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    full_chunk_text_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_title_snapshot: Mapped[str | None] = mapped_column(String(512), nullable=True)
    document_filename_snapshot: Mapped[str | None] = mapped_column(String(512), nullable=True)
    chunk_index_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_token_count_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    message: Mapped[Message] = relationship(back_populates="evidence")
