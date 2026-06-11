import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation, Message, MessageEvidence, MessageRole
from app.services.retrieval_service import ChunkSearchResult, search_chunks

DEFAULT_CONVERSATION_TITLE = "New conversation"
DEFAULT_EVIDENCE_LIMIT = 5
MAX_EXCERPT_CHARS = 600


@dataclass(frozen=True)
class ChatTurn:
    user_message: Message
    assistant_message: Message


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conversation_title_from_question(question: str) -> str:
    normalized = re.sub(r"\s+", " ", question).strip()
    if not normalized:
        return DEFAULT_CONVERSATION_TITLE
    return normalized[:60]


def _excerpt(text: str, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


def create_conversation(db: Session, title: str | None = None) -> Conversation:
    cleaned_title = title.strip() if title else DEFAULT_CONVERSATION_TITLE
    conversation = Conversation(conversation_id=str(uuid4()), title=cleaned_title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session) -> list[Conversation]:
    statement = select(Conversation).order_by(Conversation.updated_at.desc())
    return list(db.scalars(statement).all())


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def delete_conversation(db: Session, conversation: Conversation) -> None:
    db.delete(conversation)
    db.commit()


def list_messages(db: Session, conversation_id: str) -> list[Message]:
    statement = (
        select(Message)
        .options(selectinload(Message.evidence))
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.message_id.asc())
    )
    return list(db.scalars(statement).all())


def _build_assistant_content(question: str, results: list[ChunkSearchResult]) -> str:
    if not results:
        return (
            "Evidence preview: no relevant evidence was found for this question.\n\n"
            "PaperLens has stored your question, but the local lexical search did not match any "
            "indexed chunks. Try chunking ingested documents first or use terms that appear in the "
            "uploaded sources."
        )

    lines = [
        "Evidence preview: this deterministic draft is grounded only in retrieved local chunks.",
        "",
        f"Question: {question.strip()}",
        "",
        "Retrieved evidence:",
    ]
    for result in results:
        lines.append(
            f"{result.rank}. {result.document.title} "
            f"(document_id={result.document.id}, chunk_id={result.chunk.chunk_id}, "
            f"chunk_index={result.chunk.chunk_index}, score={result.score:g})"
        )
        lines.append(f"   {_excerpt(result.chunk.text, max_chars=260)}")
    lines.append("")
    lines.append("No external LLM was called for this response.")
    return "\n".join(lines)


def _create_evidence_rows(
    assistant_message: Message,
    results: list[ChunkSearchResult],
) -> list[MessageEvidence]:
    return [
        MessageEvidence(
            evidence_id=str(uuid4()),
            message_id=assistant_message.message_id,
            document_id=result.document.id,
            chunk_id=result.chunk.chunk_id,
            rank=result.rank,
            score=result.score,
            excerpt=_excerpt(result.chunk.text),
        )
        for result in results
    ]


def post_user_message(
    db: Session,
    conversation: Conversation,
    content: str,
    evidence_limit: int = DEFAULT_EVIDENCE_LIMIT,
) -> ChatTurn:
    question = content.strip()
    results = search_chunks(db, query=question, limit=evidence_limit)
    timestamp = _now()
    assistant_timestamp = timestamp + timedelta(microseconds=1)

    if conversation.title == DEFAULT_CONVERSATION_TITLE:
        conversation.title = _conversation_title_from_question(question)
    conversation.updated_at = assistant_timestamp

    user_message = Message(
        message_id=str(uuid4()),
        conversation_id=conversation.conversation_id,
        role=MessageRole.USER,
        content=question,
        created_at=timestamp,
    )
    assistant_message = Message(
        message_id=str(uuid4()),
        conversation_id=conversation.conversation_id,
        role=MessageRole.ASSISTANT,
        content=_build_assistant_content(question, results),
        created_at=assistant_timestamp,
    )
    evidence_rows = _create_evidence_rows(assistant_message, results)

    db.add_all([conversation, user_message, assistant_message, *evidence_rows])
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    assistant_message.evidence = evidence_rows
    return ChatTurn(user_message=user_message, assistant_message=assistant_message)
