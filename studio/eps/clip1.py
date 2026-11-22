# Кліп-воронка №1 (активність 78, 22.11) — з «ШІ для професій #1» (6-2a9ncHaz4), вчитель: 0:31.8–1:05.1 → Short 1080×1920.
# RELATED: 6-2a9ncHaz4 — ШІ для вчителя, студента, ФОП і SMM: ChatGPT, Gemini, Claude | ШІ для професій #1 (1.11). Картка «Повний розбір ↓» веде на нього (Related video ставить власник у Studio).
# Чому цей шматок: утримання YouTube Analytics (органіка, 1.10–22.11) — relativeRetentionPerformance 0.59→0.83 на 0:44–1:12,
#   найвища ділянка першої половини ролика (решта 0.2–0.5); самодостатній блок «Вчитель: Gemini у Classroom», перша фраза — теза.
# БЕЗ нової озвучки (TTS-квота — на guide1 та ep83–86): голос з prof1/vo.wav, межі речень з prof1/align.json (сегмент #3).
# Останнє речення сегмента («За довідкою Google… в усіх редакціях Workspace for Education») не взято — воно в описі.
# Факти — з фактчеку prof1 (docs/research/professions-ai-2026-10-31.md): Gemini у Classroom — план уроку, тест (експорт у Forms),
#   критерії; NotebookLM перейменовано на Gemini Notebook (16.07.2026), Audio Overview.
# Запуск: python3 eps/clip1.py && bash eps/build.sh clip1 && python3 eps/clip_cut.py loud clip1
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SLUG = "clip1"; SRC = "prof1"
SERIES = "ШІ ДЛЯ ПРОФЕСІЙ"
KEYS = ["план уроку", "тест", "подкаст"]
CUTS = [(31.82, 65.09, [31.82, 36.35, 43.86, 49.8, 54.1, 59.53], [
    "Найкорисніший ШІ для вчителя вже живе в Google Classroom.",
    "Відкрий інструменти Gemini і натисни «план уроку»: вкажи клас, тему і тривалість — і отримаєш структуру заняття.",
    "Поруч кнопка «тест»: питання за темою, які можна перенести в Google Forms і відредагувати.",
    "Третя — «критерії оцінювання»: таблиця рівнів для практичної чи есе.",
    "А тему пояснить Gemini Notebook — так тепер називається NotebookLM.",
    "Завантаж розділ підручника, попроси аудіоогляд, і учні слухають тему як подкаст."])]
SCENES = [
 dict(kind="hookIcon", label="", title="", icon="form", tone="news", badge="ВЧИТЕЛЮ", hook="ШІ вже *у твоєму Classroom*"),
 dict(kind="list", label="GEMINI У CLASSROOM", title="Урок за 5 хвилин",
      items=[["form", "План уроку — 1 кнопка"], ["check", "Тест → Google Forms"], ["chart", "Критерії оцінювання"], ["video", "Тема як подкаст"]]),
 dict(kind="hookIcon", label="ПОВНИЙ РОЗБІР ↓", title="ШІ для професій #1", icon="video", tone="news", badge="+ студент, ФОП, SMM"),
 dict(kind="outro", label="", title=""),
]
META = dict(
 title="ШІ для вчителя: план уроку і тест за 5 хвилин у Google Classroom 🍎 #ШІ #shorts",
 first_comment="Вчителі, що вже віддали ШІ — плани, тести чи перевірку? 👇 Повний розбір: https://youtu.be/6-2a9ncHaz4",
 description=("ШІ для вчителя вже вбудований у Google Classroom: інструменти Gemini складають план уроку за класом, темою й тривалістю, "
  "роблять тест, який можна перенести в Google Forms, і критерії оцінювання. А Gemini Notebook (колишній NotebookLM) робить з розділу "
  "підручника аудіоогляд — учні слухають тему як подкаст. За довідкою Google, Gemini в Classroom доступний в усіх редакціях Workspace for Education. "
  "План і тест перед уроком перечитай — ШІ теж помиляється.\n\n"
  "▶ Повний розбір «ШІ для професій #1» — вчитель, студент, ФОП і SMM: https://youtu.be/6-2a9ncHaz4\n\n"
  "Джерела:\n• Google, Gemini у Classroom: https://support.google.com/edu/classroom/answer/15410566\n"
  "• Google, NotebookLM → Gemini Notebook: https://blog.google/innovation-and-ai/products/gemini-notebook/notebooklm-gemini-notebook/\n"
  "• Google, Audio Overviews: https://support.google.com/notebooklm/answer/16206563\n\n"
  "Фрагмент повного розбору, озвучка — та сама. Ведучий Байт — віртуальний персонаж, озвучка створена за допомогою ШІ."),
 tags=["ШІ для вчителя", "Google Classroom", "Gemini в Classroom", "план уроку", "тест Google Forms", "Gemini Notebook", "NotebookLM",
       "ШІ для професій", "Gemini", "AI for teachers", "ШІ", "штучний інтелект", "ШІкарно"],
 playlists=["prof"],
)
if __name__ == "__main__":
    import clip_cut; clip_cut.build(SLUG, SRC, CUTS, SCENES, SERIES, KEYS)
