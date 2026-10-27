#!/usr/bin/env python3
"""CLI пульта.
  python3 pult.py note "Short заплановано на 19:00" youtube   — віха в журнал (напрямок необов'язковий)
  python3 pult.py state '{"headline": "...", "next_run": "2026-10-28T07:10:00Z", "metrics": {...}, "tasks": [...]}'
  python3 pult.py state-file path.json
Поля state: headline, next_run (ISO), metrics {yt_subs, tg_subs, reserve, gemini_left}, tasks [{title, area, status, note, due}],
questions [{text, status}], today [{time, title, area, status}] — дашборд показує все, що є.
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import pultlib as P


def note(text, area=None):
    return P.send("/api/ingest", {"ts": int(time.time() * 1000), "kind": "note", "area": area or P.area_of(text),
                                  "text": P.redact(text, 300), "ok": True})


def state(patch):
    return P.send("/api/state", patch)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] == "note":
        print(note(a[1], a[2] if len(a) > 2 else None))
    elif a[0] == "state":
        print(state(json.loads(a[1])))
    elif a[0] == "state-file":
        print(state(json.load(open(a[1]))))
