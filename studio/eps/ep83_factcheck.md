# Фактчек ep83 — «Шахрайські SMS на iPhone: Moonlock від MacPaw — чесно, чи варто?» (22.11.2026)

Самоперевірка сценариста за першоджерелами 22.11.2026 (незалежна перевірка — окремо, від Диспетчера).

| # | Твердження у сценарії / описі | Джерело | Вердикт |
|---|---|---|---|
| 1 | Moonlock — застосунок MacPaw для iPhone, вийшов в App Store 18.11 | https://macpaw.com/news/moonlock-iphone (18.11.2026); App Store: розробник MacPaw Way Ltd, v1.0 — 30.10, v1.0.3 — 12.11 | PASS (публічний анонс — 18.11; у ролику дату не називаємо) |
| 2 | MacPaw «київська» | https://macpaw.com/about — «Our Kyiv headquarters…» | PASS |
| 3 | «Ховає підозрілі SMS у спам» | https://apps.apple.com/ua/app/moonlock/id6799935865 — Safe SMS: підозрілі SMS від невідомих відправників → Junk, «Nothing is deleted»; анонс — фільтр «when enabled» | PASS (умови — треба ввімкнути, лише невідомі відправники — в описі) |
| 4 | «Перевіряє скрін чи QR-код і пояснює, що не так» | App Store (тексти, скріни, QR → вердикт і пояснення); анонс — Scam Detect | PASS |
| 5 | «Після тижня тріалу — майже 60 доларів на рік»; на екрані $11.99/міс або $59.99/рік | App Store UA: In-App Purchases Moonlock Monthly 11,99 USD, Yearly 59,99 USD; 7-day free trial | PASS (App Store UA). Увага: MacRumors / dev.ua пишуть $13.50/міс на 1 пристрій ($4.50/міс при річній) — це плани сайту MacPaw; Setapp — у тарифі. В описі позначено «у App Store Україна» |
| 6 | «Лише англійською» | App Store UA — Languages: English | PASS |
| 7 | «Тільки iOS 26» (екран «iOS 26+») | App Store UA — Requires iOS 26.0 or later | PASS |
| 8 | «Чи розуміє українські SMS — компанія не пише» | Анонс macpaw.com/news/moonlock-iphone, App Store, macpaw.com/news/moonlock-scam-detector — мови розпізнавання не названо | PASS (відсутність заяви) |
| 9 | Не кажемо «ШІ ловить шахраїв» | Анонс і App Store не кажуть, що Moonlock використовує ШІ (MacPaw називає себе «a global AI technology company») | PASS (свідомо не стверджуємо) |
| 10 | Чутку «Scam Detect обробляє OpenAI» не озвучуємо | Лише переказ AppleInsider у пошуку; першоджерела немає. App Store натомість: «Security checks run on your iPhone» | n/a (не використано) |
| 11 | Порада: скрін у ChatGPT без своїх даних, у банк дзвонити самому | Загальна порада безпеки (як ep77); ChatGPT приймає фото — help.openai.com/en/articles/8400551 | PASS (порада) |
| 12 | Оцінка 6/10, «свої, київські» | Суб'єктивна думка Байта, позначено в описі; не реклама | n/a |
| 13 | Попит: «moonlock» 297 (0/10 укр. у топ-10), «шахрайські схеми» 87 | studio/yt/kw.py --check 2, 22.11 | n/a (дані) |

FAIL: немає. Голос (gsay) — 483 знаки ≈ 30–33 с; після озвучки перевірити vo.wav ≤33 с.
Примітка: Moonlock уже згадано в ep77 (20.11) як новину; ep83 — окремий кут «чесний огляд: ціна й мінуси».
