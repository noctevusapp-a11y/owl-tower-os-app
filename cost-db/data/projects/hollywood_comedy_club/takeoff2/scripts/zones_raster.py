"""Floor / ceiling zone areas by raster flood fill on a vector plan page (A-2.10 p4, A-2.20 p5, RCPs p6/p7 of
03_Architectural_Plans_Demo_RCP.pdf, or the finish plans p6/p7 of the IFB Interior Design part01 PDF).
Same barrier logic as rooms_raster.py (wall / column / window / millwork strokes at 1 px, door leaf + swing-arc chords,
cap-to-cap chords at cased openings) but seeds and extra closing segments are given in DISPLAY points, and every seed
gets its own fill so a leak shows up as two seeds reporting the same area.
Area = pixels / (54 px/ft)^2; perimeter = outer contour length / 54 (follows door swing arcs: slight over-length).
Usage: python3 -I zones_raster.py <pdf> <page> <out_prefix> seed=NAME:x,y ... close=x0,y0,x1,y1 ... [skip=layerkey,...] [keep=railing,...] [poche=1]
"""
import sys, csv, math, pymupdf, numpy as np, cv2
from shapely.geometry import LineString
from shapely.ops import unary_union, polygonize
PT_PER_FT = 13.5; Z = 4.0; PX_PER_FT = PT_PER_FT * Z
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
seeds, closes, extra_skip = [], [], []
USE_POCHE = False; KEEP = []
for a in sys.argv[4:]:
    if a.startswith('seed='):
        nm, xy = a[5:].split(':'); seeds.append((nm, tuple(float(v) for v in xy.split(','))))
    elif a.startswith('close='): closes.append(tuple(float(v) for v in a[6:].split(',')))
    elif a.startswith('skip='): extra_skip += a[5:].split(',')
    elif a.startswith('poche='): USE_POCHE = a[6:] == '1'
    elif a.startswith('keep='): KEEP += a[5:].split(',')
p = pymupdf.open(pdf)[pn - 1]
M = p.rotation_matrix * pymupdf.Matrix(Z, Z)
W, H = int(p.rect.width * Z), int(p.rect.height * Z)
SKIP = ['poche', 'grid', 'Dimension', 'A-Note', 'A-Keynote', 'A-Symbol', 'titleblock', 'X_EQUIPF', 'Wall-Iden', 'Scope', 'GKstamp',
        'A-Text', 'pattern-floor', 'equip', 'A-GLAZ', 'KEYN', 'plumb', 'elect', 'mech', 'flr-drain', 'furn', 'bar-equipment', 'hidden',
        'HID', 'i-demo', 'ADA', 'site', 'kitchen', 'structural', 'overhead', 'light', 'door-header', 'ceiling-header', 'a-extg-ceiling',
        'a-new-ceiling', 'catwalk', 'railing'] + extra_skip
SKIP = [k for k in SKIP if k not in KEEP]
WALL = ('a-new-wall', 'i-new-wall', 'a-extg-wall', 'a-ex-wall', 'a-extg-partition', 'a-new-wall-low', 'a-extg-wall-low')
def T(q): r = q * M; return (r.x, r.y)
def segs(x):
    o = []
    for it in x['items']:
        if it[0] == 'l': o.append([T(it[1]), T(it[2])])
        elif it[0] == 'c':
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]; pts = []
            for k in range(13):
                t = k / 12; pts.append(T(p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3))
            o.append(pts)
        elif it[0] == 're':
            rr = it[1]; o.append([T(pymupdf.Point(rr.x0, rr.y0)), T(pymupdf.Point(rr.x1, rr.y0)), T(pymupdf.Point(rr.x1, rr.y1)), T(pymupdf.Point(rr.x0, rr.y1)), T(pymupdf.Point(rr.x0, rr.y0))])
        elif it[0] == 'qu':
            q = it[1]; o.append([T(q.ul), T(q.ur), T(q.lr), T(q.ll), T(q.ul)])
    return o
img = np.zeros((H, W), np.uint8)
def draw(poly):
    pts = np.array([[int(round(x)), int(round(y))] for x, y in poly], np.int32)
    cv2.polylines(img, [pts], False, 255, 1)
wall_lines = []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if any(k.lower() in L.lower() for k in SKIP): continue
    if x['type'] != 's':
        if 'door' in L.lower() and x['type'] in ('fs', 'f'):
            for s in segs(x): draw(s)
        continue
    for s in segs(x):
        draw(s)
        if any(L.endswith(w) for w in WALL):
            ls = LineString(s)
            if ls.length >= 0.2: wall_lines.append(ls)
# door chords (leaf sliver hinge->tip, arc tip->strike)
leaves, arcs = [], []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if 'door' not in L.lower(): continue
    pts = []
    for it in x['items']:
        if it[0] == 'l': pts += [T(it[1]), T(it[2])]
    if x['type'] == 'fs' and len(pts) >= 4:
        best = None
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dd = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                if best is None or dd > best[0]: best = (dd, pts[i], pts[j])
        if best and 20 * Z < best[0] < 100 * Z: leaves.append((best[1], best[2]))
    elif x['type'] == 's' and sum(1 for it in x['items'] if it[0] == 'l') >= 12:
        ls = [it for it in x['items'] if it[0] == 'l']
        a_, c_ = T(ls[0][1]), T(ls[-1][2])
        if 20 * Z < math.hypot(a_[0] - c_[0], a_[1] - c_[1]) < 140 * Z: arcs.append((a_, c_))
def near(a, b, tol=2.5 * Z): return math.hypot(a[0] - b[0], a[1] - b[1]) < tol
chords = []
for (h1, h2) in leaves:
    for (a_, c_) in arcs:
        hinge = strike = None
        if near(h1, a_): hinge, strike = h2, c_
        elif near(h1, c_): hinge, strike = h2, a_
        elif near(h2, a_): hinge, strike = h1, c_
        elif near(h2, c_): hinge, strike = h1, a_
        if hinge is not None: chords.append((hinge, strike)); break
# cap-to-cap chords between facing thin-face ends (cased openings 1'-9" .. 5'-2")
faces = []
for f in polygonize(unary_union(wall_lines)):
    A = f.area / Z / Z; P = f.length / Z
    if A < 2 or A > 30000: continue
    disc = P * P - 16 * A; t = (P - math.sqrt(disc)) / 4 if disc > 0 else 2 * A / P
    if 2.5 <= t <= 18: faces.append(f.bounds)
for i, ba in enumerate(faces):
    for j, bb in enumerate(faces):
        if j <= i: continue
        ax0, ay0, ax1, ay1 = ba; bx0, by0, bx1, by1 = bb
        oy = min(ay1, by1) - max(ay0, by0); ox = min(ax1, bx1) - max(ax0, bx0)
        if oy > 0.6 * min(ay1 - ay0, by1 - by0) and ox < 0 and (ay1 - ay0) <= 18 * Z and (by1 - by0) <= 18 * Z and 20 * Z <= -ox <= 88 * Z:
            y = (max(ay0, by0) + min(ay1, by1)) / 2; xa, xb = (ax1, bx0) if ax1 < bx0 else (bx1, ax0); chords.append(((xa, y), (xb, y)))
        if ox > 0.6 * min(ax1 - ax0, bx1 - bx0) and oy < 0 and (ax1 - ax0) <= 18 * Z and (bx1 - bx0) <= 18 * Z and 20 * Z <= -oy <= 88 * Z:
            x = (max(ax0, bx0) + min(ax1, bx1)) / 2; ya, yb = (ay1, by0) if ay1 < by0 else (by1, ay0); chords.append(((x, ya), (x, yb)))
for c in chords: draw([c[0], c[1]])
for (x0, y0, x1, y1) in closes: draw([(x0 * Z, y0 * Z), (x1 * Z, y1 * Z)])
if USE_POCHE:   # gray new-wall poche (0.686 gray) as a barrier: closes the bracket gaps drawn in the new walls
    pix = p.get_pixmap(matrix=pymupdf.Matrix(Z, Z))
    rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    r_, g_, b_ = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    gray = ((r_ > 150) & (r_ < 200) & (abs(r_ - g_) < 6) & (abs(g_ - b_) < 6)).astype(np.uint8) * 255
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    img = np.maximum(img, gray[:H, :W])
img = cv2.dilate(img, np.ones((3, 3), np.uint8))
free = (img == 0).astype(np.uint8)
vis = cv2.cvtColor(255 - img, cv2.COLOR_GRAY2BGR)
for c in chords: cv2.line(vis, (int(c[0][0]), int(c[0][1])), (int(c[1][0]), int(c[1][1])), (0, 0, 255), 3)
for (x0, y0, x1, y1) in closes: cv2.line(vis, (int(x0 * Z), int(y0 * Z)), (int(x1 * Z), int(y1 * Z)), (255, 0, 255), 3)
rows = []
rng = np.random.RandomState(7)
for nm, (sx, sy) in seeds:
    seed = (int(sx * Z), int(sy * Z))
    if free[seed[1], seed[0]] == 0: rows.append((nm, 0, 0, 'seed on a line', sx, sy)); continue
    mask = np.zeros((H + 2, W + 2), np.uint8); ff = free.copy(); cv2.floodFill(ff, mask, seed, 2)
    region = (ff == 2).astype(np.uint8); a = int(region.sum())
    cnts, hier = cv2.findContours(region, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    outer = max(cnts, key=cv2.contourArea); per = cv2.arcLength(outer, True)
    bx, by, bw, bh = cv2.boundingRect(outer)
    rows.append((nm, a / PX_PER_FT ** 2, per / PX_PER_FT, f'bbox pt ({bx / Z:.0f},{by / Z:.0f})-({(bx + bw) / Z:.0f},{(by + bh) / Z:.0f})', sx, sy))
    col = [int(v) for v in rng.randint(60, 230, 3)]
    vis[region == 1] = (vis[region == 1] * 0.5 + np.array(col) * 0.5).astype(np.uint8)
    cv2.putText(vis, f'{nm} {a / PX_PER_FT ** 2:.0f}SF {per / PX_PER_FT:.0f}LF', (seed[0] + 10, seed[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
with open(f'{out}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['zone', 'area_sf', 'perim_ft', 'note', 'seed_x', 'seed_y'])
    for r in rows: w.writerow([r[0], round(r[1], 1), round(r[2], 1), r[3], r[4], r[5]])
for r in rows: print(f'{r[0]:>10} {r[1]:8.1f} SF {r[2]:7.1f} LF  {r[3]}')
cv2.imwrite(f'{out}.png', vis)
