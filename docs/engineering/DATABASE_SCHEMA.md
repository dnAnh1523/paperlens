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
| `page_number` | integer nullable | Source page number when chunked from a page artifact |
| `page_start` | integer nullable | Start offset within the source page text |
| `page_end` | integer nullable | End offset within the source page text |
| `source_kind` | string nullable | Source artifact kind, for example `page_text` or `extracted_text` |
| `source_path` | text nullable | Local source artifact path used to create the chunk |
| `estimated_token_count` | integer | Character-based token estimate |
| `created_at` | datetime | Creation timestamp |

### `chunk_embeddings`

Stores local embedding vectors for chunks. Milestone 13 uses deterministic fake/hash vectors only; the
table is scaffolding for later semantic retrieval.

| Column | Type | Meaning |
|---|---|---|
| `chunk_embedding_id` | string UUID | Primary key |
| `chunk_id` | string UUID | Foreign key to `document_chunks.chunk_id` |
| `document_id` | string UUID | Foreign key to `documents.id` |
| `provider` | string | Embedding provider name, for example `local-hash` |
| `model` | string | Embedding model name, for example `fake-hash-v1` |
| `dimension` | integer | Vector dimension |
| `vector` | text | JSON array of floats stored in SQLite |
| `created_at` | datetime | Creation timestamp |

The table has a uniqueness constraint on `chunk_id`, `provider`, and `model`. Re-indexing a document
deletes existing rows for the same provider/model and recreates them from the current chunks.

### `conversations`

Stores chat conversation metadata.

| Column | Type | Meaning |
|---|---|---|
| `conversation_id` | string UUID | Primary key |
| `title` | string | Display title |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### `messages`

Stores user and assistant messages.

| Column | Type | Meaning |
|---|---|---|
| `message_id` | string UUID | Primary key |
| `conversation_id` | string UUID | Foreign key to `conversations.conversation_id` |
| `role` | enum | `user` or `assistant` |
| `content` | text | Message body |
| `created_at` | datetime | Creation timestamp |

### `message_evidence`

Stores evidence snapshots linked to assistant messages.

| Column | Type | Meaning |
|---|---|---|
| `evidence_id` | string UUID | Primary key |
| `message_id` | string UUID | Foreign key to `messages.message_id` |
| `document_id` | string UUID | Source document identifier |
| `chunk_id` | string UUID | Source chunk identifier |
| `rank` | integer | Retrieval rank used in the assistant response |
| `score` | float | Lexical retrieval score |
| `excerpt` | text | Snapshot text stored with the message |
| `full_chunk_text_snapshot` | text nullable | Full retrieved chunk text captured when the assistant answer was created |
| `document_title_snapshot` | string nullable | Source document title captured at answer time |
| `document_filename_snapshot` | string nullable | Source document filename captured at answer time |
| `chunk_index_snapshot` | integer nullable | Source chunk index captured at answer time |
| `char_start_snapshot` | integer nullable | Source chunk start offset captured at answer time |
| `char_end_snapshot` | integer nullable | Source chunk end offset captured at answer time |
| `page_number` | integer nullable | Source page number copied from the retrieved chunk |
| `page_start` | integer nullable | Start offset within the source page text |
| `page_end` | integer nullable | End offset within the source page text |
| `estimated_token_count_snapshot` | integer nullable | Estimated token count copied from the retrieved chunk |

## Current migration strategy

The API calls `Base.metadata.create_all()` at startup. Milestone 13 adds `chunk_embeddings` through the
same local startup creation path. For Milestones 11 and 12, startup also performs a small SQLite-only
additive column check for page-aware chunk metadata and stable evidence snapshot metadata. This keeps
local Windows development moving without introducing Alembic yet.

Later milestones should introduce Alembic migrations before schema changes become complex.
