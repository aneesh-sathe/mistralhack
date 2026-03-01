"use client";

import { motion } from "framer-motion";
import { fadeUp } from "@/lib/animations";

function EmptyShelfIllustration() {
  return (
    <svg width="120" height="90" viewBox="0 0 120 90" fill="none" aria-hidden="true">
      {/* Shelf */}
      <rect x="8" y="68" width="104" height="8" rx="4" fill="#e2ddff" />
      {/* Books - ghosted outlines */}
      <rect x="18" y="36" width="16" height="32" rx="3" stroke="#c9c1ff" strokeWidth="1.5" strokeDasharray="4 3" />
      <rect x="38" y="44" width="14" height="24" rx="3" stroke="#c9c1ff" strokeWidth="1.5" strokeDasharray="4 3" />
      <rect x="56" y="30" width="18" height="38" rx="3" stroke="#c9c1ff" strokeWidth="1.5" strokeDasharray="4 3" />
      <rect x="78" y="42" width="12" height="26" rx="3" stroke="#c9c1ff" strokeWidth="1.5" strokeDasharray="4 3" />
      <rect x="94" y="38" width="14" height="30" rx="3" stroke="#c9c1ff" strokeWidth="1.5" strokeDasharray="4 3" />
      {/* Stars */}
      <path d="M60 12L61.5 16.5H66L62.3 19.2L63.8 23.7L60 21L56.2 23.7L57.7 19.2L54 16.5H58.5L60 12Z" fill="#a99cff" />
      <circle cx="22" cy="18" r="3" fill="#e2ddff" />
      <circle cx="100" cy="22" r="2" fill="#e2ddff" />
    </svg>
  );
}

function OpenBookIllustration() {
  return (
    <svg width="120" height="90" viewBox="0 0 120 90" fill="none" aria-hidden="true">
      {/* Left page */}
      <path d="M12 20C12 16.7 14.7 14 18 14H58V74H18C14.7 74 12 71.3 12 68V20Z" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      {/* Right page */}
      <path d="M108 20C108 16.7 105.3 14 102 14H62V74H102C105.3 74 108 71.3 108 68V20Z" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      {/* Lines on left */}
      <line x1="22" y1="30" x2="52" y2="30" stroke="#c9c1ff" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="22" y1="38" x2="52" y2="38" stroke="#c9c1ff" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="22" y1="46" x2="44" y2="46" stroke="#c9c1ff" strokeWidth="1.5" strokeLinecap="round" />
      {/* Question marks */}
      <text x="68" y="50" fill="#a99cff" fontSize="24" fontWeight="700">?</text>
      <text x="87" y="40" fill="#c9c1ff" fontSize="16" fontWeight="700">?</text>
      {/* Spine */}
      <line x1="60" y1="14" x2="60" y2="74" stroke="#a99cff" strokeWidth="2" />
    </svg>
  );
}

function ChatBubblesIllustration() {
  return (
    <svg width="120" height="90" viewBox="0 0 120 90" fill="none" aria-hidden="true">
      {/* Large bubble */}
      <rect x="10" y="10" width="70" height="40" rx="14" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      <path d="M24 50L18 62L36 50H24Z" fill="#f2efff" stroke="#c9c1ff" strokeWidth="1.5" />
      {/* Lines in bubble */}
      <line x1="20" y1="24" x2="68" y2="24" stroke="#c9c1ff" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="20" y1="34" x2="56" y2="34" stroke="#c9c1ff" strokeWidth="1.5" strokeLinecap="round" />
      {/* Small reply bubble */}
      <rect x="52" y="50" width="56" height="30" rx="10" fill="#e2ddff" stroke="#a99cff" strokeWidth="1.5" />
      <path d="M66 50L60 40L80 50H66Z" fill="#e2ddff" stroke="#a99cff" strokeWidth="1.5" />
      <line x1="62" y1="62" x2="96" y2="62" stroke="#a99cff" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="62" y1="70" x2="82" y2="70" stroke="#a99cff" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

interface EmptyStateProps {
  className?: string;
  action?: React.ReactNode;
}

export function EmptyDocuments({ className, action }: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center gap-4 py-16 text-center ${className || ""}`}
    >
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      >
        <EmptyShelfIllustration />
      </motion.div>
      <div className="space-y-1">
        <h3 className="text-lg font-bold text-slate-800">Your learning library is empty</h3>
        <p className="max-w-xs text-sm text-slate-500">
          Upload your first PDF to start turning documents into interactive lessons.
        </p>
      </div>
      {action}
    </motion.div>
  );
}

export function EmptyModules({ className }: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center gap-4 py-12 text-center ${className || ""}`}
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
      >
        <OpenBookIllustration />
      </motion.div>
      <div className="space-y-1">
        <h3 className="text-lg font-bold text-slate-800">No modules found yet</h3>
        <p className="max-w-xs text-sm text-slate-500">
          Document is still being processed. Modules will appear here shortly.
        </p>
      </div>
      <motion.div
        className="flex gap-1.5"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-1.5 w-1.5 rounded-full bg-brand-300" />
        ))}
      </motion.div>
    </motion.div>
  );
}

export function EmptyCaptions({ className }: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center gap-4 py-8 text-center ${className || ""}`}
    >
      <OpenBookIllustration />
      <div className="space-y-1">
        <p className="text-sm font-semibold text-slate-700">Captions unavailable</p>
        <p className="text-xs text-slate-500">Generate a lesson to see captions here.</p>
      </div>
    </motion.div>
  );
}

export function EmptyChat({ className }: EmptyStateProps) {
  const examples = ["What is the main concept here?", "Can you explain this in simpler terms?", "Give me a quick summary"];

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center gap-4 py-6 text-center ${className || ""}`}
    >
      <ChatBubblesIllustration />
      <div className="space-y-1">
        <p className="text-sm font-semibold text-slate-700">Ask anything about this lesson</p>
        <p className="text-xs text-slate-500">Responses are grounded in the module content.</p>
      </div>
      <div className="flex flex-col gap-1.5 w-full">
        {examples.map((ex) => (
          <div key={ex} className="rounded-xl border border-dashed border-brand-200 bg-brand-50/50 px-3 py-2 text-xs text-brand-600">
            "{ex}"
          </div>
        ))}
      </div>
    </motion.div>
  );
}
