# PaperLens

PaperLens is an applied CS thesis + production-style software project for evidence-type-aware multimodal RAG over scientific and technical papers.

This scaffold uses a **local-native Windows development setup** instead of Docker.

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

## Storage strategy

Local development uses:

- SQLite for metadata
- local folders for document/page assets
- Qdrant Client local mode for vector search experiments

Production can later use:

- PostgreSQL
- S3 or MinIO
- managed Qdrant or another vector database
- Redis worker queues

## Current status

This is the first local-native scaffold. It intentionally avoids Docker to protect disk space on Windows development machines.
