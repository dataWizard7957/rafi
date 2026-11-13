"use client";
import { useEffect, useState } from "react";
import { onSnapshot, orderBy as ob, limit as lim, query, QueryConstraint } from "firebase/firestore";
import { shopCol } from "./firebase";

export type Row = { id: string; [key: string]: any };

/** Live Firestore collection under shops/{SHOP_ID}/{name}. */
export function useCollection(name: string, opts: { orderBy?: string; desc?: boolean; limit?: number } = {}) {
  const [rows, setRows] = useState<Row[]>([]);
  useEffect(() => {
    const c: QueryConstraint[] = [];
    if (opts.orderBy) c.push(ob(opts.orderBy, opts.desc ? "desc" : "asc"));
    if (opts.limit) c.push(lim(opts.limit));
    return onSnapshot(query(shopCol(name), ...c), (snap) =>
      setRows(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
    );
  }, [name, opts.orderBy, opts.desc, opts.limit]);
  return rows;
}

export const toDate = (ts: any): Date | null =>
  ts?.toDate ? ts.toDate() : typeof ts === "string" ? new Date(ts) : null;

export const timeAgo = (ts: any) => {
  const d = toDate(ts);
  if (!d) return "just now";
  const s = Math.max(0, Math.round((Date.now() - d.getTime()) / 1000));
  return s < 60 ? `${s}s ago` : s < 3600 ? `${Math.round(s / 60)}m ago` : `${Math.round(s / 3600)}h ago`;
};
