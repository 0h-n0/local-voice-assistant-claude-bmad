/**
 * REST API client for voice assistant backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Message response from backend */
export interface MessageResponse {
  id: string;
  role: "user" | "assistant";
  content: string;
  stt_latency_ms: number | null;
  llm_latency_ms: number | null;
  tts_latency_ms: number | null;
  created_at: string;
}

/** Conversation response from backend */
export interface ConversationResponse {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
}

/** Conversation list item (without messages) */
export interface ConversationListItem {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

/** Pagination metadata */
export interface ConversationListMeta {
  total: number;
  limit: number;
  offset: number;
}

/** Conversation list response */
export interface ConversationListResponse {
  data: ConversationListItem[];
  meta: ConversationListMeta;
}

/**
 * Fetch paginated list of conversations
 */
export async function fetchConversations(
  limit = 20,
  offset = 0
): Promise<ConversationListResponse> {
  const res = await fetch(
    `${API_BASE}/api/v1/conversations?limit=${limit}&offset=${offset}`
  );
  if (!res.ok) {
    throw new Error("Failed to fetch conversations");
  }
  return res.json();
}

/**
 * Fetch a specific conversation with messages
 */
export async function fetchConversation(
  id: string
): Promise<ConversationResponse> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}`);
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Conversation not found");
    }
    throw new Error("Failed to fetch conversation");
  }
  return res.json();
}

/**
 * Delete a conversation and all its messages
 */
export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Conversation not found");
    }
    throw new Error("Failed to delete conversation");
  }
}
