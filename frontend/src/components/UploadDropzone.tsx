"use client";

import { ChangeEvent, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
}

export default function UploadDropzone({ onUpload }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
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

  return (
    <div className="card border border-dashed border-slate-300 p-5">
      <input ref={inputRef} type="file" accept="application/pdf" onChange={onChange} className="hidden" />
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Upload PDF</h3>
          <p className="text-sm text-slate-600">Drop any subject PDF to auto-generate lessons.</p>
        </div>
        <Button disabled={busy} onClick={() => inputRef.current?.click()} className="min-w-[170px]">
          {busy ? "Uploading..." : "Choose PDF"}
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm font-medium text-rose-600">{error}</p> : null}
    </div>
  );
}
