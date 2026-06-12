from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.answer_provider import router as answer_provider_router
from app.api.conversations import router as conversations_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.config import settings
from app.db.session import init_db


def create_app() -> FastAPI:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    app = FastAPI(
        title="PaperLens API",
        description="Backend API for evidence-type-aware multimodal RAG over scientific papers.",
        version="0.0.1",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(answer_provider_router)
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(conversations_router)
    app.include_router(search_router)
    return app


app = create_app()
