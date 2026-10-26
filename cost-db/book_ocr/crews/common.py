"""Shared helpers: TSV/IA loading, line grouping, numeric token normalisation."""
import csv, json, re

BOOK = '/tmp/claude-0/book'


def load_tsv_words(path, x_off=0, y_off=0, page_w=1.0, page_h=1.0):
    """tesseract TSV -> list of words with normalised coords (0..1 of the full page)."""
    words = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
            if r['level'] != '5':
                continue
            t = r['text'].strip()
            if not t:
                continue
            l, tp, w, h = int(r['left']), int(r['top']), int(r['width']), int(r['height'])
            words.append({
                'x0': (l + x_off) / page_w, 'y0': (tp + y_off) / page_h,
                'x1': (l + w + x_off) / page_w, 'y1': (tp + h + y_off) / page_h,
                't': t, 'conf': float(r['conf']),
            })
    return words


def load_ia_words(path):
    d = json.load(open(path))
    return [dict(w, conf=None) for w in d['words']]


def group_lines(words, ytol):
    """Group words into lines by y-centre proximity (greedy, sorted by y)."""
    ws = sorted(words, key=lambda w: ((w['y0'] + w['y1']) / 2, w['x0']))
    lines = []
    for w in ws:
        yc = (w['y0'] + w['y1']) / 2
        if lines and abs(lines[-1]['y'] - yc) < ytol:
            ln = lines[-1]
            ln['w'].append(w)
            n = len(ln['w'])
            ln['y'] = (ln['y'] * (n - 1) + yc) / n
        else:
            lines.append({'y': yc, 'w': [w]})
    for ln in lines:
        ln['w'].sort(key=lambda w: w['x0'])
    return lines


NUM_RE = re.compile(r'^[\$S§s]?\s*\(?\s*([0-9OoIl|,\.\s/\]]+)\)?%?$')


def norm_num_token(t):
    """Normalise an OCR token that should be a number. Returns (value, flags) or (None, reason).
    flags: set of strings: 'dollar', 'fixed' (character repairs made), 'nodec' (no decimal point found)."""
    s = t.strip()
    flags = set()
    if s.startswith(('$', 'S$', '$S')):
        flags.add('dollar')
    s = s.strip('|}{ ')
    s = re.sub(r'%[\]\}\|]*$', '%', s)
    s = re.sub(r'(\d)[.,:;]+$', r'\1', s)      # trailing punctuation after the last digit
    pct = s.endswith('%')
    s = s.lstrip('$S§s ').rstrip('%').strip()
    s = s.replace('|', '').replace(']', '1').replace('}', '').replace(' ', '')
    s2 = s.replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1').replace('/', '7')
    if s2 != s:
        flags.add('fixed')
    s = s2
    # comma used as decimal point (e.g. 43,30) -> treat any comma as decimal if it is followed by exactly 2 digits
    # and there is no other decimal point; a thousands comma ("1,086.40") is removed.
    if ',' in s:
        if '.' in s:
            s = s.replace(',', '')
        elif re.fullmatch(r'\d+,\d{1,2}', s):
            s = s.replace(',', '.')
            flags.add('fixed')
        elif re.fullmatch(r'\d{1,3},\d{3}', s):
            s = s.replace(',', '')
            flags.add('fixed')
        else:
            return None, 'bad-comma'
    if s.count('.') > 1:
        return None, 'multi-dot'
    if not re.fullmatch(r'\d*\.?\d+', s):
        return None, 'not-num'
    if '.' not in s and not pct:
        flags.add('nodec')
    elif re.fullmatch(r'\d*\.\d', s):
        flags.add('onedec')
    try:
        return float(s), flags
    except ValueError:
        return None, 'not-num'


def digits_only(v):
    """Digit string of a number formatted to 2 decimals (for compatibility checks)."""
    return f'{v:.2f}'.replace('.', '').lstrip('0') or '0'


def compatible(v, tok):
    """Is value v compatible with OCR token tok?  Exact digits (a lost decimal point is fine), or one
    substituted digit; one dropped/extra digit only for a token without a decimal separator (so that
    '182.40' is never taken for 1824.00)."""
    t = tok.replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1').replace(']', '1').replace('/', '7')
    d2 = re.sub(r'[^0-9]', '', t).lstrip('0') or '0'
    dotted = bool(re.search(r'\d[.,]\d', t))
    forms = {digits_only(v), (f'{v:g}'.replace('.', '').lstrip('0') or '0')}
    for d1 in forms:
        if d1 == d2:
            return True
        if len(d1) == len(d2) and sum(a != b for a, b in zip(d1, d2)) == 1:
            return True
        if not dotted and abs(len(d1) - len(d2)) == 1 and lev(d1, d2) == 1:
            return True
        if dotted and len(d1) == len(d2) + 1 and d1.startswith(d2):
            return True      # dropped last digit ('51.1' for 51.11)
    return False


def lev(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fmt(v):
    return '' if v is None else f'{v:.2f}'
