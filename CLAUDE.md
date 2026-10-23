# ШІкарно — сайт shikarno.com.ua

Цей репозиторій — сайт-блог каналу «ШІкарно» (новини ШІ українською, ведучий — робот Байт).
Сайт статичний: Python-генератор збирає Markdown у HTML, GitHub Actions публікує на GitHub Pages.
Детальні правила: docs/content-guide.md (як писати статті), docs/project-state.md (стан усього проєкту).

## Швидкий старт
```bash
pip install -r requirements.txt
python3 build.py            # → dist/
python3 build.py --preview  # → preview.html (весь сайт в одному файлі, навігація через #)
```
Пости з датою в майбутньому НЕ публікуються, доки не настане їхній час: workflow запускається ще й кожні 30 хв (cron),
тож дайджест, записаний у суботу з датою «неділя 12:00», з'явиться сам (`--future` у build.py — щоб побачити їх локально).
Пуш у `main` → workflow `.github/workflows/pages.yml` збирає і деплоїть (~1 хв).

## Структура
- `config.py` — домен (`domain`, `url`), посилання на YouTube/Telegram, назви тегів `TAG_NAMES`.
- `content/posts/РРРР-ММ-ДД-slug.md` — статті; `content/pages/*.md` — сторінки (pro-nas).
- `templates/` — Jinja2: base (SEO head), index, post, tag, page, 404, macros (Байт SVG з mood talk/happy/judge, лого, Short-фасад).
- `static/` — style.css (токени світлої/темної теми), site.js (фасад YouTube → iframe youtube-nocookie), favicon.svg, og.png, logo.png.
- `build.py` — парсинг front matter, sitemap.xml, rss.xml, robots.txt, CNAME, JSON-LD.

## Front matter статті
```yaml
kind: news              # news | rozbir | dajdzhest | misyats → розділи /novyny/ /rozbory/ /dajdzhest/ /za-misyats/
number: 1               # номер розбору/дайджесту/місячного (бейдж «Дайджест #1»)
duration: "6:24"        # для довгих відео
chapters: [{t: "0:00", title: "...", link: "/novyny/<slug>/"}]   # таймкоди → «Зміст випуску» + Clip schema (ключові моменти в Google)
title: "..."            # H1 і <title>; ключова фраза на початку, ≤ ~90 знаків
slug: latin-translit    # URL /novyny/<slug>/ — НЕ змінювати після публікації
date: 2026-10-23T13:00:00+03:00   # час виходу ролика (Київ)
updated: ...            # при суттєвих правках
description: "..."      # meta description, 140–170 знаків, з ключовими словами
tags: [chatgpt, openai] # ключі з config.TAG_NAMES; перший тег = хлібні крихти
youtube: VIDEO_ID       # Short; дає VideoObject і фасад
source: {name: ..., url: ...}      # головне джерело (конкретна стаття, не головна сторінка)
sources: [{name: ..., url: ...}]   # додаткові джерела
summary: ["...", ...]   # 3–4 пункти «Коротко»
verdict: {score: 1-10, plus: "...", minus: "..."}
faq: [{q: "...", a: "..."}]        # 3 питання → FAQPage schema
telegram_post: 123      # id поста в @shikarno_ai_ua (t.me/shikarno_ai_ua/123) → віджет коментарів;
                        # без нього — кнопка «Обговорити в Telegram». Ставити після tg.video/tg.post (message_id з відповіді)
```

## SEO, яке вже є (не ламати)
canonical, OG/Twitter, robots max-image-preview, JSON-LD NewsArticle + VideoObject + BreadcrumbList + FAQPage,
WebSite+Organization на головній, sitemap.xml, rss.xml, внутрішні посилання «Читай також» за тегами,
швидкість (без JS-фреймворків, відео вантажиться лише після кліку).

## Правила
- Факти — лише з джерел, перевірених під час написання; цифри компаній про себе позначати як їхні.
- Цитати з джерел коротші за 15 слів і не більше однієї з джерела; решта — своїми словами.
- Мова — українська, звертання на «ти», без канцеляриту. Не «рашистські» сервіси: Semrush не використовувати (рішення власника).
- Секретів у репозиторії немає й не має бути (токени, ключі).
- Дизайн: бренд-кольори #FFD60A, #7C5CFF→#FF4F8B, #4CF2FF, фон #0B0A1C→#1A1240; Montserrat 800/900 + Golos Text.
