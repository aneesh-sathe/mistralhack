"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { chatWithModuleStream, getCaptions } from "@/lib/api";
import { EmptyCaptions, EmptyChat } from "@/components/EmptyStates";
import { staggerContainer, staggerItem } from "@/lib/animations";
import { ModuleChatTurn } from "@/lib/types";

interface CaptionPanelProps {
  moduleId: string;
  currentTime: number;
  onSeekTo?: (seconds: number) => void;
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
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length < 3) return;
    const [startRaw, endRaw] = lines[1].split(" --> ");
    if (!startRaw || !endRaw) return;
    rows.push({ index: idx, start: parseTs(startRaw), end: parseTs(endRaw), text: lines.slice(2).join(" ") });
  });
  return rows;
}

export default function CaptionPanel({ moduleId, currentTime, onSeekTo }: CaptionPanelProps) {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [tab, setTab] = useState<"captions" | "chat">("captions");
  const [chatTurns, setChatTurns] = useState<ModuleChatTurn[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatModel, setChatModel] = useState<string>("");
  const captionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

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
    return () => { active = false; };
  }, [moduleId]);

  const activeIndex = useMemo(
    () => segments.findIndex((seg) => currentTime >= seg.start && currentTime <= seg.end),
    [segments, currentTime]
  );

  useEffect(() => {
    if (tab !== "captions" || activeIndex < 0) return;
    captionRefs.current[activeIndex]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [activeIndex, tab]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatTurns]);

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
        onMeta: ({ model }) => { if (model) setChatModel(model); },
        onToken: (delta) => {
          setChatTurns((prev) => {
            if (!prev.length) return prev;
            const next = [...prev];
            const last = next[next.length - 1];
            if (last.role !== "assistant") return prev;
            next[next.length - 1] = { ...last, content: last.content + delta };
            return next;
          });
        },
      });
    } catch (err) {
      setChatTurns((prev) => {
        const next = [...prev];
        if (next[next.length - 1]?.role === "assistant" && !next[next.length - 1].content) next.pop();
        return next;
      });
      setChatError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setChatBusy(false);
    }
  };

  return (
    <div className="card h-full p-3">
      {/* Tab switcher */}
      <div className="mb-3 flex gap-2 rounded-full bg-slate-100 p-1">
        {(["captions", "chat"] as const).map((t) => (
          <button
            key={t}
            className={`flex-1 rounded-full px-3 py-2 text-sm font-semibold transition ${
              tab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-800"
            }`}
            onClick={() => setTab(t)}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Captions tab */}
      {tab === "captions" && (
        <div className="h-[450px] overflow-y-auto pr-1">
          {segments.length === 0 ? (
            <EmptyCaptions />
          ) : (
            <motion.div
              className="space-y-1.5"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {segments.map((segment, idx) => (
                <motion.button
                  key={`${segment.index}-${segment.start}`}
                  ref={(el) => { captionRefs.current[idx] = el; }}
                  type="button"
                  variants={staggerItem}
                  onClick={() => onSeekTo?.(segment.start)}
                  className={`w-full rounded-xl px-3 py-2 text-left text-sm leading-relaxed transition ${
                    idx === activeIndex
                      ? "bg-brand-50 font-semibold text-brand-700 ring-1 ring-brand-200"
                      : "bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {segment.text}
                </motion.button>
              ))}
            </motion.div>
          )}
        </div>
      )}

      {/* Chat tab */}
      {tab === "chat" && (
        <div className="flex h-[450px] flex-col">
          <div className="flex-1 space-y-2 overflow-y-auto pr-1">
            {chatTurns.length === 0 ? (
              <EmptyChat />
            ) : (
              <AnimatePresence initial={false}>
                {chatTurns.map((turn, index) => (
                  <motion.div
                    key={`${turn.role}-${index}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25 }}
                    className={`rounded-xl px-3 py-2 text-sm ${
                      turn.role === "user"
                        ? "ml-8 border border-brand-200 bg-brand-50 text-brand-700"
                        : "mr-8 border border-slate-200 bg-slate-50 text-slate-800"
                    }`}
                  >
                    <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.08em] text-slate-400">
                      {turn.role}
                    </p>
                    <p className="whitespace-pre-wrap leading-relaxed">{turn.content}</p>
                    {turn.role === "assistant" && chatBusy && index === chatTurns.length - 1 && !turn.content && (
                      <span className="inline-flex gap-0.5">
                        {[0, 1, 2].map((i) => (
                          <motion.span
                            key={i}
                            className="inline-block h-1.5 w-1.5 rounded-full bg-slate-400"
                            animate={{ y: [0, -4, 0] }}
                            transition={{ duration: 0.5, delay: i * 0.1, repeat: Infinity }}
                          />
                        ))}
                      </span>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
            <div ref={chatBottomRef} />
          </div>

          <form onSubmit={submitChat} className="mt-3 space-y-2 border-t border-slate-200 pt-3">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submitChat(e as unknown as FormEvent);
                }
              }}
              placeholder="Ask a question about this lesson..."
              rows={3}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-100"
            />
            <div className="flex items-center justify-between gap-3">
              <p className="truncate text-xs text-slate-400">{chatModel ? `Model: ${chatModel}` : ""}</p>
              <button
                type="submit"
                disabled={chatBusy || !chatInput.trim()}
                className="rounded-full bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50 active:scale-95"
              >
                {chatBusy ? "Sending..." : "Send"}
              </button>
            </div>
            <AnimatePresence>
              {chatError && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-sm font-medium text-rose-600"
                >
                  {chatError}
                </motion.p>
              )}
            </AnimatePresence>
          </form>
        </div>
      )}
    </div>
  );
}
