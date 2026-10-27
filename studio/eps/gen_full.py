"""Одна TTS-заявка на весь епізод → розбиття на сцени за найдовшими паузами → Whisper-звірка."""
import sys, json, re, os, numpy as np, soundfile as sf, importlib
sys.path.insert(0,"/home/claude/gem"); sys.path.insert(0,"/home/claude/eps")
from gtts import tts
import sherpa_onnx
d="/home/claude/sherpa-onnx-whisper-small/"
R=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d+"small-encoder.int8.onnx",decoder=d+"small-decoder.int8.onnx",tokens=d+"small-tokens.txt",language="uk",task="transcribe",num_threads=2)
def words(s): return re.sub(r"[^\w' ]"," ",s.lower().replace("ʼ","'")).split()
def wer(ref,hyp):
    a,b=words(ref),words(hyp); D=np.zeros((len(a)+1,len(b)+1)); D[:,0]=range(len(a)+1); D[0,:]=range(len(b)+1)
    for i in range(1,len(a)+1):
        for j in range(1,len(b)+1): D[i,j]=min(D[i-1,j]+1,D[i,j-1]+1,D[i-1,j-1]+(a[i-1]!=b[j-1]))
    return D[-1,-1]/max(1,len(a))
def asr(w,sr):
    s=R.create_stream(); s.accept_waveform(sr,np.concatenate([w,np.zeros(sr//3,dtype=np.float32)])); R.decode_stream(s); return s.result.text
def pauses(w,sr,thr=0.012,minlen=0.05):
    env=np.convolve(np.abs(w),np.ones(int(sr*0.02))/int(sr*0.02),"same"); quiet=env<thr
    res=[]; i=0; n=len(w)
    while i<n:
        if quiet[i]:
            j=i
            while j<n and quiet[j]: j+=1
            if (j-i)/sr>=minlen and i>0 and j<n: res.append((i,j))
            i=j
        else: i+=1
    return res
def split_scenes(w,sr,texts):
    """межа сцени = довга пауза, після якої ~2.5 с аудіо збігаються з ПОЧАТКОМ наступної сцени,
    а до якої — з КІНЦЕМ поточної (короткі Whisper-перевірки)"""
    N=len(texts); P=[((a+b)//2,(b-a)/sr) for a,b in pauses(w,sr,thr=0.03,minlen=0.2)]
    L=np.array([len(t) for t in texts],float); exp=np.cumsum(L)[:-1]/L.sum()*len(w)
    win=int(2.5*sr); bounds=[0]
    for k in range(N-1):
        head=" ".join(words(texts[k+1])[:4]); tail=" ".join(words(texts[k])[-4:])
        cand=sorted([(m,d) for m,d in P if m>bounds[-1]+sr and abs(m-exp[k])<8*sr],key=lambda x:abs(x[0]-exp[k]))[:6]
        best=None
        for m,d in cand:
            h=asr(w[m:m+win],sr); t=asr(w[max(bounds[-1],m-win):m],sr)
            hw=" ".join(words(h)[:4]); tw=" ".join(words(t)[-4:])
            sc=wer(head,hw)+wer(tail,tw)+abs(m-exp[k])/sr*0.03
            if best is None or sc<best[0]: best=(sc,m)
        bounds.append(best[1])
    bounds.append(len(w))
    return [w[bounds[i]:bounds[i+1]] for i in range(N)]
def trim(x,sr):
    idx=np.where(np.abs(x)>0.005)[0]; return x[max(0,idx[0]-480):idx[-1]+int(0.12*sr)]
if __name__=="__main__":
    ep=importlib.import_module(sys.argv[1]); voice=sys.argv[2]; model=sys.argv[3]
    out=f"/home/claude/eps/{ep.SLUG}"; os.makedirs(out,exist_ok=True)
    texts=[s["gsay"] for s in ep.SCENES]
    raw=f"{out}/full_{model}_{voice}.wav"
    if not os.path.exists(raw): print(tts("\n\n".join(texts),voice,raw,model=model))
    w,sr=sf.read(raw,dtype="float32")
    segs=[trim(x,sr) for x in split_scenes(w,sr,texts)]
    SR=sr; parts=[np.zeros(int(0.2*SR),dtype=np.float32)]; t=0.2; tl=[]
    for i,(s,x) in enumerate(zip(ep.SCENES,segs)):
        hyp=asr(x,sr); print(i, round(wer(s["text"],hyp),2), "%.1fs"%(len(x)/sr), hyp, flush=True)
        tl.append({"start":t,"end":t+len(x)/SR}); parts+=[x,np.zeros(int(0.12*SR),dtype=np.float32)]; t+=len(x)/SR+0.12
    a=np.concatenate(parts); sf.write(f"{out}/vo_raw.wav",a,SR); json.dump(tl,open(f"{out}/vo_tl.json","w"))
    print("total",round(len(a)/SR,1))
