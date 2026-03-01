"use client";

import { ChangeEvent, DragEvent, useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
}

export default function UploadDropzone({ onUpload }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounterRef = useRef(0);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File must be under 50MB.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      await onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const onChange = async (event: ChangeEvent<HTMLInputElement>) => {
    await handleFile(event.target.files?.[0]);
  };

  // Page-level drag-and-drop
  const onWindowDragEnter = useCallback((e: Event) => {
    const dragEvent = e as unknown as DragEvent;
    if (!dragEvent.dataTransfer) return;
    dragCounterRef.current++;
    const types = Array.from(dragEvent.dataTransfer.types);
    if (types.includes("Files")) {
      setIsDragging(true);
    }
  }, []);

  const onWindowDragLeave = useCallback(() => {
    dragCounterRef.current--;
    if (dragCounterRef.current <= 0) {
      dragCounterRef.current = 0;
      setIsDragging(false);
    }
  }, []);

  const onWindowDragOver = useCallback((e: Event) => {
    e.preventDefault();
  }, []);

  const onWindowDrop = useCallback(
    async (e: Event) => {
      e.preventDefault();
      dragCounterRef.current = 0;
      setIsDragging(false);
      const dropEvent = e as unknown as DragEvent;
      const file = dropEvent.dataTransfer?.files?.[0];
      await handleFile(file);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  useEffect(() => {
    window.addEventListener("dragenter", onWindowDragEnter);
    window.addEventListener("dragleave", onWindowDragLeave);
    window.addEventListener("dragover", onWindowDragOver);
    window.addEventListener("drop", onWindowDrop);
    return () => {
      window.removeEventListener("dragenter", onWindowDragEnter);
      window.removeEventListener("dragleave", onWindowDragLeave);
      window.removeEventListener("dragover", onWindowDragOver);
      window.removeEventListener("drop", onWindowDrop);
    };
  }, [onWindowDragEnter, onWindowDragLeave, onWindowDragOver, onWindowDrop]);

  return (
    <>
      {/* Full-page drag overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            className="drag-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <motion.div
              className="drag-overlay-inner"
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.94, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <motion.div
                animate={{ scale: [1, 1.08, 1] }}
                transition={{ duration: 1.2, repeat: Infinity }}
                className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100"
              >
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                  <path d="M16 6V22M16 6L10 12M16 6L22 12" stroke="#5f43ff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M6 24H26" stroke="#5f43ff" strokeWidth="2.5" strokeLinecap="round" />
                </svg>
              </motion.div>
              <p className="text-xl font-black text-slate-900">Drop your PDF here</p>
              <p className="mt-1 text-sm text-slate-500">Release to upload</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Local dropzone card */}
      <div className="card border border-dashed border-slate-300 p-5">
        <input ref={inputRef} type="file" accept="application/pdf" onChange={onChange} className="hidden" />
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Upload PDF</h3>
            <p className="text-sm text-slate-600">Drop any subject PDF or click to browse. Max 50MB.</p>
          </div>
          <Button loading={busy} disabled={busy} onClick={() => inputRef.current?.click()} className="min-w-[170px]">
            {busy ? "Uploading" : "Choose PDF"}
          </Button>
        </div>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="mt-3 text-sm font-medium text-rose-600"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
