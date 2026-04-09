const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type ChatPayload = {
  messages: Array<{ role: string; agent: string; content: string }>;
  waiting_for_hitl: boolean;
  hitl_question: string;
  session_done: boolean;
  final_report: Record<string, unknown> | null;
};

export type SessionSummary = {
  id: string;
  title: string;
  waiting_for_hitl?: boolean;
  hitl_question?: string;
  created_at?: string;
};

export type SessionMessagesPayload = {
  messages: Array<{ role: string; agent: string; content: string }>;
};

export async function apiFetch<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {})
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export const authApi = {
  register: (email: string, password: string) =>
    apiFetch<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    })
};

export const sessionsApi = {
  create: (token: string) => apiFetch<SessionSummary>("/sessions", { method: "POST", body: JSON.stringify({}) }, token),
  list: (token: string) => apiFetch<SessionSummary[]>("/sessions", {}, token),
  messages: (token: string, sessionId: string) =>
    apiFetch<SessionMessagesPayload>(`/sessions/${sessionId}/messages`, {}, token)
};

export const chatApi = {
  send: (token: string, sessionId: string, message: string) =>
    apiFetch<ChatPayload>(
      "/chat/message",
      { method: "POST", body: JSON.stringify({ session_id: sessionId, message }) },
      token
    ),
  hitl: (token: string, sessionId: string, answer: string) =>
    apiFetch<ChatPayload>(
      "/chat/hitl",
      { method: "POST", body: JSON.stringify({ session_id: sessionId, answer }) },
      token
    ),
  report: (token: string, sessionId: string) => apiFetch<{ final_report: Record<string, unknown> | null }>(`/reports/${sessionId}`, {}, token)
};
