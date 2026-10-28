"""New-wall takeoff from the vector plans A-2.10 (p4) and A-2.20 (p5) of
/tmp/claude-0/hollywood/03_Architectural_Plans_Demo_RCP.pdf (Kelly Architects, Issued for Bid 9/9/2026).

Method
1. Every CAD stroke of the plan (walls, doors, columns, millwork; annotation/hatch/grid layers skipped) is
   noded and polygonized with shapely -> closed faces.
2. A face is a new-wall run when it is thin (equivalent rectangle thickness <= 13 pt = 11.5 in at 3/16"=1'-0")
   and either (a) >= 55 % of its interior renders as the solid gray wall poche (legend "New wall"), or
   (b) >= 60 % of its boundary lies on the CAD layers *a-new-wall / i-new-wall / a-new-wall-low.
3. Per run: thickness t = (P - sqrt(P^2 - 16A))/4, centerline length = A/t, wall-type tag from the nearest
   'A-Wall-Iden' tick whose tag text ('1','2','3','5','1A','AC','E', 8.8 pt font) is within 40 pt; untagged
   runs inherit the tag of a touching run of the same thickness (chained walls split at doors/intersections).
   Hatch count = number of dark (0.2 gray) 'a-poche' cross-hatch strokes inside the face (legend: cross-hatch =
   "New full height wall to ceiling with 400S162-54 @ 16" o.c."); 0 = plain "New wall".
4. Scale: 13.5 pt/ft, calibrated by calibrate_scale.py against 32 (p4) / 31 (p5) printed dimension strings.
5. Writes wall_runs_p<N>.csv and an overlay PNG; uncovered gray poche blobs are listed so nothing is dropped
   silently. An exclusion box (unrotated PDF pt) removes the 1704 N Vine exit-stair scope (separate permit).
Usage: python3 -I wall_runs.py <pdf> <page> <outdir> [x0,y0,x1,y1 ...]
"""
import sys, math, csv, fitz, numpy as np, cv2
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union, polygonize
from PIL import Image, ImageDraw
PT_PER_FT = 13.5
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
excl = [tuple(float(v) for v in a.split(',')) for a in sys.argv[4:] if a != '-']
d = fitz.open(pdf); p = d[pn-1]
Z = 3.0
M = p.rotation_matrix * fitz.Matrix(Z, Z)      # unrotated drawing coords -> rendered pixel coords
Minv = ~M
pix = p.get_pixmap(matrix=fitz.Matrix(Z, Z))
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
r, g, b = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
gray = ((r > 150) & (r < 200) & (abs(r-g) < 6) & (abs(g-b) < 6)).astype(np.uint8)
gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
def to_px(pt):
    q = fitz.Point(pt) * M; return (q.x, q.y)
for (x0, y0, x1, y1) in excl:
    qs = [to_px((x, y)) for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    cv2.fillPoly(gray, np.array([[[int(q[0]), int(q[1])] for q in qs]], dtype=np.int32), 0)
H, W = gray.shape
SKIP = ('poche', 'grid', 'Dimension', 'A-Note', 'A-Keynote', 'A-Symbol', 'titleblock', 'X_EQUIPF', 'Wall-Iden',
        'Scope', 'GKstamp', 'A-Text', 'pattern-floor', 'equip', 'A-GLAZ', 'KEYN', 'plumb', 'elect', 'mech',
        'flr-drain', 'catwalk', 'furn', 'bar-equipment', 'hidden', 'HID', 'site', 'i-demo', 'ADA')
def segs(x):
    o = []
    for it in x['items']:
        if it[0] == 'l': o.append([(it[1].x, it[1].y), (it[2].x, it[2].y)])
        elif it[0] == 'c':
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]; pts = [p0]
            for k in range(1, 13):
                t = k/12; pts.append(p0*(1-t)**3 + p1*3*t*(1-t)**2 + p2*3*t*t*(1-t) + p3*t**3)
            o.append([(q.x, q.y) for q in pts])
        elif it[0] == 're':
            rr = it[1]; o.append([(rr.x0, rr.y0), (rr.x1, rr.y0), (rr.x1, rr.y1), (rr.x0, rr.y1), (rr.x0, rr.y0)])
        elif it[0] == 'qu':
            q = it[1]; o.append([(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y), (q.ul.x, q.ul.y)])
    return o
lines, newlines, ticks, hatch = [], [], [], []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if L == 'A-Wall-Iden' and x['type'] == 'fs':
        rr = x['rect']; ticks.append(((rr.x0+rr.x1)/2, (rr.y0+rr.y1)/2)); continue
    if L.endswith('a-poche') and x['type'] == 's' and x.get('color') and abs(x['color'][0]-0.2) < 0.05:
        # dark 0.2-gray strokes on a-poche = the cross-hatch of 'New full height wall to ceiling' (legend)
        for s in segs(x):
            if len(s) >= 2 and math.hypot(s[0][0]-s[-1][0], s[0][1]-s[-1][1]) > 2:
                hatch.append(((s[0][0]+s[-1][0])/2, (s[0][1]+s[-1][1])/2))
        continue
    if any(k.lower() in L.lower() for k in SKIP): continue
    if x['type'] != 's': continue
    for s in segs(x):
        ls = LineString(s)
        if ls.length < 0.05: continue
        lines.append(ls)
        if 'new-wall' in L: newlines.append(ls)
faces = list(polygonize(unary_union(lines)))
newu = unary_union(newlines).buffer(0.35)
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
from shapely.strtree import STRtree
hatch_pts = [Point(h) for h in hatch]
htree = STRtree(hatch_pts) if hatch_pts else None
def face_cov(f):
    bx0, by0, bx1, by1 = f.bounds
    cs = [to_px(c) for c in [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]]
    px0 = max(0, int(min(c[0] for c in cs))-2); px1 = min(W, int(max(c[0] for c in cs))+3)
    py0 = max(0, int(min(c[1] for c in cs))-2); py1 = min(H, int(max(c[1] for c in cs))+3)
    if px1 <= px0 or py1 <= py0: return 0.0, None
    sub = gray[py0:py1, px0:px1]
    m = np.zeros_like(sub)
    pts = np.array([[[int(round(q[0]))-px0, int(round(q[1]))-py0] for q in (to_px(c) for c in f.exterior.coords)]], dtype=np.int32)
    cv2.fillPoly(m, pts, 1); m = cv2.erode(m, np.ones((3, 3), np.uint8))
    n = m.sum()
    return ((sub & m).sum()/n if n else 0.0), (py0, px0, m)
kept = []; covered = np.zeros_like(gray)
for f in faces:
    A = f.area
    if A < 2 or A > 25000: continue
    P = f.length; disc = P*P - 16*A
    t = (P - math.sqrt(disc))/4 if disc > 0 else 2*A/P
    if t > 13 or t < 0.8: continue
    share = f.exterior.intersection(newu).length / f.exterior.length
    if share < 0.3: continue  # cheap pre-filter; raster test below decides the rest
    cov, mk = face_cov(f)
    if cov < 0.55 and share < 0.6: continue
    nh = len(htree.query(f, predicate='contains')) if htree else 0
    tg = '?'; td = None
    for tk in ticks:
        dd = f.distance(Point(tk))
        if dd < 2.5 and (td is None or dd < td): td = dd; tg = tick_tag(tk)
    kept.append([f, t, A, cov, share, tg, nh])
    if mk:
        py0, px0, m = mk; covered[py0:py0+m.shape[0], px0:px0+m.shape[1]] |= m
# raster-only pass for gray faces whose boundary is mostly existing-wall lines (share < 0.3)
for f in faces:
    A = f.area
    if A < 2 or A > 25000: continue
    P = f.length; disc = P*P - 16*A
    t = (P - math.sqrt(disc))/4 if disc > 0 else 2*A/P
    if t > 13 or t < 0.8: continue
    share = f.exterior.intersection(newu).length / f.exterior.length
    if share >= 0.3: continue
    cov, mk = face_cov(f)
    if cov < 0.75: continue
    nh = len(htree.query(f, predicate='contains')) if htree else 0
    tg = '?'; td = None
    for tk in ticks:
        dd = f.distance(Point(tk))
        if dd < 2.5 and (td is None or dd < td): td = dd; tg = tick_tag(tk)
    kept.append([f, t, A, cov, share, tg, nh])
    if mk:
        py0, px0, m = mk; covered[py0:py0+m.shape[0], px0:px0+m.shape[1]] |= m
# tag propagation along touching runs of similar thickness
changed = True
while changed:
    changed = False
    for k in kept:
        if k[5] != '?': continue
        for k2 in kept:
            if k2[5] == '?' or k2 is k: continue
            if abs(k2[1]-k[1]) < 1.2 and k[0].distance(k2[0]) < 1.0:
                k[5] = k2[5] + '*'; changed = True; break
kept.sort(key=lambda k: (round(k[0].centroid.y/40), k[0].centroid.x))
print("tick report (tag, tick xy, nearest face id, distance):")
for tk in ticks:
    best = None
    for i, k in enumerate(kept):
        dd = k[0].distance(Point(tk))
        if best is None or dd < best[0]: best = (dd, i)
    print(f"   {tick_tag(tk):>3} at ({tk[0]:.0f},{tk[1]:.0f}) -> face {best[1]} d={best[0]:.1f}")
unc = (gray.astype(bool) & ~covered.astype(bool)).astype(np.uint8)
unc = cv2.morphologyEx(unc, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
nlab, lab, stats, cents = cv2.connectedComponentsWithStats(unc)
tot = sum(k[2]/k[1] for k in kept)/PT_PER_FT
print(f"page {pn}: faces {len(faces)}, kept {len(kept)}, centerline total {tot:.1f} ft, gray px {gray.sum()}, covered {(gray & covered).sum()}")
unc_rows = []
for i in range(1, nlab):
    if stats[i, cv2.CC_STAT_AREA] > 300:
        c = fitz.Point(cents[i][0], cents[i][1]) * Minv
        if c.x < 230: continue  # legend swatches
        unc_rows.append((i, stats[i, cv2.CC_STAT_AREA], c.x, c.y))
print("uncovered gray blobs:", [(i, n, round(x), round(y)) for i, n, x, y in unc_rows])
with open(f'{out}/wall_runs_p{pn}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['id', 'page', 'tag', 'thick_in', 'len_ft', 'hatch', 'cov', 'newshare', 'cx', 'cy', 'x0', 'y0', 'x1', 'y1'])
    for i, (f, t, A, cov, share, tg, nh) in enumerate(kept):
        bb = f.bounds; c = f.centroid
        w.writerow([i, pn, tg, round(t/PT_PER_FT*12, 2), round(A/t/PT_PER_FT, 2), nh, round(cov, 2), round(share, 2), round(c.x, 1), round(c.y, 1)] + [round(v, 1) for v in bb])
im = Image.fromarray(img).convert('RGBA'); ov = Image.new('RGBA', im.size, (255, 255, 255, 0)); dr = ImageDraw.Draw(ov)
COL = {'1': (255, 0, 0), '2': (0, 160, 0), '3': (0, 0, 255), '5': (255, 0, 255), '1A': (255, 128, 0), 'AC': (0, 180, 180), 'E': (120, 120, 120), '?': (0, 0, 0)}
for i, (f, t, A, cov, share, tg, nh) in enumerate(kept):
    col = COL[tg.rstrip('*')]
    pts = [to_px(c) for c in f.exterior.coords]
    dr.polygon(pts, fill=col+(110,), outline=col+(255,))
    c = to_px((f.centroid.x, f.centroid.y)); dr.text((c[0]+3, c[1]-6), f"{i}", fill=(0, 0, 0, 255))
for i, n, x, y in unc_rows:
    c = to_px((x, y)); dr.ellipse((c[0]-20, c[1]-20, c[0]+20, c[1]+20), outline=(255, 0, 0, 255), width=3); dr.text((c[0]+22, c[1]-6), f"U{i}", fill=(255, 0, 0, 255))
Image.alpha_composite(im, ov).convert('RGB').save(f'{out}/wall_runs_p{pn}.png')
print('wrote', f'{out}/wall_runs_p{pn}.png')
