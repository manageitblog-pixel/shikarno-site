#!/usr/bin/env python3
"""Журнал реальної роботи агентів для студії HQ (власник 22.11: «чому такі великі перерви між задачами?» — дашборд має показувати, хто працює зараз).
studio/hq/activity.json: {"items":[{id, agent, task, started, finished|null, result}]}
usage:
  python3 studio/yt/activity.py start <agent_id> "<задача>"        → друкує id
  python3 studio/yt/activity.py done <id> "<результат>"
  python3 studio/yt/activity.py list
agent_id — з AGENTS у studio/yt/hq_data.py (shorts, longs, factcheck, qa, lp, post, clip, designer, trend, de, da, seo, cm, dist, coo, cso, eic, ea).
"""
import sys, os, json, datetime
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hq", "activity.json")


def load():
    try: return json.load(open(F))
    except Exception: return {"items": []}


def save(d):
    d["items"] = d["items"][-200:]
    json.dump(d, open(F, "w"), ensure_ascii=False, indent=1)


def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    a = sys.argv[1:]; d = load()
    if a and a[0] == "start":
        i = str(int(max([int(x["id"]) for x in d["items"]] or [0])) + 1)
        d["items"].append(dict(id=i, agent=a[1], task=a[2], started=now(), finished=None, result="")); save(d); print(i)
    elif a and a[0] == "done":
        for x in d["items"]:
            if x["id"] == a[1]: x["finished"] = now(); x["result"] = a[2] if len(a) > 2 else ""
        save(d); print("ok")
    else:
        for x in d["items"][-20:]: print(x["id"], x["agent"], "✓" if x["finished"] else "…", x["task"][:70])
