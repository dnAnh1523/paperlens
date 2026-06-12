# API

Base URL for local development:

```text
http://127.0.0.1:8000
```

## Health

```http
GET /health
```

Returns service status and local development storage configuration.

## Documents

### Upload document

```http
POST /documents
Content-Type: multipart/form-data
```

Form fields:

| Name | Type | Required |
|---|---|---|
| `file` | file | yes |

Supported content types:

- `application/pdf`
- `image/jpeg`
- `image/png`
- `image/webp`
- `text/plain`
- `text/markdown`
- `text/csv`

Current upload limit: 50 MB.

After the file is stored, the API runs the synchronous ingestion foundation. Text, Markdown, and
text-layer PDF uploads normally return with document status `ready`. Scanned PDFs without an
extractable text layer return with document status `failed` and an ingestion job error that identifies
OCR as future work. Upload-accepted formats without an extractor return with document status `failed`
and an ingestion job error.

### List documents

```http
GET /documents
```

Returns uploaded documents ordered by newest first.

### Get document detail

```http
GET /documents/{document_id}
```

Returns document metadata and associated ingestion jobs.

### Get ingestion status

```http
GET /documents/{document_id}/ingestion
```

Returns the latest ingestion job for a document.

### Trigger or retry ingestion

```http
POST /documents/{document_id}/ingestion
```

Runs ingestion synchronously for the stored source file and returns the updated ingestion job.

### Get extracted text preview

```http
GET /documents/{document_id}/ingestion/text-preview?max_chars=1000
```

Returns a preview of `data/storage/artifacts/documents/{document_id}/extracted_text.txt`.
`max_chars` must be between 1 and 10000.

For PDFs, the preview is read from the combined extracted text artifact and includes coarse page markers
such as `--- Page 1 ---` when extraction succeeds.

### Trigger or re-run chunking

```http
POST /documents/{document_id}/chunks
```

Reads `data/storage/artifacts/documents/{document_id}/extracted_text.txt`, replaces existing chunks for the document, stores new rows in SQLite, writes `chunks.json`, and returns the chunks.
For PDFs with `pages/page_*.txt` artifacts, chunks include nullable page metadata:
`page_number`, `page_start`, `page_end`, `source_kind`, and `source_path`.

### List chunks

```http
GET /documents/{document_id}/chunks?offset=0&limit=20
```

Returns chunks ordered by `chunk_index`. `limit` must be between 1 and 100.
Text and Markdown chunks return `null` page fields. PDF page-aware chunks return page metadata when
available.

### Get one chunk

```http
GET /documents/{document_id}/chunks/{chunk_id}
```

Returns one chunk for the document.
The response includes page metadata fields when available.

### Get chunk source context

```http
GET /documents/{document_id}/chunks/{chunk_id}/context?before=1&after=1
```

Returns document metadata, the selected chunk, previous chunks, and next chunks ordered by
`chunk_index`. `before` and `after` must be between 0 and 5.
Selected and neighboring chunks include page metadata when available.

### Index local chunk embeddings

```http
POST /documents/{document_id}/embeddings?dimension=64
```

Builds or rebuilds deterministic local fake embeddings for the document's current chunks. This endpoint
does not call external APIs and does not change lexical retrieval behavior. `dimension` must be between
1 and 1024 and defaults to 64.

Response:

```json
{
  "document_id": "document-uuid",
  "provider": "local-hash",
  "model": "fake-hash-v1",
  "dimension": 64,
  "chunk_count": 3,
  "embedding_count": 3,
  "is_indexed": true,
  "latest_created_at": "2026-06-11T16:00:00Z"
}
```

If the document has no chunks, the endpoint returns `409 Conflict` with a message telling the user to
run chunking first.

### Get local embedding status

```http
GET /documents/{document_id}/embeddings/status?dimension=64
```

Returns chunk count and embedding count for the local fake provider/model/dimension. `is_indexed` is
`true` only when the document has at least one chunk and each current chunk has a stored embedding row.

### Delete document

```http
DELETE /documents/{document_id}
```

Deletes document metadata, the local stored file directory, and derived artifact directory.

## Search

### Search chunks

```http
GET /search?query=local%20retrieval&limit=10&mode=auto
```

Runs local lexical search across stored chunks and returns ranked matches with chunk text, nullable page
metadata, and document metadata. `limit` must be between 1 and 50. `mode` can be `auto`, `like`, or
`fts5`.

- `auto`: use SQLite FTS5 when available and fall back to LIKE otherwise.
- `like`: force the SQLite LIKE fallback.
- `fts5`: force SQLite FTS5 and return `409 Conflict` if the local SQLite build does not support FTS5.

Response payload includes `mode` and the active `backend` used for that search.

### Get retrieval status

```http
GET /search/status?mode=auto
```

Returns whether SQLite FTS5 is available, the default retrieval mode, and the active backend that would
be used for the requested mode.

## Conversations

### Create conversation

```http
POST /conversations
Content-Type: application/json
```

Optional body:

```json
{
  "title": "My paper questions"
}
```

Creates a conversation. If no title is supplied, the title starts as `New conversation` and is updated from the first user message.

### List conversations

```http
GET /conversations
```

Returns conversations ordered by most recently updated first.

### Get conversation

```http
GET /conversations/{conversation_id}
```

Returns conversation metadata.

### Delete conversation

```http
DELETE /conversations/{conversation_id}
```

Deletes the conversation and cascades stored messages and evidence rows.

### Post user message

```http
POST /conversations/{conversation_id}/messages?limit=5
Content-Type: application/json
```

Request body:

```json
{
  "content": "What does the paper say about retrieval quality?"
}
```

Stores the user message, searches local chunks, stores a deterministic assistant message, and stores
evidence rows for retrieved chunks. Evidence rows include answer-time snapshot fields:
`excerpt`, `full_chunk_text_snapshot`, `document_title_snapshot`, `document_filename_snapshot`,
`chunk_index_snapshot`, `char_start_snapshot`, `char_end_snapshot`, `page_number`, `page_start`,
`page_end`, and `estimated_token_count_snapshot`. `limit` must be between 0 and 20.

### List messages

```http
GET /conversations/{conversation_id}/messages
```

Returns conversation messages ordered by creation time. Assistant messages include linked evidence rows
with nullable page metadata and stable evidence snapshot fields.

### Get message evidence source

```http
GET /conversations/{conversation_id}/messages/{message_id}/evidence/{evidence_id}/source
```

Returns the source context for a stored assistant evidence row. When the original chunk still exists,
the response is marked live and includes the selected chunk plus neighboring chunks:

```json
{
  "source_status": "live",
  "is_stale": false,
  "note": null,
  "evidence": {
    "evidence_id": "evidence-uuid",
    "message_id": "assistant-message-uuid",
    "document_id": "document-uuid",
    "chunk_id": "chunk-uuid",
    "rank": 1,
    "score": 3.5,
    "excerpt": "retrieved chunk text",
    "full_chunk_text_snapshot": "retrieved chunk text",
    "document_title_snapshot": "paper",
    "document_filename_snapshot": "paper.pdf",
    "chunk_index_snapshot": 2,
    "char_start_snapshot": 1200,
    "char_end_snapshot": 2400,
    "page_number": 3,
    "page_start": 10,
    "page_end": 1210,
    "estimated_token_count_snapshot": 300
  },
  "document": {
    "id": "document-uuid",
    "title": "paper",
    "original_filename": "paper.pdf"
  },
  "selected_chunk": {
    "chunk_id": "chunk-uuid",
    "document_id": "document-uuid",
    "chunk_index": 2,
    "text": "retrieved chunk text",
    "char_start": 1200,
    "char_end": 2400,
    "page_number": 3,
    "page_start": 10,
    "page_end": 1210,
    "estimated_token_count": 300
  },
  "previous_chunks": [],
  "next_chunks": []
}
```

When the chunk was regenerated or deleted, the response is marked stale and returns the stored evidence
snapshot instead of failing the preview:

```json
{
  "source_status": "snapshot",
  "is_stale": true,
  "note": "This chunk was regenerated or deleted. Showing the evidence snapshot captured when the answer was created.",
  "evidence": {
    "evidence_id": "evidence-uuid",
    "message_id": "assistant-message-uuid",
    "document_id": "document-uuid",
    "chunk_id": "old-chunk-uuid",
    "rank": 1,
    "score": 3.5,
    "excerpt": "captured excerpt",
    "full_chunk_text_snapshot": "captured full chunk text",
    "document_title_snapshot": "paper",
    "document_filename_snapshot": "paper.pdf",
    "chunk_index_snapshot": 2,
    "char_start_snapshot": 1200,
    "char_end_snapshot": 2400,
    "page_number": 3,
    "page_start": 10,
    "page_end": 1210,
    "estimated_token_count_snapshot": 300
  },
  "document": {
    "id": "document-uuid",
    "title": "paper",
    "original_filename": "paper.pdf"
  },
  "selected_chunk": {
    "chunk_id": "old-chunk-uuid",
    "document_id": "document-uuid",
    "chunk_index": 2,
    "text": "captured full chunk text",
    "char_start": 1200,
    "char_end": 2400,
    "page_number": 3,
    "page_start": 10,
    "page_end": 1210,
    "estimated_token_count": 300
  },
  "previous_chunks": [],
  "next_chunks": []
}
```
