"""Build the OpenAPI spec for Rafi's Orchestrate tools from the FastAPI /tools routes.

Orchestrate calls these routes directly over HTTP (OpenAPI tools), so no Python tool
runtime is needed on the Orchestrate side. Tool names and descriptions match the
ones the agent YAMLs already use.

Usage (from the repo root):
  python orchestrate/build_openapi.py <public-api-url> [out-file]
The API key is sent by the Orchestrate connection (api_key kind) as the X-Rafi-Key header.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))

from fastapi import FastAPI  # noqa: E402

from tools import router  # noqa: E402

# (method, path) -> (tool name, description). Names must match the agent YAMLs.
TOOLS = {
    ("get", "/tools/stock"): ("get_stock", "List every item with qty, par, category, status, restock date, "
                              "missed requests (lostDemand) and units sold in the last 24 hours."),
    ("get", "/tools/orders"): ("get_recent_orders", "Customer orders from the last N hours."),
    ("post", "/tools/tasks"): ("create_task", "Add a task to the owner's Today list. priority is high, medium or low. "
                               "created_by is your agent name. evidence_count is how many reviews, requests or data "
                               "points support it."),
    ("post", "/tools/log"): ("log", "Write one short line to the shop's live agent feed explaining what you did or decided."),
    ("post", "/tools/scan_shelf"): ("scan_shelf", "Count items in a shelf photo. Updates stock to the photo counts and "
                                    "returns detections, drift (system vs photo) and low items, or status 'retake' if "
                                    "the photo is unreliable."),
    ("get", "/tools/settings"): ("get_settings", "Shop settings: snow_expected, ramadan, store info."),
    ("post", "/tools/mark_restocked"): ("mark_restocked", "Mark an item as back on the shelf after a delivery."),
    ("get", "/tools/reviews"): ("get_new_reviews", "Get the next unlabeled customer reviews (id, text, rating)."),
    ("post", "/tools/review_labels"): ("save_review_labels", "Save labels for reviews. labels is a list of objects with "
                                       "id, theme (food quality, wait time, staff, price, cleanliness, stock or "
                                       "availability, other), sentiment (positive, neutral, negative), item (product "
                                       "name or empty) and quote (max 10 words from the review). Returns errors to fix "
                                       "and resend."),
    ("post", "/tools/replies"): ("draft_reply", "Save a short, warm reply draft to a review for the owner to post."),
    ("get", "/tools/open_tasks"): ("get_open_tasks", "Open tasks on the owner's Today list."),
    ("get", "/tools/holds"): ("get_holds", "Customers waiting on out-of-stock items (holds with status 'waiting')."),
    ("post", "/tools/supplier_drafts"): ("draft_supplier_order", "Draft ONE order for ONE supplier for the owner to "
                                         "approve. lines is a list of {sku, qty}. reason must cite the evidence: missed "
                                         "requests, holds, reviews, sales pace, drift."),
    ("post", "/tools/holds/fulfill"): ("fulfill_holds", "Turn waiting holds for a restocked item into pickup orders. "
                                       "Returns the customers to notify."),
    ("post", "/tools/notify"): ("notify_customer", "Notify a waiting customer (simulated message shown in the feed). "
                                "Write the message in the customer's language."),
}


def build(server_url: str) -> dict:
    app = FastAPI(title="Rafi tools", version="1.0.0")
    app.include_router(router)
    spec = app.openapi()

    paths = {}
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            key = (method, path)
            if key not in TOOLS:
                continue
            name, desc = TOOLS[key]
            op["operationId"] = name
            op["summary"] = name
            op["description"] = desc
            # The key comes from the connection, not from the model.
            op["parameters"] = [p for p in op.get("parameters", []) if p.get("name", "").lower() != "x-rafi-key"]
            if not op["parameters"]:
                op.pop("parameters")
            op["responses"] = {"200": op["responses"].get("200", {"description": "OK"})}
            paths.setdefault(path, {})[method] = op

    missing = set(TOOLS) - {(m, p) for p, ops in paths.items() for m in ops}
    if missing:
        raise SystemExit(f"Routes not found for: {sorted(missing)}")

    spec["paths"] = paths
    spec["servers"] = [{"url": server_url.rstrip("/")}]
    spec.setdefault("components", {})["securitySchemes"] = {
        "RafiKey": {"type": "apiKey", "in": "header", "name": "X-Rafi-Key"}}
    spec["security"] = [{"RafiKey": []}]
    for schema in ("HTTPValidationError", "ValidationError"):
        spec["components"].get("schemas", {}).pop(schema, None)
    return spec


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python orchestrate/build_openapi.py <public-api-url> [out-file]")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "orchestrate", "tools", "rafi_openapi.json")
    spec = build(sys.argv[1])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
    print(f"Wrote {len(TOOLS)} tools to {out}")
