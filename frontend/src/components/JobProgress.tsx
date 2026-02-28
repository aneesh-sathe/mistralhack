"use client";

import { useEffect, useState } from "react";

import { getJob } from "@/lib/api";
import { JobItem } from "@/lib/types";

interface JobProgressProps {
  jobId: string | null;
  onComplete?: (job: JobItem) => void;
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
    const poll = async () => {
      try {
        const res = await getJob(jobId);
        if (!active) return;
        setJob(res);
        if ((res.status === "succeeded" || res.status === "failed") && onComplete) {
          onComplete(res);
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to fetch job");
      }
    };

    poll();
    const id = setInterval(poll, 2000);

    return () => {
      active = false;
      clearInterval(id);
    };
  }, [jobId, onComplete]);

  if (!jobId) {
    return null;
  }

  if (error) {
    return <div className="card p-4 text-sm text-red-600">{error}</div>;
  }

  if (!job) {
    return <div className="card p-4 text-sm text-slate-600">Loading job...</div>;
  }

  const percent = job.progress?.percent ?? 0;
  const stage = job.progress?.stage || "queued";

  return (
    <div className="card p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-medium text-slate-900">Job: {job.status}</span>
        <span className="text-slate-600">{percent}%</span>
      </div>
      <div className="h-2 w-full rounded bg-slate-200">
        <div className="h-2 rounded bg-brand-500 transition-all" style={{ width: `${Math.min(100, Math.max(0, percent))}%` }} />
      </div>
      <p className="mt-2 text-sm text-slate-600">Stage: {stage}</p>
      {job.error ? <p className="mt-2 text-sm text-red-600">{job.error}</p> : null}
    </div>
  );
}
