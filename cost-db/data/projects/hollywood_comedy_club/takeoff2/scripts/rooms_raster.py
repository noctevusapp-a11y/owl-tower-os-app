"""Room floor areas and wall-line perimeters by raster flood fill on the vector plans
A-2.10 (p4) / A-2.20 (p5) of 03_Architectural_Plans_Demo_RCP.pdf, and ceiling zones on the RCPs (p6/p7).
- Wall / column / window / storefront / millwork / railing strokes are drawn 1 px wide at 4 px/pt (54 px/ft).
- Door symbols stay as drawn (leaf + swing arc close the opening). Cased openings and door openings whose
  symbol does not close are closed by CHORDS: a wall opening is detected as a gap of 1.5 ft .. 6.5 ft between two
  collinear wall faces (new-wall poche faces and existing double-line wall faces, from polygonize); the chord is
  drawn along the wall centreline. Extra closing segments can be passed on the command line (x0,y0,x1,y1 in pt).
- Flood fill from each room label; area = pixels / 54^2 SF; perimeter = outer contour length / 54 LF.
  The perimeter follows door swing arcs where a door symbol closes the opening (slight over-length, see notes);
  door openings are NOT deducted: deduct door widths from A-7.10 separately.
Usage: python3 -I rooms_raster.py <pdf> <page> <outdir> [x0,y0,x1,y1 ...]"""
import sys, csv, math, fitz, numpy as np, cv2
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
PT_PER_FT = 13.5; Z = 4.0; PX_PER_FT = PT_PER_FT*Z
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = fitz.open(pdf); p = d[pn-1]
W, H = int(p.mediabox.width*Z), int(p.mediabox.height*Z)
SKIP = ('poche', 'grid', 'Dimension', 'A-Note', 'A-Keynote', 'A-Symbol', 'titleblock', 'X_EQUIPF', 'Wall-Iden',
        'Scope', 'GKstamp', 'A-Text', 'pattern-floor', 'equip', 'A-GLAZ', 'KEYN', 'plumb', 'elect', 'mech',
        'flr-drain', 'furn', 'bar-equipment', 'hidden', 'HID', 'i-demo', 'ADA', 'site', 'kitchen', 'structural',
        'overhead', 'light', 'a-extg-ceiling', 'door-header', 'ceiling-header')
if pn in (6, 7):   # RCPs: ceiling zone boundaries and door/window headers ARE the zone edges
    SKIP = tuple(k for k in SKIP if k not in ('a-extg-ceiling', 'door-header', 'ceiling-header', 'overhead'))
WALL = ('a-new-wall', 'i-new-wall', 'a-extg-wall', 'a-ex-wall', 'a-extg-partition', 'a-new-wall-low', 'a-extg-wall-low')
LABELS = {
 4: {'01': (513, 1727), '02': (836, 1486), '03': (384, 1732), '04': (764, 1117), '05': (384, 1424), '06': (1247, 1676),
     '07': (1031, 914), '08': (1344, 560), '09': (721, 692), '10': (652, 744), '11': (670, 1123), '12': (673, 878), '13': (722, 851)},
 5: {'21': (1074, 1017), '22': (720, 1114), '23': (720, 1177), '24': (740, 736), '25': (888, 1655), '26': (409, 1551),
     '27': (409, 1761), '28': (1206, 1655), '29': (1218, 1109), '30': (1226, 1017), '32': (847, 747), '34': (1223, 849),
     '35': (720, 958), '05': (384, 1424), '06': (1260, 1337), '10': (718, 670)},
 6: {'CLG3A_02': (898, 1475), 'CLG3A_06': (1250, 1668), 'C1D_04': (910, 1215), 'C1D_05': (367, 1337), 'C1D_01': (685, 1725),
     'C1D_03': (461, 1689), 'C1D_07': (994, 973), 'C1D_09': (739, 760), 'C1D_08': (1367, 559), 'C1A_11': (672, 1161), 'C1A_12': (652, 922),
     'C1A_13': (770, 880), 'C1D_02a': (1150, 1445), 'C1D_02b': (420, 1514), 'C1D_02c': (455, 1691), 'C1D_02d': (680, 1727), 'C1D_02e': (960, 1701),
     'C1D_02f': (1060, 1705), 'C1D_10': (658, 659)},
 7: {'SOFFIT_a': (846, 1385), 'SOFFIT_b': (967, 1344), 'SOFFIT_c': (1022, 1344), 'SOFFIT_d': (1073, 1344), 'SOFFIT_e': (737, 1344),
     'SOFFIT_f': (681, 1344), 'SOFFIT_g': (612, 1382), 'SOFFIT_h': (567, 1382), 'CLG3A_21': (1037, 920)},
}
CLOSE = [tuple(float(v) for v in a.split(',')) for a in sys.argv[4:]]
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
img = np.zeros((H, W), np.uint8)
def draw(poly, color=255):
    pts = np.array([[int(round(x*Z)), int(round(y*Z))] for x, y in poly], np.int32)
    cv2.polylines(img, [pts], False, color, 1)
wall_lines = []; leaves = []; arcs = []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if any(k.lower() in L.lower() for k in SKIP): continue
    if x['type'] != 's':
        if 'door' in L.lower() and x['type'] in ('fs', 'f'):   # door leaf drawn as a filled sliver: draw its outline
            for s in segs(x): draw(s)
        continue
    if 'door' in L.lower():
        pts = []
        for s in segs(x): pts += s
        if len(pts) >= 2:
            if len(x['items']) == 1 and x['items'][0][0] == 'l': leaves.append((pts[0], pts[-1]))
            elif len(x['items']) >= 4: arcs.append((pts[0], pts[-1]))
    for s in segs(x):
        draw(s)
        if any(L.endswith(w) for w in WALL):
            ls = LineString(s)
            if ls.length >= 0.05: wall_lines.append(ls)
# wall faces (thin faces bounded by wall lines) for the gap detector
faces = []
for f in polygonize(unary_union(wall_lines)):
    A = f.area; P = f.length
    if A < 2 or A > 30000: continue
    disc = P*P-16*A; t = (P-math.sqrt(disc))/4 if disc > 0 else 2*A/P
    if 2.5 <= t <= 18: faces.append((f.bounds, t))
chords = []
# door symbols: the leaf is a filled sliver ('fs' on a door layer) whose two extreme points are hinge and tip;
# the swing arc is a polyline whose endpoints are the tip and the strike -> chord hinge->strike closes the opening.
leaves, arcs = [], []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if 'door' not in L.lower(): continue
    pts = []
    for it in x['items']:
        if it[0] == 'l': pts += [(it[1].x, it[1].y), (it[2].x, it[2].y)]
    if x['type'] == 'fs' and len(pts) >= 4:
        best = None
        for i in range(len(pts)):
            for j in range(i+1, len(pts)):
                dd = math.hypot(pts[i][0]-pts[j][0], pts[i][1]-pts[j][1])
                if best is None or dd > best[0]: best = (dd, pts[i], pts[j])
        if best and 20 < best[0] < 100: leaves.append((best[1], best[2]))
    elif x['type'] == 's' and sum(1 for it in x['items'] if it[0] == 'l') >= 12:
        ls = [it for it in x['items'] if it[0] == 'l']
        a_, c_ = (ls[0][1].x, ls[0][1].y), (ls[-1][2].x, ls[-1][2].y)
        if 20 < math.hypot(a_[0]-c_[0], a_[1]-c_[1]) < 140: arcs.append((a_, c_))
def near(a, b, tol=2.5): return math.hypot(a[0]-b[0], a[1]-b[1]) < tol
ndoor = 0
for (h1, h2) in leaves:
    for (a_, c_) in arcs:
        hinge = strike = None
        if near(h1, a_): hinge, strike = h2, c_
        elif near(h1, c_): hinge, strike = h2, a_
        elif near(h2, a_): hinge, strike = h1, c_
        elif near(h2, c_): hinge, strike = h1, a_
        if hinge is not None:
            chords.append((hinge, strike)); ndoor += 1; break
print(f"page {pn}: door symbols closed (leaf+arc): {ndoor} of {len(leaves)} leaves / {len(arcs)} arcs")
# cased openings: wall end caps (short edges of the solid-poche footprint polygons, length ~ wall thickness)
# facing each other across a 2 ft .. 5 ft gap -> chord between cap midpoints
tris = []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if 'poche' not in L or x['type'] != 'fs' or x.get('fill') is None or abs(x['fill'][0]-0.686) > 0.02: continue
    pts = []
    for it in x['items']:
        if it[0] == 'l': pts.append((it[1].x, it[1].y)); pts.append((it[2].x, it[2].y))
    for k in range(0, len(pts), 6):
        uniq = []
        for q in pts[k:k+6]:
            if all(abs(q[0]-u[0]) > 1e-6 or abs(q[1]-u[1]) > 1e-6 for u in uniq): uniq.append(q)
        if len(uniq) >= 3:
            from shapely.geometry import Polygon
            pg = Polygon(uniq[:3])
            if pg.is_valid and pg.area > 0: tris.append(pg)
U = unary_union(tris)
caps = []
for pg in (U.geoms if U.geom_type == 'MultiPolygon' else [U]):
    if pg.area < 5: continue
    ring = list(pg.simplify(0.4).exterior.coords)
    for i in range(len(ring)-1):
        a, b = ring[i], ring[i+1]
        Lc = math.hypot(b[0]-a[0], b[1]-a[1])
        if 4 <= Lc <= 12.5:
            caps.append(((a[0]+b[0])/2, (a[1]+b[1])/2, (b[0]-a[0])/Lc, (b[1]-a[1])/Lc, Lc))
# existing walls: short a-extg-wall strokes joining the two wall lines are caps too
for x in p.get_drawings():
    L = x.get('layer') or ''
    if not (L.endswith('a-extg-wall') or L.endswith('a-extg-partition')) or x['type'] != 's': continue
    for it in x['items']:
        if it[0] == 'l':
            Lc = abs(it[1]-it[2])
            if 4 <= Lc <= 12.5:
                caps.append(((it[1].x+it[2].x)/2, (it[1].y+it[2].y)/2, (it[2].x-it[1].x)/Lc, (it[2].y-it[1].y)/Lc, Lc))
ncap = 0
for i, (x1, y1, dx1, dy1, L1) in enumerate(caps):
    for j, (x2, y2, dx2, dy2, L2) in enumerate(caps):
        if j <= i: continue
        if abs(dx1*dx2+dy1*dy2) < 0.95: continue            # caps parallel
        g = math.hypot(x2-x1, y2-y1)
        if not (24 <= g <= 70): continue                    # 1'-9" .. 5'-2" opening
        ux, uy = (x2-x1)/g, (y2-y1)/g
        if abs(ux*dx1+uy*dy1) > 0.15: continue              # connection perpendicular to the caps
        if abs(L1-L2) > 3.5: continue
        chords.append(((x1, y1), (x2, y2))); ncap += 1
print(f"page {pn}: cap-to-cap chords: {ncap} from {len(caps)} caps")
# cap -> existing column (octagon outlines on a-extg-struct) across a 1'-9" .. 5'-2" gap
cols = []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if L.endswith('a-extg-struct') and x['type'] == 's' and len(x['items']) == 8 and all(it[0] == 'l' for it in x['items']):
        rr = x['rect']
        if 10 < rr.width < 45 and abs(rr.width-rr.height) < 4:
            cols.append(Polygon([(it[1].x, it[1].y) for it in x['items']]))
ncol = 0
for (x1, y1, dx1, dy1, L1) in caps:
    P0 = Point(x1, y1)
    for cg in cols:
        g = cg.distance(P0)
        if 24 <= g <= 70:
            # direction from cap to column must be perpendicular to the cap edge
            q = cg.exterior.interpolate(cg.exterior.project(P0))
            ux, uy = (q.x-x1)/g, (q.y-y1)/g
            if abs(ux*dx1+uy*dy1) < 0.25:
                chords.append(((x1, y1), (q.x, q.y))); ncol += 1
print(f"page {pn}: cap-to-column chords: {ncol} ({len(cols)} columns)")
for i, (ba, ta) in enumerate(faces):
    for j, (bb, tb) in enumerate(faces):
        if j <= i: continue
        ax0, ay0, ax1, ay1 = ba; bx0, by0, bx1, by1 = bb
        # horizontal pair: y-ranges overlap, gap along x
        oy = min(ay1, by1) - max(ay0, by0); ox = min(ax1, bx1) - max(ax0, bx0)
        if oy > 0.6*min(ay1-ay0, by1-by0) and ox < 0 and (ay1-ay0) <= 18 and (by1-by0) <= 18:
            gap = -ox
            if 20 <= gap <= 88:
                y = (max(ay0, by0)+min(ay1, by1))/2
                xa, xb = (ax1, bx0) if ax1 < bx0 else (bx1, ax0)
                chords.append(((xa, y), (xb, y)))
        if ox > 0.6*min(ax1-ax0, bx1-bx0) and oy < 0 and (ax1-ax0) <= 18 and (bx1-bx0) <= 18:
            gap = -oy
            if 20 <= gap <= 88:
                x = (max(ax0, bx0)+min(ax1, bx1))/2
                ya, yb = (ay1, by0) if ay1 < by0 else (by1, ay0)
                chords.append(((x, ya), (x, yb)))
for c in chords: draw([c[0], c[1]])
for seg in CLOSE: draw([(seg[0], seg[1]), (seg[2], seg[3])])
print(f"page {pn}: wall faces {len(faces)}, chords {len(chords)}")
img = cv2.dilate(img, np.ones((3, 3), np.uint8))
free = (img == 0).astype(np.uint8)
rows = []
vis = cv2.cvtColor(255-img, cv2.COLOR_GRAY2BGR)
for c in chords:
    cv2.line(vis, (int(c[0][0]*Z), int(c[0][1]*Z)), (int(c[1][0]*Z), int(c[1][1]*Z)), (0, 0, 255), 3)
for tag, (lx, ly) in LABELS[pn].items():
    seed = (int(lx*Z), int(ly*Z))
    if free[seed[1], seed[0]] == 0:
        rows.append((tag, 0, 0, 0, 'seed on a line', '')); continue
    mask = np.zeros((H+2, W+2), np.uint8)
    ff = free.copy()
    cv2.floodFill(ff, mask, seed, 2)
    region = (ff == 2).astype(np.uint8)
    area_px = int(region.sum())
    cnts, hier = cv2.findContours(region, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    outer = max(cnts, key=cv2.contourArea)
    per = cv2.arcLength(outer, True)
    holes = sum(1 for i in range(len(cnts)) if hier[0][i][3] >= 0)
    bb = cv2.boundingRect(outer)
    note = 'LEAK?' if area_px/PX_PER_FT**2 > 2500 else ''
    rows.append((tag, area_px/PX_PER_FT**2, per/PX_PER_FT, holes, note, bb))
    col = (np.random.randint(60, 230), np.random.randint(60, 230), np.random.randint(60, 230))
    vis[region == 1] = (vis[region == 1]*0.5 + np.array(col)*0.5).astype(np.uint8)
    cv2.putText(vis, f"{tag} {area_px/PX_PER_FT**2:.0f}SF {per/PX_PER_FT:.0f}LF", (seed[0]+10, seed[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
with open(f'{out}/rooms_raster_p{pn}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['tag', 'area_sf', 'perim_ft', 'holes', 'note', 'bbox_px'])
    for r in rows: w.writerow([r[0], round(r[1], 1), round(r[2], 1), r[3], r[4], r[5]])
for r in rows: print(r[0], round(r[1], 1), 'SF', round(r[2], 1), 'LF', 'holes', r[3], r[4], r[5])
rot = cv2.rotate(vis, cv2.ROTATE_90_COUNTERCLOCKWISE) if p.rotation == 270 else vis
cv2.imwrite(f'{out}/rooms_raster_p{pn}.png', rot)
