"use client";

import { createContext, ReactNode, useCallback, useContext, useMemo, useRef, useState } from "react";

import Toast, { ToastTone } from "@/components/ui/toast";

interface ToastAction {
  label: string;
  onClick: () => void;
}

interface ToastInput {
  title: string;
  description?: string;
  tone?: ToastTone;
  action?: ToastAction;
  durationMs?: number;
  dedupeKey?: string;
}

interface ToastEntry extends ToastInput {
  id: string;
}

interface ToastContextValue {
  notify: (payload: ToastInput) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

function buildToastId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);
  const seenKeysRef = useRef<Set<string>>(new Set());

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback(
    (payload: ToastInput) => {
      if (payload.dedupeKey) {
        if (seenKeysRef.current.has(payload.dedupeKey)) return;
        seenKeysRef.current.add(payload.dedupeKey);
      }

      const id = buildToastId();
      const entry: ToastEntry = { id, ...payload };
      setToasts((prev) => [...prev, entry]);

      const ttl = typeof payload.durationMs === "number" ? payload.durationMs : 7000;
      if (ttl > 0) {
        window.setTimeout(() => dismiss(id), ttl);
      }
    },
    [dismiss]
  );

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2 px-4" aria-live="polite">
        {toasts.map((entry) => (
          <div key={entry.id} className="pointer-events-auto">
            <Toast
              title={entry.title}
              description={entry.description}
              tone={entry.tone}
              actionLabel={entry.action?.label}
              onAction={entry.action?.onClick}
              onClose={() => dismiss(entry.id)}
            />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
