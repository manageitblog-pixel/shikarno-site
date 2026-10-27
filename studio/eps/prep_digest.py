import sys, json, importlib, numpy as np, soundfile as sf
sys.path.insert(0,"/home/claude/eps")
dg=importlib.import_module(sys.argv[1]); D=f"/home/claude/eps/{dg.SLUG}"
FPS=30; tl=json.load(open(f"{D}/vo_tl.json")); v,SR=sf.read(f"{D}/vo.wav")
total=int((tl[-1]["end"]+4.0)*FPS)
m=[]
for f in range(total):
    a=int(f/FPS*SR); b=int((f+1)/FPS*SR); seg=v[a:b] if a<len(v) else np.zeros(1)
    m.append(float(np.sqrt(np.mean(seg**2))) if len(seg) else 0.0)
m=np.array(m); m=np.clip(m/np.percentile(m[m>0.01],90),0,1); m=np.convolve(m,[.25,.5,.25],"same")
V="аеєиіїоуюяaeiouy"; segs=[]; words=[]
import os, re
AL=json.load(open(f"{D}/align.json")) if os.path.exists(f"{D}/align.json") else None
def sents(t): return [x for x in re.split(r"(?<=[.!?…])\s+", t.strip()) if x]
def spread(ws, st, en, i, gstart):
    wts=[max(1,sum(c.lower() in V for c in w))+(0.7 if w[-1] in ",.?!:" else 0) for w in ws]
    T=sum(wts); tt=st; grp=gstart; cnt=0
    for w,k in zip(ws,wts):
        d=(en-st)*k/T; words.append({"w":w,"s":round(tt*FPS),"e":round((tt+d)*FPS),"g":f"{i}-{grp}"}); tt+=d; cnt+=1
        if cnt>=5 or w[-1] in ",.?!:" or len(w)>12: grp+=1; cnt=0
    return grp+1
for i,(s,t) in enumerate(zip(dg.SEGS,tl)):
    st,en=t["start"],t["end"]; nxt=tl[i+1]["start"] if i+1<len(tl) else total/FPS
    sc={k:v for k,v in s.items() if k not in ("text","gsay","pt")}; sc.update({"from":round(st*FPS),"to":round(nxt*FPS)})
    seqstart = 0 if i==0 else sc["from"]-6
    ss=sents(s["text"]); A=AL[i] if AL and i<len(AL) and len(AL[i])==len(ss) else None
    if A:
        g=0
        for k,sen in enumerate(ss):
            a=A[k]; b=(A[k+1]-0.12) if k+1<len(ss) else en
            g=spread(sen.replace(" —","").split(), a, b, i, g)
        if "pt" in s:
            def tm(p):
                k=int(p); fr=p-k; a=A[k]; b=A[k+1] if k+1<len(A) else en
                return a+(b-a)*fr
            sc["at"]=[max(4,round(tm(p)*FPS)-seqstart) for p in s["pt"]]
    else:
        spread(s["text"].replace(" —","").split(), st, en, i, 0)
    segs.append(sc)
titles=[s["title"].split(":")[0] for s in dg.SEGS if s["kind"]=="points"]
json.dump({**{k:getattr(dg,K) for k,K in [("kicker","KICKER"),("sub","SUB"),("big","BIG"),("agendaTitle","AGENDA_TITLE"),("red","RED")] if hasattr(dg,K)},"total":total,"num":dg.NUM,"dates":dg.DATES,"segs":segs,"words":words,"mouth":[round(x,3) for x in m.tolist()],"titles":titles},open(f"{D}/props.json","w"),ensure_ascii=False)
chap=[(0,"Вступ")]+[(s["from"]/FPS,f'{s["n"]}. {s["title"]}') for s in segs if s["kind"]=="points"]+[(s["from"]/FPS,"Коротко") for s in segs if s["kind"]=="quick"]+[(s["from"]/FPS,"Фінал") for s in segs if s["kind"]=="outro"]
json.dump([[round(a,1),b] for a,b in chap],open(f"{D}/chapters.json","w"),ensure_ascii=False)
print(total/FPS, chap)
