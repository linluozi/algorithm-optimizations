"""Render the banner and social-preview image from measured data.

Needs Pillow, which is not a dependency of the package itself:

    python -m pip install pillow
    python scripts/make_assets.py

The chart is read from benchmarks/results.json — it is not drawn by hand, so it
cannot drift away from the numbers in the README.
"""

from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "benchmarks", "results.json")
OUT_DIR = os.path.join(ROOT, "assets")

PAPER = (253, 249, 241)
PAPER2 = (246, 238, 223)
INK = (42, 33, 24)
INK2 = (90, 74, 56)
INK3 = (138, 122, 102)
CLAY = (194, 96, 60)
CLAY_D = (176, 74, 48)
AMBER = (198, 141, 58)
LINE = (216, 202, 178)

LABELS = {
    "naive": "naive loop",
    "naive-nocopy": "naive, no tail copy",
    "pairwise-indexed": "pairwise, indexed",
    "pairwise": "pairwise, zip(it, it)",
    "builtin": "min() / max()",
}


def font(size, bold=False, mono=False):
    if mono:
        names = ["consola.ttf", "Consola.ttf", "DejaVuSansMono.ttf"]
    elif bold:
        names = ["georgiab.ttf", "DejaVuSerif-Bold.ttf", "arialbd.ttf"]
    else:
        names = ["georgia.ttf", "DejaVuSerif.ttf", "arial.ttf"]
    for name in names:
        for base in ("C:/Windows/Fonts/", "/usr/share/fonts/truetype/dejavu/"):
            path = os.path.join(base, name)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except OSError:
                    pass
    return ImageFont.load_default()


def load_rows():
    with open(RESULTS, encoding="utf-8") as fh:
        data = json.load(fh)
    variants = data["cases"]["min-max/3000k"]["variants"]
    return [(LABELS[k], variants[k]["best_ms"]) for k in LABELS if k in variants]


def wash(img, height):
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        colour = tuple(int(a + (b - a) * t) for a, b in zip(PAPER, PAPER2))
        draw.line([(0, y), (img.width, y)], fill=colour)
    draw.rectangle([0, 0, img.width, 6], fill=CLAY)
    return draw


def draw_chart(draw, rows, x0, y0, width, bar_h, gap, label_size, value_size):
    base = rows[0][1]
    peak = max(v for _, v in rows)
    label_w = int(width * 0.19)
    value_w = 150
    track = width - label_w - value_w
    for i, (name, ms) in enumerate(rows):
        y = y0 + i * (bar_h + gap)
        ratio = ms / base
        if ratio > 1.002:
            colour = CLAY_D
        elif ratio < 0.999:
            colour = AMBER
        else:
            colour = (152, 134, 110)
        draw.text((x0, y + (bar_h - label_size) // 2 - 3), name,
                  font=font(label_size), fill=INK if i else INK2)
        w = max(4, int(track * ms / peak))
        draw.rounded_rectangle([x0 + label_w, y, x0 + label_w + w, y + bar_h],
                               radius=4, fill=colour)
        tail = f"{ms:5.1f} ms" + (f"   {ratio:.2f}x" if i else "   1.00x")
        draw.text((x0 + label_w + w + 12, y + (bar_h - value_size) // 2 - 2), tail,
                  font=font(value_size, mono=True), fill=INK2)


def build(width, height, path, scale):
    """scale = 0 for the wide banner, 1 for the taller social card."""
    img = Image.new("RGB", (width, height), PAPER)
    draw = wash(img, height)
    rows = load_rows()

    pad = 56
    if scale == 0:
        eyebrow_y, title_y, title_size, line_h = 26, 48, 36, 43
        sub_y, sub_size, chart_y, bar_h, gap = 142, 15, 190, 17, 15
        label_size, value_size = 15, 13
        footer = False
    else:
        eyebrow_y, title_y, title_size, line_h = 40, 72, 44, 52
        sub_y, sub_size, chart_y, bar_h, gap = 196, 17, 252, 30, 24
        label_size, value_size = 18, 16
        footer = True

    draw.text((pad, eyebrow_y), "ALGORITHM OPTIMIZATIONS · MEASURED, NOT ASSERTED",
              font=font(12, mono=True), fill=INK3)
    right = "CPython 3.13 / Ryzen 7 H 255"
    tw = draw.textlength(right, font=font(12, mono=True))
    draw.text((width - pad - tw, eyebrow_y), right, font=font(12, mono=True), fill=INK3)

    draw.text((pad, title_y), "25% fewer comparisons,", font=font(title_size, bold=True), fill=INK)
    draw.text((pad, title_y + line_h), "58% more time.", font=font(title_size, bold=True), fill=CLAY)
    draw.text((pad, sub_y), "Pairwise min/max on 3,000,000 integers, best of 5, isolated processes.",
              font=font(sub_size), fill=INK2)

    draw_chart(draw, rows, pad, chart_y, width - 2 * pad, bar_h, gap, label_size, value_size)

    if footer:
        foot_y = height - 40
        draw.line([(pad, foot_y - 14), (width - pad, foot_y - 14)], fill=LINE, width=1)
        draw.text((pad, foot_y), "bars = wall clock ·  red = slower than the naive loop",
                  font=font(13), fill=INK3)
        note = "benchmarks/results.json"
        tw = draw.textlength(note, font=font(12, mono=True))
        draw.text((width - pad - tw, foot_y), note, font=font(12, mono=True), fill=INK3)

    img.save(path, optimize=True)
    print("wrote", path, img.size)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    build(1280, 400, os.path.join(OUT_DIR, "banner.png"), 0)
    build(1280, 640, os.path.join(OUT_DIR, "social-preview.png"), 1)


if __name__ == "__main__":
    main()
