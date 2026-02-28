"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import JobProgress from "@/components/JobProgress";
import UploadDropzone from "@/components/UploadDropzone";
import { listDocuments, uploadDocument } from "@/lib/api";
import { DocumentItem } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const payload = await listDocuments();
      setDocuments(payload.documents);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onUpload = async (file: File) => {
    const res = await uploadDocument(file);
    setJobId(res.job_id);
    await refresh();
  };

  return (
    <section className="space-y-4">
      <header>
        <h1 className="font-display text-3xl font-bold text-slate-900">Your Documents</h1>
        <p className="text-sm text-slate-600">Upload a math PDF and track parsing progress.</p>
      </header>

      <UploadDropzone onUpload={onUpload} />
      <JobProgress jobId={jobId} onComplete={refresh} />

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="grid gap-3">
        {documents.map((doc) => (
          <div key={doc.id} className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-medium text-slate-900">{doc.title}</h2>
                <p className="text-xs text-slate-500">{doc.filename}</p>
              </div>
              <Link className="text-sm font-medium text-brand-700" href={`/documents/${doc.id}`}>
                Open
              </Link>
            </div>
            <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">Status: {doc.status}</p>
          </div>
        ))}

        {!documents.length ? <div className="card p-4 text-sm text-slate-600">No documents uploaded yet.</div> : null}
      </div>
    </section>
  );
}
