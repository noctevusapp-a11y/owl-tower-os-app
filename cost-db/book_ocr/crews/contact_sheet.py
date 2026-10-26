#!/usr/bin/env python3
"""Build a contact sheet (one PNG) of crew-header crops whose crew id is not confirmed by two OCR
readings, or whose readings had to be reinterpreted (digit -> letter suffix), or which is duplicated.
Usage: contact_sheet.py <out.png> [max_rows]   (reads work/crews_raw.json)"""
import json, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, '/tmp/claude-0/book/scripts_crews')
from common import BOOK

OFFS = json.load(open(f'{BOOK}/work/page_offsets.json'))
SIDE_BASE = {'L': 0.0, 'R': 0.4965}
crews = json.load(open(f'{BOOK}/work/crews_raw.json'))
ids = [c['crew_id'] for c in crews]
sel = []
for i, c in enumerate(crews):
    raw = [v.upper().replace('—', '-').replace('–', '-') for v in c['id_readings'].values()]
    exact = sum(r == c['crew_id'] for r in raw)
    dup = ids.count(c['crew_id']) > 1
    if c['id_conf'] != 'agree' or exact < 2 or dup or c['crew_id'] is None:
        sel.append((i, c, 'dup' if dup else ''))
out = sys.argv[1]
maxrows = int(sys.argv[2]) if len(sys.argv) > 2 else 60
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
sel = sel[start:start + maxrows]
tiles = []
for i, c, flag in sel:
    im = Image.open(f'{BOOK}/work/render/p{c["page"]:04d}_400.png')
    W, H = im.size
    shift = SIDE_BASE[c['side']] + OFFS[str(c['page'])][c['side']]
    x0, x1 = int(W * max(0, shift - 0.004)), int(W * (shift + 0.135))
    y0, y1 = int(H * (c['y'] - 0.009)), int(H * (c['y'] + 0.009))
    tile = im.crop((x0, y0, x1, y1)).convert('L')
    tiles.append((tile, f'#{i} p{c["page"]}{c["side"]} id={c["crew_id"]} {c["id_conf"][:12]} {flag} {list(c["id_readings"].values())}'[:110]))
tw = max(t.width for t, _ in tiles) + 1200
th = max(t.height for t, _ in tiles)
sheet = Image.new('L', (tw, th * len(tiles)), 255)
dr = ImageDraw.Draw(sheet)
for k, (t, label) in enumerate(tiles):
    sheet.paste(t, (0, k * th))
    dr.text((t.width + 10, k * th + th // 3), label, fill=0)
sheet = sheet.resize((sheet.width // 2, sheet.height // 2))
sheet.save(out)
print(len(sel), 'tiles ->', out)
