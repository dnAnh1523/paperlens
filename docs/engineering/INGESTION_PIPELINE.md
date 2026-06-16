# Ingestion Pipeline

PaperLens ingestion is local-native first. The Milestone 3 foundation runs synchronously in the FastAPI process after upload or when explicitly retried through the API. This keeps local Windows 11 development simple while leaving a clear service boundary for a later background worker.

## Current flow

1. A document is uploaded with `POST /documents`.
2. The backend stores the source file under `data/storage/documents/{document_id}/`.
3. The backend creates or reuses an ingestion job for the document.
4. The ingestion service extracts basic text.
5. Extracted artifacts are written under `data/storage/artifacts/documents/{document_id}/`.
6. SQLite metadata is updated with the ingestion status.
7. Chunking is run explicitly with `POST /documents/{document_id}/chunks`.

## Supported extraction

- `.txt` / `text/plain`
- `.md` and `.markdown` / `text/markdown`
- `.pdf` / `application/pdf` through the existing PyMuPDF dependency

Images, CSV files, and other upload-accepted formats do not have text extractors yet. They are marked as failed with a clear unsupported extractor message.

PDF extraction is text-layer only. PaperLens reads PDFs page by page with PyMuPDF, normalizes excessive
whitespace conservatively, writes per-page text artifacts, and preserves a combined `extracted_text.txt`
for chunking compatibility. Scanned PDFs without an extractable text layer are marked as failed with a
clear OCR warning. PaperLens does not fake OCR output. Future optional OCR adapters may use
open-source tools such as Tesseract if they remain optional, documented, and graceful when binaries or
local resources are unavailable.

## Job statuses

Ingestion jobs are exposed through the API with these statuses:

- `pending`
- `running`
- `completed`
- `failed`

The related document status is updated to `processing`, `ready`, or `failed`.

## Artifact layout

```text
data/storage/
  documents/{document_id}/
    uploaded-source-file
  artifacts/documents/{document_id}/
    extracted_text.txt
    metadata.json
    pages/
      page_001.txt
      page_002.txt
    chunks.json
```

`extracted_text.txt` contains UTF-8 text. `metadata.json` records the extractor name, source path, content type, character count, and extraction timestamp.
`chunks.json` is written after explicit chunking and mirrors the SQLite chunk rows for local inspection.

For PDFs, `metadata.json` also records:

- `page_count`
- `extracted_page_count`
- `pages_with_text`
- `pages_without_text`
- `extraction_method`
- `warnings`
- `page_text_paths`

The combined PDF `extracted_text.txt` includes page markers such as `--- Page 1 ---` so previews and
chunks retain coarse page boundaries. Page files are stored under `pages/page_001.txt`,
`pages/page_002.txt`, and so on.

## Chunking behavior

Chunking is explicit in Milestone 4. Successful ingestion creates extracted text, but it does not automatically create chunks. Run:

```http
POST /documents/{document_id}/chunks
```

The chunking service reads `extracted_text.txt`, deletes old chunks for that document, writes fresh `document_chunks` rows, and writes `chunks.json`.
Retrying ingestion invalidates existing chunks because the extracted text may have changed.

For PDFs with page artifacts, Milestone 11 chunks each `pages/page_*.txt` file independently. Each
chunk stores `page_number`, page-local offsets, extracted-text offsets, source artifact kind, and source
artifact path. Text and Markdown documents keep the original `extracted_text.txt` chunking path and have
null page fields.

## Browser workflow

Milestone 7 exposes ingestion and chunking controls in the document library UI. The Prepare document action runs:

1. `POST /documents/{document_id}/ingestion`
2. `POST /documents/{document_id}/chunks`

The backend endpoints remain explicit. The UI simply performs the normal local workflow in sequence and shows ingestion status, extracted text preview, and chunk count.

## Local commands

From `apps/api`:

```powershell
python -m pytest -q
```

From `apps/web`:

```powershell
npm run build
```

## Known limitations

- Ingestion is synchronous and runs inside the API request for now.
- PDF extraction is text-layer only; scanned PDFs need an optional OCR adapter later and are currently
  marked failed.
- Chunking is character-based and paragraph-aware; it is not semantic chunking.
- No page rendering, table extraction, figure extraction, equation parsing, embeddings, or vector indexing is implemented yet.
- No Celery, Redis, Docker, object-storage server, vector database server, or cloud service is required
  for this milestone's default workflow.
