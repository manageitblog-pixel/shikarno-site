import sys, json, numpy as np, soundfile as sf, importlib, os
sys.path.insert(0,"/home/claude/eps"); sys.path.insert(0,"/home/claude/gem")
import gen_full as G; from gtts import tts
dg=importlib.import_module("special1"); D="/home/claude/eps/special1"
old,SR=sf.read(f"{D}/vo_raw_v1.wav",dtype="float32"); otl=json.load(open(f"{D}/vo_tl_v1.json"))
oseg=[old[int(t["start"]*SR):int(t["end"]*SR)] for t in otl]
NEW=[1,5,6]; raw=f"{D}/part2.wav"
if not os.path.exists(raw):
    for m in ["gemini-3.8-flash-tts","gemini-3.8-flash-lite-tts"]:
        try: print(m, tts("\n\n".join(dg.SEGS[i]["gsay"] for i in NEW),"Sadachbia",raw,model=m)); break
        except Exception as e: print("fail",m,e)
w,sr=sf.read(raw,dtype="float32"); assert sr==SR
nseg=[G.trim(p,sr) for p in G.split_scenes(w,sr,[dg.SEGS[i]["gsay"] for i in NEW])]
mp={0:oseg[0],1:nseg[0],2:oseg[2],3:oseg[3],4:oseg[4],5:nseg[1],6:nseg[2]}
for k in range(7,13): mp[k]=oseg[k-2]
out=[np.zeros(int(0.3*SR),dtype=np.float32)]; t=0.3; tl=[]
for i in range(13):
    x=mp[i]; gap=0.35 if dg.SEGS[i]["kind"] in ("verdict","agenda","intro") else 0.2
    tl.append({"start":t,"end":t+len(x)/SR}); out+=[x,np.zeros(int(gap*SR),dtype=np.float32)]; t+=len(x)/SR+gap
    print(i, round(len(x)/SR,1), G.asr(x[:int(2.5*SR)],SR)[:40], "|", G.asr(x[-int(2.5*SR):],SR)[-40:])
a=np.concatenate(out); sf.write(f"{D}/vo_raw.wav",a,SR); json.dump(tl,open(f"{D}/vo_tl.json","w")); print(len(a)/SR)
