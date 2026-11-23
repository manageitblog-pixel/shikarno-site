#!/usr/bin/env python3
"""База аналітики ШІкарно (власник 22.11: «тримати аналітику, базу історичних даних і аналізувати»).

studio/data/analytics.sqlite:
  videos(id, slug, title, published, duration_s, short, format, playlists)          — паспорт кожного ролика
  daily(video_id, date, views, engaged, avg_pct, avg_dur, subs, shares, likes)     — щоденні цифри (YouTube Analytics);
                                                                                     avg_pct/avg_dur NULL = API не дав утримання (малі дні)
  traffic(video_id, source, views, updated)                                         — джерела трафіку за весь час
  snap(video_id, date, views_public)                                                — публічний лічильник (свіжий, без затримки 2–3 дні)
  daily.watch_min, daily.subs_lost                                                  — хвилини перегляду й відписки (з 22.11)
  channel_daily(date, views, watch_min, subs_gained, subs_lost, avg_pct, long_watch_min, short_views) — канал по днях (у базі з 25.07; sync тягне з 2026-10-01);
                                                                                     дні без переглядів API не віддає (пропуск = 0); avg_pct NULL = немає утримання
  traffic_daily(video_id, date, source, views)                                     — джерела трафіку по днях (останні 60 днів, історія не перезаписується)
  tg_daily(date, members)                                                           — підписники Telegram-каналу на дату

usage:
  python3 studio/yt/analytics_db.py sync [--days 120]   # оновити все (щодня зранку в радарі)
  python3 studio/yt/analytics_db.py report               # формати: медіана переглядів на 7-й день, % перегляду, підписки/1000
  python3 studio/yt/analytics_db.py top [N]              # топ і низ роликів за переглядами 7 днів
  python3 studio/yt/analytics_db.py formats              # застосувати studio/data/format_overrides.json без звернень до API
  python3 studio/yt/analytics_db.py hours                # години перегляду довгих (videoOnDemand) за 365 днів — для YPP
"""
import sys, os, json, sqlite3, datetime, statistics, urllib.request, urllib.parse
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, os.path.dirname(__file__))
import yt, audit

DB = os.path.join(os.path.dirname(__file__), "..", "data", "analytics.sqlite")
UP = "/home/claude/eps/uploaded.json"
OVERRIDES = os.path.join(os.path.dirname(__file__), "..", "data", "format_overrides.json")
FORMATS = {"tier", "prof", "sec", "skills", "digest", "free", "try", "check", "news", "guide"}


def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("pragma busy_timeout=10000")
    c.executescript("""
    create table if not exists videos(id text primary key, slug text, title text, published text, duration_s int, short int, format text, playlists text);
    create table if not exists daily(video_id text, date text, views int, engaged int, avg_pct real, avg_dur real, subs int, shares int, likes int, primary key(video_id,date));
    create table if not exists traffic(video_id text, source text, views int, updated text, primary key(video_id,source));
    create table if not exists snap(video_id text, date text, views_public int, primary key(video_id,date));
    create table if not exists channel_daily(date text primary key, views int, watch_min real, subs_gained int, subs_lost int, avg_pct real, long_watch_min real, short_views int);
    create table if not exists traffic_daily(video_id text, date text, source text, views int, primary key(video_id,date,source));
    create table if not exists tg_daily(date text primary key, members int);
    """)
    have = {r[1] for r in c.execute("pragma table_info(daily)")}
    for col, typ in (("watch_min", "real"), ("subs_lost", "int")):
        if col not in have: c.execute(f"alter table daily add column {col} {typ}")
    return c


def ya(**q):
    q["ids"] = "channel==MINE"
    r = urllib.request.Request("https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(q),
                               headers={"Authorization": "Bearer " + yt.token()})
    return json.load(urllib.request.urlopen(r, timeout=60))


def clamp_pct(x):
    return None if x is None else max(0.0, min(100.0, float(x)))


def no_retention(views, avg_pct, avg_dur, watch_min):
    """YouTube не віддає утримання для днів з 1–3 переглядами: views>0, а avg_pct=avg_dur=watch_min=0.
    Такий 0 — «немає даних», не «0% перегляду»: зберігаємо avg_pct/avg_dur як NULL (data-quality 22.11)."""
    return (views or 0) > 0 and not avg_pct and not avg_dur and not watch_min


def sync_channel(c, start="2026-10-01", end=None):
    """Канал по днях: загальні цифри + хвилини довгих (videoOnDemand) + перегляди Shorts (фільтр creatorContentType працює)."""
    end = end or datetime.date.today().isoformat()
    rows = {r[0]: list(r[1:]) for r in ya(startDate=start, endDate=end, dimensions="day",
            metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,averageViewPercentage").get("rows", [])}
    lw = {r[0]: r[1] for r in ya(startDate=start, endDate=end, dimensions="day", metrics="estimatedMinutesWatched",
                                 filters="creatorContentType==videoOnDemand").get("rows", [])}
    sv = {r[0]: r[1] for r in ya(startDate=start, endDate=end, dimensions="day", metrics="views",
                                 filters="creatorContentType==shorts").get("rows", [])}
    for d, (v, wm, sg, sl, pct) in rows.items():
        pct = None if no_retention(v, pct, None, wm) else clamp_pct(pct)  # 1–3 перегляди за день: 0% = «немає даних» (data-quality 22.11, ніч)
        c.execute("insert or replace into channel_daily values(?,?,?,?,?,?,?,?)", (d, v, wm, sg, sl, pct, lw.get(d, 0), sv.get(d, 0)))
    return len(rows)


def sync_tg(c):
    sys.path.insert(0, "/home/claude/tg"); import tg
    n = tg.call("getChatMemberCount", chat_id=tg.CH)["result"]
    c.execute("insert or replace into tg_daily values(?,?)", (datetime.date.today().isoformat(), n))
    return n


def long_hours_12m():
    """Години перегляду довгих відео (creatorContentType==videoOnDemand) за останні 365 днів — з API, не захардкоджено."""
    end = datetime.date.today(); start = end - datetime.timedelta(days=365)
    r = ya(startDate=start.isoformat(), endDate=end.isoformat(), metrics="estimatedMinutesWatched", filters="creatorContentType==videoOnDemand")
    return round(((r.get("rows") or [[0]])[0][0] or 0) / 60, 1)


def all_videos():
    ch = yt.api("channels", part="contentDetails", mine="true")["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        q = dict(part="contentDetails", playlistId=up, maxResults=50)
        if tok: q["pageToken"] = tok
        r = yt.api("playlistItems", **q)
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok: return ids


def fmt(title, pls):
    for k in ("tier", "prof", "sec", "skills", "digest", "free", "try", "check"):
        if k in pls: return k
    for rx, k in audit.PL_RULES:
        import re
        if re.search(rx, title.lower()): return k
    return "news"


def load_overrides(path=None):
    """{video_id: format} з format_overrides.json; ключі на «_» — коментарі. Невідомий формат → ValueError (щоб не зіпсувати медіани)."""
    path = path or OVERRIDES
    if not os.path.exists(path): return {}
    raw = json.load(open(path, encoding="utf-8"))
    ov = {k: v for k, v in raw.items() if not k.startswith("_")}
    bad = {k: v for k, v in ov.items() if v not in FORMATS}
    if bad: raise ValueError(f"format_overrides: невідомі формати {bad}")
    return ov


def apply_overrides(c, ov=None):
    """Ручні виправлення формату поверх плейлиста (data-quality 23.11): плейлист/регекс помиляються, override — ні.
    Викликається в sync після запису videos, тож повторний sync не відкочує правку. Повертає [(id, було, стало)]."""
    ov = load_overrides() if ov is None else ov; changed = []
    for vid, f in ov.items():
        r = c.execute("select format from videos where id=?", (vid,)).fetchone()
        if r and r[0] != f:
            c.execute("update videos set format=? where id=?", (f, vid)); changed.append((vid, r[0], f))
    return changed


def sync(days=120):
    c = db(); today = datetime.date.today()
    slug_by_id = {v: k for k, v in json.load(open(UP)).items()}
    pls = audit.playlist_map()
    ids = all_videos()
    for i in range(0, len(ids), 50):
        for v in yt.api("videos", part="snippet,contentDetails,statistics,status", id=",".join(ids[i:i + 50]))["items"]:
            if v["status"]["privacyStatus"] != "public": continue
            d = audit.iso_sec(v["contentDetails"]["duration"]); t = v["snippet"]["title"]; p = pls.get(v["id"], [])
            c.execute("insert or replace into videos values(?,?,?,?,?,?,?,?)",
                      (v["id"], slug_by_id.get(v["id"], ""), t, v["snippet"]["publishedAt"], d, int(d <= 180), fmt(t, p), ",".join(p)))
            c.execute("insert or replace into snap values(?,?,?)", (v["id"], today.isoformat(), int(v["statistics"].get("viewCount", 0))))
    print("format overrides:", len(apply_overrides(c)), "змінено")
    start = (today - datetime.timedelta(days=days)).isoformat(); end = today.isoformat()
    # API не дає day×video разом для всіх → по ролику
    vids = [r[0] for r in c.execute("select id from videos")]
    for vid in vids:
        try:
            r = ya(startDate=start, endDate=end, dimensions="day", filters=f"video=={vid}",
                   metrics="views,engagedViews,averageViewPercentage,averageViewDuration,subscribersGained,shares,likes,estimatedMinutesWatched,subscribersLost")
        except Exception as e:
            print("ERR daily", vid, e); continue
        for row in r.get("rows", []):
            row = list(row); row[3] = clamp_pct(row[3])  # бувало 600% — обрізаємо до 0..100
            if no_retention(row[1], row[3], row[4], row[8]): row[3] = row[4] = None  # API не дав утримання ≠ 0%
            c.execute("insert or replace into daily(video_id,date,views,engaged,avg_pct,avg_dur,subs,shares,likes,watch_min,subs_lost) values(?,?,?,?,?,?,?,?,?,?,?)", (vid, *row))
        try:
            t = ya(startDate="2026-01-01", endDate=end, dimensions="insightTrafficSourceType", filters=f"video=={vid}", metrics="views")
            for s, n in t.get("rows", []):
                c.execute("insert or replace into traffic values(?,?,?,?)", (vid, s, n, end))
        except Exception as e:
            print("ERR traffic", vid, e)
        try:  # по днях — історія не перезаписується
            t = ya(startDate=(today - datetime.timedelta(days=60)).isoformat(), endDate=end, dimensions="day,insightTrafficSourceType",
                   filters=f"video=={vid}", metrics="views")
            for d, s, n in t.get("rows", []):
                c.execute("insert or replace into traffic_daily values(?,?,?,?)", (vid, d, s, n))
        except Exception as e:
            print("ERR traffic_daily", vid, e)
    c.commit()
    try: print("channel_daily:", sync_channel(c, start=min("2026-10-01", start)), "днів")
    except Exception as e: print("ERR channel_daily", e)
    try: print("tg_daily: учасників", sync_tg(c))
    except Exception as e: print("ERR tg_daily", e)
    c.commit()
    n = c.execute("select count(*) from videos").fetchone()[0]; m = c.execute("select count(*) from daily").fetchone()[0]
    print(f"sync OK: {n} відео, {m} рядків daily")


def first7(c, vid):
    pub = c.execute("select published from videos where id=?", (vid,)).fetchone()[0][:10]
    end = (datetime.date.fromisoformat(pub) + datetime.timedelta(days=6)).isoformat()
    # % перегляду зважений лише на дні, де API дав утримання (avg_pct NULL = немає даних, не 0%)
    r = c.execute("select sum(views), sum(views*avg_pct)/nullif(sum(case when avg_pct is not null then views end),0), sum(subs) "
                  "from daily where video_id=? and date between ? and ?", (vid, pub, end)).fetchone()
    return (r[0] or 0, r[1] or 0, r[2] or 0)


def report():
    c = db(); by = {}
    cutoff = (datetime.date.today() - datetime.timedelta(days=9)).isoformat()  # дані запізнюються на 2–3 дні
    for vid, f, sh, pub in c.execute("select id, format, short, published from videos"):
        if pub[:10] > cutoff: continue
        v, pct, s = first7(c, vid); by.setdefault(("S" if sh else "L") + ":" + f, []).append((v, pct, s))
    print(f"{'формат':16} {'n':>3} {'мед.перегл.7д':>14} {'мед.%перегл':>12} {'підп/1000':>10}")
    rows = []
    for k, xs in by.items():
        tv = sum(x[0] for x in xs); ts = sum(x[2] for x in xs)
        rows.append((statistics.median(x[0] for x in xs), k, len(xs), statistics.median(x[1] for x in xs), 1000 * ts / max(tv, 1)))
    for med, k, n, pct, spk in sorted(rows, reverse=True):
        print(f"{k:16} {n:3} {med:14.0f} {pct:11.1f}% {spk:10.1f}")


def top(n=10):
    c = db(); out = []
    cutoff = (datetime.date.today() - datetime.timedelta(days=9)).isoformat()
    for vid, t, f, pub in c.execute("select id, title, format, published from videos"):
        if pub[:10] > cutoff: continue
        v, pct, s = first7(c, vid); out.append((v, pct, s, f, t[:70], vid))
    out.sort(reverse=True)
    for lab, part in (("ТОП", out[:n]), ("НИЗ", out[-n:])):
        print("==", lab)
        for v, pct, s, f, t, vid in part: print(f"{v:6} {pct:5.1f}% +{s:<3} {f:7} {t} {vid}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["report"]
    if a[0] == "sync": sync(int(a[2]) if len(a) > 2 and a[1] == "--days" else 120)
    elif a[0] == "hours": print(f"довгі (videoOnDemand), 365 днів: {long_hours_12m()} год")
    elif a[0] == "formats":
        c = db(); ch = apply_overrides(c); c.commit()
        for vid, old, new in ch: print(f"{vid}: {old} → {new}")
        print(f"format overrides: {len(ch)} змінено, {len(load_overrides())} у файлі")
    elif a[0] == "top": top(int(a[1]) if len(a) > 1 else 10)
    else: report()
