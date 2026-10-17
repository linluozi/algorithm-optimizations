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
    """Return (rows, machine label) straight from the measured JSON."""
    with open(RESULTS, encoding="utf-8") as fh:
        data = json.load(fh)
    variants = data["cases"]["min-max/3000k"]["variants"]
    rows = [(LABELS[k], variants[k]["best_ms"]) for k in LABELS if k in variants]
    machine = data["machine"]
    os_family = machine["platform"].split("-")[0]
    label = f"{os_family} · {machine['implementation']} {machine['python']}"
    return rows, label


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
    rows, machine_label = load_rows()

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
    right = machine_label
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


def load_sorting():
    """Rows of (shape, naive_ms, early_ms, cocktail_ms) from the measured JSON."""
    with open(RESULTS, encoding="utf-8") as fh:
        data = json.load(fh)
    order = ("sorted", "adjacent-50", "far-50", "random", "reversed")
    pretty = {
        "sorted": "already sorted",
        "adjacent-50": "50 adjacent swaps",
        "far-50": "50 far-apart swaps",
        "random": "random",
        "reversed": "reversed",
    }
    rows = []
    for shape in order:
        case = data["cases"][f"sort/{shape}/2000"]["variants"]
        rows.append((
            pretty[shape],
            case["naive"]["best_ms"],
            case["early"]["best_ms"],
            case["cocktail"]["best_ms"],
        ))
    return rows, f"{data['machine']['implementation']} {data['machine']['python']}"


def build_sorting(width, height, path):
    """Impact map: speedup over plain bubble sort, log scale, 1.0x marked."""
    img = Image.new("RGB", (width, height), PAPER)
    draw = wash(img, height)
    rows, machine = load_sorting()

    pad = 56
    draw.text((pad, 26), "WHERE EACH CHANGE ACTUALLY PAYS OFF", font=font(12, mono=True), fill=INK3)
    tw = draw.textlength(machine, font=font(12, mono=True))
    draw.text((width - pad - tw, 26), machine, font=font(12, mono=True), fill=INK3)

    draw.text((pad, 46), "Two changes, two different inputs.", font=font(34, bold=True), fill=INK)

    # legend
    ly = 104
    lx = pad
    for label, colour in (("early exit", AMBER), ("+ bidirectional", CLAY)):
        draw.rounded_rectangle([lx, ly, lx + 22, ly + 12], radius=3, fill=colour)
        draw.text((lx + 30, ly - 4), label, font=font(14), fill=INK2)
        lx += 30 + draw.textlength(label, font=font(14)) + 34
    draw.text((lx + 10, ly - 4), "·  right of the 1x line = faster than plain bubble sort",
              font=font(14), fill=INK3)

    x0, x1 = pad + 196, width - pad - 118
    top = 152
    row_h = 70
    bar_h = 19
    lo, hi = 0.9, 1100.0
    import math

    def sx(v):
        frac = (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
        return x0 + frac * (x1 - x0)

    base_x = sx(1.0)
    rows_bottom = top + row_h * len(rows) - 22
    # gridlines
    for tick in (1, 10, 100, 1000):
        gx = sx(tick)
        draw.line([(gx, top - 12), (gx, rows_bottom)], fill=LINE, width=1)
        label = f"{tick}x"
        draw.text((gx - draw.textlength(label, font=font(12, mono=True)) / 2, rows_bottom + 10),
                  label, font=font(12, mono=True), fill=INK3)

    for i, (name, naive, early, cocktail) in enumerate(rows):
        y = top + i * row_h
        draw.text((pad, y + 6), name, font=font(17), fill=INK)
        draw.text((pad, y + 30), f"{naive:.1f} ms baseline", font=font(12, mono=True), fill=INK3)
        for j, (colour, ms) in enumerate(((AMBER, early), (CLAY, cocktail))):
            by = y + j * (bar_h + 4)
            speedup = naive / ms
            label = (f"{ms:.3g} ms · {speedup:.2f}x" if speedup < 100
                     else f"{ms:.3g} ms · {speedup:.0f}x")
            tw = draw.textlength(label, font=font(12, mono=True))
            if speedup >= 1.005:
                x = sx(speedup)
                draw.rounded_rectangle([base_x, by, max(x, base_x + 2), by + bar_h], radius=3, fill=colour)
                if x + tw + 12 < width - pad:
                    draw.text((x + 8, by + 1), label, font=font(12, mono=True), fill=INK2)
                else:
                    draw.text((x - tw - 8, by + 1), label, font=font(12, mono=True), fill=(255, 250, 240))
            else:
                # slower than the baseline: a hairline left of 1x, label to the right
                # (the row to the right of the line is empty by definition)
                draw.rounded_rectangle([base_x - 3, by, base_x, by + bar_h], radius=1,
                                       fill=(176, 74, 48))
                draw.text((base_x + 10, by + 1), label, font=font(12, mono=True), fill=INK2)

    img.save(path, optimize=True)
    print("wrote", path, img.size)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    build(1280, 400, os.path.join(OUT_DIR, "banner.png"), 0)
    build(1280, 640, os.path.join(OUT_DIR, "social-preview.png"), 1)
    build_sorting(1280, 548, os.path.join(OUT_DIR, "sorting-shapes.png"))


if __name__ == "__main__":
    main()
