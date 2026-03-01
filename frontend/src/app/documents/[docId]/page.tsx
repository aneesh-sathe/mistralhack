"use client";

import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import ModuleList from "@/components/ModuleList";
import PageTransition from "@/components/PageTransition";
import { useToast } from "@/components/ToastProvider";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { deleteModule, getDocument, getDocumentModules } from "@/lib/api";
import { fadeUp } from "@/lib/animations";
import { DocumentItem, ModuleItem } from "@/lib/types";

function statusColor(status: DocumentItem["status"] | undefined): { pill: string; pulse: boolean } {
  if (status === "PARSED") return { pill: "bg-emerald-100 text-emerald-800", pulse: false };
  if (status === "PARSING") return { pill: "bg-amber-100 text-amber-800", pulse: true };
  if (status === "FAILED") return { pill: "bg-rose-100 text-rose-800", pulse: false };
  return { pill: "bg-slate-100 text-slate-700", pulse: false };
}

export default function DocumentDetailPage({ params }: { params: { docId: string } }) {
  const { docId } = params;
  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [modules, setModules] = useState<ModuleItem[]>([]);
  const [deletingModuleId, setDeletingModuleId] = useState<string | null>(null);
  const [pendingDeleteModule, setPendingDeleteModule] = useState<ModuleItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { notify } = useToast();

  const load = useCallback(async () => {
    try {
      const [docRes, modRes] = await Promise.all([getDocument(docId), getDocumentModules(docId)]);
      setDoc(docRes);
      setModules(modRes.modules);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load document");
    }
  }, [docId]);

  useEffect(() => {
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, [load]);

  const confirmDeleteModule = async () => {
    if (!pendingDeleteModule) return;
    const toDelete = pendingDeleteModule;
    setPendingDeleteModule(null);

    try {
      setDeletingModuleId(toDelete.id);
      // Optimistic removal
      setModules((prev) => prev.filter((m) => m.id !== toDelete.id));
      await deleteModule(toDelete.id);
      notify({ title: "Module deleted", description: toDelete.title, tone: "success" });
    } catch (err) {
      // Rollback
      await load();
      setError(err instanceof Error ? err.message : "Failed to delete module");
      notify({ title: "Delete failed", description: toDelete.title, tone: "error" });
    } finally {
      setDeletingModuleId(null);
    }
  };

  const { pill, pulse } = statusColor(doc?.status);

  return (
    <PageTransition>
      <section className="space-y-4">
        <header className="soft-section p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="max-w-2xl">
              <h1 className="text-3xl font-black text-slate-900">{doc?.title || "Document"}</h1>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">
                View extracted modules and generate a final lesson from this document.
              </p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                {doc?.filename || "Preparing metadata..."}
              </p>
            </div>
            <span className={`status-pill self-start ${pill}`}>
              {pulse && (
                <motion.span
                  className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current"
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                />
              )}
              {doc?.status || "loading"}
            </span>
          </div>
        </header>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        <motion.div variants={fadeUp} initial="hidden" animate="visible" className="space-y-2">
          <h2 className="text-xl font-black text-slate-900">Extracted Modules</h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Choose a module to generate and preview the final lesson video.
          </p>
        </motion.div>

        <ModuleList modules={modules} deletingModuleId={deletingModuleId} onDeleteModule={setPendingDeleteModule} />

        <ConfirmDialog
          open={Boolean(pendingDeleteModule)}
          title="Delete module?"
          description={
            pendingDeleteModule
              ? `This removes "${pendingDeleteModule.title}" and any generated lesson assets. This action cannot be undone.`
              : ""
          }
          confirmLabel={deletingModuleId ? "Deleting..." : "Delete module"}
          cancelLabel="Cancel"
          busy={Boolean(deletingModuleId)}
          onConfirm={confirmDeleteModule}
          onCancel={() => { if (!deletingModuleId) setPendingDeleteModule(null); }}
          tone="danger"
        />
      </section>
    </PageTransition>
  );
}
