#!/usr/bin/env python3
"""Хук Claude Code → пульт. Читає подію зі stdin, відправляє короткий опис (без секретів) у фоні й одразу виходить.
Підключено в .claude/settings.json. Без studio/pult/.token нічого не робить."""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import pultlib as P
import human as H


def describe(ev):
    """→ (kind, area, текст простими словами, технічні деталі, ok)"""
    name = ev.get("hook_event_name", "")
    tool = ev.get("tool_name", "") or ""
    ti = ev.get("tool_input") or {}
    if name == "UserPromptSubmit":
        return "prompt", "pult", "Ти написав: " + P.redact(ev.get("prompt", ""), 140), "", True
    if name == "SessionStart":
        return "session", "pult", "Почав роботу", "", True
    if name == "Stop":
        return "stop", "pult", "Закінчив етап — чекаю наступного запуску або твого повідомлення", "", True
    if name == "Notification":
        return "wait", "pult", "Чекаю: " + P.redact(ev.get("message", "потрібна увага"), 120), "", True
    if name in ("SubagentStart", "SubagentStop"):
        return "agent", "other", ("Помічник узявся за частину роботи" if name == "SubagentStart" else "Помічник закінчив свою частину"), "", True
    ok = name != "PostToolUseFailure"
    text, area = H.human(tool, ti)
    if tool == "Bash":
        detail = "$ " + ti.get("command", "")
    elif tool in ("Write", "Edit", "Read", "NotebookEdit"):
        detail = ti.get("file_path", "")
    elif tool == "WebFetch":
        detail = ti.get("url", "")
    else:
        detail = tool.split("__")[-1] + " " + json.dumps(ti, ensure_ascii=False)
    area = area or P.area_of(tool, detail)
    if not ok:
        text = "Не вийшло: " + text[:1].lower() + text[1:] + " — розбираюсь"
        detail += " → " + str(ev.get("error", ""))
    return "tool", area, P.redact(text, 160), P.redact(detail, 300), ok


def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return
    if not P.token():
        return
    kind, area, text, detail, ok = describe(ev)
    data = {"ts": int(time.time() * 1000), "sid": ev.get("session_id", "")[-12:], "kind": kind,
            "tool": (ev.get("tool_name") or "").split("__")[-1], "area": area, "text": text, "detail": detail, "ok": ok}
    if os.fork():  # батько виходить одразу — Claude не чекає мережу
        return
    try:
        os.setsid()
        P.send("/api/ingest", data)
    except Exception:
        pass
    os._exit(0)


if __name__ == "__main__":
    main()
