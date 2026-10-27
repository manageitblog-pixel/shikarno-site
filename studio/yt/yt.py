"""YouTube helper: токен, статистика, завантаження (resumable)."""
import json, os, sys, time, urllib.request, urllib.parse
D="/home/claude/yt"
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
    return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"Authorization":"Bearer "+token()})))
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
    size=os.path.getsize(path)
    req=urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json; charset=UTF-8",
                 "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(size)})
    loc=urllib.request.urlopen(req).headers["Location"]
    with open(path,"rb") as f:
        r=urllib.request.Request(loc,data=f.read(),method="PUT",headers={"Content-Type":"video/mp4"})
        v=json.load(urllib.request.urlopen(r))
    print("uploaded:", v["id"], v["status"]["privacyStatus"]); return v["id"]
if __name__=="__main__":
    recent()

def _put(path, body, part):
    url="https://www.googleapis.com/youtube/v3/"+path+"?part="+part
    r=urllib.request.Request(url,data=json.dumps(body).encode(),method="PUT",
        headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json; charset=UTF-8"})
    return json.load(urllib.request.urlopen(r))
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
    r=urllib.request.Request("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",data=json.dumps(body).encode(),method="POST",
        headers={"Authorization":"Bearer "+token(),"Content-Type":"application/json; charset=UTF-8"})
    return json.load(urllib.request.urlopen(r))["id"]
