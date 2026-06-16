# Roadmap

PaperLens is a zero-budget-first, local-native applied CS thesis project and production-style
engineering artifact. Completed milestones are intentionally scoped to local evidence preview and
retrieval evaluation before adding optional embeddings, vector retrieval, OCR, multimodal models, or
LLM answer synthesis.

Zero-budget-first means the default workflow must run locally without paid services. It still allows
optional future adapters that use free-tier APIs, open-source OCR, local open-source tools, free
inference providers, OpenAI-compatible free-provider proxies, or free deployment tiers when they are
disabled by default and fail gracefully.

## Completed Milestones

### M0: Foundation

- Repository scaffold
- Documentation scaffold
- GitHub Actions scaffold
- Initial local-native direction

### M1: Document Metadata and Upload Flow

- SQLite document metadata
- `ingestion_jobs` table
- Local document storage
- Upload, list, read, and delete document APIs

### M2: Document Library UI

- Next.js document upload/list/delete UI
- API connectivity state
- Document metadata display

### M3: Ingestion Foundation

- Synchronous ingestion
- Text and Markdown extraction
- Text-layer PDF extraction where supported
- Ingestion status endpoints
- Extracted text preview

### M4: Chunking and Retrieval Foundation

- `document_chunks` table
- Deterministic text chunking
- Chunk list/detail APIs
- LIKE-based local lexical search

### M5: Chat Evidence API

- Conversations, messages, and message evidence tables
- Deterministic assistant evidence-preview responses
- No LLM calls

### M6: Chat UI

- Conversation list
- Message input and history
- Assistant evidence cards

### M7: Local End-to-End Workflow

- Browser workflow for upload, ingest, chunk, and chat
- Document prepare action
- Chunk readiness and preview state

### M8: Source Evidence Preview

- Chunk context endpoint
- Expandable evidence cards
- Previous/selected/next chunk inspection

### M9: Evaluation Harness

- Retrieval evaluation dataset format
- Local CLI runner
- `hit@k`, MRR, and no-result metrics
- Gitignored eval run outputs

### M10: PDF Extraction Hardening

- Page-by-page PyMuPDF text extraction
- PDF extraction metadata
- Page text artifacts
- Clear scanned/no-text PDF failure behavior

### M11: Page-Aware Chunking

- Page metadata on chunks
- Page metadata in search/chat/source-preview responses
- Re-chunking without duplicates

### M12: Stable Evidence Snapshots

- Full evidence snapshot fields
- Live source context preferred
- Snapshot fallback for stale/deleted chunks

### M13: Embedding Abstraction

- Embedding provider protocol
- Deterministic fake/hash provider
- SQLite chunk embedding table
- Explicit fake embedding indexing/status APIs
- Lexical retrieval unchanged

### M14: Zero-Budget FTS5 Retrieval

- Removed unused vector-client dependency
- LIKE/FTS5/AUTO retrieval modes
- FTS5 availability detection
- FTS index maintenance during chunking/deletion
- Zero-budget docs cleanup

### M15: Retrieval Eval Comparison

- Compare LIKE, FTS5, and AUTO on the same dataset
- Mode summary and per-question HIT/MISS output
- FTS5-unavailable handling

### M16: Eval Fixture Seeding

- Local fixture seed command without running FastAPI
- Idempotent/reset behavior
- Smoke fixture seeding workflow
- Honest smoke-test documentation

### M17: Retrieval Benchmark v1

- Synthetic technical benchmark fixture
- Natural-language questions
- Difficulty and evidence-type labels
- Distractor-sensitive cases

### M18: Retrieval Report Generation

- JSON report output with structured data for later plotting
- Markdown report output for thesis drafting
- Reports under ignored `evals/runs/`

### M19: Research Docs Cleanup

- Align project context, thesis docs, product roadmap, and ADRs with M1-M18.
- Record what current experiments measure and what they do not prove.
- Keep overclaiming out of thesis and product docs.
- Clarify zero-budget-first default versus optional free-tier/open-source adapters.

### M20: Answer Provider Interface

- `AnswerProvider` protocol for chat answer text generation.
- `AnswerRequest`, `AnswerResult`, and `EvidenceInput` structures.
- Deterministic evidence-preview provider remains the default.
- Existing chat API behavior and evidence snapshot storage preserved.
- No real LLM provider calls, API keys, model downloads, or new dependencies.

### M21: Provider Diagnostics

- `GET /answer-provider/status` backend endpoint.
- Provider metadata for type, display name, default status, availability, API key requirement,
  network requirement, model download requirement, streaming support, and status message.
- Frontend provider status panel in the chat workspace.
- Deterministic evidence-preview provider remains the default.
- Diagnostic only; no LLM synthesis, network call, API key, or model download.

### M22: OpenAI-Compatible Answer Provider

- Optional `openai-compatible` `AnswerProvider` adapter.
- Configurable `llm_base_url`, `llm_model`, optional `llm_api_key`, timeout, max tokens, and
  temperature.
- Evidence-grounded `/chat/completions` request construction.
- Graceful fallback to deterministic evidence preview on missing config, timeout, provider error,
  rate limit, invalid response, or network failure.
- Provider diagnostics show model and safe host without exposing secrets.
- Disabled by default; no real provider calls in tests.

## Proposed Next Milestones

### M23: Benchmark Expansion

- Add multiple synthetic and real text-layer documents.
- Add more distractors and evidence-type categories.
- Track per-evidence-type results in reports.

### M24: OCR and Scanned PDF Strategy

- Research open-source OCR options such as Tesseract and dependency cost.
- Decide whether OCR can remain zero-budget-first and Windows-friendly.
- Prototype only if disk/runtime cost is acceptable.

### M25: Table and Figure Evidence Planning

- Define table/figure extraction requirements.
- Add fixture design for table-like and figure-caption evidence.
- Avoid heavy dependencies until the research value is clear.

### M26: Optional Real Embedding Adapter

- Keep fake/hash provider as default.
- Add optional real embedding provider only if it does not become a required dependency.
- Prefer local open-source or zero-cost/free-tier providers, and do not make paid providers part of
  the core workflow.
- Evaluate semantic retrieval separately from lexical baselines.

### M27: Optional LLM Answer Synthesis Evaluation

- Add citation-constrained answer synthesis only after retrieval evaluation is stable.
- Keep deterministic evidence preview as the fallback.
- Evaluate optional free-tier LLM providers or OpenAI-compatible free-provider proxies behind an
  `AnswerProvider` implementation.
- Do not make API credentials, quota, or paid APIs required for local development.

### M28: Free Deployment Experiments

- Test free deployment tiers for demos only after local workflows are stable.
- Keep local SQLite/storage workflow as the core development default.
- Document graceful failure and fallback behavior when quotas or hosted services are unavailable.

## Explicit Non-Goals for Current Local Default

- No Docker requirement for the default workflow.
- No cloud account requirement for the default workflow.
- No paid API requirement for the default workflow.
- No real embedding model download requirement for the default workflow.
- No hosted vector database requirement for the default workflow.
- No LLM answer synthesis in the default workflow yet.
- No OCR, table extraction, figure extraction, or equation parsing yet.
- Optional zero-cost/free-tier adapters are allowed only when isolated, disabled by default, and
  graceful when unavailable.
