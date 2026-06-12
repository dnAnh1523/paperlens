# Methodology

The current methodology is to build and evaluate a zero-budget-first local retrieval baseline before
adding optional semantic retrieval or multimodal generation.

System variants currently implemented:

- `like`: SQLite LIKE lexical retrieval.
- `fts5`: SQLite FTS5 lexical retrieval when available.
- `auto`: FTS5 when available, otherwise LIKE.

Evaluation protocol:

1. Seed a known fixture into local SQLite/storage state.
2. Run ingestion and chunking through the same services used by the app.
3. Run the retrieval evaluation CLI in single-mode or comparison mode.
4. Measure `hit@k`, MRR, no-result queries, and per-question HIT/MISS status.
5. Save JSON and Markdown reports under ignored `evals/runs/`.

Current datasets:

- `sample_retrieval_smoke.json`: anchor-term smoke test for pipeline plumbing.
- `retrieval_benchmark_v1.json`: synthetic natural-language benchmark with distractors and
  evidence-type labels.

See `docs/thesis/EXPERIMENT_LOG.md` for reproducible commands.
