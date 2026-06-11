# Frontend Design

PaperLens uses Next.js for the local development web interface. The frontend should remain thin: it presents document/library/chat workflows and calls the FastAPI backend for all persistent state.

## Milestone 2 UI

The document library page performs four integration tasks:

- checks API health via `GET /health`;
- lists documents via `GET /documents`;
- uploads a file with `POST /documents`;
- deletes a document with `DELETE /documents/{document_id}`.

## Configuration

The frontend reads `NEXT_PUBLIC_API_BASE_URL` when provided. If absent, it defaults to `http://127.0.0.1:8000`.

For Windows 11 local-native development, set npm cache outside the C drive when installing dependencies:

```powershell
$env:NPM_CONFIG_CACHE="F:\paperlens-npm-cache"; npm install
```

## Current limitations

- No authentication.
- No real ingestion progress UI yet.
- No chat interface yet.
- No source preview or PDF page viewer yet.
