"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { videoUrl } from "@/lib/api";

interface VideoPlayerProps {
  moduleId: string;
  onTimeUpdate?: (time: number) => void;
  seekTo?: number | null;
  onSeekHandled?: () => void;
}

function PlayIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path d="M6.5 4.5l9 5.5-9 5.5V4.5z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <rect x="4.5" y="3.5" width="4" height="13" rx="1.5" />
      <rect x="11.5" y="3.5" width="4" height="13" rx="1.5" />
    </svg>
  );
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

export default function VideoPlayer({ moduleId, onTimeUpdate, seekTo, onSeekHandled }: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [seekIndicator, setSeekIndicator] = useState<string | null>(null);
  const [speed, setSpeed] = useState(1);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-hide controls
  const resetHideTimer = useCallback(() => {
    setShowControls(true);
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    hideTimerRef.current = setTimeout(() => {
      if (playing) setShowControls(false);
    }, 3000);
  }, [playing]);

  useEffect(() => {
    return () => { if (hideTimerRef.current) clearTimeout(hideTimerRef.current); };
  }, []);

  useEffect(() => {
    if (!playing) {
      setShowControls(true);
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    }
  }, [playing]);

  // Seek effect
  useEffect(() => {
    if (typeof seekTo !== "number" || !ref.current) return;
    ref.current.currentTime = Math.max(0, seekTo);
    const p = ref.current.play();
    if (p?.catch) p.catch(() => undefined);
    onSeekHandled?.();
  }, [onSeekHandled, seekTo]);

  const showSeekIndicator = (text: string) => {
    setSeekIndicator(text);
    setTimeout(() => setSeekIndicator(null), 800);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const video = ref.current;
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
      if (!containerRef.current?.matches(":focus-within") && document.activeElement !== containerRef.current) {
        // Only handle if video container is focused or no other input
        if (target.tagName !== "BODY") return;
      }
      if (!video) return;

      switch (e.key) {
        case " ":
        case "k":
          e.preventDefault();
          if (video.paused) video.play().catch(() => undefined);
          else video.pause();
          break;
        case "ArrowRight":
          e.preventDefault();
          video.currentTime = Math.min(video.duration, video.currentTime + 5);
          showSeekIndicator("+5s");
          break;
        case "ArrowLeft":
          e.preventDefault();
          video.currentTime = Math.max(0, video.currentTime - 5);
          showSeekIndicator("-5s");
          break;
        case "ArrowUp":
          e.preventDefault();
          video.volume = Math.min(1, video.volume + 0.1);
          setVolume(video.volume);
          showSeekIndicator(`Vol ${Math.round(video.volume * 100)}%`);
          break;
        case "ArrowDown":
          e.preventDefault();
          video.volume = Math.max(0, video.volume - 0.1);
          setVolume(video.volume);
          showSeekIndicator(`Vol ${Math.round(video.volume * 100)}%`);
          break;
        case "m":
        case "M":
          video.muted = !video.muted;
          setMuted(video.muted);
          showSeekIndicator(video.muted ? "Muted" : "Unmuted");
          break;
        case "f":
        case "F":
          if (document.fullscreenElement) document.exitFullscreen();
          else containerRef.current?.requestFullscreen();
          break;
        default:
          if (e.key >= "0" && e.key <= "9") {
            const pct = Number(e.key) * 0.1;
            video.currentTime = video.duration * pct;
            showSeekIndicator(`${Number(e.key) * 10}%`);
          }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const togglePlay = () => {
    const video = ref.current;
    if (!video) return;
    if (video.paused) video.play().catch(() => undefined);
    else video.pause();
  };

  const onScrubberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = ref.current;
    if (!video) return;
    video.currentTime = Number(e.target.value);
  };

  const onVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = ref.current;
    if (!video) return;
    const v = Number(e.target.value);
    video.volume = v;
    video.muted = v === 0;
    setVolume(v);
    setMuted(v === 0);
  };

  const cycleSpeed = () => {
    const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
    const idx = speeds.indexOf(speed);
    const next = speeds[(idx + 1) % speeds.length];
    setSpeed(next);
    if (ref.current) ref.current.playbackRate = next;
    showSeekIndicator(`${next}x`);
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className="card relative overflow-hidden border-slate-200 p-0 group"
      onMouseMove={resetHideTimer}
      onMouseEnter={resetHideTimer}
      tabIndex={0}
      style={{ outline: "none" }}
    >
      {/* Video */}
      <div className="relative aspect-video w-full bg-black" onClick={togglePlay}>
        <video
          ref={ref}
          className="h-full w-full object-contain"
          crossOrigin="use-credentials"
          src={videoUrl(moduleId)}
          onTimeUpdate={() => {
            const v = ref.current;
            if (!v) return;
            setCurrentTime(v.currentTime);
            onTimeUpdate?.(v.currentTime);
          }}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onLoadedMetadata={() => { if (ref.current) setDuration(ref.current.duration); }}
          onVolumeChange={() => { if (ref.current) { setVolume(ref.current.volume); setMuted(ref.current.muted); } }}
        />

        {/* Center play/pause flash */}
        <AnimatePresence>
          {!playing && (
            <motion.div
              key="paused-icon"
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.2 }}
              transition={{ duration: 0.2 }}
              className="pointer-events-none absolute inset-0 flex items-center justify-center"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm">
                <PlayIcon />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Seek indicator */}
        <AnimatePresence>
          {seekIndicator && (
            <motion.div
              key={seekIndicator}
              initial={{ opacity: 0, y: 4, x: "-50%" }}
              animate={{ opacity: 1, y: 0, x: "-50%" }}
              exit={{ opacity: 0, y: -8, x: "-50%" }}
              className="pointer-events-none absolute top-4 left-1/2 rounded-full bg-black/60 px-4 py-1.5 text-sm font-semibold text-white backdrop-blur-sm"
            >
              {seekIndicator}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls bar */}
      <motion.div
        animate={{ opacity: showControls ? 1 : 0, y: showControls ? 0 : 6 }}
        transition={{ duration: 0.2 }}
        className="flex flex-col gap-2 bg-white p-3"
      >
        {/* Scrubber */}
        <div className="group/scrub relative flex items-center gap-2">
          <span className="shrink-0 text-xs tabular-nums text-slate-500">{formatTime(currentTime)}</span>
          <div className="relative flex-1">
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-brand-500 transition-none"
                style={{ width: `${progress}%` }}
              />
            </div>
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              step={0.1}
              onChange={onScrubberChange}
              className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
              aria-label="Video progress"
            />
          </div>
          <span className="shrink-0 text-xs tabular-nums text-slate-500">{formatTime(duration)}</span>
        </div>

        {/* Control buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={togglePlay}
            aria-label={playing ? "Pause" : "Play"}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-500 text-white transition hover:bg-brand-700 active:scale-95"
          >
            {playing ? <PauseIcon /> : <PlayIcon />}
          </button>

          {/* Volume */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => { if (ref.current) { ref.current.muted = !muted; setMuted(!muted); } }}
              aria-label={muted ? "Unmute" : "Mute"}
              className="flex h-7 w-7 items-center justify-center rounded text-slate-500 hover:text-slate-900"
            >
              {muted || volume === 0 ? (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 6H5L9 3V13L5 10H2V6Z" fill="currentColor" />
                  <path d="M13 5L11 8M11 5L13 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 6H5L9 3V13L5 10H2V6Z" fill="currentColor" />
                  <path d="M11 5.5C12.5 6.5 12.5 9.5 11 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={muted ? 0 : volume}
              onChange={onVolumeChange}
              className="w-16 cursor-pointer accent-brand-500"
              aria-label="Volume"
            />
          </div>

          <div className="ml-auto flex items-center gap-1.5">
            {/* Speed */}
            <button
              type="button"
              onClick={cycleSpeed}
              className="rounded-full border border-slate-200 px-2 py-0.5 text-xs font-semibold text-slate-600 hover:border-slate-400"
            >
              {speed}x
            </button>

            {/* Fullscreen */}
            <button
              type="button"
              onClick={() => {
                if (document.fullscreenElement) document.exitFullscreen();
                else containerRef.current?.requestFullscreen();
              }}
              aria-label="Fullscreen"
              className="flex h-7 w-7 items-center justify-center rounded text-slate-500 hover:text-slate-900"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1 4.5V1H4.5M9.5 1H13V4.5M13 9.5V13H9.5M4.5 13H1V9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
