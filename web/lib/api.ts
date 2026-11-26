export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080").replace(/\/$/, "");
export const WS_URL = API_URL.replace(/^http/, "ws");

import { DEMO, demoPost, demoUpload } from "./demo";

export async function post(path: string, body?: unknown) {
  if (DEMO) return demoPost(path);
  const r = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

/** Fetch a bundled demo file from /public/demo and wrap it as a File for upload(). */
export async function demoFile(name: string, type: string): Promise<File> {
  const r = await fetch(`/demo/${name}`);
  if (!r.ok) throw new Error(`Demo file missing: ${name}`);
  return new File([await r.blob()], name, { type });
}

export async function upload(path: string, field: string, file: File) {
  if (DEMO) return demoUpload(path, file);
  const fd = new FormData();
  fd.append(field, file);
  const r = await fetch(`${API_URL}${path}`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
