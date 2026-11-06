"""Дані для дашборду аналітики ШІкарно: YouTube Analytics + Search Console + Telegram → JSON у /home/claude/dash/."""
import sys, json, re, datetime, urllib.request, urllib.parse
sys.path.insert(0, '/home/claude/yt'); sys.path.insert(0, '/home/claude/tg')
import yt, tg
OUT = '/home/claude/dash/'; START = '2026-10-20'
today = datetime.date.today().isoformat()
def ya(**q):
    u = "https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(q)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": "Bearer " + yt.token()})))
def gsc(body):
    S = urllib.parse.quote("https://shikarno.com.ua/", safe='')
    r = urllib.request.Request(f"https://www.googleapis.com/webmasters/v3/sites/{S}/searchAnalytics/query", data=json.dumps(body).encode(),
                               headers={"Authorization": "Bearer " + yt.token(), "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))
def dump(name, rows): json.dump(rows, open(OUT + name, 'w'), ensure_ascii=False); print(name, len(rows))

r = ya(ids="channel==MINE", startDate=START, endDate=today, metrics="views,subscribersGained,estimatedMinutesWatched", dimensions="day", sort="day")
dump('yt_daily.json', [{"day": d, "views": v, "subs": s, "minutes": m} for d, v, s, m in r.get('rows', [])])

r = ya(ids="channel==MINE", startDate=START, endDate=today, metrics="views", dimensions="insightTrafficSourceType", sort="-views")
names = {"SHORTS": "Стрічка Shorts", "YT_SEARCH": "Пошук YouTube", "YT_CHANNEL": "Сторінка каналу", "YT_OTHER_PAGE": "Інші сторінки YouTube",
         "NOTIFICATION": "Сповіщення", "EXT_URL": "Зовнішні сайти", "SUBSCRIBER": "Підписники", "RELATED_VIDEO": "Пов'язані відео",
         "HASHTAGS": "Хештеги", "PLAYLIST": "Плейлисти", "NO_LINK_OTHER": "Інше", "END_SCREEN": "Кінцеві заставки"}
dump('yt_traffic.json', [{"source": names.get(k, k), "views": v} for k, v in r.get('rows', [])])

r = ya(ids="channel==MINE", startDate=START, endDate=today, metrics="views,engagedViews,averageViewPercentage,subscribersGained,likes,shares",
       dimensions="video", sort="-views", maxResults=50)
rows = r.get('rows', []); ids = [x[0] for x in rows]
meta = {}
for k in range(0, len(ids), 50):
    for v in yt.api("videos", part="snippet,contentDetails", id=",".join(ids[k:k+50]))['items']:
        d = v['contentDetails']['duration']; m = re.match(r'P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', d)
        sec = int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)
        t = re.sub(r'\s*#\w+', '', v['snippet']['title']).strip()
        fmt = 'Довге' if sec > 180 else ('Тір-лист' if 'Тір-лист' in t else 'Професії' if 'для професій' in t or 'ШІ для ' in t[:8] else 'Шахраї/безпека' if re.search('шахра|безпек|паролі', t, re.I) else 'Скіли' if 'скіл' in t.lower() else 'Інше')
        meta[v['id']] = (t, v['snippet']['publishedAt'][:10], fmt)
dump('yt_videos.json', [{"id": i, "video": meta.get(i, ('?', '', ''))[0], "published": meta.get(i, ('', '?', ''))[1], "format": meta.get(i, ('', '', '?'))[2],
                         "views": vw, "engaged_share": round(e / vw, 3) if vw else 0, "avg_view_pct": round(p / 100, 3), "subs": s, "likes": l, "shares": sh}
                        for i, vw, e, p, s, l, sh in rows])

r = gsc({"startDate": START, "endDate": today, "dimensions": ["date"], "rowLimit": 200, "dataState": "all"})
dump('site_daily.json', [{"day": x['keys'][0], "impressions": x['impressions'], "clicks": x['clicks'], "position": round(x['position'], 1)} for x in r.get('rows', [])])
r = gsc({"startDate": START, "endDate": today, "dimensions": ["query"], "rowLimit": 10, "dataState": "all"})
dump('site_queries.json', [{"query": x['keys'][0], "impressions": x['impressions'], "clicks": x['clicks'], "position": round(x['position'], 1)} for x in r.get('rows', [])])

ch = yt.api("channels", part="statistics", mine="true")["items"][0]["statistics"]
tgm = tg.call('getChatMemberCount', chat_id=tg.CH).get('result')
dump('totals.json', [{"metric": "Підписники YouTube", "value": int(ch['subscriberCount'])}, {"metric": "Переглядів YouTube всього", "value": int(ch['viewCount'])},
                     {"metric": "Учасники Telegram-каналу", "value": tgm}, {"metric": "Відео на каналі", "value": int(ch['videoCount'])}])
