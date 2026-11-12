// Байт · ШІкарно (@ShikarnoBaitBot) — «Твій ШІ-помічник за 10 хвилин».
// Webhook → Durable Object (SQLite): користувачі (tg id, ім'я, email за згодою, професія, ШІ, прогрес).
// Секрет воркера: BOT_TOKEN. Секрет вебхука = перші 32 символи SHA-256 від токена (обчислюється тут і при setWebhook).
const SITE = "https://shikarno.com.ua";
const PROF = {
  vch: { name: "Вчитель", page: "/pomichnyk-vchytel/", emoji: "👩‍🏫",
    first: ["Перевір твір (вставляю текст нижче). Учень 1, 6 клас. Оціни за 12-бальною шкалою і дай дружній відгук.",
            "План уроку на 45 хвилин: Прикметник, 6 клас, з грою на 7 хвилин.",
            "Лист батькам: дитина 3 тижні не здає домашні завдання. Тон — підтримка, без звинувачень."] },
  fop: { name: "ФОП / малий бізнес", page: "/pomichnyk-fop/", emoji: "☕",
    first: ["Склади контент-план на тиждень для Instagram і Telegram моєї кав'ярні: 5 постів, з ідеями для фото.",
            "Відповідь на відгук: «Чекав каву 20 хвилин». Ввічливо, з вибаченням і пропозицією.",
            "Зроби прайс-лист на 10 позицій з короткими апетитними описами."] },
};
const AI = { gpt: "ChatGPT", gem: "Gemini", cla: "Claude", idk: "Не знаю — порадь" };
const PRIVACY = SITE + "/pryvatnist/";

const enc = new TextEncoder();
async function hookSecret(tok) {
  const h = await crypto.subtle.digest("SHA-256", enc.encode(tok));
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json" } });

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/tg" && req.method === "POST") {
      if (req.headers.get("x-telegram-bot-api-secret-token") !== await hookSecret(env.BOT_TOKEN)) return json({ error: "auth" }, 401);
      const stub = env.DB.get(env.DB.idFromName("main"));
      return stub.fetch(req);
    }
    return new Response("Байт на зв'язку 🤖 Пиши в Telegram: https://t.me/ShikarnoBaitBot", { headers: { "content-type": "text/plain; charset=utf-8" } });
  },
};

export class BaitDB {
  constructor(ctx, env) {
    this.env = env; this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS u (id INTEGER PRIMARY KEY, name TEXT, email TEXT, consent INTEGER DEFAULT 0, prof TEXT, ai TEXT,
      step TEXT, src TEXT, created INTEGER, updated INTEGER, setup INTEGER DEFAULT 0)`);
  }
  api(method, body) {
    return fetch(`https://api.telegram.org/bot${this.env.BOT_TOKEN}/${method}`, { method: "POST",
      headers: { "content-type": "application/json" }, body: JSON.stringify(body) }).then(r => r.json()).catch(() => ({}));
  }
  send(chat, text, extra = {}) { return this.api("sendMessage", { chat_id: chat, text, parse_mode: "HTML", disable_web_page_preview: true, ...extra }); }
  user(id) { return this.sql.exec(`SELECT * FROM u WHERE id=?`, id).toArray()[0]; }
  upsert(id, f) {
    const now = Date.now(), u = this.user(id);
    if (!u) this.sql.exec(`INSERT INTO u (id, created, updated) VALUES (?, ?, ?)`, id, now, now);
    for (const [k, v] of Object.entries(f)) this.sql.exec(`UPDATE u SET ${k}=?, updated=? WHERE id=?`, v, now, id);
  }
  async subscribed(id) {
    const r = await this.api("getChatMember", { chat_id: this.env.CHANNEL, user_id: id });
    if (!r.ok) return null; // бот не адмін у каналі — не блокуємо
    return ["creator", "administrator", "member", "restricted"].includes(r.result.status);
  }
  esc(s) { return String(s ?? "").replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

  async fetch(req) {
    const upd = await req.json().catch(() => ({}));
    try { await this.handle(upd); } catch (e) { await this.send(this.env.OWNER_CHAT_ID, "⚠️ Байт-бот помилка: " + this.esc(String(e).slice(0, 300))); }
    return json({ ok: true });
  }

  async handle(upd) {
    const cb = upd.callback_query;
    if (cb) { await this.api("answerCallbackQuery", { callback_query_id: cb.id }); return this.onButton(cb.from, cb.data); }
    const m = upd.message; if (!m || m.chat.type !== "private") return;
    const id = m.from.id, t = (m.text || "").trim();
    if (t.startsWith("/start")) return this.start(m.from, t.split(" ")[1] || "");
    if (t === "/stats" && String(id) === this.env.OWNER_CHAT_ID) return this.stats(id);
    if (t === "/delete") { this.sql.exec(`DELETE FROM u WHERE id=?`, id); return this.send(id, "Готово: я видалив усі твої дані (ім'я, пошту, вибір). Щоб почати знову — /start"); }
    const u = this.user(id);
    if (u?.step === "name") return this.gotName(id, t);
    if (u?.step === "email") return this.gotEmail(id, t);
    return this.send(id, "Натисни /start, щоб зібрати свого ШІ-помічника 🤖\nПитання чи щось не вийшло — пиши сюди, я передам людям ШІкарно.");
  }

  async start(from, src) {
    this.upsert(from.id, { step: "sub", src: src.slice(0, 32) });
    const sub = await this.subscribed(from.id);
    if (sub === false) return this.send(from.id,
      `Привіт, я <b>Байт</b> 🤖 За 10 хвилин зберу тобі особистого ШІ-помічника під твою роботу — безкоштовно.\n\nОдна умова: підпишись на наш канал <b>ШІкарно</b> — там щодня корисне про ШІ українською. Потім натисни «Я підписався».`,
      { reply_markup: { inline_keyboard: [[{ text: "📢 Підписатися на ШІкарно", url: "https://t.me/shikarno_ai_ua" }], [{ text: "✅ Я підписався", callback_data: "sub" }]] } });
    return this.askProf(from.id);
  }
  askProf(id) {
    this.upsert(id, { step: "prof" });
    return this.send(id, `Привіт, я <b>Байт</b> 🤖 Зберу тобі готового ШІ-помічника — не урок, а робочий інструмент.\n\n<b>Хто ти?</b>`,
      { reply_markup: { inline_keyboard: [
        ...Object.entries(PROF).map(([k, p]) => [{ text: `${p.emoji} ${p.name}`, callback_data: "p:" + k }]),
        [{ text: "🧩 Інша професія (скоро)", callback_data: "p:other" }]] } });
  }
  async onButton(from, d) {
    const id = from.id;
    if (d === "sub") {
      const sub = await this.subscribed(id);
      if (sub === false) return this.send(id, "Ще не бачу підписки 🙈 Підпишись на @shikarno_ai_ua і натисни «Я підписався» ще раз.");
      return this.askProf(id);
    }
    if (d === "p:other") {
      this.upsert(id, { prof: "other", step: "other" });
      await this.send(this.env.OWNER_CHAT_ID, `🧩 Байт-бот: запит «інша професія» від ${this.esc(from.first_name)} (id ${id})`);
      return this.send(id, "Напиши одним повідомленням, хто ти за професією і що забирає найбільше часу — я передам команді, і ми зберемо набір під тебе. Коли буде готово — я напишу 🙌");
    }
    if (d.startsWith("p:")) {
      const k = d.slice(2); if (!PROF[k]) return;
      this.upsert(id, { prof: k, step: "ai" });
      return this.send(id, "Яким ШІ користуєшся (або хочеш)?", { reply_markup: { inline_keyboard:
        Object.entries(AI).map(([a, n]) => [{ text: n, callback_data: "a:" + a }]) } });
    }
    if (d.startsWith("a:")) {
      const a = d.slice(2); if (!AI[a]) return;
      this.upsert(id, { ai: a, step: "name" });
      return this.send(id, "Як тебе звати? Напиши ім'я — лише для привітання 🙂", { reply_markup: { force_reply: true, input_field_placeholder: "Ім'я" } });
    }
    if (d === "e:skip") { this.upsert(id, { step: "done" }); return this.deliver(id); }
    if (d === "setup") {
      this.upsert(id, { setup: 1 });
      const u = this.user(id), p = PROF[u?.prof];
      if (!p) return;
      return this.send(id, `Супер, ${this.esc(u.name)}! 🎉 Спробуй прямо зараз — скопіюй у свого помічника:\n\n` +
        p.first.map((c, i) => `${i + 1}. <code>${this.esc(c)}</code>`).join("\n\n") +
        `\n\nЩовівторка я надсилатиму апгрейд твого помічника. Щось не вийшло — просто напиши сюди.`);
    }
  }
  gotName(id, t) {
    const name = t.replace(/[<>]/g, "").slice(0, 40);
    if (!name || name.startsWith("/")) return this.send(id, "Напиши, будь ласка, ім'я 🙂");
    this.upsert(id, { name, step: "email" });
    return this.send(id,
      `Приємно, ${this.esc(name)}! Останнє (за бажанням): залиш <b>email</b> — надішлю туди паспорт помічника й щотижневі апгрейди.\n\n` +
      `Надсилаючи пошту, ти погоджуєшся, що ШІкарно зберігає її лише для цих листів (<a href="${PRIVACY}">політика конфіденційності</a>). Видалити дані — /delete.`,
      { reply_markup: { inline_keyboard: [[{ text: "Пропустити →", callback_data: "e:skip" }]] } });
  }
  gotEmail(id, t) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(t)) return this.send(id, "Схоже, це не email 🤔 Напиши ще раз або натисни «Пропустити».",
      { reply_markup: { inline_keyboard: [[{ text: "Пропустити →", callback_data: "e:skip" }]] } });
    this.upsert(id, { email: t.slice(0, 120).toLowerCase(), consent: 1, step: "done" });
    return this.deliver(id);
  }
  async deliver(id) {
    const u = this.user(id), p = PROF[u.prof]; if (!p) return this.askProf(id);
    const ai = AI[u.ai] || "ChatGPT", where = u.ai === "idk" ? "Раджу почати з безкоштовного ChatGPT або Gemini — на сторінці є кроки для обох." : `На сторінці відкрий розділ «Крок 2» → ${ai}.`;
    await this.send(id,
      `${p.emoji} <b>${this.esc(u.name)}, твій помічник готовий!</b>\n\n` +
      `1️⃣ Відкрий набір і натисни «Скопіювати» біля інструкції.\n2️⃣ ${this.esc(where)}\n3️⃣ Встав — і помічник уже знає твою роботу.\n\n` +
      `Усередині: 30 готових команд, шаблони, картка безпеки і маршрут на 4 тижні.`,
      { reply_markup: { inline_keyboard: [[{ text: "📦 Відкрити мій набір", url: SITE + p.page }], [{ text: "✅ Налаштував!", callback_data: "setup" }]] } });
    await this.send(this.env.OWNER_CHAT_ID, `🤖 Байт-бот: новий помічник — ${p.name}, ${this.esc(ai)}${u.email ? ", з email" : ""}`);
  }
  stats(id) {
    const r = this.sql.exec(`SELECT COUNT(*) n, SUM(email IS NOT NULL) e, SUM(setup) s, SUM(step='done') d FROM u`).toArray()[0];
    const by = this.sql.exec(`SELECT prof, COUNT(*) n FROM u GROUP BY prof`).toArray().map(x => `${x.prof || "—"}: ${x.n}`).join(", ");
    return this.send(id, `📊 Байт-бот\nСтарти: ${r.n}\nОтримали набір: ${r.d || 0}\nНалаштували: ${r.s || 0}\nEmail: ${r.e || 0}\nЗа професіями: ${by}`);
  }
}
