# Незалежний фактчек — гайд #1 «ChatGPT з нуля українською» (studio/eps/guide1.py)

Перевірено 22.11.2026: сторінки відкрито curl-ом зі стандартними заголовками (help.openai.com віддав 200).
Сегменти пронумеровано за індексом у `SEGS` (0 — вступ).

| # | Твердження | URL | Статус | Примітка |
|---|---|---|---|---|
| 3 | Україна є у списку підтримуваних країн з приміткою «з певними винятками», винятки не уточнено | https://help.openai.com/en/articles/7947663-chatgpt-supported-countries | PASS | «Ukraine (with certain exceptions)», без деталей |
| 4 | Розробник застосунку iOS — OpenAI OpCo; потрібна iOS 18 або новіша | https://apps.apple.com/ua/app/chatgpt/id6448311069 | PASS | «Requires iOS 18.0 or later», OpenAI OpCo, LLC |
| 4 | Android-застосунок у Google Play від OpenAI | https://play.google.com/store/apps/details?id=com.openai.chatgpt | PASS | Розробник «OpenAI Opco, LLC» |
| 5 | Без акаунта: одна розмова за раз, історія не зберігається, новий чат прибирає попередній | https://help.openai.com/en/articles/9125172-the-chatgpt-home-page | PASS | Доступ без акаунта може залежати від регіону чи мережі |
| 6 | Реєстрація через пошту, Google, Microsoft чи Apple; входити тим самим методом; особиста, а не робоча пошта | https://help.openai.com/en/articles/7426629-why-cant-i-log-in-to-chatgpt ; https://help.openai.com/en/articles/9125172-the-chatgpt-home-page | PASS | «Try the method you used to create your account»; рекомендовано пошту, яку контролюєш ти |
| 7 | При проблемах зі входом тимчасово вимкнути особистий VPN чи проксі, почистити кеш і куки, спробувати інкогніто | https://help.openai.com/en/articles/7426629-why-cant-i-log-in-to-chatgpt | PASS | «Temporarily pause any personal VPN or proxy services and refresh the page» |
| 10 | Мова визначається автоматично; українська підтримується; шляхи Settings → General → Language і App → Language; змінити можна лише після входу | https://help.openai.com/en/articles/8357869-how-to-change-your-language-setting-in-chatgpt | PASS | — |
| 13, 15 | Текстові чати у Free без ліміту з захистом від зловживань; файли, картинки, голос і аналіз даних мають окремі ліміти; ChatGPT попередить | https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq | PASS | — |
| 14 | Free: пошук, фото й файли, картинки, аналіз даних, готові GPT, Library на 500 МБ | https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq | PASS | — |
| 14 | «Є готові GPT… користуватися ними можна» | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts | FAIL (неповно) | Сьогодні це правда, але OpenAI оголосила, що згортає власні GPT і переносить їх на плагіни; стандартне відключення заплановане на 11.12.2026. Гайд застаріє за три тижні |
| 14 | Модель Luna без номера версії | https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq ; https://chatgpt.com/pricing | PASS | У довідці «GPT-5.6 Luna», на сторінці тарифів «GPT-6 Luna». У скрипті версії немає, як і треба |
| 15 | Deep research у Free з лімітом | https://chatgpt.com/pricing | PASS | «Limited deep research» |
| 16 | Голос у Free з окремим лімітом | https://chatgpt.com/pricing ; https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq | PASS | «Limited voice chats» |
| 27 | Ліміт інструмента: треба чекати; «Context window full» — це межа розмови, пам'ять чи старі чати чіпати не треба; ранні інструкції можуть не перейти | https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq | PASS | — |
| 28 | Go доступний у всіх країнах, де підтримується ChatGPT; текстові чати безлімітні у Free і Go; вищі ліміти на картинки, файли й аналіз даних; довша пам'ять | https://help.openai.com/en/articles/11989085-what-is-chatgpt-go | PASS | — |
| 28, 29 | Go — $8 на місяць у США | https://openai.com/index/introducing-chatgpt-go/ | PASS | «In the US, Go is available for $8 per month». На chatgpt.com/pricing ціни підвантажує JS, у HTML їх немає |
| 29, 30 | Plus — $20 на місяць, оплата щомісяця; пріоритет у години пік, вищі ліміти, моделі міркувань, швидші відповіді; ліміти можливі при великому навантаженні | https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus | PASS | — |
| 29 | У Plus є deep research і немає реклами | https://chatgpt.com/pricing ; https://help.openai.com/en/articles/20001047-ads-in-chatgpt | PASS | — |
| 29, 31 | Pro: $100, $200 або $500, три місячні плани; що дорожчий, то більше використання; Codex | https://help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers | PASS | — |
| 29 | Business: $25 за місце на місяць або $20 при оплаті за рік | https://help.openai.com/en/articles/8792828-chatgpt-business-overview | PASS | Стандартне місце; є ще преміум-місця за $125/$100 |
| 32 | Покупки в доларах, оплата в місцевій валюті лише в обмеженому списку країн | https://help.openai.com/en/articles/11989085-what-is-chatgpt-go | PASS | — |
| 32 | Український App Store: Go 6,99, Plus 22,99, Pro 100 — 119 USD | https://apps.apple.com/ua/app/chatgpt/id6448311069 | PASS | «ChatGPT Go 6,99 USD», «Plus 22,99 USD», «Pro 100 119,00 USD» |
| 33 | Реклама може з'являтися у Free і Go в окремих регіонах, під відповіддю; не впливає на відповіді; у Plus і Pro реклами немає | https://help.openai.com/en/articles/20001047-ads-in-chatgpt | PASS | — |
| 33 | Free без реклами: ліміти нижчі, частина інструментів (картинки) недоступна | https://help.openai.com/en/articles/20001047-ads-in-chatgpt | PASS | «no access to some tools like image generation or deep research» |
| 34 | «Plus потрібен, коли тобі важливі потужніші моделі міркувань і проєкти» | https://chatgpt.com/pricing ; https://help.openai.com/en/articles/11989085-what-is-chatgpt-go | FAIL | Проєкти є вже у Free (таблиця на сторінці тарифів: Projects — Free: Yes) і в Go (довідка Go). Це не причина брати Plus |
| 37 | На особистих Free, Plus і Pro передача даних для покращення моделей увімкнена за замовчуванням; вимикається в Settings → Data controls → «Improve the model for everyone»; історія чатів лишається | https://help.openai.com/en/articles/7730893-data-controls-faq | PASS | «data sharing is enabled by default… keep your chat history» |
| 38 | Тимчасовий чат: кнопка Temporary; не потрапляє в історію, не оновлює пам'ять, не йде на навчання, поки його не збережеш; копія зберігається до 30 днів | https://help.openai.com/en/articles/8914046-temporary-chat-faq | PASS | Нюанс: персоналізований тимчасовий чат може використовувати вже наявну пам'ять. Скрипт цього не заперечує |
| 39 | Пам'ять: Settings → Personalization → Memory; якщо вимкнути пам'ять, минулі чати не видаляються | https://help.openai.com/en/articles/8590148-memory-faq | PASS | «does not delete past chats» / «original chats remain in your history» |
| 41 | Під полем вводу ChatGPT попереджає про помилки | — | UNVERIFIED | Це елемент інтерфейсу, у довідці не знайшов. Змісту не шкодить, але варто показати скрін |
| 44 | Claude Free: веб-пошук, пам'ять, ліміти кожні 5 годин і щотижня | https://claude.com/pricing | PASS | — |
| 44 | Gemini Free: з Google-акаунтом, генерація картинок, Deep Research, Gemini Live | https://gemini.google/subscriptions/ | PASS | — |
| 0 | «Усі факти — зі сторінок OpenAI» | — | PASS (з приміткою) | Сегмент 44 спирається на сторінки Anthropic і Google, але сам це називає |

## Вердикт: FAIL → 22.11 виправлено сегменти 14 і 34 дослівно за рекомендацією → PASS (лишається: показати попередження під полем вводу скріном)

Потрібні дві точкові правки тексту, далі скрипт можна озвучувати.

1. **Сегмент 14.** Замінити
   «Є готові GPT — спеціалізовані боти від інших людей і компаній: користуватися ними можна.»
   на
   «Є готові GPT — спеціалізовані боти від інших людей і компаній. Поки що ними можна користуватися, але OpenAI вже оголосила, що згортає GPT і переносить їх на плагіни.»

2. **Сегмент 34.** Замінити
   «Plus потрібен, коли тобі важливі потужніші моделі міркувань і проєкти, а ChatGPT — щоденний робочий інструмент.»
   на
   «Plus потрібен, коли тобі важливі потужніші моделі міркувань і розширений deep research, а ChatGPT — щоденний робочий інструмент.»

Необов'язково: у сегменті 41 показати на екрані скрін попередження під полем вводу.

## Повторна перевірка 22.11

Інший фактчекер, сценарій не редагував. `git log -p -- studio/eps/guide1.py`: після f76fa84 є один коміт, 33835a2. Він змінює рівно два рядки: `text` сегментів 14 і 34. Слайди, `points`, інші сегменти й PARTS не зачеплено. Першоджерела відкрито 22.11 curl-ом (200). chatgpt.com через Playwright без логіну показує лише Cloudflare «Verify you are human», тож інтерфейс побачити не вдалося.

| # | Формулювання зараз | Першоджерело (22.11) | Статус | Точна заміна (TTS-частина ≤1300) |
|---|---|---|---|---|
| 14 | «Поки що ними можна користуватися, але OpenAI вже оголосила, що згортає GPT і переносить їх на плагіни.» | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts — «planning to retire custom GPTs», «Standard retirement is scheduled for December 11, 2026», «includes all ChatGPT plans»; https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq — на особистих акаунтах «continue using existing GPTs», створювати нові не можна | FAIL | Сам факт тепер правильний, але дати немає. Гайд виходить 25.11, а GPT вимкнуть 11.12, тобто через 16 днів. Глядач не дізнається, що функція зникне так скоро. Замінити це речення на: «Але одинадцятого грудня OpenAI їх вимикає і переносить на плагіни, тож звикати до них не варто.» (95 знаків замість 102; у gsay 100 замість 113 → частина [12,13,14,15] 1278 замість 1291) |
| 34 | «Plus потрібен, коли тобі важливі потужніші моделі міркувань і розширений deep research…» | https://chatgpt.com/pricing — Plus: «Advanced reasoning models», «Expanded deep research»; у таблиці Deep research: Free і Go «Limited», Plus «Yes»; Projects: Free/Go/Plus/Pro «Yes». https://help.openai.com/en/articles/11989085-what-is-chatgpt-go — у Go є projects | PASS | — |
| 41 | «Внизу під полем вводу ChatGPT і сам про це попереджає.» | Живий інтерфейс недоступний (Cloudflare). У довідці і на сторінці тарифів такого тексту не знайдено. Ідею підтверджує https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth — «verify important information from reliable sources» | UNVERIFIED → переформулювати | «OpenAI і сама в довідці радить перевіряти важливе.» (50 знаків замість 54; gsay 55 замість 60). Інший варіант — лишити речення, якщо на екрані буде свіжий скрін із цим попередженням |
| інше | Решта сценарію | diff 33835a2 | не змінювалось | Висновки першої перевірки чинні |

Перед озвучкою 23.11 потрібна заміна в сегменті 14. Заміна в сегменті 41 — бажана.

Вердикт: FAIL

## Перевірка 3 (22.11)

Третій незалежний фактчекер, сценарій не редагував. `git show be9b26a -- studio/eps/guide1.py`: змінено рівно два рядки, `text` сегментів 14 і 41 (2 insertions, 2 deletions). Змінено лише ці два речення, решту тексту, слайди, `points` і PARTS не зачеплено. `python3 -c "import sys; sys.path.insert(0,'studio/eps'); import guide1"` проходить, тобто assert ≤1300 знаків на частину виконується. Першоджерела відкрито 22.11 curl-ом (усі 200).

| # | Формулювання зараз | Першоджерело (22.11) | Статус | Примітка |
|---|---|---|---|---|
| 14 | «Але одинадцятого грудня OpenAI їх вимикає і переносить на плагіни, тож звикати до них не варто.» | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts — «planning to retire custom GPTs and help creators move their workflows to plugins», «Standard retirement is scheduled for December 11, 2026», «includes all ChatGPT plans»; https://help.openai.com/en/articles/20001519-custom-gpt-retirement-and-migration-faq — «Custom GPTs are scheduled to retire on Dec 11, 2026», «Restrictions on creating or publishing GPTs are separate from retirement of existing GPTs» | PASS | «Вимикає» тут коректне: 11.12 вимикають самі наявні GPT, а не лише їх створення (створення на особистих тарифах закрили раніше, див. 9275245). Дата 11.12 стосується всіх особистих тарифів. Пізніша дата 28.02.2027 діє лише для FedRAMP і Enterprise з відстрочкою, глядачів гайду це не стосується. «Переносить на плагіни» — спрощення: заміну-плагін переносить творець GPT, автоматично вона не з'являється. Для гайду новачка це допустимо, і висновок «звикати не варто» від цього не змінюється |
| 41 | «OpenAI і сама в довідці радить перевіряти важливе.» | https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth — «verify important information from reliable sources», «Please check important information» | PASS | Переказ точний, і неперевірене твердження про попередження під полем вводу з тексту зникло |
| інше | Решта сценарію | diff be9b26a | не змінювалось | Висновки попередніх перевірок чинні. Сегмент 34 — PASS (перевірка 2) |

Обидві правки з перевірки 2 внесено дослівно, і вони відповідають першоджерелам. Сценарій можна озвучувати 23.11.

Вердикт: PASS
