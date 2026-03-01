"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getJob } from "@/lib/api";
import {
  activeGenerationJobsEventName,
  readTrackedGenerationJobs,
  TrackedGenerationJob,
  untrackGenerationJob,
} from "@/lib/jobTracker";
import { JobItem } from "@/lib/types";

function tone(status: JobItem["status"] | "loading"): string {
  if (status === "succeeded") return "bg-emerald-100 text-emerald-800";
  if (status === "failed") return "bg-rose-100 text-rose-800";
  if (status === "running") return "bg-amber-100 text-amber-800";
  if (status === "queued") return "bg-slate-100 text-slate-700";
  return "bg-slate-100 text-slate-700";
}

function shortModuleLabel(job: TrackedGenerationJob): string {
  if (job.moduleTitle) return job.moduleTitle;
  return `Module ${job.moduleId.slice(0, 8)}`;
}

export default function GlobalJobProgress() {
  const [tracked, setTracked] = useState<TrackedGenerationJob[]>([]);
  const [jobsById, setJobsById] = useState<Record<string, JobItem>>({});
  const [errorById, setErrorById] = useState<Record<string, string>>({});

  const refreshTracked = useCallback(() => {
    setTracked(readTrackedGenerationJobs());
  }, []);

  useEffect(() => {
    refreshTracked();
    const eventName = activeGenerationJobsEventName();
    const onUpdate = () => refreshTracked();
    const onStorage = () => refreshTracked();

    window.addEventListener(eventName, onUpdate);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(eventName, onUpdate);
      window.removeEventListener("storage", onStorage);
    };
  }, [refreshTracked]);

  useEffect(() => {
    if (!tracked.length) {
      setJobsById({});
      setErrorById({});
      return;
    }

    let active = true;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const poll = async () => {
      const nextJobs: Record<string, JobItem> = {};
      const nextErrors: Record<string, string> = {};
      const completed: string[] = [];

      await Promise.all(
        tracked.map(async (item) => {
          try {
            const job = await getJob(item.jobId);
            nextJobs[item.jobId] = job;
            if (job.status === "succeeded" || job.status === "failed") {
              completed.push(item.jobId);
            }
          } catch (err) {
            nextErrors[item.jobId] = err instanceof Error ? err.message : "Failed to fetch job progress";
          }
        })
      );

      if (!active) return;
      setJobsById(nextJobs);
      setErrorById(nextErrors);

      if (completed.length) {
        for (const jobId of completed) {
          untrackGenerationJob(jobId);
        }
      }
    };

    poll();
    intervalId = setInterval(poll, 2000);
    return () => {
      active = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [tracked]);

  const visible = useMemo(
    () => [...tracked].sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
    [tracked]
  );

  if (!visible.length) return null;

  return (
    <div className="mx-auto w-full max-w-[1110px] px-4 pb-2 pt-4 sm:px-6">
      <div className="surface-muted p-3">
        <div className="mb-3 text-xs font-bold uppercase tracking-[0.08em] text-slate-500">Generation In Progress</div>
        <div className="space-y-2">
          {visible.map((entry) => {
            const job = jobsById[entry.jobId];
            const error = errorById[entry.jobId];
            const status = job?.status || "loading";
            const stage = job?.progress?.stage || "queued";
            const percent = job?.progress?.percent ?? 0;

            return (
              <div key={entry.jobId} className="rounded-xl border border-slate-200 bg-white p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <Link href={`/modules/${entry.moduleId}`} className="text-sm font-semibold text-slate-700 hover:text-slate-900">
                    {shortModuleLabel(entry)}
                  </Link>
                  <span className={`status-pill ${tone(status)}`}>{status}</span>
                </div>
                <div className="mb-2 flex items-center justify-between gap-2 text-xs font-semibold text-slate-600">
                  <span>{stage}</span>
                  <span>{Math.min(100, Math.max(0, percent))}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-200">
                  <div
                    className="h-2 rounded-full bg-brand-500 transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
                  />
                </div>
                {error ? <p className="mt-2 text-xs font-medium text-rose-700">{error}</p> : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
