"""Python tools for the Rafi Orchestrate agents (watsonx Orchestrate ADK).

Every tool calls the Rafi API on Cloud Run. Orchestrate never touches Firestore directly.
Credentials come from the Orchestrate connection `rafi_api` (key-value: RAFI_API, RAFI_KEY),
falling back to environment variables for local testing.

Import (see ../import_all.sh):
  orchestrate tools import -k python -f orchestrate/tools/rafi_tools.py \
      -r orchestrate/tools/requirements.txt --app-id rafi_api
Verify flags and the connections helper against the current ADK docs.
"""
import os

import requests
from ibm_watsonx_orchestrate.agent_builder.tools import tool

APP_ID = "rafi_api"


def _creds() -> tuple[str, str]:
    try:
        from ibm_watsonx_orchestrate.run import connections

        kv = connections.key_value(APP_ID)
        return kv["RAFI_API"].rstrip("/"), kv["RAFI_KEY"]
    except Exception:
        return os.environ["RAFI_API"].rstrip("/"), os.environ["RAFI_KEY"]


def _call(method: str, path: str, json: dict | None = None, params: dict | None = None) -> dict:
    base, key = _creds()
    r = requests.request(method, f"{base}{path}", json=json, params=params,
                         headers={"X-Rafi-Key": key}, timeout=60)
    if r.status_code >= 400:
        return {"error": f"{r.status_code}: {r.text[:300]}"}
    return r.json()


# ---------- Shared ----------

@tool(name="get_stock", description="List every item with qty, par, category, status, restock date, "
      "missed requests (lostDemand) and units sold in the last 24 hours.")
def get_stock() -> dict:
    return _call("GET", "/tools/stock")


@tool(name="get_recent_orders", description="Customer orders from the last N hours.")
def get_recent_orders(hours: int = 24) -> dict:
    return _call("GET", "/tools/orders", params={"hours": hours})


@tool(name="create_task", description="Add a task to the owner's Today list. priority is high, medium or low. "
      "created_by is your agent name. evidence_count is how many reviews, requests or data points support it.")
def create_task(title: str, detail: str, priority: str = "medium", created_by: str = "manager",
                evidence_count: int = 0) -> dict:
    return _call("POST", "/tools/tasks", json={"title": title, "detail": detail, "priority": priority,
                                                "created_by": created_by, "evidence_count": evidence_count})


@tool(name="log", description="Write one short line to the shop's live agent feed explaining what you did or decided.")
def log(agent: str, message: str, to: str = "feed") -> dict:
    return _call("POST", "/tools/log", json={"agent": agent, "message": message, "to": to})


# ---------- Shelf Agent ----------

@tool(name="scan_shelf", description="Count items in a shelf photo. Updates stock to the photo counts and returns "
      "detections, drift (system vs photo) and low items, or status 'retake' if the photo is unreliable.")
def scan_shelf(scan_id: str) -> dict:
    return _call("POST", "/tools/scan_shelf", json={"scan_id": scan_id})


@tool(name="get_settings", description="Shop settings: snow_expected, ramadan, store info.")
def get_settings() -> dict:
    return _call("GET", "/tools/settings")


@tool(name="mark_restocked", description="Mark an item as back on the shelf after a delivery.")
def mark_restocked(sku: str) -> dict:
    return _call("POST", "/tools/mark_restocked", json={"sku": sku})


# ---------- Review Agent ----------

@tool(name="get_new_reviews", description="Get the next unlabeled customer reviews (id, text, rating).")
def get_new_reviews(limit: int = 20) -> dict:
    return _call("GET", "/tools/reviews", params={"limit": limit})


@tool(name="save_review_labels", description="Save labels for reviews. labels is a list of objects with id, theme "
      "(food quality, wait time, staff, price, cleanliness, stock or availability, other), sentiment "
      "(positive, neutral, negative), item (product name or empty) and quote (max 10 words from the review). "
      "Returns errors to fix and resend.")
def save_review_labels(labels: list[dict]) -> dict:
    return _call("POST", "/tools/review_labels", json={"labels": labels})


@tool(name="draft_reply", description="Save a short, warm reply draft to a review for the owner to post.")
def draft_reply(review_id: str, text: str) -> dict:
    return _call("POST", "/tools/replies", json={"review_id": review_id, "text": text})


# ---------- Rafi Manager ----------

@tool(name="get_open_tasks", description="Open tasks on the owner's Today list.")
def get_open_tasks() -> dict:
    return _call("GET", "/tools/open_tasks")


@tool(name="get_holds", description="Customers waiting on out-of-stock items (holds with status 'waiting').")
def get_holds() -> dict:
    return _call("GET", "/tools/holds")


@tool(name="draft_supplier_order", description="Draft ONE order for ONE supplier for the owner to approve. "
      "lines is a list of {sku, qty}. reason must cite the evidence: missed requests, holds, reviews, sales pace, drift.")
def draft_supplier_order(supplier_id: str, lines: list[dict], reason: str) -> dict:
    return _call("POST", "/tools/supplier_drafts", json={"supplier_id": supplier_id, "lines": lines,
                                                          "reason": reason})


@tool(name="fulfill_holds", description="Turn waiting holds for a restocked item into pickup orders. "
      "Returns the customers to notify.")
def fulfill_holds(sku: str) -> dict:
    return _call("POST", "/tools/holds/fulfill", json={"sku": sku})


@tool(name="notify_customer", description="Notify a waiting customer (simulated message shown in the feed). "
      "Write the message in the customer's language.")
def notify_customer(hold_id: str, message: str) -> dict:
    return _call("POST", "/tools/notify", json={"hold_id": hold_id, "message": message})
