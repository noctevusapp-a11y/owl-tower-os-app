"""New-wall takeoff by raster poche on the vector plans A-2.10 (p4) / A-2.20 (p5) of
/tmp/claude-0/hollywood/03_Architectural_Plans_Demo_RCP.pdf (Kelly Architects 2604, Issued for Bid 9/9/2026).

Why raster: the legend draws every NEW wall as a solid gray poche (RGB 175 = 0.686 gray fills on layer 'a-poche') and a
NEW FULL HEIGHT WALL as the same poche with a dark cross-hatch; the curved walls are Bezier faces that polygonize badly,
so the poche itself is measured here.
Method
 1. Render the page at Z px/pt (Z=4 -> 54 px/ft at 3/16"=1'-0", 13.5 pt/ft, calibrated by calibrate_scale.py).
 2. Mask the 0.686-gray pixels (150..200, neutral), close 7x7 to bridge the hatch strokes, drop blobs < 150 px.
    Exclusion polygons (display pt) remove the 1704 N Vine exit-stair scope (separate permit) and the legend swatches.
 3. Connected component -> skeleton (skimage) -> centreline length L = skeleton px / 54 ft; thickness t = area / skeleton px.
 4. Hatch count per component = dark (0.2 gray) 'a-poche' stroke midpoints inside the component (legend: cross-hatch =
    "New full height wall to ceiling with 400S162-54 @ 16" o.c."); 0 = plain "New wall, see wall notes".
 5. Wall-type tags: 'A-Wall-Iden' tick rectangles -> nearest 8.8-pt tag text ('1','1A','2','3','5','AC','E'); a tick is
    assigned to the component whose dilated mask contains it. Components without a tick are listed for manual assignment.
 6. Day-2 poche: fills on layer '*_Day2|i-new-poche' are reported separately (their fill colour is sampled and printed).
Usage: python3 -I poche_walls.py <pdf> <page> <outdir> [excl x0,y0,x1,y1 ... in DISPLAY pt]
"""
import sys, csv, math, collections, pymupdf, numpy as np, cv2
from skimage.morphology import skeletonize
PT_PER_FT = 13.5; Z = 4.0; PX_PER_FT = PT_PER_FT * Z
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
excl = [tuple(float(v) for v in a.split(',')) for a in sys.argv[4:]]
p = pymupdf.open(pdf)[pn - 1]
M = p.rotation_matrix * pymupdf.Matrix(Z, Z)          # unrotated drawing pt -> rendered (display) px
pix = p.get_pixmap(matrix=pymupdf.Matrix(Z, Z))       # pymupdf renders in display orientation
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()
H, W = img.shape[:2]
r, g, b = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
gray = ((r > 150) & (r < 200) & (abs(r - g) < 6) & (abs(g - b) < 6)).astype(np.uint8)
def to_px(x, y):
    q = pymupdf.Point(x, y) * M; return q.x, q.y
# fill colours on the poche layers (report)
cols = collections.Counter()
for d in p.get_drawings():
    L = d.get('layer') or ''
    if 'poche' in L and d['type'] in ('f', 'fs') and d.get('fill') is not None:
        cols[(L, tuple(round(c, 3) for c in d['fill']))] += 1
print('poche fill colours:', dict(cols))
for (x0, y0, x1, y1) in excl:
    cv2.rectangle(gray, (int(x0 * Z), int(y0 * Z)), (int(x1 * Z), int(y1 * Z)), 0, -1)
gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, stats, cents = cv2.connectedComponentsWithStats(gray, connectivity=8)
# hatch strokes (dark 0.2 gray on a-poche)
hatch = []
for d in p.get_drawings():
    L = d.get('layer') or ''
    if L.endswith('a-poche') and d['type'] == 's' and d.get('color') and abs(d['color'][0] - 0.2) < 0.05:
        for it in d['items']:
            if it[0] == 'l' and abs(it[1] - it[2]) > 2:
                hatch.append(to_px((it[1].x + it[2].x) / 2, (it[1].y + it[2].y) / 2))
# wall-type ticks and tag texts
tags = []
for bk in p.get_text('dict')['blocks']:
    for l in bk.get('lines', []):
        for s in l['spans']:
            t = s['text'].strip()
            if t in ('1', '2', '3', '5', '1A', 'AC', 'E') and abs(s['size'] - 8.8) < 0.3:
                bx = s['bbox']; tags.append((t, to_px((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)))
ticks = []
for d in p.get_drawings():
    if (d.get('layer') or '') == 'A-Wall-Iden' and d['type'] == 'fs':
        rr = d['rect']; c = to_px((rr.x0 + rr.x1) / 2, (rr.y0 + rr.y1) / 2)
        best = min(tags, key=lambda t: math.hypot(t[1][0] - c[0], t[1][1] - c[1]))
        dd = math.hypot(best[1][0] - c[0], best[1][1] - c[1])
        ticks.append((best[0] if dd < 40 * Z else '?', c))
dil = cv2.dilate(lab.astype(np.int32).astype(np.float32), np.ones((9, 9), np.uint8))  # nearest label by max-dilate
rows = []
vis = img.copy()
rng = np.random.RandomState(3)
for i in range(1, n):
    a = stats[i, cv2.CC_STAT_AREA]
    if a < 150: continue
    x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
    sub = (lab[y:y + h, x:x + w] == i)
    sk = skeletonize(sub)
    # skeleton length: count 8-connected steps (diagonal = sqrt 2)
    ys, xs = np.nonzero(sk)
    pts = set(zip(ys.tolist(), xs.tolist()))
    Lpx = 0.0
    for (yy, xx) in pts:
        if (yy, xx + 1) in pts: Lpx += 1
        if (yy + 1, xx) in pts: Lpx += 1
        if (yy + 1, xx + 1) in pts and (yy, xx + 1) not in pts and (yy + 1, xx) not in pts: Lpx += math.sqrt(2)
        if (yy + 1, xx - 1) in pts and (yy, xx - 1) not in pts and (yy + 1, xx) not in pts: Lpx += math.sqrt(2)
    if Lpx < 1: continue
    t_px = a / Lpx
    nh = sum(1 for (hx, hy) in hatch if 0 <= int(hy) < H and 0 <= int(hx) < W and lab[int(hy), int(hx)] == i)
    tk = [t for (t, c) in ticks if 0 <= int(c[1]) < H and 0 <= int(c[0]) < W and int(dil[int(c[1]), int(c[0])]) == i]
    cx, cy = cents[i]
    rows.append([i, round(Lpx / PX_PER_FT, 2), round(t_px / Z / PT_PER_FT * 12, 1), nh, '+'.join(tk) if tk else '?',
                 round(cx / Z), round(cy / Z), round(x / Z), round(y / Z), round((x + w) / Z), round((y + h) / Z)])
    col = tuple(int(v) for v in rng.randint(40, 220, 3))
    vis[lab == i] = col
    cv2.putText(vis, f"{i}", (int(cx) + 6, int(cy) - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3)
    cv2.putText(vis, f"{i}", (int(cx) + 6, int(cy) - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 1)
for (t, c) in ticks:
    cv2.circle(vis, (int(c[0]), int(c[1])), 10, (255, 0, 0), 2)
    cv2.putText(vis, t, (int(c[0]) + 10, int(c[1]) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 0, 0), 2)
rows.sort(key=lambda r: (r[6] // 40, r[5]))
with open(f'{out}/poche_p{pn}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['comp', 'len_ft', 'thick_in', 'hatch', 'ticks', 'cx', 'cy', 'x0', 'y0', 'x1', 'y1'])
    w.writerows(rows)
tot = sum(r[1] for r in rows)
print(f'page {pn}: {len(rows)} components, {tot:.1f} LF total; by tick tag:')
bt = collections.defaultdict(float)
for r in rows: bt[r[4]] += r[1]
for k, v in sorted(bt.items()): print(f'   {k:>8}: {v:7.1f} LF')
cv2.imwrite(f'{out}/poche_p{pn}.png', cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
print('wrote', f'{out}/poche_p{pn}.png')
