export type Role = "user" | "assistant";

export interface ApiMessage {
  role: Role;
  content: string;
}

export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface RetrievedDocument {
  source: string;
  chunk_index: number;
  score: number;
}

export interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ExecutionMetadata {
  route?: "filiais" | "bulas";
  trace_id?: string;
  tool_calls?: ToolCall[];
  sources?: string[];
  search_query?: string | null;
  retrieved_documents?: RetrievedDocument[];
  usage?: Usage | null;
  latency_ms?: number;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  isStreaming?: boolean;
  metadata?: ExecutionMetadata;
}

export type StreamEventName =
  | "metadata"
  | "content"
  | "done"
  | "error";
