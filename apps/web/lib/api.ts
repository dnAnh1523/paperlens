export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export type ApiHealth = {
  status: string;
  service: string;
};

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export type PaperLensDocument = {
  id: string;
  title: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  sha256: string;
  storage_path: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
};

export type IngestionJobStatus = "pending" | "running" | "completed" | "failed";

export type IngestionJob = {
  id: string;
  document_id: string;
  status: IngestionJobStatus;
  stage: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type IngestionTextPreview = {
  document_id: string;
  text: string;
  total_characters: number;
  preview_characters: number;
};

export type DocumentChunk = {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  char_start: number;
  char_end: number;
  page_number: number | null;
  page_start: number | null;
  page_end: number | null;
  source_kind: string | null;
  source_path: string | null;
  estimated_token_count: number;
  created_at: string;
};

export type ChunkContextDocument = {
  id: string;
  title: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
};

export type DocumentChunkContext = {
  document: ChunkContextDocument;
  selected_chunk: DocumentChunk;
  previous_chunks: DocumentChunk[];
  next_chunks: DocumentChunk[];
};

export type EvidenceSourceDocument = {
  id: string;
  title: string;
  original_filename: string;
};

export type EvidenceSourceChunk = {
  chunk_id: string;
  document_id: string;
  chunk_index: number | null;
  text: string;
  char_start: number | null;
  char_end: number | null;
  page_number: number | null;
  page_start: number | null;
  page_end: number | null;
  estimated_token_count: number | null;
};

export type Conversation = {
  conversation_id: string;
  title: string;
  scoped_document_id: string | null;
  scoped_document: {
    id: string;
    title: string;
    original_filename: string;
  } | null;
  source_document_ids: string[] | null;
  created_at: string;
  updated_at: string;
};

export type MessageRole = "user" | "assistant";

export type MessageEvidence = {
  evidence_id: string;
  message_id: string;
  document_id: string;
  chunk_id: string;
  rank: number;
  score: number;
  excerpt: string;
  full_chunk_text_snapshot: string | null;
  document_title_snapshot: string | null;
  document_filename_snapshot: string | null;
  chunk_index_snapshot: number | null;
  char_start_snapshot: number | null;
  char_end_snapshot: number | null;
  page_number: number | null;
  page_start: number | null;
  page_end: number | null;
  estimated_token_count_snapshot: number | null;
};

export type MessageEvidenceSource = {
  source_status: "live" | "snapshot";
  is_stale: boolean;
  note: string | null;
  evidence: MessageEvidence;
  document: EvidenceSourceDocument;
  selected_chunk: EvidenceSourceChunk;
  previous_chunks: EvidenceSourceChunk[];
  next_chunks: EvidenceSourceChunk[];
};

export type AnswerProvenance = {
  provider_name: string;
  provider_type: "deterministic" | "free-tier-api" | "local-model" | "openai-compatible" | "unknown";
  model_name: string | null;
  fallback_used: boolean;
  fallback_reason: string | null;
};

export type ChatMessage = {
  message_id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  answer_provenance: AnswerProvenance | null;
  evidence: MessageEvidence[];
};

export type ChatTurn = {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
};

export type AnswerProviderStatus = {
  provider_name: string;
  provider_type: "deterministic" | "free-tier-api" | "local-model" | "openai-compatible" | "unknown";
  display_name: string;
  model_name: string | null;
  base_url_host: string | null;
  is_default: boolean;
  is_available: boolean;
  requires_api_key: boolean;
  requires_network: boolean;
  requires_model_download: boolean;
  supports_streaming: boolean;
  status_message: string;
};

async function parseError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    return JSON.stringify(payload.detail ?? payload);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<ApiHealth> {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json() as Promise<ApiHealth>;
}

export async function fetchAnswerProviderStatus(): Promise<AnswerProviderStatus> {
  const response = await fetch(`${API_BASE_URL}/answer-provider/status`, { cache: "no-store" });
  return parseJsonResponse<AnswerProviderStatus>(response);
}

export async function fetchDocuments(conversationId?: string): Promise<PaperLensDocument[]> {
  const url = conversationId
    ? `${API_BASE_URL}/documents?conversation_id=${encodeURIComponent(conversationId)}`
    : `${API_BASE_URL}/documents`;
  const response = await fetch(url, { cache: "no-store" });
  return parseJsonResponse<PaperLensDocument[]>(response);
}

export async function uploadDocument(file: File, conversationId?: string): Promise<PaperLensDocument> {
  const body = new FormData();
  body.append("file", file);

  const url = conversationId
    ? `${API_BASE_URL}/documents?conversation_id=${encodeURIComponent(conversationId)}`
    : `${API_BASE_URL}/documents`;

  const response = await fetch(url, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json() as Promise<PaperLensDocument>;
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}

export async function updateDocumentTitle(
  documentId: string,
  title: string,
): Promise<PaperLensDocument> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return parseJsonResponse<PaperLensDocument>(response);
}

export async function fetchDocumentIngestion(documentId: string): Promise<IngestionJob> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/ingestion`, {
    cache: "no-store",
  });
  return parseJsonResponse<IngestionJob>(response);
}

export async function triggerDocumentIngestion(documentId: string): Promise<IngestionJob> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/ingestion`, {
    method: "POST",
  });
  return parseJsonResponse<IngestionJob>(response);
}

export async function fetchDocumentTextPreview(
  documentId: string,
  maxChars = 800,
): Promise<IngestionTextPreview> {
  const params = new URLSearchParams({ max_chars: String(maxChars) });
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/ingestion/text-preview?${params}`, {
    cache: "no-store",
  });
  return parseJsonResponse<IngestionTextPreview>(response);
}

export async function createDocumentChunks(documentId: string): Promise<DocumentChunk[]> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/chunks`, {
    method: "POST",
  });
  return parseJsonResponse<DocumentChunk[]>(response);
}

export async function fetchDocumentChunks(documentId: string, limit = 100): Promise<DocumentChunk[]> {
  const params = new URLSearchParams({ offset: "0", limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/chunks?${params}`, {
    cache: "no-store",
  });
  return parseJsonResponse<DocumentChunk[]>(response);
}

export async function fetchDocumentChunkContext(
  documentId: string,
  chunkId: string,
  before = 1,
  after = 1,
): Promise<DocumentChunkContext> {
  const params = new URLSearchParams({ before: String(before), after: String(after) });
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/chunks/${chunkId}/context?${params}`, {
    cache: "no-store",
  });
  return parseJsonResponse<DocumentChunkContext>(response);
}

export async function fetchMessageEvidenceSource(
  conversationId: string,
  messageId: string,
  evidenceId: string,
): Promise<MessageEvidenceSource> {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}/messages/${messageId}/evidence/${evidenceId}/source`,
    { cache: "no-store" },
  );
  return parseJsonResponse<MessageEvidenceSource>(response);
}

export async function createConversation(
  title?: string,
  scopedDocumentId?: string,
  sourceDocumentIds?: string[],
  signal?: AbortSignal,
): Promise<Conversation> {
  const payload: { title?: string; scoped_document_id?: string; source_document_ids?: string[] } = {};
  if (title) {
    payload.title = title;
  }
  if (scopedDocumentId) {
    payload.scoped_document_id = scopedDocumentId;
  }
  if (sourceDocumentIds) {
    payload.source_document_ids = sourceDocumentIds;
  }
  const hasPayload = Object.keys(payload).length > 0;
  const response = await fetch(`${API_BASE_URL}/conversations`, {
    method: "POST",
    headers: hasPayload ? { "Content-Type": "application/json" } : undefined,
    body: hasPayload ? JSON.stringify(payload) : undefined,
    signal,
  });
  return parseJsonResponse<Conversation>(response);
}

export async function updateConversation(
  conversationId: string,
  payload: { title?: string; source_document_ids?: string[] },
  signal?: AbortSignal,
): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  return parseJsonResponse<Conversation>(response);
}

export async function fetchConversations(): Promise<Conversation[]> {
  const response = await fetch(`${API_BASE_URL}/conversations`, { cache: "no-store" });
  return parseJsonResponse<Conversation[]>(response);
}

export async function fetchConversation(conversationId: string): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    cache: "no-store",
  });
  return parseJsonResponse<Conversation>(response);
}

export async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}

export async function postConversationMessage(
  conversationId: string,
  content: string,
  limit = 5,
  signal?: AbortSignal,
): Promise<ChatTurn> {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages?${params}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  });
  return parseJsonResponse<ChatTurn>(response);
}

export async function fetchConversationMessages(conversationId: string): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
    cache: "no-store",
  });
  return parseJsonResponse<ChatMessage[]>(response);
}

export async function updateConversationMessage(
  conversationId: string,
  messageId: string,
  content: string,
  limit = 5,
  signal?: AbortSignal,
): Promise<ChatTurn> {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/${messageId}?${params}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  });
  return parseJsonResponse<ChatTurn>(response);
}
