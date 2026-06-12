from fastapi import APIRouter

from app.generation.answer_service import get_answer_provider_status
from app.schemas.answer_provider import AnswerProviderStatusRead

router = APIRouter(prefix="/answer-provider", tags=["answer-provider"])


@router.get("/status", response_model=AnswerProviderStatusRead)
def read_answer_provider_status() -> AnswerProviderStatusRead:
    return AnswerProviderStatusRead.model_validate(
        get_answer_provider_status(),
        from_attributes=True,
    )
