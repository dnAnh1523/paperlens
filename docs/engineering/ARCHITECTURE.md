# PaperLens Architecture

## Zero-Budget-First Local Architecture

```text
Next.js web app
    -> HTTP
FastAPI backend
    ->
SQLite metadata database
Local file storage
SQLite LIKE/FTS5 retrieval
Fake/hash embeddings for local scaffolding
AnswerProvider interface
```

The default local workflow is zero-budget-first. It does not require Docker, paid APIs, cloud
accounts, hosted vector databases, model downloads, or API keys.

Optional adapters may later use free-tier APIs, open-source OCR, local open-source models, free
inference providers, OpenAI-compatible free-provider proxies, or free deployment tiers. They must be
disabled by default, isolated behind interfaces, documented clearly, and graceful when credentials,
quota, binaries, or local resources are unavailable.

## Evidence Pipeline Target

```text
PDF paper
    -> page-aware text extraction
    -> source-grounded chunks
    -> lexical retrieval baseline
    -> AnswerProvider
    -> evidence-preview chat with citations
```

The default `AnswerProvider` is deterministic and local. It returns the current evidence-preview text
without LLM calls, API keys, model downloads, or paid services. Later research work may add
layout-aware evidence extraction, real embeddings, optional LLM answer providers, multimodal
reasoning, and optional deployment adapters. Those additions must stay behind interfaces and must not
become local development or core-test requirements.

## Production Architecture Target

Production experiments may later use PostgreSQL, object storage, managed retrieval services,
background workers, CI/CD deployment, or free hosting tiers behind optional interfaces. Docker, cloud
accounts, and paid services are not required for local development.
