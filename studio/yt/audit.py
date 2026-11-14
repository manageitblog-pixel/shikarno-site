#!/usr/bin/env python3
"""Аудит упаковки ВСІХ публічних і запланованих відео за правилами каналу (власник 14.11: «перевіряй все і пофікси пайплайн»).

Правила (джерела: docs/RUNBOOK.md «ХЕШТЕГИ З 5.11», «КЛЮЧОВІ СЛОВА 9.11», docs/shorts-checklist.md п.17–21,
docs/research/hashtags-2026-11-01.md, docs/research/vidiq-tags-2026-11-09.md):
  SHORTS  T1 назва закінчується «#ШІ #shorts»        D1 останній рядок опису «#shorts #штучнийінтелект #ші #<інструмент>», інших рядків-хештегів нема
  ДОВГІ   T1 у назві без хештегів                      D1 останній рядок «#штучнийінтелект #ші #<інструменти>», без #shorts
  УСІ     D2 перший рядок опису — текст (не хештег/не порожній)   G1 5–15 тегів  G2 без російських  G3 ≥1 англ. тег
          G4 тег з назвою інструмента з назви ролика   P1 є хоча б в одному плейлисті   C1 є коментар каналу
usage: python3 studio/yt/audit.py           # звіт → studio/yt/audit_report.json + друк
       python3 studio/yt/audit.py --fix     # виправити механічні (хештеги, англ. теги, рос. теги, плейлисти)
Назви й тексти описів НЕ переписує — лише хвіст-хештеги й теги.
"""
import sys, os, re, json, urllib.request
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, os.path.dirname(__file__))
import yt

TOOLS = [  # (ознака в назві, хештег, англ. теги)
    ("chatgpt", "#chatgpt", ["chatgpt", "openai"]), ("openai", "#chatgpt", ["openai"]), ("codex", "#chatgpt", ["openai codex"]),
    ("gemini", "#gemini", ["google gemini", "gemini ai"]), ("google", "#gemini", ["google ai"]),
    ("claude", "#claude", ["claude ai", "anthropic claude"]), ("anthropic", "#claude", ["anthropic"]),
    ("copilot", "#copilot", ["microsoft copilot"]), ("meta", "#metaai", ["meta ai"]), ("grok", "#grok", ["grok ai"]),
    ("deepseek", "#deepseek", ["deepseek"]), ("сяйво", "#сяйво", ["ukrainian llm"]), ("київстар", "#сяйво", ["kyivstar ai"]),
    ("mcp", "#claude", ["mcp server"]), ("nvidia", "#nvidia", ["nvidia ai"]), ("шахра", "#шахраї", ["ai scam"]),
    ("дипфейк", "#дипфейк", ["deepfake"]),
]
RU_CH = re.compile(r"[ыэъё]", re.I)
RU_WORDS = {"нейросеть", "нейросети", "искусственный", "интеллект", "бесплатно", "как", "что", "чат"}
PL = {"news": "PLTBOXlyURN0g", "sec": "PLK19K_iOB7fU", "skills": "PLDoCjFWXo6eI", "prof": "PLUNuDFNf9LVc", "tier": "PLbWfeHw_IhwY",
      "check": "PLY2sr8xgYaG4", "digest": "PLb2dDm0ckIWk", "try": "PLJmaWDPrufYo", "free": "PLHQnxB4mtNbM"}
PL_RULES = [  # перше збігання по назві → плейлист
    (r"тір|tier", "tier"), (r"шахра|scam|безпек|дірк|приватн|знає про тебе|пам.ят|wallet|злам", "sec"),
    (r"скіл|skill|mcp|конектор", "skills"), (r"професі|вчител|лікар|юрист|водій|hr|smm", "prof"),
    (r"за тиждень|за місяць|дайджест|жовтень|листопад", "digest"), (r"безкоштовн|free", "free"),
    (r"пробує|спробував|тест", "try"), (r"перевір", "check"), (r".", "news"),
]
REPORT = os.path.join(os.path.dirname(__file__), "audit_report.json")


def iso_sec(d):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d)
    dd, h, mi, s = [int(x or 0) for x in m.groups()]
    return dd * 86400 + h * 3600 + mi * 60 + s


def videos():
    up = yt.api("channels", part="contentDetails", mine="true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        q = dict(part="contentDetails", playlistId=up, maxResults=50)
        if tok: q["pageToken"] = tok
        r = yt.api("playlistItems", **q); ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok: break
    out = []
    for k in range(0, len(ids), 50):
        for v in yt.api("videos", part="snippet,status,contentDetails", id=",".join(ids[k:k + 50]))["items"]:
            st = v["status"]; t = v["snippet"]["title"]
            if st["privacyStatus"] == "public" or st.get("publishAt"):
                if not re.search(r"ТЕСТ|ПРИКЛАД|не публік", t, re.I):
                    out.append(v)
    return out


def playlist_map():
    m = {}
    for key, pl in PL.items():
        tok = None
        while True:
            q = dict(part="contentDetails", playlistId=pl, maxResults=50)
            if tok: q["pageToken"] = tok
            r = yt.api("playlistItems", **q)
            for i in r["items"]: m.setdefault(i["contentDetails"]["videoId"], []).append(key)
            tok = r.get("nextPageToken")
            if not tok: break
    return m


def channel_commented(vid, me):
    try:
        r = yt.api("commentThreads", part="snippet", videoId=vid, maxResults=20)
        return any(c["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value") == me for c in r["items"])
    except Exception:
        return None  # коментарі вимкнені / ще не опубліковано


def tools_in(title):
    t = title.lower(); return [x for x in TOOLS if x[0] in t]


def check(v, pls, me):
    sn = v["snippet"]; title = sn["title"]; desc = sn.get("description", ""); tags = sn.get("tags", [])
    short = iso_sec(v["contentDetails"]["duration"]) <= 180
    lines = [l for l in desc.strip().split("\n")]
    last = lines[-1].strip() if lines else ""
    issues = []
    tl = tools_in(title)
    if short:
        if not title.rstrip().endswith("#ШІ #shorts"): issues.append("T1")
        if not last.startswith("#shorts #штучнийінтелект #ші"): issues.append("D1")
    else:
        if re.search(r"#[^\s\d]", title): issues.append("T1")
        if not last.startswith("#штучнийінтелект #ші") or "#shorts" in last: issues.append("D1")
    hash_lines = [l for l in lines[:-1] if l.strip().startswith("#")]
    if hash_lines: issues.append("D1x")
    first = next((l for l in lines if l.strip()), "")
    if not first or first.strip().startswith("#"): issues.append("D2")
    if len(tags) < 5 or sum(len(t) + 3 for t in tags) > 480: issues.append("G1")
    low = [t.lower() for t in tags]
    if "ші" not in low or "штучний інтелект" not in low: issues.append("G5")
    if any(RU_CH.search(t) or t.lower() in RU_WORDS for t in tags): issues.append("G2")
    if not any(re.fullmatch(r"[A-Za-z0-9 .\-+]+", t) for t in tags): issues.append("G3")
    if tl and not any(x[0] in " ".join(tags).lower() for x in tl): issues.append("G4")
    if any(t.startswith("#") for t in tags): issues.append("G6")
    if not pls.get(v["id"]): issues.append("P1")
    if v["status"]["privacyStatus"] == "public":
        c = channel_commented(v["id"], me)
        if c is False: issues.append("C1")
    return dict(id=v["id"], title=title, short=short, issues=issues, tags=len(tags), status=v["status"]["privacyStatus"])


def fix(v, r):
    sn = v["snippet"]; title = sn["title"]; desc = sn.get("description", "").rstrip(); tags = list(sn.get("tags", []))
    tl = tools_in(title)
    hs = []
    for x in tl:
        if x[1] not in hs: hs.append(x[1])
    lines = desc.split("\n")
    # прибрати всі рядки-хештеги (і останній), потім додати один стандартний
    body = [l for l in lines if not l.strip().startswith("#")]
    while body and not body[-1].strip(): body.pop()
    if r["short"]:
        tail = "#shorts #штучнийінтелект #ші" + ("" if not hs else " " + hs[0])
        if not title.rstrip().endswith("#ШІ #shorts"):
            t = re.sub(r"(\s*#[^\s\d]\S*)+\s*$", "", title).rstrip()
            title = (t + " #ШІ #shorts") if len(t) <= 88 else title
    else:
        tail = "#штучнийінтелект #ші" + ("" if not hs else " " + " ".join(hs[:3]))
        title = re.sub(r"\s*#[^\s\d]\S*", "", title).strip()
    new_desc = "\n".join(body) + "\n\n" + tail
    tags = [t for t in tags if not (RU_CH.search(t) or t.lower() in RU_WORDS)]
    tags = list(dict.fromkeys(t.lstrip("#").strip() for t in tags if t.lstrip("#").strip()))
    en = []
    for x in tl:
        for e in x[2]:
            if e not in [t.lower() for t in tags] and e not in en: en.append(e)
    if not any(re.fullmatch(r"[A-Za-z0-9 .\-+]+", t) for t in tags) and not en: en = ["ai news ukrainian"]
    for x in tl:
        if x[0] not in " ".join(tags).lower() and x[0].isascii(): tags.insert(0, x[0].capitalize())
    tags = tags + en[:3]
    for must in ["штучний інтелект", "ШІ"]:
        if must.lower() not in [t.lower() for t in tags]: tags.insert(0, must)
    if "ШІкарно" in tags: tags.remove("ШІкарно")
    tags = tags + ["ШІкарно"]
    while sum(len(t) + 3 for t in tags) > 480 and len(tags) > 8: tags.pop(-2)
    body_json = {"id": v["id"], "snippet": {"title": title, "description": new_desc, "tags": tags, "categoryId": sn["categoryId"],
                 **{k: sn[k] for k in ("defaultLanguage", "defaultAudioLanguage") if k in sn}}}
    changed = (title != sn["title"]) or (new_desc != sn.get("description", "")) or (tags != sn.get("tags", []))
    if changed: yt._put("videos", body_json, "snippet")
    if "P1" in r["issues"]:
        key = next(k for pat, k in PL_RULES if re.search(pat, title, re.I))
        yt.add_to_playlist(v["id"], key)
    return changed


if __name__ == "__main__":
    me = yt.api("channels", part="id", mine="true")["items"][0]["id"]
    vs = videos(); pls = playlist_map()
    res = [check(v, pls, me) for v in vs]
    bad = [r for r in res if r["issues"]]
    from collections import Counter
    cnt = Counter(i for r in res for i in r["issues"])
    print(f"відео: {len(res)}, з проблемами: {len(bad)}; {dict(cnt)}")
    for r in bad: print(("S " if r["short"] else "L ") + r["id"], ",".join(r["issues"]), "|", r["title"][:70])
    json.dump(res, open(REPORT, "w"), ensure_ascii=False, indent=1)
    if "--fix" in sys.argv:
        byid = {v["id"]: v for v in vs}; n = 0
        for r in bad:
            if set(r["issues"]) - {"C1"}:
                try:
                    if fix(byid[r["id"]], r): n += 1
                except Exception as e: print("ERR", r["id"], e)
        print("виправлено відео:", n)
