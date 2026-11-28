#!/usr/bin/env python3
"""Дошка ідей редколегії (власник 22.11: «ресерчери знаходять топ ідеї… узгоджувати, рейтингувати і приймати рішення, що піде і куди»).

Файл: studio/data/ideas.json — список ідей. Кожна ідея:
  id, title, source (URL першоджерела або «kw.py»/«outliers»), added, by (хто додав: researcher-news|researcher-search|researcher-niche|owner),
  format (tier|prof|free|sec|news|skills|try|check|digest|guide), channels [short, long, site, tg, tiktok, insta],
  demand 1–5 (пошуковий попит: kw.py / Search Console), fresh 1–5 (свіжість), show 1–5 («можна показати»), fit 1–5 (для кого: люди/бізнес/ІТ),
  опційно: hook (release|niche|you|plain — тип хука; без поля — детектор за заголовком), length (план, секунди Short; без поля — множник 1),
  status (new|approved|in_work|done|rejected), decision (коментар редколегії), video_id / url (коли вийшло),
  prior_at_publish / score_at_publish (пишеться автоматично при set video_id=… або status=done — для аудиту прогнозів).
Бал = demand × fresh × show × fit × prior(format) × hook × length (аудит docs/research/forecast-audit-2026-11-22.md):
  prior — зважена медіана переглядів Short за 7 днів лише по роликах із закритим 7-денним вікном, вага 0.5^(вік/14 дн),
  шкала ln(1+медіана)/ln(1+200); prof і tier розведені за заголовком; hook: реліз/бета/нішевий бренд ×0.6, «твоє» + дія ×1.3;
  length: ≤35 с ×1.0, 35–45 ×0.6, >45 ×0.5. На дошці поруч — P25–P75 формату (діапазон, а не точка).

usage:
  python3 studio/yt/ideas.py add '{"title":"...","format":"tier","channels":["short","site"],"demand":4,"fresh":3,"show":5,"fit":5,"source":"...","length":30}'
  python3 studio/yt/ideas.py board [N]        # рейтинг відкритих ідей + кандидати на рімейк
  python3 studio/yt/ideas.py set <id> status=approved decision="..."
  python3 studio/yt/ideas.py link <id> <video_id> [--at 2026-11-24T17:00:00Z] [--dur <с>]   # при заливці/виході: фіксує прогноз (prior, бал, P25–P75) у момент виходу
                                                                              # (finalize.py --idea <id> робить це сам; аудит 23.11: 0 з 74 ідей були прив'язані)
  python3 studio/yt/ideas.py forecast <video_id> '{"title":"...","format":"tier","length":30}' [--at ...] [--dur <с>]
                                                                              # ролик БЕЗ ідеї на дошці → studio/data/forecasts.json (CSO 28.11,
                                                                              # аудит прогнозів 28.11 п. 5: 4 з 4 роликів 20–22.11 без прогнозу)
Прогноз Short — двома числами (CSO 28.11, аудит 28.11 п. 2): p_zero_feed — ймовірність «нуля стрічки» (RUNBOOK «НУЛЬ СТРІЧКИ»),
  і P25–медіана–P75 формату за умови показу. На бал (рейтинг) p_zero не впливає: він однаковий для всіх Shorts.
  p_zero_feed — лише для Shorts: фактична тривалість ≤180 с (--dur / videos.duration_s); довге відео формату sec/tier (шоу) його не отримує.
"""
import sys, os, re, json, sqlite3, datetime, statistics, math
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
F = os.path.join(D, "ideas.json"); DB = os.path.join(D, "analytics.sqlite")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")); from util import read_json, write_json_atomic, update_json, locked

HALF_LIFE = 14      # днів: вага 0.5^(вік/14)
REF = 200           # 7-денні перегляди, що дають prior = 1 (ln-шкала)
MANUAL = {"guide": 0.6, "digest": 0.74}  # довгі формати: даних Shorts немає. digest 0.74 = ln(51)/ln(201), медіана 4 випусків 11/48/51/101
                                          # за 7 днів (CSO 28.11, аудит прогнозів 28.11 п. 3; було 0.5 ≈ 13 переглядів)
LONG = set(MANUAL)                        # довгі: «нуль стрічки» Shorts до них не застосовний
P_ZERO = 0.35                             # P(нуль стрічки) Short: 3 з 8 за 15–22.11 (аудит 28.11 п. 2); переглядати на бектесті 01.12
FC = os.path.join(D, "forecasts.json")    # прогнози роликів без ідеї: {video_id: forecast}
SHORT_MAX = 180                           # с: Short — ≤180 с (28.11: шоу #3 S_6k_2vDGTM 13:30 формату sec отримало p_zero_feed)


def load(): return read_json(F, [])
def save(x): write_json_atomic(F, x)


def fmt_of(f, title):
    """Формат за суттю: серія «ШІ для <професія>» → prof, «Тір-лист» / «який ШІ для» → tier (у videos є помилки розмітки)."""
    t = (title or "").lower()
    if "ші для професій" in t or t.startswith("ші для "): return "prof"
    if "тір-лист" in t or "який ші для" in t: return "tier"
    if f == "prof": return "news"     # «ChatGPT у Chrome» записано як prof
    return f


def _wq(xs, q):
    """Зважений квантиль: xs = [(значення, вага)]."""
    xs = sorted(xs); tot = sum(w for _, w in xs); acc = 0
    for v, w in xs:
        acc += w
        if acc >= q * tot: return v
    return xs[-1][0]


def _db():
    try:
        import analytics_db; return analytics_db.db()
    except Exception:
        c = sqlite3.connect(DB); c.execute("pragma busy_timeout=10000"); return c


def stats(today=None):
    """{format: dict(n, med, p25, p75)} — зважені за свіжістю, лише ролики із закритим 7-денним вікном."""
    if not os.path.exists(DB): return {}
    c = _db(); today = today or datetime.date.today()
    last = c.execute("select max(date) from daily").fetchone()[0]
    if not last: return {}
    last = datetime.date.fromisoformat(last[:10]); by = {}
    for vid, f, pub, title in c.execute("select id, format, published, title from videos where short=1"):
        p = datetime.date.fromisoformat(pub[:10]); end = p + datetime.timedelta(days=6)
        if end > last or end >= today: continue          # вікно не закрите — не знаємо факту
        v = c.execute("select sum(views) from daily where video_id=? and date between ? and ?", (vid, p.isoformat(), end.isoformat())).fetchone()[0] or 0
        by.setdefault(fmt_of(f, title), []).append((v, 0.5 ** ((today - p).days / HALF_LIFE)))
    return {k: dict(n=len(x), med=_wq(x, .5), p25=_wq(x, .25), p75=_wq(x, .75)) for k, x in by.items() if len(x) >= 3}


def _lg(v): return math.log1p(v) / math.log1p(REF)


def priors(S=None):
    """prior формату = ln(1+зважена медіана)/ln(1+200), без нормування до максимуму і без нижньої межі."""
    S = stats() if S is None else S
    p = {k: round(_lg(s["med"]), 3) for k, s in S.items()}
    for k, v in MANUAL.items(): p.setdefault(k, v)
    return p


RELEASE = re.compile(r"\d+\.\d+|\b[A-Za-z]+[- ]\d+\b|\bбета\b|\bbeta\b|\(бета\)|вийшов|вийшла|реліз", re.I)
YOU = re.compile(r"\b(тв(ій|оя|ою|ої|оє|оїй|оєї|оєму|оїх|оїм|оїми|оєю|ого|оєму|оїй)|тебе|тобі)\b", re.I)
ACTION = re.compile(r"як (вимкнути|стерти|увімкнути|перевірити|захистити|видалити)|перевір|за \d+ (с|секунд)", re.I)


def hook_mult(i):
    h = i.get("hook")
    if h in ("release", "niche"): return 0.6
    if h == "you": return 1.3
    if h == "plain": return 1.0
    t = i.get("title", "")
    if RELEASE.search(t): return 0.6
    if YOU.search(t) and ACTION.search(t): return 1.3
    return 1.0


def length_mult(i):
    L = i.get("length")
    try: L = float(L)
    except (TypeError, ValueError): return 1.0
    return 1.0 if L <= 35 else 0.85 if L <= 45 else 0.8   # аудит 22.11: старі 0.6/0.5 занижували прогноз ×2.3


def score(i, P):
    f = i.get("format", "news")
    pr = P.get(f, P.get("news", 0.3))
    return round(i.get("demand", 1) * i.get("fresh", 1) * i.get("show", 1) * i.get("fit", 1) * pr * hook_mult(i) * length_mult(i), 1)


def remakes(n=5):
    """Контроль якості (не множник): ≥65 % перегляду при <30 переглядах за 7 днів — зміст добрий, хук слабкий → новий хук, нова ідея."""
    if not os.path.exists(DB): return []
    c = _db(); last = c.execute("select max(date) from daily").fetchone()[0]; out = []
    for vid, pub, title in c.execute("select id, published, title from videos where short=1"):
        end = (datetime.date.fromisoformat(pub[:10]) + datetime.timedelta(days=6)).isoformat()
        if not last or end > last: continue
        v, pct = c.execute("select sum(views), sum(views*avg_pct)/max(sum(views),1) from daily where video_id=? and date between ? and ?", (vid, pub[:10], end)).fetchone()
        if (v or 0) < 30 and 65 <= (pct or 0) <= 100: out.append((pub[:10], vid, v or 0, round(pct), title.replace(" #ШІ #shorts", "")))
    return sorted(out, reverse=True)[:n]


def _dur(v):
    try: v = int(float(v))
    except (TypeError, ValueError): return None
    return v if v > 0 else None


def is_short(i, dur=None):
    """Short = фактична тривалість ≤180 с; без тривалості — явне i["short"], інакше формат (не довгий = Short).
    Формат sec/tier/… буває і в шоу (довге відео), тож фактична тривалість важливіша за формат і за плановий length."""
    if i.get("format", "news") in LONG: return False
    d = _dur(dur) or _dur(i.get("dur_s"))
    if d is not None: return d <= SHORT_MAX
    if i.get("short") is not None: return bool(i["short"]) and i["short"] not in ("0", "false", "False")
    return True


def video_dur(vid):
    """Тривалість ролика з даталейку (videos.duration_s) або None."""
    if not vid or not os.path.exists(DB): return None
    try: r = _db().execute("select duration_s from videos where id=?", (vid,)).fetchone()
    except Exception: return None
    return _dur(r[0]) if r else None


def forecast(i, S, P, at=None, dur=None):
    """Прогноз у момент виходу: P25–медіана–P75 формату (за умови показу), множники і p_zero_feed (лише Shorts: ≤180 с)."""
    f = i.get("format", "news"); st = S.get(f) or {}
    out = {"at": at or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "format": f,
           "p25": st.get("p25"), "med": st.get("med"), "p75": st.get("p75"), "n": st.get("n"),
           "hook_mult": hook_mult(i), "length_mult": length_mult(i)}
    d = _dur(dur) or _dur(i.get("dur_s"))
    if d is not None: out["dur_s"] = d
    if is_short(i, d): out["p_zero_feed"] = P_ZERO
    return out


def record(vid, i, at=None, path=None, dur=None):
    """Записати прогноз ролика без ідеї в forecasts.json (один раз; повторний виклик не переписує). Повертає запис."""
    path = path or FC; S = stats(); P = priors(S)
    with locked(path):
        x = read_json(path, {})
        if vid not in x:
            f = i.get("format", "news")
            x[vid] = dict(title=i.get("title"), length=i.get("length"), prior=round(P.get(f, P.get("news", 0.3)), 3),
                          **forecast(i, S, P, at, dur or video_dur(vid)))
            write_json_atomic(path, x)
    return x[vid]


def link(idea_id, vid, at=None, dur=None):
    """Прив'язати ролик до ідеї й записати прогноз станом на зараз (один раз; повторний виклик прогноз не переписує)."""
    S = stats(); P = priors(S); dur = _dur(dur) or video_dur(vid)
    with locked(F):
        x = load(); hit = None
        for i in x:
            if i["id"] == str(idea_id):
                hit = i; i["video_id"] = vid
                if at: i["published_at"] = at
                if i.get("status") in ("new", "approved", "in_work", None): i["status"] = "done"
                if "prior_at_publish" not in i:
                    f = i.get("format", "news")
                    i["prior_at_publish"] = round(P.get(f, P.get("news", 0.3)), 3); i["score_at_publish"] = score(i, P)
                    i["forecast_at_publish"] = forecast(i, S, P, dur=dur)
        if hit is None: sys.exit(f"ідеї {idea_id} немає")
        save(x)
    print("linked", idea_id, vid, hit.get("score_at_publish"), hit.get("forecast_at_publish"))


def board(n=15):
    S = stats(); P = priors(S); xs = [i for i in load() if i.get("status", "new") in ("new", "approved")]
    for i in xs: i["score"] = score(i, P)
    xs.sort(key=lambda i: -i["score"])
    print("prior:", {k: round(v, 2) for k, v in sorted(P.items(), key=lambda x: -x[1])})
    print(f"Shorts: P(нуль стрічки) ≈ {P_ZERO}; діапазони нижче — за умови показу")
    print("7 дн, P25–медіана–P75 (n):", {k: f"{s['p25']}–{s['med']}–{s['p75']} ({s['n']})" for k, s in sorted(S.items(), key=lambda x: -x[1]['med'])})
    for i in xs[:n]:
        s = S.get(i.get("format", "")); rng = f"{s['p25']}–{s['p75']}" if s else "—"
        print(f"{i['score']:6.1f} [{i['status']:8}] {i['id']:>3} {i.get('format',''):6} {rng:>9} {','.join(i.get('channels',[])):18} {i['title'][:80]}")
    r = remakes()
    if r:
        print("кандидати на рімейк (≥65 % перегляду, <30 переглядів):")
        for d, vid, v, pct, t in r: print(f"  {d} {vid} {v:>3} перегл. {pct}%  {t[:70]}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["board"]
    if a[0] == "add":
        with locked(F):
            x = load(); i = json.loads(a[1]); i.setdefault("status", "new"); i.setdefault("added", datetime.date.today().isoformat())
            i["id"] = str(max([int(j["id"]) for j in x] or [0]) + 1); x.append(i); save(x); print("added", i["id"])
    elif a[0] == "set":
        with locked(F):
            x = load(); P = None
            for i in x:
                if i["id"] == a[1]:
                    for kv in a[2:]:
                        k, v = kv.split("=", 1); i[k] = v
                    if "prior_at_publish" not in i and (i.get("video_id") or i.get("url") or i.get("status") == "done"):
                        P = P or priors(); i["prior_at_publish"] = P.get(i.get("format", "news"), P.get("news", 0.3)); i["score_at_publish"] = score(i, P)
            save(x); print("ok")
    elif a[0] == "link":
        link(a[1], a[2], a[a.index("--at") + 1] if "--at" in a else None, a[a.index("--dur") + 1] if "--dur" in a else None)
    elif a[0] == "forecast":
        print("forecast", a[1], record(a[1], json.loads(a[2]), a[a.index("--at") + 1] if "--at" in a else None,
                                       dur=a[a.index("--dur") + 1] if "--dur" in a else None))
    else:
        board(int(a[1]) if len(a) > 1 else 15)
