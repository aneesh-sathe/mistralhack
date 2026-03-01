"use client";

import { motion } from "framer-motion";
import { fadeUp } from "@/lib/animations";
import { Button } from "@/components/ui/button";

function BrokenWandIllustration() {
  return (
    <svg width="100" height="90" viewBox="0 0 100 90" fill="none" aria-hidden="true">
      {/* Wand handle */}
      <rect x="10" y="58" width="45" height="8" rx="4" fill="#c9c1ff" transform="rotate(-40 10 58)" />
      {/* Wand top part - broken */}
      <rect x="52" y="20" width="38" height="8" rx="4" fill="#a99cff" transform="rotate(-40 52 20)" />
      {/* Break spark */}
      <path d="M48 44L52 38L50 44L56 40L52 46L56 44L50 50" stroke="#ff9f43" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      {/* Stars */}
      <circle cx="72" cy="14" r="3" fill="#ffe22a" />
      <circle cx="82" cy="28" r="2" fill="#ff6eb4" />
      <circle cx="20" cy="22" r="2" fill="#56ea99" />
      {/* Sad face */}
      <circle cx="54" cy="70" r="12" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      <circle cx="50" cy="67" r="1.5" fill="#a99cff" />
      <circle cx="58" cy="67" r="1.5" fill="#a99cff" />
      <path d="M50 74C50 74 52 72 58 74" stroke="#a99cff" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function DisconnectedPlugIllustration() {
  return (
    <svg width="100" height="90" viewBox="0 0 100 90" fill="none" aria-hidden="true">
      {/* Plug left part */}
      <rect x="10" y="38" width="36" height="14" rx="7" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      <line x1="18" y1="28" x2="18" y2="38" stroke="#c9c1ff" strokeWidth="3" strokeLinecap="round" />
      <line x1="28" y1="28" x2="28" y2="38" stroke="#c9c1ff" strokeWidth="3" strokeLinecap="round" />
      {/* Gap */}
      <path d="M46 45H54" stroke="#fbbf24" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="2 2" />
      {/* Plug right part */}
      <rect x="54" y="38" width="36" height="14" rx="7" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      <line x1="72" y1="52" x2="72" y2="62" stroke="#c9c1ff" strokeWidth="3" strokeLinecap="round" />
      <line x1="82" y1="52" x2="82" y2="62" stroke="#c9c1ff" strokeWidth="3" strokeLinecap="round" />
      {/* Sparks in gap */}
      <path d="M49 38L52 44L49 50" stroke="#ff9f43" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export function GenerationError({ message, onRetry, className }: ErrorStateProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center gap-4 py-10 text-center ${className || ""}`}
    >
      <motion.div
        animate={{ rotate: [0, -3, 3, -3, 0] }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <BrokenWandIllustration />
      </motion.div>
      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-800">Generation hit a snag</h3>
        <p className="max-w-xs text-sm text-slate-500">
          {message || "Something went wrong while generating your lesson. This sometimes happens — try again!"}
        </p>
      </div>
      {onRetry && (
        <Button onClick={onRetry} className="min-w-[120px]">
          Try again
        </Button>
      )}
    </motion.div>
  );
}

export function UploadError({ message, onRetry, className }: ErrorStateProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`rounded-xl border border-rose-200 bg-rose-50 p-4 ${className || ""}`}
    >
      <div className="flex items-start gap-3">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="mt-0.5 shrink-0">
          <circle cx="10" cy="10" r="9" fill="#fecdd3" stroke="#f43f5e" strokeWidth="1.5" />
          <path d="M7 7L13 13M13 7L7 13" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <div className="flex-1 space-y-1">
          <p className="text-sm font-semibold text-rose-800">Upload didn&apos;t quite work</p>
          <p className="text-xs text-rose-600">{message || "Only PDF files under 50MB are accepted."}</p>
        </div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded-full border border-rose-200 bg-white px-3 py-1 text-xs font-semibold text-rose-700 hover:border-rose-400"
          >
            Try again
          </button>
        )}
      </div>
    </motion.div>
  );
}

export function NetworkError({ onRetry, countdown, className }: ErrorStateProps & { countdown?: number }) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center gap-4 py-8 text-center ${className || ""}`}
    >
      <DisconnectedPlugIllustration />
      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-800">Connection lost</h3>
        <p className="text-sm text-slate-500">
          {countdown != null && countdown > 0
            ? `Retrying in ${countdown}s...`
            : "Check your connection and try again."}
        </p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:border-slate-700"
        >
          Retry now
        </button>
      )}
    </motion.div>
  );
}
