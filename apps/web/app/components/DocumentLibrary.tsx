"use client";

import {
  DragEvent,
  FormEvent,
  MouseEvent,
  useRef,
  useState,
  useEffect
} from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  LoaderCircle,
  MoreVertical,
  PanelLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  Plus,
  Trash2,
  Upload,
  X,
  RotateCcw
} from "lucide-react";

import {
  PaperLensDocument,
  Conversation,
  uploadDocument,
  deleteDocument,
  updateDocumentTitle,
  triggerDocumentIngestion,
  createDocumentChunks
} from "../../lib/api";

const PaperLensLogo = ({ className, style }: { className?: string; style?: React.CSSProperties }) => (
  <svg
    viewBox="0 0 1319 1159"
    className={className}
    style={{
      width: "1.6rem",
      height: "auto",
      display: "inline-block",
      verticalAlign: "middle",
      fill: "currentColor",
      ...style,
    }}
  >
    <path
      fillRule="evenodd"
      d="m667 0.6c9.6 0.2 23.1 1.1 30 1.9 6.9 0.9 17.9 2.7 24.5 4 6.6 1.3 17.4 4 24 5.9 6.6 1.9 17.8 5.6 25 8.2 7.2 2.6 20.4 8.5 29.5 13 9.1 4.6 22.6 12.3 30 17.2 7.4 4.9 16.9 11.6 21.1 14.8 4.2 3.2 12.7 10.4 18.8 15.9 6.2 5.5 15.6 14.9 20.9 20.9 5.3 5.9 12.3 14.3 15.6 18.5 3.2 4.2 10.2 14.1 15.5 22.1 5.3 8 17.4 26.9 26.8 42 9.4 15.1 25.3 40.8 35.3 57 10.1 16.2 30.5 49.1 45.3 73 14.8 23.9 45.8 73.9 68.7 111 22.9 37.1 58 93.8 78 126 20 32.2 47 75.8 60 97 13 21.2 28.2 46.2 33.7 55.5 5.5 9.3 12.3 21.3 15.1 26.5 2.8 5.2 7.5 15.1 10.5 22 3 6.9 7 17.5 9 23.5 2 6 5 16.6 6.6 23.5 1.7 6.9 4 18.8 5.1 26.5 1.1 7.8 2.3 22.4 2.7 33 0.4 11.9 0.1 24.2-0.6 33-0.7 7.7-2.2 19-3.2 25-1.1 6-3.1 15.3-4.4 20.5-1.3 5.2-4.1 14.5-6.1 20.5-2 6-5.8 16.2-8.6 22.5-2.7 6.3-7.6 16.5-10.9 22.5-3.3 6-9.8 16.6-14.3 23.5-4.6 6.9-11.6 16.5-15.6 21.5-4.1 5-10.5 12.4-14.3 16.5-3.8 4.1-11.2 11.5-16.5 16.4-5.4 4.8-14.7 12.5-20.7 17.1-6 4.6-16.2 11.5-22.5 15.4-6.3 4-16.2 9.6-22 12.5-5.8 3-15.9 7.5-22.5 10.1-6.6 2.7-16.7 6.3-22.5 8-5.8 1.8-15.9 4.5-22.5 6-6.6 1.5-17.6 3.5-24.5 4.5-6.9 1-21.7 2.4-33 3-14.9 0.8-121 1-388 0.8-345.4-0.3-368.3-0.4-381-2.1-7.4-1-20-3.1-28-4.7-8-1.6-19.9-4.4-26.5-6.3-6.6-1.9-16.5-5.2-22-7.2-5.5-2-15.2-6.2-21.5-9.2-6.3-3-17.3-8.9-24.4-13.1-7.1-4.2-17.9-11.5-24.2-16.2-6.2-4.7-16.1-12.8-22-18-5.8-5.2-15.2-14.6-20.8-20.9-5.5-6.2-13.5-15.9-17.8-21.5-4.2-5.5-10.8-15.3-14.7-21.6-4-6.3-10-17.3-13.5-24.5-3.5-7.2-8.7-19.1-11.4-26.5-2.8-7.4-6.7-19.6-8.6-27-1.9-7.4-4.4-18.5-5.5-24.5-1.1-6-2.5-17.1-3.2-24.5-0.7-8.3-0.9-20.6-0.6-32 0.4-10.2 1.3-23 2.1-28.5 0.8-5.5 2.5-14.7 3.7-20.5 1.1-5.8 3.5-15 5.1-20.5 1.6-5.5 5-15.4 7.4-22 2.4-6.6 7.9-19.2 12.3-28 4.3-8.8 10.7-21 14.3-27 3.6-6 14.6-24.3 24.5-40.5 9.9-16.2 37.5-61 61.3-99.5 23.8-38.5 58.7-94.8 77.5-125 18.8-30.3 50.1-80.6 69.5-112 19.4-31.4 44.8-72.3 56.3-91 11.5-18.7 28.9-46.6 38.5-62 9.7-15.4 20.7-32.7 24.5-38.5 3.9-5.8 10.7-15.5 15.3-21.5 4.5-6 12.5-15.6 17.6-21.2 5.1-5.7 13.6-14.2 18.8-18.9 5.2-4.8 13.5-11.9 18.5-15.7 5-3.9 15.1-11 22.5-15.9 7.4-4.9 21.6-12.9 31.5-17.8 9.9-4.9 22.3-10.4 27.5-12.4 5.2-1.9 14.9-5.1 21.5-7.1 6.6-2 18.5-4.9 26.5-6.5 8-1.6 20.3-3.6 27.5-4.5 7.2-0.8 15.7-1.7 19-1.9 3.3-0.2 13.9-0.2 23.5 0zm-30.5 172c-4.4 0.8-12.5 2.8-18 4.5-5.5 1.7-14.7 5.5-20.5 8.5-5.8 2.9-14.1 7.9-18.5 11.1-4.4 3.3-11.4 9.2-15.4 13.3-4.1 4.1-10.2 10.9-13.4 15-3.3 4.1-9.5 12.7-13.7 19-4.2 6.3-16.6 25.7-27.5 43-10.9 17.3-31.9 51.1-46.8 75-14.8 23.9-55.9 89.6-91.2 146-35.3 56.4-77 123.2-92.7 148.5-15.7 25.3-40 64.5-54.1 87-14 22.5-27.8 45-30.6 50-2.9 5-7 12.7-9.1 17.2-2.2 4.6-5.5 12.7-7.4 18-1.8 5.4-3.9 12.3-4.5 15.3-0.6 3-1.5 9.8-2.1 15-0.6 6.2-0.6 13.1 0 20 0.6 5.8 2.1 14.8 3.5 20 1.4 5.2 5 14.5 7.9 20.5 3 6 8.1 14.6 11.3 19 3.3 4.4 10.1 11.9 15.1 16.7 5.1 4.9 13.1 11.4 18 14.5 4.8 3.1 11.8 7.1 15.7 8.9 3.9 1.8 10.6 4.3 15 5.7 4.4 1.4 13 3.3 19 4.4 10.6 1.7 25.8 1.8 383 1.8 298.9 0 373.8-0.3 381-1.3 5-0.7 13.3-2.4 18.5-3.8 5.2-1.4 14-4.6 19.5-7.2 5.5-2.7 13.6-7.2 17.9-10.2 4.4-3 11.4-8.9 15.5-13 4.2-4.1 10-10.7 12.9-14.5 2.9-3.8 8-12.4 11.3-19 3.7-7.7 6.8-15.6 8.4-22 1.4-5.5 3-14.7 3.5-20.5 0.5-6.3 0.5-14.7 0-21-0.5-5.8-2.1-15-3.5-20.5-1.5-5.5-4.4-14.3-6.6-19.5-2.3-5.2-7.3-15.1-11.1-22-3.9-6.9-19.5-32.5-34.6-57-15.1-24.5-46.5-74.9-69.7-112-23.2-37.1-59.9-95.6-81.5-130-21.6-34.4-65.2-103.9-96.8-154.5-31.6-50.6-60.5-96.5-64.2-102-3.7-5.5-9.4-13.4-12.7-17.5-3.3-4.1-9.8-11-14.4-15.4-4.6-4.3-12.4-10.5-17.4-13.8-5-3.3-12.2-7.6-16-9.5-3.8-2-11.5-5-17-6.9-5.5-1.8-14.3-4-19.5-4.9-5.7-0.9-15.3-1.5-24-1.4-8 0-18.1 0.7-22.5 1.5z"
    />
  </svg>
);

const MAX_SOURCES_PER_BATCH = 10;
const ACCEPTED_SOURCE_TYPES = ".pdf,.txt,.md,.csv,image/png,image/jpeg,image/webp";

type DocumentLibraryProps = {
  activeWorkspace: Conversation | null;
  documents: PaperLensDocument[];
  onSelectDocument: (document: PaperLensDocument) => void;
  onToggleSourceAssociation: (documentId: string) => void;
  onRefreshSources: () => Promise<void>;
  onNavigateHome: () => void;
  isOpen?: boolean;
  onToggleSidebar?: () => void;
};

type UploadQueueStatus = "queued" | "uploading" | "preparing" | "ready" | "failed";

type UploadQueueItem = {
  name: string;
  status: UploadQueueStatus;
  message?: string;
};

type SourceStatus = {
  label: string;
  tone: "ready" | "processing" | "needsPreparation" | "failed";
  isReady: boolean;
  isProcessing: boolean;
  canPrepare: boolean;
};

type SourceMenuState = {
  documentId: string;
  top: number;
  left: number;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[unitIndex]}`;
}

function getSourceLabel(document: PaperLensDocument): string {
  return document.title?.trim() || document.original_filename;
}

function getSourceStatus(document: PaperLensDocument): SourceStatus {
  const isProcessing = document.status === "processing";
  if (isProcessing) {
    return {
      label: "Processing",
      tone: "processing",
      isReady: false,
      isProcessing: true,
      canPrepare: false,
    };
  }

  const failed = document.status === "failed";
  if (failed) {
    return {
      label: "Failed",
      tone: "failed",
      isReady: false,
      isProcessing: false,
      canPrepare: true,
    };
  }

  if (document.status === "ready") {
    return {
      label: "Ready",
      tone: "ready",
      isReady: true,
      isProcessing: false,
      canPrepare: false,
    };
  }

  return {
    label: "Needs preparation",
    tone: "needsPreparation",
    isReady: false,
    isProcessing: false,
    canPrepare: true,
  };
}

function getFileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return FileText;
  if (ext === "csv") return FileSpreadsheet;
  if (ext === "png" || ext === "jpg" || ext === "jpeg" || ext === "webp") return FileImage;
  return File;
}

export function DocumentLibrary({
  activeWorkspace,
  documents,
  onToggleSourceAssociation,
  onRefreshSources,
  onNavigateHome,
  isOpen = true,
  onToggleSidebar,
}: DocumentLibraryProps) {
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);
  const widthRef = useRef(sidebarWidth);

  useEffect(() => {
    widthRef.current = sidebarWidth;
  }, [sidebarWidth]);

  useEffect(() => {
    const saved = localStorage.getItem("paperlens-sidebar-width");
    if (saved) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= 260 && parsed <= 480) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSidebarWidth(parsed);
      }
    }
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: globalThis.MouseEvent) => {
      const newWidth = e.clientX;
      const clampedWidth = Math.max(260, Math.min(480, newWidth));
      setSidebarWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      localStorage.setItem("paperlens-sidebar-width", widthRef.current.toString());
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [isAddSourceOpen, setIsAddSourceOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [sourceMenu, setSourceMenu] = useState<SourceMenuState | null>(null);
  const [renamingDocumentId, setRenamingDocumentId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [preparingDocId, setPreparingDocId] = useState<string | null>(null);
  const [isCollapseHovered, setIsCollapseHovered] = useState(false);
  const [isExpandHovered, setIsExpandHovered] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const renameInputRef = useRef<HTMLInputElement | null>(null);

  const activeMenuDocument =
    sourceMenu === null ? null : documents.find((doc) => doc.id === sourceMenu.documentId) ?? null;

  // Documents associated with the active workspace
  const workspaceDocIds = activeWorkspace?.source_document_ids || [];
  const associatedDocuments = documents.filter((doc) => workspaceDocIds.includes(doc.id));

  async function prepareDocument(document: PaperLensDocument) {
    setPreparingDocId(document.id);
    try {
      const job = await triggerDocumentIngestion(document.id);
      if (job.status !== "completed") {
        throw new Error(job.error_message ?? `Preparation ended with status ${job.status}.`);
      }
      await createDocumentChunks(document.id);
    } finally {
      setPreparingDocId(null);
    }
  }

  function closeAddSourceDialog() {
    setIsAddSourceOpen(false);
    setIsDraggingFile(false);
    setSelectedFiles([]);
    setUploadQueue([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function addSelectedFiles(fileList: FileList | File[]) {
    const incomingFiles = Array.from(fileList);
    if (incomingFiles.length === 0) return;

    setSelectedFiles((currentFiles) => {
      const nextFiles = [...currentFiles, ...incomingFiles].slice(0, MAX_SOURCES_PER_BATCH);
      if (currentFiles.length + incomingFiles.length > MAX_SOURCES_PER_BATCH) {
        setError(`Add up to ${MAX_SOURCES_PER_BATCH} sources at a time.`);
      } else {
        setError(null);
      }
      return nextFiles;
    });
    setUploadQueue([]);
  }

  function removeSelectedFile(index: number) {
    setSelectedFiles((currentFiles) => currentFiles.filter((_, fileIndex) => fileIndex !== index));
    setUploadQueue([]);
  }

  async function handleBatchUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedFiles.length === 0) {
      setError("Choose at least one source to add.");
      return;
    }

    const filesToUpload = selectedFiles.slice(0, MAX_SOURCES_PER_BATCH);
    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    let nextQueue: UploadQueueItem[] = filesToUpload.map((file) => ({
      name: file.name,
      status: "queued",
    }));
    setUploadQueue(nextQueue);

    function setQueueItem(index: number, nextItem: Partial<UploadQueueItem>) {
      nextQueue = nextQueue.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...nextItem } : item
      );
      setUploadQueue(nextQueue);
    }

    let addedCount = 0;
    let failedCount = 0;

    for (const [index, file] of filesToUpload.entries()) {
      try {
        setQueueItem(index, { status: "uploading", message: formatBytes(file.size) });
        const uploadedDocument = await uploadDocument(file, activeWorkspace?.conversation_id);
        
        // Auto-associate with the active workspace!
        if (activeWorkspace) {
          await onToggleSourceAssociation(uploadedDocument.id);
        }

        setQueueItem(index, { status: "preparing", message: "Extracting and chunking" });
        await prepareDocument(uploadedDocument);
        setQueueItem(index, { status: "ready", message: "Prepared" });
        addedCount += 1;
      } catch (uploadError) {
        const message = uploadError instanceof Error ? uploadError.message : "Upload failed.";
        setQueueItem(index, { status: "failed", message });
        failedCount += 1;
      }
    }

    await onRefreshSources();
    setIsUploading(false);

    if (failedCount === 0) {
      setSuccessMessage(`Added and prepared ${addedCount} ${addedCount === 1 ? "source" : "sources"}.`);
      closeAddSourceDialog();
    } else {
      setError(`Added ${addedCount} ${addedCount === 1 ? "source" : "sources"}. ${failedCount} need attention.`);
    }
  }

  async function handlePrepare(document: PaperLensDocument) {
    setSourceMenu(null);
    setError(null);
    setSuccessMessage(null);
    try {
      await prepareDocument(document);
      await onRefreshSources();
      setSuccessMessage(`Prepared ${document.original_filename}.`);
    } catch (prepareError) {
      const message = prepareError instanceof Error ? prepareError.message : "Document preparation failed.";
      setError(message);
    }
  }

  async function handleRename(document: PaperLensDocument) {
    const nextTitle = renameValue.trim();
    if (!nextTitle) {
      setError("Source name cannot be empty.");
      return;
    }

    setIsRenaming(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await updateDocumentTitle(document.id, nextTitle);
      await onRefreshSources();
      setRenamingDocumentId(null);
      setRenameValue("");
      setSuccessMessage(`Renamed source successfully.`);
    } catch (renameError) {
      setError(renameError instanceof Error ? renameError.message : "Rename failed.");
    } finally {
      setIsRenaming(false);
    }
  }

  async function handleDelete(document: PaperLensDocument) {
    setSourceMenu(null);
    const shouldDelete = window.confirm(`Delete ${document.original_filename}?`);
    if (!shouldDelete) return;

    setError(null);
    setSuccessMessage(null);
    try {
      await deleteDocument(document.id);
      await onRefreshSources();
      setSuccessMessage(`Deleted ${document.original_filename}.`);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Delete failed.");
    }
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDraggingFile(false);
    addSelectedFiles(event.dataTransfer.files);
  }

  function openSourceMenu(event: MouseEvent<HTMLButtonElement>, documentId: string) {
    event.stopPropagation();
    const rect = event.currentTarget.getBoundingClientRect();
    setSourceMenu({
      documentId,
      top: Math.min(rect.bottom + 6, window.innerHeight - 132),
      left: Math.min(Math.max(12, rect.right - 188), window.innerWidth - 200),
    });
  }

  function beginRename(document: PaperLensDocument) {
    setSourceMenu(null);
    setRenamingDocumentId(document.id);
    setRenameValue(getSourceLabel(document));
  }

  return (
    <aside
      className={`${isOpen ? "sourceSidebar" : "sourceSidebar collapsed"} ${isResizing ? "resizing" : ""}`}
      style={{ width: isOpen ? `${sidebarWidth}px` : undefined }}
      aria-label="Sidebar"
    >
      {/* 1. COLLAPSED STATE (Slim Pill Mode) */}
      <div className="miniSidebarContentWrapper">
        <button
          type="button"
          className="miniSidebarExpandButton tooltip-container"
          onClick={onToggleSidebar}
          aria-label="Expand sidebar"
          onMouseEnter={() => setIsExpandHovered(true)}
          onMouseLeave={() => setIsExpandHovered(false)}
        >
          {isExpandHovered ? (
            <PanelLeftOpen aria-hidden="true" className="buttonIcon" />
          ) : (
            <PanelLeft aria-hidden="true" className="buttonIcon" />
          )}
          <span className="tooltip-text">Expand sidebar</span>
        </button>

        <div className="miniSidebarActions">
          <button
            type="button"
            className="miniSidebarActionButton"
            onClick={() => {
              setIsAddSourceOpen(true);
              setError(null);
            }}
            title="Add Source"
          >
            <Plus aria-hidden="true" className="buttonIcon" />
          </button>
        </div>

        <div className="miniSidebarList">
          {associatedDocuments.map((doc) => {
            const sourceStatus = getSourceStatus(doc);
            const DocIcon = getFileIcon(doc.original_filename);

            return (
              <div 
                className="miniSidebarItem tooltip-container" 
                key={`mini-${doc.id}`}
                title={getSourceLabel(doc)}
              >
                <DocIcon aria-hidden="true" className="buttonIcon" />
                <span className={`mini-status-dot ${sourceStatus.tone}`} />
                <span className="tooltip-text">{getSourceLabel(doc)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. EXPANDED STATE */}
      <div className="sidebarContentWrapper">
        {/* Transparent Header Logo */}
        <div className="sourceBrand">
          <button 
            type="button" 
            className="sidebarLogoButton" 
            onClick={onNavigateHome}
            title="Go to Dashboard"
            style={{ background: 'transparent', border: 0, padding: 0, cursor: 'pointer', boxShadow: 'none' }}
          >
            <h1 className="sidebarLogo" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <PaperLensLogo style={{ width: '1.6rem', height: 'auto', color: 'var(--primary)' }} />
              <span>PaperLens<span className="logoDot">+</span></span>
            </h1>
          </button>

          <button
            type="button"
            className="sidebarCollapseButton tooltip-container"
            onClick={onToggleSidebar}
            aria-label="Collapse sidebar"
            onMouseEnter={() => setIsCollapseHovered(true)}
            onMouseLeave={() => setIsCollapseHovered(false)}
          >
            {isCollapseHovered ? (
              <PanelLeftClose aria-hidden="true" className="buttonIcon" />
            ) : (
              <PanelLeft aria-hidden="true" className="buttonIcon" />
            )}
            <span className="tooltip-text">Collapse sidebar</span>
          </button>
        </div>

        {/* Section 2: Detailed Source Manager (Checkboxes) */}
        <div className="sidebar-section" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div className="sidebarActions" style={{ marginBottom: 12 }}>
            <button
              type="button"
              className="addSourceButton"
              onClick={() => {
                setIsAddSourceOpen(true);
                setError(null);
              }}
            >
              <Plus aria-hidden="true" className="buttonIcon" />
              Add Source
            </button>
          </div>

          {error && <div className="inlineNotice error" style={{ marginBottom: 12 }}>{error}</div>}
          {successMessage && <div className="inlineNotice success" style={{ marginBottom: 12 }}>{successMessage}</div>}

          <div className="sourceListHeader">
            <span>Sources in Workspace</span>
            <span className="sidebarClearAll">{associatedDocuments.length} active</span>
          </div>

          <div className="sourceList" style={{ flex: 1 }}>
            {documents.length === 0 ? (
              <div className="sourceEmpty">
                <strong>No sources yet</strong>
                <p>Upload a document source to associate it with this workspace.</p>
              </div>
            ) : (
              documents.map((doc) => {
                const sourceStatus = getSourceStatus(doc);
                const isAssociated = workspaceDocIds.includes(doc.id);
                const isBusy = preparingDocId === doc.id;
                const sourceLabel = getSourceLabel(doc);
                const isRenamingSource = renamingDocumentId === doc.id;

                return (
                  <div className={`sourceRow ${isAssociated ? "selected" : ""}`} key={doc.id}>
                    {isRenamingSource ? (
                      <form
                        className="sourceRenameForm"
                        onSubmit={(e) => {
                          e.preventDefault();
                          void handleRename(doc);
                        }}
                      >
                        <input
                          ref={renameInputRef}
                          value={renameValue}
                          aria-label="Rename source"
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Escape") {
                              setRenamingDocumentId(null);
                              setRenameValue("");
                            }
                          }}
                          disabled={isRenaming}
                        />
                        <button type="submit" disabled={isRenaming}>Save</button>
                        <button
                          type="button"
                          className="quietButton"
                          onClick={() => {
                            setRenamingDocumentId(null);
                            setRenameValue("");
                          }}
                          disabled={isRenaming}
                        >
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <>
                        <div className="sourceCheckboxWrapper">
                          <input
                            type="checkbox"
                            className="sourceCheckbox"
                            id={`assoc-${doc.id}`}
                            checked={isAssociated}
                            onChange={() => onToggleSourceAssociation(doc.id)}
                            disabled={isBusy}
                          />
                        </div>

                        <button
                          type="button"
                          className="sourceSelectButton"
                          onClick={() => onToggleSourceAssociation(doc.id)}
                          style={{ paddingLeft: 4 }}
                        >
                          <FileText aria-hidden="true" className="sourceGlyph" />
                          <span className="sourceRowText">
                            <span className="sourceRowTitle">{sourceLabel}</span>
                            <span className="sourceRowMeta">
                              {sourceStatus.isReady ? "Prepared" : formatBytes(doc.file_size_bytes)}
                            </span>
                          </span>
                          <span className="sourceStatusSlot" aria-label={sourceStatus.label}>
                            {isBusy || sourceStatus.tone === "processing" ? (
                              <LoaderCircle aria-hidden="true" className="sourceStatusIcon processing spinIcon" />
                            ) : sourceStatus.tone === "ready" ? (
                              <CheckCircle2 aria-hidden="true" className="sourceStatusIcon ready" />
                            ) : sourceStatus.tone === "failed" ? (
                              <AlertTriangle aria-hidden="true" className="sourceStatusIcon failed" />
                            ) : (
                              <Clock3 aria-hidden="true" className="sourceStatusIcon needsPreparation" />
                            )}
                          </span>
                        </button>

                        <button
                          type="button"
                          className="sourceMenuButton"
                          aria-label={`Actions for ${sourceLabel}`}
                          aria-expanded={sourceMenu?.documentId === doc.id}
                          onClick={(e) => openSourceMenu(e, doc.id)}
                          disabled={isBusy}
                        >
                          <MoreVertical aria-hidden="true" />
                        </button>
                      </>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Source Menu popup */}
      {sourceMenu && activeMenuDocument && (
        <div className="sourceMenuLayer" onClick={() => setSourceMenu(null)}>
          <div
            className="sourceMenu"
            style={{ top: sourceMenu.top, left: sourceMenu.left }}
            onClick={(e) => e.stopPropagation()}
          >
            <button type="button" onClick={() => beginRename(activeMenuDocument)}>
              <Pencil aria-hidden="true" className="buttonIcon" />
              Rename source
            </button>
            {getSourceStatus(activeMenuDocument).canPrepare && (
              <button type="button" onClick={() => void handlePrepare(activeMenuDocument)}>
                <RotateCcw aria-hidden="true" className="buttonIcon" />
                Prepare source
              </button>
            )}
            <button
              type="button"
              className="sourceMenuDanger"
              onClick={() => void handleDelete(activeMenuDocument)}
            >
              <Trash2 aria-hidden="true" className="buttonIcon" />
              Delete source
            </button>
          </div>
        </div>
      )}

      {/* Batch Upload Modal */}
      {isAddSourceOpen && (
        <div
          className="modalLayer"
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget && !isUploading) {
              closeAddSourceDialog();
            }
          }}
        >
          <section className="addSourceDialog" role="dialog" aria-modal="true" aria-labelledby="add-source-title">
            <div className="dialogHeader">
              <div>
                <h2 id="add-source-title">Add Source</h2>
                <p>Drop up to {MAX_SOURCES_PER_BATCH} files. PaperLens uploads and indexes them globally.</p>
              </div>
              <button
                type="button"
                className="iconButton"
                aria-label="Close add source dialog"
                onClick={closeAddSourceDialog}
                disabled={isUploading}
              >
                <X aria-hidden="true" />
              </button>
            </div>

            <form onSubmit={handleBatchUpload} className="addSourceForm">
              <input
                ref={fileInputRef}
                className="fileInput"
                id="paper-files"
                name="paper-files"
                type="file"
                multiple
                accept={ACCEPTED_SOURCE_TYPES}
                onChange={(e) => addSelectedFiles(e.target.files ?? [])}
              />
              <label
                className={isDraggingFile ? "modalDropzone dragging" : "modalDropzone"}
                htmlFor="paper-files"
                onDragLeave={() => setIsDraggingFile(false)}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDraggingFile(true);
                }}
                onDrop={handleDrop}
              >
                <Upload aria-hidden="true" className="modalDropzoneIcon" />
                <strong>Drag files here or click to browse</strong>
                <span>PDF, Markdown, text, CSV, PNG, JPG, or WebP</span>
              </label>

              {selectedFiles.length > 0 && (
                <div className="selectedFiles">
                  {selectedFiles.map((file, index) => (
                    <div className="selectedFileRow" key={`${file.name}-${file.lastModified}-${index}`}>
                      <FileText aria-hidden="true" className="sourceGlyph" />
                      <span>{file.name}</span>
                      <small>{formatBytes(file.size)}</small>
                      <button
                        type="button"
                        className="iconButton"
                        aria-label={`Remove ${file.name}`}
                        onClick={() => removeSelectedFile(index)}
                        disabled={isUploading}
                      >
                        <X aria-hidden="true" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {uploadQueue.length > 0 && (
                <div className="uploadQueue" aria-live="polite">
                  {uploadQueue.map((item) => (
                    <div className={`uploadQueueRow ${item.status}`} key={item.name}>
                      {item.status === "ready" ? (
                        <CheckCircle2 aria-hidden="true" className="sourceStatusIcon ready" />
                      ) : item.status === "failed" ? (
                        <AlertTriangle aria-hidden="true" className="sourceStatusIcon failed" />
                      ) : (
                        <LoaderCircle aria-hidden="true" className="sourceStatusIcon processing spinIcon" />
                      )}
                      <span>{item.name}</span>
                      <small>{item.message ?? item.status}</small>
                    </div>
                  ))}
                </div>
              )}

              <div className="dialogActions">
                <button type="button" className="quietButton" onClick={closeAddSourceDialog} disabled={isUploading}>
                  Cancel
                </button>
                <button type="submit" disabled={isUploading || selectedFiles.length === 0}>
                  {isUploading ? (
                    <LoaderCircle aria-hidden="true" className="buttonIcon spinIcon" />
                  ) : (
                    <Upload aria-hidden="true" className="buttonIcon" />
                  )}
                  {isUploading ? "Uploading" : "Add selected"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}

      {isOpen && (
        <div
          className="sidebarResizer"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
        />
      )}
    </aside>
  );
}
