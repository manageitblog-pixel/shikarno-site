# Сайт ШІкарно — shikarno.com.ua (стан на 23.10.2026)

## Що є
- Статичний сайт-блог: Python-генератор (Jinja2 + Markdown) → GitHub Pages. Без сервера, бази й адмінки — пости публікує Claude.
- Репозиторій: github.com/manageitblog-pixel/shikarno-site (public, гілка main). Пуш → GitHub Actions «Build and deploy» → сайт за ~1 хв.
- У репозиторії є CLAUDE.md і docs/content-guide.md — правила для Claude Code і Cowork (структура, front matter, SEO, тон).
- Домен shikarno.com.ua (реєстратор imena.ua, DNS-панель dnshosting.org): 4×A @ → 185.199.108–111.153, CNAME www → manageitblog-pixel.github.io., MX imena не чіпати. GitHub Pages: Custom domain shikarno.com.ua, DNS check successful (23.10). Enforce HTTPS — увімкнути, щойно GitHub випустить сертифікат.
- Розділи: /novyny/ (статті до Shorts), /rozbory/ (екстрені розбори), /dajdzhest/ (дайджест тижня), /za-misyats/ (ШІ за місяць), /teg/<tag>/. Тип задає kind у front matter; таймкоди (chapters) → «Зміст випуску» + Clip schema (ключові моменти відео в Google).
- Відкладена публікація: пост з датою в майбутньому з'являється сам (workflow ще й за cron кожні 30 хв) — дайджест можна залити в суботу з датою «неділя 12:00».
- Контент: розбір #1 PHP2Shell (7KYKPMVQiUI); 6 лонгрідів (еп. 1–6), кожен 600–1000 слів, з блоком «Коротко», таблицями, вердиктом Байта, FAQ і 2–3 джерелами.
- SEO: canonical, OG (static/og.png), JSON-LD NewsArticle + VideoObject + BreadcrumbList + FAQPage, Organization/WebSite, sitemap.xml, rss.xml, robots.txt, теги /teg/<tag>/, «Про нас» з редакційною політикою.
- Дизайн: бренд-бук (Montserrat 900 + Golos Text, жовта плашка «ШІ», Байт SVG), світла/темна тема. Прев'ю: артефакт «Прев'ю сайту ШІкарно».

## Доступи
- GitHub: fine-grained токен «shikarno-site» (лише цей репозиторій; Contents/Workflows/Pages RW; до 21.01.2027). Токен НЕ записувати в документи — в робочому середовищі /home/claude/gh/.token, після скидання середовища попросити у користувача ще раз.
- Права адміністратора репозиторію в токена немає: налаштування Pages/домену змінює користувач.
- Домени shikarno.com.ua і github.io закриті в мережі Claude — перевіряти сайт може лише користувач (або додати домен у Settings → Capabilities).

## Рішення користувача
- Semrush не використовувати (російське походження засновників) — від'єднати в Settings → Connectors.
- Пости мають бути широкими, якісними, з SEO-оптимізацією; сайт — швидкий і SEO-дружній.

## Щодня (крок автопілота після завантаження ролика)
1. Клонувати репозиторій (токен), `pip install -r requirements.txt`.
2. Написати content/posts/РРРР-ММ-ДД-<slug>.md за docs/content-guide.md: факти з першоджерел (ті самі, що для ролика + 1–2 додаткові), youtube: <id>, verdict такий самий, як у ролику.
3. `python3 build.py` (перевірити без помилок) → commit → push.
4. У пості Telegram давати посилання на статтю https://shikarno.com.ua/novyny/<slug>/ поруч із YouTube.

## Довгі формати на сайті (обов'язково разом з відео)
- Екстрений розбір → стаття kind: rozbir у той самий час, що й відео (900–1400 слів, таблиця «що робити», «чого не робити»).
- Дайджест #N → kind: dajdzhest, date = неділя 12:00, chapters з таймкодів meta.json, пункти з посиланнями на статті. Заливати в суботу разом із завантаженням відео.
- ШІ за місяць → kind: misyats, перший понеділок 19:00, 2000–3500 слів, розділи «ШІ у світі» / «ШІ в Україні» / тренди / цифри / що чекати.
- Дайджест #1 (3PkeNHJyqdQ, 25.10 12:00) — сценарію в середовищі вже немає: зробити статтю з таймкодів і опису відео (yt API) до 12:00 25.10.
- Статей ще немає для еп. 7–12 (хакер з ШІ-агентами, Gemini skills, AI Edge Foresight, PHP2Shell Short, Claude Duet, Walmart vs Amazon) — дописати.

## Далі (у черзі)
- Enforce HTTPS у GitHub Pages (користувач).
- Google Search Console: ресурс «Домен», TXT-запис в imena → надіслати sitemap https://shikarno.com.ua/sitemap.xml.
- Google Analytics 4 → вставити тег; читати статистику через Google API напряму (OAuth, scope analytics.readonly + webmasters.readonly), як YouTube API.
- Ключові слова: Ubersuggest (вже підключений у claude.ai) — за потреби.
- Посилання на сайт у профілі YouTube-каналу (Studio) і в закріпленому пості Telegram.
- Пізніше: коментарі через Telegram-групу, розділ дайджестів.
