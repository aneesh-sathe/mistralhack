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

interface ChatStreamHandlers {
  onMeta?: (meta: { model?: string; module_id?: string }) => void;
  onToken?: (delta: string) => void;
  onDone?: () => void;
}

export async function chatWithModuleStream(
  moduleId: string,
  message: string,
  history: ModuleChatTurn[],
  handlers: ChatStreamHandlers = {}
) {
  const res = await fetch(`${API_BASE}/api/modules/${moduleId}/chat/stream`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, history }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  if (!res.body) {
    throw new Error("Streaming response body is unavailable");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const handleLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed) return;

    const evt = JSON.parse(trimmed) as {
      type: string;
      model?: string;
      module_id?: string;
      delta?: string;
      message?: string;
    };

    if (evt.type === "meta") {
      handlers.onMeta?.({ model: evt.model, module_id: evt.module_id });
      return;
    }
    if (evt.type === "token") {
      if (evt.delta) handlers.onToken?.(evt.delta);
      return;
    }
    if (evt.type === "error") {
      throw new Error(evt.message || "Streaming chat failed");
    }
    if (evt.type === "done") {
      handlers.onDone?.();
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      handleLine(line);
    }
  }

  if (buffer.trim()) {
    handleLine(buffer);
  }
}
