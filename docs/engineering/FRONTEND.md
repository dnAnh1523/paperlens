# Frontend Design

PaperLens uses Next.js for the local development web interface. The frontend should remain thin: it presents document/library/chat workflows and calls the FastAPI backend for all persistent state.

## Milestone 2 UI

The document library page performs four integration tasks:

- checks API health via `GET /health`;
- lists documents via `GET /documents`;
- uploads a file with `POST /documents`;
- deletes a document with `DELETE /documents/{document_id}`.

## Milestone 6 Chat UI

The home page now includes an evidence chat workspace alongside the document library. The chat UI performs these integration tasks:

- lists conversations with `GET /conversations`;
- creates a conversation with `POST /conversations`;
- deletes a conversation with `DELETE /conversations/{conversation_id}`;
- reads message history with `GET /conversations/{conversation_id}/messages`;
- posts a question with `POST /conversations/{conversation_id}/messages`;
- renders assistant evidence rows returned by the backend.

The frontend does not call an LLM. Assistant content and evidence snippets are the deterministic backend evidence preview from the local FastAPI API.

## Milestone 7 Local Workflow UI

The document library now supports the full local happy path from the browser:

- loads ingestion status with `GET /documents/{document_id}/ingestion`;
- retries ingestion with `POST /documents/{document_id}/ingestion`;
- shows extracted text preview from `GET /documents/{document_id}/ingestion/text-preview`;
- runs chunking with `POST /documents/{document_id}/chunks`;
- shows chunk readiness with `GET /documents/{document_id}/chunks`;
- prepares a document by running ingestion and chunking in sequence from the UI.

This keeps the backend endpoints explicit while removing the need for manual curl commands during normal local testing.

## Configuration

The frontend reads `NEXT_PUBLIC_API_BASE_URL` when provided. If absent, it defaults to `http://127.0.0.1:8000`.

For Windows 11 local-native development, set npm cache outside the C drive when installing dependencies:

```powershell
$env:NPM_CONFIG_CACHE="F:\paperlens-npm-cache"; npm install
```

## Current limitations

- No authentication.
- Ingestion and chunking still run synchronously through API requests.
- No source preview or PDF page viewer yet.
