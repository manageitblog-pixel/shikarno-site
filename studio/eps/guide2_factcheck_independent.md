# Гайд #2 «Claude безкоштовно» — незалежний фактчек (22.11.2026)

Перевірено всі поля `text` у SEGS файлу studio/eps/guide2.py (сегменти 0–47) за сторінками, відкритими 22.11.2026.
Номери сегментів — порядкові індекси в SEGS. Номерів версій моделей у тексті немає — OK.

## Джерела
- P = https://claude.com/pricing (картки, таблиця порівняння, FAQ)
- GS = https://support.claude.com/en/articles/8114491-get-started-with-claude
- UL = https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work
- BP = https://support.claude.com/en/articles/9797557-usage-limit-best-practices
- PRO = https://support.claude.com/en/articles/8325606-what-is-the-pro-plan
- AGE = https://support.claude.com/en/articles/13117299-minimum-age-requirement-access-restriction
- LANG = https://support.claude.com/en/articles/10769299-how-to-use-claude-in-your-preferred-language
- REG = https://www.anthropic.com/legal/supported-regions (сюди редиректить anthropic.com/supported-countries; редакція від 12.11.2026)
- LOGIN = https://support.claude.com/en/articles/13189465-log-in-to-your-claude-account
- MODEL = https://support.claude.com/en/articles/8664678-change-the-model-effort-and-thinking-settings
- UP = https://support.claude.com/en/articles/8241126-upload-files-to-claude
- FILES = https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude
- ART = https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them
- IMG = https://support.claude.com/en/articles/9002504-can-claude-produce-images
- MEM = https://support.claude.com/en/articles/12123587-import-and-export-your-memory-from-claude
- INC = https://support.claude.com/en/articles/12260368-use-incognito-chats
- RET = https://privacy.claude.com/en/articles/10023548-how-long-do-you-store-my-data
- TRAIN = https://privacy.claude.com/en/articles/10023580-is-my-data-used-for-model-training
- PRIV = https://privacy.claude.com/en/articles/12109829-how-do-i-change-my-model-improvement-privacy-settings
- TERMS = https://www.anthropic.com/news/updates-to-our-consumer-terms
- IOS = https://apps.apple.com/ua/app/claude-by-anthropic/id6473753684
- OAI = https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq (вже перевірено для гайду #1, guide1_factcheck_independent.md)

## Таблиця

| Сегм. | Твердження | Джерело | Статус | Примітка |
|---|---|---|---|---|
| 0 | Free робить файли Excel/Word, міні-застосунки (артефакти), пам'ять; ліміт на 5 год | P, FILES, ART, GS | PASS | |
| 3 | Claude — LLM від Anthropic, навчений бути корисним, чесним і нешкідливим | GS | PASS | «Helpful, honest, and harmless» |
| 3 | Родини Haiku, Sonnet, Opus, Fable; Fable найсильніша; у Free є Sonnet і Haiku, Opus і Fable — ні | P (таблиця Models; FAQ «Fable, our top model») | PASS | |
| 4 | ChatGPT Free: текстові чати без ліміту, малює картинки, інтерфейс українською | OAI | PASS | Перевірено в гайді #1 |
| 4 | У Claude все рахується в одне вікно на 5 год | UL, P FAQ | PASS | Усі продукти Claude беруть з одного ліміту |
| 4 | **«у Claude [інтерфейсу українською] — ні»** | LANG, IOS | **FAIL** | LANG стосується лише вебу й ПК (11 мов, української немає). У списку мов застосунку для iPhone в App Store (UA) є Ukrainian. Треба уточнити: веб і ПК |
| 4–5 | Claude не генерує фото й ілюстрації; робить схеми, діаграми, інтерактивні візуалізації в розмові; аналізує завантажені картинки | IMG | PASS | Візуалізації — бета на вебі й ПК |
| 7 | Україна в списку, крім Криму, Донецької, Луганської, Херсонської, Запорізької областей; треба перебувати в підтримуваній локації | REG, GS | PASS | |
| 8 | Лише з 18 років; App Store 18+ | GS, AGE, IOS | PASS | |
| 9 | Веб, Desktop для Windows і Mac, iPhone, Android; розробник Anthropic PBC; iOS 18+ | GS, IOS | PASS | |
| 10 | Вхід через Google або email-посилання; пароля створити не можна; спам/mail.anthropic.com; той самий email на телефоні | LOGIN | PASS | |
| 11, 41 | Від галочки залежить 30 днів або до 5 років зберігання; змінити можна будь-коли | TERMS, RET, PRIV | PASS | 5 років — лише для нових/продовжених чатів, знеособлено (сегм. 41 це каже) |
| 12 | 11 мов інтерфейсу на вебі й ПК, перелік; української немає; можна писати будь-якою мовою | LANG | PASS | Тут скоуп правильний (веб і ПК) |
| 13 | Голос: Settings → Capabilities → Voice → Spoken language; пам'ять є у Free | LANG, P | PASS | |
| 14 | «+» ліворуч унизу поля вводу; модель біля кнопки надсилання; «More models»; змінити посеред розмови; профіль ліворуч унизу | GS, MODEL, LANG | PASS | |
| 16 | Картка Free: $0; чат веб/ПК/моб.; пошук, файли, код; пам'ять; застосунки; артефакти; Claude Design, Slides, Docs | P | PASS | |
| 17 | У Free немає Opus, Fable, Research, Claude Code, Chrome, Microsoft 365; є голос, інкогніто, навички | P (таблиця) | PASS | |
| 18 | 5-годинне вікно від першого повідомлення, повне оновлення; кількість не названо, залежить від попиту; Claude повідомить; Settings → Usage | GS, UL | PASS | |
| 19 | Суперечність щодо тижневого ліміту у Free | P vs UL, P FAQ | PASS | Підтверджено: картка Free «every 5 hours and every week» і рядок таблиці «Limit every week: Limited» проти UL («Paid plans have… weekly limits») і FAQ P («paid plans add weekly limits on top»). Подано нейтрально. Необов'язково: додати «і в таблиці» поруч із карткою |
| 20 | Довгий чат, великі файли, застосунки й пошук витрачають більше; нижчий Effort розтягує ліміт | BP, UL, MODEL | PASS | «Перечитує всю розмову» — пояснення своїми словами, BP: «Current conversation length» |
| 21 | Історію чатів імпортувати не можна; імпорт пам'яті є у Free на вебі й ПК; Settings → Your Claude → Start import | GS, MEM | PASS | MEM попереджає, що функція експериментальна |
| 23 | Говорити з Claude як з колегою, бути конкретним, уточнювати | GS | PASS | |
| 24–25 | «+» → «Add files or photos»; до 20 файлів на чат, 500 МБ кожен; PDF до 1000 стор.; візуальні елементи лише в PDF до 100 стор.; JPEG, PNG, GIF, WebP | UP | PASS | XLSX потребує ввімкненого створення файлів |
| 27 | Код і файли — для всіх, включно з Free, веб/ПК/моб.; Excel з формулами, PowerPoint, Word, PDF; у Free увімкнено за замовчуванням; Settings → Capabilities | FILES | PASS | |
| 30 | Фото від 1000×1000 пікселів | UP | PASS | |
| 32 | Артефакти на всіх планах включно з Free; Docs, Slides, Design — теж; відкриваються поруч, редагуються, діляться | ART | PASS | |
| 34 | Проєкти: таблиця «Up to 5» для Free проти картки Pro й FAQ | P | PASS | Підтверджено: таблиця «Projects: Up to 5», картка Pro містить «Projects», FAQ «What do I get with Claude Pro?» — «projects to organize your chats». Подано нейтрально |
| 36 | Pro $20/міс або $17/міс за рік ($200 одразу); щонайменше в 5 разів більше за 5-годинну сесію, ніж Free; Opus, Research, Claude Code, проєкти; Fable за кредити | P | PASS | |
| 37 | Ціни в USD без податків; Max $100 (5× Pro, Fable до половини тижневого ліміту); Ultra $200 (10× тижневого використання Pro, без 5-год ліміту для верифікованих); Team $25/$20 за місце | P | PASS | |
| 38 | Ціна залежить від регіону, податок входить або додається; claude.ai/upgrade або магазин; скасування Settings → Billing або в App Store/Google Play; після скасування — Free, чати лишаються | PRO, P FAQ | PASS | |
| 39 | Офіційна оплата — в акаунті й у магазинах застосунків | P FAQ | PASS | Порада редакції, яка не суперечить джерелу |
| 41 | Settings → Privacy → «Help improve our AI models»; нові чати не йдуть у навчання; вже використане лишається | PRIV, RET | PASS | |
| 42 | Видалений чат зникає з історії одразу, із серверів за 30 днів; позначені — до 2 років; оцінки зберігають розмову до 5 років | RET, TRAIN | PASS | 2 роки — для вхідних і вихідних даних; оцінки класифікаторів зберігають до 7 років (у тексті цього немає, і це OK) |
| 43 | Інкогніто є у Free; іконка привида вгорі праворуч; не потрапляє в історію/пам'ять, не для навчання; зберігається 30 днів; закритий не відкриєш | INC, RET | PASS | INC: у новому інтерфейсі в інкогніто не можна створювати файли й запускати код (у тексті не згадано, і це не помилка) |
| 45 | **«кнопки англійською»** | LANG, IOS | **FAIL** | Те саме узагальнення, що в сегм. 4: застосунок для iPhone в App Store має українську локалізацію |
| 45 | Free: пошук, пам'ять, файли, артефакти, застосунки; найсильніших моделей немає; 18+ | P, GS | PASS | |
| 1, 2, 6, 15, 22, 26, 28–29, 31, 33, 35, 40, 44, 46–47 | Навігація, промпти, поради | — | PASS | Фактичних тверджень про продукт немає або вони повторюють уже перевірені |

## Вердикт: FAIL → 22.11 виправлено сегменти 4, 19, 45 дослівно за рекомендацією → PASS

Потрібні 2 точкові заміни (усе інше PASS). Відповідно оновити `gsay` і перевірити assert `≤1300` на частину:

1. Сегмент 4 (kind="compare"), `text`:
   - було: «Третя — мова кнопок: у ChatGPT інтерфейс є українською, а в Claude — ні.»
   - стало: «Третя — мова кнопок: у ChatGPT інтерфейс є українською, а в Claude на вебі й у програмі для комп'ютера — ні.»
2. Сегмент 45 (вердикт), `text`:
   - було: «…найсильніших моделей у Free немає, кнопки англійською, і користуватися можна лише з вісімнадцяти.»
   - стало: «…найсильніших моделей у Free немає, кнопки на вебі й у програмі для комп'ютера англійською, і користуватися можна лише з вісімнадцяти.»

Необов'язково, для повноти (сегм. 19): «На картці безкоштовного плану написано…» → «На картці безкоштовного плану і в таблиці порівняння написано…».

## Сторінка сайту (content/posts/2026-10-29-claude-bezkoshtovno.md) — виправлено
- «Чого немає у Free: … Projects» — FAIL (таблиця P: «Up to 5»). Projects прибрано зі списку й описано розбіжність нейтрально.
- Тижневий ліміт у Free (summary, FAQ, розділ «Ліміти») подавався як безумовний факт. Тепер текст указує на розбіжність між карткою й таблицею з одного боку і FAQ та довідкою UL з другого.
- Ultra: «у 10 разів більше, ніж у Pro, без 5-годинного ліміту» → «у 10 разів більше тижневого використання… без 5-годинного ліміту для верифікованих акаунтів» (P).
- Інтерфейс: «інтерфейсу українською немає» і «кнопки й англійською» уточнено: на вебі й у програмі для ПК (LANG, IOS).
- Інші твердження про ліміти (usage credits лише на платних, Max — пріоритет у години пік, Team Premium $125/$100, Enterprise $20/місце + API) — PASS.
