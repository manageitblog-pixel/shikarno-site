# Переїзд конвеєра ШІкарно в цю сесію (інструкція для Claude)

Мета: одна сесія веде все — сайт (цей репозиторій, push працює), Shorts/дайджест/місячний (Remotion + Gemini TTS), YouTube, Telegram, пульт.

## 1. Розгорнути
```bash
bash studio/bootstrap.sh
```
Створює /home/claude/{rv,eps,tg,yt,gem,pdf} як симлінки на studio/, ставить numpy/soundfile/sherpa-onnx/playwright, whisper-small для звірки озвучки, ffmpeg, npm ci для Remotion. Усі скрипти розраховані на шляхи /home/claude/... — нічого не переписувати.

## 2. Секрети (НЕ в репозиторій — він публічний)
Відкрий приватний артефакт власника «Доступи ШІкарно» https://claude.ai/artifact/4gHKdHWPS6jDMuY2RygU7x (Artifact read) і запиши:
- `/home/claude/tg/.token` — токен @ShikarnoUABot (рядок)
- `/home/claude/gem/.key` — Gemini API key (рядок)
- `/home/claude/yt/client_secret.json` — `{"installed":{"client_id":"…","client_secret":"…","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","redirect_uris":["http://localhost"]}}`
- `/home/claude/yt/token.json` — `{"refresh_token":"…","access_token":"","expires_in":0,"obtained":0}` (refresh token — у тому ж артефакті, рядок «YouTube refresh token»)
- `/home/claude/tg/owner.json` — `{"chat_id":133254760,"confirmed":true}` — власник підтверджений 27.10 (133254760 = @ybm_ua), записати одразу. tg/offset.txt не переносити: перший inbox.py забере лише нові повідомлення.
Перевірка: `python3 -c "import sys;sys.path.insert(0,'/home/claude/yt');import yt;yt.recent(3)"` і `python3 /home/claude/tg/inbox.py`.

## 3. Пробний рендер
`cd /home/claude && python3 eps/prep_ep.py ep15` (озвучка вже є лише в старій сесії — для проби зроби новий Short за RUNBOOK, 1 запит Gemini). Якщо Remotion не знаходить браузер: `export REMOTION_BROWSER=$(find / -name headless_shell -type f 2>/dev/null | head -1)`.

## 4. Стан і правила
- Інструкція автопілота: docs/RUNBOOK.md (джерело правди), плейбук: docs/youtube-playbook.md.
- Стан: studio/eps/uploaded.json, reserve.json (10 у запасі), tiktok.json (що викладено в TikTok), experiments.json (тест довжини 26.10–8.11), comments.json, publishing-schedule.md.
- Пульт власника: https://claude.ai/artifact/QGsgcJGTSM3gFS61nJXYJz (ArtifactData: tasks, questions, meta/status, meta/log). Якщо інструмента ArtifactData у сесії немає — скажи власнику.
- Документ стратегії: https://claude.ai/artifact/WJk2PoUoZBVxn84z2kRVYr ; матеріали «ШІ за жовтень»: studio/eps/month_oct/research.md (вихід 2.11 19:00 Київ, озвучка 29–31.10).
- Після кожного запуску: git add studio/eps/*.json studio/eps/*.py docs content && commit && push (стан конвеєра живе в репозиторії, контейнер може бути перезапущений).

## 5. Розклад (перехоплення від старої сесії)
Стара сесія веде автопілот до переїзду і ставить собі запуски «ШІкарно: ранок/вечір <дата>» (send_later). Після кроків 1–4: list_triggers → видалити/вимкнути майбутні одноразові «ШІкарно: …», що належать старій сесії (вони прийдуть не сюди). Звірити останній стан: yt.recent(5), що вже заплановано на сьогодні. Потім поставити собі send_later на найближчий 07:10Z з текстом «Автопілот ШІкарно <дата>: виконай docs/RUNBOOK.md за днем тижня» і далі щодня ланцюжком (ранок 07:10Z + вечір 17:05Z). Повідомити власнику в бот: «Переїзд завершено».

## Обмеження
- TikTok/Reels: автопублікація недоступна (API TikTok без аудиту — лише приватні пости при приватному акаунті; інструменти «для своїх акаунтів» аудит не проходять). Робочий шлях: щодня надсилати власнику в @ShikarnoUABot відео + підпис, він викладає вручну.
- Не синтезувати голоси й образи реальних людей; Semrush не використовувати; секрети тільки в /home/claude/* і в «Доступах».
