"""Simulated POS sales feed for the demo.

Writes one random sale every 5-10 seconds through api/inventory_source.py, the same
gateway a real Square or Clover adapter would use. The dashboard labels it as simulated.

Run from the repo root:  python seed/pos_feed.py
Stop with Ctrl+C.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import inventory_source as inv  # noqa: E402
from db import SERVER_TS, col  # noqa: E402

# Fast movers sell more often. Sahadi hummus is out, so it is skipped automatically.
# Pita stays low-weight so its system count stays near 12 for the drift demo.
WEIGHTS = {"pita": 2, "milk": 5, "hummus-house": 4, "tomatoes": 4, "cucumbers": 3,
           "yogurt": 3, "chicken": 2, "dates": 2, "flatbread": 2}
PROTECTED_MIN = {"hummus-house": 3}  # keep the demo substitute in stock


def pick(items):
    pool = [i for i in items if i.get("qty", 0) > PROTECTED_MIN.get(i["sku"], 0)]
    weights = [WEIGHTS.get(i["sku"], 1) for i in pool]
    return random.choices(pool, weights=weights, k=1)[0] if pool else None


def main():
    col("settings").document("main").set({"posFeedRunning": True}, merge=True)
    print("POS feed (simulated) running. Ctrl+C to stop.")
    try:
        while True:
            item = pick(inv.get_stock())
            if item:
                qty = 1 if random.random() < 0.8 else 2
                inv.record_sale(item["sku"], qty, "pos_sim")
                col("settings").document("main").set({"posFeedLastSale": SERVER_TS}, merge=True)
                print(f"sale: {qty} x {item['name']}")
            time.sleep(random.uniform(5, 10))
    except KeyboardInterrupt:
        col("settings").document("main").set({"posFeedRunning": False}, merge=True)
        print("\nPOS feed stopped.")


if __name__ == "__main__":
    main()
