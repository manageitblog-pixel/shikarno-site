#!/usr/bin/env python3
"""Збір реальних пошукових підказок Google (autocomplete) українською.

Для кожного seed: сам seed, seed + " " + літера українського алфавіту,
питальний префікс + " " + seed. hl=uk, gl=ua, послідовно, пауза 0.3–0.5 с.

Autocomplete НЕ дає обсягів пошуку. Проксі популярності — у скількох різних
seed фраза з'являється в підказках (і скільки разів загалом).

    python3 tools/keywords.py            # збір → tools/keywords_raw.json (кеш)
    python3 tools/keywords.py --report   # лише звіт зі збереженого кешу
"""
import json, random, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

SEEDS = [
    "chatgpt", "чат gpt", "gpt 6", "gemini", "джеміні", "claude", "клод ші",
    "штучний інтелект", "ші українською", "нейромережа", "нейромережі для",
    "ші агент", "ші для бізнесу", "промпти", "генерація відео ші", "flux",
    "google maps carplay", "android auto gemini", "meta muse", "anthropic",
    "openai", "php вразливість", "кібербезпека ші", "chatgpt безкоштовно",
    "chatgpt україна", "gemini українською",
]
LETTERS = "а б в г ґ д е є ж з и і ї й к л м н о п р с т у ф х ц ч ш щ ю я".split()
PREFIXES = ["як", "що таке", "чи", "де", "скільки", "навіщо"]

URL = "https://suggestqueries.google.com/complete/search?client=firefox&hl=uk&gl=ua&q="
RAW = Path(__file__).with_name("keywords_raw.json")


def suggest(q):
    for attempt in range(3):
        try:
            req = urllib.request.Request(URL + urllib.parse.quote(q),
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            return [s.strip().lower() for s in data[1]]
        except Exception as e:  # noqa: BLE001
            print("  ! ", q, e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    return []


def queries_for(seed):
    yield seed
    for l in LETTERS:
        yield f"{seed} {l}"
    for p in PREFIXES:
        yield f"{p} {seed}"


def collect():
    raw = json.loads(RAW.read_text()) if RAW.exists() else {}
    for seed in SEEDS:
        raw.setdefault(seed, {})
        for q in queries_for(seed):
            if q in raw[seed]:
                continue
            raw[seed][q] = suggest(q)
            time.sleep(random.uniform(0.3, 0.5))
        RAW.write_text(json.dumps(raw, ensure_ascii=False, indent=1))
        n = len({s for v in raw[seed].values() for s in v})
        print(f"{seed}: {n} унікальних підказок", flush=True)
    return raw


def rank(raw):
    """phrase → (кількість seed, кількість появ)."""
    seeds, hits = defaultdict(set), defaultdict(int)
    for seed, qs in raw.items():
        for q, sugg in qs.items():
            for s in sugg:
                if s in qs:  # підказка, що дослівно = нашому запиту, не рахуємо
                    continue
                seeds[s].add(seed)
                hits[s] += 1
    return sorted(((p, len(seeds[p]), hits[p]) for p in hits),
                  key=lambda x: (-x[1], -x[2], x[0]))


if __name__ == "__main__":
    raw = json.loads(RAW.read_text()) if "--report" in sys.argv else collect()
    ranked = rank(raw)
    out = Path(__file__).with_name("keywords_ranked.json")
    out.write_text(json.dumps(ranked, ensure_ascii=False, indent=0))
    print(f"Усього фраз: {len(ranked)} → {out}")
    for p, s, h in ranked[:40]:
        print(f"{s:2d} {h:3d}  {p}")
