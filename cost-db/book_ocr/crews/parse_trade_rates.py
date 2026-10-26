#!/usr/bin/env python3
"""TABLE 1: labor trade rates (PDF page 963). Two OCR readings (360 dpi book OCR, 400 dpi re-render),
cells by x position, arithmetic verification, output derived/trade_rates_2022.csv."""
import csv, json, re, sys
sys.path.insert(0, '/tmp/claude-0/book/scripts_crews')
from common import *

# ---- readings -------------------------------------------------------------
# 360 dpi: page 2818 x 3791
w360 = load_tsv_words(f'{BOOK}/ocr/p0963.tsv', 0, 0, 2818, 3791)
# 400 dpi crop
bx = open(f'{BOOK}/work/t400/p0963_T.box').read().split()
x0, y0, x1, y1, W, H = map(int, bx)
w400 = load_tsv_words(f'{BOOK}/work/t400/p0963_T.tsv', x0, y0, W, H)

# column boundaries in page-width fractions (from the 400 dpi crop positions / 3132)
COLS = [('abbr', 0.00, 0.085), ('trade', 0.085, 0.36), ('base_hourly', 0.36, 0.415), ('base_daily', 0.415, 0.48),
        ('wc_pct', 0.48, 0.545), ('fixed_oh_pct', 0.545, 0.60), ('overhead_pct', 0.60, 0.655), ('profit_pct', 0.655, 0.70),
        ('total_op_pct', 0.70, 0.775), ('op_amount_hourly', 0.775, 0.835), ('rate_op_hourly', 0.835, 0.895), ('rate_op_daily', 0.895, 1.0)]
NUMCOLS = [c for c, _, _ in COLS[2:]]


def col_of(w):
    xc = (w['x0'] + w['x1']) / 2
    for name, a, b in COLS:
        if a <= xc < b:
            return name
    return None


def table_rows(words, ytol):
    rows = []
    for ln in group_lines(words, ytol):
        if not (0.395 < ln['y'] < 0.94):
            continue
        cells = {}
        for w in ln['w']:
            c = col_of(w)
            if c is None:
                continue
            t = w['t'].strip('|}{')
            if c not in ('abbr', 'trade') and not re.search(r'[0-9OoIl]', t):
                continue   # rule fragments ('|', '}', 'S$') in numeric columns
            if not t:
                continue
            cells.setdefault(c, []).append(t)
        if 'trade' not in cells:
            continue
        rows.append({'y': ln['y'], 'cells': {k: ' '.join(v) for k, v in cells.items()}})
    return rows


r360 = table_rows(w360, 0.006)
r400 = table_rows(w400, 0.006)
print(len(r360), len(r400), 'rows')

# align rows of the two readings by y (same page geometry)
rows = []
for a in r400:
    b = min(r360, key=lambda r: abs(r['y'] - a['y']))
    if abs(b['y'] - a['y']) > 0.006:
        b = None
    rows.append((a, b))


def cand(tok):
    """candidate values from a token: direct normalisation plus decimal repair"""
    if tok is None:
        return []
    out = []
    v, fl = norm_num_token(tok)
    if v is not None:
        if 'nodec' in fl:
            out.append((v / 100, 'nodec'))   # a lost decimal point is the common failure
            out.append((v / 10, 'nodec'))
            out.append((v, 'nodec'))
        else:
            out.append((v, 'ok' if 'fixed' not in fl else 'fixed'))
    return out


KNOWN_ABBR = set('Skwk Clab Asbe Boil Bric Brhe Carp Cefi Elec Elev Eqhv Eqmd Eqlt Eqol Eqmm Glaz Lath Marb Mill Mstz Pord Psst Pape Pile Plas Plah Plum Rodm Rofc Rots Rohe Shee Spri Stpi Ston Sswk Tilf Tilh Trlt Trhv Sswl Wrck'.split())
FIXED_OH = None
PROFIT = None
out = []
for a, b in rows:
    ca, cb = a['cells'], (b['cells'] if b else {})
    notes = []
    abbr_a, abbr_b = (ca.get('abbr') or '').strip(), (cb.get('abbr') or '').strip()
    if abbr_a in KNOWN_ABBR: abbr = abbr_a
    elif abbr_b in KNOWN_ABBR: abbr = abbr_b
    elif abbr_a == abbr_b: abbr = abbr_a
    else:
        abbr = abbr_a or abbr_b; notes.append(f'abbr readings differ: {abbr_a!r} / {abbr_b!r}')
    if abbr and abbr not in KNOWN_ABBR:
        near = [k for k in KNOWN_ABBR if lev(k.lower(), abbr.lower()) <= 1 or lev(k.lower(), abbr_b.lower()) <= 1]
        if len(near) == 1:
            notes.append(f'abbr read as {abbr!r}/{abbr_b!r}, matched to expected {near[0]!r}'); abbr = near[0]
        else:
            notes.append('abbr not in expected list')
    trade_a, trade_b = ca.get('trade', ''), cb.get('trade', '')
    if trade_a == trade_b:
        trade = trade_a
    else:
        bad = lambda t: len(re.sub(r"[A-Za-z0-9 ,&()$./*'-]", '', t))
        trade = min((trade_a, trade_b), key=bad)
        notes.append(f'trade text differs between OCRs: {trade_a!r} / {trade_b!r}')
    vals = {}
    toks = {}
    for c in NUMCOLS:
        ta, tb = ca.get(c), cb.get(c)
        toks[c] = (ta, tb)
        la, lb = cand(ta), cand(tb)
        # agreed direct reading?
        direct_a = [v for v, k in la if k != 'nodec']
        direct_b = [v for v, k in lb if k != 'nodec']
        rep_a = [v for v, k in la if k == 'nodec']
        rep_b = [v for v, k in lb if k == 'nodec']
        if direct_a and direct_b and abs(direct_a[0] - direct_b[0]) < 0.005:
            vals[c] = direct_a[0]
        elif (direct_a and any(abs(direct_a[0] - r) < 0.005 for r in rep_b)) or (direct_b and any(abs(direct_b[0] - r) < 0.005 for r in rep_a)):
            vals[c] = (direct_a or direct_b)[0]
            notes.append(f'{c}: one reading lost its decimal point ({ta!r} / {tb!r}), digits agree')
        else:
            vals[c] = None  # resolve below with the identities
            if ta != tb:
                notes.append(f'{c}: readings {ta!r} / {tb!r}')
    # Fixed overhead and profit are printed on the first row only (arrows below): carry down
    if vals.get('fixed_oh_pct') is not None:
        FIXED_OH = vals['fixed_oh_pct']
    elif toks['fixed_oh_pct'] == (None, None):
        vals['fixed_oh_pct'] = FIXED_OH; notes.append('fixed_oh carried from first row (arrow)')
    if vals.get('profit_pct') is not None:
        PROFIT = vals['profit_pct']
    elif toks['profit_pct'] == (None, None):
        vals['profit_pct'] = PROFIT; notes.append('profit carried from first row (arrow)')

    # ---- resolve unresolved cells with the identities ----
    def pick(c, target):
        """accept target for column c if compatible with at least one OCR token"""
        ta, tb = toks[c]
        for t in (ta, tb):
            if t is not None and compatible(target, t):
                return True
        return False

    for _ in range(3):
        v = vals
        # Daily = Hourly x 8
        if v['base_hourly'] is None and v['base_daily'] is not None:
            t = round(v['base_daily'] / 8, 2)
            if pick('base_hourly', t): v['base_hourly'] = t; notes.append(f'base_hourly from daily/8 ({toks["base_hourly"]})')
        if v['base_daily'] is None and v['base_hourly'] is not None:
            t = round(v['base_hourly'] * 8, 2)
            if pick('base_daily', t): v['base_daily'] = t; notes.append(f'base_daily from hourly*8 ({toks["base_daily"]})')
        # F = B + C + D + E
        if v['total_op_pct'] is None and None not in (v['wc_pct'], v['fixed_oh_pct'], v['overhead_pct'], v['profit_pct']):
            t = round(v['wc_pct'] + v['fixed_oh_pct'] + v['overhead_pct'] + v['profit_pct'], 1)
            if pick('total_op_pct', t): v['total_op_pct'] = t; notes.append(f'total_op_pct from B+C+D+E ({toks["total_op_pct"]})')
        if v['total_op_pct'] is None and None not in (v['base_hourly'], v['op_amount_hourly']):
            # G = A x F  ->  F = G / A (G is rounded to 0.05, so F may be off by 0.1: the token must agree)
            t = round(v['op_amount_hourly'] / v['base_hourly'] * 100, 1)
            if pick('total_op_pct', t): v['total_op_pct'] = t; notes.append(f'total_op_pct from G/A ({toks["total_op_pct"]})')
        if v['wc_pct'] is None and None not in (v['total_op_pct'], v['fixed_oh_pct'], v['overhead_pct'], v['profit_pct']):
            t = round(v['total_op_pct'] - v['fixed_oh_pct'] - v['overhead_pct'] - v['profit_pct'], 1)
            if pick('wc_pct', t): v['wc_pct'] = t; notes.append(f'wc_pct from F-C-D-E ({toks["wc_pct"]})')
        if v['overhead_pct'] is None and None not in (v['total_op_pct'], v['fixed_oh_pct'], v['wc_pct'], v['profit_pct']):
            t = round(v['total_op_pct'] - v['fixed_oh_pct'] - v['wc_pct'] - v['profit_pct'], 1)
            if pick('overhead_pct', t): v['overhead_pct'] = t; notes.append(f'overhead_pct from F-B-C-E ({toks["overhead_pct"]})')
        # H = A + G ; I = H x 8 ; G = A x F
        if v['rate_op_hourly'] is None:
            t = None
            if v['rate_op_daily'] is not None:
                t = round(v['rate_op_daily'] / 8, 2)
            elif None not in (v['base_hourly'], v['op_amount_hourly']):
                t = round(v['base_hourly'] + v['op_amount_hourly'], 2)
            if t is not None and pick('rate_op_hourly', t): v['rate_op_hourly'] = t; notes.append(f'rate_op_hourly from identity ({toks["rate_op_hourly"]})')
        if v['rate_op_daily'] is None and v['rate_op_hourly'] is not None:
            t = round(v['rate_op_hourly'] * 8, 2)
            if pick('rate_op_daily', t): v['rate_op_daily'] = t; notes.append(f'rate_op_daily from H*8 ({toks["rate_op_daily"]})')
        if v['op_amount_hourly'] is None:
            t = None
            if None not in (v['rate_op_hourly'], v['base_hourly']):
                t = round(v['rate_op_hourly'] - v['base_hourly'], 2)
            elif None not in (v['base_hourly'], v['total_op_pct']):
                t = round(v['base_hourly'] * v['total_op_pct'] / 100, 2)
            if t is not None and pick('op_amount_hourly', t): v['op_amount_hourly'] = t; notes.append(f'op_amount_hourly from identity ({toks["op_amount_hourly"]})')
        if v['base_hourly'] is None and None not in (v['rate_op_hourly'], v['op_amount_hourly']):
            t = round(v['rate_op_hourly'] - v['op_amount_hourly'], 2)
            if pick('base_hourly', t): v['base_hourly'] = t; notes.append(f'base_hourly from H-G ({toks["base_hourly"]})')

    # ---- checks ----
    v = vals
    checks = []
    def ck(name, cond):
        checks.append((name, cond))
    if None not in (v['base_hourly'], v['base_daily']):
        ck('daily=8h', abs(v['base_hourly'] * 8 - v['base_daily']) < 0.011)
    if None not in (v['wc_pct'], v['fixed_oh_pct'], v['overhead_pct'], v['profit_pct'], v['total_op_pct']):
        ck('F=B+C+D+E', abs(v['wc_pct'] + v['fixed_oh_pct'] + v['overhead_pct'] + v['profit_pct'] - v['total_op_pct']) < 0.051)
    if None not in (v['base_hourly'], v['total_op_pct'], v['op_amount_hourly']):
        # printed amount is rounded to the nearest 0.05
        # F is printed rounded to 0.1 % and G to the nearest 0.05, so allow for both roundings
        ck('G=A*F', abs(v['base_hourly'] * v['total_op_pct'] / 100 - v['op_amount_hourly']) < 0.03 + v['base_hourly'] * 0.0006)
    if None not in (v['base_hourly'], v['op_amount_hourly'], v['rate_op_hourly']):
        ck('H=A+G', abs(v['base_hourly'] + v['op_amount_hourly'] - v['rate_op_hourly']) < 0.011)
    if None not in (v['rate_op_hourly'], v['rate_op_daily']):
        ck('I=8H', abs(v['rate_op_hourly'] * 8 - v['rate_op_daily']) < 0.011)
    missing = [c for c in NUMCOLS if v[c] is None]
    failed = [n for n, ok in checks if not ok]
    for c in missing:
        notes.append(f'UNRESOLVED {c}: tokens {toks[c]}')
    for n in failed:
        notes.append(f'CHECK FAILED {n}')
    row = {'abbr': abbr, 'trade': trade, **{c: fmt(v[c]) for c in NUMCOLS},
           'checks_ok': 'true' if (not missing and not failed and len(checks) == 5) else 'false',
           'notes': '; '.join(notes)}
    row['_toks'] = toks; row['_trade_b'] = trade_b
    out.append(row)

for r in out:
    print(r['abbr'], '|', r['trade'], '|', [r[c] for c in NUMCOLS], r['checks_ok'], r['notes'])
FIELDS = ['abbr', 'trade'] + NUMCOLS + ['checks_ok', 'notes']
with open(f'{BOOK}/derived/trade_rates_2022.csv', 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=FIELDS)
    wr.writeheader()
    for r in out:
        wr.writerow({k: r[k] for k in FIELDS})
print('rows', len(out), 'checks_ok', sum(r['checks_ok'] == 'true' for r in out))

json.dump([{k: v for k, v in r.items() if not k.startswith('_')} for r in out], open(f'{BOOK}/work/trade_rates_raw.json', 'w'), indent=1)
