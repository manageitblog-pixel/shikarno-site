"""Повідомляє Bing/IndexNow (а через Bing — Copilot і пошук ChatGPT) про нові й змінені сторінки.
push: сторінки змінених у коміті постів; cron: пости, що щойно стали публічними (відкладена публікація)."""
import json, os, re, subprocess, sys, urllib.request, datetime as dt
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); from config import SITE
SEC = {"news": "novyny", "rozbir": "rozbory", "dajdzhest": "dajdzhest", "misyats": "za-misyats"}
key = (ROOT/"static/indexnow-key.txt").read_text().strip()
now = dt.datetime.now(dt.timezone.utc)
event = os.environ.get("GITHUB_EVENT_NAME", "push")
changed = set()
if event == "push":
    try:
        out = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        changed = {f for f in out if f.startswith("content/")}
    except Exception: pass
urls = set()
for f in (ROOT/"content/posts").glob("*.md"):
    fm = yaml.safe_load(f.read_text(encoding="utf-8").split("---", 2)[1])
    d = fm["date"] if isinstance(fm["date"], dt.datetime) else dt.datetime.fromisoformat(str(fm["date"]))
    if d > now: continue
    just_live = 0 <= (now - d).total_seconds() < 40*60
    if just_live or str(f.relative_to(ROOT)) in changed:
        urls.add(f"{SITE['url']}/{SEC[fm.get('kind','news')]}/{fm['slug']}/")
for f in changed:
    if f.startswith("content/pages/"): urls.add(f"{SITE['url']}/{Path(f).stem}/")
if not urls: print("IndexNow: нічого нового"); sys.exit(0)
urls.add(SITE["url"] + "/")
body = json.dumps({"host": SITE["domain"], "key": key, "keyLocation": f"{SITE['url']}/{key}.txt", "urlList": sorted(urls)}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=20) as r: print("IndexNow", r.status, sorted(urls))
except Exception as e: print("IndexNow помилка:", e)
