---
name: growth-loop
description: Щотижневий цикл росту ШІкарно (неділя або на запит власника «як ростемо?»): зняти метрики YouTube/Telegram/сайту/TikTok, порівняти з цілями docs/growth-plan-2026-11.md, вирішити, які формати подвоїти й прибрати, і надіслати власнику звіт у бот.
---
# Цикл росту ШІкарно

1. **YouTube** (`/home/claude/yt/yt.py`, токен з analytics scope): YouTube Analytics `dimensions=video` за 7 днів — views, engagedViews, averageViewPercentage, subscribersGained, shares; `insightTrafficSourceType` (SHORTS, YT_SEARCH, HASHTAGS, RELATED_VIDEO). Дані запізнюються на 2–3 дні — для свіжих роликів брати публічний viewCount.
2. **Формати**: згрупувати ролики за форматом (тір-лист, шахраї, новина, Байт пробує, гумор, скіли/професії) — медіана % перегляду і підписок/1000.
3. **Telegram**: `tg.call('getChatMemberCount', chat_id=tg.CH)`.
4. **Сайт**: Search Console `searchAnalytics/query` (покази, кліки, позиція, топ-запити); Cloudflare — лише якщо є CF_TOKEN.
5. **TikTok**: скріни власника → eps/tiktok.json (views_*).
6. **Рішення**: нижні 20% форматів — прибрати з розкладу; верхні — +1 слот. Записати в docs/RUNBOOK.md (МІКС SHORTS) з датою.
7. **Звіт власнику** (tg.call sendMessage chat_id=133254760): 5 рядків цифр vs цілі з плану, 3 рішення на тиждень, 1 прохання до власника (якщо є). Без води.

Правила: не купувати ботів/підписників; факти про платформи — лише з офіційних сторінок або позначати як оцінку; секрети не друкувати.

- Скан аномалій ніші: `python3 studio/yt/outliers.py 30` → 2–3 теми в план тижня (docs/research/volgin-method-2026-11-06.md).
