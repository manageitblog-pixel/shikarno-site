# Черга заливки 25.11.2026 — ep83 і ep85 (Shorts: «Moonlock — чесно» і «Тір-лист Байта #8»)

Підготував: продакшн Shorts, 24.11.2026. Сьогодні НЕ заливали — заливка 25.11 після скидання квоти YouTube (~08:00Z).
Обидва ролики — VARIANT в `exp-2026-11-22-frame0` (FRAME0=True) і VARIANT в `exp-2026-11-24-yt-related-cta-v2`
(голосовий заклик «…у відео під роликом» в outro Є, підтверджено ASR vo.wav 24.11; Related ставить власник у Studio).
Шаблон і кадр 0 — як у ep84/ep86 (Ep/Generic.tsx не чіпали). Озвучка — наявні vo.wav, нових TTS-запитів не було.
Результати рендеру й перевірок — у розділі «QA 24.11» внизу.

| | ep83_moonlock_chesno | ep85_tier_travel |
|---|---|---|
| Вихід (publish_at) | **2026-11-26T17:00:00Z** (чт, 19:00 Київ) | **2026-11-28T17:00:00Z** (сб, 19:00 Київ) |
| Відео | /home/claude/eps/ep83_moonlock_chesno/final.mp4 | /home/claude/eps/ep85_tier_travel/final.mp4 |
| Обкладинка (Thumb4, v4) | /home/claude/eps/ep83_moonlock_chesno/thumb.jpg | /home/claude/eps/ep85_tier_travel/thumb.jpg |
| TG / TikTok | …/ep83_moonlock_chesno/tg.mp4, tiktok.mp4 | …/ep85_tier_travel/tg.mp4, tiktok.mp4 |
| Плейлисти | sec (як ep77/ep78 — audit.playlist_map 24.11) | tier (як ep81/ep82) |
| Ідея (ideas.json) | 17 | 20 |
| Related (власник, Studio) | GNqU-wcz9Ws «Що ШІ знає про тебе» | M-KQwpDwpA4 (гайд #1 ChatGPT, вихід 25.11 17Z — до 28.11 перевірити, що public) |
| Стаття сайту | **нова** /novyny/moonlock-chy-varto-platyty/ (24.11, продовження ep77; наявну /novyny/moonlock-iphone-shakhrajski-sms/ НЕ чіпаємо) | нова /novyny/kudy-poikhaty-na-vykhidni-shi-tir-lyst/ (24.11) |

**vid:** — (заповнити після заливки)

**Статті сайту (написано 24.11, без `youtube:` — додати ПІСЛЯ заливки):**
- ep83 → `content/posts/2026-11-26-moonlock-chy-varto-platyty.md`, slug **moonlock-chy-varto-platyty** (date 2026-11-26T19:00:00+02:00)
- ep85 → `content/posts/2026-11-28-kudy-poikhaty-na-vykhidni-shi-tir-lyst.md`, slug **kudy-poikhaty-na-vykhidni-shi-tir-lyst** (date 2026-11-28T19:00:00+02:00)
- Після заливки: `youtube: <vid>` у front matter обох → `python3 build.py --future` → `python3 studio/ops.py backfill` → commit/push.
  Опис YouTube ep83 веде на стару статтю (ep77) — за бажанням замінити «Стаття:» на /novyny/moonlock-chy-varto-platyty/ (до заливки, у JSON нижче).

## 1. Заливка — ОДНА команда (обидва ролики)

Та сама, що 24.11 для ep84/ep86 (ідемпотентна: slug з eps/uploaded.json пропускає; yt.upload відсікає дубль назви за 24 год).
Робить: upload (private + publishAt) → schedule → uploaded.json → finalize (обкладинка, плейлисти, теги, коментар у чергу,
thumb_test v4, прогноз ідеї) → `ops.py exp add … frame0`. Має закінчитись `PASS` для кожного.
У `exp-2026-11-24-yt-related-cta-v2` обидва вже є у variant (youtube підтягнеться з publications); у `tg-specific-cta`
variant уже 5/5 — не додаємо (коментар у тому самому форматі, лише для однорідності).

```bash
cd /home/user/shikarno-site && python3 - ep83_moonlock_chesno ep85_tier_travel <<'PY'
import sys, re, json, subprocess
sys.path[:0] = ["/home/claude/yt", "/home/claude/eps", "/home/user/shikarno-site/studio"]
import yt, meta
from util import update_json
doc = open("docs/research/upload-queue-2026-11-25.md", encoding="utf-8").read()
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
                    "--comment", m["comment"], "--at", m["publish_at"], "--style", "v4", "--idea", m["idea"]], check=False)
    subprocess.run(["python3", "studio/ops.py", "exp", "add", "exp-2026-11-22-frame0", slug, "--agent", "production"], check=False)
    print("RELATED (власник у Studio):", vid, "→", m["related"])
PY
```

Після команди: закомітити eps/uploaded.json, eps/thumb_test.json, eps/pending_comments.json (як зазвичай), записати vid
у claude/publishing-schedule.md і в цей файл (рядок «vid:»). Якщо finalize дав не PASS — повторити лише finalize:
`python3 studio/yt/finalize.py <vid> <playlists> --thumb /home/claude/eps/<slug>/thumb.jpg --comment "<comment з JSON>" --at <publish_at> --style v4 --idea <idea>`.
Якщо обкладинка впала з 429 — за RUNBOOK: jpg власнику в бот для ручної заливки + `thumbs_push` щогодини.

## 2. Метадані (читає команда вище)

Факти — з ep83_factcheck*.md / ep85_factcheck*.md (незалежні: ep83 18 PASS, 0 FAIL, 1 UNVERIFIED-дрібне; ep85 11 PASS,
0 FAIL; CTA 22.11 — PASS обидва). Враховано рекомендації фактчекерів: ep83 — лише ціни App Store UA (інші плани — окремо,
з джерелом), «Junk» без неперевіреної локалізованої назви папки, «iOS 26 і новіше», застосунок не названо ШІ, «не реклама»;
ep85 — Карти в Gemini з увімкненою історією, 18+ лише для сторінки місця, офлайн-камера лише із завантаженою мовою,
режим розмови НЕ офлайн. Перший коментар ep85 у сценарії («Пиши місто — Байт складе топ») замінено форматом «А чи Б» —
так не лишається невиконаної обіцянки контенту. FOOT з eps/meta.py додається автоматично.

```json upload-meta
{
 "ep83_moonlock_chesno": {
  "publish_at": "2026-11-26T17:00:00Z",
  "title": "Шахрайські SMS на iPhone: Moonlock від MacPaw — чесно, чи варто? #shorts",
  "description": "Moonlock від київської MacPaw для iPhone — чесний огляд Байта: чи варто платити за захист від шахрайських SMS.\n\n• Плюси: Safe SMS (функцію треба ввімкнути) переносить схожі на шахрайські SMS від невідомих відправників у папку Junk — нічого не видаляється; Scam Detect перевіряє текст, скрін чи QR-код і пояснює, що не так.\n• Мінуси: у App Store Україна — 7 днів тріалу, далі $11.99/міс або $59.99/рік (на сайті MacPaw і в Setapp — інші плани); інтерфейс лише англійською; лише iPhone з iOS 26 і новіше.\n• Чи розпізнає українські SMS — MacPaw не пише.\n\nБезкоштовно: скинь скрін у ChatGPT, але спершу замаж своє ім'я, номер і дані картки. У банк дзвони сам — за номером на звороті картки.\n\nОцінка 6/10 — суб'єктивна думка Байта, не реклама.\n\nДжерела:\n• App Store Україна, Moonlock: https://apps.apple.com/ua/app/moonlock/id6799935865\n• MacPaw, анонс Moonlock для iPhone: https://macpaw.com/news/moonlock-iphone\n• MacRumors, інші тарифи: https://macrumors.com/2026/11/18/macpaw-moonlock-cybersecurity-app-iphone\n\nСтаття: https://shikarno.com.ua/novyny/moonlock-iphone-shakhrajski-sms/",
  "hashtags": "#shorts #шахраї #кібербезпека #iPhone",
  "tags": ["moonlock", "macpaw", "moonlock macpaw", "шахрайські смс", "шахрайські схеми", "шахраї", "як перевірити смс", "захист від шахраїв", "iphone", "безпека iPhone", "кібербезпека", "ChatGPT", "ШІкарно"],
  "playlists": ["sec"],
  "idea": "17",
  "comment": "Захист від шахрайських SMS: А — Moonlock за $60 на рік, Б — скрін у ChatGPT безкоштовно? Пиши А чи Б 👇\n🎁 50 промптів українською, PDF безкоштовно — у Telegram: t.me/shikarno_ai_ua/37",
  "related": "GNqU-wcz9Ws"
 },
 "ep85_tier_travel": {
  "publish_at": "2026-11-28T17:00:00Z",
  "title": "Куди поїхати на вихідні: який ШІ спланує поїздку? 🧳 Тір-лист Байта #8 #ШІ #shorts",
  "description": "Куди поїхати на вихідні і який ШІ допоможе спланувати поїздку — тір-лист Байта #8.\n\n• Місце — Gemini: бере з Google Карт адреси, рейтинги й години роботи (працює з увімкненою історією Gemini; сторінка місця з відгуками й фото — 18+, особистий акаунт).\n• План — Claude: попроси розписати день за днем таблицею.\n• Валіза — ChatGPT: через пошук (є й на безкоштовному плані) гляне погоду і складе чекліст речей.\n• Мова — Google Перекладач: наведи камеру на вивіску — без інтернету працює, якщо мову завантажено заздалегідь; з людьми — режим розмови (для української потрібен інтернет).\n\nСуб'єктивний рейтинг Байта; можливості — з офіційних довідок сервісів.\n\nДжерела:\n• Google, Карти в Gemini: https://support.google.com/gemini/answer/16622866\n• Google, історія Gemini і Карти: https://support.google.com/gemini/answer/13695044\n• OpenAI, пошук у ChatGPT: https://help.openai.com/en/articles/9237897-chatgpt-search\n• Google Перекладач, камера: https://support.google.com/translate/answer/6142483\n• Google Перекладач, розмова: https://support.google.com/translate/answer/6142474\n\nСтаття: https://shikarno.com.ua/novyny/kudy-poikhaty-na-vykhidni-shi-tir-lyst/",
  "hashtags": "#shorts #ШІ #подорожі #тірлист",
  "tags": ["куди поїхати на вихідні", "куди поїхати відпочивати", "куди поїхати в україні", "куди поїхати на вихідні в україні", "планування подорожі", "ШІ для подорожей", "Gemini", "Google Maps", "Claude", "ChatGPT", "Google Перекладач", "тір-лист ШІ", "ШІ", "штучний інтелект", "ШІкарно"],
  "playlists": ["tier"],
  "idea": "20",
  "comment": "Вихідні: А — план від Claude таблицею, Б — як вийде, навмання? Пиши А чи Б 👇\n🎁 Промпт «План подорожі» + ще 49, PDF безкоштовно — у Telegram: t.me/shikarno_ai_ua/37",
  "related": "M-KQwpDwpA4"
 }
}
```

## 3. СИНХРОН (RUNBOOK) — у день виходу кожного ролика

Для ep83 — 26.11, для ep85 — 28.11 (усе до/о 17:00Z):

1. **Сайт** (до виходу):
   - ep83: (змінено 24.11 головною сесією) окрема коротка стаття `content/posts/2026-11-26-moonlock-chy-varto-platyty.md`
     (кут «ціна/мінуси/6/10», посилання на ep77-статтю; ту сторінку НЕ змінювати) — лише додати `youtube: <vid>`.
   - ep85: стаття `content/posts/2026-11-28-kudy-poikhaty-na-vykhidni-shi-tir-lyst.md` уже написана 24.11 (slug = «Стаття:» опису)
     — лише додати `youtube: <vid>` → `python3 build.py --future` → `python3 studio/ops.py backfill` → push.
2. **Перевірка в момент виходу** (RUNBOOK, рядок про audit): `python3 -c "import sys;sys.path[:0]=['studio/yt','/home/claude/yt'];import audit,yt;v=yt.api('videos',part='snippet,status,contentDetails',id='<vid>')['items'][0];print(audit.check(v,audit.playlist_map(),None)['issues'])"` → порожньо (або лише C1 до post_comments).
3. **Telegram**: `tg.video` з /home/claude/eps/<slug>/tg.mp4, підпис у стилі блогу 600–950 знаків → message_id →
   `telegram_post: <id>` у статтю → build → push.
4. **TikTok** (vidIQ, у час виходу YouTube): /home/claude/eps/<slug>/tiktok.mp4 (≤10 МБ), підпис без фактів поза статтею +
   3–5 хештегів, рядок «промпт із ролика — у Telegram (посилання в біо)»; запис у eps/tiktok.json `posted_auto`.
5. **Коментар-питання**: з pending_comments.json публікує `post_comments.py` після виходу.
6. **Related video** — власник у Studio: ep83 → GNqU-wcz9Ws; ep85 → M-KQwpDwpA4. **ep85:** до 28.11 17Z перевірити через API,
   що M-KQwpDwpA4 public; якщо гайд не вийшов — запасна outro з ep85_factcheck_independent.md (потрібна переозвучка outro).

## 4. Нагадування для main session (send_later — ставить головна сесія)

- 25.11 ~08:10Z (після скидання квоти): «Залити ep83 і ep85 однією командою з docs/research/upload-queue-2026-11-25.md §1; чекати PASS».
- 26.11 ~15:00Z: СИНХРОН ep83 (§3).
- 28.11 ~15:00Z: СИНХРОН ep85 (§3; спершу — гайд #1 public?).

## QA 24.11 (рендер і перевірки)

Озвучка — наявні vo.wav (24.11: ep83 F0 135,1, ep85 F0 137,0), нових TTS-запитів не було.
`python3 eps/prep_ep.py ep83|ep85` → `eps/build.sh <slug>` (шаблон Ep/Generic.tsx без змін, як ep84/ep86; FRAME0=True,
KEYS зі сценарію, плашка серії — з thumb.props.json). tg.mp4: 720×1280 crf 26, aac 128k; tiktok.mp4: 1080×1920 crf 28, aac 128k.

**Перевірка озвучки (низький ASR-збіг ep83 0,494).** audit_vo.py + ковзні вікна ASR 2,5 с з кроком 1,25 с по всьому vo_raw.wav.
Низький збіг — артефакт ASR (склеює «ей-ем-ес → СМС», «відпідроликом», цифри словами → цифрами; сегмент 1 «0,235» —
через «Хове/Успам/QR-коти»). У вікнах чути **всі слова сценарію по порядку, без пропусків і повторів**: ep83 —
«…від київської МакПо обіцяє їх ловити. Чи варто?», «…і пояснює, що не так», «…тільки iOS 26…», «…а в банк дзвони сам»;
ep85 — «нотатки», «жести», «навіть офлайн, а з людьми — режим розмови», outro до «…під роликом». Найдовша пауза 0,49/0,51 с.
Одне застереження ep83 (не блокує): в outro «Що ШІ знає про тебе» ASR стабільно чує «Що **AI** знає» (у дублі take2 — «СІ»),
а спектр не показує другого «ш» після «що» → TTS, імовірно, прочитав «ШІ» як «ей-ай». Сенс і назва довгого не втрачені,
слово не пропущено; на екрані — «ШІ». Якщо головна сесія вважає це неприйнятним — переозвучити лише outro (1 TTS-запит).

| | ep83_moonlock_chesno | ep85_tier_travel | ep84 (еталон) |
|---|---|---|---|
| Тривалість final.mp4 | 32.63 с | 30.93 с | 29.73 с |
| Формат | 1080×1920, 30 fps, h264 + aac 44.1 кГц | те саме | те саме |
| Гучність (EBU R128) | −13.3 LUFS, peak −0.3 dBFS | −12.1 LUFS, peak −0.4 dBFS | −12.1 LUFS, −0.3 dBFS |
| A/V | аудіо final ↔ vo.wav зсув 0 мс (крос-кореляція); відео = аудіо за тривалістю | те саме | — |
| Розмір final / tg / tiktok | 18.7 / 3.0 / 5.5 МБ | 19.9 / 3.2 / 5.8 МБ | 19.5 / 3.2 / 7.5 МБ |

Кадри (переглянуто):
- **0 с** — новий кадр 0 (FRAME0): шапка «ШІкарно · ЗАХИСТ» / «ШІкарно · ТІР-ЛИСТ БАЙТА #8», хук («*Шахрайські SMS* на
  твоєму айфоні?» червоним — tone scam / «Куди поїдеш на *вихідні?*»), ep83 — іконка-щит з бейджем «ЧЕСНО» і Байт shock
  (Байт частково перекриває низ щита — так задумано компонуванням hookIcon + кадр 0), ep85 — перший рядок тір-листа і Байт judge;
  пігулки «Moonlock · $59.99/рік» / «місця · маршрут · валіза». Нічого не обрізано.
- **1 с** — Байт пішов у кут, субтитри «Шахрайські SMS лізуть» / «Куди поїдеш на», хук і шапка тримаються.
- **~80 %** — ep83 (26.1 с): вердикт 6/10, «+ Свої, київські, і ховає спам», «− Платно й лише англійською», «Спробуй тріал»,
  субтитр «а в банк»; ep85 (24.75 с) — межа тір-лист → outro; додатково 23.5 с: повна таблиця 4×3, підсвічено
  «Мова → Перекладач», субтитр «а з людьми». Додатково ep83 9 с / 18 с: «Ховає підозрілі SMS», «Перевіряє скрін і QR»;
  «$11.99/міс або $59.99/рік», «Лише англійською», «Тільки iOS 26+» — у межах карток. Аутро (30.5 / 27.5 с) — як у ep84.
- Текст на екрані ↔ фактчек: ціни лише App Store UA, «iOS 26+», застосунок не названо ШІ; ROWS ep85 = сценарій.
- Дрібниця шаблону (не блокує, як у попередніх): у підсвіченому субтитрі «перевіряє скрін» пробіл між словами вужчий.

Обкладинки Thumb4 (v4, 1080×1920, c1 #7C5CFF / c2 #FF4F8B):
- ep83: серія «ЗАХИСТ» (= плашка кадру 0), «SMS від *шахраїв?*», ключі «Moonlock · $59.99/рік», логотип Apple (платформа iPhone),
  Байт shock. (Перша версія «Шахрайські *SMS?*» не влазила по ширині → текст скорочено.)
- ep85: серія «ТІР-ЛИСТ БАЙТА #8», «Куди на *вихідні?*», ключі «місця · маршрут · валіза», логотипи Gemini/Claude/ChatGPT
  (як у ролику), Байт happy.
- props: /home/claude/eps/<slug>/thumb.props.json; png + jpg поруч.

Висновок: обидва готові до заливки 25.11 (QA PASS); ≤ 35 с, гучність на рівні ep84, кадр 0 відповідає варіанту exp-frame0.

**Outro ep83 («ШІ» → «ей-ай»), 24.11:** 1 TTS-запит (gemini-3.8-flash-tts Sadachbia, hype, текст для TTS «Що штучний інтелект знає
про тебе — у відео під роликом.») → F0 175,6 Гц (BAD: смуга 141,5±8; решта vo ~135, стара outro 107,9), ASR «Що ж, тучної інтелекти…»;
2-й запит (спокійніший стиль) — 429 (квота). Фрагмент НЕ підставлено: vo.wav/final/tg/tiktok ep83 без змін — заливаємо як є.
Невикористаний дубль: /home/claude/eps/ep83_moonlock_chesno/takes/outro_fix_take1.wav.
