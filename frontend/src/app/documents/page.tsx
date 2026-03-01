"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import JobProgress from "@/components/JobProgress";
import UploadDropzone from "@/components/UploadDropzone";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api";
import { DocumentItem } from "@/lib/types";

function statusTone(status: DocumentItem["status"]): string {
  if (status === "PARSED") return "bg-emerald-100 text-emerald-800";
  if (status === "PARSING") return "bg-amber-100 text-amber-900";
  if (status === "FAILED") return "bg-rose-100 text-rose-800";
  return "bg-slate-100 text-slate-700";
}

const DOC_COLORS = ["bg-[#dce4ff]", "bg-[#d4efdf]", "bg-[#f6e8c0]", "bg-[#efd9e7]"];

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

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

  const onDeleteDocument = async (doc: DocumentItem) => {
    const ok = window.confirm(`Delete lesson \"${doc.title}\"? This removes generated assets too.`);
    if (!ok) return;

    try {
      setDeletingDocId(doc.id);
      await deleteDocument(doc.id);
      await refresh();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete lesson");
    } finally {
      setDeletingDocId(null);
    }
  };

  return (
    <section className="mx-auto max-w-5xl space-y-4">
      <div className="soft-section space-y-4 px-6 py-7 text-center md:px-10 md:py-10">
        <p className="mx-auto inline-flex rounded-full border border-slate-300 bg-white/80 px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] text-slate-700">
          Lessons Library
        </p>
        <h1 className="text-4xl font-black leading-tight text-slate-900 md:text-5xl">All Stored Lessons</h1>
        <p className="mx-auto max-w-3xl text-sm leading-relaxed text-slate-700 md:text-base">
          Upload and manage your lesson sources. Open any lesson to generate visuals, audio narration, captions, and interactive module chat.
        </p>
        <div className="mx-auto max-w-3xl">
          <UploadDropzone onUpload={onUpload} />
        </div>
      </div>

      <JobProgress jobId={jobId} onComplete={refresh} />
      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p> : null}

      <div className="grid gap-3 sm:grid-cols-2">
        {documents.map((doc, index) => (
          <article key={doc.id} className={`card p-4 ${DOC_COLORS[index % DOC_COLORS.length]}`}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="line-clamp-1 text-lg font-black text-slate-900">{doc.title}</h2>
              <span className={`status-pill ${statusTone(doc.status)}`}>{doc.status}</span>
            </div>
            <p className="mb-4 line-clamp-2 text-sm text-slate-700">{doc.filename}</p>
            <div className="flex items-center gap-2">
              <Link
                className="inline-flex rounded-lg border border-slate-400 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:border-slate-700"
                href={`/documents/${doc.id}`}
              >
                Open modules
              </Link>
              <button
                type="button"
                disabled={deletingDocId === doc.id}
                onClick={() => onDeleteDocument(doc)}
                className="inline-flex rounded-lg border border-rose-300 bg-white px-3 py-1.5 text-sm font-semibold text-rose-700 transition hover:border-rose-500 disabled:opacity-60"
              >
                {deletingDocId === doc.id ? "Deleting..." : "Delete"}
              </button>
            </div>
          </article>
        ))}

        {!documents.length ? (
          <div className="card col-span-full p-6 text-center text-sm text-slate-600">
            No lessons yet. Upload your first PDF to start generating lessons.
          </div>
        ) : null}
      </div>
    </section>
  );
}
