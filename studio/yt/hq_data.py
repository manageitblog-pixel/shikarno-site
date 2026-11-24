#!/usr/bin/env python3
"""Дані для студії «ШІкарно HQ» (власник 22.11: «дашборд і студія, де бігають усі агенти, задачі, ідеї… я як CEO спостерігаю»).
Збирає знімок з даталейку (studio/data/analytics.sqlite), дошки ідей і RUNBOOK-розкладу → studio/hq/data.json.
Запуск: python3 studio/yt/hq_data.py   (агент-збирач запускає кожні 4 год і перепубліковує data.json в артефакт)."""
import os, sys, json, sqlite3, datetime, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
DB = os.path.join(ROOT, "studio", "data", "analytics.sqlite")
OUT = os.path.join(ROOT, "studio", "hq", "data.json")

# Відділи й агенти студії (docs/agents-farm.md). schedule — київський час; next рахує сторінка.
AGENTS = [  # оргструктура v3 (погоджено власником 22.11, docs/org/org-design-2026-11-22.md)
  dict(id="coo", name="Директор студії (COO)", dept="exec", emoji="C", role="Думає за студію: ≥3 власні ініціативи за запуск, конвеєр без пропусків, вечірній звіт власнику; Диспетчер пулу агентів", schedule="09:27 і 20:27; Диспетчер щогодини :17", kpi="0 пропущених слотів"),
  dict(id="cso", name="Директор зі стратегії (CSO)", dept="exec", emoji="S", role="Ціль STAR (YPP до 31.01), портфель ставок, критерії зупинки, тижневий огляд", schedule="щодня 11:19 (пн — глибоко)", kpi="темп до YPP по 4 платформах"),
  dict(id="algo", name="Дослідник алгоритмів платформ (Platform Intelligence)", dept="research", emoji="A", role="Зміни алгоритмів YouTube/TikTok/Google/Telegram з першоджерел, плейбуки, експерименти, пропозиція дня", schedule="щодня 14:13", kpi="плейбуки свіжі ≤7 днів; ≥1 експеримент у роботі"),
  dict(id="eic", name="Головний редактор (Editor-in-Chief)", dept="exec", emoji="E", role="Що, куди й коли: рішення по дошці ідей, тижнева сітка", schedule="щодня 08:43", kpi="≥7 схвалених ідей наперед"),
  dict(id="shorts", name="Сценарист Shorts (Shorts Scriptwriter)", dept="editorial", emoji="W", role="Тір-листи й професії під пошукові запити; відповідь у перші 2 с", schedule="за чергою Диспетчера; вихід щодня 19:00", kpi="% перегляду ≥60"),
  dict(id="longs", name="Шоуранер (Long-form Writer / Showrunner)", dept="editorial", emoji="L", role="Шоу «ШІ за тиждень» (нд 14:00) і гайди 18–22 хв (ср 19:00)", schedule="пн/сб 09:23 (гайд/шоу); вихід ср 19:00 і нд 14:00", kpi="2+ довгих/тиждень"),
  dict(id="factcheck", name="Фактчекер (Fact-checker)", dept="qa", emoji="F", role="Кожне твердження ↔ першоджерело; без PASS — назад автору", schedule="перед озвучкою", kpi="0 фактів без джерела"),
  dict(id="qa", name="QA-інженер контенту (Content QA Engineer)", dept="qa", emoji="Q", role="Голос F0, звірка ASR, кадри, finalize PASS", schedule="після рендеру", kpi="0 вад після виходу"),
  dict(id="lp", name="Лінійний продюсер (Line Producer)", dept="production", emoji="P", role="Черга queue.json, зворотний відлік, бюджет озвучки й рендеру, ескалації", schedule="за чергою Диспетчера (окремої задачі в розкладі немає)", kpi="100% слотів у строк"),
  dict(id="post", name="Продюсер постпродакшну (Post-production Producer)", dept="production", emoji="V", role="Озвучка Байта, рендер, обкладинка, заливка, finalize", schedule="за чергою", kpi="0 FAIL"),
  dict(id="clip", name="Кліп-редактор (Clip Editor)", dept="production", emoji="K", role="2–3 вертикальні нарізки з кожного довгого з посиланням на довгий", schedule="у день виходу довгого", kpi="≥2 нарізки на довгий"),
  dict(id="designer", name="Дизайнер упаковки (Motion & Packaging Designer)", dept="design", emoji="G", role="Кадр 0, обкладинки v4, графіка; ср — ресерч стилю конкурентів і 1 A/B", schedule="щодня 15:07, ср ресерч", kpi="0 вад; 1 A/B на тиждень"),
  dict(id="trend", name="Дослідник трендів (Trend Researcher)", dept="research", emoji="R", role="Першоджерела, HN, DOU, аномалії й конкуренти → ідеї на дошку", schedule="08:43 радар; пн 10:37 конкуренти; фонові скани", kpi="≥5 ідей/день з першоджерелом"),
  dict(id="de", name="Інженер даних (Data Engineer)", dept="research", emoji="D", role="Даталейк: новини, YouTube, сайт, ніша, 500 конкурентів; оновлення HQ", schedule="кожні 4 год :52 (02:52, 06:52 … Київ)", kpi="HQ свіжіший за 4 год"),
  dict(id="da", name="Аналітик даних (Data Analyst)", dept="research", emoji="A", role="Формати, % перегляду, аудит прогнозів (бал ідеї vs факт), тижневий звіт", schedule="за чергою + нд 11:13 цикл росту", kpi="точність прогнозу"),
  dict(id="seo", name="SEO-спеціаліст (SEO Specialist)", dept="growth", emoji="O", role="Ключові слова, назви й теги, сторінки-гайди сайту під Search Console", schedule="щодня 12:13", kpi="топ-3 у Google; кліки ×5"),
  dict(id="cm", name="Комʼюніті-менеджер (Community Manager)", dept="growth", emoji="M", role="Telegram і коментарі: промпт дня, воронки, модерація, експеримент тижня", schedule="щодня 08:41 + за чергою Диспетчера", kpi="TG 6 → 150 до 31.01"),
  dict(id="dist", name="Менеджер дистрибуції (Distribution Manager)", dept="dist", emoji="T", role="TikTok через vidIQ, плейлисти, пов'язане відео, кінцеві заставки", schedule="у час виходу", kpi="100% Shorts у TikTok"),
  dict(id="ea", name="Асистент власника (Executive Assistant)", dept="exec", emoji="B", role="Повідомлення власника → задачі й рішення; щогодинна перевірка", schedule="щогодини :06 + вотчер бота", kpi="відповідь < 1 год"),
]
DEPTS = [
  dict(id="exec", name="Керівництво", color="#FFD60A"), dict(id="editorial", name="Редакція", color="#FF4F8B"),
  dict(id="qa", name="Контроль якості", color="#7DF29B"), dict(id="production", name="Продакшн", color="#7C5CFF"),
  dict(id="design", name="Дизайн", color="#FF8FD8"), dict(id="research", name="Дослідження та аналітика", color="#4CF2FF"),
  dict(id="growth", name="Зростання (Growth)", color="#FFA94D"), dict(id="dist", name="Дистрибуція", color="#C792FF"),
]
# Реальний розклад (звірено з list_triggers 24.11; час — Київ). Час виходу роликів — це publish_at у YouTube, не запуск агента.
SCHEDULE = [  # (Київ, що, агент)
  ("щогодини :06", "Асистент власника: перевірка бота, відкладені статті, оновлення HQ", "ea"),
  ("щогодини :17", "Диспетчер: пул 5 агентів, самоперевірка, оновлення HQ", "coo"),
  ("кожні 4 год :52", "Інженер даних: даталейк, TikTok/TG-знімок, HQ (02:52, 06:52, 10:52, 14:52, 18:52, 22:52)", "de"),
  ("08:41", "Комʼюніті-менеджер: Telegram-відділ (метрика, пост дня, воронки)", "cm"),
  ("08:43", "Ранкова редакція: аналітика, радар, редколегія, автоаудит", "eic"),
  ("09:23 пн/сб", "Шоуранер: гайд (пн) і шоу «ШІ за тиждень» (сб)", "longs"),
  ("09:27", "Директор студії: стан конвеєра й ініціативи", "coo"),
  ("10:37 пн", "Дослідник трендів: конкуренти (спершу українські)", "trend"),
  ("11:13 нд", "Аналітик даних: тижневий цикл росту", "da"),
  ("11:19", "Директор зі стратегії: трекер YPP (пн — глибоко)", "cso"),
  ("12:13", "SEO-спеціаліст: ключові слова, YouTube-SEO, сторінки сайту", "seo"),
  ("14:00 нд", "Вихід шоу «ШІ за тиждень» (YouTube)", "longs"),
  ("14:13", "Дослідник алгоритмів платформ: зміни, лайфхаки, експерименти", "algo"),
  ("15:07", "Дизайнер: кадр 0 і обкладинка дня (ср — ресерч стилю)", "designer"),
  ("15:00 за планом", "Вихід кліпу-воронки (YouTube Short з довгого) + TikTok", "clip"),
  ("15:23 і 19:23", "Менеджер дистрибуції: Instagram Reels — дзеркало кліпу й Short дня", "dist"),
  ("19:00", "Вихід Short дня (YouTube) + TikTok + стаття + TG", "dist"),
  ("19:00 ср", "Вихід гайду (довге відео)", "longs"),
  ("20:27", "Директор студії: вечірній звіт власнику", "coo"),
]
# Старі/неточні agent_id у журналі activity.json → реальні ролі з AGENTS (інакше офіс не бачить, хто працює)
ALIASES = {"editor": "shorts", "voice": "post", "production": "post", "design": "designer", "analyst": "da",
           "niche": "trend", "dispatcher": "coo", "writer": "shorts", "showrunner": "longs", "data": "de",
           "community": "cm", "tg": "cm", "distribution": "dist", "algorithms": "algo", "research": "trend",
           "instagram": "dist", "ig": "dist"}
ASKS = os.path.join(ROOT, "studio", "hq", "asks.json")
TG_CACHE = os.path.expanduser("~/.cache/shikarno_tg_public.json") if os.access(os.path.expanduser("~"), os.W_OK) else "/tmp/shikarno_tg_public.json"
TG_PUBLIC = "https://t.me/s/shikarno_ai_ua"


def now_utc(): return datetime.datetime.now(datetime.timezone.utc)
def iso(dt): return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def tg_public(max_age_min=15):
    """Публічна сторінка каналу t.me/s/… : дати й перегляди постів (без токена). Кеш 15 хв, таймаут 10 с.
    Повертає dict(fetched, posts=[{id, date, views, text}], subscribers) або кеш/None з error."""
    import re, html, urllib.request
    cache = None
    try: cache = json.load(open(TG_CACHE))
    except Exception: pass
    if cache and (now_utc() - datetime.datetime.fromisoformat(cache["fetched"].replace("Z", "+00:00"))).total_seconds() < max_age_min * 60:
        return cache
    def views(v):
        v = v.strip().upper(); m = 1
        if v.endswith("K"): m, v = 1000, v[:-1]
        elif v.endswith("M"): m, v = 1000000, v[:-1]
        try: return int(float(v) * m)
        except ValueError: return None
    posts, subs, before = {}, None, None
    try:
        for _ in range(4):  # ≤4 сторінки по ~20 постів — вистачає на 7+ днів
            url = TG_PUBLIC + (f"?before={before}" if before else "")
            h = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (HQ dashboard)"}), timeout=10).read().decode("utf-8", "replace")
            if subs is None:
                m = re.search(r'counter_value">([^<]+)</span> <span class="counter_type">subscribers', h)
                subs = views(m.group(1)) if m else None
            blocks = re.split(r'(?=<div class="tgme_widget_message_wrap)', h)[1:]
            ids = []
            for b in blocks:
                m = re.search(r'data-post="shikarno_ai_ua/(\d+)"', b); d = re.search(r'<time datetime="([^"]+)" class="time"', b) or re.search(r'tgme_widget_message_date.*?<time datetime="([^"]+)"', b, re.S)
                if not m or not d: continue
                v = re.search(r'tgme_widget_message_views">([^<]+)<', b)
                t = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', b, re.S)
                txt = html.unescape(re.sub(r"<[^>]+>", " ", t.group(1))) if t else ("відео" if "video_player" in b else "медіа")
                pid = int(m.group(1)); ids.append(pid)
                posts[pid] = dict(id=pid, date=datetime.datetime.fromisoformat(d.group(1)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                  views=views(v.group(1)) if v else None, text=re.sub(r"\s+", " ", txt).strip()[:140])
            if not ids: break
            oldest = min(posts.values(), key=lambda p: p["id"])
            if oldest["date"] < iso(now_utc() - datetime.timedelta(days=8)): break
            before = min(ids)
        if not posts: raise RuntimeError("на сторінці не знайдено постів")
        res = dict(fetched=iso(now_utc()), subscribers=subs, posts=sorted(posts.values(), key=lambda p: p["id"]))
        try:
            os.makedirs(os.path.dirname(TG_CACHE), exist_ok=True); json.dump(res, open(TG_CACHE, "w"), ensure_ascii=False)
        except Exception: pass
        return res
    except Exception as e:
        if cache: cache = dict(cache); cache["error"] = f"кеш: t.me не відповів ({type(e).__name__})"; return cache
        return dict(fetched=None, posts=[], subscribers=None, error=f"немає даних: t.me не відповів ({type(e).__name__})")


CF_CACHE = os.path.expanduser("~/.cache/shikarno_cf.json") if os.access(os.path.expanduser("~"), os.W_OK) else "/tmp/shikarno_cf.json"
CF_GQL = "https://api.cloudflare.com/client/v4/graphql"


def cf_live(max_age_min=10):
    """Cloudflare Web Analytics (RUM) наживо: перегляди сторінок (pageloads) і візити сайту.
    Ключ читання підставляє проксі середовища (у запиті — заглушка), Account ID — config.SITE["cf_account"].
    Дні — київські (00:00–24:00 Europe/Kyiv). Кожен день — окремий аліас із вузьким фільтром: широкий діапазон
    Cloudflare семплює (×10), а вузький віддає точні числа; дні старші ~9 діб CF уже зберігає семпльовано — позначаємо sampled.
    Кеш 10 хв (~/.cache/shikarno_cf.json), таймаут 10 с; при помилці — кеш з позначкою або dict(error="немає даних …")."""
    import urllib.request
    from zoneinfo import ZoneInfo
    cache = None
    try: cache = json.load(open(CF_CACHE))
    except Exception: pass
    if cache and cache.get("updated") and (now_utc() - datetime.datetime.fromisoformat(cache["updated"].replace("Z", "+00:00"))).total_seconds() < max_age_min * 60:
        return cache
    try:
        sys.path.insert(0, ROOT); import config
        acct = config.SITE.get("cf_account")
        if not acct: raise RuntimeError("немає cf_account у config.py")
        KY = ZoneInfo("Europe/Kyiv"); now = now_utc(); today = now.astimezone(KY).date()
        def kb(d):  # межі київського дня в UTC
            a = datetime.datetime.combine(d, datetime.time(), KY).astimezone(datetime.timezone.utc)
            b = datetime.datetime.combine(d + datetime.timedelta(days=1), datetime.time(), KY).astimezone(datetime.timezone.utc)
            return iso(a), iso(b)
        G = "rumPageloadEventsAdaptiveGroups"; parts = []
        days = [today - datetime.timedelta(days=i) for i in range(13, -1, -1)]
        for i, d in enumerate(days):
            a, b = kb(d)
            parts.append(f'd{i}: {G}(limit:1, filter:{{datetime_geq:"{a}", datetime_lt:"{b}"}}) {{ count sum {{ visits }} confidence(level:0.95) {{ count {{ sampleSize }} }} }}')
        h0 = iso((now - datetime.timedelta(hours=23)).replace(minute=0, second=0, microsecond=0)); w7 = kb(today - datetime.timedelta(days=6))[0]
        parts.append(f'h: {G}(limit:100, filter:{{datetime_geq:"{h0}"}}, orderBy:[datetimeHour_ASC]) {{ count sum {{ visits }} dimensions {{ datetimeHour }} }}')
        for k, dim in (("p", "requestPath"), ("r", "refererHost"), ("c", "countryName")):
            parts.append(f'{k}: {G}(limit:{6 if k == "r" else 5}, filter:{{datetime_geq:"{w7}"}}, orderBy:[count_DESC]) {{ count dimensions {{ {dim} }} }}')
        parts.append(f't: {G}(limit:1, filter:{{datetime_geq:"{w7}"}}) {{ count sum {{ visits }} }}')
        query = '{ viewer { accounts(filter:{accountTag:"%s"}) { %s } } }' % (acct, "\n".join(parts))
        req = urllib.request.Request(CF_GQL, data=json.dumps({"query": query}).encode(),
                                     headers={"Authorization": "Bearer proxy-injected", "Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=10))
        if r.get("errors"): raise RuntimeError(str(r["errors"][0].get("message", "помилка GraphQL"))[:160])
        A = r["data"]["viewer"]["accounts"][0]
        dl = []
        for i, d in enumerate(days):
            g = A[f"d{i}"][0] if A[f"d{i}"] else None
            n = g["count"] if g else 0; ss = g["confidence"]["count"]["sampleSize"] if g else 0
            dl.append(dict(d=d.isoformat(), pageloads=n, visits=(g["sum"]["visits"] if g else 0), sampled=bool(g and ss < n)))
        # погодинно за останні 24 год (з нулями для годин без переглядів)
        hm = {x["dimensions"]["datetimeHour"]: x for x in A["h"]}; hours = []
        t0 = datetime.datetime.fromisoformat(h0.replace("Z", "+00:00"))
        for i in range(24):
            k = iso(t0 + datetime.timedelta(hours=i)); x = hm.get(k)
            hours.append(dict(h=k, pageloads=x["count"] if x else 0, visits=x["sum"]["visits"] if x else 0))
        ref = lambda h: h or "(прямі / без реферера)"
        t7 = A["t"][0] if A["t"] else {"count": 0, "sum": {"visits": 0}}
        res = dict(updated=iso(now), source="Cloudflare Web Analytics", tz="Europe/Kyiv",
                   today_pageloads=dl[-1]["pageloads"], today_visits=dl[-1]["visits"],
                   yesterday_pageloads=dl[-2]["pageloads"], yesterday_visits=dl[-2]["visits"],
                   pageloads_7d=t7["count"], visits_7d=t7["sum"]["visits"],
                   last24h=dict(pageloads=sum(h["pageloads"] for h in hours), visits=sum(h["visits"] for h in hours), hours=hours),
                   days=dl,
                   top_pages_7d=[dict(path=x["dimensions"]["requestPath"], count=x["count"]) for x in A["p"]][:5],
                   top_referrers_7d=[dict(host=ref(x["dimensions"]["refererHost"]), count=x["count"]) for x in A["r"] if x["dimensions"]["refererHost"] != "shikarno.com.ua"][:5],
                   top_countries_7d=[dict(country=x["dimensions"]["countryName"], count=x["count"]) for x in A["c"]][:5])
        try:
            os.makedirs(os.path.dirname(CF_CACHE), exist_ok=True); json.dump(res, open(CF_CACHE, "w"), ensure_ascii=False)
        except Exception: pass
        return res
    except Exception as e:
        why = str(e)[:120] if isinstance(e, RuntimeError) else type(e).__name__
        if cache: cache = dict(cache); cache["error"] = f"кеш: Cloudflare не відповів ({why})"; return cache
        return dict(updated=None, error=f"немає даних: Cloudflare не відповів ({why})")


def cf_store(c, live):
    """Денні рядки (київські дні) у site_rum_daily — щоб історія накопичувалась і за межами вікна CF."""
    if not live or not live.get("days") or live.get("error"): return
    c.execute("create table if not exists site_rum_daily(date text primary key, pageloads int, visits int, sampled int default 0, updated text)")
    # точний день (sampled=0) ніколи не затираємо оцінкою CF (за ~9 днів CF віддає старі дні семпльованими ×10)
    c.executemany("""insert into site_rum_daily(date, pageloads, visits, sampled, updated) values(?,?,?,?,?)
                     on conflict(date) do update set pageloads=excluded.pageloads, visits=excluded.visits,
                       sampled=excluded.sampled, updated=excluded.updated
                     where excluded.sampled=0 or site_rum_daily.sampled=1""",
                  [(d["d"], d["pageloads"], d["visits"], int(d.get("sampled", False)), live["updated"]) for d in live["days"]])
    c.commit()


def yt_live():
    """YouTube Data API наживо: статистика каналу (1 од.) + 15 останніх завантажень з переглядами (2 од.)."""
    sys.path.insert(0, "/home/claude/yt"); import yt
    ch = yt.api("channels", part="statistics,contentDetails", mine="true")["items"][0]
    st = ch["statistics"]; out = dict(at=iso(now_utc()), subs=int(st["subscriberCount"]), views=int(st["viewCount"]), videos=int(st["videoCount"]), recent=[])
    try:
        up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        ids = [i["contentDetails"]["videoId"] for i in yt.api("playlistItems", part="contentDetails", playlistId=up, maxResults=20)["items"]]
        vs = yt.api("videos", part="snippet,statistics,status,contentDetails", id=",".join(ids))["items"]
        for v in vs:
            s = v["status"]; pub = v["snippet"].get("publishedAt", "")
            if s.get("privacyStatus") != "public": continue
            out["recent"].append(dict(id=v["id"], title=v["snippet"]["title"], published=pub, views=int(v["statistics"].get("viewCount", 0)),
                                      likes=int(v["statistics"].get("likeCount", 0)), dur=v["contentDetails"].get("duration", "")))
        out["recent"].sort(key=lambda r: r["published"], reverse=True)
    except Exception as e:
        out["recent_error"] = type(e).__name__
    return out


def main():
    c = sqlite3.connect(DB); c.create_function("ul", 1, lambda x: (x or "").lower())
    import analytics_db
    today = datetime.date.today(); gen = now_utc()
    q = lambda s, *a: c.execute(s, a).fetchall()
    fresh, notes = {}, []  # fresh: джерело → час/дата, станом на які показані дані (для підписів на сторінці)

    # --- YouTube наживо (Data API) ---
    live = None
    try: live = yt_live(); fresh["yt_live"] = live["at"]
    except Exception as e: notes.append(f"YouTube Data API недоступний ({type(e).__name__}) — живих лічильників немає")
    subs = live["subs"] if live else None; views_total = live["views"] if live else None

    # --- YouTube Analytics (запізнюється на 2–3 дні): вікно = 7 днів, що закінчуються останнім днем з даними ---
    ya_last = (q("select max(date) from daily")[0][0] or today.isoformat())[:10]
    ch_last = (q("select max(date) from channel_daily")[0][0] or ya_last)[:10]
    fresh["yt_analytics"] = min(ya_last, ch_last)
    w0 = (datetime.date.fromisoformat(ya_last) - datetime.timedelta(days=6)).isoformat()
    last7 = q("select sum(views), sum(views*avg_pct)/nullif(sum(case when avg_pct is not null then views end),0), sum(subs) from daily where date between ? and ?", w0, ya_last)[0]
    ch7 = q("select sum(views), sum(subs_gained)-sum(subs_lost) from channel_daily where date between ? and ?", w0, ch_last)[0]
    days = q("select date, sum(views), sum(views*avg_pct)/nullif(sum(case when avg_pct is not null then views end),0) from daily where date >= ? group by date order by date", (today - datetime.timedelta(days=40)).isoformat())
    site = q("select date, clicks, impressions, position from site_daily order by date")
    def wk(d): x = datetime.date.fromisoformat(d[:10]); return (x - datetime.timedelta(days=x.weekday())).isoformat()
    H = {}
    for d, v, wm, sg, sl, lw, sv in q("select date, views, watch_min, subs_gained, subs_lost, long_watch_min, short_views from channel_daily order by date"):
        h = H.setdefault(wk(d), dict(w=wk(d), views=0, subs=0, long_h=0.0, short_views=0, clicks=0, impr=0))
        h["views"] += v or 0; h["subs"] += (sg or 0) - (sl or 0); h["long_h"] += (lw or 0) / 60; h["short_views"] += sv or 0
    for d, cl, im, _ in site:
        h = H.setdefault(wk(d), dict(w=wk(d), views=0, subs=0, long_h=0.0, short_views=0, clicks=0, impr=0)); h["clicks"] += cl or 0; h["impr"] += im or 0
    hist = sorted(H.values(), key=lambda h: h["w"]); cs = ch = 0
    site_last = site[-1][0][:10] if site else None
    for h in hist:
        end = (datetime.date.fromisoformat(h["w"]) + datetime.timedelta(days=6)).isoformat()
        h["partial"] = end > ch_last; h["partial_site"] = bool(site_last and end > site_last)
    for h in hist: cs += h["subs"]; ch += h["long_h"]; h["subs_cum"] = cs; h["long_cum"] = round(ch, 1); h["long_h"] = round(h["long_h"], 1)
    # підписники загалом на кінець тижня: живе число мінус приріст після цього тижня (а не «+161 з початку обліку» поруч із 315)
    if subs is not None:
        for h in hist: h["subs_total"] = subs - (cs - h["subs_cum"])
    long_hours = None
    try: long_hours = analytics_db.long_hours_12m()
    except Exception: long_hours = round(ch, 1)

    # --- Telegram: учасники (Bot API → tg_daily) + пости з публічної сторінки t.me/s ---
    tg_hist = [dict(d=d, n=n) for d, n in q("select date, members from tg_daily order by date")]
    tg_members = None
    try:
        sys.path.insert(0, "/home/claude/tg"); import tg
        tg_members = tg.call("getChatMemberCount", chat_id=tg.CH).get("result"); fresh["tg_members"] = iso(now_utc())
    except Exception:
        if tg_hist: fresh["tg_members"] = tg_hist[-1]["d"]
    tp = tg_public()
    if tp.get("fetched"): fresh["tg_posts"] = tp["fetched"]
    c7 = iso(gen - datetime.timedelta(days=7))
    p7 = [p for p in tp.get("posts", []) if p["date"] >= c7]
    v7 = [p["views"] for p in p7 if p["views"] is not None]

    # --- формати: медіана перших 7 днів по роликах, для яких 7 днів уже є в Analytics ---
    fm = {}
    cutoff = (datetime.date.fromisoformat(ya_last) - datetime.timedelta(days=6)).isoformat()
    for vid, f, sh, pub in q("select id, format, short, published from videos"):
        if pub[:10] > cutoff: continue
        v, p, s_ = analytics_db.first7(c, vid); fm.setdefault(("Short · " if sh else "Довгий · ") + f, []).append((v, p))
    formats = sorted([dict(name=k, n=len(x), views=statistics.median(a for a, _ in x), pct=round(statistics.median(b for _, b in x), 1)) for k, x in fm.items()], key=lambda r: -r["views"])

    # --- відео: список і «всього» — наживо з Data API; «перші 7 днів» — з Analytics, якщо вже є ---
    meta = {vid: (t, f, sh, pub) for vid, t, f, sh, pub in q("select id, title, format, short, published from videos")}
    def clean(t): return t.replace(" #ШІ #shorts", "").replace(" #shorts", "")
    vids = []
    src = live["recent"][:14] if live and live.get("recent") else [dict(id=k, title=m[0], published=m[3], views=None) for k, m in sorted(meta.items(), key=lambda kv: kv[1][3], reverse=True)[:14]]
    for r in src:
        m = meta.get(r["id"]); pub = (r.get("published") or (m[3] if m else ""))[:10]
        v = p = None; complete = False
        if m:
            v, p, _ = analytics_db.first7(c, r["id"]); complete = (datetime.date.fromisoformat(pub) + datetime.timedelta(days=6)).isoformat() <= ya_last
            if pub > ya_last: v = p = None
        total = r.get("views")
        if total is None:
            snap = q("select views_public from snap where video_id=? order by date desc limit 1", r["id"]); total = snap[0][0] if snap else None
        short = bool(m[2]) if m else ("#shorts" in r["title"].lower() or _short_dur(r.get("dur", "")))
        vids.append(dict(id=r["id"], title=clean(r["title"]), format=(m[1] if m else None), short=short, published=pub, views7=v, pct=(round(p, 1) if p else None), complete=complete, total=total))

    ideas = json.load(open(os.path.join(ROOT, "studio", "data", "ideas.json"))) if os.path.exists(os.path.join(ROOT, "studio", "data", "ideas.json")) else []
    try:
        import ideas as I; P = I.priors()
        for i in ideas: i["score"] = I.score(i, P)
    except Exception:
        pass
    ideas_open = [i for i in ideas if i.get("status") not in ("done", "rejected", "dropped")]
    ideas_open.sort(key=lambda i: -(i.get("score") or 0))
    fresh["ideas"] = iso(datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(ROOT, "studio", "data", "ideas.json")), datetime.timezone.utc)) if ideas else None
    lake = {t: q(f"select count(*) from {t}")[0][0] for t in ("videos", "daily", "news", "niche", "comp", "comp_videos", "research", "posts", "site_queries")}
    lake["comp"] = q("select count(distinct channel_id) from comp")[0][0]
    lake["comp_ai"] = q("select count(*) from comp_ai where ai_share>=0.3")[0][0]
    news = [dict(date=d, source=s, title=t, score=sc, url=u) for u, s, d, t, sc in q("select url, source, published, title, score from news where source in ('openai','google','gemini','deepmind','anthropic','microsoft','msnews','meta','metaeng','hf','nvidia','mistral','apple','techcrunch','verge','venturebeat','ars','mittr','wired','ain','devua','speka','liga','hn','dou') order by published desc, fetched desc limit 12")]
    nf = q("select max(fetched) from news")[0][0]; fresh["news"] = nf
    fresh["comp"] = q("select max(date) from comp")[0][0]
    def comp(lang, n):
        return [dict(channel=t, subs=s_, lang=l, avg=int(a), n=k) for t, s_, l, a, k in q("select c.title, c.subs, c.lang, avg(v.views), count(v.video_id) from (select * from comp where (channel_id, date) in (select channel_id, max(date) from comp group by channel_id)) c join comp_ai a using(channel_id) join comp_videos v on v.channel_id=c.channel_id where a.ai_share>=0.3 and c.lang=? and v.published>=? and c.title not like 'ШІкарно%' and c.title not like 'Google%' and c.title not like 'OpenAI%' and c.title not like 'Anthropic%' group by c.channel_id order by avg(v.views) desc limit ?", lang, (today - datetime.timedelta(days=90)).isoformat(), n)]
    comp_top = comp('uk', 10) + comp('en', 5)
    tt = json.load(open(os.path.join(ROOT, "studio", "eps", "tiktok.json"))).get("posted_auto", {})

    yt_p = dict(subs=subs, views_total=views_total, videos=live["videos"] if live else None, live_at=live["at"] if live else None,
                views_7d=last7[0], pct_7d=round(last7[1], 1) if last7[1] else None, subs_7d=ch7[1], window=[w0, ya_last], long_hours=long_hours,
                history=[dict(x=h["w"], v=h["views"], p=h["partial"]) for h in hist if h["w"] >= "2026-10-01"],
                best=[dict(title=v["title"], views=v["views7"], id=v["id"]) for v in sorted([v for v in vids if v["views7"]], key=lambda v: -v["views7"])[:3]],
                best_live=[dict(title=v["title"], views=v["total"], id=v["id"]) for v in sorted([v for v in vids if v["total"] is not None], key=lambda v: -v["total"])[:3]])

    # --- TikTok: сума по ВСІХ відомих відео (останній знімок кожного video_id), як у growth_snapshot.tiktok() ---
    tk = None
    try:
        rows = q("""select t.video_id, t.posted, t.title, t.views, t.likes, t.saves, t.shares, t.date from tiktok_snap t
            join (select video_id, max(date) d from tiktok_snap group by video_id) m on m.video_id=t.video_id and m.d=t.date order by t.views desc""")
    except sqlite3.OperationalError:
        rows = []
    if rows:
        tl = max(r[7] for r in rows); fresh["tiktok"] = tl
        c7t = (datetime.date.fromisoformat(tl[:10]) - datetime.timedelta(days=6)).isoformat()
        # історія: для кожного знімка — сума останніх відомих переглядів кожного відео на той момент (без «падінь» від випадіння старих)
        snaps = q("select date, video_id, views from tiktok_snap order by date"); known, th = {}, []
        for d in sorted({r[0] for r in snaps}):
            for dd, vid, v in snaps:
                if dd == d: known[vid] = v or 0
            th.append(dict(x=d, v=sum(known.values())))
        tk = dict(videos=len(rows), views_total=sum(r[3] or 0 for r in rows), views_7d=sum(r[3] or 0 for r in rows if (r[1] or "") >= c7t), new_7d=sum(1 for r in rows if (r[1] or "") >= c7t),
                  saves_total=sum(r[5] or 0 for r in rows), likes_total=sum(r[4] or 0 for r in rows), last_snapshot=tl,
                  best=[dict(title=r[2], views=r[3], saves=r[5], id=r[0], posted=r[1]) for r in rows[:3]], history=th)
    # --- Instagram (@shikarno_ai_ua, з 23.11): останній знімок кожного Reel з ig_snap + підписники з ig_account (instagram_ingest.py) ---
    ig = None
    try:
        irows = q("""select s.shortcode, s.published, s.plays, s.likes, s.saves, s.shares, s.avg_watched_pct, s.ts from ig_snap s
            join (select shortcode, max(ts) t from ig_snap group by shortcode) m on m.shortcode=s.shortcode and m.t=s.ts order by s.plays desc, s.avg_watched_pct desc""")
        iacc = q("select ts, followers, views_30d, reach_30d from ig_account order by ts")
    except sqlite3.OperationalError:
        irows, iacc = [], []
    if irows:
        il = max(r[7] for r in irows); fresh["instagram"] = il
        caps = {}
        try:  # підписи Reels беремо з останнього сирого знімка (у таблиці їх немає)
            import glob as _g, re as _re
            lastf = sorted(_g.glob(os.path.join(ROOT, "studio", "data", "instagram", "*.json")))[-1]
            for r in json.load(open(lastf, encoding="utf-8")).get("reels_response", {}).get("reels", []):
                caps[r["shortcode"]] = _re.split(r"[\U0001F000-\U0001FFFF☀-➿]", r.get("caption") or "")[0].strip()
        except Exception:
            pass
        a = iacc[-1] if iacc else (None, None, None, None)
        # mode=account знімається раз на добу, а 4-годинні знімки пишуть views/reach = NULL → беремо останнє відоме значення (COO 24.11: було «—»)
        acc = next((r for r in reversed(iacc) if r[2] is not None or r[3] is not None), None)
        if acc: a = (a[0], a[1], acc[2], acc[3])
        acc_at = (f"{acc[0][8:10]}.{acc[0][5:7]} {acc[0][11:13]}Z" if acc and len(acc[0]) >= 13 else None) if acc else None
        ihs = q("select ts, sum(plays) from ig_snap group by ts order by ts")
        ig = dict(ig_goal=100, ig_goal_note="до 1.12; далі 500 до 31.01 (поріг «Подарунків» — перевірити для України)", followers=a[1], views_30d=a[2], reach_30d=a[3], acc_at=acc_at, reels=len(irows), plays_total=sum(r[2] or 0 for r in irows),
                  likes_total=sum(r[3] or 0 for r in irows), saves_total=sum(r[4] or 0 for r in irows), last_snapshot=il,
                  best=[dict(shortcode=r[0], title=caps.get(r[0]) or r[0], plays=r[2], pct=(round(r[6]) if r[6] else None), published=(r[1] or "")[:10]) for r in irows[:3]],
                  history=[dict(x=t, v=v or 0) for t, v in ihs], followers_hist=[dict(x=t, v=f) for t, f, _, _ in iacc])
    weeks = [w for (w,) in q("select distinct week from site_queries_weekly order by week desc limit 4")]
    tq = q(f"select query, sum(clicks), sum(impressions), sum(position*impressions)/max(sum(impressions),1) from site_queries_weekly where week in ({','.join('?'*len(weeks))}) group by query order by sum(clicks) desc, sum(impressions) desc limit 5", *weeks) if weeks else []
    s28 = site[-28:]; ic = sum(r[2] or 0 for r in s28); cc = sum(r[1] or 0 for r in s28)
    fresh["site"] = site_last
    site_p = dict(impr_28d=ic, clicks_28d=cc, ctr=round(cc / ic * 100, 2) if ic else None, avg_pos=round(sum((r[3] or 0) * (r[2] or 0) for r in s28) / ic, 1) if ic else None,
                  last_day=site_last, first_day=s28[0][0][:10] if s28 else None, weeks=(weeks[-1] + "…" + weeks[0]) if weeks else None,
                  top_queries=[dict(q=a, clicks=b, impr=i_, pos=round(p_, 1)) for a, b, i_, p_ in tq],
                  history=[dict(x=h["w"], v=h["impr"], p=h["partial_site"]) for h in hist if h["w"] >= "2026-10-01"])
    members = tg_members if tg_members is not None else (tg_hist[-1]["n"] if tg_hist else tp.get("subscribers"))
    tg_p = dict(members=members, tg_goal=150, posts_7d=len(p7) if tp.get("fetched") or tp.get("posts") else None,
                views_7d=sum(v7) if v7 else None, views_avg=round(sum(v7) / len(v7), 1) if v7 else None, posts_error=tp.get("error"),
                best=[dict(id=p["id"], text=p["text"], views=p["views"], date=p["date"]) for p in sorted(p7, key=lambda p: -(p["views"] or 0))[:3]],
                history=[dict(x=t["d"], v=t["n"]) for t in tg_hist], since=tg_hist[0]["d"] if tg_hist else None)
    # --- Сайт наживо: Cloudflare Web Analytics (перегляди сторінок за сьогодні/вчора/14 днів) ---
    cf = cf_live()
    if cf.get("updated"): fresh["site_live"] = cf["updated"]
    if cf.get("error"): notes.append("Cloudflare: " + cf["error"])
    try: cf_store(c, cf)
    except Exception as e: notes.append(f"site_rum_daily не записано ({type(e).__name__})")
    site_p["live"] = cf
    platforms = dict(youtube=yt_p, tiktok=tk, instagram=ig, site=site_p, telegram=tg_p)

    # --- журнал агентів: аліаси → реальні ролі ---
    act = (json.load(open(os.path.join(ROOT, "studio", "hq", "activity.json"))) if os.path.exists(os.path.join(ROOT, "studio", "hq", "activity.json")) else {"items": []})["items"]
    ids = {a["id"] for a in AGENTS}; acts = []
    opened = [x for x in act if not x.get("finished")]
    for x in act[-40:] + [x for x in opened if x not in act[-40:]]:
        x = dict(x); raw = x.get("agent"); x["agent"] = ALIASES.get(raw, raw)
        if x["agent"] != raw: x["agent_raw"] = raw
        if x["agent"] not in ids: x["agent_raw"] = raw; x["agent"] = "coo"
        if x.get("result") and len(x["result"]) > 220: x["result"] = x["result"][:219] + "…"
        acts.append(x)
    if act: fresh["activity"] = max((x.get("finished") or x.get("started") or "") for x in act)

    try: asks = json.load(open(ASKS))
    except Exception: asks = {"items": [], "updated": None}
    asks_items = [a for a in asks.get("items", []) if a.get("status") != "done"]
    fresh["asks"] = asks.get("updated")

    data = dict(
        generated=iso(gen), fresh=fresh, notes=notes,
        kpi=dict(subs=subs, subs_goal=1000, long_hours=long_hours, long_hours_goal=4000, views_total=views_total, videos=yt_p["videos"],
                 views_7d=last7[0], pct_7d=yt_p["pct_7d"], subs_7d=ch7[1], window=[w0, ya_last],
                 tg=members, tg_goal=150, site_clicks_28d=cc, site_impr_28d=ic, tiktok_auto=len(tt)),
        days=[dict(d=d, v=v, p=round(p or 0, 1)) for d, v, p in days], site=[dict(d=d, c=cl, i=im, pos=round(po, 1)) for d, cl, im, po in site],
        history=hist, tg_hist=tg_hist, platforms=platforms, formats=formats, formats_cutoff=cutoff, videos=vids, ideas=ideas_open[:12],
        ideas_count=dict(total=len(ideas), open=len(ideas_open)), lake=lake, news=news, competitors=comp_top,
        activity=acts, agents=AGENTS, depts=DEPTS, schedule=[dict(time=a, what=b, agent=c_) for a, b, c_ in SCHEDULE], asks=asks_items,
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("hq data OK:", OUT, len(json.dumps(data)) // 1024, "KB", "· notes:", "; ".join(notes) or "—", "· tg:", tp.get("error") or "ok")


def _short_dur(d):
    import re
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m: return False
    h, mi, se = (int(x or 0) for x in m.groups()); return h * 3600 + mi * 60 + se <= 180


if __name__ == "__main__":
    main()
