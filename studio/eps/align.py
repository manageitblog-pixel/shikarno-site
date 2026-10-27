# Вирівнювання речень сценарію з реальною озвучкою (Whisper на початках після пауз).
# Пише <D>/align.json: для кожного сегмента — абсолютні часи початку кожного речення (с).
import sys, json, re, difflib, importlib, soundfile as sf
sys.path.insert(0,"/home/claude/eps"); import gen_full as G
def sents(t): return [s for s in re.split(r"(?<=[.!?…])\s+", t.strip()) if s]
def norm(s): return re.sub(r"[^а-яіїєґa-z0-9]", "", s.lower())
def run(modname):
    m=importlib.import_module(modname); D=f"/home/claude/eps/{m.SLUG}"
    segs=getattr(m,"SCENES",None) or m.SEGS
    w,sr=sf.read(f"{D}/vo_raw.wav",dtype="float32"); tl=json.load(open(f"{D}/vo_tl.json"))
    out=[]
    for i,(s,t) in enumerate(zip(segs,tl)):
        ss=sents(s["gsay"]); st,en=t["start"],t["end"]
        if len(ss)<=1: out.append([st]); continue
        x=w[int(st*sr):int(en*sr)]
        cands=[0.0]+[b/sr for a,b in G.pauses(x,sr) if b-a>0.15*sr and b/sr<len(x)/sr-0.8]
        heads={c:norm(G.asr(x[int(c*sr):int((c+2.2)*sr)],sr)) for c in cands}
        tot=sum(len(q) for q in ss); res=[st]; prev=0.0; acc=len(ss[0]); fb=[False]
        for j in range(1,len(ss)):
            exp=(en-st)*acc/tot; acc+=len(ss[j]); key=norm(ss[j])[:14]
            best=None;bs=0
            for c in cands:
                if c<=prev+0.5 or abs(c-exp)>7: continue
                h=heads[c]; sc=difflib.SequenceMatcher(None,key,h[:len(key)+2]).ratio()
                k2=norm(" ".join(ss[j].split()[1:]))[:10]
                if k2 and len(h)>=len(k2):
                    sc2=max(difflib.SequenceMatcher(None,k2,h[o:o+len(k2)]).ratio() for o in range(0,min(14,len(h)-len(k2)+1)))
                    sc=max(sc,sc2*0.95)
                if sc>bs: bs,best=sc,c
            if best is None or bs<0.45: best=max(prev+0.5,exp); tag="~"
            else: tag=""
            res.append(st+best); prev=best; fb.append(tag=="~")
            print(f"{i}.{j} {tag}{best:6.2f}s (очік {exp:6.2f}) score={bs:.2f} | {ss[j][:40]} | {heads.get(best,'')[:30]}")
        # фолбеки — лінійна інтерполяція між найближчими знайденими якорями за кількістю символів
        L=[len(q) for q in ss]; anch=[k for k in range(len(ss)) if not fb[k]]
        for k in range(len(ss)):
            if not fb[k]: continue
            p=max(a for a in anch if a<k); nx=[a for a in anch if a>k]
            tp=res[p]; tn=res[nx[0]] if nx else en; cn=sum(L[p:nx[0]]) if nx else sum(L[p:])
            res[k]=tp+(tn-tp)*sum(L[p:k])/cn
            print(f"  інтерп {i}.{k} -> {res[k]-st:.2f}s")
        out.append(res)
    json.dump(out,open(f"{D}/align.json","w"))
if __name__=="__main__": run(sys.argv[1])
