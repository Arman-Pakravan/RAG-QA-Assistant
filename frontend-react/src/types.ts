// Shared type definitions matching the FastAPI backend responses.

export type QueryType = "lookup" | "explanation" | "how_to" | "policy" | "data";
export type Confidence = "high" | "medium" | "low" | null;

export interface Source {
  document_name: string;
  section_title: string;
  content_type: string;
  score: number;
}

export interface AskResponse {
  query: string;
  query_type: QueryType;
  answer: string;
  confidence: Confidence;
  top_score: number | null;
  sources: Source[];
}

export interface CompareResponse {
  query: string;
  doc_a: string;
  doc_b: string;
  answer: string;
  sources: Source[];
  chunks_a_count: number;
  chunks_b_count: number;
}

export interface UploadResponse {
  document_name: string;
  pages: number;
  chunks_indexed: number;
  total_chunks_in_index: number;
}

export interface IndexedDoc {
  filename: string;
  stem: string;
}

export interface DocumentsResponse {
  documents: IndexedDoc[];
}

export interface StatsResponse {
  total_chunks: number;
  documents: string[];
  embedding_dim: number;
}

// A single chat message, kept on the client side
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  query_type?: QueryType;
  confidence?: Confidence;
  sources?: Source[];
  isCompare?: boolean;
  isError?: boolean;
}