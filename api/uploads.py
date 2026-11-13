"""Browser-facing routes: uploads, approvals, deliveries, events and demo reset."""
import csv
import io
import uuid
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

import inventory_source as inv
from db import SERVER_TS, col, get_settings
from events import log_event, trigger_manager
from seed_loader import load_seed
from vision import save_photo, scan_shelf

router = APIRouter()


@router.post("/uploads/shelf")
async def upload_shelf(photo: UploadFile = File(...), direct: bool = False):
    """Save a shelf photo. direct=true scans immediately without agents (hour-4 fallback)."""
    scan_id = uuid.uuid4().hex[:12]
    url = save_photo(scan_id, await photo.read())
    col("scans").document(scan_id).set({"imageUrl": url, "status": "new", "createdAt": SERVER_TS})
    if direct:
        return scan_shelf(scan_id)
    await trigger_manager("shelf_photo", {"scan_id": scan_id, "summary": "New shelf photo to check"}, "owner")
    return {"scan_id": scan_id, "status": "sent_to_manager"}


@router.post("/uploads/reviews")
async def upload_reviews(file: UploadFile = File(...)):
    text = (await file.read()).decode("utf-8-sig")
    count = 0
    for row in csv.DictReader(io.StringIO(text)):
        rid = row.get("id") or uuid.uuid4().hex[:10]
        col("reviews").document(rid).set({"text": row.get("text", ""), "rating": int(row.get("rating") or 0),
                                          "date": row.get("date", ""), "theme": None, "createdAt": SERVER_TS})
        count += 1
    await trigger_manager("reviews_uploaded", {"count": count, "summary": f"{count} new reviews to read"}, "owner")
    return {"loaded": count}


@router.post("/orders/{draft_id}/approve")
def approve(draft_id: str):
    ref = col("supplierDrafts").document(draft_id)
    draft = ref.get().to_dict()
    if not draft:
        raise HTTPException(404, "Unknown draft")
    supplier = col("suppliers").document(draft["supplierId"]).get().to_dict() or {}
    lead = int(supplier.get("leadTimeDays", 1))
    if get_settings().get("snow_expected"):
        lead += 1
    eta = datetime.combine(date.today() + timedelta(days=lead), time(9, 0))
    for line in draft.get("lines", []):
        inv.set_restock_eta(line["sku"], eta)
    ref.update({"status": "approved", "approvedAt": SERVER_TS, "restockEta": eta.isoformat()})
    log_event("owner", "manager", "order_approved",
              f"Fatima approved the {draft.get('supplierName')} order. Expected {eta:%a %b %d}, 9 am.")
    return {"ok": True, "restockEta": eta.isoformat()}


class ReceivedIn(BaseModel):
    qty: int | None = None


@router.post("/inventory/{sku}/received")
async def received(sku: str, body: ReceivedIn | None = None):
    item = inv.get_item(sku)
    if not item:
        raise HTTPException(404, "Unknown sku")
    qty = (body.qty if body and body.qty else None) or item.get("par", 10)
    inv.record_delivery(sku, qty)
    log_event("owner", "feed", "delivery_received", f"{qty} {item['name']} received")
    await trigger_manager("restocked", {"sku": sku, "item": item["name"], "qty": qty,
                                        "summary": f"{item['name']} restocked: fulfill holds, notify, reply"}, "owner")
    return {"ok": True}


class EventIn(BaseModel):
    type: str
    payload: dict = {}


@router.post("/agents/event")
async def agents_event(body: EventIn):
    return await trigger_manager(body.type, body.payload, "owner")


@router.post("/demo/reset")
def demo_reset():
    counts = load_seed()
    log_event("system", "feed", "reset", "Demo reset to starting state")
    return {"ok": True, "loaded": counts}
