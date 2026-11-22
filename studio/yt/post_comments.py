"""Перші коментарі на заплановані ролики: API не дає коментувати приватні, тож чергу (eps/pending_comments.json) постимо після publishAt."""
import sys,os,json,datetime
sys.path.insert(0,'/home/claude/yt'); import yt
sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),"..")); from util import read_json, update_json
P="/home/claude/eps/pending_comments.json"
pc=read_json(P,{}); now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
done=[]
for vid,c in list(pc.items()):
    if c["at"]<=now:
        try: print(vid,"comment",yt.comment(vid,c["text"])); done.append(vid)
        except Exception as e: print(vid,"ERR",e)
# під блокуванням перечитуємо: finalize міг додати нові коментарі, поки ми постили
def drop(d):
    for v in done: d.pop(v,None)
pc=update_json(P,drop,{}); print("left",len(pc))
