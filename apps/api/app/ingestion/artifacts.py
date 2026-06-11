import json
import shutil
from pathlib import Path
from typing import Any

from app.config import settings
from app.ingestion.extractors import PageExtraction

EXTRACTED_TEXT_FILENAME = "extracted_text.txt"
METADATA_FILENAME = "metadata.json"
CHUNKS_FILENAME = "chunks.json"


def document_artifact_dir(document_id: str) -> Path:
    return settings.storage_path / "artifacts" / "documents" / document_id


def clear_document_artifacts(document_id: str) -> None:
    artifact_dir = document_artifact_dir(document_id)
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir, ignore_errors=True)


def write_extracted_text(document_id: str, text: str) -> Path:
    artifact_dir = document_artifact_dir(document_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / EXTRACTED_TEXT_FILENAME
    output_path.write_text(text, encoding="utf-8")
    return output_path


def read_extracted_text(document_id: str) -> str | None:
    text_path = document_artifact_dir(document_id) / EXTRACTED_TEXT_FILENAME
    if not text_path.exists():
        return None
    return text_path.read_text(encoding="utf-8")


def write_metadata(document_id: str, metadata: dict[str, Any]) -> Path:
    artifact_dir = document_artifact_dir(document_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / METADATA_FILENAME
    output_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def write_page_texts(document_id: str, page_texts: list[PageExtraction]) -> list[Path]:
    pages_dir = document_artifact_dir(document_id) / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[Path] = []
    for page in page_texts:
        output_path = pages_dir / f"page_{page.page_number:03d}.txt"
        output_path.write_text(page.text, encoding="utf-8")
        output_paths.append(output_path)
    return output_paths


def write_chunks_artifact(document_id: str, chunks: list[dict[str, Any]]) -> Path:
    artifact_dir = document_artifact_dir(document_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / CHUNKS_FILENAME
    output_path.write_text(json.dumps(chunks, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
