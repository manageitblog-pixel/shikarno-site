#!/usr/bin/env python3
"""Щовечірній зріз росту проти цілей звіту 1.12 (docs/org/strategy.md §9).

Знімає реальні цифри з першоджерел і дописує один JSON-рядок у studio/data/growth_1201.jsonl:
  YouTube підписники      — YouTube Data API channels.statistics (публічний лічильник, без затримки)
  години довгих за 12 міс — analytics_db.long_hours_12m() (YouTube Analytics, запізнення 2–3 дні)
  кліки/покази Google 28д — Search Console (lake.gsc), вікно = 28 днів до останньої дати з даними
  Telegram                — Bot API getChatMemberCount
  TikTok                  — останній знімок studio/data/tiktok/*.json (vidIQ; сам скрипт TikTok не знімає)
  Сайт наживо             — Cloudflare Web Analytics (hq_data.cf_live): перегляди сторінок сьогодні (Київ) і за 7 днів
Якщо джерело впало — значення null і текст помилки в "errors"; вигаданих цифр немає.

usage: python3 studio/yt/growth_snapshot.py          # зняти й дописати рядок
       python3 studio/yt/growth_snapshot.py --dry    # лише показати, не писати
"""
import sys, os, json, glob, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "studio", "data", "growth_1201.jsonl")
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, HERE)

BASE = {"yt_subs": 311, "long_hours_12m": 10.5, "gsc_clicks_28d": 43, "gsc_impr_28d": 3669, "tg_members": 6, "tiktok_views": 15304}  # TikTok: з 23.11 19:18Z база = сума всіх відомих відео (11); стара 12387 рахувала лише 7 останніх. Like-for-like ті самі 7: 12387 → 12483 (+96) за 22.11 20:53Z–23.11 16:56Z
TARGET = {"yt_subs": 330, "long_hours_12m": 14, "gsc_clicks_28d": 60, "tg_members": 15}


def yt_channel():
    import yt
    s = yt.api("channels", part="statistics", mine="true")["items"][0]["statistics"]
    return {"yt_subs": int(s["subscriberCount"]), "yt_views_total": int(s["viewCount"]), "yt_videos": int(s["videoCount"])}


def long_hours():
    import analytics_db
    return {"long_hours_12m": analytics_db.long_hours_12m()}


def gsc_28d():
    import lake
    today = datetime.date.today()
    rows = lake.gsc({"startDate": (today - datetime.timedelta(days=40)).isoformat(), "endDate": today.isoformat(), "dimensions": ["date"]})
    if not rows: raise RuntimeError("Search Console повернув 0 рядків")
    last = max(datetime.date.fromisoformat(r["keys"][0]) for r in rows); start = last - datetime.timedelta(days=27)
    win = [r for r in rows if start <= datetime.date.fromisoformat(r["keys"][0]) <= last]
    return {"gsc_clicks_28d": int(sum(r["clicks"] for r in win)), "gsc_impr_28d": int(sum(r["impressions"] for r in win)),
            "gsc_window": f"{start}..{last}"}


def telegram():
    sys.path.insert(0, "/home/claude/tg"); import tg
    return {"tg_members": int(tg.call("getChatMemberCount", chat_id=tg.CH)["result"])}


def tiktok():
    """Сума переглядів по ВСІХ відомих відео: для кожного video_id — останній знімок у tiktok_snap.
    (До 23.11 рахували лише останні ~7 відео зі знімка — при кожному новому пості старе випадало, сума «падала».)"""
    import sqlite3
    c = sqlite3.connect(os.path.join(ROOT, "studio", "data", "analytics.sqlite"))
    rows = c.execute("""select t.video_id, t.views, t.date from tiktok_snap t
        join (select video_id, max(date) d from tiktok_snap group by video_id) m
        on m.video_id=t.video_id and m.d=t.date""").fetchall()
    if not rows: raise RuntimeError("tiktok_snap порожня")
    return {"tiktok_views": sum(r[1] or 0 for r in rows), "tiktok_videos": len(rows),
            "tiktok_snapshot": max(r[2] for r in rows)}


def site_live():
    import hq_data
    r = hq_data.cf_live()
    if r.get("error") and not r.get("days"): raise RuntimeError(r["error"])
    return {"site_pageloads_today": r["today_pageloads"], "site_pageloads_7d": r["pageloads_7d"]}


def main():
    rec = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "date": datetime.date.today().isoformat()}
    errors = {}
    for name, fn, keys in (("youtube", yt_channel, ["yt_subs"]), ("analytics", long_hours, ["long_hours_12m"]),
                           ("search_console", gsc_28d, ["gsc_clicks_28d", "gsc_impr_28d"]), ("telegram", telegram, ["tg_members"]),
                           ("tiktok", tiktok, ["tiktok_views"]),
                           ("cloudflare", site_live, ["site_pageloads_today", "site_pageloads_7d"])):
        try: rec.update(fn())
        except Exception as e:
            errors[name] = str(e)[:300]
            for k in keys: rec[k] = None
    rec["vs_base"] = {k: (round(rec[k] - b, 1) if rec.get(k) is not None else None) for k, b in BASE.items()}
    rec["to_target"] = {k: (round(t - rec[k], 1) if rec.get(k) is not None else None) for k, t in TARGET.items()}
    if errors: rec["errors"] = errors
    line = json.dumps(rec, ensure_ascii=False)
    print(line)
    if "--dry" not in sys.argv:
        with open(OUT, "a", encoding="utf-8") as f: f.write(line + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
