# Спроба завантажити екстрений PHP Short і запланувати на 08:00 Київ (05:00Z)
import sys,json,urllib.request,datetime
sys.path.insert(0,'/home/claude/yt'); sys.path.insert(0,'/home/claude/eps')
import yt, meta
u=json.load(open('/home/claude/eps/uploaded.json'))
if "ep10_php2shell" in u: print("ALREADY",u["ep10_php2shell"]); sys.exit()
m=meta.META4["ep10_php2shell"]
now=datetime.datetime.now(datetime.timezone.utc)
at="2026-10-23T04:00:00Z" if now<datetime.datetime(2026,10,23,3,50,tzinfo=datetime.timezone.utc) else None
try:
    vid=yt.upload("/home/claude/eps/ep10_php2shell/final.mp4",m["title"],m["description"],m["tags"],privacy="private" if at else "public",category="28")
except urllib.error.HTTPError as e: print("FAIL",e.code,e.read().decode()[:120]); sys.exit()
if at: yt.schedule(vid,at)
u["ep10_php2shell"]=vid; json.dump(u,open('/home/claude/eps/uploaded.json','w')); print("OK",vid,at or "public now")
