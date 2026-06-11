from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.models.document import Document


class ExtractionError(Exception):
    """Raised when an extractor supports a document but cannot extract it."""


class UnsupportedExtractionError(ExtractionError):
    """Raised when no extractor exists for the uploaded document type."""


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    extractor_name: str


class TextExtractor(Protocol):
    name: str

    def can_extract(self, document: Document) -> bool:
        ...

    def extract(self, document: Document) -> ExtractionResult:
        ...


def _document_suffix(document: Document) -> str:
    return Path(document.original_filename or document.storage_path).suffix.lower()


def _read_utf8_text(path: Path) -> str:
    content = path.read_bytes()
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("utf-8", errors="replace")


class PlainTextExtractor:
    name = "plain-text"

    def can_extract(self, document: Document) -> bool:
        return document.content_type == "text/plain" or _document_suffix(document) == ".txt"

    def extract(self, document: Document) -> ExtractionResult:
        path = Path(document.storage_path)
        return ExtractionResult(text=_read_utf8_text(path), extractor_name=self.name)


class MarkdownExtractor:
    name = "markdown"

    def can_extract(self, document: Document) -> bool:
        suffix = _document_suffix(document)
        return document.content_type == "text/markdown" or suffix in {".md", ".markdown"}

    def extract(self, document: Document) -> ExtractionResult:
        path = Path(document.storage_path)
        return ExtractionResult(text=_read_utf8_text(path), extractor_name=self.name)


class PdfTextExtractor:
    name = "pdf-text"

    def can_extract(self, document: Document) -> bool:
        return document.content_type == "application/pdf" or _document_suffix(document) == ".pdf"

    def extract(self, document: Document) -> ExtractionResult:
        try:
            import fitz
        except ImportError as exc:
            raise UnsupportedExtractionError("PDF extraction requires PyMuPDF.") from exc

        path = Path(document.storage_path)
        try:
            with fitz.open(path) as pdf:
                pages = [page.get_text("text") for page in pdf]
        except Exception as exc:
            raise ExtractionError(f"PDF text extraction failed: {exc}") from exc

        return ExtractionResult(text="\n".join(pages).strip(), extractor_name=self.name)


EXTRACTORS: tuple[TextExtractor, ...] = (
    PlainTextExtractor(),
    MarkdownExtractor(),
    PdfTextExtractor(),
)


def extract_text(document: Document) -> ExtractionResult:
    path = Path(document.storage_path)
    if not path.exists():
        raise ExtractionError("Stored source file was not found.")

    for extractor in EXTRACTORS:
        if extractor.can_extract(document):
            return extractor.extract(document)

    raise UnsupportedExtractionError(
        f"No text extractor is available for {document.content_type} files."
    )
