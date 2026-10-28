#!/usr/bin/env python3
"""Composite grid of close-ups centred on keynote tags of a demo plan, with the
dashed chains (demo_chains.py csv) drawn in red and labelled by id, so each
keynote can be tied to measured linework.

usage: tag_grid.py <pdf> <page> <chains_csv> <out_jpg> <half_size_pt> <cols> TAG[:instance] ...
Tag positions come from the page text layer (standalone 1-2 digit words in the
plan area, unrotated y < 1980 and x >= 100).
"""
import sys, csv, re
import pymupdf
from PIL import Image, ImageDraw, ImageFont

pdf, pno, csvp, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
half, cols = float(sys.argv[5]), int(sys.argv[6])
want = sys.argv[7:]
page = pymupdf.open(pdf)[pno - 1]; M = page.rotation_matrix; dpi = 150; sc = dpi / 72.0
words = page.get_text("words")
pos = {}
for w in words:
    x0, y0, x1, y1, t = w[:5]
    if re.fullmatch(r"\d{1,2}", t) and y0 < 1980 and x0 >= 100:
        pos.setdefault(int(t), []).append(((x0 + x1) / 2, (y0 + y1) / 2))
for k in pos: pos[k].sort()
chains = list(csv.DictReader(open(csvp)))
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
bigfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
tiles = []
for spec in want:
    tag, inst = (spec.split(":") + ["0"])[:2]; tag, inst = int(tag), int(inst)
    if tag not in pos or inst >= len(pos[tag]):
        print("missing", spec); continue
    cx, cy = pos[tag][inst]
    clip = pymupdf.Rect(cx - half, cy - half, cx + half, cy + half)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    # the pixmap of a rotated page is rendered rotated; chain coords must be mapped the same way.
    # pymupdf renders clip in unrotated space then applies rotation -> compute via page.rotation_matrix on
    # the clip rect to find the displayed origin.
    dr = ImageDraw.Draw(img)
    cr = clip * M  # displayed rect
    for r in chains:
        a = pymupdf.Point(float(r["xA"]), float(r["yA"])) * M; b = pymupdf.Point(float(r["xB"]), float(r["yB"])) * M
        if not (cr.x0 - 5 <= a.x <= cr.x1 + 5 and cr.y0 - 5 <= a.y <= cr.y1 + 5) and not (cr.x0 - 5 <= b.x <= cr.x1 + 5 and cr.y0 - 5 <= b.y <= cr.y1 + 5):
            continue
        ax, ay = (a.x - cr.x0) * sc, (a.y - cr.y0) * sc; bx, by = (b.x - cr.x0) * sc, (b.y - cr.y0) * sc
        dr.line([(ax, ay), (bx, by)], fill=(255, 0, 0), width=2)
        dr.text(((ax + bx) / 2 + 2, (ay + by) / 2 + 2), f"{r['id']}:{r['len_ft']}", fill=(0, 0, 220), font=font)
    dr.rectangle([0, 0, 150, 34], fill=(255, 255, 160)); dr.text((4, 4), f"KN{tag}#{inst}", fill=(0, 0, 0), font=bigfont)
    tiles.append(img)
if not tiles: sys.exit("no tiles")
tw, th = tiles[0].size; rows = (len(tiles) + cols - 1) // cols
grid = Image.new("RGB", (cols * tw, rows * th), (255, 255, 255))
for i, t in enumerate(tiles): grid.paste(t, ((i % cols) * tw, (i // cols) * th))
grid.save(out, quality=85); print(out, grid.size, "tiles", len(tiles))
