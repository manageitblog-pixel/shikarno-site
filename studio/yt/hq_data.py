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
  dict(id="coo", name="Директор студії (COO)", dept="exec", emoji="C", role="Конвеєр без пропусків, впровадження оргструктури, ескалації, вечірній звіт власнику", schedule="щодня 09:27 і 20:27", kpi="0 пропущених слотів"),
  dict(id="cso", name="Директор зі стратегії (CSO)", dept="exec", emoji="S", role="Ціль STAR (YPP до 31.01), портфель ставок, критерії зупинки, тижневий огляд", schedule="щопонеділка 11:19", kpi="прогноз ±30% до факту"),
  dict(id="eic", name="Головний редактор (Editor-in-Chief)", dept="exec", emoji="E", role="Що, куди й коли: рішення по дошці ідей, тижнева сітка", schedule="щодня 08:43", kpi="≥7 схвалених ідей наперед"),
  dict(id="shorts", name="Сценарист Shorts (Shorts Scriptwriter)", dept="editorial", emoji="W", role="Тір-листи й професії під пошукові запити; відповідь у перші 2 с", schedule="щодня до 12:00", kpi="% перегляду ≥60"),
  dict(id="longs", name="Шоуранер (Long-form Writer / Showrunner)", dept="editorial", emoji="L", role="Шоу «ШІ за тиждень» (нд 14:00) і гайди 18–22 хв (ср 19:00)", schedule="пн, чт–пт", kpi="2+ довгих/тиждень"),
  dict(id="factcheck", name="Фактчекер (Fact-checker)", dept="qa", emoji="F", role="Кожне твердження ↔ першоджерело; без PASS — назад автору", schedule="перед озвучкою", kpi="0 фактів без джерела"),
  dict(id="qa", name="QA-інженер контенту (Content QA Engineer)", dept="qa", emoji="Q", role="Голос F0, звірка ASR, кадри, finalize PASS", schedule="після рендеру", kpi="0 вад після виходу"),
  dict(id="lp", name="Лінійний продюсер (Line Producer)", dept="production", emoji="P", role="Черга queue.json, зворотний відлік, бюджет озвучки й рендеру, ескалації", schedule="щодня 09:30 і 16:00", kpi="100% слотів у строк"),
  dict(id="post", name="Продюсер постпродакшну (Post-production Producer)", dept="production", emoji="V", role="Озвучка Байта, рендер, обкладинка, заливка, finalize", schedule="за чергою", kpi="0 FAIL"),
  dict(id="clip", name="Кліп-редактор (Clip Editor)", dept="production", emoji="K", role="2–3 вертикальні нарізки з кожного довгого з посиланням на довгий", schedule="у день виходу довгого", kpi="≥2 нарізки на довгий"),
  dict(id="designer", name="Дизайнер упаковки (Motion & Packaging Designer)", dept="design", emoji="G", role="Кадр 0, обкладинки v4, графіка; ср — ресерч стилю конкурентів і 1 A/B", schedule="щодня 15:07, ср ресерч", kpi="0 вад; 1 A/B на тиждень"),
  dict(id="trend", name="Дослідник трендів (Trend Researcher)", dept="research", emoji="R", role="Першоджерела, HN, DOU, аномалії й конкуренти → ідеї на дошку", schedule="щодня 08:43; пн конкуренти", kpi="≥5 ідей/день з першоджерелом"),
  dict(id="de", name="Інженер даних (Data Engineer)", dept="research", emoji="D", role="Даталейк: новини, YouTube, сайт, ніша, 500 конкурентів; оновлення HQ", schedule="кожні 4 год", kpi="HQ свіжіший за 4 год"),
  dict(id="da", name="Аналітик даних (Data Analyst)", dept="research", emoji="A", role="Формати, % перегляду, аудит прогнозів (бал ідеї vs факт), тижневий звіт", schedule="щоранку + нд 11:13", kpi="точність прогнозу"),
  dict(id="seo", name="SEO-спеціаліст (SEO Specialist)", dept="growth", emoji="O", role="Ключові слова, назви й теги, сторінки-гайди сайту під Search Console", schedule="щодня 12:13", kpi="топ-3 у Google; кліки ×5"),
  dict(id="cm", name="Комʼюніті-менеджер (Community Manager)", dept="growth", emoji="M", role="Telegram і коментарі: промпт дня, воронки, модерація, експеримент тижня", schedule="щодня 08:41 + кожні 4 год", kpi="TG 6 → 150 до 31.01"),
  dict(id="dist", name="Менеджер дистрибуції (Distribution Manager)", dept="dist", emoji="T", role="TikTok через vidIQ, плейлисти, пов'язане відео, кінцеві заставки", schedule="у час виходу", kpi="100% Shorts у TikTok"),
  dict(id="ea", name="Асистент власника (Executive Assistant)", dept="exec", emoji="B", role="Повідомлення власника → задачі й рішення; щогодинна перевірка", schedule="щогодини :49 + вотчер", kpi="відповідь < 1 год"),
]
DEPTS = [
  dict(id="exec", name="Керівництво", color="#FFD60A"), dict(id="editorial", name="Редакція", color="#FF4F8B"),
  dict(id="qa", name="Контроль якості", color="#7DF29B"), dict(id="production", name="Продакшн", color="#7C5CFF"),
  dict(id="design", name="Дизайн", color="#FF8FD8"), dict(id="research", name="Дослідження та аналітика", color="#4CF2FF"),
  dict(id="growth", name="Зростання (Growth)", color="#FFA94D"), dict(id="dist", name="Дистрибуція", color="#C792FF"),
]
SCHEDULE = [  # (Київ, що, агент)
  ("щогодини :49", "Асистент власника: перевірка бота", "ea"), ("кожні 4 год :52", "Інженер даних: даталейк і HQ", "de"),
  ("08:41", "Комʼюніті-менеджер: промпт дня в TG", "cm"), ("08:43", "Дослідник трендів + Головний редактор: радар і рішення", "eic"),
  ("09:27", "Директор студії: стан конвеєра", "coo"), ("09:30", "Лінійний продюсер: черга дня", "lp"),
  ("10:37 пн", "Дослідник трендів: конкуренти", "trend"), ("11:19 пн", "Директор зі стратегії: тижневий огляд STAR", "cso"),
  ("11:23 сб/пн", "Шоуранер: шоу (сб) і гайд (пн)", "longs"), ("12:13", "SEO-спеціаліст", "seo"),
  ("14:00 нд", "Шоу «ШІ за тиждень»", "longs"), ("15:07", "Дизайнер: кадр 0 і обкладинка дня", "designer"),
  ("16:00", "Лінійний продюсер: зворотний відлік", "lp"), ("19:00", "Short дня + TikTok + стаття + TG", "shorts"),
  ("20:27", "Директор студії: звіт власнику", "coo"),
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
