# usage: python3 upload_reserve.py slug [slug...] — завантажує резервні Shorts private без дати, ставить обкладинку, пише в reserve.json
import sys,json; sys.path.insert(0,'/home/claude/yt'); sys.path.insert(0,'/home/claude/eps')
import yt, meta, importlib; from thumb import set_thumb
M={}
for k in dir(meta):
    if k.startswith("META") and isinstance(getattr(meta,k),dict): M.update(getattr(meta,k))
res=json.load(open('/home/claude/eps/reserve.json'))
for slug in sys.argv[1:]:
    if slug in res: print(slug,"already",res[slug]); continue
    m=M[slug]
    vid=yt.upload(f'/home/claude/eps/{slug}/final.mp4',m['title'],m['description'],m['tags'],privacy="private",category="28")
    print(slug,vid,'thumb','default' in set_thumb(vid,f'/home/claude/eps/thumbs/{slug}.jpg'))
    res[slug]=vid; json.dump(res,open('/home/claude/eps/reserve.json','w'),ensure_ascii=False,indent=1)
print(len(res),"у запасі")
