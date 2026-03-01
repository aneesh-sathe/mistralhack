"use client";

import { ButtonHTMLAttributes } from "react";

import { clsx } from "clsx";

export type ToastTone = "success" | "error" | "info";

interface ToastProps {
  title: string;
  description?: string;
  tone?: ToastTone;
  actionLabel?: string;
  onAction?: ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
  onClose?: () => void;
}

function toneClass(tone: ToastTone): string {
  if (tone === "success") return "border-emerald-200 bg-emerald-50 text-emerald-900";
  if (tone === "error") return "border-rose-200 bg-rose-50 text-rose-900";
  return "border-slate-200 bg-white text-slate-900";
}

export default function Toast({ title, description, tone = "info", actionLabel, onAction, onClose }: ToastProps) {
  return (
    <div className={clsx("w-full max-w-sm rounded-xl border p-3 shadow-[0_10px_24px_rgba(15,23,42,0.14)]", toneClass(tone))}>
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-sm font-semibold leading-tight">{title}</p>
          {description ? <p className="text-xs leading-relaxed text-slate-600">{description}</p> : null}
        </div>
        <button
          type="button"
          aria-label="Dismiss notification"
          onClick={onClose}
          className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-slate-300 bg-white text-xs font-semibold text-slate-600 transition hover:border-slate-500 hover:text-slate-900"
        >
          x
        </button>
      </div>

      {actionLabel && onAction ? (
        <div className="mt-3">
          <button
            type="button"
            onClick={onAction}
            className="inline-flex rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-700"
          >
            {actionLabel}
          </button>
        </div>
      ) : null}
    </div>
  );
}
