"""Linear-foot take-off of pipe and duct runs read off the 200-dpi sheet renders
(the kelly_tiles/<TAG>_p<nn>.jpg renders listed in SHEET_INDEX.md, 6800 x 4400 px = 34 x 22 in).

Scale calibration
  * Addendum 2 P-2 / P-3 / P-4 / P-7 and the MEP set M-2 carry the plan-title strip
    "SCALE: 3/16" = 1'-0"" (the title blocks print 1/4" = 1'-0", which is the sheet default).
    3/16 in per ft at 200 dpi = 37.5 px/ft.  Check: Hood 2 on M-2 (M-6 length 3'-6") measures
    131 px = 3.49 ft; the P-7 gas run dimensioned 26'-0" measures 975 px = 26.0 ft.
  * M-4 MECHANICAL BUILDING SECTION B is titled 1/8" = 1'-0" = 25 px/ft.
Segments are (x0, y0, x1, y1) page pixels of the run centre-lines as read on the gridded crops
(scripts/grid_crops.py).  Vertical risers between floors are not drawn in plan and are listed
separately as open items in mep_notes.md.
Usage: python3 -I measure_runs.py
"""
import math, collections

PX_PER_FT = 37.5
RUNS = [
    # sheet, system, size, label on sheet, [(x0,y0,x1,y1), ...]
    # ---------------- P-2  1ST LEVEL HOT & COLD WATER (Addendum 2 p2) ----------------
    ('P-2', 'CW', '2-1/2"', '2.5" CW (FV) (115 WSFU): (E) 2" meter in sidewalk vault -> 2.5" PRV in basement -> tee at col. line C/D',
     [(4950, 1905, 4400, 1905), (4400, 1905, 4400, 2045), (4400, 2045, 2830, 2045)]),
    ('P-2', 'CW', '2"', '2" CW (FV) (60 WSFU): tee -> (E) restrooms header', [(2830, 2045, 2830, 2800)]),
    ('P-2', 'CW', '1-1/2"', '1-1/2" CW FEED UP TO WATER HTR (55 WSFU): tee -> riser at scullery wall',
     [(2830, 2045, 1615, 2045), (1615, 2045, 1615, 2200)]),
    ('P-2', 'HW', '1-1/2"', '1-1/2" HW (39 WSFU) from WH riser along scullery', [(1590, 2200, 1590, 2005), (1590, 2005, 1850, 2005)]),
    ('P-2', 'HW', '1-1/4"', '1-1/4" HW (24 WSFU)', [(1850, 2005, 2000, 2005)]),
    ('P-2', 'HW', '1"', '1" HW (16 WSFU) / (12 WSFU) kitchen main east, then south to (E) restrooms',
     [(2000, 2005, 2860, 2005), (2860, 2005, 2860, 2800)]),
    ('P-2', 'HW', '1"', '1" H&CW (12 WSFU) branch to KS-1 3-comp sink (HW leg)', [(1735, 2005, 1735, 2400)]),
    ('P-2', 'CW', '1"', '1" H&CW (12 WSFU) branch to KS-1 3-comp sink (CW leg)', [(1770, 2045, 1770, 2400)]),
    ('P-2', 'HW', '3/4"', '3/4" H&CW (8 WSFU) branch to bar BS-1/BS-2 (HW leg)',
     [(1880, 2005, 1880, 2390), (1880, 2390, 2040, 2390), (2040, 2390, 2040, 2140)]),
    ('P-2', 'CW', '3/4"', '3/4" H&CW (8 WSFU) branch to bar BS-1/BS-2 (CW leg)',
     [(1905, 2045, 1905, 2390), (1905, 2390, 2060, 2390), (2060, 2390, 2060, 2140)]),
    ('P-2', 'HW', '3/4"', '3/4" HW (4 WSFU) / (3 WSFU) north branch to HS-1 and KS-2', [(2200, 2005, 2200, 1600)]),
    ('P-2', 'CW', '3/4"', '3/4" CW (5 WSFU) / (4 WSFU) north branch to HS-1 and KS-2', [(2225, 2045, 2225, 1600)]),
    ('P-2', 'CW', '3/4"', '3/4" CW (2 WSFU) to inline filter, items 73/76 ice machines', [(2060, 2440, 2300, 2440)]),
    ('P-2', 'CW', '3/4"', '3/4" CW to inline filter to item 45 combi oven', [(2850, 1150, 2990, 1150)]),
    ('P-2', 'HW', '1/2"', '1/2" HW (1 WSFU) to cook-line HS-1', [(2200, 1600, 2200, 1270), (2200, 1270, 2680, 1270), (2680, 1270, 2680, 1160)]),
    ('P-2', 'CW', '1/2"', '1/2" CW (2 WSFU) to cook-line HS-1', [(2240, 1600, 2240, 1300), (2240, 1300, 2850, 1300), (2850, 1300, 2850, 1150)]),
    ('P-2', 'CW-filtered', '1/2"', '1/2" filtered CW to #80 soda dispenser, #82 coffee, #83 tea (3 drops)', [(2300, 2440, 2750, 2440)]),
    ('P-2', 'HWR', '1/2"', '1/2" H.W.R. from furthest fixture (cook-line HS-1) back to riser',
     [(2650, 1160, 2650, 1255), (2650, 1255, 2175, 1255), (2175, 1255, 2175, 1980), (2175, 1980, 1560, 1980), (1560, 1980, 1560, 2200)]),
    ('P-2', 'HWR', '1/2"', '1/2" H.W.R. restroom leg parallel to 1" HW', [(2890, 2045, 2890, 2800)]),
    ('P-2', 'CW', 'not labeled', '(E) restroom branch header below the 2" CW (sizes not labeled)', [(2830, 2800, 2060, 2800)]),
    ('P-2', 'HW', 'not labeled', '(E) restroom branch header below the 1" HW (sizes not labeled)', [(2860, 2820, 2080, 2820)]),
    # ---------------- P-4  MEZZ. LEVEL HOT & COLD WATER (Addendum 2 p4, lower half) ----------------
    ('P-4', 'HW', '1"', '1" HW (8 WSFU) prep bar -> mezz restrooms', [(1680, 2880, 1790, 2880), (1790, 2880, 1980, 3300), (1980, 3300, 2250, 3300)]),
    ('P-4', 'CW', '1"', '1" CW (13 WSFU) prep bar -> mezz restrooms', [(1680, 2880, 1790, 2880), (1790, 2880, 1980, 3300), (1980, 3300, 2250, 3300)]),
    ('P-4', 'CW', '3/4"', '3/4" CW (7 WSFU) to WC-1, L-1, L-1, WC-1', [(2250, 3300, 3160, 3300), (2680, 3300, 2680, 3470), (2850, 3300, 2850, 3470), (2980, 3300, 2980, 3470), (3160, 3300, 3160, 3470)]),
    ('P-4', 'HW', 'not labeled', 'HW to mezz lavatories beyond the 1" HW (8 WSFU) label', [(2250, 3320, 2980, 3320), (2850, 3320, 2850, 3470), (2980, 3320, 2980, 3470)]),
    ('P-4', 'HWR', '1/2"', '1/2" H.W.R. from furthest fixture (mezz L-1) w/ circuit setter & access panel back to riser',
     [(2980, 3470, 2980, 3330), (2980, 3330, 1980, 3330), (1980, 3330, 1790, 2900), (1790, 2900, 1640, 2900), (1640, 2900, 1640, 2830)]),
    ('P-4', 'HW+CW', '1-1/2"', '1-1/2" H&CW connections to water heater (50 WSFU), plan length only', [(1665, 2830, 1665, 2700), (1665, 2830, 1665, 2700)]),
    # ---------------- P-3  1ST LEVEL WASTE & VENT (Addendum 2 p3) ----------------
    ('P-3', 'SAN', '4"', 'NEW 4" SAN main POC-1 (upstream of kitchen, 27 DFU) -> POC-2 (upstream of restrooms, 85 DFU) replacing the main through the kitchen (A-1.10 KN16)',
     [(1655, 1265, 1880, 1265), (1880, 1265, 2860, 2390), (2860, 2390, 2900, 2470)]),
    ('P-3', 'SAN', '4"', '4" SAN scullery/bar branch from 4" end-of-line W.C.O. (19 -> 26 -> 33 -> 68 -> 73 DFU) to POC-2',
     [(1520, 2300, 2855, 2300), (2855, 2300, 2855, 2420), (2855, 2420, 2900, 2470)]),
    ('P-3', 'SAN', '4"', '4" SAN (12 DFU) riser from mezzanine, plan length to POC-2', [(2825, 2450, 2900, 2470)]),
    ('P-3', 'SAN', '3"', '3" SAN (12 DFU) KS-1 3-comp header; 3" SAN (4 DFU) GT-1 / MS-1',
     [(1600, 2300, 1600, 2440), (1600, 2440, 1860, 2440), (1590, 2440, 1590, 2500), (1590, 2500, 1750, 2500)]),
    ('P-3', 'SAN', '2"', '2" SAN branches: PW-1/DM-1 (5 DFU), HS-1 (2 DFU), FD-1 (1 DFU), mezz 2" riser (7 DFU) tie-in, cook-line FS-1 run (3/5 DFU), FS-1 serving combi oven, walk-in FS-1',
     [(1780, 1900, 1780, 1705), (1700, 1705, 2200, 1705), (1560, 2030, 1560, 2300), (1740, 2050, 1740, 2300), (1590, 2400, 1590, 2500),
      (2855, 1175, 2855, 2300), (2800, 1575, 2990, 1575), (2680, 1815, 2990, 1850), (2900, 1280, 2990, 1280), (1935, 1215, 2030, 1265)]),
    # ---------------- P-4  MEZZ. LEVEL WASTE & VENT (Addendum 2 p4, upper half) ----------------
    ('P-4', 'SAN', '2"', '2" SAN (7 -> 4 -> 2 DFU) prep bar: riser -> BS-3, BS-4, FD-1 -> BS-5',
     [(1510, 800, 2060, 800), (2060, 800, 2080, 1060), (1660, 980, 1660, 800), (1700, 860, 1700, 800), (1780, 870, 1780, 800)]),
    ('P-4', 'SAN', '4"', '4" SAN (12 DFU) mezz restrooms to riser', [(2920, 820, 2920, 1330)]),
    ('P-4', 'SAN', '3"', '3" SAN (5 DFU / 6 DFU) to WC-1 and L-1 each side', [(2920, 1370, 2680, 1370), (2920, 1370, 3160, 1370)]),
    # ---------------- M-2  MECHANICAL 1ST FLOOR PLAN (MEP p2) ----------------
    ('M-2', 'SA duct WSHP-8', '37 in wide (scaled, not labeled)', 'WSHP-8 discharge, unit to elbow', [(4130, 1308, 3832, 1308)]),
    ('M-2', 'SA duct WSHP-8', '40 in wide (scaled, not labeled)', 'kitchen supply trunk north-south with 2 round diffusers in lift-out panels', [(3832, 1302, 3832, 2170)]),
    ('M-2', 'SA duct WSHP-8', '42 in wide (scaled, not labeled)', 'EXPOSED A/C SUPPLY DUCT BELOW CEILING east-west, 6 drops', [(3832, 2170, 2740, 2170)]),
    ('M-2', 'SA duct WSHP-8', '16 in wide (scaled, not labeled)', 'SOFFIT FOR A/C SUPPLY to (E) men\'s restroom', [(3225, 2235, 3225, 3050), (3225, 3080, 3790, 3080)]),
    ('M-2', 'MUA duct', '32 in wide (scaled, not labeled)', 'EXPOSED MUA SUPPLY DUCT BELOW CEILING west of (E) MUA riser, 4 drops', [(3480, 1390, 2585, 1390)]),
    ('M-2', 'MUA duct', '19 in wide (scaled, not labeled)', 'MUA supply east of riser toward hoods', [(3480, 1390, 3745, 1390)]),
    ('M-2', 'SA duct dining', '22 in wide (scaled, not labeled)', 'A/C SUPPLY UNDER MEZZANINE LEVEL, south run from SE riser, 2 drops', [(5650, 3695, 4715, 3695)]),
    ('M-2', 'SA duct dining', '19 in wide (scaled, not labeled)', 'A/C SUPPLY UNDER MEZZANINE LEVEL, east wall run with 5 side grilles', [(5515, 3695, 5515, 1690)]),
    ('M-2', 'SA duct dining', '21 in wide (scaled, not labeled)', 'A/C SUPPLY UNDER MEZZANINE LEVEL, north run, 3 drops', [(5515, 1690, 4635, 1690)]),
]
RUNS_SECTION = [  # M-4 section B at 1/8" = 1'-0" (25 px/ft)
    ('M-4', 'grease duct', 'riser 16x14 (M-2)', 'Hood 1 riser to collector', [(4800, 3720, 4800, 3590)]),
    ('M-4', 'grease duct', 'riser 12x12 (M-2)', 'Hood 2 (right) riser to collector', [(4600, 3720, 4600, 3590)]),
    ('M-4', 'grease duct', 'not labeled', 'collector from Hood 2 riser to Hood 1 riser, sloped to shaft', [(4600, 3590, 4830, 3560)]),
    ('M-4', 'grease duct', 'not labeled', 'main from Hood 1 riser to (E) fire-rated shaft', [(4830, 3560, 5190, 3500)]),
    ('M-4', 'grease duct', 'not labeled', 'vertical in (E) shaft, level 02 to roof AS DRAWN (section broken between levels 05 and 13)', [(5190, 3500, 5190, 1950)]),
]

def lf(segs, ppf):
    return sum(math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in segs) / ppf

if __name__ == '__main__':
    tot = collections.OrderedDict()
    print(f"{'sheet':5} {'system':18} {'size':34} {'LF':>7}  label")
    for sheet, system, size, label, segs in RUNS:
        v = lf(segs, PX_PER_FT)
        tot[(sheet, system, size)] = tot.get((sheet, system, size), 0) + v
        print(f"{sheet:5} {system:18} {size:34} {v:7.1f}  {label}")
    for sheet, system, size, label, segs in RUNS_SECTION:
        v = lf(segs, 25.0)
        tot[(sheet, system, size)] = tot.get((sheet, system, size), 0) + v
        print(f"{sheet:5} {system:18} {size:34} {v:7.1f}  {label}")
    print("\n== totals by sheet / system / size")
    for k, v in tot.items():
        print(f"  {k[0]:5} {k[1]:18} {k[2]:34} {v:7.1f} LF")
