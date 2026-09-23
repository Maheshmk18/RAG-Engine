import type {
  ApiErrorBody,
  DocumentItem,
  Message,
  SearchResponse,
  Session,
  SessionDetail,
} from "./types";

const API_ROOT = `${(import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "")}/api/v1`;
const CLIENT_KEY = "erag.client";
const ADMIN_KEY = "erag.admin";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, body: ApiErrorBody | null) {
    super(body?.error.message ?? "Something went wrong. Please try again.");
    this.status = status;
    this.code = body?.error.code ?? "unknown";
  }
}

function read(storage: () => Storage, key: string): string | null {
  try {
    return storage().getItem(key);
  } catch {
    return null;
  }
}

function write(storage: () => Storage, key: string, value: string | null) {
  try {
    if (value === null) storage().removeItem(key);
    else storage().setItem(key, value);
  } catch {
    return;
  }
}

let fallbackClientId: string | null = null;

export function clientId(): string {
  const stored = read(() => localStorage, CLIENT_KEY);
  if (stored) return stored;
  const created = crypto.randomUUID();
  write(() => localStorage, CLIENT_KEY, created);
  fallbackClientId ??= created;
  return read(() => localStorage, CLIENT_KEY) ?? fallbackClientId;
}

export const adminKey = {
  get: () => read(() => sessionStorage, ADMIN_KEY),
  set: (value: string | null) => write(() => sessionStorage, ADMIN_KEY, value),
};

export async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("X-Client-Id", clientId());
  const key = adminKey.get();
  if (key && !headers.has("X-Admin-Key")) headers.set("X-Admin-Key", key);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_ROOT}${path}`, { ...init, headers });
  if (response.ok) return response;
  const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
  throw new ApiError(response.status, body);
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init);
  return (response.status === 204 ? undefined : await response.json()) as T;
}

const send = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const api = {
  verifyAdminKey: (key: string) =>
    json<void>("/admin/verify", { method: "POST", headers: { "X-Admin-Key": key } }),

  documents: () => json<DocumentItem[]>("/documents"),
  uploadDocument: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return json<DocumentItem>("/documents", { method: "POST", body });
  },
  reprocessDocument: (id: string) => json<DocumentItem>(`/documents/${id}/reprocess`, send("POST")),
  deleteDocument: (id: string) => json<void>(`/documents/${id}`, send("DELETE")),
  documentFile: async (id: string) => (await request(`/documents/${id}/file`)).blob(),

  sessions: () => json<Session[]>("/chat/sessions"),
  session: (id: string) => json<SessionDetail>(`/chat/sessions/${id}`),
  createSession: () => json<Session>("/chat/sessions", send("POST", {})),
  renameSession: (id: string, title: string) =>
    json<Session>(`/chat/sessions/${id}`, send("PATCH", { title })),
  deleteSession: (id: string) => json<void>(`/chat/sessions/${id}`, send("DELETE")),
  feedback: (messageId: string, value: 1 | -1 | null) =>
    json<Message>(`/chat/messages/${messageId}/feedback`, send("POST", { value })),
  ask: (sessionId: string, content: string, signal: AbortSignal) =>
    request(`/chat/sessions/${sessionId}/messages`, { ...send("POST", { content }), signal }),

  search: (query: string) => json<SearchResponse>("/retrieval/search", send("POST", { query })),
};
