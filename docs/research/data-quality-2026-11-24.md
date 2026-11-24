# Якість даталейку, експерименти, ops — 24.11.2026 (~20:30Z)

Аналітик даних. Попередні звіти: `data-quality-2026-11-22.md`, `data-quality-2026-11-23.md`. Що там уже описано й не змінилось, тут не повторюю.
Джерела фактів: `studio/data/analytics.sqlite` (лише читання), `studio/data/ops.sqlite`, YouTube Data API `videos.status` (24.11 ~20:25Z), HTTP-коди сторінок сайту.
**Записи:** лише в `ops.sqlite`, 7 переходів `scheduled → published` через `ops.transition()` (розділ 3). В `analytics.sqlite` нічого не писав.

## 1. Даталейк

### Що виправлено з 23.11 (іншими агентами, перевірив)
- `cf_store`: точний день (`sampled=0`) більше не затирається семпльованим (`where excluded.sampled=0 or site_rum_daily.sampled=1`).
- Telegram пишеться в `tg_daily` з `growth_snapshot.telegram()`, тобто не залежить від YouTube-sync. Є 3 дні поспіль: 22–24.11, по 6 учасників.
- `growth_snapshot.tiktok()` і `hq_data` рахують TikTok за всіма відомими відео (останній знімок кожного id).
- `load_overrides` пропускає лише ключі `_comment*`, тож override clip2 `_wp0rz8edB8` (id починається з «_») працює.

### Стан таблиць
| таблиця | стан 24.11 | проблема | серйозність |
|---|---|---|---|
| `daily` / `traffic_daily` | 800 / 1393 рядки, 21.10–21.11, 32 дні **без пропусків дат** | Дублів немає (PK). Затримка 3 дні: це норма Analytics | — |
| `channel_daily` | 42 рядки, 25.07–21.11 | **78 пропущених дат**: 25.07 з 0 переглядів, далі поодинокі серпневі дні, суцільно лише з ~12.10. Це не дірка в зборі: в API немає днів без переглядів. Для рядів «до/після» беріть ≥21.10 або доповнюйте нулями | низька |
| `site_daily` | 27 днів, 27.10–22.11, без пропусків | — | — |
| `snap` | 22–24.11, 93→96 відео | Монотонно, падінь немає. ep82 і clip2 (публічні з 24.11 17Z/13Z) ще не в `videos`: останній sync був раніше 13Z. Підтягнуться наступним sync | — |
| `tiktok_snap` | 13 знімків, 22.11–24.11T16 | **1) Нове:** у знімку 24T16 сума за 7 відео = 1 662, бо Сяйво (5 200) і пам'ять ChatGPT (4 900) випали з першої сторінки vidIQ. Сума за останнім знімком непридатна, а «всі відомі» (growth/hq) коректні. **2)** Перший знімок `2026-11-22` без години: fetched 17:55Z, тобто він справді найстаріший. Сортування не ламає, лишаю. **3)** Неповнота акаунта (~12–13 відомих id) без змін з 23.11. Падінь переглядів по відео немає | середня (без змін) |
| `ig_snap` | 6 знімків 23T21–24T16, 10 Reels | Монотонно. Новий Reel DgIDsZ-AaNV (24.11 13:28Z) є лише в 1 знімку | — |
| `ig_account` | 6 рядків | `views_30d`/`reach_30d` NULL у 4 з 6: це не помилка, `account_response` є лише у 23T21 і 24T08 (збирач бере mode=account не щоразу). Followers 4→7 о 16Z (з `reels_response.followersCount`). У рядах «перегляди 30 днів» брати лише рядки з `views_30d is not null` | низька |
| `tg_daily` | 3 рядки | Ряд іде. Δ = 0 | — |
| `site_rum_daily` | 15 днів, 10–24.11 | Фікс sampled діє. Лишилось: **рядок поточного дня (24.11: 8/4) частковий і не позначений**. 10.11 уже за вікном CF (updated 23.11), тож далі не зміниться | низька |
| `posts` | 108 | — | — |

### `format_overrides.json` проти `videos.format`
Розбіжностей **0**: усі 16 override, що вже є в `videos`, застосовані. `6mIdp843fKo` (clip3) і `M-KQwpDwpA4` (guide1) ще приватні, тож у `videos` їх немає: override спрацює після 25.11. Невідомих форматів немає. Евристика за slug (`clip*/cut*`→clip, `guide*`, `_tier_`, `_prof_`, `weekly*`) проти `format` теж без розбіжностей.
Порожній `slug` досі у 2 роликів: `6h_3_wnO3Z0` і `theMaZ3jGR4` (з 22.11). Їх немає в `uploaded.json`, тож це ручне завантаження, і виправляти треба там.

## 2. Експерименти (`ops.py exp list`: 5 running, 14 designed)

| експеримент | плечі в `experiment_items` | дати: ops vs strategy.md | метрика | проблема |
|---|---|---|---|---|
| **frame0** | control 10, variant 3/5 (ep82, ep84, ep86) | 24–29.11 = strategy | є (`daily`, `traffic_daily`, `avg_pct`) | **ep83 і ep85 не залиті**: `uploaded.json` = null, картки youtube немає, тож у варіант їх не додано. Перед 26/28.11 потрібна заливка + `exp add` |
| **yt-related-cta** (заморожений CSO 24.11) | control 5 (ep82–86), variant 0 | 30.11–06.12 | є | Status досі `running`, вердикт не рахуємо (`strategy_change` 5b980a0b). ep83/ep85 у контролі без публікацій. Як оформити — нижче |
| **yt-related-cta-v2** | control 1 (ep82), variant 4 (ep83–86) | 24.11–04.12, вердикт 13.12 = strategy | є (RELATED_VIDEO у `traffic_daily`) | **strategy §24.11 пише «ep83–86 уже залиті й готові», але залиті лише ep84 (RIt-PqOGJTg, 27.11 17Z) і ep86 (xYez8pJmL4E, 29.11 17Z)**. ep83/ep85 без id. Контроль 30.11–04.12 ще не додано (так і задумано) |
| **seo-title-ctr** | 4/4 | start 23.11 = strategy; **`end_date` NULL** | частково (GSC page×date для DiD не в лейку) | **Ключі не збігаються:** 2 контролі (`claude-bezkoshtovno`, `gemini-dlya-studentiv-bezkoshtovno`) записані slug-ом, а в `publications` ці сторінки мають content_id `ep22_claude_free` і `ep18_gemini_students`. Join `experiment_items` ↔ `publications` губить 2 з 8. Збирачу брати slug із `external_id` |
| **tg-specific-cta** | control 10, variant 5 | start 23.11 = strategy; **`end_date` NULL** (strategy: оцінка 29–30.11) | частково: `tg_daily` іде, а відповіді на коментарі за 72 год і перегляди поста №37 не збираються | clip1 без `scheduled_at`. Варіант ep78 (Rlm1u-I6x00): у YouTube `publishAt` = **25.11 15:00Z**, а в ops/на сайті 17:00Z. Перший коментар (`pending_comments`) теж о 15:00Z, тож 72 год рахувати від 15:00Z |

**Загальне:** `publications.experiment_id` — одне поле, і воно ненадійне. ep82 є у 4 експериментах, а в полі стоїть лише tg-specific-cta. У ep84/ep86 поле NULL, бо `exp add` виконали до того, як backfill створив картку (UPDATE зачепив 0 рядків). Джерело правди — `experiment_items`.

### Як CSO може оформити заморожений yt-related-cta
`ops.py exp redesign … --set status=…` **не спрацює** (перевірено на копії БД): `status` не входить у поля дизайну, а `redesign` дозволений лише в `designed`. Те саме з `end_date` для running seo/tg. CLI для `running → collecting/decided` немає. Варіанти:
1. **(рекомендую, DE)** Додати в ops.py `exp close ID --decision pause --reason … [--result …]`: `running → decided`, `decision='pause'`, `decision_id` = рядок `agent_decisions(experiment)` з before/after. Тригер `exp_frozen` це дозволяє, бо status/decision/result у ньому не заморожені. Тим самим шляхом (`exp set-end ID --date`) ставити `end_date` для running.
2. До того: CSO вже записав рішення (`strategy_change` 5b980a0b). Ручний `update experiments set status='decided', decision='pause'` технічно проходить, але обходить журнал. Без `decide` поруч цього не робити.

## 3. ops.sqlite: `verify` і публікації

`python3 studio/ops.py verify` → `ok: true`, 88 decisions, 328 events, `errors: []`. Додатково перевірив: стан кожної картки = `to_state` її останньої події, подій-сиріт немає, дублів youtube `external_id` немає.

**Чому backfill не оновлює ep82:** `backfill()` → `pub_create()` повертає False, якщо картка `(content_id, platform)` уже є («існуюча не чіпається», за задумом). Переходів він не робить. Картку ep82/youtube (legacy=0) створив finalize о 22.11 19:19Z зі станом `scheduled`, а кроку reconcile «publishAt минув → published» ще немає (крок 4 плану, після 25.11 18Z). До 20:25Z **жодна картка ніколи не змінювала стан**: publications 321 = pub_events 321.

**Виправлено** (`ops.transition`, ребро `scheduled → published`, reason з доказом):
- youtube: ep80_prof_olx, ep81_tier_kids, clip2, **ep82_tier_kitchen**. API: `privacyStatus=public`, publishedAt 22.11 17:00:24Z / 23.11 17:00:01Z / 24.11 13:00:12Z / 24.11 17:00:19Z.
- website: ep80, ep81, ep82. Сторінки `/novyny/…/` віддають HTTP 200.
Після цього `verify` ok.

**Не чіпав, бо немає підтвердження з першоджерела** (кому: DE/COO):
- `yt_comment` scheduled з минулим часом: ep80, ep81, clip2, ep82. `bvS0k_r3_bs` і `_wp0rz8edB8` досі в `pending_comments.json`, тобто коментар, схоже, ще не опубліковано. Перевірити постер коментарів.
- `tiktok` scheduled з минулим часом: ep30_tier_home (22.11 13:30Z), clip2, ep82. У `tiktok_snap` id — це числові TikTok id, а в ops — UUID vidIQ, тож зіставити автоматично не можна.

**Пропоную DE (крок 4):** `ops.py reconcile`: для `youtube` scheduled з `scheduled_at < now` викликати `videos.status`, при `public` робити transition; для website — HTTP 200. Інакше `exp status` і звіти показують `scheduled` у вже вийшлих роликів. Також `runs` = 0: жоден агент не пише `run start/finish`, тож усі 88 рішень мають `run_id`, якого немає в `runs`.
