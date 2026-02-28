"use client";

import { useEffect, useMemo, useState } from "react";

import { getCaptions, getScript } from "@/lib/api";

interface CaptionPanelProps {
  moduleId: string;
  currentTime: number;
}

interface Segment {
  index: number;
  start: number;
  end: number;
  text: string;
}

function parseTs(value: string): number {
  const [hms, ms] = value.split(",");
  const [h, m, s] = hms.split(":").map(Number);
  return h * 3600 + m * 60 + s + Number(ms) / 1000;
}

function parseSrt(srt: string): Segment[] {
  const blocks = srt.trim().split(/\n\s*\n/g);
  const rows: Segment[] = [];
  blocks.forEach((block, idx) => {
    const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
    if (lines.length < 3) return;
    const timing = lines[1];
    const [startRaw, endRaw] = timing.split(" --> ");
    if (!startRaw || !endRaw) return;
    rows.push({
      index: idx,
      start: parseTs(startRaw),
      end: parseTs(endRaw),
      text: lines.slice(2).join(" "),
    });
  });
  return rows;
}

export default function CaptionPanel({ moduleId, currentTime }: CaptionPanelProps) {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [scriptText, setScriptText] = useState("");
  const [tab, setTab] = useState<"captions" | "script">("captions");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [srt, script] = await Promise.all([getCaptions(moduleId), getScript(moduleId)]);
        if (!active) return;
        setSegments(parseSrt(srt));
        setScriptText(script.script_text || "");
      } catch {
        if (!active) return;
        setSegments([]);
        setScriptText("");
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [moduleId]);

  const activeIndex = useMemo(
    () => segments.findIndex((segment) => currentTime >= segment.start && currentTime <= segment.end),
    [segments, currentTime]
  );

  return (
    <div className="card h-full p-4">
      <div className="mb-3 flex gap-2">
        <button
          className={`rounded px-3 py-1 text-sm ${tab === "captions" ? "bg-brand-500 text-white" : "bg-slate-100 text-slate-700"}`}
          onClick={() => setTab("captions")}
        >
          Captions
        </button>
        <button
          className={`rounded px-3 py-1 text-sm ${tab === "script" ? "bg-brand-500 text-white" : "bg-slate-100 text-slate-700"}`}
          onClick={() => setTab("script")}
        >
          Script
        </button>
      </div>

      {tab === "captions" ? (
        <div className="max-h-[420px] space-y-2 overflow-y-auto pr-2">
          {segments.map((segment, idx) => (
            <p
              key={`${segment.index}-${segment.start}`}
              className={`rounded px-2 py-1 text-sm ${idx === activeIndex ? "bg-brand-100 text-brand-700" : "text-slate-700"}`}
            >
              {segment.text}
            </p>
          ))}
          {!segments.length ? <p className="text-sm text-slate-500">Captions unavailable.</p> : null}
        </div>
      ) : (
        <div className="max-h-[420px] overflow-y-auto pr-2 text-sm text-slate-700">
          {scriptText || "Script unavailable."}
        </div>
      )}
    </div>
  );
}
