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

