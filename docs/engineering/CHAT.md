# Chat

Milestone 5 added the backend chat foundation for retrieval-grounded evidence previews. Milestone 20
routes assistant answer text through an `AnswerProvider` interface. Milestone 21 adds provider status
diagnostics for the backend API and web UI. Milestone 22 adds one optional generic
OpenAI-compatible provider adapter. The current default workflow does not call an LLM, embedding
model, vector database, cloud service, or paid API. Deterministic evidence previews remain available
without credentials or paid services.

## Flow

1. Create a conversation with `POST /conversations`.
2. Post a user message with `POST /conversations/{conversation_id}/messages`.
3. The backend stores the user message.
4. The backend searches local chunks with the existing lexical retrieval service.
5. The backend sends the question and retrieved evidence to the configured answer provider.
6. The default provider returns deterministic evidence-preview text.
7. The backend stores an assistant message and links retrieved chunks as `message_evidence` rows.
8. Message history can be read with `GET /conversations/{conversation_id}/messages`.

## Answer providers

M20 adds the answer provider boundary in `apps/api/app/generation/answer_service.py`.

Provider inputs:

- `AnswerRequest`
- `EvidenceInput`

Provider output:

- `AnswerResult`

The default provider is:

```text
provider: deterministic-evidence
model: evidence-preview-template-v1
```

The default provider reproduces the existing evidence-preview behavior. It formats retrieved chunks,
document references, chunk references, page metadata when available, scores, and the no-evidence
message. It does not synthesize claims beyond the retrieved evidence list.

The local config setting is:

```text
answer_provider=deterministic-evidence
```

M22 adds this optional provider name:

```text
answer_provider=openai-compatible
```

OpenAI-compatible configuration fields:

```text
llm_base_url=https://example-provider.local/v1
llm_model=example-model
llm_api_key=
llm_requires_api_key=false
llm_timeout_seconds=30
llm_max_tokens=700
llm_temperature=0
```

`llm_base_url` and `llm_model` are required when `answer_provider=openai-compatible`. `llm_api_key`
is required only when `llm_requires_api_key=true`. The API key is sent as a bearer token when present
and is never exposed in provider status responses.

The adapter sends a standard OpenAI-compatible `/chat/completions` request with the user question and
retrieved evidence snippets. Its system instruction tells the provider to answer only from the supplied
evidence, avoid invented facts, and avoid invented citations. PaperLens evidence rows remain the
authoritative citations stored with the assistant message.

If configuration is missing, the endpoint is unavailable, the request times out, the provider returns
an error or rate limit, or the response shape is invalid, the provider returns a clear fallback message
and deterministic evidence-preview text. Evidence rows are still stored by PaperLens.

Groq, NVIDIA NIM, other OpenAI-compatible free-tier APIs, local OpenAI-compatible servers, and custom
proxy/router endpoints are configuration examples only. None is hardcoded, official, or required.
Unsupported provider names still fail clearly during provider selection.

### Manual OpenAI-compatible smoke validation

A manual validation run confirmed the generic OpenAI-compatible adapter with NVIDIA NIM as one
compatible endpoint example:

- backend configured with `answer_provider=openai-compatible`
- `provider_name`: `openai-compatible`
- `model_name`: `meta/llama-3.1-8b-instruct`
- `base_url_host`: `integrate.api.nvidia.com`
- provider status: available
- frontend provider status panel rendered the active provider
- chat returned an evidence-grounded answer draft from the configured provider
- PaperLens evidence cards still displayed under the assistant response

This validation supports adapter compatibility with one endpoint. It is not a benchmark, does not
claim universal NVIDIA NIM support, and does not make NVIDIA NIM required or first-class. Provider
quotas, model availability, rate limits, and endpoint behavior may vary. No API key or secret is
recorded in documentation. The deterministic evidence-preview provider remains the default.

## Provider diagnostics

M21 adds a diagnostic endpoint:

```http
GET /answer-provider/status
```

The response includes:

- `provider_name`
- `provider_type`
- `display_name`
- `model_name`
- `base_url_host`
- `is_default`
- `is_available`
- `requires_api_key`
- `requires_network`
- `requires_model_download`
- `supports_streaming`
- `status_message`

For the default deterministic provider, the endpoint reports available, no API key, no network, no
model download, and no streaming support. For the OpenAI-compatible provider, it reports
`provider_type: "openai-compatible"`, the configured model, a safe base URL host, network requirement,
API-key requirement based on `llm_requires_api_key`, and whether required config is present.
Unsupported provider config returns an unavailable `unknown` provider status with a clear status
message.

The frontend chat workspace shows this same status in a small diagnostic panel. The panel is
informational only; it does not change provider selection and does not add LLM synthesis.

## Frontend flow

Milestone 6 adds a Next.js chat workspace to the home page:

1. The UI loads existing conversations.
2. The user creates or selects a conversation.
3. The user submits a question.
4. The UI displays the stored user message and deterministic assistant message.
5. Assistant evidence rows are shown as citation cards with rank, score, excerpt, document id, and chunk id.
6. If no evidence is returned, the UI shows the backend no-evidence message.
7. The UI shows answer provider diagnostics so users can see that the active provider is deterministic
   evidence preview rather than LLM synthesis.

Milestone 8 makes those evidence cards expandable. Opening a card loads source context from
`GET /documents/{document_id}/chunks/{chunk_id}/context` and shows the selected chunk, source offsets,
estimated token count, document filename, and neighboring chunks.
Milestone 11 adds page numbers and page-local offsets to those cards when the retrieved chunk came from
a PDF page artifact.
Milestone 12 switches the chat evidence expander to
`GET /conversations/{conversation_id}/messages/{message_id}/evidence/{evidence_id}/source`. The
backend returns live chunk context when available and falls back to the stored evidence snapshot when
the original chunk was regenerated or deleted.

## Response behavior

Assistant messages always identify themselves as evidence previews. When chunks match, the default
provider lists retrieved evidence snippets with document, chunk, and page references when page metadata
is available. When no chunks match, the response clearly says no relevant evidence was found and
suggests chunking ingested documents or using terms from uploaded sources.

## Evidence storage

Each evidence row stores:

- `evidence_id`
- `message_id`
- `document_id`
- `chunk_id`
- `rank`
- `score`
- `excerpt`
- `full_chunk_text_snapshot`
- `document_title_snapshot`
- `document_filename_snapshot`
- `chunk_index_snapshot`
- `char_start_snapshot`
- `char_end_snapshot`
- `page_number`
- `page_start`
- `page_end`
- `estimated_token_count_snapshot`

The excerpt and full chunk text are snapshots of retrieved chunk text. They are stored with the message
so the conversation remains interpretable and inspectable even if chunks are regenerated later.

## Stable source preview

The expanded source preview first tries to resolve the current chunk row by `document_id` and `chunk_id`.
If the live chunk still exists, the response is marked `source_status: "live"` and includes neighboring
chunks. If the live chunk is gone because the document was re-chunked or deleted, the response is marked
`source_status: "snapshot"` and includes the stored answer-time snapshot with this note:

```text
This chunk was regenerated or deleted. Showing the evidence snapshot captured when the answer was created.
```

Snapshot fallback does not reconstruct previous or next chunks; it only shows the captured selected
chunk text and metadata.

## Local limitations

- Retrieval is lexical and uses `auto` mode: SQLite FTS5 when available, otherwise LIKE fallback.
- No semantic retrieval, embedding-ranked retrieval, reranking, or LLM answer synthesis yet.
- Deterministic evidence preview is the only default provider.
- Provider status UI is diagnostic only.
- The OpenAI-compatible provider is optional, disabled by default, and not exercised by CI against a
  real network endpoint.
- No PDF page viewer yet.
- Conversation schema is created with the existing local `create_all()` startup behavior; Alembic migrations are still future work.
