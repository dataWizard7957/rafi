"""Shelf scanning with Gemini vision (Vertex AI) and drift detection."""
import os
import tempfile

from google import genai
from google.genai import types
from pydantic import BaseModel

import inventory_source as inv
from config import GCS_BUCKET, PROJECT, VISION_LOCATION, VISION_MODEL, gemini_client
from db import SERVER_TS, col

DRIFT_UNITS = 3
DRIFT_RATIO = 0.30
RETAKE_CONFIDENCE = 0.6

_client = None


def client() -> genai.Client:
    global _client
    if _client is None:
        # GEMINI_VISION_LOCATION (default "global"): gemini-3.8-flash is served from global
        _client = gemini_client(VISION_LOCATION)
    return _client


class Detection(BaseModel):
    item: str
    count: int
    confidence: float


def _image_part(image_url: str) -> types.Part:
    if image_url.startswith("gs://"):
        return types.Part.from_uri(file_uri=image_url, mime_type="image/jpeg")
    path = image_url.removeprefix("local:")
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/jpeg")


def save_photo(scan_id: str, data: bytes) -> str:
    """Store a shelf photo in Cloud Storage, or on local disk when no bucket is set."""
    if GCS_BUCKET:
        from google.cloud import storage

        blob = storage.Client(project=PROJECT).bucket(GCS_BUCKET).blob(f"scans/{scan_id}.jpg")
        blob.upload_from_string(data, content_type="image/jpeg")
        return f"gs://{GCS_BUCKET}/scans/{scan_id}.jpg"
    scan_dir = os.path.join(tempfile.gettempdir(), "rafi-scans")
    os.makedirs(scan_dir, exist_ok=True)
    path = os.path.join(scan_dir, f"{scan_id}.jpg")
    with open(path, "wb") as f:
        f.write(data)
    return f"local:{path}"


def scan_shelf(scan_id: str) -> dict:
    """Count items in a scan, compare with system stock, record drift, trust the photo."""
    ref = col("scans").document(scan_id)
    scan = ref.get().to_dict() or {}
    stock = inv.get_stock()
    names = [i["name"] for i in stock]

    prompt = (
        "Count the visible units of each product on this shelf. "
        f"Only use names from this list: {names}. "
        "Give a confidence from 0 to 1 per item. Return JSON only, using the response schema."
    )
    resp = client().models.generate_content(
        model=VISION_MODEL,
        contents=[_image_part(scan["imageUrl"]), prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[Detection],
            temperature=0,
        ),
    )
    detections = [d.model_dump() for d in (resp.parsed or [])]

    avg_conf = sum(d["confidence"] for d in detections) / max(len(detections), 1)
    if not detections or avg_conf < RETAKE_CONFIDENCE:
        ref.update({"detections": detections, "status": "retake"})
        return {"scan_id": scan_id, "status": "retake", "avg_confidence": round(avg_conf, 2),
                "message": "Counts look unreliable. Ask the owner for a clearer photo."}

    by_name = {i["name"].lower(): i for i in stock}
    drift, low = [], []
    for d in detections:
        item = by_name.get(d["item"].lower())
        if not item:
            continue
        system_qty, photo_qty = item.get("qty", 0), d["count"]
        diff = abs(system_qty - photo_qty)
        if diff > DRIFT_UNITS or (system_qty and diff / system_qty > DRIFT_RATIO):
            drift.append({"item": item["name"], "sku": item["sku"],
                          "systemQty": system_qty, "photoQty": photo_qty})
        inv.set_count(item["sku"], photo_qty, "shelf_photo")  # trust the photo
        if photo_qty < 0.3 * item.get("par", 0):
            low.append({"item": item["name"], "sku": item["sku"],
                        "photoQty": photo_qty, "par": item.get("par")})

    ref.update({"detections": detections, "drift": drift, "status": "done",
                "scannedAt": SERVER_TS})
    return {"scan_id": scan_id, "status": "done", "detections": detections,
            "drift": drift, "low": low}
