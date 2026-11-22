"""YouTube helper: токен, статистика, завантаження (resumable)."""
import json, os, re, sys, time, datetime, urllib.request, urllib.parse, urllib.error
D="/home/claude/yt"
QUOTA_LOG=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"data","quota.log")
RETRY_CODES={429,500,502,503,504}
def _scrub(s):
    return re.sub(r"ya29\.[A-Za-z0-9_.-]+|AIza[A-Za-z0-9_-]{20,}|1//[A-Za-z0-9_-]{20,}","•••",str(s))
def _units(method, url):
    p=urllib.parse.urlparse(url).path
    if "/upload/" in p and p.endswith("/videos"): return 1600
    if p.endswith("/search"): return 100
    if p.endswith("/thumbnails/set"): return 50
    if method in ("POST","PUT","DELETE"): return 50
    return 1
def _log_quota(method, url):
    try:
        os.makedirs(os.path.dirname(QUOTA_LOG), exist_ok=True)
        p=urllib.parse.urlparse(url).path.replace("/youtube/v3/","")
        with open(QUOTA_LOG,"a") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{method} {p}\t{_units(method,url)}\n")
    except OSError: pass
def _req(url, data=None, method=None, headers=None, tries=3, timeout=60, log=True):
    """urlopen з timeout, backoff (1, 4 с) на мережеві помилки і 429/5xx; інші 4xx — одразу RuntimeError з тілом."""
    method=method or ("POST" if data is not None else "GET")
    if log: _log_quota(method, url)
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url,data=data,method=method,headers=headers or {}),timeout=timeout)
        except urllib.error.HTTPError as e:
            body=_scrub(e.read().decode("utf-8","replace")[:800])
            if e.code in RETRY_CODES and i<tries-1:
                print(f"yt: HTTP {e.code}, повтор {i+2}/{tries}", file=sys.stderr); time.sleep(4**i); continue
            raise RuntimeError(f"YouTube API {method} {urllib.parse.urlparse(url).path}: HTTP {e.code}: {body}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if i<tries-1:
                print(f"yt: мережева помилка ({_scrub(e)}), повтор {i+2}/{tries}", file=sys.stderr); time.sleep(4**i); continue
            raise RuntimeError(f"YouTube API {method} {urllib.parse.urlparse(url).path}: мережа: {_scrub(e)}") from None
def token():
    t=json.load(open(f"{D}/token.json")); c=json.load(open(f"{D}/client_secret.json"))["installed"]
    if time.time() > t.get("obtained",0)+t.get("expires_in",0)-120:
        data=urllib.parse.urlencode({"client_id":c["client_id"],"client_secret":c["client_secret"],
            "refresh_token":t["refresh_token"],"grant_type":"refresh_token"}).encode()
        n=json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token",data=data))
        t.update(n); t["obtained"]=time.time(); json.dump(t,open(f"{D}/token.json","w"))
    return t["access_token"]
def api(path, **q):
    url="https://www.googleapis.com/youtube/v3/"+path+"?"+urllib.parse.urlencode(q)
    return json.load(_req(url,headers={"Authorization":"Bearer "+token()}))
def recent(n=5):
    ch=api("channels",part="contentDetails",mine="true")["items"][0]
    up=ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items=api("playlistItems",part="contentDetails",playlistId=up,maxResults=n)["items"]
    ids=",".join(i["contentDetails"]["videoId"] for i in items)
    for v in api("videos",part="snippet,statistics,status,contentDetails",id=ids)["items"]:
        print(v["snippet"]["publishedAt"][:16], v["status"]["privacyStatus"], v["contentDetails"]["duration"], v["statistics"], "|", v["snippet"]["title"])
def upload(path, title, description, tags, privacy="private", category="28", lang="uk", publish_at=None):
    meta={"snippet":{"title":title,"description":description,"tags":tags,"categoryId":category,
                     "defaultLanguage":lang,"defaultAudioLanguage":lang},
          "status":{"privacyStatus":privacy,"selfDeclaredMadeForKids":False}}
    if publish_at: meta["status"].update({"privacyStatus":"private","publishAt":publish_at})
    dup=_find_recent_upload(title)
    if dup:
        print(f"УВАГА: ролик з такою самою назвою вже залито за останні 24 год — {dup}; повторно НЕ заливаю", file=sys.stderr)
        print("uploaded:", dup, "(existing)", flush=True); return dup
    size=os.path.getsize(path)
    loc=_req("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json; charset=UTF-8",
                 "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(size)}).headers["Location"]
    with open(path,"rb") as f: blob=f.read()
    v=json.load(_req(loc,data=blob,method="PUT",headers={"Content-Type":"video/mp4"},log=False))
    print("uploaded:", v["id"], v["status"]["privacyStatus"], flush=True); return v["id"]
def _find_recent_upload(title, hours=24):
    """Ідемпотентність: id ролика з точно такою назвою з плейлиста uploads за останні `hours` год (2 одиниці квоти)."""
    try:
        up=api("channels",part="contentDetails",mine="true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        items=api("playlistItems",part="snippet",playlistId=up,maxResults=20).get("items",[])
    except Exception as e:
        print("yt: перевірка дублів не вдалася (заливаю далі):", _scrub(e), file=sys.stderr); return None
    now=datetime.datetime.now(datetime.timezone.utc)
    for it in items:
        sn=it.get("snippet",{})
        if sn.get("title","").strip()!=title.strip(): continue
        try: ts=datetime.datetime.fromisoformat(sn["publishedAt"].replace("Z","+00:00"))
        except (KeyError, ValueError): continue
        if now-ts<=datetime.timedelta(hours=hours):
            return sn.get("resourceId",{}).get("videoId")
    return None
if __name__=="__main__":
    recent()

def _put(path, body, part):
    url="https://www.googleapis.com/youtube/v3/"+path+"?part="+part
    return json.load(_req(url,data=json.dumps(body).encode(),method="PUT",
        headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json; charset=UTF-8"}))
def schedule(vid, publish_at_utc):
    """publish_at_utc: '2026-10-22T17:00:00Z' — ролик стане публічним у цей час"""
    v=_put("videos",{"id":vid,"status":{"privacyStatus":"private","publishAt":publish_at_utc,"selfDeclaredMadeForKids":False,"embeddable":True,"publicStatsViewable":True,"license":"youtube"}},"status")
    return v["status"]
def set_category(vid, cat="28"):
    sn=api("videos",part="snippet",id=vid)["items"][0]["snippet"]
    body={"id":vid,"snippet":{"title":sn["title"],"description":sn["description"],"tags":sn.get("tags",[]),"categoryId":cat,
          "defaultLanguage":sn.get("defaultLanguage","uk"),"defaultAudioLanguage":sn.get("defaultAudioLanguage","uk")}}
    return _put("videos",body,"snippet")["snippet"]["categoryId"]

def comment(vid, text):
    body={"snippet":{"videoId":vid,"topLevelComment":{"snippet":{"textOriginal":text}}}}
    return json.load(_req("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",data=json.dumps(body).encode(),method="POST",
        headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json; charset=UTF-8"}))["id"]

PLAYLISTS={"news":"PLTBOXlyURN0g","sec":"PLK19K_iOB7fU","skills":"PLDoCjFWXo6eI","prof":"PLUNuDFNf9LVc","tier":"PLbWfeHw_IhwY",
           "check":"PLY2sr8xgYaG4","digest":"PLb2dDm0ckIWk","try":"PLJmaWDPrufYo","free":"PLHQnxB4mtNbM"}
def add_to_playlist(vid, *keys):
    """Після КОЖНОЇ заливки (власник 14.11: «нічого не забув?»): yt.add_to_playlist(vid, "news", "sec")"""
    out=[]
    for k in keys:
        pl=PLAYLISTS.get(k,k)
        out.append(json.load(_req("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
            data=json.dumps({"snippet":{"playlistId":pl,"resourceId":{"kind":"youtube#video","videoId":vid}}}).encode(),method="POST",
            headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json"}))["id"])
    return out
