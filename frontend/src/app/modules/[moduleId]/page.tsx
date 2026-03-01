"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import CaptionPanel from "@/components/CaptionPanel";
import Confetti from "@/components/Confetti";
import SuccessAnimation from "@/components/SuccessAnimation";
import PageTransition from "@/components/PageTransition";
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
import { fadeUp } from "@/lib/animations";
import { ModuleAssets, ModuleItem } from "@/lib/types";

function statusConfig(status: ModuleItem["status"] | undefined): { pill: string; pulse: boolean } {
  if (status === "DONE") return { pill: "bg-emerald-100 text-emerald-800", pulse: false };
  if (status === "GENERATING") return { pill: "bg-amber-100 text-amber-900", pulse: true };
  if (status === "FAILED") return { pill: "bg-rose-100 text-rose-800", pulse: false };
  return { pill: "bg-slate-100 text-slate-700", pulse: false };
}

const GENERATING_COPY = [
  "Crafting your lesson... ✨",
  "Teaching the AI to teach... 🎓",
  "Animating knowledge... 🎨",
  "Brewing some wisdom... ☕",
  "Rendering frames of insight...",
];

export default function ModulePage({ params }: { params: { moduleId: string } }) {
  const { moduleId } = params;
  const [module, setModule] = useState<ModuleItem | null>(null);
  const [assets, setAssets] = useState<ModuleAssets | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [startingGeneration, setStartingGeneration] = useState(false);
  const [videoTime, setVideoTime] = useState(0);
  const [seekTarget, setSeekTarget] = useState<number | null>(null);
  const [resumeAt, setResumeAt] = useState<number | null>(null);
  // Used to skip the grid fade-in animation on re-mounts (prevents whitewash replay).
  const videoGridShown = useRef(false);
  useEffect(() => {
    if (canPlay) videoGridShown.current = true;
  });
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confetti, setConfetti] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [copyIndex, setCopyIndex] = useState(0);
  const router = useRouter();
  const { notify } = useToast();

  const load = useCallback(async () => {
    try {
      const mod = await getModule(moduleId);
      setModule((prev) => {
        // Detect transition to DONE → trigger celebration
        if (prev?.status === "GENERATING" && mod.status === "DONE") {
          setConfetti(true);
          setShowSuccess(true);
          setTimeout(() => setConfetti(false), 3000);
          setTimeout(() => setShowSuccess(false), 2500);
        }
        return mod;
      });
      try {
        const a = await getModuleAssets(moduleId);
        // Never regress from a valid video path to none (e.g. during regeneration
        // or when the backend is busy with a background job).
        setAssets((prev) => {
          if (!a?.final_muxed_path && prev?.final_muxed_path) return prev;
          return a;
        });
      } catch {
        // Keep existing assets on error too.
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load module");
    }
  }, [moduleId]);

  useEffect(() => {
    load();
  }, [load]);

  // Resume position
  useEffect(() => {
    if (typeof window === "undefined") return;
    const key = `learnstral.lesson-time.${moduleId}`;
    const raw = window.localStorage.getItem(key);
    if (!raw) { setResumeAt(null); return; }
    const parsed = Number(raw);
    if (Number.isFinite(parsed) && parsed > 10) setResumeAt(parsed);
    else setResumeAt(null);
  }, [moduleId]);

  // Track generation job
  useEffect(() => {
    const refreshTracked = () => {
      const tracked = trackedGenerationJobForModule(moduleId);
      setJobId((prev) => {
        const next = tracked?.jobId || null;
        if (prev && !next) void load();
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

  // Poll while generating
  useEffect(() => {
    if (!jobId && module?.status !== "GENERATING") return;
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, [jobId, load, module?.status]);

  // Cycle copy during generation
  useEffect(() => {
    if (!startingGeneration && !jobId && module?.status !== "GENERATING") return;
    const id = setInterval(() => {
      setCopyIndex((prev) => (prev + 1) % GENERATING_COPY.length);
    }, 2800);
    return () => clearInterval(id);
  }, [startingGeneration, jobId, module?.status]);

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
        title: "Generation started ✨",
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
      notify({ title: "Module deleted", description: module.title, tone: "success" });
      router.push(`/documents/${module.document_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete module");
      notify({ title: "Delete failed", description: module.title, tone: "error" });
    } finally {
      setDeleting(false);
      setConfirmDeleteOpen(false);
    }
  };

  const canPlay = Boolean(assets?.final_muxed_path);
  const generationActive = startingGeneration || Boolean(jobId) || module?.status === "GENERATING";
  const { pill, pulse } = statusConfig(module?.status);

  const onVideoTimeUpdate = (time: number) => {
    setVideoTime(time);
    if (typeof window === "undefined") return;
    window.localStorage.setItem(`learnstral.lesson-time.${moduleId}`, time.toFixed(2));
  };

  return (
    <PageTransition>
      <Confetti active={confetti} />

      <section className="space-y-4">
        <header className="soft-section p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="max-w-3xl">
              <h1 className="text-3xl font-black text-slate-900">{module?.title || "Module"}</h1>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">
                {module?.summary || "Preparing module summary..."}
              </p>
            </div>
            <span className={`status-pill self-start ${pill}`}>
              {pulse && (
                <motion.span
                  className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current"
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                />
              )}
              {module?.status || "loading"}
            </span>
          </div>
        </header>

        <div className="surface-muted flex flex-col items-start gap-3 p-4 md:flex-row md:items-center md:justify-between">
          <div className="text-sm text-slate-600">
            Generate a fresh lesson package for this module (animation, voice, captions, final MP4).
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={generationActive || deleting}
              onClick={() => setConfirmDeleteOpen(true)}
              className="inline-flex rounded-full border border-rose-200 bg-white px-4 py-2 text-sm font-semibold text-rose-700 transition hover:border-rose-400 disabled:opacity-60"
            >
              {deleting ? "Deleting..." : "Delete module"}
            </button>
            <Button
              onClick={startGeneration}
              disabled={generationActive || deleting}
              loading={generationActive}
            >
              {generationActive ? GENERATING_COPY[copyIndex] : "Generate Lesson ✨"}
            </Button>
          </div>
        </div>

        <AnimatePresence>
          {generationActive && (
            <motion.div
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              exit={{ opacity: 0, y: -4, transition: { duration: 0.2 } }}
              className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <div className="waveform">
                  {Array.from({ length: 5 }, (_, i) => (
                    <div key={i} className="waveform-bar" style={{ animationDelay: `${i * 0.1}s` }} />
                  ))}
                </div>
                <p className="text-sm font-medium text-amber-800">
                  Lesson generation is running in the background. Track progress in the activity panel above.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0, transition: { type: "spring", stiffness: 400 } }}
              exit={{ opacity: 0 }}
              className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {canPlay && resumeAt !== null && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            >
              Resume where you left off?
              <button
                type="button"
                onClick={() => { setSeekTarget(resumeAt); setResumeAt(null); }}
                className="ml-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 transition hover:border-brand-400"
              >
                Resume at {Math.floor(resumeAt / 60)}:{String(Math.floor(resumeAt % 60)).padStart(2, "0")}
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Success celebration overlay */}
        <AnimatePresence>
          {showSuccess && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="fixed inset-0 z-40 flex items-center justify-center pointer-events-none"
            >
              <div className="flex flex-col items-center gap-4 rounded-3xl bg-white/90 px-12 py-10 shadow-lift-lg backdrop-blur-sm">
                <SuccessAnimation size={80} />
                <p className="text-xl font-black text-slate-900">Lesson Ready! 🎉</p>
                <p className="text-sm text-slate-500">Your video and captions are ready to watch.</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {canPlay ? (
          <motion.div
            initial={videoGridShown.current ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="grid gap-4 xl:grid-cols-[1.8fr_1fr]"
          >
            <VideoPlayer
              moduleId={moduleId}
              onTimeUpdate={onVideoTimeUpdate}
              seekTo={seekTarget}
              onSeekHandled={() => setSeekTarget(null)}
            />
            <CaptionPanel moduleId={moduleId} currentTime={videoTime} onSeekTo={setSeekTarget} />
          </motion.div>
        ) : (
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            className="card p-5 text-sm text-slate-600"
          >
            No final media available yet. Click{" "}
            <span className="font-bold text-slate-900">Generate Lesson ✨</span>{" "}
            to produce the video and captions.
          </motion.div>
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
          onCancel={() => { if (!deleting) setConfirmDeleteOpen(false); }}
          tone="danger"
        />
      </section>
    </PageTransition>
  );
}
