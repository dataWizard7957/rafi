"use client";
import ReorderCard from "@/components/ReorderCard";
import WaitingCustomers from "@/components/WaitingCustomers";
import { useCollection } from "@/lib/useCollection";

export default function Orders() {
  const drafts = useCollection("supplierDrafts", { orderBy: "createdAt", desc: true });
  const orders = useCollection("orders", { orderBy: "createdAt", desc: true, limit: 20 });
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <section className="lg:col-span-2">
        <h1 className="h2 text-2xl">Supplier orders</h1>
        <p className="mb-3 text-sm text-stone-600">Nothing is ordered until you approve it.</p>
        <div className="grid gap-3 md:grid-cols-2">
          {drafts.map((d) => <ReorderCard key={d.id} draft={d} />)}
          {drafts.length === 0 && <div className="text-sm text-stone-500">No drafts yet.</div>}
        </div>
        <h2 className="h2 mt-6">Customer orders</h2>
        <ul className="space-y-2 text-sm">
          {orders.map((o) => (
            <li key={o.id} className="rounded-lg border border-stone-100 bg-white p-3">
              <span className="font-medium">{o.customerName}</span>{" "}
              <span className="chip bg-stone-100 text-stone-600">{o.source}</span>{" "}
              <span className="chip bg-cedar-50 text-cedar-700">{o.status}</span>
              <div>{(o.items ?? []).map((l: any) => `${l.qty} ${l.name ?? l.sku}`).join(", ")}</div>
            </li>
          ))}
        </ul>
      </section>
      <aside>
        <h2 className="h2">Waiting customers</h2>
        <WaitingCustomers />
      </aside>
    </div>
  );
}
