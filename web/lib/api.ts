export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080").replace(/\/$/, "");
export const WS_URL = API_URL.replace(/^http/, "ws");

export async function post(path: string, body?: unknown) {
  const r = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export async function upload(path: string, field: string, file: File) {
  const fd = new FormData();
  fd.append(field, file);
  const r = await fetch(`${API_URL}${path}`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
