"""WebSocket relay between the browser and the Gemini Live API (Front Desk agent).

Browser -> server: binary frames of 16 kHz 16-bit mono PCM; text frames of JSON
  {"type": "text", "text": "..."} for typed input, {"type": "end"} to hang up.
Server -> browser: binary frames of 24 kHz 16-bit mono PCM (Rafi's voice); text frames of JSON
  {"type": "transcript", "who": "caller"|"rafi", "text": "..."}
  {"type": "tool", "name": "...", "args": {...}, "result": {...}}
  {"type": "interrupted"} when the caller talks over Rafi (stop playback).
Verify method names against the current google-genai Live API docs if the SDK version changes.
"""
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from config import LIVE_MODEL, LOCATION, PROJECT
from db import SERVER_TS, col
from front_desk import DECLARATIONS, SYSTEM_INSTRUCTIONS, run_tool

router = APIRouter()


def _config() -> types.LiveConnectConfig:
    return types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(parts=[types.Part(text=SYSTEM_INSTRUCTIONS)]),
        tools=[types.Tool(function_declarations=[types.FunctionDeclaration(**d) for d in DECLARATIONS])],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )


@router.websocket("/voice/session")
async def voice_session(ws: WebSocket):
    await ws.accept()
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    transcript: list[dict] = []
    done = asyncio.Event()

    async with client.aio.live.connect(model=LIVE_MODEL, config=_config()) as session:

        async def from_browser():
            try:
                while not done.is_set():
                    msg = await ws.receive()
                    if msg.get("type") == "websocket.disconnect":
                        break
                    if msg.get("bytes"):
                        await session.send_realtime_input(
                            audio=types.Blob(data=msg["bytes"], mime_type="audio/pcm;rate=16000"))
                    elif msg.get("text"):
                        data = json.loads(msg["text"])
                        if data.get("type") == "end":
                            break
                        if data.get("type") == "text":
                            await session.send_client_content(
                                turns=types.Content(role="user", parts=[types.Part(text=data["text"])]),
                                turn_complete=True)
            except WebSocketDisconnect:
                pass
            finally:
                done.set()

        async def to_browser():
            try:
                while not done.is_set():
                    async for resp in session.receive():
                        if resp.data:
                            await ws.send_bytes(resp.data)
                        sc = resp.server_content
                        if sc:
                            for who, tr in (("caller", sc.input_transcription), ("rafi", sc.output_transcription)):
                                if tr and tr.text:
                                    transcript.append({"who": who, "text": tr.text})
                                    await ws.send_text(json.dumps({"type": "transcript", "who": who, "text": tr.text}))
                            if sc.interrupted:
                                await ws.send_text(json.dumps({"type": "interrupted"}))
                        if resp.tool_call:
                            responses = []
                            for fc in resp.tool_call.function_calls:
                                args = dict(fc.args or {})
                                result = run_tool(fc.name, args)  # fast Firestore calls, run on the loop
                                await ws.send_text(json.dumps(
                                    {"type": "tool", "name": fc.name, "args": args, "result": result}, default=str))
                                responses.append(types.FunctionResponse(id=fc.id, name=fc.name,
                                                                        response={"result": result}))
                            await session.send_tool_response(function_responses=responses)
            except (WebSocketDisconnect, RuntimeError):
                pass
            finally:
                done.set()

        tasks = [asyncio.create_task(from_browser()), asyncio.create_task(to_browser())]
        await done.wait()
        for t in tasks:
            t.cancel()

    if transcript:
        col("calls").add({"transcript": transcript, "createdAt": SERVER_TS,
                          "summary": " / ".join(t["text"] for t in transcript[:3])[:200]})
    try:
        await ws.close()
    except RuntimeError:
        pass
