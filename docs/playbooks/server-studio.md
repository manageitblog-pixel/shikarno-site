# Плейбук: власний сервер-студія (план, 26.11.2026)

Статус: **ПЛАН, рішення за власником.** Власник 25.11: «нормальний сервер взяти і там побудувати систему гарну з усім — прям студію, і там сейвити»; «підготуй план, я подумаю, поки працюємо по старій схемі»; раніше — «спершу результат, потім інвестую».
До рішення працюємо як зараз: хмарний контейнер Claude Code + bootstrap.sh + резерв у git (озвучка, ops) + нічний резерв у Google Drive (drive_sync.py).
Російські сервіси й хостинги не розглядаємо. Секретів у цьому файлі немає і не буде.

## (а) Навіщо: що це вирішує

| Проблема зараз | Що дає сервер |
|---|---|
| Рестарт контейнера 25.11 стер mp4, WAV, ops.sqlite, токени. Відновлюємо з git і Drive, але медіа в git не кладемо, а Drive-токен живе ~7 днів (режим Testing). | Постійний диск. Медіа, бази й секрети лежать на сервері, контейнер стає «тонким клієнтом»: після рестарту за ≤5 хв стягує потрібне через HTTPS. |
| _vo_backup (opus, 3,3 МБ) і ops_dump.sql (300 КБ) зараз лежать у **публічному** репо shikarno-site. | Переносимо їх на сервер, з git прибираємо (див. «Міграція»). У публічному репо лишаються тільки сайт і код. |
| Рендер Remotion+Chromium+ffmpeg ділить ресурси з усім іншим у контейнері, а Whisper і node_modules щоразу ставляться заново. | Окремий воркер рендеру з уже встановленими залежностями. Docker-образ збирається один раз. |
| Cron і нічний бекап працюють лише тоді, коли жива сесія. | Планувальник 24/7: нічний бекап, знімок аналітики, перевірка стану. Рішення приймає Claude у сесіях, як і раніше (на сервері **немає** LLM-агента). |

## (б) Архітектура

```
 Claude Code (хмарний контейнер)                Сервер (Hetzner, ЄС)
 ─────────────────────────────                  ──────────────────────────────────────────────
 studio_sync.py / render.py  ── HTTPS 443 ──▶  Caddy (автоматичний TLS, Let's Encrypt)
 (Bearer-токен підставляє проксі,                  │
  токена немає ні в git, ні в чаті)                ▼
                                               api (FastAPI)  ── /data  (том: eps, vo, sqlite)
                                                  │  ▲
                                                  ▼  │ черга (sqlite)
                                               worker-render (Remotion + Chromium + ffmpeg + Whisper)
                                               scheduler (cron: бекап, знімки, healthcheck)
                                               bot (опційно, фаза 3: прийом вебхука Telegram)
                                                  │
                                                  ▼ щоночі
                                     Storage Box (BorgBackup/restic, порт 23) + Google Drive (як зараз)
```

Docker Compose (`studio/server/compose.yml`; код пишемо в репо, **секретів у ньому немає**):

| Сервіс | Що робить |
|---|---|
| `caddy` | Єдиний відкритий порт 443. TLS сам, через TLS-ALPN-01, тому порт 80 не потрібен. Проксіює на `api:8000`. |
| `api` | FastAPI. Кожен запит лише з `Authorization: Bearer <STUDIO_TOKEN>`, порівняння через `hmac.compare_digest`. Ендпоінти: `PUT /files/{path}` (вивантажити), `GET /files/{path}` (завантажити), `GET /files?prefix=` (список і md5), `POST /render` (`{slug, kind: short\|ep\|digest}` → `job_id`), `GET /jobs/{id}` (статус, лог, шлях до mp4), `POST /secrets/{name}` (лише запис, прочитати назад не можна), `GET /health`, `POST /admin/update` (git pull + `compose up -d --build`). Ліміт розміру файлу 2 ГБ, шляхи тільки всередині /data. |
| `worker-render` | Бере задачі з черги й запускає ті самі скрипти студії (`prep_ep.py`, Remotion). Образ: node + Chromium headless_shell + ffmpeg + python (numpy, soundfile, sherpa-onnx, whisper-small). |
| `scheduler` | supercronic: 03:30 Київ — бекап `/data` у Storage Box (borg, з шифруванням) і drive_sync; щодня — `lake.py snapshot`; щогодини — healthcheck (диск, черга). |
| `bot` (фаза 3) | За потреби переносимо прийом вебхука Telegram із воркера пульта. Сьогодні він працює 24/7 і так, тож поспіху немає. |
| сховище | Звичайний том `/data` на NVMe-диску сервера. MinIO не ставимо: на нашому обсязі (сотні МБ – кілька ГБ) це зайвий сервіс. S3 знадобиться — є Hetzner Object Storage. |

Клієнт у студії: `studio/server/studio_sync.py` (push/pull/status). Він повторює drive_sync.py, але працює з нашим API, тож refresh-токени Google для нього не потрібні.

## (в) Безпека

- **Назовні тільки 443.** Hetzner Cloud Firewall і UFW на сервері: вхідний 443/tcp для всіх; 22/tcp **лише з IP власника** (або взагалі закритий, а адмініструємо через веб-консоль Hetzner). З контейнера Claude Code SSH все одно не працює: вихідний 22 закритий, перевірено. Тому все керування йде через HTTPS-API.
- **Токен.** STUDIO_TOKEN (32 байти випадкові) генерує сам сервер при першому старті й записує в `/opt/studio/secrets/studio_token` (права 600). Власник один раз переносить його у безпечну форму credential (host = домен студії). Далі проксі середовища сам підставляє заголовок, і токен не потрапляє ні в git, ні в чат, ні в логи. Ротація: `POST /admin/rotate-token`, після неї власник оновлює форму.
- **Секрети студії** (бот, Gemini, YouTube, Drive) зберігаються лише на сервері в `/opt/studio/secrets/` через `POST /secrets/*`, тільки на запис. Контейнер отримує їх для своєї роботи, як і зараз, з «Доступів». У фазі 2 відео на YouTube вивантажує вже сервер, і локальні секрети в контейнері перестають бути потрібні.
- **Оновлення.** `unattended-upgrades` (безпекові патчі Ubuntu, автоперезавантаження о 04:30 за потреби). Образи Docker перезбираються раз на тиждень через scheduler. fail2ban на SSH.
- **Бекапи.** Щоночі borg у Storage Box (шифрування repokey, зберігаємо 7 денних і 4 тижневі копії) і копія в Google Drive, як зараз. Раз на місяць — пробне відновлення одного епізоду.
- **Логи** без тіл запитів і без заголовків Authorization.

## (г) Залізо й ціна (перевірено 26.11.2026 на hetzner.com, усі ціни в EUR **без ПДВ**)

ПДВ залежить від країни й статусу платника, кінцеву суму Hetzner показує в кошику. Білінг погодинний зі стелею на місяць: видалив сервер раніше — платиш лише години. Отже, тиждень проби на CPX32 коштує ≈ 0,0489 × 168 ≈ €8,2.

| Варіант | vCPU / RAM / диск | €/міс Гельсінкі (HEL1) | €/міс Німеччина (FSN1/NBG1) | Примітка |
|---|---|---|---|---|
| **CPX32** (Regular Performance, AMD, shared) — **рекомендую** | 4 / 8 ГБ / 160 ГБ NVMe | **€30,49** | €35,99 | Доступний для замовлення. €0,0489/год. IPv4 і 20 ТБ трафіку включені. |
| CX33 (Cost-Optimized, Intel/AMD) | 4 / 8 ГБ / 80 ГБ NVMe | €8,99 | — | На 26.11 «currently unavailable». Брати, якщо з'явиться. |
| CAX21 (Cost-Optimized, ARM Ampere) | 4 / 8 ГБ / 80 ГБ NVMe | €10,99 | — | Теж «unavailable». ARM — ризик для Chromium/Remotion, потрібен окремий тест. |
| CPX22 (менший запасний) | 2 / 4 ГБ / 80 ГБ NVMe | €16,99 | €19,99 | Дешевше, але 4 ГБ для Remotion+Chromium+Whisper впритул. |

Сховище для бекапу:

| Варіант | Обсяг | Ціна | Примітка |
|---|---|---|---|
| **Hetzner Storage Box BX11** — рекомендую | 1 ТБ | **€3,20/міс** без ПДВ | SFTP, rsync, BorgBackup, Restic, Rclone, WebDAV, HTTPS. 10 снапшотів. |
| Hetzner Object Storage | 1 ТБ і 1 ТБ egress включено | €6,49/міс база, без ПДВ | S3-сумісне, FSN1/HEL1/NBG1. |
| Cloudflare R2 (альтернатива) | 10 ГБ-міс безкоштовно | далі $0,015/ГБ-міс, egress безкоштовний | Підтверджено на developers.cloudflare.com/r2/pricing. Підійде як друга офсайт-копія бекапу без медіа. |

**Разом:** CPX32 HEL1 + BX11 = **€33,69/міс без ПДВ**. Якщо з'явиться CX33: €8,99 + €3,20 = €12,19/міс.
Джерела: hetzner.com/cloud/regular-performance, /cloud/cost-optimized, /storage/storage-box, /storage/object-storage (відкрито 26.11.2026).

## (д) Кроки власника (≈20 хв, коли й якщо вирішить)

1. **Реєстрація** на console.hetzner.com: акаунт, підтвердження особи, спосіб оплати.
2. **Сервер:** Create Server → Location **Helsinki** → Image **Ubuntu 24.04** → Type **Shared vCPU · Regular Performance · CPX32** → Networking IPv4 + IPv6 → Firewall: створити «studio» з правилом inbound TCP 443 (Any). SSH лише зі свого IP або не відкривати зовсім → **Cloud config**: вставити скрипт нижче → Name `studio` → Create.
3. **DNS:** у реєстратора shikarno.com.ua додати запис `A studio → <IPv4 сервера>`. Сайт на GitHub Pages це не зачіпає.
4. **Токен студії:** через 5–10 хв у консолі Hetzner відкрити сервер → Console (веб-термінал; пароль root дає «Reset root password») → `cat /opt/studio/secrets/studio_token`. Вставити рядок у безпечну форму, яку я покажу (credential для `studio.shikarno.com.ua`). У чат не надсилати.
5. *(опційно, можна пізніше)* **Storage Box BX11** у тій самій консолі. Його пароль власник вводить через ту саму веб-консоль сервера (`/opt/studio/bin/set-storagebox`), не в чат.
6. Написати в бот «сервер готовий». Далі все роблю я: деплой, перенесення, тест відновлення.

### Cloud-init (вставити в поле «Cloud config»; секретів немає, токен сервер генерує сам)

```yaml
#cloud-config
package_update: true
package_upgrade: true
packages: [docker.io, docker-compose-v2, git, ufw, fail2ban, unattended-upgrades, borgbackup, sqlite3, curl]
users:
  - name: studio
    groups: [docker]
    shell: /bin/bash
    lock_passwd: true
write_files:
  - path: /etc/apt/apt.conf.d/20auto-upgrades
    content: |
      APT::Periodic::Update-Package-Lists "1";
      APT::Periodic::Unattended-Upgrade "1";
  - path: /etc/apt/apt.conf.d/52studio-reboot
    content: |
      Unattended-Upgrade::Automatic-Reboot "true";
      Unattended-Upgrade::Automatic-Reboot-Time "04:30";
runcmd:
  - ufw default deny incoming
  - ufw default allow outgoing
  - ufw allow 443/tcp
  # SSH лише з IP власника: розкоментуй і впиши свій IP (інакше SSH закритий, вхід — веб-консоль Hetzner)
  # - ufw allow from 203.0.113.10 to any port 22 proto tcp
  - ufw --force enable
  - systemctl enable --now docker fail2ban
  - mkdir -p /opt/studio/secrets /opt/studio/data /opt/studio/bin
  - sh -c 'umask 077; [ -s /opt/studio/secrets/studio_token ] || head -c 32 /dev/urandom | base64 | tr -d "=+/\n" > /opt/studio/secrets/studio_token'
  - git clone --depth 1 https://github.com/manageitblog-pixel/shikarno-site /opt/studio/repo
  - chown -R studio:studio /opt/studio
  - sh -c 'cd /opt/studio/repo/studio/server && STUDIO_DOMAIN=studio.shikarno.com.ua docker compose up -d --build || echo "compose ще не готовий — Claude задеплоїть через API"'
final_message: "studio ready: token in /opt/studio/secrets/studio_token"
```
Репо публічне, токен для клону не потрібен. `studio/server/` (compose.yml, Caddyfile, api/, worker/, scheduler/) з'явиться в репо до кроку 2: це **фаза 0** моєї роботи. Без схвалення власника її не починаємо.

## (е) Міграція

**Фаза 0 (я, ~1 сесія, без витрат):** код `studio/server/` і `studio_sync.py`. Локальний тест API в контейнері (uvicorn + curl).
**Фаза 1 (після кроків власника):**

| Що | Звідки | Куди на сервері |
|---|---|---|
| Медіа епізодів (final/tg/tiktok mp4, обкладинки, srt) | /home/claude/eps/<slug>/ + Drive «Відео й озвучка» | /data/eps/<slug>/ |
| Озвучка opus | studio/eps/_vo_backup/ (публічний git) | /data/vo/<slug>/ → **прибрати з git** (`git rm -r --cached`, у .gitignore) |
| ops.sqlite + ops_dump.sql | studio/data/ (дамп у публічному git) | /data/db/ops.sqlite + нічний дамп → **дамп прибрати з git** |
| analytics.sqlite + snapshot | studio/data/ | /data/db/ |
| Копія Drive | Google Drive «ШІкарно студія» | лишається другою офсайт-копією, як і була |

Порядок: спершу залити все на сервер і звірити md5, потім один тиждень паралельно (git-резерв і сервер), і лише після цього прибирати з git. Історія git зберігає старі версії. Вони не секретні, але якщо власник захоче, історію можна почистити окремим кроком (`git filter-repo`) — це вже за окремим рішенням.

**Лишається в git:** сайт (content, templates, static, build.py), увесь код студії, RUNBOOK і docs, JSON стану конвеєра (uploaded.json, reserve.json тощо), drive_index.json.

**bootstrap.sh** отримає крок: якщо credential студії є, виконати `studio_sync.py restore --recent 7` (епізоди за 7 днів, vo, sqlite). Інакше — як зараз (git + Drive).

**Перевірка (критерій готовності):** перезапустити контейнер → `bash studio/bootstrap.sh` → за **≤5 хв** на місці ops.sqlite (`ops.py verify` → ok), analytics.sqlite, озвучка й mp4 останніх 7 днів, а `POST /render` для тестового Short повертає mp4. Час фіксуємо в dispatch-log.

**Фаза 2:** рендер і вивантаження на YouTube переходять на сервер; контейнер лише ставить задачі. **Фаза 3** (за потреби): вебхук бота й планувальник публікацій.

## (ж) Ризики і що НЕ змінюється

| Ризик | Що робимо |
|---|---|
| Сервер упав або акаунт заблоковано | Нічний borg у Storage Box і копія в Drive. Старий шлях (контейнер + git + Drive) лишається робочим запасним. |
| Дешеві типи (CX33/CAX21) зараз недоступні | Стартуємо на CPX32. Тип можна змінити пізніше через Rescale (диск зменшувати не можна, тому на менший тип переходимо з опцією «CPU and RAM only»). |
| Витік STUDIO_TOKEN | Лише HTTPS, токен тільки у формі credential і на сервері. Ротація одним запитом, логи без заголовків. |
| Проксі контейнера не пускає на новий домен | Додаємо host у мережу середовища (update_environment, власник схвалює). Credential, збережений через форму, теж дозволяє host. |
| Ще одна стаття витрат ~€34/міс | Погодинний білінг: можна взяти тиждень на пробу (≈€8) і видалити, якщо не дасть результату. |
| ПДВ | Ціни без ПДВ; підсумок — у кошику Hetzner. |

**НЕ змінюється:** сайт лишається на GitHub Pages (workflow pages.yml, cron 30 хв). Бот і пульт — на теперішньому воркері, доки не вирішимо інакше. Рішення приймає Claude в сесіях за RUNBOOK. «Доступи» лишаються джерелом секретів для контейнера. Нічний drive_sync працює далі.
