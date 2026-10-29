import sys, pymupdf
pdf, pref = sys.argv[1], sys.argv[2]
pages = [int(a) for a in sys.argv[3:]] if len(sys.argv) > 3 else None
d = pymupdf.open(pdf)
for i, p in enumerate(d):
    if pages and (i+1) not in pages: continue
    M = p.rotation_matrix
    rows = []
    for b in p.get_text('blocks'):
        r = pymupdf.Rect(b[:4]) * M
        rows.append((round(r.y0), round(r.x0), b[4].replace('\n', ' | ')))
    rows.sort()
    with open(f'{pref}_p{i+1:02d}.txt', 'w') as f:
        for y, x, t in rows: f.write(f'{x:5d} {y:5d}  {t}\n')
    print(pref, i+1, len(rows), p.rect, p.rotation)
