---
title: "Конектори Claude від А до Я: Google Drive, Gmail, Календар і свій MCP-сервер — розбір #5"
slug: konektory-claude-vid-a-do-ya
kind: rozbir
number: 5
date: 2026-11-11T19:00:00+02:00
description: "Як підключити Google Drive, Gmail і Календар до Claude, які дозволи ставити в Tool permissions і як написати свій MCP-сервер у терміналі. Кроки, ліміти і 4 правила безпеки."
tags: [claude, instrumenty, biznes, rozrobka, google]
youtube: kKYvFHKIvKM
telegram_post: 111
duration: "10:03"
chapters: [{t: "0:00", title: "Вступ"}, {t: "0:38", title: "Що таке конектор і MCP", link: "/novyny/skil-konektor-mcp-prostymy-slovamy/"}, {t: "1:23", title: "Google Drive у Claude"}, {t: "3:12", title: "Gmail і Календар"}, {t: "5:24", title: "Свій MCP-сервер (реальний термінал)"}, {t: "8:23", title: "Безпека", link: "/novyny/3-pravyla-bezpeky-konektoriv/"}, {t: "9:26", title: "Коротко"}, {t: "9:46", title: "Фінал"}]
source: {name: "Claude Help Center: Use Google Workspace connectors", url: "https://support.claude.com/en/articles/10166901-use-google-workspace-connectors"}
sources:
  - {name: "Claude Help Center: Use connectors to extend Claude's capabilities", url: "https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities"}
  - {name: "Model Context Protocol: What is MCP", url: "https://modelcontextprotocol.io/docs/getting-started/intro"}
  - {name: "Model Context Protocol: Build an MCP server", url: "https://modelcontextprotocol.io/docs/develop/build-server"}
summary:
  - "Конектор дає Claude доступ до сервісу (Диск, пошта, календар), MCP — відкритий стандарт таких підключень."
  - "Google Drive, Gmail і Календар підключаються в Customize → Connectors на всіх тарифах Claude; у Team/Enterprise спершу вмикає власник організації."
  - "Claude може писати чернетки, надсилати листи й ставити зустрічі — але за замовчуванням питає підтвердження. Дозволи налаштовуються в Tool permissions."
  - "Свій MCP-сервер на Python — кілька десятків рядків; головне правило stdio-сервера — нічого не друкувати в stdout."
verdict: {score: 9, plus: "реальна економія годин на пошті й документах, працює навіть на безкоштовному тарифі", minus: "це доступ до твоїх даних: обережно з дозволами «Always allow»"}
faq:
  - q: "Як підключити Google Drive до Claude?"
    a: "Відкрий Customize → Connectors, обери Google Drive і увійди через Google. Потім у чаті натисни «+» → Add from Google Drive і вибери файл або встав посилання. Claude читає Docs, Sheets, Slides, PDF і файли Office, але лише текст — картинки всередині документів не обробляє."
  - q: "Чи може Claude сам надіслати лист з Gmail?"
    a: "Так, за довідкою Anthropic Claude може надсилати, відповідати й пересилати листи та створювати події в Календарі. За замовчуванням він питає підтвердження перед кожною такою дією. Вміст вкладень у листах Claude не бачить — лише їх назви."
  - q: "Чи тренує Anthropic моделі на моїй пошті й Диску?"
    a: "Anthropic заявляє, що не тренує моделі на даних конекторів Gmail, Drive і Calendar. Але якщо на споживчому тарифі ти дозволив використання чатів для покращення моделей, вміст, скопійований у чат, може туди потрапити. Відключити конектор можна в Customize → Connectors → Disconnect."
---
Це базовий розбір: про конектори ми більше не пояснюватимемо з нуля — у нових роликах посилатимемося сюди. Нижче — все з відео, з кроками й посиланнями.

## Що таке конектор і MCP

**Конектор** — це доступ ШІ до твого сервісу: Диска, пошти, календаря. **MCP** (Model Context Protocol) — відкритий стандарт, за яким такі підключення будуються. На офіційному сайті його порівнюють з USB-C: один роз'єм для різних пристроїв. Детальніше простими словами — [у цій статті](/novyny/skil-konektor-mcp-prostymy-slovamy/).

## Google Drive у Claude

1. **Customize → Connectors** → Google Drive → увійти через Google.
2. У чаті: **«+» → Add from Google Drive** → знайти файл або вставити посилання.
3. У приватному проєкті: **Files → «+» → Drive**.

Claude шукає й читає Google Docs, Sheets, Slides, PDF, файли Office — **лише текст**, картинки всередині документів не бачить. Кілька файлів мають влазити в контекст розмови. Доступ — лише до підключеного акаунта і лише коли ти просиш.

## Gmail і Календар

За довідкою Anthropic, Claude уміє:

- **Gmail:** шукати й читати листи звичайною мовою, писати чернетки, працювати з мітками; **надсилати, відповідати й пересилати** — з твоїм підтвердженням. Вміст вкладень недоступний.
- **Календар:** дивитися події (і спільні календарі), **створювати, змінювати й видаляти** зустрічі, шукати спільний вільний час, відповідати на запрошення.

**Промпти для бізнесу:**
- «Знайди всі листи від клієнтів за тиждень, де питають про ціну, і склади таблицю: хто, що питав, чи відповіли».
- «Знайди у вівторок і середу годину, вільну в мене і в Олени, і створи зустріч "Планування грудня"».

## Дозволи: Tool permissions

**Customize → Connectors → конектор → Tool permissions** — для кожної дії: **Always allow** (без питань), **Needs approval** (з підтвердженням) або **Blocked** (заборонено). Порада: читання — «Always allow», надсилання й видалення — «Needs approval».

## Свій MCP-сервер (для айтішників)

У відео ми в реальному терміналі зібрали сервер, який віддає Claude курс валют НБУ. Каркас за офіційним гайдом modelcontextprotocol.io:

```python
from mcp.server import MCPServer

mcp = MCPServer("nbu")

@mcp.tool()
async def rate(code: str) -> str:
    """Курс валюти НБУ на сьогодні."""
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Головне правило stdio-сервера: **нічого не друкуй у stdout** — `print()` ламає обмін повідомленнями. Логи пиши через `logging`.

## 4 правила безпеки

1. **Лише сервери від тих, кому довіряєш.** Anthropic пише, що власні (кастомні) конектори вона не перевіряє, а шкідливий сервер може містити приховані інструкції. Локальний MCP-сервер — звичайна програма з твоїми правами на комп'ютері.
2. **Найменші права**, а не «повний доступ».
3. **Усе, що пише, надсилає чи видаляє, — з підтвердженням** (Needs approval).
4. **Невикористане — відключи**: Disconnect у Claude і myaccount.google.com/connections у Google.

Детальніше — [3 правила безпеки конекторів](/novyny/3-pravyla-bezpeky-konektoriv/).
