"""Firestore access. Every collection lives under shops/{SHOP_ID}/."""
import firebase_admin
from firebase_admin import firestore

from config import SHOP_ID

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()
SERVER_TS = firestore.SERVER_TIMESTAMP
Increment = firestore.Increment


def shop_ref():
    return db.collection("shops").document(SHOP_ID)


def col(name: str):
    return shop_ref().collection(name)


def docs(name: str, limit: int | None = None) -> list[dict]:
    q = col(name)
    if limit:
        q = q.limit(limit)
    return [{"id": d.id, **d.to_dict()} for d in q.stream()]


def get_settings() -> dict:
    snap = col("settings").document("main").get()
    return snap.to_dict() or {}
