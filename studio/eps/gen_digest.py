import sys, os, json, importlib, numpy as np, soundfile as sf
sys.path.insert(0,"/home/claude/eps"); sys.path.insert(0,"/home/claude/gem")
import gen_full as G
from gtts import tts
dg=importlib.import_module(sys.argv[1]); voice=sys.argv[2]; models=sys.argv[3].split(",")
D=f"/home/claude/eps/{dg.SLUG}"; os.makedirs(D,exist_ok=True)
segs_audio=[]
for pi,idxs in enumerate(dg.PARTS):
    texts=[dg.SEGS[i]["gsay"] for i in idxs]
    raw=f"{D}/part{pi}.wav"
    if not os.path.exists(raw):
        for m in models:
            try: print(pi, m, tts("\n\n".join(texts),voice,raw,model=m)); break
            except Exception as e: print("fail",m,e)
    w,sr=sf.read(raw,dtype="float32")
    parts=G.split_scenes(w,sr,texts)
    for i,x in zip(idxs,parts):
        x=G.trim(x,sr); hyp=G.asr(x[:sr*12],sr); print(i, "%.1fs"%(len(x)/sr), hyp[:90], flush=True); segs_audio.append(x)
SR=24000; out=[np.zeros(int(0.3*SR),dtype=np.float32)]; t=0.3; tl=[]
for i,x in enumerate(segs_audio):
    gap=0.35 if dg.SEGS[i]["kind"] in ("verdict","agenda","intro") else 0.2
    tl.append({"start":t,"end":t+len(x)/SR}); out+=[x,np.zeros(int(gap*SR),dtype=np.float32)]; t+=len(x)/SR+gap
a=np.concatenate(out); sf.write(f"{D}/vo_raw.wav",a,SR); json.dump(tl,open(f"{D}/vo_tl.json","w"))
print("total %.1f s"%(len(a)/SR))
