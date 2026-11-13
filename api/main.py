"""Rafi API: FastAPI app for Cloud Run.

Run locally:  uvicorn main:app --reload --port 8080   (from the api/ folder)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from tools import router as tools_router
from uploads import router as uploads_router
from voice import router as voice_router

app = FastAPI(title="Rafi API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)
app.include_router(uploads_router)
app.include_router(tools_router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "rafi-api"}
