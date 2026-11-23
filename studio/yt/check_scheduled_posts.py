"""Відкладені статті, які вже мали вийти, але сайт віддає 404.

GitHub cron для pages.yml 23.11 не спрацьовував (ні */30, ні 7,22,37,52) — статті з'являлись лише
після ручного запуску workflow. Цей скрипт щогодини (перевірка бота :49) знаходить пости з датою
в останні N годин і перевіряє живий URL. Вихід: рядки «404 <url>» і код 1, якщо треба запускати pages.yml.
python3 studio/yt/check_scheduled_posts.py [hours=6]
"""
import sys, os, re, glob, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECTION = {"news": "novyny", "rozbir": "rozbory", "dajdzhest": "dajdzhest", "misyats": "za-misyats"}


def front(path):
    s = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---", s, re.S)
    if not m: return {}
    d = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^(kind|slug|date):\s*(.+)$", line)
        if mm: d[mm.group(1)] = mm.group(2).strip().strip('"\'')
    return d


def due(hours, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    out = []
    for p in glob.glob(os.path.join(ROOT, "content/posts/*.md")):
        f = front(p)
        if not f.get("date") or not f.get("slug"): continue
        try: dt = datetime.datetime.fromisoformat(f["date"])
        except ValueError: continue
        if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
        if now - datetime.timedelta(hours=hours) <= dt <= now:
            out.append(f"https://shikarno.com.ua/{SECTION.get(f.get('kind', 'news'), 'novyny')}/{f['slug']}/")
    return out


def status(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url + "?chk=1", method="HEAD"), timeout=20).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


if __name__ == "__main__":
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 6
    bad = [u for u in due(hours) if status(u) != 200]
    for u in bad: print("404", u)
    print(f"due≤{hours}h checked; missing: {len(bad)}")
    sys.exit(1 if bad else 0)
