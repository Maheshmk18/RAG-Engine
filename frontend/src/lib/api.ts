import type {
  ApiErrorBody,
  DocumentItem,
  Message,
  Role,
  SearchResponse,
  Session,
  SessionDetail,
  TokenResponse,
  User,
} from "./types";

const API_ROOT = `${(import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "")}/api/v1`;
const TOKEN_KEY = "amd.token";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: Record<string, string>;

  constructor(status: number, body: ApiErrorBody | null) {
    super(body?.error.message ?? "Something went wrong. Please try again.");
    this.status = status;
    this.code = body?.error.code ?? "unknown";
    this.fields = Object.fromEntries(
      (body?.error.details ?? []).map((detail) => [detail.field, detail.message]),
    );
  }
}

type UnauthorizedListener = () => void;
let onUnauthorized: UnauthorizedListener = () => {};

export const session = {
  token: (): string | null => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  store: (token: string) => {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      return;
    }
  },
  clear: () => {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      return;
    }
  },
  onUnauthorized: (listener: UnauthorizedListener) => {
    onUnauthorized = listener;
  },
};

export async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = session.token();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_ROOT}${path}`, { ...init, headers });
  if (response.ok) return response;

  const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
  if (response.status === 401 && token) {
    session.clear();
    onUnauthorized();
  }
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
  login: (email: string, password: string) =>
    json<TokenResponse>("/auth/login", send("POST", { email, password })),
  me: () => json<User>("/auth/me"),
  updateProfile: (fullName: string) =>
    json<User>("/auth/me", send("PATCH", { full_name: fullName })),
  changePassword: (currentPassword: string, newPassword: string) =>
    json<void>(
      "/auth/me/password",
      send("POST", { current_password: currentPassword, new_password: newPassword }),
    ),

  users: () => json<User[]>("/users"),
  createUser: (data: { email: string; full_name: string; password: string; role: Role }) =>
    json<User>("/users", send("POST", data)),
  updateUser: (id: string, data: Partial<Pick<User, "full_name" | "role" | "is_active">>) =>
    json<User>(`/users/${id}`, send("PATCH", data)),
  deleteUser: (id: string) => json<void>(`/users/${id}`, send("DELETE")),

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
