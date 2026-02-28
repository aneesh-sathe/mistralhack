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
    <video
      ref={ref}
      className="w-full rounded-lg border border-slate-200 bg-black"
      controls
      crossOrigin="use-credentials"
      src={videoUrl(moduleId)}
      onTimeUpdate={() => {
        if (!ref.current || !onTimeUpdate) return;
        onTimeUpdate(ref.current.currentTime);
      }}
    />
  );
}
