"""Try candidate vision model IDs in two locations and report which work."""
from google import genai

PROJECT = "rafi-hack-2026"
MODELS = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite",
          "gemini-3.1-flash-lite", "gemini-2.5-flash"]
LOCATIONS = ["us-central1", "global"]

for loc in LOCATIONS:
    client = genai.Client(vertexai=True, project=PROJECT, location=loc)
    for m in MODELS:
        try:
            r = client.models.generate_content(model=m, contents="Reply with the word OK.")
            print(f"WORKS   {loc:12} {m:24} -> {r.text.strip()[:20]}")
        except Exception as e:
            print(f"FAILS   {loc:12} {m:24} -> {str(e)[:90]}")
