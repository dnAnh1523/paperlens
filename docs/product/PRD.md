# PaperLens Product Requirements Document

## Product summary

PaperLens helps users ask grounded questions over scientific and technical papers. It focuses on evidence that text-only RAG often misses: figures, tables, charts, equations, and page layout.
The current M1-M18 implementation is a zero-budget-first local evidence-preview foundation, not a
completed multimodal QA product.

## Target users

- Students reading papers
- Researchers doing literature review
- Engineers studying technical reports
- Applied ML/AI practitioners comparing methods and results

## Core user stories

- As a user, I can upload a scientific PDF.
- As a user, I can see ingestion status.
- As a user, I can ask questions about the paper.
- As a user, I can receive answers with citations.
- As a user, I can inspect the source page, table, or figure used as evidence.

## In scope

- Scientific and technical PDFs
- Text evidence now; table, figure, chart, equation, and page-image evidence as future optional
  evidence types
- Source-grounded evidence previews now; full QA answer synthesis later
- Evidence previews
- Evaluation suite

## Out of scope for early versions

- Medical diagnosis
- Legal advice
- Autonomous scientific claim verification across the web
- Full video/audio RAG
- Multi-user enterprise permissions beyond basic workspace design

## Success criteria

- The default app runs locally on Windows 11 without Docker, paid APIs, cloud accounts, hosted vector
  databases, large model downloads, or API keys.
- The system retrieves and previews relevant text evidence with source citations.
- Users can inspect source chunks and stable evidence snapshots.
- Evaluation can compare LIKE, FTS5, and AUTO retrieval modes.
- Future optional adapters for OCR, free-tier LLM providers, open-source tools, deployment, and
  multimodal evidence stay isolated and disabled by default.
