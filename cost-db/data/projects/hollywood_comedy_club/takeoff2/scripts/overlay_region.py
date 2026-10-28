#!/usr/bin/env python3
"""Render a region of a demo-plan page with paired demo walls (green, W<id>)
and unpaired dashed chains (red, <id>) drawn, for manual identification.
usage: overlay_region.py <pdf> <page> <walls_csv> <singles_csv> <out_jpg> X0 Y0 X1 Y1 [dpi]
X/Y in rotated (as-displayed) page points (landscape 2448 x 1584)."""
import sys, csv
import pymupdf
from PIL import Image, ImageDraw, ImageFont
pdf, pno, wcsv, scsv, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
X0, Y0, X1, Y1 = map(float, sys.argv[6:10]); dpi = int(sys.argv[10]) if len(sys.argv) > 10 else 150
page = pymupdf.open(pdf)[pno - 1]; M = page.rotation_matrix; sc = dpi / 72.0; Minv = ~M
pA = pymupdf.Point(X0, Y0) * Minv; pB = pymupdf.Point(X1, Y1) * Minv
clip = pymupdf.Rect(min(pA.x, pB.x), min(pA.y, pB.y), max(pA.x, pB.x), max(pA.y, pB.y))
pix = page.get_pixmap(dpi=dpi, clip=clip); img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
dr = ImageDraw.Draw(img); font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
def draw(xa, ya, xb, yb, col, label, w):
    a = pymupdf.Point(xa, ya) * M; b = pymupdf.Point(xb, yb) * M
    if not (X0 - 5 <= a.x <= X1 + 5 and Y0 - 5 <= a.y <= Y1 + 5) and not (X0 - 5 <= b.x <= X1 + 5 and Y0 - 5 <= b.y <= Y1 + 5): return
    ax, ay = (a.x - X0) * sc, (a.y - Y0) * sc; bx, by = (b.x - X0) * sc, (b.y - Y0) * sc
    dr.line([(ax, ay), (bx, by)], fill=col, width=w); dr.text(((ax + bx) / 2 + 2, (ay + by) / 2 + 2), label, fill=col, font=font)
for r in csv.DictReader(open(scsv)): draw(float(r["xA"]), float(r["yA"]), float(r["xB"]), float(r["yB"]), (255, 0, 0), r["id"], 2)
for r in csv.DictReader(open(wcsv)): draw(float(r["xA"]), float(r["yA"]), float(r["xB"]), float(r["yB"]), (0, 150, 0), "W" + r["wall"] + ":" + r["faceA_ft"], 4)
img.save(out, quality=85); print(out, img.size)
