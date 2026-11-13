export const AGENTS: Record<string, { label: string; tone: string }> = {
  front_desk: { label: "Front Desk", tone: "bg-date-100 text-date-600" },
  shelf_agent: { label: "Shelf Agent", tone: "bg-cedar-50 text-cedar-700" },
  review_agent: { label: "Review Agent", tone: "bg-cedar-50 text-cedar-700" },
  manager: { label: "Rafi Manager", tone: "bg-cedar-100 text-cedar-800" },
  owner: { label: "Fatima", tone: "bg-stone-100 text-stone-700" },
  api: { label: "System", tone: "bg-stone-100 text-stone-600" },
  system: { label: "System", tone: "bg-stone-100 text-stone-600" },
};
export const agentLabel = (id: string) => AGENTS[id]?.label ?? id;
export const agentTone = (id: string) => AGENTS[id]?.tone ?? "bg-stone-100 text-stone-600";
