"""Agent feed logging and Manager triggers."""
import asyncio
import json

from db import SERVER_TS, col
from orchestrate_client import run_manager


def _short_error(err) -> str:
    """Feed-safe error summary: no URLs or instance IDs."""
    text = str(err or "")
    if "Orchestrate not configured" in text:
        return "Orchestrate not configured"
    for code in ("400", "401", "403", "404", "429", "500", "502", "503"):
        if f"'{code} " in text or f" {code} " in text:
            return f"Orchestrate error {code}"
    return "Orchestrate unavailable"


def log_event(frm: str, to: str, type_: str, message: str) -> None:
    col("agentEvents").add(
        {"from": frm, "to": to, "type": type_, "message": message, "createdAt": SERVER_TS}
    )


async def trigger_manager(event_type: str, payload: dict, source: str = "api") -> dict:
    """Send an event to Rafi Manager and record it in the agent feed."""
    summary = payload.get("summary") or json.dumps(payload)[:160]
    log_event(source, "manager", event_type, summary)
    message = (
        f"EVENT: {event_type}\n"
        f"PAYLOAD: {json.dumps(payload, default=str)}\n"
        "Handle this event following your instructions, then update Today's list."
    )
    result = await run_manager(message)
    if not result.get("ok"):
        # Full error (with the Orchestrate instance URL) goes to the server log only, never the public feed.
        print(f"[orchestrate] Manager not reached: {result.get('error')}", flush=True)
        log_event("api", "feed", "manager_unreachable", f"Manager not reached ({_short_error(result.get('error'))})")
    return result


def fire_and_forget(event_type: str, payload: dict, source: str = "api") -> None:
    """Trigger the Manager without blocking the caller (used from voice tools)."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(trigger_manager(event_type, payload, source))
    except RuntimeError:
        asyncio.run(trigger_manager(event_type, payload, source))
