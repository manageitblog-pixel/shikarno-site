"""Генерує картинку 1200×630 для кожної статті (og:image, Google Discover, соцмережі)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools/fonts/Montserrat.ttf"
LOGO = ROOT / "static/bait.png"
W, H = 1200, 630

def _font(size, weight):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([weight])
    return f

def _wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=font) <= width: line = test
        else: lines.append(line); line = word
    if line: lines.append(line)
    return lines

def make(title, label, out):
    img = Image.new("RGB", (W, H), "#0B0A1C")
    px = img.load()
    for y in range(H):  # нічний градієнт
        t = y / H
        c = tuple(int(a + (b - a) * t) for a, b in zip((11, 10, 28), (26, 18, 64)))
        for x in range(W): px[x, y] = c
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, H - 14, W, H), 0, fill="#FF4F8B")
    # мітка
    lf = _font(30, 800)
    lw = d.textlength(label, font=lf)
    d.rounded_rectangle((70, 60, 70 + lw + 36, 112), 12, fill="#FFD60A")
    d.text((88, 68), label, font=lf, fill="#0B0A1C")
    # заголовок: підбираємо розмір, щоб влізло в 4 рядки
    for size in (64, 58, 52, 46, 42):
        tf = _font(size, 900)
        lines = _wrap(d, title, tf, 820)
        if len(lines) <= 4: break
    lines = lines[:4]
    y = 150
    for ln in lines:
        d.text((70, y), ln, font=tf, fill="#F3F0FF"); y += int(size * 1.18)
    # бренд
    bf = _font(40, 900)
    d.rounded_rectangle((70, H - 104, 136, H - 50), 10, fill="#FFD60A")
    d.text((80, H - 101), "ШІ", font=bf, fill="#0B0A1C")
    d.text((142, H - 101), "карно", font=bf, fill="#FFFFFF")
    d.text((300, H - 92), "shikarno.com.ua", font=_font(26, 600), fill="#A9A3C9")
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA").resize((260, 260))
        img.paste(logo, (W - 300, H - 360), logo)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
