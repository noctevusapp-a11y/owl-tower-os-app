#!/usr/bin/env python3
"""Survey the vector content of a PDF page: stroke styles (width, dash, color)
and text with positions. Used to separate demo (dashed) walls from the rest on
A-1.10 / A-1.20 of 03_Architectural_Plans_Demo_RCP.pdf.

usage: vec_survey.py <pdf> <page_1based> [--text] [--styles]
"""
import sys, collections, json
import pymupdf

pdf, pno = sys.argv[1], int(sys.argv[2])
doc = pymupdf.open(pdf)
page = doc[pno - 1]
print("page rect", page.rect, "rotation", page.rotation)
draws = page.get_drawings()
print("drawings:", len(draws))
styles = collections.Counter()
lens = collections.defaultdict(float)
for d in draws:
    key = (d.get("type"), round(d.get("width") or 0, 2), str(d.get("dashes")), str(d.get("color")))
    styles[key] += 1
    for it in d["items"]:
        if it[0] == "l":
            p1, p2 = it[1], it[2]
            lens[key] += ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
if "--styles" in sys.argv:
    for k, n in styles.most_common(60):
        print(n, k, "total len pt", round(lens[k], 1))
if "--text" in sys.argv:
    for b in page.get_text("words"):
        x0, y0, x1, y1, w = b[:5]
        print(round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1), w)
