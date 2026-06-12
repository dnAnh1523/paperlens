# PaperLens Architecture

## Local-Native Development Architecture

```text
Next.js web app
    -> HTTP
FastAPI backend
    ->
SQLite metadata database
Local file storage
SQLite LIKE/FTS5 retrieval
Fake/hash embeddings for local scaffolding
```

Local development is zero-budget. It does not require Docker, paid APIs, hosted vector databases, model
downloads, or API keys.

## Evidence Pipeline Target

```text
PDF paper
    -> page-aware text extraction
    -> source-grounded chunks
    -> lexical retrieval baseline
    -> evidence-preview chat with citations
```

Later research work may add layout-aware evidence extraction, real embeddings, multimodal reasoning,
and optional production adapters. Those additions must stay behind interfaces and must not become local
development requirements.

## Production Architecture Target

Production may later use PostgreSQL, object storage, managed retrieval services, background workers,
and CI/CD deployment behind optional interfaces. Docker and paid services are not required for local
development.
