"use client";
import AgentFeed from "@/components/AgentFeed";
import LiveCallPanel from "@/components/LiveCallPanel";
import DemoCallScript from "@/components/DemoCallScript";
import RecentCalls from "@/components/RecentCalls";

export default function FrontDesk() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <h1 className="h2 text-2xl">Front Desk</h1>
        <p className="mb-4 text-sm text-stone-600">
          Demo uses the browser microphone. Rafi answers in the caller&apos;s language and uses live stock.
        </p>
        <LiveCallPanel />
        <DemoCallScript />
        <RecentCalls />
      </div>
      <aside>
        <h2 className="h2">Agent feed</h2>
        <AgentFeed limit={10} />
      </aside>
    </div>
  );
}
