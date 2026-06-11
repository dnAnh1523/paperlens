# Chat

Milestone 5 adds the backend chat foundation for retrieval-grounded evidence previews. It does not call an LLM, embedding model, vector database, cloud service, or paid API.

## Flow

1. Create a conversation with `POST /conversations`.
2. Post a user message with `POST /conversations/{conversation_id}/messages`.
3. The backend stores the user message.
4. The backend searches local chunks with the existing lexical retrieval service.
5. The backend stores an assistant message generated from a deterministic template.
6. Retrieved chunks are stored as `message_evidence` rows linked to the assistant message.
7. Message history can be read with `GET /conversations/{conversation_id}/messages`.

## Frontend flow

Milestone 6 adds a Next.js chat workspace to the home page:

1. The UI loads existing conversations.
2. The user creates or selects a conversation.
3. The user submits a question.
4. The UI displays the stored user message and deterministic assistant message.
5. Assistant evidence rows are shown as citation cards with rank, score, excerpt, document id, and chunk id.
6. If no evidence is returned, the UI shows the backend no-evidence message.

Milestone 8 makes those evidence cards expandable. Opening a card loads source context from
`GET /documents/{document_id}/chunks/{chunk_id}/context` and shows the selected chunk, source offsets,
estimated token count, document filename, and neighboring chunks.
Milestone 11 adds page numbers and page-local offsets to those cards when the retrieved chunk came from
a PDF page artifact.

## Response behavior

Assistant messages always identify themselves as evidence previews. When chunks match, the response lists retrieved evidence snippets with document, chunk, and page references when page metadata is available. When no chunks match, the response clearly says no relevant evidence was found and suggests chunking ingested documents or using terms from uploaded sources.

## Evidence storage

Each evidence row stores:

- `evidence_id`
- `message_id`
- `document_id`
- `chunk_id`
- `rank`
- `score`
- `excerpt`
- `page_number`
- `page_start`
- `page_end`

The excerpt is a snapshot of retrieved chunk text. It is stored with the message so the conversation remains interpretable even if chunks are regenerated later.

The expanded source preview reads the current chunk row by `document_id` and `chunk_id`. If chunks are
regenerated after a conversation was created, an old evidence row can still show its stored excerpt, but
the source context lookup may return `Chunk not found`.

## Local limitations

- Retrieval is lexical and LIKE-based.
- No semantic retrieval, embeddings, reranking, or answer synthesis yet.
- No PDF page viewer yet.
- Conversation schema is created with the existing local `create_all()` startup behavior; Alembic migrations are still future work.
