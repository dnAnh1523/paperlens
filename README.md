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

## Run retrieval evaluation

After uploading and preparing local documents, run a deterministic retrieval eval from the repository root:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_eval.json --mode auto
```

The sample dataset is designed for `evals/fixtures/sample_retrieval_source.txt`. Upload that file in
the web UI, click `Prepare document`, then run the command above. JSON reports can be written with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_eval.json --mode like --write-json
```

Generated reports under `evals/runs/` are ignored by Git.

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
