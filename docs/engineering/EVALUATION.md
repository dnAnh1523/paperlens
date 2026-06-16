# Evaluation

Milestone 9 adds a local retrieval evaluation harness. The default harness is deterministic and does
not call an LLM, embedding model, vector database, cloud service, Docker service, or paid API.
Future optional evaluation variants may test free-tier or open-source adapters, but core evals must
remain runnable without credentials or hosted services.

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
      "scoped_document_filename": "sample_retrieval_source.txt",
      "expected_chunk_text_contains": ["SQLite for metadata"],
      "difficulty": "easy",
      "evidence_type": "method",
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
- `scoped_document_filename`: optional exact source filename used as a document filter before retrieval.
- `expected_chunk_text_contains`: optional string or list of strings that overrides term matching for the chunk text.
- `difficulty`: optional `easy`, `medium`, or `hard`.
- `evidence_type`: optional `method`, `result`, `table`, `figure_caption`, `limitation`, or `definition`.
- `notes`: optional evaluator notes.

A case is a hit when a retrieved chunk matches the expected filename, if provided, and contains all
required expected chunk terms.

When `scoped_document_filename` is present, the eval runner searches only chunks from the most recent
local document row with that original filename. If the scoped document has not been seeded, the case
returns no results instead of silently falling back to global retrieval.

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

## Retrieval benchmark v1

Milestone 17 adds a harder local benchmark:

```text
evals/fixtures/retrieval_benchmark_v1_source.txt
evals/datasets/retrieval_benchmark_v1.json
```

The benchmark fixture is a synthetic scientific/technical report with abstract-like, methods,
results, table-like, figure-caption-like, stable snapshot definition, limitations, and distractor
sections. The dataset uses natural-language questions and expected evidence criteria. It includes
difficulty and evidence-type labels so reports can be grouped later.

Seed the benchmark fixture:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset
```

Run the benchmark comparison:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes
```

Write reproducible local report artifacts:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown
```

This benchmark is intentionally not an anchor-term smoke test. It includes stale pilot results,
similar figure captions, and repeated generic retrieval terms. Non-perfect scores are useful because
they show where local lexical retrieval fails or retrieves plausible but wrong evidence.

## Scoped retrieval regression eval

Milestone 27 adds a small scoped retrieval regression dataset:

```text
evals/fixtures/scoped_retrieval_alpha_source.txt
evals/fixtures/scoped_retrieval_beta_source.txt
evals/datasets/scoped_retrieval_eval.json
```

The alpha and beta fixtures intentionally share terms such as shared alloy membrane, calibration
drift, evidence cards, and local lexical retrieval. Scoped cases use `scoped_document_filename` to
prove retrieval is filtered to the selected source before evidence is evaluated. The unscoped contrast
case uses the same query without a scope so reports show the difference between scoped and global
retrieval behavior.

Seed both scoped fixtures from the repository root:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/scoped_retrieval_alpha_source.txt --reset
```

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/scoped_retrieval_beta_source.txt --reset
```

Run the scoped comparison:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/scoped_retrieval_eval.json --compare-modes
```

This eval is a regression check for document filtering. It does not prove FTS5 is better than LIKE.

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

## Report files

Write a local JSON report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode auto --write-json
```

Write a comparison JSON report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes --write-json
```

Write a Markdown report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-markdown
```

Write both JSON and Markdown reports with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown
```

Generated reports are written under `evals/runs/`, which is gitignored. JSON report files include:

- `generated_at`: UTC timestamp for the local run.
- `dataset_path`: dataset path passed to the CLI.
- `report_kind`: `single` or `comparison`.
- `report`: structured summary, per-case results, retrieved evidence, and mode comparison data.

Markdown report files include:

- run metadata with dataset path/name, timestamp, evaluated modes, and FTS5 availability.
- metrics table with mode, backend, `hit@k`, MRR, no-result queries, and availability.
- per-question result table with document scope, difficulty, evidence type, and mode-specific status.
- interpretation notes for reading local lexical retrieval metrics.
- limitations for thesis-safe reporting.

## Limitations

- Metrics only check local lexical retrieval against expected filenames and chunk text terms.
- The committed sample is a smoke test with explicit anchor terms, not a benchmark for retrieval
  quality.
- `retrieval_benchmark_v1` is still small and synthetic; it is useful for regression checks and early
  failure analysis, not for final thesis claims.
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
