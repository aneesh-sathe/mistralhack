"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import CaptionPanel from "@/components/CaptionPanel";
import { useToast } from "@/components/ToastProvider";
import VideoPlayer from "@/components/VideoPlayer";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { deleteModule, generateModule, getModule, getModuleAssets } from "@/lib/api";
import {
  activeGenerationJobsEventName,
  trackedGenerationJobForModule,
  trackGenerationJob,
} from "@/lib/jobTracker";
import { ModuleAssets, ModuleItem } from "@/lib/types";

function statusTone(status: ModuleItem["status"] | undefined): string {
  if (status === "DONE") return "bg-emerald-100 text-emerald-800";
  if (status === "GENERATING") return "bg-amber-100 text-amber-900";
  if (status === "FAILED") return "bg-rose-100 text-rose-800";
  return "bg-slate-100 text-slate-700";
}

export default function ModulePage({ params }: { params: { moduleId: string } }) {
  const { moduleId } = params;
  const [module, setModule] = useState<ModuleItem | null>(null);
  const [assets, setAssets] = useState<ModuleAssets | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [startingGeneration, setStartingGeneration] = useState(false);
  const [videoTime, setVideoTime] = useState(0);
  const [seekTarget, setSeekTarget] = useState<number | null>(null);
  const [resumeAt, setResumeAt] = useState<number | null>(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { notify } = useToast();

  const load = useCallback(async () => {
    try {
      const mod = await getModule(moduleId);
      setModule(mod);
      try {
        const a = await getModuleAssets(moduleId);
        setAssets(a);
      } catch {
        setAssets(null);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load module");
    }
  }, [moduleId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const key = `learnstral.lesson-time.${moduleId}`;
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      setResumeAt(null);
      return;
    }
    const parsed = Number(raw);
    if (Number.isFinite(parsed) && parsed > 10) {
      setResumeAt(parsed);
    } else {
      setResumeAt(null);
    }
  }, [moduleId]);

  useEffect(() => {
    const refreshTracked = () => {
      const tracked = trackedGenerationJobForModule(moduleId);
      setJobId((prev) => {
        const next = tracked?.jobId || null;
        if (prev && !next) {
          void load();
        }
        return next;
      });
    };

    refreshTracked();
    const eventName = activeGenerationJobsEventName();
    window.addEventListener(eventName, refreshTracked);
    window.addEventListener("storage", refreshTracked);
    return () => {
      window.removeEventListener(eventName, refreshTracked);
      window.removeEventListener("storage", refreshTracked);
    };
  }, [load, moduleId]);

  useEffect(() => {
    if (!jobId && module?.status !== "GENERATING") return;
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, [jobId, load, module?.status]);

  const startGeneration = async () => {
    if (startingGeneration) return;
    try {
      setStartingGeneration(true);
      const res = await generateModule(moduleId);
      setJobId(res.job_id);
      trackGenerationJob({
        jobId: res.job_id,
        moduleId,
        moduleTitle: module?.title,
        createdAt: new Date().toISOString(),
      });
      setError(null);
      notify({
        title: "Generation started",
        description: module?.title || "Module",
        tone: "info",
        dedupeKey: `generation-start-${res.job_id}`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start generation");
      notify({
        title: "Generation failed to start",
        description: module?.title || "Module",
        tone: "error",
      });
    } finally {
      setStartingGeneration(false);
    }
  };

  const onDeleteModule = async () => {
    if (!module || deleting || module.status === "GENERATING") return;
    try {
      setDeleting(true);
      await deleteModule(module.id);
      notify({
        title: "Module deleted",
        description: module.title,
        tone: "success",
      });
      router.push(`/documents/${module.document_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete module");
      notify({
        title: "Delete failed",
        description: module.title,
        tone: "error",
      });
    } finally {
      setDeleting(false);
      setConfirmDeleteOpen(false);
    }
  };

  const canPlay = Boolean(assets?.final_muxed_path);
  const generationActive = startingGeneration || Boolean(jobId) || module?.status === "GENERATING";

  const onVideoTimeUpdate = (time: number) => {
    setVideoTime(time);
    if (typeof window === "undefined") return;
    window.localStorage.setItem(`learnstral.lesson-time.${moduleId}`, time.toFixed(2));
  };

  return (
    <section className="space-y-4">
      <header className="soft-section p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="max-w-3xl">
            <h1 className="text-3xl font-black text-slate-900">{module?.title || "Module"}</h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              {module?.summary || "Preparing module summary..."}
            </p>
          </div>
          <span className={`status-pill ${statusTone(module?.status)}`}>{module?.status || "loading"}</span>
        </div>
      </header>

      <div className="surface-muted flex flex-col items-start gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <div className="text-sm text-slate-600">Generate a fresh lesson package for this module (animation, voice, captions, final MP4).</div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={generationActive || deleting}
            onClick={() => setConfirmDeleteOpen(true)}
            className="inline-flex rounded-full border border-rose-200 bg-white px-4 py-2 text-sm font-semibold text-rose-700 transition hover:border-rose-400 disabled:opacity-60"
          >
            {deleting ? "Deleting..." : "Delete module"}
          </button>
          <Button onClick={startGeneration} disabled={generationActive || deleting}>
            {generationActive ? "Generating..." : "Generate Lesson"}
          </Button>
        </div>
      </div>

      {generationActive ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-800">
          Lesson generation is running in the background. Track progress in the activity panel above.
        </div>
      ) : null}

      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p> : null}

      {canPlay && resumeAt !== null ? (
        <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
          Resume where you left off?
          <button
            type="button"
            onClick={() => {
              setSeekTarget(resumeAt);
              setResumeAt(null);
            }}
            className="ml-2 rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-700"
          >
            Resume at {Math.floor(resumeAt / 60)}:{String(Math.floor(resumeAt % 60)).padStart(2, "0")}
          </button>
        </div>
      ) : null}

      {canPlay ? (
        <div className="grid gap-4 xl:grid-cols-[1.8fr_1fr]">
          <VideoPlayer
            moduleId={moduleId}
            onTimeUpdate={onVideoTimeUpdate}
            seekTo={seekTarget}
            onSeekHandled={() => setSeekTarget(null)}
          />
          <CaptionPanel moduleId={moduleId} currentTime={videoTime} onSeekTo={setSeekTarget} />
        </div>
      ) : (
        <div className="card p-5 text-sm text-slate-600">
          No final media available yet. Click <span className="font-bold text-slate-900">Generate Lesson</span> to produce the video and captions.
        </div>
      )}

      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Delete this module?"
        description={
          module
            ? `This will remove "${module.title}" and all generated lesson artifacts. This action cannot be undone.`
            : ""
        }
        confirmLabel={deleting ? "Deleting..." : "Delete module"}
        cancelLabel="Cancel"
        busy={deleting}
        onConfirm={onDeleteModule}
        onCancel={() => {
          if (!deleting) setConfirmDeleteOpen(false);
        }}
        tone="danger"
      />
    </section>
  );
}
