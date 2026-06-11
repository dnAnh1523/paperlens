"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  PaperLensDocument,
  deleteDocument,
  fetchDocuments,
  fetchHealth,
  uploadDocument,
} from "../../lib/api";

type ApiState = "checking" | "online" | "offline";

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

  const documentCountLabel = useMemo(() => {
    if (documents.length === 1) {
      return "1 document";
    }
    return `${documents.length} documents`;
  }, [documents.length]);

  async function refreshDocuments() {
    const nextDocuments = await fetchDocuments();
    setDocuments(nextDocuments);
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
  }, []);

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

  return (
    <section className="workspace" aria-label="PaperLens document workspace">
      <div className="workspaceHeader">
        <div>
          <p className="eyebrow">Milestone 2</p>
          <h2>Document library</h2>
          <p className="sectionText">
            Upload papers into local storage and verify that the FastAPI document endpoints are wired into
            the interface.
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
        {documents.map((document) => (
          <article className="documentCard" key={document.id}>
            <div>
              <div className="documentMetaLine">
                <span className="kindBadge">{getDocumentKind(document)}</span>
                <span className="statusBadge">{document.status}</span>
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
              </dl>
            </div>
            <button type="button" className="dangerButton" onClick={() => void handleDelete(document)}>
              Delete
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
