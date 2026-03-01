"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { staggerContainer, staggerItem, cardHover } from "@/lib/animations";
import { EmptyModules } from "@/components/EmptyStates";
import { ModuleItem } from "@/lib/types";

interface ModuleListProps {
  modules: ModuleItem[];
  deletingModuleId?: string | null;
  onDeleteModule?: (module: ModuleItem) => void;
}

function statusStyle(status: ModuleItem["status"]): { pill: string; pulse: boolean } {
  if (status === "DONE") return { pill: "bg-emerald-100 text-emerald-800", pulse: false };
  if (status === "GENERATING") return { pill: "bg-amber-100 text-amber-900", pulse: true };
  if (status === "FAILED") return { pill: "bg-rose-100 text-rose-800", pulse: false };
  return { pill: "bg-slate-100 text-slate-700", pulse: false };
}

export default function ModuleList({ modules, deletingModuleId = null, onDeleteModule }: ModuleListProps) {
  if (!modules.length) {
    return <EmptyModules />;
  }

  return (
    <motion.div
      className="grid gap-3 sm:grid-cols-2"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      {modules.map((module) => {
        const { pill, pulse } = statusStyle(module.status);
        return (
          <motion.div
            key={module.id}
            variants={staggerItem}
            {...cardHover}
            className="card p-4"
          >
            <div className="mb-3 flex items-center justify-between gap-2">
              <h3 className="text-lg font-bold text-slate-900">{module.title}</h3>
              <span className={`status-pill ${pill} ${pulse ? "status-pill-pulse" : ""}`}>
                {pulse && (
                  <motion.span
                    className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current"
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                  />
                )}
                {module.status}
              </span>
            </div>
            <p className="mb-4 text-sm leading-relaxed text-slate-600">{module.summary}</p>
            <div className="flex items-center gap-2">
              <Link
                className="inline-flex items-center rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:border-slate-700 hover:text-slate-900"
                href={`/modules/${module.id}`}
              >
                Open lesson
              </Link>
              {onDeleteModule ? (
                <button
                  type="button"
                  disabled={deletingModuleId === module.id || module.status === "GENERATING"}
                  onClick={() => onDeleteModule(module)}
                  className="inline-flex rounded-full border border-rose-200 bg-white px-3 py-1.5 text-sm font-semibold text-rose-700 transition hover:border-rose-400 disabled:opacity-60"
                >
                  {deletingModuleId === module.id ? "Deleting..." : "Delete"}
                </button>
              ) : null}
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
