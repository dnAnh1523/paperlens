# Thesis Outline

## Proposed Title

PaperLens: Local Evidence-Grounded Retrieval Infrastructure for Scientific Document Question Answering

Alternative title:

Evidence-Type-Aware Retrieval Foundations for Zero-Budget Scientific Document QA

## Problem Statement

Scientific and technical documents contain evidence across text, tables, figures, captions, equations,
and page layout. Early RAG systems often flatten documents into text chunks and can lose source
context, page provenance, and evidence type. PaperLens investigates a local-first foundation for
evidence-grounded scientific document QA, beginning with text-layer ingestion, page-aware chunking,
lexical retrieval, deterministic evidence-preview chat, source context inspection, and reproducible
retrieval evaluation.

The current implementation does not yet perform multimodal reasoning. It is the zero-budget-first
local engineering base needed before adding optional OCR, table extraction, figure extraction,
embeddings, and LLM answer synthesis.

## Research Questions

RQ1. How reliably can a local lexical retrieval baseline recover expected evidence chunks from
scientific/technical documents?

RQ2. Which evidence categories are most fragile in a text-only local retrieval baseline, such as
methods, results, table-like rows, figure-caption-like text, definitions, and limitations?

RQ3. How can source-grounded evidence previews and stable evidence snapshots improve inspectability
and reproducibility before LLM answer synthesis is introduced?

RQ4. What architecture boundaries are needed to add semantic retrieval, OCR, table/figure extraction,
and multimodal answer generation later without breaking the zero-budget-first local default workflow?

## Chapter 1: Introduction

- Motivation: scientific QA requires grounded evidence, not generic document chat.
- Problem: text-only chunking and retrieval can miss tables, figures, captions, equations, and layout.
- Scope: local evidence-grounded retrieval foundation, not completed multimodal QA.
- Contributions:
  - local-native document ingestion and artifact storage
  - page-aware text extraction and chunking
  - LIKE/FTS5/AUTO retrieval comparison
  - deterministic evidence-preview chat and source context inspection
  - stable evidence snapshots
  - reproducible smoke and benchmark evaluation with Markdown/JSON reports

## Chapter 2: Background and Related Work

- Retrieval-augmented generation for document QA.
- Scientific document parsing and text-layer PDF extraction.
- Lexical retrieval baselines, including LIKE-style matching and SQLite FTS5/BM25.
- Evidence provenance, citations, and source inspection.
- Evaluation methods for retrieval: `hit@k`, MRR, no-result counts, and evidence-type labels.
- Gaps before multimodal RAG: OCR, table structure, figure understanding, layout-aware evidence, and
  LLM faithfulness.

## Chapter 3: System Design

- Local-native architecture:
  - FastAPI backend
  - Next.js frontend
  - SQLite metadata
  - local file/artifact storage
- Document lifecycle:
  - upload
  - ingestion
  - page-aware extraction
  - chunking
  - retrieval
  - chat evidence preview
- Data model:
  - documents
  - ingestion jobs
  - document chunks
  - chunk embeddings placeholder
  - conversations
  - messages
  - message evidence snapshots
- Retrieval design:
  - LIKE fallback
  - SQLite FTS5 when available
  - AUTO mode
  - no real embeddings yet
- Evidence inspectability:
  - live chunk context endpoint
  - snapshot fallback after re-chunking
  - frontend evidence cards
- Evaluation infrastructure:
  - fixture seeding
  - smoke dataset
  - benchmark v1
  - JSON/Markdown report generation

## Chapter 4: Implementation

- Windows 11 local development workflow.
- FastAPI service modules and modular ingestion/chunking/retrieval services.
- Text and text-layer PDF extraction behavior.
- Page-aware chunk metadata.
- FTS5 availability detection and LIKE fallback.
- Deterministic fake/hash embedding provider as architecture-only scaffolding.
- Chat evidence API without LLM calls.
- Frontend document library, prepare flow, chat UI, and source preview.
- Gitignored runtime data and eval report outputs.

## Chapter 5: Evaluation

- Evaluation goals:
  - verify pipeline reproducibility
  - compare local lexical retrieval modes
  - identify retrieval failure modes before semantic retrieval
- Smoke test:
  - explicit anchor terms
  - validates seeding, ingestion, chunking, and retrieval plumbing
  - not a benchmark
- Retrieval benchmark v1:
  - synthetic scientific/technical fixture
  - natural-language questions
  - distractor paragraphs
  - evidence-type labels
  - expected evidence criteria
- Metrics:
  - `hit@k`
  - MRR
  - no-result query count
  - per-question HIT/MISS analysis
- Report artifacts:
  - Markdown for thesis discussion
  - JSON for later plotting
- Interpretation rules:
  - FTS5 results are local benchmark evidence only
  - benchmark v1 is synthetic and not a universal retrieval proof

## Chapter 6: Results and Discussion

- Smoke test result interpretation:
  - expected perfect retrieval when the pipeline is working
  - confirms plumbing, not quality
- Benchmark v1 result interpretation:
  - compare LIKE, FTS5, and AUTO on the same local seeded fixture
  - identify distractor-sensitive cases
  - discuss evidence types where lexical retrieval struggles
- Engineering findings:
  - local-native setup kept the project feasible under zero budget
  - evidence snapshots improved historical inspectability
  - source preview made retrieval behavior easier to debug

## Chapter 7: Limitations

- No LLM answer synthesis yet.
- No real semantic embeddings or vector retrieval yet.
- No multimodal vision model integration yet.
- No OCR for scanned PDFs.
- No rendered PDF page viewer.
- No table, figure, chart, or equation extraction yet.
- Benchmark v1 is synthetic and small.
- FTS5 availability and ranking can vary by local SQLite build.
- Current results should not be generalized to all scientific-paper QA tasks.

## Chapter 8: Future Work

- Add larger benchmark datasets with multiple documents and distractors.
- Add OCR strategy for scanned PDFs.
- Add table extraction and structured table retrieval.
- Add figure/caption extraction and page image preview.
- Add equation-aware extraction experiments.
- Add optional real embeddings behind the provider interface.
- Add semantic retrieval and reranking.
- Add LLM answer synthesis with citation constraints.
- Add multimodal evidence-type routing once text-only baselines are reliable.
