# Фактчек ep81 «Який ШІ для дітей?» — незалежний

Перевірено 22.11.2026: `studio/eps/ep81.py` (SCENES text/gsay, ROWS) і `meta.py` → `ep81_tier_kids` (title, description, tags).
Усі першоджерела відкрито під час цієї перевірки.

| # | Твердження | Джерело | Статус | Примітка |
|---|---|---|---|---|
| 1 | ChatGPT — «з 13 і зі згоди батьків»; опис: «не для дітей до 13, з 13 до 18 — з дозволу батьків» | https://help.openai.com/en/articles/8313401-is-chatgpt-safe-for-all-ages | PASS | «not meant for children under 13»; 13–18 «obtain parental consent». |
| 2 | ChatGPT для англійської: «розмова голосом» (опис) | https://help.openai.com/en/articles/8400625-voice-mode-faq | PASS | «natural, free-form voice conversation», є й на безкоштовному плані з лімітами. Рекомендація має віковий застереження в озвучці, тож не підштовхує до використання молодшими 13. |
| 3 | Gemini «пояснить кроками» (домашка) | — (загальна можливість чат-бота) | PASS (порада) | Це порада, як питати, а не заява компанії. В озвучці рядок «Домашка» без вікової примітки, але рядок «Безпека» відразу каже, що до 13 Gemini вмикає батько. Це не блокує. |
| 4 | Family Link: «до 13 Gemini вмикаєш ти»; опис: «доступний лише в контрольованому акаунті, якщо батьки ввімкнуть» | https://support.google.com/gemini/answer/16109150 | PASS | «A parent must enable access before their child under 13…». Недоступно в ЄЕЗ, Швейцарії та UK, а розгортання поступове. В описі не обіцяємо, що функція є всюди, тож це прийнятно. |
| 5 | Gemini Storybook: ілюстрована книжка на 10 сторінок, «але це 18+», «створюєш її ти» | https://gemini.google/overview/storybook/ | PASS | «10-page storybook», «available to all Gemini users over the age of 18». Формулювання «створюєш її ти» правильно кладе дію на дорослого. |
| 6 | Claude — лише 18+ (тільки в описі) | https://support.claude.com/en/articles/13117299-minimum-age-requirement-access-restriction | PASS | «at least 18 years old to create and use a Claude account». |
| 7 | AI Quests — безкоштовна веб-гра українською, 11–14 років, без реєстрації | https://research.google/ai-quests/intl/uk_ua/faq | PASS | «відкритий і безкоштовний ресурс», «учнів середньої школи (11–14 років)», ім'я, логін і пошту вводити не треба, українська є в меню мов. |
| 8 | «гра Google» / «Google Research» | https://research.google/ai-quests/intl/uk_ua/faq | PASS | Розробник — Google Research, основний співавтор — Stanford Accelerator for Learning. |
| 9 | Запуск разом з МОН і Мінцифри (лише коментар у файлі та посилання на DOU в описі) | https://dou.ua/lenta/news/google-ai-quests-ukraine-kids/ (вторинне джерело) | PASS (вторинне) | DOU, 16.11: «запуск з Міносвіти та Мінцифри». Деталь некритична, в озвучку й текст опису не винесена. |
| 10 | Рядки «списати/гугл/зубрити/мультик…» і вибір «найкраще» | — | n/a (думка) | Це думка. Подано як «Тір-лист Байта» в title і «Суб'єктивний рейтинг Байта» в описі. |
| 11 | Теги (`з якого віку ChatGPT`, `Gemini для дітей`, `Family Link`, `AI Quests`, `Gemini Storybook`…) | — | PASS | Фактичних тверджень у тегах немає. |

Ризики для батьків: явних порушень немає. Кожен сервіс із віковим обмеженням має застереження (ChatGPT — 13+ і згода батьків; Storybook — 18+; Gemini до 13 — лише після ввімкнення батьками; Claude — 18+ в описі). Нічого не радить обходити вікові правила.

Порівняння з файлом автора (`ep81_factcheck.md`): висновки збігаються, розбіжностей немає.

Необов'язкова порада (на вердикт не впливає): у рядку «Домашка» можна додати «з батьками», але через обмеження ≤35 с це не вимога.

Вердикт: PASS
