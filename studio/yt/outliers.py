"""Пошук «аномалій» у ніші (метод з відео VOLGIN, 6.11): свіжі відео, де перегляди >> підписників каналу.
Запуск: python3 studio/yt/outliers.py [днів=30] → топ-40 за views/subs. Квота: ~100 од. на запит пошуку."""
import sys,re,datetime;sys.path.insert(0,'/home/claude/yt');import yt,lake
days=int(sys.argv[1]) if len(sys.argv)>1 else 30
after=(datetime.datetime.utcnow()-datetime.timedelta(days=days)).strftime('%Y-%m-%dT00:00:00Z')
qs=["штучний інтелект","ChatGPT українською","нейромережі як","Gemini безкоштовно","Claude ШІ","ШІ для бізнесу","ШІ для роботи","нейромережа для фото","ШІ агенти","вайбкодинг"]
vids=set()
for q in qs:
    for it in yt.api('search',part='snippet',q=q,type='video',order='viewCount',publishedAfter=after,relevanceLanguage='uk',maxResults=25,regionCode='UA')['items']: vids.add(it['id']['videoId'])
ids=list(vids);V={};C={}
for i in range(0,len(ids),50):
    for it in yt.api('videos',part='snippet,statistics,contentDetails',id=','.join(ids[i:i+50]))['items']: V[it['id']]=it
chs=list({v['snippet']['channelId'] for v in V.values()})
for i in range(0,len(chs),50):
    for it in yt.api('channels',part='statistics,snippet',id=','.join(chs[i:i+50]))['items']: C[it['id']]=it
rows=[]
for k,v in V.items():
    c=C.get(v['snippet']['channelId'])
    if not c: continue
    subs=int(c['statistics'].get('subscriberCount',0) or 0);views=int(v['statistics'].get('viewCount',0))
    sec=sum(int(n)*{'H':3600,'M':60,'S':1}[u] for n,u in re.findall(r'(\d+)([HMS])',v['contentDetails']['duration']))
    rows.append((views/max(subs,100),views,subs,sec,v['snippet']['publishedAt'][:10],c['snippet']['title'][:25],v['snippet']['title'][:90],k,
                 int(lake.is_ru(v['snippet']['title'],c['snippet']['title'],c['snippet'].get('description','')[:300]))))
# 28.11: російськомовні канали (назва/опис/заголовок, див. lake.is_ru) не показуємо в топі — лише в лейку з ru=1
for r in sorted((r for r in rows if not r[8]),reverse=True)[:40]: print(f"{r[0]:6.1f}x {r[1]:>7}v {r[2]:>7}s {r[3]//60:>3}m{r[3]%60:02d} {r[4]} {r[5]:25} | {r[6]} {r[7]}")
# 22.11: кожен запуск поповнює даталейк (studio/data/analytics.sqlite, таблиця niche) — історія ніші для аналізу «що вистрілює»
import os,sqlite3
_db=sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','analytics.sqlite'))
_db.execute("create table if not exists niche(video_id text, fetched text, channel text, title text, published text, duration_s int, views int, channel_subs int, ratio real, ru int, primary key(video_id,fetched))")
_today=datetime.date.today().isoformat()
for r in rows: _db.execute("insert or replace into niche values(?,?,?,?,?,?,?,?,?,?)",(r[7],_today,r[5],r[6],r[4],r[3],r[1],r[2],r[0],r[8]))
_db.commit(); print(f"niche: +{len(rows)} рядків у даталейк; ru перераховано по каналах:", lake.recompute_ru(_db))
