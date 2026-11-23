#!/usr/bin/env python3
"""Instagram у даталейк: studio/data/instagram/<дата>.json (vidiq_instagram_owner_insights, mode=reels + mode=account)
→ таблиці ig_snap (по Reels) і ig_account (підписники, перегляди/охоплення за 30 днів) в analytics.sqlite.
Акаунт @shikarno_ai_ua (vidIQ platformAccountId 29646238265010544), перші 9 Reels — 23.11.
Запуск: python3 studio/yt/instagram_ingest.py   (ідемпотентно: insert or replace по (ts, shortcode) і ts)."""
import os, glob, json, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(ROOT, "studio", "data", "analytics.sqlite")
SRC = os.path.join(ROOT, "studio", "data", "instagram")


def _metric(acc, name):
    for m in (acc or {}).get("data", []):
        if m.get("name") == name:
            return (m.get("total_value") or {}).get("value")
    return None


def ingest(db=DB, src=SRC):
    c = sqlite3.connect(db)
    c.execute("""create table if not exists ig_snap(ts text, shortcode text, published text, plays int, likes int, comments int,
                 shares int, saves int, avg_watched_pct real, skip_rate real, primary key(ts, shortcode))""")
    c.execute("create table if not exists ig_account(ts text primary key, followers int, views_30d int, reach_30d int)")
    files = sorted(glob.glob(os.path.join(src, "*.json"))); n = 0
    for f in files:
        d = json.load(open(f, encoding="utf-8")); ts = d.get("date") or os.path.basename(f)[:-5]
        rr = d.get("reels_response") or {}; acc = d.get("account_response") or {}
        for r in rr.get("reels", []):
            c.execute("insert or replace into ig_snap values(?,?,?,?,?,?,?,?,?,?)",
                      (ts, r["shortcode"], r.get("timestamp"), r.get("playCount"), r.get("likeCount"), r.get("commentCount"),
                       r.get("shares"), r.get("saves"), r.get("avgWatchedPct"), r.get("skipRate")))
            n += 1
        followers = (acc.get("account") or {}).get("followers_count")
        if followers is None: followers = rr.get("followersCount")
        c.execute("insert or replace into ig_account values(?,?,?,?)", (ts, followers, _metric(acc, "views"), _metric(acc, "reach")))
    c.commit()
    total = c.execute("select count(*) from ig_snap").fetchone()[0]
    c.close()
    return len(files), n, total


def main():
    nf, n, total = ingest()
    print(f"ig_snap: {nf} знімків, {n} рядків записано; у таблиці {total}")


if __name__ == "__main__":
    main()
