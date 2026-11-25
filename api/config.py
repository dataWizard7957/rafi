"""Runtime configuration. All values come from environment variables (see .env.example)."""
import os

# Google
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "rafi-hack")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
# Verify both model IDs in Vertex AI Model Garden before the demo.
LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.8-live")
VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-3.8-flash")
VISION_LOCATION = os.getenv("GEMINI_VISION_LOCATION", "global")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")  # empty = keep shelf photos on local disk (dev only)

# IBM watsonx Orchestrate (Tokyo). No watsonx.ai Runtime is used.
ORCHESTRATE_URL = os.getenv("ORCHESTRATE_URL", "").rstrip("/")
ORCHESTRATE_APIKEY = os.getenv("ORCHESTRATE_APIKEY", "")
ORCHESTRATE_MANAGER_AGENT = os.getenv("ORCHESTRATE_MANAGER_AGENT", "rafi_manager")
# Verify the run endpoint path against the current Orchestrate API docs.
ORCHESTRATE_RUN_PATH = os.getenv("ORCHESTRATE_RUN_PATH", "/v1/orchestrate/runs")

# App
SHOP_ID = os.getenv("SHOP_ID", "cedar-and-date")
RAFI_KEY = os.getenv("RAFI_KEY", "dev-key-change-me")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
SEED_DIR = os.getenv("SEED_DIR", os.path.join(os.path.dirname(__file__), "..", "seed"))

# Gemini: a Google AI Studio API key (GEMINI_API_KEY) takes priority; otherwise Vertex AI.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def gemini_client(location: str):
    from google import genai

    if GEMINI_API_KEY:
        # The SDK's default API version returns 404 for Live with an API key; v1beta works.
        return genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta"})
    return genai.Client(vertexai=True, project=PROJECT, location=location)
