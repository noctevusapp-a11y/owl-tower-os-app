#!/usr/bin/env python3
"""TABLE 2: crew listings, PDF pages 763-799.

Readings per page: T400 = own tesseract on calibrated column crops at 400 dpi, IA = the scan's text
layer, T360 = the book OCR at 360 dpi.  They are merged word-by-word into lines; numeric cells are
assigned to table columns by their right edge (the columns are right-aligned); every cell keeps its
readings, and the crew identities (daily = hr x 8 x qty, sums, labour hours, cost per labour-hour)
choose between disagreeing readings.  Crews that still fail get a fourth reading, TROW: each row of
the crew is cropped from the 400 dpi render (row located by its ink profile), upscaled 2x and read
with tesseract psm 7.  Nothing is filled in unless an OCR reading is compatible with the value
(digits within one edit) or two independent printed identities agree on it (noted as such).
"""
import csv, itertools, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageOps
sys.path.insert(0, '/tmp/claude-0/book/scripts_crews')
from common import *

PAGES = range(763, 800)
OFFS = json.load(open(f'{BOOK}/work/page_offsets.json'))
ROWDIR = f'{BOOK}/work/rows'
os.makedirs(ROWDIR, exist_ok=True)
ENV = dict(os.environ, OMP_THREAD_LIMIT='1')

# reference column geometry (PDF page 763, left table, page-width fractions): right edges of the
# right-aligned numeric columns, and the right limit of the description column.
COL_RIGHT = {'bare_hr': 0.172, 'bare_daily': 0.234, 'op_hr': 0.279, 'op_daily': 0.342, 'lh_bare': 0.388, 'lh_op': 0.441}
DESC_MAX_X1 = 0.136
SIDE_BASE = {'L': 0.0, 'R': 0.4965}
NUMCOLS = list(COL_RIGHT)
QTY_RE = re.compile(r'^(\d{0,2}\.\d{1,3}|\d{1,4})$')
HDR_WORDS = {'bare', 'incl.', 'incl', 'costs', 'o&p', 'hr.', 'hr', 'daily', 'o8p', 'oap', 'cost', 'crew', 'no.', 'subs', 'per',
             'labor-hour', 'o8&p', 'ogp', '0&p', 'inc', 'hr,', 'daly', 'dally', 'lncl.', 'incl,'}
def SUM_TOL(n):
    # each printed daily is rounded to the cent and the printed total is the rounded exact sum
    return 0.006 + 0.005 * n


SRC_WEIGHT = {'T400': 1.0, 'IA': 1.0, 'TROW': 0.8, 'T360': 0.7, 'TCELL': 0.6}
TOT_KEYS = ('lh', 'bare_total', 'op_total', 'bare_total_per_lh', 'op_total_per_lh', 'bare_labor_per_lh', 'op_labor_per_lh',
            'bare_equip_per_lh', 'op_equip_per_lh')
_IMG = {}


# ---------------------------------------------------------------- loading ------------------------
def page_dims_360(page):
    with open(f'{BOOK}/ocr/p{page:04d}.tsv') as f:
        f.readline(); r = f.readline().split('\t')
    return int(r[8]), int(r[9])


def load_sources(page):
    srcs = {}
    w, h = page_dims_360(page)
    srcs['T360'] = load_tsv_words(f'{BOOK}/ocr/p{page:04d}.tsv', 0, 0, w, h)
    srcs['IA'] = load_ia_words(f'{BOOK}/ia/p{page:04d}.json')
    t = []
    for side in 'LR':
        bx = open(f'{BOOK}/work/t400/p{page:04d}_{side}.box').read().split()
        x0, y0, x1, y1, W, H = map(int, bx)
        t += load_tsv_words(f'{BOOK}/work/t400/p{page:04d}_{side}.tsv', x0, y0, W, H)
    srcs['T400'] = t
    return srcs


def clean_tok(t):
    return t.strip('|}{[]¢°«»—_ ').strip()


def side_words(words, side, off):
    shift = SIDE_BASE[side] + off
    lo, hi = -0.02 + shift, 0.47 + shift
    out = []
    for w in words:
        xc = (w['x0'] + w['x1']) / 2
        if lo <= xc < hi:
            out.append(dict(w, x0=w['x0'] - shift, x1=w['x1'] - shift))
    return out


def col_of_num(w):
    best, bd = None, 1
    for c, r in COL_RIGHT.items():
        d = abs(w['x1'] - r)
        if d < bd:
            best, bd = c, d
    return best if bd < 0.022 else None


def align_y(srcs):
    """shift IA and T360 word boxes vertically so that they agree with T400 (the text layer is offset on some pages)"""
    ref = {}
    for w in srcs['T400']:
        if len(w['t']) >= 3:
            ref.setdefault(w['t'], []).append(w)
    for s in ('IA', 'T360'):
        dys = []
        for w in srcs[s]:
            for r in ref.get(w['t'], []):
                if abs(r['x0'] - w['x0']) < 0.008 and abs(r['y0'] - w['y0']) < 0.012:
                    dys.append(((r['y0'] + r['y1']) - (w['y0'] + w['y1'])) / 2)
                    break
        if len(dys) >= 10:
            dys.sort()
            dy = dys[len(dys) // 2]
            srcs[s] = [dict(w, y0=w['y0'] + dy, y1=w['y1'] + dy) for w in srcs[s]]
            srcs.setdefault('_dy', {})[s] = round(dy, 4)


def build_lines(srcs, side, off):
    allw = []
    for s, ws in srcs.items():
        if s.startswith('_'):
            continue
        for w in side_words(ws, side, off):
            t = clean_tok(w['t'])
            if t:
                allw.append(dict(w, t=t, src=s))
    # T400 (own OCR of the rendered page) has the most reliable row geometry: its lines anchor the
    # other sources' words; words that fit no T400 line form lines of their own (rows T400 dropped).
    anchors = group_lines([w for w in allw if w['src'] == 'T400'], 0.005)
    rest = []
    for w in allw:
        if w['src'] == 'T400':
            continue
        yc = (w['y0'] + w['y1']) / 2
        best = min(anchors, key=lambda ln: abs(ln['y'] - yc), default=None)
        if best is not None and abs(best['y'] - yc) < 0.0075:
            best['w'].append(w)
        else:
            rest.append(w)
    lines = anchors + group_lines(rest, 0.005)
    for ln in lines:
        ln['w'].sort(key=lambda w: w['x0'])
        # the row's y is the median of all its words: a junk T400 line must not drag a real row onto itself
        ys = sorted((w['y0'] + w['y1']) / 2 for w in ln['w'])
        ln['y'] = ys[len(ys) // 2]
    lines.sort(key=lambda ln: ln['y'])
    return lines


# ---------------------------------------------------------------- row-level OCR ------------------
def page_image(page):
    if page not in _IMG:
        _IMG[page] = Image.open(f'{BOOK}/work/render/p{page:04d}_400.png')
    return _IMG[page]


def row_ocr(page, side, yc):
    """4th reading of one table row: crop by ink profile around yc, 2x upscale, tesseract psm 7.
    Returns words in reference (side-shifted) coordinates."""
    key = f'{page}_{side}_{yc:.4f}'
    base = f'{ROWDIR}/{key}'
    im = page_image(page)
    W, H = im.size
    shift = SIDE_BASE[side] + OFFS[str(page)][side]
    x0, x1 = int(W * max(0, shift - 0.006)), int(W * min(1, shift + 0.468))
    y0, y1 = int(H * (yc - 0.0105)), int(H * (yc + 0.0125))
    if not os.path.exists(base + '.tsv'):
        band = np.array(im.crop((x0, y0, x1, y1)))
        runs = text_runs(band, 14)
        if not runs:
            return []
        centre = int(H * yc) - y0
        a, b = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - centre))
        a, b = max(0, a - 4), min(band.shape[0], b + 4)
        crop = im.crop((x0, y0 + a, x1, y0 + b))
        scale = 2
        for scale in (2, 3):
            big = ImageOps.autocontrast(crop, cutoff=1).resize((crop.width * scale, crop.height * scale), Image.LANCZOS)
            big.save(base + '.png')
            subprocess.run(['tesseract', base + '.png', base, '--psm', '7', 'tsv'], env=ENV,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(base + '.tsv') and any(w['t'].strip() for w in load_tsv_words(base + '.tsv', 0, 0, 1, 1)):
                break
        with open(base + '.box', 'w') as f:
            f.write(f'{x0} {y0 + a} {scale}\n')
        if not os.path.exists(base + '.tsv'):
            return []
    parts = open(base + '.box').read().split()
    bx0, by0 = int(parts[0]), int(parts[1])
    scale = int(parts[2]) if len(parts) > 2 else 2
    words = []
    for w in load_tsv_words(base + '.tsv', 0, 0, 1, 1):
        words.append({'x0': (w['x0'] / scale + bx0) / W - shift, 'x1': (w['x1'] / scale + bx0) / W - shift,
                      'y0': (w['y0'] / scale + by0) / H, 'y1': (w['y1'] / scale + by0) / H, 't': clean_tok(w['t']), 'src': 'TROW', 'conf': w['conf']})
    return [w for w in words if w['t'] and w['x1'] > 0.002]


def text_runs(band, min_len):
    """vertical runs of text rows in a grey band: ink above the band's baseline but below a rule"""
    ink = (band < 128).mean(axis=1)
    base = float(np.percentile(ink, 20))
    runs, start = [], None
    for i, v in enumerate(ink):
        txt = base + 0.015 < v < 0.3 + base
        if txt and start is None:
            start = i
        elif not txt and start is not None:
            runs.append((start, i)); start = None
    if start is not None:
        runs.append((start, len(ink)))
    return [r for r in runs if r[1] - r[0] >= min_len]


def cell_ocr(page, side, yc, col):
    """last resort for one cell: crop the column cell of that row, 3x upscale, tesseract psm 7 with a
    digit whitelist.  Returns the token or None."""
    key = f'{page}_{side}_{yc:.4f}_{col}'
    base = f'{ROWDIR}/{key}'
    if not os.path.exists(base + '.txt'):
        im = page_image(page)
        W, H = im.size
        shift = SIDE_BASE[side] + OFFS[str(page)][side]
        if col == 'qty':
            x0, x1 = int(W * max(0, shift - 0.004)), int(W * (shift + 0.03))
        else:
            r = COL_RIGHT[col]
            x0, x1 = int(W * (shift + r - 0.052)), int(W * (shift + r + 0.006))
        y0, y1 = int(H * (yc - 0.0105)), int(H * (yc + 0.0125))
        band = np.array(im.crop((x0, y0, x1, y1)))
        runs = text_runs(band, 12)
        if not runs:
            open(base + '.txt', 'w').write('')
            return None
        centre = int(H * yc) - y0
        a, b = min(runs, key=lambda q: abs((q[0] + q[1]) / 2 - centre))
        a, b = max(0, a - 5), min(band.shape[0], b + 5)
        crop = im.crop((x0, y0 + a, x1, y0 + b))
        crop = ImageOps.autocontrast(crop, cutoff=1).resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
        crop.save(base + '.png')
        subprocess.run(['tesseract', base + '.png', base, '--psm', '7', '-c', 'tessedit_char_whitelist=0123456789.$,'], env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(base + '.txt'):
            open(base + '.txt', 'w').write('')
    t = open(base + '.txt').read().strip().replace(' ', '')
    nums = re.findall(r'\$?\d[\d,]*(?:\.\d+)?', t)
    return nums[-1] if nums else None


def cell_fallback(crew, page):
    """OCR the individual cells that are still without a value"""
    added = False
    for m in crew['members']:
        if m['qty'] is None and not any(w['src'] == 'TCELL' for w in m['by_src'].get('TCELL', [])):
            t = cell_ocr(page, crew['side'], m['y'], 'qty')
            if t and QTY_RE.match(t):
                m['by_src'].setdefault('TCELL', []).append({'x0': 0.002, 'x1': 0.02, 'y0': m['y'], 'y1': m['y'], 't': t, 'src': 'TCELL', 'conf': 0})
                added = True
        for col in ('bare_hr', 'bare_daily', 'op_hr', 'op_daily'):
            if m['kind'] == 'equipment' and col.endswith('_hr'):
                continue
            c = m['vals'][col]
            if c.value is None and not any(src == 'TCELL' for src, _ in c.readings):
                t = cell_ocr(page, crew['side'], m['y'], col)
                if t:
                    m['by_src'].setdefault('TCELL', []).append({'x0': COL_RIGHT[col] - 0.05, 'x1': COL_RIGHT[col], 'y0': m['y'], 'y1': m['y'], 't': t, 'src': 'TCELL', 'conf': 0})
                    added = True
    T = crew['totals']
    labor = [m for m in crew['members'] if m['kind'] == 'labor']
    equip = [m for m in crew['members'] if m['kind'] == 'equipment']
    targets = []
    if crew.get('totals_y') is not None:
        targets += [('bare_total', crew['totals_y'], 'bare_daily', None), ('op_total', crew['totals_y'], 'op_daily', None),
                    ('bare_total_per_lh', crew['totals_y'], 'lh_bare', None), ('op_total_per_lh', crew['totals_y'], 'lh_op', None)]
    if labor:
        targets += [('bare_labor_per_lh', labor[0]['y'], 'lh_bare', labor[0]), ('op_labor_per_lh', labor[0]['y'], 'lh_op', labor[0])]
    if equip:
        targets += [('bare_equip_per_lh', equip[-1]['y'], 'lh_bare', equip[-1]), ('op_equip_per_lh', equip[-1]['y'], 'lh_op', equip[-1])]
    for key, y, col, mem in targets:
        c = T[key]
        if c.value is None and not any(src == 'TCELL' for src, _ in c.readings):
            t = cell_ocr(page, crew['side'], y, col)
            if t:
                w = {'x0': COL_RIGHT[col] - 0.05, 'x1': COL_RIGHT[col], 'y0': y, 'y1': y, 't': t, 'src': 'TCELL', 'conf': 0}
                if mem is None:
                    crew['totals_by_src'].setdefault('TCELL', []).append(w)
                else:
                    mem['by_src'].setdefault('TCELL', []).append(w)
                added = True
    return added


# ---------------------------------------------------------------- line classification -----------
def by_source(words):
    d = {}
    for w in words:
        d.setdefault(w['src'], []).append(w)
    for ws in d.values():
        ws.sort(key=lambda w: w['x0'])
    return d


def classify(line):
    by_src = by_source(line['w'])
    toks = line['w']
    ids = {}
    for s, ws in by_src.items():
        for i, w in enumerate(ws[:2]):
            if w['t'].lower().strip('.,:') in ('crew', 'craw', 'crow', 'cew', 'grew', 'crews') and i + 1 < len(ws) and w['x0'] > 0.015:
                ids[s] = ws[i + 1]['t'].replace('—', '-').replace('–', '-').replace('_', '-').strip('.,:;')
    if ids:
        return 'header', ids
    joined = ' '.join(' '.join(w['t'] for w in ws) for ws in by_src.values()).lower()
    if re.search(r'(l\.?h\.?,|lh,|lh\.|l\.h|daily tota|dally tota|daly tota|daily total|dailytotals|totals|totais|totas)', joined):
        return 'totals', by_src
    words = [w['t'].lower().strip('.,') for w in toks]
    if words and all(x in HDR_WORDS for x in words):
        return 'skip', 'colhdr'
    for ws in by_src.values():
        sw = [w['t'].lower().strip('.,') for w in ws]
        if 'bare' in sw and any(x in ('incl', 'ancl', 'lncl', 'inci', 'inc') for x in sw) and not any(re.search(r'\d', x) for x in sw):
            return 'skip', 'colhdr'
    if not any(s in by_src for s in ('T400', 'IA')):
        return 'skip', 'T360-only'
    if looks_like_totals(by_src):
        return 'totals', by_src
    desc_words = [w for w in toks if w['x1'] < DESC_MAX_X1 + 0.01]
    if not desc_words and not any(col_of_num(w) in ('bare_daily', 'op_daily') and re.search(r'[0-9]', w['t']) for w in toks):
        return 'skip', 'no-desc'
    return 'member', by_src


def looks_like_totals(by_src, strict=True):
    """totals row without a readable label: $-amounts in the daily columns, no Hr amounts, and no real
    description word (only Daily/Totals-like fragments) in the T400/IA readings"""
    good = {k: v for k, v in by_src.items() if k in ('T400', 'IA', 'TROW')}
    if any(readings_for(good, c) for c in ('bare_hr', 'op_hr')):
        return False
    dollar = any(tok.lstrip().startswith(('$', 'S$', '$S')) or tok.startswith('S') and tok[1:2].isdigit()
                 for c in ('bare_daily', 'op_daily') for _, tok in readings_for(by_src, c))
    label = any(re.search(r'(dai?ly|dall?y|tota|tots|toas|l\.?h\b)', w['t'].lower()) for ws in by_src.values() for w in ws if w['x1'] < DESC_MAX_X1)
    if not dollar and not label:
        return False
    if not strict:
        # inside a block: $-amounts are decisive, but a row that starts with a count is a member row
        q, _ = desc_and_qty(good)
        return dollar and (label or not q)
    for ws in good.values():
        for w in ws:
            if w['x1'] < DESC_MAX_X1 and w['x0'] > 0.012:
                t = re.sub(r'[^a-z]', '', w['t'].lower())
                if len(t) >= 4 and min(lev(t, 'daily'), lev(t, 'totals')) > 2 and not re.search(r'(dai?ly|dall?y|tota|tots|toas)', t):
                    return False
    return True


def readings_for(by_src, col):
    out = []
    for s, ws in by_src.items():
        toks = [w for w in ws if col_of_num(w) == col and re.search(r'[0-9]', w['t'])]
        if toks:
            out.append((s, ' '.join(w['t'] for w in toks)))
    return out


def desc_and_qty(by_src):
    q, d = {}, {}
    for s, ws in by_src.items():
        dw = [w for w in ws if w['x1'] < DESC_MAX_X1 + 0.012 and w['x0'] < DESC_MAX_X1 - 0.01]
        if not dw:
            continue
        first = dw[0]['t']
        g = re.match(r'^(\.?\d{1,2})([A-Za-z(].+)$', first)      # '.5FE.' / '2Laborers': count glued to the word
        if g and dw[0]['x0'] < 0.03:
            dw = [dict(dw[0], t=g.group(1)), dict(dw[0], t=g.group(2))] + dw[1:]
            first = g.group(1)
        f = first.replace('l', '1').replace('I', '1').replace('T', '1').replace('J', '1').replace(']', '1').replace('O', '0').replace(',', '.')
        m = re.match(r'^(\d{1,2})-(.+)$', f)          # "2-50' Air Hoses" -> qty 2
        if m and dw[0]['x0'] < 0.03:
            q[s] = m.group(1)
            d[s] = ' '.join(['-' + first.split('-', 1)[1]] + [w['t'] for w in dw[1:]])
        elif QTY_RE.match(f) and dw[0]['x0'] < 0.03:
            q[s] = f
            d[s] = ' '.join(w['t'] for w in dw[1:])
        else:
            d[s] = ' '.join(w['t'] for w in dw)
    return q, d


def lh_readings(by_src):
    out = []
    for s, ws in by_src.items():
        for w in ws[:2]:
            if w['x0'] > 0.03:
                break
            f = w['t'].replace('B', '8').replace('T', '1').replace('l', '1').replace('I', '1').replace(']', '1').replace('O', '0').replace(',', '.')
            m = re.match(r'^(\d+(?:\.\d+)?)(?:$|[Ll])', f)
            if m:
                out.append((s, m.group(1)))
                break
    return out


# ---------------------------------------------------------------- cells --------------------------
def candidates(readings, allow_int=False):
    cands = {}
    for s, tok in readings:
        v, fl = norm_num_token(tok)
        if v is None:
            continue
        if 'nodec' in fl and not allow_int:
            for alt in (round(v / 100, 2), round(v / 10, 2), float(v)):
                c = cands.setdefault(alt, {'direct': 0, 'repair': 0, 'srcs': set()})
                c['repair'] += 1; c['srcs'].add(s)
        elif 'onedec' in fl and not allow_int:
            # every printed amount has two decimals: a one-decimal token lost a digit somewhere
            for alt in (round(v, 2), round(v * 10, 2)):
                c = cands.setdefault(alt, {'direct': 0, 'repair': 0, 'srcs': set()})
                c['repair'] += 1; c['srcs'].add(s)
        else:
            c = cands.setdefault(round(v, 2), {'direct': 0, 'repair': 0, 'srcs': set()})
            c['direct'] += 1; c['srcs'].add(s)
    return cands


def best_direct(cands):
    direct = {v: c for v, c in cands.items() if c['direct'] > 0}
    if not direct:
        return None, 'none'
    top = max(direct.items(), key=lambda kv: kv[1]['direct'])
    if top[1]['direct'] >= 2 and top[1]['direct'] > sum(c['direct'] for v, c in direct.items() if v != top[0]):
        return top[0], 'agree'
    if len(direct) == 1:
        return top[0], 'single'
    return None, 'conflict'


def is_compatible(v, readings):
    return any(compatible(v, tok) for _, tok in readings)


class Cell:
    def __init__(self, readings, allow_int=False):
        self.readings = readings
        self.cands = candidates(readings, allow_int)
        self.value, self.how = best_direct(self.cands)
        self.note = ''

    def set(self, v, how, note=''):
        self.value, self.how, self.note = v, how, note

    def options(self):
        opts = sorted(self.cands.items(), key=lambda kv: (-kv[1]['direct'], -kv[1]['repair']))
        return [v for v, _ in opts]

    def __repr__(self):
        return f'{self.value}({self.how})'


def is_labor(vals):
    """a labour line has an hourly rate: read by T400/IA, or a numeric value >= 10 from any source"""
    hr_ok = any(src in ('T400', 'IA') and len(re.sub(r'[^0-9]', '', tok)) >= 3 for col in ('bare_hr', 'op_hr') for src, tok in vals[col].readings)
    hr_val = any(norm_num_token(tok)[0] is not None and norm_num_token(tok)[0] >= 10 for col in ('bare_hr', 'op_hr') for _, tok in vals[col].readings)
    return hr_ok or hr_val


def build_cells(crew):
    """(re)build Cell objects from the raw per-source words of each line"""
    for m in crew['members']:
        q, d = desc_and_qty(m['by_src'])
        m['qty_readings'], m['desc_readings'] = q, d
        m['vals'] = {c: Cell(readings_for(m['by_src'], c)) for c in NUMCOLS}
    tb = crew.get('totals_by_src')
    if tb:
        T = {'lh': Cell(lh_readings(tb), allow_int=True), 'bare_total': Cell(readings_for(tb, 'bare_daily')),
             'op_total': Cell(readings_for(tb, 'op_daily')), 'bare_total_per_lh': Cell(readings_for(tb, 'lh_bare')),
             'op_total_per_lh': Cell(readings_for(tb, 'lh_op'))}
    else:
        T = {k: Cell([]) for k in TOT_KEYS[:5]}
    lab_b, lab_o, eq_b, eq_o = [], [], [], []
    for mem in crew['members']:
        rb, ro = mem['vals']['lh_bare'].readings, mem['vals']['lh_op'].readings
        if not (rb or ro):
            continue
        if is_labor(mem['vals']):
            if not lab_b and not lab_o:
                lab_b, lab_o = rb, ro
        else:
            eq_b, eq_o = eq_b + rb, eq_o + ro
    T.update({'bare_labor_per_lh': Cell(lab_b), 'op_labor_per_lh': Cell(lab_o), 'bare_equip_per_lh': Cell(eq_b), 'op_equip_per_lh': Cell(eq_o)})
    crew['totals'] = T


# ---------------------------------------------------------------- identities ---------------------
def resolve_crew(crew, rates):
    notes = []
    members = crew['members']
    for m in members:
        vals = {}
        for s, q in m['qty_readings'].items():
            try:
                v = float(q)
            except ValueError:
                continue
            # a leading-dot fraction is never produced by OCR noise, a lost dot is common: trust the dotted reading
            w = SRC_WEIGHT[s] * (1.5 if q.startswith('.') or '.' in q else 1.0)
            vals[v] = vals.get(v, 0) + w
        m['qty'] = None
        if vals:
            dsrc = choose_desc(m['desc_readings'])[1]
            if dsrc in m['qty_readings']:
                try:
                    vals[float(m['qty_readings'][dsrc])] += 0.3     # the source that read the description best
                except (ValueError, KeyError):
                    pass
            ranked = sorted(vals.items(), key=lambda kv: -kv[1])
            if len(ranked) == 1 or ranked[0][1] > ranked[1][1] + 0.05:
                m['qty'] = ranked[0][0]
        m['qty_options'] = [v for v, _ in sorted(vals.items(), key=lambda kv: -kv[1])]
        # a lost leading dot ('.5' read as '5', '.25' as '25') is common: keep the dotted variants as fallbacks
        for q in list(m['qty_options']):
            if q == int(q) and q >= 1:
                for alt in (q / 10, q / 100, q / 1000):
                    alt = round(alt, 3)
                    if alt not in m['qty_options'] and alt < 10:
                        m['qty_options'].append(alt)
        for s, q in m['qty_readings'].items():          # '125' -> .125, '2125' -> 2.125 (3-4 digit tokens)
            if re.fullmatch(r'\d{3,4}', q):
                alt = round(int(q) / 1000, 3)
                if alt not in m['qty_options']:
                    m['qty_options'].append(alt)
        m['kind'] = 'labor' if is_labor(m['vals']) else 'equipment'

    # labour pairs
    for m in members:
        if m['kind'] != 'labor':
            continue
        for hc, dc, tag in (('bare_hr', 'bare_daily', 'bare'), ('op_hr', 'op_daily', 'op')):
            H, D = m['vals'][hc], m['vals'][dc]
            qopts = list(m['qty_options']) or [1.0]
            if m['qty'] is not None and m['qty'] not in qopts:
                qopts.insert(0, m['qty'])
            sols = []
            for q in qopts:
                for h in H.options():
                    for d in D.options():
                        if abs(h * 8 * q - d) < 0.006:
                            sols.append((q, h, d))
            def score(sol):
                q, h, d = sol
                return ((H.cands[h]['direct'] > 0) + (D.cands[d]['direct'] > 0), h in rates[tag], q == m['qty'],
                        H.cands[h]['direct'] + D.cands[d]['direct'])
            if sols:
                sols.sort(key=score, reverse=True)
                q, h, d = sols[0]
                if len(sols) > 1 and score(sols[1]) == score(sols[0]) and (sols[1][1] != h or sols[1][2] != d):
                    notes.append(f'{m["member_no"]}:{tag} ambiguous pair {sols[:3]}')
                if H.value != h:
                    H.set(h, 'identity', f'from {H.readings} via daily=hr*8*qty')
                if D.value != d:
                    D.set(d, 'identity', f'from {D.readings} via daily=hr*8*qty')
                if m['qty'] != q:
                    notes.append(f'{m["member_no"]}: qty {q:g} chosen by identity from {m["qty_readings"]}')
                    m['qty'] = q
            else:
                q = m['qty'] if m['qty'] is not None else (qopts[0] if m['qty_options'] else None)
                # both amounts read directly and agreeing on a plausible quantity (multiple of 1/8, or .33/.66 thirds)
                if H.value is not None and D.value is not None and H.how in ('agree', 'single') and D.how in ('agree', 'single') and H.value in rates[tag]:
                    qd = D.value / 8 / H.value
                    plaus = abs(qd * 8 - round(qd * 8)) < 0.002 or abs(qd * 3 - round(qd * 3)) < 0.02
                    rd = list(m['qty_readings'].values())
                    if plaus and 0 < qd < 20 and (not rd or any(compatible(round(qd, 3), r) for r in rd)):
                        qd = round(qd, 3)
                        notes.append(f'{m["member_no"]}: qty {qd:g} from daily/(8*hr) (readings {m["qty_readings"]})')
                        m['qty'] = qd
                        if qd not in m['qty_options']:
                            m['qty_options'].insert(0, qd)
                        continue
                if q is not None and H.value is not None and H.how in ('agree', 'single') and (H.value in rates[tag] or H.how == 'agree'):
                    t = round(H.value * 8 * q, 2)
                    if D.readings and is_compatible(t, D.readings):
                        D.set(t, 'identity', f'from {D.readings} via hr*8*qty')
                    elif not D.readings:
                        D.set(None, 'missing', 'no reading')
                    else:
                        D.set(None, 'unresolved', f'readings {D.readings} incompatible with hr*8*qty={t}')
                elif q is not None and D.value is not None and D.how in ('agree', 'single'):
                    t = round(D.value / 8 / q, 2)
                    if H.readings and is_compatible(t, H.readings) and (t in rates[tag] or D.how == 'agree'):
                        H.set(t, 'identity', f'from {H.readings} via daily/8/qty')
                    else:
                        H.set(None, 'unresolved', f'readings {H.readings}; daily/8/qty={t}')
                else:
                    if H.how in ('none', 'conflict'):
                        H.set(None, 'unresolved' if H.readings else 'missing')
                    if D.how in ('none', 'conflict'):
                        D.set(None, 'unresolved' if D.readings else 'missing')
                if H.value is None or D.value is None:
                    notes.append(f'{m["member_no"]}:{tag} unresolved pair H={H.readings} D={D.readings} qty={m["qty_readings"]}')

    # labour hours
    T = crew['totals']
    lh_calc = None
    labor = [m for m in members if m['kind'] == 'labor']
    if labor and all(m['qty'] is not None for m in labor):
        lh_calc = round(sum(m['qty'] * 8 for m in labor), 3)
    LH = T['lh']
    if lh_calc is not None:
        if LH.value is not None and abs(LH.value - lh_calc) > 0.01:
            if lh_calc in LH.options() or is_compatible(lh_calc, LH.readings):
                LH.set(lh_calc, 'identity', f'from {LH.readings} via 8*sum(qty)')
            else:
                notes.append(f'L.H. printed {LH.value:g} ({LH.readings}) != 8*sum(qty) = {lh_calc:g}')
        elif LH.value is None:
            if is_compatible(lh_calc, LH.readings):
                LH.set(lh_calc, 'identity', f'from {LH.readings} via 8*sum(qty)')
            elif not LH.readings:
                LH.set(lh_calc, 'identity-noread', 'no OCR reading of the L.H. figure; value is 8*sum(labor qty)')
            else:
                notes.append(f'L.H. readings {LH.readings} incompatible with 8*sum(qty) = {lh_calc:g}')

    # sums
    for dc, tc, tag in (('bare_daily', 'bare_total', 'bare'), ('op_daily', 'op_total', 'op')):
        cells = [m['vals'][dc] for m in members] + [T[tc]]
        tol = SUM_TOL(len(members))
        def ok(vals):
            *ds, tot = vals
            return None not in vals and abs(sum(ds) - tot) < tol
        if ok([c.value for c in cells]):
            continue
        opts = []
        for i, c in enumerate(cells):
            fixed = i < len(members) and members[i]['kind'] == 'labor' and c.how == 'identity' and c.value is not None
            if fixed or c.how == 'agree':
                opts.append([c.value])
            elif c.how == 'single':
                opts.append([c.value] + [v for v in c.options() if v != c.value and c.cands[v]['direct'] > 0])
            else:
                o = c.options()
                if c.value is not None and c.value not in o:
                    o = [c.value] + o
                opts.append(o if o else [None])
        n = 1
        for o in opts:
            n *= max(1, len(o))
        sols = []
        if n <= 50000:
            for combo in itertools.product(*opts):
                if ok(combo):
                    sols.append(combo)
        def sc(combo):
            return sum(c.cands.get(v, {'direct': 0})['direct'] for c, v in zip(cells, combo))
        if sols:
            sols.sort(key=sc, reverse=True)
            if len(sols) == 1 or sc(sols[0]) > sc(sols[1]):
                for c, v in zip(cells, sols[0]):
                    if c.value != v:
                        c.set(v, 'identity', f'from {c.readings} via sum of dailies = total')
            else:
                notes.append(f'{tag}: several sum solutions {sols[:3]}')
            continue
        missing = [i for i, c in enumerate(cells) if c.value is None]
        if not missing:
            # every cell has a reading-backed value but the sum fails: is exactly one cell off by a single
            # misread digit, with the per-labour-hour figures confirming the corrected value?
            lhv = T['lh'].value
            fixes = []
            for i, c in enumerate(cells):
                others = sum(x.value for j, x in enumerate(cells[:-1]) if j != i)
                t = round(cells[-1].value - others, 2) if i < len(cells) - 1 else round(others, 2)
                if t <= 0 or not is_compatible(t, c.readings):
                    continue
                if lhv:
                    if i == len(cells) - 1:
                        p = T[f'{tag}_total_per_lh'].value
                        conf = p is not None and abs(p - t / lhv) < 0.0051 + 0.02 / lhv
                    else:
                        kind = members[i]['kind']
                        grp = [x.value for j, x in enumerate(cells[:-1]) if members[j]['kind'] == kind and j != i] + [t]
                        p = T[f'{tag}_labor_per_lh' if kind == 'labor' else f'{tag}_equip_per_lh'].value
                        conf = p is not None and abs(p - sum(grp) / lhv) < 0.0051 + 0.02 / lhv
                    if conf:
                        fixes.append((i, t))
            # several cells of the same kind can absorb the same correction: prefer the one whose
            # readings do not agree among themselves, and only act when that choice is unique
            weak = [f for f in fixes if cells[f[0]].how != 'agree']
            pick = weak if weak else fixes
            if len(pick) == 1:
                i, t = pick[0]
                c = cells[i]
                c.set(t, 'identity', f'OCR readings {c.readings} contradicted by the sum and per-LH identities; {t} differs by one digit')
                continue
        if len(missing) == 1:
            i = missing[0]
            known = [c.value for j, c in enumerate(cells) if j != i]
            t = round(sum(known), 2) if i == len(cells) - 1 else round(cells[-1].value - sum(known[:-1]), 2)
            if cells[i].readings and is_compatible(t, cells[i].readings):
                cells[i].set(t, 'identity', f'from {cells[i].readings} via sum of dailies = total')
            else:
                cells[i].set(None, 'unresolved' if cells[i].readings else 'missing', f'sum needs {t}')
                notes.append(f'{tag}: {"total" if i == len(cells) - 1 else "member " + str(i + 1)} unresolved (sum needs {t}, readings {cells[i].readings})')
        else:
            notes.append(f'{tag}: sum of dailies != total ({[c.value for c in cells]})')

    # cost per labour-hour
    lh = T['lh'].value
    derived = {}
    if lh:
        for tag, dc in (('bare', 'bare_daily'), ('op', 'op_daily')):
            lab = [m['vals'][dc].value for m in members if m['kind'] == 'labor']
            eq = [m['vals'][dc].value for m in members if m['kind'] == 'equipment']
            derived[f'{tag}_labor_daily'] = round(sum(lab), 2) if lab and None not in lab else None
            derived[f'{tag}_equip_daily'] = round(sum(eq), 2) if None not in eq else None
            tot = T[f'{tag}_total'].value
            for key, num in ((f'{tag}_labor_per_lh', derived[f'{tag}_labor_daily']),
                             (f'{tag}_equip_per_lh', derived[f'{tag}_equip_daily'] if eq else None),
                             (f'{tag}_total_per_lh', tot)):
                c = T[key]
                if num is None:
                    continue
                t = round(num / lh, 2)
                if c.value is None or abs(c.value - t) > 0.011:
                    if c.readings and is_compatible(t, c.readings):
                        c.set(t, 'identity', f'from {c.readings} via daily/LH')
                    elif c.value is not None:
                        notes.append(f'{key} printed {c.value} ({c.readings}) != {num}/{lh:g} = {t}')
                    elif c.readings:
                        notes.append(f'{key} readings {c.readings} incompatible with {t}')
                    else:
                        notes.append(f'{key} not read (expected {t})')
            tc, pc = T[f'{tag}_total'], T[f'{tag}_total_per_lh']
            ds = [m['vals'][dc].value for m in members]
            if tc.value is None and not tc.readings and None not in ds and pc.value is not None and pc.how in ('agree', 'single'):
                s = round(sum(ds), 2)
                if abs(pc.value - s / lh) < 0.0051:
                    tc.set(s, 'identity-noread', f'no OCR reading; sum of dailies {s} agrees with total_per_lh {pc.value} x LH {lh:g}')
    crew['derived'] = derived

    # final checks
    checks = {}
    lab_ok = all(m['qty'] is not None for m in members)
    for m in labor:
        for hc, dc in (('bare_hr', 'bare_daily'), ('op_hr', 'op_daily')):
            h, d = m['vals'][hc].value, m['vals'][dc].value
            if None in (h, d, m['qty']) or abs(h * 8 * m['qty'] - d) > 0.006:
                lab_ok = False
    checks['labor_daily=hr*8*qty'] = lab_ok
    checks['lh=8*sum(qty)'] = lh_calc is not None and T['lh'].value is not None and abs(lh_calc - T['lh'].value) < 0.01
    for dc, tc in (('bare_daily', 'bare_total'), ('op_daily', 'op_total')):
        ds = [m['vals'][dc].value for m in members]
        tot = T[tc].value
        checks[f'sum({dc})={tc}'] = None not in ds and tot is not None and abs(sum(ds) - tot) < SUM_TOL(len(members))
    has_eq = any(m['kind'] == 'equipment' for m in members)
    for key in ('bare_labor_per_lh', 'op_labor_per_lh', 'bare_total_per_lh', 'op_total_per_lh', 'bare_equip_per_lh', 'op_equip_per_lh'):
        checks[key] = False
    if lh:
        for key, num in (('bare_labor_per_lh', derived.get('bare_labor_daily')), ('op_labor_per_lh', derived.get('op_labor_daily')),
                         ('bare_total_per_lh', T['bare_total'].value), ('op_total_per_lh', T['op_total'].value)):
            c = T[key].value
            checks[key] = c is not None and num is not None and abs(num / lh - c) < 0.011
        for key, num in (('bare_equip_per_lh', derived.get('bare_equip_daily')), ('op_equip_per_lh', derived.get('op_equip_daily'))):
            c = T[key].value
            checks[key] = (not has_eq and c is None) or (has_eq and c is not None and num is not None and abs(num / lh - c) < 0.011)
    crew['checks'] = checks
    crew['notes'] = notes


def crew_needs_more(crew):
    if not all(crew['checks'].values()):
        return True
    for m in crew['members']:
        for k in ('bare_hr', 'bare_daily', 'op_hr', 'op_daily'):
            c = m['vals'][k]
            if c.readings and c.how != 'agree':
                return True
        if len(m['qty_readings']) < 2:
            return True
    for k in TOT_KEYS:
        c = crew['totals'][k]
        if c.readings and c.how != 'agree':
            return True
    return False


# ---------------------------------------------------------------- page parsing -------------------
# highest crew number printed in each series (2022 book); a larger number means the last digit is a letter suffix
SERIES_MAX = {'A': 13, 'B': 95, 'C': 35, 'D': 15, 'E': 30, 'F': 10, 'G': 10, 'H': 10, 'J': 10, 'K': 10, 'L': 15, 'M': 10, 'Q': 25, 'R': 35, 'W': 50}
DIGIT_SUFFIX = {'1': 'I', '0': 'O', '5': 'S', '8': 'B', '2': 'Z', '6': 'G'}


def norm_crew_id(cand):
    cand = cand.upper().strip('.,:;')
    m = re.match(r'^([A-Z])[-–—_C:. ]?([0-9OIL]{1,3})([A-Z0-9])?$', cand)
    if not m:
        return None
    letter, digits, suffix = m.groups()
    if letter not in SERIES_MAX:
        return None
    if not suffix and len(digits) >= 2 and digits[-1] in 'OIL' and digits[-2].isdigit():
        digits, suffix = digits[:-1], digits[-1]          # 'B-10L': the trailing letter is the suffix
    digits = digits.replace('O', '0').replace('I', '1').replace('L', '1')
    if len(digits) == 3 or int(digits) > SERIES_MAX[letter]:
        if suffix:
            return None
        digits, suffix = digits[:-1], digits[-1]
        if int(digits) > SERIES_MAX[letter]:
            return None
    if suffix and suffix.isdigit():
        suffix = DIGIT_SUFFIX.get(suffix)
        if not suffix:
            return None
    return f'{letter}-{int(digits)}{suffix or ""}'


# crew ids settled by looking at the page image (contact sheet of header crops): (page, side, y within 0.01)
EYE_IDS = [(764, 'L', 0.8623, 'A-3Q'), (768, 'R', 0.4712, 'B-10O'), (768, 'R', 0.6396, 'B-10Q'), (769, 'R', 0.4804, 'B-11Q'),
           (770, 'R', 0.8564, 'B-12O'), (771, 'L', 0.1955, 'B-12Q'), (772, 'L', 0.1051, 'B-13I'), (777, 'L', 0.0996, 'B-34Q'),
           (785, 'L', 0.7511, 'B-81A'), (794, 'R', 0.7124, 'H-2'), (796, 'R', 0.7552, 'Q-4')]


def eye_id(page, side, y):
    for p, sd, yy, cid in EYE_IDS:
        if p == page and sd == side and abs(yy - y) < 0.006:
            return cid
    return None


def finish_totals_fallback(cur):
    """a crew whose totals line was garbled: the last member line carrying $-values (and no Hr) is the totals"""
    if cur is None or cur.get('totals_by_src') is not None or not cur['members']:
        return
    last = cur['members'][-1]
    bs = last['by_src']
    if looks_like_totals(bs):
        cur['totals_by_src'] = bs
        cur['totals_y'] = last['y']
        cur['members'].pop()
        cur.setdefault('notes_pre', []).append('totals line identified by position/$ (its label was unreadable)')


def parse_page(page, rates, debug=False):
    srcs = load_sources(page)
    align_y(srcs)
    crews = []
    for side in 'LR':
        off = OFFS[str(page)][side]
        lines = build_lines(srcs, side, off)
        cur = None
        for ln in lines:
            if not (0.075 < ln['y'] < 0.955):
                continue
            kind, info = classify(ln)
            if debug:
                print(f'{side} {ln["y"]:.4f} {kind:7s}', ' | '.join(f"{w['src'][:2]}:{w['t']}" for w in ln['w'])[:160])
            if kind == 'header':
                if cur is not None and not cur['members'] and cur['totals_by_src'] is None and ln['y'] - cur['y'] < 0.013:
                    cur['id_readings'].update(info)      # same header read at slightly different y by another source
                    continue
                finish_totals_fallback(cur)
                cur = {'page': page, 'side': side, 'y': ln['y'], 'id_readings': info, 'members': [], 'totals_by_src': None}
                crews.append(cur)
            elif kind == 'skip' and info == 'colhdr':
                finish_totals_fallback(cur)
            elif kind == 'member' and cur is not None and cur['members'] and cur['totals_by_src'] is None and looks_like_totals(info, strict=False):
                cur['totals_by_src'] = info      # $-amounts, no hourly rate: the totals row with an unreadable label
                cur['totals_y'] = ln['y']
            elif kind == 'member' and cur is not None:
                q, d = desc_and_qty(info)
                if not q and not any(readings_for(info, c) for c in NUMCOLS):
                    continue
                if cur['totals_by_src'] is not None:
                    good = {k: v for k, v in info.items() if k in ('T400', 'IA')}
                    if not any(readings_for(good, c) for c in ('bare_daily', 'op_daily')):
                        continue      # stray words, not a row
                    # a member row after the totals: the next crew's header was not recognised
                    cur = {'page': page, 'side': side, 'y': ln['y'] - 0.015, 'id_readings': {}, 'members': [], 'totals_by_src': None,
                           'notes_pre': ['header line not found in the page OCRs; crew id read from a row crop']}
                    crews.append(cur)
                cur['members'].append({'member_no': len(cur['members']) + 1, 'by_src': info, 'y': ln['y']})
            elif kind == 'totals' and cur is not None and cur['totals_by_src'] is None:
                cur['totals_by_src'] = info
                cur['totals_y'] = ln['y']
        finish_totals_fallback(cur)
    # rows are >= 0.0115 apart: a 'member' within 0.0095 of its neighbour is a stray OCR line
    def support(m):
        bs = m['by_src']
        good = {k: v for k, v in bs.items() if k in ('T400', 'IA')}
        ncells = sum(1 for c in NUMCOLS if readings_for(good, c))
        q, _ = desc_and_qty(good)
        return (ncells, bool(q), 'T400' in bs, len(bs))
    for c in crews:
        ms = c['members']
        keep = []
        for m in ms:
            if keep and m['y'] - keep[-1]['y'] < 0.0095:
                if support(m) > support(keep[-1]):
                    keep[-1] = m
                continue
            keep.append(m)
        if c.get('totals_y') is not None and keep and c['totals_y'] - keep[-1]['y'] < 0.0095:
            keep.pop()
        if len(keep) != len(ms):
            c.setdefault('notes_pre', []).append(f'{len(ms) - len(keep)} stray OCR line(s) between rows dropped')
        c['members'] = keep
    crews = [c for c in crews if c['members'] or any(norm_crew_id(v) for v in c['id_readings'].values())]
    for c in crews:
        vote_id(c)
        for i, m in enumerate(c['members']):
            m['member_no'] = i + 1
        if c['totals_by_src'] is None and c['members']:
            # the totals row sits one row pitch (plus rule) below the last member: read it directly from the image
            ty = c['members'][-1]['y'] + 0.0138
            tw = row_ocr(page, c['side'], ty)
            if tw:
                c['totals_by_src'] = {'TROW': tw}
                c['totals_y'] = ty
                c.setdefault('notes_pre', []).append('totals line was unreadable in the page OCRs; read from a row crop')
            else:
                c.setdefault('notes_pre', []).append('no totals line found')
        build_cells(c)
        resolve_crew(c, rates)
        if crew_needs_more(c):
            for m in c['members']:
                if 'TROW' not in m['by_src']:
                    m['by_src']['TROW'] = row_ocr(page, c['side'], m['y'])
            if c['totals_by_src'] is not None and 'TROW' not in c['totals_by_src']:
                c['totals_by_src']['TROW'] = row_ocr(page, c['side'], c['totals_y'])
            if 'TROW' not in c['id_readings']:
                hw = row_ocr(page, c['side'], c['y'])
                for i, w in enumerate(hw[:2]):
                    if w['t'].lower().strip('.,:') in ('crew', 'craw', 'crow', 'cew', 'grew') and i + 1 < len(hw):
                        c['id_readings']['TROW'] = hw[i + 1]['t']
                        vote_id(c)
            build_cells(c)
            resolve_crew(c, rates)
            c['row_ocr'] = True
            if not all(c['checks'].values()) and cell_fallback(c, page):
                build_cells(c)
                resolve_crew(c, rates)
                c['cell_ocr'] = True
    return crews


def desc_key(d):
    words = re.sub(r'[^a-z0-9 ]', ' ', d.lower()).split()
    return ' '.join(w[:-1] if len(w) > 3 and w.endswith('s') else w for w in words)


def equipment_rate_check(all_crews, rates):
    """An equipment line's daily amount is quantity x the item's daily rate, and that rate is the same in
    every crew of the book.  Collect the rate per description (mode of daily/qty), then re-check each
    line's quantity (a lost leading dot or a misread count) against it."""
    groups = {}
    for c in all_crews:
        for m in c['members']:
            if m['kind'] != 'equipment' or m['qty'] is None:
                continue
            v = m['vals']['bare_daily'].value
            if v is None:
                continue
            k = desc_key(choose_desc(m['desc_readings'])[0])
            groups.setdefault(k, []).append((round(v / m['qty'], 2), m['qty'], len(m['qty_readings'])))
    ref = {}
    for k, lst in groups.items():
        cnt = {}
        for u, q, n in lst:
            cnt[u] = cnt.get(u, 0) + (2 if q != int(q) or n >= 2 else 1)
        u, w = max(cnt.items(), key=lambda kv: kv[1])
        if w >= 3 and w > sum(cnt.values()) / 2:
            ref[k] = u
    import difflib
    for c in all_crews:
        for m in c['members']:
            if m['kind'] != 'equipment' or m['vals']['bare_daily'].value is None:
                continue
            k = desc_key(choose_desc(m['desc_readings'])[0])
            if k not in ref:
                # fuzzy on the words only: the numbers (sizes, capacities) must be identical
                nums = re.findall(r'\d+', k)
                near = [r for r in difflib.get_close_matches(k, list(ref), n=3, cutoff=0.8) if re.findall(r'\d+', r) == nums]
                if not near:
                    continue
                k = near[0]
            v = m['vals']['bare_daily'].value
            if m['qty'] is not None and abs(v / m['qty'] - ref[k]) < 0.011:
                continue
            alts = [q for q in (m['qty_options'] + [m['qty']] if m['qty'] is not None else m['qty_options']) if q and abs(v / q - ref[k]) < 0.011]
            if alts:
                if m['qty'] != alts[0]:
                    c['notes'].append(f'{m["member_no"]}: equipment qty {alts[0]:g} (readings {m["qty_readings"]}) from the item rate {ref[k]} seen in other crews')
                    m['qty'] = alts[0]
                    if m['qty'] is not None:
                        c['checks']['labor_daily=hr*8*qty'] = c['checks']['labor_daily=hr*8*qty'] and all(mm['qty'] is not None for mm in c['members'])
            elif m['qty'] is None and abs(v / ref[k] - round(v / ref[k] * 8) / 8) < 0.002:
                q = round(v / ref[k] * 8) / 8
                c['notes'].append(f'{m["member_no"]}: equipment qty {q:g} from the item rate {ref[k]} seen in other crews (no quantity reading)')
                m['qty'] = q
                c['checks']['labor_daily=hr*8*qty'] = all(mm['qty'] is not None for mm in c['members']) and c['checks']['labor_daily=hr*8*qty'] or (
                    all(mm['qty'] is not None for mm in c['members']) and all(
                        mm['vals'][h].value is not None and mm['vals'][d].value is not None and abs(mm['vals'][h].value * 8 * mm['qty'] - mm['vals'][d].value) < 0.006
                        for mm in c['members'] if mm['kind'] == 'labor' for h, d in (('bare_hr', 'bare_daily'), ('op_hr', 'op_daily'))))
            else:
                c['notes'].append(f'{m["member_no"]}: equipment daily {v} / qty {m["qty"]} does not match the item rate {ref[k]} seen in other crews')


def vote_id(c):
    votes = {}
    for s, cand in c['id_readings'].items():
        cid = norm_crew_id(cand)
        if cid:
            votes[cid] = votes.get(cid, 0) + 1
    if votes:
        top = max(votes.items(), key=lambda kv: kv[1])
        c['crew_id'] = top[0]
        c['id_conf'] = 'agree' if top[1] >= 2 and len(votes) == 1 else ('single' if len(votes) == 1 else 'conflict:' + str(votes))
    else:
        c['crew_id'] = None
        c['id_conf'] = 'none:' + str(c['id_readings'])
    seen = eye_id(c['page'], c['side'], c['y'])
    if seen:
        c['crew_id'] = seen
        c['id_conf'] = 'agree'
        c.setdefault('notes_pre', []).append(f'crew id {seen} confirmed by eye on the page image (OCR readings {list(c["id_readings"].values())})')


def load_rates():
    base, op = set(), set()
    for r in csv.DictReader(open(f'{BOOK}/derived/trade_rates_2022.csv')):
        if r['base_hourly']:
            b = float(r['base_hourly']); base |= {b, round(b + 0.5, 2), round(b + 2.0, 2)}
        if r['rate_op_hourly']:
            op.add(float(r['rate_op_hourly']))
    return {'bare': base, 'op': op}


def choose_desc(d):
    """the reading whose words are most confirmed by the other readings (ties: T400, IA, TROW, T360)"""
    order = ('T400', 'IA', 'TROW', 'T360', 'TCELL')
    best, bs = '', None
    bscore = -1
    for s in order:
        if not d.get(s):
            continue
        toks = [t.lower().strip('.,') for t in d[s].split()]
        others = [set(t.lower().strip('.,') for t in d[o].split()) for o in order if o != s and d.get(o)]
        score = sum(any(t in oth for oth in others) for t in toks) - 0.5 * len(re.sub(r"[A-Za-z0-9 ,.&()/'\"x#-]", '', d[s]))
        if score > bscore:
            best, bs, bscore = d[s], s, score
    return best, bs


def cell_note(k, cell):
    if cell.how in ('identity', 'identity-noread'):
        return f'{k} {cell.note}'
    if cell.how in ('unresolved', 'conflict'):
        return f'UNRESOLVED {k}: {cell.readings}'
    if cell.how == 'missing':
        return f'UNRESOLVED {k}: no reading'
    if cell.how == 'single':
        return f'{k} single reading {cell.readings}'
    return ''


if __name__ == '__main__':
    rates = load_rates()
    pages = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(PAGES)
    debug = '--debug' in sys.argv
    all_crews = []
    for page in pages:
        crews = parse_page(page, rates, debug)
        all_crews += crews
        print(f'  page {page}: {len(crews)} crews', flush=True)
    equipment_rate_check(all_crews, rates)
    for c in all_crews:
        if True:
            page = c['page']
            ok = all(c['checks'].values())
            print(f"p{page} {c['side']} {c['crew_id']} ({c['id_conf']}) members={len(c['members'])} ok={ok}{' rowocr' if c.get('row_ocr') else ''}")
            if not ok or debug:
                for m in c['members']:
                    print('   ', m['member_no'], m['kind'], m['qty'], m['qty_readings'], choose_desc(m['desc_readings'])[0][:40],
                          {k: v for k, v in m['vals'].items() if k in ('bare_hr', 'bare_daily', 'op_hr', 'op_daily')})
                print('    totals', c['totals'])
                print('    checks', {k: v for k, v in c['checks'].items() if not v})
                print('    notes', c['notes'], c.get('notes_pre'))
    with open(f'{BOOK}/derived/crews_2022.csv', 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['crew_id', 'page_pdf', 'member_no', 'kind', 'quantity', 'description', 'bare_hr', 'bare_daily', 'op_hr', 'op_daily', 'notes'])
        for c in all_crews:
            for m in c['members']:
                desc, src = choose_desc(m['desc_readings'])
                notes = [n for n in (cell_note(k, m['vals'][k]) for k in ('bare_hr', 'bare_daily', 'op_hr', 'op_daily')
                                     if not (m['kind'] == 'equipment' and k in ('bare_hr', 'op_hr'))) if n]
                if m['qty'] is None:
                    notes.append(f'UNRESOLVED quantity: {m["qty_readings"]}')
                elif len(set(m['qty_readings'].values())) > 1:
                    notes.append(f'quantity readings {m["qty_readings"]}')
                wr.writerow([c['crew_id'] or '', c['page'], m['member_no'], m['kind'],
                             '' if m['qty'] is None else f'{m["qty"]:g}', desc,
                             fmt(m['vals']['bare_hr'].value) if m['kind'] == 'labor' else '',
                             fmt(m['vals']['bare_daily'].value),
                             fmt(m['vals']['op_hr'].value) if m['kind'] == 'labor' else '',
                             fmt(m['vals']['op_daily'].value), '; '.join(notes)])
    with open(f'{BOOK}/derived/crews_2022_totals.csv', 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['crew_id', 'page_pdf', 'labor_hours_per_day', 'bare_daily_total', 'op_daily_total', 'bare_labor_daily', 'bare_equip_daily',
                     'op_labor_daily', 'op_equip_daily', 'bare_labor_per_lh', 'op_labor_per_lh', 'bare_equip_per_lh', 'op_equip_per_lh',
                     'bare_total_per_lh', 'op_total_per_lh', 'checks_ok', 'notes'])
        for c in all_crews:
            T, d = c['totals'], c['derived']
            notes = list(c.get('notes_pre', [])) + c['notes']
            if c['id_conf'] != 'agree':
                notes.append(f'crew id {c["id_conf"]} {c["id_readings"]}')
            for k in TOT_KEYS:
                n = cell_note(k, T[k])
                if n and not n.startswith(k + ' single'):
                    notes.append(n)
            failed = [k for k, v in c['checks'].items() if not v]
            if failed:
                notes.append('CHECKS FAILED: ' + ', '.join(failed))
            lhv = T['lh'].value
            wr.writerow([c['crew_id'] or '', c['page'], '' if lhv is None else f'{lhv:g}', fmt(T['bare_total'].value), fmt(T['op_total'].value),
                         fmt(d.get('bare_labor_daily')), fmt(d.get('bare_equip_daily')), fmt(d.get('op_labor_daily')), fmt(d.get('op_equip_daily')),
                         fmt(T['bare_labor_per_lh'].value), fmt(T['op_labor_per_lh'].value), fmt(T['bare_equip_per_lh'].value), fmt(T['op_equip_per_lh'].value),
                         fmt(T['bare_total_per_lh'].value), fmt(T['op_total_per_lh'].value),
                         'true' if not failed else 'false', '; '.join(notes)])
    n_ok = sum(all(c['checks'].values()) for c in all_crews)
    print(f'crews {len(all_crews)} ok {n_ok} members {sum(len(c["members"]) for c in all_crews)}')
    json.dump([{'crew_id': c['crew_id'], 'id_conf': c['id_conf'], 'id_readings': c['id_readings'], 'page': c['page'], 'side': c['side'], 'y': c['y'],
                'checks': c['checks'], 'notes': c['notes'], 'notes_pre': c.get('notes_pre', []), 'totals_y': c.get('totals_y'),
                'members': [{'no': m['member_no'], 'y': m['y'], 'qty': m['qty'], 'qty_readings': m['qty_readings'], 'kind': m['kind'], 'desc': m['desc_readings'],
                             'vals': {k: [v.value, v.how, v.readings] for k, v in m['vals'].items()}} for m in c['members']],
                'totals': {k: [v.value, v.how, v.readings] for k, v in c['totals'].items()}} for c in all_crews],
              open(f'{BOOK}/work/crews_raw.json', 'w'), indent=1)
