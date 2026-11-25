"""Routes called by the Orchestrate agents' Python tools. All require the X-Rafi-Key header."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

import inventory_source as inv
from config import RAFI_KEY
from db import SERVER_TS, col, docs, get_settings
from events import log_event
from vision import scan_shelf

THEMES = {"food quality", "wait time", "staff", "price", "cleanliness", "stock or availability", "other"}
SENTIMENTS = {"positive", "neutral", "negative"}


def require_key(x_rafi_key: str = Header(default="")):
    if x_rafi_key != RAFI_KEY:
        raise HTTPException(status_code=401, detail="Bad X-Rafi-Key")


router = APIRouter(prefix="/tools", dependencies=[Depends(require_key)])


# ---------- Stock and orders ----------

@router.get("/stock")
def stock():
    items = inv.get_stock()
    for i in items:
        i["sales24h"] = inv.sales_last_hours(i["sku"], 24)
    return {"items": items}


@router.get("/orders")
def orders(hours: int = 24):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = [o for o in docs("orders") if not o.get("createdAt") or o["createdAt"] >= since]
    return {"orders": rows}


@router.get("/settings")
def settings():
    return get_settings()


class ScanIn(BaseModel):
    scan_id: str


@router.post("/scan_shelf")
def tool_scan_shelf(body: ScanIn):
    result = scan_shelf(body.scan_id)
    for d in result.get("drift", []):
        log_event("shelf_agent", "feed", "drift",
                  f"{d['item']}: system says {d['systemQty']}, shelf shows {d['photoQty']}")
    return result


class SkuIn(BaseModel):
    sku: str


@router.post("/mark_restocked")
def mark_restocked(body: SkuIn):
    item = inv.get_item(body.sku)
    if not item:
        raise HTTPException(404, "Unknown sku")
    col("inventory").document(body.sku).update({"restockEta": None})
    log_event("shelf_agent", "manager", "restocked", f"{item['name']} is back on the shelf")
    return {"ok": True}


# ---------- Reviews ----------

@router.get("/reviews")
def new_reviews(limit: int = 20):
    rows = [r for r in docs("reviews") if not r.get("theme")]
    return {"reviews": [{"id": r["id"], "text": r.get("text"), "rating": r.get("rating")} for r in rows[:limit]],
            "remaining": max(0, len(rows) - limit)}


class Label(BaseModel):
    id: str
    theme: str
    sentiment: str
    item: str | None = None
    quote: str | None = None


class LabelsIn(BaseModel):
    labels: list[Label]


@router.post("/review_labels")
def review_labels(body: LabelsIn):
    errors, saved = [], 0
    for lb in body.labels:
        if lb.theme not in THEMES:
            errors.append(f"{lb.id}: theme must be one of {sorted(THEMES)}")
            continue
        if lb.sentiment not in SENTIMENTS:
            errors.append(f"{lb.id}: sentiment must be positive, neutral or negative")
            continue
        quote = " ".join((lb.quote or "").split()[:10]) or None
        col("reviews").document(lb.id).update(
            {"theme": lb.theme, "sentiment": lb.sentiment, "item": lb.item, "quote": quote})
        saved += 1
    return {"saved": saved, "errors": errors}


class ReplyIn(BaseModel):
    review_id: str
    text: str


@router.post("/replies")
def replies(body: ReplyIn):
    col("reviews").document(body.review_id).update({"replyDraft": body.text})
    log_event("review_agent", "feed", "reply_drafted", body.text[:140])
    return {"ok": True}


# ---------- Tasks, orders, holds, feed ----------

class TaskIn(BaseModel):
    title: str
    detail: str = ""
    priority: str = "medium"
    created_by: str = "manager"
    evidence_count: int = 0


@router.post("/tasks")
def tasks(body: TaskIn):
    col("tasks").add({"title": body.title, "detail": body.detail, "priority": body.priority,
                      "createdBy": body.created_by, "evidenceCount": body.evidence_count,
                      "status": "open", "createdAt": SERVER_TS})
    return {"ok": True}


@router.get("/open_tasks")
def open_tasks():
    return {"tasks": [t for t in docs("tasks") if t.get("status") == "open"]}


class Line(BaseModel):
    sku: str
    qty: int


class DraftIn(BaseModel):
    supplier_id: str
    lines: list[Line]
    reason: str


@router.post("/supplier_drafts")
def supplier_drafts(body: DraftIn):
    # The model sometimes sends "supplier_produce" or "Produce" for the id "produce"; normalise it.
    sid = body.supplier_id.strip().lower().removeprefix("supplier_").removeprefix("supplier-")
    supplier = col("suppliers").document(sid).get().to_dict() or {}
    if supplier:
        body.supplier_id = sid
    names = {i["sku"]: i["name"] for i in inv.get_stock()}
    order_text = "\n".join(f"- {ln.qty} x {names.get(ln.sku, ln.sku)}" for ln in body.lines)
    email = (f"Hello {supplier.get('name', 'team')},\n\nCedar & Date Market would like to order:\n"
             f"{order_text}\n\nThank you,\nFatima")
    _, ref = col("supplierDrafts").add({"supplierId": body.supplier_id, "supplierName": supplier.get("name"),
                                        "lines": [ln.model_dump() for ln in body.lines], "reason": body.reason,
                                        "emailBody": email, "status": "draft", "createdAt": SERVER_TS})
    log_event("manager", "owner", "order_drafted", f"Order for {supplier.get('name')}: {body.reason}")
    return {"ok": True, "draft_id": ref.id}


@router.get("/holds")
def holds():
    return {"holds": [h for h in docs("holds") if h.get("status") == "waiting"]}


@router.post("/holds/fulfill")
def fulfill_holds(body: SkuIn):
    fulfilled = []
    for h in docs("holds"):
        if h.get("sku") != body.sku or h.get("status") != "waiting":
            continue
        item = inv.get_item(body.sku)
        if not item or item.get("qty", 0) < h["qty"]:
            break
        inv.record_sale(body.sku, h["qty"], "hold")
        col("orders").add({"items": [{"sku": body.sku, "name": h.get("item"), "qty": h["qty"]}],
                           "customerName": h.get("customerName"), "phone": h.get("phone"),
                           "language": h.get("language"), "status": "ready", "source": "hold",
                           "createdAt": SERVER_TS})
        col("holds").document(h["id"]).update({"status": "ready"})
        fulfilled.append({"hold_id": h["id"], "customer": h.get("customerName"), "language": h.get("language")})
    return {"fulfilled": fulfilled}


class NotifyIn(BaseModel):
    hold_id: str
    message: str


@router.post("/notify")
def notify(body: NotifyIn):
    hold = col("holds").document(body.hold_id).get().to_dict() or {}
    col("holds").document(body.hold_id).update({"notification": body.message})
    log_event("manager", hold.get("customerName", "customer"), "notify_simulated", body.message)
    return {"ok": True, "simulated": True}


class LogIn(BaseModel):
    agent: str
    message: str
    to: str = "feed"


@router.post("/log")
def log(body: LogIn):
    log_event(body.agent, body.to, "note", body.message[:300])
    return {"ok": True}
