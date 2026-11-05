# Скіли, MCP і конектори — дослідження для розбору #1 (перевірено 5.11.2026)

## MCP (modelcontextprotocol.io/docs/getting-started/intro)
- Відкритий стандарт підключення ШІ-застосунків до зовнішніх систем: дані (файли, бази), інструменти (пошук, калькулятор), сценарії.
- Аналогія сайту: як USB-C для ШІ-застосунків. Підтримують Claude, ChatGPT, VS Code, Cursor тощо.
- Створений Anthropic (support.claude.com 11175166: «open standard created by Anthropic»).

## Claude Skills (support.claude.com/en/articles/12512180)
- Тарифи: Free, Pro, Max, Ultra, Team, Enterprise; потрібне виконання коду.
- Free/Pro/Max/Ultra: Settings > Capabilities → «Code execution and file creation» («Create and edit files»). Далі Customize > Skills — перемикачі.
- Claude сам застосовує доречні скіли.
- Вбудовані: Excel, Word, PowerPoint, PDF.
- Свій скіл: папка за структурою → ZIP → Customize > Skills → «+» → «+ Create skill» → «Upload a skill». Видно лише тобі, поки не поділишся (Team/Enterprise).
- Безпека: ризики prompt injection і витоку даних; ставити лише з довірених джерел, переглядати файли, скрипти, мережеві з'єднання.
- Скіли працюють і в Claude for Excel/PowerPoint/Word/Outlook (/ у бічній панелі).

## Claude custom connectors / remote MCP (support.claude.com/en/articles/11175166)
- Free, Pro, Max, Ultra, Team, Enterprise; Free — лише 1 custom connector.
- Pro/Max: Customize > Connectors → «+ Add» → «Add custom connector» → назва + URL сервера → авторизація → Add.
- У чаті: «+» внизу ліворуч → Connectors → перемикачі на розмову.
- Не перевіряються Anthropic; можуть читати й змінювати дані в межах дозволів; «Allow always» лише для довірених; відкликати доступ можна будь-коли.
- Під час Research Claude може викликати інструменти без підтвердження — вимикати інструменти запису.

## Gemini Skills (support.google.com/gemini/answer/17094296)
- 18+, вхід в акаунт, увімкнена Keep Activity; мобільний застосунок, Mac, веб.
- Для чатів підписка не потрібна (Tasks і розклад — потрібна Google AI).
- gemini.google.com → бічна панель Customize (або More) → Skills.
- Створення: «Create with Gemini», шаблон з «Recommended», вручну, Upload (SKILL.md / папка / .zip до 100 МБ), або попросити в чаті.
- Виклик: «/» (або «@») у чаті; активні скіли Gemini застосовує сам; можна комбінувати.
- Файли-референси: з пристрою, Drive, Photos, Notebooks; формати pdf/docx/md/txt/csv/xlsx/pptx/png/jpg/код. Скрипти без доступу до інтернету.
- Приклади Google: виписки банку → таблиця, описи товарів, кар'єрні поради за резюме, поєднання скілів.
- Gems автоматично перетворять на скіли, коли їх приберуть.

## ChatGPT (OpenAI 403 → з пошуку по домену, позначати)
- openai.com/index/introducing-apps-in-chatgpt: застосунки в ChatGPT для залогінених користувачів Free, Go, Plus, Pro поза ЄЕЗ, Швейцарією і Британією (на момент запуску).
- help.openai.com 12584461 (сніпет пошуку): власні MCP-сервери — Business, Enterprise/Edu (повний MCP); Pro — підключення з правами читання/fetch. Free не згадано.
- developers.openai.com/api/docs/mcp: ChatGPT вимагає ручного підтвердження перед діями запису; власні MCP-сервери OpenAI не перевіряє.
