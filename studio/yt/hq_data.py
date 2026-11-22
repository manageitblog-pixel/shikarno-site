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
  dict(id="coo", name="Директор студії (COO)", dept="exec", emoji="C", role="Думає за студію: ≥3 власні ініціативи за запуск, конвеєр без пропусків, вечірній звіт власнику", schedule="щодня 09:27 і 20:27", kpi="0 пропущених слотів"),
  dict(id="cso", name="Директор зі стратегії (CSO)", dept="exec", emoji="S", role="Ціль STAR (YPP до 31.01), портфель ставок, критерії зупинки, тижневий огляд", schedule="щодня 11:19 (пн — глибоко)", kpi="темп до YPP по 4 платформах"),
  dict(id="algo", name="Дослідник алгоритмів платформ (Platform Intelligence)", dept="research", emoji="A", role="Зміни алгоритмів YouTube/TikTok/Google/Telegram з першоджерел, плейбуки, експерименти, пропозиція дня", schedule="щодня 14:13", kpi="плейбуки свіжі ≤7 днів; ≥1 експеримент у роботі"),
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
  ("10:37 пн", "Дослідник трендів: конкуренти", "trend"), ("11:19", "Директор зі стратегії: трекер YPP (пн — глибоко)", "cso"), ("14:13", "Дослідник алгоритмів платформ", "algo"),
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
    # історія (власник 22.11: «там історичність результатів показуй») — по тижнях (пн), з channel_daily / site_daily / tg_daily
    def wk(d): x = datetime.date.fromisoformat(d[:10]); return (x - datetime.timedelta(days=x.weekday())).isoformat()
    H = {}
    for d, v, wm, sg, sl, lw, sv in q("select date, views, watch_min, subs_gained, subs_lost, long_watch_min, short_views from channel_daily order by date"):
        h = H.setdefault(wk(d), dict(w=wk(d), views=0, subs=0, long_h=0.0, short_views=0, clicks=0, impr=0))
        h["views"] += v or 0; h["subs"] += (sg or 0) - (sl or 0); h["long_h"] += (lw or 0) / 60; h["short_views"] += sv or 0
    for d, cl, im, _ in site:
        h = H.setdefault(wk(d), dict(w=wk(d), views=0, subs=0, long_h=0.0, short_views=0, clicks=0, impr=0)); h["clicks"] += cl or 0; h["impr"] += im or 0
    hist = sorted(H.values(), key=lambda h: h["w"]); cs = ch = 0
    last = (q("select max(date) from channel_daily")[0][0] or today.isoformat())[:10]
    for h in hist: h["partial"] = (datetime.date.fromisoformat(h["w"]) + datetime.timedelta(days=6)).isoformat() > last
    for h in hist: cs += h["subs"]; ch += h["long_h"]; h["subs_cum"] = cs; h["long_cum"] = round(ch, 1); h["long_h"] = round(h["long_h"], 1)
    tg_hist = [dict(d=d, n=n) for d, n in q("select date, members from tg_daily order by date")]
    long_hours = None
    try: long_hours = analytics_db.long_hours_12m()
    except Exception: long_hours = round(ch, 1)
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
    news = [dict(date=d, source=s, title=t, score=sc, url=u) for u, s, d, t, sc in q("select url, source, published, title, score from news where source in ('openai','google','gemini','deepmind','anthropic','microsoft','msnews','meta','metaeng','hf','nvidia','mistral','apple','techcrunch','verge','venturebeat','ars','mittr','wired','ain','devua','speka','liga','hn','dou') order by published desc, fetched desc limit 12")]
    # власник 22.11: «чому тільки англомовні? рідні аудиторії — українські» → окремо укр (головне) і англ (орієнтир)
    def comp(lang, n):
        return [dict(channel=t, subs=s_, lang=l, avg=int(a), n=k) for t, s_, l, a, k in q("select c.title, c.subs, c.lang, avg(v.views), count(v.video_id) from comp c join comp_ai a using(channel_id) join comp_videos v on v.channel_id=c.channel_id where a.ai_share>=0.3 and c.lang=? and v.published>=? and c.title not like 'ШІкарно%' and c.title not like 'Google%' and c.title not like 'OpenAI%' and c.title not like 'Anthropic%' group by c.channel_id order by avg(v.views) desc limit ?", lang, (today - datetime.timedelta(days=90)).isoformat(), n)]
    comp_top = comp('uk', 10) + comp('en', 5)
    tt = json.load(open(os.path.join(ROOT, "studio", "eps", "tiktok.json"))).get("posted_auto", {})
    # платформи (власник 22.11: «аналітика по TikTok, сайту і Telegram, а не тільки YouTube») — лише фактичні дані, без екстраполяцій
    yt_p = dict(subs=subs, views_7d=last7[0], long_hours=long_hours, history=[dict(x=h["w"], v=h["views"], p=h["partial"]) for h in hist if h["w"] >= "2026-10-01"],
                best=[dict(title=v["title"], views=v["views7"], id=v["id"]) for v in sorted(vids, key=lambda v: -(v["views7"] or 0))[:3]])
    tk = None
    try:
        tl = q("select max(date) from tiktok_snap")[0][0]
    except sqlite3.OperationalError:
        tl = None
    if tl:
        tv = q("select video_id, posted, title, views, likes, saves, shares from tiktok_snap where date=? order by views desc", tl)
        c7 = (datetime.date.fromisoformat(tl[:10]) - datetime.timedelta(days=6)).isoformat()
        tk = dict(videos=len(tv), views_total=sum(r[3] or 0 for r in tv), views_7d=sum(r[3] or 0 for r in tv if (r[1] or "") >= c7), new_7d=sum(1 for r in tv if (r[1] or "") >= c7),
                  saves_total=sum(r[5] or 0 for r in tv), likes_total=sum(r[4] or 0 for r in tv), last_snapshot=tl,
                  best=[dict(title=r[2], views=r[3], saves=r[5], id=r[0], posted=r[1]) for r in tv[:3]],
                  history=[dict(x=d, v=v) for d, v in q("select date, sum(views) from tiktok_snap group by date order by date")])
    weeks = [w for (w,) in q("select distinct week from site_queries_weekly order by week desc limit 4")]
    tq = q(f"select query, sum(clicks), sum(impressions), sum(position*impressions)/max(sum(impressions),1) from site_queries_weekly where week in ({','.join('?'*len(weeks))}) group by query order by sum(clicks) desc, sum(impressions) desc limit 5", *weeks) if weeks else []
    s28 = site[-28:]; ic = sum(r[2] or 0 for r in s28); cc = sum(r[1] or 0 for r in s28)
    site_p = dict(impr_28d=ic, clicks_28d=cc, ctr=round(cc / ic * 100, 2) if ic else None, avg_pos=round(sum((r[3] or 0) * (r[2] or 0) for r in s28) / ic, 1) if ic else None,
                  last_day=site[-1][0] if site else None, weeks=(weeks[-1] + "…" + weeks[0]) if weeks else None,
                  top_queries=[dict(q=a, clicks=b, impr=i_, pos=round(p_, 1)) for a, b, i_, p_ in tq],
                  history=[dict(x=h["w"], v=h["impr"], p=h["partial"]) for h in hist if h["w"] >= "2026-10-01"])
    tg_p = dict(members=tg_members if tg_members is not None else (tg_hist[-1]["n"] if tg_hist else None), tg_goal=150, posts_7d=None,
                history=[dict(x=t["d"], v=t["n"]) for t in tg_hist], since=tg_hist[0]["d"] if tg_hist else None)
    platforms = dict(youtube=yt_p, tiktok=tk, site=site_p, telegram=tg_p)
    data = dict(
        generated=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        kpi=dict(subs=subs, subs_goal=1000, long_hours=long_hours, long_hours_goal=4000, views_total=views_total, views_7d=last7[0], pct_7d=round(last7[1] or 0, 1), subs_7d=last7[2],
                 tg=tg_members, tg_goal=150, site_clicks_28d=sum(r[1] for r in site[-28:]), site_impr_28d=sum(r[2] for r in site[-28:]), tiktok_auto=len(tt)),
        days=[dict(d=d, v=v, p=round(p or 0, 1)) for d, v, p in days], site=[dict(d=d, c=cl, i=im, pos=round(po, 1)) for d, cl, im, po in site],
        history=hist, tg_hist=tg_hist, platforms=platforms, formats=formats, videos=vids, ideas=ideas[:12], lake=lake, news=news, competitors=comp_top,
        activity=(json.load(open(os.path.join(ROOT, "studio", "hq", "activity.json"))) if os.path.exists(os.path.join(ROOT, "studio", "hq", "activity.json")) else {"items": []})["items"][-30:],
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
