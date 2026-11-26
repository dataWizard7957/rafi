"use client";
import { useEffect, useRef, useState } from "react";
import { callReady, playCall, type CallLine } from "@/lib/demo";

const CALLS: { n: 1 | 2; label: string; hint: string }[] = [
  { n: 1, label: "Call 1 · Ahmed", hint: "Out of stock → substitute. Then approve the hummus draft on Orders." },
  { n: 2, label: "Call 2 · Sara", hint: "The hold. Then tap Received on Sahadi hummus on Today." },
];

// Demo stand-in for LiveCallPanel: plays a recorded call and applies its tool calls.
export default function DemoCallPanel() {
  const [lines, setLines] = useState<CallLine[]>([]);
  const [playing, setPlaying] = useState(false);
  const [note, setNote] = useState("");
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [lines]);

  async function play(n: 1 | 2) {
    const blocked = callReady(n);
    if (blocked) return setNote(blocked);
    setNote("");
    setLines([]);
    setPlaying(true);
    try {
      await playCall(n, (l) => setLines((prev) => [...prev, l]));
    } finally {
      setPlaying(false);
    }
  }

  return (
    <div className="card">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {CALLS.map((c) => (
          <button key={c.n} className="btn" disabled={playing} onClick={() => play(c.n)} title={c.hint}>
            Play {c.label}
          </button>
        ))}
        <span className="chip bg-stone-100 text-stone-600">Recorded call · voice needs Gemini Live</span>
        {playing && <span className="chip animate-pulse bg-cedar-100 text-cedar-800">On a call</span>}
      </div>
      {note && <div className="mb-3 rounded-lg bg-amber-50 p-2 text-sm text-amber-800">{note}</div>}
      <div className="h-96 space-y-2 overflow-y-auto rounded-lg bg-cream p-3">
        {lines.length === 0 && (
          <div className="space-y-1 text-sm text-stone-500">
            {CALLS.map((c) => <p key={c.n}><span className="font-medium">{c.label}:</span> {c.hint}</p>)}
          </div>
        )}
        {lines.map((l, i) => (
          <div
            key={i}
            className={
              l.who === "tool"
                ? "font-mono text-xs text-stone-500"
                : l.who === "caller"
                ? "ml-auto max-w-[80%] rounded-lg bg-white p-2"
                : "max-w-[80%] rounded-lg bg-cedar-50 p-2 text-cedar-800"
            }
          >
            {l.who !== "tool" && <div className="text-xs font-semibold">{l.who === "caller" ? "Caller" : "Rafi"}</div>}
            {l.text}
          </div>
        ))}
        <div ref={end} />
      </div>
    </div>
  );
}
