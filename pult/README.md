# Пульт ШІкарно — живий журнал автопілота

Cloudflare Worker + Durable Object (SQLite) + WebSocket. Сторінка: `https://shikarno-pult.manageit-blog.workers.dev/p/<VIEW_KEY>` (ключ — в артефакті «Доступи ШІкарно»).
Ідея збору подій — як у disler/claude-code-hooks-multi-agent-observability і simple10/agents-observe (хуки Claude Code → POST), але сервер у хмарі, тож посилання працює завжди.

- Події: `.claude/settings.json` → `studio/pult/hook.py` (у фоні, ≤1 запит на дію, секрети маскуються `pultlib.redact`).
- Віхи і стан: `python3 studio/pult/pult.py note "..." [area]`, `pult.py state '{...}'` (headline, next_run, metrics, tasks, today, questions).
- Секрети воркера: INGEST_TOKEN (запис; у сесії — studio/pult/.token), VIEW_KEY (перегляд; studio/pult/.viewkey). Обидва не в git.
- Деплой: `.github/workflows/pult.yml` при зміні pult/** (секрети воркера зберігаються між деплоями).
