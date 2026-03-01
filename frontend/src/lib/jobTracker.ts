"use client";

export type TrackedJobKind = "parse_document" | "generate_module_assets";
export type TrackedEntityType = "document" | "module";

export interface TrackedJob {
  jobId: string;
  kind: TrackedJobKind | string;
  entityType: TrackedEntityType;
  entityId: string;
  title?: string;
  createdAt: string;
}

export interface TrackedGenerationJob {
  jobId: string;
  moduleId: string;
  moduleTitle?: string;
  createdAt: string;
}

export interface TrackedDocumentParseJob {
  jobId: string;
  documentId: string;
  documentTitle?: string;
  createdAt: string;
}

const STORAGE_KEY = "learnstral.activeJobs.v2";
const LEGACY_STORAGE_KEY = "learnstral.activeGenerationJobs.v1";
const EVENT_NAME = "learnstral:active-jobs-updated";

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

function toTrackedJob(item: unknown): TrackedJob | null {
  if (!item || typeof item !== "object") return null;

  const raw = item as Record<string, unknown>;
  const jobId = String(raw.jobId || "").trim();
  const createdAt = String(raw.createdAt || "").trim();
  if (!jobId || !createdAt) return null;

  const entityType = String(raw.entityType || "").trim();
  const entityId = String(raw.entityId || "").trim();
  const kind = String(raw.kind || "").trim();
  const title = String(raw.title || "").trim() || undefined;

  if ((entityType === "document" || entityType === "module") && entityId) {
    return {
      jobId,
      kind: kind || "generate_module_assets",
      entityType,
      entityId,
      title,
      createdAt,
    };
  }

  // Backward compatibility for v1 generation-tracker payloads.
  const moduleId = String(raw.moduleId || "").trim();
  if (!moduleId) return null;
  const moduleTitle = String(raw.moduleTitle || "").trim() || undefined;
  return {
    jobId,
    kind: "generate_module_assets",
    entityType: "module",
    entityId: moduleId,
    title: moduleTitle,
    createdAt,
  };
}

function parseTrackedJobs(raw: string | null): TrackedJob[] {
  if (!raw) return [];
  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) return [];

  const jobs: TrackedJob[] = [];
  for (const item of parsed) {
    const normalized = toTrackedJob(item);
    if (normalized) jobs.push(normalized);
  }
  return jobs;
}

export function readTrackedJobs(): TrackedJob[] {
  if (!isBrowser()) return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = parseTrackedJobs(raw);
    if (parsed.length) return parsed;

    // Read legacy generation jobs once and migrate in-memory.
    const legacy = parseTrackedJobs(window.localStorage.getItem(LEGACY_STORAGE_KEY));
    if (legacy.length) {
      writeTrackedJobs(legacy);
      window.localStorage.removeItem(LEGACY_STORAGE_KEY);
      return legacy;
    }
    return [];
  } catch {
    return [];
  }
}

function writeTrackedJobs(jobs: TrackedJob[]): void {
  if (!isBrowser()) return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
  emitUpdate();
}

export function trackJob(job: TrackedJob): void {
  const existing = readTrackedJobs();
  const deduped = existing.filter((item) => item.jobId !== job.jobId);
  deduped.push(job);
  writeTrackedJobs(deduped);
}

export function untrackJob(jobId: string): void {
  const existing = readTrackedJobs();
  const next = existing.filter((item) => item.jobId !== jobId);
  if (next.length === existing.length) return;
  writeTrackedJobs(next);
}

export function trackedJobForEntity(entityType: TrackedEntityType, entityId: string): TrackedJob | null {
  const existing = readTrackedJobs();
  const match = existing
    .filter((item) => item.entityType === entityType && item.entityId === entityId)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
  return match || null;
}

export function trackDocumentParseJob(job: TrackedDocumentParseJob): void {
  trackJob({
    jobId: job.jobId,
    kind: "parse_document",
    entityType: "document",
    entityId: job.documentId,
    title: job.documentTitle,
    createdAt: job.createdAt,
  });
}

export function readTrackedGenerationJobs(): TrackedGenerationJob[] {
  return readTrackedJobs()
    .filter((item) => item.entityType === "module")
    .map((item) => ({
      jobId: item.jobId,
      moduleId: item.entityId,
      moduleTitle: item.title,
      createdAt: item.createdAt,
    }));
}

export function trackGenerationJob(job: TrackedGenerationJob): void {
  trackJob({
    jobId: job.jobId,
    kind: "generate_module_assets",
    entityType: "module",
    entityId: job.moduleId,
    title: job.moduleTitle,
    createdAt: job.createdAt,
  });
}

export function untrackGenerationJob(jobId: string): void {
  untrackJob(jobId);
}

export function trackedGenerationJobForModule(moduleId: string): TrackedGenerationJob | null {
  const item = trackedJobForEntity("module", moduleId);
  if (!item) return null;
  return {
    jobId: item.jobId,
    moduleId: item.entityId,
    moduleTitle: item.title,
    createdAt: item.createdAt,
  };
}
