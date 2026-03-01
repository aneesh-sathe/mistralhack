"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const UPLOAD_COPY = [
  "Uploading your PDF... 📤",
  "Preparing your document...",
  "Almost there...",
];

const PARSING_COPY = [
  "Turning PDFs into magic... 🪄",
  "Reading every page carefully...",
  "Extracting knowledge...",
  "Finding all the good stuff...",
];

const GENERATING_COPY = [
  "Crafting your lesson... ✨",
  "Teaching the AI to teach... 🎓",
  "Animating knowledge... 🎨",
  "Brewing some wisdom... ☕",
  "Rendering frames of insight...",
  "Mixing audio and visuals...",
];

const PROCESSING_COPY = [
  "Processing in the background...",
  "Crunching numbers...",
  "Almost ready...",
];

function useCyclingCopy(copies: string[], intervalMs = 2800) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((prev) => (prev + 1) % copies.length);
    }, intervalMs);
    return () => clearInterval(id);
  }, [copies.length, intervalMs]);

  return copies[index];
}

function Waveform({ color = "#5f43ff" }: { color?: string }) {
  return (
    <div className="waveform">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="waveform-bar" style={{ backgroundColor: color, animationDelay: `${i * 0.1}s` }} />
      ))}
    </div>
  );
}

function BookPages() {
  return (
    <div className="relative h-10 w-10">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute inset-0 rounded border-2 border-brand-300 bg-brand-50"
          animate={{
            rotate: [0, -15 + i * 5, 0],
            x: [0, -4 + i * 2, 0],
          }}
          transition={{
            duration: 1.2,
            delay: i * 0.15,
            repeat: Infinity,
            repeatDelay: 0.3,
          }}
          style={{ transformOrigin: "bottom left" }}
        />
      ))}
      <div className="absolute inset-0 rounded border-2 border-brand-500 bg-brand-100" />
    </div>
  );
}

function FilmStrip() {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <motion.div
          key={i}
          className="h-10 w-7 rounded bg-slate-200"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.2, delay: i * 0.2, repeat: Infinity }}
        />
      ))}
    </div>
  );
}

interface LoadingStateProps {
  type: "upload" | "parsing" | "generating" | "processing";
  className?: string;
}

export function LoadingState({ type, className }: LoadingStateProps) {
  const copies = {
    upload: UPLOAD_COPY,
    parsing: PARSING_COPY,
    generating: GENERATING_COPY,
    processing: PROCESSING_COPY,
  }[type];

  const copy = useCyclingCopy(copies);

  const illustration = {
    upload: (
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 1.4, repeat: Infinity }}
      >
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="12" fill="#f2efff" />
          <path d="M14 24V26H26V24M20 14V22M20 14L16 18M20 14L24 18" stroke="#5f43ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </motion.div>
    ),
    parsing: <BookPages />,
    generating: <Waveform />,
    processing: <FilmStrip />,
  }[type];

  return (
    <motion.div
      className={`flex flex-col items-center gap-4 p-8 ${className || ""}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {illustration}
      <motion.p
        key={copy}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: 0.3 }}
        className="text-sm font-semibold text-slate-600"
      >
        {copy}
      </motion.p>
    </motion.div>
  );
}

export function SkeletonCard() {
  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="shimmer h-5 w-32 rounded-lg" />
        <div className="shimmer h-5 w-16 rounded-full" />
      </div>
      <div className="shimmer mb-4 h-4 w-full rounded-lg" />
      <div className="shimmer h-4 w-2/3 rounded-lg" />
      <div className="mt-4 flex gap-2">
        <div className="shimmer h-8 w-24 rounded-full" />
        <div className="shimmer h-8 w-16 rounded-full" />
      </div>
    </div>
  );
}
