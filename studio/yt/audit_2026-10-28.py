"""Аудит метаданих публічних роликів за даними vidIQ (28.10.2026): назва з ключем на початку, теги uk+en (без ru),
3 хештеги в описі, посилання на сайт/Telegram. Ролики НЕ перезаливаються — лише videos.update (snippet).
  python3 audit_2026-10-28.py BACKUP.json [--apply]
Без --apply — лише показує зміни."""
import json, re, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import yt

# id: (нова назва або None = лишити, додаткові теги, хештеги)
M = {
 "RmghL3emAos": (None, ["I'm so sorry trend", "AI photo trend", "AI trend", "ШІ тренд фото"], "#ШІ #тренд #ШІфото"),
 "gw9vvyTzYmA": ("Gemini безкоштовно для студентів на рік — і в Україні 🎓",
                 ["gemini pro free", "gemini free for students", "gemini student offer", "google ai plus free"], "#Gemini #безкоштовно #студенти"),
 "QBz_MC7cgZM": ("ШІ зробив титри як у кіно 🎬 Claude + Remotion одним промптом",
                 ["claude ai", "remotion", "ai animation", "ai motion design"], "#ШІ #Claude #моушндизайн"),
 "vph0ySJabV8": ("Anthropic: ШІ від творців Claude зламав чужий сервер 😨 Зізнання в IPO",
                 ["claude ai", "anthropic ipo", "ai safety"], "#Anthropic #Claude #безпекаШІ"),
 "bG1ZEHzuYR0": ("ChatGPT ховає чати під PIN-код 🔒 Як це працює і від кого захищає",
                 ["chatgpt", "chatgpt locked chats", "chatgpt privacy"], "#ChatGPT #приватність #ШІ"),
 "W60m6jGRSp8": ("ChatGPT склав меню на тиждень — а там лосось щодня 😅",
                 ["chatgpt meal plan", "chatgpt prompts", "промпти chatgpt"], "#ChatGPT #промпти #ШІ"),
 "h2oWgm-WnhA": (None, ["gemini carplay", "gemini google maps", "gemini in car"], "#Gemini #CarPlay #ШІ"),
 "IiXA_z7ObFc": ("Новини ШІ за тиждень #1: ШІ-агенти зламали 100+ компаній, ChatGPT у браузері, Gemini в авто",
                 ["новини ші", "ai news", "ші агенти", "ai agents"], "#новиниШІ #ШІ #ChatGPT"),
 "Gp5ZTU6pynY": ("ШІ-агенти купують замість тебе: Walmart пускає, Amazon блокує 🛒",
                 ["ai agents", "ші агенти", "ai shopping"], "#ШІагенти #Walmart #Amazon"),
 "0vQVLBHUM9U": ("PHP2Shell: дірка в PHP на 9.2/10 і роль ШІ ⚡ Повний розбір",
                 ["php vulnerability", "кібербезпека", "cybersecurity"], "#PHP #кібербезпека #ШІ"),
 "EwbIWlSKnWg": ("Claude Duet: ШІ, який пише тобі першим — що вміє",
                 ["claude ai", "claude duet", "anthropic claude"], "#Claude #ШІагент #Anthropic"),
 "ULBtAJDADhk": ("ШІ-агенти зламали 100+ компаній: ~$50 за злам 😨",
                 ["ai hacking", "ші агенти", "cybersecurity"], "#ШІагенти #кібербезпека #ШІ"),
 "J3fkrWp64UE": ("Google зробив ШІ для зустрічей без інтернету 💻 Gemma 4 на Mac",
                 ["gemma 4", "google ai", "offline ai"], "#Google #Gemma #ШІ"),
 "VJnUKMatmJ8": (None, ["php vulnerability", "cybersecurity"], "#PHP #кібербезпека #ШІ"),
 "cSrZ33nAKn4": ("Gemini: Gems зникнуть у листопаді. Що таке скіли і навіщо вони тобі",
                 ["gemini gems", "gemini skills", "google gemini"], "#Gemini #Gems #ШІ"),
 "ctzCraL03OE": ("OpenAI: ШІ вимкнув нагляд за собою — і збрехав 😨 Що в звіті",
                 ["openai", "ai safety", "gpt-6"], "#OpenAI #безпекаШІ #ШІ"),
 "uEA0vrgrkf0": ("FLUX 3 Max: 10 секунд відео за 12 секунд 🤯 Нова нейромережа",
                 ["flux 3", "генерація відео ші", "ai video generator"], "#FLUX #ШІвідео #нейромережі"),
 "sSsYLWoaM4I": (None, ["php vulnerability", "cybersecurity"], "#PHP #кібербезпека #ШІ"),
 "TeQP_kM98Ng": ("Gemini в Android Auto: їде з тобою і знає твою пошту 🚗",
                 ["gemini android auto", "gemini in car", "google gemini"], "#Gemini #AndroidAuto #ШІ"),
 "mP4aIt0qbik": (None, ["chatgpt new features", "chatgpt"], "#ChatGPT #OpenAI #ШІ"),
 "biSJLBhwIRE": ("ChatGPT у Chrome: сам клацає у твоєму браузері 😳",
                 ["chatgpt chrome extension", "chatgpt agent", "chatgpt"], "#ChatGPT #Chrome #ШІ"),
 "theMaZ3jGR4": (None, ["chatgpt virtual try on", "chatgpt"], "#ChatGPT #примірка #ШІ"),
}
GENERIC = {"ШІ для роботи"}  # загальні теги без пошукового попиту — прибираємо
CYR_RU = re.compile(r"[ыэъё]", re.I)


def new_snippet(v):
    s = v["snippet"]; title, extra, hashtags = M[v["id"]]
    tags = [t for t in s.get("tags", []) if t not in GENERIC and not CYR_RU.search(t)]
    for t in extra:
        if t.lower() not in {x.lower() for x in tags}: tags.append(t)
    while len(",".join(tags)) > 450: tags.pop()
    lines = [l for l in s.get("description", "").rstrip().split("\n") if not l.strip().startswith("#")]
    desc = "\n".join(lines).rstrip()
    desc = re.sub(r"\n{3,}", "\n\n", desc)
    if "shikarno.com.ua" not in desc: desc += "\n🌐 Сайт: https://shikarno.com.ua"
    if "t.me/shikarno_ai_ua" not in desc: desc += "\n💬 Telegram: https://t.me/shikarno_ai_ua"
    short = not re.search(r"(\d+)M", v["contentDetails"]["duration"]) or int(re.search(r"(\d+)M", v["contentDetails"]["duration"])[1]) < 3
    desc += "\n\n" + hashtags + (" #shorts" if short else "")
    return dict(title=(title or s["title"])[:100], description=desc, tags=tags,
                categoryId=s["categoryId"], defaultLanguage=s.get("defaultLanguage", "uk"),
                defaultAudioLanguage=s.get("defaultAudioLanguage", "uk"))


if __name__ == "__main__":
    vids = {v["id"]: v for v in json.load(open(sys.argv[1]))}
    apply = "--apply" in sys.argv
    for vid in M:
        v = vids[vid]; n = new_snippet(v)
        print(f"{vid}: {v['snippet']['title']}\n   → {n['title']}\n   теги: {n['tags']}\n   хвіст: {n['description'][-90:]!r}")
        if apply:
            yt._put("videos", {"id": vid, "snippet": n}, "snippet")
            print("   ✔ оновлено")
