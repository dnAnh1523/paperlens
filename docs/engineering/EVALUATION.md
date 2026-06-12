# Evaluation

Milestone 9 adds a local retrieval evaluation harness. It is deterministic and does not call an LLM,
embedding model, vector database, cloud service, Docker service, or paid API.

## Dataset format

Retrieval datasets are JSON files with a top-level `cases` list:

```json
{
  "name": "sample_retrieval_smoke",
  "description": "Optional description",
  "default_k": 5,
  "cases": [
    {
      "id": "local-stack",
      "question": "What local stack does PaperLens use?",
      "expected_terms": ["SQLite", "local folders"],
      "expected_answer_terms": ["metadata"],
      "expected_document_filename": "sample_retrieval_source.txt",
      "expected_chunk_text_contains": ["SQLite for metadata"],
      "notes": "Optional notes"
    }
  ]
}
```

Supported case fields:

- `question`: required search query.
- `expected_terms`: optional string or list of strings expected in a retrieved evidence chunk.
- `expected_answer_terms`: optional string or list of strings, used when `expected_terms` is absent.
- `expected_document_filename`: optional exact source filename match.
- `expected_chunk_text_contains`: optional string or list of strings that overrides term matching for the chunk text.
- `notes`: optional evaluator notes.

A case is a hit when a retrieved chunk matches the expected filename, if provided, and contains all
required expected chunk terms.

## Sample smoke dataset

Committed sample files:

```text
evals/fixtures/sample_retrieval_source.txt
evals/datasets/sample_retrieval_smoke.json
```

This sample is a smoke test for fixture seeding, chunk indexing, and retrieval plumbing. It deliberately
uses explicit anchor terms in the fixture and queries:

- `localstackeval`
- `chunkingeval`
- `sourceprevieweval`

When LIKE, FTS5, and AUTO all return 3/3, that means the seeded fixture can be found consistently by
each retrieval mode. It does not prove FTS5 is better than LIKE, and it is not a retrieval-quality
benchmark.

To run the smoke test, seed the fixture into the local app state from the repository root:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/sample_retrieval_source.txt --reset
```

The seeding command does not require the FastAPI server. It creates or reuses a document row for the
fixture, copies the source into local app storage, runs ingestion, and runs chunking. `--reset` removes
matching fixture documents before recreating them, which is useful when you want a clean eval setup.

Then run:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode auto
```

The script defaults to the same local app state used by the backend development setup:

```text
apps/api/data/sqlite/paperlens.db
apps/api/data/storage
```

Environment variables `DATABASE_URL` and `LOCAL_STORAGE_ROOT` can override those paths.

## Metrics

The report prints:

- `Mode`: requested retrieval mode, one of `auto`, `like`, or `fts5`.
- `Backend`: actual retrieval backend used for results.
- `SQLite FTS5 available`: whether the local SQLite build supports FTS5.
- `hit@k`: fraction of cases where a matching chunk appears in the top `k` results.
- `MRR`: mean reciprocal rank of the first matching chunk.
- `No-result queries`: number of cases where retrieval returned no chunks.

Override `k` with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --limit 10 --mode like
```

Compare retrieval modes with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode auto
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode like
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode fts5
```

If SQLite FTS5 is unavailable, `--mode fts5` exits with a clear unavailable message. `--mode auto`
falls back to LIKE.

Milestone 15 adds one-command comparison across LIKE, FTS5 when available, and AUTO:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes
```

The comparison report prints one mode summary table with `hit@k`, MRR, no-result count, and active
backend for each mode. It also prints a per-question HIT/MISS summary. If FTS5 is unavailable, the
FTS5 row is marked unavailable and LIKE/AUTO still run.

## JSON reports

Write a local JSON report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode auto --write-json
```

Write a comparison JSON report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes --write-json
```

Generated reports are written under `evals/runs/`, which is gitignored.

## Limitations

- Metrics only check local lexical retrieval against expected filenames and chunk text terms.
- The committed sample is a smoke test with explicit anchor terms, not a benchmark for retrieval
  quality.
- There is no LLM judge, answer faithfulness score, semantic similarity, reranking, or embedding recall yet.
- A future benchmark should use harder natural-language questions, multiple documents, distractor
  chunks, expected evidence spans, and mode-specific analysis.
- The harness evaluates current local SQLite state, so documents must be seeded or uploaded,
  ingested, and chunked first.

## PDF notes

PDF eval cases should use text-layer PDFs for now. Milestone 10 preserves page markers in
`extracted_text.txt` and writes page-level text artifacts, so retrieval cases can target terms that
appear on specific pages. Scanned PDFs without a text layer are expected to fail ingestion until OCR is
implemented.
