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

### Delete document

```http
DELETE /documents/{document_id}
```

Deletes document metadata and the local stored file directory.
