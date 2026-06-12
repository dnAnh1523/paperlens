# Limitations

Current M1-M18 limitations:

- No LLM answer synthesis.
- No real semantic embeddings.
- No vector database.
- No multimodal vision model integration.
- No OCR for scanned PDFs.
- No rendered PDF page viewer.
- No table, figure, chart, or equation extraction.
- Page awareness currently comes from extracted text artifacts, not visual page geometry.
- Benchmark v1 is synthetic and small.
- Smoke test results are plumbing checks, not retrieval-quality evidence.
- FTS5 availability and ranking can vary by local SQLite build.
- Current reports evaluate retrieval against expected chunk text, not answer faithfulness.

Threats to validity:

- Synthetic fixtures may not represent real scientific-paper distributions.
- Lexical retrieval can reward repeated terms and miss paraphrases.
- Local database state must be controlled with fixture seeding before comparing results.
- Results from a Windows local development environment may not transfer directly to production
  infrastructure.
