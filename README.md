# Rafi: your shop's AI crew

Four AI agents for a small neighborhood shop. Front Desk answers the phone (Gemini Live), the Shelf Agent and Review Agent do the work, and Rafi Manager coordinates them (watsonx Orchestrate, default model `gpt-oss-120b`). Every supplier order waits for the owner's tap.

Built by **Assembly Line AI** for the Michigan DevFest AI Hackathon, November 13, 2026. Demo shop: **Cedar & Date Market** (fictional), Dearborn.

- **What to build:** [SPEC.md](SPEC.md)
- **Where we are:** [PROGRESS.md](PROGRESS.md)

## Repo

```
api/           FastAPI backend for Cloud Run (voice relay, uploads, agent tools, events)
orchestrate/   Orchestrate agents (YAML) and Python tools, plus import_all.sh
web/           Next.js dashboard (static export for Firebase Hosting)
seed/          Demo data, simulated POS sales feed, seed loader
Dockerfile     Builds the API image (run from the repo root)
```

## Quick start

### 1. Google Cloud

```bash
gcloud config set project rafi-hack
gcloud services enable aiplatform.googleapis.com run.googleapis.com firestore.googleapis.com storage.googleapis.com secretmanager.googleapis.com
gcloud firestore databases create --location=us-central1      # once
gsutil mb -l us-central1 gs://rafi-hack-scans                  # shelf photos
gcloud auth application-default login                          # local dev credentials
```

### 2. API (local)

```bash
cp .env.example .env            # fill in values
python -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt
set -a && source .env && set +a
python seed/load_seed.py        # load Cedar & Date Market
cd api && uvicorn main:app --reload --port 8080
```

Check: `curl localhost:8080/health`

### 3. Web (local)

```bash
cd web
cp .env.local.example .env.local   # Firebase web config + API URL
npm install
npm run dev                        # http://localhost:3000
```

### 4. Orchestrate (IBM, Tokyo)

```bash
pip install --upgrade ibm-watsonx-orchestrate
# connect the ADK to the Tokyo instance (see orchestrate/import_all.sh header)
orchestrate models list            # ensure the default model is gpt-oss-120b and keep llm: in agents/*.yaml aligned
RAFI_API=<cloud-run-url> RAFI_KEY=<same as API> ./orchestrate/import_all.sh
```

The tools need a public API URL, so deploy the API (step 5) before importing.

### 5. Deploy

```bash
# API -> Cloud Run (from the repo root)
gcloud run deploy rafi-api --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=rafi-hack,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_LIVE_MODEL=gemini-3.8-live,GEMINI_VISION_MODEL=gemini-3.8-flash,GEMINI_VISION_LOCATION=global,GCS_BUCKET=rafi-hack-scans,SHOP_ID=cedar-and-date,ORCHESTRATE_URL=<tokyo-instance-url>,ORCHESTRATE_MANAGER_AGENT=rafi_manager,ORCHESTRATE_RUN_PATH=/v1/orchestrate/runs,ALLOWED_ORIGINS=* \
  --set-secrets RAFI_KEY=rafi-key:latest,ORCHESTRATE_APIKEY=orchestrate-apikey:latest

# Web -> Firebase Hosting
cd web && npm run build && cd .. && firebase deploy --only hosting,firestore:rules
```

Cloud Run's service account needs Vertex AI User, Cloud Datastore User and Storage Object Admin.

## Demo

1. `POST /demo/reset` (or the Reset button on the Agent feed page).
2. Start the simulated POS feed: `python seed/pos_feed.py`.
3. Follow the 3-minute script in SPEC.md section 6 and PROGRESS.md.

## Honest labels

- Phone calls use the browser microphone, not a phone number.
- Customer notifications are simulated in the agent feed.
- The POS sales feed is simulated; `api/inventory_source.py` is where a Square or Clover adapter plugs in.
- Cedar & Date Market and all suppliers are fictional.

## Verify before the demo

Gemini Live and vision model IDs, the Orchestrate default model name, ADK YAML fields and CLI flags, and the Orchestrate run endpoint (`ORCHESTRATE_RUN_PATH`). These were written from docs and not tested against the live services.
