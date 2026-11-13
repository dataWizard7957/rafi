"use client";
import { useEffect, useState } from "react";
import { useCollection, toDate } from "@/lib/useCollection";

const CREW = [
  ["front_desk", "Front Desk", "Gemini Live"],
  ["shelf_agent", "Shelf Agent", "Orchestrate · Granite"],
  ["review_agent", "Review Agent", "Orchestrate · Granite"],
  ["manager", "Rafi Manager", "Orchestrate · Granite"],
];

export default function CrewStatusBar() {
  const events = useCollection("agentEvents", { orderBy: "createdAt", desc: true, limit: 20 });
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 2000);
    return () => clearInterval(t);
  }, []);
  const active = (id: string) =>
    events.some((e) => e.from === id && now - (toDate(e.createdAt)?.getTime() ?? now) < 15000);
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {CREW.map(([id, name, runs]) => (
        <div key={id} className="card flex items-center gap-3 py-3">
          <span className={`h-3 w-3 rounded-full ${active(id) ? "animate-pulse bg-cedar-600" : "bg-stone-300"}`} />
          <div>
            <div className="font-semibold">{name}</div>
            <div className="text-xs text-stone-500">{runs}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
