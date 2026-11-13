"use client";
import { useState } from "react";
import { upload } from "@/lib/api";
import { useCollection } from "@/lib/useCollection";

export default function Shelf() {
  const scans = useCollection("scans", { orderBy: "createdAt", desc: true, limit: 1 });
  const [busy, setBusy] = useState(false);
  const [direct, setDirect] = useState(false);
  const [error, setError] = useState("");
  const scan = scans[0];

  async function send(file?: File) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await upload(`/uploads/shelf${direct ? "?direct=true" : ""}`, "photo", file);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="h2 text-2xl">Shelf</h1>
      <div className="card flex flex-wrap items-center gap-4">
        <label className="btn cursor-pointer">
          {busy ? "Uploading…" : "Take or upload shelf photo"}
          <input type="file" accept="image/*" capture="environment" className="hidden"
                 onChange={(e) => send(e.target.files?.[0])} />
        </label>
        <label className="flex items-center gap-2 text-sm text-stone-600">
          <input type="checkbox" checked={direct} onChange={(e) => setDirect(e.target.checked)} />
          Scan directly (skip agents, fallback mode)
        </label>
        {error && <div className="text-sm text-red-600">{error}</div>}
      </div>
      {scan && (
        <div className="grid gap-6 md:grid-cols-2">
          <section className="card">
            <h2 className="h2">Latest scan · {scan.status}</h2>
            {scan.status === "retake" && <p className="text-amber-700">Photo was unclear. Please take another.</p>}
            <ul className="space-y-1 text-sm">
              {(scan.detections ?? []).map((d: any) => (
                <li key={d.item} className="flex justify-between">
                  <span>{d.item}</span>
                  <span className="text-stone-500">{d.count} · {Math.round(d.confidence * 100)}%</span>
                </li>
              ))}
            </ul>
          </section>
          <section className="card">
            <h2 className="h2">Drift (system vs shelf)</h2>
            {(scan.drift ?? []).length === 0 && <p className="text-sm text-stone-500">No drift found.</p>}
            <ul className="space-y-2 text-sm">
              {(scan.drift ?? []).map((d: any) => (
                <li key={d.sku} className="rounded-lg bg-amber-50 p-2 text-amber-800">
                  {d.item}: system says {d.systemQty}, shelf shows {d.photoQty}
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
