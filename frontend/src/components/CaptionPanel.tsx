"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { chatWithModuleStream, getCaptions } from "@/lib/api";
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
    if (!message || chatBusy) return;

    const historyForApi = [...chatTurns];
    const userTurn: ModuleChatTurn = { role: "user", content: message };
    setChatTurns((prev) => [...prev, userTurn, { role: "assistant", content: "" }]);
    setChatInput("");
    setChatBusy(true);
    setChatError(null);

    try {
      await chatWithModuleStream(moduleId, message, historyForApi, {
        onMeta: ({ model }) => {
          if (model) setChatModel(model);
        },
        onToken: (delta) => {
          setChatTurns((prev) => {
            if (!prev.length) return prev;
            const next = [...prev];
            const lastIdx = next.length - 1;
            const last = next[lastIdx];
            if (last.role !== "assistant") return prev;
            next[lastIdx] = { ...last, content: last.content + delta };
            return next;
          });
        },
      });
    } catch (err) {
      setChatTurns((prev) => {
        if (!prev.length) return prev;
        const next = [...prev];
        const lastIdx = next.length - 1;
        if (next[lastIdx].role === "assistant" && !next[lastIdx].content) {
          next.pop();
        }
        return next;
      });
      setChatError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setChatBusy(false);
    }
  };

  return (
    <div className="card h-full p-3">
      <div className="mb-3 flex gap-2 rounded-full bg-slate-100 p-1">
        <button
          className={`flex-1 rounded-full px-3 py-2 text-sm font-semibold transition ${
            tab === "captions" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
          }`}
          onClick={() => setTab("captions")}
        >
          Captions
        </button>
        <button
          className={`flex-1 rounded-full px-3 py-2 text-sm font-semibold transition ${
            tab === "chat" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
          }`}
          onClick={() => setTab("chat")}
        >
          Chat
        </button>
      </div>

      {tab === "captions" ? (
        <div className="h-[450px] space-y-2 overflow-y-auto pr-1">
          {segments.map((segment, idx) => (
            <p
              key={`${segment.index}-${segment.start}`}
              className={`rounded-xl px-3 py-2 text-sm leading-relaxed transition ${
                idx === activeIndex ? "bg-brand-50 text-brand-700" : "bg-slate-50 text-slate-700"
              }`}
            >
              {segment.text}
            </p>
          ))}
          {!segments.length ? <p className="text-sm text-slate-500">Captions unavailable.</p> : null}
        </div>
      ) : null}

      {tab === "chat" ? (
        <div className="flex h-[450px] flex-col">
          <div className="flex-1 space-y-2 overflow-y-auto pr-1">
            {chatTurns.map((turn, index) => (
              <div
                key={`${turn.role}-${index}`}
                className={`rounded-xl px-3 py-2 text-sm ${
                  turn.role === "user"
                    ? "ml-8 border border-brand-200 bg-brand-50 text-brand-700"
                    : "mr-8 border border-slate-200 bg-slate-50 text-slate-800"
                }`}
              >
                <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.08em] text-slate-500">{turn.role}</p>
                <p className="whitespace-pre-wrap leading-relaxed">{turn.content}</p>
              </div>
            ))}
            {!chatTurns.length ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-4 text-sm text-slate-500">
                Ask questions about this lesson. Responses are grounded in the module content.
              </div>
            ) : null}
          </div>

          <form onSubmit={submitChat} className="mt-3 space-y-2 border-t border-slate-200 pt-3">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question about this lesson..."
              rows={3}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-brand-500"
            />
            <div className="flex items-center justify-between gap-3">
              <p className="truncate text-xs text-slate-500">{chatModel ? `Model: ${chatModel}` : ""}</p>
              <button
                type="submit"
                disabled={chatBusy || !chatInput.trim()}
                className="rounded-full bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
              >
                {chatBusy ? "Sending..." : "Send"}
              </button>
            </div>
            {chatError ? <p className="text-sm font-medium text-rose-600">{chatError}</p> : null}
          </form>
        </div>
      ) : null}
    </div>
  );
}
