#!/usr/bin/env python3
"""IG-версії Shorts: перший кадр = обкладинка, що вміщається в кроп сітки 3:4.

Instagram у сітці профілю показує Reels центральним кропом 1080×1440 (y 240–1680),
а обкладинкою бере перший кадр. Тому:
  ig_cover.png — 1080×1920: thumb.png (v4) як картка 810×1440 у зоні 3:4, поля — розмитий thumb;
  ig.mp4       — 0,5 с обкладинки + оригінальний final.mp4 без змін (звук зсунуто на 0,5 с, тиша спочатку).
Також: обкладинки хайлайтів (1080×1080, іконка в колі ~700 px).

  python3 studio/eps/ig_cover.py reels [slug ...]
  python3 studio/eps/ig_cover.py highlights
  python3 studio/eps/ig_cover.py sheet OUT.jpg     # контактний аркуш кропів 3:4 перших кадрів ig.mp4
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

EPS = Path(__file__).resolve().parent
W, H = 1080, 1920
CROP_TOP, CROP_H = 240, 1440          # центральний кроп 3:4
COVER_SEC = 0.5

YELLOW, PURPLE, PINK, CYAN = (255, 214, 10), (124, 92, 255), (255, 79, 139), (76, 242, 255)
BG0, BG1 = (11, 10, 28), (26, 18, 64)

# slug → (оригінал, обкладинка YouTube, тека для ig.mp4 / ig_cover.png)
REELS = {
    "ep81_tier_kids": ("ep81_tier_kids/final.mp4", "ep81_tier_kids/thumb.png", "ep81_tier_kids"),
    "ep79_tier_money": ("ep79_tier_money/final.mp4", "ep79_tier_money/thumb.png", "ep79_tier_money"),
    "ep80_prof_olx": ("ep80_prof_olx/final.mp4", "ep80_prof_olx/thumb.png", "ep80_prof_olx"),
    "cut6_c1_chatgpt": ("cuts6/c1_chatgpt.mp4", "cuts6/c1_thumb.png", "cut6_c1_chatgpt"),
    "ep76_inkognito_shi": ("ep76_inkognito_shi/final.mp4", "ep76_inkognito_shi/thumb.png", "ep76_inkognito_shi"),
}


def rounded_mask(size, r, ss=4):
    w, h = size
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize(size, Image.LANCZOS)


def make_cover(thumb_path: Path) -> Image.Image:
    th = Image.open(thumb_path).convert("RGB").resize((W, H), Image.LANCZOS)
    # фон: той самий thumb, збільшений, розмитий і притемнений (без нових елементів)
    bg = th.resize((int(W * 1.15), int(H * 1.15)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), BG0), 0.45)
    # картка: увесь thumb у зоні 3:4 з відступом під обвід
    pad = 16
    ch = CROP_H - 2 * pad
    cw = round(ch * W / H)
    card = th.resize((cw, ch), Image.LANCZOS)
    x, y = (W - cw) // 2, CROP_TOP + pad
    r = 44
    # тінь
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((x, y + 18, x + cw, y + ch + 18), r, fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    bg.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh)
    # обвід жовтим (бренд)
    ring = rounded_mask((cw + 16, ch + 16), r + 8)
    bg.paste(Image.new("RGB", ring.size, YELLOW), (x - 8, y - 8), ring)
    bg.paste(card, (x, y), rounded_mask((cw, ch), r))
    return bg


def run(cmd):
    subprocess.run(cmd, check=True)


def make_reel(slug: str):
    src, thumb, out = REELS[slug]
    src, thumb, out = EPS / src, EPS / thumb, EPS / out
    out.mkdir(exist_ok=True)
    cover = make_cover(thumb)
    cover_png = out / "ig_cover.png"
    cover.save(cover_png)
    ig = out / "ig.mp4"
    fc = (
        f"[0:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p,trim=duration={COVER_SEC},setpts=PTS-STARTPTS[c];"
        f"[1:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p,setpts=PTS-STARTPTS[m];"
        f"[c][m]concat=n=2:v=1:a=0[v];"
        f"[1:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"adelay={int(COVER_SEC * 1000)}:all=1,asetpts=PTS-STARTPTS[a]"
    )
    run(["ffmpeg", "-v", "error", "-y",
         "-loop", "1", "-framerate", "30", "-t", str(COVER_SEC), "-i", str(cover_png),
         "-i", str(src),
         "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(ig)])
    print(slug, ig, ig.stat().st_size)


# ---------- хайлайти ----------
SS = 4  # суперсемплінг


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def diag_gradient(size, c0, c1):
    w, h = size
    g = Image.new("RGB", (256, 1))
    for i in range(256):
        g.putpixel((i, 0), lerp(c0, c1, i / 255))
    g = g.resize((w * 2, 1)).resize((w * 2, h * 2))
    return g.rotate(-45, resample=Image.BICUBIC).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))


def icon_tier(d, cx, cy, s):
    cols = [(255, 92, 92), YELLOW, (61, 220, 132)]
    rh, gap, w = 0.30 * s, 0.10 * s, 1.5 * s
    top = cy - (3 * rh + 2 * gap) / 2
    for i, c in enumerate(cols):
        y = top + i * (rh + gap)
        x0 = cx - w / 2
        d.rounded_rectangle((x0, y, x0 + rh * 1.1, y + rh), 0.06 * s, fill=c)
        for j in range(3 - i):
            bx = x0 + rh * 1.1 + 0.08 * s + j * (rh + 0.06 * s)
            d.rounded_rectangle((bx, y, bx + rh, y + rh), 0.06 * s, fill=(255, 255, 255))


def icon_shield(d, cx, cy, s):
    w, h = 1.25 * s, 1.5 * s
    top = cy - h / 2
    pts = [(cx, top)]
    pts += [(cx + w / 2, top + 0.16 * h), (cx + w / 2, top + 0.48 * h)]
    for k in range(1, 21):
        t = k / 20
        pts.append((cx + w / 2 * (1 - t) ** 1.2, top + 0.48 * h + 0.52 * h * math.sin(t * math.pi / 2)))
    pts = pts + [(2 * cx - x, y) for x, y in reversed(pts[1:])]
    d.polygon(pts, fill=(255, 255, 255))
    # замок
    lw, lh = 0.5 * s, 0.38 * s
    ly = cy + 0.02 * s
    d.arc((cx - 0.17 * s, ly - 0.36 * s, cx + 0.17 * s, ly + 0.02 * s), 180, 360, fill=PURPLE, width=int(0.075 * s))
    d.line((cx - 0.17 * s + 0.037 * s, ly - 0.18 * s, cx - 0.17 * s + 0.037 * s, ly), fill=PURPLE, width=int(0.075 * s))
    d.line((cx + 0.17 * s - 0.037 * s, ly - 0.18 * s, cx + 0.17 * s - 0.037 * s, ly), fill=PURPLE, width=int(0.075 * s))
    d.rounded_rectangle((cx - lw / 2, ly - 0.02 * s, cx + lw / 2, ly + lh), 0.06 * s, fill=PURPLE)
    d.ellipse((cx - 0.055 * s, ly + 0.09 * s, cx + 0.055 * s, ly + 0.2 * s), fill=YELLOW)
    d.rectangle((cx - 0.025 * s, ly + 0.15 * s, cx + 0.025 * s, ly + 0.28 * s), fill=YELLOW)


def icon_gift(d, cx, cy, s):
    w = 1.3 * s
    bt, bb = cy - 0.2 * s, cy + 0.75 * s
    d.rounded_rectangle((cx - w / 2 + 0.07 * s, bt, cx + w / 2 - 0.07 * s, bb), 0.07 * s, fill=(255, 255, 255))
    d.rounded_rectangle((cx - w / 2, bt - 0.3 * s, cx + w / 2, bt + 0.05 * s), 0.07 * s, fill=(255, 255, 255))
    rb = 0.2 * s
    d.rectangle((cx - rb / 2, bt - 0.3 * s, cx + rb / 2, bb), fill=YELLOW)
    d.rectangle((cx - w / 2, bt - 0.05 * s, cx + w / 2, bt + 0.05 * s), fill=PURPLE)
    lw = int(0.1 * s)
    d.ellipse((cx - 0.55 * s, bt - 0.75 * s, cx - 0.02 * s, bt - 0.3 * s), outline=YELLOW, width=lw)
    d.ellipse((cx + 0.02 * s, bt - 0.75 * s, cx + 0.55 * s, bt - 0.3 * s), outline=YELLOW, width=lw)


def icon_case(d, cx, cy, s):
    w, h = 1.5 * s, 1.0 * s
    top = cy - h / 2 + 0.12 * s
    d.rounded_rectangle((cx - 0.3 * s, top - 0.32 * s, cx + 0.3 * s, top + 0.1 * s), 0.1 * s,
                        outline=(255, 255, 255), width=int(0.1 * s))
    d.rounded_rectangle((cx - w / 2, top, cx + w / 2, top + h), 0.12 * s, fill=(255, 255, 255))
    d.rectangle((cx - w / 2, top + 0.4 * h, cx + w / 2, top + 0.4 * h + 0.06 * s), fill=PURPLE)
    d.rounded_rectangle((cx - 0.13 * s, top + 0.32 * h, cx + 0.13 * s, top + 0.32 * h + 0.22 * s), 0.04 * s, fill=YELLOW)


def icon_book(d, cx, cy, s):
    w, h = 0.72 * s, 1.1 * s
    top = cy - h / 2
    for sgn in (-1, 1):
        x_in, x_out = cx + sgn * 0.04 * s, cx + sgn * (0.04 * s + w)
        pts = [(x_in, top + 0.08 * s), (x_out, top), (x_out, top + h), (x_in, top + h + 0.08 * s)]
        d.polygon(pts, fill=(255, 255, 255))
        for k in range(4):
            yy = top + 0.22 * s + k * 0.2 * s
            a, b = cx + sgn * 0.16 * s, cx + sgn * (w - 0.08 * s)
            d.line((a, yy + 0.02 * s, b, yy), fill=PURPLE if k else YELLOW, width=int(0.06 * s))
    d.polygon([(cx - 0.04 * s, top + h + 0.08 * s), (cx + 0.04 * s, top + h + 0.08 * s),
               (cx + 0.04 * s, top + h + 0.2 * s), (cx - 0.04 * s, top + h + 0.2 * s)], fill=YELLOW)


HIGHLIGHTS = [("tir-lysty", "Тір-листи", icon_tier), ("bezpeka", "Безпека", icon_shield),
              ("bezkoshtovno", "Безкоштовно", icon_gift), ("profesii", "Професії", icon_case),
              ("gajdy", "Гайди", icon_book)]


def make_highlight(fn):
    S = 1080 * SS
    img = diag_gradient((S, S), BG0, BG1)
    d = ImageDraw.Draw(img)
    c, R = S / 2, 350 * SS
    # бірюзове кільце + коло з градієнтом бренду
    d.ellipse((c - R - 14 * SS, c - R - 14 * SS, c + R + 14 * SS, c + R + 14 * SS), fill=CYAN)
    disk = diag_gradient((int(2 * R), int(2 * R)), PURPLE, PINK)
    m = Image.new("L", disk.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, disk.width - 1, disk.height - 1), fill=255)
    img.paste(disk, (int(c - R), int(c - R)), m)
    fn(ImageDraw.Draw(img), c, c, 260 * SS)
    return img.resize((1080, 1080), Image.LANCZOS)


def highlights():
    out = EPS / "ig_highlights"
    out.mkdir(exist_ok=True)
    paths = []
    for slug, _name, fn in HIGHLIGHTS:
        p = out / f"{slug}.png"
        make_highlight(fn).save(p)
        paths.append(p)
        print(p)
    return paths


def sheet(out_jpg: str, kind="reels"):
    from PIL import ImageFont
    font = ImageFont.truetype(str(EPS.parents[1] / "tools/fonts/Montserrat.ttf"), 22)
    if kind == "reels":
        tiles = []
        for slug, (_s, _t, o) in REELS.items():
            f0 = Path(out_jpg).with_name(f"f0_{slug}.png")
            run(["ffmpeg", "-v", "error", "-y", "-i", str(EPS / o / "ig.mp4"), "-frames:v", "1", str(f0)])
            im = Image.open(f0).convert("RGB").crop((0, CROP_TOP, W, CROP_TOP + CROP_H)).resize((360, 480), Image.LANCZOS)
            tiles.append((slug, im))
        tw, th = 360, 480
    else:
        tiles = []
        for slug, name, _fn in HIGHLIGHTS:
            im = Image.open(EPS / "ig_highlights" / f"{slug}.png").convert("RGB").resize((240, 240), Image.LANCZOS)
            m = Image.new("L", im.size, 0)
            ImageDraw.Draw(m).ellipse((0, 0, 239, 239), fill=255)
            c = Image.new("RGB", im.size, (255, 255, 255)); c.paste(im, (0, 0), m)
            tiles.append((name, c))
        tw, th = 240, 240
    g = 20
    sheet_im = Image.new("RGB", (len(tiles) * (tw + g) + g, th + 70), (255, 255, 255))
    d = ImageDraw.Draw(sheet_im)
    for i, (name, im) in enumerate(tiles):
        x = g + i * (tw + g)
        sheet_im.paste(im, (x, g))
        d.text((x, th + g + 10), name, fill=(20, 20, 20), font=font)
    sheet_im.save(out_jpg, quality=90)
    print(out_jpg)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "reels"
    if cmd == "reels":
        for s in sys.argv[2:] or REELS:
            make_reel(s)
    elif cmd == "highlights":
        highlights()
    elif cmd == "sheet":
        sheet(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "reels")
