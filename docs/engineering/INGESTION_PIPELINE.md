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
    chunks.json
```

`extracted_text.txt` contains UTF-8 text. `metadata.json` records the extractor name, source path, content type, character count, and extraction timestamp.
`chunks.json` is written after explicit chunking and mirrors the SQLite chunk rows for local inspection.

## Chunking behavior

Chunking is explicit in Milestone 4. Successful ingestion creates extracted text, but it does not automatically create chunks. Run:

```http
POST /documents/{document_id}/chunks
```

The chunking service reads `extracted_text.txt`, deletes old chunks for that document, writes fresh `document_chunks` rows, and writes `chunks.json`.
Retrying ingestion invalidates existing chunks because the extracted text may have changed.

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
- PDF extraction is text-layer only; scanned PDFs need OCR later.
- Chunking is character-based and paragraph-aware; it is not semantic chunking.
- No page rendering, table extraction, figure extraction, equation parsing, embeddings, or vector indexing is implemented yet.
- No Celery, Redis, Docker, MinIO, Qdrant server, or cloud service is required for this milestone.
