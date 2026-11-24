"""Таймер відкладених статей для .github/workflows/release-timer.yml.

Чому: GitHub `schedule` — best-effort і під навантаженням скидає запуски. 23–24.11 з ~120 очікуваних
запусків cron pages.yml відбулось 3 (19:25Z, 04:23Z, 15:10Z) — статті 13:00 і 19:00 з'являлись
лише після ручного запуску. Події `push` і `workflow_dispatch` надійні, тож таймер чекає (`sleep`)
до найближчої статті з датою в майбутньому і запускає pages.yml через workflow_dispatch.

Друкує рядки для $GITHUB_OUTPUT:
  wait=<секунд>   — скільки чекати (нічого, якщо майбутніх статей у межах HORIZON немає)
  release=1|0     — 1: після очікування запустити pages.yml; 0: лише перезапустити таймер (стаття далі за MAX_WAIT)
  next=<ISO>      — для журналу
Без залежностей (лише stdlib), щоб не ставити pip у таймері.
"""
import datetime as dt
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_WAIT = 5 * 3600 + 40 * 60      # job на GitHub-hosted runner живе ≤ 6 год
BUFFER = 60                         # build.py бере пост, лише коли date < now
HORIZON = dt.timedelta(days=14)     # далі — не тримаємо runner, чекаємо push


def future_dates(now):
    out = []
    for p in glob.glob(os.path.join(ROOT, "content/posts/*.md")):
        s = open(p, encoding="utf-8").read()
        m = re.match(r"---\n(.*?)\n---", s, re.S)
        if not m: continue
        fm = m.group(1)
        if re.search(r"^draft:\s*true", fm, re.M): continue
        d = re.search(r"^date:\s*['\"]?([^'\"\n]+)", fm, re.M)
        if not d: continue
        try: t = dt.datetime.fromisoformat(d.group(1).strip())
        except ValueError: continue
        if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
        if now < t <= now + HORIZON: out.append(t)
    return sorted(out)


def plan(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    fut = future_dates(now)
    if not fut: return None
    delta = int((fut[0] - now).total_seconds()) + BUFFER
    if delta <= MAX_WAIT: return {"wait": delta, "release": 1, "next": fut[0].isoformat()}
    return {"wait": MAX_WAIT, "release": 0, "next": fut[0].isoformat()}


if __name__ == "__main__":
    p = plan()
    if not p:
        print("next=none")
        sys.exit(0)
    for k, v in p.items(): print(f"{k}={v}")
