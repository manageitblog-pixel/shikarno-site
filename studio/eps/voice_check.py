"""Перевірка тембру Байта: медіана F0 озвучки vs еталон ep26_tier2 (вірусний Short). Власник 3.11: «тримай голос і марку».
usage: python3 voice_check.py <dir_or_wav> → OK/BAD, код виходу 1 якщо відхилення > TOL.

v2 (23.11, docs/research/voice-f0-2026-11-23.md) — той самий стандарт, виміряний коректно:
  * уся озвучка, а не перші 25 с (у частинах гайду 54–89 с старий замір бачив 28–46 % звуку);
  * захист від октавних помилок: кадри поза [m0/1.5, 1.5·m0] від першої медіани відкидаються
    (стара АКФ давала 8–29 % кадрів >200 Гц і завищувала медіану на ~6 Гц vs Praat);
  * параболічне уточнення лагу (крок 0.7 Гц → суб-семпл).
  Звірено з Praat (parselmouth to_pitch_ac): різниця 0.2±2.0 Гц на 21 дублі guide1 + еталоні.
  Еталон той самий файл ep26_tier2/vo_raw.wav: нова шкала 141.4 Гц (стара 145.5; номінал «143» —
  між Praat 141.5 і pYIN 145.8). REF = 141.5, допуск той самий ±8 Гц. Друкує також стару цифру (legacy).
"""
import sys
import numpy as np

REF, TOL = 141.5, 8.0
# Перевизначення для одного довгого відео, щоб нові частини звучали як уже озвучені (рішення COO 23.11, guide1): VC_REF/VC_TOL.
import os as _os
REF = float(_os.environ.get("VC_REF", REF)); TOL = float(_os.environ.get("VC_TOL", TOL))
REF_LEGACY = 143.0
FMIN, FMAX, RMS_GATE, VOICING = 70.0, 400.0, 0.02, 0.3


def track(x, sr, interp=True):
    """(t, f0) по кадрах 40 мс / крок 20 мс; АКФ як у v1 (поріг гучності 0.02 RMS, вокалізація 0.3)."""
    x = np.asarray(x, np.float64)
    fr = int(0.04 * sr); hop = fr // 2; lo, hi = int(sr / FMAX), int(sr / FMIN)
    ts, fs = [], []
    for i in range(0, len(x) - fr, hop):
        s = x[i:i + fr]
        if np.sqrt(np.mean(s ** 2)) < RMS_GATE: continue
        s = s - s.mean(); c = np.correlate(s, s, "full")[fr - 1:]
        k = lo + int(np.argmax(c[lo:hi]))
        if c[k] <= VOICING * c[0]: continue
        kk = float(k)
        if interp and lo < k < hi - 1:
            a, b, d = c[k - 1], c[k], c[k + 1]; den = a - 2 * b + d
            if den < 0: kk = k + 0.5 * (a - d) / den
        ts.append(i / sr); fs.append(sr / kk)
    return np.array(ts), np.array(fs)


def measure(x, sr):
    """dict(f0 — медіана по всьому файлу з октавним захистом, head25, legacy — як v1, windows — медіани по 20 с)."""
    t, f = track(x, sr)
    if len(f) == 0:
        return dict(f0=float("nan"), head25=float("nan"), legacy=float("nan"), windows=[], frames=0)
    m0 = np.median(f); keep = (f > m0 / 1.5) & (f < m0 * 1.5); t, f = t[keep], f[keep]
    tl, fl = track(x[:sr * 25], sr, interp=False)
    dur = len(x) / sr
    win = [round(float(np.median(f[(t >= a) & (t < a + 20)])), 1)
           for a in np.arange(0, max(dur - 5, 1), 20) if ((t >= a) & (t < a + 20)).sum() >= 20]
    return dict(f0=float(np.median(f)), head25=float(np.median(f[t < 25])) if (t < 25).any() else float("nan"),
                legacy=float(np.median(fl)) if len(fl) else float("nan"), windows=win, frames=int(len(f)))


def verdict(f0):
    return bool(abs(f0 - REF) <= TOL)


def main(argv):
    import soundfile as sf
    p = argv[1]; p = p if p.endswith(".wav") else p.rstrip("/") + "/vo_raw.wav"
    w, sr = sf.read(p, dtype="float32"); w = w.mean(1) if w.ndim > 1 else w
    r = measure(w, sr); ok = verdict(r["f0"])
    # деталі першим рядком (без «F0 », щоб regex run_voice брав головну цифру), вердикт — останнім (policy бере хвіст stdout)
    print(f"деталі: перші 25 с {r['head25']:.1f} Гц; по 20 с {r['windows']}; стара шкала v1 {r['legacy']:.1f} vs {REF_LEGACY}")
    print(f"{'OK' if ok else 'BAD'} F0 {r['f0']:.1f} Hz (еталон {REF}±{TOL}, весь файл)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
