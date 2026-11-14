#!/usr/bin/env python3
"""ОДИН крок після заливки (власник 14.11: «перевіряй все і пофікси пайплайн»).
usage: python3 studio/yt/finalize.py <vid> <playlist-key...> --thumb <jpg> --comment "<питання>" [--at 2026-11-14T12:00:00Z] [--style v2|v3|v4]
Робить: обкладинка → плейлист(и) → хвіст-хештеги/теги за правилами (audit.fix) → коментар у pending_comments → запис у thumb_test.json →
перевіряє ролик audit.check і друкує PASS або список проблем. Без PASS ролик не вважається готовим.
"""
import sys, os, json, subprocess, argparse
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, os.path.dirname(__file__))
import yt, audit

ap = argparse.ArgumentParser()
ap.add_argument("vid"); ap.add_argument("pl", nargs="+")
ap.add_argument("--thumb", required=True); ap.add_argument("--comment", required=True)
ap.add_argument("--at"); ap.add_argument("--style", default="")
a = ap.parse_args()

subprocess.run(["python3", "/home/claude/yt/thumb.py", a.vid, a.thumb], check=True, capture_output=True)
pls = audit.playlist_map()
have = set(pls.get(a.vid, []))
for k in a.pl:
    if k not in have: yt.add_to_playlist(a.vid, k)
v = yt.api("videos", part="snippet,status,contentDetails", id=a.vid)["items"][0]
audit.fix(v, audit.check(v, {a.vid: a.pl}, None))
pc = "/home/claude/eps/pending_comments.json"; p = json.load(open(pc))
p[a.vid] = {"at": a.at or v["status"].get("publishAt") or "", "text": a.comment}; json.dump(p, open(pc, "w"), ensure_ascii=False, indent=1)
if a.style:
    tt = "/home/claude/eps/thumb_test.json"; d = json.load(open(tt))
    d[a.vid] = {"ep": v["snippet"]["title"][:40], "style": a.style, "set": v["status"].get("publishAt", "")}; json.dump(d, open(tt, "w"), ensure_ascii=False, indent=1)
v = yt.api("videos", part="snippet,status,contentDetails", id=a.vid)["items"][0]
r = audit.check(v, audit.playlist_map(), None)
iss = [i for i in r["issues"] if i != "C1"]  # коментар з'явиться після publishAt (post_comments.py)
print("PASS" if not iss else "FAIL " + ",".join(iss), "|", r["title"])
sys.exit(0 if not iss else 1)
