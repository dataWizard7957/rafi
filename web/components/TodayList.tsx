"use client";
import { useCollection } from "@/lib/useCollection";
import { agentLabel, agentTone } from "./agents";

const rank: Record<string, number> = { high: 0, medium: 1, low: 2 };

export default function TodayList({ max = 5 }: { max?: number }) {
  const tasks = useCollection("tasks")
    .filter((t) => t.status === "open")
    .sort((a, b) => (rank[a.priority] ?? 3) - (rank[b.priority] ?? 3))
    .slice(0, max);
  return (
    <ol className="space-y-2">
      {tasks.length === 0 && <li className="text-sm text-stone-500">Nothing yet. Run the morning brief.</li>}
      {tasks.map((t, i) => (
        <li key={t.id} className="flex gap-3 rounded-lg border border-stone-100 bg-white p-3">
          <span className="text-lg font-bold text-cedar-600">{i + 1}</span>
          <div className="flex-1">
            <div className="font-medium">{t.title}</div>
            {t.detail && <div className="text-sm text-stone-600">{t.detail}</div>}
            <div className="mt-1 flex gap-2">
              <span className={`chip ${agentTone(t.createdBy)}`}>{agentLabel(t.createdBy)}</span>
              {t.priority === "high" && <span className="chip bg-red-50 text-red-700">High</span>}
              {t.evidenceCount > 0 && <span className="chip bg-stone-100 text-stone-600">{t.evidenceCount} signals</span>}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
