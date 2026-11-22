# Незалежний фактчек — гайд #3 «Gemini безкоштовно українською» (studio/eps/guide3.py, вихід ср 9.12)

Фактчекер: незалежний (сценарій писав не я). Перевірено 22.11.2026 ~16:00 Київ: озвучка (поле `text`, з якого генерується `gsay`) і тексти на екрані (title/points/items/left/right/plus/minus).
Метод: кожне фактичне твердження звірено з першоджерелом, відкритим зараз (curl і WebFetch сторінок support.google.com у версіях `hl=en` та `hl=uk`, gemini.google/subscriptions і /students `?hl=uk`, blog.google, App Store UA, support.claude.com, claude.com/pricing, help.openai.com). Інтерфейс gemini.google.com додатково відкрито через Playwright (chromium, uk-UA, без входу в акаунт). Самоперевірку автора (guide3_factcheck.md) я відкрив лише після власної перевірки.
Цифри Google (ліміти, мови, країни) — це заяви компанії, і в ролику вони подані як «за довідкою Google».

| Твердження | Джерело | Статус | Нотатка |
|---|---|---|---|
| Gemini підтримує українську офіційно (інтро, compare, розділ 2) | https://support.google.com/gemini/answer/13575153?hl=uk | PASS | Українська є у списку підтримуваних мов |
| Gemini малює картинки, робить Deep Research, працює з поштою — за 0 ₴ (інтро) | https://gemini.google/subscriptions/?hl=uk ; https://support.google.com/gemini/answer/16275805?hl=en | PASS | У Free є картинки, Deep Research і підключені застосунки (Connected apps = ✓). «Gemini у Gmail» на сторінці тарифів — окрема платна функція (панель у самому Gmail), але в ролику йдеться про @Gmail у чаті, а це є у Free |
| Моделі Hydrogen / Neon / Carbon: швидка / глибший аналіз / найсильніша | https://support.google.com/gemini/answer/18648722?hl=en | PASS | Опис збігається з довідкою, номер версії «4» у ролику не звучить |
| У Free режим Auto: Hydrogen або швидша легка модель, щоб берегти ліміт | там само | PASS | «Hydrogen or a fast, lightweight model … while conserving your usage» |
| Neon — від Pro, Carbon — лише в Ultra | там само (таблиця моделей) | PASS | Plus має Auto і Hydrogen, Pro — ще й Neon, Ultra — ще й Carbon |
| ChatGPT має український інтерфейс | https://help.openai.com/en/articles/8357869-how-to-change-your-language-setting-in-chatgpt | PASS | Українська є у списку мов інтерфейсу |
| У Claude на вебі кнопки лишаються англійською | https://support.claude.com/en/articles/10769299-how-to-use-claude-in-your-preferred-language | PASS | Української серед мов інтерфейсу немає |
| Gemini і ChatGPT малюють, Claude — ні | https://support.claude.com/en/articles/9002504-can-claude-produce-images ; https://chatgpt.com/pricing | PASS | Claude не генерує фото й ілюстрації (лише SVG/HTML-візуалізації). У ChatGPT Free генерація є, але обмежена |
| Deep Research є в Gemini Free; Research у Claude — лише в платних планах | https://support.google.com/gemini/answer/16275805?hl=en ; https://claude.com/pricing | PASS | У Claude Free стоїть «No» |
| Вебзастосунок доступний у 230+ країнах, Україна в списку, VPN не потрібен | https://support.google.com/gemini/answer/13575153?hl=uk | PASS | «понад 230 країнах і регіонах», Україна в списку |
| Мобільна доступність залежить від мов і країн мобільного застосунку | там само | PASS | |
| Вебзастосунок доступний «більш ніж 40 мовами» (на екрані «40+ мов») | там само, `hl=uk` і `hl=en` | PASS | В українській версії довідки — «більше ніж 40 мовами», в англійській (оновленій) — «more than 70 languages». Формулювання правдиве, але застаріле. Можна сказати «понад сімдесят», це необов'язково |
| Пишеш українською — відповідає українською, можна попросити запам'ятати | — | PASS | Це порада, не твердження про конкретну функцію |
| Входи: сайт gemini.google.com, Android, iPhone | https://apps.apple.com/ua/app/google-gemini/id6477489729 | PASS | |
| App Store: розробник Google, iOS 18.2+, позначка 13+ | там само | PASS | Google LLC, iOS 18.2 або новіша, 13+ |
| На Android Gemini може працювати як помічник телефона | https://support.google.com/gemini/answer/14554984?hl=en | PASS | «Use Gemini as your primary mobile assistant» |
| Windows: Windows 10+, 8 ГБ RAM, gemini.google/desktop, Alt + Space | https://support.google.com/gemini/answer/18263854?hl=en | PASS | Усі чотири деталі є в довідці |
| Є застосунок для Mac | довідка Gemini, стаття «Use the Gemini app on Mac» (є в навігації 16868299 і 18263854) | PASS | |
| Google-акаунтом в Україні можна керувати з 13 років | https://support.google.com/accounts/answer/1350409?hl=en | PASS | України немає у винятках, тож діє стандартний вік 13 |
| Deep Research — з 18 | https://support.google.com/gemini/answer/15719111?hl=en | PASS | «Be 18 or over» |
| Редагування фото — з 18, генерація картинок — з 13 | https://support.google.com/gemini/answer/14286560?hl=en | PASS | |
| Навички (skills) — з 18 | https://support.google.com/gemini/answer/17094296?hl=en | PASS | «To create and use skills, you must: Be 18 or over» |
| Імпорт з інших чат-ботів — з 18 | https://support.google.com/gemini/answer/16868299?hl=en | PASS | |
| Платні плани Google AI — лише 18+, «за сторінкою тарифів» | https://gemini.google/subscriptions/?hl=uk | PASS | У футері сторінки тарифів — «віком від 18 років». Довідка (16275805, 14517446) натомість пише «13+ у більшості країн». Ролик правильно посилається саме на сторінку тарифів, тож це не помилка, але Google суперечить сам собі |
| Вхід — праворуч угорі | Playwright gemini.google.com?hl=uk (uk-UA) | PASS | Кнопка «Увійти» стоїть праворуч угорі (x≈1520, y≈14) |
| Без входу частина функцій працює, але історія не зберігається | https://support.google.com/gemini/answer/13275745?hl=en | PASS | |
| Кнопка додавання файлів відкриває ще й Canvas і Deep Research | 16047321 і 15719111 (`?hl=en`) | PASS | «Add Files → Canvas», «Add Files → Deep Research» |
| Меню з чатами і «Новий чат» — ліворуч угорі | 13275745 і Playwright | PASS | |
| Free — 0 ₴ на місяць з акаунтом Google; три платні плани: Plus, Pro, Ultra | https://gemini.google/subscriptions/?hl=uk | PASS | |
| Картка Free: автовибір моделі, створення й редагування зображень, Deep Research, Live, Canvas, навички, Google Flow, Gemini Notebook, 15 ГБ | там само | PASS | Flow у Free дають з обмеженим доступом. У ролику слово «обмежений» не звучить, але й безліміт не обіцяють |
| Без плану немає: генерації відео, Redo з Nano Banana Pro, щоденного брифу, запланованих дій | https://support.google.com/gemini/answer/16275805?hl=en (таблиця функцій) | PASS | У колонці «Without a Google AI plan» тут стоїть порожня позначка. Ще недоступний «Early access» |
| У Free є Canvas, навички, підключені застосунки, тести й картки, аудіоогляди, слайди, музика, картинки, Deep Research | там само | PASS | Скрізь ✓ |
| Ліміт рахується за обчисленнями (складність, функція, довжина чату) | там само | PASS | «compute-based usage limits» |
| Ліміт оновлюється кожні 5 годин, доки не дійдеш тижневої межі | там само | PASS | «refreshes every 5 hours until you reach your weekly limit» |
| Точну кількість запитів Google не називає: у Free — «стандартні ліміти» | там само | PASS | «Standard limits» |
| Plus — 2×, Pro — 4× | там само ; сторінка тарифів | PASS | |
| Контекст: Free 32k, Plus 128k, Pro і Ultra — 1 млн токенів | 16275805 | PASS | |
| Витрати: короткий запит — дуже мало, довга розмова — помірно, великі файли теж «важкі», найдорожче — Deep Research і медіа | 16275805 (таблиця «Understanding usage») | PASS | Very low / Medium / Medium / High / High. Медіа — «images, music, and video» |
| Порада Google: нова тема — новий чат | там само | PASS | «Start a new chat when you move to a new topic» |
| Запит можна відредагувати, і Gemini перепише відповідь | 13275745 | PASS | |
| Пункт меню під відповіддю продовжує розмову в новому чаті (гілка) | https://support.google.com/gemini/answer/13666746?hl=en | PASS | «Below a response, click Menu → Branch in a new chat» |
| Google: на відповіді не варто покладатися як на професійну пораду | 13275745 | PASS | «don't rely on responses … for professional advice» |
| Файли: до 10 за раз, до 100 МБ, відео до 2 ГБ | https://support.google.com/gemini/answer/14903178?hl=en | PASS | |
| Free: загалом 5 хв відео і 10 хв аудіо; Pro/Ultra — 1 год відео і 3 год аудіо | там само | PASS | |
| З Диска — потрібні увімкнена історія і підключений Google Workspace | там само | PASS | |
| Приклад з круговою діаграмою витрат є в довідці; для завантаженої таблиці на вебі будується графік, де можна змінити тип і підписи | 13275745 ; 14903178 | PASS | |
| Підключення до Gmail, Календаря, Диска є у Free; @ → обрати застосунок | https://support.google.com/gemini/answer/13695044?hl=en ; 16275805 | PASS | |
| На вебі й iPhone підключені застосунки працюють лише з увімкненою історією; від'єднати можна в налаштуваннях підключень | 13695044 | PASS | «When History is off, Connected Apps won't be available on gemini.google.com, iOS devices…» |
| Тести й картки — у Free | 16275805 | PASS | |
| Блокноти: файли-джерела, Gemini пам'ятає їх у розмові; доступ відкривають поступово | https://support.google.com/gemini/answer/16972047?hl=en | PASS | «remembers your sources… gradually making this feature available» |
| Gemini Live у застосунку на телефоні: камера і голос | https://support.google.com/gemini/answer/15274899?hl=en | PASS | У вебзастосунку Live немає, і ролик правильно каже «на телефоні» |
| Nano Banana точно пише текст на зображеннях і тримає схожість персонажа | 14286560 | PASS | «accurate text rendering, and subject consistency» |
| Бічне меню → розділ **Images** (озвучка) | 14286560 `?hl=uk` ; Playwright gemini.google.com?hl=uk | **FAIL** | В українському інтерфейсі, за яким іде гайд, розділ називається «Зображення» (так і в довідці uk, і на живій сторінці). Назва «Images» є лише в англійському інтерфейсі |
| Google нагадує: не порушуй чужих авторських прав і приватності | 14286560 | PASS | |
| Canvas: документ, слайди, код, застосунок; правки руками зберігаються самі | https://support.google.com/gemini/answer/16047321?hl=en | PASS | «Changes are auto-saved» |
| «Створити» в Canvas → аудіоогляд, тест, інфографіка, вебсторінка; поки лише з 18 | там само | PASS | «For now, this feature isn't available to users under 18» |
| Deep Research: план, багато пошукових запитів, план можна правити, звіт за 5–10 хв, експорт у Google Документи | 15719111 | PASS | «Edit plan», «about 5-10 minutes», «Export to Docs» |
| Імпорт: не лише пам'ять, а й уся історія; промпт для пам'яті туди й назад | 16868299 | PASS | |
| Шлях: **Settings → Import memory to Gemini** (озвучка) | 16868299 `?hl=uk` | **FAIL** | В українському інтерфейсі пункти звуться «Налаштування» → «Імпортувати пам'ять у Gemini». Англійські назви глядач з uk-інтерфейсом не знайде |
| Архів zip до 5 ГБ, до 5 архівів на день, обробка — до доби; спершу експорт у ChatGPT або Claude | 16868299 | PASS | |
| Імпортовані чати зберігаються в історії і йдуть на покращення сервісів, зокрема на навчання моделей | 16868299 ; 13594961 | PASS | |
| Plus — 224,99 ₴/міс; 2× ліміти, відео, 128k, 400 ГБ | сторінка тарифів ; 16275805 | PASS | |
| ChatGPT Plus і Claude Pro — по $20 на місяць | https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus ; https://claude.com/pricing | PASS | Claude Pro коштує $20 при помісячній оплаті ($17 — за річної) |
| Pro — 909,99 ₴: 4×, Neon, 1 млн токенів, 5 ТБ | сторінка тарифів ; 18648722 ; 16275805 | PASS | |
| Ultra — від 4 599 ₴ (5× від Pro) або 9 099,99 ₴ (20× від Pro) | сторінка тарифів | PASS | |
| Студентам коледжів від 18 років, які відповідають вимогам, — AI Plus на рік безкоштовно, оформити до 31.12.2026 | https://gemini.google/students/?hl=uk | PASS | |
| Студентам потрібен спосіб оплати; після року — 224,99 ₴/міс, якщо не скасувати | там само | PASS | |
| Скасування: **Settings → Manage subscription** → Google One (озвучка і екран «Settings → Manage subscription → Google One») | 14517446 `?hl=uk` | **FAIL** | В українському інтерфейсі: «Налаштування» → «Керувати підпискою». Сам шлях правильний, неправильні назви пунктів для uk-UI |
| Скасувати можна будь-коли; за неповний період не повертають, крім випадків, передбачених законом | сторінка тарифів | PASS | |
| Коли план закінчується, зникають переваги Google One, зокрема додаткове місце | 14517446 | PASS | У довідці це описано на прикладі AI Pro, але логіка та сама |
| Налаштування «Історія дій»; увімкнене — автовидалення через 18 міс; можна 3, 36 міс або безстроково | https://support.google.com/gemini/answer/13594961?hl=uk | PASS | Оновлено 17.11.2026, як і на екрані |
| Навчання моделей тепер можна вимкнути окремо від історії | 13594961 ; https://blog.google/innovation-and-ai/products/gemini-app/updated-controls/ | PASS | |
| Google розгортає ці налаштування по всьому світу протягом кількох тижнів | blog.google updated-controls (16.11.2026) | PASS | У Google: «start rolling out … globally … in the coming weeks», тобто це дата початку, а не тривалість. Можна сказати точніше: «почне розгортати в найближчі тижні». Не FAIL |
| З вимкненою історією майбутні чати зберігаються ~2 місяці (відповідати, обробляти відгуки, захищати сервіс) | 13594961 (uk і en) | PASS | |
| Тимчасові чати — теж ~2 місяці; на навчання не йдуть; з вимкненою історією і без відгуків нові чати на навчання теж не йдуть | 13594961 | PASS | |
| Частину чатів читають спеціалісти; чати відокремлюють від акаунта; перевірені зберігаються до 3 років навіть після видалення | 13594961 | PASS | |
| Відгук разом із розмовою можуть перевірити люди і зберігати до 3 років | 13594961 | PASS | «Reviewed feedback, associated conversations … up to 3 years» |
| Цитата «Не вказуйте конфіденційну інформацію, якщо не хочете, щоб її переглядали спеціалісти» | 13594961 `?hl=uk` | PASS | Дослівний початок речення, 10 слів (до 15). У Google далі йде «…чи використовувала компанія Google…», обрізання сенсу не спотворює |
| Тимчасовий чат: кнопка поруч із «Новий чат»; не з'являється в історії і списку чатів; не працюють підключені застосунки, персоналізація, відгуки; після виходу повернутися не можна | 13275745 | PASS | |
| Google радить перевіряти відповіді | 13275745 | PASS | «double-check responses» |
| Гайд про Claude вийшов «минулого тижня» | studio/eps/guide2.py (вихід ср 2.12) | PASS | Внутрішній факт: 2.12 → 9.12 |
| Про ~2 місяці «вже розповідали в шоу» | content/posts/2026-11-22-shi-za-tyzhden-2.md | PASS | Розділ «Gemini тримає чати ~2 місяці» |
| Окремий розбір про приватність, посилання в описі | content/posts/2026-11-14-shcho-shi-znaye-pro-tebe-pryvatnist.md | PASS | |
| «Щонеділі — шоу „ШІ за тиждень“, щодня — короткі тір-листи» (аутро) | docs/org/dispatch-log.md (тір-листи, «ШІ за тиждень» #2) | PASS | Це розклад каналу, не факт про Google. Сторонніх джерел не потребує |

## Підсумок

- Тверджень: **84**
- **PASS: 81**
- **FAIL: 3** (усі три — назви пунктів інтерфейсу англійською, хоча гайд прямо веде глядача в український інтерфейс)
- **UNVERIFIED: 0**

Жодної фактичної помилки в цінах, лімітах, віці, доступності чи приватності не знайдено.
Необов'язкові уточнення (це не FAIL): «понад 40 мов» → можна «понад 70» (англійська довідка, оновлена); «розгортає протягом кількох тижнів» → «почне розгортати в найближчі тижні».

## Виправлення для кожного FAIL (точні заміни в studio/eps/guide3.py)

1. **Сегмент «Картинки: з 13, редагування — з 18»** (`text`):
   - було: `Відкрий бічне меню, розділ Images, обери шаблон або напиши свій запит.`
   - стане: `Відкрий бічне меню, розділ «Зображення», обери шаблон або напиши свій запит.`
   - Пару `("Images","Імеджіз")` у `G()` після цього можна прибрати.

2. **Сегмент «Переходиш з ChatGPT? Забери історію»** (`text`):
   - було: `Шлях: Settings, пункт Import memory to Gemini.`
   - стане: `Шлях: «Налаштування», пункт «Імпортувати пам'ять у Gemini».`

3. **Сегмент «Скасування»**:
   - `points[0]`: було `"Settings → Manage subscription → Google One"`, стане `"Налаштування → Керувати підпискою → Google One"`
   - `text`: було `У Gemini: Settings, пункт Manage subscription — відкриються налаштування Google One, де скасовуєш підписку.`
     стане `У Gemini: «Налаштування», пункт «Керувати підпискою» — відкриються налаштування Google One, де скасовуєш підписку.`

Після замін перевір assert у кінці файлу (сума `gsay` у частині ≤ 1300 знаків). Українські назви не довші за англійські транслітерації, тож межу не перевищать.

Вердикт: FAIL
