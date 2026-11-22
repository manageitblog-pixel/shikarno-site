"""Тести журналу автономії (plan §12 п.21–22 + бекфіл і стани). Без мережі, тимчасова БД.
python3 -m unittest studio/tests/test_ops.py
"""
import datetime as dt, json, os, sqlite3, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ops  # noqa: E402

NOW = dt.datetime(2026, 11, 22, 16, 0, tzinfo=dt.timezone.utc)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.c = ops.db(self.dir / "ops.sqlite")

    def tearDown(self):
        self.c.close(); self.tmp.cleanup()


class AppendOnly(Base):
    def test_decisions_update_delete_blocked(self):
        ops.decide("topic_select", "eic", {"news": ["u1"]}, {"pick": "u1"}, conn=self.c)
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("update agent_decisions set output='x'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("delete from agent_decisions")
        self.assertEqual(self.c.execute("select count(*) from agent_decisions").fetchone()[0], 1)

    def test_pub_events_update_delete_blocked(self):
        ops.pub_create("ep1", "youtube", conn=self.c)
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("update pub_events set to_state='published'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("delete from pub_events")

    def test_bad_enum_rejected(self):
        with self.assertRaises(ValueError):
            ops.decide("nonsense", "eic", {}, conn=self.c)
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("insert into publications(content_id,platform,state) values('x','myspace','pending')")


class Verify(Base):
    def _fill(self):
        for i in range(5):
            ops.decide("factcheck", "factcheck", {"i": i}, {"verdict": "PASS"}, conn=self.c)
        ops.pub_create("ep1", "telegram", conn=self.c)

    def test_clean_chain_ok(self):
        self._fill()
        v = ops.verify(self.c)
        self.assertTrue(v["ok"], v["errors"]); self.assertEqual(v["decisions"], 5); self.assertEqual(v["events"], 1)

    def test_tampered_row_detected(self):
        self._fill()
        self.c.execute("drop trigger ad_no_update")
        self.c.execute("update agent_decisions set output='{\"verdict\":\"FAIL\"}' where seq=3")
        v = ops.verify(self.c)
        self.assertFalse(v["ok"])
        self.assertTrue(any("seq=3" in e for e in v["errors"]))
        self.assertTrue(any("ad_no_update" in e for e in v["errors"]))

    def test_rehashed_row_breaks_link(self):
        """Підробник перерахував hash рядка — ламається prev_hash наступного."""
        self._fill()
        self.c.executescript("drop trigger ad_no_update;")
        r = dict(self.c.execute("select * from agent_decisions where seq=2").fetchone())
        r["output"] = "forged"; h = ops._row_hash(r, ops.AD_COLS)
        self.c.execute("update agent_decisions set output=?, hash=? where seq=2", (r["output"], h))
        self.c.executescript(ops.SCHEMA)   # тригер повернуто
        v = ops.verify(self.c)
        self.assertFalse(v["ok"]); self.assertTrue(any("seq=3" in e and "prev_hash" in e for e in v["errors"]))

    def test_deleted_row_detected_in_new_file(self):
        """Копія БД без тригерів і без рядка → розрив."""
        self._fill()
        dst = self.dir / "forged.sqlite"
        f = sqlite3.connect(dst)
        f.executescript(";".join(r[0] for r in self.c.execute(
            "select sql from sqlite_master where name in ('agent_decisions','pub_events') and type='table'")))
        for t in ("agent_decisions", "pub_events"):
            rows = self.c.execute(f"select * from {t}").fetchall()
            for r in rows:
                if t == "agent_decisions" and r["seq"] == 4: continue
                f.execute(f"insert into {t} values({','.join('?' * len(r))})", tuple(r))
        f.commit(); f.close()
        v = ops.verify(ops.db(dst))
        self.assertFalse(v["ok"]); self.assertTrue(any("seq=5" in e for e in v["errors"]))


class Backfill(Base):
    def setUp(self):
        super().setUp()
        eps = self.dir / "eps"; posts = self.dir / "posts"; eps.mkdir(); posts.mkdir()
        (eps / "uploaded.json").write_text(json.dumps({"ep1_a": "VID1", "ep2_b": "VID2", "ep3_c": "VID3"}))
        (eps / "tiktok.json").write_text(json.dumps({"posted": {"file": "x"}, "posted_auto": {
            "ep1_a": {"url": "https://www.tiktok.com/@x/video/1", "postId": "p1"},
            "ep2_b": {"scheduled": "2026-11-23T13:30:00Z", "postId": "p2"}}}))
        (eps / "pending_comments.json").write_text(json.dumps({"VID3": {"at": "2026-11-25T17:00:00Z", "text": "?"}}))
        (posts / "2026-11-20-a.md").write_text('---\nkind: news\ntitle: "A"\nslug: a-post\n'
                                               'date: 2026-11-20T19:00:00+02:00\nyoutube: VID1\ntelegram_post: 77\n---\nbody')
        (posts / "2026-11-25-c.md").write_text('---\nkind: rozbir\nslug: c-post\ndate: 2026-11-25T19:00:00+02:00\n'
                                               'youtube: VID3\n---\nbody')
        self.kw = dict(conn=self.c, eps=eps, posts=posts, now_dt=NOW)

    def test_idempotent(self):
        r1 = ops.backfill(**self.kw)
        self.assertEqual(r1["total_added"], 9)
        snap = [tuple(r) for r in self.c.execute("select * from publications order by 1,2")]
        r2 = ops.backfill(**self.kw)
        self.assertEqual(r2["total_added"], 0)
        self.assertEqual(snap, [tuple(r) for r in self.c.execute("select * from publications order by 1,2")])
        self.assertEqual(self.c.execute("select count(*) from pub_events").fetchone()[0], 9)
        self.assertEqual(self.c.execute("select count(*) from agent_decisions").fetchone()[0], 1)
        self.assertTrue(ops.verify(self.c)["ok"])

    def test_mapping(self):
        ops.backfill(**self.kw)
        st = {(r["content_id"], r["platform"]): r for r in self.c.execute("select * from publications")}
        self.assertEqual(st[("ep1_a", "youtube")]["state"], "published")
        self.assertEqual(st[("ep3_c", "youtube")]["state"], "scheduled")          # прем'єра 25.11
        self.assertEqual(st[("ep1_a", "website")]["external_url"], "https://shikarno.com.ua/novyny/a-post/")
        self.assertEqual(st[("ep3_c", "website")]["external_url"], "https://shikarno.com.ua/rozbory/c-post/")
        self.assertEqual(st[("ep1_a", "telegram")]["external_id"], "77")
        self.assertEqual(st[("ep1_a", "tiktok")]["state"], "published")
        self.assertEqual(st[("ep2_b", "tiktok")]["state"], "scheduled")
        self.assertEqual(st[("ep3_c", "yt_comment")]["scheduled_at"], "2026-11-25T17:00:00Z")
        self.assertTrue(all(r["legacy"] == 1 for r in st.values()))


class StateMachine(Base):
    def test_happy_path(self):
        ops.pub_create("ep9", "youtube", conn=self.c)
        for s in ("validated", "approved_by_policy", "uploading", "uploaded", "scheduled", "published", "distributed"):
            ops.transition("ep9", "youtube", s, "test", conn=self.c)
        r = self.c.execute("select state, attempts from publications where content_id='ep9'").fetchone()
        self.assertEqual((r["state"], r["attempts"]), ("distributed", 1))
        self.assertEqual(self.c.execute("select count(*) from pub_events").fetchone()[0], 8)

    def test_forbidden_edges(self):
        ops.pub_create("ep9", "youtube", conn=self.c)
        for bad in ("published", "uploading", "rolled_back", "distributed"):
            with self.assertRaises(ValueError):
                ops.transition("ep9", "youtube", bad, "skip", conn=self.c)
        self.assertEqual(self.c.execute("select state from publications").fetchone()[0], "pending")
        self.assertEqual(self.c.execute("select count(*) from pub_events").fetchone()[0], 1)

    def test_in_doubt_no_retry_and_failed_reapprove(self):
        ops.pub_create("ep9", "telegram", "approved_by_policy", conn=self.c)
        ops.transition("ep9", "telegram", "uploading", "post", conn=self.c)
        ops.transition("ep9", "telegram", "in_doubt", "timeout", conn=self.c)
        with self.assertRaises(ValueError):
            ops.transition("ep9", "telegram", "uploading", "retry", conn=self.c)   # повтор заборонено
        ops.transition("ep9", "telegram", "failed", "reconcile: not found", conn=self.c)
        with self.assertRaises(ValueError):
            ops.transition("ep9", "telegram", "uploading", "retry", conn=self.c)
        ops.transition("ep9", "telegram", "approved_by_policy", "new approve", conn=self.c)
        ops.transition("ep9", "telegram", "published", "sent", external_id="123", conn=self.c)
        ops.transition("ep9", "telegram", "rolled_back", "deleted", conn=self.c)
        with self.assertRaises(ValueError):
            ops.transition("ep9", "telegram", "published", "again", conn=self.c)

    def test_duplicate_card_and_state_column_guard(self):
        self.assertTrue(ops.pub_create("ep9", "tiktok", conn=self.c))
        self.assertFalse(ops.pub_create("ep9", "tiktok", conn=self.c))
        with self.assertRaises(ValueError):
            ops.transition("ep9", "tiktok", "validated", "x", state="published", conn=self.c)


class RunsExperiments(Base):
    def test_runs_and_report(self):
        rid = ops.run_start("render", "shorts", conn=self.c)
        ops.run_finish(rid, "failed", "build.sh exit 1", conn=self.c)
        r = self.c.execute("select status, error from runs where run_id=?", (rid,)).fetchone()
        self.assertEqual(tuple(r), ("failed", "build.sh exit 1"))
        txt = ops.report(ops.now()[:10], conn=self.c)
        self.assertIn("render:failed=1", txt); self.assertIn("Журнал: OK", txt)

    def test_experiment_frozen_after_running(self):
        self.c.execute("insert into experiments(experiment_id,hypothesis,variant,control,sample_size,success_metric,"
                       "threshold,status) values('e1','h','v','c',3,'views_7d_median','{}','designed')")
        self.c.execute("update experiments set hypothesis='h2' where experiment_id='e1'")
        self.c.execute("update experiments set status='running' where experiment_id='e1'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("update experiments set variant='v2' where experiment_id='e1'")
        self.c.execute("update experiments set status='decided', decision='promote' where experiment_id='e1'")


if __name__ == "__main__":
    unittest.main()
