#!/usr/bin/env python3
"""Вирівнювання тегів усіх публічних відео (власник 9.11: «треба вирівняти теги усі»).

Прибирає загальні шаблонні теги, лишає тематичні й додає 2–4 фрази з підказок пошуку YouTube (UA/uk)
під тему конкретного ролика. Назви й описи не чіпає. ШІкарно лишається одним брендовим тегом у кінці.
usage: python3 studio/yt/retag.py            # план без запису → studio/yt/retag_plan.json
       python3 studio/yt/retag.py --apply    # записати (videos.update, 50 од. квоти на відео)
"""
import sys, json, os
sys.path.insert(0, "/home/claude/yt"); sys.path.insert(0, os.path.dirname(__file__))
import yt
from kw import suggest, RU

GENERIC = {"ші", "шікарно", "штучний інтелект", "ai новини", "ai", "нейромережі", "нейромережа", "ші новини",
           "новини ші", "штучний інтелект українською", "ai news", "ші українською"}
PLAN = os.path.join(os.path.dirname(__file__), "retag_plan.json")


def all_public():
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
        for v in yt.api("videos", part="snippet,status", id=",".join(ids[k:k + 50]))["items"]:
            if v["status"]["privacyStatus"] == "public":
                out.append(v)
    return out


STOP = {"тепер", "через", "якщо", "чому", "який", "яка", "які", "твою", "твої", "твоїм", "щоб", "shorts", "для", "або", "без", "байта"}


def words(text):
    import re
    return {w for w in re.findall(r"[\w'’-]{4,}", text.lower()) if w not in STOP}


def new_tags(tags, title):
    spec = [t for t in tags if t.lower() not in GENERIC]
    have = {t.lower() for t in spec}
    tw = words(title)
    add = []
    for seed in spec:
        sw = words(seed)
        for s in suggest(seed.lower() + " "):
            sl = s.lower()
            if RU.search(s) or sl in have:
                continue
            extra = words(s) - sw          # нові слова підказки мають бути з назви ролика
            if not extra or not (extra & tw):
                continue
            add.append(s); have.add(sl)
        if len(add) >= 4: break
    res = spec + add[:4] + ["ШІкарно"]
    while sum(len(t) + (2 if " " in t else 0) + 1 for t in res) > 480:  # ліміт YouTube 500 знаків
        res.pop(-2)
    return res


def main():
    apply = "--apply" in sys.argv
    if apply:
        plan = json.load(open(PLAN))
        done = 0
        for vid, p in plan.items():
            v = yt.api("videos", part="snippet", id=vid)["items"][0]["snippet"]
            body = {"id": vid, "snippet": {k: v[k] for k in ("title", "description", "categoryId") if k in v}}
            for k in ("defaultLanguage", "defaultAudioLanguage"):
                if k in v: body["snippet"][k] = v[k]
            body["snippet"]["tags"] = p["new"]
            try:
                yt._put("videos", body, "snippet"); done += 1
            except Exception as e:
                print("ERR", vid, e); break
        print("updated", done, "of", len(plan)); return
    plan = {}
    for v in all_public():
        old = v["snippet"].get("tags", [])
        plan[v["id"]] = {"title": v["snippet"]["title"], "old": old, "new": new_tags(old, v["snippet"]["title"])}
    json.dump(plan, open(PLAN, "w"), ensure_ascii=False, indent=1)
    print("plan:", len(plan), "→", PLAN)


if __name__ == "__main__":
    main()
