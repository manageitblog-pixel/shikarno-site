"""Відновлення озвучки з резерву studio/eps/_vo_backup/<slug>/*.opus → /home/claude/eps/<slug>/*.wav (PCM16 моно).
Лише якщо WAV відсутній (наявне не перезаписується). vo.wav — 44,1 кГц (як після мастерингу в run_voice.short), решта — 24 кГц.
usage: python3 studio/eps/restore_vo.py [--dest /home/claude/eps] [slug ...]"""
import os, sys, shutil, subprocess
HERE = os.path.dirname(os.path.realpath(__file__)); BK = os.path.join(HERE, "_vo_backup")


def main(argv):
    dest = "/home/claude/eps"
    if "--dest" in argv: i = argv.index("--dest"); dest = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if not os.path.isdir(BK): print("restore_vo: резерву немає"); return 0
    slugs = argv or sorted(s for s in os.listdir(BK) if os.path.isdir(os.path.join(BK, s)))
    n = bad = 0
    for s in slugs:
        src, dst = os.path.join(BK, s), os.path.join(dest, s)
        for f in sorted(os.listdir(src)):
            name, ext = os.path.splitext(f); os.makedirs(dst, exist_ok=True)
            if ext == ".opus":
                out = os.path.join(dst, name + ".wav")
                if os.path.exists(out): continue
                sr = "44100" if name == "vo" else "24000"
                r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(src, f), "-ac", "1", "-ar", sr,
                                    "-c:a", "pcm_s16le", out], capture_output=True, text=True)
                if r.returncode: bad += 1; print("restore_vo FAIL", s, f, r.stderr[-200:]); continue
            elif ext == ".json":
                out = os.path.join(dst, f)
                if os.path.exists(out): continue
                shutil.copy(os.path.join(src, f), out)
            else:
                continue
            n += 1; print("restore_vo:", s, os.path.basename(out))
    print(f"restore_vo: відновлено {n}, помилок {bad}"); return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
