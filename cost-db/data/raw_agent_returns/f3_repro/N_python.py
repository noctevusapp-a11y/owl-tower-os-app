from prelude import *
import decimal

def hdr(t): print('\n=== ' + t)

hdr('F3-04 rental_day path drops fuel silently')
def mk(members, **eq):
    db = S.real_db(); S.validate_definitions(db); S.add_source(db)
    S.add_labor_actual(db, 'TEST-LRT-CEM', 'TR-CEM', 40)
    S.set_crew(db, 'CRW-CON-FLAT', 8, members)
    S.set_productivity(db, 'WI-CON-001', 2, 8, 2000)
    S.add_equipment_rate(db, 'TEST-EQR-PT', 'EQ-PTROWEL', **eq)
    return db
db = mk([('labor', 'TR-CEM', 2, False), ('equipment', 'EQ-PTROWEL', 1, False)], rate_hr=25, rate_day=150, fuel_included=False, fuel_cost=9)
for basis in ('hourly', 'rental_day'):
    r = Engine(db).unit_cost('WI-CON-001', 1, S.params(equipment_basis=basis))
    l = [x for x in r.lines if x['line_kind'] == 'equipment'][0]
    print(basis, 'equipment $/SF =', l['unit_cost'], '| fuel flags:', [w for w in l['warnings'] if 'FUEL' in w])
print('expected: hourly (25+9)*8/2000 = 0.136 (ok); rental_day 150/2000 = 0.075 -> fuel (fuel_included=False, fuel_cost_hr=9) is dropped with NO flag')

hdr('F3-05 crew_members.labor_rate_id pin ("overrides resolution") is ignored')
db = S.priced_drywall_db()
S.add_labor_actual(db, 'TEST-LRT-DRYW-PINNED', 'TR-DRYW', 100)
for r in db['labor_rates']:
    if r['labor_rate_id'] == 'TEST-LRT-DRYW-PINNED': r['effective_from'] = date(2025, 1, 1)
for m in db['crew_members']:
    if m['trade_code'] == 'TR-DRYW': m['labor_rate_id'] = 'TEST-LRT-DRYW-PINNED'
r = run(db); print('labor cost/SF', r.run['labor_cost'], '(1.15 if the $100 pin were honoured, 0.55 = pin ignored)')

hdr('F3-07 a zero price is a valid, complete, strict input')
db = S.priced_drywall_db()
for o in db['price_observations']:
    if o['observation_id'] == 'TEST-OBS-BOARDA': o['price_amount'] = D(0)
r = run(db); print(r.status, r.run['direct_cost_total'], 'board unit cost', mat(r)['unit_cost'], '| validator:', [(i.rule_code, i.severity) for i in validate(db, production=False) if i.record_id == 'TEST-OBS-BOARDA'])

hdr('F3-08 no range check on component waste / price / wage (only PostgreSQL CHECKs stop them)')
for w in (D('5'), D('-0.5')):
    db = S.priced_drywall_db()
    for c in db['work_item_components']:
        if c['work_item_id'] == WI and c['component_kind'] == 'material' and 'CAT-DRY-BRD' in (c['product_spec_key'] or ''): c['waste_factor'] = w
    r = run(db); print('waste', w, r.status, 'material_cost', r.run['material_cost'], '| validator issues:', [i.rule_code for i in validate(db, production=False)])
db = S.priced_drywall_db()
for x in db['labor_rates']:
    if x['trade_code'] == 'TR-DRYW': x.update(total_hr=D(-40), base_wage_hr=D(-40))
r = run(db); print('negative wage', r.status, r.run['direct_cost_total'], [i.rule_code for i in validate(db, production=False)])
db = S.priced_drywall_db()
for p in db['productivity_observations']:
    if p['work_item_id'] == WI: p['daily_output'] = D(-5)
r = run(db); print('negative daily output', r.status, r.run['direct_cost_total'])

hdr('F3-09 which of two eligible tier prices is used depends on observation ids (same day)')
def build(base_id, tier_id):
    db = S.priced_drywall_db()
    for o in db['price_observations']:
        if o['observation_id'] == 'TEST-OBS-BOARDA': o['observation_id'] = base_id
    o = S.add_obs(db, tier_id, 'TEST-PRD-BOARDA', '9.60', 32, 'SF'); o['qty_tier_min'] = D('3200')
    return db
for ids in (('TEST-OBS-A1', 'TEST-OBS-B2'), ('TEST-OBS-B2', 'TEST-OBS-A1')):
    print('base', ids[0], 'tier', ids[1], '-> board $/SF', mat(run(build(*ids), quantity=D('5000')))['unit_cost'], '(tier price 0.30 applies at 5000 SF)')

hdr('F3-10 with_assumptions: assumed factor / product used but has_assumptions=False, line origin "observed"')
db = S.priced_drywall_db()
S.add_factor(db, 'TEST-ADJ-C', 'productivity_condition', 'labor', '1.20', condition='occupied_building', origin='assumed')
r = run(db, conditions=('occupied_building',), mode='with_assumptions')
print(r.status, 'has_assumptions =', r.run['has_assumptions'], '| labor line origin_summary =', [l for l in r.lines if l['line_kind'] == 'labor'][0]['origin_summary'])

hdr('F3-11 strict mode reads the ASSUMED/unreviewed region hierarchy (wage of REG-MD-31084 applied to LA County)')
db = S.real_db(); S.validate_definitions(db); S.add_source(db); S.add_all_burdens(db); S.add_stat_wage(db, 'TEST-W1', 'TR-DRYW', '30')
reg = {x['region_id']: x for x in db['regions']}
print('REG-CA-037 parent:', reg['REG-CA-037']['parent_region_id'], '| origin/review of REG-CA-037:', reg['REG-CA-037']['origin'], reg['REG-CA-037']['review_status'])
lr = Engine(db).labor_rate('TR-DRYW', S.params(labor_basis='stat_loaded', annual_paid_hours=D(2080), mode='strict'))
print('strict run uses', lr['inputs'][0]['region_id'], 'flags', lr['flags'][:1])

hdr('F3-14 retail_promo channel with promo_flag=False is used as an ordinary price')
db = S.priced_drywall_db()
for o in db['price_observations']:
    if o['observation_id'] == 'TEST-OBS-BOARDA': o['price_channel'] = 'retail_promo'; o['promo_flag'] = False
r = run(db); print(r.status, mat(r)['unit_cost'])

hdr('F3-15 promote_validated promotes rows of a REJECTED source / REJECTED product; raw hash not required; unknown_needs_check ok')
db = S.real_db(); S.add_source(db, 'SRC-FETCHED-X', method='fetched_primary', review='rejected', reuse='unknown_needs_check')
S.add_product(db, 'TEST-PRD-A', 'gyp_half_reg_4x8', 32, 'SF', 'A', 'A-1', source='SRC-FETCHED-X')
for p in db['products']:
    if p['product_id'] == 'TEST-PRD-A': p.update(review_status='rejected')
S.add_obs(db, 'TEST-OBS-A', 'TEST-PRD-A', '12.80', 32, 'SF', source='SRC-FETCHED-X', review='unreviewed')
iss = validate(db, production=False)
print(promote_validated(db, iss, 'rev', '2026-10-24T00:00:00+00:00'), [(o['review_status'], o['raw_file_sha256']) for o in db['price_observations']])

hdr('F3-16 run_id depends on physical row order')
db = S.paint_db()
a = Engine(db).unit_cost('WI-PNT-001', 1, S.params()).run['run_id']
db.tables['products'].reverse(); db.tables['price_observations'].reverse(); db.tables['product_consumption'].reverse()
print('same data, reversed table order -> same id?', a == Engine(db).unit_cost('WI-PNT-001', 1, S.params()).run['run_id'])

hdr('F3-17 duplicate labor component / duplicate assembly child double the cost silently')
db = S.priced_drywall_db()
lab = [c for c in db['work_item_components'] if c['work_item_id'] == WI and c['component_kind'] == 'labor'][0]
dup = dict(lab); dup['component_id'] = 'TEST-WIC-DUPLAB'; dup['line_no'] = 99; dup['cost_tags'] = []
db.add('work_item_components', dup)
r = run(db); print('labor cost', r.run['labor_cost'], '(0.55 expected) status', r.status, 'validator', [i.rule_code for i in validate(db, production=False)])
adb = S.assembly_db()
adb.add('assembly_components', {'assembly_component_id': 'TEST-ASC-DUP', 'assembly_id': 'TEST-ASM-1', 'assembly_version': 1, 'line_no': 3, 'work_item_id': 'TEST-WI-9', 'work_item_version': 1, 'qty_per_assembly_unit': D('3'), 'qty_unit_id': 'EA', 'qty_formula': 'dup', 'qty_origin': 'derived', 'cost_tags': [], 'notes': None})
ra = Engine(adb).assembly_cost('TEST-ASM-1', 1, S.params()); print('assembly total', ra.run['direct_cost_total'], '(7.998376 without the duplicated child)')

hdr('F3-19 engine depends on the ambient Decimal context')
db = S.priced_drywall_db()
for prec in (28, 12):
    decimal.getcontext().prec = prec
    try: print('prec', prec, run(db).run['run_id'])
    except Exception as e: print('prec', prec, 'EXCEPTION', type(e).__name__)
decimal.getcontext().prec = 28

hdr('F3-20 RunParams edge cases accepted')
for kw in (dict(known_at=__import__('datetime').datetime(2026, 1, 1)), dict(annual_paid_hours=D('Infinity'))):
    try: S.params(**kw); print('ACCEPTED', list(kw))
    except Exception as e: print('rejected', list(kw), e)

hdr('F3-24 productivity_condition scales labor hours but not equipment hours')
db = mk([('labor', 'TR-CEM', 2, False), ('equipment', 'EQ-PTROWEL', 1, False)], rate_hr=25)
S.add_factor(db, 'TEST-ADJ-E', 'productivity_condition', 'equipment', '1.20', condition='occupied_building')
S.add_factor(db, 'TEST-ADJ-L', 'productivity_condition', 'labor', '1.20', condition='occupied_building')
r = Engine(db).unit_cost('WI-CON-001', 1, S.params(conditions=('occupied_building',)))
for k in ('labor', 'equipment'):
    l = [x for x in r.lines if x['line_kind'] == k][0]; print(k, 'hours/unit', l['quantity'], 'unit_cost', l['unit_cost'])

hdr('F3-21 validator: fabricated complete run with empty inputs; stale run after input flagged')
db = S.priced_drywall_db(); res = run(db)
fake = dict(res.run); fake.update(run_id='RUN-fake00000001', direct_cost_total=D('123.45'))
db.add('calculation_runs', fake)
db.add('calculation_run_lines', {'run_id': 'RUN-fake00000001', 'line_no': 1, 'line_kind': 'material', 'component_ref': 'x', 'description': 'made up', 'quantity': None, 'quantity_unit_id': None, 'quantity_kind': 'none', 'unit_cost': None, 'extended_cost': D('123.45'), 'formula': 'invented', 'inputs': [], 'origin_summary': 'observed', 'warnings': []})
print('issues for the fabricated run (no engine):', [i.rule_code for i in validate(db, production=False) if 'fake' in i.record_id])
db = S.priced_drywall_db(); res = run(db); db.add('calculation_runs', res.run)
for ln in res.lines: db.add('calculation_run_lines', ln)
for o in db['price_observations']:
    if o['observation_id'] == 'TEST-OBS-BOARDA': o['review_status'] = 'flagged'
print('stored run whose input observation was later flagged -> validator (no engine):', [i.rule_code for i in validate(db, production=False)])
