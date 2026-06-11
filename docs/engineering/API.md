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

### Delete document

```http
DELETE /documents/{document_id}
```

Deletes document metadata, the local stored file directory, and derived artifact directory.
