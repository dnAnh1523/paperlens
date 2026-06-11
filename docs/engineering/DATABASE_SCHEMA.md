# Database Schema

PaperLens currently uses SQLite for local-native development. This is a development-friendly metadata store, not the final production database.

## Tables

### `documents`

Stores one uploaded source file.

| Column | Type | Meaning |
|---|---|---|
| `id` | string UUID | Primary key |
| `title` | string | Display title derived from filename |
| `original_filename` | string | Filename supplied by user |
| `content_type` | string | MIME type from upload |
| `file_size_bytes` | integer | Stored file size |
| `sha256` | string | File content hash |
| `storage_path` | text | Local filesystem path for the stored file |
| `status` | enum | `pending`, `processing`, `ready`, or `failed` |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### `ingestion_jobs`

Tracks the ingestion lifecycle for a document.

| Column | Type | Meaning |
|---|---|---|
| `id` | string UUID | Primary key |
| `document_id` | string UUID | Foreign key to `documents.id` |
| `status` | enum | `pending`, `running`, `completed`, or `failed` |
| `stage` | string | Current pipeline stage, initially `queued` |
| `error_message` | text nullable | Failure detail |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `started_at` | datetime nullable | Start timestamp |
| `finished_at` | datetime nullable | End timestamp |

### `document_chunks`

Stores source-grounded text chunks derived from extracted document text.

| Column | Type | Meaning |
|---|---|---|
| `chunk_id` | string UUID | Primary key |
| `document_id` | string UUID | Foreign key to `documents.id` |
| `chunk_index` | integer | Stable order within a document |
| `text` | text | Chunk text |
| `char_start` | integer | Start offset in extracted text |
| `char_end` | integer | End offset in extracted text |
| `estimated_token_count` | integer | Character-based token estimate |
| `created_at` | datetime | Creation timestamp |

## Current migration strategy

For Milestone 1, the API calls `Base.metadata.create_all()` at startup. This is acceptable for the local-native scaffold.

Later milestones should introduce Alembic migrations before schema changes become complex.
