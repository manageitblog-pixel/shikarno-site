# Шпаргалка «Який ШІ для чого — 40 задач на 1 сторінці» (рішення власника 31.10: замість «50 промптів»). Суб'єктивний рейтинг Байта.
# python3 studio/pdf/tier40.py → studio/pdf/shikarno-yakyi-shi-dlya-chogo.pdf
import base64, html, os
R = os.path.dirname(os.path.abspath(__file__)) + "/../.."
font = base64.b64encode(open(f"{R}/tools/fonts/Montserrat.ttf", "rb").read()).decode()
bait = base64.b64encode(open(f"{R}/static/bait.png", "rb").read()).decode()
e = html.escape
S = [
 ("💼 Робота", [
  ("Резюме", "Word", "Canva", "ChatGPT"), ("Лист клієнту", "Вручну", "Шаблон", "Claude"), ("Переклад", "Google", "DeepL", "Claude"),
  ("Таблиці", "Формули", "Copilot", "Gemini"), ("Нотатки зустрічі", "Блокнот", "Notion", "NotebookLM"), ("Презентація", "PowerPoint", "Canva", "Gamma"),
  ("Логотип", "Руками", "Canva", "ChatGPT"), ("Пошук інформації", "Google", "ChatGPT", "Perplexity"), ("Код", "Copilot", "Cursor", "Claude"),
  ("Пост у соцмережі", "Вручну", "Canva", "ChatGPT")]),
 ("🏠 Дім", [
  ("Рецепт з того, що є", "Google", "ChatGPT", "Gemini"), ("Ремонт за фото", "Майстер", "YouTube", "ChatGPT"), ("Бюджет", "Зошит", "Excel", "Claude"),
  ("Подорож", "Турагент", "Booking", "Gemini"), ("Рослини", "Сусідка", "Google Lens", "Gemini"), ("Скарга чи заява", "Вручну", "Шаблон", "Claude"),
  ("Порівняти тарифи", "Вручну", "Google", "ChatGPT"), ("Подарунок", "Вгадати", "Маркетплейс", "ChatGPT"), ("План на тиждень", "Папір", "Календар", "Gemini"),
  ("Питання про здоров'я", "Форум", "ШІ — підготувати питання", "Лікар")]),
 ("🎓 Навчання", [
  ("Пояснити тему", "Підручник", "YouTube", "NotebookLM"), ("Перевірити домашку", "Списати", "Google", "ChatGPT"), ("Англійська", "Словник", "Duolingo", "ChatGPT голосом"),
  ("Конспект відео", "Дивитись усе", "Субтитри", "NotebookLM"), ("Підготовка до іспиту", "Зубрити", "Картки", "NotebookLM"), ("Есе", "Списати", "Google", "Claude + ти"),
  ("Математика", "Калькулятор", "Photomath", "Gemini"), ("Наукові джерела", "Вікіпедія", "Google Scholar", "Perplexity"), ("План реферату", "Вручну", "Шаблон", "ChatGPT"),
  ("Самоперевірка", "Без тестів", "Quizlet", "NotebookLM")]),
 ("🎬 Фото, відео, звук", [
  ("Редагувати фото", "Руками", "Canva", "Gemini"), ("Прибрати фон", "Paint", "remove.bg", "Canva"), ("Відео з тексту", "Вручну", "CapCut", "Veo"),
  ("Субтитри", "Вручну", "YouTube", "CapCut"), ("Озвучка", "Диктофон", "CapCut", "ElevenLabs"), ("Чистий звук", "Audacity", "CapCut", "Adobe Podcast"),
  ("Фото профілю", "Селфі", "Фільтр", "ChatGPT"), ("Обкладинка", "Руками", "Canva", "ChatGPT"), ("Мем", "Вручну", "Шаблон", "ChatGPT"),
  ("Чи фото справжнє?", "Повірити", "Google Lens", "Шукати джерело")]),
]
n = sum(len(r) for _, r in S); assert n == 40, n
def table(name, rows):
    tr = "".join(f"<tr><td class=t>{e(a)}</td><td class=b>{e(b)}</td><td class=g>{e(c)}</td><td class=x>{e(d)}</td></tr>" for a, b, c, d in rows)
    return f"<section><h2>{e(name)}</h2><table><tr><th></th><th class=hb>ПОГАНО</th><th class=hg>ДОБРЕ</th><th class=hx>НАЙКРАЩЕ</th></tr>{tr}</table></section>"
H = f'''<!doctype html><html lang="uk"><head><meta charset="utf-8"><style>
@font-face{{font-family:M;src:url(data:font/ttf;base64,{font})}}
@page{{size:A4 landscape;margin:0}}
*{{box-sizing:border-box}} body{{font-family:M,sans-serif;margin:0;width:297mm;height:210mm;background:linear-gradient(160deg,#0B0A1C,#1A1240);color:#fff;padding:8mm 10mm 6mm;overflow:hidden}}
header{{display:flex;align-items:center;gap:5mm;margin-bottom:3mm}} .logo{{font-size:15pt;font-weight:900}} .logo span{{background:#FFD60A;color:#0B0A1C;padding:0 1.5mm;border-radius:1.2mm}}
h1{{font-size:21pt;font-weight:900;margin:0;line-height:1}} h1 b{{color:#FFD60A}} .sub{{font-size:8.5pt;color:#c9c2ff;margin-top:1mm}}
header img{{height:17mm;margin-left:auto}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:3mm 7mm}}
h2{{font-size:11pt;margin:0 0 1mm;color:#4CF2FF}}
table{{width:100%;border-collapse:separate;border-spacing:1mm .7mm;font-size:7.6pt;font-weight:700}}
th{{font-size:6.8pt;font-weight:900;color:#0B0A1C;border-radius:1mm;padding:.7mm 0}} .hb{{background:#FF3B5C}} .hg{{background:#FFD60A}} .hx{{background:#2EE59D}}
td{{padding:.9mm 1.5mm;border-radius:1.2mm;background:rgba(255,255,255,.07);text-align:center;width:23%}} td.t{{text-align:left;background:none;width:31%;color:#fff}}
td.b{{color:#ffb3c0}} td.g{{color:#ffe98a}} td.x{{color:#9dffd6;background:rgba(46,229,157,.14);border:1px solid rgba(46,229,157,.5)}}
footer{{margin-top:2.5mm;font-size:6.9pt;color:#bdb6ff;line-height:1.4}} footer b{{color:#fff}} footer a{{color:#4CF2FF;text-decoration:none}}
</style></head><body>
<header><div><div class=logo><span>ШІ</span>карно</div></div><div><h1>Який ШІ для чого: <b>40 задач</b></h1>
<div class=sub>Тір-лист робота Байта: що погано, що добре і що найкраще. Суб'єктивний рейтинг, не реклама.</div></div>
<img src="data:image/png;base64,{bait}"></header>
<div class=grid>{"".join(table(*s) for s in S)}</div>
<footer><b>Безкоштовно:</b> ChatGPT, Gemini, Claude, NotebookLM, Perplexity, Canva, CapCut, DeepL та більшість інших мають безкоштовну версію з денними лімітами. <b>Платно:</b> Copilot у Excel, Veo (підписка Google). Ціни й ліміти змінюються — перевіряй на сайті сервісу.
<b>Безпека:</b> не вставляй у ШІ паролі, номери карток і фото документів; факти й цифри перевіряй. · Нові тір-листи щодня: <a href="https://t.me/shikarno_ai_ua">t.me/shikarno_ai_ua</a> · YouTube @shikarno_ua · TikTok @shikarno_ai_ua · версія 1, листопад 2026</footer>
</body></html>'''
D = os.path.dirname(os.path.abspath(__file__))
open(f"{D}/tier40.html", "w").write(H)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1123, "height": 794}); pg.set_content(H); pg.wait_for_timeout(500)
    pg.pdf(path=f"{D}/shikarno-yakyi-shi-dlya-chogo.pdf", width="297mm", height="210mm", print_background=True, page_ranges="1")
    pg.screenshot(path=f"{D}/tier40.png", full_page=False); b.close()
print("ok", n)
