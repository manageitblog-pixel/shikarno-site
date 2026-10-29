"""props.json для композиції Chat («Промпт → ВИДАВ»): спершу prep_ep (scenes/words/mouth для мікшу), далі поля чату.
Сцени сценарію: 0 — промпт друкується, 1 — обмін репліками (TURNS по черзі), 2 — «ВИДАВ», 3.. — реакції (REACTIONS), остання — outro."""
import sys, json, importlib, subprocess
sys.path.insert(0, "/home/claude/eps")
mod = sys.argv[1]; ep = importlib.import_module(mod); D = f"/home/claude/eps/{ep.SLUG}"
subprocess.run([sys.executable, "/home/claude/eps/prep_ep.py", mod], check=True)
p = json.load(open(f"{D}/props.json")); sc = p["scenes"]; F = lambda i: sc[i]["from"]
s1, s2 = F(1), F(2)
turns = [dict(who=w, text=t, at=round(s1 + k * (s2 - s1) / len(ep.TURNS))) for k, (w, t) in enumerate(ep.TURNS)]
rx = [dict(text=t, from_=F(i), to=F(i + 1) if i + 1 < len(sc) else p["total"]) for i, t in ep.REACTIONS]
p.update(question=ep.QUESTION, model=ep.MODEL, accent=getattr(ep, "ACCENT", None), prompt=ep.PROMPT, hook=getattr(ep, "HOOK", None), promptFrom=-40, promptTo=s1 - 8,
         turns=turns, reveal=s2 - 4, answer=ep.ANSWER, reactions=[{"text": r["text"], "from": r["from_"], "to": r["to"]} for r in rx],
         outroFrom=sc[-1]["from"] - 6)
json.dump(p, open(f"{D}/props.json", "w"), ensure_ascii=False)
print(ep.SLUG, p["total"], "reveal", p["reveal"], "outro", p["outroFrom"])
