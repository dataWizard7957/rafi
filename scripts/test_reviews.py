"""Test the reviews API tools end-to-end.

1. GET /tools/reviews?limit=5 — prints unlabelled reviews
2. POST /tools/review_labels with valid labels for all 5, plus one bad label (theme "smell")
3. Checks the errors returned for the bad label
4. Verifies the saved labels in Firestore via the admin SDK

Run from the rafi/ directory:
    python scripts/test_reviews.py

RAFI_KEY is read from the RAFI_KEY environment variable (set via .env).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import requests
import firebase_admin
from firebase_admin import firestore

from config import RAFI_KEY, SHOP_ID

API = "http://localhost:8080"
HEADERS = {"X-Rafi-Key": RAFI_KEY}

VALID_THEMES = {
    "food quality", "wait time", "staff", "price",
    "cleanliness", "stock or availability", "other"
}
VALID_SENTIMENTS = {"positive", "neutral", "negative"}


def _db():
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    return firestore.client()


def step1_get_reviews():
    print("=" * 60)
    print("Step 1: GET /tools/reviews?limit=5")
    print("=" * 60)
    r = requests.get(f"{API}/tools/reviews", params={"limit": 5}, headers=HEADERS, timeout=10)
    if not r.ok:
        print(f"ERROR {r.status_code}: {r.text}")
        sys.exit(1)
    data = r.json()
    reviews = data.get("reviews", [])
    remaining = data.get("remaining", 0)
    print(f"Got {len(reviews)} reviews ({remaining} more remaining)")
    for rev in reviews:
        rating = rev.get("rating", "?")
        text = (rev.get("text") or "")[:80]
        print(f"  [{rev['id']}] *{rating}  {text!r}")
    return reviews


def step2_post_labels(reviews: list[dict]):
    print("\n" + "=" * 60)
    print("Step 2: POST /tools/review_labels (valid + 1 bad)")
    print("=" * 60)

    labels = []
    for rev in reviews:
        text = (rev.get("text") or "").lower()
        # Assign a sensible theme based on text keywords
        if any(w in text for w in ("hummus", "pita", "bread", "out of stock", "stock", "empty")):
            theme = "stock or availability"
        elif any(w in text for w in ("taste", "fresh", "quality", "delicious", "flavor")):
            theme = "food quality"
        elif any(w in text for w in ("price", "expensive", "cheap", "cost")):
            theme = "price"
        elif any(w in text for w in ("wait", "slow", "fast", "quick")):
            theme = "wait time"
        elif any(w in text for w in ("staff", "rude", "friendly", "help", "service")):
            theme = "staff"
        elif any(w in text for w in ("clean", "dirty", "mess")):
            theme = "cleanliness"
        else:
            theme = "other"

        sentiment = "positive" if rev.get("rating", 3) >= 4 else (
            "negative" if rev.get("rating", 3) <= 2 else "neutral"
        )
        words = (rev.get("text") or "").split()
        quote = " ".join(words[:8]) if len(words) >= 3 else None
        labels.append({
            "id": rev["id"],
            "theme": theme,
            "sentiment": sentiment,
            "item": None,
            "quote": quote,
        })

    # Add one deliberately bad label
    bad_label = {
        "id": "fake-id-bad-label",
        "theme": "smell",           # invalid — not in the allowed set
        "sentiment": "negative",
        "item": None,
        "quote": None,
    }
    labels.append(bad_label)

    print(f"Sending {len(labels)} labels ({len(reviews)} valid + 1 bad):")
    for lb in labels:
        marker = " <-- BAD (theme='smell')" if lb["theme"] == "smell" else ""
        print(f"  [{lb['id'][:20]:20s}] theme={lb['theme']:25s} sentiment={lb['sentiment']}{marker}")

    r = requests.post(
        f"{API}/tools/review_labels",
        json={"labels": labels},
        headers=HEADERS,
        timeout=10,
    )
    if not r.ok:
        print(f"ERROR {r.status_code}: {r.text}")
        sys.exit(1)
    result = r.json()
    print(f"\nResponse: saved={result['saved']}  errors={len(result.get('errors', []))}")
    for err in result.get("errors", []):
        print(f"  ERROR: {err}")

    assert result["saved"] == len(reviews), f"Expected {len(reviews)} saved, got {result['saved']}"
    assert len(result.get("errors", [])) == 1, f"Expected 1 error for bad label, got {result.get('errors')}"
    print("\nOK: valid labels saved, bad theme rejected with error")
    return [lb["id"] for lb in labels if lb["theme"] != "smell"]


def step3_verify_firestore(saved_ids: list[str]):
    print("\n" + "=" * 60)
    print("Step 3: Verify labels saved in Firestore")
    print("=" * 60)
    db = _db()
    col = db.collection("shops").document(SHOP_ID).collection("reviews")
    ok = 0
    for rid in saved_ids:
        doc = col.document(rid).get().to_dict() or {}
        theme = doc.get("theme")
        sentiment = doc.get("sentiment")
        if theme in VALID_THEMES and sentiment in VALID_SENTIMENTS:
            print(f"  [{rid[:20]:20s}] OK theme={theme}  sentiment={sentiment}")
            ok += 1
        else:
            print(f"  [{rid[:20]:20s}] FAIL theme={theme!r}  sentiment={sentiment!r}")

    assert ok == len(saved_ids), f"Only {ok}/{len(saved_ids)} docs verified in Firestore"
    print(f"\nOK: All {ok} labels confirmed in Firestore")


if __name__ == "__main__":
    reviews = step1_get_reviews()
    if not reviews:
        print("\nNo unlabelled reviews found. Run `python seed/load_seed.py --fresh` to reload reviews.")
        sys.exit(0)
    saved_ids = step2_post_labels(reviews)
    step3_verify_firestore(saved_ids)
    print("\nALL REVIEW TESTS PASSED")
