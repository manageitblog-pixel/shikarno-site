# Черга заливки 24.11.2026 — ep84 і ep86 (Shorts, «ШІ для професій» #10 і #11)

Підготував: продакшн Shorts, 23.11.2026 (activity 125). Сьогодні НЕ заливали — квоту YouTube 23.11 зарезервовано.
Обидва ролики — VARIANT в `exp-2026-11-22-frame0` (FRAME0=True) і CONTROL в `exp-2026-11-22-yt-related-cta`
(Related ставить власник у Studio; голосового заклику в останні 5 с немає). Шаблон той самий, що в ep82 (Generic.tsx не чіпали).

| | ep84_prof_logoped | ep86_prof_manikyur |
|---|---|---|
| Вихід (publish_at) | **2026-11-27T17:00:00Z** (пт, 19:00 Київ) | **2026-11-29T17:00:00Z** (нд, 19:00 Київ) |
| Відео | /home/claude/eps/ep84_prof_logoped/final.mp4 | /home/claude/eps/ep86_prof_manikyur/final.mp4 |
| Обкладинка (Thumb4, v4) | /home/claude/eps/ep84_prof_logoped/thumb.jpg | /home/claude/eps/ep86_prof_manikyur/thumb.jpg |
| TG / TikTok | …/ep84_prof_logoped/tg.mp4, tiktok.mp4 | …/ep86_prof_manikyur/tg.mp4, tiktok.mp4 |
| Плейлисти | prof tier | prof tier |
| Related (власник, Studio) | 6-2a9ncHaz4 (ШІ для професій #1) | 6-2a9ncHaz4 (ШІ для професій #1) |
| Стаття сайту (slug, має вийти разом з роликом) | /novyny/logopedychni-zanyattya-z-shi/ | /novyny/manikyur-i-shi/ |

Результати рендеру й перевірок — у розділі «QA 23.11» внизу.

## 1. Заливка — ОДНА команда (обидва ролики)

Скрипт ідемпотентний: slug, який уже є в eps/uploaded.json, пропускає; yt.upload сам відсікає дубль назви за 24 год.
Робить: upload (private + publishAt) → schedule → uploaded.json → finalize (обкладинка, плейлисти, теги, коментар у чергу,
thumb_test v4) → `ops.py exp add … frame0`. Має закінчитись `PASS` для кожного.

```bash
cd /home/user/shikarno-site && python3 - ep84_prof_logoped ep86_prof_manikyur <<'PY'
import sys, re, json, subprocess
sys.path[:0] = ["/home/claude/yt", "/home/claude/eps", "/home/user/shikarno-site/studio"]
import yt, meta
from util import update_json
doc = open("docs/research/upload-queue-2026-11-24.md", encoding="utf-8").read()
Q = json.loads(re.search(r"```json upload-meta\n(.*?)\n```", doc, re.S).group(1))
for slug in sys.argv[1:]:
    m = Q[slug]; up = json.load(open("/home/claude/eps/uploaded.json"))
    if slug in up: print(slug, "вже залито:", up[slug]); vid = up[slug]
    else:
        desc = m["description"] + meta.FOOT + "\n\n" + m["hashtags"]
        vid = yt.upload(f"/home/claude/eps/{slug}/final.mp4", m["title"], desc, m["tags"], privacy="private", category="28", publish_at=m["publish_at"])
        print(slug, vid, yt.schedule(vid, m["publish_at"]))
        update_json("/home/claude/eps/uploaded.json", lambda d: d.__setitem__(slug, vid), {})
    subprocess.run(["python3", "studio/yt/finalize.py", vid, *m["playlists"], "--thumb", f"/home/claude/eps/{slug}/thumb.jpg",
                    "--comment", m["comment"], "--at", m["publish_at"], "--style", "v4",
                    "--idea", {"ep84_prof_logoped": "3", "ep86_prof_manikyur": "21"}[slug]], check=False)  # 24.11 COO: прогноз у ideas.json
    subprocess.run(["python3", "studio/ops.py", "exp", "add", "exp-2026-11-22-frame0", slug, "--agent", "production"], check=False)
    print("RELATED (власник у Studio):", vid, "→", m["related"])
PY
```

Після команди: закомітити eps/uploaded.json, eps/thumb_test.json, eps/pending_comments.json (як зазвичай), записати vid
у claude/publishing-schedule.md і в цей файл (рядок «vid:»). Якщо finalize дав не PASS — повторити лише finalize:
`python3 studio/yt/finalize.py <vid> prof tier --thumb /home/claude/eps/<slug>/thumb.jpg --comment "<comment з JSON>" --at <publish_at> --style v4`.
Якщо обкладинка впала з 429 — за RUNBOOK: jpg власнику в бот для ручної заливки + `thumbs_push` щогодини.

## 2. Метадані (читає команда вище)

Факти — з ep84_factcheck*.md / ep86_factcheck*.md (обидва незалежні: 0 FAIL). Рекомендації фактчекерів враховано
(перевіряти картинки очима; «Free з меншими лімітами»; без «по всій Україні»). FOOT з eps/meta.py додається автоматично,
рядок Telegram — yt.with_tg.

```json upload-meta
{
 "ep84_prof_logoped": {
  "publish_at": "2026-11-27T17:00:00Z",
  "title": "Логопедичні заняття з ШІ: картки на Р, ігри, звіти | ШІ для професій #10 #ШІ #shorts",
  "description": "Логопедичні заняття з ШІ — тір-лист Байта для логопедів і батьків: де штучний інтелект справді допомагає, а де — ні.\n\n• Картки на звук Р — Gemini: опиши, що намалювати, і він згенерує картинки (базова генерація є й без підписки, з лімітами).\n• Гра на пам'ять — Gemini Canvas: попроси зробити квіз чи гру з картками.\n• Домашка — Claude: напише пам'ятку батькам простими словами.\n• Звіт — ChatGPT у тимчасовому чаті: розмова не потрапляє в історію й пам'ять і не йде на навчання моделей (OpenAI може зберігати копію до 30 днів для безпеки).\n• Вимова — найкраще живий логопед: ШІ не замінює фахівця й не ставить діагнозів.\n\nНе завантажуй у чат ім'я, діагноз, медичні документи чи записи голосу дитини. Картинки перевіряй очима — ШІ може помилитися з предметом чи буквою. Суб'єктивний рейтинг Байта; можливості — з офіційних довідок сервісів.\n\nДжерела:\n• Google, генерація зображень у Gemini: https://support.google.com/gemini/answer/14286560\n• Google, Canvas у Gemini: https://gemini.google/overview/canvas/\n• OpenAI, тимчасовий чат: https://help.openai.com/en/articles/8914046-temporary-chat-faq\n\nСтаття: https://shikarno.com.ua/novyny/logopedychni-zanyattya-z-shi/",
  "hashtags": "#shorts #ШІ #логопед #ШІдляпрофесій",
  "tags": ["логопедичні заняття", "логопед українською мовою", "логопед буква р", "вправи з логопедом", "вправи для букви р", "ШІ для логопеда", "Gemini", "Gemini Canvas", "Claude", "ChatGPT", "ШІ для професій", "ШІ", "штучний інтелект", "AI for speech therapy", "ШІкарно"],
  "playlists": ["prof", "tier"],
  "comment": "Логопеди, а ви вже пробували ШІ? Для чого — картки, ігри чи звіти? Пишіть, що працює, а що ні",
  "related": "6-2a9ncHaz4"
 },
 "ep86_prof_manikyur": {
  "publish_at": "2026-11-29T17:00:00Z",
  "title": "Манікюр і ШІ: дизайн нігтів, відповіді в директ, ціна | ШІ для професій #11 #ШІ #shorts",
  "description": "Манікюр і ШІ — тір-лист Байта для майстринь манікюру: де штучний інтелект економить час, а де — ні.\n\n• Дизайн нігтів — Gemini: опиши сукню чи настрій, і він намалює варіанти (генерація картинок є й без підписки, але з меншими лімітами).\n• Директ — Claude: напише ввічливі відповіді про ціну й запис, які можна зберегти шаблонами.\n• Ціна — ChatGPT: порахує собівартість процедури з твоїх цифр — гель, фрези, оренда.\n• Грибок чи зміна кольору нігтя — найкраще дерматолог: ні майстер, ні ШІ діагнозів не ставлять.\n\nНе вантаж у чат телефони, імена й фото рук чи обличчя клієнток без їхньої згоди. Цифри, які порахував ШІ, перевір сама. Суб'єктивний рейтинг Байта; можливості — з офіційних сторінок сервісів.\n\nДжерела:\n• Google, генерація зображень у Gemini: https://support.google.com/gemini/answer/14286560\n• Anthropic, тарифи Claude: https://claude.com/pricing\n• OpenAI, тарифи ChatGPT: https://chatgpt.com/pricing\n\nСтаття: https://shikarno.com.ua/novyny/manikyur-i-shi/",
  "hashtags": "#shorts #ШІ #манікюр #ШІдляпрофесій",
  "tags": ["манікюр", "дизайн нігтів", "манікюр для початківців", "майстер манікюру", "ШІ для майстра манікюру", "ціна на манікюр", "відповіді клієнтам в директ", "Gemini", "Claude", "ChatGPT", "ШІ для професій", "ШІ", "штучний інтелект", "AI nail design", "ШІкарно"],
  "playlists": ["prof", "tier"],
  "comment": "Майстрині, а ви вже пробували ШІ? Для чого — дизайн, директ чи ціни? Пишіть, що працює, а що ні",
  "related": "6-2a9ncHaz4"
 }
}
```

## 3. СИНХРОН (RUNBOOK) — у день виходу кожного ролика

Для ep84 — 27.11, для ep86 — 29.11 (усе до/о 17:00Z):

1. **Сайт** (до виходу): стаття `content/posts/2026-11-27-logopedychni-zanyattya-z-shi.md` /
   `content/posts/2026-11-29-manikyur-i-shi.md`, `kind: news`, `date: 2026-11-27T19:00:00+02:00` / `2026-11-29T19:00:00+02:00`,
   slug **саме такий, як у «Стаття:» опису**, `youtube: <vid>`, тір-лист таблицею, «Коротко», вердикт, FAQ ×3, джерела з
   фактчеку, теги з config.TAG_NAMES → `python3 build.py --future` без помилок → push (з'явиться сам у час виходу).
2. **Перевірка в момент виходу** (RUNBOOK, рядок про audit): `python3 -c "import sys;sys.path[:0]=['studio/yt','/home/claude/yt'];import audit,yt;v=yt.api('videos',part='snippet,status,contentDetails',id='<vid>')['items'][0];print(audit.check(v,audit.playlist_map(),None)['issues'])"` → порожньо (або лише C1 до post_comments).
3. **Telegram**: `tg.video` з /home/claude/eps/<slug>/tg.mp4, підпис у стилі блогу 600–950 знаків (емодзі + жирний
   заголовок; 2 абзаци суті; «💼 Кому корисно»; «🤖 Вердикт Байта: X/10»; «🔗 Джерело», «📖 Читати розбір на сайті»
   https://shikarno.com.ua/novyny/<slug>/, «▶️ Дивитись на YouTube») → message_id → `telegram_post: <id>` у статтю → build → push.
4. **TikTok** (vidIQ, у час виходу YouTube): `vidiq_social_account_list` → `vidiq_file_upload` /home/claude/eps/<slug>/tiktok.mp4
   (≤10 МБ) → `vidiq_social_post_draft_create` (підпис без фактів поза статтею + 3–5 хештегів; налаштування власника 22.11:
   публічно, коментарі так, Music Usage Confirmation, «створено ШІ» так) → `vidiq_social_post_publish` → запис у eps/tiktok.json
   `posted_auto` → посилання власнику в бот.
5. **Коментар-питання**: з pending_comments.json публікує `post_comments.py` після виходу (під запланованими не можна).
6. **Related video** 6-2a9ncHaz4 — власник у Studio (у звіті власнику: «Related video: <Short> → 6-2a9ncHaz4»).

## 4. Нагадування для main session (send_later — ставить головна сесія)

- 24.11 ~08:10Z (після скидання квоти): «Залити ep84 і ep86 однією командою з docs/research/upload-queue-2026-11-24.md §1; чекати PASS».
- 27.11 ~15:00Z: СИНХРОН ep84 (§3: стаття вже в main? TG, TikTok о 17:00Z, audit-перевірка).
- 29.11 ~15:00Z: СИНХРОН ep86 (так само).

## QA 23.11 (рендер і перевірки)

Озвучка — наявні vo.wav (QA KEEP, docs/research/voice-qa-2026-11-23.md), нових TTS-запитів не було.
`python3 eps/prep_ep.py ep84|ep86` → `eps/build.sh <slug>` (шаблон Ep/Generic.tsx без змін, як ep82; SERIES/KEYS/FRAME0=True зі сценарію).

| | ep84_prof_logoped | ep86_prof_manikyur | ep82 (еталон) |
|---|---|---|---|
| Тривалість final.mp4 | 29.73 с | 31.83 с | — |
| Формат | 1080×1920, 30 fps, h264 + aac 44.1 кГц | те саме | те саме |
| Гучність (EBU R128) | −12.1 LUFS, peak −0.3 dBFS | −11.5 LUFS, peak −0.4 dBFS | −11.3 LUFS, −0.4 dBFS |
| Розмір final / tg / tiktok | 19.5 / 3.2 / 7.5 МБ | 21.0 / 3.4 / 8.1 МБ | — |

Кадри (переглянуто):
- **0 с** — новий кадр 0 (FRAME0): шапка «ШІкарно · ШІ ДЛЯ ПРОФЕСІЙ #10/#11», хук у 2 рядки з жовтим акцентом
  («Твоя дитина не вимовляє *Р*?» / «Твої клієнтки хочуть *дизайн?*»), перший рядок тір-листа, Байт (judge), пігулки
  «картки на Р · ігри · звіти» / «дизайн · директ · ціна». Нічого не обрізано, без накладань.
- **1 с** — Байт пішов, субтитри «Твоя дитина не» / «Твої клієнтки хочуть», хук і шапка тримаються.
- **~80 %** — ep84 (23.8 с): повна таблиця 5×3, підсвічено «Вимова → Логопед», субтитр «не ставить.»; ep86 (25.5 с) —
  межа на аутро; додатково 24.5 с: повна таблиця 4×3, «Грибок → Дерматолог». Аутро (28.5 с) — те саме, що в ep82
  (Байт, лого, «Підписатись», 4 соцмережі, курсор — частина анімації шаблону).
- Підписи рядків ≤7 знаків влазять у колонку; «Диктофон», «Дерматолог», «Копіпаста» — у межах клітинок.

Обкладинки Thumb4 (v4, 1080×1920, c1 #7C5CFF / c2 #FF4F8B, логотипи Gemini/Claude/ChatGPT — як у ролику):
- ep84: серія «ШІ ДЛЯ ПРОФЕСІЙ #10», «Не каже *Р?*», ключі «картки на Р · ігри · звіти», Байт talk.
  (Перша версія «Не каже *Р*?» лишала «?» вдовою на окремому рядку → знак питання внесено в плашку.)
- ep86: серія «ШІ ДЛЯ ПРОФЕСІЙ #11», «Нігті під *сукню*», ключі «дизайн · директ · ціна», Байт happy.
- props: /home/claude/eps/<slug>/thumb.props.json; png + jpg поруч.

Висновок: обидва готові до заливки 24.11; ≤ 35 с, гучність на рівні ep82, кадр 0 відповідає варіанту exp-frame0.
