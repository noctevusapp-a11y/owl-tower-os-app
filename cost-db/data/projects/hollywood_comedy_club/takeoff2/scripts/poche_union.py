"""Exact vector wall-poche takeoff: the plans fill every new-wall footprint with a SOLID hatch exported as
triangle pairs on layers '*|a-poche' / '*|i-new-poche' (fill gray 0.686). Union of those triangles = new-wall
footprint polygons. Each connected polygon: thickness t=(P-sqrt(P^2-16A))/4 (exact for a rectangle),
centerline length = A/t. Hatch count = 'i-new-poche' hatch strokes inside (legend: cross-hatch = full-height
wall to ceiling). Tags from 'A-Wall-Iden' ticks on the polygon. Exclusion boxes drop the exit-stair scope.
Usage: python3 -I poche_union.py <pdf> <page> <outdir> [x0,y0,x1,y1 ...]"""
import sys, math, csv, fitz
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from PIL import Image, ImageDraw
PT_PER_FT = 13.5
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
excl = [box(*[float(v) for v in a.split(',')]) for a in sys.argv[4:] if a != '-']
d = fitz.open(pdf); p = d[pn-1]
tris, hatch, ticks = [], [], []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if L == 'A-Wall-Iden' and x['type'] == 'fs':
        rr = x['rect']; ticks.append(((rr.x0+rr.x1)/2, (rr.y0+rr.y1)/2)); continue
    if 'poche' not in L: continue
    if x['type'] == 's' and 'i-new-poche' in L:
        for it in x['items']:
            if it[0] == 'l': hatch.append(Point((it[1].x+it[2].x)/2, (it[1].y+it[2].y)/2))
        continue
    if x['type'] != 'fs' or x.get('fill') is None or abs(x['fill'][0]-0.686) > 0.02: continue
    pts = []
    for it in x['items']:
        if it[0] == 'l': pts.append((it[1].x, it[1].y)); pts.append((it[2].x, it[2].y))
    # triangles: consecutive groups of 3 'l' items (6 points, 3 distinct)
    for k in range(0, len(pts), 6):
        tri = pts[k:k+6]
        uniq = []
        for q in tri:
            if all(abs(q[0]-u[0]) > 1e-6 or abs(q[1]-u[1]) > 1e-6 for u in uniq): uniq.append(q)
        if len(uniq) >= 3:
            pg = Polygon(uniq[:3])
            if pg.is_valid and pg.area > 0: tris.append(pg)
U = unary_union(tris)
for e in excl: U = U.difference(e)
polys = list(U.geoms) if U.geom_type == 'MultiPolygon' else [U]
tags = []
for bk in p.get_text('dict')['blocks']:
    for l in bk.get('lines', []):
        for s in l['spans']:
            t = s['text'].strip()
            if t in ('1', '2', '3', '5', '1A', 'AC', 'E') and abs(s['size']-8.8) < 0.3:
                tags.append((t, (s['bbox'][0]+s['bbox'][2])/2, (s['bbox'][1]+s['bbox'][3])/2))
def tick_tag(tk):
    best = None
    for t, x, y in tags:
        dd = math.hypot(x-tk[0], y-tk[1])
        if dd < 40 and (best is None or dd < best[0]): best = (dd, t)
    return best[1] if best else '?'
htree = STRtree(hatch) if hatch else None
rows = []
for i, pg in enumerate(sorted(polys, key=lambda g: (-g.area))):
    A = pg.area; P = pg.exterior.length
    if A < 1: continue
    disc = P*P-16*A; t = (P-math.sqrt(disc))/4 if disc > 0 else 2*A/P
    tg = sorted(set(tick_tag(tk) for tk in ticks if pg.distance(Point(tk)) < 2.5))
    nh = len(htree.query(pg, predicate='within')) if htree else 0
    c = pg.centroid
    rows.append((i, A, P, t, A/t, tg, nh, pg))
print(f"page {pn}: {len(tris)} triangles, {len(polys)} polygons, total footprint {U.area/PT_PER_FT**2:.1f} SF")
with open(f'{out}/poche_p{pn}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['id', 'area_sf', 'thick_in', 'len_ft', 'tags', 'hatch', 'cx', 'cy', 'x0', 'y0', 'x1', 'y1'])
    for i, A, P, t, L, tg, nh, pg in rows:
        bb = pg.bounds; c = pg.centroid
        w.writerow([i, round(A/PT_PER_FT**2, 2), round(t/PT_PER_FT*12, 2), round(L/PT_PER_FT, 2), '/'.join(tg), nh, round(c.x), round(c.y)] + [round(v) for v in bb])
Z = 3.0; M = p.rotation_matrix*fitz.Matrix(Z, Z)
pix = p.get_pixmap(matrix=fitz.Matrix(Z, Z)); im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples).convert('RGBA')
ov = Image.new('RGBA', im.size, (255, 255, 255, 0)); dr = ImageDraw.Draw(ov)
def T(pt): q = fitz.Point(pt)*M; return (q.x, q.y)
import random; random.seed(3)
for i, A, P, t, L, tg, nh, pg in rows:
    col = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
    dr.polygon([T(c) for c in pg.exterior.coords], fill=col+(120,), outline=col+(255,))
    for ring in pg.interiors: dr.polygon([T(c) for c in ring.coords], fill=(255, 255, 255, 0), outline=col+(255,))
    c = T((pg.centroid.x, pg.centroid.y)); dr.text((c[0]+3, c[1]-6), f"P{i}", fill=(0, 0, 0, 255))
Image.alpha_composite(im, ov).convert('RGB').save(f'{out}/poche_p{pn}.png')
