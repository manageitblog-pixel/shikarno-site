# Instagram + Threads напряму через API Meta (без vidIQ)

Оновлено: 23.11.2026. Навіщо: власна обкладинка Reels (`cover_url`), сторіз, пости в Threads — те, чого не дає vidIQ.
Позначка **[перевіримо на екрані разом]** = у документації Meta цієї кнопки/шляху не знайшли, звіримо наживо.

---

## Частина 1. Для власника (~15 хв, з компа)

Що треба мати: Facebook-акаунт (вхід на developers.facebook.com), Instagram @shikarno_ai_ua — професійний і **публічний**, Threads-профіль на тому ж Instagram.

### URL, які вписуємо в застосунок (копіюй звідси)

| Поле | Значення |
|---|---|
| Privacy Policy URL | `https://shikarno.com.ua/pryvatnist/` |
| Terms of Service URL | `https://shikarno.com.ua/umovy/` |
| Redirect URL / OAuth Redirect URIs (Instagram і Threads) | `https://shikarno.com.ua/meta-callback/` |
| Deauthorize callback URL (Instagram), Uninstall callback (Threads) | `https://shikarno.com.ua/meta-callback/` |
| Data deletion request URL (Instagram), Delete callback (Threads) | `https://shikarno.com.ua/meta-callback/` |

Сторінка `/meta-callback/` — службова (noindex): «авторизацію завершено» + інструкція з видалення даних. Політика й умови вже згадують застосунок Meta.
Увага: Meta порівнює redirect **дослівно** (може сама додати `/` в кінці) — вписуй рівно як у таблиці.

### Крок 1. Створити застосунок для Instagram
1. developers.facebook.com → My Apps → **Create App** (кнопка вгорі праворуч).
2. Use case: **Other** → Next. Тип: **Business** → Next.
3. Назва: `ShIkarno Publisher`, контактний email → Next. Бізнес-портфоліо можна підключити пізніше (App settings > Basic) — для власного акаунта зараз не потрібно.
4. У списку продуктів знайди **Instagram** → **Set up**. З'явиться розділ **API setup with Instagram login**.

### Крок 2. Підключити свій Instagram і отримати токен Instagram
1. Ліве меню: **Instagram > API setup with Instagram business login**.
2. У блоці про токени — **Add account** (додати Instagram-акаунт) → увійди як @shikarno_ai_ua. **[точну назву кнопки перевіримо на екрані разом]**
3. Якщо Meta попросить прийняти запрошення тестувальника: в Instagram (веб) → налаштування → «Apps and websites» → вкладка «Tester invites» → Accept. **[шлях з неофіційних джерел — перевіримо на екрані разом]** Альтернатива: App roles > Roles → Add People → Instagram Tester.
4. Біля свого акаунта натисни **Generate token** → увійди в Instagram → скопіюй токен. **Не надсилай його в чат!**
5. Блок «3. Set up Instagram business login» → **Set up** → впиши Redirect URL з таблиці; у **Business login settings** — OAuth Redirect URIs, Deauthorize callback URL, Data deletion request URL → **Save**.
6. App settings > Basic: впиши Privacy Policy URL і Terms of Service URL → Save. **[розташування полів перевіримо на екрані разом]**

Цей токен — **довготривалий, 60 днів** (так пише Meta про токени з дашборда).

### Крок 3. Threads
1. Threads потребує **окремого use case «Threads»**: або **Create App** ще раз → use case **Threads** (назва `ShIkarno Threads`), або додати use case Threads у той самий застосунок. **[що з двох запропонує екран — перевіримо разом]** Увага: у Threads-застосунку свій окремий App ID і секрет — бери саме «Threads App ID».
2. У налаштуваннях use case увімкни дозволи `threads_basic` і `threads_content_publish`; впиши Redirect / Uninstall / Delete callback URL з таблиці. **[назви полів перевіримо на екрані разом]**
3. **App roles > Roles → Add People → Threads Tester** → свій профіль.
4. Прийми запрошення: Threads (сайт або застосунок) → Налаштування акаунта → **Website permissions** → запрошення → Accept.
5. Отримати токен: у налаштуваннях use case Threads шукаємо генератор токена користувача. **[у документації не описаний — перевіримо на екрані разом]** Якщо його нема — робимо вхід через `https://threads.com/oauth/authorize?...` (посилання збере студія), обмін коду на токен потребує секрету застосунку — його теж вносимо лише через захищену форму, не в чат.

### Крок 4. Передати токени студії (безпечно)
Студія відкриє **захищену форму середовища** (два запити):
- хост **`graph.instagram.com`** — токен Instagram з кроку 2;
- хост **`graph.threads.net`** — токен Threads (і, якщо попросимо, той самий ще раз для `graph.threads.com` — у Meta два робочі домени Threads).

Тип: Bearer (заголовок `Authorization: Bearer …`). Токен вводиш лише у форму — ні в чат, ні в репо, ні в Telegram.

### Чого НЕ треба
App Review і публікація застосунку (Live) **не потрібні**: ми публікуємо лише у свій акаунт. Instagram дає Standard Access для акаунтів, якими ти володієш і які додані в застосунок; у Threads тестувальники можуть надати будь-які дозволи без App Review.

---

## Частина 2. Для студії (технічна)

### Токени
| | Instagram | Threads |
|---|---|---|
| Хост | `graph.instagram.com` | `graph.threads.net` (=`graph.threads.com`, обидва робочі за changelog) |
| Звідки | App Dashboard → Generate token (одразу long-lived) | OAuth code → short-lived (1 год) → `GET /access_token?grant_type=th_exchange_token&client_secret=…` |
| Термін | 60 днів | 60 днів |
| Оновлення | `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=…` | `GET https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=…` |
| Умови оновлення | токен ≥24 год і не прострочений; `instagram_business_basic` | ≥24 год, не прострочений; `threads_basic`. Не оновлений за 60 днів — помирає назавжди |

**Оновлення без власника — можна**: refresh не потребує ні входу користувача, ні секрету застосунку. Але refresh **повертає НОВИЙ токен у тілі відповіді**, а збережений у проксі ключ лишиться старим → після refresh треба знову внести новий токен через форму (або ж щомісяця просити власника згенерувати новий). План: раз на ~45 днів робимо refresh і одразу оновлюємо секрет середовища. Нагадування — у RUNBOOK. Проксі підставляє `Authorization: Bearer`; refresh документований з `access_token` у query — першим ділом перевірити, чи endpoint приймає Bearer-заголовок (якщо ні — refresh робить власник у браузері або через форму).

Перевірка токена: `GET https://graph.instagram.com/v27.0/me?fields=user_id,username,account_type` (Instagram), `GET https://graph.threads.net/v1.0/me?fields=id,username` (Threads).

### Instagram: Reel з обкладинкою
```
POST https://graph.instagram.com/v27.0/<IG_ID>/media
  media_type=REELS
  video_url=https://…/reel.mp4        # публічний URL на момент виклику
  cover_url=https://…/cover.jpg       # обкладинка для вкладки Reels; має пріоритет над thumb_offset
  caption=…  share_to_feed=true       # true = і стрічка, і Reels
→ {id: <CONTAINER_ID>}
GET  …/<CONTAINER_ID>?fields=status_code     # FINISHED | IN_PROGRESS | ERROR | EXPIRED | PUBLISHED; раз на хв, ≤5 хв
POST …/<IG_ID>/media_publish  creation_id=<CONTAINER_ID>
```
Специфікація відео: MP4/MOV, moov atom спереду, H264/HEVC, AAC ≤48 кГц, 23–60 fps, ширина ≤1920, 9:16, ≤25 Мбіт/с, 3 с–15 хв, ≤300 МБ. Зображення — лише JPEG. Контейнер не опублікований за 24 год → EXPIRED.

### Instagram: Story
```
POST …/<IG_ID>/media  media_type=STORIES  image_url=…jpg   (або video_url=…)
→ status_code → media_publish як вище
```
Стікери посилань/опитувань/локації через API не публікуються; collaborators для Stories не підтримуються.

### Threads: пост
```
POST https://graph.threads.net/v1.0/<THREADS_USER_ID>/threads
  media_type=TEXT|IMAGE|VIDEO  text=…  [image_url|video_url]  [link_attachment — лише для TEXT]
→ {id}; чекати ~30 с (для відео — статус)
GET  …/<CONTAINER_ID>?fields=status,error_message   # FINISHED | IN_PROGRESS | ERROR | EXPIRED | PUBLISHED
POST …/<THREADS_USER_ID>/threads_publish  creation_id=<id>
```
Текст ≤500 знаків (емодзі рахуються за байтами UTF-8); ≤5 унікальних посилань на пост (інакше `THREADS_API__LINK_LIMIT_EXCEEDED`).

### Ліміти
- Instagram: `GET …/<IG_ID>/content_publishing_limit?fields=config,quota_usage`. Довідник: **50 контейнерів / 24 год**; гайд Content Publishing пише «100 постів / 24 год» — документація суперечить сама собі, **довіряти відповіді `config.quota_total`**. Карусель = 1.
- Threads: `GET …/<THREADS_USER_ID>/threads_publishing_limit?fields=quota_usage,config` — 250 постів і 1000 відповідей / 24 год.
- Нам вистачає з запасом (1–3 Reels + кілька сторіз на день).

### Джерела (Meta, перевірено 23.11.2026)
- Get started (Instagram Login): https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started
- Create an Instagram app: https://developers.facebook.com/docs/instagram-platform/create-an-instagram-app
- Business Login / scopes / обмін токена: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login
- Refresh токена Instagram: https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token
- Content Publishing: https://developers.facebook.com/docs/instagram-platform/content-publishing
- IG User media (cover_url, Stories, специфікації): https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media
- content_publishing_limit: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit
- Threads get started (тестувальники, токени): https://developers.facebook.com/docs/threads/get-started
- Threads access tokens: https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions
- Threads long-lived tokens: https://developers.facebook.com/docs/threads/get-started/long-lived-tokens
- Threads posts: https://developers.facebook.com/docs/threads/posts
- Threads troubleshooting (статус, ліміти): https://developers.facebook.com/docs/threads/troubleshooting
- Threads changelog (домени .net/.com): https://developers.facebook.com/docs/threads/changelog
- App roles: https://developers.facebook.com/docs/development/build-and-test/app-roles

## План після підключення (власник 23.11)
- Сторіз щодня: анонс ролика дня + заклик на Telegram / YouTube / TikTok. Перевірити, чи API підтримує стікер-посилання в сторіз (за нашими даними — ні; тоді «посилання в профілі»).
- Reels — переходять з vidIQ на пряме API з `cover_url` (обкладинка окремо, без 0,5 с кадру).
- Threads — той самий ролик/текст дня.
- Щоденний тригер «Instagram Reel дня» (19:23 Київ) — розширити на сторіз і Threads.
