# Problem Statement

Scientific and technical documents contain evidence in text, tables, figures, captions, equations, and
page layout. A text-only retrieval system can lose important context when source evidence is flattened
into chunks without page metadata, evidence-type labels, or inspectable citations.

PaperLens currently focuses on the local retrieval foundation for this problem. The M1-M18 system
supports local upload, text-layer ingestion, page-aware chunking, LIKE/FTS5/AUTO retrieval,
deterministic chat evidence previews, source context inspection, stable evidence snapshots, fixture
seeding, benchmark comparison, and JSON/Markdown report generation.

Current non-scope:

- LLM answer synthesis.
- Real semantic embeddings or vector retrieval.
- OCR for scanned PDFs.
- Table, figure, chart, and equation extraction.
- Multimodal vision model reasoning.
- Paid APIs, cloud services, Docker, or hosted databases as local requirements.
