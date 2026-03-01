"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

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

function tone(status: JobItem["status"] | "loading"): { pill: string; pulse: boolean } {
  if (status === "succeeded") return { pill: "bg-emerald-100 text-emerald-800", pulse: false };
  if (status === "failed") return { pill: "bg-rose-100 text-rose-800", pulse: false };
  if (status === "running") return { pill: "bg-amber-100 text-amber-800", pulse: true };
  return { pill: "bg-slate-100 text-slate-700", pulse: false };
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

// Page visibility API hook
function usePageVisible() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const onChange = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);
  return visible;
}

export default function GlobalJobProgress() {
  const [tracked, setTracked] = useState<TrackedJob[]>([]);
  const [jobsById, setJobsById] = useState<Record<string, JobItem>>({});
  const [errorById, setErrorById] = useState<Record<string, string>>({});
  const [collapsed, setCollapsed] = useState(false);
  const { notify } = useToast();
  const router = useRouter();
  const pageVisible = usePageVisible();

  const refreshTracked = useCallback(() => {
    setTracked(readTrackedJobs());
  }, []);

  useEffect(() => {
    refreshTracked();
    const eventName = activeGenerationJobsEventName();
    const onUpdate = () => refreshTracked();
    window.addEventListener(eventName, onUpdate);
    window.addEventListener("storage", onUpdate);
    return () => {
      window.removeEventListener(eventName, onUpdate);
      window.removeEventListener("storage", onUpdate);
    };
  }, [refreshTracked]);

  useEffect(() => {
    if (!tracked.length || !pageVisible) {
      setJobsById({});
      setErrorById({});
      return;
    }

    let active = true;

    const poll = async () => {
      if (!active || !pageVisible) return;
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
                ? entry.entityType === "module" ? "Lesson ready! 🎉" : "Document processed ✅"
                : entry.entityType === "module" ? "Lesson generation failed" : "Document processing failed",
              description: activityLabel(entry),
              tone: success ? "success" : "error",
              action: {
                label: success
                  ? entry.entityType === "module" ? "Open lesson" : "Open modules"
                  : "View details",
                onClick: () => router.push(activityHref(entry)),
              },
              dedupeKey: `job-complete-${jobId}`,
            });
          }

          untrackJob(jobId);
        }
        refreshTracked();
      }
    };

    poll();
    const intervalId = setInterval(poll, 2500);
    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, [notify, router, tracked, pageVisible, refreshTracked]);

  const visible = useMemo(
    () => [...tracked].sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
    [tracked]
  );

  if (!visible.length) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.25 }}
        className="mx-auto w-full max-w-[1110px] px-4 pb-2 pt-4 sm:px-6"
      >
        <div className="surface-muted p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <motion.div
                className="h-1.5 w-1.5 rounded-full bg-amber-500"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              />
              <span className="text-xs font-bold uppercase tracking-[0.08em] text-slate-500">
                Background Activity ({visible.length})
              </span>
            </div>
            <button
              type="button"
              onClick={() => setCollapsed((v) => !v)}
              className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              aria-label={collapsed ? "Expand activity panel" : "Collapse activity panel"}
            >
              <motion.svg
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                animate={{ rotate: collapsed ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </motion.svg>
            </button>
          </div>

          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="space-y-2 pt-1">
                  {visible.map((entry) => {
                    const job = jobsById[entry.jobId];
                    const error = errorById[entry.jobId];
                    const status = job?.status || "loading";
                    const stage = formatStageLabel(job?.progress?.stage);
                    const percent = clampPercent(job?.progress?.percent);
                    const { pill, pulse } = tone(status);

                    return (
                      <div key={entry.jobId} className="rounded-xl border border-slate-200 bg-white p-3">
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <Link href={activityHref(entry)} className="text-sm font-semibold text-slate-700 hover:text-brand-600">
                            {activityLabel(entry)}
                          </Link>
                          <span className={`status-pill ${pill}`}>
                            {pulse && (
                              <motion.span
                                className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current"
                                animate={{ opacity: [0.4, 1, 0.4] }}
                                transition={{ duration: 1.2, repeat: Infinity }}
                              />
                            )}
                            {statusLabel(status)}
                          </span>
                        </div>
                        <div className="mb-2 flex items-center justify-between gap-2 text-xs font-semibold text-slate-500">
                          <span>{stage}</span>
                          <span>{percent}%</span>
                        </div>
                        <div className="progress-bar">
                          <motion.div
                            className="progress-bar-fill"
                            animate={{ width: `${percent}%` }}
                            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                          />
                        </div>
                        {error && <p className="mt-2 text-xs font-medium text-rose-700">{error}</p>}
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
