# PaperLens Architecture

## Local-native development architecture

```text
Next.js web app
    ↓ HTTP
FastAPI backend
    ↓
SQLite metadata database
Local file storage
Qdrant Client local vector store
OpenAI or compatible LLM API later
```

## Evidence pipeline target

```text
PDF paper
    ↓
page rendering + text extraction
    ↓
layout-aware evidence extraction
    ↓
text chunks + table assets + figure assets + equation assets
    ↓
embeddings and evidence-type metadata
    ↓
evidence-type-aware retrieval
    ↓
multimodal answer generation with citations
```

## Production architecture target

Production may later use PostgreSQL, managed Qdrant, object storage, background workers, and CI/CD deployment. Docker is not required for local development.
