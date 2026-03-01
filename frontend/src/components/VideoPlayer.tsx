"use client";

import { useRef } from "react";

import { videoUrl } from "@/lib/api";

interface VideoPlayerProps {
  moduleId: string;
  onTimeUpdate?: (time: number) => void;
}

export default function VideoPlayer({ moduleId, onTimeUpdate }: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement | null>(null);

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
