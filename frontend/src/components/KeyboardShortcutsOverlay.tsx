"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { scaleIn } from "@/lib/animations";

interface Shortcut {
  key: string;
  description: string;
}

const VIDEO_SHORTCUTS: Shortcut[] = [
  { key: "Space", description: "Play / Pause" },
  { key: "← →", description: "Seek ±5 seconds" },
  { key: "↑ ↓", description: "Volume ±10%" },
  { key: "M", description: "Mute / Unmute" },
  { key: "F", description: "Fullscreen" },
  { key: "0–9", description: "Jump to 0–90%" },
  { key: ", .", description: "Previous / Next caption" },
];

const GLOBAL_SHORTCUTS: Shortcut[] = [
  { key: "?", description: "Show / hide shortcuts" },
];

export default function KeyboardShortcutsOverlay() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
      if (e.key === "?") {
        setOpen((v) => !v);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
          />
          <motion.div
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-6 shadow-lift-lg"
            variants={scaleIn}
            initial="hidden"
            animate="visible"
            exit="exit"
            role="dialog"
            aria-label="Keyboard shortcuts"
          >
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-lg font-black text-slate-900">Keyboard Shortcuts</h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close"
                className="rounded-full p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-widest text-slate-400">Video Player</p>
                <div className="space-y-2">
                  {VIDEO_SHORTCUTS.map((s) => (
                    <div key={s.key} className="flex items-center justify-between gap-4">
                      <span className="text-sm text-slate-600">{s.description}</span>
                      <kbd>{s.key}</kbd>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-widest text-slate-400">Global</p>
                <div className="space-y-2">
                  {GLOBAL_SHORTCUTS.map((s) => (
                    <div key={s.key} className="flex items-center justify-between gap-4">
                      <span className="text-sm text-slate-600">{s.description}</span>
                      <kbd>{s.key}</kbd>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <p className="mt-5 text-xs text-slate-400">Press <kbd>Esc</kbd> or <kbd>?</kbd> to close</p>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
