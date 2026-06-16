# ADR-0008: Use Fake/Hash Embeddings Only as an Architecture Placeholder

## Status

Accepted

## Context

PaperLens will eventually need semantic retrieval experiments, but the default local workflow cannot
require paid embedding APIs, large local model downloads, Hugging Face dependencies, vector databases,
or model-serving infrastructure. The backend still benefits from proving that chunk embedding rows,
provider abstractions, and re-indexing flows can exist without changing lexical retrieval behavior.

## Decision

PaperLens will include a deterministic local fake/hash embedding provider only for architecture and
test scaffolding:

- The provider returns stable vectors for the same input text.
- Vectors are stored in SQLite for chunk/provider/model indexing tests.
- Fake/hash embeddings are not used for search ranking or chat evidence ranking.
- No real embedding model, paid API, model download, vector database, or semantic retrieval is part of
  the default M1-M18 system. Future optional providers may use local open-source models or
  zero-cost/free-tier APIs behind the same interface.

## Consequences

Positive:

- The embedding interface and storage lifecycle can be tested early.
- Re-indexing and duplicate-prevention behavior can be exercised without external dependencies.
- The zero-budget constraint stays intact.

Negative:

- Fake/hash vectors have no meaningful semantic quality.
- Any evaluation result from LIKE/FTS5/AUTO remains lexical.
- Future real embeddings must be introduced behind the provider interface, disabled by default,
  graceful when unavailable, and evaluated separately.
