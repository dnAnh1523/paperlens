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

After the file is stored, the API runs the synchronous ingestion foundation. Text and Markdown uploads normally return with document status `ready`. Upload-accepted formats without an extractor return with document status `failed` and an ingestion job error.

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

### Trigger or re-run chunking

```http
POST /documents/{document_id}/chunks
```

Reads `data/storage/artifacts/documents/{document_id}/extracted_text.txt`, replaces existing chunks for the document, stores new rows in SQLite, writes `chunks.json`, and returns the chunks.

### List chunks

```http
GET /documents/{document_id}/chunks?offset=0&limit=20
```

Returns chunks ordered by `chunk_index`. `limit` must be between 1 and 100.

### Get one chunk

```http
GET /documents/{document_id}/chunks/{chunk_id}
```

Returns one chunk for the document.

### Get chunk source context

```http
GET /documents/{document_id}/chunks/{chunk_id}/context?before=1&after=1
```

Returns document metadata, the selected chunk, previous chunks, and next chunks ordered by
`chunk_index`. `before` and `after` must be between 0 and 5.

### Delete document

```http
DELETE /documents/{document_id}
```

Deletes document metadata, the local stored file directory, and derived artifact directory.

## Search

### Search chunks

```http
GET /search?query=local%20retrieval&limit=10
```

Runs local lexical search across stored chunks and returns ranked matches with chunk text and document metadata. `limit` must be between 1 and 50.

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

Stores the user message, searches local chunks, stores a deterministic assistant message, and stores evidence rows for retrieved chunks. `limit` must be between 0 and 20.

### List messages

```http
GET /conversations/{conversation_id}/messages
```

Returns conversation messages ordered by creation time. Assistant messages include linked evidence rows.
