# Сайт ШІкарно — shikarno.com.ua (стан на 23.10.2026, вечір)

## Що є
- Статичний сайт-блог: Python-генератор (Jinja2 + Markdown + Pillow для OG-карток) → GitHub Pages, HTTPS увімкнено. Без сервера, бази й адмінки — пости публікує Claude.
- Репозиторій: github.com/manageitblog-pixel/shikarno-site (public, main). Пуш → GitHub Actions «Build and deploy» (build → deploy → indexnow), ~1 хв; ще й cron кожні 30 хв для відкладених постів.
- Пам'ять у репо: CLAUDE.md, docs/content-guide.md, docs/seo-strategy.md (SEO + потрапляння у відповіді ШІ), docs/RUNBOOK.md (актуальний автопілот), docs/project-state.md (цей файл), docs/tasks/ (відкриті задачі).
- Домен shikarno.com.ua (imena.ua, DNS у dnshosting.org): 4×A @ → 185.199.108–111.153, CNAME www → manageitblog-pixel.github.io., MX imena не чіпати. GitHub Pages: custom domain + Enforce HTTPS.
- Розділи: /novyny/, /rozbory/, /dajdzhest/, /za-misyats/, /teg/<tag>/ (хаби з вступом — config.TAG_INTRO), /pro-nas/ (редакційна політика), /spivpratsia/ (реклама й партнерства).
- Відкладена публікація: date у майбутньому → стаття з'явиться сама в цей час.
- Опубліковано: еп.1–9 (статті 600–1000 слів), розбір #1 PHP2Shell; заплановано: еп.11 Claude Duet (24.10 13:00), еп.12 Walmart vs Amazon (24.10 19:00) — без youtube ID, додасть Cowork.
- Кожна стаття: «Коротко», таблиці, практичний блок, вердикт Байта, FAQ (FAQPage), 2–3 джерела, внутрішні посилання, блок «Обговорення» (віджет Telegram за telegram_post або кнопка), OG-картка 1200×630.
- SEO: canonical, robots max-image-preview, JSON-LD NewsArticle/VideoObject(+Clip)/Breadcrumb/FAQPage/Organization, sitemap.xml, news-sitemap.xml, rss.xml.
- ШІ-пошук (GEO): robots.txt явно дозволяє GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended, Bingbot та ін.; /llms.txt генерується автоматично; IndexNow повідомляє Bing (Copilot, пошук ChatGPT) про нові сторінки після кожного деплою.

## Доступи
- GitHub: fine-grained токен «shikarno-site» (лише цей репозиторій; Contents/Workflows/Pages RW; до 21.01.2027). НЕ записувати в документи — /home/claude/gh/.token у робочому середовищі; після скидання попросити ще раз. Cowork-сесії потрібен той самий токен.
- Прав адміністратора репо в токена немає: Pages/домен змінює користувач.
- shikarno.com.ua і github.io закриті в мережі Claude — перевіряє користувач (або додати домен у Settings → Capabilities).

## Рішення користувача
- Semrush не використовувати (російське походження засновників).
- Пости — широкі, якісні, SEO-оптимізовані; сайт не відстає від YouTube ні на день і рухається ширше (вічнозелені гайди, власні новини) — він головне джерело трафіку.
- Сайт має потрапляти і в Google, і у відповіді ШІ-асистентів.

## Щодня (крок автопілота після завантаження ролика)
1. Клонувати репо (токен), `pip install -r requirements.txt`.
2. content/posts/РРРР-ММ-ДД-<slug>.md за docs/content-guide.md: факти з першоджерел, youtube: <id>, verdict як у ролику, date = час виходу ролика.
3. `python3 build.py` → commit → push (стаття з'явиться в момент виходу відео).
4. Після tg.video — `telegram_post: <message_id>` у статтю → push. У пості Telegram — посилання на статтю.
5. Раз на тиждень — вічнозелений гайд (див. docs/seo-strategy.md §2).

## Відкриті задачі
- Cowork: docs/tasks/2026-10-23-site-links.md — посилання на сайт в описах роликів, каналу, Telegram; оновити eps/RUNBOOK.md з репо; youtube ID для еп.11–12; дайджест #1 на сайт до 25.10 12:00.
- Користувач: Search Console (ресурс «Домен», TXT в imena, sitemap.xml і news-sitemap.xml); Bing Webmaster Tools — імпорт із Search Console; посилання на сайт у шапці YouTube-каналу; посилання на пости Telegram еп.1, 2, 6 (для коментарів); контакт для реклами (config.SITE.contact, поки канал).
- Далі: GA4 + читання статистики через Google API; Google News Publisher Center через 2–3 тижні; місячна перевірка цитувань у ChatGPT/Gemini/Perplexity/Claude.
