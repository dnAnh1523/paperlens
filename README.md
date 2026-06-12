# PaperLens

PaperLens is an applied CS thesis + production-style software project for evidence-type-aware multimodal RAG over scientific and technical papers.

This scaffold uses a **zero-budget, local-native Windows development setup** instead of Docker. Local
development does not require paid APIs, hosted vector databases, cloud services, model downloads, or
API keys.

## Local development on Windows 11

Assumptions:

- Editor: VS Code
- Shell: PowerShell
- Commands: one line each
- Project location: preferably on a non-C drive, for example `F:\paperlens`

## Start backend

```powershell
cd apps/api
```

```powershell
py -3.12 -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install --no-cache-dir -e .[dev]
```

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/health`.

## Start frontend

```powershell
cd apps/web
```

```powershell
npm install
```

```powershell
npm run dev
```

Open `http://127.0.0.1:3000`.

## Run retrieval smoke test

Seed the committed sample fixture into the same local SQLite/storage state used by the app:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/sample_retrieval_source.txt --reset
```

Then run the deterministic retrieval smoke test from the repository root:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode auto
```

The sample smoke dataset is designed for `evals/fixtures/sample_retrieval_source.txt` and uses explicit
anchor terms such as `localstackeval`, `chunkingeval`, and `sourceprevieweval`. A 3/3 result means the
fixture was seeded, indexed, and found by retrieval; it does not prove retrieval quality or show that
FTS5 is better than LIKE. Harder benchmark datasets are future work.

The seed command creates or reuses the local document record, stores the fixture under the app storage
folder, ingests it, and chunks it without requiring the FastAPI server. JSON reports can be written
with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --mode like --write-json
```

Compare LIKE, FTS5 when available, and AUTO with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes
```

Write the comparison report JSON with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes --write-json
```

Write a Markdown report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json --compare-modes --write-markdown
```

Generated JSON and Markdown reports under `evals/runs/` are ignored by Git.

## Run retrieval benchmark v1

Seed the harder benchmark fixture:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset
```

Run LIKE, FTS5 when available, and AUTO against the benchmark:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes
```

Write thesis-friendly JSON and Markdown report artifacts:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown
```

`retrieval_benchmark_v1` uses natural-language questions, distractor paragraphs, table-like rows,
figure-caption-like text, and limitations. It is intended to reveal local lexical retrieval failure
modes. Non-perfect scores are expected and useful. The Markdown report includes run metadata, a metrics
table, per-question results, interpretation notes, and limitations.

## Storage strategy

Local development uses:

- SQLite for metadata
- local folders for document/page assets
- SQLite LIKE/FTS5 lexical retrieval
- deterministic fake/hash embeddings for pipeline scaffolding only

Optional production work can later introduce managed services behind interfaces, but they are not part
of the default zero-budget development setup:

- PostgreSQL
- object storage
- a managed vector database
- Redis worker queues

## Current status

PaperLens intentionally avoids Docker, paid APIs, hosted services, and model downloads in local
development to stay usable on zero budget.
