"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useToast } from "@/components/ToastProvider";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import UploadDropzone from "@/components/UploadDropzone";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api";
import { trackDocumentParseJob } from "@/lib/jobTracker";
import { DocumentItem } from "@/lib/types";

function statusTone(status: DocumentItem["status"]): string {
  if (status === "PARSED") return "bg-emerald-100 text-emerald-800";
  if (status === "PARSING") return "bg-amber-100 text-amber-900";
  if (status === "FAILED") return "bg-rose-100 text-rose-800";
  return "bg-slate-100 text-slate-700";
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);
  const [pendingDeleteDoc, setPendingDeleteDoc] = useState<DocumentItem | null>(null);
  const { notify } = useToast();

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

  useEffect(() => {
    const hasRunning = documents.some((item) => item.status === "PARSING" || item.status === "PDF_UPLOADED");
    if (!hasRunning) return;

    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [documents, refresh]);

  const onUpload = async (file: File) => {
    const res = await uploadDocument(file);
    trackDocumentParseJob({
      jobId: res.job_id,
      documentId: res.document_id,
      documentTitle: file.name.replace(/\.pdf$/i, ""),
      createdAt: new Date().toISOString(),
    });
    notify({
      title: "Upload received",
      description: "Document processing has started in the background.",
      tone: "info",
      dedupeKey: `upload-${res.job_id}`,
    });
    await refresh();
  };

  const onDeleteDocument = async () => {
    if (!pendingDeleteDoc) return;
    try {
      setDeletingDocId(pendingDeleteDoc.id);
      await deleteDocument(pendingDeleteDoc.id);
      await refresh();
      setError(null);
      notify({
        title: "Lesson deleted",
        description: pendingDeleteDoc.title,
        tone: "success",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete lesson");
      notify({
        title: "Delete failed",
        description: pendingDeleteDoc.title,
        tone: "error",
      });
    } finally {
      setDeletingDocId(null);
      setPendingDeleteDoc(null);
    }
  };

  return (
    <section className="mx-auto max-w-5xl space-y-5">
      <div className="soft-section p-7 text-center">
        <h1 className="text-4xl font-black leading-tight text-slate-900 md:text-5xl">All Stored Lessons</h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-600 md:text-base">
          Upload a PDF for any subject, generate lessons, and manage everything in one place.
        </p>
        <div className="mx-auto mt-6 max-w-3xl">
          <UploadDropzone onUpload={onUpload} />
        </div>
      </div>

      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p> : null}

      <div className="grid gap-3 sm:grid-cols-2">
        {documents.map((doc) => (
          <article key={doc.id} className="card p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="line-clamp-1 text-lg font-black text-slate-900">{doc.title}</h2>
              <span className={`status-pill ${statusTone(doc.status)}`}>{doc.status}</span>
            </div>
            <p className="mb-4 line-clamp-2 text-sm text-slate-600">{doc.filename}</p>
            <div className="flex items-center gap-2">
              <Link
                className="inline-flex rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:border-slate-700"
                href={`/documents/${doc.id}`}
              >
                Open modules
              </Link>
              <button
                type="button"
                disabled={deletingDocId === doc.id}
                onClick={() => setPendingDeleteDoc(doc)}
                className="inline-flex rounded-full border border-rose-200 bg-white px-3 py-1.5 text-sm font-semibold text-rose-700 transition hover:border-rose-400 disabled:opacity-60"
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

      <ConfirmDialog
        open={Boolean(pendingDeleteDoc)}
        title="Delete lesson?"
        description={
          pendingDeleteDoc
            ? `This will remove "${pendingDeleteDoc.title}" and all generated assets. This action cannot be undone.`
            : ""
        }
        confirmLabel={deletingDocId ? "Deleting..." : "Delete lesson"}
        cancelLabel="Cancel"
        busy={Boolean(deletingDocId)}
        onConfirm={onDeleteDocument}
        onCancel={() => {
          if (!deletingDocId) setPendingDeleteDoc(null);
        }}
        tone="danger"
      />
    </section>
  );
}
