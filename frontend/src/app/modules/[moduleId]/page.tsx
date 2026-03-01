"use client";

import { useCallback, useEffect, useState } from "react";

import CaptionPanel from "@/components/CaptionPanel";
import JobProgress from "@/components/JobProgress";
import VideoPlayer from "@/components/VideoPlayer";
import { Button } from "@/components/ui/button";
import { generateModule, getModule, getModuleAssets } from "@/lib/api";
import { JobItem, ModuleAssets, ModuleItem } from "@/lib/types";

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
  const [videoTime, setVideoTime] = useState(0);
  const [error, setError] = useState<string | null>(null);

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

  const startGeneration = async () => {
    try {
      const res = await generateModule(moduleId);
      setJobId(res.job_id);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start generation");
    }
  };

  const onJobComplete = async (_job: JobItem) => {
    await load();
  };

  const canPlay = Boolean(assets?.final_muxed_path);

  return (
    <section className="space-y-4">
      <header className="soft-section p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 className="text-3xl font-black text-slate-900">{module?.title || "Module"}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-700">{module?.summary || "Preparing module summary..."}</p>
          </div>
          <span className={`status-pill ${statusTone(module?.status)}`}>{module?.status || "loading"}</span>
        </div>
      </header>

      <div className="surface-muted flex flex-col items-start gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <div className="text-sm text-slate-700">Generate a fresh lesson package for this module (script, animation, voice, captions, final MP4).</div>
        <Button onClick={startGeneration}>Generate Lesson</Button>
      </div>

      <JobProgress jobId={jobId} onComplete={onJobComplete} />

      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p> : null}

      {canPlay ? (
        <div className="grid gap-4 xl:grid-cols-[1.8fr_1fr]">
          <VideoPlayer moduleId={moduleId} onTimeUpdate={setVideoTime} />
          <CaptionPanel moduleId={moduleId} currentTime={videoTime} />
        </div>
      ) : (
        <div className="card p-5 text-sm text-slate-700">
          No final media available yet. Click <span className="font-bold">Generate Lesson</span> to produce the video and captions.
        </div>
      )}
    </section>
  );
}
