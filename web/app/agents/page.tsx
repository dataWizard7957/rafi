"use client";
import { useState } from "react";
import AgentFeed from "@/components/AgentFeed";
import CrewStatusBar from "@/components/CrewStatusBar";
import { post } from "@/lib/api";

export default function Agents() {
  const [busy, setBusy] = useState("");
  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(label);
    try { await fn(); } finally { setBusy(""); }
  };
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="h2 text-2xl">Agent feed</h1>
        <div className="flex gap-2">
          <button className="btn" disabled={!!busy}
            onClick={() => run("brief", () => post("/agents/event", { type: "morning_brief", payload: { summary: "Morning brief" } }))}>
            {busy === "brief" ? "Running…" : "Run morning brief"}
          </button>
          <button className="btn-ghost" disabled={!!busy}
            onClick={() => confirm("Reset the demo shop?") && run("reset", () => post("/demo/reset"))}>
            {busy === "reset" ? "Resetting…" : "Reset demo"}
          </button>
        </div>
      </div>
      <CrewStatusBar />
      <AgentFeed limit={60} />
    </div>
  );
}
