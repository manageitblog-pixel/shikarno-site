import datetime as D, json
LONG={1:("prof","Професії #1"),2:("month","ШІ за жовтень"),4:("prof","Професії #2"),6:("skills","Скіли й MCP #1"),8:("digest","Дайджест #2"),
10:("prof","Професії #3"),13:("skills","Скіли й MCP #2"),15:("digest","Дайджест #3"),17:("prof","Професії #4"),20:("skills","Скіли й MCP #3"),
22:("digest","Дайджест #4"),24:("prof","Професії #5"),27:("skills","Скіли й MCP #4"),29:("digest","Дайджест #5")}
COL={"prof":"#7C5CFF","skills":"#4CF2FF","digest":"#FFD60A","month":"#FF4F8B"}
cells=""
first=D.date(2026,11,1).weekday()
cells+="".join('<div class="c empty"></div>' for _ in range(first))
for d in range(1,31):
    dt=D.date(2026,11,d); past=d<=3
    l=LONG.get(d)
    lb=f'<div class="lg" style="background:{COL[l[0]]}">{l[1]}</div>' if l else ""
    cells+=f'<div class="c{" past" if past else ""}"><div class="dn">{d}</div><div class="sh">4 Shorts</div>{lb}</div>'
types=[("Новина + вердикт",27,"#FFD60A"),("Байт пробує",19,"#4CF2FF"),("Чат / тренд",15,"#FF4F8B"),("ШІ для професій",15,"#7C5CFF"),
("Скіли (1 скіл = 1 результат)",12,"#9BE564"),("Антишахраї",8,"#FF6B6B"),("Не плати за це",8,"#FFA94D"),("Тір-листи",16,"#B197FC")]
mx=max(t[1] for t in types)
bars="".join(f'<div class="br"><span class="bl">{n}</span><div class="bt"><div class="bf" style="width:{v/mx*100:.0f}%;background:{c}"></div></div><b>{v}</b></div>' for n,v,c in types)
html=f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&family=Golos+Text:wght@400;600&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box}}body{{margin:0;width:1200px;background:linear-gradient(160deg,#0B0A1C,#1A1240);color:#fff;font-family:"Golos Text",sans-serif;padding:48px}}
h1{{font:900 56px Montserrat;margin:0}}h1 span{{color:#FFD60A}}.sub{{opacity:.75;font-size:22px;margin:8px 0 28px}}
.kpi{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:30px}}.k{{background:#ffffff12;border-radius:18px;padding:18px}}
.k b{{font:900 46px Montserrat;display:block}}.k span{{font-size:17px;opacity:.8}}
.wd{{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:6px;font:800 16px Montserrat;opacity:.6;text-align:center}}
.cal{{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}}.c{{background:#ffffff10;border-radius:14px;min-height:112px;padding:10px;position:relative}}
.c.empty{{background:none}}.c.past{{opacity:.55}}.dn{{font:900 24px Montserrat}}.sh{{font-size:14px;opacity:.75}}
.lg{{margin-top:8px;color:#0B0A1C;font:800 13px Montserrat;border-radius:8px;padding:5px 7px}}
h2{{font:900 30px Montserrat;margin:34px 0 14px}}.br{{display:grid;grid-template-columns:330px 1fr 56px;align-items:center;gap:14px;margin:9px 0;font-size:19px}}
.bt{{background:#ffffff14;border-radius:9px;height:22px}}.bf{{height:22px;border-radius:9px}}.br b{{font:900 22px Montserrat;text-align:right}}
.lgd{{display:flex;gap:18px;flex-wrap:wrap;margin-top:14px;font-size:17px}}.lgd i{{display:inline-block;width:16px;height:16px;border-radius:4px;margin-right:6px;vertical-align:-2px}}
.ft{{margin-top:28px;opacity:.6;font-size:16px}}</style></head><body>
<h1>Листопад у <span>ШІкарно</span></h1><div class="sub">План публікацій · 1–30.11.2026 · 1–3.11 уже вийшло</div>
<div class="kpi"><div class="k"><b>120</b><span>Shorts на YouTube<br>4 на день</span></div><div class="k"><b>14</b><span>великих відео<br>3 на тиждень</span></div>
<div class="k"><b>~134</b><span>статті на сайті</span></div><div class="k"><b>~134</b><span>пости в Telegram</span></div><div class="k"><b>~84</b><span>TikTok<br>3 на день з 4.11</span></div></div>
<div class="wd"><div>Пн</div><div>Вт</div><div>Ср</div><div>Чт</div><div>Пт</div><div>Сб</div><div>Нд</div></div><div class="cal">{cells}</div>
<div class="lgd"><span><i style="background:#7C5CFF"></i>ШІ для професій (розбір)</span><span><i style="background:#4CF2FF"></i>Скіли, MCP і конектори</span><span><i style="background:#FFD60A"></i>Дайджест тижня</span><span><i style="background:#FF4F8B"></i>ШІ за місяць</span></div>
<h2>Shorts за типами (120)</h2>{bars}
<div class="ft">Shorts щодня о 10:00 · 14:00 · 19:00 · 21:00 (Київ). Великі — 19:00, дайджест — неділя 12:00. «ШІ за листопад» — 1.12.<br>TikTok — 12:00 · 17:00 · 21:00. Розподіл типів з 11.11 орієнтовний.</div>
</body></html>'''
open("nov.html","w").write(html)
print(sum(t[1] for t in types))
