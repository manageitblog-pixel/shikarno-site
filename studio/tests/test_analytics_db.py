"""Тести збирача аналітики без мережі: утримання «немає даних» має бути NULL, а не 0 (data-quality 22.11).
python3 -m unittest studio/tests/test_analytics_db.py
"""
import os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "yt"))
import analytics_db  # noqa: E402


class NoRetention(unittest.TestCase):
    def test_small_day_without_retention(self):
        self.assertTrue(analytics_db.no_retention(2, 0.0, 0.0, 0))
        self.assertTrue(analytics_db.no_retention(1, 0, None, 0))

    def test_real_values_kept(self):
        self.assertFalse(analytics_db.no_retention(2, 45.0, 0.0, 0))   # watch_min округлюється до 0, але % є
        self.assertFalse(analytics_db.no_retention(0, 0, 0, 0))         # немає переглядів — нема чого позначати


class ChannelDaily(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._db, self._ya = analytics_db.DB, analytics_db.ya
        analytics_db.DB = os.path.join(self.tmp.name, "a.sqlite")

        def fake_ya(**q):
            if q.get("filters") == "creatorContentType==videoOnDemand":
                return {"rows": [["2026-10-03", 0], ["2026-11-10", 12.0]]}
            if q.get("filters") == "creatorContentType==shorts":
                return {"rows": [["2026-10-03", 2], ["2026-11-10", 80]]}
            return {"rows": [["2026-10-03", 2, 0, 0, 0, 0.0],          # API не дав утримання
                             ["2026-11-10", 100, 40.0, 3, 0, 612.0]]}  # лупи Shorts → clamp 100
        analytics_db.ya = fake_ya

    def tearDown(self):
        analytics_db.DB, analytics_db.ya = self._db, self._ya
        self.tmp.cleanup()

    def test_avg_pct_null_not_zero(self):
        c = analytics_db.db()
        self.assertEqual(analytics_db.sync_channel(c, start="2026-10-01", end="2026-11-20"), 2)
        got = dict(c.execute("select date, avg_pct from channel_daily").fetchall())
        self.assertIsNone(got["2026-10-03"])
        self.assertEqual(got["2026-11-10"], 100.0)
        c.close()


if __name__ == "__main__":
    unittest.main()
