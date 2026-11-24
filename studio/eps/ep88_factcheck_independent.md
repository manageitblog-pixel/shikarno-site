Вердикт: PASS

# Незалежний фактчек ep88 — «ChatGPT Plus: не плати, поки не перевіриш ці 3 речі» (24.11.2026)

Перевіряв: незалежний фактчекер (сценарій не писав). Об'єкт: studio/eps/ep88.py — text і gsay усіх сцен, пункти items, KEYS, назва, перший коментар, опис.
Першоджерела відкрито 24.11.2026 під час перевірки; коментарі-шапку сценарію за джерело не брав.

| Твердження | Джерело | Статус | Нотатка |
|---|---|---|---|
| Plus коштує $20 («20 доларів», KEYS «$20/міс») | https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus | PASS | «$20/month (billed monthly)». chatgpt.com/pricing у знімку сум не показує; в описі позначено «ціна OpenAI» — ок |
| «Текстові чати без ліміту» (Free) | https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq ; https://chatgpt.com/pricing | PASS | «unlimited everyday text chats, subject to abuse-prevention safeguards»; pricing: «Unlimited text chats subject to abuse guardrails». Застереження є в описі |
| Пошук, файли й картинки — з лімітом (Free) | 9275245 | PASS | Пошук у Free є; «File uploads, image generation… have separate usage limits» |
| Загального тріалу немає — лише запрошення | https://help.openai.com/en/articles/8381046 ; 6950777 ; chatgpt.com/pricing | PASS | Тріали лише через invite/referral/promo; на сторінці Plus і тарифів тріалу немає |
| «Іноді — з карткою» | 8381046 | PASS | «Some promotions require adding a valid payment method» |
| Тріал «може сам стати платною підпискою» | 8381046 | PASS | «Others renew as paid subscriptions» |
| Пункт екрана «Далі — платно» | 8381046 | ВИПРАВЛЕНО | Узагальнення: частина промо просто закінчується. Замінено на «Може стати платним» |
| Сайт: Налаштування → Billing → Cancel | https://help.openai.com/en/articles/7232927 | PASS | Settings → Billing → «Cancel plan» → Cancel |
| iPhone — через Apple (опис: Налаштування → твоє імʼя → Підписки) | 7232927 | PASS | Settings app → your name → Subscriptions → ChatGPT → Cancel Subscription |
| Android — Google Play → Підписки (опис) | 7232927 | PASS | Play Store → Subscriptions → ChatGPT → Cancel subscription |
| «За добу до списання» / «щонайменше за 24 год» | 7232927 | PASS | «Cancel at least 24 hours before your next billing date» |
| Видалити застосунок — не скасування | 7232927 | PASS | «Uninstalling the app does not cancel your subscription» |
| Опис: гроші автоматично не повертають | 7232927 | PASS | «does not automatically refund previous charges» |
| Назва, хук, outro, перший коментар | — | PASS | Питання/заклики без нових фактів |
| gsay без «ШІ» великими й без латиниці | — | PASS | Вимова «Чат Джі-Пі-Ті», «Біллінг», «Еппл»; gsay 470 знаків |

## Підсумок
14 PASS, 1 дрібна неточність виправлена прямо в сценарії, 0 FAIL. Цифра $20 — ціна OpenAI (позначено). Російських джерел і Semrush не використано.

## Зміна
```diff
- items=[["warning","Лише за запрошенням"],["money","Іноді — з карткою"],["bolt","Далі — платно"]],
+ items=[["warning","Лише за запрошенням"],["money","Іноді — з карткою"],["bolt","Може стати платним"]],
```
