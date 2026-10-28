"""New-wall runs from the solid wall poche of A-2.10 (p4) / A-2.20 (p5), 03_Architectural_Plans_Demo_RCP.pdf.
1. The new-wall footprint = union of the gray (0.686) solid-hatch triangles on the '*|a-poche' / '*|i-new-poche'
   layers (legend: solid gray = new wall). Exclusion boxes drop the 1704 N Vine exit-stair scope.
2. Each footprint polygon is rasterised (4 px/pt) and decomposed into straight runs: horizontal runs = morphological
   opening with a horizontal line kernel (3 x wall thickness), vertical runs = opening of the remainder with a
   vertical kernel; what is left (curved / diagonal walls, short stubs) is measured as area / thickness.
3. Run length = bbox length of the run component (horizontal: width, vertical: height) in pt / 13.5 pt per ft
   (scale 3/16" = 1'-0", calibrated by calibrate_scale.py on 32 / 31 printed dimension strings).
   Thickness = component area / length. Corner overlap is avoided by removing horizontal runs before the vertical pass.
4. Wall type = text of the 'A-Wall-Iden' tag tick(s) lying on the run ('1','1A','2','3','5','AC'; 8.8 pt text within
   40 pt of the tick). Hatch = count of dark (0.2 gray) 'a-poche' cross-hatch strokes inside the run (legend:
   cross-hatch = 'New full height wall to ceiling with 400S162-54 @ 16" o.c. studs'); 0 = plain 'New wall'.
Usage: python3 -I poche_runs.py <pdf> <page> <outdir> [x0,y0,x1,y1 ...]"""
import sys, math, csv, fitz, numpy as np, cv2
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
PT_PER_FT = 13.5; Z = 4.0
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
excl = [box(*[float(v) for v in a.split(',')]) for a in sys.argv[4:]]
d = fitz.open(pdf); p = d[pn-1]
W, H = int(p.mediabox.width*Z), int(p.mediabox.height*Z)
tris, hatch, ticks = [], [], []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if L == 'A-Wall-Iden' and x['type'] == 'fs':
        rr = x['rect']; ticks.append(((rr.x0+rr.x1)/2, (rr.y0+rr.y1)/2)); continue
    if 'poche' not in L: continue
    if L.endswith('a-poche') and x['type'] == 's' and x.get('color') and abs(x['color'][0]-0.2) < 0.05:
        for it in x['items']:
            if it[0] == 'l' and abs(it[1]-it[2]) > 2: hatch.append(((it[1].x+it[2].x)/2, (it[1].y+it[2].y)/2))
        continue
    if x['type'] != 'fs' or x.get('fill') is None or abs(x['fill'][0]-0.686) > 0.02: continue
    pts = []
    for it in x['items']:
        if it[0] == 'l': pts.append((it[1].x, it[1].y)); pts.append((it[2].x, it[2].y))
    for k in range(0, len(pts), 6):
        uniq = []
        for q in pts[k:k+6]:
            if all(abs(q[0]-u[0]) > 1e-6 or abs(q[1]-u[1]) > 1e-6 for u in uniq): uniq.append(q)
        if len(uniq) >= 3:
            pg = Polygon(uniq[:3])
            if pg.is_valid and pg.area > 0: tris.append(pg)
U = unary_union(tris)
for e in excl: U = U.difference(e)
polys = [g for g in (U.geoms if U.geom_type == 'MultiPolygon' else [U]) if g.area > 1]
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
tick_tags = [(tk, tick_tag(tk)) for tk in ticks]
runs = []
for pi, pg in enumerate(polys):
    A = pg.area; P = pg.exterior.length; disc = P*P-16*A
    t = (P-math.sqrt(disc))/4 if disc > 0 else 2*A/P
    if t < 1.5: continue   # sliver / line artefact
    tpx = max(4, int(round(t*Z)))
    mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mask, [np.array([[int(round(x*Z)), int(round(y*Z))] for x, y in pg.exterior.coords], np.int32)], 1)
    for ring in pg.interiors:
        cv2.fillPoly(mask, [np.array([[int(round(x*Z)), int(round(y*Z))] for x, y in ring.coords], np.int32)], 0)
    kl = int(3*tpx)
    hmask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((1, kl), np.uint8))
    rest = mask & ~hmask
    vmask = cv2.morphologyEx(rest, cv2.MORPH_OPEN, np.ones((kl, 1), np.uint8))
    resid = rest & ~vmask
    def comps(m, kind):
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        for i in range(1, n):
            x0, y0, w, h, a = st[i]
            if a < 4*tpx*tpx*0.5: continue
            if kind == 'H': L = w/Z; th = a/w/Z
            elif kind == 'V': L = h/Z; th = a/h/Z
            else: th = t; L = (a/Z/Z)/th
            comp = (lab == i)
            bx = (x0/Z, y0/Z, (x0+w)/Z, (y0+h)/Z)
            tk = sorted(set(tg for (c, tg) in tick_tags if bx[0]-3 <= c[0] <= bx[2]+3 and bx[1]-3 <= c[1] <= bx[3]+3 and comp[min(H-1, max(0, int(c[1]*Z))), min(W-1, max(0, int(c[0]*Z)))] or
                            (bx[0]-3 <= c[0] <= bx[2]+3 and bx[1]-3 <= c[1] <= bx[3]+3 and cv2.dilate(comp.astype(np.uint8), np.ones((9, 9), np.uint8))[min(H-1, max(0, int(c[1]*Z))), min(W-1, max(0, int(c[0]*Z)))])))
            nh = sum(1 for (hx, hy) in hatch if bx[0] <= hx <= bx[2] and bx[1] <= hy <= bx[3] and comp[min(H-1, max(0, int(hy*Z))), min(W-1, max(0, int(hx*Z)))])
            runs.append(dict(poly=pi, kind=kind, len_ft=L/PT_PER_FT, thick_in=th/PT_PER_FT*12, tags='/'.join(tk), hatch=nh,
                             cx=(bx[0]+bx[2])/2, cy=(bx[1]+bx[3])/2, x0=bx[0], y0=bx[1], x1=bx[2], y1=bx[3]))
    comps(hmask, 'H'); comps(vmask, 'V'); comps(resid, 'R')
runs.sort(key=lambda r: (r['poly'], r['kind'], r['cy'], r['cx']))
tot = sum(r['len_ft'] for r in runs)
print(f"page {pn}: {len(polys)} polygons, {len(runs)} runs, total {tot:.1f} LF; by kind:", {k: round(sum(r['len_ft'] for r in runs if r['kind'] == k), 1) for k in 'HVR'})
with open(f'{out}/poche_runs_p{pn}.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['id', 'poly', 'kind', 'len_ft', 'thick_in', 'tags', 'hatch', 'cx', 'cy', 'x0', 'y0', 'x1', 'y1'])
    w.writeheader()
    for i, r in enumerate(runs):
        rr = dict(id=i, **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}); w.writerow(rr)
for i, r in enumerate(runs):
    print(f"  {i:>3} P{r['poly']:<2} {r['kind']} len={r['len_ft']:6.2f} t={r['thick_in']:5.2f} tags={r['tags']:<6} hatch={r['hatch']:>3} c=({r['cx']:.0f},{r['cy']:.0f})")
# overlay
M = p.rotation_matrix*fitz.Matrix(3, 3)
pix = p.get_pixmap(matrix=fitz.Matrix(3, 3))
from PIL import Image, ImageDraw
im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples).convert('RGBA'); ov = Image.new('RGBA', im.size, (255, 255, 255, 0)); dr = ImageDraw.Draw(ov)
def T(pt): q = fitz.Point(pt)*M; return (q.x, q.y)
COL = {'H': (255, 0, 0), 'V': (0, 0, 255), 'R': (0, 160, 0)}
for i, r in enumerate(runs):
    pts = [T((r['x0'], r['y0'])), T((r['x1'], r['y0'])), T((r['x1'], r['y1'])), T((r['x0'], r['y1']))]
    dr.rectangle([min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts)], outline=COL[r['kind']]+(255,), width=2)
    c = T((r['cx'], r['cy'])); dr.rectangle([c[0]-2, c[1]-7, c[0]+46, c[1]+7], fill=(255, 255, 200, 230)); dr.text((c[0], c[1]-6), f"{i}:{r['tags'] or '?'}{'#' if r['hatch'] else ''}", fill=(0, 0, 0, 255))
Image.alpha_composite(im, ov).convert('RGB').save(f'{out}/poche_runs_p{pn}.png')
