# ADR-0011: Optional OpenAI-Compatible Answer Provider

## Status

Accepted

## Context

PaperLens is zero-budget-first. The default local workflow and core tests must not require paid
services, API keys, cloud accounts, model downloads, Docker, or hosted vector databases.

M20 introduced the `AnswerProvider` interface and M21 added provider diagnostics. The next adapter
boundary should support future experimentation with free-tier APIs, local OpenAI-compatible servers,
or custom proxy/router endpoints without making any one provider official or required.

## Decision

PaperLens will add a single optional `openai-compatible` answer provider adapter.

The adapter uses the OpenAI-compatible `/chat/completions` request shape through the existing
lightweight HTTP client dependency. It is configured with:

- `answer_provider=openai-compatible`
- `llm_base_url`
- `llm_model`
- `llm_api_key`
- `llm_requires_api_key`
- `llm_timeout_seconds`
- `llm_max_tokens`
- `llm_temperature`

The deterministic provider remains the default. The OpenAI-compatible provider is disabled unless
explicitly selected.

Groq, NVIDIA NIM, other OpenAI-compatible free-tier APIs, local OpenAI-compatible servers, and custom
proxy/router endpoints are configuration examples only. They are not hardcoded and are not official
defaults.

## Evidence Discipline

The adapter sends the user question and retrieved PaperLens evidence snippets to the provider. The
system instruction requires the provider to answer only from supplied evidence and not invent facts,
documents, chunks, pages, or citations.

PaperLens `message_evidence` rows remain the authoritative citations. Provider-generated text is an
answer draft, not the source of citation truth.

## Failure Behavior

The adapter must fail gracefully when:

- required config is missing;
- the endpoint is unreachable;
- the request times out;
- the provider returns an error or rate limit;
- the response body is malformed or missing answer text.

In those cases, chat returns a clear fallback message and deterministic evidence-preview text while
preserving evidence rows.

## Consequences

Positive:

- One generic adapter can support multiple compatible zero-cost or local endpoints later.
- Core development and CI remain credential-free and network-free.
- Provider diagnostics can report model and safe host metadata without exposing secrets.

Negative:

- Compatibility varies across OpenAI-compatible providers.
- The adapter cannot prove answer faithfulness by itself.
- Network and quota behavior remain outside the deterministic test path.

## Guardrails

- No real provider call occurs in tests.
- No provider SDK is added.
- API keys are never logged or exposed through status responses.
- Paid services must never become mandatory for local development, core tests, or the core evidence
  pipeline.
