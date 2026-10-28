#!/usr/bin/env python3
"""Scale calibration helper: list straight segments near a bbox (unrotated page
coordinates, points) so a dimension line can be matched to its dimension text.

usage: vec_calib.py <pdf> <page_1based> x0 y0 x1 y1 [minlen]
"""
import sys
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = map(float, sys.argv[3:7])
minlen = float(sys.argv[7]) if len(sys.argv) > 7 else 5
doc = pymupdf.open(pdf)
page = doc[pno - 1]
rows = []
for d in page.get_drawings():
    for it in d["items"]:
        if it[0] != "l":
            continue
        p1, p2 = it[1], it[2]
        if not (x0 <= p1.x <= x1 and y0 <= p1.y <= y1 and x0 <= p2.x <= x1 and y0 <= p2.y <= y1):
            continue
        L = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
        if L < minlen:
            continue
        rows.append((round(L, 2), round(p1.x, 1), round(p1.y, 1), round(p2.x, 1), round(p2.y, 1), round(d.get("width") or 0, 2), str(d.get("color"))))
rows.sort(reverse=True)
for r in rows[:40]:
    print(r)
