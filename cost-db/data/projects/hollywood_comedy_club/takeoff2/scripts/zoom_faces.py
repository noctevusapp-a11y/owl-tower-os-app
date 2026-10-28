"""Zoomed crops of the plan with the poche wall runs (poche_runs_p<N>.csv) and their ids, for manual
tag review. Usage: python3 -I zoom_faces.py <pdf> <page> <outdir> name:x0,y0,x1,y1 ..."""
import sys, csv, fitz
from PIL import Image, ImageDraw, ImageFont
pdf, pn, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = fitz.open(pdf); p = d[pn-1]
Z = 6.0
M = p.rotation_matrix*fitz.Matrix(Z, Z)
rows = list(csv.DictReader(open(f'{out}/poche_runs_p{pn}.csv')))
pix = p.get_pixmap(matrix=fitz.Matrix(Z, Z)); im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples).convert('RGBA')
ov = Image.new('RGBA', im.size, (255, 255, 255, 0)); dr = ImageDraw.Draw(ov)
def T(pt): q = fitz.Point(pt)*M; return (q.x, q.y)
COL = {'1': (255, 0, 0), '2': (0, 160, 0), '3': (0, 0, 255), '5': (255, 0, 255), '1A': (255, 128, 0), 'AC': (0, 180, 180), 'E': (120, 120, 120), '?': (0, 0, 0)}
for r in rows:
    x0, y0, x1, y1 = float(r['x0']), float(r['y0']), float(r['x1']), float(r['y1'])
    col = COL.get(r['tags'].split('/')[0] if r['tags'] else '?', (0, 0, 0))
    pts = [T((x0, y0)), T((x1, y0)), T((x1, y1)), T((x0, y1))]
    dr.rectangle([min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts)], outline=col+(255,), width=3)
    c = T((float(r['cx']), float(r['cy'])))
    dr.rectangle([c[0]-2, c[1]-14, c[0]+60, c[1]+14], fill=(255, 255, 200, 220))
    dr.text((c[0], c[1]-12), f"{r['id']}:{r['tags'] or '?'}{'#' if int(r['hatch']) else ''} {float(r['len_ft']):.1f}", fill=(0, 0, 0, 255))
im = Image.alpha_composite(im, ov).convert('RGB')
for a in sys.argv[4:]:
    name, box = a.split(':'); x0, y0, x1, y1 = [float(v) for v in box.split(',')]
    pts = [T((x0, y0)), T((x1, y0)), T((x1, y1)), T((x0, y1))]
    X0, Y0 = int(min(q[0] for q in pts)), int(min(q[1] for q in pts)); X1, Y1 = int(max(q[0] for q in pts)), int(max(q[1] for q in pts))
    cr = im.crop((X0, Y0, X1, Y1)); w, h = cr.size
    if max(w, h) > 2000: s = 2000/max(w, h); cr = cr.resize((int(w*s), int(h*s)))
    cr.save(f'{out}/zoom_p{pn}_{name}.jpg', quality=85); print(name, cr.size)
