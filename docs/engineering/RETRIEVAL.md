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
- `estimated_token_count` is a simple character-based estimate.

This policy is deterministic and designed for local testing, not final retrieval quality.

## Search

Search is exposed at:

```http
GET /search?query=...&limit=10
```

Milestone 4 uses a SQLite `LIKE`-based lexical fallback instead of FTS5. This keeps setup reliable across local Windows 11 SQLite builds and avoids extra migration complexity. The search service tokenizes the query, filters chunks containing at least one query term, scores matches by term frequency with a small phrase-match bonus, and returns ranked chunks with document metadata.

## Chat evidence

Milestone 5 reuses the same lexical search service for chat. When a user posts a message, the backend searches chunks with the message content, stores the retrieved chunk metadata as `message_evidence`, and returns a deterministic assistant message. Evidence rows keep `document_id`, `chunk_id`, rank, score, and an excerpt snapshot so chat history remains understandable even if chunks are later regenerated.

## Browser usage

Milestone 7 makes chunking available from the document library UI. Users can upload a text or Markdown file, prepare it from the browser, then ask chat questions that match the resulting chunks. No manual curl command is required for the normal local evidence-preview loop.

## Limitations

- No embeddings or vector search yet.
- No semantic reranking yet.
- No citation assembly beyond chunk metadata.
- Chat responses are deterministic evidence previews, not generated answers.
- No evidence-type-specific retrieval beyond text chunks.
- LIKE-based search is acceptable for small local corpora but should be replaced or complemented by FTS5 and embeddings later.
