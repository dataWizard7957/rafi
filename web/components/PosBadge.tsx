"use client";
import { useEffect, useState } from "react";
import { useCollection, toDate } from "@/lib/useCollection";

export default function PosBadge() {
  const settings = useCollection("settings");
  const main = settings.find((s) => s.id === "main");
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 3000);
    return () => clearInterval(t);
  }, []);
  const last = toDate(main?.posFeedLastSale)?.getTime() ?? 0;
  const live = main?.posFeedRunning && now - last < 30000;
  return (
    <span className={`chip ${live ? "bg-cedar-100 text-cedar-800" : "bg-stone-100 text-stone-500"}`}>
      <span className={`mr-1.5 h-2 w-2 rounded-full ${live ? "animate-pulse bg-cedar-600" : "bg-stone-400"}`} />
      POS sales feed (simulated){live ? "" : " · off"}
    </span>
  );
}
