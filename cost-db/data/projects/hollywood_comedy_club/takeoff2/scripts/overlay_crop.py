#!/usr/bin/env python3
"""Render a region of a PDF page with the dashed chains (from demo_chains.py
csv) drawn and labelled by id, for manual identification of demo walls.

usage: overlay_crop.py <pdf> <page> <chains_csv> <out_jpg> X0 Y0 X1 Y1 [dpi]
X/Y are in rotated (as-displayed) page points: 0..2448 x 0..1584 for the
landscape sheet.
"""
import sys, csv
import pymupdf
from PIL import Image, ImageDraw, ImageFont

pdf, pno, csvp, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
X0, Y0, X1, Y1 = map(float, sys.argv[5:9])
dpi = int(sys.argv[9]) if len(sys.argv) > 9 else 150
page = pymupdf.open(pdf)[pno - 1]
M = page.rotation_matrix
sc = dpi / 72.0
# clip is given in unrotated coords: invert the rotation matrix
Minv = ~M
pA = pymupdf.Point(X0, Y0) * Minv; pB = pymupdf.Point(X1, Y1) * Minv
clip = pymupdf.Rect(min(pA.x, pB.x), min(pA.y, pB.y), max(pA.x, pB.x), max(pA.y, pB.y))
pix = page.get_pixmap(dpi=dpi, clip=clip)
img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
dr = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
for r in csv.DictReader(open(csvp)):
    a = pymupdf.Point(float(r["xA"]), float(r["yA"])) * M
    b = pymupdf.Point(float(r["xB"]), float(r["yB"])) * M
    if not (X0 - 5 <= a.x <= X1 + 5 and Y0 - 5 <= a.y <= Y1 + 5) and not (X0 - 5 <= b.x <= X1 + 5 and Y0 - 5 <= b.y <= Y1 + 5):
        continue
    ax, ay = (a.x - X0) * sc, (a.y - Y0) * sc; bx, by = (b.x - X0) * sc, (b.y - Y0) * sc
    dr.line([(ax, ay), (bx, by)], fill=(255, 0, 0), width=3)
    dr.text(((ax + bx) / 2 + 2, (ay + by) / 2 + 2), r["id"], fill=(0, 0, 230), font=font)
img.save(out, quality=85)
print(out, img.size)
