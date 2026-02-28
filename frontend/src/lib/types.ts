export interface User {
  id: string;
  google_sub?: string | null;
  email: string;
  name: string;
  avatar_url?: string | null;
}

export interface AuthMeResponse {
  user: User;
  dev_auth_bypass: boolean;
}

export interface DocumentItem {
  id: string;
  user_id: string;
  title: string;
  filename: string;
  storage_path: string;
  status: "PDF_UPLOADED" | "PARSING" | "PARSED" | "FAILED";
  created_at: string;
  updated_at: string;
}

export interface ModuleItem {
  id: string;
  document_id: string;
  title: string;
  summary: string;
  prerequisites: string[];
  chunk_refs: string[];
  status: "READY" | "GENERATING" | "DONE" | "FAILED";
  created_at: string;
  updated_at: string;
}

export interface JobItem {
  id: string;
  type: string;
  status: "queued" | "running" | "succeeded" | "failed";
  payload: Record<string, unknown>;
  progress: {
    stage?: string;
    percent?: number;
    history?: string[];
  };
  result: Record<string, unknown>;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModuleAssets {
  id: string;
  module_id: string;
  script_text: string | null;
  script_json: Record<string, unknown>;
  manim_code: string | null;
  audio_path: string | null;
  captions_srt_path: string | null;
  video_path: string | null;
  final_muxed_path: string | null;
  status: string;
  error?: string | null;
}
