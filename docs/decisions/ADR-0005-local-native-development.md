# ADR-0005: Use local-native development instead of Docker by default

## Status

Accepted

## Context

The initial Docker-based scaffold required multiple large images and caused disk pressure on Windows 11 machines where Docker Desktop stores WSL2 data on the C drive by default.

## Decision

PaperLens will use local-native development by default:

- FastAPI runs directly in a Python virtual environment.
- Next.js runs directly with Node/npm.
- SQLite stores local metadata.
- Local folders store documents and extracted assets.
- Qdrant Client local mode is used for vector search experiments.

Docker may return later as an optional deployment artifact.

## Consequences

Positive:

- Lower disk usage.
- Easier debugging in VS Code.
- Fewer network-heavy image pulls.
- Better fit for Windows 11 development on a non-C drive.

Negative:

- Less environment parity with production.
- More responsibility for local Python/Node setup.
- Some services must be replaced with lightweight local alternatives during early development.
