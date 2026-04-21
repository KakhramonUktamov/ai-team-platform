const API = process.env.NEXT_PUBLIC_API_URL || "";

export async function apiPost(path: string, body: any) {
  const r = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}

export async function apiGet(path: string) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}

export async function apiDelete(path: string) {
  const r = await fetch(`${API}${path}`, { method: "DELETE" });
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}

export async function* streamAgent(agentType: string, payload: any) {
  const r = await fetch(`${API}/api/agents/${agentType}/stream`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  const reader = r.body?.getReader();
  const dec = new TextDecoder();
  if (!reader) return;
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() || "";
    for (const l of lines) {
      if (l.startsWith("data:")) {
        try { const d = JSON.parse(l.slice(5).trim()); if (d.text && !d.done) yield d.text; } catch {}
      }
    }
  }
}

export async function* streamChat(payload: any) {
  const r = await fetch(`${API}/api/chat/message/stream`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  const reader = r.body?.getReader();
  const dec = new TextDecoder();
  if (!reader) return;
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() || "";
    for (const l of lines) {
      if (l.startsWith("data:")) {
        try { const d = JSON.parse(l.slice(5).trim()); if (d.text && !d.done) yield d.text; } catch {}
      }
    }
  }
}
