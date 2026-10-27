import sys, json, re, numpy as np, soundfile as sf, importlib, time
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
ep=importlib.import_module(sys.argv[1]); voice=sys.argv[2] if len(sys.argv)>2 else "Sadachbia"
out=f"/home/claude/eps/{ep.SLUG}"; import os; os.makedirs(out,exist_ok=True)
SR=24000; parts=[np.zeros(int(0.2*SR),dtype=np.float32)]; t=0.2; tl=[]; log=[]
for i,s in enumerate(ep.SCENES):
    best=None
    for attempt in range(3):
        tts(s["gsay"],voice,f"{out}/sc{i}.wav"); time.sleep(4)
        w,sr=sf.read(f"{out}/sc{i}.wav",dtype="float32"); assert sr==SR
        idx=np.where(np.abs(w)>0.01)[0]; w=w[max(0,idx[0]-480):idx[-1]+1200]
        hyp=asr(w,sr); e=wer(s["text"],hyp)
        if best is None or e<best[0]: best=(e,w,hyp)
        if e<=0.25: break
    e,w,hyp=best; log.append((i,round(e,2),hyp)); print(i,round(e,2),hyp,flush=True)
    tl.append({"start":t,"end":t+len(w)/SR}); parts+=[w,np.zeros(int(0.12*SR),dtype=np.float32)]; t+=len(w)/SR+0.12
a=np.concatenate(parts); sf.write(f"{out}/vo_raw.wav",a,SR); json.dump(tl,open(f"{out}/vo_tl.json","w"))
print("total",round(len(a)/SR,1))
