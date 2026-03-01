"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/ToastProvider";
import { getJob } from "@/lib/api";
import { clampPercent, formatStageLabel, statusLabel } from "@/lib/jobStages";
import {
  activeGenerationJobsEventName,
  readTrackedJobs,
  TrackedJob,
  untrackJob,
} from "@/lib/jobTracker";
import { JobItem } from "@/lib/types";

function tone(status: JobItem["status"] | "loading"): string {
  if (status === "succeeded") return "bg-emerald-100 text-emerald-800";
  if (status === "failed") return "bg-rose-100 text-rose-800";
  if (status === "running") return "bg-amber-100 text-amber-800";
  if (status === "queued") return "bg-slate-100 text-slate-700";
  return "bg-slate-100 text-slate-700";
}

function activityLabel(job: TrackedJob): string {
  if (job.title) return job.title;
  const prefix = job.entityType === "module" ? "Module" : "Document";
  return `${prefix} ${job.entityId.slice(0, 8)}`;
}

function activityHref(job: TrackedJob): string {
  if (job.entityType === "module") return `/modules/${job.entityId}`;
  return `/documents/${job.entityId}`;
}

export default function GlobalJobProgress() {
  const [tracked, setTracked] = useState<TrackedJob[]>([]);
  const [jobsById, setJobsById] = useState<Record<string, JobItem>>({});
  const [errorById, setErrorById] = useState<Record<string, string>>({});
  const { notify } = useToast();
  const router = useRouter();

  const refreshTracked = useCallback(() => {
    setTracked(readTrackedJobs());
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
          const entry = tracked.find((item) => item.jobId === jobId);
          const completedJob = nextJobs[jobId];

          if (entry && completedJob) {
            const success = completedJob.status === "succeeded";
            notify({
              title: success
                ? entry.entityType === "module"
                  ? "Lesson ready"
                  : "Document processed"
                : entry.entityType === "module"
                  ? "Lesson generation failed"
                  : "Document processing failed",
              description: activityLabel(entry),
              tone: success ? "success" : "error",
              action: {
                label: success
                  ? entry.entityType === "module"
                    ? "Open lesson"
                    : "Open modules"
                  : "View details",
                onClick: () => router.push(activityHref(entry)),
              },
              dedupeKey: `job-complete-${jobId}`,
            });
          }

          untrackJob(jobId);
        }
      }
    };

    poll();
    intervalId = setInterval(poll, 2000);
    return () => {
      active = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [notify, router, tracked]);

  const visible = useMemo(
    () => [...tracked].sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
    [tracked]
  );

  if (!visible.length) return null;

  return (
    <div className="mx-auto w-full max-w-[1110px] px-4 pb-2 pt-4 sm:px-6">
      <div className="surface-muted p-3">
        <div className="mb-3 text-xs font-bold uppercase tracking-[0.08em] text-slate-500">Background Activity</div>
        <div className="space-y-2">
          {visible.map((entry) => {
            const job = jobsById[entry.jobId];
            const error = errorById[entry.jobId];
            const status = job?.status || "loading";
            const stage = formatStageLabel(job?.progress?.stage);
            const percent = clampPercent(job?.progress?.percent);

            return (
              <div key={entry.jobId} className="rounded-xl border border-slate-200 bg-white p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <Link href={activityHref(entry)} className="text-sm font-semibold text-slate-700 hover:text-slate-900">
                    {activityLabel(entry)}
                  </Link>
                  <span className={`status-pill ${tone(status)}`}>{statusLabel(status)}</span>
                </div>
                <div className="mb-2 flex items-center justify-between gap-2 text-xs font-semibold text-slate-600">
                  <span>{stage}</span>
                  <span>{percent}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-200">
                  <div
                    className="h-2 rounded-full bg-brand-500 transition-all duration-500"
                    style={{ width: `${percent}%` }}
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
