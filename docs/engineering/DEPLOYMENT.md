# Deployment

PaperLens has no production deployment target yet. The default development and evaluation workflow is
local on Windows 11 and must remain usable without Docker, cloud accounts, paid services, hosted
databases, model downloads, or API keys.

## Current Status

- Backend runs locally with FastAPI and SQLite.
- Frontend runs locally with Next.js.
- Uploaded documents, extracted artifacts, chunks, and eval outputs are stored in local folders.
- No deployment provider is required for core development or tests.

## Future Optional Deployment Experiments

Future deployment work may test zero-cost options such as:

- free cloud deployment tiers
- static frontend hosting tiers
- local tunnel demos
- free managed database tiers for demos
- optional container packaging for deployment only

Any deployment adapter must be optional, documented, disabled by default, and graceful when quota,
credentials, or hosted services are unavailable. Paid infrastructure must never be mandatory for the
core evidence pipeline.
