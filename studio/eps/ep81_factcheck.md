# Фактчек ep81 — «Який ШІ для дітей? Тір-лист Байта #6» (22.11.2026)

Перевірено за офіційними сторінками 22.11.2026. Зауваження: окремого агента-фактчекера в цій сесії запустити не було як
(інструмента Agent немає), тому кожне твердження сценарист перевірив повторно сам, по першоджерелах.

| # | Твердження у сценарії / описі | Джерело | Вердикт |
|---|---|---|---|
| 1 | ChatGPT не для дітей до 13; з 13 до 18 — з дозволу батьків («з 13 і з дозволу батьків») | https://help.openai.com/en/articles/8313401-is-chatgpt-safe-for-all-ages — «not meant for children under 13», «ages 13 to 18 obtain parental consent» | PASS |
| 2 | ChatGPT «поговорить голосом» (голосовий режим, є й на безкоштовному плані з лімітами; можна просити іншою мовою) | https://help.openai.com/en/articles/8400625-voice-mode-faq | PASS |
| 3 | Gemini дитині до 13 — лише якщо батьки ввімкнуть (контрольований акаунт, Family Link → Controls → Gemini) | https://support.google.com/gemini/answer/16109150 — «A parent must enable access before their child under 13…» | PASS (примітка: недоступно в ЄЕЗ/Швейцарії/UK; розгортання поступове — в описі «доступний лише … якщо батьки ввімкнуть», не обіцяємо, що є всюди) |
| 4 | Gemini «пояснить кроками» (домашка) | Загальна можливість чат-бота; це порада, як питати, а не заява компанії | PASS (порада) |
| 5 | Gemini Storybook — ілюстрована книжка на 10 сторінок, лише 18+ («Gemini Storybook, але це 18+») | https://gemini.google/overview/storybook/ — «10-page storybook», «available to all Gemini users over the age of 18» | PASS (озвучку українською не згадуємо: мови озвучки обмежені) |
| 6 | Claude — лише з 18 (після скорочення до ≤35 с — лише в описі ролика) | https://support.claude.com/en/articles/13117299-minimum-age-requirement-access-restriction — «at least 18 years old to create and use a Claude account» | PASS |
| 7 | AI Quests — безкоштовна гра Google українською, 11–14 років, без реєстрації, веб | https://research.google/ai-quests/intl/uk_ua/faq — «учнів середньої школи (11–14 років)», «відкритий і безкоштовний ресурс», дані вводити не треба | PASS |
| 8 | AI Quests зробила Google Research (зі Stanford Accelerator for Learning) | https://research.google/ai-quests/intl/uk_ua/faq | PASS |
| 9 | Запуск української версії разом з МОН і Мінцифри (лише в коментарі файлу, не в озвучці) | https://dou.ua/lenta/news/google-ai-quests-ukraine-kids/ ; новина МОН https://mon.gov.ua/news/google-zapuskaie-ukrainskoiu-bezkoshtovnu-hru-ai-quests-pro-shtuchnyi-intelekt-dlia-shkoliariv (сторінка віддала 403 боту, підтверджено через пошукову видачу) | PASS (Мінцифри — лише за DOU; в ролик не виносимо) |
| 10 | Рядки «погано/добре» (списати, гугл, зубрити, мультик…) і вибір «найкраще» | Суб'єктивний рейтинг Байта, позначено в описі | n/a |

FAIL: немає. Виправлення під час перевірки: прибрано «з озвучкою» для Storybook (мови озвучки обмежені), Claude не ставимо
в рядки для дітей (18+), лише як попередження в описі. Ревізія за даними Аналітика 22.11: текст скорочено до ≤35 с,
гачок — питання «Твоя дитина питає ШІ?»; нових тверджень не додано, усі перевірені вище збереглися.
