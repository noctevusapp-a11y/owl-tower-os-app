#!/usr/bin/env python3
"""Pair the dashed chains from demo_chains.py into double-line walls.

A demo wall on A-1.10 / A-1.20 is drawn as two parallel dashed lines (wall
faces). Two chains are a wall when: same angle (within 2 deg), perpendicular
offset 3..14 pt (= 2.7..12.4 in at 13.5 pt/ft), and their extents along the
line overlap by at least 60 % of the shorter one. The wall length is the
overlap length of the two faces (centre-line length). Chains left unpaired are
reported separately (single dashed outlines: platform, booths, bar equipment,
trench lines, basement line, ...).

usage: demo_walls.py <chains_csv> <walls_csv> <singles_csv> [overlay_png_in overlay_png_out pdf page dpi]
"""
import sys, csv, math
PT_PER_FT = 13.5
chains = list(csv.DictReader(open(sys.argv[1])))
for c in chains:
    for k in ("len_pt", "len_ft", "ang", "xA", "yA", "xB", "yB"):
        c[k] = float(c[k])
    c["id"] = int(c["id"]); c["n_dashes"] = int(c["n_dashes"])
    a = math.radians(c["ang"]); ux, uy = math.cos(a), math.sin(a)
    c["u"] = (ux, uy)
    c["off"] = -uy * c["xA"] + ux * c["yA"]
    t1, t2 = ux * c["xA"] + uy * c["yA"], ux * c["xB"] + uy * c["yB"]
    c["t0"], c["t1"] = min(t1, t2), max(t1, t2)

def angdiff(a, b):
    return abs(((a - b + 90) % 180) - 90)

used = set(); walls = []
chains.sort(key=lambda c: -c["len_pt"])
for i, a in enumerate(chains):
    if a["id"] in used: continue
    best = None
    for b in chains:
        if b["id"] == a["id"] or b["id"] in used: continue
        if angdiff(a["ang"], b["ang"]) > 2.0: continue
        # offset of b measured in a's frame
        ux, uy = a["u"]
        offb = -uy * b["xA"] + ux * b["yA"]
        gap = abs(offb - a["off"])
        if not (3.0 <= gap <= 14.0): continue
        tb0, tb1 = ux * b["xA"] + uy * b["yA"], ux * b["xB"] + uy * b["yB"]
        tb0, tb1 = min(tb0, tb1), max(tb0, tb1)
        ov = min(a["t1"], tb1) - max(a["t0"], tb0)
        short = min(a["t1"] - a["t0"], tb1 - tb0)
        if ov <= 0 or ov < 0.6 * short: continue
        score = ov
        if best is None or score > best[0]:
            best = (score, b, gap, ov)
    if best:
        _, b, gap, ov = best
        used.add(a["id"]); used.add(b["id"])
        L = max(a["t1"], b["t1"] if False else a["t1"]) - a["t0"]  # face A extent
        walls.append(dict(wall=len(walls), chainA=a["id"], chainB=b["id"], thick_in=round(gap / PT_PER_FT * 12, 1),
                          faceA_ft=round(a["len_ft"], 2), faceB_ft=round(b["len_ft"], 2), overlap_ft=round(ov / PT_PER_FT, 2),
                          ang=a["ang"], xA=a["xA"], yA=a["yA"], xB=a["xB"], yB=a["yB"]))
singles = [c for c in chains if c["id"] not in used]
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(walls[0].keys())); w.writeheader(); w.writerows(walls)
with open(sys.argv[3], "w", newline="") as f:
    keys = ["id", "n_dashes", "len_pt", "len_ft", "ang", "xA", "yA", "xB", "yB"]
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
    for c in singles: w.writerow({k: c[k] for k in keys})
print("walls", len(walls), "sum faceA ft", round(sum(w["faceA_ft"] for w in walls), 1), "singles", len(singles), "sum ft", round(sum(c["len_ft"] for c in singles), 1))

if len(sys.argv) > 8:
    import pymupdf
    from PIL import Image, ImageDraw, ImageFont
    pdf, pno, dpi = sys.argv[6], int(sys.argv[7]), int(sys.argv[8])
    page = pymupdf.open(pdf)[pno - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    dr = ImageDraw.Draw(img); M = page.rotation_matrix; sc = dpi / 72.0
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    for w in walls:
        pA = pymupdf.Point(w["xA"], w["yA"]) * M; pB = pymupdf.Point(w["xB"], w["yB"]) * M
        dr.line([(pA.x * sc, pA.y * sc), (pB.x * sc, pB.y * sc)], fill=(0, 160, 0), width=5)
        dr.text(((pA.x + pB.x) / 2 * sc + 3, (pA.y + pB.y) / 2 * sc + 3), f"W{w['wall']}", fill=(0, 110, 0), font=font)
    for c in singles:
        pA = pymupdf.Point(c["xA"], c["yA"]) * M; pB = pymupdf.Point(c["xB"], c["yB"]) * M
        dr.line([(pA.x * sc, pA.y * sc), (pB.x * sc, pB.y * sc)], fill=(255, 0, 0), width=3)
        dr.text(((pA.x + pB.x) / 2 * sc + 3, (pA.y + pB.y) / 2 * sc + 3), f"{c['id']}", fill=(0, 0, 255), font=font)
    img.save(sys.argv[5]); print("overlay", sys.argv[5])
