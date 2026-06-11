from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.ingestion_job import IngestionJob
from app.services.ingestion_service import run_ingestion


class IngestionPipeline:
    """Synchronous ingestion entry point that can later be moved behind a worker."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, document: Document) -> IngestionJob:
        return run_ingestion(self.db, document)
