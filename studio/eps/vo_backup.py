"""Резерв озвучки поза контейнером (25.11: рестарт стер усі part*.wav/vo.wav, квота TTS ~15 запитів/добу).
Після кожного чистого фіналу (run_voice.guide_part → part_final, run_voice.short → short_final) WAV стискається в Opus
(48 кбіт/с, моно, 24 кГц, ~360 КБ/хв) у studio/eps/_vo_backup/<slug>/ і комітиться/пушиться лише ця тека.
Відновлення — studio/eps/restore_vo.py (викликається з bootstrap.sh). Помилки тут НІКОЛИ не валять озвучку."""
import os, sys, json, time, shutil, subprocess
HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BK = os.path.join(HERE, "_vo_backup")
BRANCH = os.environ.get("VO_BACKUP_BRANCH", "claude/inspiring-mccarthy-77osj6")
TRAILER = ("\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_015jXV5qSKwiFSLT57DpHniU")


def _log(**k):
    k["t"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); print(json.dumps(k, ensure_ascii=False), file=sys.stderr, flush=True)


def to_opus(wav, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ac", "1", "-ar", "24000", "-c:a", "libopus", "-b:a", "48k",
                    "-fflags", "+bitexact", "-flags:a", "+bitexact", "-map_metadata", "-1", out],
                   check=True, timeout=300)


def backup(slug, wavs, label, extra=(), push=True):
    """wavs — шляхи WAV (зберігаються як <ім'я>.opus); extra — дрібні файли як є (vo_tl.json). Повертає список файлів або []."""
    try:
        d = os.path.join(BK, slug); os.makedirs(d, exist_ok=True); done = []
        for w in wavs:
            if os.path.exists(w):
                o = os.path.join(d, os.path.splitext(os.path.basename(w))[0] + ".opus"); to_opus(w, o); done.append(o)
        for f in extra:
            if os.path.exists(f):
                o = os.path.join(d, os.path.basename(f)); shutil.copy(f, o); done.append(o)
        if not done: return []
        if push: _git(slug, label)
        _log(ev="vo_backup", slug=slug, label=label, files=[os.path.basename(x) for x in done],
             kb=round(sum(os.path.getsize(x) for x in done) / 1024))
        return done
    except Exception as e:  # noqa: BLE001 — резерв не повинен зупиняти озвучку
        _log(ev="vo_backup_fail", slug=slug, label=label, err=str(e)[:300]); return []


def _git(slug, label):
    rel = os.path.relpath(os.path.join(BK, slug), REPO)
    g = lambda *a: subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, timeout=120)
    try:
        r = g("add", "--", rel)
        if r.returncode: raise RuntimeError("add: " + r.stderr[-200:])
        if g("diff", "--cached", "--quiet", "--", rel).returncode == 0: return  # нічого нового
        # pathspec → комітиться ЛИШЕ тека резерву, навіть якщо інші агенти щось застейджили
        r = g("commit", "-m", f"vo backup {slug} {label}{TRAILER}", "--", rel)
        if r.returncode: raise RuntimeError("commit: " + (r.stderr or r.stdout)[-200:])
        r = g("push", "origin", f"HEAD:{BRANCH}")
        if r.returncode: raise RuntimeError("push (коміт лишився локально, піде з наступним push): " + r.stderr[-200:])
    except Exception as e:  # noqa: BLE001
        _log(ev="vo_backup_git_fail", slug=slug, label=label, err=str(e)[:300])


# COO 28.11: гайди #1/#2 втратили vo.wav/align.json (рестарт) → clip_cut.py не має джерела, кліпів немає. Частини partN.opus
# уже в git, з них vo_raw/vo.wav відтворюються; align.json (Whisper, довго) і vo_tl.json — ні. Після align.py довгого:
#   python3 studio/eps/vo_backup.py meta <slug>   → align.json + vo_tl.json у _vo_backup/<slug>/ (КБ, коміт лише цієї теки)
if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "meta":
        D = os.path.join("/home/claude/eps", sys.argv[2])
        got = backup(sys.argv[2], [], "meta", extra=[os.path.join(D, f) for f in ("align.json", "vo_tl.json")])
        print("vo_backup meta:", [os.path.basename(x) for x in got] or "НІЧОГО (немає align.json/vo_tl.json)")
        sys.exit(0 if got else 1)
    print("usage: vo_backup.py meta <slug>"); sys.exit(2)
