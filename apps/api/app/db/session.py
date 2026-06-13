from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base
import app.models  # noqa: F401


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_sqlite_columns(table_name: str, columns: dict[str, str]) -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        table_info = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        if not table_info:
            return
        existing_columns = {row[1] for row in table_info}
        for column_name, column_definition in columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
                )


def init_db() -> None:
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns(
        "document_chunks",
        {
            "page_number": "INTEGER",
            "page_start": "INTEGER",
            "page_end": "INTEGER",
            "source_kind": "VARCHAR(32)",
            "source_path": "TEXT",
        },
    )
    _ensure_sqlite_columns(
        "message_evidence",
        {
            "full_chunk_text_snapshot": "TEXT",
            "document_title_snapshot": "VARCHAR(512)",
            "document_filename_snapshot": "VARCHAR(512)",
            "chunk_index_snapshot": "INTEGER",
            "char_start_snapshot": "INTEGER",
            "char_end_snapshot": "INTEGER",
            "page_number": "INTEGER",
            "page_start": "INTEGER",
            "page_end": "INTEGER",
            "estimated_token_count_snapshot": "INTEGER",
        },
    )
    _ensure_sqlite_columns(
        "messages",
        {
            "answer_provider_name": "VARCHAR(64)",
            "answer_provider_type": "VARCHAR(64)",
            "answer_model_name": "VARCHAR(256)",
            "answer_fallback_used": "BOOLEAN",
            "answer_fallback_reason": "TEXT",
        },
    )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
