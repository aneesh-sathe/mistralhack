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
    if (!file) {
      return;
    }
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
    <div className="card p-6">
      <p className="mb-3 text-sm text-slate-600">Upload a math PDF to start module extraction.</p>
      <div className="flex items-center gap-3">
        <input ref={inputRef} type="file" accept="application/pdf" onChange={onChange} className="text-sm" />
        <Button disabled={busy} onClick={() => inputRef.current?.click()}>
          {busy ? "Uploading..." : "Choose PDF"}
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
