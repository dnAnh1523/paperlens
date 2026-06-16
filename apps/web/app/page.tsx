"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Plus, Trash2, MessageSquare, Clock, Files, LoaderCircle, AlertCircle, Pencil } from "lucide-react";
import { ChatWorkspace } from "./components/ChatWorkspace";
import { DocumentLibrary } from "./components/DocumentLibrary";
import { 
  PaperLensDocument, 
  Conversation, 
  fetchConversations, 
  deleteConversation, 
  createConversation,
  fetchDocuments,
  updateConversation
} from "../lib/api";

import { PaperLensLogo } from "./components/PaperLensLogo";

export default function HomePage() {
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<PaperLensDocument[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [clearingWorkspaces, setClearingWorkspaces] = useState(false);
  const [editingWorkspaceId, setEditingWorkspaceId] = useState<string | null>(null);
  const [editingWorkspaceTitle, setEditingWorkspaceTitle] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmClearAll, setConfirmClearAll] = useState(false);
  const confirmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [convs, docs] = await Promise.all([
        fetchConversations(),
        fetchDocuments(activeWorkspaceId || undefined)
      ]);
      setConversations(convs);
      setDocuments(docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.");
    } finally {
      setIsLoading(false);
    }
  }, [activeWorkspaceId]);

  useEffect(() => {
    let ignore = false;
    const init = async () => {
      try {
        const convs = await fetchConversations();
        if (ignore) return;
        setConversations(convs);
      } catch (err) {
        if (ignore) return;
        setError(err instanceof Error ? err.message : "Failed to load data.");
      } finally {
        if (ignore) return;
        setIsLoading(false);
      }
    };
    void init();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!activeWorkspaceId) {
      Promise.resolve().then(() => {
        setDocuments([]);
      });
      return;
    }
    let ignore = false;
    const loadWorkspaceDocuments = async () => {
      try {
        const docs = await fetchDocuments(activeWorkspaceId);
        if (ignore) return;
        setDocuments(docs);
      } catch (err) {
        if (ignore) return;
        console.error("Failed to load workspace documents:", err);
      }
    };
    void loadWorkspaceDocuments();
    return () => {
      ignore = true;
    };
  }, [activeWorkspaceId]);

  const handleCreateWorkspace = async () => {
    try {
      setCreatingWorkspace(true);
      const newWs = await createConversation("None Title Workspace", undefined, []);
      setConversations((current) => [newWs, ...current]);
      setActiveWorkspaceId(newWs.conversation_id);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create workspace.");
    } finally {
      setCreatingWorkspace(false);
    }
  };

  const handleDeleteWorkspace = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setConfirmDeleteId(id);
    // Auto-dismiss the confirm after 5 seconds if no action
    if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
    confirmTimeoutRef.current = setTimeout(() => setConfirmDeleteId(null), 5000);
  };

  const handleConfirmDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
    setConfirmDeleteId(null);
    setDeletingId(id);
    try {
      await deleteConversation(id);
      setConversations((current) => current.filter((c) => c.conversation_id !== id));
      if (activeWorkspaceId === id) {
        setActiveWorkspaceId(null);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete workspace.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
    setConfirmDeleteId(null);
  };

  const handleClearAllWorkspaces = () => {
    if (conversations.length === 0) return;
    setConfirmClearAll(true);
  };

  const handleConfirmClearAll = async () => {
    setConfirmClearAll(false);
    try {
      setClearingWorkspaces(true);
      await Promise.all(conversations.map((conv) => deleteConversation(conv.conversation_id)));
      setConversations([]);
      setActiveWorkspaceId(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to clear workspaces.");
    } finally {
      setClearingWorkspaces(false);
    }
  };

  const handleToggleSourceAssociation = async (docId: string) => {
    if (!activeWorkspaceId) return;
    const ws = conversations.find(c => c.conversation_id === activeWorkspaceId);
    if (!ws) return;

    const currentIds = ws.source_document_ids || [];
    const updatedIds = currentIds.includes(docId)
      ? currentIds.filter(id => id !== docId)
      : [...currentIds, docId];

    try {
      const updatedWs = await updateConversation(activeWorkspaceId, {
        source_document_ids: updatedIds
      });
      setConversations((current) =>
        current.map((c) => (c.conversation_id === activeWorkspaceId ? updatedWs : c))
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update workspace sources.");
    }
  };

  const handleSaveWorkspaceTitleCard = async (conversationId: string) => {
    if (!editingWorkspaceTitle.trim()) {
      setEditingWorkspaceId(null);
      return;
    }
    try {
      const updated = await updateConversation(conversationId, {
        title: editingWorkspaceTitle.trim()
      });
      setConversations((current) =>
        current.map((c) => (c.conversation_id === conversationId ? updated : c))
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to rename workspace.");
    } finally {
      setEditingWorkspaceId(null);
    }
  };

  const activeWorkspace = conversations.find(c => c.conversation_id === activeWorkspaceId) || null;

  if (isLoading && conversations.length === 0) {
    return (
      <div className="dashboard-loading">
        <LoaderCircle className="spinIcon" size={48} />
        <p>Loading your workspaces...</p>
      </div>
    );
  }

  // Dashboard view
  if (!activeWorkspaceId) {
    return (
      <div className="dashboard-shell">
        <header className="dashboard-header">
          <div className="dashboard-logo-container" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PaperLensLogo style={{ width: '1.8rem', height: 'auto', color: 'var(--primary)' }} />
            <span className="sidebarLogo" style={{ fontSize: "1.6rem", fontWeight: 800, margin: 0 }}>
              PaperLens<span className="logoDot">+</span>
            </span>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {conversations.length > 0 && (
              confirmClearAll ? (
                <div className="delete-confirm-inline">
                  <span className="delete-confirm-label">Clear all {conversations.length} workspaces?</span>
                  <button
                    type="button"
                    className="delete-confirm-yes"
                    disabled={clearingWorkspaces}
                    onClick={() => void handleConfirmClearAll()}
                  >
                    {clearingWorkspaces ? <LoaderCircle className="spinIcon" size={13} /> : "Yes"}
                  </button>
                  <button
                    type="button"
                    className="delete-confirm-no"
                    onClick={() => setConfirmClearAll(false)}
                  >
                    No
                  </button>
                </div>
              ) : (
                <button 
                  type="button" 
                  className="clear-all-workspaces-btn"
                  onClick={handleClearAllWorkspaces}
                  disabled={clearingWorkspaces}
                >
                  {clearingWorkspaces ? (
                    <LoaderCircle className="spinIcon" size={16} />
                  ) : (
                    <Trash2 size={16} />
                  )}
                  <span style={{ marginLeft: '6px' }}>Clear All Workspaces</span>
                </button>
              )
            )}
          </div>
        </header>

        <main className="dashboard-main">
          <div className="dashboard-welcome">
            <h1 className="dashboard-title">Chat with your sources</h1>
            <p className="dashboard-subtitle">
              Retrieving evidence across isolated workspaces. Select or create a workspace to begin.
            </p>
          </div>

          {error && (
            <div className="dashboard-error-notice">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          <div className="dashboard-grid">
            {/* Create new card */}
            <div 
              className={`dashboard-card create-card${creatingWorkspace ? ' disabled' : ''}`}
              onClick={creatingWorkspace ? undefined : handleCreateWorkspace}
              style={creatingWorkspace ? { opacity: 0.6, pointerEvents: 'none' } : undefined}
            >
              <div className="create-card-content">
                {creatingWorkspace ? (
                  <LoaderCircle size={36} className="spinIcon create-icon" />
                ) : (
                  <Plus size={36} className="create-icon" />
                )}
                <span>{creatingWorkspace ? 'Creating...' : 'Create New Chat'}</span>
              </div>
            </div>

            {/* List existing workspaces */}
            {conversations.map((conv) => {
              const sourceCount = conv.source_document_ids?.length || 0;
              const associatedDocs = documents.filter(d => 
                conv.source_document_ids?.includes(d.id)
              );

              return (
                <div 
                  key={conv.conversation_id} 
                  className="dashboard-card workspace-card"
                  onClick={() => setActiveWorkspaceId(conv.conversation_id)}
                >
                  <div className="workspace-card-header">
                    <MessageSquare size={20} className="chat-icon" />
                    <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                      {confirmDeleteId === conv.conversation_id ? (
                        <div
                          className="delete-confirm-inline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <span className="delete-confirm-label">Delete?</span>
                          <button
                            type="button"
                            className="delete-confirm-yes"
                            onClick={(e) => void handleConfirmDelete(conv.conversation_id, e)}
                          >
                            {deletingId === conv.conversation_id ? (
                              <LoaderCircle size={13} className="spinIcon" />
                            ) : "Yes"}
                          </button>
                          <button
                            type="button"
                            className="delete-confirm-no"
                            onClick={handleCancelDelete}
                          >
                            No
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="edit-workspace-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingWorkspaceId(conv.conversation_id);
                              setEditingWorkspaceTitle(conv.title);
                            }}
                            title="Rename Workspace"
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            type="button"
                            className="delete-workspace-btn"
                            onClick={(e) => handleDeleteWorkspace(conv.conversation_id, e)}
                            title="Delete Workspace"
                          >
                            <Trash2 size={16} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {editingWorkspaceId === conv.conversation_id ? (
                    <input
                      type="text"
                      className="workspace-card-title-input"
                      value={editingWorkspaceTitle}
                      onChange={(e) => setEditingWorkspaceTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onBlur={() => handleSaveWorkspaceTitleCard(conv.conversation_id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          void handleSaveWorkspaceTitleCard(conv.conversation_id);
                        } else if (e.key === "Escape") {
                          setEditingWorkspaceId(null);
                        }
                      }}
                      autoFocus
                    />
                  ) : (
                    <h3 className="workspace-card-title">{conv.title}</h3>
                  )}

                  <div className="workspace-card-meta">
                    <div className="meta-item">
                      <Clock size={14} />
                      <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                    </div>
                    <div className="meta-item">
                      <Files size={14} />
                      <span>{sourceCount} {sourceCount === 1 ? "source" : "sources"}</span>
                    </div>
                  </div>

                  {associatedDocs.length > 0 && (
                    <div className="workspace-card-sources">
                      {associatedDocs.slice(0, 3).map(doc => (
                        <span key={doc.id} className="source-mini-badge" title={doc.original_filename}>
                          {doc.title || doc.original_filename}
                        </span>
                      ))}
                      {associatedDocs.length > 3 && (
                        <span className="source-mini-badge more">+{associatedDocs.length - 3} more</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </main>
      </div>
    );
  }

  // Active Workspace / Chat view
  return (
    <main className={isSidebarOpen ? "appShell" : "appShell sidebar-collapsed"}>
      <DocumentLibrary
        activeWorkspace={activeWorkspace}
        documents={documents}
        onSelectDocument={() => {}}
        onToggleSourceAssociation={handleToggleSourceAssociation}
        onRefreshSources={loadData}
        onNavigateHome={() => setActiveWorkspaceId(null)}
        isOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />
      <ChatWorkspace
        activeWorkspace={activeWorkspace}
        setConversations={setConversations}
        activeWorkspaceId={activeWorkspaceId}
      />
    </main>
  );
}
