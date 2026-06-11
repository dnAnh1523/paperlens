"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  ChatMessage,
  Conversation,
  DocumentChunk,
  DocumentChunkContext,
  MessageEvidence,
  createConversation,
  deleteConversation,
  fetchConversationMessages,
  fetchConversations,
  fetchDocumentChunkContext,
  postConversationMessage,
} from "../../lib/api";

type EvidencePreviewState = {
  isOpen: boolean;
  isLoading?: boolean;
  context?: DocumentChunkContext;
  error?: string;
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatScore(score: number): string {
  return Number.isInteger(score) ? String(score) : score.toFixed(2);
}

function getMessageLabel(message: ChatMessage): string {
  return message.role === "user" ? "You" : "PaperLens";
}

function formatChunkLocation(chunk: DocumentChunk): string {
  if (chunk.page_number !== null) {
    return `Page ${chunk.page_number}, chunk ${chunk.chunk_index}`;
  }
  return `Chunk ${chunk.chunk_index}`;
}

function SourceContextChunk({
  chunk,
  label,
  isSelected = false,
}: {
  chunk: DocumentChunk;
  label: string;
  isSelected?: boolean;
}) {
  return (
    <section className={isSelected ? "sourceChunk selected" : "sourceChunk"}>
      <div className="sourceChunkHeader">
        <strong>{label}</strong>
        <span>{formatChunkLocation(chunk)}</span>
      </div>
      <p>{chunk.text}</p>
    </section>
  );
}

export function ChatWorkspace() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evidencePreviews, setEvidencePreviews] = useState<Record<string, EvidencePreviewState>>({});

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.conversation_id === selectedConversationId) ?? null,
    [conversations, selectedConversationId],
  );

  async function loadMessages(conversationId: string) {
    setIsLoadingMessages(true);
    setError(null);
    try {
      const nextMessages = await fetchConversationMessages(conversationId);
      setMessages(nextMessages);
      setEvidencePreviews({});
    } catch (loadError) {
      setMessages([]);
      setEvidencePreviews({});
      setError(loadError instanceof Error ? loadError.message : "Failed to load messages.");
    } finally {
      setIsLoadingMessages(false);
    }
  }

  async function refreshConversations(preferredConversationId?: string) {
    const nextConversations = await fetchConversations();
    setConversations(nextConversations);
    const nextSelectedId = preferredConversationId ?? nextConversations[0]?.conversation_id ?? null;
    setSelectedConversationId(nextSelectedId);
    if (nextSelectedId) {
      await loadMessages(nextSelectedId);
    } else {
      setMessages([]);
      setEvidencePreviews({});
    }
  }

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoadingConversations(true);
      setError(null);
      try {
        const nextConversations = await fetchConversations();
        if (!isMounted) {
          return;
        }
        setConversations(nextConversations);
        const nextSelectedId = nextConversations[0]?.conversation_id ?? null;
        setSelectedConversationId(nextSelectedId);
        if (nextSelectedId) {
          const nextMessages = await fetchConversationMessages(nextSelectedId);
          if (isMounted) {
            setMessages(nextMessages);
          }
        }
      } catch (loadError) {
        if (isMounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load conversations.");
        }
      } finally {
        if (isMounted) {
          setIsLoadingConversations(false);
        }
      }
    }

    void load();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleCreateConversation() {
    setIsCreating(true);
    setError(null);
    try {
      const conversation = await createConversation();
      setConversations((currentConversations) => [conversation, ...currentConversations]);
      setSelectedConversationId(conversation.conversation_id);
      setMessages([]);
      setEvidencePreviews({});
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create conversation.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleSelectConversation(conversationId: string) {
    if (conversationId === selectedConversationId) {
      return;
    }
    setSelectedConversationId(conversationId);
    await loadMessages(conversationId);
  }

  async function handleDeleteConversation() {
    if (!selectedConversation) {
      return;
    }
    const shouldDelete = window.confirm(`Delete conversation "${selectedConversation.title}"?`);
    if (!shouldDelete) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    try {
      await deleteConversation(selectedConversation.conversation_id);
      const remainingConversations = conversations.filter(
        (conversation) => conversation.conversation_id !== selectedConversation.conversation_id,
      );
      setConversations(remainingConversations);
      const nextSelectedId = remainingConversations[0]?.conversation_id ?? null;
      setSelectedConversationId(nextSelectedId);
      if (nextSelectedId) {
        await loadMessages(nextSelectedId);
      } else {
        setMessages([]);
        setEvidencePreviews({});
      }
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete conversation.");
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleToggleEvidencePreview(evidence: MessageEvidence) {
    const currentPreview = evidencePreviews[evidence.evidence_id];
    if (currentPreview?.isOpen) {
      setEvidencePreviews((currentPreviews) => ({
        ...currentPreviews,
        [evidence.evidence_id]: {
          ...(currentPreviews[evidence.evidence_id] ?? {}),
          isOpen: false,
        },
      }));
      return;
    }

    setEvidencePreviews((currentPreviews) => ({
      ...currentPreviews,
      [evidence.evidence_id]: {
        ...(currentPreviews[evidence.evidence_id] ?? {}),
        isOpen: true,
        isLoading: !currentPreviews[evidence.evidence_id]?.context,
        error: undefined,
      },
    }));

    if (currentPreview?.context) {
      return;
    }

    try {
      const context = await fetchDocumentChunkContext(evidence.document_id, evidence.chunk_id);
      setEvidencePreviews((currentPreviews) => ({
        ...currentPreviews,
        [evidence.evidence_id]: {
          ...(currentPreviews[evidence.evidence_id] ?? {}),
          context,
          isLoading: false,
        },
      }));
    } catch (previewError) {
      setEvidencePreviews((currentPreviews) => ({
        ...currentPreviews,
        [evidence.evidence_id]: {
          ...(currentPreviews[evidence.evidence_id] ?? {}),
          isLoading: false,
          error: previewError instanceof Error ? previewError.message : "Failed to load source context.",
        },
      }));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setError("Ask a question before sending.");
      return;
    }

    setIsSending(true);
    setError(null);
    try {
      let conversationId = selectedConversationId;
      if (!conversationId) {
        const conversation = await createConversation();
        conversationId = conversation.conversation_id;
        setConversations((currentConversations) => [conversation, ...currentConversations]);
        setSelectedConversationId(conversationId);
      }

      const turn = await postConversationMessage(conversationId, trimmedQuestion);
      setMessages((currentMessages) => [
        ...currentMessages,
        turn.user_message,
        turn.assistant_message,
      ]);
      setQuestion("");
      await refreshConversations(conversationId);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Failed to send message.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="workspace chatWorkspace" aria-label="PaperLens chat workspace">
      <div className="workspaceHeader">
        <div>
          <p className="eyebrow">Milestone 11</p>
          <h2>Evidence chat</h2>
          <p className="sectionText">
            Ask over chunked local documents, then open evidence cards to inspect page-aware source context.
          </p>
        </div>
        <div className="statusPill">
          <span aria-hidden="true" />
          Chat API
        </div>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      <div className="chatLayout">
        <aside className="conversationPanel" aria-label="Conversations">
          <div className="conversationPanelHeader">
            <h3>Conversations</h3>
            <button type="button" onClick={() => void handleCreateConversation()} disabled={isCreating}>
              {isCreating ? "Creating..." : "New"}
            </button>
          </div>

          {isLoadingConversations ? <p className="conversationHint">Loading conversations...</p> : null}
          {!isLoadingConversations && conversations.length === 0 ? (
            <div className="conversationEmpty">
              <strong>No conversations yet.</strong>
              <p>Start one, then ask about evidence from chunked documents.</p>
            </div>
          ) : null}

          <div className="conversationList">
            {conversations.map((conversation) => (
              <button
                type="button"
                className={
                  conversation.conversation_id === selectedConversationId
                    ? "conversationItem selected"
                    : "conversationItem"
                }
                key={conversation.conversation_id}
                onClick={() => void handleSelectConversation(conversation.conversation_id)}
              >
                <span>{conversation.title}</span>
                <small>{formatDate(conversation.updated_at)}</small>
              </button>
            ))}
          </div>
        </aside>

        <div className="chatPanel">
          <div className="chatPanelHeader">
            <div>
              <h3>{selectedConversation?.title ?? "New conversation"}</h3>
              <p>{selectedConversation ? formatDate(selectedConversation.updated_at) : "Ready to start"}</p>
            </div>
            <button
              type="button"
              className="dangerButton"
              onClick={() => void handleDeleteConversation()}
              disabled={!selectedConversation || isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </div>

          <div className="messageList" aria-live="polite">
            {isLoadingMessages ? <p className="emptyState">Loading messages...</p> : null}
            {!isLoadingMessages && messages.length === 0 ? (
              <div className="emptyState">
                <strong>No messages yet.</strong>
                <p>Prepare a document first, then ask using terms that appear in the extracted text.</p>
              </div>
            ) : null}

            {messages.map((message) => (
              <article className={`messageBubble ${message.role}`} key={message.message_id}>
                <div className="messageMeta">
                  <strong>{getMessageLabel(message)}</strong>
                  <span>{formatDate(message.created_at)}</span>
                </div>
                <p>{message.content}</p>

                {message.role === "assistant" && message.evidence.length > 0 ? (
                  <div className="evidenceList" aria-label="Retrieved evidence">
                    {message.evidence.map((evidence) => {
                      const preview = evidencePreviews[evidence.evidence_id];
                      const context = preview?.context;
                      const documentLabel = context?.document.original_filename ?? evidence.document_id.slice(0, 8);

                      return (
                        <article
                          className={preview?.isOpen ? "evidenceCard expanded" : "evidenceCard"}
                          key={evidence.evidence_id}
                        >
                          <button
                            type="button"
                            className="evidenceSummary"
                            onClick={() => void handleToggleEvidencePreview(evidence)}
                            aria-expanded={Boolean(preview?.isOpen)}
                            aria-controls={`evidence-context-${evidence.evidence_id}`}
                          >
                            <span>
                              <strong>Evidence {evidence.rank}</strong>
                              <small>{documentLabel}</small>
                            </span>
                            <span className="evidenceScore">Score {formatScore(evidence.score)}</span>
                          </button>
                          <p className="evidenceExcerpt">{evidence.excerpt}</p>
                          <dl>
                            <div>
                              <dt>Document</dt>
                              <dd>{evidence.document_id.slice(0, 8)}</dd>
                            </div>
                            <div>
                              <dt>Page</dt>
                              <dd>{evidence.page_number ?? "N/A"}</dd>
                            </div>
                            <div>
                              <dt>Chunk</dt>
                              <dd>{evidence.chunk_id.slice(0, 8)}</dd>
                            </div>
                          </dl>

                          {preview?.isOpen ? (
                            <div className="sourcePreviewPanel" id={`evidence-context-${evidence.evidence_id}`}>
                              {preview.isLoading ? (
                                <p className="sourcePreviewStatus">Loading source context...</p>
                              ) : null}
                              {preview.error ? <div className="alert error">{preview.error}</div> : null}

                              {context ? (
                                <>
                                  <div className="sourcePreviewHeader">
                                    <div>
                                      <strong>{context.document.original_filename}</strong>
                                      <span>{context.document.title}</span>
                                    </div>
                                    <span>{formatChunkLocation(context.selected_chunk)}</span>
                                  </div>

                                  <dl className="sourceMetaGrid">
                                    <div>
                                      <dt>Document id</dt>
                                      <dd>{context.document.id.slice(0, 8)}</dd>
                                    </div>
                                    <div>
                                      <dt>Chunk id</dt>
                                      <dd>{context.selected_chunk.chunk_id.slice(0, 8)}</dd>
                                    </div>
                                    <div>
                                      <dt>Page</dt>
                                      <dd>{context.selected_chunk.page_number ?? "N/A"}</dd>
                                    </div>
                                    <div>
                                      <dt>Page offsets</dt>
                                      <dd>
                                        {context.selected_chunk.page_start !== null &&
                                        context.selected_chunk.page_end !== null
                                          ? `${context.selected_chunk.page_start}-${context.selected_chunk.page_end}`
                                          : "N/A"}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Offsets</dt>
                                      <dd>
                                        {context.selected_chunk.char_start}-{context.selected_chunk.char_end}
                                      </dd>
                                    </div>
                                    <div>
                                      <dt>Estimated tokens</dt>
                                      <dd>{context.selected_chunk.estimated_token_count}</dd>
                                    </div>
                                  </dl>

                                  <div className="sourceContextList">
                                    {context.previous_chunks.map((chunk) => (
                                      <SourceContextChunk
                                        chunk={chunk}
                                        label="Previous context"
                                        key={chunk.chunk_id}
                                      />
                                    ))}
                                    <SourceContextChunk
                                      chunk={context.selected_chunk}
                                      label="Retrieved chunk"
                                      isSelected
                                    />
                                    {context.next_chunks.map((chunk) => (
                                      <SourceContextChunk chunk={chunk} label="Next context" key={chunk.chunk_id} />
                                    ))}
                                    {context.previous_chunks.length === 0 && context.next_chunks.length === 0 ? (
                                      <p className="sourcePreviewStatus">No neighboring chunks are available.</p>
                                    ) : null}
                                  </div>
                                </>
                              ) : null}
                            </div>
                          ) : null}
                        </article>
                      );
                    })}
                  </div>
                ) : null}
                {message.role === "assistant" && message.evidence.length === 0 ? (
                  <div className="noEvidenceHint">
                    Prepare documents from the library, then ask with words that appear in those chunks.
                  </div>
                ) : null}
              </article>
            ))}
          </div>

          <form className="messageComposer" onSubmit={handleSubmit}>
            <label htmlFor="chat-question">Question</label>
            <div className="messageComposerControls">
              <textarea
                id="chat-question"
                value={question}
                placeholder="Ask about a method, result, limitation, or claim"
                onChange={(event) => setQuestion(event.target.value)}
                rows={3}
              />
              <button type="submit" disabled={isSending}>
                {isSending ? "Sending..." : "Send"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
