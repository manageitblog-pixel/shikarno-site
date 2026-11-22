# Фактчек: studio/eps/guide1.py — «ChatGPT з нуля українською» (Гайд #1)

Дата перевірки: 22.11.2026. Метод: кожне фактичне твердження сценарію звірено з офіційною сторінкою (help.openai.com, openai.com, chatgpt.com/pricing, apps.apple.com, play.google.com, claude.com/pricing, gemini.google/subscriptions), завантаженою curl-ом того ж дня.
Обмеження: цей фактчек зробив сам автор сценарію (Шоуранер), а не окремий агент. Інструмента для запуску окремого агента в цій сесії не було (див. звіт у dispatch-log). Поради та думки Байта («один чат — одна задача», формула промпту, вердикт 9/10) — це не факти, тому їх не перевіряли.

| # | Твердження (сегмент) | Джерело | Результат |
|---|---|---|---|
| 1 | Україна є в списку підтримуваних країн із приміткою «with certain exceptions»; VPN не потрібен (3) | https://help.openai.com/en/articles/7947663-chatgpt-and-openai-api-supported-countries-and-territories | PASS |
| 2 | Три офіційні входи: chatgpt.com, Android, iPhone/iPad (4) | https://play.google.com/store/apps/details?id=com.openai.chatgpt · https://apps.apple.com/ua/app/chatgpt/id6448311069 | PASS |
| 3 | Розробник — OpenAI OpCo/Opco, LLC; потрібна iOS 18.0 або новіша (4) | ті самі сторінки App Store / Google Play | PASS |
| 4 | Без акаунта: одна розмова за раз, історія не зберігається, новий чат «стирає» старий (5) | https://help.openai.com/en/articles/9125172-the-chatgpt-home-page | PASS (OpenAI додає: у деяких місцях чи мережах можуть одразу попросити увійти) |
| 5 | Реєстрація через пошту, Google, Microsoft чи Apple; входити тим самим способом (6) | https://help.openai.com/en/articles/7426629-why-cant-i-log-in-to-chatgpt | PASS |
| 6 | Для особистого користування — особиста, а не робоча пошта (6) | https://help.openai.com/en/articles/9125172-the-chatgpt-home-page | PASS |
| 7 | OpenAI радить тимчасово вимкнути особистий VPN чи проксі, почистити кеш і куки, спробувати інкогніто чи інший браузер (7) | https://help.openai.com/en/articles/7426629-why-cant-i-log-in-to-chatgpt | PASS |
| 8 | Поле вводу, «+»/скріпка для файлів, бічне меню з історією (8) | Free FAQ (меню «+») + інтерфейс | PASS (загальний опис інтерфейсу) |
| 9 | Мова визначається автоматично; українська підтримується; шлях Settings → General → Language; у застосунку — App → Language; змінити мову можна лише після входу (10) | https://help.openai.com/en/articles/8357869-how-to-change-your-language-setting-in-chatgpt | PASS |
| 10 | Українська є серед мов застосунку в App Store | https://apps.apple.com/ua/app/chatgpt/id6448311069 | PASS |
| 11 | Free: безлімітні звичайні текстові чати із захистом від зловживань; файли, картинки, голос, аналіз даних мають окремі ліміти; ChatGPT повідомить про ліміт (13) | https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq | PASS |
| 12 | Free: пошук в інтернеті, фото й файли, картинки, аналіз даних, готові GPT, Library на 500 МБ (14) | Free tier FAQ | PASS |
| 13 | Модель Free — «Luna» (14) | Free FAQ: «GPT-5.6 Luna»; таблиця chatgpt.com/pricing: «GPT-6 Luna: Yes» для Free | PASS лише для «Luna». OpenAI сама собі суперечить щодо версії, тому номер у сценарії не називаємо. **На сайті написано «GPT-6 Luna», і довідка зараз з цим не збігається.** |
| 14 | Deep research у Free обмежений (15) | https://chatgpt.com/pricing (Free: Deep research — Limited) | PASS |
| 15 | Голосовий режим у Free є, з окремим лімітом (16) | Free FAQ; pricing (Free: Voice — Yes) | PASS |
| 16 | Ліміт інструмента скінчився — треба чекати, поки оновиться (27) | Free tier FAQ | PASS |
| 17 | «Context window full» стосується лише цієї розмови: пам'ять і чати не треба видаляти, можна одразу відкрити новий чат, а ранні інструкції можуть не перейти (27) | Free tier FAQ («Why does ChatGPT say my chat is full?») | PASS |
| 18 | Go доступний у всіх країнах, де підтримують ChatGPT; текстові чати в Free і Go безлімітні; у Go вищі ліміти на картинки, файли й аналіз даних і довша пам'ять (28) | https://help.openai.com/en/articles/11989085-what-is-chatgpt-go | PASS (згадку «і проєкти» прибрано: за таблицею pricing проєкти є вже у Free) |
| 19 | Go коштує $8 на місяць у США (28, 29) | https://openai.com/index/introducing-chatgpt-go/ | PASS |
| 20 | Plus коштує $20 на місяць: моделі міркувань, вищі ліміти, deep research, без реклами (29, 30) | https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus · https://help.openai.com/en/articles/20001047-ads-in-chatgpt | PASS (згадку «проєкти» прибрано) |
| 21 | Plus: пріоритет у години пік, швидші відповіді, можливі обмеження на кількість повідомлень за великого навантаження (30) | What is ChatGPT Plus? | PASS |
| 22 | Pro має три місячні плани: $100, $200, $500; що дорожчий план, то більше використання; Codex входить у Pro (29, 31) | https://help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers | PASS |
| 23 | Business: $25 за місце на місяць або $20 при оплаті за рік (29) | https://help.openai.com/en/articles/8792828-chatgpt-business-overview | PASS |
| 24 | Покупки в доларах; оплата в місцевій валюті — лише в обмеженому списку країн (32) | What is ChatGPT Go? (Availability) | PASS |
| 25 | Український App Store, 22.11: Go 6,99 $, Plus 22,99 $, Pro 100 — 119 $ (32) | https://apps.apple.com/ua/app/chatgpt/id6448311069 (In-App Purchases) | PASS |
| 26 | Реклама може з'являтися у Free і Go в окремих регіонах, під відповіддю; за словами OpenAI, на відповіді не впливає; у Plus і Pro реклами немає; є безкоштовний режим без реклами з нижчими лімітами і без створення картинок (33) | https://help.openai.com/en/articles/20001047-ads-in-chatgpt | PASS (відсутність впливу — твердження компанії, у сценарії так і підписано) |
| 27 | На особистих акаунтах Free/Plus/Pro передача даних для навчання ввімкнена за замовчуванням; її вимикає перемикач Settings → Data controls → «Improve the model for everyone», а історія при цьому лишається (37) | https://help.openai.com/en/articles/7730893-data-controls-faq | PASS |
| 28 | Тимчасовий чат: New chat → Temporary; не потрапляє в історію, не оновлює пам'ять, не йде на навчання, доки його не збережеш; копію можуть тримати до 30 днів з міркувань безпеки (38) | https://help.openai.com/en/articles/8914046-temporary-chat-faq | PASS |
| 29 | Пам'ять: Settings → Personalization → Memory, там можна переглянути й видалити збережене; вимкнення пам'яті не видаляє минулі чати (39) | https://help.openai.com/en/articles/8590148-memory-faq | PASS |
| 30 | ChatGPT сам попереджає під полем вводу, що може помилятися (41) | Free tier FAQ: на скріні інтерфейсу «ChatGPT can make mistakes. Check important info.» | PASS |
| 31 | Безкоштовний Claude: веб-пошук, пам'ять, ліміти оновлюються кожні 5 годин і щотижня (44) | https://claude.com/pricing | PASS |
| 32 | Безкоштовний Gemini за $0 з Google-акаунтом: генерація картинок, Deep Research, Gemini Live (44) | https://gemini.google/subscriptions/ | PASS |
| 33 | Наступного тижня вийде гайд «Claude безкоштовно» (44, 47) | docs/org/strategy.md §5 п.8 (план на 2.12) | PASS (внутрішній план; якщо дата зміниться, це речення треба переписати) |

**Підсумок:** 33 твердження: 33 PASS, 0 FAIL. Два формулювання виправлено до фіналу: «проєкти» прибрано з переваг Go і Plus (вони є у Free), номер версії Luna прибрано (джерела OpenAI суперечать одне одному).
**Для сайту:** сторінка chatgpt-bezkoshtovno-v-ukraini пише «GPT-6 Luna» і «Plus — власні GPT-и». Довідка OpenAI на 22.11 каже «GPT-5.6 Luna» і що нові GPT не можна створювати на жодному особистому тарифі (Free/Go/Plus/Pro). Варто звірити.
