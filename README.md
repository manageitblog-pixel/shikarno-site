# Сайт ШІкарно

Статичний сайт без сервера й адмінки. Пости — файли Markdown у content/posts/.

- Збірка: `pip install jinja2 markdown pyyaml && python3 build.py` → папка dist/
- Прев'ю одним файлом: `python3 build.py --preview` → preview.html
- Домен — у config.py (SITE.url) і dist/CNAME (створюється автоматично).
- Новий пост: content/posts/РРРР-ММ-ДД-slug.md з полями title, slug, date, description, tags, youtube, source; необов'язково verdict: {score, plus, minus}.
- Хостинг: GitHub Pages (Actions) або Cloudflare Pages (build command: `pip install -r requirements.txt && python3 build.py`, output: dist).
