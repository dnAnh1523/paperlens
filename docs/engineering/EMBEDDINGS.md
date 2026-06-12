# Embeddings

Milestone 13 adds the local embedding abstraction and SQLite storage schema needed before semantic
retrieval is introduced. It does not call model APIs, cloud APIs, paid services, vector database
servers, Docker, or an LLM.

## Provider Interface

Embedding providers expose:

- `provider_name`
- `model_name`
- `dimension`
- `embed_texts(texts: list[str]) -> list[list[float]]`

The interface lives in `apps/api/app/embeddings/providers.py`. Future real providers should implement
the same contract and can be selected by service/API wiring later.

## Local Fake Provider

The default provider is:

```text
provider: local-hash
model: fake-hash-v1
dimension: 64 by default
```

It creates deterministic SHA-256-based vectors and normalizes them. The same text, model, and dimension
produce the same vector every time. These vectors are only for exercising indexing and storage paths;
they are not semantically meaningful.

## Storage

Chunk embeddings are stored in SQLite table `chunk_embeddings`.

The vector is stored as a JSON array of floats in the `vector` text column. This keeps the local schema
simple until a real vector index is added.

Re-indexing a document deletes existing rows for the same document/provider/model and recreates them
from current chunks. Re-running chunking clears stale embedding rows for that document.

## API

Index a document's current chunks:

```powershell
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/documents/{document_id}/embeddings?dimension=64"
```

Read embedding index status:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/documents/{document_id}/embeddings/status?dimension=64"
```

If a document has no chunks, indexing returns `409 Conflict` and asks the user to run chunking first.

## Current Limitations

- Fake/hash embeddings are not used by LIKE or FTS5 search or chat ranking.
- No semantic model is bundled yet.
- No vector database or ANN index is used yet.
- No external embedding API is called.
- No model weights are downloaded.
- No migration framework is added; local SQLite uses the existing startup `create_all()` path.
