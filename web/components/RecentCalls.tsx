"use client";
import { useState } from "react";
import { useCollection } from "@/lib/useCollection";

function when(ts: any): string {
  const d = ts?.toDate ? ts.toDate() : ts ? new Date(ts) : null;
  return d ? d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "just now";
}

// Calls are saved by the API when a call ends (Firestore "calls").
export default function RecentCalls() {
  const calls = useCollection("calls", { orderBy: "createdAt", desc: true, limit: 5 });
  const [open, setOpen] = useState<string | null>(null);
  if (!calls.length) return null;
  return (
    <section className="mt-6">
      <h2 className="h2">Recent calls</h2>
      <div className="space-y-2">
        {calls.map((c: any, i: number) => (
          <div key={c.id} className="card text-sm">
            <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen(open === c.id ? null : c.id)}>
              <span>
                <span className="rounded-full bg-cedar-50 px-2 py-0.5 text-xs font-semibold text-cedar-700">Demo call {calls.length - i}</span>
                <span className="ml-2 text-stone-500">{when(c.createdAt)} · {(c.transcript ?? []).length} lines</span>
              </span>
              <span className="text-stone-400">{open === c.id ? "Hide" : "Show transcript"}</span>
            </button>
            {open === c.id && (
              <div className="mt-3 space-y-1">
                {(c.transcript ?? []).map((t: any, j: number) => (
                  <p key={j}>
                    <span className={t.who === "rafi" ? "font-semibold text-cedar-700" : "font-semibold text-stone-700"}>
                      {t.who === "rafi" ? "Rafi" : "Caller"}:
                    </span>{" "}
                    {t.text}
                  </p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
