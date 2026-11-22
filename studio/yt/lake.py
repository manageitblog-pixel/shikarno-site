#!/usr/bin/env python3
"""Даталейк ШІкарно — довідник для агентів (власник 22.11: «великий даталейк на різних дослідженнях… щоб агенти могли на основі чогось приймати рішення»).

Одна база studio/data/analytics.sqlite. Таблиці:
  videos, daily, traffic, snap       — наш YouTube (analytics_db.py sync)
  niche                              — чужі відео ніші (outliers.py; + `lake.py niche` — ширші UA/EN запити)
  research                           — усі теми з радарів docs/research/radar-*.md (дата, назва, оцінка, формат, джерела [V]/[S])
  site_daily, site_queries, site_pages — Search Console (покази, кліки, позиції)
  posts                              — усі статті сайту (slug, дата, kind, теги, youtube, слів)

usage:
  python3 studio/yt/lake.py ingest              # research + posts + Search Console (+ niche за потреби окремо)
  python3 studio/yt/lake.py niche               # ширша ніша: UA + англомовні ШІ-запити (квота ~2000 од.)
  python3 studio/yt/lake.py comp [500]         # ≥500 каналів-конкурентів: знімок статистики + останні 15 відео (щотижня)
  python3 studio/yt/lake.py ask "<тема>"        # що ми знаємо про тему: наші ролики й цифри, статті, радари, ніша, пошук
  python3 studio/yt/lake.py sql "select ..."    # довільний запит
  python3 studio/yt/lake.py stats               # скільки чого в лейку
"""
import sys, os, re, glob, json, sqlite3, datetime, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(ROOT, "studio", "data", "analytics.sqlite")
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, HERE)


def db():
    c = sqlite3.connect(DB)
    c.executescript("""
    create table if not exists research(date text, n int, title text, score int, plan text, sources text, verified int, file text, primary key(date,n,file));
    create table if not exists posts(slug text primary key, date text, kind text, title text, tags text, youtube text, words int);
    create table if not exists site_daily(date text primary key, clicks int, impressions int, ctr real, position real);
    create table if not exists site_queries(query text, period text, clicks int, impressions int, ctr real, position real, primary key(query,period));
    create table if not exists site_pages(page text, period text, clicks int, impressions int, ctr real, position real, primary key(page,period));
    create table if not exists comp(channel_id text, date text, title text, subs int, views int, videos int, country text, lang text, primary key(channel_id,date));
    create table if not exists comp_videos(video_id text primary key, channel_id text, title text, published text, duration_s int, views int, likes int, comments int, fetched text);
    create table if not exists niche(video_id text, fetched text, channel text, title text, published text, duration_s int, views int, channel_subs int, ratio real, ru int, primary key(video_id,fetched));
    """)
    c.create_function("ul", 1, lambda x: (x or "").lower())  # SQLite lower() не знає кирилиці
    return c


def ingest_research(c):
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "docs", "research", "radar-*.md"))):
        d = re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1); t = open(f, encoding="utf-8").read()
        for m in re.finditer(r"^## (\d+)\. (.+?)$(.*?)(?=^## |\Z)", t, re.S | re.M):
            head = m.group(2); body = m.group(3)
            sc = re.search(r"(\d+)/10", head); plan = head.split("→", 1)[1].strip() if "→" in head else ""
            title = re.sub(r"\s*—\s*\d+/10.*$", "", head).strip()
            urls = re.findall(r"https?://[^\s\)\]>,]+", body)
            c.execute("insert or replace into research values(?,?,?,?,?,?,?,?)",
                      (d, int(m.group(1)), title, int(sc.group(1)) if sc else None, plan, " ".join(dict.fromkeys(urls)), int("[V]" in body), os.path.basename(f)))
            n += 1
    print("research:", n)


def ingest_posts(c):
    n = 0
    for f in glob.glob(os.path.join(ROOT, "content", "posts", "*.md")):
        t = open(f, encoding="utf-8").read(); fm, _, body = t.partition("\n---\n")
        g = lambda k: (re.search(rf"^{k}:\s*(.+)$", fm, re.M) or [None, ""])[1].strip().strip('"')
        c.execute("insert or replace into posts values(?,?,?,?,?,?,?)", (g("slug"), g("date")[:10], g("kind"), g("title"), g("tags"), g("youtube"), len(body.split())))
        n += 1
    print("posts:", n)


def gsc(body):
    import yt
    r = urllib.request.Request("https://www.googleapis.com/webmasters/v3/sites/https%3A%2F%2Fshikarno.com.ua%2F/searchAnalytics/query",
                               data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + yt.token(), "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=60)).get("rows", [])


def ingest_site(c):
    end = (datetime.date.today() - datetime.timedelta(days=2)).isoformat(); start = "2026-10-01"
    for r in gsc({"startDate": start, "endDate": end, "dimensions": ["date"]}):
        c.execute("insert or replace into site_daily values(?,?,?,?,?)", (r["keys"][0], r["clicks"], r["impressions"], r["ctr"], r["position"]))
    per = f"{start}..{end}"
    for dim, tab in (("query", "site_queries"), ("page", "site_pages")):
        for r in gsc({"startDate": start, "endDate": end, "dimensions": [dim], "rowLimit": 1000}):
            c.execute(f"insert or replace into {tab} values(?,?,?,?,?,?)", (r["keys"][0], per, r["clicks"], r["impressions"], r["ctr"], r["position"]))
    print("site:", c.execute("select count(*) from site_daily").fetchone()[0], "днів,", c.execute("select count(*) from site_queries").fetchone()[0], "запитів")


NICHE_Q = ["штучний інтелект", "ChatGPT українською", "нейромережі", "Gemini", "Claude", "ШІ для бізнесу", "ШІ для роботи", "ШІ для вчителя",
           "ШІ безкоштовно", "нейромережа для фото", "ШІ агенти", "вайбкодинг", "промпти ChatGPT", "ШІ для студента", "як заробити на ШІ",
           "AI tools tier list", "ChatGPT tips", "Claude AI tutorial", "Gemini AI tips", "AI for teachers", "AI side hustle", "best AI tools 2026"]


def niche(days=60):
    import yt
    c = db(); after = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z"); vids = set()
    for q in NICHE_Q:
        en = q.isascii()
        try:
            for it in yt.api("search", part="snippet", q=q, type="video", order="viewCount", publishedAfter=after, maxResults=25,
                             **({} if en else {"relevanceLanguage": "uk", "regionCode": "UA"}))["items"]:
                vids.add(it["id"]["videoId"])
        except Exception as e:
            print("quota/err", q, e); break
    ids = list(vids); V, C = {}, {}
    for i in range(0, len(ids), 50):
        for it in yt.api("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))["items"]: V[it["id"]] = it
    chs = list({v["snippet"]["channelId"] for v in V.values()})
    for i in range(0, len(chs), 50):
        for it in yt.api("channels", part="statistics,snippet", id=",".join(chs[i:i + 50]))["items"]: C[it["id"]] = it
    today = datetime.date.today().isoformat(); n = 0
    for k, v in V.items():
        ch = C.get(v["snippet"]["channelId"])
        if not ch: continue
        subs = int(ch["statistics"].get("subscriberCount", 0) or 0); views = int(v["statistics"].get("viewCount", 0))
        sec = sum(int(a) * {"H": 3600, "M": 60, "S": 1}[u] for a, u in re.findall(r"(\d+)([HMS])", v["contentDetails"]["duration"]))
        t = v["snippet"]["title"]
        c.execute("insert or replace into niche values(?,?,?,?,?,?,?,?,?,?)", (k, today, ch["snippet"]["title"], t, v["snippet"]["publishedAt"][:10], sec, views, subs,
                                                                           views / max(subs, 100), int(bool(re.search(r"[ыэъё]", t.lower())))))
        n += 1
    c.commit(); print("niche +", n)


COMP_Q = NICHE_Q + ["нейромережі українською", "ChatGPT для початківців", "ШІ новини", "AI українською", "штучний інтелект для бізнесу",
          "Midjourney українською", "ШІ для SMM", "автоматизація ШІ", "ШІ для програмістів", "Claude Code", "Cursor AI", "AI news this week",
          "AI explained", "ChatGPT vs Gemini", "AI automation", "n8n AI agent", "prompt engineering", "AI productivity tools", "AI shorts", "AI video generator"]


def lang_of(title):
    t = title.lower()
    if re.search(r"[ыэъё]", t): return "ru"
    if re.search(r"[іїєґ]", t): return "uk"
    if re.search(r"[а-я]", t): return "cyr"
    return "en"


def competitors(target=500, per_q=50):
    """Збирає й оновлює ≥500 каналів ніші: статистика каналу (знімок на дату) + останні 15 відео кожного. Квота: пошук 100/запит."""
    import yt
    c = db(); today = datetime.date.today().isoformat()
    have = {r[0] for r in c.execute("select distinct channel_id from comp")}
    new = set()
    nv = [r[0] for r in c.execute("select distinct video_id from niche")]
    for i in range(0, len(nv), 50):  # канали з уже зібраної ніші — 1 од. квоти на 50 відео
        for v in yt.api("videos", part="snippet", id=",".join(nv[i:i + 50]))["items"]: new.add(v["snippet"]["channelId"])
    print("канали з ніші:", len(have | new))
    for q in COMP_Q:
        if len(have | new) >= target: break
        en = q.isascii(); tok = None
        for _ in range(2):
            try:
                r = yt.api("search", part="snippet", q=q, type="channel" if _ else "video", maxResults=per_q,
                           **({} if en else {"relevanceLanguage": "uk", "regionCode": "UA"}))
            except Exception as e:
                print("quota/err", q, e); target = 0; break
            for it in r["items"]:
                new.add(it["snippet"]["channelId"])
    ids = list(have | new); n = 0
    for i in range(0, len(ids), 50):
        for ch in yt.api("channels", part="statistics,snippet,contentDetails", id=",".join(ids[i:i + 50]))["items"]:
            st = ch["statistics"]; sn = ch["snippet"]
            c.execute("insert or replace into comp values(?,?,?,?,?,?,?,?)", (ch["id"], today, sn["title"], int(st.get("subscriberCount", 0) or 0),
                      int(st.get("viewCount", 0) or 0), int(st.get("videoCount", 0) or 0), sn.get("country", ""), lang_of(sn["title"] + " " + sn.get("description", "")[:200])))
            up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
            try:
                vids = [x["contentDetails"]["videoId"] for x in yt.api("playlistItems", part="contentDetails", playlistId=up, maxResults=15)["items"]]
            except Exception:
                vids = []
            if vids:
                for v in yt.api("videos", part="snippet,statistics,contentDetails", id=",".join(vids))["items"]:
                    sec = sum(int(a) * {"H": 3600, "M": 60, "S": 1}[u] for a, u in re.findall(r"(\d+)([HMS])", v["contentDetails"].get("duration", "PT0S")))
                    stt = v["statistics"]
                    c.execute("insert or replace into comp_videos values(?,?,?,?,?,?,?,?,?)", (v["id"], ch["id"], v["snippet"]["title"], v["snippet"]["publishedAt"][:10], sec,
                              int(stt.get("viewCount", 0)), int(stt.get("likeCount", 0) or 0), int(stt.get("commentCount", 0) or 0), today))
            n += 1
        c.commit()
    print("ШІ-каналів (≥30% відео про ШІ):", ai_share(c))
    print(f"comp: {n} каналів оновлено, {c.execute('select count(*) from comp_videos').fetchone()[0]} відео конкурентів")


AI_RX = r"(ші|ai|штучн|нейро|gpt|chatgpt|claude|клод|gemini|джеміні|midjourney|промпт|prompt|llm|агент|agent|автоматиз|вайбкод|vibe ?cod|cursor|codex|copilot|n8n|openai|anthropic|deepseek|grok)"


def ai_share(c):
    """Частка відео каналу про ШІ → таблиця comp_ai (канал вважаємо конкурентом, якщо ≥30%)."""
    c.execute("drop table if exists comp_ai")
    c.execute("create table comp_ai(channel_id text primary key, ai_share real, n int)")
    rx = re.compile(AI_RX, re.I)
    by = {}
    for ch, t in c.execute("select channel_id,title from comp_videos"):
        a = by.setdefault(ch, [0, 0]); a[1] += 1; a[0] += bool(rx.search(t))
    for ch, (k, n) in by.items(): c.execute("insert into comp_ai values(?,?,?)", (ch, k / n, n))
    c.commit()
    return sum(1 for k, n in by.values() if k / n >= 0.3)


def ask(q):
    c = db(); like = f"%{q.lower()}%"
    print(f"== Наші ролики про «{q}» (перегляди за 7 днів / % перегляду)")
    try:
        import analytics_db
        for vid, t, f in c.execute("select id,title,format from videos where ul(title) like ?", (like,)):
            v, p, s = analytics_db.first7(c, vid); print(f"  {v:6} {p:5.1f}% {f:7} {t[:80]}")
    except Exception as e: print("  ", e)
    print("== Статті сайту")
    for r in c.execute("select date,slug,words from posts where ul(title) like ? or ul(slug) like ? order by date desc limit 8", (like, like)): print("  ", *r)
    print("== Пошук Google (запити з показами)")
    for r in c.execute("select query,impressions,clicks,round(position,1) from site_queries where ul(query) like ? order by impressions desc limit 8", (like,)): print("  ", *r)
    print("== Радари (теми, оцінка, план)")
    for r in c.execute("select date,score,title,plan from research where ul(title) like ? or ul(plan) like ? order by date desc limit 8", (like, like)): print("  ", r[0], f"{r[1]}/10", r[2][:70], "→", r[3][:50])
    print("== Ніша (чужі відео, views/subs)")
    for r in c.execute("select round(max(ratio),1),max(views),channel,title from niche where ul(title) like ? and ru=0 group by video_id order by max(ratio) desc limit 8", (like,)): print("  ", f"{r[0]}x", r[1], r[2][:20], "|", r[3][:70])


def stats():
    c = db()
    for t in ("videos", "daily", "traffic", "niche", "comp", "comp_videos", "research", "posts", "site_daily", "site_queries", "site_pages"):
        print(f"{t:14}", c.execute(f"select count(*) from {t}").fetchone()[0])


if __name__ == "__main__":
    a = sys.argv[1:] or ["stats"]
    if a[0] == "ingest":
        c = db(); ingest_research(c); ingest_posts(c)
        try: ingest_site(c)
        except Exception as e: print("site ERR", e)
        c.commit(); stats()
    elif a[0] == "niche": niche()
    elif a[0] == "comp": competitors(int(a[1]) if len(a) > 1 else 500)
    elif a[0] == "ask": ask(" ".join(a[1:]))
    elif a[0] == "sql":
        for r in db().execute(a[1]): print(*r)
    else: stats()
