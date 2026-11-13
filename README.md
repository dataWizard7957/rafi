# Rafi: your shop's AI crew

Rafi gives a small neighborhood shop four AI agents that answer the phone, watch the shelves, read reviews and draft supplier orders. Every order waits for the owner's tap.

Built by **Assembly Line AI** for the Michigan DevFest AI Hackathon (November 13, 2026). The demo shop, **Cedar & Date Market** in Dearborn, and all of its suppliers are fictional.

## The crew


| Agent | Runs on | Job |
|---|---|---|
| **Front Desk** | Gemini Live (`gemini-3.8-live`) | Answers calls, checks stock, offers substitutes, takes orders and holds, logs missed requests |
| **Shelf Agent** | watsonx Orchestrate | Counts items in shelf photos (Gemini vision, `gemini-3.8-flash`) and flags stock drift |
| **Review Agent** | watsonx Orchestrate | Labels customer reviews by theme and drafts replies |
| **Rafi Manager** | watsonx Orchestrate | Coordinates the other agents, drafts supplier orders, fulfills holds when stock arrives |

The Orchestrate agents use the instance's default model, `gpt-oss-120b`. They call the Rafi API through 15 Python tools built with the Orchestrate ADK.

### The loop

1. A caller asks for Sahadi hummus. It's out, so Front Desk offers the house-made one and logs the missed request.
2. Rafi Manager sees the pattern (missed requests, reviews, sales pace) and drafts a supplier order.
3. The owner approves it. The next caller hears "back tomorrow morning" and gets a hold.
4. The owner taps **Received**. The hold becomes a pickup order, the customer is notified and review replies are drafted.

## Architecture

```
Browser mic ──► api/ (FastAPI, Cloud Run) ◄──► Gemini Live + Gemini vision (Vertex AI)
                    │   ▲
     events ────────┘   └──── /tools/* (X-Rafi-Key) ◄── Orchestrate agents (Tokyo)
                    │
                Firestore ◄──── web/ (Next.js dashboard, Firebase Hosting)
                Cloud Storage (shelf photos)
```

## Repo

```
api/           FastAPI backend: voice relay, uploads, agent tools, events
orchestrate/   Agent YAMLs, Python tools, import scripts (import_all.ps1 / .sh)
web/           Next.js dashboard (static export for Firebase Hosting)
seed/          Demo data, simulated POS sales feed, seed loader
scripts/       Model and endpoint test scripts
Dockerfile     API image (build from the repo root)
```

## Setup

Commands are for Windows PowerShell; bash equivalents work the same way.

### 1. Google Cloud

```powershell
$P = "rafi-hack-2026"
gcloud config set project $P
gcloud services enable aiplatform.googleapis.com run.googleapis.com firestore.googleapis.com `
  storage.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud firestore databases create --location=us-central1     # once
gcloud storage buckets create gs://rafi-hack-2026-scans --location=us-central1
gcloud auth application-default login                        # local credentials
```

### 2. API (local)

```powershell
Copy-Item .env.example .env          # fill in values; never commit .env
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r api\requirements.txt
python seed\load_seed.py             # loads Cedar & Date Market
cd api; uvicorn main:app --reload --port 8080
```

Check it with `curl http://localhost:8080/health`.

| Variable | Value |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | `rafi-hack-2026` |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` |
| `GEMINI_LIVE_MODEL` | `gemini-3.8-live` |
| `GEMINI_VISION_MODEL` | `gemini-3.8-flash` |
| `GEMINI_VISION_LOCATION` | `global` (the vision model is served only from global) |
| `GCS_BUCKET` | `rafi-hack-2026-scans` (empty for local dev: photos go to the temp folder) |
| `ORCHESTRATE_URL`, `ORCHESTRATE_APIKEY` | Your Orchestrate instance URL and IBM API key |
| `ORCHESTRATE_MANAGER_AGENT` | `rafi_manager` |
| `ORCHESTRATE_RUN_PATH` | Orchestrate run endpoint (not yet verified, see below) |
| `SHOP_ID` | `cedar-and-date` |
| `RAFI_KEY` | A long random string shared with the Orchestrate tools |
| `ALLOWED_ORIGINS` | The dashboard URL (`*` only for local dev) |

### 3. Web (local)

```powershell
cd web
Copy-Item .env.local.example .env.local   # Firebase web config + NEXT_PUBLIC_API_URL
npm install
npm run dev                               # http://localhost:3000
```

### 4. Deploy the API to Cloud Run

The default compute service account needs `roles/aiplatform.user`, `roles/datastore.user`, `roles/storage.objectAdmin` and `roles/secretmanager.secretAccessor`. Store `RAFI_KEY` and `ORCHESTRATE_APIKEY` in Secret Manager as `rafi-key` and `orchestrate-apikey`, then:

```powershell
gcloud run deploy rafi-api --source . --region us-central1 --allow-unauthenticated `
  --set-env-vars "GOOGLE_CLOUD_PROJECT=rafi-hack-2026,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_LIVE_MODEL=gemini-3.8-live,GEMINI_VISION_MODEL=gemini-3.8-flash,GEMINI_VISION_LOCATION=global,GCS_BUCKET=rafi-hack-2026-scans,SHOP_ID=cedar-and-date,ORCHESTRATE_URL=<instance-url>,ORCHESTRATE_MANAGER_AGENT=rafi_manager,ORCHESTRATE_RUN_PATH=<run-path>,ALLOWED_ORIGINS=<dashboard-url>" `
  --set-secrets "RAFI_KEY=rafi-key:latest,ORCHESTRATE_APIKEY=orchestrate-apikey:latest"
```

Then set `NEXT_PUBLIC_API_URL` in `web\.env.local` to the Cloud Run URL.

### 5. Import the agents into Orchestrate

Requires ADK `ibm-watsonx-orchestrate` 2.20.0 connected to your instance (steps are in the header of `orchestrate\import_all.ps1`). The tools need the public API URL, so deploy first.

```powershell
$env:RAFI_API = "<cloud-run-url>"
$env:RAFI_KEY = "<same value as .env>"
.\orchestrate\import_all.ps1
orchestrate agents list     # expect 3 agents
orchestrate tools list      # expect 15 tools
```

### 6. Deploy the dashboard

```powershell
cd web; npm run build; cd ..
firebase deploy --only hosting,firestore:rules
```

## Running the demo

1. `POST /demo/reset`, or press Reset on the Agent feed page.
2. Start the simulated POS feed: `python seed\pos_feed.py`.
3. Run through the loop above. Progress and the demo script are in [PROGRESS.md](PROGRESS.md).

## Honest labels

- Calls use the browser microphone, not a phone number.
- Customer notifications are simulated and appear in the agent feed.
- The POS sales feed is simulated. `api/inventory_source.py` is where a Square or Clover adapter would plug in.
- No watsonx.ai Runtime is used.

## Status

- **Verified:** `gemini-3.8-live` (us-central1), `gemini-3.8-flash` (global), the Orchestrate default model `gpt-oss-120b`, ADK 2.20.0 CLI flags.
- **Not yet verified:** the Orchestrate run endpoint and payload (`ORCHESTRATE_RUN_PATH`). If the API can't reach Rafi Manager it logs "Manager not reached" in the feed, and the Manager can be triggered from the Orchestrate chat instead.
