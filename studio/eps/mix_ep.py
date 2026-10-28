import json, sys, numpy as np, soundfile as sf
D=sys.argv[1]; ep=json.load(open(f"{D}/props.json")); FPS=30; SR=44100
v,_vsr=sf.read(f"{D}/vo.wav"); assert _vsr==SR, f"vo.wav must be {SR} Hz, got {_vsr}"; n=int(ep["total"]/FPS*SR); t=np.arange(n)/SR
rng=np.random.default_rng(1)
def place(buf,sig,frame,gain=1.0):
    a=int(frame/FPS*SR); m=min(len(sig),n-a)
    if m>0 and a>=0: buf[a:a+m]+=sig[:m]*gain
def env(m,att,dec): s=np.arange(m)/SR; return np.minimum(1,s/att)*np.exp(-s*dec)
def whoosh(d=0.35):
    m=int(d*SR); x=rng.standard_normal(m); s=np.arange(m)/SR
    # проста «розгортка» фільтра через ковзне середнє різної довжини
    out=np.zeros(m); k=np.linspace(40,4,m).astype(int)
    c=np.cumsum(np.insert(x,0,0))
    for i in range(m):
        j=max(0,i-k[i]); out[i]=(c[i+1]-c[j])/(i+1-j)
    return out*np.sin(np.pi*s/d)**2*1.6
def pop(f0=900): m=int(0.09*SR); s=np.arange(m)/SR; return np.sin(2*np.pi*(f0+800*np.exp(-s*60))*s)*env(m,0.002,45)
def click(): m=int(0.03*SR); return rng.standard_normal(m)*env(m,0.0005,250)*0.6
def ding(f0=1318): m=int(1.2*SR); s=np.arange(m)/SR; return (np.sin(2*np.pi*f0*s)+0.5*np.sin(2*np.pi*f0*2.01*s)+0.3*np.sin(2*np.pi*f0*3.02*s))*env(m,0.003,4)*0.5
def cash():
    a=ding(2093)*0.6; b=np.zeros(int(0.08*SR)); return np.concatenate([b,ding(2637)*0.5])[:len(a)]+a
def impact(): m=int(0.6*SR); s=np.arange(m)/SR; return np.sin(2*np.pi*(45+120*np.exp(-s*25))*s)*env(m,0.002,7)*1.2
fx=np.zeros(n)
place(fx,impact(),2,0.8); place(fx,whoosh(0.5),0,0.5); place(fx,whoosh(0.4),12,0.4)
for i,s in enumerate(ep["scenes"]):
    st=0 if i==0 else s["from"]-6
    if i>0: place(fx,whoosh(),st-4,0.35)
    if s["kind"]!="outro": place(fx,pop(),st+4,0.35)
    if s["kind"].startswith("money"):
        for k in (10,45,95): place(fx,pop(1300),st+k,0.3)
        place(fx,cash(),st+120,0.45)
    if s["kind"] in ("tier","paidFree"):  # як у Generic.tsx: рядок кожні step кадрів, клітинки через 4/6 кадрів
        nxt=ep["scenes"][i+1]["from"]-6 if i+1<len(ep["scenes"]) else ep["total"]; dur=nxt-st; rows=s.get("items",[])
        step=max(12,(dur-20)//max(1,len(rows)))
        import re as _re
        norm=lambda w:_re.sub(r"[^\w]","",w.lower()); frm=st; starts=[]
        for r,row in enumerate(rows):  # як rowStarts у Generic.tsx: момент, коли в озвучці звучить назва рядка
            w=next((x for x in ep["words"] if x["s"]>=frm and norm(x["w"])==norm(row[0])),None) if s["kind"]=="tier" else None
            if i==0 and r==0: starts.append(st)
            elif w: starts.append(w["s"]-4); frm=w["s"]+1
            else: starts.append(st+r*step)
        for r in range(len(rows)):
            a=starts[r]
            place(fx,whoosh(0.3),a-5,0.35)
            if not (i==0 and r==0): place(fx,impact(),a,0.35)
            for j,dj in enumerate((0,4,8) if s["kind"]=="tier" else (0,6)): place(fx,pop(900+250*j),a+dj+2,0.3)
    if s["kind"].startswith("verdict"):
        place(fx,ding(),st+48,0.4); place(fx,pop(700),st+60,0.3); place(fx,pop(500),st+100,0.3)
    if s["kind"]=="outro":
        place(fx,pop(),st+24,0.35); place(fx,click(),st+70,0.9); place(fx,ding(1760),st+72,0.3)
# музика
mus=np.zeros(n); bpm=104; beat=60/bpm; bar=beat*4
ch=[[220,261.6,329.6,440],[174.6,220,261.6,349.2],[261.6,329.6,392,523.3],[196,246.9,293.7,392]]
for i in range(int(n/SR/bar)+1):
    a,b=int(i*bar*SR),min(n,int((i+1)*bar*SR))
    if a>=n: break
    s=t[a:b]-t[a]; e=np.minimum(1,s*4)*np.minimum(1,(s[-1]-s+1e-3)*4)
    for fq in ch[i%4]: mus[a:b]+=(np.sin(2*np.pi*fq*s)+0.25*np.sin(2*np.pi*fq*2.003*s))*e*0.035
    mus[a:b]+=np.sin(2*np.pi*ch[i%4][0]/2*s)*e*0.08
for k in range(int(n/SR/(beat/2))):
    a=int(k*beat/2*SR); m=min(n-a,int(0.25*SR)); s=np.arange(m)/SR
    fq=ch[int(k*beat/2/bar)%4][(k*3)%4]*2; mus[a:a+m]+=np.sin(2*np.pi*fq*s)*np.exp(-s*12)*0.04
for k in range(int(n/SR/beat)):
    a=int(k*beat*SR); m=min(n-a,int(0.3*SR)); s=np.arange(m)/SR
    mus[a:a+m]+=np.sin(2*np.pi*(48+110*np.exp(-s*35))*s)*np.exp(-s*12)*0.5
    if k%2: mus[a:a+m]+=rng.standard_normal(m)*np.exp(-s*28)*0.09
    h=int((k+0.5)*beat*SR); mm=min(n-h,int(0.04*SR))
    if mm>0: mus[h:h+mm]+=rng.standard_normal(mm)*np.exp(-np.arange(mm)/SR*130)*0.05
mus/=np.abs(mus).max()
vv=np.zeros(n); vv[:min(n,len(v))]=v[:n]
act=np.convolve((np.abs(vv)>0.03).astype(float),np.ones(SR//4)/(SR//4),"same")
mix=vv+mus*0.14*(1-0.6*np.clip(act*3,0,1))+fx*0.6
mix*=np.minimum(1,(n-np.arange(n))/(SR*0.6))
mix=mix/np.abs(mix).max()*0.95
sf.write(f"{D}/mix.wav",np.stack([mix,mix],1),SR); print("ok", n/SR)
