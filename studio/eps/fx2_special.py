import sys, json, numpy as np, soundfile as sf, importlib
sys.path.insert(0,"/home/claude/eps"); import gen_full as G
dg=importlib.import_module("special1"); D="/home/claude/eps/special1"
segs=[]
for pi,idxs in enumerate(dg.PARTS):
    w,sr=sf.read(f"{D}/part{pi}.wav",dtype="float32")
    ps=G.split_scenes(w,sr,[dg.SEGS[i]["gsay"] for i in idxs])
    if pi==0:
        x=ps[3]; cut=[b for a,b in G.pauses(x,sr) if abs(b/sr-8.52)<0.05][0]-int(0.08*sr)
        ps[2]=np.concatenate([ps[2],x[:cut]]); ps[3]=x[cut:]
    segs+=[G.trim(p,sr) for p in ps]
SR=24000; out=[np.zeros(int(0.3*SR),dtype=np.float32)]; t=0.3; tl=[]
for i,x in enumerate(segs):
    gap=0.35 if dg.SEGS[i]["kind"] in ("verdict","agenda","intro") else 0.2
    tl.append({"start":t,"end":t+len(x)/SR}); out+=[x,np.zeros(int(gap*SR),dtype=np.float32)]; t+=len(x)/SR+gap
    print(i, round(len(x)/SR,1), G.asr(x[:int(2.5*SR)],SR)[:40], "|", G.asr(x[-int(2.5*SR):],SR)[-40:])
a=np.concatenate(out); sf.write(f"{D}/vo_raw.wav",a,SR); json.dump(tl,open(f"{D}/vo_tl.json","w")); print(len(a)/SR)
