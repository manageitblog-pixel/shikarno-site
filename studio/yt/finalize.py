#!/usr/bin/env python3
"""ОДИН крок після заливки (власник 14.11: «перевіряй все і пофікси пайплайн»).
usage: python3 studio/yt/finalize.py <vid> <playlist-key...> --thumb <jpg> --comment "<питання>" [--at 2026-11-14T12:00:00Z] [--style v2|v3|v4]
Робить: обкладинка → плейлист(и) → хвіст-хештеги/теги за правилами (audit.fix) → коментар у pending_comments → запис у thumb_test.json →
перевіряє ролик audit.check і друкує PASS або список проблем. Без PASS ролик не вважається готовим.
"""
import sys, os, json, subprocess, argparse
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")); from util import update_json
import yt, audit

ap = argparse.ArgumentParser()
ap.add_argument("vid"); ap.add_argument("pl", nargs="+")
ap.add_argument("--thumb", required=True); ap.add_argument("--comment", required=True)
ap.add_argument("--at"); ap.add_argument("--style", default="")
a = ap.parse_args()
import time
# YouTube віддає застарілий snippet ~30 с після заливки/зміни (15.11: теги «зникли», а fix перезаписав опис) → чекаємо, поки теги з'являться
# 22.11: одразу після заливки duration = P0D → audit вважав 6-хв шоу Short-ом і дописав «#ШІ #shorts» → чекаємо й обробку відео (до ~10 хв)
def fresh(vid, tries=40):
    for _ in range(tries):
        v = yt.api("videos", part="snippet,status,contentDetails", id=vid)["items"][0]
        if v["snippet"].get("tags") and audit.iso_sec(v["contentDetails"].get("duration", "P0D")) > 0: return v
        time.sleep(15)
    sys.exit("FAIL відео ще не оброблене (duration 0) — повтори finalize пізніше")

subprocess.run(["python3", "/home/claude/yt/thumb.py", a.vid, a.thumb], check=True, capture_output=True)
pls = audit.playlist_map()
have = set(pls.get(a.vid, []))
for k in a.pl:
    if k not in have: yt.add_to_playlist(a.vid, k)
v = fresh(a.vid)
audit.fix(v, audit.check(v, {a.vid: a.pl}, None))
pc = "/home/claude/eps/pending_comments.json"
update_json(pc, lambda p: p.__setitem__(a.vid, {"at": a.at or v["status"].get("publishAt") or "", "text": a.comment}), {})
if a.style:
    tt = "/home/claude/eps/thumb_test.json"
    update_json(tt, lambda d: d.__setitem__(a.vid, {"ep": v["snippet"]["title"][:40], "style": a.style, "set": v["status"].get("publishAt", "")}), {})
time.sleep(20); v = fresh(a.vid)
r = audit.check(v, audit.playlist_map(), None)
iss = [i for i in r["issues"] if i != "C1"]  # коментар з'явиться після publishAt (post_comments.py)
print("PASS" if not iss else "FAIL " + ",".join(iss), "|", r["title"])
sys.exit(0 if not iss else 1)
