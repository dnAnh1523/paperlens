from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "paperlens-api",
        "env": settings.app_env,
        "storage": settings.local_storage_root,
        "vector_store": "qdrant-client-local-mode",
    }
