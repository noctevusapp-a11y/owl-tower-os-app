#!/usr/bin/env python3
"""Build dashed polylines ("chains") from the heavy dashed demo linework on
A-1.10 / A-1.20 (03_Architectural_Plans_Demo_RCP.pdf pages 2-3) and measure
their end-to-end length in feet.

Scale calibration: 3/16" = 1'-0" -> 13.5 pt/ft, verified on the drawing
("4'" dimension line on page 3 = 54.0 pt; "21'-9 1/2"" on page 4 = 294.3 pt).

Method: take every black stroke of width 0.24-0.36 pt whose straight segments
are 12..30 pt long (the demo dashes are 15-22 pt long, drawn as separate
segments by the CAD plot driver), group the
segments that are collinear (same angle within 2 deg, perpendicular offset
< 1.2 pt) and chain them where the gap between consecutive dashes is < GAP pt.
A chain's length is measured from the first dash start to the last dash end
(gaps included), i.e. the drawn length of the dashed line.

usage: demo_chains.py <pdf> <page> <out_csv> <overlay_png> [render_dpi]
"""
import sys, math, csv
import pymupdf
from PIL import Image, ImageDraw, ImageFont

PT_PER_FT = 13.5
GAP = 14.0
pdf, pno, out_csv, out_png = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
dpi = float(sys.argv[5]) if len(sys.argv) > 5 else 150.0

doc = pymupdf.open(pdf)
page = doc[pno - 1]
segs = []
for d in page.get_drawings():
    if d.get("type") != "s" or str(d.get("color")) != "(0.0, 0.0, 0.0)":
        continue
    if round(d.get("width") or 0, 2) not in (0.24, 0.3, 0.36):
        continue
    for it in d["items"]:
        if it[0] != "l":
            continue
        p1, p2 = it[1], it[2]
        L = math.hypot(p1.x - p2.x, p1.y - p2.y)
        if 12 <= L <= 30:
            segs.append(((p1.x, p1.y), (p2.x, p2.y), L))

# normalise direction so angle in [0,180)
def norm(s):
    (x1, y1), (x2, y2), L = s
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
    if ang > 179.0:
        ang -= 180.0
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    # perpendicular offset c = -uy*x + ux*y (constant along the line)
    c = -uy * x1 + ux * y1
    t1, t2 = ux * x1 + uy * y1, ux * x2 + uy * y2
    return ang, c, min(t1, t2), max(t1, t2), (x1, y1), (x2, y2)

items = [norm(s) for s in segs]
# group by angle bucket and offset
items.sort(key=lambda r: (round(r[0] / 2.0), r[1], r[2]))
chains = []
cur = []
def flush():
    if cur:
        chains.append(list(cur))
for r in items:
    if cur:
        a0, c0, _, tprev_end = cur[-1][0], cur[-1][1], cur[-1][2], cur[-1][3]
        same = abs(((r[0] - a0 + 90) % 180) - 90) <= 2.0 and abs(r[1] - c0) < 1.2 and (r[2] - tprev_end) < GAP and (r[2] - tprev_end) > -2
        if not same:
            flush(); cur = []
    cur.append(r)
flush()

rows = []
for i, ch in enumerate(chains):
    n = len(ch)
    t0 = min(r[2] for r in ch); t1 = max(r[3] for r in ch)
    L = t1 - t0
    ang = ch[0][0]
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    c = ch[0][1]
    # endpoints in page coords: x = ux*t - uy*c ; y = uy*t + ux*c
    xA, yA = ux * t0 - uy * c, uy * t0 + ux * c
    xB, yB = ux * t1 - uy * c, uy * t1 + ux * c
    rows.append(dict(id=i, n_dashes=n, len_pt=round(L, 1), len_ft=round(L / PT_PER_FT, 2), ang=round(ang, 1),
                     xA=round(xA, 1), yA=round(yA, 1), xB=round(xB, 1), yB=round(yB, 1)))
rows = [r for r in rows if r["n_dashes"] >= 2]
with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("chains with >=2 dashes:", len(rows), "total ft", round(sum(r["len_ft"] for r in rows), 1))

# overlay on a render (rotation applied)
pix = page.get_pixmap(dpi=int(dpi))
img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
dr = ImageDraw.Draw(img)
M = page.rotation_matrix
sc = dpi / 72.0
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
except Exception:
    font = ImageFont.load_default()
for r in rows:
    pA = pymupdf.Point(r["xA"], r["yA"]) * M
    pB = pymupdf.Point(r["xB"], r["yB"]) * M
    dr.line([(pA.x * sc, pA.y * sc), (pB.x * sc, pB.y * sc)], fill=(255, 0, 0), width=4)
    mx, my = (pA.x + pB.x) / 2 * sc, (pA.y + pB.y) / 2 * sc
    dr.text((mx + 3, my + 3), f"{r['id']}", fill=(0, 0, 255), font=font)
img.save(out_png)
print("overlay", out_png, img.size)
