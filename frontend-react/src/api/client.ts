import type {
  AskResponse,
  CompareResponse,
  DocumentsResponse,
  StatsResponse,
  UploadResponse,
} from "../types";

const API_URL = "http://localhost:8000";

class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/upload`, { method: "POST", body: form });
  return handleResponse<UploadResponse>(res);
}

export async function ask(query: string): Promise<AskResponse> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return handleResponse<AskResponse>(res);
}

export async function compare(
  query: string,
  doc_a: string,
  doc_b: string,
): Promise<CompareResponse> {
  const res = await fetch(`${API_URL}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, doc_a, doc_b }),
  });
  return handleResponse<CompareResponse>(res);
}

export async function listDocuments(): Promise<DocumentsResponse> {
  const res = await fetch(`${API_URL}/documents`);
  return handleResponse<DocumentsResponse>(res);
}

export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_URL}/stats`);
  return handleResponse<StatsResponse>(res);
}

export async function resetIndex(): Promise<void> {
  const res = await fetch(`${API_URL}/reset`, { method: "POST" });
  await handleResponse(res);
}

export function pdfUrl(filename: string): string {
  return `${API_URL}/documents/${encodeURIComponent(filename)}`;
}