#!/usr/bin/env python3
"""Друга хвиля тегів за даними vidIQ (9.11, country=UA). Цифри: estimatedMonthlySearch / competition (0–100, менше = легше).
штучний інтелект 13 410/34 · ШІ 17 496/48 · ші для бізнесу 5 140/28 · chatgpt (UA 8 033) · google gemini (UA 2 606)
notebooklm (UA 9 124) · nano banana pro (UA 2 991)/40 · nano banana tutorial 44 357/31 · deepfake (UA 2 893)/42
claude mcp 97 544/47 · claude ai skills 13 155/61 (+81%) · claude ai free unlimited 640 488/39 · claude code (UA 47 203)
промпти українською <750/8 · готові промпти <750/18 · промпти для chatgpt <750/17. Звіт: docs/research/vidiq-tags-2026-11-09.md
"""
import sys, json
sys.path.insert(0, "/home/claude/yt"); import yt

def rules(title, tags):
    t = (title + " " + " ".join(tags)).lower()
    add = ["штучний інтелект", "ШІ"]
    if any(w in t for w in ["бізнес", "роботи", "фоп", "hr", "smm", "професі", "найм", "для роботи"]): add.append("ші для бізнесу")
    if "chatgpt" in t: add.append("chatgpt")
    if "gemini" in t: add.append("google gemini")
    if "notebook" in t: add.append("notebooklm")
    if "nano banana" in t: add += ["nano banana pro", "nano banana tutorial"]
    if any(w in t for w in ["дипфейк", "deepfake", "шахра", "«син»", "scam"]): add += ["deepfake", "діпфейк"]
    if "claude" in t: add.append("claude ai")
    if "mcp" in t or "конектор" in t: add.append("claude mcp")
    if "скіл" in t or "skills" in t: add.append("claude ai skills")
    if "claude безкоштовно" in t: add.append("claude ai free unlimited")
    if "claude code" in t: add.append("claude code")
    if "промпт" in t: add += ["промпти українською", "готові промпти", "промпти для chatgpt"]
    return add

def main():
    plan = json.load(open("studio/yt/retag_plan.json"))
    n = 0; log = {}
    for vid, p in plan.items():
        sn = yt.api("videos", part="snippet", id=vid)["items"][0]["snippet"]
        cur = sn.get("tags", [])
        low = {x.lower() for x in cur}
        add = [a for a in rules(sn["title"], cur) if a.lower() not in low]
        if not add: continue
        new = add + [x for x in cur if x != "ШІкарно"] + ["ШІкарно"]
        while sum(len(x) + (2 if " " in x else 0) + 1 for x in new) > 480:
            new.pop(-2)
        body = {"id": vid, "snippet": {k: sn[k] for k in ("title", "description", "categoryId") if k in sn}}
        for k in ("defaultLanguage", "defaultAudioLanguage"):
            if k in sn: body["snippet"][k] = sn[k]
        body["snippet"]["tags"] = new
        yt._put("videos", body, "snippet"); n += 1; log[vid] = {"title": sn["title"], "added": add}
    json.dump(log, open("studio/yt/retag_vidiq_log.json", "w"), ensure_ascii=False, indent=1)
    print("updated", n)

if __name__ == "__main__":
    main()
