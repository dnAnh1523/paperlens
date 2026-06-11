"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  ChatMessage,
  Conversation,
  createConversation,
  deleteConversation,
  fetchConversationMessages,
  fetchConversations,
  postConversationMessage,
} from "../../lib/api";

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
    } catch (loadError) {
      setMessages([]);
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
      }
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete conversation.");
    } finally {
      setIsDeleting(false);
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
          <p className="eyebrow">Milestone 7</p>
          <h2>Evidence chat</h2>
          <p className="sectionText">
            Ask over chunked local documents and inspect the deterministic evidence preview from FastAPI.
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
                    {message.evidence.map((evidence) => (
                      <div className="evidenceCard" key={evidence.evidence_id}>
                        <div className="evidenceHeader">
                          <strong>Evidence {evidence.rank}</strong>
                          <span>Score {formatScore(evidence.score)}</span>
                        </div>
                        <p>{evidence.excerpt}</p>
                        <dl>
                          <div>
                            <dt>Document</dt>
                            <dd>{evidence.document_id.slice(0, 8)}</dd>
                          </div>
                          <div>
                            <dt>Chunk</dt>
                            <dd>{evidence.chunk_id.slice(0, 8)}</dd>
                          </div>
                        </dl>
                      </div>
                    ))}
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
