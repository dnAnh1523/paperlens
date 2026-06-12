# ADR-0007: Use SQLite FTS5 Before Hosted or Vector Retrieval

## Status

Accepted

## Context

PaperLens needs default retrieval behavior that can be developed, tested, and evaluated without paid
services, hosted vector databases, model downloads, or cloud accounts. The project also needs a
baseline that is simple enough to understand before adding optional embeddings or multimodal retrieval.

SQLite is already used for local metadata. Many local SQLite builds include FTS5, while some do not.

## Decision

PaperLens will use local lexical retrieval first:

- `like`: deterministic SQLite `LIKE` fallback.
- `fts5`: SQLite FTS5 when the local SQLite build supports it.
- `auto`: FTS5 when available, otherwise LIKE.

Hosted vector databases, cloud search services, real embeddings, rerankers, and semantic retrieval
remain future optional adapter work. Zero-cost/free-tier or local open-source options are preferred,
and any adapter must be disabled by default and fail gracefully when unavailable.

## Consequences

Positive:

- Default retrieval works without Docker, network services, API keys, model downloads, or hosted databases.
- LIKE provides a reliable fallback when FTS5 is unavailable.
- FTS5 gives a stronger local lexical baseline for benchmark comparison.
- The benchmark harness can compare modes reproducibly on local state.

Negative:

- FTS5 remains lexical, not semantic.
- Results can vary with local SQLite FTS5 availability and ranking behavior.
- Synthetic benchmark wins for FTS5 are local evidence, not universal proof.
- The architecture still needs future optional embedding/vector work before answering semantic
  retrieval research questions.
