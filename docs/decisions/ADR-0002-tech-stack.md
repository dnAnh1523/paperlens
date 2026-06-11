# ADR-0002: Initial technology stack

## Status

Accepted

## Decision

PaperLens starts with:

- FastAPI backend
- Next.js frontend
- SQLite metadata store for local development
- Local folder storage for documents and extracted assets
- Qdrant Client local mode for vector experiments
- GitHub Actions for CI

## Notes

The original Docker-first stack was replaced because it caused disk pressure on Windows 11 development machines. Production services can be introduced later behind interfaces.
