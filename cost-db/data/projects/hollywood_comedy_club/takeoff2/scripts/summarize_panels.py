"""Summarise panels_extracted.csv (from extract_panels.py): per panel, count of described
circuits by breaker (amps/poles) and list kitchen-equipment, HVAC, lighting, LV-related
descriptions. Multi-pole breakers are listed once (continuation rows read '-').
Usage: python3 -I summarize_panels.py panels_extracted.csv
"""
import sys, csv, collections, re
rows = list(csv.DictReader(open(sys.argv[1])))
SKIP = {'', 'x', '-', 'SPARE', 'Spare', 'SPACE', 'END OF PANEL', '#META'}
BLEED = re.compile(r'(wilshire|los angeles|t e l|RESTRICTIONS|Kelly Architects|Boulevard|Club$|90028|Comedy$|Hollywood,?$|PROJECT$|^- 6263|Calculations|^by:|Checked|Drawn|Origin|Scale|IFC|Shown|Job QC|XXX|RL EL|QC Jan|INFO|Date:|2026)')
def clean(d):
    d = d.strip()
    d = BLEED.sub('', d).strip(' -')
    return d
out = {}
for r in rows:
    p = r['panel']
    o = out.setdefault(p, {'ckts': [], 'meta': ''})
    if r['ldesc'] == '#META':
        o['meta'] = r['lva'] + ' | ' + r['rdesc']; continue
    for side in ('l', 'r'):
        d = clean(r[side + 'desc']); b = r[side + 'bkr'].strip(); pl = r[side + 'pole'].strip()
        if d in SKIP or not d: continue
        if b in ('-', '') and pl in ('-', '', 'x') and side == 'l' and r['lva'] in ('-', 'x', ''):
            # continuation line of a multipole breaker or unsized; keep only if description is new
            pass
        o['ckts'].append((d, b if b not in ('', 'x') else '?', pl if pl not in ('', 'x') else '?', r[side + 'va']))
for p, o in out.items():
    print(f"\n=== PANEL {p}: {o['meta']}")
    c = collections.Counter((b, pl) for d, b, pl, va in o['ckts'])
    print("  described circuit lines:", len(o['ckts']), " by (bkr A, poles):", dict(sorted(c.items())))
    for d, b, pl, va in o['ckts']:
        print(f"    {b:>4}A/{pl:<2}P {va:>6}  {d}")
