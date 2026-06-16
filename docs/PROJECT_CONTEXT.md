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
- Development mode: zero-budget-first local-native default, no Docker requirement
- Preferred project drive: non-C drive, for example `F:\paperlens`

## Current local stack

- Backend: FastAPI
- Frontend: Next.js
- Metadata storage: SQLite during local development
- File storage: local folders during local development
- Retrieval: SQLite LIKE fallback and SQLite FTS5 when available
- Embeddings: deterministic fake/hash vectors for pipeline scaffolding only
- Answer generation: provider interface with deterministic evidence-preview provider as the default,
  provider status diagnostics, an optional OpenAI-compatible adapter disabled by default, and one
  manual adapter smoke validation recorded with NVIDIA NIM as an endpoint example
- Evaluation: local fixture seeding, smoke test, synthetic benchmark v1, and JSON/Markdown reports
- Optional adapters later: free-tier APIs, open-source OCR, local models, free deployment tiers,
  OpenAI-compatible free-provider proxies, PostgreSQL, object storage, and managed services behind
  interfaces

## Current product state after Milestone 24

PaperLens can run a complete local, non-LLM evidence-preview workflow:

1. Upload local `.txt`, `.md`, or text-layer `.pdf` documents.
2. Ingest supported documents into local extracted-text artifacts.
3. Chunk extracted text with source offsets and page metadata when page artifacts exist.
4. Search chunks with SQLite LIKE, SQLite FTS5 when available, or AUTO mode.
5. Create deterministic chat evidence-preview responses through the default `AnswerProvider`
   without calling an LLM.
6. Inspect live source context behind evidence cards.
7. Fall back to stored evidence snapshots when chunks are regenerated or deleted.
8. Seed local evaluation fixtures without a running API server.
9. Compare LIKE, FTS5, and AUTO on smoke and benchmark datasets.
10. Generate local JSON and Markdown retrieval reports under ignored `evals/runs/`.
11. View the configured answer provider status in the backend API and web chat workspace.
12. Optionally configure a generic OpenAI-compatible answer provider for evidence-grounded answer
    drafts without changing the default deterministic provider.
13. Use bounded document, conversation, and chat panels so long lists do not push active chat content
    out of reach.
14. Refer to one manual smoke-validation record showing the generic OpenAI-compatible adapter working
    with NVIDIA NIM as one endpoint example.

The default system is still not a full multimodal RAG system. It has no required LLM answer synthesis,
no real embeddings, no vector database, no OCR, no rendered PDF/page viewer, no table/figure/equation
extraction, and no multimodal vision model integration. The optional OpenAI-compatible adapter is
generic, disabled by default, and not tied to a paid provider. The NVIDIA NIM validation is a manual
smoke test of one compatible endpoint, not a benchmark or universal support claim.

## Why Docker was removed from local development

Docker image pulls and WSL2 Docker storage consumed too much disk space on the Windows C drive. PaperLens will continue with local-native development first. Docker may return later only as an optional deployment artifact, not as the default development path.

## Current research questions

- RQ1: Does evidence-type-aware retrieval improve scientific-paper QA compared with text-only RAG?
- RQ2: Does sending relevant figure/table/page images to a multimodal model improve faithfulness?
- RQ3: Which evidence types cause the most failures in standard RAG?
- RQ4: Can structured table extraction plus multimodal reasoning outperform caption-only retrieval for table-heavy questions?

## Implemented so far

- Local-native FastAPI and Next.js scaffold.
- SQLite metadata and local document/artifact storage.
- Document upload, listing, deletion, ingestion, chunking, and retrieval APIs.
- Page-aware PDF text extraction for text-layer PDFs.
- Page-aware chunk metadata and local lexical search with LIKE/FTS5/AUTO modes.
- Deterministic chat evidence-preview API and frontend chat UI.
- AnswerProvider interface with deterministic local evidence-preview provider as the default.
- Answer provider status API and frontend diagnostic panel.
- Optional OpenAI-compatible answer provider adapter for future free-tier, local server, or proxy
  experiments, plus a manual smoke-validation record using NVIDIA NIM as one compatible endpoint
  example.
- Source context preview and stable evidence snapshot fallback.
- Fake/hash embedding indexing scaffold that does not affect retrieval ranking.
- Local retrieval evaluation harness, fixture seeding, benchmark v1, and JSON/Markdown reports.
- GitHub Actions for API, web, security, and docs.
- Documentation record for thesis, product, engineering, and architecture decisions.

## Next tasks

1. Improve evaluation datasets with more documents, distractors, and evidence-type coverage.
2. Add OCR strategy research before implementing scanned-PDF support.
3. Add table/figure/equation extraction experiments behind local, optional components.
4. Add real local, open-source, or zero-cost/free-tier embeddings only after the zero-budget-first
   architecture is stable.
5. Harden optional OpenAI-compatible provider evaluation only after retrieval, citations, and
   benchmark reporting are sufficiently grounded.
6. Expand thesis result analysis using committed benchmark reports and clearly stated limitations.

## Known risks

- Windows path differences can break scripts if not kept simple.
- Large PDF/image processing can still consume disk space.
- OCR and table extraction dependencies may be heavy; introduce open-source options carefully.
- Optional free-tier or zero-cost multimodal/LLM adapters must be quota-aware, disabled by default,
  and never required for the core evidence pipeline.
- Synthetic benchmark results can be overread if docs do not clearly separate smoke tests, local
  lexical benchmarks, and final thesis claims.

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
- No external LLM, embedding model, vector database, queue, Docker service, or paid API call is used
  by the current implementation.
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
- No new backend service, Docker dependency, vector database, embedding model, LLM call, or paid API
  integration is required by the current implementation.

Current limitation: preparation is still synchronous and best suited to small local `.txt`, `.md`, and text-layer `.pdf` files.

## Milestone 8 Progress: Source Evidence Preview

Implemented in feature branch `feature/m8-source-evidence-preview`:

- Read-only chunk context endpoint for selected chunk plus neighboring chunks.
- Context responses include document metadata, chunk indexes, source offsets, estimated token counts, and full chunk text.
- Chat evidence cards expand in the browser and lazy-load source context on demand.
- Evidence cards continue to show stored excerpt snapshots even if live source context cannot be loaded later.
- No PDF page rendering, vector database, embedding model, LLM call, Docker service, or paid API
  integration is required by the current implementation.

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
- Updated health/frontend/docs surfaces so the default stack is clearly SQLite/local by default.
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

## Milestone 16 Progress: Eval Fixture Seeding

Implemented in feature branch `feature/m16-eval-fixture-seeding`:

- Added `scripts/seed_eval_fixture.py` to seed a committed local fixture into the app SQLite/storage
  state without running the FastAPI server.
- The seeding path creates or reuses a document record, stores the fixture under the normal local
  document storage folder, runs ingestion, and runs chunking.
- `--reset` removes matching fixture documents before recreating them, which makes sample retrieval
  evaluation reproducible from local state.
- The sample smoke-test flow is now:
  `python scripts/seed_eval_fixture.py --fixture evals/fixtures/sample_retrieval_source.txt --reset`
  followed by `python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes`.
- The committed sample uses explicit anchor terms, so 3/3 across LIKE, FTS5, and AUTO verifies local
  seeding/indexing/retrieval plumbing only. It is not a retrieval-quality benchmark.

Current limitation: fixture seeding writes to the configured local development database and storage
folder. Harder benchmark datasets with natural-language questions and distractor documents are future
work. Generated SQLite files, uploads, artifacts, and eval run outputs remain ignored by Git.

## Milestone 17 Progress: Retrieval Benchmark v1

Implemented in feature branch `feature/m17-retrieval-benchmark-v1`:

- Added `evals/fixtures/retrieval_benchmark_v1_source.txt`, a synthetic scientific/technical report
  with methods, results, table-like rows, figure-caption-like text, limitations, and distractors.
- Added `evals/datasets/retrieval_benchmark_v1.json` with natural-language questions, expected
  evidence criteria, difficulty labels, and evidence-type labels.
- Extended the local eval loader/report data to preserve optional `difficulty` and `evidence_type`
  fields.
- The benchmark can be seeded with
  `python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset`
  and compared with
  `python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes`.

Current limitation: benchmark v1 is still synthetic and lexical. Non-perfect scores are expected and
useful, but they are early failure-analysis signals rather than final thesis retrieval-quality claims.

## Milestone 18 Progress: Retrieval Report Generation

Implemented in feature branch `feature/m18-retrieval-report-generation`:

- Extended `scripts/run_retrieval_eval.py` with `--write-markdown` alongside the existing JSON report
  output path.
- JSON reports now include run metadata, the dataset path, report kind, structured summaries,
  per-question results, retrieved evidence, and comparison data for later plotting.
- Markdown reports include run metadata, a mode metrics table, per-question result table,
  interpretation notes, and limitations suitable for thesis drafting.
- Reports are generated locally and written under ignored `evals/runs/`.
- The benchmark report command is:
  `python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown`.

Current limitation: generated reports reflect the current local SQLite/artifact state and lexical
retrieval only. They do not include LLM judging, semantic retrieval, embeddings, OCR, or vector search.

## Milestone 19 Progress: Research Docs Cleanup

Implemented in feature branch `feature/m19-research-docs-cleanup`:

- Updated project context, thesis notes, product roadmap, and architecture decisions after M1-M18.
- Added thesis experiment log and thesis outline documents.
- Added ADRs for zero-budget-first local default, SQLite FTS5 baseline retrieval, fake/hash
  embeddings, and stable evidence snapshots.
- Clarified that PaperLens is zero-budget-first, not local-only forever.
- Documented optional future free-tier/open-source adapters as disabled-by-default interfaces.

Current limitation: this milestone changed documentation only. It did not add OCR, LLM synthesis,
semantic retrieval, deployment, or multimodal vision.

## Milestone 20 Progress: Answer Provider Interface

Implemented in feature branch `feature/m20-answer-provider-interface`:

- Added an `AnswerProvider` protocol with `AnswerRequest`, `AnswerResult`, and `EvidenceInput`
  structures.
- Added `DeterministicEvidenceAnswerProvider` as the default local provider.
- Refactored chat message creation so assistant content is generated through the provider interface.
- Kept existing deterministic evidence-preview content, no-evidence behavior, and evidence snapshot
  storage backward compatible.
- Added a minimal `answer_provider` config setting that defaults to `deterministic-evidence`.
- Unsupported provider names fail clearly at provider selection time.

Current limitation: M20 does not add LLM synthesis or any real provider integration. The only
implemented answer provider is deterministic and local. Future optional providers may use free-tier
APIs or local/open-source tools only if they stay isolated, disabled by default, documented, and
graceful when unavailable.

## Milestone 21 Progress: Provider Diagnostics

Implemented in feature branch `feature/m21-provider-diagnostics`:

- Added answer provider status metadata for provider name, provider type, display name, availability,
  default status, API key requirement, network requirement, model download requirement, streaming
  support, and status message.
- Added `GET /answer-provider/status`.
- Deterministic provider status reports available, local, no API key, no network, no model download,
  and no streaming support.
- Unsupported provider config reports an unavailable `unknown` provider status instead of breaking the
  diagnostics endpoint.
- Added a small frontend provider status panel in the chat workspace.

Current limitation: M21 is diagnostic only. It does not add LLM synthesis, streaming, optional
free-tier providers, local model providers, network calls, API keys, or model downloads.

## Milestone 22 Progress: OpenAI-Compatible Answer Provider

Implemented in feature branch `feature/m22-openai-compatible-provider`:

- Added `OpenAICompatibleAnswerProvider` behind the existing `AnswerProvider` interface.
- Added opt-in config fields: `answer_provider`, `llm_base_url`, `llm_api_key`, `llm_model`,
  `llm_timeout_seconds`, `llm_max_tokens`, `llm_temperature`, and `llm_requires_api_key`.
- The deterministic provider remains the default and requires no network, key, model download, or
  paid service.
- The OpenAI-compatible adapter sends the user question and retrieved evidence snippets to a
  `/chat/completions` endpoint and instructs the provider to answer only from evidence.
- Provider failures, missing config, rate limits, timeouts, network errors, and invalid responses fall
  back to deterministic evidence-preview text while preserving PaperLens evidence rows.
- Provider diagnostics report model name, safe base URL host, network requirement, API-key
  requirement, and availability without exposing secrets.

Current limitation: M22 does not make any provider official or required. Groq, NVIDIA NIM, other
OpenAI-compatible free-tier APIs, local OpenAI-compatible servers, and custom proxy/router endpoints
are configuration examples only. No real provider call happens in tests.

## Milestone 23 Progress: Bounded UI Panels

Implemented in feature branch `feature/m23-bounded-ui-panels`:

- Bounded document, conversation, and chat message panels so long local document libraries and long
  chat histories scroll inside their own regions.
- Kept the chat composer reachable while message history scrolls.
- Preserved upload, prepare, delete, chat, provider status, and evidence-card expansion behavior.
- Fixed a frontend upload form issue where the form event target could be null after an async upload.

Current limitation: the frontend still loads document and conversation lists client-side. This
milestone did not add virtualization or backend pagination.

## Milestone 24 Progress: OpenAI-Compatible Provider Manual Validation

Implemented in feature branch `feature/m24-provider-validation-log`:

- Recorded a manual smoke validation of the generic OpenAI-compatible `AnswerProvider` adapter.
- NVIDIA NIM was used as one compatible endpoint example with
  `model_name: meta/llama-3.1-8b-instruct` and `base_url_host: integrate.api.nvidia.com`.
- Provider diagnostics reported `provider_name: openai-compatible` and an available status.
- The frontend provider status panel worked, chat returned an evidence-grounded answer draft, and
  evidence cards still displayed.
- The bounded UI panels from M23 remained usable during manual validation.
- No API key or secret was recorded.

Current limitation: this is a manual smoke validation only. It does not make NVIDIA NIM required,
official, first-class, or universally supported. Provider quotas, model availability, and endpoint
behavior may vary. The deterministic evidence-preview provider remains the default.

## Zero-Budget-First Policy

PaperLens is developed under a zero-budget-first constraint.

The default workflow, core tests, and local development must not require paid API keys, cloud
accounts, hosted vector databases, Docker, large model downloads, or paid infrastructure.

Optional adapters may use free-tier APIs, open-source OCR such as Tesseract, local open-source tools,
free inference providers, OpenAI-compatible free-provider proxies, or free cloud deployment tiers.
Those adapters must be isolated behind interfaces, disabled by default, documented clearly, and fail
gracefully when credentials, quota, binaries, or local resources are unavailable.

Paid services must never be mandatory for the core evidence pipeline.
