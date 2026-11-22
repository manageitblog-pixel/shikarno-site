#!/usr/bin/env python3
"""TikTok у даталейк: studio/data/tiktok/<дата>.json (знімки профілю через vidIQ) → таблиця tiktok_snap в analytics.sqlite.
Власник 22.11: «має бути аналітика по TikTok, сайту і Telegram, а не тільки YouTube».
Запуск: python3 studio/yt/tiktok_ingest.py   (ідемпотентно: insert or replace по (date, video_id))."""
import os, glob, json, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(ROOT, "studio", "data", "analytics.sqlite")
SRC = os.path.join(ROOT, "studio", "data", "tiktok")


def main():
    c = sqlite3.connect(DB)
    c.execute("create table if not exists tiktok_snap(date text, video_id text, posted text, title text, views int, likes int, comments int, shares int, saves int, dur int, primary key(date, video_id))")
    files = sorted(glob.glob(os.path.join(SRC, "*.json"))); n = 0
    for f in files:
        d = json.load(open(f, encoding="utf-8")); date = d.get("date") or os.path.basename(f)[:10]
        for v in d.get("videos", []):
            c.execute("insert or replace into tiktok_snap values(?,?,?,?,?,?,?,?,?,?)",
                      (date, str(v["id"]), v.get("posted"), v.get("title"), v.get("views"), v.get("likes"), v.get("comments"), v.get("shares"), v.get("saves"), v.get("dur")))
            n += 1
    c.commit()
    print(f"tiktok_snap: {len(files)} знімків, {n} рядків записано; у таблиці", c.execute("select count(*) from tiktok_snap").fetchone()[0])


if __name__ == "__main__":
    main()
