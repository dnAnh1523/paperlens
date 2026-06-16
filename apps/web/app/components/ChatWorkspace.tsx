"use client";

import {
  FormEvent,
  KeyboardEvent,
  UIEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ArrowDown,
  ArrowUp,
  Check,
  Copy,
  LoaderCircle,
  Pencil,
  Quote,
  Square,
} from "lucide-react";


import {
  ChatMessage,
  Conversation,
  EvidenceSourceChunk,
  MessageEvidence,
  MessageEvidenceSource,
  fetchAnswerProviderStatus,
  fetchConversationMessages,
  fetchConversations,
  fetchMessageEvidenceSource,
  postConversationMessage,
  updateConversationMessage,
  updateConversation,
} from "../../lib/api";

type EvidencePreviewState = {
  isOpen: boolean;
  isLoading?: boolean;
  source?: MessageEvidenceSource;
  error?: string;
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatChunkLocation(chunk: EvidenceSourceChunk): string {
  if (chunk.page_number !== null) {
    return `p. ${chunk.page_number}`;
  }
  return "Source passage";
}

function getMessageLabel(message: ChatMessage): string {
  return message.role === "user" ? "You" : "PaperLens";
}

// MessageRoleIcon removed as avatars are disabled for a cleaner, minimalist layout.


function formatAnswerProvenance(message: ChatMessage): string | null {
  const provenance = message.answer_provenance;
  if (!provenance) {
    return null;
  }

  const parts = [`Provider: ${provenance.provider_name}`];
  if (provenance.model_name) {
    parts.push(`model: ${provenance.model_name}`);
  }
  if (provenance.fallback_used) {
    parts.push("fallback used");
  }
  return parts.join(" | ");
}

function CitationDetail({ preview }: { preview: EvidencePreviewState }) {
  if (preview.isLoading) {
    return (
      <p className="citationDetailStatus">
        <LoaderCircle aria-hidden="true" className="inlineIcon spinIcon" />
        Loading source context...
      </p>
    );
  }

  if (preview.error) {
    return <div className="inlineNotice error">{preview.error}</div>;
  }

  const source = preview.source;
  if (!source) {
    return <p className="citationDetailStatus">Source context is unavailable.</p>;
  }

  return (
    <div className="citationDetail">
      <div className="citationDetailHeader">
        <div>
          <strong>{source.document.original_filename}</strong>
          <span>{formatChunkLocation(source.selected_chunk)}</span>
        </div>
        <span className={source.source_status === "live" ? "sourceState live" : "sourceState snapshot"}>
          {source.source_status === "live" ? "Live" : "Snapshot"}
        </span>
      </div>
      {source.note ? <p className="citationNote">{source.note}</p> : null}
      <p className="citationChunkText">{source.selected_chunk.text}</p>
      {source.previous_chunks.length > 0 || source.next_chunks.length > 0 ? (
        <details className="nearbyContext">
          <summary>Nearby context</summary>
          {source.previous_chunks.map((chunk) => (
            <p key={`previous-${chunk.chunk_id}`}>
              <strong>Before:</strong> {chunk.text}
            </p>
          ))}
          {source.next_chunks.map((chunk) => (
            <p key={`next-${chunk.chunk_id}`}>
              <strong>After:</strong> {chunk.text}
            </p>
          ))}
        </details>
      ) : null}
    </div>
  );
}

type ChatWorkspaceProps = {
  activeWorkspace: Conversation | null;
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>;
  activeWorkspaceId: string | null;
};

export function ChatWorkspace({
  activeWorkspace,
  setConversations,
  activeWorkspaceId,
}: ChatWorkspaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [providerStatusError, setProviderStatusError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidencePreviews, setEvidencePreviews] = useState<Record<string, EvidencePreviewState>>({});
  const [showScrollLatest, setShowScrollLatest] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");
  const [regeneratingUserMessageId, setRegeneratingUserMessageId] = useState<string | null>(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editTitleValue, setEditTitleValue] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const editRef = useRef<HTMLTextAreaElement | null>(null);
  const messageListRef = useRef<HTMLDivElement | null>(null);
  const shouldAutoScrollRef = useRef(true);
  const activeRequestRef = useRef<AbortController | null>(null);

  const handleSaveWorkspaceTitle = async () => {
    if (!activeWorkspace || !editTitleValue.trim() || editTitleValue.trim() === activeWorkspace.title) {
      setIsEditingTitle(false);
      return;
    }
    try {
      const updated = await updateConversation(activeWorkspace.conversation_id, {
        title: editTitleValue.trim()
      });
      setConversations((current) =>
        current.map((c) => (c.conversation_id === activeWorkspace.conversation_id ? updated : c))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rename workspace.");
    } finally {
      setIsEditingTitle(false);
    }
  };

  const canSend = question.trim().length > 0 && !isSending;

  const handleEditTextareaInput = useCallback((element: HTMLTextAreaElement) => {
    element.style.height = "auto";
    element.style.height = `${element.scrollHeight}px`;
  }, []);

  useEffect(() => {
    if (editingMessageId && editRef.current) {
      editRef.current.focus();
      const len = editRef.current.value.length;
      editRef.current.setSelectionRange(len, len);
      handleEditTextareaInput(editRef.current);
    }
  }, [editingMessageId, handleEditTextareaInput]);

  useEffect(() => {
    if (!question && textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [question]);

  useEffect(() => {
    return () => {
      activeRequestRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const container = messageListRef.current;
    if (!container) {
      return;
    }

    if (shouldAutoScrollRef.current) {
      requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
        setShowScrollLatest(false);
      });
    } else {
      setShowScrollLatest(messages.length > 0);
    }
  }, [messages.length, isLoadingMessages]);

  const loadMessages = useCallback(async (conversationId: string) => {
    shouldAutoScrollRef.current = true;
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
  }, []);

  useEffect(() => {
    if (activeWorkspaceId) {
      void loadMessages(activeWorkspaceId);
    } else {
      setMessages([]);
    }
  }, [activeWorkspaceId, loadMessages]);

  useEffect(() => {
    let isMounted = true;

    async function loadProviderStatus() {
      setProviderStatusError(null);
      try {
        await fetchAnswerProviderStatus();
      } catch (loadError) {
        if (isMounted) {
          setProviderStatusError(
            loadError instanceof Error ? loadError.message : "Failed to load provider status.",
          );
        }
      }
    }

    void loadProviderStatus();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleToggleEvidencePreview(message: ChatMessage, evidence: MessageEvidence) {
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
        isLoading: !currentPreviews[evidence.evidence_id]?.source,
        error: undefined,
      },
    }));

    if (currentPreview?.source) {
      return;
    }

    try {
      const source = await fetchMessageEvidenceSource(
        message.conversation_id,
        message.message_id,
        evidence.evidence_id,
      );
      setEvidencePreviews((currentPreviews) => ({
        ...currentPreviews,
        [evidence.evidence_id]: {
          ...(currentPreviews[evidence.evidence_id] ?? {}),
          source,
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
    if (!trimmedQuestion || isSending || !activeWorkspaceId) {
      return;
    }

    setIsSending(true);
    setError(null);
    const controller = new AbortController();
    activeRequestRef.current = controller;
    try {
      const turn = await postConversationMessage(activeWorkspaceId, trimmedQuestion, 5, controller.signal);
      shouldAutoScrollRef.current = true;
      setMessages((currentMessages) => [
        ...currentMessages,
        turn.user_message,
        turn.assistant_message,
      ]);
      setQuestion("");
      setEvidencePreviews({});
      
      // Sync conversations list to fetch updated titles derived from the first prompt
      const nextConversations = await fetchConversations();
      setConversations(nextConversations);
    } catch (sendError) {
      if (sendError instanceof Error && sendError.name === "AbortError") {
        setError(null);
        return;
      }
      setError(sendError instanceof Error ? sendError.message : "Failed to send message.");
    } finally {
      activeRequestRef.current = null;
      setIsSending(false);
    }
  }

  async function handleCopyMessage(message: ChatMessage) {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopiedMessageId(message.message_id);
      window.setTimeout(() => {
        setCopiedMessageId((currentMessageId) =>
          currentMessageId === message.message_id ? null : currentMessageId,
        );
      }, 1400);
    } catch {
      setError("Could not copy message.");
    }
  }

  function handleEditMessage(message: ChatMessage) {
    setEditingMessageId(message.message_id);
    setEditingText(message.content);
  }

  function handleCancelEdit() {
    setEditingMessageId(null);
    setEditingText("");
  }

  function handleEditKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      handleCancelEdit();
    } else if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (editingText.trim().length > 0 && !isSending) {
        void handleSubmitEdit();
      }
    }
  }

  async function handleSubmitEdit() {
    if (!editingMessageId || editingText.trim().length === 0 || isSending || !activeWorkspaceId) {
      return;
    }

    const targetMessageId = editingMessageId;
    const targetContent = editingText.trim();

    setEditingMessageId(null);
    setEditingText("");

    setIsSending(true);
    setRegeneratingUserMessageId(targetMessageId);
    setError(null);

    const controller = new AbortController();
    activeRequestRef.current = controller;

    try {
      const turn = await updateConversationMessage(
        activeWorkspaceId,
        targetMessageId,
        targetContent,
        5,
        controller.signal,
      );

      setMessages((currentMessages) => {
        const nextMessages = [...currentMessages];
        const userIndex = nextMessages.findIndex((m) => m.message_id === targetMessageId);
        if (userIndex !== -1) {
          nextMessages[userIndex] = turn.user_message;
          const nextMsg = nextMessages[userIndex + 1];
          if (nextMsg && nextMsg.role === "assistant") {
            nextMessages[userIndex + 1] = turn.assistant_message;
          } else {
            nextMessages.splice(userIndex + 1, 0, turn.assistant_message);
          }
        }
        return nextMessages;
      });

      const nextConversations = await fetchConversations();
      setConversations(nextConversations);
    } catch (sendError) {
      if (sendError instanceof Error && sendError.name === "AbortError") {
        setError(null);
        return;
      }
      setError(sendError instanceof Error ? sendError.message : "Failed to update message.");
    } finally {
      activeRequestRef.current = null;
      setIsSending(false);
      setRegeneratingUserMessageId(null);
    }
  }

  function handleStopResponse() {
    activeRequestRef.current?.abort();
    activeRequestRef.current = null;
    setIsSending(false);
  }

  function handleComposerInput(element: HTMLTextAreaElement) {
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 176)}px`;
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }
    event.preventDefault();
    if (canSend) {
      event.currentTarget.form?.requestSubmit();
    }
  }

  function handleMessageScroll(event: UIEvent<HTMLDivElement>) {
    const container = event.currentTarget;
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    const isNearBottom = distanceFromBottom < 96;
    shouldAutoScrollRef.current = isNearBottom;
    setShowScrollLatest(!isNearBottom && messages.length > 0);
  }

  function scrollToLatest() {
    const container = messageListRef.current;
    if (!container) {
      return;
    }
    shouldAutoScrollRef.current = true;
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    setShowScrollLatest(false);
  }

  const showEmptyState = !isLoadingMessages && messages.length === 0;

  return (
    <section className={showEmptyState ? "chat-shell empty-state" : "chat-shell active-state"} aria-label="Chat workspace">
      {/* Top Header - Minimalist, borderless, no bulky badges */}
      {!showEmptyState && (
        <header className="chat-active-header">
          <div className="chat-breadcrumb">
            <span className="breadcrumb-main">Workspace</span>
            <span className="breadcrumb-separator">/</span>
            {isEditingTitle ? (
              <input
                type="text"
                className="workspace-title-input"
                value={editTitleValue}
                onChange={(e) => setEditTitleValue(e.target.value)}
                onBlur={handleSaveWorkspaceTitle}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    void handleSaveWorkspaceTitle();
                  } else if (e.key === "Escape") {
                    setIsEditingTitle(false);
                  }
                }}
                autoFocus
              />
            ) : (
              <span 
                className="breadcrumb-sub editable"
                onClick={() => {
                  setIsEditingTitle(true);
                  setEditTitleValue(activeWorkspace?.title || "");
                }}
                title="Click to rename workspace"
              >
                {activeWorkspace?.title || "Active Workspace"}
              </span>
            )}
          </div>
        </header>
      )}

      {showEmptyState ? (
        /* Centered Empty State */
        <div className="chat-centered-empty">
          <div className="empty-content-wrapper">
            <h1 className="empty-title">Chat with your sources</h1>
            <p className="empty-subtitle">Retrieving evidence across isolated workspaces.</p>
            
            <form className="chat-composer-centered" onSubmit={handleSubmit}>
              <textarea
                aria-label="Question"
                ref={textareaRef}
                value={question}
                placeholder="Ask across your prepared sources"
                onChange={(event) => {
                  setQuestion(event.target.value);
                  handleComposerInput(event.currentTarget);
                }}
                onKeyDown={handleComposerKeyDown}
                rows={1}
                style={{ minHeight: 46, maxHeight: 176 }}
              />
              <button
                type={isSending ? "button" : "submit"}
                className={isSending ? "composerActionButton stopping" : "composerActionButton"}
                aria-label={isSending ? "Stop response" : "Send question"}
                onClick={isSending ? handleStopResponse : undefined}
                disabled={!isSending && !canSend}
              >
                {isSending ? (
                  <Square aria-hidden="true" className="buttonIcon stopIcon" />
                ) : (
                  <ArrowUp aria-hidden="true" className="buttonIcon" />
                )}
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Active Chat State */
        <>
          {providerStatusError ? <div className="inlineNotice error">{providerStatusError}</div> : null}
          {error ? <div className="inlineNotice error">{error}</div> : null}

          <div
            className="chat-messages"
            aria-live="polite"
            onScroll={handleMessageScroll}
            ref={messageListRef}
          >
            {isLoadingMessages ? (
              <p className="chatState">
                <LoaderCircle aria-hidden="true" className="inlineIcon spinIcon" />
                Opening chat...
              </p>
            ) : null}

            {messages.map((message, index) => {
              const isRegenerating =
                message.role === "assistant" &&
                index > 0 &&
                messages[index - 1].message_id === regeneratingUserMessageId;

              if (isRegenerating) {
                return (
                  <article className="messageRow assistant pending" key={message.message_id}>
                    <div className="messageContentCol">
                      <div className="messageHeader">
                        <strong className="messageSenderName">PaperLens</strong>
                      </div>
                      <div className="thinkingBubble">
                        <LoaderCircle aria-hidden="true" className="inlineIcon spinIcon" />
                        Reading sources...
                      </div>
                    </div>
                  </article>
                );
              }

              const isEditing = message.role === "user" && editingMessageId === message.message_id;

              return (
                <article className={`messageRow ${message.role}`} key={message.message_id}>
                  <div className="messageContentCol">
                    {!isEditing && (
                      <div className="messageHeader">
                        <strong className="messageSenderName">{getMessageLabel(message)}</strong>
                        <span className="messageTimestamp">{formatDate(message.created_at)}</span>
                        {message.role === "assistant" && formatAnswerProvenance(message) ? (
                          <span className="answerProvenance">{formatAnswerProvenance(message)}</span>
                        ) : null}
                      </div>
                    )}

                    <div className="messageBubble">
                      {isEditing ? (
                        <div className="messageEditContainer">
                           <textarea
                            ref={editRef}
                            value={editingText}
                            onChange={(e) => {
                              setEditingText(e.target.value);
                              handleEditTextareaInput(e.currentTarget);
                            }}
                            onKeyDown={handleEditKeyDown}
                            className="messageEditTextarea"
                            rows={1}
                          />
                          <div className="messageEditActions">
                            <button
                              type="button"
                              className="messageEditCancelButton"
                              onClick={handleCancelEdit}
                            >
                              Cancel
                            </button>
                            <button
                              type="button"
                              className="messageEditSubmitButton"
                              onClick={() => void handleSubmitEdit()}
                              disabled={editingText.trim().length === 0 || isSending}
                              aria-label="Submit edit"
                            >
                              <ArrowUp className="buttonIcon" />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p>{message.content}</p>
                      )}

                      {message.role === "assistant" && message.evidence.length > 0 ? (
                        <div className="citationBlock" aria-label="Retrieved citations">
                          <div className="citationChips">
                            {message.evidence.map((evidence) => {
                              const preview = evidencePreviews[evidence.evidence_id];
                              const pageLabel = evidence.page_number === null ? null : `p. ${evidence.page_number}`;
                              const filename = evidence.document_filename_snapshot;

                              return (
                                <button
                                  type="button"
                                  className={preview?.isOpen ? "citationChip open" : "citationChip"}
                                  key={evidence.evidence_id}
                                  onClick={() => void handleToggleEvidencePreview(message, evidence)}
                                  aria-expanded={Boolean(preview?.isOpen)}
                                >
                                  <Quote aria-hidden="true" className="buttonIcon" />
                                  Source {evidence.rank}
                                  {pageLabel ? <span>{pageLabel}</span> : null}
                                  {filename ? <small>{filename}</small> : null}
                                </button>
                              );
                            })}
                          </div>
                          {message.evidence.map((evidence) => {
                            const preview = evidencePreviews[evidence.evidence_id];
                            if (!preview?.isOpen) {
                              return null;
                            }
                            return (
                              <CitationDetail
                                key={`detail-${evidence.evidence_id}`}
                                preview={preview}
                              />
                            );
                          })}
                        </div>
                      ) : null}

                      {message.role === "assistant" && message.evidence.length === 0 ? (
                        <div className="noEvidenceHint">
                          No matching evidence was returned. Add sources to this workspace to ground your answers.
                        </div>
                      ) : null}
                    </div>

                    {!isEditing && (
                      <div className="messageActions" aria-label="Message actions">
                        <button
                          type="button"
                          className="messageActionButton"
                          aria-label="Copy message"
                          onClick={() => void handleCopyMessage(message)}
                        >
                          {copiedMessageId === message.message_id ? (
                            <Check aria-hidden="true" />
                          ) : (
                            <Copy aria-hidden="true" />
                          )}
                        </button>
                        {message.role === "user" && (
                          <button
                            type="button"
                            className="messageActionButton"
                            aria-label="Edit message"
                            onClick={() => handleEditMessage(message)}
                            disabled={isSending}
                          >
                            <Pencil aria-hidden="true" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </article>
              );
            })}

            {isSending && !regeneratingUserMessageId ? (
              <article className="messageRow assistant pending">
                <div className="messageContentCol">
                  <div className="messageHeader">
                    <strong className="messageSenderName">PaperLens</strong>
                  </div>
                  <div className="thinkingBubble">
                    <LoaderCircle aria-hidden="true" className="inlineIcon spinIcon" />
                    Reading sources...
                  </div>
                </div>
              </article>
            ) : null}
          </div>
          <div className="chat-messages-fade" />

          {showScrollLatest ? (
            <button type="button" className="scrollLatestButton" onClick={scrollToLatest}>
              <ArrowDown aria-hidden="true" className="buttonIcon" />
              Latest
            </button>
          ) : null}

          <form className="chat-composer" onSubmit={handleSubmit}>
            <textarea
              aria-label="Question"
              ref={textareaRef}
              value={question}
              placeholder="Ask across your prepared sources"
              onChange={(event) => {
                setQuestion(event.target.value);
                handleComposerInput(event.currentTarget);
              }}
              onKeyDown={handleComposerKeyDown}
              rows={1}
              style={{ minHeight: 46, maxHeight: 176 }}
            />
            <button
              type={isSending ? "button" : "submit"}
              className={isSending ? "composerActionButton stopping" : "composerActionButton"}
              aria-label={isSending ? "Stop response" : "Send question"}
              onClick={isSending ? handleStopResponse : undefined}
              disabled={!isSending && !canSend}
            >
              {isSending ? (
                <Square aria-hidden="true" className="buttonIcon stopIcon" />
              ) : (
                <ArrowUp aria-hidden="true" className="buttonIcon" />
              )}
            </button>
          </form>
        </>
      )}
    </section>
  );
}
