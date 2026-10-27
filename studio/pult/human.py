"""Переклад технічних дій на людську мову для пульта власника.
human(tool, tool_input) -> (текст для людини, напрямок). Технічні подробиці йдуть окремо (detail) і на пульті сховані під «деталі».
Правило: дієслово в першій особі («Озвучую…», «Публікую…»), без шляхів, команд і англійських назв інструментів."""
import os, re
from urllib.parse import urlparse

# (регулярка по команді/шляху, текст, напрямок) — перший збіг виграє
BASH = [
    (r"shikarno-pult\.|/api/snapshot", "Перевіряю, як виглядає пульт", "pult"),
    (r"docs/RUNBOOK|RUNBOOK\.md", "Оновлюю інструкцію автопілота", "other"),
    (r"node shot\.js|screenshot", "Роблю знімок екрана для перевірки", "pult"),
    (r"gen_full|gen_digest|gen_voice", "Озвучую ролик голосом Байта", "voice"),
    (r"audit_vo|align\.py|sherpa|whisper", "Перевіряю озвучку на помилки", "voice"),
    (r"loudnorm|acompressor", "Вирівнюю гучність звуку", "voice"),
    (r"remotion still|ShortThumb|DigestThumb", "Малюю обкладинку", "render"),
    (r"prep_ep|prep_digest", "Розкладаю сцени ролика по часу", "render"),
    (r"build\.sh|build_digest|remotion render|render_chunks", "Рендерю відео", "render"),
    (r"select=|tile=|ffprobe", "Перевіряю кадри відео", "render"),
    (r"crf 2[0-9].*tiktok|tiktok\.mp4", "Готую відео для TikTok", "tiktok"),
    (r"yt\.upload|upload\(", "Завантажую ролик на YouTube", "youtube"),
    (r"thumb\.py", "Ставлю обкладинку на YouTube", "youtube"),
    (r"yt\.comment", "Пишу коментар під роликом", "youtube"),
    (r"yt\.schedule", "Ставлю ролик у розклад YouTube", "youtube"),
    (r"yt\.recent|yt\.api|analytics", "Дивлюся статистику YouTube", "youtube"),
    (r"tg\.video|sendVideo.*shikarno|tg\.post", "Публікую в Telegram-каналі", "telegram"),
    (r"sendVideo|sendMessage|chat_id=133254760", "Пишу тобі в бот", "telegram"),
    (r"inbox\.py", "Перевіряю твої повідомлення в боті", "telegram"),
    (r"setWebhook|getWebhookInfo|setMyCommands", "Налаштовую бота", "telegram"),
    (r"pult\.py|pultlib", "Оновлюю пульт", "pult"),
    (r"wrangler", "Оновлюю пульт і бота на сервері", "pult"),
    (r"build\.py", "Збираю сайт", "site"),
    (r"git push", "Публікую зміни на сайті", "site"),
    (r"git commit|git add", "Зберігаю зроблене", "site"),
    (r"git (fetch|pull|status|log|diff|show)", "Звіряю останні зміни", "site"),
    (r"sec\.gov|curl .*https?://", "Читаю першоджерело", "research"),
    (r"meta\.py|uploaded\.json|experiments\.json|publishing-schedule|reserve\.json", "Оновлюю записи про ролики", "youtube"),
    (r"tiktok\.json", "Оновлюю список роликів TikTok", "tiktok"),
    (r"bootstrap|pip install|npm (ci|install)", "Готую робоче місце", "other"),
    (r"until .*sleep|pgrep|while .*sleep", "Чекаю, поки завершиться процес", "other"),
]

FILES = [  # (шлях містить, дія для Write/Edit, дія для Read, напрямок)
    ("content/posts/", "Пишу статтю для сайту", "Перечитую статтю сайту", "site"),
    ("content/pages/", "Редагую сторінку сайту", "Перечитую сторінку сайту", "site"),
    ("templates/", "Правлю дизайн сайту", "Дивлюся шаблон сайту", "site"),
    ("docs/RUNBOOK", "Оновлюю інструкцію автопілота", "Перечитую інструкцію автопілота", "other"),
    ("docs/", "Оновлюю документи проєкту", "Перечитую документи проєкту", "site"),
    ("eps/ep", "Пишу сценарій ролика", "Перечитую сценарій ролика", "youtube"),
    ("eps/digest", "Пишу сценарій дайджесту", "Перечитую сценарій дайджесту", "youtube"),
    ("eps/r", "Пишу сценарій запасного ролика", "Перечитую сценарій ролика", "youtube"),
    ("eps/month", "Готую «ШІ за місяць»", "Перечитую матеріали «ШІ за місяць»", "youtube"),
    ("eps/meta", "Пишу назву й опис ролика", "Перечитую описи роликів", "youtube"),
    ("studio/rv/", "Правлю шаблон відео", "Дивлюся шаблон відео", "render"),
    ("tg/", "Налаштовую Telegram", "Дивлюся налаштування Telegram", "telegram"),
    ("pult/", "Покращую пульт", "Дивлюся код пульта", "pult"),
    ("scratchpad", "Роблю робочі нотатки", "Переглядаю робочі нотатки", "other"),
]

def _site(url):
    try: return urlparse(url).netloc.replace("www.", "")
    except Exception: return ""

def human(tool, ti):
    ti = ti or {}
    if tool == "Bash":
        cmd = ti.get("command", "")
        for rx, text, area in BASH:
            if re.search(rx, cmd, re.I):
                return text, area
        d = (ti.get("description") or "").strip()
        return (d[:1].upper() + d[1:] if d else "Технічна робота"), None
    if tool in ("Write", "Edit", "Read", "NotebookEdit"):
        p = ti.get("file_path", "")
        for key, w, r, area in FILES:
            if key in p:
                return (r if tool == "Read" else w), area
        return ("Переглядаю файл" if tool == "Read" else "Редагую файл") + " «" + os.path.basename(p) + "»", None
    if tool == "WebSearch":
        return "Шукаю в інтернеті: " + ti.get("query", ""), "research"
    if tool == "WebFetch":
        return "Читаю джерело: " + _site(ti.get("url", "")), "research"
    if tool in ("Grep", "Glob"):
        return "Шукаю потрібне в матеріалах", None
    if tool == "Agent":
        return "Доручаю частину роботи помічнику: " + (ti.get("description") or ""), "other"
    if tool == "Skill":
        return "Відкриваю інструкцію «" + str(ti.get("skill", "")) + "»", "other"
    t = tool.split("__")[-1]
    MAP = {
        "ArtifactData": ("Оновлюю задачі на пульті", "pult"),
        "Artifact": ("Оновлюю сторінку-документ", "pult"),
        "send_later": ("Ставлю собі нагадування", "pult"),
        "create_trigger": ("Налаштовую розклад запусків", "pult"),
        "update_trigger": ("Змінюю розклад запусків", "pult"),
        "list_triggers": ("Дивлюся розклад запусків", "pult"),
        "keyword_suggestions": ("Дивлюся, що люди шукають у Google", "research"),
        "actions_list": ("Перевіряю, чи опублікувався сайт", "site"),
        "ToolSearch": ("Підключаю потрібний інструмент", "other"),
        "TaskCreate": ("Записую план роботи", "other"), "TaskUpdate": ("Відмічаю прогрес у плані", "other"),
    }
    if t in MAP:
        return MAP[t]
    if "Ubersuggest" in tool:
        return "Аналізую пошукові запити", "research"
    if "github" in tool:
        return "Перевіряю репозиторій сайту", "site"
    return "Працюю з інструментом «" + t + "»", None
