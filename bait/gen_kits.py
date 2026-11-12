"""Генерує bait/kits.js із content/pages/pomichnyk-*.md: інструкція (перший ```text у «Крок 1») і 4 тижні маршруту.
Запуск: python3 bait/gen_kits.py (після будь-якої правки наборів)."""
import json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
out = {}
for f in sorted((ROOT / "content/pages").glob("pomichnyk-*.md")):
    t = f.read_text(encoding="utf-8")
    slug = f.stem
    step1 = t.split("## Крок 1", 1)[1].split("\n## ", 1)[0]
    m = re.search(r"```text\n(.*?)```", step1, re.S)
    instr = m.group(1).strip() if m else ""
    route = t.split("## Маршрут на 4 тижні", 1)[1].split("\n## ", 1)[0] if "## Маршрут на 4 тижні" in t else ""
    weeks = []
    for w in re.split(r"\n### ", route)[1:5]:
        lines = w.strip().splitlines()
        title = lines[0].strip()
        body = "\n".join(l for l in lines[1:] if l.strip())
        body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", body)
        weeks.append({"title": title, "body": body})
    out["/" + slug + "/"] = {"instr": instr, "weeks": weeks}
js = "// Згенеровано bait/gen_kits.py — не редагувати вручну\nexport const KITS = " + json.dumps(out, ensure_ascii=False, indent=0) + ";\n"
(ROOT / "bait/kits.js").write_text(js, encoding="utf-8")
print(len(out), "kits;", sum(len(v["instr"]) for v in out.values()) // len(out), "avg instr chars;", [len(v["weeks"]) for v in out.values()])
