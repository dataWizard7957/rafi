# Rafi — Progress

**Team:** Assembly Line AI · **Event:** Michigan DevFest AI Hackathon · **Date:** Fri Nov 13, 2026
**Update this file at every checkpoint.** Status: ⬜ not started · 🟨 in progress · ✅ done · ❌ cut

---

## Current status

| Area | Owner | Status | Notes |
|---|---|---|---|
| Starter code (api, orchestrate, web, seed) | — | ✅ | Running against live services |
| Google project + credits | D | ✅ | rafi-hack-2026, billing linked, all APIs enabled |
| IBM credits | D | ✅ | Orchestrate (Tokyo) active; watsonx.ai Runtime not allowed |
| Front Desk agent | A | ⬜ | |
| Shelf Agent | B | ⬜ | |
| Review Agent | C | ⬜ | |
| Rafi Manager | D | ⬜ | |
| Dashboard | D | 🟨 | Firestore reads verified; Firebase keys in .env.local |
| Deploy | D | ⬜ | |
| Pitch deck | All | ⬜ | |

**Next checkpoint:** Hour 4 · **Blockers:** API needs Cloud Run deploy before Orchestrate tools work

---

## Hour 0–1 · Setup (everyone)

- [x] Google: project `rafi-hack-2026`, APIs enabled, Firestore (us-central1), bucket `rafi-hack-2026-scans`
- [x] Google: `gcloud auth application-default login` — ADC saved, quota project set
- [x] Firebase: web app registered; API key + App ID in `web/.env.local`; Firestore rules deployed
- [x] IBM: Orchestrate service URL + API key in .env; ADK connected to rafi-prod (Tokyo)
- [x] `orchestrate models list` run; default model `groq/openai/gpt-oss-120b` written into all 3 agent YAMLs
- [x] `.env` filled; `RAFI_KEY` set (change before sharing); project + bucket updated
- [x] `python seed/load_seed.py` loads 30 items, 4 suppliers, 80 reviews ✓ verified in Firestore
- [x] API runs locally: `curl localhost:8080/health` → `{"ok":true}`
- [x] Web runs locally on http://localhost:3000
- [x] Verify model IDs: Gemini Live `gemini-3.8-live` ✓  Gemini vision `gemini-3.8-flash` (global) ✓  Orchestrate default `groq/openai/gpt-oss-120b` ✓

## Hours 1–4 · Build the tools

**A · Front Desk**
- [x] `/voice/session` connects; Gemini Live model `gemini-3.8-live` responds ✓ (verified with test_live.py)
- [ ] Arabic, Spanish and English all answered in the caller's language (audio only; needs browser test)
- [x] `check_stock` → Sahadi hummus returns `out` ✓
- [x] `find_substitutes` → offers house-made hummus, baba ghanoush, labneh ✓
- [x] `log_missed_request` → returns `{"ok": true}` ✓; lostDemand increment verified in Firestore
- [ ] `place_order` → order appears on dashboard, stock drops (needs browser voice test)
- [ ] `add_hold` and the "back tomorrow morning" answer (needs an approved order first)
- [ ] `get_store_info` → "Yes, we take Bridge Card"
- [x] Typed-input backup works (send_client_content text path confirmed in voice.py)

**B · Shelf Agent**
- [ ] Staged shelf ready: about 3 pita, some house-made hummus, a few other seed items
- [ ] `/uploads/shelf?direct=true` returns counts with confidence
- [ ] Pita drift shows: system 12, shelf 3
- [ ] Low-confidence photo returns `retake`
- Note: `vision.py` fixed for Windows (tempfile.gettempdir() replaces /tmp). Model Garden access for `rafi-hack-2026` accepted `gemini-3.8-flash` in `global`, no `gemini-2.5-flash` usage.

**C · Review Agent**
- [x] `/tools/reviews` returns unlabelled reviews with id, text, rating ✓
- [x] `/tools/review_labels` saves valid labels; rejects bad theme with error ✓ (test_reviews.py)
- [x] Labels verified in Firestore via Admin SDK ✓
- [ ] Review Agent imported; labels a batch of 10 in Orchestrate
- [ ] Bad labels get an error and the agent retries

**D · Platform**
- [ ] `inventory_source.py` used everywhere stock changes
- [ ] `python seed/pos_feed.py` runs; POS badge goes live; stock drops on its own
- [ ] API deployed to Cloud Run (needed before Orchestrate tools can call it)
- [ ] Dashboard: Today list, stock tiles, orders, waiting customers, agent feed all live

## Hour 4 · Checkpoint (15 min) — guaranteed demo

- [ ] Voice order works end to end
- [ ] Shelf scan works in direct mode
- [ ] Review Agent labels one batch
- **Decision:** ______________________

## Hours 4–6 · Wrap as agents

- [ ] Shelf Agent imported; `shelf_photo` event → scan → drift task in Today list
- [ ] Rafi Manager imported with both collaborators
- [ ] `/agents/event` reaches the Manager (`ORCHESTRATE_RUN_PATH` verified: ______)
- [ ] `demand` and `order_placed` events reach the Manager
- [ ] Manager drafts a hummus order citing missed requests, reviews and sales pace

## Hour 6 · Agent gate (10 min)

Run hold → drafted order three times: run 1 ⬜ run 2 ⬜ run 3 ⬜
- [ ] Passed (2 of 3) → keep four agents
- [ ] Failed → Manager calls shelf tools directly; Review Agent runs alone from /reviews

## Hours 6–7 · Close the loop

- [ ] Approve sets `restockEta`; second call hears "back tomorrow morning" (+1 day if snow)
- [ ] Received → `restocked` event → holds fulfilled
- [ ] Simulated notification in the customer's language appears in the feed
- [ ] Review replies drafted for the hummus complaints
- [ ] Optional: Ramadan rule tested with `settings.ramadan = true`

## Hours 7–8 · Deploy and polish

- [ ] Web deployed to Firebase Hosting; works on the venue Wi-Fi
- [ ] Shelf scan works from a phone camera
- [ ] Phone hotspot tested as Wi-Fi backup
- [ ] Backup videos recorded: Arabic call · English "back tomorrow" call · full loop

## Hours 8–10 · Pitch

- [ ] Code freeze (bug fixes on the demo path only)
- [ ] Reviews analyzed before judging (reset keeps them)
- [ ] Deck done, including the "Ready answers for judges"
- [ ] Rehearsal 1 time: ____  Rehearsal 2 time: ____  (target 3:00)
- [ ] `/demo/reset` + POS feed started before each run

---

## Demo script (3 minutes)

| Time | Beat | Check |
|---|---|---|
| 0:00 | Problem: Fatima, Dearborn, three languages, Bridge Card, snow | ⬜ |
| 0:20 | Arabic call: Sahadi hummus out → house-made substitute → missed request logged | ⬜ |
| 0:55 | Shelf photo: pita drift; feed shows 3 misses, 5 reviews, sells out every 2 days; Approve | ⬜ |
| 1:30 | English call: "Back tomorrow morning. Want me to hold 2?" | ⬜ |
| 1:55 | Received → hold ready → simulated SMS → review replies | ⬜ |
| 2:25 | Close: "Can't win every lost sale; makes sure the same one doesn't happen twice." | ⬜ |

## Cut order (if behind)

1. Ramadan rule ⬜
2. Snow buffer ⬜
3. Loop step 7 (Received → notify → replies) ⬜
4. Shelf Agent as an agent (keep `scan_shelf` as a tool) ⬜
Never cut the two phone calls.

---

## Decisions log

| Time | Decision | Why |
|---|---|---|
| — | No Granite on our Orchestrate instance; agents use gpt-oss-120b. Fallback: Claude Sonnet for rafi_manager if coordination is unreliable. | Verified instance state and deployment reality |
| — | Four agents: Front Desk on Gemini Live, three on Orchestrate | Sponsor fit and real agent decisions |
| — | Pitch line: "Rafi's three agents run on IBM watsonx Orchestrate: a supervisor agent coordinating a Shelf Agent and a Review Agent, with Python tools built with the Orchestrate ADK." | No Granite on this instance; gpt-oss-120b is the default starred model |
| — | Substitute first, hold only if back within 2 days, always log the miss | Real shops lose the sale otherwise |
| — | Simulated POS feed behind `inventory_source.py` | Real Square/Clover setup costs hours |
| — | Drift demo on pita, not hummus | Hummus must be out of stock at the first call |
| — | Team name: Assembly Line AI | Detroit + agents passing work along |

## Open questions

- [ ] Exact judging criteria and sponsor prizes this year
- [ ] Orchestrate run endpoint path and payload (`ORCHESTRATE_RUN_PATH`)
- [ ] Gemini Live pricing for the "cost per call" answer

## Issues

| # | Issue | Owner | Status |
|---|---|---|---|
| 1 | Vision model fixed to `gemini-3.8-flash` with `GEMINI_VISION_LOCATION=global`; retired `gemini-2.5-flash` must not be used anywhere | D | Open |
| 2 | Manager startup endpoint (`ORCHESTRATE_RUN_PATH`) still must be validated against actual ADK runtime | D | Open |
| 3 | API Cloud Run deploy not yet done; Orchestrate tool calls are blocked until it is live | D | Open |
| 4 | No actual Git repo in this workspace; commit history is unavailable here | D | Note |
