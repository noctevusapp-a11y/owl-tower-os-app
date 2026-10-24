#!/usr/bin/env python3
"""Tally the crew parse (work/crews_raw.json + derived CSVs) and print the lists for the report."""
import csv, json, re, sys, collections
sys.path.insert(0, '/tmp/claude-0/book/scripts_crews')
from common import BOOK

crews = json.load(open(f'{BOOK}/work/crews_raw.json'))
ids = [c['crew_id'] for c in crews]
dups = sorted({i for i in ids if ids.count(i) > 1 and i})
series = collections.Counter((c['crew_id'] or '?')[0] for c in crews)
n_ok = sum(all(c['checks'].values()) for c in crews)
fails = collections.Counter()
for c in crews:
    for k, v in c['checks'].items():
        if not v:
            fails[k] += 1
print('crews', len(crews), 'unique ids', len(set(ids)), 'ok', n_ok)
print('series', dict(sorted(series.items())))
print('duplicate ids', dups)
print('failing checks', dict(fails))
print('ids unresolved/uncertain:', [(c['page'], c['side'], c['crew_id'], c['id_conf'], c['id_readings']) for c in crews if c['id_conf'] != 'agree'])

# unresolved cells
unres_members, unres_totals = [], []
noread = []
for c in crews:
    for m in c['members']:
        for k in ('bare_hr', 'bare_daily', 'op_hr', 'op_daily'):
            if m['kind'] == 'equipment' and k in ('bare_hr', 'op_hr'):
                continue
            v, how, rd = m['vals'][k]
            if v is None:
                unres_members.append((c['crew_id'], c['page'], m['no'], k, rd))
            elif how == 'identity-noread':
                noread.append((c['crew_id'], c['page'], f'member {m["no"]} {k}'))
        if m['qty'] is None:
            unres_members.append((c['crew_id'], c['page'], m['no'], 'quantity', m['qty_readings']))
    for k, (v, how, rd) in c['totals'].items():
        if v is None and k not in ('bare_equip_per_lh', 'op_equip_per_lh'):
            unres_totals.append((c['crew_id'], c['page'], k, rd))
        elif v is None and any(mm['kind'] == 'equipment' for mm in c['members']):
            unres_totals.append((c['crew_id'], c['page'], k, rd))
        elif how == 'identity-noread':
            noread.append((c['crew_id'], c['page'], k))
print('\nunresolved member cells', len(unres_members))
for u in unres_members:
    print('  ', u)
print('\nunresolved totals cells', len(unres_totals))
for u in unres_totals:
    print('  ', u)
print('\ncells with no OCR reading filled from two agreeing identities', len(noread))
for u in noread:
    print('  ', u)
print('\ncrews failing checks:')
for c in crews:
    if not all(c['checks'].values()):
        print('  ', c['crew_id'], c['page'], [k for k, v in c['checks'].items() if not v], (c['notes'] + c['notes_pre'])[:3])
