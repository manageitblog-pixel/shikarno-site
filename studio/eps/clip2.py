# Кліп-воронка №2 (активність 78, 22.11) — з «ШІ для професій #1» (6-2a9ncHaz4), SMM: 4:09.4–4:30.0 + 4:36.4–4:44.4 → Short 1080×1920.
# RELATED: 6-2a9ncHaz4 — ШІ для вчителя, студента, ФОП і SMM: ChatGPT, Gemini, Claude | ШІ для професій #1 (1.11). Картка «Повний розбір ↓» веде на нього (Related video ставить власник у Studio).
# Чому цей шматок: утримання YouTube Analytics (органіка, 1.10–22.11) — relativeRetentionPerformance 0.57→0.90 на 3:58–4:40,
#   пік усього ролика на ~4:40 (блок SMM); самодостатній блок «SMM: Projects, Skills, Nano Banana», перша фраза — біль глядача.
# БЕЗ нової озвучки: голос з prof1/vo.wav, межі речень з prof1/align.json (сегмент #15).
# Вирізано речення «…старі Gems автоматично стануть скілами» (на 1.11 було майбутнє, у листопаді вже минуле — щоб не застаріло).
# Факти — з фактчеку prof1 (docs/research/professions-ai-2026-10-31.md): ChatGPT Projects; Gemini Skills (без підписки, 18+);
#   Nano Banana в Gemini з денною квотою; Claude Skills.
# Запуск: python3 eps/clip2.py && bash eps/build.sh clip2 && python3 eps/clip_cut.py loud clip2
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SLUG = "clip2"; SRC = "prof1"
SERIES = "ШІ ДЛЯ ПРОФЕСІЙ"
KEYS = ["Проєкт", "Skill", "Nano Banana"]
CUTS = [(249.44, 270.01, [249.44, 254.17, 263.15], [
    "SMM-нику найбільше часу з'їдає пояснення бренду щоразу заново.",
    "Тому перший крок — «Проєкт» у ChatGPT під кожного клієнта: бриф, гайд і найкращі пости лежать там, і контент-план виходить у стилі бренду.",
    "Голос бренду збережи як Skill у Gemini: опиши тон, заборонені слова, дай приклади — і Gemini застосовує це сам."]),
        (276.40, 284.38, [276.40, 279.47], [
    "Картинки — Nano Banana в Gemini, з денною квотою.",
    "А повторювані формати — анонс, розіграш, кейс — оформи як власні Skills у Claude."])]
SCENES = [
 dict(kind="hookIcon", label="", title="", icon="image", tone="news", badge="SMM", hook="Пояснюєш бренд *щоразу з нуля?*"),
 dict(kind="list", label="SMM · МІСЯЦЬ КОНТЕНТУ", title="Бренд запам'ятає ШІ",
      items=[["chat", "ChatGPT: Проєкт під клієнта"], ["text", "Gemini: Skill голосу бренду"], ["image", "Nano Banana: картинки"], ["check", "Claude: шаблони постів"]]),
 dict(kind="hookIcon", label="ПОВНИЙ РОЗБІР ↓", title="ШІ для професій #1", icon="video", tone="news", badge="+ готові промпти"),
 dict(kind="outro", label="", title=""),
]
META = dict(
 title="ШІ для SMM: контент-план і голос бренду без пояснень щоразу 📱 ChatGPT, Gemini, Claude #shorts",
 first_comment="SMM-ники, який ШІ у вас пише найближче до голосу бренду? 👇 Повний розбір: https://youtu.be/6-2a9ncHaz4",
 description=("ШІ для SMM: як не пояснювати бренд щоразу заново. «Проєкт» у ChatGPT під кожного клієнта — бриф, гайд і найкращі пости лежать там, "
  "і контент-план виходить у стилі бренду. Голос бренду — Skill у Gemini: тон, заборонені слова, приклади (за довідкою Google, скіли працюють "
  "без підписки, з 18 років). Картинки — Nano Banana в Gemini з денною квотою. Повторювані формати — анонс, розіграш, кейс — власні Skills у Claude.\n\n"
  "▶ Повний розбір «ШІ для професій #1» з готовими промптами для SMM, вчителя, студента і ФОП: https://youtu.be/6-2a9ncHaz4\n\n"
  "Джерела:\n• OpenAI, Projects у ChatGPT: https://help.openai.com/en/articles/10169521-projects-in-chatgpt\n"
  "• Google, Skills у Gemini: https://support.google.com/gemini/answer/17094296\n"
  "• Google, створення зображень у Gemini: https://support.google.com/gemini/answer/14286560\n"
  "• Anthropic, Skills у Claude: https://support.claude.com/en/articles/12512180-use-skills-in-claude\n\n"
  "Фрагмент повного розбору, озвучка — та сама. Ведучий Байт — віртуальний персонаж, озвучка створена за допомогою ШІ."),
 tags=["ШІ для SMM", "контент-план", "голос бренду", "SMM", "ChatGPT Projects", "Gemini Skills", "Nano Banana", "Claude Skills",
       "ШІ для професій", "AI for SMM", "ШІ", "штучний інтелект", "ШІкарно"],
 playlists=["prof"],
)
if __name__ == "__main__":
    import clip_cut; clip_cut.build(SLUG, SRC, CUTS, SCENES, SERIES, KEYS)
