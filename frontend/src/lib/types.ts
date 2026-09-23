export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  chunk_count: number;
  page_count: number | null;
  created_at: string;
  processed_at: string | null;
}

export interface Citation {
  number: number;
  chunk_id: string;
  document_id: string;
  document_title: string;
  heading: string | null;
  page: number | null;
  text: string;
  relevance: number;
}

export type MessageStatus = "answered" | "abstained" | "failed";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: MessageStatus | null;
  citations: Citation[];
  feedback: 1 | -1 | null;
  created_at: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface SessionDetail extends Session {
  messages: Message[];
}

export interface Passage {
  chunk_id: string;
  document_id: string;
  document_title: string;
  heading: string | null;
  page: number | null;
  text: string;
  relevance: number;
  fused_score: number;
  dense_rank: number | null;
  lexical_rank: number | null;
}

export interface TraceSpan {
  name: string;
  duration_ms: number;
  [attribute: string]: unknown;
}

export interface SearchResponse {
  query: string;
  candidates: number;
  passages: Passage[];
  trace: { total_ms: number; spans: TraceSpan[] };
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    request_id?: string;
  };
}
