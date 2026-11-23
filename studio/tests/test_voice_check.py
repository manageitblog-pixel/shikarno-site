"""Тести чекера F0 (studio/eps/voice_check.py v2). Без мережі й TTS: синтетичні «голосові» сигнали.
python3 -m unittest studio/tests/test_voice_check.py
"""
import math, sys, unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eps"))
import voice_check as VC  # noqa: E402

SR = 24000


def voice(f0, dur, amp=0.2, seed=0):
    """Гармонійний сигнал з F0 (1/k амплітуди гармонік, легкий шум) — грубий аналог вокалізованого мовлення."""
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * math.pi * f0 * k * t) / k for k in range(1, 8))
    x = amp * x / np.max(np.abs(x))
    return (x + np.random.default_rng(seed).normal(0, 0.002, len(x))).astype(np.float32)


def glide(f1, f2, dur, amp=0.2):
    t = np.arange(int(dur * SR)) / SR; ph = 2 * math.pi * np.cumsum(f1 + (f2 - f1) * t / dur) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 8))
    return (amp * x / np.max(np.abs(x))).astype(np.float32)


class Precision(unittest.TestCase):
    def test_steady_tone(self):
        for f in (118.0, 141.5, 157.0):
            r = VC.measure(voice(f, 6), SR)
            self.assertAlmostEqual(r["f0"], f, delta=0.6, msg=f)

    def test_silence_is_bad(self):
        r = VC.measure(np.zeros(SR * 5, np.float32), SR)
        self.assertTrue(math.isnan(r["f0"])); self.assertFalse(VC.verdict(r["f0"]))


class WholeFile(unittest.TestCase):
    def test_measures_whole_file_not_first_25s(self):
        # високий початок (як part4 take2: 142 у перші 25 с), далі 60 с значно нижче → весь файл BAD
        x = np.concatenate([voice(145, 25), voice(122, 60, seed=1)])
        r = VC.measure(x, SR)
        self.assertAlmostEqual(r["head25"], 145, delta=1)
        self.assertAlmostEqual(r["legacy"], 145, delta=2)        # стара логіка бачила лише початок
        self.assertAlmostEqual(r["f0"], 122, delta=1.5)
        self.assertFalse(VC.verdict(r["f0"]))
        self.assertGreaterEqual(len(r["windows"]), 4)

    def test_low_energy_frames_ignored(self):
        x = np.concatenate([voice(140, 10), voice(100, 10, amp=0.005, seed=2)])   # тихий хвіст під порогом 0.02
        self.assertAlmostEqual(VC.measure(x, SR)["f0"], 140, delta=1)


class OctaveGuard(unittest.TestCase):
    def test_octave_errors_rejected(self):
        # інтонація 120→160 Гц (справжня медіана 140) + 25 % кадрів з октавною помилкою вгору:
        # без захисту медіана повзе вгору (~147), як завищення старого чекера vs Praat
        x = np.concatenate([glide(120, 160, 15), glide(240, 320, 5)])
        t, f = VC.track(x, SR)
        self.assertGreater(np.median(f), 144)
        self.assertAlmostEqual(VC.measure(x, SR)["f0"], 140, delta=1)

    def test_reference_scale(self):
        self.assertEqual((VC.REF, VC.TOL), (141.5, 8.0))
        self.assertTrue(VC.verdict(133.5)); self.assertTrue(VC.verdict(149.5)); self.assertFalse(VC.verdict(132.9))

    @unittest.skipUnless(Path(__file__).resolve().parents[1].joinpath("eps/ep26_tier2/vo_raw.wav").exists(), "еталон поза git")
    def test_reference_file_is_ok(self):
        import soundfile as sf
        w, sr = sf.read(str(Path(__file__).resolve().parents[1] / "eps/ep26_tier2/vo_raw.wav"), dtype="float32")
        r = VC.measure(w, sr)
        self.assertAlmostEqual(r["f0"], VC.REF, delta=1.0)


if __name__ == "__main__":
    unittest.main()
