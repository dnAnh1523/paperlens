import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.models.document import Document


@dataclass(frozen=True)
class PageExtraction:
    page_number: int
    text: str


class ExtractionError(Exception):
    """Raised when an extractor supports a document but cannot extract it."""

    def __init__(
        self,
        message: str,
        *,
        metadata: dict[str, Any] | None = None,
        page_texts: list[PageExtraction] | None = None,
    ) -> None:
        super().__init__(message)
        self.metadata = metadata or {}
        self.page_texts = page_texts or []


class UnsupportedExtractionError(ExtractionError):
    """Raised when no extractor exists for the uploaded document type."""


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    extractor_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    page_texts: list[PageExtraction] = field(default_factory=list)


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


def _normalize_extracted_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    normalized_lines: list[str] = []
    blank_count = 0

    for raw_line in normalized.split("\n"):
        line = re.sub(r"[ \t]{3,}", "  ", raw_line.strip())
        if not line:
            blank_count += 1
            if blank_count <= 1:
                normalized_lines.append("")
            continue

        blank_count = 0
        normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


class PlainTextExtractor:
    name = "plain-text"

    def can_extract(self, document: Document) -> bool:
        return document.content_type == "text/plain" or _document_suffix(document) == ".txt"

    def extract(self, document: Document) -> ExtractionResult:
        path = Path(document.storage_path)
        return ExtractionResult(
            text=_normalize_extracted_text(_read_utf8_text(path)),
            extractor_name=self.name,
            metadata={
                "extraction_method": "utf-8-text",
                "warnings": [],
            },
        )


class MarkdownExtractor:
    name = "markdown"

    def can_extract(self, document: Document) -> bool:
        suffix = _document_suffix(document)
        return document.content_type == "text/markdown" or suffix in {".md", ".markdown"}

    def extract(self, document: Document) -> ExtractionResult:
        path = Path(document.storage_path)
        return ExtractionResult(
            text=_normalize_extracted_text(_read_utf8_text(path)),
            extractor_name=self.name,
            metadata={
                "extraction_method": "utf-8-markdown",
                "warnings": [],
            },
        )


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
                page_count = pdf.page_count
                page_texts = [
                    PageExtraction(
                        page_number=page_index + 1,
                        text=_normalize_extracted_text(page.get_text("text")),
                    )
                    for page_index, page in enumerate(pdf)
                ]
        except Exception as exc:
            raise ExtractionError(f"PDF text extraction failed: {exc}") from exc

        pages_with_text = [page.page_number for page in page_texts if page.text.strip()]
        pages_without_text = [page.page_number for page in page_texts if not page.text.strip()]
        warnings: list[str] = []
        if pages_without_text:
            warnings.append(
                "Some PDF pages have no extractable text layer. OCR is not implemented yet."
            )

        metadata: dict[str, Any] = {
            "extractor": self.name,
            "page_count": page_count,
            "extracted_page_count": len(pages_with_text),
            "pages_with_text": pages_with_text,
            "pages_without_text": pages_without_text,
            "extraction_method": "pymupdf.get_text(text)",
            "warnings": warnings,
        }

        if not pages_with_text:
            no_text_warning = (
                "No extractable PDF text layer was found. Scanned PDFs require OCR, "
                "which is future work."
            )
            metadata["warnings"] = [*warnings, no_text_warning]
            raise ExtractionError(no_text_warning, metadata=metadata, page_texts=page_texts)

        full_text_parts = [
            f"--- Page {page.page_number} ---\n{page.text}"
            for page in page_texts
            if page.text.strip()
        ]
        return ExtractionResult(
            text="\n\n".join(full_text_parts).strip(),
            extractor_name=self.name,
            metadata=metadata,
            page_texts=page_texts,
        )


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
