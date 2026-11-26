// Demo mode (NEXT_PUBLIC_DEMO=true): the real dashboard on in-browser sample data.
// No Firebase, Google Cloud or Orchestrate. Agent work is scripted to follow the
// README loop; everything resets on reload or with "Reset demo".
import inventorySeed from "../../seed/inventory.json";
import suppliersSeed from "../../seed/suppliers.json";
import settingsSeed from "../../seed/settings.json";

export const DEMO = process.env.NEXT_PUBLIC_DEMO === "true";

type Row = { id: string; [key: string]: any };
type Store = Record<string, Row[]>;
type Listener = () => void;

const listeners = new Set<Listener>();
let store: Store = {};
let seq = 0;
let started = false;

const iso = (msAgo = 0) => new Date(Date.now() - msAgo).toISOString();
const id = () => `d${Date.now().toString(36)}${(seq++).toString(36)}`;
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const emit = () => listeners.forEach((l) => l());

function rows(name: string): Row[] {
  return (store[name] ??= []);
}
function add(name: string, data: Record<string, any>, docId = id()): Row {
  const row = { id: docId, createdAt: iso(), ...data };
  store[name] = [...rows(name), row];
  emit();
  return row;
}
function update(name: string, docId: string, patch: Record<string, any>) {
  store[name] = rows(name).map((r) => (r.id === docId ? { ...r, ...patch } : r));
  emit();
}
function get(name: string, docId: string) {
  return rows(name).find((r) => r.id === docId);
}
function log(from: string, to: string, type: string, message: string) {
  add("agentEvents", { from, to, type, message });
}

// ---------------------------------------------------------------- reviews
const THEMES: [RegExp, string, string | null][] = [
  [/hummus/i, "Out of stock", "hummus-sahadi"],
  [/called|calling|picked up|no answer/i, "Unanswered calls", null],
  [/line|waited|wait/i, "Long waits", null],
  [/sticky|floor/i, "Cleanliness", null],
  [/expiry|stale/i, "Freshness", "feta"],
  [/prices went up/i, "Prices", "olive-oil"],
];

function parseCsv(text: string): Record<string, string>[] {
  const lines = text.replace(/^﻿/, "").trim().split(/\r?\n/);
  const split = (line: string) => {
    const out: string[] = [];
    let cur = "";
    let quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
      else if (ch === '"') quoted = !quoted;
      else if (ch === "," && !quoted) { out.push(cur); cur = ""; }
      else cur += ch;
    }
    out.push(cur);
    return out;
  };
  const head = split(lines[0]);
  return lines.slice(1).map((l) => Object.fromEntries(split(l).map((v, i) => [head[i], v])));
}

function label(r: Row) {
  const rating = Number(r.rating) || 0;
  const sentiment = rating <= 2 ? "negative" : rating >= 4 ? "positive" : "neutral";
  const hit = THEMES.find(([re]) => re.test(r.text));
  return { theme: hit ? hit[1] : sentiment === "positive" ? "Praise" : "Other", sentiment, item: hit?.[2] ?? null };
}

function reviewTasks() {
  const neg = rows("reviews").filter((r) => r.sentiment === "negative");
  const count = (t: string) => neg.filter((r) => r.theme === t).length;
  const tasks: [string, string, string, number][] = [
    ["Keep Sahadi hummus in stock", "Customers keep finding the shelf empty, often after work.", "high", count("Out of stock")],
    ["Answer the phone, or let Rafi do it", "Callers say nobody picks up. Front Desk can take these calls.", "high", count("Unanswered calls")],
    ["Add a second cashier on Saturdays", "Weekend lines and deli waits come up again and again.", "medium", count("Long waits")],
    ["Mop near the fridge daily", "Several reviews mention a sticky floor by the fridge.", "low", count("Cleanliness")],
  ];
  for (const [title, detail, priority, n] of tasks)
    if (n) add("tasks", { title, detail, priority, createdBy: "review_agent", evidenceCount: n, status: "open" });
}

function loadReviews(text: string) {
  const parsed = parseCsv(text);
  for (const r of parsed) {
    const rid = r.id || id();
    store.reviews = rows("reviews").filter((x) => x.id !== rid);
    add("reviews", { text: r.text ?? "", rating: Number(r.rating) || 0, date: r.date ?? "", theme: null }, rid);
  }
  return parsed.length;
}

// ---------------------------------------------------------------- seed
async function seed() {
  store = {};
  for (const item of inventorySeed as any[]) {
    const { sku, ...rest } = item;
    add("inventory", { lostDemand: 0, restockEta: null, ...rest }, sku);
  }
  for (const s of suppliersSeed as any[]) {
    const { id: sid, ...rest } = s;
    add("suppliers", rest, sid);
  }
  add("settings", { ...settingsSeed, posFeedRunning: false }, "main");
  // The Review Agent's analysis runs before the demo, so it is already there.
  try {
    const csv = await (await fetch("/demo/reviews.csv")).text();
    loadReviews(csv);
    for (const r of rows("reviews")) update("reviews", r.id, label(r));
    reviewTasks();
  } catch {
    /* reviews are optional */
  }
  add("agentEvents", { from: "review_agent", to: "feed", type: "note",
    message: "Labeled 80 reviews overnight. Top complaints: hummus out of stock and unanswered calls.", createdAt: iso(3_600_000) });
  add("agentEvents", { from: "system", to: "feed", type: "reset", message: "Demo shop ready: Cedar & Date Market", createdAt: iso(60_000) });
}

export function ensureDemo() {
  if (started) return;
  started = true;
  seed();
}

export function subscribe(listener: Listener) {
  ensureDemo();
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function query(name: string, opts: { orderBy?: string; desc?: boolean; limit?: number } = {}): Row[] {
  let out = [...rows(name)];
  if (opts.orderBy) {
    const k = opts.orderBy;
    out.sort((a, b) => String(a[k] ?? "").localeCompare(String(b[k] ?? "")) * (opts.desc ? -1 : 1));
  }
  return opts.limit ? out.slice(0, opts.limit) : out;
}

// ---------------------------------------------------------------- actions
function nineAm(daysAhead: number) {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  d.setHours(9, 0, 0, 0);
  return d;
}

async function approve(draftId: string) {
  const draft = get("supplierDrafts", draftId);
  if (!draft) throw new Error("404 Unknown draft");
  const supplier: Record<string, any> = get("suppliers", draft.supplierId) ?? {};
  const lead = Number(supplier.leadTimeDays ?? 1) + (get("settings", "main")?.snow_expected ? 1 : 0);
  const eta = nineAm(lead);
  for (const line of draft.lines ?? []) update("inventory", line.sku, { restockEta: eta.toISOString() });
  update("supplierDrafts", draftId, { status: "approved", approvedAt: iso(), restockEta: eta.toISOString() });
  const day = eta.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
  log("owner", "manager", "order_approved", `Fatima approved the ${draft.supplierName} order. Expected ${day}, 9 am.`);
  return { ok: true, restockEta: eta.toISOString() };
}

async function received(sku: string) {
  const item = get("inventory", sku);
  if (!item) throw new Error("404 Unknown sku");
  const qty = item.par ?? 10;
  update("inventory", sku, { qty: (item.qty ?? 0) + qty, restockEta: null });
  log("owner", "feed", "delivery_received", `${qty} ${item.name} received`);
  log("owner", "manager", "restocked", `${item.name} restocked: fulfill holds, notify, reply`);
  (async () => {
    await wait(1200);
    const waiting = rows("holds").filter((h) => h.sku === sku && h.status === "waiting");
    for (const h of waiting) {
      add("orders", { items: [{ sku, name: h.item, qty: h.qty }], customerName: h.customerName, phone: h.phone,
        language: h.language, status: "ready", source: "hold" });
      update("holds", h.id, { status: "ready" });
      await wait(600);
      const msg = `Hi ${h.customerName}, your ${h.qty} ${h.item} are ready for pickup at Cedar & Date Market.`;
      update("holds", h.id, { notification: msg });
      log("manager", h.customerName, "notify_simulated", msg);
    }
    if (waiting.length) log("manager", "feed", "note", `Fulfilled ${waiting.length} hold${waiting.length > 1 ? "s" : ""} for ${item.name}.`);
    await wait(1200);
    const complaints = rows("reviews").filter((r) => r.item === sku && !r.replyDraft).slice(0, 3);
    if (complaints.length) log("manager", "review_agent", "draft_replies", `Draft replies to reviews about ${item.name}`);
    const replies = [
      `Thank you for telling us. ${item.name} is back on the shelf, and we now reorder it before it runs out. Hope to see you soon!`,
      `Sorry about the empty shelf. ${item.name} just arrived, and you can call ahead and we'll hold some for you.`,
      `We heard you! ${item.name} is restocked today. Thanks for your patience and for shopping with us.`,
    ];
    for (const [i, r] of complaints.entries()) {
      await wait(700);
      const text = replies[i % replies.length];
      update("reviews", r.id, { replyDraft: text });
      log("review_agent", "feed", "reply_drafted", text);
    }
  })();
  return { ok: true };
}

async function morningBrief() {
  log("owner", "manager", "morning_brief", "Morning brief");
  (async () => {
    await wait(1500);
    const out = rows("inventory").filter((i) => (i.qty ?? 0) === 0 && !i.restockEta);
    const low = rows("inventory").filter((i) => (i.qty ?? 0) > 0 && i.qty < 0.6 * (i.par ?? 0));
    for (const i of out)
      add("tasks", { title: `${i.name} is out of stock`, detail: i.lostDemand ? `${i.lostDemand} callers asked for it this week. Approve a reorder on Orders.` : "Check the reorder on Orders.",
        priority: "high", createdBy: "manager", evidenceCount: i.lostDemand || 0, status: "open" });
    if (get("settings", "main")?.snow_expected)
      add("tasks", { title: "Snow expected tomorrow: stock up", detail: `Deliveries may slip a day. Low now: ${low.map((i) => i.name).slice(0, 3).join(", ") || "none"}.`,
        priority: "medium", createdBy: "manager", evidenceCount: low.length, status: "open" });
    log("manager", "owner", "brief_ready", `Morning brief ready: ${out.length} out of stock, ${low.length} running low, snow expected tomorrow.`);
  })();
  return { ok: true };
}

async function shelfPhoto(direct: boolean) {
  const scan = add("scans", { imageUrl: "local:demo", status: "new" });
  if (!direct) log("owner", "manager", "shelf_photo", "New shelf photo to check");
  await wait(direct ? 800 : 400);
  if (!direct) log("manager", "shelf_agent", "scan_shelf", "Count the dips shelf in the new photo");
  (async () => {
    await wait(direct ? 0 : 1500);
    const detections = [
      { item: "House-made hummus", sku: "hummus-house", count: 6, confidence: 0.93 },
      { item: "Baba ghanoush", sku: "baba-ghanoush", count: 6, confidence: 0.9 },
      { item: "Labneh", sku: "labneh", count: 4, confidence: 0.86 },
      { item: "Sahadi hummus", sku: "hummus-sahadi", count: 0, confidence: 0.95 },
    ];
    const drift = detections
      .map((d) => ({ sku: d.sku, item: d.item, systemQty: get("inventory", d.sku)?.qty ?? 0, photoQty: d.count }))
      .filter((d) => Math.abs(d.systemQty - d.photoQty) >= 2);
    update("scans", scan.id, { status: "done", detections, drift });
    for (const d of drift)
      log("shelf_agent", "feed", "drift", `${d.item}: system says ${d.systemQty}, shelf shows ${d.photoQty}`);
    if (!drift.length) log("shelf_agent", "feed", "note", "Shelf matches the system. No drift.");
  })();
  return { scan_id: scan.id, status: direct ? "done" : "sent_to_manager" };
}

async function reviewsUploaded(file: File) {
  const n = loadReviews(await file.text());
  log("owner", "manager", "reviews_uploaded", `${n} new reviews to read`);
  (async () => {
    await wait(1200);
    log("manager", "review_agent", "label_reviews", `Label ${n} reviews by theme`);
    await wait(1500);
    for (const r of rows("reviews").filter((x) => !x.theme)) update("reviews", r.id, label(r));
    store.tasks = rows("tasks").filter((t) => t.createdBy !== "review_agent");
    reviewTasks();
    log("review_agent", "feed", "note", `Labeled ${n} reviews. Top complaints: hummus out of stock and unanswered calls.`);
  })();
  return { loaded: n };
}

export async function demoPost(path: string): Promise<any> {
  ensureDemo();
  await wait(300);
  let m: RegExpMatchArray | null;
  if ((m = path.match(/^\/orders\/([^/]+)\/approve$/))) return approve(m[1]);
  if ((m = path.match(/^\/inventory\/([^/]+)\/received$/))) return received(m[1]);
  if (path === "/agents/event") return morningBrief();
  if (path === "/demo/reset") { await seed(); return { ok: true }; }
  throw new Error(`Not available in the demo: ${path}`);
}

export async function demoUpload(path: string, file: File): Promise<any> {
  ensureDemo();
  await wait(300);
  if (path.startsWith("/uploads/shelf")) return shelfPhoto(path.includes("direct=true"));
  if (path === "/uploads/reviews") return reviewsUploaded(file);
  throw new Error(`Not available in the demo: ${path}`);
}

// ---------------------------------------------------------------- calls
function etaWords(eta?: string) {
  if (!eta) return "soon";
  const d = new Date(eta);
  const days = Math.round((new Date(d).setHours(0, 0, 0, 0) - new Date().setHours(0, 0, 0, 0)) / 86_400_000);
  return days <= 0 ? "this morning" : days === 1 ? "tomorrow morning" : `${d.toLocaleDateString([], { weekday: "long" })} morning`;
}

export type CallLine = { who: "caller" | "rafi" | "tool"; text: string };

export function callReady(n: 1 | 2): string | null {
  if (n === 2 && !get("inventory", "hummus-sahadi")?.restockEta)
    return "Approve the Sahadi hummus order on Orders first, so Rafi can offer a hold.";
  return null;
}

/** Plays a scripted Front Desk call and applies what its tools would do. */
export async function playCall(n: 1 | 2, onLine: (l: CallLine) => void) {
  ensureDemo();
  const say = async (who: CallLine["who"], text: string, ms = 900) => { await wait(ms); onLine({ who, text }); };
  const transcript: { who: string; text: string }[] = [];
  const t = async (who: "caller" | "rafi", text: string) => { transcript.push({ who, text }); await say(who, text); };
  if (n === 1) {
    await t("caller", "Hi, do you have Sahadi hummus?");
    await say("tool", 'check_stock({"item_name":"Sahadi hummus"}) → out, no restock date', 600);
    await say("tool", 'log_missed_request({"item":"Sahadi hummus","outcome":"substitute"})', 400);
    const h = get("inventory", "hummus-sahadi");
    update("inventory", "hummus-sahadi", { lostDemand: (h?.lostDemand ?? 0) + 1 });
    log("front_desk", "manager", "missed_request", "Caller asked for Sahadi hummus (out). Offered a substitute.");
    await t("rafi", "Sorry, Sahadi hummus is out of stock right now. Would you like our house-made hummus instead?");
    await t("caller", "Sure, I'll take two of the house-made hummus.");
    await t("rafi", "Great. Can I get your name and phone number for the pickup?");
    await t("caller", "My name is Ahmed. 313-555-0100. I'll pick it up today at five.");
    await say("tool", 'place_order({"items":[{"item":"House-made hummus","qty":2}],"customer_name":"Ahmed"})', 600);
    const house = get("inventory", "hummus-house");
    update("inventory", "hummus-house", { qty: Math.max(0, (house?.qty ?? 0) - 2) });
    add("orders", { items: [{ sku: "hummus-house", name: "House-made hummus", qty: 2 }], customerName: "Ahmed",
      phone: "313-555-0100", language: "en", pickupTime: "17:00", status: "new", source: "phone" });
    log("front_desk", "feed", "order_placed", "Order for Ahmed: 2 House-made hummus");
    await t("rafi", "Two house-made hummus for Ahmed, pickup today at 5. You're all set!");
    add("calls", { transcript });
    (async () => {
      await wait(1500);
      if (!rows("supplierDrafts").some((d) => d.status === "draft" && d.lines?.some((l: any) => l.sku === "hummus-sahadi"))) {
        const misses = get("inventory", "hummus-sahadi")?.lostDemand ?? 1;
        const reviews = rows("reviews").filter((r) => r.item === "hummus-sahadi" && r.sentiment === "negative").length;
        const supplier = get("suppliers", "produce");
        add("supplierDrafts", { supplierId: "produce", supplierName: supplier?.name, status: "draft",
          lines: [{ sku: "hummus-sahadi", qty: 24 }, { sku: "hummus-house", qty: 6 }],
          reason: `Sahadi hummus is out: ${misses} missed request${misses > 1 ? "s" : ""} today and ${reviews} reviews complaining it's never in stock. House-made is down to ${get("inventory", "hummus-house")?.qty}.` });
        log("manager", "owner", "order_drafted", `Order for ${supplier?.name}: restock Sahadi hummus. Waiting for your approval.`);
      }
    })();
  } else {
    const when = etaWords(get("inventory", "hummus-sahadi")?.restockEta);
    await t("caller", "Hi, is Sahadi hummus back in stock?");
    await say("tool", `check_stock({"item_name":"Sahadi hummus"}) → incoming, ${when}`, 600);
    await t("rafi", `Not yet, but it's arriving ${when}. Would you like me to hold some for you?`);
    await t("caller", "Yes please, hold two for me. I'm Sara, 313-555-0199.");
    await say("tool", 'add_hold({"item":"Sahadi hummus","qty":2,"customer_name":"Sara"})', 600);
    add("holds", { sku: "hummus-sahadi", item: "Sahadi hummus", qty: 2, customerName: "Sara", phone: "313-555-0199",
      language: "en", status: "waiting" });
    log("front_desk", "manager", "demand", "Sara is waiting on 2 Sahadi hummus");
    await t("rafi", "Done. Two Sahadi hummus are on hold for you, and we'll let you know when they arrive.");
    add("calls", { transcript });
  }
}
