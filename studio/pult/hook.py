#!/usr/bin/env python3
"""Хук Claude Code → пульт. Читає подію зі stdin, відправляє короткий опис (без секретів) у фоні й одразу виходить.
Підключено в .claude/settings.json. Без studio/pult/.token нічого не робить."""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import pultlib as P


def describe(ev):
    name = ev.get("hook_event_name", "")
    tool = ev.get("tool_name", "") or ""
    ti = ev.get("tool_input") or {}
    if name == "UserPromptSubmit":
        return "prompt", "", "pult", "Людина: " + P.redact(ev.get("prompt", ""), 140), True
    if name == "SessionStart":
        return "session", "", "pult", "Сесія стартувала (" + str(ev.get("source", "")) + ")", True
    if name == "Stop":
        return "stop", "", "pult", "Хід завершено — чекаю", True
    if name == "Notification":
        return "wait", "", "pult", P.redact(ev.get("message", "Потрібна увага"), 140), True
    if name in ("SubagentStart", "SubagentStop"):
        what = "Субагент стартував" if name == "SubagentStart" else "Субагент закінчив"
        return "agent", ev.get("agent_type", "") or "", "other", what + " " + P.redact(ev.get("agent_type", ""), 40), True
    # інструменти
    ok = name != "PostToolUseFailure"
    if tool == "Bash":
        cmd = ti.get("command", "")
        text = (ti.get("description") or "") + (" · " if ti.get("description") else "") + "$ " + cmd
        area = P.area_of(cmd)
    elif tool in ("Write", "Edit", "Read", "NotebookEdit"):
        path = ti.get("file_path", "")
        rel = path.replace(os.environ.get("CLAUDE_PROJECT_DIR", "/home/user/shikarno-site") + "/", "")
        verb = {"Write": "Створює", "Edit": "Редагує", "Read": "Читає"}.get(tool, tool)
        text, area = f"{verb} {rel}", P.area_of(path)
    elif tool in ("WebSearch", "WebFetch"):
        text = ("Шукає: " + ti.get("query", "")) if tool == "WebSearch" else ("Читає " + ti.get("url", ""))
        area = "research"
    elif tool == "Grep" or tool == "Glob":
        text, area = f"{tool} {ti.get('pattern', '')}", P.area_of(ti.get("path", ""))
    elif tool == "Agent":
        text, area = "Делегує агенту: " + (ti.get("description") or ""), "other"
    else:
        short = tool.split("__")[-1]
        text = short + " " + json.dumps(ti, ensure_ascii=False)
        area = P.area_of(tool, text)
    if not ok:
        text = "ПОМИЛКА · " + text + " → " + str(ev.get("error", ""))
    return "tool", tool.split("__")[-1], area, P.redact(text), ok


def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return
    if not P.token():
        return
    kind, tool, area, text, ok = describe(ev)
    data = {"ts": int(time.time() * 1000), "sid": ev.get("session_id", "")[-12:], "kind": kind,
            "tool": tool, "area": area, "text": text, "ok": ok}
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
