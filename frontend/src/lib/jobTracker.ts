"use client";

export interface TrackedGenerationJob {
  jobId: string;
  moduleId: string;
  moduleTitle?: string;
  createdAt: string;
}

const STORAGE_KEY = "learnstral.activeGenerationJobs.v1";
const EVENT_NAME = "learnstral:active-generation-jobs-updated";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function emitUpdate(): void {
  if (!isBrowser()) return;
  window.dispatchEvent(new Event(EVENT_NAME));
}

export function activeGenerationJobsEventName(): string {
  return EVENT_NAME;
}

export function readTrackedGenerationJobs(): TrackedGenerationJob[] {
  if (!isBrowser()) return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    const jobs: TrackedGenerationJob[] = [];
    for (const item of parsed) {
      if (!item || typeof item !== "object") continue;
      const jobId = String((item as { jobId?: unknown }).jobId || "").trim();
      const moduleId = String((item as { moduleId?: unknown }).moduleId || "").trim();
      const createdAt = String((item as { createdAt?: unknown }).createdAt || "").trim();
      if (!jobId || !moduleId || !createdAt) continue;
      const moduleTitle = String((item as { moduleTitle?: unknown }).moduleTitle || "").trim();
      jobs.push({ jobId, moduleId, createdAt, moduleTitle: moduleTitle || undefined });
    }
    return jobs;
  } catch {
    return [];
  }
}

function writeTrackedGenerationJobs(jobs: TrackedGenerationJob[]): void {
  if (!isBrowser()) return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
  emitUpdate();
}

export function trackGenerationJob(job: TrackedGenerationJob): void {
  const existing = readTrackedGenerationJobs();
  const deduped = existing.filter((item) => item.jobId !== job.jobId);
  deduped.push(job);
  writeTrackedGenerationJobs(deduped);
}

export function untrackGenerationJob(jobId: string): void {
  const existing = readTrackedGenerationJobs();
  const next = existing.filter((item) => item.jobId !== jobId);
  if (next.length === existing.length) return;
  writeTrackedGenerationJobs(next);
}

export function trackedGenerationJobForModule(moduleId: string): TrackedGenerationJob | null {
  const existing = readTrackedGenerationJobs();
  const match = existing
    .filter((item) => item.moduleId === moduleId)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
  return match || null;
}
