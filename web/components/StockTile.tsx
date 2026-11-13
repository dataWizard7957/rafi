"use client";
import { useState } from "react";
import { post } from "@/lib/api";
import { Row } from "@/lib/useCollection";

const etaText = (eta?: string) => {
  if (!eta) return null;
  const d = new Date(eta);
  const days = Math.round((d.setHours(0, 0, 0, 0) - new Date().setHours(0, 0, 0, 0)) / 86400000);
  return days <= 0 ? "today" : days === 1 ? "tomorrow morning" : `in ${days} days`;
};

export default function StockTile({ item, drift }: { item: Row; drift?: { systemQty: number; photoQty: number } }) {
  const [busy, setBusy] = useState(false);
  const qty = item.qty ?? 0;
  const status = qty > 0 ? "in stock" : item.restockEta ? "incoming" : "out";
  const low = qty < 0.3 * (item.par ?? 0);
  const tone = status === "out" ? "border-red-200" : low ? "border-amber-200" : "border-cedar-100";
  return (
    <div className={`card ${tone}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="font-semibold">{item.name}</div>
        <span className={`chip ${status === "out" ? "bg-red-50 text-red-700" : status === "incoming" ? "bg-amber-50 text-amber-700" : "bg-cedar-50 text-cedar-700"}`}>
          {status}
        </span>
      </div>
      <div className="mt-1 text-2xl font-bold">
        {qty} <span className="text-sm font-normal text-stone-500">/ par {item.par}</span>
      </div>
      <div className="mt-1 space-y-0.5 text-xs text-stone-600">
        {item.restockEta && <div>Back {etaText(item.restockEta)}</div>}
        {item.lostDemand > 0 && <div className="text-date-600">{item.lostDemand} missed requests this week</div>}
        {drift && <div className="text-amber-700">Drift: system said {drift.systemQty}, shelf showed {drift.photoQty}</div>}
      </div>
      {status !== "in stock" && (
        <button
          className="btn-ghost mt-3 w-full"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try { await post(`/inventory/${item.id}/received`); } finally { setBusy(false); }
          }}
        >
          {busy ? "Saving…" : "Received"}
        </button>
      )}
    </div>
  );
}
