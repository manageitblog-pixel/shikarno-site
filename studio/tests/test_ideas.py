"""Тести прогнозу ideas.py без бази (CSO 28.11, аудит прогнозів 28.11): digest-prior, p_zero_feed, прогноз без ідеї.
python3 -m unittest studio/tests/test_ideas.py
"""
import json, math, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "yt"))
import ideas  # noqa: E402

S = {"tier": dict(n=11, med=170, p25=74, p75=336)}


class Priors(unittest.TestCase):
    def test_digest_prior_is_own_median(self):
        p = ideas.priors({})
        self.assertAlmostEqual(p["digest"], round(math.log(51) / math.log(201), 2), places=2)
        self.assertEqual(p["guide"], 0.6)

    def test_length_mult_unchanged(self):   # length 1.0 відхилено до бектесту 01.12
        self.assertEqual(ideas.length_mult({"length": 43}), 0.85)
        self.assertEqual(ideas.length_mult({"length": 52}), 0.8)


class Forecast(unittest.TestCase):
    def test_short_has_p_zero(self):
        f = ideas.forecast({"format": "tier", "title": "Тір-лист"}, S, ideas.priors(S), at="2026-11-28T17:00Z")
        self.assertEqual(f["p_zero_feed"], ideas.P_ZERO)
        self.assertEqual((f["med"], f["n"], f["at"]), (170, 11, "2026-11-28T17:00Z"))

    def test_long_has_no_p_zero(self):
        f = ideas.forecast({"format": "digest"}, S, ideas.priors(S))
        self.assertNotIn("p_zero_feed", f)


class ShortOnly(unittest.TestCase):   # 28.11: шоу #3 S_6k_2vDGTM (13:30, формат sec) отримало p_zero_feed 0.35
    def test_long_show_in_short_format(self):
        f = ideas.forecast({"format": "sec", "length": 35, "hook": "you"}, S, ideas.priors(S), dur=810)
        self.assertNotIn("p_zero_feed", f)
        self.assertEqual(f["dur_s"], 810)

    def test_short_by_duration(self):
        self.assertEqual(ideas.forecast({"format": "sec"}, S, ideas.priors(S), dur=35)["p_zero_feed"], ideas.P_ZERO)
        self.assertTrue(ideas.is_short({"format": "sec"}, 180))
        self.assertFalse(ideas.is_short({"format": "sec"}, 181))

    def test_flags_without_duration(self):
        self.assertFalse(ideas.is_short({"format": "tier", "short": False}))
        self.assertFalse(ideas.is_short({"format": "tier", "dur_s": 600}))
        self.assertTrue(ideas.is_short({"format": "tier"}))
        self.assertFalse(ideas.is_short({"format": "digest"}, 40))   # довгий формат лишається довгим

    def test_link_uses_duration(self):
        tmp = tempfile.TemporaryDirectory(); F, st = ideas.F, ideas.stats
        try:
            ideas.F = os.path.join(tmp.name, "ideas.json"); ideas.stats = lambda today=None: S
            json.dump([{"id": "38", "format": "sec", "title": "Шоу", "status": "approved"}], open(ideas.F, "w"))
            ideas.link("38", "vidL", at="2026-11-29T12:00:00Z", dur="810")
            fc = json.load(open(ideas.F))[0]["forecast_at_publish"]
            self.assertNotIn("p_zero_feed", fc)
            self.assertEqual(fc["dur_s"], 810)
        finally:
            ideas.F, ideas.stats = F, st; tmp.cleanup()


class Record(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "forecasts.json")
        self._stats = ideas.stats
        ideas.stats = lambda today=None: S

    def tearDown(self):
        ideas.stats = self._stats
        self.tmp.cleanup()

    def test_record_once(self):
        r = ideas.record("vid1", {"format": "tier", "title": "А", "length": 30}, at="2026-11-28T17:00Z", path=self.path)
        self.assertEqual(r["med"], 170)
        self.assertEqual(r["p_zero_feed"], ideas.P_ZERO)
        r2 = ideas.record("vid1", {"format": "news", "title": "Б"}, path=self.path)   # не переписує
        self.assertEqual(r2["format"], "tier")
        self.assertEqual(list(json.load(open(self.path))), ["vid1"])

    def test_record_long_no_p_zero(self):
        r = ideas.record("vidS", {"format": "sec", "title": "Шоу"}, path=self.path, dur=810)
        self.assertNotIn("p_zero_feed", r)


if __name__ == "__main__":
    unittest.main()
