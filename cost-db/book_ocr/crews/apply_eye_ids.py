#!/usr/bin/env python3
"""Apply the by-eye crew-id table (EYE_IDS in parse_crews.py) to work/crews_raw.json and the two
derived CSVs without re-running the parse (ids are labels; nothing numeric changes)."""
import csv, json, re, sys
sys.path.insert(0, '/tmp/claude-0/book/scripts_crews')
import importlib.util
spec = importlib.util.spec_from_file_location('pc', '/tmp/claude-0/book/scripts_crews/parse_crews.py')
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)
BOOK = '/tmp/claude-0/book'
crews = json.load(open(f'{BOOK}/work/crews_raw.json'))
changed = {}
for i, c in enumerate(crews):
    # undo any earlier override note, re-vote from the OCR readings, then apply the table
    c['notes_pre'] = [n for n in c.get('notes_pre', []) if not n.startswith('crew id ') or 'confirmed by eye' not in n]
    pc.vote_id(c)
    seen = pc.eye_id(c['page'], c['side'], c['y'])
    if seen and seen != c['crew_id']:
        pass
    if seen:
        changed[i] = (c['crew_id'], seen)
for i, (old, new) in changed.items():
    print(f'#{i} p{crews[i]["page"]}{crews[i]["side"]} y={crews[i]["y"]:.4f} {old} -> {new}')
json.dump(crews, open(f'{BOOK}/work/crews_raw.json', 'w'), indent=1)

# members CSV: rows follow the crews in order
rows = list(csv.reader(open(f'{BOOK}/derived/crews_2022.csv')))
hdr, body = rows[0], rows[1:]
k = 0
for i, c in enumerate(crews):
    for m in c['members']:
        r = body[k]
        assert int(r[1]) == c['page'] and int(r[2]) == m['no'], (i, k, r[:3], c['page'], m['no'])
        r[0] = c['crew_id'] or ''
        k += 1
assert k == len(body), (k, len(body))
with open(f'{BOOK}/derived/crews_2022.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(body)
# totals CSV: one row per crew
rows = list(csv.reader(open(f'{BOOK}/derived/crews_2022_totals.csv')))
hdr, body = rows[0], rows[1:]
assert len(body) == len(crews)
for r, c in zip(body, crews):
    assert int(r[1]) == c['page']
    r[0] = c['crew_id'] or ''
    notes = [n for n in r[-1].split('; ') if n and not n.startswith('crew id ')]
    if c['id_conf'] != 'agree':
        notes.append(f'crew id {c["id_conf"]} {c["id_readings"]}')
    notes = [n for n in c.get('notes_pre', []) if 'confirmed by eye' in n] + notes
    r[-1] = '; '.join(dict.fromkeys(notes))
with open(f'{BOOK}/derived/crews_2022_totals.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(body)
ids = [c['crew_id'] for c in crews]
print('crews', len(crews), 'unique ids', len(set(ids)), 'dups', sorted({i for i in ids if i and ids.count(i) > 1}), 'none', sum(i is None for i in ids))
