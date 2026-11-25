#!/usr/bin/env python3
"""Даталейк ШІкарно — довідник для агентів (власник 22.11: «великий даталейк на різних дослідженнях… щоб агенти могли на основі чогось приймати рішення»).

Одна база studio/data/analytics.sqlite. Таблиці:
  videos, daily, traffic, snap       — наш YouTube (analytics_db.py sync)
  niche                              — чужі відео ніші (outliers.py; + `lake.py niche` — ширші UA/EN запити)
  research                           — усі теми з радарів docs/research/radar-*.md (дата, назва, оцінка, формат, джерела [V]/[S])
  site_daily, site_queries, site_pages — Search Console (покази, кліки, позиції)
  site_queries_weekly                — запити Search Console по ISO-тижнях (останні 8 тижнів; week = '2026-W47')
  traffic_daily, channel_daily, tg_daily — історія по днях (analytics_db.py sync)
  posts                              — усі статті сайту (slug, дата, kind, теги, youtube, слів)

usage:
  python3 studio/yt/lake.py ingest              # research + posts + Search Console (+ niche за потреби окремо)
  python3 studio/yt/lake.py niche               # ширша ніша: UA + англомовні ШІ-запити (квота ~2000 од.)
  python3 studio/yt/lake.py comp [500]         # ≥500 каналів-конкурентів: знімок статистики + останні 15 відео (щотижня)
  python3 studio/yt/lake.py news                # новини: ~22 RSS (компанії, світові й UA ШІ-медіа), Anthropic, HN (ШІ), dou → news (кожні 4 год)
  python3 studio/yt/lake.py history [365]        # усі відео ШІ-конкурентів за рік (≈1 од. квоти на 50 відео)
  python3 studio/yt/lake.py snapshot             # знімок живої бази в studio/data/snapshot/ + studio/data/ops_dump.sql (комітити обидва раз на добу)
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
    c.execute("pragma busy_timeout=10000")
    c.executescript("""
    create table if not exists research(date text, n int, title text, score int, plan text, sources text, verified int, file text, primary key(date,n,file));
    create table if not exists posts(slug text primary key, date text, kind text, title text, tags text, youtube text, words int);
    create table if not exists site_daily(date text primary key, clicks int, impressions int, ctr real, position real);
    create table if not exists site_queries(query text, period text, clicks int, impressions int, ctr real, position real, primary key(query,period));
    create table if not exists site_pages(page text, period text, clicks int, impressions int, ctr real, position real, primary key(page,period));
    create table if not exists site_queries_weekly(week text, query text, clicks int, impressions int, ctr real, position real, primary key(week,query));
    create table if not exists traffic_daily(video_id text, date text, source text, views int, primary key(video_id,date,source));
    create table if not exists channel_daily(date text primary key, views int, watch_min real, subs_gained int, subs_lost int, avg_pct real, long_watch_min real, short_views int);
    create table if not exists tg_daily(date text primary key, members int);
    create table if not exists comp(channel_id text, date text, title text, subs int, views int, videos int, country text, lang text, primary key(channel_id,date));
    create table if not exists comp_videos(video_id text primary key, channel_id text, title text, published text, duration_s int, views int, likes int, comments int, fetched text);
    create table if not exists news(url text primary key, source text, published text, title text, score int, fetched text);
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
    # тижнева динаміка: ISO-тижні (пн–нд), останні 8; поточний неповний тиждень теж оновлюється
    last = datetime.date.fromisoformat(end); mon = last - datetime.timedelta(days=last.weekday())
    for k in range(8):
        ws = mon - datetime.timedelta(weeks=k); we = min(ws + datetime.timedelta(days=6), last)
        y, w, _ = ws.isocalendar(); wk = f"{y}-W{w:02d}"
        for r in gsc({"startDate": ws.isoformat(), "endDate": we.isoformat(), "dimensions": ["query"], "rowLimit": 1000}):
            c.execute("insert or replace into site_queries_weekly values(?,?,?,?,?,?)", (wk, r["keys"][0], r["clicks"], r["impressions"], r["ctr"], r["position"]))
    print("site_queries_weekly:", c.execute("select count(*) from site_queries_weekly").fetchone()[0], "рядків")
    print("site:", c.execute("select count(*) from site_daily").fetchone()[0], "днів,", c.execute("select count(*) from site_queries").fetchone()[0], "запитів")


NICHE_Q = ["штучний інтелект", "ChatGPT українською", "нейромережі", "Gemini", "Claude", "ШІ для бізнесу", "ШІ для роботи", "ШІ для вчителя",
           "ШІ безкоштовно", "нейромережа для фото", "ШІ агенти", "вайбкодинг", "промпти ChatGPT", "ШІ для студента", "як заробити на ШІ",
           "AI tools tier list", "ChatGPT tips", "Claude AI tutorial", "Gemini AI tips", "AI for teachers", "AI side hustle", "best AI tools 2026"]


def niche(days=60):
    import yt
    c = db(); after = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z"); vids = set()
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


def competitors(target=500, per_q=50, max_search=30):
    """Збирає й оновлює ≥500 каналів ніші: статистика каналу (знімок на дату) + останні 15 відео кожного. Квота: пошук 100/запит."""
    import yt
    c = db(); today = datetime.date.today().isoformat()
    have = {r[0] for r in c.execute("select distinct channel_id from comp")}
    new = set()
    nv = [r[0] for r in c.execute("select distinct video_id from niche")]
    for i in range(0, len(nv), 50):  # канали з уже зібраної ніші — 1 од. квоти на 50 відео
        for v in yt.api("videos", part="snippet", id=",".join(nv[i:i + 50]))["items"]: new.add(v["snippet"]["channelId"])
    print("канали з ніші:", len(have | new))
    done_q = 0
    for q in COMP_Q:
        if len(have | new) >= target or done_q >= max_search: break
        done_q += 2
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


# RSS/Atom-стрічки (перевірені живим запитом 22.11.2026). ключ → (URL, фільтр AI_RX для загальних стрічок)
FEEDS = {
    # першоджерела
    "openai": ("https://openai.com/news/rss.xml", False),
    "google": ("https://blog.google/technology/ai/rss/", False),
    "gemini": ("https://blog.google/products/gemini/rss/", False),
    "deepmind": ("https://deepmind.google/blog/rss.xml", False),
    "microsoft": ("https://www.microsoft.com/en-us/ai/blog/feed/", False),
    "msnews": ("https://news.microsoft.com/source/topics/ai/feed/", False),
    "meta": ("https://about.fb.com/news/feed/", True),
    "metaeng": ("https://engineering.fb.com/feed/", True),
    "hf": ("https://huggingface.co/blog/feed.xml", False),
    "nvidia": ("https://blogs.nvidia.com/feed/", True),
    "mistral": ("https://mistral.ai/rss.xml", False),
    "apple": ("https://www.apple.com/newsroom/rss-feed.rss", True),
    # світові ШІ-медіа
    "techcrunch": ("https://techcrunch.com/category/artificial-intelligence/feed/", False),
    "verge": ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", False),
    "venturebeat": ("https://feeds.feedburner.com/venturebeat/SZYF", False),
    "ars": ("https://arstechnica.com/ai/feed/", False),
    "mittr": ("https://www.technologyreview.com/topic/artificial-intelligence/feed", False),
    "wired": ("https://www.wired.com/feed/tag/ai/latest/rss", False),
    # українські tech-медіа (загальні стрічки → фільтр AI_RX)
    "ain": ("https://ain.ua/feed/", True),
    "devua": ("https://dev.ua/rss", True),
    "speka": ("https://speka.media/rss", True),
    "liga": ("https://tech.liga.net/ua/all/rss.xml", True),
}
FEED_MAX = 30   # ≤30 записів з одного джерела за прогін


def feed_items(xml):
    """RSS <item> / Atom <entry> → [(url, title, YYYY-MM-DD)]."""
    import xml.etree.ElementTree as ET, email.utils
    A = "{http://www.w3.org/2005/Atom}"; out = []
    root = ET.fromstring(xml)
    for it in root.iter():
        tag = it.tag
        if tag == "item":
            title = it.findtext("title") or ""; link = (it.findtext("link") or "").strip()
            if not link:
                g = it.find("guid"); link = (g.text or "").strip() if g is not None and (g.text or "").startswith("http") else ""
            raw = it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date") or ""
        elif tag == A + "entry":
            title = it.findtext(A + "title") or ""
            ls = it.findall(A + "link"); l = next((x for x in ls if x.get("rel", "alternate") == "alternate"), ls[0] if ls else None)
            link = (l.get("href") or "").strip() if l is not None else ""
            raw = it.findtext(A + "published") or it.findtext(A + "updated") or ""
        else: continue
        raw = raw.strip(); pub = ""
        if re.match(r"\d{4}-\d{2}-\d{2}", raw): pub = raw[:10]
        elif raw:
            try: pub = email.utils.parsedate_to_datetime(raw).strftime("%Y-%m-%d")
            except Exception: pub = ""
        if link and title.strip(): out.append((link, re.sub(r"\s+", " ", title).strip(), pub))
    return out


def anthropic_dates(c, get, limit=25):
    """Дата anthropic.com/news/* — лише на сторінці статті (article:published_time / datePublished); ≤limit запитів."""
    rows = c.execute("select url from news where source='anthropic' and (published is null or published='') order by fetched desc limit ?", (limit,)).fetchall()
    for (u,) in rows:
        try:
            m = re.search(r'(?:article:published_time" content="|"datePublished":")(\d{4}-\d{2}-\d{2})|<time dateTime="(\d{4}-\d{2}-\d{2})', get(u))
            if m: c.execute("update news set published=? where url=?", (m.group(1) or m.group(2), u))
        except Exception as e: print("anthropic date ERR", u, e)
    return len(rows)


def news():
    """Новини з першоджерел і обговорень → таблиця news (накопичується; дублікати за URL відкидаються)."""
    import html as H
    c = db(); today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"); n = 0
    def get(u):
        return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 shikarno-lake"}), timeout=20).read().decode("utf-8", "ignore")
    rx_ai = re.compile(r"(?<!\w)" + AI_RX, re.I); per = {}
    # COO 25.11 (data-quality): 10 пар «та сама назва, різні URL» (blog.google ↔ deepmind.google, gpt-4 ↔ gpt-4-research) → дублі ідей.
    # Дедуп у збирачі, не в базі: нова URL з уже відомою нормалізованою назвою (за 30 днів) не записується.
    norm = lambda t: re.sub(r"\W+", " ", (t or "").lower()).strip()
    seen = {norm(r[0]) for r in c.execute("select title from news where fetched >= date('now','-30 day')")}
    def dup(ti):
        k = norm(ti)
        if len(k) >= 12 and k in seen: return True
        seen.add(k); return False
    for src, (u, filt) in FEEDS.items():
        try:
            k = 0
            for link, ti, pub in feed_items(get(u)):
                if k >= FEED_MAX: break
                ti = H.unescape(ti)
                if filt and not rx_ai.search(ti): continue
                if c.execute("select 1 from news where url=?", (link,)).fetchone() is None and dup(ti): continue
                k += 1; per[src] = per.get(src, 0) + c.execute("insert or ignore into news values(?,?,?,?,?,?)", (link, src, pub, ti, None, today)).rowcount
        except Exception as e: print("feed ERR", src, str(e)[:120])
    n += sum(per.values()); print("rss нових:", ", ".join(f"{k} {v}" for k, v in sorted(per.items(), key=lambda x: -x[1])) or "0")
    try:
        t = get("https://www.anthropic.com/news")
        for path in dict.fromkeys(re.findall(r'href="(/news/[a-z0-9-]+)"', t)):
            if path.split("/")[-1] in ("announcements", "features", "partnerships", "product", "policy", "safeguards", "security"): continue
            n += c.execute("insert or ignore into news values(?,?,?,?,?,?)", ("https://www.anthropic.com" + path, "anthropic", "", path.split("/")[-1].replace("-", " "), None, today)).rowcount
    except Exception as e: print("anthropic ERR", e)
    anthropic_dates(c, get, 25)
    try:
        ids = json.loads(get("https://hacker-news.firebaseio.com/v0/topstories.json"))[:80]; rx = re.compile(AI_RX, re.I)
        for i in ids:
            h = json.loads(get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json"))
            if h and h.get("url") and rx.search(" " + h.get("title", "") + " "):
                c.execute("insert into news values(?,?,?,?,?,?) on conflict(url) do update set score=excluded.score", (h["url"], "hn", datetime.datetime.fromtimestamp(h["time"], datetime.timezone.utc).strftime("%Y-%m-%d"), h["title"], h.get("score"), today)); n += 1
    except Exception as e: print("hn ERR", e)
    try:
        t = get("https://dou.ua/lenta/news/")
        for u2, ti in re.findall(r'<h2[^>]*>\s*<a href="(https://dou.ua/lenta/[^"]+)"[^>]*>(.*?)</a>', t, re.S):
            n += c.execute("insert or ignore into news values(?,?,?,?,?,?)", (u2, "dou", today[:10], H.unescape(re.sub(r"<.*?>|\s+", " ", ti)).strip(), None, today)).rowcount
    except Exception as e: print("dou ERR", e)
    c.commit(); print("news +", n, "| всього", c.execute("select count(*) from news").fetchone()[0])


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


def history(days=365, min_share=0.3):
    """Повна історія конкурентів: усі відео ШІ-каналів за `days` днів (uploads playlist → videos). Квота ~1 од. на 50 відео."""
    import yt
    c = db(); since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat(); today = datetime.date.today().isoformat()
    chans = [r[0] for r in c.execute("select a.channel_id from comp_ai a where a.ai_share>=? order by a.channel_id", (min_share,))]
    total = 0
    for k, ch in enumerate(chans):
        try:
            up = yt.api("channels", part="contentDetails", id=ch)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except Exception as e:
            print("ERR", ch, e); continue
        tok = None; ids = []
        while True:
            q = dict(part="contentDetails", playlistId=up, maxResults=50)
            if tok: q["pageToken"] = tok
            try: r = yt.api("playlistItems", **q)
            except Exception as e: print("ERR pl", ch, e); break
            items = r["items"]; ids += [i["contentDetails"]["videoId"] for i in items if i["contentDetails"].get("videoPublishedAt", "9")[:10] >= since]
            tok = r.get("nextPageToken")
            if not tok or not items or items[-1]["contentDetails"].get("videoPublishedAt", "9")[:10] < since: break
        for i in range(0, len(ids), 50):
            for v in yt.api("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))["items"]:
                sec = sum(int(a) * {"H": 3600, "M": 60, "S": 1}[u] for a, u in re.findall(r"(\d+)([HMS])", v["contentDetails"].get("duration", "PT0S")))
                st = v["statistics"]
                c.execute("insert or replace into comp_videos values(?,?,?,?,?,?,?,?,?)", (v["id"], ch, v["snippet"]["title"], v["snippet"]["publishedAt"][:10], sec,
                          int(st.get("viewCount", 0)), int(st.get("likeCount", 0) or 0), int(st.get("commentCount", 0) or 0), today))
        total += len(ids); c.commit()
        if k % 20 == 0: print(f"{k+1}/{len(chans)} каналів, +{total} відео", flush=True)
    print(f"history: {len(chans)} каналів, {total} відео за {days} днів; всього comp_videos {c.execute('select count(*) from comp_videos').fetchone()[0]}")


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
    print("== Новини (першоджерела, HN, dou)")
    for r in c.execute("select published,source,score,title from news where ul(title) like ? order by published desc limit 8", (like,)): print("  ", *r)
    print("== Ніша (чужі відео, views/subs)")
    for r in c.execute("select round(max(ratio),1),max(views),channel,title from niche where ul(title) like ? and ru=0 group by video_id order by max(ratio) desc limit 8", (like,)): print("  ", f"{r[0]}x", r[1], r[2][:20], "|", r[3][:70])


def stats():
    c = db()
    for t in ("videos", "daily", "traffic", "traffic_daily", "channel_daily", "tg_daily", "site_queries_weekly", "news", "niche", "comp", "comp_videos", "research", "posts", "site_daily", "site_queries", "site_pages"):
        print(f"{t:14}", c.execute(f"select count(*) from {t}").fetchone()[0])


if __name__ == "__main__":
    a = sys.argv[1:] or ["stats"]
    if a[0] == "ingest":
        c = db(); ingest_research(c); ingest_posts(c)
        try: ingest_site(c)
        except Exception as e: print("site ERR", e)
        c.commit(); stats()
    elif a[0] == "niche": niche()
    elif a[0] == "snapshot":  # жива база не в git (її постійно пишуть збирачі); у git — щоденний знімок
        import shutil; src = sqlite3.connect(DB); dst = sqlite3.connect(os.path.join(ROOT, "studio", "data", "snapshot", "analytics.sqlite")); src.backup(dst); dst.close(); print("snapshot OK")
        # 25.11: ops.sqlite теж поза git → текстовий дамп studio/data/ops_dump.sql комітиться разом зі знімком
        try:
            sys.path.insert(0, os.path.join(ROOT, "studio")); import ops
            if os.path.exists(ops.DB_PATH): print("ops dump OK", ops.dump())
        except Exception as e: print("ops dump ERR", e)
    elif a[0] == "news": news()
    elif a[0] == "history": history(int(a[1]) if len(a) > 1 else 365)
    elif a[0] == "comp": competitors(int(a[1]) if len(a) > 1 else 500)
    elif a[0] == "ask": ask(" ".join(a[1:]))
    elif a[0] == "sql":
        for r in db().execute(a[1]): print(*r)
    else: stats()
