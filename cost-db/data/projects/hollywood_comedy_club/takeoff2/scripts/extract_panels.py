"""Extract the nine E-2.1 and three E-2.2 panel schedules from the vector text layer of the
MEP progress set (IFB__2604-260909-HW_Comedy-Progress_MEP.pdf, PDF pages 7 and 8).
Panel names are not in the text layer (drawn as graphics), so blocks are named by their
position on the sheet, matched against the sheet image:
  E-2.1 row1: KA, CP, HA | row2: KB, Dillons, B | row3: KC, DP, A ;  E-2.2: EH2, EHB, EPB.
Each circuit line is rebuilt from word x-offsets inside the block:
  left desc | left VA | poles | bkr | ckt L | ckt R | bkr | poles | right VA | right desc
Usage: python3 -I extract_panels.py <pdf> <out.csv>
"""
import sys, csv, pymupdf
pdf, out = sys.argv[1], sys.argv[2]
doc = pymupdf.open(pdf)
NAMES = {7: ['KA', 'CP', 'HA', 'KB', 'Dillons', 'B', 'KC', 'DP', 'A'], 8: ['EH2', 'EHB', 'EPB']}
rows_out = []
for pno in (7, 8):
    page = doc[pno - 1]
    words = page.get_text("words")
    hdr = [w for w in words if w[4] == 'PANEL' and any(v[4] == '-' and abs(v[1]-w[1]) < 3 and 0 < v[0]-w[0] < 30 for v in words)]
    hdr.sort(key=lambda w: (round(w[1] / 50), w[0]))
    assert len(hdr) == len(NAMES[pno]), (pno, len(hdr))
    ys = sorted(set(round(h[1]) for h in hdr))
    for name, h in zip(NAMES[pno], hdr):
        hx, hy = h[0], h[1]
        mnt = [w for w in words if w[4].startswith('MOUNTING') and abs(w[1]-hy) < 8 and w[0] < hx]
        x0 = max(w[0] for w in mnt)
        nxt = [w[0] for w in words if w[4].startswith('MOUNTING') and abs(w[1]-hy) < 8 and w[0] > hx]
        x1 = min(nxt) - 5 if nxt else page.rect.width
        lower = [y for y in ys if y > hy + 20]
        y1 = min(lower) - 5 if lower else page.rect.height
        blk = [w for w in words if x0-2 <= w[0] < x1 and hy-2 <= w[1] < y1]
        # header info
        line = lambda yy, tol=8: ' '.join(w[4] for w in sorted([w for w in blk if abs(w[1]-yy) < tol], key=lambda w: w[0]))
        meta = {'mounting': line(hy), 'voltage': line(hy + 19)}
        # circuit rows: y between header+55 and the 'VA PER PHASE' row
        vpp = [w for w in blk if w[4] == 'PER' and any(v[4] == 'PHASE' and abs(v[1]-w[1]) < 3 and 0 < v[0]-w[0] < 15 for v in blk) and w[1] > hy + 60]
        yend = min(w[1] for w in vpp) if vpp else y1
        body = [w for w in blk if hy + 55 < w[1] < yend - 1]
        body.sort(key=lambda w: (w[1], w[0]))
        rows = []
        for w in body:
            if rows and abs(rows[-1]['y'] - w[1]) < 3.5:
                rows[-1]['w'].append(w)
            else:
                rows.append({'y': w[1], 'w': [w]})
        # merge circuit-number-only rows into the nearest description row
        def is_cktonly(r):
            return all(w[4].isdigit() and 290 < w[0]-x0 < 318 for w in r['w'])
        merged = []
        for r in rows:
            if is_cktonly(r) and merged and abs(merged[-1]['y'] - r['y']) < 9:
                merged[-1]['w'] += r['w']
            else:
                merged.append(r)
        for r in merged:
            ws = sorted(r['w'], key=lambda w: w[0])
            cols = {'ldesc': [], 'lva': [], 'lpole': [], 'lbkr': [], 'cktL': [], 'cktR': [], 'rbkr': [], 'rpole': [], 'rva': [], 'rdesc': []}
            for w in ws:
                dx = w[0] - x0
                t = w[4]
                if dx < 136: cols['ldesc'].append(t)
                elif dx < 262: cols['lva'].append(t)
                elif dx < 278: cols['lpole'].append(t)
                elif dx < 294: cols['lbkr'].append(t)
                elif dx < 306: cols['cktL'].append(t)
                elif dx < 318: cols['cktR'].append(t)
                elif dx < 330: cols['rbkr'].append(t)
                elif dx < 345: cols['rpole'].append(t)
                elif dx < 490: cols['rva'].append(t)
                else: cols['rdesc'].append(t)
            rows_out.append({'sheet': 'E-2.1' if pno == 7 else 'E-2.2', 'panel': name, 'y': round(r['y'], 1),
                             **{k: ' '.join(v) for k, v in cols.items()}})
        rows_out.append({'sheet': 'E-2.1' if pno == 7 else 'E-2.2', 'panel': name, 'y': 0, 'ldesc': '#META', 'lva': meta['mounting'], 'rdesc': meta['voltage'],
                         'lpole': '', 'lbkr': '', 'cktL': '', 'cktR': '', 'rbkr': '', 'rpole': '', 'rva': ''})
with open(out, 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=['sheet', 'panel', 'y', 'ldesc', 'lva', 'lpole', 'lbkr', 'cktL', 'cktR', 'rbkr', 'rpole', 'rva', 'rdesc'])
    wr.writeheader(); wr.writerows(rows_out)
print(len(rows_out), 'rows')
