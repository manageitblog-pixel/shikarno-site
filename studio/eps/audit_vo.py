# Повна звірка озвучки зі сценарієм: транскрибує КОЖЕН сегмент повністю (шматками по паузах ≤15 с)
# usage: python eps/audit_vo.py <script_module> [vo_raw.wav path]
import sys, json, soundfile as sf, importlib, re
sys.path.insert(0,"/home/claude/eps"); import gen_full as G
m=importlib.import_module(sys.argv[1]); D=f"/home/claude/eps/{m.SLUG}"
segs=getattr(m,"SCENES",None) or m.SEGS
w,sr=sf.read(sys.argv[2] if len(sys.argv)>2 else f"{D}/vo_raw.wav",dtype="float32")
tl=json.load(open(f"{D}/vo_tl.json"))
def words(s): return re.findall(r"[а-яіїєґa-z0-9']+", s.lower())
import os
ST=int(os.environ.get("START","0"))
for i,t in enumerate(tl):
    if i<ST: continue
    x=w[int(t["start"]*sr):int(t["end"]*sr)]
    ps=[b for a,b in G.pauses(x,sr) if b-a>2400]+[len(x)]
    pieces=[];cur=0
    for c in ps:
        while c-cur>8*sr: pieces.append((cur,cur+7*sr)); cur+=7*sr
        if c-cur>=4*sr or c==len(x): pieces.append((cur,c)); cur=c
    hyp=" ".join(G.asr(x[a:b],sr) for a,b in pieces if b-a>sr*0.3)
    exp=segs[i]["gsay"]; we,wh=words(exp),words(hyp)
    ratio=len(wh)/max(1,len(we))
    flag=" <<< ПЕРЕВІР (довжина)" if ratio>1.25 or ratio<0.8 else ""
    print(f"### {i} {segs[i]['kind']} {t['start']:.1f}-{t['end']:.1f}s слів {len(wh)}/{len(we)}{flag}")
    print("  ОЧІК:", exp); print("  ЧУЄМ:", hyp)
