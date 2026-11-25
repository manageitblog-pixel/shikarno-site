"""Оркестратор озвучки наперед: guide1 (по частинах, calm) потім Shorts ep83..ep86 (hype, через gen_full).
Зупиняється на першому RuntimeError квоти. Лог у LOG (JSON-рядки)."""
import sys, os, json, time, subprocess, shutil, re, difflib, importlib
import numpy as np, soundfile as sf
sys.path.insert(0, "/home/claude/eps"); sys.path.insert(0, "/home/claude/gem")
import gen_full as G
import gtts
import voice_check as VC  # REF — еталон F0 у шкалі чекера (v2: 141.5)
LOG = os.environ.get("VOICE_LOG", "/home/claude/eps/voice_log.jsonl")
MODEL, VOICE = "gemini-3.8-flash-tts", "Sadachbia"
REQ = {"ok": 0}
def log(**k):
    # 25.11: поле "d" (дата UTC) — інакше доби в voice_log плутаються
    k["t"] = time.strftime("%H:%M:%SZ", time.gmtime()); k["d"] = time.strftime("%Y-%m-%d", time.gmtime()); print(json.dumps(k, ensure_ascii=False), flush=True)
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
    # 24.11 власник: «Чому якість страждає?» — у guide1 ч.3/ч.11 пішли фолбеки 139/113 Гц (норма 128,5±8), бо після 2 дублів
    # брали найкращий будь-який. Тепер: дублі нумеруються наскрізно між запусками, і поза нормою частина НЕ стає partN.wav,
    # доки не вичерпано MAX_TAKES (за замовчуванням 6) — оркестратор перезапише її в наступному вікні квоти.
    prev = len([f for f in os.listdir(tk) if re.match(rf"part{pi}_take\d+_f0_", f)])
    max_takes = int(os.environ.get("MAX_TAKES", "6"))
    for take in (prev + 1, prev + 2):
        if os.path.exists(raw): os.remove(raw)
        try:
            tts_call("\n\n".join(texts), raw)
        except RuntimeError:
            if best is None: raise
            # 429 на другому дублі: дубль збережено в takes/; у partN.wav — лише чистий (24.11: брудний чекає наступного вікна)
            if best[0] == 0:
                shutil.copy(f"{tk}/part{pi}_take{best[1]}_f0_{best[2]:.1f}.wav", raw)
                log(ev="part_final", part=pi, take=best[1], f0=best[2], clean=True, note="take2 quota")
            else:
                log(ev="part_retry_later", part=pi, best_take=best[1], f0=best[2], note="take2 quota")
            raise
        F, ok = f0(raw); w, sr = sf.read(raw, dtype="float32")
        segs = [G.trim(x, sr) for x in G.split_scenes(w, sr, texts)]
        au = [audit_seg(x, sr, dg.SEGS[i]["gsay"]) for i, x in zip(idxs, segs)]
        shutil.copy(raw, f"{tk}/part{pi}_take{take}_f0_{F:.1f}.wav")
        # повтор — лише на абзацах ≥ 8 слів: заголовок «Розділ перший — безпека» (3 слова) ASR чує як «без пека» → 1,33 (хибно, weekly3 ч.0)
        rep = any(a["ratio"] > 1.3 and len(words(dg.SEGS[i]["gsay"])) >= 8 for i, a in zip(idxs, au))
        log(ev="part", part=pi, take=take, f0=F, f0_ok=ok, dur=round(len(w) / sr, 1),
            audit=[dict(seg=i, ratio=a["ratio"], match=a["match"]) for i, a in zip(idxs, au)], repeat_suspect=rep)
        json.dump(dict(f0=F, ok=ok, audit=[dict(seg=i, **a) for i, a in zip(idxs, au)]),
                  open(f"{tk}/part{pi}_take{take}_audit.json", "w"), ensure_ascii=False, indent=1)
        sc = (0 if ok else 1) + (1 if rep else 0)
        if best is None or sc < best[0] or (sc == best[0] and abs(F - float(os.environ.get("VC_REF", VC.REF))) < abs(best[2] - float(os.environ.get("VC_REF", VC.REF)))): best = (sc, take, F)
        if ok and not rep: break
    if os.path.exists(raw): os.remove(raw)
    if best[0] > 0 and take < max_takes:
        log(ev="part_retry_later", part=pi, best_take=best[1], f0=best[2], takes=take, max_takes=max_takes); return
    shutil.copy(f"{tk}/part{pi}_take{best[1]}_f0_{best[2]:.1f}.wav", raw)
    log(ev="part_final", part=pi, take=best[1], f0=best[2], clean=best[0] == 0, **({} if best[0] == 0 else {"needs_review": True}))
def short(mod):
    ep = importlib.import_module(mod); D = f"/home/claude/eps/{ep.SLUG}"; os.makedirs(f"{D}/takes", exist_ok=True)
    if os.path.exists(f"{D}/vo.wav"): return  # уже озвучено — не витрачати квоту
    # 24.11: «ШІ» великими в gsay TTS читає як «ей-ай»/«ша» (ep83 outro, ASR ep84 «ша для вчителя»); довгі мають
    # tts-заміну ШІ→«штучний інтелект», Shorts — ні. Не палимо квоту: спершу виправити gsay у сценарії.
    bad = [i for i, s in enumerate(ep.SCENES) if re.search(r"(?<![А-ЯІЇЄҐа-яіїєґ])ШІ(?![а-яіїєґ])", s.get("gsay", ""))]
    if bad: log(ev="gsay_lint", ep=mod, scenes=bad, fix="ШІ → «штучний інтелект» або «ші» у gsay"); return
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
        if best is None or abs(F - float(os.environ.get("VC_REF", VC.REF))) < abs(best[1] - float(os.environ.get("VC_REF", VC.REF))): best = (take, F)
        if ok: break
    ref = float(os.environ.get("VC_REF", VC.REF))
    fb = [f for f in os.listdir(f"{D}/takes") if re.match(r"vo_fallback_f0_[\d.]+_raw\.wav$", f)]
    if fb:  # QA 23.11: запасний дубль (з таймлайном) лишається, якщо новий не ближчий до еталона
        fF = float(re.search(r"f0_([\d.]+)_raw", fb[0]).group(1))
        if abs(fF - ref) <= abs(best[1] - ref):
            base = fb[0][:-len("_raw.wav")]
            shutil.copy(f"{D}/takes/{base}_raw.wav", f"{D}/vo_raw.wav"); shutil.copy(f"{D}/takes/{base}_tl.json", f"{D}/vo_tl.json")
            log(ev="short_fallback_kept", ep=mod, new_f0=best[1], fallback_f0=fF); best = None
    if best is not None:
        for f in ("vo_raw.wav", "vo_tl.json"): shutil.copy(f"{D}/takes/take{best[0]}_{f}", f"{D}/{f}")
    best = best or (0, fF)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/vo_raw.wav", "-af",
                    "highpass=f=60,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7",
                    "-ar", "44100", f"{D}/vo.wav"], check=True)
    a = subprocess.run([sys.executable, "/home/claude/eps/audit_vo.py", mod, "--json"], capture_output=True, text=True)
    js = json.loads(a.stdout.strip().splitlines()[-1])
    log(ev="short_final", ep=mod, take=best[0], f0=best[1], overall_match=js["overall_match"],
        segs=[(s["i"], s["len_ratio"], s["match"]) for s in js["segments"]], dur=js["duration_s"])
if __name__ == "__main__":
    # 25.11 COO: один оркестратор за раз — Диспетчер :17, нагадування guide1 09:00Z і ручні запуски перетинались би
    # у вікні 08–09Z (пачка ~30 хв) і писали б той самий partN.wav. Другий запуск просто виходить.
    import fcntl
    _lk = open("/home/claude/eps/.run_voice.lock", "w")
    try:
        fcntl.flock(_lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log(ev="skip_locked", note="інший run_voice.py уже працює"); sys.exit(0)
    try:
        # guide1: частини 0–9 озвучено старим calm (за v2-вимірювачем медіана 128,5 Гц) → решту частин тим самим промптом
        # і в межах власної смуги відео 128,5±8, щоб висота не стрибала посеред ролика (рішення COO 23.11, ops policy).
        PER_GUIDE = {"guide1": {"TTS_PACE": "calm_v1", "VC_REF": "128.5", "VC_TOL": "6"},
                     # 25.11 COO: перезапис ч.4 (121,2 BAD) і ч.9 (136,7 — стрибок +11/−12 Гц до сусідів 125,3/124,2) — смуга сусідів
                     # 126±5, інакше 136 знову «OK» у 130±8. Інші частини вже є й не перезаписуються.
                     "guide2": {"VC_REF": "126", "VC_TOL": "5"},  # calm v2 дав 135,6/129,9/128,5/126,1 — тест v2 не пройшов (≥133,5 у 2 з 3); смуга власної медіани, щоб не палити квоту
                     # шоу #3: смуга шоу #1–#2 (весь файл v2: 128,5 і 129,6; частини 121,4–136,4), а не 141,5 — інакше палить по 2 запити
                     # на частину (ч.0: 114,5/116,5/126,9). docs/research/voice-weekly3-2026-11-24.md. Остання частина (оновлення 28.11 + outro) — окремо 28.11
                     # 25.11 COO: ч.2 120,3 BAD і ч.3 135,9 (стрибок +15,6 Гц) → перезапис у смузі сусідів 126±5 (медіана частин 125,3)
                     "weekly3": {"VC_REF": "126", "VC_TOL": "5", "UPTO": "11"},
                     # гайд #3 (вихід 9.12): смуга як у гайдів #1–#2 (~128–130); 24.11 — озвучка наперед, бо черга порожня. Перед виходом — повторний фактчек (Gemini міняється швидко)
                     "guide3": {"VC_REF": "130", "VC_TOL": "8"}}
        def guide(name):
            for k in ("VC_REF", "VC_TOL"): os.environ.pop(k, None)
            os.environ.update({k: v for k, v in PER_GUIDE.get(name, {}).items() if k != "UPTO"})
            dg = importlib.import_module(name); D = f"/home/claude/eps/{dg.SLUG}"; os.makedirs(D, exist_ok=True)
            upto = int(PER_GUIDE.get(name, {}).get("UPTO", len(dg.PARTS)))
            for pi, idxs in enumerate(dg.PARTS):
                if pi >= upto: break
                if os.path.exists(f"{D}/part{pi}.wav"): continue
                os.environ["TTS_PACE"] = PER_GUIDE.get(name, {}).get("TTS_PACE", "calm"); guide_part(dg, D, pi, idxs)
        # Черга (оновлювати): guide1 25.11 → guide2 27.11 → шоу #3 29.11 (ч.0–10) → повтори Shorts ep83/ep85 (є запасні дублі)
        # 25.11 12:10Z: рестарт контейнера стер усі part*.wav; guide1 і guide2 вже залиті на YouTube — не переозвучувати (заміна копій скасована)
        # guide("guide1")
        # guide("guide2")  # CSO 23.11 — залито h5aUeuaD8OE
        guide("weekly3")  # шоу #3, вихід 29.11 12:00Z; фактчек PASS 23.11 (гайд #2 → пт 27.11, якщо QA до 26.11 20:00; у ep83/ep85 є запасні дублі)
        guide("guide3")  # 24.11 власник: «спершу результат» → довгі в черзі першими; гайд #3 (9.12, спроба 2.12)
        for k in ("VC_REF", "VC_TOL"): os.environ.pop(k, None)
        for mod in ("ep88", "ep89", "ep90"): short(mod)  # 25.11: ep83–86 уже залиті (медіа стерто рестартом) — не переозвучувати; ep88–90 вихід 30.11–2.12
        log(ev="all_done", ok_requests=REQ["ok"])
    except RuntimeError as e:
        log(ev="STOP", reason=str(e)[:300], ok_requests=REQ["ok"])
