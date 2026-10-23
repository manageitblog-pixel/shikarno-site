# Задача для Cowork (23.10): синхронізувати YouTube і Telegram із сайтом

Виконувати, коли закінчиш поточний рендер. Це легкі API-запити; заплановані ролики не чіпати (publishAt лишається).
Ключі: GitHub-токен «shikarno-site» — у приватному артефакті «Доступи ШІкарно» (посилання дасть користувач) → зберегти в /home/claude/gh/.token.
Репо: `git clone https://x-access-token:$(cat /home/claude/gh/.token)@github.com/manageitblog-pixel/shikarno-site.git`. Правила статей: CLAUDE.md, docs/content-guide.md.

## 1. Автопілот (першим ділом)
`curl -s https://raw.githubusercontent.com/manageitblog-pixel/shikarno-site/main/docs/RUNBOOK.md -o /home/claude/eps/RUNBOOK.md`
Новий крок 0 у RUNBOOK: на кожному запуску перевіряти docs/tasks/ і виконувати відкриті задачі.

## 2. Описи роликів YouTube
Для кожного відео: videos.list(part=snippet) → якщо в описі ще немає «shikarno.com.ua», дописати в кінець блок →
videos.update(part=snippet) з тими самими title, categoryId, tags, defaultLanguage (snippet надсилається повністю).
Потрібен scope youtube.force-ssl; якщо його немає — нове посилання авторизації (PKCE, redirect http://localhost, scope youtube.upload + youtube + youtube.force-ssl) користувачу.
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
| Еп.7 хакер з ШІ-агентами | ULBtAJDADhk | https://shikarno.com.ua/novyny/haker-shi-agenty-100-zlamiv/ |
| Еп.8 Gemini skills | cSrZ33nAKn4 | https://shikarno.com.ua/novyny/gemini-skills-zamist-gems/ |
| Еп.9 AI Edge Foresight | J3fkrWp64UE | https://shikarno.com.ua/novyny/google-ai-edge-foresight/ |
| Еп.10 Short PHP2Shell | sSsYLWoaM4I | https://shikarno.com.ua/rozbory/php2shell-vrazlyvist-php/ |
| Розбір #1 PHP2Shell | 7KYKPMVQiUI | https://shikarno.com.ua/rozbory/php2shell-vrazlyvist-php/ |
| Еп.11 Claude Duet | eps/uploaded.json | https://shikarno.com.ua/novyny/claude-duet/ |
| Еп.12 Walmart vs Amazon | eps/uploaded.json | https://shikarno.com.ua/novyny/walmart-vs-amazon-shi-agenty/ |
| Дайджест #1 | 3PkeNHJyqdQ | https://shikarno.com.ua/dajdzhest/dajdzhest-1/ (стаття з п.5) |
| Резерви R1/R2 | eps/reserve.json | без «📖» |
Еп.1: якщо назва досі «21 жовтня 2026 р.» — поставити нормальну з eps/meta.py; categoryId 28.

## 3. Опис каналу YouTube
channels.list(part=brandingSettings, mine=true) → дописати «🌐 Сайт з розборами: https://shikarno.com.ua» → channels.update (решту полів зберегти).

## 4. Telegram @shikarno_ai_ua (бот @ShikarnoUABot, chat -1004419046740)
- setChatDescription: дописати «🌐 shikarno.com.ua — розбори з джерелами» (≤255 знаків).
- Закріплене (getChat → pinned_message): якщо автор — бот, додати рядок «🌐 Сайт: https://shikarno.com.ua»; інакше — текст користувачу.
- message_id постів з роликами еп.1, 2, 6 (і всіх наступних) → у відповідні статті `telegram_post: <id>` → build → push (вмикає коментарі на сайті).

## 5. Сайт
- content/posts/2026-10-24-claude-duet.md і 2026-10-24-walmart-vs-amazon-shi-agenty.md: додати `youtube: <ID>`.
- Дайджест #1: content/posts/2026-10-25-dajdzhest-1.md — kind: dajdzhest, number: 1, slug: dajdzhest-1, date: 2026-10-25T12:00:00+03:00, youtube: 3PkeNHJyqdQ, duration, chapters з meta.json (link на статті сайту), summary = 5 головних новин, FAQ, джерела. До суботи ввечері — з'явиться сам о 12:00.
- `python3 build.py` без помилок → commit → push.

## 7. Оновити приватний артефакт «Доступи ШІкарно»
Посилання на артефакт — у повідомленні користувача (у репозиторій його і ключі НЕ писати: репо публічне).
Через Artifact tool (action "edit", url артефакту) заповнити рядки, які зараз «_вписати_», значеннями з твого середовища:
- Бот @ShikarnoUABot (канал) — токен з /home/claude/tg/.token;
- Gemini API key — з /home/claude/gem/.key;
- YouTube OAuth client — client_id і client_secret з /home/claude/yt/client_secret.json (сам файл не вставляти цілком); дата отримання поточного refresh token і коли він спливає (режим Testing — 7 днів);
- будь-які інші ключі чи ID, які є в тебе і яких немає в артефакті (Telegram-група, Threads тощо).
Після оновлення перевір, що таблиці не розламались (action "read"), і скажи користувачу, що додано.

## 6. Звіт користувачу
Що оновлено на YouTube і в Telegram, message_id постів, що на сайті. Після виконання — перенести цей файл у docs/tasks/done/.
