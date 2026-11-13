"""Test the Gemini Live session with a text message.

Sends "Do you have Sahadi hummus?" then "What can I get instead?" and prints
transcripts and all tool calls across two turns.
Uses the same config as api/voice.py.

Run from the rafi/ directory:
    python scripts/test_live.py
"""
import asyncio
import os
import sys

# Allow imports from api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from google import genai
from google.genai import types

from config import LIVE_MODEL, LOCATION, PROJECT
from front_desk import DECLARATIONS, SYSTEM_INSTRUCTIONS, run_tool


def _config() -> types.LiveConnectConfig:
    return types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(parts=[types.Part(text=SYSTEM_INSTRUCTIONS)]),
        tools=[types.Tool(function_declarations=[types.FunctionDeclaration(**d) for d in DECLARATIONS])],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )


async def recv_turn(session, label: str) -> int:
    """Drain one complete model turn. Returns total audio bytes received."""
    print(f"\n--- {label} ---")
    total_audio = 0
    async for resp in session.receive():
        if resp.data:
            total_audio += len(resp.data)

        sc = resp.server_content
        if sc:
            for who, tr in (("caller", sc.input_transcription), ("rafi", sc.output_transcription)):
                if tr and tr.text:
                    print(f"[transcript/{who}] {tr.text}")
            if sc.interrupted:
                print("[interrupted]")
            if sc.turn_complete:
                print(f"[turn_complete] audio={total_audio}b")
                break

        if resp.tool_call:
            responses = []
            for fc in resp.tool_call.function_calls:
                args = dict(fc.args or {})
                print(f"[tool_call] {fc.name}({args})")
                result = run_tool(fc.name, args)
                print(f"[tool_result] {result}")
                responses.append(
                    types.FunctionResponse(id=fc.id, name=fc.name, response={"result": result})
                )
            await session.send_tool_response(function_responses=responses)

    return total_audio


async def run():
    print(f"Connecting to Gemini Live — model={LIVE_MODEL} project={PROJECT} location={LOCATION}")
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

    async with client.aio.live.connect(model=LIVE_MODEL, config=_config()) as session:

        # Turn 1: ask about hummus
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text="Do you have Sahadi hummus?")]),
            turn_complete=True,
        )
        await recv_turn(session, "Turn 1 — 'Do you have Sahadi hummus?'")

        # Turn 2: ask for a substitute
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text="What can I get instead?")]),
            turn_complete=True,
        )
        await recv_turn(session, "Turn 2 — 'What can I get instead?'")

        # Turn 3: I'll take it, log the miss
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text="I'll take 2 of that please, my name is Ahmed, phone 313-555-0100")]),
            turn_complete=True,
        )
        await recv_turn(session, "Turn 3 — place order")

    print("\nSession closed.")


if __name__ == "__main__":
    asyncio.run(run())
