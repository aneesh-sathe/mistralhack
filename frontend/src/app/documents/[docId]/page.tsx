"use client";

import { useCallback, useEffect, useState } from "react";

import ModuleList from "@/components/ModuleList";
import { getDocument, getDocumentModules } from "@/lib/api";
import { DocumentItem, ModuleItem } from "@/lib/types";

export default function DocumentDetailPage({ params }: { params: { docId: string } }) {
  const { docId } = params;
  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [modules, setModules] = useState<ModuleItem[]>([]);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <section className="space-y-4">
      <header className="card p-4">
        <h1 className="font-display text-2xl font-bold text-slate-900">{doc?.title || "Document"}</h1>
        <p className="text-sm text-slate-600">Status: {doc?.status || "loading"}</p>
      </header>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div>
        <h2 className="mb-2 font-display text-xl font-semibold">Modules</h2>
        <ModuleList modules={modules} />
      </div>
    </section>
  );
}
