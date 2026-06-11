from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatTurnRead, ConversationCreate, ConversationRead, MessageCreate, MessageRead
from app.services.chat_service import (
    DEFAULT_EVIDENCE_LIMIT,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
    post_user_message,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_chat_conversation(
    payload: ConversationCreate | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Conversation:
    return create_conversation(db, title=payload.title if payload else None)


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

    turn = post_user_message(
        db,
        conversation=conversation,
        content=payload.content,
        evidence_limit=limit,
    )
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
