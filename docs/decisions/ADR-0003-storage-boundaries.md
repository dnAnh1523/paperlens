# ADR-0003: Storage Boundaries

## Status

Accepted, amended by Milestone 14 for zero-budget-first local development.

## Decision

For current local development, use SQLite for metadata, SQLite lexical retrieval indexes, and local
folders for large binary artifacts. Production storage adapters can be introduced later behind optional
interfaces.

## Consequences

- Large images and PDFs are not stored in SQLite.
- SQLite FTS rows and fake embedding rows are treated as indexes, not the source of truth.
- Metadata consistency must be maintained during indexing and deletion.
