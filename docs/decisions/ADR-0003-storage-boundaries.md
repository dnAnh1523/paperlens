# ADR-0003: Storage Boundaries

## Status

Accepted

## Decision

Use PostgreSQL for canonical metadata, Qdrant for vectors, and MinIO/S3 for large binary artifacts.

## Consequences

- Large images and PDFs are not stored in PostgreSQL.
- Qdrant is treated as an index, not the source of truth.
- Metadata consistency must be maintained during indexing and deletion.
