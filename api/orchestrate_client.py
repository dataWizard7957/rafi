"""Starts Rafi Manager runs in watsonx Orchestrate.

The run endpoint path is configurable (ORCHESTRATE_RUN_PATH). Check it against
the current Orchestrate API reference before the demo. If Orchestrate is not
configured or the call fails, the event is still logged so the demo keeps going,
and the Manager can be triggered from the Orchestrate chat UI instead.
"""
import time

import httpx

from config import (
    ORCHESTRATE_APIKEY,
    ORCHESTRATE_MANAGER_AGENT,
    ORCHESTRATE_RUN_PATH,
    ORCHESTRATE_URL,
)

_token: dict = {"value": None, "expires": 0}


async def _iam_token() -> str:
    if _token["value"] and _token["expires"] > time.time() + 60:
        return _token["value"]
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": ORCHESTRATE_APIKEY,
            },
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        body = r.json()
    _token["value"] = body["access_token"]
    _token["expires"] = body.get("expiration", time.time() + 3000)
    return _token["value"]


async def run_manager(message: str) -> dict:
    if not (ORCHESTRATE_URL and ORCHESTRATE_APIKEY):
        return {"ok": False, "error": "Orchestrate not configured"}
    try:
        token = await _iam_token()
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{ORCHESTRATE_URL}{ORCHESTRATE_RUN_PATH}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "agent_id": ORCHESTRATE_MANAGER_AGENT,
                    "message": {"role": "user", "content": message},
                },
            )
            r.raise_for_status()
            return {"ok": True, "response": r.json()}
    except Exception as exc:  # keep the demo alive
        return {"ok": False, "error": str(exc)}
