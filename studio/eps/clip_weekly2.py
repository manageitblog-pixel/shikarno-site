# Кліп-воронка з шоу «ШІ за тиждень #2» (aTUsauz53rs, 0:44–1:18) → Short 1080×1920, ідея №8 дошки.
# БЕЗ нової озвучки: голос вирізано з weekly2/vo.wav (ті самі речення, що в шоу; факти — Google, блог, 16.11.2026).
# Запуск: python3 eps/clip_weekly2.py && bash eps/build.sh clip_weekly2  (mix_ep → Remotion Ep → final.mp4)
import json, os, numpy as np, soundfile as sf
SRC="/home/claude/eps/weekly2"; SLUG="clip_weekly2"; D=f"/home/claude/eps/{SLUG}"; FPS=30
# шматки озвучки шоу: (початок, кінець, [межі речень], текст речень) — межі з weekly2/align.json, краї — по тиші
CUTS=[(44.50,50.80,[44.568,48.917],["Раніше, якщо вимкнути історію, чати зберігались сімдесят дві години.","Тепер — близько двох місяців."]),
      (58.10,77.85,[58.175,63.066,69.962,75.682],["Перше: «вимкнув історію» більше не означає «за три дні все зникло».",
        "Друге: тепер можна лишити історію, але вимкнути навчання на твоїх чатах — це окремий перемикач.",
        "Третє: частину розмов перевіряють рецензенти, і такі чати зберігаються до трьох років.","Тож особисте в чат не пиши."])]
SCENES=[
 dict(kind="hookIcon", label="", title="", icon="chat", tone="news", badge="72 год → 2 міс",
      hook="Твої чати в Gemini живуть *2 місяці?*"),
 dict(kind="list", label="GOOGLE · 16.11.2026", title="Що змінилось у Gemini",
      items=[["chat","Не стерто за 3 дні"],["shield","Навчання окремо"],["warning","Частину читають люди"]]),
 dict(kind="hookIcon", label="ПОВНИЙ ВИПУСК ↓", title="ШІ за тиждень #2", icon="video", tone="news", badge="ще 5 новин"),
 dict(kind="outro", label="", title=""),
]
if __name__=="__main__":
    os.makedirs(D,exist_ok=True)
    v,SR=sf.read(f"{SRC}/vo.wav"); assert SR==44100
    lead=0.12; gap=0.30; out=[np.zeros(int(lead*SR))]; t=lead; sents=[]; tl=[]
    for a,b,starts,texts in CUTS:
        seg=v[int(a*SR):int(b*SR)].copy(); fd=int(0.03*SR); seg[:fd]*=np.linspace(0,1,fd); seg[-fd:]*=np.linspace(1,0,fd)
        ends=starts[1:]+[b]
        for s,e,tx in zip(starts,ends,texts): sents.append((t+s-a,t+e-a-(0.12 if e!=b else 0.05),tx))
        tl.append({"start":round(t,3),"end":round(t+b-a,3)}); out+= [seg,np.zeros(int(gap*SR))]; t+=b-a+gap
    tl.append({"start":round(t+0.2,3),"end":round(t+2.0,3)})   # картка «Повний випуск» (без голосу)
    tl.append({"start":round(t+2.4,3),"end":round(t+2.9,3)})   # outro (підписка), +2.2 с у total
    vo=np.concatenate(out); total=int((tl[-1]["end"]+2.2)*FPS)
    vo=np.concatenate([vo,np.zeros(max(0,int(total/FPS*SR)-len(vo)))]); sf.write(f"{D}/vo.wav",vo,SR)
    # рот Байта — як у prep_ep.py
    m=np.array([float(np.sqrt(np.mean(vo[int(f/FPS*SR):int((f+1)/FPS*SR)]**2))) for f in range(total)])
    m=np.clip(m/np.percentile(m[m>0.01],90),0,1); m=np.convolve(m,[.25,.5,.25],"same")
    # субтитри: слова розкладаю всередині КОЖНОГО речення (межі з align.json), групи по ≤3 слова
    V="аеєиіїоуюяaeiouy"; words=[]; si=0
    for sc_i,(a,b,starts,texts) in enumerate(CUTS):
        grp=0
        for st,en,tx in sents[si:si+len(texts)]:
            ws=tx.replace(" —","").split(); k=[max(1,sum(c.lower() in V for c in w))+(0.7 if w[-1] in ",.?!:»" else 0) for w in ws]
            T=sum(k); tt=st; cnt=0
            for w,kk in zip(ws,k):
                d=(en-st)*kk/T; words.append({"w":w,"s":round(tt*FPS),"e":round((tt+d)*FPS),"g":f"{sc_i}-{grp}"}); tt+=d; cnt+=1
                if cnt>=3 or w[-1] in ",.?!:" or len(w)>11: grp+=1; cnt=0
            grp+=1
        si+=len(texts)
    scenes=[]
    for i,(s,x) in enumerate(zip(SCENES,tl)):
        nxt=tl[i+1]["start"] if i+1<len(tl) else total/FPS
        sc=dict(s); sc.update({"from":round(x["start"]*FPS),"to":round(nxt*FPS)}); scenes.append(sc)
    scenes[0]["from"]=0
    json.dump({"series":"ШІ ЗА ТИЖДЕНЬ #2","total":total,"scenes":scenes,"words":words,"mouth":[round(x,3) for x in m.tolist()]},
              open(f"{D}/props.json","w"),ensure_ascii=False)
    json.dump(tl,open(f"{D}/vo_tl.json","w"))
    print(SLUG,total,total/FPS,[(s["kind"],s["from"]) for s in scenes])
