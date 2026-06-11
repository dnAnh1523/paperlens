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
- Vector store: Qdrant Client local mode during local development
- Production target later: PostgreSQL + managed vector database + object storage + queue workers

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
