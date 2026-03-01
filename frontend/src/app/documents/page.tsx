"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { useToast } from "@/components/ToastProvider";
import Confetti from "@/components/Confetti";
import { EmptyDocuments } from "@/components/EmptyStates";
import PageTransition from "@/components/PageTransition";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import UploadDropzone from "@/components/UploadDropzone";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api";
import { trackDocumentParseJob } from "@/lib/jobTracker";
import { staggerContainer, staggerItem, cardHover } from "@/lib/animations";
import { DocumentItem } from "@/lib/types";

function statusConfig(status: DocumentItem["status"]): { pill: string; pulse: boolean } {
  if (status === "PARSED") return { pill: "bg-emerald-100 text-emerald-800", pulse: false };
  if (status === "PARSING") return { pill: "bg-amber-100 text-amber-900", pulse: true };
  if (status === "FAILED") return { pill: "bg-rose-100 text-rose-800", pulse: false };
  return { pill: "bg-slate-100 text-slate-700", pulse: false };
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);
  const [pendingDeleteDoc, setPendingDeleteDoc] = useState<DocumentItem | null>(null);
  const [confetti, setConfetti] = useState(false);
  const [firstUpload, setFirstUpload] = useState(false);
  const { notify } = useToast();
  const hasLoadedRef = useRef(false);

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
    refresh().then(() => { hasLoadedRef.current = true; });
  }, [refresh]);

  useEffect(() => {
    const hasRunning = documents.some((item) => item.status === "PARSING" || item.status === "PDF_UPLOADED");
    if (!hasRunning) return;

    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [documents, refresh]);

  const triggerConfetti = () => {
    setConfetti(true);
    setTimeout(() => setConfetti(false), 2500);
  };

  const onUpload = async (file: File) => {
    // Check if this is the first ever upload
    const isFirst = documents.length === 0 && !firstUpload;

    const res = await uploadDocument(file);
    trackDocumentParseJob({
      jobId: res.job_id,
      documentId: res.document_id,
      documentTitle: file.name.replace(/\.pdf$/i, ""),
      createdAt: new Date().toISOString(),
    });

    if (isFirst) {
      setFirstUpload(true);
      triggerConfetti();
      notify({
        title: "First upload! 🎉",
        description: "Your learning journey starts now.",
        tone: "success",
        dedupeKey: `first-upload`,
      });
    } else {
      notify({
        title: "Upload received 📤",
        description: "Document processing has started in the background.",
        tone: "info",
        dedupeKey: `upload-${res.job_id}`,
      });
    }
    await refresh();
  };

  const onDeleteDocument = async () => {
    if (!pendingDeleteDoc) return;
    const docToDelete = pendingDeleteDoc;
    setPendingDeleteDoc(null);

    try {
      setDeletingDocId(docToDelete.id);
      // Optimistic removal
      setDocuments((prev) => prev.filter((d) => d.id !== docToDelete.id));
      await deleteDocument(docToDelete.id);
      setError(null);
      notify({
        title: "Document deleted",
        description: docToDelete.title,
        tone: "success",
      });
    } catch (err) {
      // Roll back on failure
      await refresh();
      setError(err instanceof Error ? err.message : "Failed to delete document");
      notify({
        title: "Delete failed",
        description: docToDelete.title,
        tone: "error",
      });
    } finally {
      setDeletingDocId(null);
    }
  };

  return (
    <PageTransition>
      <Confetti active={confetti} />
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

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        {documents.length === 0 ? (
          <EmptyDocuments />
        ) : (
          <motion.div
            className="grid gap-3 sm:grid-cols-2"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            <AnimatePresence mode="popLayout">
              {documents.map((doc) => {
                const { pill, pulse } = statusConfig(doc.status);
                return (
                  <motion.article
                    key={doc.id}
                    variants={staggerItem}
                    exit={{ opacity: 0, x: -16, transition: { duration: 0.2 } }}
                    {...cardHover}
                    className="card p-4"
                  >
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <h2 className="line-clamp-1 text-lg font-black text-slate-900">{doc.title}</h2>
                      <span className={`status-pill ${pill}`}>
                        {pulse && (
                          <motion.span
                            className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current"
                            animate={{ opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1.2, repeat: Infinity }}
                          />
                        )}
                        {doc.status}
                      </span>
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
                  </motion.article>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}

        <ConfirmDialog
          open={Boolean(pendingDeleteDoc)}
          title="Delete document?"
          description={
            pendingDeleteDoc
              ? `This will remove "${pendingDeleteDoc.title}" and all generated assets. This action cannot be undone.`
              : ""
          }
          confirmLabel={deletingDocId ? "Deleting..." : "Delete document"}
          cancelLabel="Cancel"
          busy={Boolean(deletingDocId)}
          onConfirm={onDeleteDocument}
          onCancel={() => {
            if (!deletingDocId) setPendingDeleteDoc(null);
          }}
          tone="danger"
        />
      </section>
    </PageTransition>
  );
}
