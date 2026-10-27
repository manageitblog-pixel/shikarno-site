import sys,json,urllib.request
sys.path.insert(0,'/home/claude/yt'); import yt
def set_thumb(vid,path):
    ct="image/png" if path.endswith(".png") else "image/jpeg"
    r=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",data=open(path,"rb").read(),method="POST",headers={"Authorization":"Bearer "+yt.token(),"Content-Type":ct})
    try: return json.load(urllib.request.urlopen(r))["items"][0]
    except urllib.error.HTTPError as e: return {"err":e.code,"msg":e.read().decode()[:300]}
if __name__=="__main__": print(set_thumb(sys.argv[1],sys.argv[2]))
