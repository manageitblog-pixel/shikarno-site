#!/usr/bin/env python3
"""Ключові слова для ролика без vidIQ (власник 9.11: «теги однотипні… обирай нішеві, менш конкурентні»).

Попит: підказки пошуку YouTube (autocomplete, hl=uk, gl=UA) для зерна + «як/що/чому/безкоштовно…» + літери.
Конкуренція: для топ-запитів — пошук YouTube Data API (UA, uk, за 12 міс): скільки з топ-10 роликів
україномовні, медіана переглядів і розмір каналів. Чим менше україномовних і слабші канали — тим легше.
Російськомовні підказки відкидаються (ы, э, ъ, ё).

usage: python3 studio/yt/kw.py "claude" [--check 8]
Квота API: ~101 одиниця на перевірений запит (search 100 + videos 1).
"""
import sys, json, re, statistics, urllib.parse, urllib.request
sys.path.insert(0, "/home/claude/yt")

RU = re.compile(r"[ыэъё]|\b(как|или|бесплатно|возможност\w*|жизни|что|чем|нейросет\w*|пользоват\w*|сделать|работа\w*|нужно)\b", re.I)
PREFIX = ["", "як ", "що таке ", "чому ", "безкоштовно ", "для ", "українською "]
SUFFIX = ["", " українською", " безкоштовно", " як користуватися", " для бізнесу", " для початківців"]
LETTERS = list("абвгдежзиклмнопрстуфхцчшщюя")


def suggest(q):
    u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "ds": "yt", "hl": "uk", "gl": "UA", "q": q})
    try:
        return json.load(urllib.request.urlopen(u, timeout=10))[1]
    except Exception:
        return []


def demand(seed):
    seen = {}
    qs = [p + seed for p in PREFIX] + [seed + s for s in SUFFIX[1:]] + [seed + " " + l for l in LETTERS]
    for rank_q in qs:
        for i, s in enumerate(suggest(rank_q)):
            if RU.search(s) or not any(t[:5].lower() in s.lower() for t in seed.split() if len(t) > 2):
                continue  # російське або не про нашу тему
            seen[s] = seen.get(s, 0) + (10 - i)  # вища позиція і частіша поява = більший попит
    return sorted(seen.items(), key=lambda x: -x[1])


def competition(q):
    import yt
    from datetime import datetime, timedelta, timezone
    after = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = yt.api("search", part="snippet", q=q, type="video", regionCode="UA", relevanceLanguage="uk",
               maxResults=10, publishedAfter=after)
    items = s.get("items", [])
    if not items:
        return None
    ids = ",".join(i["id"]["videoId"] for i in items)
    v = yt.api("videos", part="statistics,snippet", id=ids)["items"]
    views = [int(x["statistics"].get("viewCount", 0)) for x in v]
    uk = sum(1 for x in v if (x["snippet"].get("defaultAudioLanguage", "") or x["snippet"].get("defaultLanguage", "")).startswith("uk")
             or re.search(r"[іїєґ]", x["snippet"]["title"], re.I))
    return {"uk_in_top10": uk, "median_views": int(statistics.median(views)) if views else 0}


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    seed = sys.argv[1]
    n = int(sys.argv[sys.argv.index("--check") + 1]) if "--check" in sys.argv else 8
    d = demand(seed)
    print(f"Попит (підказки YouTube, UA/uk), зерно «{seed}»: {len(d)} фраз")
    for s, sc in d[:30]:
        print(f"  {sc:4d}  {s}")
    if n:
        print(f"\nКонкуренція для топ-{n} (YouTube API, UA, 12 міс):")
        print("  укр.у топ-10 | медіана переглядів | фраза   → легше: мало укр. роликів і низька медіана")
        for s, _ in d[:n]:
            c = competition(s)
            if c:
                print(f"  {c['uk_in_top10']:>5}/10   {c['median_views']:>10}   {s}")


if __name__ == "__main__":
    main()
