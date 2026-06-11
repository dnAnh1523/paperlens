"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  IngestionJob,
  IngestionTextPreview,
  PaperLensDocument,
  createDocumentChunks,
  deleteDocument,
  fetchDocumentChunks,
  fetchDocumentIngestion,
  fetchDocumentTextPreview,
  fetchDocuments,
  fetchHealth,
  triggerDocumentIngestion,
  uploadDocument,
} from "../../lib/api";

type ApiState = "checking" | "online" | "offline";
type WorkflowAction = "ingesting" | "chunking" | "preparing";

type DocumentWorkflowState = {
  ingestion?: IngestionJob;
  preview?: IngestionTextPreview;
  chunkCount?: number;
  isLoading?: boolean;
  action?: WorkflowAction;
  workflowError?: string;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[unitIndex]}`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function getDocumentKind(document: PaperLensDocument): string {
  if (document.content_type === "application/pdf") {
    return "PDF";
  }
  if (document.content_type.startsWith("image/")) {
    return "Image";
  }
  if (document.content_type.includes("markdown")) {
    return "Markdown";
  }
  if (document.content_type.startsWith("text/")) {
    return "Text";
  }
  if (document.content_type.includes("csv")) {
    return "CSV";
  }
  return document.content_type;
}

export function DocumentLibrary() {
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [documents, setDocuments] = useState<PaperLensDocument[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [workflowStates, setWorkflowStates] = useState<Record<string, DocumentWorkflowState>>({});

  const documentCountLabel = useMemo(() => {
    if (documents.length === 1) {
      return "1 document";
    }
    return `${documents.length} documents`;
  }, [documents.length]);

  const updateWorkflowState = useCallback((documentId: string, nextState: Partial<DocumentWorkflowState>) => {
    setWorkflowStates((currentStates) => ({
      ...currentStates,
      [documentId]: {
        ...currentStates[documentId],
        ...nextState,
      },
    }));
  }, []);

  const loadWorkflowState = useCallback(async (documentId: string) => {
    updateWorkflowState(documentId, { isLoading: true, workflowError: undefined });
    const [ingestionResult, chunksResult, previewResult] = await Promise.allSettled([
      fetchDocumentIngestion(documentId),
      fetchDocumentChunks(documentId),
      fetchDocumentTextPreview(documentId),
    ]);

    updateWorkflowState(documentId, {
      ingestion: ingestionResult.status === "fulfilled" ? ingestionResult.value : undefined,
      chunkCount: chunksResult.status === "fulfilled" ? chunksResult.value.length : 0,
      preview: previewResult.status === "fulfilled" ? previewResult.value : undefined,
      isLoading: false,
      workflowError:
        ingestionResult.status === "rejected" && ingestionResult.reason instanceof Error
          ? ingestionResult.reason.message
          : undefined,
    });
  }, [updateWorkflowState]);

  const loadWorkflowStates = useCallback(async (nextDocuments: PaperLensDocument[]) => {
    await Promise.all(nextDocuments.map((document) => loadWorkflowState(document.id)));
  }, [loadWorkflowState]);

  async function refreshDocuments() {
    const nextDocuments = await fetchDocuments();
    setDocuments(nextDocuments);
    await loadWorkflowStates(nextDocuments);
  }

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        await fetchHealth();
        if (!isMounted) {
          return;
        }
        setApiState("online");
        const nextDocuments = await fetchDocuments();
        if (!isMounted) {
          return;
        }
        setDocuments(nextDocuments);
        await loadWorkflowStates(nextDocuments);
      } catch (loadError) {
        if (!isMounted) {
          return;
        }
        setApiState("offline");
        setError(loadError instanceof Error ? loadError.message : "Failed to connect to the API.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      isMounted = false;
    };
  }, [loadWorkflowStates]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setError("Choose a file before uploading.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const uploadedDocument = await uploadDocument(selectedFile);
      setSelectedFile(null);
      const input = event.currentTarget.elements.namedItem("paper-file") as HTMLInputElement | null;
      if (input) {
        input.value = "";
      }
      await refreshDocuments();
      setSuccessMessage(`Uploaded ${uploadedDocument.original_filename}.`);
      setApiState("online");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(document: PaperLensDocument) {
    const shouldDelete = window.confirm(`Delete ${document.original_filename}?`);
    if (!shouldDelete) {
      return;
    }

    setError(null);
    setSuccessMessage(null);
    try {
      await deleteDocument(document.id);
      setDocuments((currentDocuments) => currentDocuments.filter((item) => item.id !== document.id));
      setSuccessMessage(`Deleted ${document.original_filename}.`);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Delete failed.");
    }
  }

  async function handleIngest(document: PaperLensDocument) {
    updateWorkflowState(document.id, { action: "ingesting", workflowError: undefined });
    setError(null);
    setSuccessMessage(null);
    try {
      const job = await triggerDocumentIngestion(document.id);
      await loadWorkflowState(document.id);
      setSuccessMessage(
        job.status === "completed"
          ? `Ingested ${document.original_filename}.`
          : `Ingestion finished with status ${job.status}.`,
      );
    } catch (ingestError) {
      const message = ingestError instanceof Error ? ingestError.message : "Ingestion failed.";
      updateWorkflowState(document.id, { workflowError: message });
      setError(message);
    } finally {
      updateWorkflowState(document.id, { action: undefined });
    }
  }

  async function handleChunk(document: PaperLensDocument) {
    updateWorkflowState(document.id, { action: "chunking", workflowError: undefined });
    setError(null);
    setSuccessMessage(null);
    try {
      const chunks = await createDocumentChunks(document.id);
      await loadWorkflowState(document.id);
      setSuccessMessage(`Created ${chunks.length} chunks for ${document.original_filename}.`);
    } catch (chunkError) {
      const message = chunkError instanceof Error ? chunkError.message : "Chunking failed.";
      updateWorkflowState(document.id, { workflowError: message });
      setError(message);
    } finally {
      updateWorkflowState(document.id, { action: undefined });
    }
  }

  async function handlePrepare(document: PaperLensDocument) {
    updateWorkflowState(document.id, { action: "preparing", workflowError: undefined });
    setError(null);
    setSuccessMessage(null);
    try {
      const job = await triggerDocumentIngestion(document.id);
      if (job.status !== "completed") {
        throw new Error(job.error_message ?? `Ingestion ended with status ${job.status}.`);
      }
      const chunks = await createDocumentChunks(document.id);
      await refreshDocuments();
      setSuccessMessage(`Prepared ${document.original_filename} with ${chunks.length} searchable chunks.`);
    } catch (prepareError) {
      const message = prepareError instanceof Error ? prepareError.message : "Document preparation failed.";
      updateWorkflowState(document.id, { workflowError: message });
      setError(message);
      await loadWorkflowState(document.id);
    } finally {
      updateWorkflowState(document.id, { action: undefined });
    }
  }

  return (
    <section className="workspace" aria-label="PaperLens document workspace">
      <div className="workspaceHeader">
        <div>
          <p className="eyebrow">Milestone 7</p>
          <h2>Document library</h2>
          <p className="sectionText">
            Upload a local source file, prepare extracted text and chunks, then ask evidence-preview
            questions in chat.
          </p>
        </div>
        <div className={`statusPill ${apiState}`}>
          <span aria-hidden="true" />
          API {apiState}
        </div>
      </div>

      <form className="uploadPanel" onSubmit={handleUpload}>
        <label htmlFor="paper-file">Upload a paper or source file</label>
        <div className="uploadControls">
          <input
            id="paper-file"
            name="paper-file"
            type="file"
            accept=".pdf,.txt,.md,.csv,image/png,image/jpeg,image/webp"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
          <button type="submit" disabled={isUploading || apiState === "offline"}>
            {isUploading ? "Uploading..." : "Upload"}
          </button>
        </div>
        <p className="hint">API base URL: {API_BASE_URL}</p>
      </form>

      {error ? <div className="alert error">{error}</div> : null}
      {successMessage ? <div className="alert success">{successMessage}</div> : null}

      <div className="libraryHeader">
        <h3>{documentCountLabel}</h3>
        <button type="button" className="secondaryButton" onClick={() => void refreshDocuments()} disabled={isLoading}>
          Refresh
        </button>
      </div>

      {isLoading ? <p className="emptyState">Loading documents...</p> : null}

      {!isLoading && documents.length === 0 ? (
        <div className="emptyState">
          <strong>No documents yet.</strong>
          <p>Upload a small PDF, Markdown file, text file, CSV, or image to test the local document flow.</p>
        </div>
      ) : null}

      <div className="documentList">
        {documents.map((document) => {
          const workflow = workflowStates[document.id];
          const action = workflow?.action;
          const isBusy = Boolean(action || workflow?.isLoading);
          const chunkCount = workflow?.chunkCount ?? 0;

          return (
            <article className="documentCard workflowCard" key={document.id}>
              <div className="documentMetaLine">
                <span className="kindBadge">{getDocumentKind(document)}</span>
                <span className="statusBadge">{document.status}</span>
                {workflow?.ingestion ? (
                  <span className="statusBadge">ingestion {workflow.ingestion.status}</span>
                ) : null}
              </div>
              <h4>{document.title}</h4>
              <p>{document.original_filename}</p>
              <dl>
                <div>
                  <dt>Size</dt>
                  <dd>{formatBytes(document.file_size_bytes)}</dd>
                </div>
                <div>
                  <dt>Uploaded</dt>
                  <dd>{formatDate(document.created_at)}</dd>
                </div>
                <div>
                  <dt>SHA-256</dt>
                  <dd>{document.sha256.slice(0, 16)}...</dd>
                </div>
                <div>
                  <dt>Chunks</dt>
                  <dd>{workflow?.isLoading ? "Checking..." : `${chunkCount} ready`}</dd>
                </div>
              </dl>

              <div className="workflowPanel">
                <div className="workflowActions">
                  <button
                    type="button"
                    className="secondaryButton"
                    onClick={() => void handleIngest(document)}
                    disabled={isBusy}
                  >
                    {action === "ingesting" ? "Ingesting..." : "Ingest / retry"}
                  </button>
                  <button
                    type="button"
                    className="secondaryButton"
                    onClick={() => void handleChunk(document)}
                    disabled={isBusy}
                  >
                    {action === "chunking" ? "Chunking..." : "Chunk / rechunk"}
                  </button>
                  <button type="button" onClick={() => void handlePrepare(document)} disabled={isBusy}>
                    {action === "preparing" ? "Preparing..." : "Prepare document"}
                  </button>
                  <button
                    type="button"
                    className="dangerButton"
                    onClick={() => void handleDelete(document)}
                    disabled={isBusy}
                  >
                    Delete
                  </button>
                </div>

                {workflow?.workflowError ? <div className="alert error">{workflow.workflowError}</div> : null}

                {workflow?.preview ? (
                  <div className="previewPanel">
                    <div className="previewHeader">
                      <strong>Extracted text preview</strong>
                      <span>
                        {workflow.preview.preview_characters} of {workflow.preview.total_characters} chars
                      </span>
                    </div>
                    <p>{workflow.preview.text}</p>
                  </div>
                ) : (
                  <p className="hint">
                    No extracted text preview yet. Ingest or prepare a text, Markdown, or text-layer PDF file.
                  </p>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
