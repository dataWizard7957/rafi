"use client";
import { useRef, useState } from "react";
import { WS_URL } from "@/lib/api";

type Line = { who: "caller" | "rafi" | "tool"; text: string };

export default function LiveCallPanel() {
  const [live, setLive] = useState(false);
  const [lines, setLines] = useState<Line[]>([]);
  const [typed, setTyped] = useState("");
  const ws = useRef<WebSocket | null>(null);
  const micCtx = useRef<AudioContext | null>(null);
  const playCtx = useRef<AudioContext | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const nextTime = useRef(0);
  const sources = useRef<AudioBufferSourceNode[]>([]);

  const add = (who: Line["who"], text: string) =>
    setLines((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.who === who && who !== "tool") return [...prev.slice(0, -1), { who, text: last.text + text }];
      return [...prev, { who, text }];
    });

  const play = (buf: ArrayBuffer) => {
    const ctx = playCtx.current!;
    const pcm = new Int16Array(buf);
    const audio = ctx.createBuffer(1, pcm.length, 24000);
    const ch = audio.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 0x8000;
    const src = ctx.createBufferSource();
    src.buffer = audio;
    src.connect(ctx.destination);
    nextTime.current = Math.max(nextTime.current, ctx.currentTime);
    src.start(nextTime.current);
    nextTime.current += audio.duration;
    sources.current.push(src);
    src.onended = () => (sources.current = sources.current.filter((s) => s !== src));
  };

  const stopPlayback = () => {
    sources.current.forEach((s) => { try { s.stop(); } catch {} });
    sources.current = [];
    nextTime.current = 0;
  };

  async function start() {
    setLines([]);
    playCtx.current = new AudioContext({ sampleRate: 24000 });
    micCtx.current = new AudioContext();
    await micCtx.current.audioWorklet.addModule("/pcm-recorder.js");
    stream.current = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 },
    });
    const socket = new WebSocket(`${WS_URL}/voice/session`);
    socket.binaryType = "arraybuffer";
    socket.onmessage = (ev) => {
      if (typeof ev.data !== "string") return play(ev.data);
      const msg = JSON.parse(ev.data);
      if (msg.type === "transcript") add(msg.who, msg.text);
      if (msg.type === "interrupted") stopPlayback();
      if (msg.type === "tool") add("tool", `${msg.name}(${JSON.stringify(msg.args)})`);
    };
    socket.onclose = () => stop();
    socket.onopen = () => {
      const src = micCtx.current!.createMediaStreamSource(stream.current!);
      const node = new AudioWorkletNode(micCtx.current!, "pcm-recorder");
      node.port.onmessage = (e) => socket.readyState === WebSocket.OPEN && socket.send(e.data);
      src.connect(node);
      setLive(true);
    };
    ws.current = socket;
  }

  function stop() {
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify({ type: "end" }));
    ws.current?.close();
    ws.current = null;
    stream.current?.getTracks().forEach((t) => t.stop());
    micCtx.current?.close();
    stopPlayback();
    playCtx.current?.close();
    setLive(false);
  }

  return (
    <div className="card">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {!live ? (
          <button className="btn text-lg" onClick={start}>Call Rafi</button>
        ) : (
          <button className="btn bg-red-600 text-lg hover:bg-red-700" onClick={stop}>Hang up</button>
        )}
        <span className="chip bg-stone-100 text-stone-600">Arabic · Spanish · English</span>
        {live && <span className="chip animate-pulse bg-cedar-100 text-cedar-800">Live</span>}
      </div>
      <div className="h-96 space-y-2 overflow-y-auto rounded-lg bg-cream p-3">
        {lines.length === 0 && <div className="text-sm text-stone-500">Press Call Rafi and ask for Sahadi hummus.</div>}
        {lines.map((l, i) => (
          <div
            key={i}
            dir="auto"
            className={
              l.who === "tool"
                ? "font-mono text-xs text-stone-500"
                : l.who === "caller"
                ? "ml-auto max-w-[80%] rounded-lg bg-white p-2"
                : "max-w-[80%] rounded-lg bg-cedar-50 p-2 text-cedar-800"
            }
          >
            {l.who !== "tool" && <div className="text-xs font-semibold">{l.who === "caller" ? "Caller" : "Rafi"}</div>}
            {l.text}
          </div>
        ))}
      </div>
      {live && (
        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (!typed.trim()) return;
            ws.current?.send(JSON.stringify({ type: "text", text: typed }));
            add("caller", typed);
            setTyped("");
          }}
        >
          <input
            className="flex-1 rounded-lg border border-stone-200 px-3 py-2"
            placeholder="Backup: type what the caller says"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
          />
          <button className="btn-ghost">Send</button>
        </form>
      )}
    </div>
  );
}
