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

export type Conversation = {
  conversation_id: string;
  title: string;
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
};

export type ChatMessage = {
  message_id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  evidence: MessageEvidence[];
};

export type ChatTurn = {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
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

export async function fetchDocuments(): Promise<PaperLensDocument[]> {
  const response = await fetch(`${API_BASE_URL}/documents`, { cache: "no-store" });
  return parseJsonResponse<PaperLensDocument[]>(response);
}

export async function uploadDocument(file: File): Promise<PaperLensDocument> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents`, {
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

export async function createConversation(title?: string): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations`, {
    method: "POST",
    headers: title ? { "Content-Type": "application/json" } : undefined,
    body: title ? JSON.stringify({ title }) : undefined,
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
): Promise<ChatTurn> {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages?${params}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  return parseJsonResponse<ChatTurn>(response);
}

export async function fetchConversationMessages(conversationId: string): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
    cache: "no-store",
  });
  return parseJsonResponse<ChatMessage[]>(response);
}
