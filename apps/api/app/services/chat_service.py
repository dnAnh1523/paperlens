import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.generation.answer_service import (
    AnswerProvider,
    AnswerRequest,
    EvidenceInput,
    excerpt_text,
    get_answer_provider,
)
from app.models.conversation import Conversation, Message, MessageEvidence, MessageRole
from app.services.retrieval_service import ChunkSearchResult, search_chunks

DEFAULT_CONVERSATION_TITLE = "New conversation"
DEFAULT_EVIDENCE_LIMIT = 5


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


def get_message_evidence(
    db: Session,
    conversation_id: str,
    message_id: str,
    evidence_id: str,
) -> MessageEvidence | None:
    statement = (
        select(MessageEvidence)
        .join(Message, Message.message_id == MessageEvidence.message_id)
        .where(
            Message.conversation_id == conversation_id,
            Message.message_id == message_id,
            MessageEvidence.evidence_id == evidence_id,
        )
    )
    return db.scalars(statement).first()


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


def _evidence_input_from_search_result(result: ChunkSearchResult) -> EvidenceInput:
    return EvidenceInput(
        rank=result.rank,
        score=result.score,
        document_id=result.document.id,
        document_title=result.document.title,
        document_filename=result.document.original_filename,
        chunk_id=result.chunk.chunk_id,
        chunk_index=result.chunk.chunk_index,
        text=result.chunk.text,
        page_number=result.chunk.page_number,
    )


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
            excerpt=excerpt_text(result.chunk.text),
            full_chunk_text_snapshot=result.chunk.text,
            document_title_snapshot=result.document.title,
            document_filename_snapshot=result.document.original_filename,
            chunk_index_snapshot=result.chunk.chunk_index,
            char_start_snapshot=result.chunk.char_start,
            char_end_snapshot=result.chunk.char_end,
            page_number=result.chunk.page_number,
            page_start=result.chunk.page_start,
            page_end=result.chunk.page_end,
            estimated_token_count_snapshot=result.chunk.estimated_token_count,
        )
        for result in results
    ]


def post_user_message(
    db: Session,
    conversation: Conversation,
    content: str,
    evidence_limit: int = DEFAULT_EVIDENCE_LIMIT,
    answer_provider: AnswerProvider | None = None,
) -> ChatTurn:
    question = content.strip()
    results = search_chunks(db, query=question, limit=evidence_limit)
    provider = answer_provider or get_answer_provider()
    answer = provider.generate(
        AnswerRequest(
            question=question,
            evidence=[_evidence_input_from_search_result(result) for result in results],
        )
    )
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
        content=answer.content,
        created_at=assistant_timestamp,
    )
    evidence_rows = _create_evidence_rows(assistant_message, results)

    db.add_all([conversation, user_message, assistant_message, *evidence_rows])
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    assistant_message.evidence = evidence_rows
    return ChatTurn(user_message=user_message, assistant_message=assistant_message)
