"""Load demo seed data into Firestore. Used by /demo/reset and seed/load_seed.py."""
import csv
import json
import os

from config import SEED_DIR
from db import SERVER_TS, col

RESET_COLLECTIONS = ["inventory", "sales", "orders", "holds", "calls", "scans",
                     "supplierDrafts", "suppliers", "settings", "agentEvents"]


def _read(name: str):
    with open(os.path.join(SEED_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _clear(name: str) -> None:
    for d in col(name).stream():
        d.reference.delete()


def load_seed(keep_reviews: bool = True) -> dict:
    """Reset the demo shop. Reviews (and review tasks) are kept by default so the
    Review Agent's pre-demo analysis survives every reset."""
    for name in RESET_COLLECTIONS:
        _clear(name)
    for t in col("tasks").stream():
        if not keep_reviews or t.to_dict().get("createdBy") != "review_agent":
            t.reference.delete()

    inventory = _read("inventory.json")
    for item in inventory:
        sku = item.pop("sku")
        col("inventory").document(sku).set({"lostDemand": 0, "restockEta": None, **item})
    suppliers = _read("suppliers.json")
    for s in suppliers:
        col("suppliers").document(s.pop("id")).set(s)
    col("settings").document("main").set(_read("settings.json"))

    reviews_loaded = 0
    existing = list(col("reviews").limit(1).stream())
    if not keep_reviews or not existing:
        _clear("reviews")
        with open(os.path.join(SEED_DIR, "reviews.csv"), encoding="utf-8") as f:
            for row in csv.DictReader(f):
                col("reviews").document(row["id"]).set({
                    "text": row["text"], "rating": int(row["rating"]), "date": row["date"],
                    "theme": None, "createdAt": SERVER_TS})
                reviews_loaded += 1
    return {"inventory": len(inventory), "suppliers": len(suppliers), "reviews": reviews_loaded}
