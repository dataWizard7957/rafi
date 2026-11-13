"""Single gateway for every stock read and write.

Today this is backed by Firestore. In production, a Square or Clover adapter
implements the same functions and nothing else in the app changes.
"""
from datetime import datetime, timedelta, timezone

from google.cloud.firestore_v1 import transactional

from db import SERVER_TS, Increment, col, db


def _status(item: dict) -> str:
    if item.get("qty", 0) > 0:
        return "in_stock"
    return "incoming" if item.get("restockEta") else "out"


def get_stock() -> list[dict]:
    items = []
    for d in col("inventory").stream():
        item = {"sku": d.id, **d.to_dict()}
        item["status"] = _status(item)
        items.append(item)
    return items


def get_item(sku: str) -> dict | None:
    snap = col("inventory").document(sku).get()
    if not snap.exists:
        return None
    item = {"sku": sku, **snap.to_dict()}
    item["status"] = _status(item)
    return item


def find_item(name: str) -> dict | None:
    """Match a spoken item name against names and aliases (English, Arabic, Spanish)."""
    needle = name.strip().lower()
    best = None
    for item in get_stock():
        names = [item.get("name", "")] + item.get("aliases", [])
        names = [n.lower() for n in names]
        if needle in names:
            return item
        if any(needle in n or n in needle for n in names) and best is None:
            best = item
    return best


def record_sale(sku: str, qty: int, source: str) -> None:
    ref = col("inventory").document(sku)

    @transactional
    def _txn(txn):
        snap = ref.get(transaction=txn)
        current = (snap.to_dict() or {}).get("qty", 0)
        txn.update(ref, {"qty": max(0, current - qty)})

    _txn(db.transaction())
    col("sales").add({"sku": sku, "qty": qty, "source": source, "createdAt": SERVER_TS})


def record_delivery(sku: str, qty: int) -> None:
    col("inventory").document(sku).update(
        {"qty": Increment(qty), "restockEta": None, "lostDemand": 0}
    )


def set_count(sku: str, qty: int, source: str) -> None:
    col("inventory").document(sku).update({"qty": max(0, qty), "lastCountSource": source})


def add_lost_demand(sku: str, qty: int) -> None:
    col("inventory").document(sku).update({"lostDemand": Increment(qty)})


def set_restock_eta(sku: str, eta: datetime) -> None:
    col("inventory").document(sku).update({"restockEta": eta.isoformat()})


def sales_last_hours(sku: str, hours: int = 24) -> int:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    total = 0
    for d in col("sales").where("sku", "==", sku).stream():
        row = d.to_dict()
        ts = row.get("createdAt")
        if ts is None or ts >= since:
            total += row.get("qty", 0)
    return total
