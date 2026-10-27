// Пульт ШІкарно — живий журнал роботи автопілота.
// Події шлють хуки Claude Code (studio/pult/hook.py) і CLI (studio/pult/pult.py) → Durable Object (SQLite) → WebSocket у дашборд.
// Секрети воркера: INGEST_TOKEN (запис), VIEW_KEY (перегляд: /p/<VIEW_KEY>), BOT_TOKEN і TG_WEBHOOK_SECRET (@ShikarnoUABot).
// Бот: Telegram webhook → /tg → миттєва відповідь власнику + черга, яку сесія забирає через /api/tg/pull (studio/tg/inbox.py).
import DASHBOARD from "./dashboard.html";

const KEEP = 20000; // скільки подій тримати
const AREAS = ["youtube", "voice", "render", "site", "telegram", "tiktok", "research", "pult", "other"];

const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const stub = env.PULT.get(env.PULT.idFromName("main"));
    const p = url.pathname;
    if (p === "/tg") {
      if (req.method !== "POST" || req.headers.get("x-telegram-bot-api-secret-token") !== env.TG_WEBHOOK_SECRET) return json({ error: "auth" }, 401);
      return stub.fetch(req);
    }
    if (p === "/api/ingest" || p === "/api/state" || p === "/api/tg/pull" || p === "/api/purge") {
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
    this.env = env;
    this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS ev (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, sid TEXT, kind TEXT, tool TEXT, area TEXT, text TEXT, ok INTEGER)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS ev_ts ON ev(ts)`);
    try { this.sql.exec(`ALTER TABLE ev ADD COLUMN detail TEXT`); } catch (e) {} // технічні подробиці (на пульті — під «деталі»)
    this.sql.exec(`CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS tg (id INTEGER PRIMARY KEY, ts INTEGER, upd TEXT, taken INTEGER DEFAULT 0)`);
  }

  state() {
    const r = this.sql.exec(`SELECT v FROM kv WHERE k='state'`).toArray()[0];
    return r ? JSON.parse(r.v) : {};
  }

  broadcast(msg) {
    const s = JSON.stringify(msg);
    for (const ws of this.ctx.getWebSockets()) { try { ws.send(s); } catch (e) {} }
  }

  addEvent(row) {
    const id = this.sql.exec(`INSERT INTO ev (ts,sid,kind,tool,area,text,ok) VALUES (?,?,?,?,?,?,?) RETURNING id`,
      row.ts, row.sid || "", row.kind, row.tool || "", row.area, row.text, row.ok ? 1 : 0).one().id;
    this.broadcast({ type: "events", events: [{ id, ...row, ok: row.ok ? 1 : 0 }] });
  }

  async tgCall(method, params) {
    const r = await fetch(`https://api.telegram.org/bot${this.env.BOT_TOKEN}/${method}`, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(params) });
    return r.json().catch(() => ({}));
  }

  statusText() {
    const st = this.state(), now = Date.now();
    const last = this.sql.exec(`SELECT ts, area, text FROM ev WHERE kind IN ('tool','note') ORDER BY id DESC LIMIT 1`).toArray()[0];
    const busy = last && now - last.ts < 120000;
    const kyiv = t => new Date(t).toLocaleString("uk-UA", { timeZone: "Europe/Kyiv", hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
    const nr = st.next_run ? Date.parse(st.next_run) : null;
    const notes = this.sql.exec(`SELECT ts, text FROM ev WHERE kind='note' ORDER BY id DESC LIMIT 4`).toArray();
    let t = busy ? `🟢 Байт зараз працює: ${last.text.slice(0, 120)}` : `⏸ Байт зараз не працює${last ? ` (остання дія ${kyiv(last.ts)})` : ""}.`;
    if (nr) t += `\n⏰ Наступний запуск: ${kyiv(nr)} (Київ).`;
    if (st.headline) t += `\n\n${st.headline}`;
    if (notes.length) t += "\n\nОстаннє:\n" + notes.map(n => `• ${kyiv(n.ts)} — ${n.text.slice(0, 100)}`).join("\n");
    const open = (st.tasks || []).filter(x => x.status === "waiting_owner");
    if (open.length) t += "\n\nЧекає тебе:\n" + open.map(x => "• " + x.title).join("\n");
    return t;
  }

  async onTelegram(upd) {
    const id = Number(upd.update_id) || Date.now();
    this.sql.exec(`INSERT OR IGNORE INTO tg (id, ts, upd) VALUES (?,?,?)`, id, Date.now(), JSON.stringify(upd));
    this.sql.exec(`DELETE FROM tg WHERE taken=1 AND ts < ?`, Date.now() - 14 * 86400e3);
    const m = upd.message;
    if (!m || m.chat?.type !== "private") return; // група/канал — у черзі для сесії (модерація)
    const owner = String(m.chat.id) === String(this.env.OWNER_CHAT_ID);
    const text = (m.text || m.caption || (m.photo ? "[фото]" : m.document ? "[файл]" : m.video ? "[відео]" : "[повідомлення]")).trim();
    const cmd = text.split(/[\s@]/)[0].toLowerCase();
    const pultUrl = `https://shikarno-pult.manageit-blog.workers.dev/p/${this.env.VIEW_KEY}`;
    if (!owner) {
      if (cmd === "/start") await this.tgCall("sendMessage", { chat_id: m.chat.id, text: "Привіт! Це бот каналу ШІкарно — новини ШІ українською. Канал: https://t.me/shikarno_ai_ua" });
      return;
    }
    this.sql.exec(`UPDATE tg SET taken=1 WHERE id=?`, id); // команди нижче — службові, сесії не потрібні
    if (cmd === "/status" || cmd === "/статус") {
      await this.tgCall("sendMessage", { chat_id: m.chat.id, text: this.statusText(), disable_web_page_preview: true });
      return;
    }
    if (cmd === "/pult" || cmd === "/пульт") {
      await this.tgCall("sendMessage", { chat_id: m.chat.id, text: "📡 Пульт наживо: " + pultUrl, disable_web_page_preview: true });
      return;
    }
    if (cmd === "/start" || cmd === "/help") {
      await this.tgCall("sendMessage", { chat_id: m.chat.id, text: "Я на зв'язку цілодобово.\n/status — що Байт робить зараз і що далі\n/pult — посилання на живий пульт\nБудь-яке інше повідомлення — задача або відповідь для Байта: я одразу підтверджу, а Байт візьме його в роботу на найближчій перевірці." });
      return;
    }
    this.sql.exec(`UPDATE tg SET taken=0 WHERE id=?`, id); // звичайне повідомлення — у чергу для сесії
    this.addEvent({ ts: Date.now(), kind: "prompt", area: "telegram", text: "Власник у боті: " + text.slice(0, 300), ok: true });
    const st = this.state(), nr = st.next_run ? Date.parse(st.next_run) : null;
    const last = this.sql.exec(`SELECT ts FROM ev WHERE kind IN ('tool','note') ORDER BY id DESC LIMIT 1`).toArray()[0];
    const busy = last && Date.now() - last.ts < 120000;
    const when = busy ? "Байт зараз працює — прочитає за кілька хвилин."
      : `Байт прочитає на найближчій перевірці (щогодини, цілодобово)${nr ? `; повний запуск — ${new Date(nr).toLocaleString("uk-UA", { timeZone: "Europe/Kyiv", hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" })}` : ""}.`;
    await this.tgCall("sendMessage", { chat_id: m.chat.id, text: "✅ Прийняв. " + when, reply_to_message_id: m.message_id });
  }

  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/tg") {
      const upd = await req.json().catch(() => null);
      if (upd) { try { await this.onTelegram(upd); } catch (e) { console.log("tg", e); } }
      return json({ ok: true });
    }
    if (url.pathname === "/api/purge") { // прибрати старі технічні записи (віхи й твої повідомлення лишаються)
      const b = await req.json().catch(() => ({}));
      this.sql.exec(`DELETE FROM ev WHERE ts < ? AND kind NOT IN ('note','prompt')`, Number(b.before) || 0);
      this.broadcast({ type: "reload" });
      return json({ ok: true });
    }
    if (url.pathname === "/api/tg/pull") {
      const rows = this.sql.exec(`SELECT id, upd FROM tg WHERE taken=0 ORDER BY id LIMIT 200`).toArray();
      if (rows.length) this.sql.exec(`UPDATE tg SET taken=1 WHERE id <= ? AND taken=0`, rows[rows.length - 1].id);
      return json({ updates: rows.map(r => JSON.parse(r.upd)) });
    }
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
          detail: String(e.detail || "").slice(0, 600),
          ok: e.ok === false ? 0 : 1,
        };
        const id = this.sql.exec(`INSERT INTO ev (ts,sid,kind,tool,area,text,ok,detail) VALUES (?,?,?,?,?,?,?,?) RETURNING id`,
          row.ts, row.sid, row.kind, row.tool, row.area, row.text, row.ok, row.detail).one().id;
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
