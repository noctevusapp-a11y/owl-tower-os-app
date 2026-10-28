#!/usr/bin/env python3
"""Full-sheet overlay in display orientation (no clip): render the whole page
with pymupdf at <dpi>, then draw (a) paired demo walls (green, W<id>:<ft>),
(b) unpaired dashed chains >= 2 ft (red, <id>), (c) keynote tag positions from
the text layer (yellow box, KN<n>) using page.rotation_matrix. Then crop the
quadrants with PIL. The keynote boxes landing on the drawn tag circles is the
visual check that the coordinate mapping is right.

usage: sheet_overlay.py <pdf> <page> <walls_csv> <singles_csv> <out_prefix> [dpi]
"""
import sys, csv, re
import pymupdf
from PIL import Image, ImageDraw, ImageFont

pdf, pno, wcsv, scsv, pref = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
dpi = int(sys.argv[6]) if len(sys.argv) > 6 else 120
page = pymupdf.open(pdf)[pno - 1]; M = page.rotation_matrix; sc = dpi / 72.0
pix = page.get_pixmap(dpi=dpi); img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
print("render", img.size, "page.rect", page.rect, "rot", page.rotation)
dr = ImageDraw.Draw(img)
f14 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
f18 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
def P(x, y):
    p = pymupdf.Point(float(x), float(y)) * M; return p.x * sc, p.y * sc
for r in csv.DictReader(open(scsv)):
    if float(r["len_ft"]) < 2: continue
    a = P(r["xA"], r["yA"]); b = P(r["xB"], r["yB"])
    dr.line([a, b], fill=(255, 0, 0), width=2); dr.text(((a[0] + b[0]) / 2 + 2, (a[1] + b[1]) / 2 + 1), r["id"], fill=(200, 0, 0), font=f14)
for r in csv.DictReader(open(wcsv)):
    a = P(r["xA"], r["yA"]); b = P(r["xB"], r["yB"])
    dr.line([a, b], fill=(0, 150, 0), width=4); dr.text(((a[0] + b[0]) / 2 + 3, (a[1] + b[1]) / 2 + 3), "W" + r["wall"] + ":" + r["faceA_ft"], fill=(0, 110, 0), font=f14)
for w in page.get_text("words"):
    x0, y0, x1, y1, t = w[:5]
    if re.fullmatch(r"\d{1,2}", t) and y0 < 1980 and x0 >= 100:
        x, y = P((x0 + x1) / 2, (y0 + y1) / 2)
        dr.rectangle([x + 8, y - 22, x + 52, y - 2], fill=(255, 255, 120)); dr.text((x + 10, y - 21), "KN" + t, fill=(0, 0, 0), font=f18)
W, H = img.size
# plan area only (exclude keynote column): x < 0.80 W
boxes = {"q00": (0, 0, int(W * 0.42), int(H * 0.52)), "q01": (int(W * 0.40), 0, int(W * 0.80), int(H * 0.52)),
         "q10": (0, int(H * 0.48), int(W * 0.42), H), "q11": (int(W * 0.40), int(H * 0.48), int(W * 0.80), H)}
for k, b in boxes.items():
    img.crop(b).save(f"{pref}_{k}.jpg", quality=85); print(k, b)
img.save(f"{pref}_full.jpg", quality=80)
