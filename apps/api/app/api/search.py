from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chunk import (
    ChunkSearchResponseRead,
    ChunkSearchResultRead,
    DocumentChunkRead,
    SearchDocumentRead,
)
from app.services.retrieval_service import search_chunks

router = APIRouter(tags=["search"])


@router.get("/search", response_model=ChunkSearchResponseRead)
def search_documents(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> ChunkSearchResponseRead:
    results = search_chunks(db, query=query, limit=limit)
    return ChunkSearchResponseRead(
        query=query,
        total=len(results),
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
