# PaperLens Product Requirements Document

## Product summary

PaperLens helps users ask grounded questions over scientific and technical papers. It focuses on evidence that text-only RAG often misses: figures, tables, charts, equations, and page layout.

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
- Text, table, figure, chart, equation, and page-image evidence
- Source-grounded QA
- Evidence previews
- Evaluation suite

## Out of scope for early versions

- Medical diagnosis
- Legal advice
- Autonomous scientific claim verification across the web
- Full video/audio RAG
- Multi-user enterprise permissions beyond basic workspace design

## Success criteria

- The system retrieves relevant evidence for text, table, and figure questions.
- Answers cite source pages/assets.
- Evaluation can compare text-only vs multimodal variants.
- The app runs locally with Docker Compose.
