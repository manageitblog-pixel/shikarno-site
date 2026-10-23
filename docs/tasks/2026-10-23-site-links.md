# Задача: прописати сайт shikarno.com.ua у YouTube і Telegram

Виконати в сесії, де є доступи (yt/token.json, tg/.token). Рендер не чіпати: це лише легкі API-запити.

## 1. Описи роликів YouTube
Для кожного відео: videos.list(part=snippet) → дописати блок у КІНЕЦЬ опису, якщо там ще немає «shikarno.com.ua» →
videos.update(part=snippet) з тими самими title, categoryId, tags, defaultLanguage (snippet надсилається повністю, інакше поля зітруться).
status/publishAt НЕ чіпати — заплановані ролики мають вийти за розкладом.
Потрібен scope youtube.force-ssl (або youtube); якщо в токені лише upload+readonly — згенерувати нове посилання авторизації (PKCE, redirect http://localhost) зі scope youtube.upload + youtube + youtube.force-ssl і надіслати користувачу.

Блок (<URL> — з таблиці; якщо статті немає, рядок «📖» пропустити):
```
———
📖 Розбір з джерелами: <URL>
🌐 Сайт: https://shikarno.com.ua
💬 Telegram: https://t.me/shikarno_ai_ua
```

| Відео | ID | Стаття |
|---|---|---|
| Еп.1 примірка | theMaZ3jGR4 | https://shikarno.com.ua/novyny/chatgpt-prymirka-odyagu/ |
| Еп.2 Chrome | biSJLBhwIRE | https://shikarno.com.ua/novyny/chatgpt-u-chrome-vkladky/ |
| Еп.3 FLUX 3 Max | uEA0vrgrkf0 | https://shikarno.com.ua/novyny/flux-3-max-video/ |
| Еп.4 Gemini в авто | TeQP_kM98Ng | https://shikarno.com.ua/novyny/gemini-android-auto/ |
| Еп.5 агенти OpenAI | ctzCraL03OE | https://shikarno.com.ua/novyny/agenty-openai-nagliad/ |
| Еп.6 Intelligent UI | mP4aIt0qbik | https://shikarno.com.ua/novyny/chatgpt-intelligent-ui-gpt-6/ |
| Розбір #1 PHP2Shell | 7KYKPMVQiUI | https://shikarno.com.ua/rozbory/php2shell-vrazlyvist-php/ |
| Еп.7–12, Еп.10 Short, Дайджест #1, резерви R1/R2 | див. eps/uploaded.json, reserve.json | статті ще немає — лише рядки «🌐» і «💬» |

Заодно: еп.1 — якщо назва досі «21 жовтня 2026 р.», поставити нормальну назву з eps/meta.py; categoryId 28.

## 2. Опис каналу YouTube
channels.list(part=brandingSettings, mine=true) → дописати в brandingSettings.channel.description рядок
«🌐 Сайт з розборами: https://shikarno.com.ua» → channels.update(part=brandingSettings) (решту полів зберегти).
Посилання в шапці каналу (Studio → Основна інформація → Посилання) API не змінює — це робить користувач.

## 3. Telegram @shikarno_ai_ua (бот @ShikarnoUABot)
- getChat(-1004419046740) → description; дописати «🌐 shikarno.com.ua — розбори з джерелами» (ліміт 255 знаків) → setChatDescription.
- pinned_message з getChat: якщо його автор — бот, editMessageText/editMessageCaption: додати рядок «🌐 Сайт: https://shikarno.com.ua». Якщо не бот — надіслати користувачу готовий текст.
- Знайти message_id постів з роликами еп.1, 2, 6 (логи tg.video / відповіді API) і повідомити їх: вони потрібні сайту для коментарів (front matter `telegram_post`).
- Далі в кожному пості про ролик — рядок «📖 Читати розбір на сайті» з посиланням на статтю (вже в RUNBOOK, крок 10).

## 4. Звіт
Коротко користувачу: які відео оновлено, що з каналом, нові описи Telegram, message_id для еп.1, 2, 6.

## 5. Оновити автопілот (ОБОВ'ЯЗКОВО)
Кожна публікація тепер іде в ТРИ місця: YouTube → стаття на сайті → пост у Telegram з посиланнями на статтю і відео.
- Замінити /home/claude/eps/RUNBOOK.md на актуальну версію з репозиторію:
  `curl -s https://raw.githubusercontent.com/manageitblog-pixel/shikarno-site/main/docs/RUNBOOK.md -o /home/claude/eps/RUNBOOK.md`
  (нові кроки: 8b — стаття на сайт; 10 — посилання «📖 Читати розбір на сайті» і telegram_post у статті; дайджест/розбір/місячний — стаття kind: dajdzhest/rozbir/misyats).
- Для пушу на сайт потрібен GitHub-токен «shikarno-site»: попросити в користувача і зберегти в /home/claude/gh/.token (у документи не писати).
  Клон: `git clone https://x-access-token:$(cat /home/claude/gh/.token)@github.com/manageitblog-pixel/shikarno-site.git`; правила статей — CLAUDE.md і docs/content-guide.md у репозиторії.
- Еп.10 (Short PHP2Shell, sSsYLWoaM4I): у описі дати посилання на https://shikarno.com.ua/rozbory/php2shell-vrazlyvist-php/.

## 6. Сайт: дописати ID відео й дайджест
- Статті еп.11 (content/posts/2026-10-24-claude-duet.md) і еп.12 (2026-10-24-walmart-vs-amazon-shi-agenty.md) вже в репо з датою виходу роликів — додати `youtube: <ID>` з eps/uploaded.json → push.
- Дайджест #1 (3PkeNHJyqdQ, 25.10 12:00): стаття kind: dajdzhest, number: 1, date: 2026-10-25T12:00:00+03:00, chapters з meta.json (link на статті сайту, де вони є) → push у суботу.
