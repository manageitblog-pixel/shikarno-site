#!/usr/bin/env python3
"""Щовечірній зріз росту проти цілей звіту 1.12 (docs/org/strategy.md §9).

Знімає реальні цифри з першоджерел і дописує один JSON-рядок у studio/data/growth_1201.jsonl:
  YouTube підписники      — YouTube Data API channels.statistics (публічний лічильник, без затримки)
  години довгих за 12 міс — analytics_db.long_hours_12m() (YouTube Analytics, запізнення 2–3 дні)
  кліки/покази Google 28д — Search Console (lake.gsc), вікно = 28 днів до останньої дати з даними
  Telegram                — Bot API getChatMemberCount
  TikTok                  — останній знімок studio/data/tiktok/*.json (vidIQ; сам скрипт TikTok не знімає)
Якщо джерело впало — значення null і текст помилки в "errors"; вигаданих цифр немає.

usage: python3 studio/yt/growth_snapshot.py          # зняти й дописати рядок
       python3 studio/yt/growth_snapshot.py --dry    # лише показати, не писати
"""
import sys, os, json, glob, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "studio", "data", "growth_1201.jsonl")
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, HERE)

BASE = {"yt_subs": 311, "long_hours_12m": 10.5, "gsc_clicks_28d": 43, "gsc_impr_28d": 3669, "tg_members": 6, "tiktok_views": 12387}
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
    files = sorted(glob.glob(os.path.join(ROOT, "studio", "data", "tiktok", "*.json")))
    if not files: raise RuntimeError("немає знімків studio/data/tiktok/")
    d = json.load(open(files[-1], encoding="utf-8")); v = d.get("videos", [])
    return {"tiktok_views": sum(x.get("views") or 0 for x in v), "tiktok_videos": len(v),
            "tiktok_snapshot": d.get("fetched") or d.get("date") or os.path.basename(files[-1])}


def main():
    rec = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "date": datetime.date.today().isoformat()}
    errors = {}
    for name, fn, keys in (("youtube", yt_channel, ["yt_subs"]), ("analytics", long_hours, ["long_hours_12m"]),
                           ("search_console", gsc_28d, ["gsc_clicks_28d", "gsc_impr_28d"]), ("telegram", telegram, ["tg_members"]),
                           ("tiktok", tiktok, ["tiktok_views"])):
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
