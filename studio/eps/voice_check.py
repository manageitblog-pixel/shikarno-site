"""Перевірка тембру Байта: медіана F0 озвучки vs еталон ep26_tier2 (вірусний, 143 Гц). Власник 3.11: «тримай голос і марку».
usage: python3 voice_check.py <dir_or_wav> → OK/BAD, код виходу 1 якщо відхилення > TOL."""
import sys, numpy as np, soundfile as sf
REF, TOL = 143.0, 8.0
def f0(x, sr):
    fr = int(0.04*sr); hop = fr//2; out = []
    for i in range(0, len(x)-fr, hop):
        s = x[i:i+fr]
        if np.sqrt(np.mean(s**2)) < 0.02: continue
        s = s-s.mean(); c = np.correlate(s, s, 'full')[fr-1:]; lo, hi = int(sr/400), int(sr/70)
        k = lo+np.argmax(c[lo:hi])
        if c[k] > 0.3*c[0]: out.append(sr/k)
    return np.median(out)
p = sys.argv[1]; p = p if p.endswith(".wav") else p.rstrip("/")+"/vo_raw.wav"
w, sr = sf.read(p, dtype="float32"); w = w.mean(1) if w.ndim > 1 else w
m = f0(w[:sr*25], sr); ok = abs(m-REF) <= TOL
print(f"{'OK' if ok else 'BAD'} F0 {m:.1f} Hz (еталон {REF}±{TOL})"); sys.exit(0 if ok else 1)
