#!/usr/bin/env python3
"""Find closed dashed rectangles (equipment outlines, walk-ins, booths,
coffers) on a demo plan from the chains csv: two horizontal + two vertical
chains whose ends meet within TOL pt. Also sums the collinear extent of a
diagonal dashed run (the KN16 sanitary line on A-1.10) when --diag is given.

usage: demo_rects.py <chains_csv> <page_rot_matrix_pdf> <page> [--diag ANGLE_DEG]
Prints rectangles with display-space centre, size in ft, and the chain ids.
"""
import sys, csv, math
import pymupdf
TOL = 4.0; PT_PER_FT = 13.5
chains = list(csv.DictReader(open(sys.argv[1])))
page = pymupdf.open(sys.argv[2])[int(sys.argv[3]) - 1]; M = page.rotation_matrix
for c in chains:
    for k in ("len_ft", "ang", "xA", "yA", "xB", "yB"): c[k] = float(c[k])
    c["id"] = int(c["id"])
H = [c for c in chains if abs(c["ang"]) < 1 or abs(c["ang"] - 180) < 1]
V = [c for c in chains if abs(c["ang"] - 90) < 1]
def ends(c):
    return (min(c["xA"], c["xB"]), max(c["xA"], c["xB"]), min(c["yA"], c["yB"]), max(c["yA"], c["yB"]))
rects = []
for h1 in H:
    x0, x1, y, _ = ends(h1)
    for h2 in H:
        if h2["id"] <= h1["id"]: continue
        a0, a1, y2, _ = ends(h2)
        if abs(a0 - x0) > TOL or abs(a1 - x1) > TOL or abs(y2 - y) < 10: continue
        ylo, yhi = min(y, y2), max(y, y2)
        vs = [v for v in V if abs(ends(v)[2] - ylo) <= TOL and abs(ends(v)[3] - yhi) <= TOL and (abs(v["xA"] - x0) <= TOL or abs(v["xA"] - x1) <= TOL)]
        if len({round(v["xA"]) for v in vs}) >= 2:
            cx, cy = (x0 + x1) / 2, (ylo + yhi) / 2
            p = pymupdf.Point(cx, cy) * M
            w, hgt = (x1 - x0) / PT_PER_FT, (yhi - ylo) / PT_PER_FT
            rects.append((round(p.x), round(p.y), round(w, 2), round(hgt, 2), h1["id"], h2["id"], [v["id"] for v in vs]))
rects.sort()
print("closed dashed rectangles:", len(rects))
for r in rects: print("  disp(%d,%d) %.2f x %.2f ft  H%s/H%s V%s" % r)
if "--diag" in sys.argv:
    ang = float(sys.argv[sys.argv.index("--diag") + 1])
    D = [c for c in chains if abs(((c["ang"] - ang + 90) % 180) - 90) < 2.5]
    # group collinear
    groups = []
    for c in D:
        a = math.radians(c["ang"]); ux, uy = math.cos(a), math.sin(a)
        off = -uy * c["xA"] + ux * c["yA"]; t0 = ux * c["xA"] + uy * c["yA"]; t1 = ux * c["xB"] + uy * c["yB"]
        placed = False
        for g in groups:
            if abs(g["off"] - off) < 3:
                g["t"].append((min(t0, t1), max(t0, t1))); g["ids"].append(c["id"]); placed = True; break
        if not placed: groups.append({"off": off, "t": [(min(t0, t1), max(t0, t1))], "ids": [c["id"]]})
    for g in groups:
        tt = sorted(g["t"]); ext = tt[-1][1] - tt[0][0]; drawn = sum(b - a for a, b in tt)
        if ext / PT_PER_FT > 5:
            print("diag group off=%.1f extent %.2f ft (drawn dashes %.2f ft) ids %s" % (g["off"], ext / PT_PER_FT, drawn / PT_PER_FT, g["ids"]))
