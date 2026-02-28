"use client";

import { useCallback, useEffect, useState } from "react";

import CaptionPanel from "@/components/CaptionPanel";
import JobProgress from "@/components/JobProgress";
import VideoPlayer from "@/components/VideoPlayer";
import { Button } from "@/components/ui/button";
import { generateModule, getModule, getModuleAssets } from "@/lib/api";
import { JobItem, ModuleAssets, ModuleItem } from "@/lib/types";

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
      <header className="card p-4">
        <h1 className="font-display text-2xl font-bold text-slate-900">{module?.title || "Module"}</h1>
        <p className="text-sm text-slate-600">{module?.summary || ""}</p>
        <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">Status: {module?.status || "loading"}</p>
      </header>

      <div className="flex items-center gap-3">
        <Button onClick={startGeneration}>Generate Lesson</Button>
        {assets ? <span className="text-sm text-slate-600">Asset status: {assets.status}</span> : null}
      </div>

      <JobProgress jobId={jobId} onComplete={onJobComplete} />

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {canPlay ? (
        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <VideoPlayer moduleId={moduleId} onTimeUpdate={setVideoTime} />
          <CaptionPanel moduleId={moduleId} currentTime={videoTime} />
        </div>
      ) : (
        <div className="card p-4 text-sm text-slate-600">
          Generate assets to view the lesson video and synced captions.
        </div>
      )}
    </section>
  );
}
