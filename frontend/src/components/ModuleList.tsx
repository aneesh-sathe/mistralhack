"use client";

import Link from "next/link";

import { ModuleItem } from "@/lib/types";

interface ModuleListProps {
  modules: ModuleItem[];
}

export default function ModuleList({ modules }: ModuleListProps) {
  if (!modules.length) {
    return <div className="card p-4 text-sm text-slate-600">No modules yet.</div>;
  }

  return (
    <div className="grid gap-3">
      {modules.map((module) => (
        <div key={module.id} className="card p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-display text-lg font-semibold text-slate-900">{module.title}</h3>
              <p className="text-sm text-slate-600">{module.summary}</p>
            </div>
            <Link className="text-sm font-medium text-brand-700" href={`/modules/${module.id}`}>
              Open
            </Link>
          </div>
          <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">Status: {module.status}</p>
        </div>
      ))}
    </div>
  );
}
