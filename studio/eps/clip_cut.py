# Спільний конвеєр кліпів-воронок з довгих відео (Кліп-редактор, 22.11) — узагальнення clip_weekly2.py.
# БЕЗ нової озвучки: голос вирізається з <src>/vo.wav довгого ролика по межах речень з <src>/align.json,
# краї підганяються до найтихішого місця (щоб не різати посеред слова), 30 мс фейди.
# Сценарій кліпу (eps/clipN.py) задає SRC, CUTS, SCENES, SERIES, KEYS; build() пише vo.wav, props.json, vo_tl.json.
# Далі: bash eps/build.sh clipN (mix_ep → Remotion Ep → final.mp4), потім python3 eps/clip_cut.py loud clipN (−14 LUFS).
import json, os, sys, subprocess, numpy as np, soundfile as sf
FPS = 30
V = "аеєиіїоуюяaeiouy"

def snap(v, SR, t, back=0.35, fwd=0.02):
    """Найтихіше 20-мс вікно в [t-back, t+fwd] — точка різу між реченнями."""
    w = int(0.02 * SR); best, bt = 1e9, t
    for x in np.arange(t - back, t + fwd, 0.005):
        a = int(x * SR); seg = v[a:a + w]
        e = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 1e9
        if e < best: best, bt = e, x + 0.01
    return round(bt, 3), 20 * np.log10(best + 1e-9)

def build(SLUG, SRC, CUTS, SCENES, series, keys=None, frame0=True, list_from=1, card_s=1.8):
    """CUTS: [(a, b, [starts], [texts])] у часі vo.wav джерела; a, b — межі речень з align.json (до snap).
    SCENES: [hook, list(s)..., endcard, outro]; list_from — з якого (глобального) речення починається 2-га сцена."""
    D = f"/home/claude/eps/{SLUG}"; os.makedirs(D, exist_ok=True)
    v, SR = sf.read(f"/home/claude/eps/{SRC}/vo.wav"); assert SR == 44100
    if v.ndim > 1: v = v.mean(1)
    lead = 0.12; gap = 0.30; out = [np.zeros(int(lead * SR))]; t = lead; sents = []; tl = []; report = []
    for a0, b0, starts, texts in CUTS:
        a, ea = snap(v, SR, a0); b, eb = snap(v, SR, b0)
        report.append((a0, a, round(ea), b0, b, round(eb)))
        seg = v[int(a * SR):int(b * SR)].copy(); fd = int(0.03 * SR)
        seg[:fd] *= np.linspace(0, 1, fd); seg[-fd:] *= np.linspace(1, 0, fd)
        st = [max(a, s) for s in starts]; ends = st[1:] + [b]
        for s, e, tx in zip(st, ends, texts):
            sents.append((t + s - a, t + e - a - (0.12 if e != b else 0.05), tx))
        tl.append({"start": round(t, 3), "end": round(t + b - a, 3)}); out += [seg, np.zeros(int(gap * SR))]; t += b - a + gap
    voice_end = t - gap
    # таймлайн сцен: hook з 0; list — з речення list_from; картка «Повний розбір ↓»; outro
    stl = [0.0, sents[list_from][0] - 0.15] + [voice_end + 0.25, voice_end + 0.25 + card_s]
    total = int((stl[-1] + 2.6) * FPS)
    vo = np.concatenate(out); vo = np.concatenate([vo, np.zeros(max(0, int(total / FPS * SR) - len(vo)))])[:int(total / FPS * SR)]
    sf.write(f"{D}/vo.wav", vo, SR)
    m = np.array([float(np.sqrt(np.mean(vo[int(f / FPS * SR):int((f + 1) / FPS * SR)] ** 2))) for f in range(total)])
    m = np.clip(m / np.percentile(m[m > 0.01], 90), 0, 1); m = np.convolve(m, [.25, .5, .25], "same")
    # субтитри: слова всередині кожного речення пропорційно складам, групи ≤3 слова
    words = []; grp = 0
    for st, en, tx in sents:
        ws = tx.replace(" —", "").split(); k = [max(1, sum(c.lower() in V for c in w)) + (0.7 if w[-1] in ",.?!:»" else 0) for w in ws]
        T = sum(k); tt = st; cnt = 0
        for w, kk in zip(ws, k):
            d = (en - st) * kk / T; words.append({"w": w, "s": round(tt * FPS), "e": round((tt + d) * FPS), "g": f"g{grp}"}); tt += d; cnt += 1
            if cnt >= 3 or w[-1] in ",.?!:" or len(w) > 11: grp += 1; cnt = 0
        grp += 1
    assert len(SCENES) == len(stl), (len(SCENES), len(stl))
    scenes = []
    for i, s in enumerate(SCENES):
        sc = dict(s); sc["from"] = round(stl[i] * FPS); sc["to"] = round(stl[i + 1] * FPS) if i + 1 < len(stl) else total; scenes.append(sc)
    props = {"series": series, "total": total, "scenes": scenes, "words": words, "mouth": [round(x, 3) for x in m.tolist()]}
    if keys: props["keys"] = keys
    if frame0 is not None: props["frame0"] = frame0
    json.dump(props, open(f"{D}/props.json", "w"), ensure_ascii=False)
    json.dump(tl, open(f"{D}/vo_tl.json", "w"))
    print(SLUG, "total", total, f"{total / FPS:.1f}s", "voice", f"{voice_end:.1f}s", [(s["kind"], s["from"]) for s in scenes])
    for r in report: print("  cut a %.2f→%.3f (%d dB)  b %.2f→%.3f (%d dB)" % r)

def loud(SLUG, target=-14.0):
    """Гучність final.mp4 → target LUFS (лінійне підсилення, відео без перекодування); перевірка True Peak ≤ −1 dBTP."""
    D = f"/home/claude/eps/{SLUG}"
    def meas(p):
        r = subprocess.run(["ffmpeg", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        s = r[r.rfind("Summary:"):]; I = float(s.split("I:")[1].split("LUFS")[0]); P = float(s.split("Peak:")[1].split("dBFS")[0]); return I, P
    I, P = meas(f"{D}/final.mp4"); g = target - I
    if abs(g) > 0.3:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/final.mp4", "-c:v", "copy", "-af", f"volume={g:.2f}dB",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", f"{D}/final_l.mp4"], check=True)
        os.replace(f"{D}/final_l.mp4", f"{D}/final.mp4")
    I2, P2 = meas(f"{D}/final.mp4")
    print(SLUG, f"LUFS {I:.1f} → {I2:.1f}, true peak {P2:.1f} dBTP", "OK" if abs(I2 - target) <= 1 and P2 <= -1 else "CHECK")

if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "loud":
    loud(sys.argv[2])
