"use client";
import AgentFeed from "@/components/AgentFeed";
import CrewStatusBar from "@/components/CrewStatusBar";
import PosBadge from "@/components/PosBadge";
import StockTile from "@/components/StockTile";
import TodayList from "@/components/TodayList";
import WaitingCustomers from "@/components/WaitingCustomers";
import { useCollection } from "@/lib/useCollection";

export default function Today() {
  const inventory = useCollection("inventory");
  const orders = useCollection("orders", { orderBy: "createdAt", desc: true, limit: 5 });
  const scans = useCollection("scans", { orderBy: "createdAt", desc: true, limit: 1 });
  const drift = Object.fromEntries((scans[0]?.drift ?? []).map((d: any) => [d.sku, d]));
  const watch = inventory
    .filter((i) => (i.qty ?? 0) < 0.3 * (i.par ?? 0) || i.lostDemand > 0 || drift[i.id] || i.restockEta)
    .sort((a, b) => (a.qty ?? 0) - (b.qty ?? 0));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-cedar-800">Good morning, Fatima</h1>
        <PosBadge />
      </div>
      <CrewStatusBar />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section>
            <h2 className="h2">Today&apos;s priorities</h2>
            <TodayList max={5} />
          </section>
          <section>
            <h2 className="h2">Stock to watch</h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {watch.map((i) => <StockTile key={i.id} item={i} drift={drift[i.id]} />)}
              {watch.length === 0 && <div className="text-sm text-stone-500">All stock looks healthy.</div>}
            </div>
          </section>
          <div className="grid gap-6 md:grid-cols-2">
            <section>
              <h2 className="h2">Latest orders</h2>
              <ul className="space-y-2 text-sm">
                {orders.map((o) => (
                  <li key={o.id} className="rounded-lg border border-stone-100 bg-white p-3">
                    <span className="font-medium">{o.customerName}</span>{" "}
                    <span className="text-stone-500">({o.source})</span>
                    <div>{(o.items ?? []).map((l: any) => `${l.qty} ${l.name ?? l.sku}`).join(", ")}</div>
                  </li>
                ))}
              </ul>
            </section>
            <section>
              <h2 className="h2">Waiting customers</h2>
              <WaitingCustomers />
            </section>
          </div>
        </div>
        <aside>
          <h2 className="h2">Agent feed</h2>
          <AgentFeed limit={12} />
        </aside>
      </div>
    </div>
  );
}
