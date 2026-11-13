"use client";
import { useState } from "react";
import { post } from "@/lib/api";
import { Row } from "@/lib/useCollection";

export default function ReorderCard({ draft }: { draft: Row }) {
  const [busy, setBusy] = useState(false);
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="font-semibold">{draft.supplierName ?? draft.supplierId}</div>
        <span className={`chip ${draft.status === "approved" ? "bg-cedar-100 text-cedar-800" : "bg-amber-50 text-amber-700"}`}>
          {draft.status === "approved" ? "Approved" : "Waiting for you"}
        </span>
      </div>
      <ul className="my-2 text-sm">
        {(draft.lines ?? []).map((l: any) => (
          <li key={l.sku}>{l.qty} × {l.sku}</li>
        ))}
      </ul>
      <div className="rounded-lg bg-cedar-50 p-2 text-sm text-cedar-800">
        <span className="font-medium">Why: </span>{draft.reason}
      </div>
      {draft.status !== "approved" && (
        <button
          className="btn mt-3 w-full"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try { await post(`/orders/${draft.id}/approve`); } finally { setBusy(false); }
          }}
        >
          {busy ? "Approving…" : "Approve order"}
        </button>
      )}
    </div>
  );
}
