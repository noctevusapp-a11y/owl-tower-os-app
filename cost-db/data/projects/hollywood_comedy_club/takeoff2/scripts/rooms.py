"""Room polygons (floor area SF, wall perimeter LF) from the vector plans A-2.10 (p4) / A-2.20 (p5) of
/tmp/claude-0/hollywood/03_Architectural_Plans_Demo_RCP.pdf (same .dwg base as the A-2.75/A-2.76 finish plans).
Every CAD stroke on wall / door / window / column / storefront / millwork layers is noded and polygonized
(shapely); the face that contains the room-name label (text on the sheet) is the room. Door leaves and swing
arcs close the door openings, so the face perimeter is the wall-line perimeter at finish face (door openings
are NOT deducted here; door widths come from A-7.10). Scale 13.5 pt/ft (calibrate_scale.py).
Usage: python3 -I rooms.py <pdf> <page> <outdir>"""
import sys, csv, fitz
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
from PIL import Image, ImageDraw
PT_PER_FT = 13.5
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = fitz.open(pdf); p = d[pn-1]
SKIP = ('poche', 'grid', 'Dimension', 'A-Note', 'A-Keynote', 'A-Symbol', 'titleblock', 'X_EQUIPF', 'Wall-Iden',
        'Scope', 'GKstamp', 'A-Text', 'pattern-floor', 'equip', 'A-GLAZ', 'KEYN', 'plumb', 'elect', 'mech',
        'flr-drain', 'furn', 'bar-equipment', 'hidden', 'HID', 'i-demo', 'ADA', 'site', 'vertcirc', 'catwalk',
        'kitchen', 'structural', 'railing', 'ceiling', 'overhead')
# a-new-structural = post symbols, a-extg-struct = columns (kept: columns are wall-like boundaries), vertcirc = stairs/lift (skip)
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
lines = []
for x in p.get_drawings():
    L = x.get('layer') or ''
    if any(k.lower() in L.lower() for k in SKIP): continue
    if L == 'a-extg-struct' or L.endswith('a-extg-struct'): pass
    if x['type'] != 's': continue
    for s in segs(x):
        ls = LineString(s)
        if ls.length >= 0.05: lines.append(ls)
faces = list(polygonize(unary_union(lines)))
labels = {}
for bk in p.get_text('dict')['blocks']:
    for l in bk.get('lines', []):
        for s in l['spans']:
            t = s['text'].strip()
            if abs(s['size']-8.8) < 0.3 and (t.isdigit() and len(t) == 2):
                labels.setdefault(t, []).append(((s['bbox'][0]+s['bbox'][2])/2, (s['bbox'][1]+s['bbox'][3])/2))
rows = []
for tag, pts in sorted(labels.items()):
    for (x, y) in pts:
        pt = Point(x, y)
        cands = [f for f in faces if f.contains(pt)]
        if not cands: rows.append((tag, x, y, None)); continue
        f = min(cands, key=lambda g: g.area)
        rows.append((tag, x, y, f))
with open(f'{out}/rooms_p{pn}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['tag', 'label_x', 'label_y', 'area_sf', 'perim_ft', 'holes', 'x0', 'y0', 'x1', 'y1'])
    for tag, x, y, f in rows:
        if f is None: w.writerow([tag, round(x), round(y), '', '', '', '', '', '', '']); continue
        w.writerow([tag, round(x), round(y), round(f.area/PT_PER_FT**2, 1), round(f.exterior.length/PT_PER_FT, 1), len(f.interiors)] + [round(v) for v in f.bounds])
Z = 3.0; M = p.rotation_matrix*fitz.Matrix(Z, Z)
pix = p.get_pixmap(matrix=fitz.Matrix(Z, Z)); im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples).convert('RGBA')
ov = Image.new('RGBA', im.size, (255, 255, 255, 0)); dr = ImageDraw.Draw(ov)
def T(pt): q = fitz.Point(pt)*M; return (q.x, q.y)
import random; random.seed(5)
for tag, x, y, f in rows:
    if f is None: continue
    col = (random.randint(30, 220), random.randint(30, 220), random.randint(30, 220))
    dr.polygon([T(c) for c in f.exterior.coords], fill=col+(70,), outline=col+(255,))
    c = T((x, y)); dr.text((c[0]+10, c[1]+10), f"{tag}: {f.area/PT_PER_FT**2:.0f} SF / {f.exterior.length/PT_PER_FT:.0f} LF", fill=(0, 0, 0, 255))
Image.alpha_composite(im, ov).convert('RGB').save(f'{out}/rooms_p{pn}.png')
for tag, x, y, f in rows:
    print(tag, (round(x), round(y)), ('%.1f SF, %.1f LF, holes %d' % (f.area/PT_PER_FT**2, f.exterior.length/PT_PER_FT, len(f.interiors))) if f is not None else 'NO FACE')
