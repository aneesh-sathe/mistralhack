"use client";

import { ButtonHTMLAttributes, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";

export type ToastTone = "success" | "error" | "info";

interface ToastProps {
  title: string;
  description?: string;
  tone?: ToastTone;
  actionLabel?: string;
  durationMs?: number;
  onAction?: ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
  onClose?: () => void;
}

const toneConfig: Record<
  ToastTone,
  { container: string; icon: React.ReactNode; bar: string }
> = {
  success: {
    container: "border-emerald-200 bg-emerald-50 text-emerald-900",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" fill="#10b981" />
        <path d="M4.5 8L7 10.5L11.5 5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    bar: "bg-emerald-500",
  },
  error: {
    container: "border-rose-200 bg-rose-50 text-rose-900",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" fill="#f43f5e" />
        <path d="M5.5 5.5L10.5 10.5M10.5 5.5L5.5 10.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    bar: "bg-rose-500",
  },
  info: {
    container: "border-slate-200 bg-white text-slate-900",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" fill="#6366f1" />
        <path d="M8 7.5V11M8 5.5V6" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    bar: "bg-indigo-500",
  },
};

export default function Toast({
  title,
  description,
  tone = "info",
  actionLabel,
  durationMs = 7000,
  onAction,
  onClose,
}: ToastProps) {
  const [progress, setProgress] = useState(100);
  const config = toneConfig[tone];

  useEffect(() => {
    if (durationMs <= 0) return;
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / durationMs) * 100);
      setProgress(remaining);
      if (remaining === 0) clearInterval(interval);
    }, 50);
    return () => clearInterval(interval);
  }, [durationMs]);

  return (
    <div
      className={clsx(
        "relative w-full max-w-sm overflow-hidden rounded-xl border shadow-lift",
        config.container
      )}
    >
      <div className="flex items-start gap-3 p-3 pr-10">
        <span className="mt-0.5 shrink-0">{config.icon}</span>
        <div className="min-w-0 flex-1 space-y-0.5">
          <p className="text-sm font-semibold leading-tight">{title}</p>
          {description ? (
            <p className="text-xs leading-relaxed opacity-70">{description}</p>
          ) : null}
        </div>
      </div>

      <button
        type="button"
        aria-label="Dismiss notification"
        onClick={onClose}
        className="absolute right-2 top-2 inline-flex h-6 w-6 items-center justify-center rounded-full opacity-50 transition hover:opacity-100"
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M1 1L9 9M9 1L1 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      {actionLabel && onAction ? (
        <div className="px-3 pb-3">
          <button
            type="button"
            onClick={onAction}
            className="inline-flex rounded-full border border-current/20 bg-white/60 px-3 py-1.5 text-xs font-semibold transition hover:bg-white"
          >
            {actionLabel}
          </button>
        </div>
      ) : null}

      {/* Auto-dismiss progress bar */}
      {durationMs > 0 && (
        <div className="absolute bottom-0 left-0 h-0.5 w-full bg-current/10">
          <div
            className={clsx("h-full transition-none", config.bar, "opacity-40")}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}
