# ADR-0006: Zero-Budget-First Local Default

## Status

Accepted

## Context

PaperLens is built as an applied CS thesis and production-style engineering project under a
zero-budget-first constraint. The default workflow must work on Windows 11 with VS Code and PowerShell
without requiring paid APIs, cloud accounts, hosted databases, Docker, large model downloads, or API
keys.

Earlier milestones showed that Docker-first development and cloud-looking defaults increased disk,
setup, and budget risk before the core research pipeline was stable. At the same time, PaperLens can
grow beyond the local default through optional zero-cost integrations for OCR, deployment, LLM
experiments, or semantic retrieval later.

## Decision

PaperLens will keep local-native development as the default and allow optional zero-cost adapters:

- FastAPI runs in a local Python virtual environment by default.
- Next.js runs with local Node/npm by default.
- SQLite stores local metadata and retrieval indexes by default.
- Local folders store uploaded documents, extracted text, page artifacts, chunks, and eval outputs by
  default.
- Retrieval uses SQLite LIKE and SQLite FTS5 when available by default.
- Fake/hash embeddings are allowed only as deterministic architecture scaffolding by default.
- Optional adapters may use free-tier APIs, open-source OCR such as Tesseract, local open-source
  models, free inference providers, OpenAI-compatible free-provider proxies, or free deployment tiers.
- Optional adapters must be isolated behind interfaces, disabled by default, documented clearly, and
  fail gracefully when credentials, quota, binaries, or local resources are unavailable.
- Paid services must never be mandatory for the core evidence pipeline.

## Consequences

Positive:

- The project remains reproducible on a student Windows 11 machine.
- Development avoids hidden costs and API-key blockers.
- CI and local debugging stay small enough for early thesis work.
- The architecture can later experiment with free-tier or open-source adapters without making them
  requirements.

Negative:

- Local SQLite and lexical retrieval are not production retrieval infrastructure.
- Optional adapters require extra configuration and careful failure handling.
- Some scientific-document features, especially OCR and table/figure extraction, remain deferred
  until their dependency and cost impact are understood.
