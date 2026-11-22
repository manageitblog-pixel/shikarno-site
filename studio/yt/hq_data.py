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
AGENTS = [
  dict(id="editor", name="Головний редактор", dept="board", emoji="E", role="Оркестратор: план дня, рішення по темах, контроль, звіт власнику", schedule="щодня, постійно", kpi="усі слоти виконані"),
  dict(id="radar", name="Ресерчер новин", dept="research", emoji="R", role="Першоджерела (OpenAI, Google, Anthropic, DeepMind), HN, DOU — радар щоранку", schedule="щодня 08:43", kpi="≥5 тем з першоджерел"),
  dict(id="search", name="Ресерчер пошуку", dept="research", emoji="S", role="Що шукають: підказки YouTube (kw.py), Search Console сайту", schedule="у радарі + SEO", kpi="попит для кожної ідеї"),
  dict(id="niche", name="Ресерчер ніші", dept="research", emoji="N", role="Аномалії й конкуренти: outliers, 500 ШІ-каналів, що вистрілює", schedule="щодня + пн аналіз", kpi="500 конкурентів у базі"),
  dict(id="collector", name="Агент-збирач", dept="data", emoji="D", role="Наповнює даталейк: новини, YouTube, сайт, ніша, конкуренти; знімок бази", schedule="кожні 4 год", kpi="база росте щодня"),
  dict(id="analyst", name="Аналітик", dept="data", emoji="A", role="Медіани форматів, % перегляду, тижневий цикл росту", schedule="щоранку + нд", kpi="сер. % перегляду ≥60"),
  dict(id="shorts", name="Сценарист Shorts", dept="production", emoji="W", role="Тір-листи й професії під пошукові запити", schedule="щодня до 17Z", kpi="1 Short/день"),
  dict(id="longs", name="Сценарист довгих", dept="production", emoji="L", role="Шоу «ШІ за тиждень» (нд 14:00), гайд (ср 19:00)", schedule="сб + пн", kpi="2 довгих/тиждень"),
  dict(id="studio", name="Продакшн", dept="production", emoji="P", role="Озвучка Байта, рендер, обкладинки, заливка, finalize", schedule="за чергою", kpi="0 FAIL"),
  dict(id="factcheck", name="Фактчекер", dept="qa", emoji="F", role="Кожне твердження ↔ першоджерело; не пройшло — назад автору", schedule="перед озвучкою", kpi="0 неперевірених фактів"),
  dict(id="qa", name="QA відео", dept="qa", emoji="Q", role="Кадри, голос (F0), субтитри, обкладинка, finalize PASS", schedule="після рендеру", kpi="PASS на кожному"),
  dict(id="seo", name="SEO-відділ", dept="seo", emoji="K", role="Ключові слова, назви й теги, 1 сторінка сайту на день", schedule="щодня 12:13", kpi="кліки з Google ↑"),
  dict(id="tg", name="Telegram-відділ", dept="tg", emoji="T", role="Ріст каналу: промпт дня, воронки, експеримент тижня, модерація", schedule="щодня 08:41", kpi="6 → 150 учасників"),
  dict(id="tiktok", name="Дистрибуція", dept="dist", emoji="V", role="TikTok через vidIQ, згодом Instagram", schedule="разом з YouTube", kpi="кожен Short у TikTok"),
  dict(id="bot", name="Черговий бота", dept="board", emoji="B", role="Повідомлення власника, щогодинна перевірка", schedule="кожну годину + вотчер", kpi="відповідь < 1 год"),
]
DEPTS = [
  dict(id="board", name="Редколегія", color="#FFD60A"), dict(id="research", name="Дослідження", color="#4CF2FF"),
  dict(id="data", name="Даталейк", color="#7C5CFF"), dict(id="production", name="Виробництво", color="#FF4F8B"),
  dict(id="qa", name="Контроль якості", color="#7DF29B"), dict(id="seo", name="SEO", color="#FFA94D"),
  dict(id="tg", name="Telegram", color="#5AB2FF"), dict(id="dist", name="Дистрибуція", color="#C792FF"),
]
SCHEDULE = [  # (Київ, що, агент)
  ("щогодини :49", "Перевірка бота", "bot"), ("кожні 4 год :52", "Агент-збирач даталейку", "collector"),
  ("08:41", "Telegram-відділ: промпт дня", "tg"), ("08:43", "Радар і редколегія", "radar"),
  ("10:37 пн", "Конкуренти: тижневий аналіз", "niche"), ("11:23 сб/пн", "Довгі: шоу (сб) і гайд (пн)", "longs"),
  ("12:13", "SEO-відділ", "seo"), ("14:00 нд", "Шоу «ШІ за тиждень»", "longs"),
  ("19:00", "Short дня + TikTok + стаття + TG", "studio"), ("11:13 нд", "Цикл росту і звіт власнику", "analyst"),
]


def main():
    c = sqlite3.connect(DB); c.create_function("ul", 1, lambda x: (x or "").lower())
    import analytics_db
    today = datetime.date.today()
    q = lambda s, *a: c.execute(s, a).fetchall()
    # KPI
    subs = None
    try:
        sys.path.insert(0, "/home/claude/yt"); import yt
        st = yt.api("channels", part="statistics", mine="true")["items"][0]["statistics"]; subs = int(st["subscriberCount"]); views_total = int(st["viewCount"])
    except Exception:
        views_total = None
    last7 = q("select sum(views), sum(views*avg_pct)/max(sum(views),1), sum(subs) from daily where date >= ?", (today - datetime.timedelta(days=9)).isoformat())[0]
    days = q("select date, sum(views), sum(views*avg_pct)/max(sum(views),1) from daily where date >= ? group by date order by date", (today - datetime.timedelta(days=40)).isoformat())
    site = q("select date, clicks, impressions, position from site_daily order by date")
    tg_members = None
    try:
        sys.path.insert(0, "/home/claude/tg"); import tg
        tg_members = tg.call("getChatMemberCount", chat_id=tg.CH).get("result")
    except Exception:
        pass
    # формати (7 днів, медіана)
    fm = {}
    cutoff = (today - datetime.timedelta(days=9)).isoformat()
    for vid, f, sh, pub in q("select id, format, short, published from videos"):
        if pub[:10] > cutoff: continue
        v, p, s = analytics_db.first7(c, vid); fm.setdefault(("Short · " if sh else "Довгий · ") + f, []).append((v, p))
    formats = sorted([dict(name=k, n=len(x), views=statistics.median(a for a, _ in x), pct=round(statistics.median(b for _, b in x), 1)) for k, x in fm.items()], key=lambda r: -r["views"])
    # відео
    vids = []
    for vid, t, f, sh, pub in q("select id, title, format, short, published from videos order by published desc limit 14"):
        v, p, s = analytics_db.first7(c, vid)
        snap = q("select views_public from snap where video_id=? order by date desc limit 1", vid)
        vids.append(dict(id=vid, title=t.replace(" #ШІ #shorts", "").replace(" #shorts", ""), format=f, short=bool(sh), published=pub[:10], views7=v, pct=round(p, 1), total=snap[0][0] if snap else None))
    ideas = json.load(open(os.path.join(ROOT, "studio", "data", "ideas.json"))) if os.path.exists(os.path.join(ROOT, "studio", "data", "ideas.json")) else []
    try:
        import ideas as I; P = I.priors()
        for i in ideas: i["score"] = I.score(i, P)
    except Exception:
        pass
    ideas.sort(key=lambda i: -(i.get("score") or 0))
    lake = {t: q(f"select count(*) from {t}")[0][0] for t in ("videos", "daily", "news", "niche", "comp", "comp_videos", "research", "posts", "site_queries")}
    lake["comp_ai"] = q("select count(*) from comp_ai where ai_share>=0.3")[0][0]
    news = [dict(date=d, source=s, title=t, score=sc, url=u) for u, s, d, t, sc in q("select url, source, published, title, score from news where source in ('openai','google','deepmind','anthropic','hn','dou') order by published desc, fetched desc limit 12")]
    comp_top = [dict(channel=t, subs=s, lang=l, avg=int(a)) for t, s, l, a in q("select c.title, c.subs, c.lang, avg(v.views) from comp c join comp_ai a using(channel_id) join comp_videos v on v.channel_id=c.channel_id where a.ai_share>=0.3 and c.lang in ('uk','en') and v.published>=? group by c.channel_id order by avg(v.views) desc limit 10", (today - datetime.timedelta(days=90)).isoformat())]
    tt = json.load(open(os.path.join(ROOT, "studio", "eps", "tiktok.json"))).get("posted_auto", {})
    data = dict(
        generated=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        kpi=dict(subs=subs, subs_goal=1000, long_hours=10.1, long_hours_goal=4000, views_total=views_total, views_7d=last7[0], pct_7d=round(last7[1] or 0, 1), subs_7d=last7[2],
                 tg=tg_members, tg_goal=150, site_clicks_28d=sum(r[1] for r in site[-28:]), site_impr_28d=sum(r[2] for r in site[-28:]), tiktok_auto=len(tt)),
        days=[dict(d=d, v=v, p=round(p or 0, 1)) for d, v, p in days], site=[dict(d=d, c=cl, i=im, pos=round(po, 1)) for d, cl, im, po in site],
        formats=formats, videos=vids, ideas=ideas[:12], lake=lake, news=news, competitors=comp_top,
        agents=AGENTS, depts=DEPTS, schedule=[dict(time=a, what=b, agent=c_) for a, b, c_ in SCHEDULE],
        asks=[dict(what="Дозвіл vidIQ у .claude/settings.json (TikTok без підтверджень)", status="чекає власника"),
              dict(what="Підключити Instagram (бізнес/автор-акаунт) через vidIQ", status="чекає власника"),
              dict(what="Скріни переглядів TikTok за тиждень", status="чекає власника")],
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("hq data OK:", OUT, len(json.dumps(data)) // 1024, "KB")


if __name__ == "__main__":
    main()
