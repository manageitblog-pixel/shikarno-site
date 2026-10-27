"""Сценарій + vo.wav + vo_tl.json → props.json для композиції Ep (сцени, слова субтитрів, рот)"""
import sys, json, importlib, numpy as np, soundfile as sf
sys.path.insert(0,"/home/claude/eps")
ep=importlib.import_module(sys.argv[1]); D=f"/home/claude/eps/{ep.SLUG}"
FPS=30; tl=json.load(open(f"{D}/vo_tl.json")); v,SR=sf.read(f"{D}/vo.wav")
total=int((tl[-1]["end"]+2.2)*FPS)
m=[]
for f in range(total):
    a=int(f/FPS*SR); b=int((f+1)/FPS*SR); seg=v[a:b] if a<len(v) else np.zeros(1)
    m.append(float(np.sqrt(np.mean(seg**2))) if len(seg) else 0.0)
m=np.array(m); m=np.clip(m/np.percentile(m[m>0.01],90),0,1); m=np.convolve(m,[.25,.5,.25],"same")
V="аеєиіїоуюяaeiouy"; scenes=[]; words=[]
for i,(s,t) in enumerate(zip(ep.SCENES,tl)):
    st,en=t["start"],t["end"]; nxt=tl[i+1]["start"] if i+1<len(tl) else total/FPS
    sc={k:v for k,v in s.items() if k not in ("text","gsay","say")}
    sc.update({"from":round(st*FPS),"to":round(nxt*FPS)}); scenes.append(sc)
    ws=s["text"].replace(" —","").split()
    wts=[max(1,sum(c.lower() in V for c in w))+(0.7 if w[-1] in ",.?!:" else 0) for w in ws]
    T=sum(wts); tt=st; grp=0; cnt=0
    for w,k in zip(ws,wts):
        d=(en-st)*k/T; words.append({"w":w,"s":round(tt*FPS),"e":round((tt+d)*FPS),"g":f"{i}-{grp}"}); tt+=d; cnt+=1
        if cnt>=3 or w[-1] in ",.?!:" or len(w)>11: grp+=1; cnt=0
json.dump({"alert":getattr(ep,"ALERT",None),"total":total,"scenes":scenes,"words":words,"mouth":[round(x,3) for x in m.tolist()]},open(f"{D}/props.json","w"),ensure_ascii=False)
print(ep.SLUG,total,[(s["kind"],s["from"]) for s in scenes])
