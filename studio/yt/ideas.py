#!/usr/bin/env python3
"""Дошка ідей редколегії (власник 22.11: «ресерчери знаходять топ ідеї… узгоджувати, рейтингувати і приймати рішення, що піде і куди»).

Файл: studio/data/ideas.json — список ідей. Кожна ідея:
  id, title, source (URL першоджерела або «kw.py»/«outliers»), added, by (хто додав: researcher-news|researcher-search|researcher-niche|owner),
  format (tier|prof|free|sec|news|skills|try|check|digest|guide), channels [short, long, site, tg, tiktok, insta],
  demand 1–5 (пошуковий попит: kw.py / Search Console), fresh 1–5 (свіжість), show 1–5 («можна показати»), fit 1–5 (для кого: люди/бізнес/ІТ),
  status (new|approved|in_work|done|rejected), decision (коментар редколегії), video_id / url (коли вийшло).
Бал = demand × fresh × show × fit × prior(format), де prior — медіана переглядів формату за 7 днів з бази analytics_db
(нормована до найкращого формату). Після виходу — фактичні цифри з бази → перевірка прогнозу.

usage:
  python3 studio/yt/ideas.py add '{"title":"...","format":"tier","channels":["short","site"],"demand":4,"fresh":3,"show":5,"fit":5,"source":"..."}'
  python3 studio/yt/ideas.py board [N]        # рейтинг відкритих ідей
  python3 studio/yt/ideas.py set <id> status=approved decision="..."
"""
import sys, os, json, sqlite3, datetime, statistics
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
F = os.path.join(D, "ideas.json"); DB = os.path.join(D, "analytics.sqlite")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")); from util import read_json, write_json_atomic, update_json, locked


def load(): return read_json(F, [])
def save(x): write_json_atomic(F, x)


def priors():
    """Медіана переглядів за перші 7 днів по формату Shorts з бази; нормовано 0.2–1."""
    if not os.path.exists(DB): return {}
    c = sqlite3.connect(DB); by = {}
    for vid, f, pub in c.execute("select id, format, published from videos where short=1"):
        end = (datetime.date.fromisoformat(pub[:10]) + datetime.timedelta(days=6)).isoformat()
        v = c.execute("select sum(views) from daily where video_id=? and date between ? and ?", (vid, pub[:10], end)).fetchone()[0] or 0
        by.setdefault(f, []).append(v)
    med = {k: statistics.median(v) for k, v in by.items() if len(v) >= 3}
    top = max(med.values()) if med else 1
    p = {k: max(0.2, v / top) for k, v in med.items()}
    p.setdefault("prof", p.get("tier", 1)); p.setdefault("guide", 0.6); p.setdefault("digest", 0.5)
    return p


def score(i, P):
    return round(i.get("demand", 1) * i.get("fresh", 1) * i.get("show", 1) * i.get("fit", 1) * P.get(i.get("format", "news"), 0.3), 1)


def board(n=15):
    P = priors(); xs = [i for i in load() if i.get("status", "new") in ("new", "approved")]
    for i in xs: i["score"] = score(i, P)
    xs.sort(key=lambda i: -i["score"])
    print("prior:", {k: round(v, 2) for k, v in sorted(P.items(), key=lambda x: -x[1])})
    for i in xs[:n]:
        print(f"{i['score']:6.1f} [{i['status']:8}] {i['id']:>3} {i.get('format',''):6} {','.join(i.get('channels',[])):18} {i['title'][:80]}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["board"]
    if a[0] == "add":
        with locked(F):
            x = load(); i = json.loads(a[1]); i.setdefault("status", "new"); i.setdefault("added", datetime.date.today().isoformat())
            i["id"] = str(max([int(j["id"]) for j in x] or [0]) + 1); x.append(i); save(x); print("added", i["id"])
    elif a[0] == "set":
        with locked(F):
            x = load()
            for i in x:
                if i["id"] == a[1]:
                    for kv in a[2:]:
                        k, v = kv.split("=", 1); i[k] = v
            save(x); print("ok")
    else:
        board(int(a[1]) if len(a) > 1 else 15)
