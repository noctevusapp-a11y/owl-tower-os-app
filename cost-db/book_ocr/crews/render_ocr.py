#!/usr/bin/env python3
"""Render the crew pages (PDF 763-799) and the trade-rate page (963) at 400 dpi,
crop each crew column (per-page horizontal calibration from the IA text layer, since
recto/verso pages are shifted by ~0.055 of the page width), and run tesseract (psm 6, TSV).
Outputs under /tmp/claude-0/book/work/t400/ plus work/page_offsets.json.
"""
import json, os, statistics, subprocess, sys
import pymupdf
from PIL import Image

BOOK = '/tmp/claude-0/book'
OUT = f'{BOOK}/work/t400'
REN = f'{BOOK}/work/render'
os.makedirs(OUT, exist_ok=True)
os.makedirs(REN, exist_ok=True)
ENV = dict(os.environ, OMP_THREAD_LIMIT='1')

# reference geometry = PDF page 763 (odd page): x0 of the "Costs" header word of each table
REF_COSTS = {'L': 0.3606, 'R': 0.8562}


def page_offsets(page):
    """horizontal shift of the left/right crew table relative to page 763, from the IA text layer"""
    ia = json.load(open(f'{BOOK}/ia/p{page:04d}.json'))['words']
    off = {}
    for side, lo, hi in (('L', 0.0, 0.5), ('R', 0.5, 1.0)):
        xs = [w['x0'] for w in ia if w['t'] == 'Costs' and lo <= w['x0'] < hi]
        # keep the dominant cluster (the header word repeats once per crew block)
        xs.sort()
        best = None
        for x in xs:
            c = [y for y in xs if abs(y - x) < 0.01]
            if best is None or len(c) > len(best):
                best = c
        if best and len(best) >= 2:
            off[side] = round(statistics.median(best) - REF_COSTS[side], 4)
        else:
            off[side] = 0.0 if page % 2 == 1 else 0.055   # parity default
    return off


def render(page):
    if 712 <= page <= 847:
        doc = pymupdf.open(f'{BOOK}/parts/rsmeans_part05_p0712-0847.pdf'); idx = page - 712
    else:
        doc = pymupdf.open(f'{BOOK}/parts/rsmeans_part06_p0848-0964.pdf'); idx = page - 848
    path = f'{REN}/p{page:04d}_400.png'
    if not os.path.exists(path):
        doc[idx].get_pixmap(dpi=400, colorspace=pymupdf.csGRAY).save(path)
    return path


def ocr(png, base, psm=6):
    subprocess.run(['tesseract', png, base, '--psm', str(psm), 'tsv'], env=ENV,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


pages = [int(a) for a in sys.argv[1:]] or list(range(763, 800))
offsets = {}
if os.path.exists(f'{BOOK}/work/page_offsets.json'):
    offsets = json.load(open(f'{BOOK}/work/page_offsets.json'))
for page in pages:
    path = render(page)
    im = Image.open(path)
    w, h = im.size
    if page == 963:
        box = (0, int(h * 0.30), w, int(h * 0.97))
        crop = f'{REN}/p{page:04d}_T.png'
        im.crop(box).save(crop)
        ocr(crop, f'{OUT}/p{page:04d}_T')
        with open(f'{OUT}/p{page:04d}_T.box', 'w') as f:
            f.write(f'{box[0]} {box[1]} {box[2]} {box[3]} {w} {h}\n')
        continue
    off = page_offsets(page)
    offsets[str(page)] = off
    crops = {
        'L': (0, int(h * 0.05), int(w * min(1.0, 0.475 + off['L'])), int(h * 0.965)),
        'R': (int(w * (0.485 + off['R'])), int(h * 0.05), int(w * min(1.0, 0.975 + off['R'])), int(h * 0.965)),
    }
    for side, box in crops.items():
        crop = f'{REN}/p{page:04d}_{side}.png'
        im.crop(box).save(crop)
        ocr(crop, f'{OUT}/p{page:04d}_{side}')
        with open(f'{OUT}/p{page:04d}_{side}.box', 'w') as f:
            f.write(f'{box[0]} {box[1]} {box[2]} {box[3]} {w} {h}\n')
    json.dump(offsets, open(f'{BOOK}/work/page_offsets.json', 'w'), indent=1)
    print('done', page, off, flush=True)
