"""Попит і конкуренція за запитом/тегом на YouTube (як vidIQ keyword score, але з офіційного API).
  python3 kw.py "chatgpt безкоштовно" "#штучнийінтелект" ...
Для кожного запиту:
  sugg   — скільки підказок YouTube-автодоповнення починається з запиту (попит: люди це набирають);
  n30    — скільки роликів за 30 днів знайшов пошук (оцінка YouTube, конкуренція);
  top    — медіана переглядів топ-10 за 30 днів (скільки реально беруть ролики на цю тему);
  small  — скільки з топ-10 від каналів < 10 тис. підписників (чи пускає тема малі канали);
  score  — 0–100: високий попит + переглядів багато + малі канали в топі + мало конкурентів.
Квота: ~102 одиниці на запит (search 100 + videos 1 + channels 1), денний ліміт 10 000."""
import json, math, statistics, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import yt


def suggest(q):
    u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "ds": "yt", "hl": "uk", "gl": "UA", "q": q})
    return json.load(urllib.request.urlopen(u, timeout=15))[1]


def research(q):
    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = yt.api("search", part="snippet", q=q, type="video", maxResults=10, order="relevance",
               publishedAfter=since, regionCode="UA", relevanceLanguage="uk")
    ids = [i["id"]["videoId"] for i in s.get("items", [])]
    vids = yt.api("videos", part="statistics,snippet", id=",".join(ids))["items"] if ids else []
    chs = {v["snippet"]["channelId"] for v in vids}
    subs = {c["id"]: int(c["statistics"].get("subscriberCount", 0))
            for c in yt.api("channels", part="statistics", id=",".join(chs))["items"]} if chs else {}
    views = [int(v["statistics"].get("viewCount", 0)) for v in vids]
    small = sum(subs.get(v["snippet"]["channelId"], 0) < 10000 for v in vids)
    sg = suggest(q)
    n30 = s.get("pageInfo", {}).get("totalResults", 0)
    top = int(statistics.median(views)) if views else 0
    score = (min(len(sg), 10) * 3                      # попит: до 30
             + min(math.log10(top + 1) * 10, 40)        # охоплення теми: до 40 (10k переглядів = 40)
             + small * 2                                 # малі канали в топі: до 20
             + max(0, 10 - math.log10(n30 + 1) * 2))     # конкуренція: до 10
    best = max(vids, key=lambda v: int(v["statistics"].get("viewCount", 0)), default=None)
    return dict(q=q, sugg=len(sg), n30=n30, top=top, small=small, score=round(score),
                ex=sg[:4], best=(best["snippet"]["title"][:60], int(best["statistics"].get("viewCount", 0))) if best else None)


if __name__ == "__main__":
    for q in sys.argv[1:]:
        r = research(q)
        print(f"{r['score']:>3}  {r['q']:<34} sugg={r['sugg']:<2} n30={r['n30']:<8} top={r['top']:<7} small={r['small']}  {r['ex']}")
        if r["best"]: print(f"      найкращий: {r['best'][1]} — {r['best'][0]}")
