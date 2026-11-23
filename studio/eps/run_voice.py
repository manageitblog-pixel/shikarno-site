"""Оркестратор озвучки наперед: guide1 (по частинах, calm) потім Shorts ep83..ep86 (hype, через gen_full).
Зупиняється на першому RuntimeError квоти. Лог у LOG (JSON-рядки)."""
import sys, os, json, time, subprocess, shutil, re, difflib, importlib
import numpy as np, soundfile as sf
sys.path.insert(0, "/home/claude/eps"); sys.path.insert(0, "/home/claude/gem")
import gen_full as G
import gtts
LOG = os.environ.get("VOICE_LOG", "/home/claude/eps/voice_log.jsonl")
MODEL, VOICE = "gemini-3.8-flash-tts", "Sadachbia"
REQ = {"ok": 0}
def log(**k):
    k["t"] = time.strftime("%H:%M:%SZ", time.gmtime()); print(json.dumps(k, ensure_ascii=False), flush=True)
    open(LOG, "a").write(json.dumps(k, ensure_ascii=False) + "\n")
def f0(path):
    r = subprocess.run([sys.executable, "/home/claude/eps/voice_check.py", path], capture_output=True, text=True)
    m = re.search(r"F0 ([\d.]+)", r.stdout); return float(m.group(1)), r.returncode == 0
def words(s): return re.findall(r"[а-яіїєґa-z0-9']+", s.lower().replace("ʼ", "'"))
def audit_seg(x, sr, exp):
    ps = [b for a, b in G.pauses(x, sr) if b - a > 2400] + [len(x)]; pieces = []; cur = 0
    for c in ps:
        while c - cur > 8 * sr: pieces.append((cur, cur + 7 * sr)); cur += 7 * sr
        if c - cur >= 4 * sr or c == len(x): pieces.append((cur, c)); cur = c
    hyp = " ".join(G.asr(x[a:b], sr) for a, b in pieces if b - a > sr * 0.3)
    we, wh = words(exp), words(hyp)
    mt = sum(b.size for b in difflib.SequenceMatcher(None, we, wh, autojunk=False).get_matching_blocks())
    return dict(ratio=round(len(wh) / max(1, len(we)), 2), match=round(mt / max(1, len(we)), 2), hyp=hyp)
def tts_call(text, out):
    gap = 20 - (time.time() - tts_call.last)
    if gap > 0: time.sleep(gap)
    try:
        r = gtts.tts(text, VOICE, out, model=MODEL); REQ["ok"] += 1; log(ev="tts_ok", n=REQ["ok"], out=out, res=str(r)); return True
    finally:
        tts_call.last = time.time()
tts_call.last = 0
def guide_part(dg, D, pi, idxs):
    raw = f"{D}/part{pi}.wav"; texts = [dg.SEGS[i]["gsay"] for i in idxs]
    tk = f"{D}/takes"; os.makedirs(tk, exist_ok=True)
    best = None
    for take in (1, 2):
        if os.path.exists(raw): os.remove(raw)
        tts_call("\n\n".join(texts), raw)
        F, ok = f0(raw); w, sr = sf.read(raw, dtype="float32")
        segs = [G.trim(x, sr) for x in G.split_scenes(w, sr, texts)]
        au = [audit_seg(x, sr, dg.SEGS[i]["gsay"]) for i, x in zip(idxs, segs)]
        shutil.copy(raw, f"{tk}/part{pi}_take{take}_f0_{F:.1f}.wav")
        rep = any(a["ratio"] > 1.3 for a in au)
        log(ev="part", part=pi, take=take, f0=F, f0_ok=ok, dur=round(len(w) / sr, 1),
            audit=[dict(seg=i, ratio=a["ratio"], match=a["match"]) for i, a in zip(idxs, au)], repeat_suspect=rep)
        json.dump(dict(f0=F, ok=ok, audit=[dict(seg=i, **a) for i, a in zip(idxs, au)]),
                  open(f"{tk}/part{pi}_take{take}_audit.json", "w"), ensure_ascii=False, indent=1)
        sc = (0 if ok else 1) + (1 if rep else 0)
        if best is None or sc < best[0] or (sc == best[0] and abs(F - 143) < abs(best[2] - 143)): best = (sc, take, F)
        if ok and not rep: break
    shutil.copy(f"{tk}/part{pi}_take{best[1]}_f0_{best[2]:.1f}.wav", raw)
    log(ev="part_final", part=pi, take=best[1], f0=best[2], clean=best[0] == 0)
def short(mod):
    ep = importlib.import_module(mod); D = f"/home/claude/eps/{ep.SLUG}"; os.makedirs(f"{D}/takes", exist_ok=True)
    if os.path.exists(f"{D}/vo.wav"): return  # уже озвучено — не витрачати квоту
    env = dict(os.environ, TTS_PACE="hype"); best = None
    for take in (1, 2):
        for f in os.listdir(D):
            if f.startswith("full_") and f.endswith(".wav"): os.remove(f"{D}/{f}")
        gap = 20 - (time.time() - tts_call.last)
        if gap > 0: time.sleep(gap)
        r = subprocess.run([sys.executable, "/home/claude/eps/gen_full.py", mod, VOICE, MODEL], capture_output=True, text=True, env=env)
        tts_call.last = time.time()
        err = "\n".join(l for l in r.stderr.splitlines() if "HTTP" in l or "Error" in l or "quota" in l)
        if r.returncode != 0:
            log(ev="short_fail", ep=mod, take=take, err=err[-600:])
            if "quota exhausted" in r.stderr: raise RuntimeError("quota: " + mod)
            raise RuntimeError("gen_full failed " + mod)
        REQ["ok"] += 1; log(ev="tts_ok", n=REQ["ok"], out=mod, http_notes=err[-300:])
        F, ok = f0(D)
        for f in ("vo_raw.wav", "vo_tl.json"): shutil.copy(f"{D}/{f}", f"{D}/takes/take{take}_{f}")
        log(ev="short", ep=mod, take=take, f0=F, f0_ok=ok, scenes=[l for l in r.stdout.splitlines() if re.match(r"^\d+ ", l)])
        if best is None or abs(F - 143) < abs(best[1] - 143): best = (take, F)
        if ok: break
    for f in ("vo_raw.wav", "vo_tl.json"): shutil.copy(f"{D}/takes/take{best[0]}_{f}", f"{D}/{f}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/vo_raw.wav", "-af",
                    "highpass=f=60,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7",
                    "-ar", "44100", f"{D}/vo.wav"], check=True)
    a = subprocess.run([sys.executable, "/home/claude/eps/audit_vo.py", mod, "--json"], capture_output=True, text=True)
    js = json.loads(a.stdout.strip().splitlines()[-1])
    log(ev="short_final", ep=mod, take=best[0], f0=best[1], overall_match=js["overall_match"],
        segs=[(s["i"], s["len_ratio"], s["match"]) for s in js["segments"]], dur=js["duration_s"])
if __name__ == "__main__":
    try:
        def guide(name):
            dg = importlib.import_module(name); D = f"/home/claude/eps/{dg.SLUG}"; os.makedirs(D, exist_ok=True)
            for pi, idxs in enumerate(dg.PARTS):
                if os.path.exists(f"{D}/part{pi}.wav"): continue
                os.environ["TTS_PACE"] = "calm"; guide_part(dg, D, pi, idxs)
        # Черга за датами виходу (оновлювати): guide1 25.11 → ep83 26.11 → ep84–86 → guide2 2.12 (незалежний PASS 23.11)
        guide("guide1")
        for mod in ("ep83", "ep84", "ep85", "ep86"): short(mod)
        guide("guide2")
        log(ev="all_done", ok_requests=REQ["ok"])
    except RuntimeError as e:
        log(ev="STOP", reason=str(e)[:300], ok_requests=REQ["ok"])
