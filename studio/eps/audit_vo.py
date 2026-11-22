# Повна звірка озвучки зі сценарієм: транскрибує КОЖЕН сегмент повністю (шматками по паузах ≤15 с)
# usage: python eps/audit_vo.py <script_module> [vo_raw.wav path]
import sys, json, soundfile as sf, importlib, re
JSON_OUT="--json" in sys.argv; sys.argv=[a for a in sys.argv if a!="--json"]  # --json: див. кінець файлу
REC=[]
sys.path.insert(0,"/home/claude/eps"); import gen_full as G
m=importlib.import_module(sys.argv[1]); D=f"/home/claude/eps/{m.SLUG}"
segs=getattr(m,"SCENES",None) or m.SEGS
w,sr=sf.read(sys.argv[2] if len(sys.argv)>2 else f"{D}/vo_raw.wav",dtype="float32")
tl=json.load(open(f"{D}/vo_tl.json"))
def words(s): return re.findall(r"[а-яіїєґa-z0-9']+", s.lower())
import os
ST=int(os.environ.get("START","0"))
for i,t in enumerate(tl):
    if i<ST: continue
    x=w[int(t["start"]*sr):int(t["end"]*sr)]
    ps=[b for a,b in G.pauses(x,sr) if b-a>2400]+[len(x)]
    pieces=[];cur=0
    for c in ps:
        while c-cur>8*sr: pieces.append((cur,cur+7*sr)); cur+=7*sr
        if c-cur>=4*sr or c==len(x): pieces.append((cur,c)); cur=c
    hyp=" ".join(G.asr(x[a:b],sr) for a,b in pieces if b-a>sr*0.3)
    exp=segs[i]["gsay"]; we,wh=words(exp),words(hyp)
    ratio=len(wh)/max(1,len(we))
    flag=" <<< ПЕРЕВІР (довжина)" if ratio>1.25 or ratio<0.8 else ""
    print(f"### {i} {segs[i]['kind']} {t['start']:.1f}-{t['end']:.1f}s слів {len(wh)}/{len(we)}{flag}")
    print("  ОЧІК:", exp); print("  ЧУЄМ:", hyp)
    REC.append(dict(i=i, kind=segs[i]['kind'], start=t["start"], end=t["end"], exp=we, hyp=wh, ratio=ratio))

# --json (для quality-політики studio/policy.py): word-match по сегментах, тривалість, гучність, найдовша пауза.
# Пише {D}/audit_vo.json і друкує той самий JSON останнім рядком. Без --json поведінка вище не змінюється.
if JSON_OUT:
    import difflib, math, numpy as np
    def _match(a, b):
        return sum(x.size for x in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    segs_out=[]; tot_e=tot_m=0
    for r in REC:
        mt=_match(r["exp"], r["hyp"]); tot_e+=len(r["exp"]); tot_m+=mt
        segs_out.append(dict(i=r["i"], kind=r["kind"], start=round(r["start"],2), end=round(r["end"],2),
                             words_exp=len(r["exp"]), words_heard=len(r["hyp"]), len_ratio=round(r["ratio"],3),
                             match=round(mt/max(1,len(r["exp"])),3)))
    mono=w.mean(1) if w.ndim>1 else w
    rms=float(np.sqrt(np.mean(mono**2))) if len(mono) else 0.0
    gaps=[(b-a)/sr for a,b in G.pauses(mono,sr)]
    res=dict(script=sys.argv[1], slug=m.SLUG, segments=segs_out, overall_match=round(tot_m/max(1,tot_e),3),
             duration_s=round(len(mono)/sr,2), mean_volume_db=round(20*math.log10(rms),1) if rms>0 else -200.0,
             longest_pause_s=round(max(gaps),2) if gaps else 0.0, start_segment=ST)
    json.dump(res, open(f"{D}/audit_vo.json","w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))
