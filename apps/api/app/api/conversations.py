from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.generation.answer_service import UnsupportedAnswerProviderError
from app.models.conversation import Conversation, Message, MessageEvidence
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.chat import (
    ChatTurnRead,
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    EvidenceSourceChunkRead,
    EvidenceSourceDocumentRead,
    MessageCreate,
    MessageEvidenceRead,
    MessageEvidenceSourceRead,
    MessageRead,
    MessageUpdate,
)
from app.services.chunking_service import get_document_chunk_context
from app.services.chat_service import (
    DEFAULT_EVIDENCE_LIMIT,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_message_evidence,
    list_conversations,
    list_messages,
    post_user_message,
    regenerate_user_message,
)
from app.services.document_service import get_document

STALE_EVIDENCE_NOTE = (
    "This chunk was regenerated or deleted. Showing the evidence snapshot captured when the "
    "answer was created."
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _document_source_read(document: Document | None, evidence: MessageEvidence) -> EvidenceSourceDocumentRead:
    return EvidenceSourceDocumentRead(
        id=evidence.document_id,
        title=(
            document.title
            if document is not None
            else evidence.document_title_snapshot or evidence.document_id
        ),
        original_filename=(
            document.original_filename
            if document is not None
            else evidence.document_filename_snapshot or "Unknown document"
        ),
    )


def _document_snapshot_read(evidence: MessageEvidence) -> EvidenceSourceDocumentRead:
    return EvidenceSourceDocumentRead(
        id=evidence.document_id,
        title=evidence.document_title_snapshot or evidence.document_id,
        original_filename=evidence.document_filename_snapshot or "Unknown document",
    )


def _live_chunk_source_read(chunk: DocumentChunk) -> EvidenceSourceChunkRead:
    return EvidenceSourceChunkRead(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        page_number=chunk.page_number,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        estimated_token_count=chunk.estimated_token_count,
    )


def _snapshot_chunk_source_read(evidence: MessageEvidence) -> EvidenceSourceChunkRead:
    return EvidenceSourceChunkRead(
        chunk_id=evidence.chunk_id,
        document_id=evidence.document_id,
        chunk_index=evidence.chunk_index_snapshot,
        text=evidence.full_chunk_text_snapshot or evidence.excerpt,
        char_start=evidence.char_start_snapshot,
        char_end=evidence.char_end_snapshot,
        page_number=evidence.page_number,
        page_start=evidence.page_start,
        page_end=evidence.page_end,
        estimated_token_count=evidence.estimated_token_count_snapshot,
    )


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_chat_conversation(
    payload: ConversationCreate | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Conversation:
    try:
        return create_conversation(
            db,
            title=payload.title if payload else None,
            scoped_document_id=payload.scoped_document_id if payload else None,
            source_document_ids=payload.source_document_ids if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_chat_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
) -> Conversation:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if payload.title is not None:
        conversation.title = payload.title.strip()
    if payload.source_document_ids is not None:
        conversation.source_document_ids = payload.source_document_ids

    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("", response_model=list[ConversationRead])
def read_conversations(db: Session = Depends(get_db)) -> list[Conversation]:
    return list_conversations(db)


@router.get("/{conversation_id}", response_model=ConversationRead)
def read_conversation(conversation_id: str, db: Session = Depends(get_db)) -> Conversation:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_conversation(conversation_id: str, db: Session = Depends(get_db)) -> None:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    delete_conversation(db, conversation)


@router.post("/{conversation_id}/messages", response_model=ChatTurnRead)
def create_conversation_message(
    conversation_id: str,
    payload: MessageCreate,
    limit: int = Query(default=DEFAULT_EVIDENCE_LIMIT, ge=0, le=20),
    db: Session = Depends(get_db),
) -> ChatTurnRead:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    try:
        turn = post_user_message(
            db,
            conversation=conversation,
            content=payload.content,
            evidence_limit=limit,
        )
    except UnsupportedAnswerProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return ChatTurnRead(
        user_message=MessageRead.model_validate(turn.user_message),
        assistant_message=MessageRead.model_validate(turn.assistant_message),
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def read_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> list[Message]:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return list_messages(db, conversation_id)


@router.patch("/{conversation_id}/messages/{message_id}", response_model=ChatTurnRead)
def update_conversation_user_message(
    conversation_id: str,
    message_id: str,
    payload: MessageUpdate,
    limit: int = Query(default=DEFAULT_EVIDENCE_LIMIT, ge=0, le=20),
    db: Session = Depends(get_db),
) -> ChatTurnRead:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    try:
        turn = regenerate_user_message(
            db,
            conversation=conversation,
            message_id=message_id,
            content=payload.content,
            evidence_limit=limit,
        )
    except UnsupportedAnswerProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if turn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User message not found")

    return ChatTurnRead(
        user_message=MessageRead.model_validate(turn.user_message),
        assistant_message=MessageRead.model_validate(turn.assistant_message),
    )


@router.get(
    "/{conversation_id}/messages/{message_id}/evidence/{evidence_id}/source",
    response_model=MessageEvidenceSourceRead,
)
def read_message_evidence_source(
    conversation_id: str,
    message_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
) -> MessageEvidenceSourceRead:
    evidence = get_message_evidence(
        db,
        conversation_id=conversation_id,
        message_id=message_id,
        evidence_id=evidence_id,
    )
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    document = get_document(db, evidence.document_id)
    context = get_document_chunk_context(
        db,
        document_id=evidence.document_id,
        chunk_id=evidence.chunk_id,
        before=1,
        after=1,
    )
    if context is not None and document is not None:
        return MessageEvidenceSourceRead(
            source_status="live",
            is_stale=False,
            note=None,
            evidence=MessageEvidenceRead.model_validate(evidence),
            document=_document_source_read(document, evidence),
            selected_chunk=_live_chunk_source_read(context.selected_chunk),
            previous_chunks=[_live_chunk_source_read(chunk) for chunk in context.previous_chunks],
            next_chunks=[_live_chunk_source_read(chunk) for chunk in context.next_chunks],
        )

    return MessageEvidenceSourceRead(
        source_status="snapshot",
        is_stale=True,
        note=STALE_EVIDENCE_NOTE,
        evidence=MessageEvidenceRead.model_validate(evidence),
        document=_document_snapshot_read(evidence),
        selected_chunk=_snapshot_chunk_source_read(evidence),
        previous_chunks=[],
        next_chunks=[],
    )
