"use client";

import Link from "next/link";

import { ModuleItem } from "@/lib/types";

interface ModuleListProps {
  modules: ModuleItem[];
}

function statusStyle(status: ModuleItem["status"]): string {
  if (status === "DONE") return "bg-emerald-100 text-emerald-800";
  if (status === "GENERATING") return "bg-amber-100 text-amber-900";
  if (status === "FAILED") return "bg-rose-100 text-rose-800";
  return "bg-slate-100 text-slate-700";
}

export default function ModuleList({ modules }: ModuleListProps) {
  if (!modules.length) {
    return <div className="card p-5 text-sm text-slate-600">No modules extracted yet for this document.</div>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {modules.map((module) => (
        <div key={module.id} className="card p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h3 className="text-lg font-bold text-slate-900">{module.title}</h3>
            <span className={`status-pill ${statusStyle(module.status)}`}>{module.status}</span>
          </div>
          <p className="mb-4 text-sm leading-relaxed text-slate-600">{module.summary}</p>
          <Link
            className="inline-flex items-center rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:border-slate-700 hover:text-slate-900"
            href={`/modules/${module.id}`}
          >
            Open lesson
          </Link>
        </div>
      ))}
    </div>
  );
}
