// Байт · ШІкарно (@ShikarnoBaitBot) — «Твій ШІ-помічник за 10 хвилин».
// Webhook → Durable Object (SQLite): користувачі (tg id, ім'я, email за згодою, професія, ШІ, прогрес).
// Секрет воркера: BOT_TOKEN. Секрет вебхука = перші 32 символи SHA-256 від токена (обчислюється тут і при setWebhook).
import { KITS } from "./kits.js";
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
  vod: { name: "Водій / кур'єр", page: "/pomichnyk-vodiy/", emoji: "🚗",
    first: ["Переклади пасажиру англійською: «Ми будемо на місці за 15 хвилин, оплата карткою можлива». І дай вимову українськими літерами.",
            "Опиши проблему для СТО: на холодну машина стукає спереду справа, на швидкості зникає. Які питання мені поставити майстру?",
            "Ось чеки за тиждень (вставляю текст). Порахуй витрати на пальне, мийку й ремонт окремо."] },
  hr: { name: "HR / рекрутер", page: "/pomichnyk-hr/", emoji: "👥",
    first: ["Напиши вакансію: менеджер з продажу, Київ, гібрид. Тон — живий, без канцеляриту, з чесним описом задач.",
            "Склади 10 питань для співбесіди на менеджера з продажу: 5 про досвід, 5 ситуаційних.",
            "Ввічлива відмова кандидату після співбесіди — тепло, з побажанням і без шаблонності."] },
  smm: { name: "SMM / маркетолог", page: "/pomichnyk-smm/", emoji: "📱",
    first: ["Контент-план на тиждень для Instagram кав'ярні: 5 постів + 2 Reels, з гачками в першому реченні.",
            "Сценарій Reels на 20 секунд: «3 помилки, через які кава вдома гірша, ніж у кав'ярні». Гачок у перші 2 секунди.",
            "5 варіантів рекламного тексту для A/B-тесту: знижка 20% на каву з собою до 10:00."] },
  stu: { name: "Студент", page: "/pomichnyk-student/", emoji: "🎓",
    first: ["Поясни простими словами (вставляю конспект лекції) і зроби 5 питань для самоперевірки.",
            "Склади план підготовки до сесії: 4 предмети, 3 тижні, по 2 години на день.",
            "Ось мій вступ до курсової (вставляю). Що покращити в структурі й логіці? Не переписуй за мене."] },
  bux: { name: "Бухгалтер", page: "/pomichnyk-bukhgalter/", emoji: "📊",
    first: ["Поясни клієнту-ФОП простими словами, навіщо подавати звіт і що буде, якщо запізнитися. Без цифр штрафів — їх я перевірю сам.",
            "Формула для Google Таблиць: сума з колонки C, якщо в колонці A дата цього місяця, а в B — «оплачено».",
            "Лист клієнту: нагадування надіслати первинні документи до 5 числа. Ввічливо й коротко."] },
  pro: { name: "Менеджер з продажу", page: "/pomichnyk-prodazhi/", emoji: "🤝",
    first: ["Скрипт першого дзвінка для B2B: продаю облік для кав'ярень. 30 секунд, без тиску, з питанням у кінці.",
            "Клієнт каже «дорого». Дай 3 чесні способи відповісти, без маніпуляцій.",
            "Фоллоу-ап після зустрічі: дякую, коротко що домовились, наступний крок і дата."] },
  rep: { name: "Репетитор", page: "/pomichnyk-repetytor/", emoji: "📚",
    first: ["Склади план заняття на 60 хв для учня 8 класу з теми «Квадратні рівняння» — з розминкою і домашнім.",
            "Поясни тему «Present Perfect» трьома способами: просто, наочно і строго.",
            "Напиши батькам короткий звіт про прогрес учня за місяць — чесно і без тиску."] },
  kra: { name: "Майстер краси", page: "/pomichnyk-krasa/", emoji: "💇",
    first: ["Напиши пост до фото манікюру (нюдовий френч, 1,5 год) з гачком і закликом записатися.",
            "Клієнтка питає ціну і чи є вікно в суботу — напиши теплу відповідь у директ.",
            "Склади пам'ятку після фарбування волосся — загальні поради, без медичних обіцянок."] },
  rie: { name: "Ріелтор", page: "/pomichnyk-rieltor/", emoji: "🏠",
    first: ["Напиши чесний опис 2-кімнатної квартири 54 м², 3/9 поверх, з косметичним ремонтом — без «елітний» і «унікальний».",
            "Склади чек-лист показу квартири на вторинці: що оглянути і що спитати власника.",
            "Напиши фоловап клієнту наступного дня після показу — без тиску, з наступним кроком."] },
  fri: { name: "Фрилансер", page: "/pomichnyk-frilanser/", emoji: "💻",
    first: ["Ось опис проєкту: [встав]. Напиши відгук до 120 слів — перший рядок про задачу клієнта, 2 уточнювальні питання.",
            "Склади 7–10 уточнювальних питань до цього брифу, щоб точно оцінити роботу: [встав]",
            "Напиши ввічливе нагадування про оплату: робота здана [дата], сума [сума], термін минув [дата]."] },
  mar: { name: "Продавець на маркетплейсах", page: "/pomichnyk-marketpleys/", emoji: "🛒",
    first: ["Ось дані про товар: [встав]. Напиши 3 назви і опис з ключовими словами — лише факти з моїх даних.",
            "Покупець питає: «[питання]». Напиши відповідь на 2–3 речення з наступним кроком до замовлення.",
            "Відповідай на негативний відгук: [встав]. Визнай проблему, запропонуй рішення, без суперечок."] },
  mai: { name: "Майстер ремонту", page: "/pomichnyk-maister/", emoji: "🔧",
    first: ["Склади попередній кошторис зі списку робіт: [встав]. Мої ціни: [встав]. Таблицею, з рядком «непередбачені роботи».",
            "Склади список матеріалів для [робота, площа] із запасом і позначкою, що звірити з заміром.",
            "Клієнт пише: «[заявка]». Напиши відповідь: коли можу приїхати на огляд, що підготувати, як формується ціна."] },
  ins: { name: "Продавець в Instagram", page: "/pomichnyk-instagram/", emoji: "📸",
    first: ["Напиши пост для Instagram про [товар]: матеріал, розміри, ціна — гачок у першому рядку, заклик написати в Direct і 3–5 хештегів.",
            "Покупець питає: «[ціна / наявність / розмір]» — напиши коротку теплу відповідь у Direct з наступним кроком до замовлення.",
            "Напиши тексти для хайлайтів «Доставка», «Оплата», «Обмін» за моїми умовами: [Нова пошта / Укрпошта, передоплата, обмін]."] },
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
  async scheduled(ev, env) {
    const stub = env.DB.get(env.DB.idFromName("main"));
    await stub.fetch("https://do/weekly", { method: "POST" });
  },
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
    for (const c of ["wk INTEGER DEFAULT 0", "wk_ts INTEGER DEFAULT 0"]) { try { this.sql.exec(`ALTER TABLE u ADD COLUMN ${c}`); } catch (e) {} }
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
    if (new URL(req.url).pathname === "/weekly") { await this.weekly(); return json({ ok: true }); }
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
    if (u?.step === "uniq" || u?.step === "other") {
      this.upsert(id, { step: "done" });
      await this.send(this.env.OWNER_CHAT_ID, `✨ Байт-бот: запит на ${u.step === "uniq" ? "УНІКАЛЬНИЙ помічник" : "іншу професію"} від ${this.esc(u.name || m.from.first_name)} (id ${id}, ${this.esc(PROF[u.prof]?.name || u.prof || "—")}):\n\n${this.esc(t.slice(0, 1500))}`);
      return this.send(id, "Записав 📝 Передав команді — напишу тобі тут, щойно твій помічник буде готовий.");
    }
    if (String(id) === this.env.OWNER_CHAT_ID && m.reply_to_message) {
      const mm = /\(id (\d+)/.exec(m.reply_to_message.text || "");
      if (mm) { await this.send(mm[1], "💬 Відповідь від команди ШІкарно:\n\n" + this.esc(t)); return this.send(id, "✅ Надіслано"); }
    }
    if (u && t) {
      await this.send(this.env.OWNER_CHAT_ID, `💬 Спитай Байта — ${this.esc(u.name || m.from.first_name)} (id ${id}, ${this.esc(PROF[u.prof]?.name || "—")}):\n\n${this.esc(t.slice(0, 1500))}\n\n↩️ Відповідай реплаєм на це повідомлення — я перешлю.`);
      return this.send(id, "Отримав 📝 Передав команді ШІкарно — відповімо тут найближчим часом.");
    }
    return this.send(id, "Натисни /start, щоб зібрати свого ШІ-помічника 🤖");
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
        ...Object.entries(PROF).reduce((rows, [k, p], i) => { const b = { text: `${p.emoji} ${p.name}`, callback_data: "p:" + k }; i % 2 ? rows[rows.length - 1].push(b) : rows.push([b]); return rows; }, []),
        [{ text: "🧩 Інша професія", callback_data: "p:other" }]] } });
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
    if (d === "wdone") return this.send(id, "Супер! 💪 Наступний крок прийде у вівторок.");
    if (d === "wfail") { this.upsert(id, { step: "done" }); return this.send(id, "Напиши одним повідомленням, що саме не вийшло — команда ШІкарно підкаже."); }
    if (d === "uniq") {
      this.upsert(id, { step: "uniq" });
      return this.send(id, "Базовий набір — під типову роботу. Хочеш помічника саме під себе? Опиши одним повідомленням: чим займаєшся (ніша, місто/онлайн), хто твої клієнти і що найбільше забирає час. Команда ШІкарно збере унікальну сторінку під тебе і я напишу, коли готово 🙌");
    }
    if (d === "e:skip") { this.upsert(id, { step: "done" }); return this.deliver(id); }
    if (d === "setup") {
      this.upsert(id, { setup: 1 });
      const u = this.user(id), p = PROF[u?.prof];
      if (!p) return;
      return this.send(id, `Супер, ${this.esc(u.name)}! 🎉 Спробуй прямо зараз — скопіюй у свого помічника:\n\n` +
        p.first.map((c, i) => `${i + 1}. <code>${this.esc(c)}</code>`).join("\n\n") +
        `\n\nЩовівторка я надсилатиму наступний крок маршруту. Щось не вийшло — просто напиши сюди.`).then(() => this.sendWeek(id));
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
    const kit = KITS[p.page];
    if (kit?.instr) {
      await this.send(id, `${p.emoji} <b>${this.esc(u.name)}, ось «мозок» твого помічника.</b> Натисни на текст нижче — він скопіюється:`);
      await this.send(id, `<pre>${this.esc(kit.instr)}</pre>`);
      const fd = new FormData();
      fd.append("chat_id", String(id));
      fd.append("caption", "Той самий текст файлом — зручно з комп'ютера.");
      fd.append("document", new Blob([kit.instr], { type: "text/plain" }), `pomichnyk-${u.prof}.txt`);
      await fetch(`https://api.telegram.org/bot${this.env.BOT_TOKEN}/sendDocument`, { method: "POST", body: fd }).catch(() => {});
    }
    await this.send(id,
      `${p.emoji} <b>${this.esc(u.name)}, твій помічник готовий!</b>\n\n` +
      `1️⃣ Скопіюй інструкцію вище.\n2️⃣ ${this.esc(where)}\n3️⃣ Встав — і помічник уже знає твою роботу.\n\n` +
      `У повному наборі на сайті: 30 готових команд, шаблони, картка безпеки і маршрут на 4 тижні.`,
      { reply_markup: { inline_keyboard: [[{ text: "📦 Повний набір: 30 команд і шаблони", url: SITE + p.page }], [{ text: "✅ Налаштував!", callback_data: "setup" }], [{ text: "✨ Хочу унікальний — під мій бізнес", callback_data: "uniq" }]] } });
    await this.send(this.env.OWNER_CHAT_ID, `🤖 Байт-бот: новий помічник — ${p.name}, ${this.esc(ai)}${u.email ? ", з email" : ""}`);
  }
  async sendWeek(id) {
    const u = this.user(id), p = PROF[u?.prof], kit = p && KITS[p.page];
    if (!kit || (u.wk || 0) >= kit.weeks.length) return;
    const w = kit.weeks[u.wk || 0];
    this.upsert(id, { wk: (u.wk || 0) + 1, wk_ts: Date.now() });
    return this.send(id, `🗺 <b>${this.esc(w.title)}</b>\n\n${w.body}\n\nЗробив? Тисни кнопку — або напиши, що не вийшло.`,
      { reply_markup: { inline_keyboard: [[{ text: "✅ Зробив", callback_data: "wdone" }, { text: "🤔 Не вийшло", callback_data: "wfail" }]] } });
  }
  async weekly() {
    const due = Date.now() - 6.5 * 864e5;
    const rows = this.sql.exec(`SELECT id FROM u WHERE setup=1 AND wk>=1 AND wk<4 AND wk_ts<?`, due).toArray();
    for (const r of rows) await this.sendWeek(r.id);
  }
  stats(id) {
    const r = this.sql.exec(`SELECT COUNT(*) n, SUM(email IS NOT NULL) e, SUM(setup) s, SUM(step='done') d, SUM(wk>=2) w2 FROM u`).toArray()[0];
    const by = this.sql.exec(`SELECT prof, COUNT(*) n FROM u GROUP BY prof`).toArray().map(x => `${x.prof || "—"}: ${x.n}`).join(", ");
    return this.send(id, `📊 Байт-бот\nСтарти: ${r.n}\nОтримали набір: ${r.d || 0}\nНалаштували: ${r.s || 0}\nEmail: ${r.e || 0}\nДійшли до 2-го тижня: ${r.w2 || 0}\nЗа професіями: ${by}`);
  }
}
