import sys, json, importlib, numpy as np, soundfile as sf
sys.path.insert(0,"/home/claude/eps"); import gen_full as G
dg=importlib.import_module("special1"); D="/home/claude/eps/special1"
w,sr=sf.read(f"{D}/part0.wav",dtype="float32")
texts=[dg.SEGS[i]["gsay"] for i in dg.PARTS[0]]
parts=G.split_scenes(w,sr,texts)
x=parts[3]
import inspect; print(inspect.signature(G.pauses))
ps=G.pauses(x,sr)
print(ps[:40])
for p in ps:
    s=p[1] if isinstance(p,(tuple,list)) else p
    if s<1 or s>len(x)/sr-3: continue
    h=G.asr(x[int(s*sr):int((s+2.5)*sr)],sr); print(round(s,2),h)
