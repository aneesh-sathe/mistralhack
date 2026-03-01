"use client";

import { useEffect, useState } from "react";

import { getJob } from "@/lib/api";
import { clampPercent, formatStageLabel, statusLabel } from "@/lib/jobStages";
import { JobItem } from "@/lib/types";

interface JobProgressProps {
  jobId: string | null;
  onComplete?: (job: JobItem) => void;
}

function tone(status: JobItem["status"]): string {
  if (status === "succeeded") return "bg-emerald-100 text-emerald-800";
  if (status === "failed") return "bg-rose-100 text-rose-800";
  if (status === "running") return "bg-amber-100 text-amber-800";
  return "bg-slate-100 text-slate-700";
}

export default function JobProgress({ jobId, onComplete }: JobProgressProps) {
  const [job, setJob] = useState<JobItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    let active = true;
    let completedNotified = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const poll = async () => {
      try {
        const res = await getJob(jobId);
        if (!active) return;
        setJob(res);
        if (res.status === "succeeded" || res.status === "failed") {
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
          if (!completedNotified && onComplete) {
            completedNotified = true;
            onComplete(res);
          }
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to fetch job");
      }
    };

    poll();
    intervalId = setInterval(poll, 2000);
    return () => {
      active = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, onComplete]);

  if (!jobId) return null;

  if (error) {
    return <div className="card border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-700">{error}</div>;
  }

  if (!job) {
    return <div className="surface-muted p-4 text-sm text-slate-600">Fetching job progress...</div>;
  }

  const percent = job.progress?.percent ?? 0;
  const stage = formatStageLabel(job.progress?.stage);
  const clampedPercent = clampPercent(percent);

  return (
    <div className="surface-muted p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={`status-pill ${tone(job.status)}`}>{statusLabel(job.status)}</span>
          <span className="text-sm font-semibold text-slate-700">{stage}</span>
        </div>
        <span className="text-sm font-bold text-slate-700">{clampedPercent}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate-200">
        <div
          className="h-2 rounded-full bg-brand-500 transition-all duration-500"
          style={{ width: `${clampedPercent}%` }}
        />
      </div>
      {job.error ? <p className="mt-3 text-sm font-medium text-rose-700">{job.error}</p> : null}
    </div>
  );
}
