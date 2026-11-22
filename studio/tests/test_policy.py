"""Тести Policy Engine (plan §12 п.1–7, 15–17 + рішення власника 22.11). Без мережі; фікстури — копії реальних
факт-файлів і сценаріїв у тимчасовій теці; тимчасові ops.sqlite, quota.log, policy.json.
python3 -m unittest studio/tests/test_policy.py
"""
import copy, datetime as dt, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
import ops  # noqa: E402
import policy as pol  # noqa: E402

REAL_EPS = STUDIO / "eps"
NOW = "2026-11-22T16:00:00Z"
ENV = ("SHK_EPS", "SHK_POLICY", "SHK_OPS_DB", "SHK_QUOTA_LOG", "SHK_POSTS")
TABLE = "| Твердження | Джерело | Статус | Нотатка |\n|---|---|---|---|\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.eps = self.d / "eps"; self.eps.mkdir()
        for f in ("ep82_factcheck_independent.md", "guide1_factcheck_independent.md", "guide3_factcheck_independent.md",
                  "ep84_factcheck_independent.md", "ep82.py", "guide1.py", "guide3.py", "meta.py"):
            shutil.copy(REAL_EPS / f, self.eps / f)
        # сценарій старший за факт-файл (інакше fact.stale)
        for f in ("ep82.py", "guide1.py", "guide3.py"):
            os.utime(self.eps / f, (1_700_000_000, 1_700_000_000))
        (self.eps / "uploaded.json").write_text("{}")
        (self.eps / "reserve.json").write_text("{}")
        (self.eps / "posts").mkdir()
        self.pol = json.loads((STUDIO / "policy.json").read_text(encoding="utf-8"))
        self.pol["legacy"]["slugs"] = []
        self.policy_path = self.d / "policy.json"
        self.write_policy(self.pol)
        self.quota = self.d / "quota.log"; self.quota.write_text("")
        self._env = {k: os.environ.get(k) for k in ENV}
        os.environ.update(SHK_EPS=str(self.eps), SHK_POLICY=str(self.policy_path), SHK_OPS_DB=str(self.d / "ops.sqlite"),
                          SHK_QUOTA_LOG=str(self.quota), SHK_POSTS=str(self.eps / "posts"))
        self._patch = (ops.SNAP_DIR, ops.ROOT, pol.ROOT)
        ops.SNAP_DIR, ops.ROOT, pol.ROOT = self.d / "snapshots", self.d, self.d
        self.c = ops.db()

    def tearDown(self):
        self.c.close()
        ops.SNAP_DIR, ops.ROOT, pol.ROOT = self._patch
        for k, v in self._env.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
        self.tmp.cleanup()

    def write_policy(self, p, raw=None):
        self.policy_path.write_text(raw if raw is not None else json.dumps(p, ensure_ascii=False), encoding="utf-8")

    def ev(self, target, action="youtube_upload", policy=None, **kw):
        a = {"type": action, "target": target, **kw}
        return pol.evaluate(a, policy=policy or self.pol, now=NOW)

    def rules(self, d, policy_name=None):
        return {r["rule"]: r for r in d["rules_triggered"] if not policy_name or r["policy"] == policy_name}

    def factfile(self, slug, body):
        (self.eps / f"{slug}.py").write_text(f'SLUG="{slug}"\nSCENES=[dict(kind="hook", text="тест")]\n')
        os.utime(self.eps / f"{slug}.py", (1_700_000_000, 1_700_000_000))
        (self.eps / f"{slug}_factcheck_independent.md").write_text(body, encoding="utf-8")


class FactPolicy(Base):
    # §12 п.1 + рішення власника №3
    def test_ep82_fact_allow_and_threshold(self):
        d = self.ev("ep82")
        self.assertEqual(d["content_id"], "ep82_tier_kitchen")
        self.assertEqual(d["evidence"]["fact"], "ALLOW", self.rules(d, "fact"))
        p2 = copy.deepcopy(self.pol); p2["fact"]["max_unverified_not_claimed"] = 2
        self.assertEqual(self.ev("ep82", policy=p2)["evidence"]["fact"], "ALLOW")
        p0 = copy.deepcopy(self.pol); p0["fact"]["max_unverified_not_claimed"] = 0
        d0 = self.ev("ep82", policy=p0)
        self.assertEqual(d0["evidence"]["fact"], "BLOCK")
        self.assertIn("fact.unverified_not_claimed", self.rules(d0))

    def test_ep82_high_risk_degrade(self):
        d = self.ev("ep82")
        self.assertIn("health", d["evidence"]["high_risk"])
        self.assertEqual(d["evidence"]["high_risk"], d["evidence"]["high_risk"])
        self.assertEqual(self.rules(d, "high_risk")["high_risk.topic"]["verdict"], "DEGRADE")

    def test_ep82_guide3_last_line_pass(self):
        for t in ("ep82", "guide3"):
            f = pol.parse_factcheck((self.eps / f"{t}_factcheck_independent.md").read_text(encoding="utf-8"))
            self.assertEqual(f["verdict"], "PASS", t)
            self.assertEqual(f["fail"], 0, t)
            self.assertEqual(self.ev(t)["evidence"]["fact"], "ALLOW", t)
        g3 = pol.parse_factcheck((self.eps / "guide3_factcheck_independent.md").read_text(encoding="utf-8"))
        self.assertEqual(g3["fail_earlier"], 3)        # перший раунд мав 3 FAIL, повторна перевірка їх закрила
        self.assertGreater(g3["final_round_rows"], 0)

    # §12 п.2
    def test_guide1_no_verdict_block(self):
        d = self.ev("guide1")
        self.assertEqual(self.rules(d)["fact.no_verdict"]["verdict"], "BLOCK")
        self.assertEqual(d["result"], "BLOCK")

    def test_file_without_verdict_block(self):
        self.factfile("ep90_x", "# фактчек\n" + TABLE + "| a | https://help.openai.com/x | PASS | |\n\nВсе добре, PASS.\n")
        d = self.ev("ep90_x")
        self.assertIn("fact.no_verdict", self.rules(d))
        self.assertEqual(d["evidence"]["fact"], "BLOCK")

    def test_verdict_not_last_line_block(self):
        self.factfile("ep91_x", TABLE + "| a | https://help.openai.com/x | PASS | |\n\nВердикт: PASS\n\nP.S. дрібниця\n")
        self.assertIn("fact.no_verdict", self.rules(self.ev("ep91_x")))

    # §12 п.3
    def test_missing_factcheck_block_and_legacy_degrade(self):
        (self.eps / "ep80.py").write_text('SLUG="ep80_prof_olx"\nSCENES=[dict(kind="hook", text="x")]\n')
        d = self.ev("ep80")
        self.assertEqual(self.rules(d)["fact.missing"]["verdict"], "BLOCK")
        p = copy.deepcopy(self.pol); p["legacy"]["slugs"] = ["ep80_prof_olx"]
        r = self.rules(self.ev("ep80", policy=p))
        self.assertNotIn("fact.missing", r)
        self.assertEqual(r["fact.missing_legacy"]["verdict"], "DEGRADE")
        self.assertEqual(r["fact.missing_legacy"]["mode"], "no_tiktok")

    # §12 п.4
    def test_fail_in_prose_not_counted(self):
        body = ("# фактчек\nЦе не FAIL, просто уточнення. FAIL немає.\n" + TABLE +
                "| a | https://help.openai.com/x | PASS | раніше думав, що FAIL, але ні |\n\nНемає (0 FAIL).\n\nВердикт: PASS\n")
        self.factfile("ep92_x", body)
        f = pol.parse_factcheck(body)
        self.assertEqual((f["fail"], f["pass"]), (0, 1))
        self.assertEqual(self.ev("ep92_x")["evidence"]["fact"], "ALLOW")
        ep82 = pol.parse_factcheck((self.eps / "ep82_factcheck_independent.md").read_text(encoding="utf-8"))
        self.assertEqual(ep82["fail"], 0)   # «тож це не FAIL» у примітці ep82

    # §12 п.5
    def test_fail_table_row_block(self):
        self.factfile("ep93_x", TABLE + "| a | https://help.openai.com/x | PASS | |\n| b | https://openai.com/y | FAIL | неправда |\n"
                                        "\nВердикт: PASS\n")
        d = self.ev("ep93_x")
        self.assertEqual(self.rules(d)["fact.fail_rows"]["verdict"], "BLOCK")
        self.factfile("ep94_x", TABLE + "| b | https://openai.com/y | **FAIL** | |\n\nВердикт: FAIL\n")
        r = self.rules(self.ev("ep94_x"))
        self.assertIn("fact.verdict_fail", r); self.assertIn("fact.fail_rows", r)

    def test_pass_after_fail_without_recheck_block(self):
        self.factfile("ep95_x", TABLE + "| b | https://openai.com/y | FAIL | |\n\nВердикт: FAIL\n\nВиправив.\n\nВердикт: PASS\n")
        self.assertIn("fact.fail_not_rechecked", self.rules(self.ev("ep95_x")))

    def test_unverified_claimed_vs_not_claimed(self):
        self.factfile("ep96_x", TABLE + "| a | https://openai.com/y | UNVERIFIED (не заявлено) | |\n"
                                        "| b | https://openai.com/z | UNVERIFIED | У ролик не виноситься, як факт не заявлено |\n"
                                        "\nВердикт: PASS\n")
        d = self.ev("ep96_x")
        self.assertEqual(d["evidence"]["fact"], "ALLOW", self.rules(d, "fact"))
        self.factfile("ep97_x", TABLE + "| a | https://openai.com/y | UNVERIFIED (дрібне) | не перевіряв |\n\nВердикт: PASS\n")
        self.assertEqual(self.rules(self.ev("ep97_x"))["fact.unverified_claimed"]["verdict"], "BLOCK")


class HardDeny(Base):
    # §12 п.7
    def test_null_or_inf_threshold_safe_mode(self):
        p = copy.deepcopy(self.pol); p["rate_limit"]["shorts_per_day"] = None
        d = self.ev("ep82", policy=p)
        self.assertEqual(d["result"], "SAFE_MODE")
        self.assertIn("rate_limit.shorts_per_day", self.rules(d)["hard_deny.invalid_threshold"]["value"])
        raw = json.dumps(self.pol, ensure_ascii=False).replace('"yt_quota_day": 10000', '"yt_quota_day": Infinity')
        self.assertIn("Infinity", raw)
        self.write_policy(None, raw)
        loaded, _ = pol.load_policy()
        d2 = pol.evaluate({"type": "youtube_upload", "target": "ep82"}, policy=loaded, now=NOW)
        self.assertEqual(d2["result"], "SAFE_MODE")

    def test_unknown_action_block(self):
        d = pol.decide({"type": "rm_rf"}, {"content_id": "x"}, self.pol)
        self.assertEqual(d["result"], "BLOCK")


class Quality(Base):
    def facts(self, **media):
        m = {"exists": True, "duration": 30.0, "has_video": True, "has_audio": True, "width": 1080, "height": 1920,
             "bytes": 1000, "mean_volume_db": -16.0, "silences": []}
        m.update(media)
        return {"content_id": "ep99_q", "now": NOW, "media": m, "voice": {"ran": True, "rc": 0, "out": "OK"},
                "asr": {"segments": [{"match": 1.0}], "overall_match": 1.0}, "thumb": [{"name": "thumb.jpg", "bytes": 5000}],
                "script": {"exists": True, "kind": "short", "texts": []}, "files": {}, "fact": {"exists": False}}

    def q(self, facts):
        d = pol.decide({"type": "youtube_upload"}, facts, self.pol)
        return d["evidence"]["quality"], self.rules(d, "quality")

    # §12 п.16
    def test_short_duration(self):
        self.assertEqual(self.q(self.facts())[0], "ALLOW")
        v, r = self.q(self.facts(duration=50.0))
        self.assertEqual(v, "DEGRADE"); self.assertEqual(r["quality.short_above_target"]["mode"], "no_tiktok")
        v, r = self.q(self.facts(duration=200.0))
        self.assertEqual(v, "BLOCK"); self.assertIn("quality.short_too_long", r)

    # §12 п.17
    def test_voice_check_fail_block(self):
        f = self.facts(); f["voice"] = {"ran": True, "rc": 1, "out": "BAD F0 170 Hz"}
        v, r = self.q(f)
        self.assertEqual(v, "BLOCK"); self.assertIn("quality.voice_check", r)

    def test_asr_and_silence_gap(self):
        f = self.facts(silences=[[10.0, 12.0], [29.2, 30.0]]); f["asr"] = {"segments": [{"match": 0.8}], "overall_match": 0.97}
        _, r = self.q(f)
        self.assertIn("quality.silence_gap", r); self.assertIn("quality.asr_segment", r)
        self.assertEqual(r["quality.silence_gap"]["value"], [[10.0, 12.0]])   # хвіст в останній секунді — не рахується

    # §12 п.15 — справжній файл з тишею (ffmpeg anullsrc), справжні ffprobe/ffmpeg
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "немає ffmpeg")
    def test_silent_final_mp4_block(self):
        slug = "ep98_silent"
        (self.eps / f"{slug}.py").write_text(f'SLUG="{slug}"\nSCENES=[dict(kind="hook", text="тиша")]\n')
        d = self.eps / slug; d.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=108x192:d=3", "-f", "lavfi",
                        "-i", "anullsrc=r=44100:cl=mono", "-t", "3", "-shortest", "-c:v", "libx264", "-c:a", "aac",
                        str(d / "final.mp4")], check=True, timeout=60)
        r = self.rules(self.ev(slug), "quality")
        self.assertEqual(r["quality.silent"]["verdict"], "BLOCK")


class GateReplay(Base):
    def _targets(self):
        for i in range(4):
            self.factfile(f"ep7{i}_r", TABLE + f"| a{i} | https://help.openai.com/{i} | PASS | |\n\nВердикт: PASS\n")
        return ["ep82", "guide1", "guide3", "ep70_r", "ep71_r", "ep72_r", "ep73_r", "ep80_none"]

    def test_shadow_always_proceeds_and_logs(self):
        self.assertEqual(json.loads((STUDIO / "policy.json").read_text(encoding="utf-8"))["mode"], "shadow")
        g = pol.gate({"type": "youtube_upload", "target": "guide1"}, now=NOW, conn=self.c)
        self.assertTrue(g["proceed"]); self.assertEqual(g["mode"], "shadow"); self.assertEqual(g["enforce_result"], "BLOCK")
        row = self.c.execute("select * from agent_decisions where decision_id=?", (g["decision_id"],)).fetchone()
        self.assertEqual((row["decision_type"], row["policy_result"]), ("policy", "BLOCK"))
        snap = pol._load_snapshot(row["input_snapshot"])
        self.assertEqual(snap["action"]["target"], "guide1"); self.assertIn("facts", snap); self.assertIn("policy", snap)
        self.assertIn("fact.no_verdict", row["rules_triggered"])
        self.assertTrue(ops.verify(self.c)["ok"])

    def test_enforce_blocks(self):
        p = copy.deepcopy(self.pol); p["mode"] = "enforce"; self.write_policy(p)
        g = pol.gate({"type": "youtube_upload", "target": "guide1"}, now=NOW, conn=self.c)
        self.assertFalse(g["proceed"])

    def test_engine_error_shadow_proceeds_enforce_fails_closed(self):
        self.write_policy(None, "{broken")
        g = pol.gate({"type": "youtube_upload", "target": "ep82"}, now=NOW, conn=self.c)
        self.assertFalse(g["proceed"]); self.assertEqual(g["result"], "BLOCK")   # policy.json не читається → enforce
        self.write_policy(self.pol)
        orig = pol.collect
        pol.collect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            g = pol.gate({"type": "youtube_upload", "target": "ep82"}, now=NOW, conn=self.c)
        finally:
            pol.collect = orig
        self.assertTrue(g["proceed"]); self.assertIn("boom", g["error"])

    # §12 п.6 + детермінізм
    def test_replay_20_decisions(self):
        ids = []
        acts = ["youtube_upload", "tg_post", "tiktok_publish", "yt_comment", "site_publish"]
        for i, t in enumerate(self._targets() * 3):
            if len(ids) >= 20: break
            g = pol.gate({"type": acts[i % len(acts)], "target": t}, now=NOW, conn=self.c)
            ids.append(g["decision_id"])
        self.assertEqual(len(ids), 20)
        for did in ids:
            r = pol.replay(did, conn=self.c)
            self.assertTrue(r["match"], r)
        self.assertTrue(ops.verify(self.c)["ok"])

    def test_decide_deterministic(self):
        a = {"type": "youtube_upload", "target": "ep82"}
        f = pol.collect(a, self.pol, NOW)
        outs = {ops.canonical(pol.decide(a, json.loads(json.dumps(f)), self.pol)) for _ in range(5)}
        self.assertEqual(len(outs), 1)

    def test_replay_detects_tamper(self):
        g = pol.gate({"type": "youtube_upload", "target": "ep82"}, now=NOW, conn=self.c)
        row = dict(self.c.execute("select * from agent_decisions where decision_id=?", (g["decision_id"],)).fetchone())
        snap = pol._load_snapshot(row["input_snapshot"])
        snap["policy"]["fact"]["max_unverified_not_claimed"] = 0           # інша політика → інший результат
        did = ops.decide("policy", "t", snap, {}, rules_triggered=json.loads(row["rules_triggered"]),
                         policy_result=row["policy_result"], conn=self.c)
        self.assertFalse(pol.replay(did, conn=self.c)["match"])


class Other(Base):
    def test_duplicate_uploaded_slug(self):
        (self.eps / "uploaded.json").write_text(json.dumps({"ep82_tier_kitchen": "VID123"}))
        r = self.rules(self.ev("ep82"))
        self.assertEqual(r["duplicate.slug_uploaded"]["verdict"], "BLOCK")

    def test_quota_retry_later(self):   # §12 п.25 (бонус)
        self.quota.write_text("2026-11-22T10:00:00\tPOST videos\t9100\n")
        r = self.rules(self.ev("ep82"))
        self.assertEqual(r["budget.yt_quota"]["verdict"], "RETRY_LATER")

    def test_schedule_conflict(self):
        ops.pub_create("ep78_signal_shi_agent", "youtube", "scheduled", scheduled_at="2026-11-25T17:00:00Z", conn=self.c)
        r = self.rules(self.ev("guide1"))
        self.assertEqual(r["schedule_conflict.slot_taken"]["verdict"], "RETRY_LATER")
        self.assertEqual(r["schedule_conflict.slot_taken"]["until"], "2026-11-26T17:00:00Z")

    def test_tiktok_waits_60_min_after_youtube(self):
        ops.pub_create("ep82_tier_kitchen", "youtube", "scheduled", scheduled_at="2026-11-22T15:30:00Z", conn=self.c)
        r = self.rules(self.ev("ep82", action="tiktok_publish"))
        self.assertEqual(r["schedule_conflict.before_youtube_public"]["until"], "2026-11-22T16:30:00Z")

    def test_policy_json_every_value_has_why(self):
        real = json.loads((STUDIO / "policy.json").read_text(encoding="utf-8"))
        missing = [k for k in ("version", "mode") if k not in real["_why"]]
        for sec, body in real.items():
            if isinstance(body, dict) and not sec.startswith("_"):
                why = body.get("_why", {})
                missing += [f"{sec}.{k}" for k in body if not k.startswith("_") and k not in why]
        self.assertEqual(missing, [])
        self.assertEqual(real["fact"]["max_unverified_claimed"], 0)
        self.assertEqual(real["schedule"]["tiktok_after_youtube_min"], 60)
        self.assertEqual((real["quality"]["short_max_s"], real["quality"]["short_target_s"]), (60, 35))

    def test_source_tier0_block(self):
        self.factfile("ep89_x", TABLE + "| a | https://example.ru/x | PASS | |\n\nВердикт: PASS\n")
        self.assertEqual(self.rules(self.ev("ep89_x"))["source_credibility.tier0"]["verdict"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
