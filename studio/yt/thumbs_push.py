"""Довантажує заставки з thumbs_2026-10-28.json (готові jpg у eps/thumbs/), поки YouTube не скаже 429.
Зроблені — у thumbs_done.json. Запускати раз на 1–2 год, поки не залишиться 0."""
import json, os, sys
sys.path.insert(0, "/home/claude/yt")
import thumb
D = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(f"{D}/thumbs_2026-10-28.json"))
done_p = f"{D}/thumbs_done.json"
done = json.load(open(done_p)) if os.path.exists(done_p) else []
for vid in M:
    if vid in done: continue
    r = thumb.set_thumb(vid, f"/home/claude/eps/thumbs/{vid}.jpg")
    if "err" in r:
        print(vid, r["err"]); break
    done.append(vid); print(vid, "ok")
json.dump(done, open(done_p, "w"), indent=1)
print("left", len([v for v in M if v not in done]))
