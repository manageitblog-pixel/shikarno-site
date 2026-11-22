# Заливка кліпу-воронки (eps/clipN.py, META) як private → scheduled; далі ОБОВ'ЯЗКОВО finalize.py (має дати PASS).
# usage: python3 studio/eps/upload_clip.py clipN 2026-11-23T13:00:00Z
# Квота: upload 1600 + обкладинка 50 + плейлист 50 + правка snippet 50 — перевір studio/data/quota.log (ліміт 10 000/добу, скидання 08:00Z).
# Ніколи не видаляє й не перезаливає: yt.upload сам пропускає дубль назви за 24 год; slug з uploaded.json — стоп.
import sys, os, json, subprocess, importlib
sys.path[:0] = ["/home/claude/yt", "/home/claude/eps", os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")]
import yt
from util import update_json
slug, at = sys.argv[1], sys.argv[2]
U = "/home/claude/eps/uploaded.json"
if slug in json.load(open(U)): sys.exit(f"{slug} вже в uploaded.json — не заливаю повторно")
m = importlib.import_module(slug); M = m.META; D = f"/home/claude/eps/{slug}"
FOOT = importlib.import_module("meta").FOOT
vid = yt.upload(f"{D}/final.mp4", M["title"], M["description"] + FOOT, M["tags"], privacy="private", publish_at=at)
update_json(U, lambda u: u.__setitem__(slug, vid), {})
print("schedule:", yt.schedule(vid, at))
r = subprocess.run(["python3", "/home/claude/yt/finalize.py", vid, *M["playlists"], "--thumb", f"{D}/thumb.jpg",
                    "--comment", M["first_comment"], "--at", at, "--style", "v4"], capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip()[-500:])
print("RESULT", slug, vid, at, "PASS" if r.returncode == 0 else "FAIL")
