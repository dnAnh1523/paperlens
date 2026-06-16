# ADR-0002: Initial Technology Stack

## Status

Accepted, amended by Milestone 14 for zero-budget-first defaults.

## Decision

PaperLens starts with:

- FastAPI backend
- Next.js frontend
- SQLite metadata store for local development
- Local folder storage for documents and extracted assets
- SQLite LIKE/FTS5 lexical retrieval for local development
- Deterministic fake/hash embeddings for indexing scaffolding
- GitHub Actions for CI

## Notes

The original Docker-first and vector-service-looking stack was replaced because it caused disk pressure
and budget risk for Windows 11 development machines. Production services can be introduced later behind
optional interfaces.
