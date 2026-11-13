"""Front Desk agent: system instructions, tool declarations and tool implementations.

Tools run server-side inside the voice session. They must stay fast: the caller is waiting.
"""
from datetime import date, datetime

import inventory_source as inv
from db import SERVER_TS, col, get_settings
from events import fire_and_forget, log_event

SYSTEM_INSTRUCTIONS = """You are Rafi, the phone assistant for Cedar & Date Market, a small Middle Eastern grocery in Dearborn, Michigan.
Reply in the caller's language: Arabic, Spanish or English. Keep answers short and warm, like a friendly shop assistant.
Always call check_stock before confirming any item.
If an item is out of stock:
  1. First call find_substitutes and offer an in-stock alternative.
  2. If none fits and restock_eta is within 2 days, offer to hold it with add_hold.
  3. Otherwise give the honest date and offer a callback with leave_message_for_owner.
Always call log_missed_request for an out-of-stock item, even if the caller takes a substitute.
Read the order back before calling place_order. Ask for the caller's name and phone number for orders and holds.
Never promise dates or delivery you were not given. The shop is pickup only.
For hours, address, payment (including Bridge Card), halal and similar questions, call get_store_info."""

_S = "STRING"


def _obj(props: dict, required: list[str]) -> dict:
    return {"type": "OBJECT", "properties": props, "required": required}


DECLARATIONS = [
    {"name": "check_stock", "description": "Check if an item is in stock. Returns qty, status and restock_eta.",
     "parameters": _obj({"item_name": {"type": _S}}, ["item_name"])},
    {"name": "find_substitutes", "description": "In-stock items in the same category as an out-of-stock item.",
     "parameters": _obj({"item_name": {"type": _S}}, ["item_name"])},
    {"name": "place_order", "description": "Place a pickup order after reading it back to the caller.",
     "parameters": _obj({
         "items": {"type": "ARRAY", "items": _obj({"item": {"type": _S}, "qty": {"type": "INTEGER"}}, ["item", "qty"])},
         "customer_name": {"type": _S}, "phone": {"type": _S},
         "pickup_time": {"type": _S}, "language": {"type": _S}},
         ["items", "customer_name"])},
    {"name": "add_hold", "description": "Hold an out-of-stock item for a customer until it is back.",
     "parameters": _obj({"item": {"type": _S}, "qty": {"type": "INTEGER"}, "customer_name": {"type": _S},
                         "phone": {"type": _S}, "language": {"type": _S}},
                        ["item", "qty", "customer_name"])},
    {"name": "log_missed_request", "description": "Record that a caller asked for an out-of-stock item.",
     "parameters": _obj({"item": {"type": _S}, "qty": {"type": "INTEGER"},
                         "outcome": {"type": _S, "description": "substitute, hold, callback or lost"}},
                        ["item", "qty", "outcome"])},
    {"name": "get_store_info", "description": "Hours, address, payment, Bridge Card, halal and pickup questions.",
     "parameters": _obj({"topic": {"type": _S}}, ["topic"])},
    {"name": "leave_message_for_owner", "description": "Leave a message or callback request for the owner.",
     "parameters": _obj({"text": {"type": _S}}, ["text"])},
]


def _eta_words(eta: str | None) -> str | None:
    if not eta:
        return None
    days = (datetime.fromisoformat(eta).date() - date.today()).days
    if days <= 0:
        return "later today"
    if days == 1:
        return "tomorrow morning"
    return f"in {days} days ({datetime.fromisoformat(eta).strftime('%A')})"


def check_stock(item_name: str) -> dict:
    item = inv.find_item(item_name)
    if not item:
        return {"found": False, "message": f"We don't carry '{item_name}'."}
    return {"found": True, "item": item["name"], "qty": item.get("qty", 0), "status": item["status"],
            "restock_eta": _eta_words(item.get("restockEta"))}


def find_substitutes(item_name: str) -> dict:
    item = inv.find_item(item_name)
    if not item:
        return {"substitutes": []}
    subs = [{"item": i["name"], "qty": i["qty"], "price": i.get("price")}
            for i in inv.get_stock()
            if i.get("category") == item.get("category") and i["sku"] != item["sku"] and i.get("qty", 0) > 0]
    return {"for": item["name"], "substitutes": subs[:3]}


def place_order(items: list, customer_name: str, phone: str = "", pickup_time: str = "",
                language: str = "") -> dict:
    lines, below_par = [], []
    for line in items:
        item = inv.find_item(line["item"])
        if not item or item.get("qty", 0) < int(line["qty"]):
            return {"ok": False, "message": f"Not enough {line['item']} in stock. Check stock again."}
        lines.append({"sku": item["sku"], "name": item["name"], "qty": int(line["qty"])})
    for ln in lines:
        inv.record_sale(ln["sku"], ln["qty"], "phone")
        after = inv.get_item(ln["sku"])
        if after and after.get("qty", 0) < 0.3 * after.get("par", 0):
            below_par.append(after["name"])
    _, ref = col("orders").add({"items": lines, "customerName": customer_name, "phone": phone,
                                "language": language, "pickupTime": pickup_time,
                                "status": "new", "source": "phone", "createdAt": SERVER_TS})
    summary = ", ".join(f"{ln['qty']} {ln['name']}" for ln in lines)
    log_event("front_desk", "feed", "order_placed", f"Order for {customer_name}: {summary}")
    if below_par:
        fire_and_forget("order_placed", {"order_id": ref.id, "below_par": below_par,
                                         "summary": f"Order lowered {', '.join(below_par)} below par"},
                        source="front_desk")
    return {"ok": True, "order_id": ref.id, "summary": summary}


def add_hold(item: str, qty: int, customer_name: str, phone: str = "", language: str = "") -> dict:
    found = inv.find_item(item)
    if not found:
        return {"ok": False, "message": f"We don't carry '{item}'."}
    _, ref = col("holds").add({"sku": found["sku"], "item": found["name"], "qty": int(qty),
                               "customerName": customer_name, "phone": phone, "language": language,
                               "status": "waiting", "createdAt": SERVER_TS})
    fire_and_forget("demand", {"sku": found["sku"], "hold_id": ref.id,
                               "summary": f"{customer_name} is waiting on {qty} {found['name']}"},
                    source="front_desk")
    return {"ok": True, "hold_id": ref.id, "restock_eta": _eta_words(found.get("restockEta"))}


def log_missed_request(item: str, qty: int, outcome: str) -> dict:
    found = inv.find_item(item)
    if not found:
        return {"ok": False}
    inv.add_lost_demand(found["sku"], int(qty))
    log_event("front_desk", "manager", "missed_request",
              f"Missed request: {qty} {found['name']} (outcome: {outcome})")
    return {"ok": True}


def get_store_info(topic: str) -> dict:
    return {"topic": topic, "info": get_settings().get("storeInfo", {})}


def leave_message_for_owner(text: str) -> dict:
    col("tasks").add({"title": "Message from a caller", "detail": text, "createdBy": "front_desk",
                      "priority": "medium", "status": "open", "createdAt": SERVER_TS})
    log_event("front_desk", "owner", "message", text[:160])
    return {"ok": True}


TOOLS = {
    "check_stock": check_stock,
    "find_substitutes": find_substitutes,
    "place_order": place_order,
    "add_hold": add_hold,
    "log_missed_request": log_missed_request,
    "get_store_info": get_store_info,
    "leave_message_for_owner": leave_message_for_owner,
}


def run_tool(name: str, args: dict) -> dict:
    fn = TOOLS.get(name)
    if not fn:
        return {"error": f"Unknown tool {name}"}
    try:
        return fn(**args)
    except Exception as exc:  # tell the model, don't crash the call
        return {"error": str(exc)}
