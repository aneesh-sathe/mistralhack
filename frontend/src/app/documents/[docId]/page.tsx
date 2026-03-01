"use client";

import { useCallback, useEffect, useState } from "react";

import ModuleList from "@/components/ModuleList";
import { useToast } from "@/components/ToastProvider";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { deleteModule, getDocument, getDocumentModules } from "@/lib/api";
import { DocumentItem, ModuleItem } from "@/lib/types";

function statusColor(status: DocumentItem["status"] | undefined): string {
  if (status === "PARSED") return "bg-emerald-100 text-emerald-800";
  if (status === "PARSING") return "bg-amber-100 text-amber-800";
  if (status === "FAILED") return "bg-rose-100 text-rose-800";
  return "bg-slate-100 text-slate-700";
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
    try {
      setDeletingModuleId(pendingDeleteModule.id);
      await deleteModule(pendingDeleteModule.id);
      setPendingDeleteModule(null);
      await load();
      notify({
        title: "Module deleted",
        description: pendingDeleteModule.title,
        tone: "success",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete module");
      notify({
        title: "Delete failed",
        description: pendingDeleteModule.title,
        tone: "error",
      });
    } finally {
      setDeletingModuleId(null);
    }
  };

  return (
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
          <span className={`status-pill ${statusColor(doc?.status)}`}>{doc?.status || "loading"}</span>
        </div>
      </header>

      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p> : null}

      <div className="space-y-2">
        <h2 className="text-xl font-black text-slate-900">Extracted Modules</h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
          Choose a module to generate and preview the final lesson video.
        </p>
      </div>

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
        onCancel={() => {
          if (!deletingModuleId) setPendingDeleteModule(null);
        }}
        tone="danger"
      />
    </section>
  );
}
