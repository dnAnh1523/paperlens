# Retrieval

PaperLens Milestone 4 adds local chunk storage and lexical retrieval without embeddings, vector databases, LLM calls, Docker, or cloud services.

## Chunking

Chunks are created explicitly:

```http
POST /documents/{document_id}/chunks
```

The service reads:

```text
data/storage/artifacts/documents/{document_id}/extracted_text.txt
```

It stores chunk rows in SQLite table `document_chunks` and writes a local artifact:

```text
data/storage/artifacts/documents/{document_id}/chunks.json
```

## Chunking policy

- Target size: about 1500 characters.
- Overlap: about 200 characters.
- Paragraph breaks are preferred when they are near the target size.
- Sentence, newline, and space boundaries are used as fallbacks.
- Empty chunks are skipped.
- `char_start` and `char_end` refer to offsets in the extracted text artifact.
- For PDFs with page artifacts, chunks are created page by page and include `page_number`,
  `page_start`, `page_end`, `source_kind`, and `source_path`.
- Text and Markdown chunks keep `page_number`, `page_start`, and `page_end` as `null`.
- `estimated_token_count` is a simple character-based estimate.

This policy is deterministic and designed for local testing, not final retrieval quality.

## Search

Search is exposed at:

```http
GET /search?query=...&limit=10&mode=auto
```

Milestone 14 supports three local retrieval modes:

- `auto`: use SQLite FTS5 when available, otherwise fall back to LIKE.
- `like`: force the original SQLite `LIKE`-based lexical search.
- `fts5`: force SQLite FTS5 and return a clear error if the local SQLite build does not support it.

Status is exposed at:

```http
GET /search/status?mode=auto
```

The LIKE fallback tokenizes the query, filters chunks containing at least one query term, scores matches
by term frequency with a small phrase-match bonus, and returns ranked chunks with document metadata.
The FTS5 path stores chunk text in a local SQLite virtual table and ranks matches with SQLite `bm25()`
plus a small lexical count score. Milestone 11 adds nullable page metadata to returned chunks when
available.

Chunking, re-chunking, and document deletion keep FTS rows aligned when FTS5 is available. Search can
also backfill the FTS table from existing chunks after a local upgrade. If FTS5 is unavailable, the app
continues to run with the LIKE fallback.

Retrieval evaluation can compare modes on the same dataset:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/sample_retrieval_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes
```

The comparison reports `hit@k`, MRR, no-result query count, active backend, and per-question HIT/MISS
status for LIKE, FTS5 when available, and AUTO. The seed command stores, ingests, and chunks the
committed sample fixture against local SQLite/storage state without requiring the FastAPI server.
The committed sample uses explicit anchor terms and should be read as a smoke test for retrieval
plumbing, not as a benchmark showing one retrieval mode is better than another.

## Embedding Index Scaffolding

Milestone 13 adds embedding provider and storage scaffolding without changing retrieval ranking. The
default provider is `local-hash` / `fake-hash-v1`, a deterministic local fake provider that turns text
into small normalized hash vectors. It is useful for testing indexing and storage paths, not semantic
quality.

Embedding rows are stored in SQLite table `chunk_embeddings` and can be built explicitly:

```http
POST /documents/{document_id}/embeddings?dimension=64
```

Status can be checked with:

```http
GET /documents/{document_id}/embeddings/status?dimension=64
```

Re-indexing removes existing rows for the same document/provider/model and recreates them from the
current chunks. Re-running chunking also clears stale embedding rows for that document. Fake/hash
embeddings are not used by the LIKE or FTS5 retrieval modes yet.

## Chat evidence

Milestone 5 reuses the same local lexical search service for chat. When a user posts a message, the
backend searches chunks with the default `auto` mode, stores the retrieved chunk metadata as
`message_evidence`, and returns a deterministic assistant message. Evidence rows keep `document_id`,
`chunk_id`, rank, score, and an excerpt snapshot so chat history remains understandable even if chunks
are later regenerated. Milestone 11 also stores `page_number`, `page_start`, and `page_end` on evidence
rows when the retrieved chunk has page metadata. Milestone 12 expands the answer-time snapshot to
include full chunk text, document title/filename, chunk index, character offsets, page offsets, and
estimated token count.

## Source context preview

Milestone 8 adds a read-only source context endpoint:

```http
GET /documents/{document_id}/chunks/{chunk_id}/context?before=1&after=1
```

The response includes document metadata, the selected chunk, previous chunks, and next chunks. Chunk
objects include page metadata when available. This lets
the frontend show exact chunk text and nearby context behind a chat evidence card without adding
embeddings, vector search, or LLM calls.

Milestone 12 adds a chat evidence source endpoint:

```http
GET /conversations/{conversation_id}/messages/{message_id}/evidence/{evidence_id}/source
```

This endpoint prefers live chunk context when the stored `chunk_id` still exists. If chunking has been
re-run or the document has been deleted, it returns `source_status: "snapshot"`, `is_stale: true`, and
the stored evidence snapshot instead of failing the evidence preview.

## Browser usage

Milestone 7 makes chunking available from the document library UI. Users can upload a text or Markdown file, prepare it from the browser, then ask chat questions that match the resulting chunks. No manual curl command is required for the normal local evidence-preview loop.

Milestone 8 lets users open an evidence card in chat to inspect the selected chunk and neighboring
chunks from the source document.
Milestone 11 adds page labels to those evidence and source-context views when chunks came from PDF page
artifacts.
Milestone 12 keeps old evidence cards expandable after chunks are regenerated by showing a marked
snapshot fallback when live context is no longer available.

## Limitations

- No real semantic embeddings or vector search yet.
- Stored fake/hash embeddings are not used for ranking yet.
- No semantic reranking yet.
- No citation assembly beyond chunk metadata.
- Chat responses are deterministic evidence previews, not generated answers.
- No evidence-type-specific retrieval beyond text chunks.
- Source preview is chunk-text context only, not a rendered PDF/page viewer.
- FTS5 availability depends on the local SQLite build; LIKE remains the reliable fallback.
