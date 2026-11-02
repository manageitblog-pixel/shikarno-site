"""Перші коментарі на заплановані ролики: API не дає коментувати приватні, тож чергу (eps/pending_comments.json) постимо після publishAt."""
import sys,json,datetime
sys.path.insert(0,'/home/claude/yt'); import yt
P="/home/claude/eps/pending_comments.json"
pc=json.load(open(P)); now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for vid,c in list(pc.items()):
    if c["at"]<=now:
        try: print(vid,"comment",yt.comment(vid,c["text"])); del pc[vid]
        except Exception as e: print(vid,"ERR",e)
json.dump(pc,open(P,"w"),ensure_ascii=False,indent=1); print("left",len(pc))
