import prompts, base64, html
font=base64.b64encode(open('/home/claude/gh/shikarno-site/tools/fonts/Montserrat.ttf','rb').read()).decode()
logo=base64.b64encode(open('/home/claude/gh/shikarno-site/static/logo.png','rb').read()).decode()
bait=base64.b64encode(open('/home/claude/gh/shikarno-site/static/bait.png','rb').read()).decode()
e=html.escape
def hl(t): # [..] → підсвітка
    import re; return re.sub(r'\[([^\]]+)\]', r'<span class="ph">[\1]</span>', e(t))
n=0; sec=''
for name,items in prompts.P:
    cards=''
    for t,p in items:
        n+=1; cards+=f'<div class="card"><div class="num">{n}</div><div><h3>{e(t)}</h3><p>{hl(p)}</p></div></div>'
    sec+=f'<section><h2>{e(name)}</h2>{cards}</section>'
H=f'''<!doctype html><html lang="uk"><head><meta charset="utf-8"><style>
@font-face{{font-family:M;src:url(data:font/ttf;base64,{font})}}
@page{{size:A4;margin:16mm 14mm 16mm 14mm}}
body{{font-family:M,sans-serif;color:#17142b;font-size:10.5pt;line-height:1.45;margin:0}}
.cover{{height:265mm;background:linear-gradient(160deg,#0B0A1C,#1A1240);color:#fff;border-radius:6mm;padding:22mm 16mm;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;page-break-after:always}}
.cover img.logo{{height:16mm}} .cover h1{{font-size:38pt;line-height:1.05;margin:0;font-weight:900}} .cover h1 b{{color:#FFD60A}}
.cover p{{font-size:13pt;color:#d9d4ff;max-width:140mm}} .cover .bait{{height:60mm;align-self:flex-end}}
.formula{{background:#f4f1ff;border-left:4px solid #7C5CFF;padding:4mm 5mm;border-radius:2mm;margin:0 0 6mm}}
h2{{font-size:15pt;font-weight:800;margin:7mm 0 3mm;color:#7C5CFF;page-break-after:avoid}}
.card{{display:flex;gap:4mm;border:1px solid #e3def7;border-radius:3mm;padding:3mm 4mm;margin:0 0 2.6mm;page-break-inside:avoid}}
.num{{flex:0 0 9mm;height:9mm;border-radius:50%;background:#FFD60A;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:10pt}}
h3{{margin:0 0 1mm;font-size:11pt;font-weight:700}} p{{margin:0}} .ph{{background:#fff3b0;border-radius:1mm;padding:0 .6mm}}
.end{{margin-top:8mm;background:#0B0A1C;color:#fff;border-radius:4mm;padding:6mm;page-break-inside:avoid}} .end a{{color:#4CF2FF}}
</style></head><body>
<div class="cover"><div style="font-size:20pt;font-weight:900"><span style="background:#FFD60A;color:#0B0A1C;padding:0 2mm;border-radius:1.5mm">ШІ</span>карно</div><div><h1><b>50</b> промптів<br>українською</h1>
<p>Готові шаблони для ChatGPT, Gemini і Claude: робота, бізнес, навчання і щоденне життя. Копіюй, заміни текст у [дужках] — і готово.</p></div>
<img class="bait" src="data:image/png;base64,{bait}"><p style="font-size:10pt;color:#bdb6ff">ШІкарно · shikarno.com.ua · t.me/shikarno_ai_ua · версія 1, жовтень 2026</p></div>
<div class="formula"><b>Формула промпту:</b> роль + задача + контекст + формат + обмеження.<br>
Найкращий результат — у діалозі: попроси чернетку, потім уточнюй («коротше», «менш офіційно», «додай цифри»). Не вставляй у чат паролі, дані клієнтів і комерційну таємницю, а факти й цифри завжди перевіряй.</div>
{sec}
<div class="end"><b>Більше промптів і новин ШІ українською</b><br>Telegram: <a href="https://t.me/shikarno_ai_ua">t.me/shikarno_ai_ua</a> · Сайт: <a href="https://shikarno.com.ua">shikarno.com.ua</a> · YouTube: <a href="https://youtube.com/@shikarno_ua">@shikarno_ua</a></div>
</body></html>'''
open('p50.html','w').write(H)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.set_content(H); pg.wait_for_timeout(500)
    pg.pdf(path='shikarno-50-promptiv.pdf',format='A4',print_background=True,margin=dict(top='16mm',bottom='16mm',left='14mm',right='14mm')); b.close()
print('ok', n)
