# Плейбук Google Search — shikarno.com.ua (22.11.2026)

Хто: SEO/КМ (рішення делеговані власником 22.11). Першоджерела перевірено 22.11.2026 (WebFetch/WebSearch).
Позначки: **[О]** — офіційно (Google Search Central / blog.google / Search Status Dashboard), **[П]** — досвід практиків (не факт, гіпотеза), **[Д]** — наші дані (studio/data/analytics.sqlite).

## 0. Де ми зараз [Д]
- Search Console, 27.10–20.11 (site_daily, 25 днів): **3 669 показів, 43 кліки, CTR 1,2 %, середня позиція 7–8**. Останні 10 днів — 130–200 показів/день, 0–5 кліків.
- Сторінки (site_pages, 1.10–20.11): `chatgpt-bezkoshtovno-v-ukraini` 1 138 показів / 11 кліків / поз. 6,8; `yak-vidklyuchyty-gemini` **533 / 0 / 6,9**; `claude-bezkoshtovno` 389 / 7 / 5,6; `anthropic-ipo` 349 / 4 / 6,7; `shcho-take-shtuchnyi-intelekt` 245 / 1 / 27,6; `yak-skachaty-chatgpt` 236 / 1 / 8,0. Найкращий CTR — `promty-dlya-chatgpt` 5,2 % і `mono-keshbek-shi` 3,8 %.
- Висновок: покази й позиції вже є (топ-10), **проблема — кліки**. На позиції 6–8 CTR 0–1 % — це сніпет/заголовок, які не перемагають сусідів, AI Overview і блоки «Схожі запитання».
- Обережно з тижневою таблицею: site_queries_weekly за W47 = 25 показів проти ~150/день у site_daily — тиждень неповний або запити анонімізовані (див. docs/research/data-quality-2026-11-22.md). Рішення — лише за site_daily і site_pages.
- **November 2026 core update** стартував 10.11 о 10:06 PT, «applies globally and to all languages», до 2 тижнів, тобто ≈ до 24.11 [О: Search Status Dashboard; дату старту бере SEJ]. Google радить не робити висновків, доки розгортання не завершиться → **жодних порівнянь «до/після» до 25.11**.
- **23.11 (дослідник алгоритмів):** [Search Status Dashboard](https://status.search.google.com/summary) — core update від 10.11 **ще без дати завершення**, нових інцидентів сканування, індексації чи показу в листопаді немає. Нових постів у Search Central Blog за 24 год не знайшли. Порівняння «до/після» досі не робимо: перше — через 2 тижні після оголошеного завершення [О].

## 1. Правила «роби / не роби»

| # | Правило | Позначка | Джерело |
|---|---|---|---|
| 1 | **Роби** контент «для людей»: перевір себе питаннями Who / How / Why. Why важить найбільше: стаття має бути корисною тому, хто прийшов напряму, а не написаною заради трафіку з пошуку. | О | [Creating helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) |
| 2 | **Роби** «Who» і «How»: підпис автора там, де читач його чекає, і чесне пояснення, як зроблено текст, **зокрема чи використано автоматизацію/ШІ**. Вигадані автори й регалії — це обман. У нас «автор» — Organization, і про ШІ на сторінках не сказано → додати сторінку «Як ми працюємо» і рядок під статтею. | О | там само |
| 3 | **Не роби** «свіжих» дат без суттєвих змін (`updated` ставимо лише після реальної правки). Google прямо називає це ознакою контенту, написаного заради пошуку. | О | там само |
| 4 | **Роби** унікальне, не «комодіті»: власний тест, ціни в гривнях, «чи доступно в Україні», скріншоти. Переказ англомовної новини програє оригіналу. | О | [AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) |
| 5 | **Не роби** масових сторінок під варіації запиту («чат gpt українською», «gpt українською безкоштовно» окремими статтями). Це може порушувати політику scaled content abuse → одна сильна сторінка + H2 під підзапити. | О | там само |
| 6 | **AI Overviews і AI Mode:** окремих вимог чи розмітки немає. Достатньо, щоб сторінка була проіндексована й могла показуватися зі сніпетом. Перехід з AI-функцій рахується в загальному трафіку Search Console. **Не вмикай** `nosnippet` / `max-snippet:0`, бо це вимикає сторінку з AI-відповідей. У нас `max-snippet:-1` ✅. | О | [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features) |
| 7 | **Знай:** Google Search **не використовує llms.txt**, «AI-файли» і Markdown-копії. Вони не допомагають і не шкодять у Google, але можуть знадобитися іншим сервісам. Нарізати текст на дрібні шматки й переписувати «під ШІ» теж не треба. llms.txt лишаємо (безкоштовно, для ChatGPT/Perplexity), але **не рахуємо його SEO-роботою**. | О | [AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) |
| 8 | **Роби** вимірювання ШІ-видимості через **звіт про генеративний ШІ в Search Console**: покази і сторінки в AI-відповідях, по країнах. Перевір перемикач участі сайту в generative AI features: його має бути увімкнено. З 31.08.2026 він доступний усім сайтам. Не вір стороннім інструментам, що «бачать внутрішні метрики Google». | О | [blog.google, 3.06/31.08.2026](https://blog.google/products-and-platforms/products/search/new-opportunities-control-and-insights-for-website-owners/); AI optimization guide |
| 9 | **Title link:** title має бути унікальним, описовим і стислим, бо довгий обрізається. Бренд став коротко на початку або в кінці через роздільник. Без набивання ключами. Google переписує title, якщо той застарів (стара дата при новому H1), неточний, повторюється на кількох сторінках або дублює назву сайту. У нас title 75–90 знаків + « \| ШІкарно», тож у видачі він обрізається. | О | [Title links](https://developers.google.com/search/docs/appearance/title-link) |
| 10 | **Сніпет:** Google здебільшого бере текст зі сторінки. Meta description він використовує, коли той точніше описує сторінку. Тому **перший абзац = пряма відповідь**, а description має бути унікальним, конкретним і підсумовувати всю сторінку, а не бути списком ключів. | О | [Snippets](https://developers.google.com/search/docs/appearance/snippet) |
| 11 | **FAQ rich results більше немає:** з 7.05.2026 Google їх не показує, документацію прибрано 15.06.2026. Видимий блок FAQ лишаємо, бо він корисний людям і дає готові відповіді, але **не чекаємо від FAQPage розширеного сніпета** й не вкладаємо в нього роботу. | О | [FAQPage docs](https://developers.google.com/search/docs/appearance/structured-data/faqpage) |
| 12 | **Article-розмітка:** author — `Person` для людей, `Organization` для організацій. Кожен автор окремим об'єктом, `author.url`/`sameAs` вказує на сторінку автора, дати в ISO 8601 з часовим поясом. Зображення репрезентативні, не логотип: 16×9, 4×3, 1×1, ≥ 50 тис. пікселів. У нас author = Organization (чесно, бо пише редакція з Байтом), але image — текстова OG-картка 1200×630 (+ превʼю YouTube 4:3 у статтях з відео), без 1×1. | О | [Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article) |
| 13 | **Відео:** відео-функції пошуку — для **watch-сторінок**, де головне на сторінці — одне відео. Стаття з вбудованим роликом watch-сторінкою не є. Ключові моменти: Clip-розмітка або таймкоди в описі YouTube. → VideoObject лишаємо, але розширених відеосніпетів для статей не чекаємо. Таймкоди в описах YouTube працюють на YouTube-результати. | О | [Video SEO](https://developers.google.com/search/docs/appearance/video) |
| 14 | **Discover:** велике зображення ≥ 1200 px, 16:9, `max-image-preview:large`. Зображення репрезентативне, **не логотип і не графіка, перевантажена текстом**. Заголовки без клікбейту, без приховування суті. Наші OG-картки — текстові, тож це ризик для Discover. | О | [Google Discover](https://developers.google.com/search/docs/appearance/google-discover) |
| 15 | **Google News / Top stories:** подавати заявку не треба. Придатність визначається автоматично, якщо сайт дотримується правил щодо контенту, а Publisher Center більше не додає публікацій. News sitemap: лише статті за 2 дні, ≤ 1 000 `<news:news>`, обов'язкові теги publication/name/language/publication_date/title. У нас news-sitemap.xml за 48 год ✅. | О (sitemap) / П (автоматичні сторінки публікацій — вторинні джерела) | [News sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap); [Google News help](https://support.google.com/news/publisher-center/answer/15898024) |
| 16 | **IndexNow Google не підтримує**: офіційної підтримки немає, тест був у 2021. Для Google працюють sitemap і URL Inspection у Search Console. IndexNow лишаємо для Bing, Copilot і Yandex-сумісних рушіїв. | П (Google офіційно не коментує) | [seroundtable](https://www.seroundtable.com/google-indexnow-32396.html), [Wikipedia: IndexNow](https://en.wikipedia.org/wiki/IndexNow) |
| 17 | **Практики:** на запити з AI Overview CTR органіки на тих самих позиціях помітно нижчий. Кліки краще тримають сторінки, що обіцяють те, чого немає в огляді: власний тест, таблицю цін у гривнях, покрокові скріни. | П | узагальнення галузевих оглядів, не офіційно |

## 2. Що вже робимо / чого ні

**Робимо ✅:** canonical; `max-image-preview:large`, `max-snippet:-1`; NewsArticle з datePublished і dateModified з поясом; BreadcrumbList; VideoObject + Clip; sitemap + news-sitemap (48 год) + rss; robots.txt пускає ШІ-ботів; llms.txt; IndexNow (Bing); OG 1200×630; «Коротко» і FAQ; ключ у title; оновлення замість дублів (`updated`); хаби тегів.

**Не робимо / робимо не так ❌:**
1. Title довгі (75–90 знаків + бренд) і з повторами («Чат GPT українською безкоштовно… — гайд 2026»). Звідси CTR 0–1 % на позиції 7 [Д].
2. Немає «Who/How»: ні підпису редакції, ні розкриття, що тексти готуються з ШІ й перевіряються за джерелами [О, правило 2].
3. Звіт про генеративний ШІ й перемикач участі в Search Console не перевіряли. У site_* цих даних немає.
4. OG-картка текстова, немає репрезентативного фото/скріну і формату 1×1 [О, правила 12 і 14].
5. Немає блоку «Байт перевірив» з власним тестом і скрінами, а саме це дає «не-комодіті» [О, правило 4].
6. docs/seo-strategy.md §5 радить «заявку в Google News (Publisher Center)», але це застаріло [О, правило 15].
7. В оцінках FAQPage досі рахується як «rich result», хоча Google його вже не показує [О, правило 11].

## 3. Три зміни з найбільшим очікуваним ефектом (експерименти, status = designed в ops.sqlite)

Старт — не раніше **25.11** (після core update). Код сайту не чіпаємо: для G1 і G3 досить правок у front matter і тексті статей, G2 — шаблон блоку в content-guide. Окремою задачею.

### G1 · `exp-2026-11-22-seo-title-ctr` (kind: metadata)
- **hypothesis:** на сторінках із ≥ 200 показами і позицією 5–9 CTR 0–1 % дає title, що обрізається й повторює ключ, та description без чіткої обіцянки. Коротший title (≤ 60 знаків до « | ШІкарно», відповідь або вигода на початку) і перший абзац-відповідь підіймуть CTR без втрати позиції.
- **variant:** `yak-vidklyuchyty-gemini`, `chatgpt-bezkoshtovno-v-ukraini`, `anthropic-ipo`, `yak-skachaty-chatgpt`: новий title ≤ 60 знаків, description 140–160 знаків з конкретикою («3 кроки», «без VPN», «ціни в грн»), перший абзац — відповідь за 1–2 речення.
- **control:** `claude-bezkoshtovno`, `gemini-dlya-studentiv-bezkoshtovno`, `chomu-ne-pratsyuie-chatgpt`, `chatgpt-vs-gemini-vs-claude` без змін.
- **success_metric:** CTR сторінки в GSC, 28 днів після проти 28 днів до, різниця-в-різницях з контролем.
- **threshold:** CTR варіанта ≥ +0,8 п.п. (і ≥ ×1,5) відносно приросту контролю, середня позиція варіанта не гірша на > 1,0.
- **sample_size:** 8 сторінок (4 + 4). guardrail: покази варіанта ≥ 0,8× бази.

### G2 · `exp-2026-11-22-seo-firsthand` (kind: format)
- **hypothesis:** блок «Байт перевірив» (власний тест: що зробили, скрін, результат, дата, ціна в грн / чи доступно в Україні) робить статтю «не-комодіті». Такі статті за 14 днів отримують більше показів і кліків, ніж переказ новини.
- **variant:** 6 нових статей-новин і гайдів з блоком «Байт перевірив», 2+ власні скріни.
- **control:** 6 найближчих за часом статей тієї ж рубрики без блоку.
- **success_metric:** медіана показів і кліків сторінки за перші 14 днів (site_pages за період).
- **threshold:** медіана показів варіанта ≥ 1,5× контролю і кліки ≥ контролю.
- **sample_size:** 12 статей.

### G3 · `exp-2026-11-22-seo-hub-refresh` (kind: strategy)
- **hypothesis:** якщо сторінку з позицією 8–30 суттєво оновити (новий H2 під підзапит із GSC і таблицю) і поставити на неї 3+ внутрішні посилання з нових статей, вона підніметься в топ-5 і збере більше показів, ніж аналогічна сторінка без змін.
- **variant:** `shcho-take-shtuchnyi-intelekt` (поз. 27,6), `promty-dlya-chatgpt`, `claude-code-shcho-tse`: суттєве оновлення, `updated` лише після реальної правки, 3+ нових внутрішніх посилань з анкором-запитом.
- **control:** `gemini-skills-zamist-gems`, `claude-5-5-opus-sonnet-haiku`, `mono-keshbek-shi` без змін.
- **success_metric:** зміна середньої позиції і показів, 28 днів після проти 28 днів до, різниця з контролем.
- **threshold:** позиція варіанта покращилась ≥ 3 місця проти контролю, а покази ≥ ×1,3.
- **sample_size:** 6 сторінок.

## 4. Ритм
- Щопонеділка: site_daily + site_pages → сторінки з ≥ 100 показами і CTR < 1 % → кандидати в G1-хвилю 2.
- Раз на місяць: звіт про генеративний ШІ в GSC + 10 питань в асистентах (seo-strategy §7).
- Після кожного core update — 2 тижні без висновків, потім порівнюємо рівні вікна.
