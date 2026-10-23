# @ShikarnoPartnersBot — заявки на співпрацю

Cloudflare Worker (worker.js), вебхук Telegram. Деплой — `.github/workflows/bot.yml` при зміні bot/**.
Секрети GitHub: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, PARTNERS_BOT_TOKEN, PARTNERS_ADMIN_CHAT_ID, PARTNERS_WEBHOOK_SECRET.

Сценарій: /start → формат → бюджет → терміни → опис і контакт (відповіддю) → заявка адміну.
Адмін відповідає на заявку (reply) → бот пересилає відповідь заявнику. Будь-яке вільне повідомлення теж іде адміну.
Команди: /start, /formats, /contact, /myid.
