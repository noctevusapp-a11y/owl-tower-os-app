"""Builds takeoff2/arch.csv (architectural takeoff, Hollywood Comedy Club, Kelly Architects 2604, GC Owl Tower).
Every quantity is either read from a schedule, measured on the vector plans (poche_walls.py / walls_by_tag.py /
rooms_raster.py outputs in the scratchpad), or derived by arithmetic written into qty_source. No prices.
The row list is appended block by block; re-running rewrites the whole CSV so partial work survives.
Usage: python3 -I build_arch.py <scratch_poche_dir> <out_csv>
"""
import sys, csv, collections
POCHE, OUT = sys.argv[1], sys.argv[2]
COLS = ['item_id', 'bid_letter_item', 'division', 'description', 'spec_or_model', 'qty', 'unit', 'qty_basis', 'qty_source',
        'furnished_by', 'installed_by', 'notes']
rows = []
def add(bid, div, desc, spec, qty, unit, basis, source, fb, ib, notes=''):
    rows.append([f'A-{len(rows) + 1:03d}', bid, div, desc, spec, qty, unit, basis, source, fb, ib, notes])
def ft(v): return round(v, 1)

# ---------------------------------------------------------------- block 1: walls ----------------------------------
wa = collections.defaultdict(float)      # (page, comp, tag) -> LF
for r in csv.DictReader(open(f'{POCHE}/walls_assigned.csv')):
    wa[(int(r['page']), int(r['comp']), r['tag'])] += float(r['len_ft'])
def LF(page, tag, comps=None):
    return sum(v for (pg, c, tg), v in wa.items() if pg == page and tg == tag and (comps is None or c in comps))
P1, P2 = 4, 5
VEC = '03_Architectural_Plans_Demo_RCP.pdf'
CAL = ('vector plans A-2.10 (p4) / A-2.20 (p5) of ' + VEC + ' at 3/16"=1\'-0" = 13.5 pt/ft (calibrate_scale.py: printed "21\'-9 1/2"" = '
       '294.3 pt, "4\'" = 54.0 pt); gray wall poche rasterised at 54 px/ft, centreline = skeleton length (scripts/poche_walls.py, '
       'scripts/walls_by_tag.py; component map poche/walls_assigned.csv)')
# --- group definitions (component ids from walls_assigned.csv, see the overlay crops) ---
g = {}
g['1_stair1_L1'] = LF(P1, '1', {1774, 1999, 2211, 2384, 2476, 2477, 2609})
g['1_grease_int'] = LF(P1, '1', {4438})
g['1_dw_L1'] = LF(P1, '1', {5374, 5509, 5510})
g['1_wait_hall'] = LF(P1, '1', {5381})
g['1_lift_L1'] = LF(P1, '1', {6090, 6143})
g['1A_kitchen'] = LF(P1, '1A')
g['2_storefront_E_L1'] = LF(P1, '2', {2609, 3760, 4531, 5757, 5842, 6157, 6462})
g['2_storefront_S_L1'] = LF(P1, '2', {6679, 6681, 6674, 6682})
g['2_corridor_L1'] = LF(P1, '2', {3094, 3556, 4206, 4528, 2370, 4001, 4415, 4535})
g['2_vestibule_wait'] = LF(P1, '2', {3283, 4438})
g['3_L1'] = LF(P1, '3')
g['AC_curved_L1'] = LF(P1, 'AC', {2370, 4739, 5524})
g['AC_column_hall'] = LF(P1, 'AC', {1879})
g['AC_lift_L1'] = LF(P1, 'AC', {5565, 6143})
g['AC_host_green'] = LF(P1, 'AC', {5182, 5183, 5352, 5864, 6164, 6461})
g['1_stair1_M'] = LF(P2, '1', {1748, 1840, 1847, 1968})
g['1_mech3'] = LF(P2, '1', {1692, 1916})
g['1_grease_duct'] = LF(P2, '1', {2034, 1824, 2558})
g['1_west_mech5'] = LF(P2, '1', {3454, 4413, 3665})
g['1_dw_M'] = LF(P2, '1', {4718, 4864, 4837})
g['1_lift_M'] = LF(P2, '1', {5648, 5462})
g['2_storefront_E_M'] = LF(P2, '2', {2490, 2910, 3462, 5215, 5426})
g['2_mech12'] = LF(P2, '2', {5469, 5459, 5614, 2094})
g['2_storefront_S_M'] = LF(P2, '2', {6032, 6033})
g['2_west_M'] = LF(P2, '2', {1738, 2582})
g['2_restrooms_M'] = LF(P2, '2', {4720, 4991, 4803, 4722, 4681, 4703, 5168, 5173, 5217, 5277})
g['2_prepbar_M'] = LF(P2, '2', {4839, 4770})
g['3_M'] = LF(P2, '3')
g['5_M'] = LF(P2, '5')
g['AC_curved_M'] = LF(P2, 'AC', {2553, 3979, 4929})
g['AC_lift_M'] = LF(P2, 'AC', {5069})
g['AC_hall_prepbar'] = LF(P2, 'AC', {3454})
g['D2_M'] = LF(P2, 'D2')
chk1 = {t: LF(P1, t) for t in ('1', '1A', '2', '3', 'AC')}
chk2 = {t: LF(P2, t) for t in ('1', '2', '3', '5', 'AC', 'D2')}
assert abs(sum(v for k, v in g.items() if k.endswith('_L1') or k in ('1_grease_int', '1_wait_hall', '1A_kitchen', '2_corridor_L1', '2_vestibule_wait', 'AC_column_hall', 'AC_host_green')) - sum(chk1.values())) < 0.05, (g, chk1)
assert abs(sum(v for k, v in g.items() if k.endswith('_M') or k in ('1_mech3', '1_grease_duct', '1_west_mech5', '2_mech12', 'AC_hall_prepbar')) - sum(chk2.values())) < 0.05, (g, chk2)

H_MEZZ_FF = 9 + 1 / 12            # 9'-1" floor-to-floor: 16 risers @ 6-13/16" (A-6.10 / A-6.11)
H_DINING = 16.75                  # 16'-9" CLG-3A (A-3.12)
H_STAIR = 18 + 7.5 / 12           # 18'-7.5" CLG-3A at stair 1 (A-3.12)
H_M78 = 7 + 8 / 12                # +/-7'-8" CLG-3A mezzanine / attic (A-3.22)
H_M710 = 7 + 10 / 12              # +/-7'-10" CLG-3A mezzanine (A-3.22)
NOTE_H1 = ('height basis: walls under the (E) mezzanine taken at 9\'-1" floor-to-floor (A-6.10/A-6.11: 16 risers @ 6-13/16"); '
           'the (E) mezzanine slab thickness is not dimensioned (A-6.11 shows 8\'-1" / 8\'-3" clear under the mezzanine framing) - RFI')
WN1 = ('A-2.10 wall note 1: 400S162-54 steel studs @ 16" o.c. w/ 5/8" Type X GWB ea. side, 4" acoustic insulation, UL U404; Mold Tough GWB at wet areas to 4\'-0"; '
       'cement board where tile occurs (A-2.20 note 1 prints 3-5/8" 20 GA studs for the same tag - conflict)')
WN1A = 'A-2.10 wall note 1A: 6" 20 GA steel studs @ 16" o.c. w/ 2 layers Type X GWB ea. side (2-hr)'
WN2 = 'A-2.10 wall note 2: 3-5/8" 20 GA steel studs @ 16" o.c. w/ 5/8" Type X GWB ea. side, 4" acoustic insulation (non-rated)'
WN3 = 'A-2.10 wall note 3: 6" 20 GA steel studs @ 16" o.c., 5/8" Dens-Glass Gold + 2 layers felt + 1" exterior plaster outside, 5/8" Type X GWB inside (1-hr exterior)'
WN5 = 'A-2.20 wall note 5: 2" steel (hat channel) attached directly to (E) wall w/ 5/8" Type X GWB on 1 side'
WNAC = ('A-2.10 wall note AC: 4" 16 GA 400S162-54 studs @ 16" o.c. w/ (2) layers 5/8" Type X GWB ea. side, acoustic insulation, UL U404, Mold Tough at wet areas to 4\'-0", '
        'cement board where tile occurs, continuous acoustical sealant at ceiling')
def wall(desc, spec, lf, h, src, notes, div='09 22 16'):
    add('Walls', div, desc, spec, ft(lf), 'LF', 'drawn', src, 'GC', 'GC', notes)
    return lf * h
# ---- Level 1 (A-2.10)
sf = collections.defaultdict(float)
sf['1'] += wall(f'Wall type 1 (1-hr, UL U404) - stair 1 enclosure, 1st floor, hatched full height to the (E) waffle slab at the stair (CLG-3A 18\'-7.5")', WN1,
                g['1_stair1_L1'], H_STAIR, 'A-2.10 components 1774+1999+2211+2384+2476+2477+2609(north run); ' + CAL,
                f'{ft(g["1_stair1_L1"])} LF x 18.63 ft = {ft(g["1_stair1_L1"] * H_STAIR)} SF; wall carries doors 05 (3\'-0" x 8\'-0", 60 min) and 06 (exterior); hatched = legend "new full height wall to ceiling"')
sf['1'] += wall('Wall type 1 (1-hr) - grease interceptor enclosure (A-2.10 KN14: 1-hr rated shaft with 6" clearance around the unit), under the (E) mezzanine', WN1,
                g['1_grease_int'], H_MEZZ_FF, 'A-2.10 component 4438 tick-1 share; ' + CAL, f'{ft(g["1_grease_int"])} LF x 9.08 ft = {ft(g["1_grease_int"] * H_MEZZ_FF)} SF; ' + NOTE_H1)
sf['1'] += wall('Wall type 1 (1-hr) - dumbwaiter shaft walls at 1st floor (A-6.30 note 4: 1-hr shaft, see A-2.10 wall types)', WN1,
                g['1_dw_L1'], H_MEZZ_FF, 'A-2.10 components 5374+5509+5510 (shaft hatched); ' + CAL, f'{ft(g["1_dw_L1"])} LF x 9.08 ft = {ft(g["1_dw_L1"] * H_MEZZ_FF)} SF; east shaft wall is the (E) wall per A-6.30 plan; ' + NOTE_H1)
sf['1'] += wall('Wall type 1 (1-hr) - wait station / hallway 04 wall, hatched', WN1, g['1_wait_hall'], H_MEZZ_FF, 'A-2.10 component 5381 (tick 1); ' + CAL,
                f'{ft(g["1_wait_hall"])} LF x 9.08 ft = {ft(g["1_wait_hall"] * H_MEZZ_FF)} SF; ' + NOTE_H1)
sf['1'] += wall('Wall type 1 (1-hr) - ADA lift shaft walls at 1st floor incl. KN13 wall filling the (E) opening to the adjacent business', WN1,
                g['1_lift_L1'], H_MEZZ_FF, 'A-2.10 components 6090 + 6143 tick-1 share; ' + CAL, f'{ft(g["1_lift_L1"])} LF x 9.08 ft = {ft(g["1_lift_L1"] * H_MEZZ_FF)} SF; lift shaft per A-6.21 KN1; ' + NOTE_H1)
sf['1A'] += wall('Wall type 1A (2-hr) - kitchen east wall (6" stud) incl. the jog at kitchen doors 07/08, under the (E) mezzanine; drawn without the full-height hatch', WN1A,
                 g['1A_kitchen'], H_MEZZ_FF, 'A-2.10 components 1780 (tick 1A) + 2854; ' + CAL, f'{ft(g["1A_kitchen"])} LF x 9.08 ft = {ft(g["1A_kitchen"] * H_MEZZ_FF)} SF; 2-hr wall must extend to the rated deck although not hatched - RFI; ' + NOTE_H1)
sf['2d'] += wall('Wall type 2 (non-rated) - lining wall along the east storefront (dining side), hatched full height to the waffle slab (CLG-3A 16\'-9")', WN2,
                 g['2_storefront_E_L1'], H_DINING, 'A-2.10 components 2609(east run)+3760+4531+5757+5842+6157+6462 (ticks 2); ' + CAL,
                 f'{ft(g["2_storefront_E_L1"])} LF x 16.75 ft = {ft(g["2_storefront_E_L1"] * H_DINING)} SF; wall tagged "2 TYP." at (1771,491); carries window type A (host)')
sf['2d'] += wall('Wall type 2 (non-rated) - lining wall along the south storefront (green room / dining), hatched full height', WN2, g['2_storefront_S_L1'], H_DINING,
                 'A-2.10 components 6679+6681(tick 2)+6674+6682; ' + CAL, f'{ft(g["2_storefront_S_L1"])} LF x 16.75 ft = {ft(g["2_storefront_S_L1"] * H_DINING)} SF; interrupted by the (E) columns')
sf['2b'] += wall('Wall type 2 (non-rated) - straight corridor wall east of hallway 04 (x=1260 line, 1\'-5" behind the curved AC wall) and kitchen/hallway wall pieces at doors 07-08, under the (E) mezzanine', WN2,
                 g['2_corridor_L1'], H_MEZZ_FF, 'A-2.10 components 3094+3556+4206(tick 2)+4528+2370(tick-2 share)+4001+4415+4535; ' + CAL,
                 f'{ft(g["2_corridor_L1"])} LF x 9.08 ft = {ft(g["2_corridor_L1"] * H_MEZZ_FF)} SF; part hatched (full height); ' + NOTE_H1)
sf['2b'] += wall('Wall type 2 (non-rated) - kitchen vestibule / wait station L-wall and wait-station wall at the grease interceptor, under the (E) mezzanine', WN2,
                 g['2_vestibule_wait'], H_MEZZ_FF, 'A-2.10 components 3283 (untagged, nearest tags 2) + 4438 tick-2 share; ' + CAL,
                 f'{ft(g["2_vestibule_wait"])} LF x 9.08 ft = {ft(g["2_vestibule_wait"] * H_MEZZ_FF)} SF; 3283 carries no tick - type 2 assumed from the adjacent "2" tags, RFI; ' + NOTE_H1)
sf['3'] += wall('Wall type 3 (1-hr exterior) - infill of the removed (E) window at the NE storefront bay beside new exit door 06, 1st-floor portion', WN3, g['3_L1'], H_MEZZ_FF,
                'A-2.10 components 1944 (tick 3)+1985+2616; ' + CAL, f'{ft(g["3_L1"])} LF x 9.08 ft = {ft(g["3_L1"] * H_MEZZ_FF)} SF (jamb returns and head/sill pieces; the bay itself is door 06 + fixed glass KN4 on A-4.01); see A-8 rows for the exterior plaster/metal panel')
sf['AC'] += wall('Wall type AC (acoustic, 1-hr UL U404) - curved wall between hallway 04 and the dining room, 1st floor, hatched full height; backs the TX-2/WC-5 acoustic panels (KN19)', WNAC,
                 g['AC_curved_L1'], H_MEZZ_FF, 'A-2.10 components 2370 (tick-AC share)+4739 (tick AC)+5524; ' + CAL,
                 f'{ft(g["AC_curved_L1"])} LF x 9.08 ft = {ft(g["AC_curved_L1"] * H_MEZZ_FF)} SF; wall sits under the (E) mezzanine edge (KN16 line at x=1330); curved - segment framing; ' + NOTE_H1)
sf['AC'] += wall('Wall type AC - wall wrapping the (E) column at the hallway 04 cased opening (door 04)', WNAC, g['AC_column_hall'], H_MEZZ_FF, 'A-2.10 component 1879 (tick AC); ' + CAL,
                 f'{ft(g["AC_column_hall"])} LF x 9.08 ft = {ft(g["AC_column_hall"] * H_MEZZ_FF)} SF; ' + NOTE_H1)
sf['AC'] += wall('Wall type AC - ADA lift lobby walls at 1st floor (room 05), hatched', WNAC, g['AC_lift_L1'], H_MEZZ_FF, 'A-2.10 components 5565 (tick AC) + 6143 tick-AC share; ' + CAL,
                 f'{ft(g["AC_lift_L1"])} LF x 9.08 ft = {ft(g["AC_lift_L1"] * H_MEZZ_FF)} SF; ' + NOTE_H1)
sf['ACd'] += wall('Wall type AC - host (01) and green room (03) enclosure walls in the double-height dining, hatched full height to the waffle slab (CLG-3A 16\'-9"); rooms have CLG-1D at 8\'-0" inside', WNAC,
                  g['AC_host_green'], H_DINING, 'A-2.10 components 5182+5183+5352+5864+6164+6461 (ticks AC at 1682,873 / 1709,846 / 1650,1196); ' + CAL,
                  f'{ft(g["AC_host_green"])} LF x 16.75 ft = {ft(g["AC_host_green"] * H_DINING)} SF; carries doors 02 (cased 3\'-0"x8\'-0"), 15, 18 (green room) and the host north wall 7\'-5"')
# ---- Mezzanine (A-2.20) - heights above the mezzanine floor
NOTE_HM = 'height basis: +/-7\'-8" (attic / stair side) or +/-7\'-10" (dining 2 / restroom side) to the (E) waffle slab per A-3.22 labels (= 16\'-9" - 9\'-1")'
sf['1m'] += wall('Wall type 1 (1-hr) - stair 1 enclosure at the mezzanine level, hatched', WN1, g['1_stair1_M'], H_M78, 'A-2.20 components 1748+1840+1847+1968 (ticks 1); ' + CAL,
                 f'{ft(g["1_stair1_M"])} LF x 7.67 ft = {ft(g["1_stair1_M"] * H_M78)} SF; carries door 21 (60 min); ' + NOTE_HM)
sf['1m'] += wall('Wall type 1 (1-hr) - mechanical room 3 west wall (28) at the attic', WN1, g['1_mech3'], H_M78, 'A-2.20 components 1692 (tick 1)+1916; ' + CAL,
                 f'{ft(g["1_mech3"])} LF x 7.67 ft = {ft(g["1_mech3"] * H_M78)} SF; carries door 31; ' + NOTE_HM)
sf['1m'] += wall('Wall type 1 (1-hr) - grease duct shaft 29 enclosure (curved R1\'-6" end) at the mezzanine (A-3.12 KN8: grease duct in 1-hr shaft)', WN1, g['1_grease_duct'], H_M710,
                 'A-2.20 components 2034+1824+2558 (tick 1); ' + CAL, f'{ft(g["1_grease_duct"])} LF x 7.83 ft = {ft(g["1_grease_duct"] * H_M710)} SF; carries door 34 (60 min, "ventilation louvers on door" - louver in a rated shaft door, RFI); ' + NOTE_HM)
sf['1m'] += wall('Wall type 1 (1-hr) - west edge wall against the (E) party wall (tag "1 | E" at 653,623) and mechanical room 5 (32) curved enclosure', WN1, g['1_west_mech5'], H_M710,
                 'A-2.20 component 3454 west + mech-room-5 sub-boxes + 4413 (tick 1) + 3665; ' + CAL, f'{ft(g["1_west_mech5"])} LF x 7.83 ft = {ft(g["1_west_mech5"] * H_M710)} SF; carries door 35 (60 min, louvered); ' + NOTE_HM)
sf['1m'] += wall('Wall type 1 (1-hr) - dumbwaiter shaft walls at the mezzanine', WN1, g['1_dw_M'], H_M710, 'A-2.20 components 4718 (tick 1)+4864+4837; ' + CAL,
                 f'{ft(g["1_dw_M"])} LF x 7.83 ft = {ft(g["1_dw_M"] * H_M710)} SF; ' + NOTE_HM)
sf['1m'] += wall('Wall type 1 (1-hr) - ADA lift shaft and mechanical room 1 west wall at the mezzanine, hatched', WN1, g['1_lift_M'], H_M710, 'A-2.20 components 5648+5462 (ticks 1); ' + CAL,
                 f'{ft(g["1_lift_M"])} LF x 7.83 ft = {ft(g["1_lift_M"] * H_M710)} SF; ' + NOTE_HM)
sf['2m'] += wall('Wall type 2 (non-rated) - lining wall along the east storefront at the attic (mech rooms 2/3 side) and mech room 2 north wall, hatched', WN2, g['2_storefront_E_M'], H_M78,
                 'A-2.20 components 2490 (tick 2)+2910+3462+5215 (tick 2)+5426; ' + CAL, f'{ft(g["2_storefront_E_M"])} LF x 7.67 ft = {ft(g["2_storefront_E_M"] * H_M78)} SF; ' + NOTE_HM)
sf['2m'] += wall('Wall type 2 (non-rated) - mechanical rooms 1/2/3 partitions (doors 29, 30, 31)', WN2, g['2_mech12'], H_M78, 'A-2.20 components 5469 (tick 2)+5459+5614 (tick 2)+2094 (tick 2); ' + CAL,
                 f'{ft(g["2_mech12"])} LF x 7.67 ft = {ft(g["2_mech12"] * H_M78)} SF; ' + NOTE_HM)
sf['2m'] += wall('Wall type 2 (non-rated) - lining wall along the south storefront under mechanical rooms 1 and 2, hatched', WN2, g['2_storefront_S_M'], H_M78, 'A-2.20 components 6032+6033; ' + CAL,
                 f'{ft(g["2_storefront_S_M"])} LF x 7.67 ft = {ft(g["2_storefront_S_M"] * H_M78)} SF; ' + NOTE_HM)
sf['2m'] += wall('Wall type 2 (non-rated) - west edge wall north of mechanical room 5 (BOH 34 side)', WN2, g['2_west_M'], H_M710, 'A-2.20 components 1738+2582 (tick 2 at 651,461); ' + CAL,
                 f'{ft(g["2_west_M"])} LF x 7.83 ft = {ft(g["2_west_M"] * H_M710)} SF; ' + NOTE_HM)
sf['2m'] += wall('Wall type 2 (non-rated) - men\'s / women\'s restroom 2 (22/23) and vestibule walls incl. the wall to the ADA lift; plumbing walls labelled "6" STUD" on A-2.20', WN2, g['2_restrooms_M'], H_M710,
                 'A-2.20 components 4720+4991+4803+4722+4681+4703+5168+5173+5217+5277 (ticks 2 "TYP."); ' + CAL,
                 f'{ft(g["2_restrooms_M"])} LF x 7.83 ft = {ft(g["2_restrooms_M"] * H_M710)} SF; 6" studs at the two "6\\" STUD" labels (1121,1049) and (1323,904) - length of the 6" portions not separable on the plan; Mold Tough GWB to 4\'-0" and cement board behind WT-1/WT-2 (see finish rows); ' + NOTE_HM)
sf['2m'] += wall('Wall type 2 (non-rated) - prep bar (24) door-26 wall pieces incl. the R1\'-6" curved end', WN2, g['2_prepbar_M'], H_M710, 'A-2.20 components 4839 (tick 2)+4770; ' + CAL,
                 f'{ft(g["2_prepbar_M"])} LF x 7.83 ft = {ft(g["2_prepbar_M"] * H_M710)} SF; ' + NOTE_HM)
sf['3'] += wall('Wall type 3 (1-hr exterior) - infill of the removed (E) window at the NE storefront bay, mezzanine/attic portion with returns', WN3, g['3_M'], H_M78,
                'A-2.20 components 1751+1785 (tick 3)+2263 (tick 3)+2408 (tick 3); ' + CAL, f'{ft(g["3_M"])} LF x 7.67 ft = {ft(g["3_M"] * H_M78)} SF; two-storey infill with the 1st-floor row; ' + NOTE_HM)
sf['5'] += wall('Wall type 5 - 2" steel furring with 5/8" Type X GWB one side on the (E) south wall of the comedy club hallway 35', WN5, g['5_M'], H_M710, 'A-2.20 components 5180+5181 (tick 5); ' + CAL,
                f'{ft(g["5_M"])} LF x 7.83 ft = {ft(g["5_M"] * H_M710)} SF; ' + NOTE_HM)
sf['ACm'] += wall('Wall type AC (acoustic) - curved wall between comedy club dining 2 (21) and the mechanical attic / open-to-below edge, hatched full height', WNAC, g['AC_curved_M'], H_M710,
                  'A-2.20 components 2553 (tick AC)+3979 (tick AC)+4929; ' + CAL,
                  f'{ft(g["AC_curved_M"])} LF x 7.83 ft = {ft(g["AC_curved_M"] * H_M710)} SF; A-3.22 prints "15\'-9" CLG-1D P-3 CURVE UP" along this wall - if that is the wall height above the mezzanine floor the SF doubles; RFI on the datum; ' + NOTE_HM)
sf['ACm'] += wall('Wall type AC - ADA lift lobby wall at the mezzanine, hatched', WNAC, g['AC_lift_M'], H_M710, 'A-2.20 component 5069 (tick AC); ' + CAL,
                  f'{ft(g["AC_lift_M"])} LF x 7.83 ft = {ft(g["AC_lift_M"] * H_M710)} SF; ' + NOTE_HM)
sf['ACm'] += wall('Wall type AC - long wall between comedy club dining 2 and the prep bar (24) / comedy club hallway (35), incl. the 3\'-10" jog (not hatched)', WNAC, g['AC_hall_prepbar'], H_M710,
                  'A-2.20 component 3454 remainder after the west-wall and mech-room-5 sub-boxes (tick AC at 792,761); ' + CAL,
                  f'{ft(g["AC_hall_prepbar"])} LF x 7.83 ft = {ft(g["AC_hall_prepbar"] * H_M710)} SF; carries the pick-up counter opening (A-5.20) and door 26; ' + NOTE_HM)
add('Walls', '09 22 16', 'Day-2 walls on the mezzanine (layer 2604-FP-02_Day2): BOH 34 partition 14.6 LF (8" drawn thickness) and the 11\'-9" wall with 1\'-6" radius ends at dining 2 (12.7 LF, 5.7")',
    'wall type not tagged; rooms 34/35 are marked "Day2" on A-7.21', ft(g['D2_M']), 'LF', 'drawn', 'A-2.20 components 2027 + 2929, fills on layer 2604-FP-02_Day2|i-new-poche; ' + CAL, 'GC', 'GC',
    'carried separately - confirm whether Day-2 scope is in the base bid; wall type and height not given (RFI)')
# ---- derived components per wall type (SF)
tot1 = sf['1'] + sf['1m']; tot1A = sf['1A']; tot2 = sf['2d'] + sf['2b'] + sf['2m']; tot3 = sf['3']; tot5 = sf['5']; totAC = sf['AC'] + sf['ACd'] + sf['ACm']
add('Walls', '09 29 00', 'Gypsum board 5/8" Type X at wall type 1, both sides (1 layer each side)', '5/8" Type X GWB (A-9.10: USG, ICC ESR-1338); Level 5 finish in patron areas, Level 4 BOH (A-2.10 gyp board finish note)',
    round(2 * tot1), 'SF', 'inferred', f'type-1 wall area {round(tot1)} SF (sum of the type-1 LF x height rows above) x 2 sides', 'GC', 'GC', 'no deduction for door openings (door schedule widths are listed in the door rows)')
add('Walls', '09 29 00', 'Gypsum board 5/8" Type X at wall type 1A, both sides, 2 layers each side', '5/8" Type X GWB, 2 layers per side', round(4 * tot1A), 'SF', 'inferred', f'type-1A wall area {round(tot1A)} SF x 4 layers', 'GC', 'GC', '')
add('Walls', '09 29 00', 'Gypsum board 5/8" Type X at wall type 2, both sides', '5/8" Type X GWB', round(2 * tot2), 'SF', 'inferred', f'type-2 wall area {round(tot2)} SF x 2 sides', 'GC', 'GC', '')
add('Walls', '09 29 00', 'Gypsum board 5/8" Type X at wall type AC, both sides, 2 layers each side', '5/8" Type X GWB, 2 layers per side', round(4 * totAC), 'SF', 'inferred', f'type-AC wall area {round(totAC)} SF x 4 layers', 'GC', 'GC', '')
add('Walls', '09 29 00', 'Gypsum board 5/8" Type X at wall type 3 (interior face) and type 5 furring (one side)', '5/8" Type X GWB', round(tot3 + tot5), 'SF', 'inferred', f'type-3 area {round(tot3)} SF + type-5 area {round(tot5)} SF, 1 layer', 'GC', 'GC', '')
add('Walls', '09 29 00', 'Exterior sheathing 5/8" Dens-Glass Gold + 2 layers felt at wall type 3 (exterior face)', 'Georgia-Pacific DensGlass Gold 5/8"; 2 layers felt per wall note 3', round(tot3), 'SF', 'inferred', f'type-3 wall area {round(tot3)} SF', 'GC', 'GC', 'the 1" exterior plaster is in the exterior rows (A-8)')
add('Walls', '07 21 16', 'Acoustic batt insulation 4" in wall types 1, 2 and AC (A-9.10 detail 4: 4" fiberglass batt, one side paper, R-13)', '4" fiberglass batt, R-13', round(tot1 + tot2 + totAC), 'SF', 'inferred',
    f'type-1 {round(tot1)} + type-2 {round(tot2)} + type-AC {round(totAC)} SF', 'GC', 'GC', 'type 1A and 3 carry no insulation in the wall notes')
add('Walls', '05 40 00', 'Steel studs 400S162-54 (16 GA) @ 16" o.c. - wall types 1 and AC (wall notes; S-2.10/S-2.20 legend "400S162-54 @ 16" typ. all walls")', '400S162-54 @ 16" o.c., top and bottom track same gauge, 1-1/2" x 16 GA bridging straps (A-9.10 details 2/3)',
    ft(g['1_stair1_L1'] + g['1_grease_int'] + g['1_dw_L1'] + g['1_wait_hall'] + g['1_lift_L1'] + g['1_stair1_M'] + g['1_mech3'] + g['1_grease_duct'] + g['1_west_mech5'] + g['1_dw_M'] + g['1_lift_M'] + g['AC_curved_L1'] + g['AC_column_hall'] + g['AC_lift_L1'] + g['AC_host_green'] + g['AC_curved_M'] + g['AC_lift_M'] + g['AC_hall_prepbar']),
    'LF', 'inferred', 'sum of the type-1 and type-AC wall rows', 'GC', 'GC', 'S-1.10 schedule prints 362S162-54 - conflict carried in demo_struct_gc_notes.md')
add('Walls', '05 40 00', 'Steel studs 3-5/8" 20 GA @ 16" o.c. - wall type 2 (6" studs at the mezzanine restroom plumbing walls per the "6\\" STUD" labels)', '362S125-33 (3-5/8" 20 GA) @ 16" o.c.',
    ft(sum(v for k, v in g.items() if k.startswith('2_'))), 'LF', 'inferred', 'sum of the type-2 wall rows', 'GC', 'GC', '')
add('Walls', '05 40 00', 'Steel studs 6" 20 GA @ 16" o.c. - wall types 1A and 3', '600S125-33 @ 16" o.c.', ft(g['1A_kitchen'] + g['3_L1'] + g['3_M']), 'LF', 'inferred', 'type-1A + type-3 wall rows', 'GC', 'GC', '')
add('Walls', '09 22 16', 'Furring channel 2" steel attached to the (E) wall - wall type 5', '2" steel furring (hat channel) per wall note 5', ft(g['5_M']), 'LF', 'inferred', 'type-5 wall row', 'GC', 'GC', '')
add('Walls', '07 92 00', 'Continuous acoustical sealant at the ceiling line of all type-AC walls, both sides', 'acoustical sealant per wall note AC', ft(2 * (g['AC_curved_L1'] + g['AC_column_hall'] + g['AC_lift_L1'] + g['AC_host_green'] + g['AC_curved_M'] + g['AC_lift_M'] + g['AC_hall_prepbar'])),
    'LF', 'inferred', 'type-AC LF x 2 sides', 'GC', 'GC', 'rated walls also need head-of-wall fire sealant - not called out, RFI')
add('Walls', '09 29 00', 'Mold Tough GWB substitution to 4\'-0" above floor at wet areas (mezzanine restrooms 22/23, 1st-floor wait station, prep bar) - wall types 1/AC/2 per wall notes', 'USG Sheetrock Mold Tough 5/8" Type X',
    round(4 * (g['2_restrooms_M'] + g['2_prepbar_M'] + g['AC_hall_prepbar'] + g['2_vestibule_wait'])), 'SF', 'inferred',
    f'wet-area wall LF ({ft(g["2_restrooms_M"])} restrooms + {ft(g["2_prepbar_M"])} prep bar + {ft(g["AC_hall_prepbar"])} prep bar/hallway AC wall + {ft(g["2_vestibule_wait"])} wait station) x 4 ft, one side', 'GC', 'GC',
    'which rooms count as "wet areas" is not defined on the drawings - RFI; substitution within the GWB SF above, not additive')
add('Walls', '09 28 13', 'Cement board substitution behind wall tile WT-1/WT-2 (mezzanine restrooms 22/23, 4\'-0" high tile walls per A-5.12 KN17)', '1/2" cement backer board',
    round(4 * g['2_restrooms_M']), 'SF', 'inferred', f'restroom wall LF {ft(g["2_restrooms_M"])} x 4 ft (tile wainscot height, A-5.12 KN17 "4\'-0" high code compliant tile wall")', 'GC', 'GC',
    'perimeter measured on the wall centrelines, both restrooms, inside faces only; substitution within the GWB SF')
add('Walls', '09 22 16', 'Low wall 24" high around the sloped ceiling of the stair landing below (A-2.20 KN17)', 'framing per wall notes, 24" tall', None, 'LF', 'not_quantifiable',
    'A-2.20 KN17 tag at (649,480) beside the KN18 sloped-ceiling line; the low wall is not drawn with a poche on the plan (only the dashed KN18 line, ~26 SF slope per demo_struct_gc.csv)', 'GC', 'GC', 'RFI: extent of the 24" guard/low wall (3 sides of the sloped area?)')
add('Walls', '05 70 00', 'Perforated metal column enclosure, floor to exposed ceiling, around the (E) plumbing lines at a column (A-2.10 KN21, A-2.20 KN23)', 'perforated metal, pattern/gauge/finish not specified',
    4, 'EA', 'drawn', 'A-2.10 KN21 tags at (1634,545) "TYP." (1 tag) and A-2.20 KN23 tags at (1273,440), (1541,555) and the "22|23" pair - 3 tags; 1 column on the 1st floor + 3 on the mezzanine', 'GC', 'GC',
    '"TYP." on the 1st-floor tag - number of columns with exposed (E) plumbing not stated, RFI; height = 16\'-9" (1st floor) / 7\'-10" (mezzanine)')
add('Walls', '09 22 16', 'GC to furr out and patch (E) wall to a continuous smooth surface (A-2.10 KN15)', 'furring + GWB patch', None, 'SF', 'not_quantifiable',
    'A-2.10 KN15 tags at (1016,751) (wait-station side of the (E) women\'s restroom wall) and (1668,1117) (green room east wall); no extent drawn', 'GC', 'GC', 'RFI: extent of furring at the two KN15 locations')
add('Walls', '09 22 16', 'Soffit / beam enclosure: frame wall around the (E) ceiling beam at the comedy club 2 elevation ("GC to frame wall around it to hide it", A-4.30 details 1 and 5) and the new soffit aligned to the lowest part of the ceiling beam, 7\'-6" min. (A-4.30 note)',
    'GWB on steel framing', None, 'LF', 'not_quantifiable', 'Addendum 1 A-4.30 text: "LINE OF (E) CEILING BEAM BEYOND; GC TO FRAME WALL AROUND IT TO HIDE IT", "ALIGN BOTTOM OF NEW SOFFIT TO BOTTOM LOWEST PART OF CEILING BEAM; MAINTAIN 7\'-6" MIN."; beam length not dimensioned on the elevation', 'GC', 'GC',
    'RFI: beam length / soffit extent; the "8\'-4"" and "7\'-8"; 7\'-6" MIN." dimensions on A-4.30 are heights')
add('Walls', '09 22 16', 'GWB ceiling above the hallway opening (A-4.31 "(N) GWB CEILING ABOVE HALLWAY OPENING")', '5/8" GWB', None, 'SF', 'not_quantifiable', 'Addendum 1 A-4.31 note at the hallway elevation; no dimensions', 'GC', 'GC', 'RFI: size of the hallway opening soffit')

def write():
    with open(OUT, 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(COLS); w.writerows(rows)
    print(f'wrote {OUT}: {len(rows)} rows')
# ---------------------------------------------------------------- block 2: doors, hardware, windows --------------
DS = 'A-7.10 door schedule, IFB Interior Design set p35 (ID part03 p12, 9/9/2026) read at 300 dpi (scratchpad/arch2/A710_dsL.jpg, A710_dsR.jpg)'
# mark, type, mode, door mat, frame mat, W, H, thk, finish, head, jamb, sill, rating, inside, outside, requirements, handing, hw set, remarks, provided
DOORS = [
 ('E01', 'A', 'P', 'Alum/GL', 'Alum', '6\'-0"', '8\'-0"', '1 3/4"', 'N/A', 'N/A', 'N/A', '7/-', 'N/R', 'Host', 'Exterior', 'exit access door; panic hardware; self closing; smoke seal/weather gasketing; unlocked during business hours', '-', 'HW-1,2,4 & 5', '', '-'),
 ('02', 'D', 'CO', 'N/A', 'WD', '3\'-0"', '8\'-0"', 'N/A', 'P-1', 'N/A', 'N/A', 'N/A', 'N/R', 'Comedy Club Dining 1', 'Host', '', '-', '-', 'cased opening', 'GC'),
 ('03', 'D', 'CO', 'N/A', 'WD', '3\'-0"', '8\'-0"', 'N/A', 'P-1', 'N/A', 'N/A', 'N/A', 'N/R', 'Hallway', 'Comedy Club Dining 1', '', '-', '-', 'cased opening', 'GC'),
 ('04', 'D', 'CO', 'N/A', 'WD', '3\'-8"', '8\'-0"', 'N/A', 'P-1', 'N/A', 'N/A', 'N/A', 'N/R', 'Hallway', 'Comedy Club Dining 1', '', '-', '-', 'cased opening', 'GC'),
 ('05', 'C', 'S', 'MT', 'Alum', '3\'-0"', '8\'-0"', '1 3/4"', '-', '6/-', '6/-', 'N/A', '60', 'Stair 1', 'Comedy Club Dining 1', 'exit access door; panic hardware; self closing; smoke seal', 'RH', 'HW-1,3 & 4', '', 'GC'),
 ('06', 'B', 'S', 'Alum/GL', 'Alum', '3\'-0"', '7\'-9"', '1 3/4"', '-', 'N/A', 'N/A', '7/-', 'N/R', 'Stair 1', 'Exterior', 'exit access door; panic hardware; self closing; smoke seal/weather gasketing; unlocked during business hours', 'LH', 'HW-1,2,4 & 5', 'new exterior exit door, design/finish to match the (E) entry door (A-4.01 KN5)', 'GC'),
 ('07', 'E', 'S', 'Alum', 'Alum', '3\'-0"', '7\'-0"', '-', '-', 'N/A', 'N/A', 'N/A', 'N/R', 'Kitchen', 'Hallway', 'self closing; no locking hardware', 'LH', 'HW-6,7 & 8', 'Eliason door with 4"x4" window', 'GC'),
 ('08', 'E', 'S', 'Alum', 'Alum', '3\'-0"', '7\'-0"', '-', '-', 'N/A', 'N/A', 'N/A', 'N/R', 'Kitchen', 'Hallway', 'self closing; no locking hardware', 'RH', 'HW-6,7 & 8', 'Eliason door with 4"x4" window', 'GC'),
 ('E09', '-', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'N/A', 'N/A', 'N/A', 'N/A', 'N/R', "Men's Restroom", 'Hallway', 'self closing; unlocked during business hours', 'LH', '-', '(E) door to remain', '-'),
 ('E10', '-', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'N/A', 'N/A', 'N/A', 'N/A', 'N/R', "Women's Restroom", 'Hallway', 'self closing; unlocked during business hours', 'LH', '-', '(E) door to remain', '-'),
 ('E11', '-', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'N/A', 'N/A', 'N/A', 'N/A', 'N/R', 'Employee Restroom', 'Kitchen', 'self closing; unlocked during business hours', 'RH', '-', '(E) door to remain', '-'),
 ('E12', '-', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'N/A', 'N/A', 'N/A', 'N/A', 'N/R', 'Dry-Storage', 'Kitchen Vestibule', 'unlocked during business hours; double deadbolt', 'LH', '-', '(E) door to remain', '-'),
 ('E13', 'D', 'CO', 'N/A', 'Alum', '3\'-0"', '7\'-0"', '-', 'N/A', 'N/A', 'N/A', 'N/A', 'N/R', 'Kitchen Vestibule', 'Kitchen', '', '-', '', '(E) cased opening', 'GC'),
 ('E14', 'C', 'S', 'MT', 'Alum', '3\'-0"', '8\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Kitchen Vestibule', 'Building Corridor', 'panic hardware; self closing; smoke seal', 'LH', 'HW-1,3 & 4', '(E) door: new hardware set', 'GC'),
 ('15', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Green Room', 'Comedy Club Dining 1', 'thumb latch on inside', 'RH', 'HW-9', 'A-4.21: single panel recessed wood door with mirror insert', 'GC'),
 ('16', 'F', 'S', 'MT/GL', 'MT', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Stair 2', 'Exterior', 'exit access door; panic hardware; self closing; smoke seal/weather gasketing; unlocked during business hours', 'RH', 'HW-9', 'exit stair 2 exterior door at 1704 N Vine - exit-stair permit 26016-10000-18605, carried in demo_struct_gc.csv X- rows; listed here for the hardware set only', 'GC'),
 ('17', 'F', 'S', 'Alum', 'Alum', '3\'-0"', '7\'-0"', '-', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Kitchen', 'Adj. (E) Restaurant', 'self closing; no locking hardware', 'RH', 'HW-6,7 & 8', 'Eliason door with 4"x4" window', 'GC'),
 ('18', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Green Room', 'Comedy Club Dining 1', 'unlocked during business hours', 'LHR', 'HW-9', 'Day 2 door', 'GC'),
 ('19', 'G', 'S', 'HM', 'HM', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', '60', 'Mech. Unit Closet', 'Hallway', 'self closing; smoke seal', 'RH', 'HW-10', 'Ventilation louvers on door', 'GC'),
 ('21', 'C', 'S', 'HM', 'HM', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', '60', 'Comedy Club Dining 2', 'Stair 1', 'exit access door; panic hardware; self closing; smoke seal', 'RH', 'HW-1,3 & 4', '', 'GC'),
 ('22', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', 'N/A', 'N/A', 'N/A', 'N/R', 'Mechanical Attic', 'Vestibule Mech. Attic', 'unlocked during business hours', 'RH', 'HW-4 & 10', '', 'GC'),
 ('23', 'D', 'CO', 'N/A', 'WD', '3\'-0"', '7\'-0"', 'N/A', 'P-1', 'N/A', 'N/A', 'N/A', 'N/R', 'Vestibule Mech. Attic', 'Comedy Club Hallway', '', '-', '-', 'cased opening', 'GC'),
 ('24', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', "Women's Restroom", 'Comedy Club Dining 2', 'self closing; thumb latch on inside', 'LH', 'HW-4 & 9', '', 'GC'),
 ('25', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', "Men's Restroom", 'Comedy Club Hallway', 'self closing; thumb latch on inside', 'LH', 'HW-4 & 9', '', 'GC'),
 ('26', 'E', 'S', 'Alum', 'Alum', '3\'-0"', '7\'-0"', '-', '-', 'N/A', 'N/A', 'N/A', 'N/R', 'Prep Bar', 'Comedy Club Dining 2', 'self closing; unlocked during business hours; no locking hardware', 'RH', 'HW-6,7 & 8', '', 'GC'),
 ('27', 'C', 'S', 'HM', 'HM', '3\'-0"', '8\'-0"', '1 3/4"', 'N/A', 'N/A', 'N/A', 'N/A', '60', 'Comedy Club Hallway', 'Stair 2', 'exit access door; panic hardware; self closing; smoke seal', 'RH', 'HW-1,3 & 4', 'door into exit stair 2 (exit-stair permit; see demo_struct_gc.csv X- rows - rated exit-access door)', '-'),
 ('28', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Mechanical Attic', 'Comedy Club Dining 2', 'unlocked during business hours', 'RH', 'HW-4 & 10', '', 'GC'),
 ('29', 'G', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Mechanical Room 1', 'Mechanical Attic', 'self closing', 'LH', 'HW-10', 'Ventilation louvers on door', 'GC'),
 ('30', 'G', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Mechanical Room 2', 'Mechanical Attic', 'self closing', 'LH', 'HW-10', 'Ventilation louvers on door', 'GC'),
 ('31', 'G', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Mechanical Room 3', 'Mechanical Attic', 'self closing; smoke seal', 'RH', 'HW-10', 'Ventilation louvers on door', 'GC'),
 ('E32', 'F', 'S', 'HM', 'HM', '2\'-7"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Electrical Room', 'Comedy Club Dining 2', 'self closing', 'LH', 'HW-10', '(E) door: new hardware, paint P-1', 'GC'),
 ('E33', 'F', 'S', 'HM', 'HM', '2\'-11"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Electrical Room', 'Comedy Club Dining 2', 'self closing', 'LH', 'HW-10', '(E) door: new hardware, paint P-1', 'GC'),
 ('34', 'G', 'S', 'HM', 'HM', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', '60', 'Grease Duct Shaft', 'Comedy Club Dining 2', 'self closing; smoke seal', 'RH', 'HW-10', 'Ventilation louvers on door (louver in a 60-min shaft door - RFI)', 'GC'),
 ('35', 'G', 'S', 'HM', 'HM', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', '60', 'Mechanical Room 5', 'Comedy Club Dining 2', 'self closing; smoke seal', 'RH', 'HW-10', 'Ventilation louvers on door (louver in a 60-min door - RFI)', 'GC'),
 ('E38', 'F', 'S', 'HM', 'HM', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', '60', 'BOH', 'Main Building Hallway', 'self closing; smoke seal', 'RH', 'HW-10', 'Ventilation louvers on door; (E) door; room 34 is Day 2', 'GC'),
 ('39', 'F', 'S', 'WD', 'WD', '3\'-0"', '7\'-0"', '1 3/4"', 'P-1', '6/-', '6/-', 'N/A', 'N/R', 'Comedy Club Dining 2', 'BOH', 'self closing', 'RH', '(blank)', 'Day 2 door; hardware set cell blank', 'GC'),
]
TYPES = {'A': 'pair, full-lite aluminum/glass storefront doors, 36" lever/pull height, 12" bottom rail', 'B': 'single full-lite aluminum/glass door, 6" stile, 12" bottom rail', 'C': 'single flush metal door, aluminum/HM frame, panic device + lever trim', 'D': 'cased opening', 'E': 'single aluminum pivot (Eliason) door with 4"x4" window, push plate, 10" kick plate', 'F': 'single flush door with lever', 'G': 'single flush door with ventilation door louver, lever'}
MAT = {'WD': 'wood, solid core (A-7.10 note: all wood doors solid core)', 'HM': 'hollow metal', 'MT': 'metal', 'Alum': 'aluminum', 'Alum/GL': 'aluminum/glass', 'MT/GL': 'metal/glass', 'N/A': 'none (cased opening)'}
for (mk, ty, mode, dm, fm, W, Hh, thk, fin, head, jamb, sill, rating, inside, outside, req, hand, hw, rem, prov) in DOORS:
    existing = mk.startswith('E')
    if mode == 'CO':
        desc = f'Cased opening {mk} (type D): {W} x {Hh}, {fm} frame, finish {fin}; {inside} / {outside}'
        div = '06 20 00'
    else:
        desc = (f'Door {mk} (type {ty}, {"pair" if mode == "P" else "single"}): {W} x {Hh} x {thk}, {MAT.get(dm, dm)} door in {MAT.get(fm, fm)} frame, finish {fin}, '
                f'rating {rating}, head/jamb/sill {head}/{jamb}/{sill}, {inside} / {outside}, handing {hand}; requirements: {req or "none marked"}; hardware {hw}')
        div = '08 11 13' if fm in ('HM', 'MT') else ('08 41 13' if 'Alum' in fm else '08 14 16')
    if existing: desc = '(E) ' + desc
    qty = 2 if mode == 'P' else 1
    basis = 'scheduled'
    note = rem
    fb = 'Owner (E) door' if existing and hw == '-' else ('GC' if prov == 'GC' else f'provided-by cell "{prov}"')
    add('Doors', div, desc, f'{TYPES.get(ty, "")}; door type elevation {ty} on A-7.10 detail 1', qty, 'LEAF' if mode == 'P' else 'EA', basis, DS, fb, 'GC', note)
add('Doors', '08 71 00', 'Hardware set HW-1: panic exit device, UL fire rated, ANSI grade 1, 32" wide, 84" vertical rod', 'Harney Hardware PE550036FPB & PE55003684VFPB, powder coated bronze', 7, 'EA', 'scheduled',
    'A-7.10 hardware schedule (tile arch2/A710_hw.jpg); doors with HW-1: E01 (pair = 2 leaves), 05, 06, E14, 21, 27 -> 2+5 = 7 devices', 'GC', 'GC', 'door 27 is the exit-stair door (separate permit) - 6 if excluded; 60-min doors 05/21/27 need the fire-rated version')
add('Doors', '08 71 00', 'Hardware set HW-2: rim lock cylinder', 'Harney Hardware PENCYSC1, aluminum', 3, 'EA', 'scheduled', 'doors with HW-2: E01 (pair, 2 leaves) + 06 = 3', 'GC', 'GC', 'one cylinder per active leaf assumed for the pair - RFI')
add('Doors', '08 71 00', 'Hardware set HW-3: panic exit device storeroom / keyed function lever trim', 'Harney Hardware PEL8001SRB, powder coated bronze', 4, 'EA', 'scheduled', 'doors with HW-3: 05, E14, 21, 27', 'GC', 'GC', '')
add('Doors', '08 71 00', 'Hardware set HW-4: surface closer', 'LCN 4040XP series, matte black', 11, 'EA', 'scheduled', 'doors with HW-4: E01 (2 leaves), 05, 06, E14, 21, 22, 24, 25, 27, 28 = 11; door types C/F/G elevations also show "self-closer HW-4" and the schedule marks self-closing on 07/08/17/26 (pivot doors, HW-6) and on 19/29-31/34/35/E32/E33/E38/39 whose sets do not list HW-4', 'GC', 'GC', 'RFI: closers for the 14 doors marked self-closing without HW-4 in their set')
add('Doors', '08 71 00', 'Hardware set HW-5: pull handle', 'not specified ("-" manufacturer/model/finish)', 3, 'EA', 'scheduled', 'doors with HW-5: E01 (2 leaves) + 06', 'GC', 'GC', 'product to be selected - RFI')
add('Doors', '08 71 00', 'Hardware set HW-6: pivot set (Eliason-type double-acting door)', 'not specified ("-"), black', 4, 'EA', 'scheduled', 'doors with HW-6: 07, 08, 17, 26', 'GC', 'GC', 'pivots are normally part of the Eliason door - RFI')
add('Doors', '08 71 00', 'Hardware set HW-7: commercial push plate 3.5" x 15"', 'Deltana commercial 3.5"x15" push plate, black', 4, 'EA', 'scheduled', 'doors with HW-7: 07, 08, 17, 26', 'GC', 'GC', 'hardware schedule remark "Loc: Kitchen Door"')
add('Doors', '08 71 00', 'Hardware set HW-8: commercial kick plate 10" x 32"', 'Deltana commercial 10"x32" kick plate, black', 4, 'EA', 'scheduled', 'doors with HW-8: 07, 08, 17, 26', 'GC', 'GC', 'type E elevation shows the 10" plate')
add('Doors', '08 71 00', 'Hardware set HW-9: keyed entry lever', 'Schlage Elan lever keyed entry F51-ELA-716, aged bronze', 5, 'EA', 'scheduled', 'doors with HW-9: 15, 16, 18, 24, 25', 'GC', 'GC', 'provided-by cell blank for HW-9; door 16 is the exit-stair exterior door (a keyed-entry lever on a panic exit door - RFI)')
add('Doors', '08 71 00', 'Hardware set HW-10: light commercial lever, single cylinder storeroom lock', 'Schlage Elan F80CS-V-ELA-716, aged bronze', 11, 'EA', 'scheduled', 'doors with HW-10: 19, 22, 28, 29, 30, 31, E32, E33, 34, 35, E38', 'GC', 'GC', 'provided-by cell blank for HW-10')
add('Doors', '08 71 00', 'Hinges (hinge finish column "-" for every door)', 'not specified', None, 'EA', 'not_quantifiable', 'A-7.10 door schedule hinge-finish column prints "-" throughout; no hinge item in the hardware schedule', 'GC', 'GC', 'RFI: hinge type/finish; 29 new swing doors + 6 (E) doors with new hardware')
add('Doors', '08 71 00', 'Smoke seal / weather gasketing at doors marked in the schedule', 'not specified; "provide hard rubber gasket at exterior doors only, to make rodent-proof" (A-7.10 detail 7)', 15, 'EA', 'scheduled',
    'doors with the smoke-seal/weather-gasketing cell shaded: E01 (pair, 2), 05, 06, 07, 08, E14, 16, 17, 19, 21, 26, 31, 34, 35, E38 -> 16 leaves (door 16 exit stair excluded = 15)', 'GC', 'GC', 'rodent-proof gasket at the 3 exterior doors (E01 pair, 06; 16 under the exit-stair permit)')
add('Doors', '08 71 00', 'Thumb latch on inside (privacy) at restroom / green room doors', 'not specified', 3, 'EA', 'scheduled', 'thumb-latch cell shaded: 15, 24, 25', 'GC', 'GC', 'door 15 set HW-9 is a keyed lever - RFI how the thumb latch is provided')
add('Doors', '08 71 00', 'Double deadbolt at (E) dry-storage door E12', 'not specified', 1, 'EA', 'scheduled', 'double-deadbolt cell shaded at E12', 'GC', 'GC', 'E12 provided-by "-"; confirm whether the deadbolt is new')
add('Doors', '08 91 00', 'Ventilation door louver in door types G', 'not specified; type G elevation "ventilation door louver" (A-7.10 detail 1)', 7, 'EA', 'scheduled', 'type G doors: 19, 29, 30, 31, 34, 35, E38', 'GC', 'GC', '3 of the 7 are 60-min rated doors (19, 34, 35) and E38 is 60 min - fire-rated louvers or RFI; louver size not given')
add('Doors', '08 11 13', 'Hollow metal door frames (type HM, 2" frame typ. per the door-type elevations), welded, for HM doors', 'HM frame; header detail 6/A-7.10 (double box header, steel stud anchors 3 min. per jamb, clear sealant each side)', 7, 'EA', 'scheduled',
    'new HM frames: 19, 21, 27, 34, 35 + (E) frames E32, E33, E38 keep their frames; door 16 MT frame (exit stair) excluded -> 5 new HM frames + 2 metal (MT) at 05/E14 are aluminum frames', 'GC', 'GC', 'counted: 19, 21, 27, 34, 35 = 5 HM; 05 and E14 are MT doors in Alum frames (2); corrected qty 5 HM + 2 Alum')
add('Doors', '08 14 16', 'Wood door frames (WD) for wood doors and cased openings, painted P-1', 'wood frame, 2" typ.; cased openings 02/03/04/23 with 2" wood frame; A-4.31 "2\\" wood frame cased opening, typ."; planton poplar moulding over doors painted P-5 (A-4.31 detail 9) at the mezzanine doors', 14, 'EA', 'scheduled',
    'WD frames: 15, 18, 22, 24, 25, 28, 29, 30, 31, 39 (10 doors) + cased openings 02, 03, 04, 23 (4) = 14', 'GC', 'GC', '(E) wood frames at E09-E12 remain')
add('Doors', '08 41 13', 'Aluminum door frames for aluminum / metal doors (05, 06, 07, 08, 17, 26, E14 (E))', 'aluminum frame, 2" typ.', 6, 'EA', 'scheduled', '05, 06, 07, 08, 17, 26 new (6); E14 and E13 existing', 'GC', 'GC', 'Eliason doors 07/08/17/26 come with their own frames - confirm')
add('Doors', '08 71 00', 'Door threshold at each door (A-2.75/A-2.76 keynote 2 "GC to provide door threshold"; threshold detail 7/A-7.10: 1/4" max. exterior / 1/2" max. interior)', 'per detail 7/A-7.10', 29, 'EA', 'inferred',
    'new swing doors in the schedule excluding (E) doors, cased openings and exit-stair doors 16/27: E01 (pair, 1 threshold), 05, 06, 07, 08, 15, 17, 18, 19, 21, 22, 24, 25, 26, 28, 29, 30, 31, 34, 35, 39 = 21 doors + (E) doors E09-E14, E32, E33, E38 (9) with new floor finishes = 30; minus E13 cased = 29', 'GC', 'GC', 'thresholds at (E) doors only where the floor finish changes (A-2.75 KN1/KN2)')
add('Doors', '08 41 13', 'Window type A (window 1): fixed aluminum storefront unit 3\'-10" x 8\'-1", 2" frame typ., 5" sill, V.I.F.', 'storefront system, non-operable 1-1/8" double pane insulated with laminated film (3/8" .030 lami - 1/2" air gap - 1/4" .030 lami) per Arcadia TC470 STC acoustic specification, 40 STC; frame finish P-2, glass GL-1 (gold mirror per A-7.20 - conflict, see notes)', 1, 'EA', 'scheduled',
    'A-7.10 window schedule and window types detail 4 (arch2/A710_win.jpg, A710_wtype.jpg)', 'GC', 'GC', 'location: the window-type drawing shows a glass panel beside a door leaf (host entry pop-up at the storefront, A-4.20); the hexagon window tag is not legible on A-2.10 - RFI; GL-1 on A-7.20 is "gold mirror, Altered Glass, loc: 2nd level bar", not a glazing type - RFI')
add('Doors', '08 31 13', 'Access hatches in drywall ceilings (CLG-1D)', 'Williams Bros. WB DW 405 Phantom series, color/finish to match adjacent (A-3.12/A-3.22 general note 3)', None, 'EA', 'not_quantifiable',
    'RCP legend symbol "Access Hatch; see Mech & Plumb dwgs." - no symbol of the legend size occurs in the plan areas of A-3.12/A-3.22 (vector search of the A-Symbol layer); count depends on the M/P drawings (mep.csv scope)', 'GC', 'GC', 'specification only; RFI for locations')
add('Doors', '08 31 13', 'Access hatches in tile ceilings', 'Williams Bros. WB DWAL 414 series, color/finish to match adjacent (general note 4)', None, 'EA', 'not_quantifiable', 'no tile ceiling occurs in the ceiling types (CLG-1A GWB, CLG-1D GWB, CLG-3A exposed concrete)', 'GC', 'GC', 'spec given without a location')
add('Doors', '08 71 00', 'Rodent-proof hard rubber gasket at exterior doors (A-7.10 detail 7 note)', 'hard rubber gasket', 3, 'EA', 'scheduled', 'exterior doors on the 6263 Hollywood frontage: E01 (pair, 2 leaves) + 06', 'GC', 'GC', 'door 16 (exit stair, Vine St) under the separate permit')
write()

print('wall LF groups:', {k: round(v, 1) for k, v in g.items()})
print('wall SF by type:', {k: round(v) for k, v in sf.items()})
