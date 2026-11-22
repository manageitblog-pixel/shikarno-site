# P0 Autonomous Operations Plan: «ШІкарно» (22.11.2026)

Режим: лише читання. Жодного файлу в репозиторії й у /home/claude не змінено. Нічого не опубліковано, задачі планувальника, промпти, дозволи й конфіги не чіпав. Значень секретів не виводив.
База: `docs/org/system-2026-11-22.md` (далі **AUDIT**) і звірка з кодом робочої копії `HEAD = c7aa4cb` (після `fbdef44`/`e420371`).

**Позначки.** **[К]** підтверджено кодом або даними (файл:рядок). **[П]** підтверджено документацією або промптами (RUNBOOK, AUDIT §6), не кодом. **[?]** ймовірно, перевірити до реалізації. **[—]** відсутнє в коді.

**Що змінилось у коді відносно AUDIT** (перевірено сьогодні):
- `pending_comments.json` для `Rlm1u-I6x00` (ep78) уже має `at=2026-11-25T17:00:00Z`, тож AUDIT §11 п.7 закрито [К дані].
- `hq_data.py:78–80` уже бере `analytics_db.long_hours_12m()`, хардкоду `10.1` немає. AUDIT §11 п.12 застарів [К].
- Нові знахідки, яких AUDIT не мав: див. §13, пункти R1–R6. Головна з них: `POST /api/purge` пульта видаляє журнал подій тим самим `INGEST_TOKEN`, який лежить у контейнері (`pult/worker.js:21–24, 137–141`) [К]. Отже, агент може стерти власний audit log.

---

## 1. Executive summary

1. Зараз автономія тримається на дисципліні промптів. Детермінованого «судді» між рішенням LLM і зовнішньою дією в коді немає [—]. `finalize.py` перевіряє лише упаковку (`finalize.py:40–43`) [К]. Фактчек код не перевіряє [—].
2. Пропоную додати один **Policy Engine**: модуль `studio/policy.py` і конфіг `studio/policy.json` у git. Він повертає `ALLOW | BLOCK | RETRY_LATER | CANARY | DEGRADE | SAFE_MODE`. LLM лише пропонує дію. Виконують її наявні функції (`yt.upload`, `yt.schedule`, `yt.comment`, `tg.video`, `post_comments.py`, `audit.fix`), і кожна з них першим рядком питає policy.
3. Стан і журнал зберігаються в одному новому SQLite-файлі `studio/data/ops.sqlite`, окремо від даталейку, бо `lake.py sql` виконує довільний SQL, а `lake.ai_share` робить `drop table` (`lake.py:242, 323–324`) [К]. Таблиці: `publications` (стан за платформами), `pub_events`, `agent_decisions`, `runs`, `experiments`, `breaker`. Таблиці журналу append-only: тригери SQLite забороняють UPDATE і DELETE, а кожен рядок має хеш-ланцюжок.
4. **Копія журналу поза контейнером.** Хеш кожного рішення йде на пульт (Cloudflare DO) наявним `/api/ingest` [К worker.js:155–176]. `/api/purge` треба вимкнути або перевести на окремий секрет, якого в контейнері немає.
5. **Publication gate** складається з 20 машинних перевірок: content_id, ланцюжок idea→script→video, `Вердикт: PASS`, ліміт UNVERIFIED, першоджерела й домени, ASR, F0, рендер, тиша в аудіо, обкладинка, тривалість, дублікати, схожість, ліміти, розклад, бюджет квоти, високоризикові теми, canary, наявність rollback. Без `ALLOW` або `CANARY` код не робить зовнішнього виклику.
6. **Ідемпотентність.** Перед кожною публічною дією записуємо intent (`state=uploading/posting`, idempotency_key). Після дії записуємо результат. Якщо після збою запис лишився «в польоті», запускається **reconcile**, а не повтор. Для YouTube є точний спосіб: статус resumable-сесії (`PUT Content-Range: bytes */N`). Цей прийом уже використовує `vidiq_put.sh:11–13` [К].
7. **Rollback без людини:** YouTube → `private` (видаляти заборонено, RUNBOOK:11) [П]; коментар → `comments.delete`; TG → `deleteMessage`/`editMessageCaption`; сайт → `git revert` + Pages; IndexNow → повторний ping. TikTok через vidIQ, ймовірно, не має API видалення [?]. Тому TikTok іде **останнім**, після canary-вікна YouTube.
8. **Зміни стратегії, форматів і промптів** (рівень D) проходять лише через `experiments`: гіпотеза, обмежений rollout, поріг, promote/pause/rollback. growth-loop більше не може сам «прибрати нижні 20%» (SKILL.md:6) без закритого експерименту.
9. **Circuit breaker** має 14 тригерів, стан зберігається в `breaker` і в `kv.state` пульта. У `SAFE_MODE` блокуються всі дії рівнів C і D, а A і B працюють далі. Відновлення автоматичне: cooldown, кілька успішних probe, потім вихід.
10. **Heartbeat ззовні.** У воркер пульта додається `scheduled()` (той самий патерн уже є в `bait/worker.js:79`) [К]. Якщо подій немає довше 3 год або Short о 17:00Z не став public, власнику йде **повідомлення**, а DO-прапорець `safe_mode` вмикається. Це сповіщення, а не approval.
11. **Межі виконання.** У `.claude/settings.json` є PreToolUse-хук на всі інструменти (`settings.json`, `hook.py`) [К], але він нічого не блокує, бо робить `fork` і `exit 0` (`hook.py:53–60`) [К]. Мінімальна зміна: синхронний виклик `policy.py check-tool` до `fork`, а `exit 2` блокує. Так закриваються E-дії: правка дозволів, хуків, policy, видалення журналу, власні доступи. Також обмежуються D-дії: `update_trigger`, `delete_trigger`, `vidiq_social_post_publish`.
12. **Чесна межа.** Усе, що живе в тому самому контейнері й репо з правом push, агент технічно може обійти: `sed` по hook.py, push у main. Справжня зовнішня межа — захист гілки або CODEOWNERS на `studio/policy*`, `.claude/**`, `studio/pult/hook.py`, а також перевірка хешів цих файлів воркером. Це одноразове налаштування, а не щоденне погодження (питання Q1 у §14).
13. **Ще одна людська залежність.** OAuth у Testing треба оновлювати щотижня кліком власника. Наступне закінчення — 25.11 ~10:31Z (`token.json.refreshed_at` + 7 днів) [К поля]. Повної автономії з Testing не буде, тож потрібен перехід у «In production» (Q2).
14. **Порядок:** (1) `ops.sqlite` і журнал, без впливу на роботу; (2) policy у **shadow mode**: лише лог, нічого не блокує; (3) enforce у `yt.*`/`tg.*`/`post_comments`/`audit --fix`; (4) хук-enforcement для MCP і файлів; (5) breaker, watchdog і щоденний звіт; (6) experiments. Enforce вмикати **не раніше вечора 25.11**: після ep81 (23.11), ep82 (24.11), ep78 і гайда #1 (25.11 17Z) та оновлення OAuth.
15. **ep78 і ep81 уже залиті й заплановані** (`uploaded.json`: `Rlm1u-I6x00`, `xaYHobFNYHo`) [К]. Gate на `upload` їх не зачепить. Зачепити може post-publish гейт (TG, TikTok, коментар) і повторний `schedule()`. Тому потрібен `legacy`-список із записом в `agent_decisions`. У ep78 немає фактчек-файлу [К фс], у ep81 є `Вердикт: PASS` [К].
16. **Студійні скрипти працюють з робочої копії.** `/home/claude/{yt,tg,eps,pult}` — це симлінки на `studio/` [К ls -la]. Зміни в Python діють одразу, без деплою. GitHub Pages деплоїть лише сайт. Деплою потребують зміни воркера (`pult.yml`) і нові workflow.

---

## 2. Autonomy matrix

Поточний рівень у таблиці — фактичний: що агент може зробити сьогодні без жодної машинної перевірки. Цільовий рівень — A…E з брифу.

### 2.1 Агенти й задачі планувальника (AUDIT §5–6) [П]

| Дія / агент | Поточний | Цільовий | Чому | Guardrails | Rollback |
|---|---|---|---|---|---|
| Головна сесія (оркестратор, auto) | без меж: Bash, Edit, Agent, trigger-tools, vidIQ | A–C через policy; D через experiments; E заборонено | одна сесія виконує всі ролі, тож межі мають бути на рівні дій, а не ролей | хук `check-tool`, policy у всіх `yt.*`/`tg.*`, breaker | за типом дії (§6) |
| Перевірка бота (`49 * * * *` Київ) | відповідає власнику, **видаляє спам у групі** | A (читання, відповіді) + D (видалення) | видалення необоротне | `delete_policy`: ≤5/добу, лише за правилами спаму, повідомлення спершу зберігається | неможливий → compensation: лог і копія тексту |
| Диспетчер (`17 * * * *` Київ) | запускає субагентів, push у 2 гілки | A/B; push = C | естафета може зациклитись | `runs`: ≤4 субагенти на годину кодом, loop-breaker (§9 T12), push лише в main | `git revert` |
| Збирач даталейку (`52 */4`) | SQLite, ideas, **approve при балі ≥300** | A (збір) + B (approve) | approve керує виробництвом | approve = рішення в `agent_decisions` з балом і порогом із policy.json | `ideas.py set status=new` |
| Радар + редколегія (`43 6 * * *`) | тема дня + **`audit.py --fix` по всіх відео** | A (тема) + D (`--fix`) | масові правки опублікованого | `bulk_edit_policy` (§3.13): ≤14 днів, ≤10 відео за запуск, знімок «до» | `_put` старого snippet із журналу |
| Telegram/Community (`41 8` Київ) | пости, модерація | C (пости) + D (видалення) | публічні дії | budget ≤2 пости/добу, дедуп за content_id | deleteMessage або edit (§6) |
| SEO-відділ (`13 12` Київ) | **нові назви й теги відео ≤14 днів**, статті, push | B (чернетки) + D (правка метаданих) + C (push) | зміна назви ламає дедуп за назвою (`yt.py:83`) | `bulk_edit_policy`, ≤3 назви/добу, лише в межах experiment | старий snippet із журналу |
| Дизайн-відділ (`7 15` Київ) | **заміна обкладинок** | B (генерація) + C (`thumbnails.set` нових) + D (заміна старих) | ліміт обкладинок API (RUNBOOK) [П] | лише відео ≤48 год або A/B-експеримент; квота | попередній thumb із журналу (jpg зберігається) |
| COO (`27 9,20` Київ) | **update_trigger/delete_trigger** | A (звіт) + D (тригери лише через policy) | агент змінює правила гри | `trigger_policy` (§3.14), снапшот старого промпту | `update_trigger` зі старим промптом |
| CSO (пн 11:19) | strategy.md | A (аналіз) + D (стратегія лише як experiment) | суперечність із growth-loop (AUDIT §11 п.6) | `experiments` | `git revert` strategy.md |
| Growth loop (нд 11:13, SKILL) | **сам прибирає 20% форматів у RUNBOOK** | A (звіт) + D (через experiment) | щотижневий хаос форматів | лише закритий експеримент змінює частки | revert рядка RUNBOOK + `experiments.rollback_ref` |
| Конкуренти (пн 10:37) | comp, ideas | A | читання | квота search ≤N/добу | — |
| Довгі відео (пн, сб 09:23) | увесь конвеєр до публікації | B → C | — | повний gate | §6 |
| Разові нагадування «вийшов» (17:04Z) | коментар, TG, TikTok, стаття | C | основна точка дублів (AUDIT §6: «повторний запуск може запостити вдруге» [—]) | state machine + idempotency | §6 |
| Незалежний фактчекер (субагент) | пише md | B | вихід — вхід gate | обов'язковий рядок `Вердикт:` і статуси рядків | — |
| Нагадування токена (25.11 08:00Z) | лінк власнику | A | — | OAuth-монітор (§9 T4) | — |

### 2.2 Скрипти й зовнішні дії [К]

| Дія / скрипт | Поточний | Цільовий | Чому | Guardrails | Rollback |
|---|---|---|---|---|---|
| `lake.py news/ingest/niche/comp/history` | A | A | читання + власна БД | rate (квота search 100 од., `yt.py:11`) | — |
| `lake.py sql "<будь-що>"` (`lake.py:323–324`) | без меж (DDL проходить) [К; автокоміт DDL — ?] | A (лише SELECT) | можна видалити таблиці | `sql` відкриває `mode=ro` | знімок `snapshot/` |
| `analytics_db.sync`, `hq_data.py`, `kw.py`, `outliers.py`, `ideas.py add/board` | A | A | — | — | — |
| `ideas.py set status=approved` | без меж | B | керує виробництвом | лог рішення | set назад |
| `gen_full.py` → `gtts.tts` (Gemini TTS) | без меж | B + budget | ~10 запитів/добу (RUNBOOK:77) [П] | `budget.tts_per_day=10` | кеш дублів (gen_full:52) |
| `voice_check.py` (exit 1 при BAD, `voice_check.py:17`) | B | B | — | вхід gate | — |
| `audit_vo.py` (лише друк, вердикту немає) [К] | B | B | gate потребує числа | `--json` з word-match по сегментах | — |
| `build.sh` (Remotion + ffmpeg, `set -e`) | B | B | — | gate: ffprobe, тиша | перерендер |
| `remotion still` / `thumb.jpg` | B | B | — | gate: є, ≤2 МБ [?ліміт YouTube] | — |
| `yt.upload` (`yt.py:56–72`) | C без бюджету; дедуп лише за точною назвою за 24 год; при збої перевірки **заливає далі** (`yt.py:79`) | C | необоротно (видаляти заборонено) | повний gate + state machine; при збої перевірки дублів `RETRY_LATER`, а не upload | `privacyStatus=private` |
| `yt.schedule` (`yt.py:96–99`) | без меж | C | саме тут резерв стає публічним | той самий gate (`upload_reserve.py` заливає без дати) | `schedule` → private без publishAt |
| `yt.comment` (`yt.py:106–109`) | C; `_req` **повторює POST на 5xx** (`yt.py:31–32`) → можливий дубль [К] | C | — | tries=1 + reconcile | `comments.delete` |
| `yt.add_to_playlist` (`yt.py:113–121`) | без перевірки наявності; POST з ретраями [К] | C | дублі в плейлисті | перевірка `playlistItems` перед вставкою (як `finalize.py:28–31`) | `playlistItems.delete` |
| `yt.set_category`, `yt._put videos` | без меж | D (для відео старших за 48 год) | — | `bulk_edit_policy` | старий snippet |
| `finalize.py` | C (thumb, playlist, fix, pending_comments) | C | — | policy перед кожною дією; PASS іде в `publications` | — |
| `thumb.py` (без timeout і retry, `thumb.py:5–7`) | C | C | — | перевести на `yt._req` | попередній jpg |
| `post_comments.py` | C; помилка → `ERR`, запис лишається, ретрай щоразу | C | — | state machine, max_attempts=3, далі `failed` | `comments.delete` |
| `audit.py --fix` (`audit.py:176–183`) | D-дія без меж: **усі** відео | D | масова незворотна правка | §3.13 | §6.6 |
| `tg.post` / `tg.video` (`tg.py:17–18`); `tg.call` повертає JSON помилки, а не виняток (`tg.py:7`) [К] | C | C | — | state machine, `ok` перевіряється кодом | `deleteMessage` / edit |
| `tg.call('deleteMessage')` у групі | без меж [П] | D | необоротно | §2.1 | compensation |
| `tg.owner_video` | A (лише власнику) | A | — | — | — |
| vidIQ MCP `vidiq_social_post_publish` | без меж у режимі auto [?] | C (останній у ланцюжку) | rollback, ймовірно, неможливий [?] | хук `check-tool` + gate + canary-вікно | compensation (§6) |
| `vidiq_put.sh` | B | B | — | — | — |
| `git push main` → Pages + IndexNow (`pages.yml`) | C, 2 гілки, `pull --no-rebase` [П] | C | публічно | лише main; ≤N статей/добу; збірка `build.py` локально перед push | `git revert` + push |
| `tools/indexnow.py` (job у CI) | C | C | — | лише URL зі статусом 200 у `dist/` | повторний ping після revert |
| `auth.py code` через `watch.py` (будь-яке повідомлення власника з `localhost`+`code=`) | A | A | — | — | — |
| `update_trigger` / `delete_trigger` / `create_trigger` (cron) | без меж [П] | D | правила гри | §3.14 | старий промпт |
| `send_later` (one-shot) | без меж | C | потрібне для нагадувань «вийшов» | ≤10 активних, без дублю на content_id | `delete_trigger` (лише one-shot) |
| Правка `.claude/settings*.json`, `.claude/agents/**`, `studio/pult/hook.py`, `studio/policy*` | без меж [К: deny-правил немає] | **E** | самонадання доступів | хук deny + CODEOWNERS (Q1) + перевірка хешів | — |
| `POST /api/purge` пульта (`worker.js:137–141`) | без меж (той самий токен) [К] | **E** | видалення audit log | вимкнути або окремий секрет поза контейнером | — |
| Видалення або UPDATE `agent_decisions` | — | **E** | immutable | SQLite-тригери + хеш-ланцюжок + DO-копія | — |
| Зміна `policy.json` (бюджети, пороги) | — | E для ручної правки агентом; D лише через `experiments.promote` для дозволених ключів | необмежений бюджет = E | whitelist ключів, верхні межі зашиті в коді | git revert |
| Агенти: правка RUNBOOK, strategy.md, SKILL.md | без меж | D (через experiment) | «покращувати власні правила» має бути контрольовано | diff-бюджет ≤40 рядків/добу, рядок у `agent_decisions` | git revert |

---

## 3. Policy Engine spec

### 3.1 Загальна будова (мінімальна)
- `studio/policy.py` — чисті функції без мережі: `evaluate(action:dict) -> Decision`. CLI: `python3 studio/policy.py check <action.json>`, `check-tool` (stdin з хука), `replay <decision_id>`, `status`.
- `studio/policy.json` — пороги й бюджети з полем `version`. Рішення зберігає `policy_version = sha256(policy.json)[:12]` і `code_version = git rev-parse HEAD`.
- **Вхід `action`:** `{type: youtube_upload|youtube_schedule|youtube_comment|playlist_add|tg_post|tg_video|tg_delete|tiktok_publish|site_push|indexnow|meta_edit|thumb_set|trigger_update|trigger_delete|trigger_create|file_edit|strategy_change, content_id, platform, payload_digest, actor, run_id, experiment_id?}`.
- **Збір фактів** (`collect(action)`) виконує код, а не LLM: читає файли `eps/<slug>/`, факт-md, `uploaded.json`, `ops.sqlite`, `quota.log`, `meta.py`. Результат — `facts` (JSON). Обидва (`facts` + `action`) пишуться в `agent_decisions.input_snapshot`, тож `replay` дає той самий результат без мережі.
- **Порядок політик** (перша сильніша перемагає): `circuit_breaker` → `hard_deny` → `budget` → `rate_limit` → `duplicate` → `fact` → `source_credibility` → `quality` → `high_risk` → `schedule_conflict` → `canary` → `rollback` → `publication`. Сила: `SAFE_MODE > BLOCK > RETRY_LATER > DEGRADE > CANARY > ALLOW`.
- **Семантика результатів:**
  - `ALLOW` — виконати.
  - `BLOCK` — не виконувати. Контент лишається `validated=false`, задача повертається автору (наявне правило «назад автору» [П]).
  - `RETRY_LATER(until)` — тимчасова причина: квота, розклад, обробка YouTube.
  - `CANARY(scope)` — виконати в обмеженому обсязі: одна платформа, без TikTok і TG до кінця вікна.
  - `DEGRADE(mode)` — виконати безпечну підмножину: YouTube scheduled, але без TG і TikTok; або private-резерв замість publishAt.
  - `SAFE_MODE` — увімкнути breaker і заблокувати C і D.
- **Збереження:** кожен виклик `evaluate` додає рядок в `agent_decisions` (`decision_type='policy'`, `policy_result`, `rules_triggered`). Помилка самого policy → `BLOCK` для C/D (fail-closed) і `ALLOW` для A/B (fail-open).
- **Shadow mode:** `policy.json.mode = "shadow" | "enforce"`. У shadow кожна політика логується, але виконання не блокується. Це дає 3–5 днів порівняння «що policy сказав vs що сталося».

Нижче кожна політика: input → rules → thresholds (дефолти в `policy.json`, остаточні значення — §14) → output. Для всіх однаково: **де зберігається** — `ops.sqlite.agent_decisions` (+ `publications.policy_decision_id`); **як логується** — рядок із `rules_triggered=[{rule, value, threshold, verdict}]`, хеш у DO пульта; **як відтворити** — `policy.py replay <decision_id>` бере `input_snapshot` і `policy_version` (стару версію policy.json з git за `code_version`) і має отримати той самий `policy_result`. Інакше це тест-фейл (§12).

### 3.2 Publication policy
- **Input:** `action.type ∈ {youtube_*, tg_*, tiktok_publish, site_push, indexnow}`, стан `publications`, результати інших політик.
- **Rules:** (1) усі обов'язкові перевірки gate (§4) мають статус; (2) переходи лише за state machine (§5); (3) порядок платформ: `youtube.scheduled` → (на publishAt) `youtube.published` → `website` → `telegram` → `tiktok` (останній, бо rollback неможливий [?]); (4) немає `publish` без `policy_decision_id` зі статусом ALLOW або CANARY не старшим за 24 год і з тим самим `payload_digest`.
- **Thresholds:** `max_decision_age_h=24`; `tiktok_after_youtube_public_min=60` (canary-вікно; див. Q7, бо RUNBOOK:71 вимагає «у час виходу YouTube» [П]).
- **Output:** агрегат усіх політик.

### 3.3 Quality policy
- **Input:** ffprobe `final.mp4` (тривалість, наявність a/v-стріму, роздільність); `ffmpeg -af volumedetect,silencedetect`; exit-код `voice_check.py`; JSON `audit_vo.py --json` (нове поле); `thumb.jpg`; `audit.check` (для YouTube після заливки).
- **Rules / thresholds:**
  - Short: `duration ≤ 60 с` для політики каналу. Ціль ≤35 с — це `DEGRADE` → канарка, а не BLOCK. Технічна межа `audit.py:93` — ≤180 с [К].
  - Long: `≥ 360 с`.
  - Відео: `1080×1920` для Short, `1920×1080` для довгих.
  - `mean_volume > −35 dB`, жодної тиші `silencedetect -50dB` довше 1,5 с поза останньою секундою. Зараз такої перевірки немає [—].
  - F0 `143±8 Гц` (`voice_check.py:4`) [К].
  - ASR: word-match кожного сегмента ≥0,90 і загальний ≥0,95.
  - `thumb.jpg` існує, <2 МБ [?ліміт], не порожній.
  - `finalize` PASS (`finalize.py:42`) — для переходу `uploaded → scheduled`.
- **Output:** ALLOW. Будь-яка жорстка вада → BLOCK. Лише м'які (тривалість вище цілі) → DEGRADE(no_tiktok) або CANARY.

### 3.4 Fact policy
- **Input:** `eps/<key>_factcheck_independent.md`. Ключ: спершу `<slug>`, потім `slug.split('_')[0]`, бо файли звуться `ep82_…`, а slug — `ep82_tier_kitchen` [К]. Для кліпів `cut6_*` — ключ батьківського випуску з `publications.parent_content_id`.
- **Rules:**
  1. Файл існує, і його автор не автор сценарію (суфікс `_independent`). Самоперевірка `epNN_factcheck.md` не рахується [К: guide1/guide2 самоперевірки, рядок 4].
  2. Є рядок `^Вердикт:\s*(PASS|FAIL)$`. **Зараз він є лише у 2 з 8 файлів** (ep81_independent:26, ep82_independent:22) [К]. Інші (guide1/2 independent) вердикту в машинному форматі не мають.
  3. Рядки таблиці зі статусом `FAIL` = 0. Згадки «не FAIL» у прозі не рахуються: парсимо лише третю колонку таблиці.
  4. `UNVERIFIED` без уточнення = 0. `UNVERIFIED (не заявлено)` (твердження в ролик не потрапило) ≤ `max_unverified_not_claimed=2` (ep82 має рівно 2 [К]). Остаточний поріг — Q3.
  5. Факт-файл свіжий: у ньому записано `sha256` сценарію `epNN.py` і meta-запису, і він збігається з поточними. Зараз хешу у файлах немає [—], тому до міграції — `mtime(factcheck) ≥ mtime(epNN.py)` як DEGRADE-перевірка.
  6. Кожне твердження зі статусом PASS має URL (колонка 2 не «—»). Виняток — рядки з позначкою `(думка)` або `n/a`.
- **Thresholds:** `max_fail=0`, `max_unverified_plain=0`, `max_unverified_not_claimed=2`, `repeat_unverified_breaker=3` (3 випуски поспіль з UNVERIFIED → T8 у §9).
- **Output:** PASS → ALLOW. Немає файлу або FAIL → BLOCK. Застарілий файл → RETRY_LATER (перезапустити фактчекера).

### 3.5 Duplicate policy
- **Input:** `uploaded.json` і `reserve.json` (slug→id) [К], `publications`, `videos.title` у SQLite, останні 50 uploads з API (`_find_recent_upload` уже бере 20 [К yt.py:77]), тексти `SCENES` останніх 30 `epNN.py`, `tiktok.json.posted_auto` [К], `content/posts/*.md` (front matter `youtube`, `slug`).
- **Rules:**
  1. `content_id` уже має `publications(platform).state ∈ {uploaded, scheduled, published, distributed}` → BLOCK (точний дубль).
  2. Slug є в `uploaded.json` або `reserve.json` → BLOCK для `youtube_upload`. Перехід `reserve → schedule` — це `youtube_schedule`, а не upload.
  3. Точна назва серед останніх 50 uploads за 7 днів → BLOCK. Зараз 24 год і 20 штук (`yt.py:73–87`) [К].
  4. Збій перевірки дублів через API → **RETRY_LATER**, а не продовження (зараз `yt.py:79` заливає далі) [К].
  5. Схожість назви (Jaccard слів без хештегів) з будь-яким відео за 30 днів ≥0,8 → BLOCK; 0,6–0,8 → CANARY (той самий формат допустимий лише як експеримент «рімейк», `ideas.remakes` уже існує [К ideas.py:115]).
  6. Схожість тексту сценарію (`difflib.SequenceMatcher` по `text`) ≥0,7 з будь-яким за 60 днів → BLOCK.
  7. TG/TikTok: content_id уже має `post_id` → BLOCK.
- **Output:** ALLOW, BLOCK або CANARY.

### 3.6 Source credibility policy
- **Input:** URL з колонки 2 факт-таблиці, `meta.description` («Джерела:»), `source` в ideas.json, front matter `source/sources` статті.
- **Rules:** tier-1 = офіційні домени компаній і довідки: `help.openai.com`, `openai.com`, `support.google.com`, `blog.google`, `deepmind.google`, `gemini.google`, `research.google`, `anthropic.com`, `support.claude.com`, `signal.org`, держсайти `*.gov.ua`. tier-2 = профільні ЗМІ: `dou.ua`, `ain.ua`, `theverge.com`… tier-0 (заборона) = домени `.ru` / `.by` і сервіси з рішення власника (CLAUDE.md: «Semrush не використовувати») [П]. Кожне фактичне твердження має ≥1 tier-1 або ≥2 tier-2. Головне джерело статті — конкретна сторінка, а не корінь домену (правило CLAUDE.md) [П].
- **Thresholds:** `min_tier1_share=0.6` тверджень; tier-0 = 0.
- **Output:** ALLOW, BLOCK (tier-0 або твердження без джерела) або DEGRADE (лише tier-2 → без TikTok).
- **Зберігання списку:** `policy.json.sources` (whitelist/blacklist). Зміна списку — D-дія.

### 3.7 Budget policy
- **Input:** `quota.log` (одиниці за добу, з 22.11) [К yt.py:15–21], лічильник TTS з `runs`, `cost_tokens` і `cost_usd` з `agent_decisions`/`runs`, кредити vidIQ (`vidiq_balance` [?]).
- **Rules / thresholds:**
  - YouTube: денна сума + вартість дії ≤ `yt_quota_day − reserve`. Квота 10 000 [П, не підтверджено кодом]. `reserve_for_upload = 1600 + 50×4` [К units yt.py:10–13]. Отже, неупload-дії зупиняються на 8 000.
  - TTS ≤10 запитів/добу [П RUNBOOK:77].
  - Токени: `tokens_day_cap` (Q5).
  - vidIQ: `vidiq_credits_floor`.
  - Будь-яке значення `∞` або `null` у бюджеті = E (BLOCK + SAFE_MODE).
  - Добу рахуємо в UTC (квота YouTube скидається за тихоокеанським часом [?]).
- **Output:** ALLOW, RETRY_LATER(next_reset), або SAFE_MODE при перевищенні >110%.

### 3.8 Rate-limit policy
- **Input:** `publications` і `pub_events` за 24 год, `runs`.
- **Rules / thresholds:**
  - Shorts на YouTube ≤ `shorts_per_day` (RUNBOOK суперечливий: 1, 3 або 4 [П], див. Q4). Дефолт 2: Short дня + кліп.
  - Long ≤1/добу.
  - TG ≤2 пости/добу [П RUNBOOK «1–2 пости/день»].
  - TikTok ≤2/добу [П «1–2/день»].
  - Статті ≤3/добу [П].
  - IndexNow ≤ число нових URL.
  - `meta_edit` ≤10/запуск і ≤20/добу.
  - `tg_delete` ≤5/добу.
  - `trigger_update` ≤1/добу, `trigger_delete` ≤2/добу (лише one-shot).
  - Субагентів ≤4/год (зараз лише в промпті [П]).
- **Output:** ALLOW або RETRY_LATER. Перевищення ×2 → SAFE_MODE (T6).

### 3.9 Schedule conflict policy
- **Input:** `publish_at` дії, усі `publications.scheduled_at` по платформі, сітка з `policy.json.slots` (Short 17:00Z, нд 12:00Z, ср 17:00Z [П]).
- **Rules:** на одній платформі дві публікації не можуть стояти ближче ніж `min_gap_min=120` → RETRY_LATER із пропозицією наступного вільного слота. `publish_at` у минулому або раніше ніж через 15 хв → BLOCK. `publish_at` поза сіткою → CANARY (експеримент часу).
- **Відомий конфлікт:** 25.11 17:00Z ep78 і гайд #1 [П AUDIT §7]. У shadow mode policy позначить конфлікт. ep78 уже заплановано, тож policy зачепить лише гайд, який ще не залито.
- **Output:** ALLOW, RETRY_LATER(slot) або BLOCK.

### 3.10 High-risk topic policy
- **Input:** назва, опис, `text` сцен, теги, `ideas.format`.
- **Rules:** словник у `policy.json.high_risk`: здоров'я, медицина, калорії, ліки; гроші, інвестиції, кредит, криптовалюта; діти, вік; вибори, війна, політика, військові; юридичні поради; персональні дані; конкретні шахраї або бренди + «обман»; смерть.
  - Збіг вимагає: tier-1 для 100% тверджень, `UNVERIFIED=0` (навіть «не заявлено»), дисклеймер в описі (regex «не медична/не фінансова/не юридична порада» — як в ep82 [К meta.py:374]).
  - Без цього → BLOCK. З цим → DEGRADE (YouTube + сайт; TG і TikTok лише після canary-вікна).
  - ep81 (діти) і ep82 (калорії) потрапили б сюди.
- **Output:** ALLOW, DEGRADE або BLOCK.

### 3.11 Canary policy
- **Input:** `experiment_id` дії, нові формат, hook, тривалість, час, CTA чи обкладинка відносно `policy.json.baseline`.
- **Rules:** будь-яке відхилення від baseline без активного експерименту → CANARY(`scope=youtube_only`, `max_items=1/day`). Варіанти активного експерименту ≤ `sample_size` і ≤30% слотів тижня. Після публікації метрики збирає `analytics_db.sync` [К], а рішення приймає §8.
- **Output:** CANARY або ALLOW (baseline).

### 3.12 Rollback policy
- **Input:** платформа, `publications.rollback_plan`.
- **Rules:** перед ALLOW має існувати машинний rollback або compensation для платформи (§6), а `rollback_plan` записано в `publications`. Якщо rollback неможливий (TikTok [?], tg_delete, IndexNow), потрібні: (а) успішний YouTube-етап того ж content_id ≥60 хв без breaker-подій; (б) `quality=ALLOW` і `fact=ALLOW` без DEGRADE. Інакше DEGRADE(skip_platform).
- **Output:** ALLOW або DEGRADE.

### 3.13 Bulk-edit policy (метадані опублікованого; частина quality/rollback)
- **Input:** список `(video_id, old_snippet, new_snippet)` від `audit.fix` або SEO.
- **Rules:**
  - Відео старше `max_age_days=14` → BLOCK. Це знімає суперечність RUNBOOK:11/:19 «старі теги не чіпати» [П].
  - ≤10 відео за запуск.
  - Назву можна змінювати лише в межах експерименту; хвіст-хештеги (`audit.py:134–139`) — дозволено.
  - `old_snippet` записується в `agent_decisions.input_snapshot` ДО `_put`.
  - Повторна правка того ж поля того ж відео за 7 днів → BLOCK (запобігає «пінг-понгу» SEO ↔ audit).
- **Output:** ALLOW (з підмножиною id), BLOCK або DEGRADE (лише теги, без назв).

### 3.14 Trigger / prompt / rules policy (D-рівень самозміни)
- **Input:** `tool_input` з `update_trigger`/`delete_trigger`/`create_trigger` (хук отримує його повністю) [К hook.py:15]; поточний промпт (`get_trigger`, лише читання); diff RUNBOOK/SKILL/strategy.
- **Rules:**
  - (1) `update_trigger` змінює prompt лише при `experiment.decision='promote'` з `rollback_ref`, diff ≤ `max_prompt_diff_chars=1500`, не для захищених задач (`policy.json.protected_triggers`: токен, перевірка бота, збирач, watchdog).
  - (2) `enabled=false` для незахищеної задачі дозволено (оборотно), `delete_trigger` — лише для one-shot, що вже спрацювали або належать скасованому content_id.
  - (3) `create_trigger` із cron → ≤1/добу, ≤25 активних.
  - (4) Старий промпт іде в `input_snapshot`.
  - (5) Через 7 днів автоматично перевіряються KPI експерименту. Погіршення > порогу → `update_trigger` зі старим промптом (auto-rollback).
- **Output:** ALLOW, BLOCK або CANARY (зміна діє лише до кінця тижня, далі auto-revert, якщо експеримент не promote).

### 3.15 Circuit breaker policy
- **Input:** таблиця `breaker` (стан по scope: `global`, `youtube`, `telegram`, `tiktok`, `site`, `tts`, `render`).
- **Rules:** `open` → SAFE_MODE для дій цього scope. `half_open` → лише probe-дії (читання API або одна canary-дія). Деталі — §9.

---

## 4. Publication gate spec

**Де вбудувати** (мінімально, по одному рядку на функцію). Кожна функція спершу кличе `policy.gate(action)` і, якщо результат не `ALLOW`/`CANARY`/`DEGRADE` з дозволеною підмножиною, кидає `PolicyBlocked`:
- `yt.upload` — `yt.py:56`, до `_find_recent_upload` (рядок 61). slug береться з `path` (`/home/claude/eps/<slug>/final.mp4` — так кличуть `upload_reserve.py:11`, `try_ep10.py:11`) [К]. Якщо slug не виводиться, результат BLOCK.
- `yt.schedule` — `yt.py:96`. Саме тут резерв стає публічним.
- `yt.comment` — `yt.py:106`, разом із `post_comments.py:6–9`.
- `yt.add_to_playlist` — `yt.py:113`.
- `yt._put` для `videos` зі зміною snippet, тобто `audit.fix` (`audit.py:159`) і `set_category` (`yt.py:100`).
- `tg.post`, `tg.video` (`tg.py:17–18`). `tg.call` лишається для читання й адміністрування, але `sendMessage`/`sendVideo` у `CH` через `call` теж іде через gate (перевірка `chat_id == CH` у `call`).
- TikTok: Python-функції немає, публікує LLM через MCP [П]. Gate спрацьовує в **PreToolUse-хуку** на `mcp__vidIQ__vidiq_social_post_publish` (і `_draft_create`). Хук синхронно кличе `policy.py check-tool`, `exit 2` блокує [К: хук є, блокування — фіча Claude Code; поведінку в режимі auto перевірити — ?].
- Сайт: `git push` (Bash) — хук-матчер на `git push`, плюс pre-push-перевірка `python3 build.py` і gate для нових `content/posts/*.md` з `youtube:`. CI (`pages.yml`) не чіпаємо.
- IndexNow: `tools/indexnow.py` працює в CI [К]. Gate у ньому: пінгувати лише URL, що є в `dist/` і не старші за 48 год (рядок 15 використовує `git diff HEAD~1`). Це потребує деплою workflow.

**Таблиця перевірок** (✓ — обов'язково, ○ — якщо застосовно, — — не застосовується):

| # | Перевірка | Джерело даних (є/немає) | YT upload | YT comment | TG | TikTok | Сайт | IndexNow |
|---|---|---|---|---|---|---|---|---|
| 1 | `content_id` | slug: ключ `uploaded.json`, тека `eps/<slug>`, ключ `meta.py` [К] | ✓ | ✓ | ✓ | ✓ | ✓ (`slug` статті + `youtube:`) | ✓ URL→content_id |
| 2 | topic→idea→script→video | `ideas.json` має поле `video_id`, але жодна ідея не зв'язана [К AUDIT §1 п.7]. Потрібне `IDEA_ID` у `epNN.py` або `publications.idea_id` | ✓ (legacy: DEGRADE) | — | ○ | ○ | ○ | — |
| 3 | статус фактчеку | `*_factcheck_independent.md`, `Вердикт:` | ✓ | ○ (текст коментаря без фактів → skip) | ✓ (caption з фактами) | ✓ | ✓ (стаття: `source` + перевірка) | — |
| 4 | кількість UNVERIFIED | та сама таблиця | ✓ | — | ✓ | ✓ | ✓ | — |
| 5 | першоджерела | колонка URL; «Джерело:» в описі | ✓ | — | ○ | ○ | ✓ (`source.url` не корінь домену) | — |
| 6 | якість джерел | §3.6 | ✓ | — | ✓ | ✓ | ✓ | — |
| 7 | ASR-звірка | `audit_vo.py` → потрібен `--json` [—] | ✓ | — | ○ (те саме відео) | ✓ | — | — |
| 8 | якість голосу | `voice_check.py` exit 0 [К] | ✓ | — | ○ | ✓ | — | — |
| 9 | рендер | `final.mp4` + ffprobe; `build.sh` `set -e`, `echo DONE` [К] | ✓ | — | ✓ (`tg.mp4`) | ✓ (`tiktok.mp4` ≤10 МБ [П]) | — | — |
| 10 | thumbnail | `eps/<slug>/thumb.jpg` [К фс] | ✓ | — | — | — | ○ (og генерує build) | — |
| 11 | тривалість | ffprobe | ✓ | — | ✓ | ✓ | — | — |
| 12 | немає тиші | ffmpeg `volumedetect`/`silencedetect` [—] | ✓ | — | ✓ | ✓ | — | — |
| 13 | дублікати | §3.5 | ✓ | ✓ (коментар каналу вже є — `audit.channel_commented` [К audit.py:79]) | ✓ | ✓ (`tiktok.json.posted_auto`) | ✓ (slug існує) | ✓ |
| 14 | схожість | §3.5 п.5–6 | ✓ | — | — | — | ✓ (назва статті) | — |
| 15 | денні ліміти | §3.8 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 16 | конфлікт розкладу | §3.9 | ✓ | ✓ (`at ≤ now` і відео public — інакше RETRY_LATER) | ✓ | ✓ | ○ (дата посту ≥ publishAt YouTube) | — |
| 17 | budget | §3.7 | ✓ | ✓ | — | ✓ (vidIQ кредити) | — | — |
| 18 | high-risk | §3.10 | ✓ | ✓ (текст) | ✓ | ✓ | ✓ | — |
| 19 | canary eligibility | §3.11 | ✓ | — | ✓ | ✓ | — | — |
| 20 | rollback plan | §3.12, §6 | ✓ | ✓ | ✓ | ✓ (compensation) | ✓ | ✓ |

**Додатково для коментаря.** Відео `public` (API не дає коментувати приватні — `post_comments.py:1`) [К]; текст ≤ ліміту; немає URL, крім `t.me/shikarno_ai_ua` і сайту.

**Dry-run.**
- `SHK_DRY_RUN=1` (env) або `python3 studio/policy.py check --dry …`. Gate проходить повністю (читання API дозволено), друкує JSON рішення, пише `agent_decisions(status='dry_run')`, жодного POST/PUT.
- `yt._req` при `SHK_DRY_RUN=1` для `method != GET` кидає `DryRun` до мережі.

**Grandfathering (щоб не зламати ep78/ep81).**
- `policy.json.legacy = ["ep78_signal_shi_agent", "ep81_tier_kids", …усі ключі uploaded.json на момент cutover]`.
- Для legacy пропускаються перевірки 2, 7 і 12 (немає даних). Перевірки 13, 15, 16 і 20 лишаються.
- Перевірка 3 для ep78: файлу немає, тому DEGRADE(`no_tiktok`). Альтернатива — дозапуск незалежного фактчекера до 25.11 17Z (Q6).
- Рішення `legacy_allow` пишеться в `agent_decisions`.

---

## 5. Idempotency / state machine spec

### 5.1 Таблиці (`studio/data/ops.sqlite`, WAL, `busy_timeout=10000`)

```sql
create table publications(            -- одна жива картка на (content_id, platform); змінюється ЛИШЕ через pubstate.transition()
  content_id text, platform text check(platform in ('youtube','telegram','tiktok','website','indexnow','yt_comment','yt_playlist')),
  state text, idem_key text unique, payload_digest text, external_id text, external_url text,
  session_ref text,          -- YouTube resumable Location / vidIQ uploadId / draft postId
  scheduled_at text, attempts int default 0, policy_decision_id text, rollback_plan text,
  parent_content_id text, idea_id text, experiment_id text, legacy int default 0, updated_at text,
  primary key(content_id, platform));
create table pub_events(               -- append-only історія переходів
  id integer primary key, content_id text, platform text, from_state text, to_state text,
  reason text, external_id text, decision_id text, run_id text, ts text, prev_hash text, hash text);
create trigger pub_events_ro_u before update on pub_events begin select raise(abort,'append-only'); end;
create trigger pub_events_ro_d before delete on pub_events begin select raise(abort,'append-only'); end;
```

`idem_key = sha256(content_id|platform|action|payload_digest)`. `payload_digest` = sha256 файлу відео + title + description + caption. Нова версія контенту (інший digest) дає новий key, але BLOCK лишається через правило «одна публікація на content_id+platform».

### 5.2 Стани й переходи (однакові для всіх платформ; не всі стани застосовні)

```
pending ─► validated ─► approved_by_policy ─► uploading ─► uploaded ─► scheduled ─► published ─► distributed
   │            │               │                  │            │           │            │
   └────────────┴───────────────┴──────► failed ◄──┴────────────┴───────────┘            │
                                         uploading ──(crash)──► in_doubt ──reconcile──► uploaded | failed
   published/scheduled/distributed ──► rolled_back ;  (rollback неможливий) ──► compensated
```

- `validated` — пройдено quality, fact, source, duplicate (артефакти готові).
- `approved_by_policy` — `evaluate()` = ALLOW або CANARY, `policy_decision_id` записано.
- `uploading` записується **до** зовнішнього виклику (intent), разом із `session_ref`, щойно той відомий.
- `in_doubt` — службовий підстан: процес побачив `uploading` або `posting` старше `inflight_timeout`. Повтор заборонено, дозволено лише reconcile.
- `failed` — після `max_attempts=3` або BLOCK. Повторний запуск можливий лише з нового `approved_by_policy`.
- `distributed` — для `youtube`: усі дочірні платформи досягли кінцевого стану.

| Платформа | uploading → uploaded | scheduled | published | Застосовні стани |
|---|---|---|---|---|
| youtube | video id отримано | `publishAt` встановлено (`schedule`) | на publishAt `privacyStatus=public` (перевіряє `post_comments`/watchdog) | усі |
| yt_comment | — | `at` з `pending_comments.json` (міграція: ця черга = `publications(platform='yt_comment', state='scheduled')`) | thread id отримано | pending, validated, approved, posting(=uploading), published, failed, rolled_back |
| yt_playlist | — | — | playlistItem id | approved, posting, published |
| telegram | — | — | `message_id` (`result.message_id`) | pending…published, rolled_back, compensated |
| tiktok | `vidiq_file_upload` + `vidiq_put.sh` OK | draft створено (`postId`) / `scheduled` у vidIQ [К tiktok.json має і `scheduled`, і `url`] | URL TikTok | усі, крім rolled_back [?] → compensated |
| website | md закомічено | `date` у майбутньому (build.py не публікує до часу [П CLAUDE.md]) | Pages build зелений + URL 200 | pending, validated, approved, uploaded, scheduled, published, rolled_back |
| indexnow | — | — | ping 200/202 | approved, published (повтор безпечний) |

### 5.3 Для кожної публічної дії

| Дія | Що зберегти ДО | Як перевірити, що вже виконано | Як не допустити повтору | Успіх API, але локальний запис втрачено |
|---|---|---|---|---|
| YouTube upload | `uploading`, `idem_key`, `payload_digest`, title; **`session_ref` (Location) одразу після init POST, до PUT** (`yt.py:66–69`) | (1) `publications.state`; (2) `uploaded.json[slug]`; (3) `_find_recent_upload` (розширити до 50/7 днів) | unique `idem_key`; flock `util.locked(ops.sqlite)` на content_id; `upload()` сам пише `uploaded.json` через `update_json` (зараз пише агент [К AUDIT]) | reconcile: `PUT session_ref` з `Content-Range: bytes */<size>`. 200/201 → тіло з `id` [? перевірити на YouTube, патерн як у vidiq_put.sh]. 308 → докачати. 404/410 → title-пошук серед uploads за 7 днів. Знайдено → `uploaded`, не знайдено → `failed`, upload знову дозволено |
| YouTube schedule | `scheduled_at` | `videos.list status.publishAt` | `_put` ідемпотентний за природою | повторний GET і запис |
| YouTube comment | `posting`, `text_digest` | `commentThreads.list videoId` і `authorChannelId == me`, текст збігається (логіка `audit.channel_commented` [К]) | **`_req(tries=1)` для POST commentThreads** (зараз 3 спроби на 5xx → дубль [К yt.py:31]) | reconcile списком коментарів → `published` з id |
| Playlist add | `posting` | `playlistItems.list playlistId, videoId` | перевірка перед insert (як `finalize.py:28–31`) | reconcile списком |
| Telegram post/video | `posting`, `caption_digest` | `publications.external_id`; [?] автофорвард у групу обговорення (`is_automatic_forward` в `updates.json` [К inbox.py:69 пише всі апдейти]) | `tg.video` кидає виняток, якщо `ok != true` (зараз повертає JSON [К tg.py:7, 16]); `timeout=300` — без retry на відправку | reconcile в `updates.json` за digest підпису. Не знайдено за 30 хв → `in_doubt` **без повтору** (краще пропуск, ніж дубль), позначка в щоденному звіті, breaker telegram `half_open` для цього content_id |
| TikTok publish | `uploading` + `uploadId`; після draft — `postId` | `tiktok.json.posted_auto[slug]` [К]; `vidiq_social_post_status(postId)` / `vidiq_social_post_list` [?] | хук блокує `vidiq_social_post_publish`, якщо в `publications` уже є `postId` у стані `published` або `scheduled` | reconcile: `post_status` за збереженим `postId`. Немає `postId` → `post_list` за підписом. Не визначено → `in_doubt`, без повтору |
| Сайт | `uploaded` = commit sha | `git log` має файл; URL на shikarno.com.ua 200 | slug unique (файл існує → BLOCK) | push пройшов, запису немає → `git ls-remote` + наявність файлу → `uploaded` |
| IndexNow | — | — | повтор нешкідливий, але обмежений rate-limit | — |

Зовнішній ланцюжок «вийшов» (нагадування 17:04Z [П]) замінюється однією ідемпотентною командою: `python3 studio/pubstate.py advance <content_id>`. Вона просуває кожну платформу на один крок, якщо policy = ALLOW. Повторний запуск безпечний, бо кожен крок пропускається, коли кінцевий стан уже досягнуто.

---

## 6. Rollback / compensation spec

| Платформа / дія | Rollback (машинний) | Можливий? | Якщо неможливий → compensation | Тригер автоматичного rollback |
|---|---|---|---|---|
| YouTube відео (scheduled) | `schedule(vid)` → `privacyStatus=private` без `publishAt` (`_put status`) | так [К механізм `_put`] | — | fact-FAIL після заливки (повторний фактчек), breaker `youtube`, дубль |
| YouTube відео (public) | `privacyStatus=private` (**не видаляти**, RUNBOOK:11 [П]) | так | якщо помилка дрібна: `_put snippet` з виправленням + коментар-уточнення | факт спростовано (повторний фактчек через 24 год для high-risk), `dup_rate>0`, сигнал «not interested» з аналітики (Q8) |
| YouTube метадані (`audit.fix`, SEO) | `_put` старого snippet з `agent_decisions.input_snapshot` | так | — | метрика CTR або переглядів за 72 год < baseline − поріг (експеримент); або будь-який `bulk_edit` поза policy |
| Обкладинка | `thumbnails.set` попереднього jpg (зберігати в `eps/<slug>/thumb_prev.jpg`) | так, але квота | — | експеримент A/B програв |
| YouTube коментар | `comments.delete(id)` (scope `youtube.force-ssl` уже є [К auth.py:117]) | так | — | дубль, high-risk текст |
| Плейлист | `playlistItems.delete(id)` | так | — | дубль |
| Telegram пост | `deleteMessage(chat_id=CH, message_id)` [? 48-год обмеження Bot API]; або `editMessageCaption`/`editMessageText` з виправленням | так / частково | після 48 год: новий пост-виправлення (compensation) + `edit` | факт-FAIL, дубль, prompt-injection у підписі |
| Telegram видалення спаму | — | ні | копія повідомлення в `agent_decisions.input_snapshot`; при помилці — повідомлення автору або групі не надсилаємо (Q9) | — |
| TikTok | видалення через vidIQ — у списку MCP-інструментів немає delete для social posts [? за переліком інструментів сесії] | ймовірно ні | (а) `vidiq_update_video`? для TikTok [?]; (б) пост-виправлення в TG і коментар на YouTube; (в) breaker `tiktok` open на 24 год; (г) у щоденному звіті — «видалити вручну в застосунку» як **інформація** (не approval) | — |
| Сайт / стаття | `git revert <sha>` + push → Pages (~1 хв [П CLAUDE.md]); або `updated:` + виправлення | так | — | build впав, 404 на URL, fact-FAIL |
| IndexNow | повторний ping URL після revert (протокол приймає і видалені URL [?]) | частково | — | після будь-якого rollback сайту |
| Промпт задачі | `update_trigger(prompt=old)` з `input_snapshot` | так | — | KPI експерименту гірші, breaker T12 (цикл) |
| `enabled=false` задачі | `update_trigger(enabled=true)` | так | — | — |
| `delete_trigger` | лише one-shot (§3.14). Recurring видаляти заборонено, тож rollback не потрібен | — | `create_trigger` з копії (`name`, `cron`, `prompt` з `input_snapshot`) — історію запусків не відновити | — |
| RUNBOOK / strategy / SKILL | `git revert` | так | — | експеримент `rollback` |
| `ideas` approve | `ideas.py set status=new` | так | — | — |

**Як виконується.** `python3 studio/pubstate.py rollback <content_id> <platform> --reason …`. Команда кличе policy (`action.type='rollback'` завжди дозволено, крім E), виконує дію, пише `rolled_back`/`compensated` і `agent_decisions(decision_type='rollback', rollback_ref=<decision_id первинної дії>)`.

---

## 7. Immutable decision log spec

### 7.1 Схема (`ops.sqlite`)

```sql
create table agent_decisions(
  seq integer primary key autoincrement,
  decision_id text unique not null,          -- uuid4
  run_id text not null,                      -- runs.run_id
  agent_name text not null,                  -- id з hq_data.AGENTS (coo, eic, shorts, factcheck…) [К hq_data.py:12–31] або 'policy'
  agent_version text,                        -- git sha файлу ролі / SKILL.md / промпту
  prompt_version text,                       -- sha256(prompt задачі) з get_trigger (лише читання) або SKILL.md
  model text,                                -- напр. claude-opus-5-5 (з get_session/хука), 'rule' для детермінованих
  decision_type text not null check(decision_type in ('topic_select','idea_approve','format_select','hook_select','script_generate',
       'factcheck','publish','seo_change','meta_edit','schedule_change','strategy_change','prompt_change','trigger_change',
       'tg_delete','experiment','policy','rollback','breaker','legacy_allow')),
  input_snapshot text not null,              -- JSON: факти, які бачив агент/policy (або sha256 + шлях у studio/data/snapshots/<decision_id>.json для >64 КБ)
  output text,                               -- JSON: що вирішено
  evidence_ids text,                         -- JSON: [news.url, research(date,n), ideas.id, video_id, факт-md sha]
  source_urls text,                          -- JSON
  rules_triggered text,                      -- JSON [{rule, value, threshold, verdict}]
  confidence real,                           -- LLM: самооцінка 0–1; rule: 1.0
  policy_result text check(policy_result in ('ALLOW','BLOCK','RETRY_LATER','CANARY','DEGRADE','SAFE_MODE') or policy_result is null),
  policy_version text, code_version text,    -- sha policy.json, git HEAD
  cost_tokens int, cost_usd real,            -- [?] з transcript_path у хуку (Stop) — у коді зараз немає [—]
  started_at text, finished_at text,
  status text check(status in ('proposed','decided','executed','failed','dry_run','superseded')),
  rollback_ref text,                         -- decision_id, яке цей запис відкочує / яким відкочено
  related_content_id text, related_video_id text, related_platform_post_id text,
  prev_hash text not null, hash text not null -- sha256(prev_hash || canonical_json(рядка без hash))
);
create trigger ad_no_update before update on agent_decisions begin select raise(abort,'append-only'); end;
create trigger ad_no_delete before delete on agent_decisions begin select raise(abort,'append-only'); end;
create index ad_content on agent_decisions(related_content_id);
create index ad_run on agent_decisions(run_id);
create table runs(run_id text primary key, task text, trigger_id text, agent_name text, started_at text, finished_at text,
  status text, error text, api_calls int, retries int, tokens int, heartbeat_at text);
```

- **«Без редагування»:** статус не оновлюється на місці. Перехід `proposed → executed/failed` записується **новим рядком** із новим `decision_id`, тим самим `decision_type` і `output.ref = <decision_id первинного рядка>`. Поточний статус рішення — останній рядок за `ref`.
- **Захист від видалення:** тригери SQLite (не захистять від `rm ops.sqlite`) + хеш-ланцюжок + кожен `hash` у DO пульта через `/api/ingest` (`kind='decision'`, `detail=hash|decision_id`) [К ingest приймає довільний kind ≤32 символи, `worker.js:161`]. Перевірка: `ops.py verify` перераховує ланцюжок і звіряє останні N хешів із DO. Розбіжність → SAFE_MODE (T15). `/api/purge` (`worker.js:137–141`) має пропускати `kind='decision'` (зараз зберігає лише `note` і `prompt` [К]). `KEEP=20000` (`worker.js:7`) обрізає й decision-події, тож потрібен виняток для `kind='decision'`. Ці зміни вимагають деплою воркера.
- **Копія:** щоденний `sqlite3 .backup` в `studio/data/snapshot/ops.sqlite` (той самий механізм, що `lake.py snapshot`, `lake.py:318–319` [К]) і коміт.

### 7.2 Ланцюжок news → idea → script → factcheck → video → publication → metrics
- `news.url` (PK [К]) → `ideas.source` + новий `ideas.news_url` → `ideas.id`.
- `epNN.py`: нові константи `CONTENT_ID = SLUG` (вже є `SLUG` [К ep78.py:6, ep81.py:8]) і `IDEA_ID = <id>`.
- `factcheck.md`: обов'язкові рядки шапки `content_id:`, `script_sha256:`, `meta_sha256:`, `Вердикт:`.
- `publications(content_id, platform).external_id` = video_id / message_id / TikTok postId.
- Метрики: `videos.slug` уже є в SQLite [К analytics_db.py:33] → `daily`, `traffic_daily` за `video_id`.
- `ideas.video_id` заповнюється автоматично при `youtube.uploaded` (поле передбачене докстрингом `ideas.py:10` [К]).
- Бекфіл legacy: `uploaded.json` (99), `tiktok.json.posted_auto`, front matter `youtube:`/`telegram_post:` статей. Скрипт `ops.py backfill` пише `legacy=1`.

### 7.3 Відтворюваність reasoning
- Детерміновані рішення (policy, `ideas.score`, `audit.check`) відтворюються **точно**: `replay` з `input_snapshot` і версією коду.
- LLM-рішення **не відтворюються бітово**. Відтворюваними робимо: (а) вхід (`input_snapshot`: які новини, бали, дошка, метрики бачив агент); (б) `prompt_version` і `model`; (в) `output` з обґрунтуванням ≤500 символів; (г) `evidence_ids`. Тоді «replay» означає, що той самий вхід можна дати іншому прогону й порівняти. Розходження — сигнал для експерименту, а не помилка.
- Як LLM пише рішення: CLI `python3 studio/ops.py decide --type topic_select --agent eic --input @file.json --output @out.json --evidence …`. Без запису в `agent_decisions` policy не пропустить C/D-дію з цим `content_id`, бо gate перевіряє, що в content_id є `topic_select` і `script_generate`.

---

## 8. Experiment loop spec

### 8.1 Таблиця

```sql
create table experiments(
  experiment_id text primary key, created_by text, hypothesis text not null,
  kind text check(kind in ('hook','format','duration','thumbnail','cta','publish_time','topic','prompt','strategy','metadata')),
  variant text not null, control text not null,            -- JSON: що саме відрізняється
  audience_format text,                                    -- напр. 'short:tier', 'long:guide'
  start_date text, end_date text, sample_size int not null,-- к-сть публікацій у варіанті
  max_share real default 0.3,                              -- частка слотів тижня
  success_metric text not null,                            -- 'views_7d_median' | 'avg_pct_7d' | 'subs_per_1k' | 'ctr_72h' | 'tg_joins'
  threshold text not null,                                 -- JSON {promote: '>= control*1.2', rollback: '< control*0.8', min_n: 3}
  guardrail_metrics text,                                  -- JSON {avg_pct_7d: '>= 30', not_interested: ...}
  status text check(status in ('designed','running','collecting','decided')),
  result text, decision text check(decision in ('promote','pause','rollback') or decision is null),
  rollback_ref text, decision_id text);
create table experiment_items(experiment_id text, content_id text, arm text check(arm in ('variant','control')), primary key(experiment_id, content_id));
```
Статуси й рішення змінюються через нові рядки `agent_decisions(decision_type='experiment')`. Сама таблиця `experiments` mutable лише для `status/result/decision`, з тригером, що забороняє міняти `hypothesis/variant/threshold/success_metric` після `running`.

### 8.2 Цикл
1. **hypothesis** — агент (CSO, growth-loop, дизайн) пише `experiments(status='designed')`.
2. **experiment design** — policy валідує: є control, `sample_size ≥3`, метрика зі списку, поріг заданий, активних експериментів на той самий `audience_format` ≤1, ≤3 експерименти одночасно.
3. **limited rollout** — публікації з `experiment_id` отримують CANARY (§3.11): ≤`max_share` слотів, лише YouTube + сайт до першого читання метрик.
4. **metric collection** — `analytics_db.sync` [К]. `first7()` уже рахує 7-денне вікно [К analytics_db.py:155]. Дані запізнюються на 2–3 дні [П SKILL.md:1], тому `collecting` триває до `end_date + 3 дні`.
5. **threshold decision** — `ops.py experiments decide`, детерміновано: медіана варіанта vs control. `promote`, якщо `≥ control×1,2` і `n ≥ min_n`. `rollback`, якщо `< control×0,8` або порушено guardrail-метрику. Інакше `pause` (недостатньо даних).
6. **promote** — єдиний шлях до змін `policy.json.baseline`, рядків RUNBOOK «МІКС SHORTS» і промптів задач (§3.14). Запис робить `ops.py`, а не вільний Edit.
7. **rollback** — повертає baseline і, якщо змінювався промпт, `update_trigger` зі старим. `rollback_ref` посилається на decision promote.
8. **decision log** — кожен крок пише рядок в `agent_decisions`.

**Обмеження автономії:** growth-loop (SKILL.md:6), CSO і COO **не змінюють** глобальні частки форматів, стратегію чи промпти поза кроком 6. Policy це забезпечує: Edit RUNBOOK у секціях зі списку `policy.json.guarded_sections` без `experiment.promote` → BLOCK через хук. Приклади експериментів: новий hook («Твоя дитина питає ШІ?» vs теза), тривалість 30 vs 45 с, обкладинка v4 vs v3 (`thumb_test.json` уже веде стиль [К finalize.py:36–38]), CTA в описі, час 17:00Z vs 15:00Z, нова рубрика.

---

## 9. Circuit breaker spec

Таблиця `breaker(scope text primary key, state text check(state in('closed','open','half_open')), reason text, opened_at text, cooldown_until text, probes_ok int, trips_24h int)` + append-only `agent_decisions(decision_type='breaker')`. Дзеркало в `kv.state.safe_mode` пульта, щоб `/status` бота показував його [К worker.js:106 `statusText()`].

**Загальне:**
- У SAFE_MODE блокуються всі C і D дії (upload, schedule, comment, TG, TikTok, push, meta_edit, trigger_*, tg_delete). Лишаються A і B: збір, аналітика, чернетки, TTS у межах бюджету, рендер, фактчек, а також **rollback і compensation** та читання для probe.
- Повідомлення власнику: один `sendMessage` у бот при переході `closed → open` і при поверненні в `closed`, не частіше 1 разу на 30 хв на scope. Це інформування, а не approval.
- Автовідновлення: `cooldown` (дефолт 30 хв, ×2 при кожному повторі за 24 год, максимум 12 год) → `half_open` → N успішних probe → `closed`.
- Запобігання повтору: `trips_24h ≥3` → scope лишається `open` до наступної доби. Щоденний звіт додає «рекомендовану зміну» у вигляді експерименту.

| # | Тригер | Як виявити (дані) | Scope / що блокувати | Що лишити | Автовідновлення | Запобігання повтору |
|---|---|---|---|---|---|---|
| T1 | Повторювані помилки external API | `runs.error`; `yt._req` викидає RuntimeError після 3 спроб [К yt.py:33,37]; `tg` `ok:false`; ≥5 помилок за 30 хв на сервіс | сервіс (`youtube`/`telegram`/`tiktok`) | інші сервіси | probe: 1 GET (`channels mine` / `getMe`) ×3 успішно | backoff ×2 |
| T2 | Budget overrun | §3.7: витрати ≥110% денного ліміту (токени, TTS, vidIQ) | global C + генеративні B (TTS) | A, rollback | наступна доба (UTC) | ліміт на run, а не лише на добу |
| T3 | Quota exhaustion | сума `quota.log` за добу ≥ 9 000 [К джерело], або HTTP 403 `quotaExceeded` у тілі `_req` | `youtube` (крім rollback-PUT, якщо квота лишилась) | TG, сайт, аналітика без YouTube Data API | скидання квоти [? PT-північ] | резерв 1 600 під upload (§3.7) |
| T4 | OAuth problems | (а) `token.json.refreshed_at + refresh_token_expires_in` < 48 год [К поля є]; (б) `invalid_grant` у `yt.token()` (`yt.py:43`, зараз без обробки) | (а) DEGRADE: попередження й нагадування-лінк `auth.py link` у бот (наявний процес); (б) `youtube` open | усе без Google API | `watch.py` уже автоматично обмінює код (`watch.py:40–49`) [К] → probe `channels mine` → closed | Q2: consent screen «In production» |
| T5 | Дублікати публікацій | duplicate policy спрацювала *після* дії (reconcile знайшов 2 external_id на content_id), або `audit` бачить 2 відео з однаковою назвою за 7 днів | global C | A/B, rollback (дубль → private) | лише після auto-rollback дубля + 24 год | аналіз `pub_events` → тест на сценарій |
| T6 | Аномальна кількість публікацій | `pub_events` `→published` за 24 год > 2× rate-ліміту, або > 3 за годину | global C | — | наступна доба | — |
| T7 | Падіння якості | ≥2 BLOCK quality поспіль; `voice_check` BAD ×3; `avg_pct_7d` медіана останніх 5 < 25% (дані `daily` [К]) | `publish` нових форматів (CANARY-only) | baseline-формати | наступні 3 ALLOW quality | експеримент на причину |
| T8 | Повторні UNVERIFIED | 3 випуски поспіль із UNVERIFIED > 0 або 2 fact-FAIL за 48 год | publish контенту з factcheck (Shorts і довгі) | дайджест без нових фактів [?], A/B | наступний PASS ×2 | промпт фактчекера → експеримент |
| T9 | Підозра на prompt injection | регулярки в `updates.json`/коментарях/RSS (`ignore previous`, «ти тепер», `system:`, base64-блоки, посилання на `/api/purge`, `update_trigger`); рішення агента посилається на `evidence_ids` із групи TG; хук бачить D/E-дію в тому ж run, де читались дані з групи | D і E для цього run + `tg_delete` | A | новий run | у `input_snapshot` позначати `untrusted=true` для даних з TG, коментарів і вебу; D-дії з такими evidence → BLOCK |
| T10 | Конфлікт розкладу | §3.9 знайшов 2 на слот, або `publishAt` іншого відео в межах 120 хв | `youtube_schedule`/upload нових | інші | вирішення: RETRY_LATER на наступний слот | — |
| T11 | Зациклення агентів | `runs`: той самий `task` або `agent_name` стартує >6 разів за годину; естафета глибша за 8 ланок; той самий `decision_type+content_id` >3 рази за 2 год | `Agent`-запуски (хук на `Agent`/`Task` tool) + C | — | 1 год | ліміт глибини естафети в policy.json |
| T12 | Відсутність heartbeat | **ззовні:** pult `scheduled()` — немає подій `ev` >3 год з 05 до 21Z; **ззовні:** GitHub Actions/воркер 17:10Z: Short дня не в RSS каналу (`youtube.com/feeds/videos.xml?channel_id=…`, без ключа) [?] | DO `safe_mode=1`; сесія на старті кожного run читає `/api/state` і поважає прапорець | — | перша подія `ev` + `runs.heartbeat_at` свіжий | §10: heartbeat кожного run |
| T13 | Критична помилка рендеру | `build.sh` exit≠0 ×2 на той самий slug; `final.mp4` без аудіо або <1 с | `render` для slug; publish цього slug | інші slug, резерв (`reserve.json` [К]) | перерендер OK | — |
| T14 | Аномальні витрати tokens / API calls | `runs.tokens` > p95×3 за 7 днів; `api_calls` за run > 300; `quota.log` рядків/год > 200 | global C + Agent-запуски | A | наступна година, далі доба | — |
| T15 | Цілісність журналу / policy | `ops.py verify`: розрив хеш-ланцюжка; sha `policy.py`/`policy.json`/`hook.py`/`settings.json` ≠ pinned у DO | **global SAFE_MODE** (усе C/D) | A | лише після збігу хешів (git restore) | CODEOWNERS (Q1) |

---

## 10. Observability spec

### 10.1 Що є зараз
- Журнал кожного виклику інструмента на пульті (`hook.py` → `/api/ingest`, `ev` до 20 000 рядків, `worker.js:7, 174`) [К].
- `/api/snapshot` агрегує помилки по areas за год/добу/тиждень (`worker.js:185–192`) [К].
- `quota.log` [К].
- `hq/activity.json` (start/done агентів, ≤200, `activity.py:13–14`) [К].

Немає [—]: `runs`, heartbeat, алертів, token cost, success-rate публікацій.

### 10.2 Мінімальна схема метрик (без нового сервісу, у `ops.sqlite` + DO)

| Метрика | Джерело / формула | Де | Поріг алерту (→ breaker) |
|---|---|---|---|
| run history | `runs` (start/finish/status/error) — `ops.py run start/finish`; задача планувальника першим кроком кличе start | ops.sqlite + `ev kind='run'` | — |
| task status | `runs` останній по `task` vs очікуваний розклад з `policy.json.schedule` (копія AUDIT §6) | ops.sqlite | пропуск >1 запланованого запуску → T12 |
| heartbeat | `runs.heartbeat_at` + `ev` max(ts) | DO (cron) | >3 год → T12 |
| error rate | `ev` ok=0 / усі за 1 год (наявний agg [К]) + `runs.status='failed'` | DO | >30% за год |
| retry rate | лічильник у `yt._req` (рядки 32, 36) → `runs.retries` | ops.sqlite | >20% запитів |
| API quota | `quota.log` сума за добу | файл → щоденний звіт | ≥8 000 → RETRY_LATER; ≥9 000 → T3 |
| token cost | [?] Stop/SubagentStop хук: `transcript_path` у вході хука → сума `usage` (поле в JSONL транскрипту [?]) → `runs.tokens` | ops.sqlite | T14 |
| publication success rate | `pub_events`: `→published` / `→approved_by_policy` за 7 днів, по платформах | ops.sqlite | <90% |
| duplicate rate | reconcile-дублі / публікації | ops.sqlite | >0 → T5 |
| factcheck pass rate | `agent_decisions(decision_type='factcheck')` PASS / усі | ops.sqlite | <70% → T8 |
| render success rate | `runs(task='render')` OK / усі | ops.sqlite | <80% |
| rollback rate | `pub_events →rolled_back|compensated` / published | ops.sqlite | >10% за тиждень |
| circuit breaker events | `agent_decisions(decision_type='breaker')` | ops.sqlite + DO | будь-яке open → повідомлення |
| OAuth days left | `token.json` поля `refreshed_at`, `refresh_token_expires_in` [К] | щоденний звіт | <2 дні → T4(а) |

### 10.3 Heartbeat і алерти ззовні (сесія може бути мертвою)
- `pult/worker.js`: додати `async scheduled(ev, env)` у `export default` (патерн `bait/worker.js:79` [К]) і `[triggers] crons = ["*/30 * * * *"]` у `pult/wrangler.toml`. Логіка: `SELECT MAX(ts) FROM ev`. Якщо прогалина більша за поріг (05–21Z), то `tgCall sendMessage OWNER_CHAT_ID` (функція вже є, `worker.js:69`) і `kv.state.safe_mode=1`. О 17:10Z: fetch RSS каналу і перевірка, чи є відео, опубліковане після 16:55Z [?: RSS показує лише public, тож це правильний сигнал]. Деплой через `pult.yml`.
- Сесія на початку кожного run: `pultlib.send('/api/state', {})` уже існує [К pultlib.py:43]. Додати GET-читання `safe_mode` і `ops.breaker` → policy.

### 10.4 Daily Autonomous Operations Report
`python3 studio/ops.py report --date YYYY-MM-DD` → markdown у `docs/ops/report-YYYY-MM-DD.md` + 10–15 рядків у бот власнику (інформування). Джерела — лише `ops.sqlite`, `quota.log`, `analytics.sqlite`, тож звіт детермінований. Розділи:
1. **Що система зробила:** `runs` за добу (к-сть, OK/failed за задачами).
2. **Які рішення прийняла:** `agent_decisions` за типом (topic, approve, publish, seo, schedule…), топ-5 з обґрунтуванням.
3. **Які експерименти запустила, зібрала, вирішила:** `experiments`.
4. **Які публікації виконала:** `publications` змінені за добу (платформа, стан, external_url).
5. **Які помилки виявила:** `runs.error`, `pub_events → failed / in_doubt`.
6. **Які guardrails спрацювали:** policy BLOCK, RETRY_LATER, DEGRADE, CANARY з `rules_triggered`; breaker-події.
7. **Що потребує уваги:** `in_doubt`, OAuth <2 днів, неможливі rollback, розбіжності хешів, квота. Це інформування, система нічого не чекає.
8. **Гіпотези далі:** топ-3 з `experiments(status='designed')` + авто-кандидати: формат зі спадом медіани, рімейк-кандидати `ideas.remakes()` [К].

Запуск: у наявній задачі COO 20:27 Київ замінити вільний звіт викликом `ops.py report` (зміна промпту — Q10).

---

## 11. Мінімальний implementation plan

Принцип: кожен крок окремо корисний і окремо відкочується (`git revert`). Порядок обрано так, щоб журнал з'явився раніше, ніж блокування, а блокування спершу працювало в shadow.

| Крок | Що | Файли / функції (точно) | Деплой? | Ризик регресії | Коли |
|---|---|---|---|---|---|
| 0 | Нічого не міняти до 25.11 ~18:00Z (ep81 23.11, ep82 24.11, ep78 і гайд 25.11 17Z, OAuth 25.11 ~10:31Z) | — | — | — | — |
| 1 | `studio/ops.py` (новий модуль): `db()` з таблицями §5.1, §7.1, §8.1, §9, тригерами; `decide()`, `run_start/finish`, `verify`, `backfill`, `report`. `.gitignore`: `studio/data/ops.sqlite*` (живу базу не в git; знімок — так) | новий файл; `.gitignore` | ні (робоча копія) | **низький**: нічого не кличе ops | 26.11 |
| 2 | Бекфіл legacy: `uploaded.json`, `tiktok.json.posted_auto`, `pending_comments.json`, front matter → `publications(legacy=1)` | `ops.py backfill` (лише читання JSON) | ні | низький | 26.11 |
| 3 | `studio/policy.py` + `studio/policy.json` (`mode: "shadow"`), функції §3; `audit_vo.py --json` (додати вихід, поточний друк не міняти) | нові файли; `studio/eps/audit_vo.py` (кінець файлу) | ні | низький: shadow лише логує | 26–27.11 |
| 4 | Виклики gate в shadow: `yt.upload` (`yt.py:56`, перед рядком 61), `yt.schedule` (`yt.py:96`), `yt.comment` (`yt.py:106`), `yt.add_to_playlist` (`yt.py:113`), `tg.post`/`tg.video` (`tg.py:17–18`), `audit.fix` (`audit.py:159`), `post_comments.py:7` | ±1–3 рядки на функцію: `policy.gate(action)  # shadow: лише лог` | ні | **середній**: імпорт policy у `yt.py`, який імпортують усі. Помилка в policy не має ламати yt → обгортка `try/except → лог`, у shadow — завжди продовжувати | 27.11 |
| 5 | Ідемпотентність без зміни поведінки: `upload()` пише `uploaded.json` через `update_json` і `publications`; `session_ref` до PUT; `_find_recent_upload` при помилці → `RETRY_LATER` (зміна `yt.py:79`); `_req(tries=1)` для `commentThreads` і `playlistItems` POST; `tg.upload/call` → виняток при `ok:false` лише в `post`/`video` | `yt.py:56–88, 106–121`; `tg.py:16–18` | ні | **середній**: зміна семантики `tg.video` (виняток замість JSON) може зламати однорядкові виклики агентів, які читають `['result']['message_id']` → залишити повернення JSON і додати перевірку | 27–28.11 |
| 6 | `pubstate.py advance/rollback/reconcile` (новий CLI), заміна ланцюжка «вийшов» | новий файл; промпти one-shot нагадувань (Q10) | ні (код); промпт — зміна задачі | середній | 28.11 |
| 7 | 3–5 днів shadow → звіт «policy сказав vs факт» → `policy.json.mode="enforce"` | `policy.json` | ні | **середній–високий**: хибний BLOCK = пропущений слот. Мітигація: DEGRADE замість BLOCK для м'яких правил перший тиждень, резерв `reserve.json` (10 шт. [К AUDIT]) | ~2.12 |
| 8 | Хук-enforcement: `hook.py main()` — до `os.fork()` (рядок 53) синхронно `policy.check_tool(ev)` для `PreToolUse`. Якщо BLOCK → `print(reason, file=sys.stderr); sys.exit(2)`. Будь-який виняток → `exit 0` (fail-open для A/B), але для списку C/D/E-інструментів → `exit 2` (fail-closed) | `studio/pult/hook.py:43–60` | ні (хук читається з робочої копії при кожній події) [К `$CLAUDE_PROJECT_DIR/studio/pult/hook.py`] | **високий**: помилка = блок усіх інструментів або жодного. Тест на копії й список інструментів-винятків (Read, Grep, Bash-читання). Timeout хука 5 с (`settings.json`) — policy має відповідати <1 с | ~2.12 |
| 9 | `lake.py sql` → `mode=ro` | `lake.py:323–324` | ні | низький | будь-коли |
| 10 | Пульт: `scheduled()` watchdog, виняток `kind='decision'` для KEEP і purge, окремий секрет для `/api/purge` | `pult/worker.js:7, 21–24, 137–141, 174`, `pult/wrangler.toml` | **так** (push `pult/**` → `pult.yml`) | середній: вебхук бота в тому ж воркері. Помилка = бот мовчить → rollback `git revert` + автодеплой | ~3.12 |
| 11 | Experiments (§8) + guarded sections RUNBOOK у policy; growth-loop SKILL.md крок 6 → «запустити експеримент» | `ops.py`, `.claude/skills/growth-loop/SKILL.md:6` | ні | низький (текст скіла) | ~5.12 |
| 12 | CODEOWNERS / branch protection для policy-шляхів (Q1) | GitHub settings | GitHub | низький | рішення власника |

**Що працює без деплою:** кроки 1–9 і 11. Студійний Python виконується з робочої копії через симлінки `/home/claude/* → studio/*` [К], хук теж. GitHub Pages деплоїть лише сайт (`pages.yml`). Деплою потребують: воркер пульта (крок 10), IndexNow-фільтр у CI і нові GitHub Actions. **Важливо:** «без деплою» означає, що зміни діють одразу в єдиному продакшн-контейнері. Тестувати треба з `SHK_DRY_RUN=1` і на копіях JSON.

---

## 12. Тести

Тестів у репозиторії немає [К AUDIT §3]. Пропоную `studio/tests/test_policy.py` (pytest або unittest, stdlib) з фікстурами-копіями, без мережі.

**Policy (детермінізм і пороги):**
1. `ep82_factcheck_independent.md` (2 × `UNVERIFIED (не заявлено)`, `Вердикт: PASS`) → `fact=ALLOW` при `max_unverified_not_claimed=2`, `BLOCK` при 0. Також `high_risk` (калорії) → DEGRADE.
2. `guide1_factcheck_independent.md` (немає рядка `Вердикт:`) → BLOCK `fact.no_verdict`.
3. Факт-файл відсутній (ep80, ep78) → BLOCK; з `legacy` → DEGRADE(no_tiktok).
4. Слово «FAIL» у прозі («це не FAIL», ep82:20) не рахується як FAIL.
5. Таблиця з `| FAIL |` → BLOCK.
6. `replay`: для 20 збережених рішень `policy.py replay` дає ідентичний `policy_result` і `rules_triggered`.
7. Пороги з `policy.json` = `null` або `∞` → E (BLOCK + SAFE_MODE).

**Duplicate / idempotency:**
8. `yt.upload` з slug, що є в `uploaded.json` → BLOCK без мережі (мок `_req` рахує виклики = 0).
9. `_find_recent_upload` кидає виняток → RETRY_LATER, upload не викликається (регресія `yt.py:79`).
10. Симуляція збою: `publications.state='uploading'` + `session_ref`, мок PUT `bytes */N` → 201 з `{"id":"X"}` → `uploaded`, `uploaded.json[slug]=X`, жодного другого init.
11. Мок 500 на `commentThreads` POST → рівно 1 POST (tries=1), стан `in_doubt`, reconcile знаходить коментар → `published`.
12. `pubstate advance` двічі поспіль → другий запуск 0 зовнішніх викликів.
13. `tg.video` повертає `{"ok":false}` → стан `failed`, а не `published`.
14. TikTok-хук: `vidiq_social_post_publish` для slug із `posted_auto` → `exit 2`.

**Quality:**
15. `final.mp4` з тишею (ffmpeg `anullsrc`) → BLOCK `quality.silent`.
16. Відео 50 с для Short → DEGRADE, 200 с → BLOCK.
17. `voice_check` exit 1 → BLOCK.

**Bulk edit / triggers:**
18. `audit.py --fix` на мок-списку 93 відео → policy пропускає лише ≤14 днів і ≤10 штук. `input_snapshot` містить старі snippet. `rollback` відновлює їх бітово.
19. `update_trigger` для `protected_triggers` → BLOCK; з `experiment.promote` → ALLOW + snapshot старого промпту.
20. `delete_trigger` для recurring → BLOCK.

**Журнал:**
21. `UPDATE agent_decisions` / `DELETE` → `sqlite3.IntegrityError('append-only')`.
22. Ручна підміна рядка через новий файл БД → `ops.py verify` бачить розрив ланцюжка → T15.
23. `/api/purge` (на локальному `wrangler dev`) не видаляє `kind='decision'`.

**Breaker:**
24. 5 RuntimeError з `_req` за 30 хв → `youtube=open`; через cooldown → `half_open`; 3 probe OK → `closed`.
25. `quota.log` із сумою 9 100 → upload RETRY_LATER, T3.
26. `token.json` з `refreshed_at` = now − 6 днів → T4(а) DEGRADE + рядок у звіті (без виводу значень токена).

**Хук (найризиковіше):**
27. Подача JSON PreToolUse для `Read` → exit 0 <200 мс; для `Edit .claude/settings.json` → exit 2; зламаний `policy.json` → `Read` exit 0, `vidiq_social_post_publish` exit 2.
28. **Ручна перевірка в сесії** [?]: чи режим auto поважає `exit 2` PreToolUse для MCP-інструментів (один dry-run на безпечному MCP-виклику, напр. `vidiq_balance` у тестовому deny-списку).

**Наскрізний dry-run (до enforce):** `SHK_DRY_RUN=1 python3 studio/pubstate.py advance ep82_tier_kitchen` → JSON рішень для всіх платформ, 0 POST/PUT у `quota.log` (рядки лише GET).

---

## 13. Ризики та failure modes

**Знахідки, що підсилюють потребу в плані** (не всі є в AUDIT):
- **R1** `POST /api/purge` з `INGEST_TOKEN` (той самий, що в контейнері `studio/pult/.token`) видаляє журнал `ev`, крім `note`/`prompt` [К worker.js:21–24, 137–141]. Агент може стерти audit log. Це E-дія без захисту.
- **R2** `_req` повторює **будь-який** метод на 429/5xx, включно з POST `commentThreads` і `playlistItems` (`yt.py:26–33`) [К]. 5xx після фактичного запису дає дубль коментаря або елемента плейлиста.
- **R3** `yt.schedule()` робить резерв публічним за розкладом без жодної перевірки (`yt.py:96–99`) [К]. `upload_reserve.py` заливає `private` без дати і пише `reserve.json` напряму, без util (`upload_reserve.py:13`) [К]. Gate лише на upload пропустив би цей шлях.
- **R4** Лише 2 з 8 факт-файлів мають машинний `Вердикт:` [К]. Без уніфікації формату gate або все заблокує, або нічого не перевірить.
- **R5** PreToolUse-хук уже стоїть на всіх подіях, але не блокує (`fork` → `exit 0`) [К hook.py:53–60]. Це найдешевша точка enforcement, але й найнебезпечніша для регресії (крок 8).
- **R6** `lake.py sql` виконує довільний SQL на живій базі [К lake.py:323–324]. DDL у Python sqlite3 виконується без явного commit [? поведінка модуля sqlite3].

**Failure modes самого плану:**

| Ризик | Ймовірність | Наслідок | Мітигація |
|---|---|---|---|
| Хибний BLOCK у день виходу | середня | пропущений слот (KPI COO) | shadow 3–5 днів; DEGRADE замість BLOCK для м'яких правил; автопідстановка з `reserve.json` |
| Хук ламає всю сесію | низька–середня | агент не може навіть читати | fail-open для A/B-інструментів; тест 27; rollback = `git revert hook.py` (діє одразу) |
| Policy обходиться через Bash (`curl` напряму в API, `python3 -c "import urllib…"`) | середня | дія без gate | хук-регулярки на `api.telegram.org`, `googleapis.com/upload`, `youtube/v3/(commentThreads|playlistItems|videos)` у Bash; T15 + звірка `quota.log`/`pub_events` (дія без `pub_events` → T5-подібний алерт). Повністю закрити в одному контейнері неможливо |
| Агент редагує `policy.json` або `hook.py` | середня | guardrails вимкнено | хук deny + хеш-pin у DO (T15) + CODEOWNERS (Q1) |
| `ops.sqlite` зіпсовано або видалено | низька | втрата стану публікацій | щоденний `.backup` у snapshot + DO-хеші; `publications` відновлюються reconcile з API, `uploaded.json`, `tiktok.json` |
| Watchdog шле хибні тривоги вночі | середня | шум | вікно 05–21Z, поріг 3 год, ≤1 повідомлення на 30 хв |
| `in_doubt` у TG, і пост справді не вийшов | низька | пропущений TG-пост | краще пропуск, ніж дубль; звіт; наступний пост дня |
| Experiments надто повільні (дані з лагом 2–3 дні) | висока | стратегія змінюється рідше | це навмисно (CSO теж проти щотижневих змін [П AUDIT §11 п.6]); `ctr_72h`/`snap` для швидких сигналів |
| Компакція контексту сесії (896k/1M [К AUDIT get_session]) губить правила | висока | агент забуває викликати `ops.decide` | правила в коді, а не в промпті: gate вимагає `topic_select`/`script_generate` у журналі для content_id |
| OAuth Testing | висока (щотижня) | зупиняються YouTube, аналітика, GSC | T4 + Q2 |
| Конфлікт 25.11 17:00Z (ep78 + гайд #1) [П] | висока | канібалізація | у shadow буде видно; гайд ще не залито, тож policy в enforce дасть RETRY_LATER на ср-слот |

---

## 14. Питання, без яких не можна реалізувати правильно

Це одноразові налаштування порогів і меж. Жодне не є щоденним погодженням.

1. **Q1. Зовнішня межа для guardrails.** Дозволяєте увімкнути захист гілки main і CODEOWNERS (або хоча б обов'язковий CI-чек) для `studio/policy*`, `studio/pult/hook.py`, `.claude/**`, `pult/**`? Без цього агент із правом push технічно може вимкнути policy, і E-рівень лишиться «м'яким». Альтернатива без GitHub: лише хеш-pin у воркері + SAFE_MODE.
2. **Q2. OAuth «In production».** Переводимо consent screen із Testing, щоб refresh-токен не закінчувався щотижня? Інакше повна автономія неможлива: кожні 7 днів потрібен ваш клік (наступний — 25.11 ~10:31Z).
3. **Q3. Поріг UNVERIFIED.** 0 будь-яких UNVERIFIED, чи дозволити ≤2 «UNVERIFIED (не заявлено)» (твердження, якого немає в ролику, як в ep82)? Для high-risk тем — завжди 0?
4. **Q4. Денні ліміти.** Скільки Shorts на день — 1, 3 чи 4 (RUNBOOK суперечить сам собі)? Скільки TG-постів, TikTok і статей? Це верхні межі для rate-limit policy.
5. **Q5. Бюджети в грошах.** Денна межа токенів або $ на Claude, кредити vidIQ, TTS (зараз 10 запитів), квота YouTube (10 000 — це з документів; яка фактична в Google Cloud?).
6. **Q6. Legacy і ep78.** У ep78 (виходить 25.11 17Z) немає фактчек-файлу. Варіанти: дозапустити незалежного фактчекера до виходу, або вийти як legacy з DEGRADE (YouTube + сайт, без TikTok і TG). Також weekly2 і кліпи `cut6_*` без власних фактчеків: чи прив'язувати кліпи до фактчеку батьківського випуску?
7. **Q7. Порядок платформ і canary-вікно.** RUNBOOK:71 вимагає TikTok «у час виходу YouTube». Для безпеки пропоную TikTok через ≥60 хв після public на YouTube, бо rollback у TikTok, ймовірно, неможливий. Погоджуєте зміну, і яке вікно?
8. **Q8. Критерії автоматичного rollback опублікованого відео** (переведення в private). Лише за спростованим фактом і дублем, чи також за метриками (наприклад, `avg_pct` < 15% за 48 год)? Нагадую: видаляти заборонено, private — оборотно.
9. **Q9. Видалення повідомлень у групі TG.** Дозволяємо автономне видалення за правилами спаму (≤5/добу, з копією), чи понизити до «приховати або обмежити», або взагалі прибрати з автономії?
10. **Q10. Зміна промптів задач для впровадження.** Щоб policy запрацював, потрібно змінити тексти задач: «вийшов» → `pubstate.py advance`, COO-звіт → `ops.py report`, першим кроком кожної задачі `ops.py run start`. Це зміна triggers. Хто її робить: ви вручну, чи агент одноразово за цим планом із записом у журнал?
11. **Q11. Межа правок старих відео.** `audit.py --fix` і SEO: лише відео ≤14 днів, чи інший вік? Чи назви можна змінювати лише в експерименті? (RUNBOOK:11/:19 суперечать щоденному `--fix` по всіх.)
12. **Q12. Список high-risk тем** (здоров'я, гроші, діти, війна, вибори, юридичне, персональні дані) і реакція на них. Пропоную DEGRADE (YouTube + сайт, TG і TikTok лише після canary). Погоджуєте, чи для частини тем BLOCK?
13. **Q13. Сповіщення.** Чи прийнятні автоматичні повідомлення в бот при SAFE_MODE і щоденний звіт (10–15 рядків)? Як часто максимум?
14. **Q14. `/api/purge`.** Вимикаємо зовсім, чи переносимо на окремий секрет, якого немає в контейнері (лише у GitHub Secrets або у вас)?
15. **Q15. Сесії й ролі.** Чи дозволяєте винести COO, CSO і growth-loop з головної сесії в окремі субагенти з обмеженим набором інструментів (`.claude/agents/*.md` з `tools:`)? Це зміна permissions-конфігу. Без неї межі ролей тримаються лише на хуку, бо всі ролі — одна сесія з повним набором інструментів.
16. **Q16. Список джерел.** Підтвердіть tier-1, tier-2 і заборонені домени (§3.6), зокрема чи рахувати tier-1 офіційні блоги компаній про самих себе (CLAUDE.md: «цифри компаній про себе позначати як їхні»).
