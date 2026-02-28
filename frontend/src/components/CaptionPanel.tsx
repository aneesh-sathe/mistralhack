"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { chatWithModule, getCaptions } from "@/lib/api";
import { ModuleChatTurn } from "@/lib/types";

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
  const [tab, setTab] = useState<"captions" | "chat">("captions");
  const [chatTurns, setChatTurns] = useState<ModuleChatTurn[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatModel, setChatModel] = useState<string>("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const srt = await getCaptions(moduleId);
        if (!active) return;
        setSegments(parseSrt(srt));
      } catch {
        if (!active) return;
        setSegments([]);
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

  const submitChat = async (event: FormEvent) => {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message || chatBusy) {
      return;
    }

    const historyForApi = [...chatTurns];
    const userTurn: ModuleChatTurn = { role: "user", content: message };
    setChatTurns((prev) => [...prev, userTurn]);
    setChatInput("");
    setChatBusy(true);
    setChatError(null);

    try {
      const res = await chatWithModule(moduleId, message, historyForApi);
      setChatModel(res.model || "");
      setChatTurns((prev) => [...prev, { role: "assistant", content: res.answer }]);
    } catch (err) {
      setChatError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setChatBusy(false);
    }
  };

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
          className={`rounded px-3 py-1 text-sm ${tab === "chat" ? "bg-brand-500 text-white" : "bg-slate-100 text-slate-700"}`}
          onClick={() => setTab("chat")}
        >
          Chat
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
      ) : null}

      {tab === "chat" ? (
        <div className="flex h-[420px] flex-col">
          <div className="flex-1 space-y-2 overflow-y-auto pr-2">
            {chatTurns.map((turn, index) => (
              <div
                key={`${turn.role}-${index}`}
                className={`rounded px-3 py-2 text-sm ${
                  turn.role === "user"
                    ? "ml-8 bg-brand-50 text-brand-700"
                    : "mr-8 bg-slate-100 text-slate-800"
                }`}
              >
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">{turn.role}</p>
                <p className="whitespace-pre-wrap">{turn.content}</p>
              </div>
            ))}
            {!chatTurns.length ? (
              <p className="text-sm text-slate-500">Ask questions about this module. The assistant uses module content only.</p>
            ) : null}
          </div>

          <form onSubmit={submitChat} className="mt-3 space-y-2 border-t border-slate-200 pt-3">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question about this lesson..."
              rows={3}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-300 focus:ring"
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">{chatModel ? `Model: ${chatModel}` : ""}</p>
              <button
                type="submit"
                disabled={chatBusy || !chatInput.trim()}
                className="rounded bg-brand-500 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              >
                {chatBusy ? "Sending..." : "Send"}
              </button>
            </div>
            {chatError ? <p className="text-sm text-red-600">{chatError}</p> : null}
          </form>
        </div>
      ) : null}
    </div>
  );
}
