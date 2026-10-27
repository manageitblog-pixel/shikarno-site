# Оновлює special1/meta.json таймкодами з chapters.json
import json,re,sys
D=f"/home/claude/eps/{sys.argv[1] if len(sys.argv)>1 else 'special1'}"
m=json.load(open(f"{D}/meta.json")); ch=json.load(open(f"{D}/chapters.json"))
ts=lambda s:f"{int(s)//60}:{int(s)%60:02d}"
lines="\n".join(f"{ts(a)} {b.replace('Коротко','Чого не робити')}" for a,b in ch)
m["description"]=re.sub(r"0:00 Вступ\n(?:\d+:\d\d [^\n]*\n)*", lines+"\n", m["description"],1)
m["description"]=m["description"].replace("Розбираємо, що сталося, кого це зачіпає,","Розбираємо, що сталося, масштаб у цифрах, як реагують компанії й хостинги, кого це зачіпає,")
m["description"]=m["description"].replace("Практичні поради — ","Реакція вендорів — https://www.helpnetsecurity.com/2026/10/22/php2shell-vulnerability-fortinet-cisco-palo-alto-networks/\nЦифри експозиції — https://www.recordedfuture.com/blog/php2shell-vulnerability-exploitation\nСтатус хостингів — https://www.activeset.co/blog/php2shell-host-status\nПрактичні поради — ") if "recordedfuture" not in m["description"] else m["description"]
json.dump(m,open(f"{D}/meta.json","w"),ensure_ascii=False,indent=1); print(lines); print(len(m["description"]))
