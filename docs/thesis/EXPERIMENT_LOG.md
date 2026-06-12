# Experiment Log

This log records local, zero-budget retrieval experiments after Milestones 1-18. All commands are
Windows PowerShell one-liners run from the repository root unless noted otherwise.

## Experiment 1: Retrieval Smoke Test

Purpose:

- Verify that fixture seeding, ingestion, chunking, indexing, and retrieval plumbing work end to end.
- Confirm that LIKE, FTS5 when available, and AUTO can find a known seeded fixture.

Fixture and dataset:

- `evals/fixtures/sample_retrieval_source.txt`
- `evals/datasets/sample_retrieval_smoke.json`

Reproduce:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/sample_retrieval_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes
```

Measures:

- Whether the seeded fixture is stored, ingested, chunked, and retrievable.
- Whether mode comparison executes without requiring the FastAPI server.

Does not prove:

- Retrieval quality.
- FTS5 superiority over LIKE.
- Semantic retrieval behavior.
- Scientific QA answer quality.

Notes:

- The smoke dataset intentionally uses explicit anchor terms such as `localstackeval`,
  `chunkingeval`, and `sourceprevieweval`.
- A perfect score is expected and should be treated as a plumbing check.

## Experiment 2: Retrieval Benchmark v1

Purpose:

- Exercise local lexical retrieval on natural-language questions.
- Include plausible distractor passages, stale pilot values, table-like rows, figure-caption-like
  text, limitations, and evidence definitions.
- Surface early failure modes before adding embeddings or LLM answer synthesis.

Fixture and dataset:

- `evals/fixtures/retrieval_benchmark_v1_source.txt`
- `evals/datasets/retrieval_benchmark_v1.json`

Reproduce:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes
```

Measures:

- `hit@k` for expected evidence chunks.
- Mean reciprocal rank of the first matching evidence chunk.
- No-result query count.
- Differences between LIKE, FTS5, and AUTO on the same local seeded state.
- Difficulty and evidence-type labels for later analysis.

Does not prove:

- General retrieval quality across real scientific corpora.
- That FTS5 is universally better than LIKE.
- That lexical retrieval is sufficient for final PaperLens research goals.
- Answer faithfulness, because no LLM answer synthesis is being evaluated.

Notes:

- Benchmark v1 is synthetic and intentionally small.
- Non-perfect scores are useful because they reveal retrieval weaknesses.
- FTS5 results are local evidence from the current SQLite build and fixture, not a universal claim.

## Experiment 3: LIKE vs FTS5 vs AUTO Comparison

Purpose:

- Compare local retrieval modes on identical seeded data.
- Confirm AUTO chooses FTS5 when available and falls back to LIKE otherwise.
- Track retrieval behavior as chunking, datasets, and scoring evolve.

Reproduce on smoke data:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/sample_retrieval_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes
```

Reproduce on benchmark data:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes
```

Measures:

- Mode availability.
- Active backend.
- `hit@k`, MRR, and no-result queries by mode.
- Per-question HIT/MISS status.

Does not prove:

- Production search performance.
- Semantic matching quality.
- Any result on SQLite builds where FTS5 is unavailable.

## Experiment 4: Report Generation

Purpose:

- Save local benchmark results as reproducible JSON and thesis-friendly Markdown artifacts.
- Keep generated outputs local and ignored by Git.
- Provide structured JSON for later plotting and Markdown for thesis drafting.

Reproduce:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown
```

Output:

- JSON and Markdown reports under `evals/runs/`.
- `evals/runs/` is gitignored.

JSON report includes:

- timestamp
- dataset path
- report kind
- structured summary
- mode comparison data
- per-question results
- retrieved evidence rows for later plotting

Markdown report includes:

- run metadata
- metrics table
- per-question result table
- interpretation notes
- limitations

Does not prove:

- Results are immutable across local databases unless the same fixture is seeded and the same code is
  used.
- Final thesis claims. The reports are intermediate experiment records.
