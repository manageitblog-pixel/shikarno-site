---
title: "Gemini 2.5 Pro і Flash підмінять 1 грудня: що перевірити розробникам"
slug: gemini-2-5-vymykayut-1-grudnya
date: 2026-11-07T14:00:00+02:00
description: "Google зробив Gemini 2.5 Pro і 2.5 Flash застарілими: з 1 грудня 2026 запити підуть на 3.8 Flash і 3.5 Flash-Lite. Що може зламатися в API і як підготуватися."
tags: [gemini, google, rozrobka]
youtube: hiUk0MF91SQ
telegram_post: 93
source: {name: "Google AI Studio: Gemini API changelog (2.11.2026)", url: "https://aistudio.google.com/docs/changelog"}
summary:
  - "2 листопада Google позначив gemini-2.5-pro і gemini-2.5-flash як застарілі."
  - "З 1 грудня 2026: 2.5 Pro → gemini-3.8-flash, 2.5 Flash → gemini-3.5-flash-lite."
  - "Google попереджає про зміни, що ламають сумісність: function calling, thought_signature, thinking_level."
  - "Порада: перемкнути модель і прогнати тести заздалегідь."
verdict: {score: 6, plus: "новіші моделі без зусиль", minus: "тихе перенаправлення може зламати інтеграції"}
faq:
  - q: "Коли перестане працювати Gemini 2.5 Pro?"
    a: "За changelog Google AI Studio, з 1 грудня 2026 року запити до gemini-2.5-pro перенаправлятимуть на gemini-3.8-flash."
  - q: "Що буде з Gemini 2.5 Flash?"
    a: "З 1 грудня 2026 запити до gemini-2.5-flash йтимуть на gemini-3.5-flash-lite."
  - q: "Що може зламатися після переходу?"
    a: "Google називає зміни, що ламають сумісність: виклик функцій (function calling), перевірку thought_signature і параметр thinking_level. Їх варто перевірити тестами до грудня."
---
Google оновив changelog Gemini API: моделі **Gemini 2.5 Pro** і **2.5 Flash** застарілі. Якщо твій бот, сервіс чи автоматизація працює на них — з **1 грудня 2026** запити підуть на інші моделі автоматично.

## Що на що зміниться

| Було | З 1.12.2026 |
|---|---|
| gemini-2.5-pro | gemini-3.8-flash |
| gemini-2.5-flash | gemini-3.5-flash-lite |

## Що може зламатися

Google прямо попереджає про зміни, що ламають сумісність:

- **виклик функцій** (function calling);
- **перевірка thought_signature**;
- **параметр thinking_level**.

## Що зробити зараз

- Знайди в коді й конфігах назви моделей `gemini-2.5-pro` і `gemini-2.5-flash`.
- Перемкни на нові моделі в тестовому середовищі й прожени тести, особливо сценарії з інструментами.
- Перевір якість відповідей: Flash-Lite — легша модель, ніж 2.5 Flash.

## Вердикт Байта

**6 з 10.** Новіші моделі — добре, але тихе перенаправлення в продакшні — погана несподіванка. Не відкладай до грудня.
