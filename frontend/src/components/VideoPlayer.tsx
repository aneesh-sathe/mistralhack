"use client";

import { useEffect, useRef } from "react";

import { videoUrl } from "@/lib/api";

interface VideoPlayerProps {
  moduleId: string;
  onTimeUpdate?: (time: number) => void;
  seekTo?: number | null;
  onSeekHandled?: () => void;
}

export default function VideoPlayer({ moduleId, onTimeUpdate, seekTo, onSeekHandled }: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (typeof seekTo !== "number") return;
    if (!ref.current) return;

    const target = Math.max(0, seekTo);
    ref.current.currentTime = target;

    const maybePromise = ref.current.play();
    if (maybePromise && typeof maybePromise.catch === "function") {
      maybePromise.catch(() => undefined);
    }

    onSeekHandled?.();
  }, [onSeekHandled, seekTo]);

  return (
    <div className="card overflow-hidden border-slate-200 p-3">
      <video
        ref={ref}
        className="aspect-video w-full rounded-2xl border border-slate-200 bg-black object-contain"
        controls
        crossOrigin="use-credentials"
        src={videoUrl(moduleId)}
        onTimeUpdate={() => {
          if (!ref.current || !onTimeUpdate) return;
          onTimeUpdate(ref.current.currentTime);
        }}
      />
    </div>
  );
}
