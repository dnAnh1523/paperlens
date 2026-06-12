# ADR-0010: Add AnswerProvider Before LLM Adapters

## Status

Accepted

## Context

PaperLens chat responses currently return deterministic evidence previews grounded in retrieved local
chunks. The project is zero-budget-first: the default workflow, local development, and core tests must
not require paid services, API keys, cloud accounts, Docker, hosted vector databases, model downloads,
or paid infrastructure.

Future work may experiment with optional free-tier APIs, local/open-source tools, local models, or
free inference providers for answer synthesis. Those adapters need a stable boundary so they do not
leak credentials, availability, quota, dependency weight, or provider-specific behavior into the core
chat service.

## Decision

PaperLens will route chat answer text through an `AnswerProvider` interface before adding any real LLM
provider integrations.

The M20 interface includes:

- `AnswerProvider`
- `AnswerRequest`
- `AnswerResult`
- `EvidenceInput`

The only implemented provider is `DeterministicEvidenceAnswerProvider`. It preserves the existing
evidence-preview response behavior and remains the default provider.

The chat service remains responsible for:

- storing user messages;
- retrieving local chunks;
- storing assistant messages;
- storing `message_evidence` snapshot rows.

The provider is responsible only for producing assistant answer text from the question and retrieved
evidence inputs.

## Consequences

Positive:

- Current deterministic behavior remains available without credentials, paid services, model
  downloads, or external calls.
- Future answer providers can be isolated behind one interface.
- Tests can inject a provider to verify chat service wiring without adding LLM dependencies.
- Optional future providers can fail gracefully without changing evidence snapshot storage.

Negative:

- The provider interface adds a small abstraction before real LLM synthesis exists.
- Current output is still an evidence preview, not a full synthesized answer.
- Provider selection must remain conservative so optional adapters do not become core requirements.

## Guardrails

- M20 does not add OpenAI, Groq, NIM, FreeLLMAPI, or any real LLM calls.
- The deterministic provider remains the default.
- Optional future providers must be disabled by default, documented clearly, and graceful when
  credentials, quota, binaries, or local resources are unavailable.
- Paid services must never be mandatory for the core evidence pipeline, core tests, or local workflow.
