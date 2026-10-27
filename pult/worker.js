// Пульт ШІкарно — живий журнал роботи автопілота.
// Події шлють хуки Claude Code (studio/pult/hook.py) і CLI (studio/pult/pult.py) → Durable Object (SQLite) → WebSocket у дашборд.
// Секрети воркера: INGEST_TOKEN (запис), VIEW_KEY (перегляд: /p/<VIEW_KEY>).
import DASHBOARD from "./dashboard.html";

const KEEP = 20000; // скільки подій тримати
const AREAS = ["youtube", "voice", "render", "site", "telegram", "tiktok", "research", "pult", "other"];

const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const stub = env.PULT.get(env.PULT.idFromName("main"));
    const p = url.pathname;
    if (p === "/api/ingest" || p === "/api/state") {
      if (req.method !== "POST") return json({ error: "method" }, 405);
      if (req.headers.get("authorization") !== `Bearer ${env.INGEST_TOKEN}`) return json({ error: "auth" }, 401);
      return stub.fetch(req);
    }
    const key = url.searchParams.get("k") || (p.startsWith("/p/") ? p.slice(3).replace(/\/$/, "") : "");
    if (p.startsWith("/p/")) {
      if (key !== env.VIEW_KEY) return new Response("Не знайдено", { status: 404 });
      return new Response(DASHBOARD, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" } });
    }
    if (p === "/api/snapshot" || p === "/ws") {
      if (key !== env.VIEW_KEY) return json({ error: "auth" }, 401);
      return stub.fetch(req);
    }
    if (p === "/robots.txt") return new Response("User-agent: *\nDisallow: /\n");
    return new Response("ШІкарно", { status: 404 });
  },
};

export class Pult {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS ev (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, sid TEXT, kind TEXT, tool TEXT, area TEXT, text TEXT, ok INTEGER)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS ev_ts ON ev(ts)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)`);
  }

  state() {
    const r = this.sql.exec(`SELECT v FROM kv WHERE k='state'`).toArray()[0];
    return r ? JSON.parse(r.v) : {};
  }

  broadcast(msg) {
    const s = JSON.stringify(msg);
    for (const ws of this.ctx.getWebSockets()) { try { ws.send(s); } catch (e) {} }
  }

  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/ws") {
      if (req.headers.get("upgrade") !== "websocket") return json({ error: "upgrade" }, 426);
      const pair = new WebSocketPair();
      this.ctx.acceptWebSocket(pair[1]);
      return new Response(null, { status: 101, webSocket: pair[0] });
    }
    if (url.pathname === "/api/ingest") {
      const body = await req.json().catch(() => null);
      const list = Array.isArray(body?.events) ? body.events : body ? [body] : [];
      const out = [];
      for (const e of list.slice(0, 50)) {
        const row = {
          ts: Number(e.ts) || Date.now(),
          sid: String(e.sid || "").slice(0, 64),
          kind: String(e.kind || "note").slice(0, 32),
          tool: String(e.tool || "").slice(0, 48),
          area: AREAS.includes(e.area) ? e.area : "other",
          text: String(e.text || "").slice(0, 400),
          ok: e.ok === false ? 0 : 1,
        };
        const id = this.sql.exec(`INSERT INTO ev (ts,sid,kind,tool,area,text,ok) VALUES (?,?,?,?,?,?,?) RETURNING id`,
          row.ts, row.sid, row.kind, row.tool, row.area, row.text, row.ok).one().id;
        out.push({ id, ...row });
      }
      this.sql.exec(`DELETE FROM ev WHERE id <= (SELECT MAX(id) FROM ev) - ?`, KEEP);
      if (out.length) this.broadcast({ type: "events", events: out });
      return json({ ok: true, n: out.length });
    }
    if (url.pathname === "/api/state") {
      const patch = await req.json().catch(() => ({}));
      const st = { ...this.state(), ...patch, updated: Date.now() };
      this.sql.exec(`INSERT OR REPLACE INTO kv (k,v) VALUES ('state',?)`, JSON.stringify(st));
      this.broadcast({ type: "state", state: st });
      return json({ ok: true });
    }
    if (url.pathname === "/api/snapshot") {
      const now = Date.now();
      const events = this.sql.exec(`SELECT * FROM ev ORDER BY id DESC LIMIT 400`).toArray().reverse();
      const agg = {};
      for (const [k, ms] of [["h", 3600e3], ["d", 86400e3], ["w", 7 * 86400e3]]) {
        agg[k] = {};
        for (const r of this.sql.exec(`SELECT area, COUNT(*) n, SUM(1-ok) err FROM ev WHERE ts > ? AND kind='tool' GROUP BY area`, now - ms).toArray())
          agg[k][r.area] = { n: r.n, err: r.err };
      }
      const human = this.sql.exec(`SELECT MAX(ts) t FROM ev WHERE kind='prompt'`).toArray()[0]?.t || null;
      return json({ now, events, agg, human, state: this.state() });
    }
    return json({ error: "nf" }, 404);
  }

  webSocketMessage(ws, msg) { if (msg === "ping") ws.send("pong"); }
  webSocketClose(ws, code) { try { ws.close(code, "bye"); } catch (e) {} }
}
