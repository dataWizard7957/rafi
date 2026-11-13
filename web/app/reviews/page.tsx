"use client";
import { useState } from "react";
import { upload } from "@/lib/api";
import { useCollection } from "@/lib/useCollection";

export default function Reviews() {
  const reviews = useCollection("reviews");
  const tasks = useCollection("tasks").filter((t) => t.createdBy === "review_agent");
  const [busy, setBusy] = useState(false);
  const labeled = reviews.filter((r) => r.theme);
  const themes: Record<string, number> = {};
  labeled.filter((r) => r.sentiment === "negative").forEach((r) => (themes[r.theme] = (themes[r.theme] ?? 0) + 1));
  const max = Math.max(1, ...Object.values(themes));
  const replies = reviews.filter((r) => r.replyDraft);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="h2 text-2xl">Reviews</h1>
        <label className="btn cursor-pointer">
          {busy ? "Uploading…" : "Upload reviews CSV"}
          <input type="file" accept=".csv" className="hidden" onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            setBusy(true);
            try { await upload("/uploads/reviews", "file", f); } finally { setBusy(false); }
          }} />
        </label>
      </div>
      <p className="text-sm text-stone-600">{labeled.length} of {reviews.length} reviews labeled by the Review Agent.</p>
      <div className="grid gap-6 md:grid-cols-2">
        <section className="card">
          <h2 className="h2">Complaint themes</h2>
          {Object.entries(themes).sort((a, b) => b[1] - a[1]).map(([t, n]) => (
            <div key={t} className="mb-2">
              <div className="flex justify-between text-sm"><span>{t}</span><span>{n}</span></div>
              <div className="h-2 rounded bg-cedar-50"><div className="h-2 rounded bg-cedar-600" style={{ width: `${(n / max) * 100}%` }} /></div>
            </div>
          ))}
          {Object.keys(themes).length === 0 && <p className="text-sm text-stone-500">No complaints labeled yet.</p>}
        </section>
        <section className="card">
          <h2 className="h2">Fixes from reviews</h2>
          <ul className="space-y-2 text-sm">
            {tasks.map((t) => (
              <li key={t.id}><span className="font-medium">{t.title}</span>{t.evidenceCount ? ` · ${t.evidenceCount} reviews` : ""}<div className="text-stone-600">{t.detail}</div></li>
            ))}
          </ul>
        </section>
      </div>
      <section>
        <h2 className="h2">Reply drafts</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {replies.map((r) => (
            <div key={r.id} className="card text-sm">
              <div className="text-stone-500">“{r.text}” · {r.rating}★</div>
              <div className="mt-2 rounded-lg bg-cedar-50 p-2 text-cedar-800">{r.replyDraft}</div>
              <button className="btn-ghost mt-2" onClick={() => navigator.clipboard.writeText(r.replyDraft)}>Copy</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
