"use client";
import { useCollection, timeAgo } from "@/lib/useCollection";
import { agentLabel, agentTone } from "./agents";

export default function AgentFeed({ limit = 30 }: { limit?: number }) {
  const events = useCollection("agentEvents", { orderBy: "createdAt", desc: true, limit });
  return (
    <ul className="space-y-2">
      {events.length === 0 && <li className="text-sm text-stone-500">No agent activity yet.</li>}
      {events.map((e) => (
        <li key={e.id} className="rounded-lg border border-stone-100 bg-white p-3 text-sm">
          <div className="mb-1 flex flex-wrap items-center gap-1.5">
            <span className={`chip ${agentTone(e.from)}`}>{agentLabel(e.from)}</span>
            {e.to && e.to !== "feed" && (
              <>
                <span className="text-stone-400">→</span>
                <span className={`chip ${agentTone(e.to)}`}>{agentLabel(e.to)}</span>
              </>
            )}
            <span className="ml-auto text-xs text-stone-400">{timeAgo(e.createdAt)}</span>
          </div>
          <div className="text-stone-700">
            {e.type === "notify_simulated" && <span className="mr-1 text-xs text-date-600">[simulated SMS]</span>}
            {e.message}
          </div>
        </li>
      ))}
    </ul>
  );
}
