// ШІкарно · Співпраця — Telegram-бот для заявок рекламодавців (Cloudflare Worker, webhook).
// Без бази: стан анкети живе в callback_data кнопок і в тексті повідомлення, на яке відповідає користувач.
// Секрети воркера: BOT_TOKEN, ADMIN_CHAT_ID, WEBHOOK_SECRET.

const SITE = "https://shikarno.com.ua";
const FORMATS = {
  sh: "Інтеграція в Short", rv: "Огляд сервісу (відео + стаття)", tg: "Пост у Telegram",
  ar: "Партнерська стаття на сайті", dg: "Згадка в дайджесті", sp: "Спецпроєкт / кілька форматів",
};
const BUDGETS = { b1: "до $100", b2: "$100–300", b3: "$300–1000", b4: "понад $1000", b0: "ще не визначено" };
const TIMES = { t1: "цього тижня", t2: "протягом місяця", t3: "пізніше / гнучко" };
const MARK = "📝 Заявка ШІкарно";

const api = (env, method, body) =>
  fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  }).then(r => r.json());

const kb = (rows) => ({ inline_keyboard: rows });
const grid = (obj, prefix, cols = 1) => {
  const btns = Object.entries(obj).map(([k, v]) => ({ text: v, callback_data: prefix + k }));
  const rows = []; for (let i = 0; i < btns.length; i += cols) rows.push(btns.slice(i, i + cols)); return rows;
};
const esc = (s) => String(s ?? "").replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

const WELCOME =
  "Привіт! Я <b>Байт</b> 🤖 — ведучий ШІкарно.\n\n" +
  "ШІкарно — медіа про штучний інтелект українською: щоденні Shorts на YouTube, Telegram-канал і сайт з розборами. " +
  "Наша аудиторія — підприємці, маркетологи, розробники і всі, хто застосовує ШІ в роботі.\n\n" +
  "Три коротких питання кнопками — і заявка в менеджера. Обери формат:";

const FORMATS_TEXT =
  "<b>Формати співпраці</b>\n\n" +
  "🎬 <b>Інтеграція в Short</b> — згадка чи демонстрація продукту в ролику\n" +
  "🔎 <b>Огляд сервісу</b> — окреме відео й стаття з чесним вердиктом Байта\n" +
  "💬 <b>Пост у Telegram</b> — нативний пост або підбірка\n" +
  "📰 <b>Партнерська стаття</b> — гайд чи кейс на shikarno.com.ua\n" +
  "🗞 <b>Згадка в дайджесті</b> — блок у недільному «Дайджесті тижня»\n" +
  "🚀 <b>Спецпроєкт</b> — серія, конкурс, навчальний цикл\n\n" +
  "<b>Правила:</b> уся реклама позначена; вердикт Байта не продається; не рекламуємо казино, ставки, піраміди, " +
  "сумнівні крипто-схеми і продукти держави-агресора.\n\n" +
  `Детальніше: ${SITE}/spivpratsia/`;

async function handleMessage(env, m) {
  const chat = m.chat.id, text = (m.text || "").trim();
  const isAdmin = String(chat) === String(env.ADMIN_CHAT_ID);

  // Адмін відповідає на заявку → пересилаємо відповідь заявнику
  if (isAdmin && m.reply_to_message) {
    const id = /#id(\d+)/.exec(m.reply_to_message.text || "")?.[1];
    if (id) {
      await api(env, "sendMessage", { chat_id: id, text: `💬 Відповідь від ШІкарно:\n\n${text || "(вкладення нижче)"}` });
      if (!m.text) await api(env, "copyMessage", { chat_id: id, from_chat_id: chat, message_id: m.message_id });
      return api(env, "sendMessage", { chat_id: chat, text: "✅ Надіслано.", reply_to_message_id: m.message_id });
    }
  }
  if (text === "/myid") return api(env, "sendMessage", { chat_id: chat, text: `Ваш chat id: ${chat}` });

  if (text.startsWith("/start"))
    return api(env, "sendMessage", { chat_id: chat, text: WELCOME, parse_mode: "HTML", reply_markup: kb(grid(FORMATS, "f:")) });
  if (text === "/formats")
    return api(env, "sendMessage", { chat_id: chat, text: FORMATS_TEXT, parse_mode: "HTML", disable_web_page_preview: true,
      reply_markup: kb([[{ text: "Подати заявку", callback_data: "go" }]]) });
  if (text === "/contact")
    return askFree(env, chat, "Пряме повідомлення менеджеру");

  // Відповідь на наше питання «опиши продукт» → формуємо заявку
  const prompt = m.reply_to_message?.text || "";
  if (prompt.startsWith(MARK)) return submitLead(env, m, prompt);

  // Будь-яке інше повідомлення — теж не губимо: шлемо адміну як вільне звернення
  await forwardFree(env, m, "Вільне повідомлення");
  return api(env, "sendMessage", { chat_id: chat,
    text: "Дякую! Передав менеджеру — відповімо тут найближчим часом. А щоб було швидше, можна заповнити коротку анкету: /start" });
}

function askFree(env, chat, kind) {
  return api(env, "sendMessage", { chat_id: chat, parse_mode: "HTML",
    text: `${MARK}\nТип: ${kind}\n\n<b>Напиши одним повідомленням</b> (у відповідь на це): що за продукт, сайт, що пропонуєш і як з тобою зв'язатися.`,
    reply_markup: { force_reply: true, input_field_placeholder: "Продукт, сайт, ідея, контакт…" } });
}

async function handleCallback(env, q) {
  const chat = q.message.chat.id, d = q.data || "";
  await api(env, "answerCallbackQuery", { callback_query_id: q.id });
  if (d === "go")
    return api(env, "sendMessage", { chat_id: chat, text: "Обери формат:", reply_markup: kb(grid(FORMATS, "f:")) });
  let [step, a, b] = d.split(":");
  if (step === "f")
    return api(env, "editMessageText", { chat_id: chat, message_id: q.message.message_id,
      text: `Формат: <b>${FORMATS[a]}</b>\n\nОрієнтовний бюджет?`, parse_mode: "HTML", reply_markup: kb(grid(BUDGETS, `b:${a}:`, 2)) });
  if (step === "b") {
    // callback "b:<fmt>:<budget>"
    return api(env, "editMessageText", { chat_id: chat, message_id: q.message.message_id,
      text: `Формат: <b>${FORMATS[a]}</b>\nБюджет: <b>${BUDGETS[b]}</b>\n\nКоли плануєте старт?`, parse_mode: "HTML",
      reply_markup: kb(grid(TIMES, `t:${a}.${b}:`)) });
  }
  if (step === "t") {
    const [fmt, bud] = a.split(".");
    await api(env, "editMessageText", { chat_id: chat, message_id: q.message.message_id, parse_mode: "HTML",
      text: `Формат: <b>${FORMATS[fmt]}</b>\nБюджет: <b>${BUDGETS[bud]}</b>\nСтарт: <b>${TIMES[b]}</b>` });
    return api(env, "sendMessage", { chat_id: chat, parse_mode: "HTML",
      text: `${MARK}\nФормат: ${FORMATS[fmt]}\nБюджет: ${BUDGETS[bud]}\nСтарт: ${TIMES[b]}\n\n` +
            "Останній крок 👇 <b>Відповідай на це повідомлення</b>: назва продукту, сайт, що хочеш показати аудиторії, і контакт (Telegram/email).",
      reply_markup: { force_reply: true, input_field_placeholder: "Продукт, сайт, ідея, контакт…" } });
  }
}

async function submitLead(env, m, prompt) {
  const u = m.from || {};
  const who = `${esc([u.first_name, u.last_name].filter(Boolean).join(" "))}${u.username ? " @" + esc(u.username) : ""}`;
  const fields = esc(prompt.split("\n").slice(1).filter(l => /^(Формат|Бюджет|Старт|Тип):/.test(l)).join("\n"));
  await api(env, "sendMessage", { chat_id: env.ADMIN_CHAT_ID, parse_mode: "HTML", disable_web_page_preview: true,
    text: `🔥 <b>Нова заявка на співпрацю</b>\nВід: ${who} #id${m.chat.id}\n\n${fields}\n\n<b>Опис:</b>\n${esc(m.text || "(вкладення)")}\n\n<i>Відповідай на це повідомлення — бот перешле відповідь заявнику.</i>` });
  if (!m.text) await api(env, "copyMessage", { chat_id: env.ADMIN_CHAT_ID, from_chat_id: m.chat.id, message_id: m.message_id });
  return api(env, "sendMessage", { chat_id: m.chat.id, parse_mode: "HTML",
    text: "✅ <b>Заявку прийнято!</b> Менеджер відповість тут, у цьому чаті, зазвичай протягом доби.\n\n" +
          `Поки чекаєш — глянь наші матеріали: ${SITE}` });
}

async function forwardFree(env, m, kind) {
  const u = m.from || {};
  const who = `${esc([u.first_name, u.last_name].filter(Boolean).join(" "))}${u.username ? " @" + esc(u.username) : ""}`;
  await api(env, "sendMessage", { chat_id: env.ADMIN_CHAT_ID, parse_mode: "HTML",
    text: `✉️ <b>${kind}</b>\nВід: ${who} #id${m.chat.id}\n\n${esc(m.text || "(вкладення)")}\n\n<i>Відповідай на це повідомлення — бот перешле.</i>` });
  if (!m.text) await api(env, "copyMessage", { chat_id: env.ADMIN_CHAT_ID, from_chat_id: m.chat.id, message_id: m.message_id });
}

export default {
  async fetch(req, env) {
    if (req.method !== "POST") return new Response("ШІкарно · Співпраця бот працює ✅");
    if (req.headers.get("x-telegram-bot-api-secret-token") !== env.WEBHOOK_SECRET) return new Response("forbidden", { status: 403 });
    const upd = await req.json();
    try {
      if (upd.message && upd.message.chat.type === "private") await handleMessage(env, upd.message);
      else if (upd.callback_query) await handleCallback(env, upd.callback_query);
    } catch (e) { console.log("error", e && e.stack || e); }
    return new Response("ok");
  },
};
