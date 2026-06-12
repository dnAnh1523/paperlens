# PaperLens Project Context

## Project identity

PaperLens is an applied computer science thesis + production-style software project.

## Problem statement

Scientific and technical papers contain important evidence across text, tables, figures, charts, equations, captions, and page layout. Text-only RAG often loses important evidence when answering questions over these documents. PaperLens investigates and implements evidence-type-aware multimodal RAG for scientific papers.

## Current development environment

- OS: Windows 11
- Editor: VS Code
- Shell: PowerShell
- Command convention: every terminal command must be written as one line
- Development mode: local-native, no Docker
- Preferred project drive: non-C drive, for example `F:\paperlens`

## Current local stack

- Backend: FastAPI
- Frontend: Next.js
- Metadata storage: SQLite during local development
- File storage: local folders during local development
- Retrieval: SQLite LIKE fallback and SQLite FTS5 when available
- Embeddings: deterministic fake/hash vectors for pipeline scaffolding only
- Production target later: optional PostgreSQL + managed services behind interfaces

## Why Docker was removed from local development

Docker image pulls and WSL2 Docker storage consumed too much disk space on the Windows C drive. PaperLens will continue with local-native development first. Docker may return later only as an optional deployment artifact, not as the default development path.

## Current research questions

- RQ1: Does evidence-type-aware retrieval improve scientific-paper QA compared with text-only RAG?
- RQ2: Does sending relevant figure/table/page images to a multimodal model improve faithfulness?
- RQ3: Which evidence types cause the most failures in standard RAG?
- RQ4: Can structured table extraction plus multimodal reasoning outperform caption-only retrieval for table-heavy questions?

## Implemented so far

- Repository scaffold
- Thesis/product/engineering documentation skeleton
- FastAPI health endpoint
- Next.js landing page
- GitHub issue templates
- GitHub Actions for API, web, security, and docs
- Local-native configuration replacing Docker-first development

## Next tasks

1. Verify backend starts locally on Windows 11.
2. Verify frontend starts locally on Windows 11.
3. Create initial SQLite schema for documents, pages, assets, chunks, conversations, and citations.
4. Implement document upload endpoint.
5. Implement local file storage service.
6. Implement PDF page rendering and metadata extraction.
7. Design evaluation dataset format.

## Known risks

- Windows path differences can break scripts if not kept simple.
- Large PDF/image processing can still consume disk space.
- OCR and table extraction dependencies may be heavy; introduce them carefully.
- Multimodal API cost must be controlled with caching and small test documents.

## Milestone 1 Progress: Document Metadata and Upload Flow

Implemented in feature branch `feature/m1-backend-document-models`:

- SQLite-backed metadata initialization for local-native development.
- `documents` table for uploaded source files.
- `ingestion_jobs` table for queued ingestion work.
- Local file storage under `data/storage/documents/{document_id}/`.
- Backend endpoints:
  - `POST /documents`
  - `GET /documents`
  - `GET /documents/{document_id}`
  - `DELETE /documents/{document_id}`
- Tests for upload, list, read, and unsupported content type rejection.

Current limitation: ingestion jobs are queued metadata only. Actual PDF parsing, figure/table extraction, and vector indexing are not implemented yet.

## Milestone 2 Progress: Document Library UI

Implemented in feature branch `feature/m2-document-library-ui`:

- Next.js document library section on the home page.
- Browser-side API client for `/health` and `/documents`.
- File upload form for PDFs, text, Markdown, CSV, PNG, JPEG, and WEBP.
- Uploaded document list with file type, status, size, upload time, and SHA-256 preview.
- Document deletion from the UI.
- Manual refresh and API connectivity state.

Current limitation: the UI only manages uploaded source files. It does not yet show ingestion progress beyond the document status field, and no PDF parsing or RAG chat UI is implemented yet.

## Milestone 3 Progress: Ingestion Foundation

Implemented in feature branch `feature/m3-ingestion-foundation`:

- Synchronous backend ingestion after upload and through a retry endpoint.
- Text extraction for `.txt`, `.md`, and text-layer `.pdf` documents.
- Ingestion job status transitions: `pending`, `running`, `completed`, and `failed`.
- Local artifact storage under `data/storage/artifacts/documents/{document_id}/`.
- Backend endpoints:
  - `GET /documents/{document_id}/ingestion`
  - `POST /documents/{document_id}/ingestion`
  - `GET /documents/{document_id}/ingestion/text-preview`
- Tests for text and Markdown ingestion, unsupported extraction, ingestion status, and retry.

Current limitation: ingestion is synchronous and extracts only source text. OCR, page rendering, table/figure/equation extraction, chunking, and vector indexing are still future work.

## Milestone 4 Progress: Chunking and Retrieval Foundation

Implemented in feature branch `feature/m4-chunking-retrieval-foundation`:

- `document_chunks` SQLite table for source-grounded extracted-text chunks.
- Explicit chunking endpoint that reads extracted text artifacts and replaces stale chunks.
- Character-based, paragraph-aware chunking with overlap and source offsets.
- Local chunk artifact at `data/storage/artifacts/documents/{document_id}/chunks.json`.
- LIKE-based lexical search across stored chunks.
- Backend endpoints:
  - `POST /documents/{document_id}/chunks`
  - `GET /documents/{document_id}/chunks`
  - `GET /documents/{document_id}/chunks/{chunk_id}`
  - `GET /search?query=...`
- Tests for chunk creation, listing, single chunk retrieval, reruns, search, and missing extracted text.

Current limitation: retrieval is lexical only. No embeddings, vector database, semantic reranking, or LLM answer generation is implemented yet.

## Milestone 5 Progress: Chat Evidence API

Implemented in feature branch `feature/m5-chat-evidence-api`:

- SQLite-backed conversations, messages, and message evidence rows.
- Backend conversation endpoints for create, list, read, delete, post message, and read history.
- Deterministic assistant response template grounded in retrieved local chunks.
- Evidence snapshots linked to assistant messages with document/chunk references, rank, score, and excerpt.
- No external LLM, embedding model, vector database, queue, Docker service, or paid API call.
- Tests for conversation creation/listing, chat turns, evidence storage, no-evidence responses, message history, and cascade delete.

Current limitation: assistant responses are retrieval previews only. They do not synthesize full natural-language answers or perform semantic retrieval.

## Milestone 6 Progress: Chat UI

Implemented in feature branch `feature/m6-chat-ui`:

- Next.js evidence chat workspace on the home page.
- Browser-side API helpers for conversation creation, listing, reading, deletion, message posting, and message history.
- Conversation selection panel with create and delete actions.
- Message list showing user prompts and deterministic assistant evidence previews.
- Evidence cards for assistant messages with rank, score, excerpt, document id, and chunk id.
- Loading and error states for conversation and message operations.

Current limitation: the UI relies on already ingested and chunked backend data. It does not yet provide manual chunking controls, source previews, or a PDF/page viewer.

## Milestone 7 Progress: Local End-to-End Workflow

Implemented in feature branch `feature/m7-e2e-local-workflow`:

- Document cards show ingestion status, chunk count, workflow errors, and extracted text preview.
- Browser actions for ingestion retry, chunking/rechunking, and preparing a document.
- Prepare document runs existing ingestion and chunking endpoints in sequence.
- Chat empty and no-evidence states guide users to prepare documents before asking questions.
- No new backend service, Docker dependency, vector database, embedding model, LLM call, or paid API integration.

Current limitation: preparation is still synchronous and best suited to small local `.txt`, `.md`, and text-layer `.pdf` files.

## Milestone 8 Progress: Source Evidence Preview

Implemented in feature branch `feature/m8-source-evidence-preview`:

- Read-only chunk context endpoint for selected chunk plus neighboring chunks.
- Context responses include document metadata, chunk indexes, source offsets, estimated token counts, and full chunk text.
- Chat evidence cards expand in the browser and lazy-load source context on demand.
- Evidence cards continue to show stored excerpt snapshots even if live source context cannot be loaded later.
- No PDF page rendering, vector database, embedding model, LLM call, Docker service, or paid API integration.

Current limitation: source preview shows extracted text chunks only. It does not yet render original PDF pages or highlight positions in the source file.

## Milestone 9 Progress: Evaluation Harness

Implemented in feature branch `feature/m9-evaluation-harness`:

- Local retrieval evaluation dataset format under `evals/datasets/`.
- Committed sample fixture under `evals/fixtures/`.
- CLI script `scripts/run_retrieval_eval.py` that runs against local SQLite chunk state.
- Metrics for `hit@k`, mean reciprocal rank, and no-result query count.
- Optional JSON reports under ignored `evals/runs/`.
- Unit tests for dataset parsing, evidence matching, and metric summaries.

Current limitation: evaluation is lexical and term-based only. It does not use LLM judging, embeddings, semantic similarity, or vector retrieval.

## Milestone 10 Progress: PDF Extraction Hardening

Implemented in feature branch `feature/m10-pdf-extraction-hardening`:

- PyMuPDF PDF extraction now reads text page by page.
- Combined `extracted_text.txt` keeps page markers for chunking and preview compatibility.
- Page-level text artifacts are written under `data/storage/artifacts/documents/{document_id}/pages/`.
- PDF metadata records page counts, extracted page counts, pages with and without text, extraction method, warnings, and page text paths.
- Scanned/no-text PDFs fail ingestion with a clear no-text-layer and OCR-future-work warning.
- Text and Markdown ingestion remain supported with the same API behavior.

Current limitation: PDF support is still text-layer only. OCR, page rendering, table extraction, figure extraction, equation parsing, and layout-aware chunking are future work.

## Milestone 11 Progress: Page-Aware Chunking

Implemented in feature branch `feature/m11-page-aware-chunking`:

- `document_chunks` now supports nullable page number, page offsets, source kind, and source path metadata.
- PDF chunks are created from page-level text artifacts when available.
- Text and Markdown chunking keep the existing extracted-text behavior with null page metadata.
- Search results, chat evidence rows, and source context responses expose page metadata when available.
- Chat evidence cards and expanded source context display page labels for PDF-derived chunks.
- Re-running chunking still deletes and recreates chunks cleanly.

Current limitation: chunks are page-local for PDFs and do not intentionally span pages. There is still no OCR, page image rendering, layout-aware chunking, embeddings, vector database, or LLM call.

## Milestone 12 Progress: Stable Evidence Snapshots

Implemented in feature branch `feature/m12-stable-evidence-snapshots`:

- Chat evidence rows now preserve full answer-time source snapshots, including full chunk text, document title/filename, chunk index, character offsets, page offsets, and estimated token count.
- Assistant message evidence responses include the snapshot fields so the frontend can render historical evidence consistently.
- A message evidence source endpoint returns live chunk context when the chunk still exists and falls back to the stored evidence snapshot when chunks are regenerated or deleted.
- Chat evidence cards mark whether the expanded source preview is live source context or a snapshot fallback.
- Historical evidence remains inspectable after re-running chunking or deleting the source document metadata.

Current limitation: snapshot fallback shows captured extracted text only. It does not render original PDF pages, highlight page coordinates, perform OCR, or reconstruct neighboring chunks after the source chunk is gone.

## Milestone 13 Progress: Embedding Abstraction

Implemented in feature branch `feature/m13-embedding-abstraction`:

- Added an embedding provider protocol with provider name, model name, dimension, and `embed_texts()`.
- Added a deterministic local `local-hash` fake embedding provider for offline development and tests.
- Added a `chunk_embeddings` SQLite table that stores one vector per chunk/provider/model.
- Added document-scoped endpoints to index chunk embeddings and read embedding index status.
- Re-indexing a document replaces existing rows for the same provider/model without duplicates.
- Existing lexical search and chat evidence behavior remain unchanged.

Current limitation: embeddings are pipeline scaffolding only. They are hash-based test vectors, not real semantic embeddings, and they are not used for retrieval ranking yet. There is still no vector database, external embedding API, LLM call, Docker service, or paid API integration.

## Milestone 14 Progress: Zero-Budget FTS5 Retrieval

Implemented in feature branch `feature/m14-zero-budget-fts5-retrieval`:

- Removed unused vector-client dependency and paid-provider default config placeholders from local backend setup.
- Updated health/frontend/docs surfaces so the default stack is clearly SQLite/local-only.
- Added retrieval modes: `auto`, `like`, and `fts5`.
- `auto` uses SQLite FTS5 when the local SQLite build supports it and falls back to LIKE otherwise.
- Chunking and re-chunking update the local FTS index when FTS5 is available.
- Document deletion and chunk deletion clear FTS rows to avoid stale retrieval results.
- Search API and retrieval eval can run in explicit modes for comparison.

Current limitation: FTS5 is lexical, not semantic. If the local SQLite build lacks FTS5, PaperLens keeps running with the LIKE fallback. Fake/hash embeddings still are not used for ranking.

## Milestone 15 Progress: Retrieval Eval Comparison

Implemented in feature branch `feature/m15-retrieval-eval-comparison`:

- Added a comparison report that evaluates the same retrieval dataset with `like`, `fts5` when
  available, and `auto`.
- Comparison output includes `hit@k`, MRR, no-result query count, active backend, and per-question
  HIT/MISS status for each mode.
- `--compare-modes` does not fail the whole run if FTS5 is unavailable; it marks FTS5 unavailable and
  continues with LIKE and AUTO.
- JSON comparison reports can be written under ignored `evals/runs/`.

Current limitation: comparison is still lexical and term-based. It does not evaluate answer generation,
semantic similarity, embeddings, reranking, or LLM faithfulness.

## Budget Constraint

PaperLens is developed under a zero-budget constraint.

The project must not require paid APIs, paid cloud services, hosted databases, paid model calls, model
downloads, Docker services, or commercial infrastructure for local development. Any future integration
with paid APIs, hosted vector databases, cloud deployment, or paid services must be optional and
isolated behind interfaces.

Default development mode must work locally on Windows 11 using free tools only.
