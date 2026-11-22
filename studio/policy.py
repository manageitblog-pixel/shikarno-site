#!/usr/bin/env python3
"""Policy Engine ШІкарно (P0 plan 22.11, крок 3): детермінований «суддя» між рішенням агента і зовнішньою дією.

Без LLM і без мережі. collect(action) читає локальні файли (eps/<slug>/, факт-md, uploaded.json, reserve.json,
tiktok.json, pending_comments.json, data/quota.log, data/ops.sqlite у режимі ro) і запускає лише локальні
ffprobe/ffmpeg/voice_check.py. decide(action, facts, policy) — чиста функція: той самий вхід → той самий вихід.
evaluate(action) = decide(action, collect(action), load_policy()).

Порядок політик (§3.1, перша сильніша перемагає): circuit_breaker → hard_deny → budget → rate_limit → duplicate →
fact → source_credibility → quality → high_risk → schedule_conflict → canary → rollback → publication.
Сила: SAFE_MODE > BLOCK > RETRY_LATER > DEGRADE > CANARY > ALLOW.

gate(action) — завжди пише рішення в ops.decide("policy", ...) з input_snapshot = {action, facts, policy} і
rules_triggered. У mode="shadow" (policy.json) завжди повертає proceed=True, а в журнал іде те, що сказав би enforce.
replay(decision_id) — відтворює рішення з input_snapshot і порівнює result + rules_triggered.

Поки (до кроку 4, після 25.11 18Z) ЖОДЕН продакшн-код policy не викликає.

CLI (лише читання, нічого не публікує):
  python3 studio/policy.py check <slug|path> --action youtube_upload|tg_post|tiktok_publish|yt_comment|site_publish|indexnow
         [--now ISO] [--publish-at ISO] [--experiment ID] [--record]   # --record → gate(): пише рішення в ops.sqlite
  python3 studio/policy.py replay <decision_id>
  python3 studio/policy.py explain [policy]
Змінні для тестів: SHK_EPS (тека eps), SHK_POLICY (policy.json), SHK_OPS_DB (ops.sqlite), SHK_POSTS (content/posts).
"""
import argparse, ast, datetime as dt, difflib, hashlib, json, math, os, re, sqlite3, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

ORDER = ("circuit_breaker", "hard_deny", "budget", "rate_limit", "duplicate", "fact", "source_credibility",
         "quality", "high_risk", "schedule_conflict", "canary", "rollback", "publication")
STRENGTH = {"ALLOW": 0, "CANARY": 1, "DEGRADE": 2, "RETRY_LATER": 3, "BLOCK": 4, "SAFE_MODE": 5}
PROCEED_IN_ENFORCE = ("ALLOW", "CANARY", "DEGRADE")

# дія → платформа (ops.PLATFORMS), breaker-scope і які перевірки §4 застосовні
ACTIONS = {
    "youtube_upload": dict(platform="youtube", scope="youtube", fact=True, quality="final.mp4", similarity=True,
                           dup_states=("uploaded", "scheduled", "published", "distributed"), rate="youtube"),
    "yt_comment": dict(platform="yt_comment", scope="youtube", fact=False, quality=None, similarity=False,
                       dup_states=("published", "distributed"), rate="yt_comment"),
    "tg_post": dict(platform="telegram", scope="telegram", fact=True, quality="tg.mp4", similarity=False,
                    dup_states=("published", "distributed"), rate="tg"),
    "tiktok_publish": dict(platform="tiktok", scope="tiktok", fact=True, quality="tiktok.mp4", similarity=False,
                           dup_states=("uploaded", "scheduled", "published", "distributed"), rate="tiktok"),
    "site_publish": dict(platform="website", scope="site", fact=True, quality=None, similarity=False,
                         dup_states=("scheduled", "published", "distributed"), rate="site"),
    "indexnow": dict(platform="indexnow", scope="site", fact=False, quality=None, similarity=False,
                     dup_states=("published", "distributed"), rate="indexnow"),
}
VERDICT_RE = re.compile(r"^Вердикт:\s*(PASS|FAIL)\s*$")
NOT_CLAIMED_RE = re.compile(r"не\s+заявлен", re.I)
URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)[^\s|)>\]»;,`]*")
BARE_RE = re.compile(r"(?<![@\w/.:-])((?:[a-z0-9-]+\.)+(?:com|org|net|ua|google|io|ai|gov|edu|ru|by|dev|app|me|be))"
                     r"(?=[/?\s|)`;,»]|$)")
WORD_RE = re.compile(r"[a-zа-яіїєґ0-9']+")


class PolicyError(Exception):
    pass


# ---------------------------------------------------------------- helpers
def _paths():
    eps = Path(os.environ.get("SHK_EPS") or HERE / "eps")
    return dict(eps=eps, policy=Path(os.environ.get("SHK_POLICY") or HERE / "policy.json"),
                ops=Path(os.environ.get("SHK_OPS_DB") or HERE / "data" / "ops.sqlite"),
                quota=Path(os.environ.get("SHK_QUOTA_LOG") or HERE / "data" / "quota.log"),
                posts=Path(os.environ.get("SHK_POSTS") or ROOT / "content" / "posts"))


def canonical(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _ts(s):
    if not s: return None
    if isinstance(s, dt.datetime): d = s
    else:
        try: d = dt.datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
        except ValueError: return None
    if d.tzinfo is None: d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def _iso(d):
    return d.replace(microsecond=0).isoformat().replace("+00:00", "Z") if d else None


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def _mtime(p):
    return _iso(dt.datetime.fromtimestamp(Path(p).stat().st_mtime, dt.timezone.utc))


def _read_json(p, default=None):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError): return default


def load_policy(path=None):
    """→ (policy dict, policy_version = sha256(файлу)[:12]). Нестандартні Infinity/NaN json теж читає — їх ловить hard_deny."""
    p = Path(path) if path else _paths()["policy"]
    raw = p.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()[:12]


def policy_version_of(policy):
    return hashlib.sha256(canonical(policy).encode()).hexdigest()[:12]


# ---------------------------------------------------------------- safe literal eval (епізоди й meta.py без імпорту)
class _NL(Exception):
    pass


def _lit(node, env):
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        out = []
        for e in node.elts:
            try: out.append(_lit(e, env))
            except _NL: pass
        return out
    if isinstance(node, ast.Dict):
        out = {}
        for k, v in zip(node.keys, node.values):
            if k is None: continue
            try: out[_lit(k, env)] = _lit(v, env)
            except (_NL, TypeError): pass
        return out
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict" and not node.args:
        out = {}
        for kw in node.keywords:
            if kw.arg is None: continue
            try: out[kw.arg] = _lit(kw.value, env)
            except _NL: pass
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _lit(node.left, env), _lit(node.right, env)
        if type(a) is not type(b): raise _NL()
        return a + b
    if isinstance(node, ast.Name) and node.id in env: return env[node.id]
    raise _NL()


def parse_module(path):
    """Верхньорівневі присвоєння-літерали модуля + X.update({...}). Код модуля не виконується."""
    src = Path(path).read_text(encoding="utf-8")
    env, updates = {}, {}
    for st in ast.parse(src).body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            try: env[st.targets[0].id] = _lit(st.value, env)
            except _NL: pass
        elif (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Attribute)
              and st.value.func.attr == "update" and len(st.value.args) == 1):
            try:
                v = _lit(st.value.args[0], env)
                if isinstance(v, dict): updates.update(v)
            except _NL: pass
    head = src.splitlines()[:4]
    return env, updates, head


def meta_index(eps):
    """slug → meta dict з eps/meta.py (усі META*-словники)."""
    p = Path(eps) / "meta.py"
    if not p.exists(): return {}
    env, upd, _ = parse_module(p)
    out = {}
    for k, v in list(env.items()) + [("_upd", upd)]:
        if k.startswith("META") or k == "_upd":
            if isinstance(v, dict):
                for slug, m in v.items():
                    if isinstance(m, dict) and "title" in m: out[slug] = m
    return out


def _key(slug):
    return slug.split("_")[0]


def script_facts(eps, slug, meta_idx=None):
    """Факти зі сценарію eps/<key>.py: kind short/long, тексти, meta, publish_at із шапки, idea link."""
    eps = Path(eps)
    p = eps / f"{_key(slug)}.py"
    if not p.exists(): p = eps / f"{slug}.py"
    if not p.exists(): return {"exists": False}
    env, _, head = parse_module(p)
    scenes = env.get("SCENES") if isinstance(env.get("SCENES"), list) else None
    segs = env.get("SEGS") if isinstance(env.get("SEGS"), list) else None
    items = scenes or segs or []
    texts = [str(s.get("text") or s.get("gsay") or "") for s in items if isinstance(s, dict)]
    long = bool(segs and not scenes) or "PARTS" in env
    meta = env.get("META") if isinstance(env.get("META"), dict) else None
    if not meta and meta_idx is not None: meta = meta_idx.get(slug)
    meta = meta or {}
    pub = None
    h = " ".join(head)
    m = re.search(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+(?:\d{1,2}:\d\d\s+Київ\s+\()?(\d{1,2})(?::(\d\d))?Z", h)
    if m:
        d, mo, y, hh, mm = int(m.group(1)), int(m.group(2)), int(m.group(3) or 2026), int(m.group(4)), int(m.group(5) or 0)
        try: pub = _iso(dt.datetime(y, mo, d, hh, mm, tzinfo=dt.timezone.utc))
        except ValueError: pub = None
    idea = env.get("IDEA_ID")
    if idea is None:
        mi = re.search(r"ідея\s*(?:[#№]|дошки\s*№?)\s*(\d+)|ідея\s+№\s*(\d+)", h, re.I)
        if mi: idea = int(mi.group(1) or mi.group(2))
    return {"exists": True, "path": str(p), "slug": env.get("SLUG") or slug, "kind": "long" if long else "short",
            "texts": texts, "title": str(meta.get("title") or ""), "description": str(meta.get("description") or ""),
            "tags": [str(t) for t in (meta.get("tags") or []) if isinstance(t, str)],
            "publish_at": pub, "idea_id": idea, "mtime": _mtime(p), "header": head[0][:200] if head else ""}


# ---------------------------------------------------------------- fact-file parser
def _tables(lines):
    """[(start_line, header_cells, rows[cells])] для markdown-таблиць."""
    out, i = [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"): j += 1
            block = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines[i:j]]
            if len(block) >= 2 and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in block[1] if c):
                out.append((i, block[0], block[2:]))
            i = j
        else:
            i += 1
    return out


def _status(cell):
    s = cell.replace("*", "").strip().upper()
    for k in ("PASS", "FAIL", "UNVERIFIED"):
        if s.startswith(k): return k
    return None


ROUND_HEAD_RE = re.compile(r"^#+\s*(?:повторна\s+перевірка|перевірка\s+\d+|перевірка\s+змін)", re.I)
SEG_RE = re.compile(r"\d+")


def _norm_claim(s):
    return " ".join(WORD_RE.findall(s.lower()))


def parse_factcheck(text):
    """Розбір *_factcheck_independent.md.

    verdict — лише з ОСТАННЬОГО непорожнього рядка «Вердикт: PASS|FAIL» (рішення власника №3).
    Статуси — лише з колонки «Статус» таблиць; слово FAIL у прозі не рахується (§3.4 п.3).
    Раунди: межа — рядок-вердикт (крім останнього) або заголовок «Повторна перевірка» / «Перевірка N» /
    «Перевірка змін…». FAIL рахуються в останньому раунді (повторна перевірка після виправлень закриває
    попередні FAIL). UNVERIFIED рахується, лише якщо пізніший раунд не перевірив те саме твердження
    (той самий сегмент «#» або те саме формулювання) — пізніший рядок заміняє ранній (виправлено 22.11).
    Якщо в раніших раундах були FAIL, останній раунд мусить мати власну таблицю статусів.
    """
    lines = text.splitlines()
    nonempty = [ln.strip() for ln in lines if ln.strip()]
    last = nonempty[-1] if nonempty else ""
    m = VERDICT_RE.match(last)
    verdict_lines = [i for i, ln in enumerate(lines) if VERDICT_RE.match(ln.strip())]
    starts = sorted({i + 1 for i in verdict_lines[:-1]} |
                    {i for i, ln in enumerate(lines) if ROUND_HEAD_RE.match(ln.strip())})
    final_start = starts[-1] if starts else 0
    res = {"verdict": m.group(1) if m else None, "rounds": max(1, len(verdict_lines)),
           "pass": 0, "fail": 0, "fail_earlier": 0, "unverified_claimed": 0, "unverified_not_claimed": 0,
           "unverified_resolved": 0, "rows": 0, "final_round_rows": 0, "fail_rows": [], "unverified_rows": [],
           "urls": []}
    items = []   # (round, seg-key, norm-claim, status, not_claimed, claim)
    for start, header, rows in _tables(lines):
        idx = next((k for k, h in enumerate(header) if re.match(r"\**\s*статус", h, re.I)), None)
        if idx is None: continue
        rnd = sum(1 for s0 in starts if s0 <= start)
        final = start >= final_start
        seg_i = next((k for k, h in enumerate(header) if h.replace("*", "").strip() in ("#", "№", "сегмент")), None)
        cl_i = next((k for k, h in enumerate(header) if re.search(r"твердженн|формулюванн", h, re.I)), None)
        if cl_i is None: cl_i = 1 if seg_i == 0 and len(header) > 1 else 0
        for cells in rows:
            if idx >= len(cells): continue
            st = _status(cells[idx])
            if not st: continue
            res["rows"] += 1
            if final: res["final_round_rows"] += 1
            claim = cells[cl_i][:90] if cl_i < len(cells) else ""
            seg = tuple(SEG_RE.findall(cells[seg_i])) if seg_i is not None and seg_i < len(cells) else ()
            if st == "PASS": res["pass"] += 1
            elif st == "FAIL":
                if final:
                    res["fail"] += 1; res["fail_rows"].append(claim)
                else:
                    res["fail_earlier"] += 1
            items.append((rnd, seg, _norm_claim(claim), st, bool(NOT_CLAIMED_RE.search(" ".join(cells[idx:]))), claim))
    for rnd, seg, nc, st, not_claimed, claim in items:
        if st != "UNVERIFIED": continue
        if any(r2 > rnd and ((seg and s2 == seg) or (nc and n2 == nc)) for r2, s2, n2, *_ in items):
            res["unverified_resolved"] += 1; continue
        if not_claimed: res["unverified_not_claimed"] += 1
        else:
            res["unverified_claimed"] += 1; res["unverified_rows"].append(claim)
    res["urls"] = extract_urls(text)
    return res


def extract_urls(text):
    hosts = []
    for m in URL_RE.finditer(text):
        hosts.append(m.group(1).lower())
    stripped = URL_RE.sub(" ", text)
    for m in BARE_RE.finditer(stripped.lower()):
        hosts.append(m.group(1))
    out = []
    for h in hosts:
        h = h.strip(".").removeprefix("www.")
        if h and h not in out: out.append(h)
    return sorted(out)


def find_factcheck(eps, slug, parent=None):
    eps = Path(eps)
    for key in [slug, _key(slug)] + ([parent, _key(parent)] if parent else []):
        p = eps / f"{key}_factcheck_independent.md"
        if p.exists(): return p
    return None


# ---------------------------------------------------------------- media probes (локальні ffprobe/ffmpeg)
def probe_media(path, policy):
    q = policy.get("quality", {})
    p = Path(path)
    if not p.exists(): return {"exists": False}
    out = {"exists": True, "bytes": p.stat().st_size}
    try:
        pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                             "-of", "json", str(p)], capture_output=True, text=True, timeout=60)
        j = json.loads(pr.stdout or "{}")
        st = j.get("streams") or []
        v = next((s for s in st if s.get("codec_type") == "video"), None)
        out.update(duration=_r((j.get("format") or {}).get("duration"), 2), has_video=bool(v),
                   has_audio=any(s.get("codec_type") == "audio" for s in st),
                   width=(v or {}).get("width"), height=(v or {}).get("height"))
    except Exception as e:  # noqa: BLE001
        out["probe_error"] = str(e)[:200]; return out
    if out.get("has_audio"):
        try:
            pr = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-vn", "-af",
                                 f"volumedetect,silencedetect=n={q.get('silence_db', -50)}dB:d={q.get('max_silence_s', 1.5)}",
                                 "-f", "null", "-"], capture_output=True, text=True, timeout=300)
            err = pr.stderr
            mv = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", err)
            out["mean_volume_db"] = (-200.0 if mv and mv.group(1) == "-inf" else _r(mv.group(1), 1)) if mv else None
            sil, cur = [], None
            for ln in err.splitlines():
                a = re.search(r"silence_start:\s*(-?[\d.]+)", ln)
                b = re.search(r"silence_end:\s*(-?[\d.]+)", ln)
                if a: cur = float(a.group(1))
                if b and cur is not None: sil.append([_r(max(0.0, cur), 2), _r(b.group(1), 2)]); cur = None
            if cur is not None: sil.append([_r(max(0.0, cur), 2), out.get("duration")])
            out["silences"] = sil
        except Exception as e:  # noqa: BLE001
            out["audio_error"] = str(e)[:200]
    return out


def voice_check(eps, slug, policy):
    d = Path(eps) / slug
    if not (d / "vo_raw.wav").exists(): return {"ran": False, "reason": "немає vo_raw.wav"}
    vc = Path(eps) / "voice_check.py"
    if not vc.exists(): return {"ran": False, "reason": "немає voice_check.py"}
    try:
        pr = subprocess.run([sys.executable, str(vc), str(d)], capture_output=True, text=True,
                            timeout=policy.get("quality", {}).get("voice_check_timeout_s", 60))
        return {"ran": True, "rc": pr.returncode, "out": (pr.stdout or pr.stderr).strip()[-160:]}
    except Exception as e:  # noqa: BLE001
        return {"ran": False, "reason": str(e)[:160]}


# ---------------------------------------------------------------- similarity
def title_words(t):
    t = re.sub(r"#\S+", " ", (t or "").lower())
    return set(WORD_RE.findall(t))


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


# ---------------------------------------------------------------- collect
def resolve(target, eps=None):
    """<slug|path> → slug. ep82 / ep82.py / eps/ep82_tier_kitchen / ep82_factcheck_independent.md → ep82_tier_kitchen."""
    eps = Path(eps or _paths()["eps"])
    t = str(target).rstrip("/")
    p = Path(t)
    name = p.name
    if name.endswith(".md"): name = name.split("_factcheck")[0]
    if name.endswith(".mp4"): name = p.parent.name
    if name.endswith(".py"): name = name[:-3]
    if (eps / f"{name}.py").exists():
        env, _, _ = parse_module(eps / f"{name}.py")
        if isinstance(env.get("SLUG"), str): return env["SLUG"]
    if (eps / name).is_dir(): return name
    for f in ("uploaded.json", "reserve.json"):
        d = _read_json(eps / f, {}) or {}
        if name in d: return name
        hits = [k for k in d if k.split("_")[0] == name]
        if len(hits) == 1: return hits[0]
    return name


def _ops_ro(path):
    if not Path(path).exists(): return None
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    c.row_factory = sqlite3.Row
    return c


def collect(action, policy=None, now=None):
    """Факти для decide(). Лише читання локальних файлів і ffprobe/ffmpeg. Нічого не пише."""
    policy = policy or load_policy()[0]
    P = _paths(); eps = P["eps"]
    a = dict(action)
    typ = a.get("type")
    spec = ACTIONS.get(typ) or {}
    now_dt = _ts(now or a.get("now")) or dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    slug = a.get("content_id") or (resolve(a["target"], eps) if a.get("target") else None)
    f = {"now": _iso(now_dt), "content_id": slug, "paths": {k: str(v) for k, v in P.items()}}
    if not slug: return f
    uploaded = _read_json(eps / "uploaded.json", {}) or {}
    reserve = _read_json(eps / "reserve.json", {}) or {}
    tiktok = (_read_json(eps / "tiktok.json", {}) or {}).get("posted_auto") or {}
    pending = _read_json(eps / "pending_comments.json", {}) or {}
    vid = uploaded.get(slug) or reserve.get(slug)
    f["files"] = {"in_uploaded": slug in uploaded, "in_reserve": slug in reserve, "video_id": vid,
                  "tiktok_posted": slug in tiktok, "comment_queued": bool(vid and vid in pending),
                  "comment_at": (pending.get(vid) or {}).get("at") if vid else None}
    midx = meta_index(eps)
    sf = script_facts(eps, slug, midx)
    f["script"] = sf
    # ---- ops.sqlite (ro)
    pubs, breaker = [], []
    c = _ops_ro(P["ops"])
    if c is not None:
        try:
            pubs = [dict(r) for r in c.execute("select content_id, platform, state, scheduled_at, external_id, legacy,"
                                               " parent_content_id from publications order by content_id, platform")]
            breaker = [dict(r) for r in c.execute("select scope, state, reason, opened_at, cooldown_until from breaker"
                                                  " order by scope")]
        finally:
            c.close()
    own = [p for p in pubs if p["content_id"] == slug]
    f["own_publications"] = own
    f["breaker"] = breaker
    parent = next((p["parent_content_id"] for p in own if p.get("parent_content_id") and p["parent_content_id"] != slug), None)
    # публікації інших content_id на цій платформі ±3 доби навколо publish_at (розклад і rate-limit)
    # пріоритет: явний publish_at дії → уже заплановане в publications (перенесення!) → шапка сценарію
    pub_at = _ts(a.get("publish_at") or
                 next((p["scheduled_at"] for p in own if p["platform"] == "youtube" and p["scheduled_at"]), None) or
                 sf.get("publish_at"))
    f["publish_at"] = _iso(pub_at)
    plat = spec.get("platform")
    centre = pub_at or now_dt
    near = []
    for p in pubs:
        if p["content_id"] == slug or p["platform"] != plat: continue
        t = _ts(p["scheduled_at"])
        if t and abs((t - centre).total_seconds()) <= 3 * 86400:
            near.append({"content_id": p["content_id"], "state": p["state"], "at": _iso(t)})
    f["nearby"] = sorted(near, key=lambda x: (x["at"], x["content_id"]))
    # ---- quota.log (вікно від останнього скидання)
    rh = policy.get("budget", {}).get("quota_reset_hour_utc", 8)
    reset = now_dt.replace(hour=rh, minute=0, second=0)
    if reset > now_dt: reset -= dt.timedelta(days=1)
    used = 0
    try:
        for ln in P["quota"].read_text(encoding="utf-8").splitlines():
            parts = ln.split("\t")
            if len(parts) >= 3:
                t = _ts(parts[0])
                if t and reset <= t <= now_dt:
                    try: used += int(parts[2])
                    except ValueError: pass
    except OSError:
        pass
    f["quota"] = {"window_start": _iso(reset), "used": used}
    # ---- fact
    fc = find_factcheck(eps, slug, parent)
    if fc:
        pf = parse_factcheck(fc.read_text(encoding="utf-8"))
        pf.update(path=str(fc), exists=True, mtime=_mtime(fc),
                  self_check_exists=(eps / f"{_key(slug)}_factcheck.md").exists())
        f["fact"] = pf
    else:
        f["fact"] = {"exists": False, "self_check_exists": (eps / f"{_key(slug)}_factcheck.md").exists()}
    desc = sf.get("description", "")
    src_part = desc.split("Джерела:", 1)[1] if "Джерела:" in desc else ""
    src_part = re.split(r"\n\n🎁|\n\nШІкарно —", src_part)[0]
    f["sources"] = {"factcheck": (f["fact"].get("urls") or []), "description": extract_urls(src_part)}
    # ---- quality
    if spec.get("quality"):
        d = eps / slug
        f["media"] = probe_media(d / spec["quality"], policy)
        f["voice"] = voice_check(eps, slug, policy)
        f["asr"] = _read_json(d / "audit_vo.json")
        thumbs = sorted([t for t in d.glob("thumb*.jpg")]) if d.is_dir() else []
        f["thumb"] = [{"name": t.name, "bytes": t.stat().st_size} for t in thumbs]
    # ---- duplicate / similarity
    if spec.get("similarity") and sf.get("exists"):
        mine_t = title_words(sf.get("title"))
        mine_s = WORD_RE.findall(" ".join(sf.get("texts") or []).lower())   # порівнюємо послідовності слів
        window = int(policy.get("duplicate", {}).get("window_items", 40))
        keys = [k for k in uploaded if _key(k) != _key(slug)][-window:]
        bt, bs = (0.0, None, None), (0.0, None)
        for k in keys:
            ok = script_facts(eps, k, midx) if (eps / f"{_key(k)}.py").exists() else {"title": (midx.get(k) or {}).get("title", "")}
            title = ok.get("title") or (midx.get(k) or {}).get("title", "")
            j = jaccard(mine_t, title_words(title))
            exact = bool(title) and title.strip() == (sf.get("title") or "").strip()
            if j > bt[0] or exact: bt = (1.0 if exact else j, k, exact)
            if mine_s and ok.get("texts"):
                sm = difflib.SequenceMatcher(None, mine_s, WORD_RE.findall(" ".join(ok["texts"]).lower()))
                # real_quick_ratio/quick_ratio — верхні межі ratio за O(1)/O(n): швидко відсікаємо явно різні тексти
                if sm.real_quick_ratio() > bs[0] and sm.quick_ratio() > bs[0]:
                    s = sm.ratio()
                    if s > bs[0]: bs = (s, k)
        f["similarity"] = {"title_max": _r(bt[0]), "title_with": bt[1], "title_exact": bool(bt[2]),
                           "script_max": _r(bs[0]), "script_with": bs[1], "compared": len(keys)}
    # ---- site
    if typ in ("site_publish", "indexnow"):
        arts = []
        for md in sorted(P["posts"].glob("*.md")) if P["posts"].exists() else []:
            head = md.read_text(encoding="utf-8")[:3000]
            if (vid and re.search(rf"^youtube:\s*['\"]?{re.escape(vid)}\b", head, re.M)) or \
                    re.search(rf"^slug:\s*['\"]?{re.escape(slug)}['\"]?\s*$", head, re.M):
                su = re.search(r"^source:.*?url:\s*['\"]?([^\s,}'\"]+)", head, re.M)
                arts.append({"file": md.name, "source_url": su.group(1) if su else None})
        f["articles"] = arts
    # ---- high-risk text (детермінований збіг робить decide зі словником policy)
    f["text_blob"] = "\n".join([sf.get("title", ""), desc, " ".join(sf.get("tags", []))] + list(sf.get("texts") or []))
    if a.get("text"): f["text_blob"] += "\n" + str(a["text"])
    f["script_mtime"] = sf.get("mtime")
    return f


# ---------------------------------------------------------------- policies (чисті функції)
def _rule(policy, rule, verdict, value=None, threshold=None, **kw):
    d = {"policy": policy, "rule": f"{policy}.{rule}", "verdict": verdict, "value": value, "threshold": threshold}
    d.update(kw)
    return d


def _walk_bad(obj, path=""):
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).startswith("_"): continue
            bad += _walk_bad(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj): bad += _walk_bad(v, f"{path}[{i}]")
    elif obj is None or (isinstance(obj, float) and (math.isinf(obj) or math.isnan(obj))):
        bad.append(path)
    return bad


def _legacy(policy, slug):
    return slug in set((policy.get("legacy") or {}).get("slugs") or [])


def _public_at(facts, platform="youtube"):
    """(state, at) публікації цього content_id на платформі; at — коли стала/стане публічною."""
    for p in facts.get("own_publications") or []:
        if p["platform"] == platform: return p["state"], _ts(p.get("scheduled_at"))
    return None, None


def p_circuit_breaker(a, f, P, ctx):
    out, now = [], _ts(f.get("now"))
    for b in f.get("breaker") or []:
        if b["scope"] not in ("global", ctx["scope"]): continue
        cd = _ts(b.get("cooldown_until"))
        if b["state"] == "open" and (cd is None or now < cd):
            out.append(_rule("circuit_breaker", "open", "SAFE_MODE", b["scope"], "closed", reason=b.get("reason")))
        elif b["state"] in ("open", "half_open"):
            out.append(_rule("circuit_breaker", "half_open", "CANARY", b["scope"], "closed", scope="probe"))
    return out


def p_hard_deny(a, f, P, ctx):
    out = []
    if a.get("type") not in ACTIONS:
        out.append(_rule("hard_deny", "unknown_action", "BLOCK", a.get("type"), sorted(ACTIONS)))
    bad = _walk_bad({k: v for k, v in P.items() if k != "legacy"})
    if bad:
        out.append(_rule("hard_deny", "invalid_threshold", "SAFE_MODE", bad[:10], "finite, not null",
                         note="null/∞ у бюджеті чи порозі = E-дія (§3.7, §12 п.7): BLOCK + SAFE_MODE"))
    if P.get("mode") not in ("shadow", "enforce"):
        out.append(_rule("hard_deny", "invalid_mode", "SAFE_MODE", P.get("mode"), ["shadow", "enforce"]))
    return out


def p_budget(a, f, P, ctx):
    B, out = P["budget"], []
    if ctx["scope"] != "youtube": return out
    used = (f.get("quota") or {}).get("used", 0)
    cost = B["yt_upload_cost"] if a["type"] == "youtube_upload" else B["yt_comment_cost"]
    nxt = _ts((f.get("quota") or {}).get("window_start"))
    nxt = _iso(nxt + dt.timedelta(days=1)) if nxt else None
    if used > B["yt_quota_day"] * B["yt_safe_mode_ratio"]:
        out.append(_rule("budget", "yt_quota_overrun", "SAFE_MODE", used, B["yt_quota_day"] * B["yt_safe_mode_ratio"]))
    elif used + cost > B["yt_quota_day"]:
        out.append(_rule("budget", "yt_quota", "RETRY_LATER", used + cost, B["yt_quota_day"], until=nxt))
    elif a["type"] != "youtube_upload" and used >= B["yt_soft_stop"]:
        out.append(_rule("budget", "yt_soft_stop", "RETRY_LATER", used, B["yt_soft_stop"], until=nxt))
    if a.get("tts_requests") is not None and a["tts_requests"] > B["tts_per_day"]:
        out.append(_rule("budget", "tts", "RETRY_LATER", a["tts_requests"], B["tts_per_day"], until=nxt))
    return out


def _is_long(slug, P):
    return any(slug.startswith(x) for x in P["rate_limit"]["long_prefixes"])


def p_rate_limit(a, f, P, ctx):
    R, out = P["rate_limit"], []
    day = (_ts(f.get("publish_at")) or _ts(f.get("now"))).date().isoformat()
    slug = f.get("content_id") or ""
    if ctx["rate"] == "youtube":
        mine_long = (f.get("script") or {}).get("kind") == "long" if (f.get("script") or {}).get("exists") \
            else _is_long(slug, P)
        key = "long_per_day" if mine_long else "shorts_per_day"
        same = [n for n in f.get("nearby") or [] if n["at"][:10] == day and _is_long(n["content_id"], P) == mine_long]
    else:
        key = f"{ctx['rate']}_per_day"
        same = [n for n in f.get("nearby") or [] if n["at"][:10] == day]
    lim, n = R[key], len(same) + 1
    if n > lim * R["safe_mode_factor"]:
        out.append(_rule("rate_limit", key, "SAFE_MODE", n, lim, day=day))
    elif n > lim:
        until = _iso(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=1))
        out.append(_rule("rate_limit", key, "RETRY_LATER", n, lim, day=day, until=until,
                         with_=[s["content_id"] for s in same]))
    return out


def p_duplicate(a, f, P, ctx):
    D, out, fl = P["duplicate"], [], f.get("files") or {}
    if f.get("duplicate_error"):
        return [_rule("duplicate", "check_failed", "RETRY_LATER", f["duplicate_error"], "ok")]
    for p in f.get("own_publications") or []:
        if p["platform"] == ctx["platform"] and p["state"] in ctx["dup_states"]:
            out.append(_rule("duplicate", "publication_exists", "BLOCK", f"{p['platform']}={p['state']}",
                             list(ctx["dup_states"]), external_id=p.get("external_id")))
    t = a["type"]
    if t == "youtube_upload" and (fl.get("in_uploaded") or fl.get("in_reserve")):
        out.append(_rule("duplicate", "slug_uploaded", "BLOCK", fl.get("video_id"), "slug ∉ uploaded.json/reserve.json"))
    if t == "tiktok_publish" and fl.get("tiktok_posted"):
        out.append(_rule("duplicate", "tiktok_posted_auto", "BLOCK", True, False))
    if t == "site_publish" and f.get("articles"):
        out.append(_rule("duplicate", "article_exists", "BLOCK", [x["file"] for x in f["articles"]], []))
    s = f.get("similarity")
    if s:
        if s.get("title_exact"):
            out.append(_rule("duplicate", "title_exact", "BLOCK", s["title_with"], "унікальна назва"))
        elif s["title_max"] >= D["title_block"]:
            out.append(_rule("duplicate", "title_similar", "BLOCK", s["title_max"], D["title_block"], with_=s["title_with"]))
        elif s["title_max"] >= D["title_canary"]:
            out.append(_rule("duplicate", "title_similar", "CANARY", s["title_max"], D["title_canary"],
                             with_=s["title_with"], scope="remake_experiment"))
        if (s.get("script_max") or 0) >= D["script_block"]:
            out.append(_rule("duplicate", "script_similar", "BLOCK", s["script_max"], D["script_block"], with_=s["script_with"]))
    return out


def p_fact(a, f, P, ctx):
    if not ctx["fact"]: return []
    F, fc, out = P["fact"], f.get("fact") or {}, []
    legacy = ctx["legacy"]
    if not fc.get("exists"):
        if legacy:
            return [_rule("fact", "missing_legacy", "DEGRADE", None, "*_factcheck_independent.md", mode="no_tiktok",
                          self_check=fc.get("self_check_exists"))]
        return [_rule("fact", "missing", "BLOCK", None, "*_factcheck_independent.md", self_check=fc.get("self_check_exists"))]
    if fc.get("verdict") is None:
        out.append(_rule("fact", "no_verdict", "BLOCK", None, "останній рядок «Вердикт: PASS|FAIL»"))
    elif fc["verdict"] == "FAIL":
        out.append(_rule("fact", "verdict_fail", "BLOCK", "FAIL", "PASS"))
    if fc.get("fail", 0) > F["max_fail"]:
        out.append(_rule("fact", "fail_rows", "BLOCK", fc["fail"], F["max_fail"], rows=fc.get("fail_rows")))
    if fc.get("fail_earlier") and not fc.get("final_round_rows"):
        out.append(_rule("fact", "fail_not_rechecked", "BLOCK", fc["fail_earlier"], "таблиця повторної перевірки"))
    if fc.get("unverified_claimed", 0) > F["max_unverified_claimed"]:
        out.append(_rule("fact", "unverified_claimed", "BLOCK", fc["unverified_claimed"], F["max_unverified_claimed"],
                         rows=fc.get("unverified_rows")))
    if fc.get("unverified_not_claimed", 0) > F["max_unverified_not_claimed"]:
        out.append(_rule("fact", "unverified_not_claimed", "BLOCK", fc["unverified_not_claimed"],
                         F["max_unverified_not_claimed"]))
    if fc.get("rows", 0) == 0 and fc.get("verdict"):
        out.append(_rule("fact", "no_status_table", "BLOCK", 0, "≥1 рядок зі статусом"))
    sm, fm = f.get("script_mtime"), fc.get("mtime")
    if sm and fm and fm < sm:
        out.append(_rule("fact", "stale", F.get("stale_is", "DEGRADE"), fm, sm, mode="no_tiktok",
                         note="сценарій змінено після фактчеку — перезапустити фактчекера"))
    return out


def _tier(host, S):
    def m(d): return host == d or host.endswith("." + d)
    if any(host.endswith(s) for s in S["tier0_suffixes"]) or any(m(d) for d in S["tier0_domains"]): return 0
    if any(m(d) for d in S["own"]): return None
    if any(m(d) for d in S["tier1"]): return 1
    if any(m(d) for d in S["tier2"]): return 2
    return 3


def source_stats(f, P):
    S = P["sources"]
    hosts = sorted(set((f.get("sources") or {}).get("factcheck", []) + (f.get("sources") or {}).get("description", [])))
    tiers = {h: _tier(h, S) for h in hosts}
    counted = {h: t for h, t in tiers.items() if t is not None}
    t1 = [h for h, t in counted.items() if t == 1]
    return {"hosts": counted, "tier0": [h for h, t in counted.items() if t == 0],
            "tier1_share": _r(len(t1) / len(counted)) if counted else None, "n": len(counted)}


def p_source_credibility(a, f, P, ctx):
    if not ctx["fact"]: return []
    S, st, out = P["sources"], source_stats(f, P), []
    if st["tier0"]:
        out.append(_rule("source_credibility", "tier0", "BLOCK", st["tier0"], 0))
    if st["n"] == 0:
        out.append(_rule("source_credibility", "no_sources", "DEGRADE", 0, "≥1 URL", mode="no_tiktok"))
    elif st["tier1_share"] < S["min_tier1_share"]:
        out.append(_rule("source_credibility", "tier1_share", "DEGRADE", st["tier1_share"], S["min_tier1_share"],
                         mode="no_tiktok"))
    for art in f.get("articles") or []:
        u = art.get("source_url")
        if u and re.fullmatch(r"https?://[^/]+/?", u):
            out.append(_rule("source_credibility", "article_source_root", "BLOCK", u, "конкретна сторінка (CLAUDE.md)"))
    return out


def p_quality(a, f, P, ctx):
    if not ctx["quality"]: return []
    Q, out, m = P["quality"], [], f.get("media") or {}
    legacy, skip = ctx["legacy"], set((P.get("legacy") or {}).get("skip_checks") or []) if ctx["legacy"] else set()
    long = (f.get("script") or {}).get("kind") == "long"
    if not m.get("exists"):
        return [_rule("quality", "no_render", "BLOCK", None, ctx["quality"])]
    if m.get("probe_error") or m.get("duration") is None:
        return [_rule("quality", "probe_failed", "BLOCK", m.get("probe_error"), "ffprobe OK")]
    if not m.get("has_video") or not m.get("has_audio"):
        out.append(_rule("quality", "streams", "BLOCK", {"video": m.get("has_video"), "audio": m.get("has_audio")}, "a+v"))
    d = m["duration"]
    if long:
        if d < Q["long_min_s"]: out.append(_rule("quality", "long_too_short", "BLOCK", d, Q["long_min_s"]))
    else:
        if d > Q["short_max_s"]:
            out.append(_rule("quality", "short_too_long", "BLOCK", d, Q["short_max_s"]))
        elif d > Q["short_target_s"]:
            out.append(_rule("quality", "short_above_target", "DEGRADE", d, Q["short_target_s"], mode="no_tiktok"))
    if a["type"] == "youtube_upload" and m.get("width"):
        want = Q["long_wh"] if long else Q["short_wh"]
        if [m.get("width"), m.get("height")] != list(want):
            out.append(_rule("quality", "resolution", "BLOCK", [m.get("width"), m.get("height")], want))
    cap = {"tiktok_publish": Q["tiktok_max_bytes"], "tg_post": Q["tg_max_bytes"]}.get(a["type"])
    if cap and m.get("bytes", 0) > cap:
        out.append(_rule("quality", "file_size", "BLOCK", m["bytes"], cap))
    mv = m.get("mean_volume_db")
    if m.get("has_audio") and mv is not None and mv <= Q["min_mean_volume_db"]:
        out.append(_rule("quality", "silent", "BLOCK", mv, Q["min_mean_volume_db"]))
    elif "silence" not in skip:
        gaps = []
        for s, e in m.get("silences") or []:
            e = min(e if e is not None else d, d - Q["silence_tail_ignore_s"])
            if e - s >= Q["max_silence_s"]: gaps.append([s, _r(e, 2)])
        if gaps: out.append(_rule("quality", "silence_gap", "BLOCK", gaps[:5], Q["max_silence_s"]))
    v = f.get("voice") or {}
    if v.get("ran") and v.get("rc") != 0:
        out.append(_rule("quality", "voice_check", "BLOCK", v.get("out"), "exit 0 (F0 143±8 Гц)"))
    elif not v.get("ran") and not legacy:
        out.append(_rule("quality", "voice_check_missing", "BLOCK", v.get("reason"), "voice_check.py exit 0"))
    if "asr" not in skip:
        asr = f.get("asr")
        if not asr:
            out.append(_rule("quality", "asr_missing", "BLOCK", None, "eps/<slug>/audit_vo.json (audit_vo.py --json)"))
        else:
            segs = [s.get("match") for s in asr.get("segments") or [] if s.get("match") is not None]
            worst = min(segs) if segs else None
            if worst is not None and worst < Q["asr_segment_min"]:
                out.append(_rule("quality", "asr_segment", "BLOCK", _r(worst), Q["asr_segment_min"]))
            if asr.get("overall_match") is not None and asr["overall_match"] < Q["asr_overall_min"]:
                out.append(_rule("quality", "asr_overall", "BLOCK", _r(asr["overall_match"]), Q["asr_overall_min"]))
    if a["type"] == "youtube_upload":
        th = [t for t in f.get("thumb") or [] if 0 < t["bytes"] < Q["thumb_max_bytes"]]
        if not th:
            out.append(_rule("quality", "thumb", "BLOCK", f.get("thumb"), f"thumb*.jpg, 0<size<{Q['thumb_max_bytes']}"))
    return out


def high_risk_matches(text, P):
    t, out = (text or "").lower(), {}
    for cat, c in sorted(P["high_risk"]["categories"].items()):
        hits = sorted({m.group(0) for pat in c["patterns"] for m in re.finditer(pat, t)})
        if hits: out[cat] = hits[:5]
    return out


def p_high_risk(a, f, P, ctx):
    H = P["high_risk"]
    hits = high_risk_matches(f.get("text_blob"), P)
    if not hits: return []
    fc, st = f.get("fact") or {}, source_stats(f, P)
    desc = ((f.get("script") or {}).get("description") or "").lower()
    missing = []
    if a["type"] != "yt_comment" and a["type"] != "indexnow":
        if not fc.get("exists"): missing.append("factcheck")
        if (st["tier1_share"] or 0) < H["require_tier1_share"]: missing.append(f"tier1_share={st['tier1_share']}")
        if fc.get("unverified_claimed", 0) > 0: missing.append("unverified_claimed")
        if fc.get("unverified_not_claimed", 0) > H["max_unverified_not_claimed"]: missing.append("unverified_not_claimed")
        for cat in hits:
            rx = H["categories"][cat].get("disclaimer")
            if rx and not re.search(rx, desc): missing.append(f"disclaimer:{cat}")
    if missing:
        return [_rule("high_risk", "requirements", "BLOCK", hits, "tier1 100%, UNVERIFIED claimed 0, дисклеймер",
                      missing=missing)]
    return [_rule("high_risk", "topic", "DEGRADE", hits, "canary-вікно для TG/TikTok", mode="youtube_site_first")]


def _slot_ok(t, kind, P):
    names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for s in P["schedule"]["slots"].get(kind, []):
        day, hm = s.split("@")
        if (day == "*" or day == names[t.weekday()]) and hm == t.strftime("%H:%M"): return True
    return False


def p_schedule_conflict(a, f, P, ctx):
    S, out, t = P["schedule"], [], a["type"]
    now, at = _ts(f.get("now")), _ts(f.get("publish_at"))
    yst, yat = _public_at(f, "youtube")
    if t == "youtube_upload":
        if at is None:
            return out   # резерв: private без дати
        if not ctx["legacy"] or not (f.get("files") or {}).get("in_uploaded"):
            if at < now + dt.timedelta(minutes=S["min_lead_min"]):
                out.append(_rule("schedule_conflict", "publish_at_past", "BLOCK", _iso(at), f"≥ now+{S['min_lead_min']}хв"))
        gap = dt.timedelta(minutes=S["min_gap_min"])
        clash = [n for n in f.get("nearby") or [] if abs(_ts(n["at"]) - at) < gap]
        if clash:
            busy = [_ts(n["at"]) for n in f.get("nearby") or []]
            nxt = at
            for _ in range(14):
                nxt += dt.timedelta(days=1)
                if all(abs(b - nxt) >= gap for b in busy): break
            out.append(_rule("schedule_conflict", "slot_taken", "RETRY_LATER", _iso(at), f"gap ≥{S['min_gap_min']}хв",
                             with_=[n["content_id"] for n in clash], until=_iso(nxt)))
        kind = (f.get("script") or {}).get("kind", "short")
        if not _slot_ok(at, kind, P):
            out.append(_rule("schedule_conflict", "off_grid", "CANARY", _iso(at), P["schedule"]["slots"].get(kind),
                             scope="publish_time_experiment"))
    elif t in ("tg_post", "yt_comment", "tiktok_publish"):
        if yst is None:
            out.append(_rule("schedule_conflict", "no_youtube", "BLOCK", None, "youtube scheduled/published"))
        else:
            wait = S["tiktok_after_youtube_min"] if t == "tiktok_publish" else 0
            ready = (yat or now) + dt.timedelta(minutes=wait)
            if yst not in ("published", "distributed", "scheduled") or (yat and now < ready):
                out.append(_rule("schedule_conflict", "before_youtube_public", "RETRY_LATER", _iso(now),
                                 _iso(ready), until=_iso(ready), wait_min=wait))
        if t == "yt_comment":
            cat = _ts((f.get("files") or {}).get("comment_at"))
            if cat and now < cat:
                out.append(_rule("schedule_conflict", "comment_at", "RETRY_LATER", _iso(now), _iso(cat), until=_iso(cat)))
    elif t == "indexnow":
        wst, wat = _public_at(f, "website")
        if wst is None or (wat and now < wat):
            out.append(_rule("schedule_conflict", "site_not_live", "RETRY_LATER", wst, "website published",
                             until=_iso(wat) if wat else None))
    return out


def p_canary(a, f, P, ctx):
    if a.get("experiment_id"):
        return [_rule("canary", "experiment", "CANARY", a["experiment_id"], "baseline", scope="youtube_only", max_items=1)]
    return []


def p_rollback(a, f, P, ctx, prior):
    R, out = P["rollback"], []
    plat = ctx["platform"]
    if plat not in R["plans"]:
        return [_rule("rollback", "no_plan", "DEGRADE", plat, "rollback_plan", mode="skip_platform")]
    if plat in R["no_rollback"]:
        dirty = [r["rule"] for r in prior if r["policy"] in ("fact", "quality", "source_credibility", "high_risk")
                 and r["verdict"] != "ALLOW"]
        yst, yat = _public_at(f, "youtube")
        now = _ts(f.get("now"))
        win = dt.timedelta(minutes=P["schedule"]["tiktok_after_youtube_min"])
        yt_ok = yst in ("published", "distributed", "scheduled") and yat is not None and now >= yat + win
        if plat == "indexnow": yt_ok, dirty = True, []
        if dirty or not yt_ok:
            out.append(_rule("rollback", "irreversible", "DEGRADE", {"dirty": dirty, "youtube_window_ok": yt_ok},
                             "fact/quality ALLOW + YouTube ≥60 хв", mode="skip_platform"))
    return out


def p_publication(a, f, P, ctx):
    out = []
    if not f.get("content_id"):
        return [_rule("publication", "no_content_id", "BLOCK", None, "slug")]
    sf = f.get("script") or {}
    if a["type"] in ("youtube_upload", "tg_post", "tiktok_publish") and not sf.get("exists") and not ctx["legacy"]:
        out.append(_rule("publication", "no_script", "BLOCK", None, "eps/<key>.py"))
    if a["type"] == "youtube_upload" and sf.get("idea_id") is None and not ctx["legacy"]:
        out.append(_rule("publication", "no_idea_link", "DEGRADE", None, "IDEA_ID / «ідея #N» у шапці",
                         mode="legacy_like", note="§4 п.2: до міграції ідей — DEGRADE, не BLOCK"))
    return out


POLICIES = {
    "circuit_breaker": p_circuit_breaker, "hard_deny": p_hard_deny, "budget": p_budget, "rate_limit": p_rate_limit,
    "duplicate": p_duplicate, "fact": p_fact, "source_credibility": p_source_credibility, "quality": p_quality,
    "high_risk": p_high_risk, "schedule_conflict": p_schedule_conflict, "canary": p_canary, "rollback": p_rollback,
    "publication": p_publication,
}


def _clean(o):
    if isinstance(o, dict): return {k.rstrip("_"): _clean(v) for k, v in o.items()}
    if isinstance(o, list): return [_clean(v) for v in o]
    if isinstance(o, float): return _r(o)
    return o


def decide(action, facts, policy):
    """Чиста функція: (action, facts, policy) → {result, rules_triggered, evidence, ...}. Без I/O."""
    a = dict(action)
    t = a.get("type")
    spec = ACTIONS.get(t)
    slug = facts.get("content_id") or ""
    rules, evidence = [], {}
    hd = p_hard_deny(a, facts, policy, {})
    if hd or not spec:
        rules = hd or [_rule("hard_deny", "unknown_action", "BLOCK", t, sorted(ACTIONS))]
    else:
        ctx = dict(spec, legacy=_legacy(policy, slug))
        for name in ORDER:
            if name == "hard_deny": continue
            try:
                r = POLICIES[name](a, facts, policy, ctx, rules) if name == "rollback" else POLICIES[name](a, facts, policy, ctx)
            except (KeyError, TypeError, ValueError) as e:   # битий policy.json / факти → fail-closed
                r = [_rule(name, "engine_error", "BLOCK", f"{type(e).__name__}: {e}"[:200], "no error")]
            evidence[name] = "ALLOW" if not r else max((x["verdict"] for x in r), key=STRENGTH.get)
            rules += r
        evidence["legacy"] = ctx["legacy"]
        evidence["sources"] = source_stats(facts, policy) if "sources" in policy else None
        evidence["high_risk_matches"] = high_risk_matches(facts.get("text_blob"), policy) if "high_risk" in policy else None
    rules = _clean(rules)
    result = max([r["verdict"] for r in rules] or ["ALLOW"], key=STRENGTH.get)
    modes = sorted({r["mode"] for r in rules if r.get("mode") and r["verdict"] == "DEGRADE"})
    scopes = sorted({r["scope"] for r in rules if r.get("scope") and r["verdict"] == "CANARY"})
    until = sorted({r["until"] for r in rules if r.get("until") and r["verdict"] == "RETRY_LATER"})
    return {"result": result, "rules_triggered": rules, "evidence": _clean(evidence),
            "degrade_modes": modes, "canary_scopes": scopes, "retry_until": until[-1] if until else None,
            "action": t, "content_id": slug}


def evaluate(action, facts=None, policy=None, now=None):
    """evaluate(action) → {result: ALLOW|BLOCK|RETRY_LATER|CANARY|DEGRADE|SAFE_MODE, rules_triggered, evidence}."""
    pv = None
    if policy is None: policy, pv = load_policy()
    if facts is None: facts = collect(action, policy, now)
    out = decide(action, facts, policy)
    out["policy_version"] = pv or policy_version_of(policy)
    return out


# ---------------------------------------------------------------- gate / replay
def gate(action, *, agent_name="policy_engine", run_id=None, now=None, conn=None):
    """Завжди пише рішення в ops.decide(). shadow → proceed=True завжди; enforce → proceed лише ALLOW/CANARY/DEGRADE.
    Помилка самого policy: shadow → proceed=True (лог), enforce → BLOCK (fail-closed для C/D)."""
    import ops
    a = dict(action)
    facts, err = None, None
    try:
        policy, pv = load_policy()
        mode = policy.get("mode")
    except Exception as e:  # noqa: BLE001
        policy, pv, mode = None, None, "enforce"
        err = f"policy.json: {type(e).__name__}: {e}"
    if policy is not None:
        try:
            facts = collect(a, policy, now)
            dec = decide(a, facts, policy)
            err = None
        except Exception as e:  # noqa: BLE001
            facts, err = None, f"{type(e).__name__}: {e}"
    if err:
        dec = {"result": "BLOCK", "rules_triggered": [_rule("engine", "error", "BLOCK", err[:300], "no error")],
               "evidence": {}, "degrade_modes": [], "canary_scopes": [], "retry_until": None}
    shadow = mode == "shadow"
    proceed = True if shadow else dec["result"] in PROCEED_IN_ENFORCE
    snapshot = {"action": a, "facts": facts, "policy": policy, "policy_version": pv}
    out = {"mode": mode or "enforce", "proceed": proceed, "enforce_result": dec["result"],
           "would_proceed_in_enforce": dec["result"] in PROCEED_IN_ENFORCE,
           "degrade_modes": dec["degrade_modes"], "canary_scopes": dec["canary_scopes"],
           "retry_until": dec["retry_until"], "error": err}
    did = ops.decide("policy", agent_name, snapshot, out, run_id=run_id, model="rule", confidence=1.0,
                     rules_triggered=dec["rules_triggered"], policy_result=dec["result"], policy_version=pv,
                     status="failed" if err else "decided", related_content_id=(facts or {}).get("content_id"),
                     related_video_id=((facts or {}).get("files") or {}).get("video_id"), conn=conn)
    out.update(decision_id=did, result=dec["result"], rules_triggered=dec["rules_triggered"], evidence=dec.get("evidence"))
    return out


def _load_snapshot(raw):
    snap = json.loads(raw)
    if isinstance(snap, dict) and set(snap) == {"sha256", "path"}:
        body = (ROOT / snap["path"]).read_text(encoding="utf-8")
        data = json.loads(body)
        if hashlib.sha256(canonical(data).encode()).hexdigest() != snap["sha256"]:
            raise PolicyError(f"snapshot {snap['path']}: sha256 не збігається")
        return data
    return snap


def replay(decision_id, conn=None):
    """Відтворює рішення з input_snapshot (без мережі й без читання файлів) і порівнює з журналом."""
    import ops
    c = conn or ops.db()
    row = c.execute("select * from agent_decisions where decision_id=?", (decision_id,)).fetchone()
    if not row: raise KeyError(decision_id)
    if row["decision_type"] != "policy": raise PolicyError(f"{decision_id}: decision_type={row['decision_type']}, не policy")
    snap = _load_snapshot(row["input_snapshot"])
    stored_rules = json.loads(row["rules_triggered"]) if row["rules_triggered"] else []
    if snap.get("policy") is None or snap.get("facts") is None:
        return {"decision_id": decision_id, "match": False, "reason": "рішення з помилкою engine — нема що відтворювати",
                "stored": row["policy_result"]}
    dec = decide(snap["action"], snap["facts"], snap["policy"])
    same_rules = canonical(dec["rules_triggered"]) == canonical(stored_rules)
    return {"decision_id": decision_id, "match": dec["result"] == row["policy_result"] and same_rules,
            "stored": row["policy_result"], "replayed": dec["result"], "rules_equal": same_rules,
            "policy_version": row["policy_version"]}


# ---------------------------------------------------------------- CLI
def explain(name=None, policy=None):
    policy = policy or load_policy()[0]
    L = [f"mode={policy.get('mode')}  version={policy.get('version')}",
         "Порядок: " + " → ".join(ORDER), "Сила: " + " > ".join(sorted(STRENGTH, key=STRENGTH.get, reverse=True)),
         "Дії: " + ", ".join(f"{k}→{v['platform']}" for k, v in ACTIONS.items())]
    for sec, body in policy.items():
        if not isinstance(body, dict) or sec.startswith("_") or (name and sec != name): continue
        L.append(f"\n[{sec}]")
        why = body.get("_why", {})
        for k, v in body.items():
            if k.startswith("_"): continue
            vs = json.dumps(v, ensure_ascii=False)
            if len(vs) > 110: vs = vs[:107] + "..."
            L.append(f"  {k} = {vs}\n      ↳ {why.get(k, '— (немає _why)')}")
    return "\n".join(L)


def _summary(d):
    rs = [f"{r['rule']}={r['verdict']}" + (f"({r['value']})" if r.get("value") not in (None, [], {}) and
                                            len(str(r.get("value"))) < 40 else "") for r in d["rules_triggered"]]
    return f"{d['content_id']} {d['action']}: {d['result']}" + (" — " + "; ".join(rs) if rs else "")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="policy.py")
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("check"); c.add_argument("target")
    c.add_argument("--action", required=True, choices=sorted(ACTIONS))
    c.add_argument("--now"); c.add_argument("--publish-at"); c.add_argument("--experiment")
    c.add_argument("--record", action="store_true", help="записати рішення в ops.sqlite через gate()")
    c.add_argument("--json", action="store_true")
    r = sp.add_parser("replay"); r.add_argument("decision_id")
    e = sp.add_parser("explain"); e.add_argument("policy", nargs="?")
    a = ap.parse_args(argv)
    if a.cmd == "explain":
        print(explain(a.policy)); return 0
    if a.cmd == "replay":
        res = replay(a.decision_id); print(json.dumps(res, ensure_ascii=False, indent=1)); return 0 if res["match"] else 1
    action = {"type": a.action, "target": a.target, "actor": "cli"}
    if a.publish_at: action["publish_at"] = a.publish_at
    if a.experiment: action["experiment_id"] = a.experiment
    if a.record:
        res = gate(action, agent_name="policy_cli", now=a.now)
        res.setdefault("action", a.action); res.setdefault("content_id", None)
    else:
        res = evaluate(action, now=a.now)
    if a.json: print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    else:
        print(_summary({"content_id": res.get("content_id") or a.target, "action": a.action, "result": res["result"],
                        "rules_triggered": res["rules_triggered"]}))
        if res.get("decision_id"): print(f"decision_id={res['decision_id']} mode={res.get('mode')} proceed={res.get('proceed')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
