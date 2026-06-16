from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chunk import (
    ChunkSearchResponseRead,
    ChunkSearchResultRead,
    DocumentChunkRead,
    RetrievalStatusRead,
    SearchDocumentRead,
)
from app.services.retrieval_service import (
    RetrievalBackendUnavailableError,
    RetrievalMode,
    get_retrieval_backend_status,
    search_chunks,
)

router = APIRouter(tags=["search"])


@router.get("/search/status", response_model=RetrievalStatusRead)
def read_retrieval_status(
    mode: RetrievalMode = Query(default=RetrievalMode.AUTO),
    db: Session = Depends(get_db),
) -> RetrievalStatusRead:
    backend_status = get_retrieval_backend_status(db, mode=mode)
    return RetrievalStatusRead(**backend_status.__dict__)


@router.get("/search", response_model=ChunkSearchResponseRead)
def search_documents(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    mode: RetrievalMode = Query(default=RetrievalMode.AUTO),
    db: Session = Depends(get_db),
) -> ChunkSearchResponseRead:
    try:
        results = search_chunks(db, query=query, limit=limit, mode=mode)
    except RetrievalBackendUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    backend = results[0].backend if results else get_retrieval_backend_status(db, mode=mode).active_mode
    return ChunkSearchResponseRead(
        query=query,
        total=len(results),
        mode=mode.value,
        backend=backend,
        results=[
            ChunkSearchResultRead(
                rank=result.rank,
                score=result.score,
                chunk=DocumentChunkRead.model_validate(result.chunk),
                document=SearchDocumentRead(
                    id=result.document.id,
                    title=result.document.title,
                    original_filename=result.document.original_filename,
                    content_type=result.document.content_type,
                    status=result.document.status,
                ),
            )
            for result in results
        ],
    )
