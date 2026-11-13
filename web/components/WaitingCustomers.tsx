"use client";
import { useCollection } from "@/lib/useCollection";

export default function WaitingCustomers() {
  const holds = useCollection("holds", { orderBy: "createdAt", desc: true });
  return (
    <ul className="space-y-2">
      {holds.length === 0 && <li className="text-sm text-stone-500">No one is waiting.</li>}
      {holds.map((h) => (
        <li key={h.id} className="rounded-lg border border-stone-100 bg-white p-3 text-sm">
          <div className="flex justify-between">
            <span className="font-medium">{h.customerName}</span>
            <span className={`chip ${h.status === "ready" ? "bg-cedar-100 text-cedar-800" : "bg-amber-50 text-amber-700"}`}>
              {h.status}
            </span>
          </div>
          <div className="text-stone-600">
            {h.qty} × {h.item} {h.language ? `· ${h.language}` : ""}
          </div>
          {h.notification && <div className="mt-1 text-xs text-date-600">[simulated SMS] {h.notification}</div>}
        </li>
      ))}
    </ul>
  );
}
