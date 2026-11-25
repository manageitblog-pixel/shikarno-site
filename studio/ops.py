#!/usr/bin/env python3
"""Журнал автономії ШІкарно (P0 plan 22.11, кроки 1–2): studio/data/ops.sqlite.

Таблиці — docs/org/autonomy-plan-2026-11-22.md §5.1 (publications, pub_events), §7.1 (agent_decisions, runs),
§8.1 (experiments, experiment_items), §9 (breaker).
agent_decisions і pub_events — append-only: SQLite-тригери забороняють UPDATE/DELETE, кожен рядок має
prev_hash/hash = sha256(prev_hash || canonical_json(рядок без hash)); verify() перераховує ланцюжки.
publications змінюються лише через transition() дозволеними ребрами (EDGES), кожен перехід → pub_events.

Поки що (до кроку 4, після 25.11 18Z) ЖОДЕН наявний код ops.py не викликає. backfill лише читає JSON.

CLI: python3 studio/ops.py verify | backfill | report [--date YYYY-MM-DD] | stats | dump | restore [--force]
     python3 studio/ops.py decide --type T --agent A --input @in.json [--output @out.json] [--content ID] ...
     python3 studio/ops.py run start TASK [--agent A] | run finish RUN_ID [--status ok|failed] [--error ...]
     python3 studio/ops.py exp list | exp status ID | exp start ID --date YYYY-MM-DD --control a,b [--variant x]
     python3 studio/ops.py exp add ID CONTENT_ID [--arm variant|control] | exp redesign ID --reason ... --set f=v
     python3 studio/ops.py exp design ID --agent A --reason ... --set hypothesis=... --set variant=... (новий designed)
БД можна підмінити змінною SHK_OPS_DB (тести).

ЗАХИСТ ВІД РЕСТАРТУ (25.11: рестарт контейнера стер ops.sqlite, бо він у .gitignore): після кожної успішної транзакції
(_tx commit, run start/finish) жива база пишеться текстовим SQL-дампом у studio/data/ops_dump.sql (у git; лише для
бойової БД DB_PATH, не для тестових). Дамп комітиться разом зі щоденним `lake.py snapshot`. Відновлення:
`python3 studio/ops.py restore` (bootstrap.sh робить це сам, якщо ops.sqlite немає).
"""
import argparse, datetime as dt, hashlib, json, os, re, sqlite3, subprocess, sys, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import util  # noqa: E402

DB_PATH = HERE / "data" / "ops.sqlite"
DUMP_PATH = HERE / "data" / "ops_dump.sql"
SNAP_DIR = HERE / "data" / "snapshots"
GENESIS = "0" * 64
SNAPSHOT_MAX = 64 * 1024
SITE_URL = "https://shikarno.com.ua"
SECTIONS = {"news": "novyny", "rozbir": "rozbory", "dajdzhest": "dajdzhest", "misyats": "za-misyats"}

PLATFORMS = ("youtube", "telegram", "tiktok", "website", "indexnow", "yt_comment", "yt_playlist")
STATES = ("pending", "validated", "approved_by_policy", "uploading", "in_doubt", "uploaded", "scheduled",
          "published", "distributed", "failed", "rolled_back", "compensated")
# §5.2: лінійний шлях; будь-який до-published стан → failed; uploading → in_doubt → reconcile;
# published/scheduled/distributed → rolled_back; rollback неможливий → compensated.
# Етапи, не застосовні на платформі (напр. telegram без uploaded/scheduled), пропускаються вперед по ланцюжку.
_CHAIN = ["pending", "validated", "approved_by_policy", "uploading", "uploaded", "scheduled", "published", "distributed"]
EDGES = {s: set() for s in STATES}
for i, s in enumerate(_CHAIN[:-1]):
    EDGES[s].add(_CHAIN[i + 1])
EDGES["approved_by_policy"] |= {"uploaded", "scheduled", "published"}   # сайт/коментар/TG/indexnow без upload-етапу
EDGES["uploading"] |= {"published", "scheduled", "in_doubt"}              # TG/коментар: posting → published
EDGES["uploaded"] |= {"published"}
EDGES["published"] |= {"rolled_back", "compensated"}
EDGES["scheduled"] |= {"rolled_back", "compensated"}
EDGES["distributed"] |= {"rolled_back", "compensated"}
EDGES["in_doubt"] |= {"uploaded", "published", "failed"}                 # лише reconcile, без повтору
EDGES["failed"] |= {"approved_by_policy"}                                  # повтор лише з нового approve
EDGES["rolled_back"] |= {"compensated"}
for s in ("pending", "validated", "approved_by_policy", "uploading", "uploaded", "scheduled"):
    EDGES[s].add("failed")

DECISION_TYPES = ("topic_select", "idea_approve", "format_select", "hook_select", "script_generate", "factcheck",
                  "publish", "seo_change", "meta_edit", "schedule_change", "strategy_change", "prompt_change",
                  "trigger_change", "tg_delete", "experiment", "policy", "rollback", "breaker", "legacy_allow")
POLICY_RESULTS = ("ALLOW", "BLOCK", "RETRY_LATER", "CANARY", "DEGRADE", "SAFE_MODE")
DECISION_STATUS = ("proposed", "decided", "executed", "failed", "dry_run", "superseded")


def _q(xs):
    return ",".join("'%s'" % x for x in xs)


SCHEMA = f"""
create table if not exists publications(
  content_id text not null, platform text not null check(platform in ({_q(PLATFORMS)})),
  state text not null check(state in ({_q(STATES)})), idem_key text unique, payload_digest text,
  external_id text, external_url text, session_ref text, scheduled_at text, attempts int default 0,
  policy_decision_id text, rollback_plan text, parent_content_id text, idea_id text, experiment_id text,
  legacy int default 0, updated_at text,
  primary key(content_id, platform));
create table if not exists pub_events(
  id integer primary key, content_id text, platform text, from_state text, to_state text,
  reason text, external_id text, decision_id text, run_id text, ts text, prev_hash text not null, hash text not null);
create trigger if not exists pub_events_ro_u before update on pub_events begin select raise(abort,'append-only'); end;
create trigger if not exists pub_events_ro_d before delete on pub_events begin select raise(abort,'append-only'); end;

create table if not exists agent_decisions(
  seq integer primary key autoincrement,
  decision_id text unique not null, run_id text not null, agent_name text not null,
  agent_version text, prompt_version text, model text,
  decision_type text not null check(decision_type in ({_q(DECISION_TYPES)})),
  input_snapshot text not null, output text, evidence_ids text, source_urls text, rules_triggered text,
  confidence real,
  policy_result text check(policy_result in ({_q(POLICY_RESULTS)}) or policy_result is null),
  policy_version text, code_version text, cost_tokens int, cost_usd real, started_at text, finished_at text,
  status text check(status in ({_q(DECISION_STATUS)})),
  rollback_ref text, related_content_id text, related_video_id text, related_platform_post_id text,
  prev_hash text not null, hash text not null);
create trigger if not exists ad_no_update before update on agent_decisions begin select raise(abort,'append-only'); end;
create trigger if not exists ad_no_delete before delete on agent_decisions begin select raise(abort,'append-only'); end;
create index if not exists ad_content on agent_decisions(related_content_id);
create index if not exists ad_run on agent_decisions(run_id);

create table if not exists runs(run_id text primary key, task text, trigger_id text, agent_name text,
  started_at text, finished_at text, status text, error text, api_calls int, retries int, tokens int, heartbeat_at text);

create table if not exists experiments(
  experiment_id text primary key, created_by text, hypothesis text not null,
  kind text check(kind in ('hook','format','duration','thumbnail','cta','publish_time','topic','prompt','strategy','metadata')),
  variant text not null, control text not null, audience_format text,
  start_date text, end_date text, sample_size int not null, max_share real default 0.3,
  success_metric text not null, threshold text not null, guardrail_metrics text,
  status text check(status in ('designed','running','collecting','decided')),
  result text, decision text check(decision in ('promote','pause','rollback') or decision is null),
  rollback_ref text, decision_id text);
create trigger if not exists exp_frozen before update of hypothesis, variant, control, threshold, success_metric on experiments
  when old.status in ('running','collecting','decided') begin select raise(abort,'experiment frozen after running'); end;
create table if not exists experiment_items(experiment_id text, content_id text,
  arm text check(arm in ('variant','control')), primary key(experiment_id, content_id));

create table if not exists breaker(scope text primary key, state text check(state in('closed','open','half_open')),
  reason text, opened_at text, cooldown_until text, probes_ok int, trips_24h int);
"""
REQUIRED_TRIGGERS = ("pub_events_ro_u", "pub_events_ro_d", "ad_no_update", "ad_no_delete")


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(s):
    return hashlib.sha256(s.encode() if isinstance(s, str) else s).hexdigest()


def canonical(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _js(v):
    return None if v is None else (v if isinstance(v, str) else canonical(v))


def db(path=None):
    path = str(path or os.environ.get("SHK_OPS_DB") or DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    c = sqlite3.connect(path, timeout=10, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("pragma busy_timeout=10000")
    c.execute("pragma journal_mode=WAL")
    c.execute("pragma foreign_keys=on")
    c.executescript(SCHEMA)
    return c


def code_version():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                              text=True, timeout=5).stdout.strip() or None
    except Exception:
        return None


# ---------- hash chain ----------
AD_COLS = ("seq", "decision_id", "run_id", "agent_name", "agent_version", "prompt_version", "model", "decision_type",
           "input_snapshot", "output", "evidence_ids", "source_urls", "rules_triggered", "confidence", "policy_result",
           "policy_version", "code_version", "cost_tokens", "cost_usd", "started_at", "finished_at", "status",
           "rollback_ref", "related_content_id", "related_video_id", "related_platform_post_id", "prev_hash")
PE_COLS = ("id", "content_id", "platform", "from_state", "to_state", "reason", "external_id", "decision_id", "run_id",
           "ts", "prev_hash")


def _row_hash(row, cols):
    return sha256(row["prev_hash"] + canonical({k: row[k] for k in cols}))


def _append(c, table, pk, cols, row):
    """У відкритій транзакції (BEGIN IMMEDIATE): дописує рядок у кінець ланцюжка."""
    last = c.execute(f"select {pk}, hash from {table} order by {pk} desc limit 1").fetchone()
    row[pk] = (last[pk] + 1) if last else 1
    row["prev_hash"] = last["hash"] if last else GENESIS
    row["hash"] = _row_hash(row, cols)
    keys = list(cols) + ["hash"]
    c.execute(f"insert into {table}({','.join(keys)}) values({','.join('?' * len(keys))})", [row[k] for k in keys])
    return row


class _tx:
    def __init__(self, c): self.c = c
    def __enter__(self):
        self.own = not self.c.in_transaction
        if self.own: self.c.execute("begin immediate")
        return self.c
    def __exit__(self, et, *_):
        if self.own:
            self.c.execute("rollback" if et else "commit")
            if not et: _after_commit(self.c)


# ---------- текстовий дамп у git (захист від рестарту контейнера) ----------
def _db_file(c):
    for r in c.execute("pragma database_list"):
        if r[1] == "main": return r[2] or ""
    return ""


def dump(conn=None, path=None):
    """Пише всю БД (схема, тригери, рядки) як SQL у path (типово studio/data/ops_dump.sql), атомарно.
    Читання в одній транзакції — дамп узгоджений, навіть якщо паралельно пишуть інші процеси."""
    c = conn or db(); path = Path(path or DUMP_PATH)
    own = not c.in_transaction
    if own: c.execute("begin")
    try:
        lines = list(c.iterdump())
    finally:
        if own: c.execute("commit")
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text("-- ШІкарно ops.sqlite dump (studio/ops.py dump); відновлення: python3 studio/ops.py restore\n"
                   + "\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return str(path)


_DEFER = {"n": 0, "pending": None}


class deferred_dump:
    """Пакетні записи (backfill): один дамп у кінці замість дампу після кожної транзакції."""
    def __enter__(self): _DEFER["n"] += 1
    def __exit__(self, *_):
        _DEFER["n"] -= 1
        c, _DEFER["pending"] = _DEFER["pending"], None
        if c is not None and _DEFER["n"] == 0: _after_commit(c)


def _after_commit(c):
    """Легкий гачок після commit: лише для бойової БД. Без git; помилка дампу не ламає запис."""
    if _DEFER["n"]:
        _DEFER["pending"] = c; return
    try:
        f = _db_file(c)
        if f and os.path.realpath(f) == os.path.realpath(DB_PATH):
            dump(c)
    except Exception as e:  # noqa: BLE001
        print(f"ops dump: {e}", file=sys.stderr)


def restore(dump_path=None, path=None, force=False):
    """Створює ops.sqlite з дампу. Якщо база вже є і в ній є рядки — відмова (без force)."""
    dump_path = Path(dump_path or DUMP_PATH); path = Path(path or os.environ.get("SHK_OPS_DB") or DB_PATH)
    if not dump_path.exists(): raise FileNotFoundError(dump_path)
    if path.exists() and not force:
        c = sqlite3.connect(str(path))
        try:
            n = sum(c.execute(f"select count(*) from {t}").fetchone()[0] for t in ("agent_decisions", "pub_events", "experiments")
                    if c.execute("select 1 from sqlite_master where name=?", (t,)).fetchone())
        finally:
            c.close()
        if n: raise FileExistsError(f"{path} уже має {n} рядків; --force, щоб перезаписати")
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(str(path) + ext): os.remove(str(path) + ext)
    c = sqlite3.connect(str(path))
    c.executescript(dump_path.read_text(encoding="utf-8")); c.close()
    v = verify(db(path))
    return {"restored": str(path), "from": str(dump_path), **v}


# ---------- decisions ----------
def decide(decision_type, agent_name, input_snapshot, output=None, *, run_id=None, agent_version=None,
           prompt_version=None, model=None, evidence_ids=None, source_urls=None, rules_triggered=None,
           confidence=None, policy_result=None, policy_version=None, cost_tokens=None, cost_usd=None,
           started_at=None, finished_at=None, status="decided", rollback_ref=None, related_content_id=None,
           related_video_id=None, related_platform_post_id=None, conn=None):
    """Додає рядок у agent_decisions (append-only). Повертає decision_id."""
    if decision_type not in DECISION_TYPES: raise ValueError(f"decision_type {decision_type!r}")
    if policy_result is not None and policy_result not in POLICY_RESULTS: raise ValueError(f"policy_result {policy_result!r}")
    if status not in DECISION_STATUS: raise ValueError(f"status {status!r}")
    did = str(uuid.uuid4())
    snap = _js(input_snapshot if input_snapshot is not None else {})
    if len(snap.encode()) > SNAPSHOT_MAX:   # великі входи — у файл, у журналі sha256 + шлях
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        p = SNAP_DIR / f"{did}.json"
        util.write_json_atomic(p, json.loads(snap) if snap[:1] in "[{" else snap)
        snap = canonical({"sha256": sha256(snap), "path": str(p.relative_to(ROOT))})
    ts = now()
    row = dict(decision_id=did, run_id=run_id or "adhoc", agent_name=agent_name, agent_version=agent_version,
               prompt_version=prompt_version, model=model, decision_type=decision_type, input_snapshot=snap,
               output=_js(output), evidence_ids=_js(evidence_ids), source_urls=_js(source_urls),
               rules_triggered=_js(rules_triggered), confidence=confidence, policy_result=policy_result,
               policy_version=policy_version, code_version=code_version(), cost_tokens=cost_tokens,
               cost_usd=cost_usd, started_at=started_at or ts, finished_at=finished_at or ts, status=status,
               rollback_ref=rollback_ref, related_content_id=related_content_id, related_video_id=related_video_id,
               related_platform_post_id=related_platform_post_id)
    c = conn or db()
    with _tx(c):
        _append(c, "agent_decisions", "seq", AD_COLS, row)
    return did


# ---------- runs ----------
def run_start(task, agent_name=None, trigger_id=None, conn=None):
    rid = str(uuid.uuid4()); ts = now(); c = conn or db()
    c.execute("insert into runs(run_id,task,trigger_id,agent_name,started_at,status,heartbeat_at,"
              "api_calls,retries,tokens) values(?,?,?,?,?,'running',?,0,0,0)",
              (rid, task, trigger_id, agent_name, ts, ts))
    if not c.in_transaction: _after_commit(c)
    return rid


def heartbeat(run_id, conn=None):
    (conn or db()).execute("update runs set heartbeat_at=? where run_id=?", (now(), run_id))


def run_finish(run_id, status="ok", error=None, api_calls=None, retries=None, tokens=None, conn=None):
    ts = now(); c = conn or db()
    cur = c.execute(
        "update runs set finished_at=?, heartbeat_at=?, status=?, error=?, api_calls=coalesce(?,api_calls),"
        " retries=coalesce(?,retries), tokens=coalesce(?,tokens) where run_id=?",
        (ts, ts, status, error, api_calls, retries, tokens, run_id))
    if cur.rowcount != 1: raise KeyError(run_id)
    if not c.in_transaction: _after_commit(c)


# ---------- publications ----------
def idem_key(content_id, platform, action, payload_digest):
    return sha256(f"{content_id}|{platform}|{action}|{payload_digest or ''}")


def _event(c, content_id, platform, frm, to, reason, external_id=None, decision_id=None, run_id=None):
    _append(c, "pub_events", "id", PE_COLS, dict(content_id=content_id, platform=platform, from_state=frm,
            to_state=to, reason=reason, external_id=external_id, decision_id=decision_id, run_id=run_id, ts=now()))


def pub_create(content_id, platform, state="pending", *, reason="create", legacy=0, payload_digest=None,
               action="publish", conn=None, **fields):
    """Створює картку (content_id, platform), якщо її ще немає. True — створено, False — вже була."""
    if platform not in PLATFORMS: raise ValueError(f"platform {platform!r}")
    if state not in STATES: raise ValueError(f"state {state!r}")
    c = conn or db()
    with _tx(c):
        if c.execute("select 1 from publications where content_id=? and platform=?", (content_id, platform)).fetchone():
            return False
        row = dict(content_id=content_id, platform=platform, state=state, legacy=legacy, updated_at=now(),
                   payload_digest=payload_digest,
                   idem_key=fields.pop("idem_key", None) or idem_key(content_id, platform, action, payload_digest),
                   **fields)
        c.execute(f"insert into publications({','.join(row)}) values({','.join('?' * len(row))})", list(row.values()))
        _event(c, content_id, platform, None, state, reason, row.get("external_id"),
               row.get("policy_decision_id"), fields.get("run_id"))
    return True


MUTABLE = ("external_id", "external_url", "session_ref", "scheduled_at", "policy_decision_id", "rollback_plan",
           "payload_digest", "experiment_id")


def transition(content_id, platform, to_state, reason, *, decision_id=None, run_id=None, conn=None, **fields):
    """Переводить картку лише дозволеним ребром EDGES. Повертає (from, to). ValueError — ребро заборонене."""
    bad = set(fields) - set(MUTABLE)
    if bad: raise ValueError(f"поля {sorted(bad)} не змінюються через transition")
    c = conn or db()
    with _tx(c):
        r = c.execute("select state, attempts from publications where content_id=? and platform=?",
                      (content_id, platform)).fetchone()
        if not r: raise KeyError((content_id, platform))
        frm = r["state"]
        if to_state not in EDGES.get(frm, ()):
            raise ValueError(f"перехід {frm} → {to_state} заборонено ({content_id}/{platform})")
        sets = dict(fields, state=to_state, updated_at=now())
        if to_state == "uploading": sets["attempts"] = (r["attempts"] or 0) + 1
        c.execute(f"update publications set {', '.join(k + '=?' for k in sets)} where content_id=? and platform=?",
                  [*sets.values(), content_id, platform])
        _event(c, content_id, platform, frm, to_state, reason, fields.get("external_id"), decision_id, run_id)
    return frm, to_state


# ---------- verify ----------
def _verify_chain(c, table, pk, cols):
    errs, prev, n = [], GENESIS, 0
    for row in c.execute(f"select * from {table} order by {pk}"):
        n += 1
        if row["prev_hash"] != prev:
            errs.append(f"{table} {pk}={row[pk]}: prev_hash не збігається з hash попереднього рядка")
        if _row_hash(row, cols) != row["hash"]:
            errs.append(f"{table} {pk}={row[pk]}: hash не збігається зі вмістом (підміна?)")
        prev = row["hash"]
    if n:
        mx = c.execute(f"select max({pk}) from {table}").fetchone()[0]
        if mx != n: errs.append(f"{table}: {n} рядків, але max {pk}={mx} (видалено рядки?)")
    return n, errs


def verify(conn=None):
    """Перевірка тригерів і хеш-ланцюжків. Повертає dict {ok, decisions, events, errors, head}."""
    c = conn or db(); errs = []
    have = {r[0] for r in c.execute("select name from sqlite_master where type='trigger'")}
    errs += [f"немає тригера {t}" for t in REQUIRED_TRIGGERS if t not in have]
    nd, e1 = _verify_chain(c, "agent_decisions", "seq", AD_COLS)
    ne, e2 = _verify_chain(c, "pub_events", "id", PE_COLS)
    errs += e1 + e2
    head = c.execute("select hash from agent_decisions order by seq desc limit 1").fetchone()
    return {"ok": not errs, "decisions": nd, "events": ne, "errors": errs, "head": head[0] if head else GENESIS}


# ---------- backfill (лише читання JSON / md) ----------
FM_KEYS = ("kind", "slug", "date", "youtube", "telegram_post", "title")


def front_matter(path):
    """Мінімальний розбір верхньорівневих скалярів front matter (stdlib, без yaml)."""
    raw = Path(path).read_text(encoding="utf-8")
    if not raw.startswith("---"): return {}
    fm = raw.split("---", 2)[1]
    out = {}
    for line in fm.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*?)\s*$", line)
        if m and m.group(1) in FM_KEYS and m.group(2):
            v = m.group(2)
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'": v = v[1:-1]
            out[m.group(1)] = v
    return out


def _parse_ts(s):
    if not s: return None
    s = str(s).strip().replace("~", "").replace(" ", "T", 1).rstrip("Z")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None: d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def _iso(d):
    return d.replace(microsecond=0).isoformat().replace("+00:00", "Z") if d else None


def backfill_sources(eps=None, posts=None):
    eps = Path(eps or "/home/claude/eps"); posts = Path(posts or ROOT / "content" / "posts")
    return {"uploaded": eps / "uploaded.json", "tiktok": eps / "tiktok.json",   # /home/claude/eps → studio/eps
            "comments": eps / "pending_comments.json", "posts": posts}


def backfill(conn=None, eps=None, posts=None, now_dt=None):
    """legacy=1 картки з наявних файлів. Ідемпотентно: існуюча (content_id, platform) не чіпається."""
    with deferred_dump():
        return _backfill(conn or db(), eps, posts, now_dt)


def _backfill(c, eps, posts, now_dt):
    src = backfill_sources(eps, posts)
    t0 = now_dt or dt.datetime.now(dt.timezone.utc)
    uploaded = util.read_json(src["uploaded"], {}) or {}
    tiktok = (util.read_json(src["tiktok"], {}) or {}).get("posted_auto") or {}
    comments = util.read_json(src["comments"], {}) or {}
    by_vid = {v: k for k, v in uploaded.items() if isinstance(v, str)}
    added = {p: 0 for p in PLATFORMS}; seen = {p: 0 for p in PLATFORMS}

    def add(content_id, platform, state, **kw):
        seen[platform] += 1
        if pub_create(content_id, platform, state, reason="legacy backfill", legacy=1, action="legacy",
                      payload_digest=kw.pop("digest", None), conn=c, **kw):
            added[platform] += 1

    # сайт (+ дата прем'єри для youtube і telegram_post)
    premiere = {}
    for md in sorted(src["posts"].glob("*.md")):
        fm = front_matter(md)
        slug = fm.get("slug") or md.stem[11:]
        when = _parse_ts(fm.get("date"))
        vid = fm.get("youtube")
        cid = by_vid.get(vid) or slug
        if vid and when: premiere[vid] = when
        url = f"{SITE_URL}/{SECTIONS.get(fm.get('kind', 'news'), 'novyny')}/{slug}/"
        st = "scheduled" if when and when > t0 else "published"
        add(cid, "website", st, external_id=slug, external_url=url, scheduled_at=_iso(when),
            digest=sha256(md.read_bytes()))
        tp = fm.get("telegram_post")
        if tp and str(tp).isdigit():
            add(cid, "telegram", "published", external_id=str(tp), external_url=f"https://t.me/shikarno_ai_ua/{tp}")
    # коментарі: черга pending_comments.json = yt_comment/scheduled (§5.2); прем'єра ≈ at коментаря
    for vid, item in comments.items():
        at = _parse_ts((item or {}).get("at"))
        if at and vid not in premiere: premiere[vid] = at
        add(by_vid.get(vid) or vid, "yt_comment", "scheduled", scheduled_at=_iso(at),
            digest=sha256((item or {}).get("text", "")), parent_content_id=by_vid.get(vid))
    # YouTube
    for slug, vid in uploaded.items():
        if not isinstance(vid, str): continue
        when = premiere.get(vid)
        st = "scheduled" if when and when > t0 else "published"
        add(slug, "youtube", st, external_id=vid, external_url=f"https://youtu.be/{vid}", scheduled_at=_iso(when))
    # TikTok (vidIQ posted_auto)
    for slug, item in tiktok.items():
        item = item or {}
        sched = _parse_ts(item.get("scheduled"))
        st = "published" if item.get("url") else ("scheduled" if sched else "uploaded")
        add(slug, "tiktok", st, external_id=item.get("postId"), external_url=item.get("url"),
            session_ref=item.get("postId"), scheduled_at=_iso(sched), parent_content_id=slug)
    total = sum(added.values())
    if total:
        decide("legacy_allow", "data_engineer", {"sources": {k: str(v) for k, v in src.items()}, "seen": seen},
               {"added": added}, model="rule", confidence=1.0, status="executed", conn=c)
    return {"added": added, "seen": seen, "total_added": total}


# ---------- experiments (§8) ----------
EXP_DESIGN_FIELDS = ("hypothesis", "variant", "control", "threshold", "success_metric", "guardrail_metrics",
                     "audience_format", "start_date", "end_date", "sample_size", "max_share", "kind")


def _exp(c, experiment_id):
    r = c.execute("select * from experiments where experiment_id=?", (experiment_id,)).fetchone()
    if not r: raise KeyError(experiment_id)
    return r


def exp_design(experiment_id, created_by, reason=None, conn=None, **fields):
    """Новий експеримент у статусі designed + рядок agent_decisions(experiment, action=design).
    Обов'язкові: hypothesis, variant, control, success_metric, threshold, sample_size. Дубль id — ValueError."""
    bad = set(fields) - set(EXP_DESIGN_FIELDS)
    if bad: raise ValueError(f"поля {sorted(bad)} не є полями дизайну")
    miss = [k for k in ("hypothesis", "variant", "control", "success_metric", "threshold", "sample_size") if not fields.get(k)]
    if miss: raise ValueError(f"бракує полів {miss}")
    c = conn or db()
    with _tx(c):
        if c.execute("select 1 from experiments where experiment_id=?", (experiment_id,)).fetchone():
            raise ValueError(f"{experiment_id} уже існує")
        row = dict(fields, experiment_id=experiment_id, created_by=created_by, status="designed")
        c.execute(f"insert into experiments({','.join(row)}) values({','.join('?' * len(row))})", list(row.values()))
        inp = {"action": "design", "experiment_id": experiment_id}
        if reason: inp["reason"] = reason
        return decide("experiment", created_by, inp, {"status": "designed", "design": fields}, model="rule",
                      confidence=1.0, status="executed", conn=c)


def exp_redesign(experiment_id, reason, agent="data_engineer", conn=None, **fields):
    """Правка дизайну, поки status='designed' (після running це блокує тригер exp_frozen). Пише decision з before/after."""
    bad = set(fields) - set(EXP_DESIGN_FIELDS)
    if bad: raise ValueError(f"поля {sorted(bad)} не є полями дизайну")
    if not fields: raise ValueError("нічого змінювати")
    c = conn or db()
    with _tx(c):
        e = _exp(c, experiment_id)
        if e["status"] != "designed":
            raise ValueError(f"{experiment_id}: status={e['status']}, дизайн змінюється лише в designed")
        before = {k: e[k] for k in fields}
        c.execute(f"update experiments set {', '.join(k + '=?' for k in fields)} where experiment_id=?",
                  [*fields.values(), experiment_id])
        return decide("experiment", agent, {"action": "redesign", "experiment_id": experiment_id, "before": before,
                                            "reason": reason}, {"after": fields}, model="rule", confidence=1.0,
                      status="executed", conn=c)


def exp_start(experiment_id, start_date, control_ids, variant_ids=(), agent="data_engineer", conn=None, note=None):
    """designed → running: фіксує experiment_items (control/variant), start_date, publications.experiment_id
    для варіанта, рядок agent_decisions(experiment). Повторний старт — ValueError. Повертає decision_id."""
    control_ids, variant_ids = list(dict.fromkeys(control_ids or [])), list(dict.fromkeys(variant_ids or []))
    if not control_ids: raise ValueError("control_ids порожній: контроль фіксується до старту")
    both = set(control_ids) & set(variant_ids)
    if both: raise ValueError(f"ролики і в control, і у variant: {sorted(both)}")
    dt.date.fromisoformat(start_date[:10])
    c = conn or db()
    with _tx(c):
        e = _exp(c, experiment_id)
        if e["status"] != "designed":
            raise ValueError(f"{experiment_id}: вже {e['status']} — повторний старт заборонено")
        if len(variant_ids) > e["sample_size"]:
            raise ValueError(f"variant {len(variant_ids)} > sample_size {e['sample_size']}")
        for arm, ids in (("control", control_ids), ("variant", variant_ids)):
            c.executemany("insert into experiment_items(experiment_id, content_id, arm) values(?,?,?)",
                          [(experiment_id, x, arm) for x in ids])
        c.execute("update experiments set status='running', start_date=? where experiment_id=?",
                  (start_date, experiment_id))
        if variant_ids:
            c.execute(f"update publications set experiment_id=? where content_id in ({','.join('?' * len(variant_ids))})",
                      [experiment_id, *variant_ids])
        inp = {"action": "start", "experiment_id": experiment_id, "design": {k: e[k] for k in EXP_DESIGN_FIELDS}}
        if note: inp["note"] = note
        return decide("experiment", agent, inp,
                      {"status": "running", "start_date": start_date, "control": control_ids, "variant": variant_ids},
                      model="rule", confidence=1.0, status="executed", conn=c)


def exp_add(experiment_id, content_id, arm="variant", agent="data_engineer", conn=None, note=None):
    """Додати ролик у running-експеримент (variant — після заливки). Дубль або перевищення sample_size — ValueError."""
    if arm not in ("variant", "control"): raise ValueError(f"arm {arm!r}")
    c = conn or db()
    with _tx(c):
        e = _exp(c, experiment_id)
        if e["status"] != "running":
            raise ValueError(f"{experiment_id}: status={e['status']}, додавати можна лише в running")
        if c.execute("select 1 from experiment_items where experiment_id=? and content_id=?",
                     (experiment_id, content_id)).fetchone():
            raise ValueError(f"{content_id} уже в {experiment_id}")
        if arm == "variant":
            n = c.execute("select count(*) from experiment_items where experiment_id=? and arm='variant'",
                          (experiment_id,)).fetchone()[0]
            if n >= e["sample_size"]: raise ValueError(f"variant уже {n} = sample_size {e['sample_size']}")
        c.execute("insert into experiment_items(experiment_id, content_id, arm) values(?,?,?)",
                  (experiment_id, content_id, arm))
        if arm == "variant":
            c.execute("update publications set experiment_id=? where content_id=?", (experiment_id, content_id))
        inp = {"action": "add", "experiment_id": experiment_id}
        if note: inp["note"] = note
        return decide("experiment", agent, inp,
                      {"content_id": content_id, "arm": arm}, model="rule", confidence=1.0, status="executed",
                      related_content_id=content_id, conn=c)


def exp_pause(experiment_id, reason, agent="coo", date=None, conn=None):
    """Закрити running-експеримент без вердикту (status decided, decision pause) — напр., дизайн суперечить фактам.
    COO 25.11: yt-related-cta v1 «заморожено» рішенням 24.11, але статус лишався running поряд з v2."""
    if not reason: raise ValueError("потрібна --reason")
    c = conn or db()
    with _tx(c):
        e = _exp(c, experiment_id)
        if e["status"] not in ("running", "collecting", "designed"):
            raise ValueError(f"{experiment_id}: status={e['status']}")
        end = date or dt.date.today().isoformat()
        did = decide("experiment", agent, {"action": "pause", "experiment_id": experiment_id, "reason": reason},
                     {"status": "decided", "decision": "pause", "end_date": end}, model="rule", confidence=1.0,
                     status="executed", conn=c)
        c.execute("update experiments set status='decided', decision='pause', end_date=?, result=?, decision_id=? "
                  "where experiment_id=?", (end, reason, did, experiment_id))
        return did


def exp_status(experiment_id, conn=None):
    c = conn or db()
    e = dict(_exp(c, experiment_id))
    items = {"control": [], "variant": []}
    for r in c.execute("select i.content_id, i.arm, p.state, p.external_id from experiment_items i left join "
                       "publications p on p.content_id=i.content_id and p.platform='youtube' "
                       "where i.experiment_id=? order by i.arm, i.content_id", (experiment_id,)):
        items[r["arm"]].append({"content_id": r["content_id"], "youtube": r["external_id"], "state": r["state"]})
    e["items"] = items
    e["decisions"] = [dict(r) for r in c.execute(
        "select seq, decision_id, agent_name, started_at, output from agent_decisions where decision_type='experiment' "
        "and json_extract(input_snapshot,'$.experiment_id')=? order by seq", (experiment_id,))]
    return e


def exp_list(conn=None):
    c = conn or db()
    return [dict(r) for r in c.execute(
        "select e.experiment_id, e.status, e.start_date, e.end_date, e.sample_size, "
        "sum(i.arm='control') control, sum(i.arm='variant') variant from experiments e "
        "left join experiment_items i using(experiment_id) group by e.experiment_id order by e.experiment_id")]


# ---------- report / stats ----------
def report(date=None, conn=None):
    c = conn or db()
    d = date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    L = [f"# Ops report {d} (UTC)"]
    runs = c.execute("select task, status, count(*) n from runs where substr(started_at,1,10)=? group by 1,2", (d,)).fetchall()
    L.append("## Запуски: " + (", ".join(f"{r['task']}:{r['status']}={r['n']}" for r in runs) or "немає"))
    dec = c.execute("select decision_type t, coalesce(policy_result,'-') p, count(*) n from agent_decisions "
                    "where substr(started_at,1,10)=? group by 1,2", (d,)).fetchall()
    L.append("## Рішення: " + (", ".join(f"{r['t']}/{r['p']}={r['n']}" for r in dec) or "немає"))
    ev = c.execute("select platform, to_state, count(*) n from pub_events where substr(ts,1,10)=? group by 1,2", (d,)).fetchall()
    L.append("## Переходи публікацій: " + (", ".join(f"{r['platform']}→{r['to_state']}={r['n']}" for r in ev) or "немає"))
    bad = c.execute("select content_id, platform, state from publications where state in ('failed','in_doubt')").fetchall()
    L.append("## Потребує уваги: " + (", ".join(f"{r['content_id']}/{r['platform']}={r['state']}" for r in bad) or "нічого"))
    errs = c.execute("select task, error from runs where substr(started_at,1,10)=? and error is not null", (d,)).fetchall()
    if errs: L.append("## Помилки: " + "; ".join(f"{r['task']}: {r['error'][:120]}" for r in errs))
    br = c.execute("select scope, state, reason from breaker where state!='closed'").fetchall()
    L.append("## Breaker: " + (", ".join(f"{r['scope']}={r['state']} ({r['reason']})" for r in br) or "усі closed"))
    ex = c.execute("select status, count(*) n from experiments group by 1").fetchall()
    L.append("## Експерименти: " + (", ".join(f"{r['status']}={r['n']}" for r in ex) or "немає"))
    v = verify(c)
    L.append(f"## Журнал: {'OK' if v['ok'] else 'РОЗРИВ — ' + '; '.join(v['errors'][:3])} "
             f"({v['decisions']} рішень, {v['events']} подій, head {v['head'][:12]})")
    return "\n".join(L)


def stats(conn=None):
    c = conn or db()
    out = {t: c.execute(f"select count(*) from {t}").fetchone()[0] for t in
           ("publications", "pub_events", "agent_decisions", "runs", "experiments", "experiment_items", "breaker")}
    out["publications_by"] = {f"{r[0]}/{r[1]}": r[2] for r in c.execute(
        "select platform, state, count(*) from publications group by 1,2 order by 1,2")}
    out["legacy"] = c.execute("select count(*) from publications where legacy=1").fetchone()[0]
    return out


# ---------- CLI ----------
def _arg_json(v):
    if v is None: return None
    if v.startswith("@"): return util.read_json(v[1:]) if v[1:] else None
    try: return json.loads(v)
    except json.JSONDecodeError: return v


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ops.py")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("verify"); sp.add_parser("backfill"); sp.add_parser("stats"); sp.add_parser("dump")
    rs = sp.add_parser("restore"); rs.add_argument("--force", action="store_true"); rs.add_argument("--from", dest="src")
    r = sp.add_parser("report"); r.add_argument("--date")
    d = sp.add_parser("decide")
    d.add_argument("--type", required=True); d.add_argument("--agent", required=True)
    d.add_argument("--input", required=True); d.add_argument("--output")
    d.add_argument("--evidence"); d.add_argument("--sources"); d.add_argument("--run")
    d.add_argument("--model"); d.add_argument("--prompt-version"); d.add_argument("--confidence", type=float)
    d.add_argument("--status", default="decided"); d.add_argument("--content"); d.add_argument("--video")
    ru = sp.add_parser("run"); ru.add_argument("action", choices=["start", "finish"]); ru.add_argument("ref")
    ru.add_argument("--agent"); ru.add_argument("--trigger"); ru.add_argument("--status", default="ok")
    ru.add_argument("--error")
    ex = sp.add_parser("exp"); ex.add_argument("action", choices=["start", "add", "status", "list", "redesign", "design", "pause"])
    ex.add_argument("id", nargs="?"); ex.add_argument("content", nargs="?")
    ex.add_argument("--date"); ex.add_argument("--control", default=""); ex.add_argument("--variant", default="")
    ex.add_argument("--arm", default="variant"); ex.add_argument("--agent", default="data_engineer")
    ex.add_argument("--reason"); ex.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE")
    a = ap.parse_args(argv)
    if a.cmd == "exp":
        out = None
        if a.action == "list": out = exp_list()
        elif not a.id: ap.error("потрібен experiment_id")
        elif a.action == "status": out = exp_status(a.id)
        elif a.action == "pause": out = {"decision_id": exp_pause(a.id, a.reason, a.agent, a.date)}
        elif a.action == "start":
            if not a.date: ap.error("exp start потребує --date YYYY-MM-DD")
            split = lambda s: [x.strip() for x in s.split(",") if x.strip()]
            out = {"decision_id": exp_start(a.id, a.date, split(a.control), split(a.variant), a.agent)}
        elif a.action == "add":
            if not a.content: ap.error("exp add ID CONTENT_ID [--arm variant|control]")
            out = {"decision_id": exp_add(a.id, a.content, a.arm, a.agent)}
        elif a.action == "redesign":
            if not a.reason or not a.set: ap.error("exp redesign ID --reason ... --set field=value")
            out = {"decision_id": exp_redesign(a.id, a.reason, a.agent, **dict(s.split("=", 1) for s in a.set))}
        elif a.action == "design":
            if not a.set: ap.error("exp design ID --agent A [--reason ...] --set field=value ...")
            f = dict(s.split("=", 1) for s in a.set)
            if "sample_size" in f: f["sample_size"] = int(f["sample_size"])
            if "max_share" in f: f["max_share"] = float(f["max_share"])
            out = {"decision_id": exp_design(a.id, a.agent, a.reason, **f)}
        print(json.dumps(out, ensure_ascii=False, indent=1)); return 0
    if a.cmd == "verify":
        v = verify(); print(json.dumps(v, ensure_ascii=False, indent=1)); return 0 if v["ok"] else 1
    if a.cmd == "dump":
        print(dump()); return 0
    if a.cmd == "restore":
        v = restore(a.src, force=a.force); print(json.dumps(v, ensure_ascii=False, indent=1)); return 0 if v["ok"] else 1
    if a.cmd == "backfill":
        print(json.dumps(backfill(), ensure_ascii=False)); return 0
    if a.cmd == "stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=1)); return 0
    if a.cmd == "report":
        print(report(a.date)); return 0
    if a.cmd == "decide":
        print(decide(a.type, a.agent, _arg_json(a.input), _arg_json(a.output), run_id=a.run, model=a.model,
                     prompt_version=a.prompt_version, evidence_ids=_arg_json(a.evidence),
                     source_urls=_arg_json(a.sources), confidence=a.confidence, status=a.status,
                     related_content_id=a.content, related_video_id=a.video)); return 0
    if a.cmd == "run":
        if a.action == "start": print(run_start(a.ref, a.agent, a.trigger))
        else: run_finish(a.ref, a.status, a.error)
        return 0


if __name__ == "__main__":
    sys.exit(main())
