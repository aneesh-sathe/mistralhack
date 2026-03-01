import { JobItem } from "@/lib/types";

const STAGE_LABELS: Record<string, string> = {
  QUEUED: "Queued",
  PARSING: "Reading document",
  CHUNKING: "Preparing sections",
  MODULE_EXTRACTION: "Creating modules",
  PARSED: "Document ready",
  RUNNING: "Starting generation",
  SCRIPT: "Writing lesson",
  SCRIPT_DONE: "Script complete",
  AUDIO_DONE: "Narration complete",
  MANIM_DONE: "Animation complete",
  VIDEO_DONE: "Video complete",
  CAPTIONS_DONE: "Captions complete",
  MUXED_DONE: "Lesson ready",
  FAILED: "Failed",
};

export function clampPercent(value: number | undefined): number {
  const parsed = typeof value === "number" ? value : 0;
  return Math.min(100, Math.max(0, Math.round(parsed)));
}

export function formatStageLabel(stage: string | undefined): string {
  if (!stage) return "Queued";
  const direct = STAGE_LABELS[stage];
  if (direct) return direct;
  return stage
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function statusLabel(status: JobItem["status"] | "loading"): string {
  if (status === "loading") return "Loading";
  if (status === "queued") return "Queued";
  if (status === "running") return "Running";
  if (status === "succeeded") return "Done";
  return "Failed";
}
