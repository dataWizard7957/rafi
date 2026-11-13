"""Load the Cedar & Date Market demo data into Firestore.

Run from the repo root:
  python seed/load_seed.py               # keeps already-analyzed reviews
  python seed/load_seed.py --fresh       # also reloads reviews (they need re-analysis)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
os.environ.setdefault("SEED_DIR", os.path.dirname(os.path.abspath(__file__)))

from seed_loader import load_seed  # noqa: E402

if __name__ == "__main__":
    print(load_seed(keep_reviews="--fresh" not in sys.argv))
