import {
  AuthMeResponse,
  DocumentItem,
  JobItem,
  ModuleAssets,
  ModuleChatResponse,
  ModuleChatTurn,
  ModuleItem,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await res.text()) as unknown as T;
  }
  return (await res.json()) as T;
}

export function getAuthMe() {
  return request<AuthMeResponse>("/api/auth/me");
}

export function listDocuments() {
  return request<{ documents: DocumentItem[] }>("/api/documents");
}

export function getDocument(docId: string) {
  return request<DocumentItem>(`/api/documents/${docId}`);
}

export function deleteDocument(docId: string) {
  return request<void>(`/api/documents/${docId}`, { method: "DELETE" });
}

export function uploadDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ document_id: string; job_id: string }>("/api/documents", {
    method: "POST",
    body: form,
  });
}

export function getDocumentModules(docId: string) {
  return request<{ modules: ModuleItem[] }>(`/api/documents/${docId}/modules`);
}

export function getModule(moduleId: string) {
  return request<ModuleItem>(`/api/modules/${moduleId}`);
}

export function generateModule(moduleId: string) {
  return request<{ job_id: string }>(`/api/modules/${moduleId}/generate`, { method: "POST" });
}

export function getModuleAssets(moduleId: string) {
  return request<ModuleAssets>(`/api/modules/${moduleId}/assets`);
}

export function getJob(jobId: string) {
  return request<JobItem>(`/api/jobs/${jobId}`);
}

export function getCaptions(moduleId: string) {
  return request<string>(`/api/artifacts/captions/${moduleId}`);
}

export function videoUrl(moduleId: string) {
  return `${API_BASE}/api/artifacts/video/${moduleId}`;
}

export function backendAuthLoginUrl() {
  return `${API_BASE}/api/auth/google/login`;
}

export function chatWithModule(moduleId: string, message: string, history: ModuleChatTurn[]) {
  return request<ModuleChatResponse>(`/api/modules/${moduleId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
}
