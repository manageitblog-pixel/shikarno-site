# Плейбук Instagram Reels: як працює і що робимо ми (v1)

Дослідник алгоритмів, 24.11.2026. Акаунт ведемо з 23.11 (9 Reels). Позначки:
**[офіц.]** — Meta for Developers, about.instagram.com, заяви Адама Моссері (переказ у профільних медіа позначено окремо);
**[практики]** — досвід практиків (не факт); **[наші дані]** — `ig_snap` (36 знімків, 23.11 21Z – 24.11 08Z).
Публікація: зараз через vidIQ, далі — пряме Graph API (`meta-direct-api.md`).

## 0. Наші дані (знімок 24.11 08Z)

| Група | Reels | Відтворення | Сер. % перегляду | Skip rate (пішли за перші 3 с) | Збереження |
|---|---|---|---|---|---|
| Старі 4 (без обкладинки, 23.11 ~20:30Z) | 4 | 0–36 | 18–59 % | 56–80 % | 1 |
| Свіжі 5 (обкладинка 0,5 с першим кадром, ~21:15Z) | 5 | 8–57 | 2,5–8 % | **82–100 %** | 0 |

Обкладинка, вклеєна першими 0,5 с, — це статичний кадр, і з нього майже всі свайпають. 24.11 `ig_cover.py` переведено на 0,1 с. Повне рішення — `cover_url` через пряме API, тоді в самому відео обкладинки немає зовсім. Перевірка — недільне порівняння 29.11.

## 1. Офіційні правила

| # | Правило | Джерело | Тип |
|---|---|---|---|
| 1 | Три головні сигнали ранжування — **час перегляду, лайки, пересилання (sends)**. Метрики варто рахувати як частку від охоплення (likes per reach, sends per reach), а не в штуках. Для не-підписників пересилання важать трохи більше, для підписників — лайки. Точних ваг Meta не публікує. | Моссері, переказ: [Buffer 2026](https://buffer.com/resources/instagram-algorithms/), [Social Media Today](https://www.socialmediatoday.com/news/instagram-chief-post-share-rates-key-driver-reach/716540/) | офіц. (переказ) |
| 2 | **Skip rate** — частка переглядів, коли людина пішла за перші 3 с. Замінила старий view rate. Мета позначає метрику як оцінку. Що нижче, то краще. | [Social Media Today: retention insights](https://www.socialmediatoday.com/news/instagram-adds-retention-insights-reels/758464/) · [Metricool](https://metricool.com/instagram-reel-analytics/) | офіц. (переказ) |
| 3 | **Максимум 5 хештегів** на Reel чи пост, з 19.12.2025. Хештеги підказують тему, а охоплення помітно не додають. | [Social Media Today](https://www.socialmediatoday.com/news/instagrams-implementing-new-limits-on-hashtag-use/808309/) · [Business Today 19.12.2025](https://www.businesstoday.in/technology/news/story/no-more-hashtag-stuffing-instagram-limits-hashtag-usage-to-just-5-per-reel-and-post-507444-2025-12-19) | офіц. (переказ) |
| 4 | **Оригінальність.** Акаунти, що переважно викладають чужий контент, не рекомендуються. З 30.04.2026 правило діє і для фото та каруселей. Ремікс зі своїм внеском дозволено. | [PetaPixel 30.04.2026](https://petapixel.com/2026/04/30/new-instagram-policies-target-reposted-content/) | офіц. (переказ) |
| 5 | **ШІ-контент** не банять і охоплення за саму «ШІ-шність» не ріжуть, але просять самим позначати ШІ. Ми вмикаємо мітку ШІ, як у TikTok (§1 п.7 `tiktok.md`). | [Metricool: Instagram news, 13.11.2026](https://metricool.com/instagram-news/) | офіц. (переказ) |
| 6 | **API:** `cover_url` — обкладинка для вкладки Reels, має пріоритет над `thumb_offset` (мс кадру). `share_to_feed` — показ і в стрічці, і в Reels. `trial_params.graduation_strategy` = `MANUAL` або `SS_PERFORMANCE`: Trial Reels через Content Publishing API, з 03.12.2025. | [IG User Media reference](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/media.md) · [Meta changelog](https://developers.facebook.com/docs/instagram-platform/changelog) | офіц. |

**Офіційні зміни за 23–24.11:** нових постів про Reels і алгоритм на about.instagram.com не знайдено (нагорі «Instagram on iPhone Duo», «Instagram Plus»). Правила вище — чинні.

## 2. Лайфхаки практиків (24.11) — **досвід практиків**

| # | Порада | Цифра / кейс | Джерело, дата | Довіра |
|---|---|---|---|---|
| П1 | **Перший кадр = текст-твердження з ключем**, а не статичний титр чи обкладинка. | Reels із хуком «текст-твердження на екрані» — медіана 1,12× звичних переглядів автора (33 Reels, 9 авторів). | [Outfame Reels Report](https://www.outfame.com/reels-report/hooks/on-screen-text-claim) | середня (мала вибірка) |
| П2 | **Trial Reels для малого акаунта**: ролик спершу бачать лише не-підписники. | Акаунт зі 100–200 підписниками: «помирав» на 200 переглядах, із trial — тисячі; 200 → 260 підписників за 2 trial. | [Reddit r/InstagramMarketing, 03.06.2026](https://www.reddit.com/r/InstagramMarketing/comments/1tvtzp0/broke_my_200_view_curse/) | низька (один кейс) |
| П3 | **Не перезаливати старі ролики як trial.** Після 20.10.2026 «повтори» старих trial провалилися. | Акаунт 400K: був +2K підписників/день, став −80/день. | [Reddit, 30.10.2026](https://www.reddit.com/r/InstagramMarketing/comments/1xj3xey/trial_reels_really_have_changed_400k_account/) | низька (один кейс), узгоджується з офіц. п.4 |
| П4 | **Хештеги не рятують охоплення**: 3 конкретні теги замість 5 загальних. | Metricool: пости з хештегами — −32 % переглядів і −34 % взаємодій (кореляція, не причина). | [Metricool DE, тренди 2026](https://metricool.com/de/instagram-trends-2026/) | середня |
| П5 | **Обкладинку бачать у профілі й вкладці Reels, а не в стрічці.** У стрічці глядач бачить кадр 0 у русі, тож обкладинка там не допомагає утримати. | Без цифр: механіка трьох розмірів показу. | [cut.pro 2026](https://cut.pro/en/blog/clip-thumbnail-first-frame-retention-2026) | низька |

## 3. Що робимо (з 24.11)
1. **Кадр 0** (Пропозиція дня 24.11): живий Байт у русі + текст-твердження з пошуковим запитом із 0,0 с. Без статичного титру. Ціль — skip rate < 70 %.
2. **Обкладинка** — лише `cover_url` (пряме API, `meta-direct-api.md`). До переходу — 0,1 с, без зміни решти кадру 0.
3. **Підпис:** 1-й рядок — запит, як його шукають. 2-й — «🎁 50 промптів — Telegram у профілі» (рішення TG-відділу 24.11). 3 конкретні хештеги (≤5, офіц. п.3). Заклик «збережи» або «А чи Б?», без «перешли» (правило власника).
4. **Пересилання** не просимо, але даємо привід переслати: «перевір, чи твій … » (практична користь для когось іншого).
5. Метрики з `ig_snap` рахуємо **на охоплення**: saves/plays, skip_rate, avg_watched_pct. Перші висновки — через 7 днів (30.11).

## 4. Експеримент тижня (designed) — `exp-2026-11-24-ig-trial-reels`
- **hypothesis:** нові оригінальні Reels, опубліковані як Trial (`SS_PERFORMANCE`), за 72 год наберуть ≥2× медіани відтворень звичайних Reels того ж тижня.
- **variant:** 3 нові Reels 30.11–6.12 із `trial_params`, `cover_url` і новим кадром 0. Лише нові ролики, без повторів (П3).
- **control:** 3 звичайні Reels того ж тижня (чергування через день), та сама обкладинка й той самий шаблон кадру 0.
- **success_metric:** plays за 72 год (`ig_snap`), плюс skip_rate і avg_watched_pct.
- **threshold:** медіана варіанта ≥2× контролю, skip_rate не гірший більш ніж на 5 п.п.
- **guardrail:** 0 позначок «неоригінальний» чи знять. Підписники не падають. Ліміт Trial Reels в API не перевищено.
- **sample_size:** 6, max_share 0,5, kind `format`.
- **Що треба для старту:** (а) перехід Reels на пряме Graph API (`meta-direct-api.md`), бо vidIQ `trial_params` не передає. (б) Тестовий виклик із `trial_params`: якщо акаунт не допущено до Trial Reels, API поверне помилку, тоді експеримент → `pause`. (в) Старт не раніше 30.11, після недільного порівняння обкладинок, щоб ефекти не змішалися. З активними (frame0 = Shorts, yt-related-cta-v2, tg-specific-cta, seo-*) не перетинається.
