#!/usr/bin/env python3
"""Hollywood Comedy Club TI (Kelly Architects job 2604) - quantity takeoff.

Writes ../takeoff.csv. Every quantity is either read from a drawing available in the bid
documents on hand, carried from the prior estimate session (transcript line cited), or an
arithmetic identity of cited numbers (the arithmetic is written in qty_source).

Run:  python3 -I takeoff.py            (from any directory; paths are resolved from this file)
"""
import csv, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
OUT = os.path.join(PROJ, "takeoff.csv")

# ---------------------------------------------------------------------------------------------
# Source documents (bid set on hand) and transcript files of the prior session (2026-10-20)
# ---------------------------------------------------------------------------------------------
A210 = "03_Architectural_Plans_Demo_RCP.pdf p4 (A-2.10 floor plan)"
A220 = "03_Architectural_Plans_Demo_RCP.pdf p5 (A-2.20 mezzanine plan)"
A110 = "03_Architectural_Plans_Demo_RCP.pdf p2 (A-1.10 demo plan)"
A120 = "03_Architectural_Plans_Demo_RCP.pdf p3 (A-1.20 demo mezzanine)"
A312 = "03_Architectural_Plans_Demo_RCP.pdf p6 (A-3.12 RCP)"
A322 = "03_Architectural_Plans_Demo_RCP.pdf p7 (A-3.22 mezzanine RCP)"
A401 = "03_Architectural_Plans_Demo_RCP.pdf p8 (A-4.01 exterior elevations)"
A511 = "03_Architectural_Plans_Demo_RCP.pdf p9 (A-5.11)"
A512 = "03_Architectural_Plans_Demo_RCP.pdf p10 (A-5.12 mezz restrooms)"
ADD = "2604-260921-HW_Comedy-Bid_Addendum1.pdf"
ST = "2604-260626-Exit_Stairs-PC_Submittal1.pdf"
T1 = "mac_session_page1.txt"
T2 = "mac_session_page2.txt"
T3 = "mac_session_page3.txt"

# ---------------------------------------------------------------------------------------------
# Cited base numbers
# ---------------------------------------------------------------------------------------------
GROSS_SF = 7141                      # T1 L437: "7,141 SF gross per Alice Teng 10/1/26"
# Room areas as measured by the prior session from A-2.10 / A-2.20 (area_alloc output), T2 L265-294
ROOM = dict(L1_13=54, L1_14=250, M_21=1088, M_22=70, M_23=70, M_24=123, M_25=183, M_26=111, M_27=81,
            M_28=99, M_29=58, M_30=45, M_E33=19, M_32=64, M_34=107, M_35=703, M_05=76, M_06=52,
            M_10=24, M_14=62)
GROUP = dict(lobby_host_green=227, dining_L1=1925, hallways=913, stairs_lift_dumbwaiter=758,
             kitchen_bar_wait=1653, restrooms=578, comedy_club_2=1088, boh_mech_shafts=767, total=7908)
# arithmetic identities of the cited group / room numbers
HALL_L1 = GROUP["hallways"] - ROOM["M_35"]                      # 913 - 703 = 210
KITCHEN_GROUP_L1 = GROUP["kitchen_bar_wait"] - ROOM["M_24"]     # 1653 - 123 = 1530 (rooms 07, 08, 09)
RR_L1_ALL = GROUP["restrooms"] - ROOM["M_22"] - ROOM["M_23"]    # 578 - 140 = 438 (rooms 11, 12, 13)
RR_MEZZ = ROOM["M_22"] + ROOM["M_23"]                           # 140
MEZZ_TOTAL = sum(v for k, v in ROOM.items() if k.startswith("M_"))   # 3035
MEZZ_CLG3A = ROOM["M_21"] + ROOM["M_35"] + RR_MEZZ + GROUP["boh_mech_shafts"]   # 2698 (all mezz rooms tagged CLG-3A on A-3.22 except prep bar 24)
CLG1D_SF = KITCHEN_GROUP_L1 + HALL_L1 + GROUP["lobby_host_green"] + ROOM["M_10"] + ROOM["M_24"]   # 2114
CLG3A_SF = GROUP["dining_L1"] + MEZZ_CLG3A                      # 1925 + 2698 = 4623
KITCHEN_DEMO_SF = 1340               # T1 L445: 02-010 "Strip kitchen ... 1340 SF ... A-1.10 KN4,5; room area measured"
BAR_LF = 62                          # T1 L446: 02-020 "Remove (E) bar, back bar, diewall, millwork 62 LF (A-1.10 KN8)"

# Wall takeoff by drawn wall-type tag, adopted in the prior session on 10/20/2026 (T1 L355, L633-639)
WALL = {"A": dict(lf=921, h=13.5, sf=12434, tags="2, AC, 1, 5"),
        "B": dict(lf=119, h=16.4, sf=1952, tags="1A (2-hr), 3 (1-hr exterior plaster)"),
        "C": dict(lf=20, h=14.0, sf=280, tags="shaft/enclosure walls with no tag")}
WALL_SRC = f"{T1} L636 (LF by drawn tag: A 921 / B 119 / C 20; average heights 13.5 / 16.4 / 14.0 ft carried from the original estimate), L637 (SF 12434 / 1952 / 280), L639 (L1 452 LF, mezz 608 LF)"

# Wall-finish areas read by the prior session from the Addendum 1 elevations (fin_load output), T2 L65-77
FIN = dict(WC8=890 + 234 + 864, WC8_WD1_mixed=135, WD1=10, WC3=260,
           WC4=773 + 44 + 177 + 795 + 55 + 1643 + 141, TX4=611, TX2=15 + 7, AC1=121,
           WT1=81 + 78, P1=162 + 169, P3=6 + 29,
           B4_L1=49 + 206 + 40 + 155, B4_mezz=86 + 9 + 33 + 125 + 11 + 260 + 21, B1=33 + 34)
FIN_SRC = f"{T2} L65-77 (fin_load.py output: wall finish SF by room and code read from Addendum 1 elevations A-4.20..A-4.34 and A-5.12)"

# Light fixture tags counted on the RCP text layers (this session; identical to T1 L404-405)
LIGHTS_L1 = dict(A1=9, D1=9, F1=22, X1=9, X2=3, Y1=2, Y2=10, Y3=9)
LIGHTS_M = dict(A1=2, B1=28, C1=6, C2=3, D1=6, F1=2, X1=9, Y1=13, Y2=1)
DECOR_L1 = 35      # G1..G18 (one each) + G5 x18 + G20 x2 on A-3.12
DECOR_M = 27       # G10, G11, G21 (one each) + G19 x11 + G20 x13 on A-3.22
EXIST_FIX_L1 = 14  # (E)A2 x11 + (E)Y3 x3 remain on A-3.12

# Doors: new-door tags (ovals) found on the plans this session
DOORS_L1 = ["01", "02", "03", "04", "05", "06", "07", "08", "15", "16", "17", "18"]
DOORS_M = ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "34", "35", "39"]
EXIST_DOORS = ["E09", "E10", "E11", "E12", "E13", "E14", "E32", "E33", "E38"]
EXT_DOORS = 4      # A-4.01 KN5 at elevations 2 and 4 (2) + exit stair submittal p3 KN3 at elevation 7 (2)

# Exit stair (1704 N Vine St) from the PC submittal
ST_RISERS = 11                       # A-6.11: "11 RISERS @ 6 9/16""
ST_TREADS = 10                       # A-6.11: "10 TREADS @ 11""
ST_RUN_FT = 10 * 11 / 12             # 9'-2" (A-6.11)
ST_RISE_FT = 6.0                     # landing at +6'-0" A.F.F. (A-6.10 / A-6.11)
ST_STRINGER_FT = math.sqrt(ST_RUN_FT ** 2 + ST_RISE_FT ** 2)
ST_WALL_L1_LF = 11 + 10.5 / 12 + 5.25 + 14 + 11 / 12 + 6 + 4 / 12 + 5 + 11 / 12   # 11'-10 1/2" + 5'-3" + 14'-11" + 6'-4" + 5'-11"
ST_WALL_M_LF = 11 + 10.5 / 12 + 5.5                                              # 11'-10 1/2" + 5'-6"
ST_WALL_H_L1 = 9 + 6.5 / 12          # A-6.11 section 1: 9'-6 1/2" V.I.F.
ST_WALL_H_M = 7 + 6.5 / 12           # A-6.11 section 2: 7'-6 1/2"
ST_WALL_SF = ST_WALL_L1_LF * ST_WALL_H_L1 + ST_WALL_M_LF * ST_WALL_H_M
ST_LANDING_W, ST_LANDING_D = 5.0, 4.0   # A-6.10 plan dims 5'-0" x 4'-0" at the landing
ST_HSS_LF = 2 * (ST_LANDING_W + ST_LANDING_D)
ST_RAIL_LF = 2 * (ST_STRINGER_FT + 1.0 + (1 + 11 / 12))   # both sides; 1'-0" top and 1'-11" (TW+12") bottom extensions, A-6.11

ROWS = []


def add(item_id, bid_item, division, desc, qty, unit, basis, source, notes=""):
    ROWS.append(dict(item_id=item_id, bid_letter_item=bid_item, division=division, description=desc,
                     qty=("" if qty is None else (round(qty, 2) if isinstance(qty, float) else qty)),
                     unit=unit, qty_basis=basis, qty_source=source, notes=notes))


# Bid-letter items (15 from the architect's bid letter + "Other required scope")
DEMO, WALLS, CEIL, FLOOR, ROOF, FIN_, EXT, DOORS, STAIRS, OWNER, LIGHT, MECH, PLUMB, LV, FB, OTHER = (
    "Demolition", "Interior walls", "Ceilings", "Flooring", "New Roofing", "Interior finishes",
    "Exterior finishes", "Doors & Hardware", "Stairs & railing", "Owner-provided equipment install",
    "Lighting", "Mechanical", "Plumbing", "Low Voltage", "F&B equipment", "Other required scope")

# ============================================= DEMOLITION =============================================
add("D01", DEMO, "02 41 19", "Strip (E) kitchen: equipment, walk-ins, hood and ducts (disconnect by trades)", KITCHEN_DEMO_SF, "SF",
    "prior_estimate", f"{T1} L445 (02-010: 1,340 SF, A-1.10 KN4, KN5; room area measured)",
    "equipment count not available (no K sheets); A-1.10 KN4, KN5")
add("D02", DEMO, "06 05 05", "Remove (E) bar, back bar, diewall and millwork", BAR_LF, "LF",
    "prior_estimate", f"{T1} L446 (02-020: 62 LF, A-1.10 KN8)", "A-1.10 KN8")
add("D03", DEMO, "02 41 19", "Remove (E) raised platforms, booths and ramp", None, "LS",
    "not quantifiable", f"{A110} KN10, KN12 (not dimensioned)", "")
add("D04", DEMO, "02 41 19", "Remove (E) curved stair to mezzanine", 1, "EA",
    "drawn", f"{A110} KN11; {A120} KN8", "")
add("D05", DEMO, "02 41 19", "Remove (E) decorative non-bearing walls around structural columns", None, "LS",
    "not quantifiable", f"{A110} KN9 (2 tags + TYP.); {A120} KN7 (3 tags + TYP.)", "SF not dimensioned")
add("D06", DEMO, "02 41 19", "Remove (E) partitions and shaft wall", None, "LS",
    "not quantifiable", f"{A120} KN4, KN13 (1 tag); {A110} dashed walls not dimensioned", "")
add("D07", DEMO, "09 05 05", "Remove (E) ceiling coffers and mouldings, expose (E) structural beams (mezzanine)", ROOM["M_21"], "SF",
    "inferred (explain)", f"{A120} KN14; area = room M-21 {ROOM['M_21']} SF ({T2} L267)", "coffer material not stated on A-1.20")
add("D08", DEMO, "02 41 19", "Saw-cut and remove (E) concrete floor for trenching, floor drains/sinks, dumbwaiter and dishwasher exhaust", None, "LS",
    "not quantifiable", f"{A110} KN6; {A120} KN6, KN18 (P sheets not issued)", "")
add("D09", DEMO, "03 01 30", "Fill (E) core-drilled floor opening for ductwork", 1, "EA",
    "drawn", f"{A120} KN19", "opening size not stated")
add("D10", DEMO, "08 05 05", "Remove two panels of (E) window glass and frame for new exit door(s)", 2, "EA",
    "drawn", f"{A110} KN13; {A120} KN9 ('two panels of window glass & frame')", "")
add("D11", DEMO, "08 05 05", "Remove (E) doors", 5, "EA",
    "drawn", f"{A110} KN19 (2 tags); {A120} KN12 (3 tags)", "tag instances counted on the text layer")
add("D12", DEMO, "26 05 05", "Remove (E) light fixtures on mezzanine ceiling", None, "LS",
    "not quantifiable", f"{A120} KN15 (count not shown)", "")
add("D13", DEMO, "26 05 05", "Remove all (E) J-boxes and conduit in their entirety", None, "LS",
    "not quantifiable", f"{A110} general note 2; {A120} general note 2", "")
add("D14", DEMO, "22 05 05", "Remove (E) bar plumbing utilities; (E) lines to remain if they cannot be removed", None, "LS",
    "not quantifiable", f"{A110} KN8, KN22; {A120} KN20", "")
add("D15", DEMO, "09 05 05", "Patch and repair (E) terrazzo floor as required", None, "LS",
    "not quantifiable", f"{A110} KN14 (extent not shown)", "")
add("D16", DEMO, "02 41 19", "Expose (E) concrete columns; patch and repair", None, "LS",
    "not quantifiable", f"{A110} KN18; {A120} KN11 (count not shown)", "")

# ============================================= INTERIOR WALLS =============================================
for cls, d in WALL.items():
    add(f"W0{'ABC'.index(cls)+1}", WALLS, "09 21 16", f"New wall class {cls} (tags {d['tags']}): LF x average height = SF of wall (one face)",
        d["sf"], "SF", "prior_estimate", f"{WALL_SRC}; SF = {d['lf']} LF x {d['h']} ft = {d['lf']*d['h']:.0f}",
        {"A": "types 1 and 2: 3-5/8 in 20 ga studs 16 in o.c., 5/8 in Type X each side, 4 in acoustic insulation; AC: 4 in 16 ga studs, 2 layers 5/8 in Type X each side; type 5: 2 in steel on (E) wall, 5/8 in one side (A-2.10 / A-2.20 wall notes)",
         "B": "1A: 6 in 20 ga studs, 2 layers Type X each side (2-hr); 3: 6 in 20 ga studs, 5/8 in DensGlass, felt, 1 in exterior plaster, 5/8 in Type X interior (A-2.10 wall notes)",
         "C": "assembly per A-6.xx / S sheets (not issued)"}[cls])
add("W04", WALLS, "09 29 10", "Wall type AC: second layer of 5/8 in Type X each side (in addition to class A base assembly)", None, "SF",
    "not quantifiable", f"{A210} AC tags x8, {A220} AC tags x4 (square tags counted on the text layer); LF per tag not separable from the class A total",
    "open item: AC share of class A not separable")
add("W05", WALLS, "09 24 23", "Wall type 3 exterior side: 5/8 in DensGlass, 2 layers felt, 1 in exterior plaster", None, "SF",
    "not quantifiable", f"{A210} type 3 tags x4; {A220} x2; LF per tag not separable from the class B total", "")
add("W06", WALLS, "09 22 16", "Furr out and patch (E) wall for a continuous smooth surface", None, "LS",
    "not quantifiable", f"{A210} KN15 (not dimensioned)", "")
add("W07", WALLS, "09 22 16", "Low wall 24 in tall around sloped ceiling (mezzanine)", None, "LF",
    "not quantifiable", f"{A220} KN17 (not dimensioned)", "")
add("W08", WALLS, "09 21 16", "Exit stair 1-hr enclosure walls (1704 N Vine): 6 in 16 ga studs 16 in o.c., 5/8 in Type X each side, 4 in acoustic insulation (UL U404)",
    ST_WALL_SF, "SF", "drawn",
    f"{ST} p3 (A-2.10 proposed plans): L1 runs 11'-10 1/2\" + 5'-3\" + 14'-11\" + 6'-4\" + 5'-11\" = {ST_WALL_L1_LF:.2f} LF; mezz runs 11'-10 1/2\" + 5'-6\" = {ST_WALL_M_LF:.2f} LF; heights {ST} p5 (A-6.11): 9'-6 1/2\" V.I.F. (L1) and 7'-6 1/2\" (mezz); SF = {ST_WALL_L1_LF:.2f} x {ST_WALL_H_L1:.3f} + {ST_WALL_M_LF:.2f} x {ST_WALL_H_M:.3f} = {ST_WALL_SF:.1f}",
    "wall note 1 on the submittal plan")
add("W09", WALLS, "09 29 10", "Level 5 skim coat premium in public patron areas (dining, vestibules, restrooms)", None, "SF",
    "not quantifiable", f"{A210} GYP BOARD FINISH note 1; public/BOH wall split not separable", "")

# ============================================= CEILINGS =============================================
add("C01", CEIL, "09 22 26", "CLG-1D: new 5/8 in Firecode 30 GWB on new steel joists (3-5/8 in under 4 ft span, 6 in elsewhere), smooth washable finish",
    CLG1D_SF, "SF", "inferred (explain)",
    f"rooms tagged CLG-1D on {A312} / {A322}: kitchen+storage+wait station {KITCHEN_GROUP_L1} (= 1653 - 123, {T2} L291, L270) + hallway L1 {HALL_L1} (= 913 - 703, {T2} L289, L280) + host+green room {GROUP['lobby_host_green']} ({T2} L287) + dumbwaiter {ROOM['M_10']} ({T2} L283) + prep bar {ROOM['M_24']} ({T2} L270) = {CLG1D_SF}",
    "excludes the 8'-0\" CLG-1D perimeter band in dining 02 and the ADA lift lobby (not measured)")
add("C02", CEIL, "09 91 23", "Paint P-1 on new CLG-1D ceilings, primer and 2 coats", CLG1D_SF, "SF",
    "inferred (explain)", f"{A312} leaders '2 / P-1 TYP.' at the CLG-1D rooms; SF = C01", "")
add("C03", CEIL, "09 29 10", "Mezzanine curved soffits CLG-1D at 15'-9\" with P-3 (8 locations)", None, "SF",
    "not quantifiable", f"{A322} 'CURVE UP 15'-9\" CLG-1D P-3' x8 (not dimensioned)", "")
add("C04", CEIL, "09 91 23", "CLG-1A: refinish (E) GWB ceilings at (E) first-floor restrooms", RR_L1_ALL, "SF",
    "inferred (explain)", f"{A312} CLG-1A tags at rooms 11, 12, 13; SF = 578 - 70 - 70 ({T2} L292, L268, L269) = {RR_L1_ALL}", "")
add("C05", CEIL, "03 35 00", "CLG-3A: clean and patch (E) exposed concrete waffle ceiling; stain and seal (E) beams and slab (ST-2/SL-2)",
    CLG3A_SF, "SF", "inferred (explain)",
    f"{A312} CLG-3A at dining 02 (1,925 SF, {T2} L288) + {A322} CLG-3A at all mezzanine rooms except prep bar: {MEZZ_CLG3A} SF (= 1088 + 703 + 140 + 767, {T2} L267, L280, L268-269, L294); {ADD} A-4.30..A-4.34 '(E) CONCRETE BEAMS & SLAB TO BE STAINED & SEAL'",
    "RCP keynote 1")
add("C06", CEIL, "07 21 29", "K-13 spray-applied acoustical insulation within (E) concrete coffers (no K-13 on ribs)", CLG3A_SF, "SF",
    "inferred (explain)", f"{A312} / {A322} keynote 1 and AC-1 tags; upper-bound surface = C05 ceiling area (coffer share not stated)", "")
add("C07", CEIL, "08 31 13", "Access hatches in GWB ceilings (Williams Bros. WB DW 405 / DWAL 414)", None, "EA",
    "not quantifiable", f"{A312} / {A322} general notes 3, 4 (hatch symbols not counted; mech/plumb drawings not issued)", "")
add("C08", CEIL, "09 22 16", "Frame around (E) ceiling beams and new soffit at hallway openings (mezzanine)", None, "LS",
    "not quantifiable", f"{ADD} A-4.30 notes 'GC TO FRAME WALL AROUND IT', 'ALIGN BOTTOM OF NEW SOFFIT'", "")

# ============================================= FLOORING =============================================
add("F01", FLOOR, "09 60 00", "Floor finish, dining 02 (level 1) - finish code not issued", GROUP["dining_L1"], "SF",
    "prior_estimate", f"{T2} L288 (1,925 SF)", "A-2.75 floor finish plan and A-7.20 schedule not issued")
add("F02", FLOOR, "09 60 00", "Floor finish, hallway 04 (level 1) - finish code not issued", HALL_L1, "SF",
    "prior_estimate", f"{T2} L289 - L280 (913 - 703)", "A-2.75 not issued")
add("F03", FLOOR, "09 30 13", "Lobby/host floor tile FL-7 / FL-8 checkerboard with GRT-1 and green room FL-4", GROUP["lobby_host_green"], "SF",
    "prior_estimate", f"{T2} L287 (227 SF, rooms 01 + 03); {ADD} A-4.20 tags FL-7, FL-8, GRT-1; A-4.21 FL-4", "lobby/green room split not separable")
add("F04", FLOOR, "09 60 00", "Floor finish, kitchen, dry storage, wait station - finish not issued", KITCHEN_GROUP_L1, "SF",
    "prior_estimate", f"{T2} L291 - L270 (1653 - 123)", "A-2.75 / A-7.20 not issued")
add("F05", FLOOR, "09 60 00", "Floor finish, mezzanine dining 2 and hallway 35 - finish not issued", ROOM["M_21"] + ROOM["M_35"], "SF",
    "prior_estimate", f"{T2} L267 + L280 (1088 + 703)", "A-2.76 not issued")
add("F06", FLOOR, "09 31 13", "Mezzanine restroom floor tile WT-1 with GRT-1 (1/8 in grout)", RR_MEZZ, "SF",
    "prior_estimate", f"{T2} L268-269 (70 + 70 SF); {A512} general note 1, tags WT-1, GRT-1", "tile product per A-7.20 (not issued)")
add("F07", FLOOR, "06 40 23", "Stage millwork platform, level 1, 18 in AFF with LVT FL-6", 12 * (8 + 8 / 12), "SF",
    "drawn", f"{ADD} A-4.22 main stage plan 12'-0\" x 8'-8\" = 104 SF; {A210} KN18", "")
add("F08", FLOOR, "06 40 23", "Stage millwork platform, mezzanine, 6 in AFF with LVT FL-6", None, "SF",
    "not quantifiable", f"{A220} KN22 (not dimensioned); {ADD} A-4.30 note 5 shows 10 in", "stage height conflict 6 in vs 10 in")
add("F09", FLOOR, "06 22 13", "Wood base B-4 painted P-2, level 1 rooms", FIN["B4_L1"], "LF",
    "prior_estimate", f"{FIN_SRC}: B-4 LF 49 + 206 + 40 + 155 = {FIN['B4_L1']}", "")
add("F10", FLOOR, "06 22 13", "LED base B-4 with P-5, mezzanine, lift lobbies and stair 2 (4 in, straight sections only)", FIN["B4_mezz"], "LF",
    "prior_estimate", f"{FIN_SRC}: B-4 LF 86 + 9 + 33 + 125 + 11 + 260 + 21 = {FIN['B4_mezz']}; {ADD} A-4.32 note on straight sections", "")
add("F11", FLOOR, "09 31 13", "Tile cove base B-1 at mezzanine restrooms", FIN["B1"], "LF",
    "prior_estimate", f"{FIN_SRC}: B-1 LF 33 + 34 = {FIN['B1']}", "")
add("F12", FLOOR, "03 35 00", "Floor preparation, leveling and moisture mitigation", None, "LS",
    "not quantifiable", "no finish plan issued (A-2.75 / A-2.76)", "")
add("F13", FLOOR, "09 66 00", "7 in terrazzo step at new exit door to match (E) sidewalk terrazzo", None, "LF",
    "not quantifiable", f"{A401} KN10 (length not dimensioned)", "")

# ============================================= NEW ROOFING =============================================
add("R01", ROOF, "07 50 00", "Roof penetrations, curbs and flashing at grease duct and rooftop equipment", None, "LS",
    "not quantifiable", "no roof plan or M sheets issued", "")

# ============================================= INTERIOR FINISHES =============================================
add("I01", FIN_, "09 72 16", "WC-8 wallcovering Type II (Calico 'Pyrite' P-1205 or equal), main room, green room, hallway", FIN["WC8"], "SF",
    "prior_estimate", f"{FIN_SRC}: WC-8 890 (L1-02) + 234 (L1-03) + 864 (L1-04) = {FIN['WC8']}; plus 135 SF mixed WD-1/WC-8 not included", "no waste added")
add("I02", FIN_, "06 22 13", "Poplar moulding grid 1/2 in x 1/4 in stained to match WC-8, at 1'-8\" W x 2'-4\" H o.c.", FIN["WC8"] * (1 / (1 + 8 / 12) + 1 / (2 + 4 / 12)), "LF",
    "inferred (explain)", f"{ADD} A-4.21..A-4.27 note; LF = WC-8 SF x (1/1.6667 + 1/2.3333) = {FIN['WC8']} x 1.0286 = {FIN['WC8'] * (1 / (1 + 8 / 12) + 1 / (2 + 4 / 12)):.0f}", "drawn size 1/2 x 1/4 in (T2 L21)")
add("I03", FIN_, "09 72 23", "WC-3 wallcovering, lobby", FIN["WC3"], "SF",
    "prior_estimate", f"{FIN_SRC}: WC-3 260 (L1-01)", "product per A-7.20 (not issued)")
add("I04", FIN_, "09 72 23", "WC-4 wallpaper, all mezzanine walls, lift vestibules, stair 2", FIN["WC4"], "SF",
    "prior_estimate", f"{FIN_SRC}: WC-4 773 + 44 + 177 + 795 + 55 + 1643 + 141 = {FIN['WC4']}", "product per A-7.20 (not issued)")
add("I05", FIN_, "09 84 13", "TX-4 fabric-wrapped 2 in acoustic panels at main stage wall", FIN["TX4"], "SF",
    "prior_estimate", f"{FIN_SRC}: TX-4 611 (L1-02); {ADD} A-4.22A detail", "")
add("I06", FIN_, "12 22 00", "TX-2 drapery with HW-20 / HW-21 hardware (lobby arch, green room window, main room)", FIN["TX2"], "SF",
    "prior_estimate", f"{FIN_SRC}: TX-2 15 + 7 = 22", "")
add("I07", FIN_, "06 42 00", "WD-1 wood paneling, main room", FIN["WD1"] + FIN["WC8_WD1_mixed"], "SF",
    "prior_estimate", f"{FIN_SRC}: WD-1 10 + mixed WD-1/WC-8 135 = {FIN['WD1'] + FIN['WC8_WD1_mixed']}", "")
add("I08", FIN_, "09 91 23", "Paint P-1 walls above tile, mezzanine restrooms, primer and 2 coats", FIN["P1"], "SF",
    "prior_estimate", f"{FIN_SRC}: P-1 162 + 169 = {FIN['P1']}", "")
add("I09", FIN_, "09 31 13", "Wall tile WT-1 wainscot 4'-0\" high, mezzanine restrooms", FIN["WT1"], "SF",
    "prior_estimate", f"{FIN_SRC}: WT-1 81 + 78 = {FIN['WT1']}; {A512} KN17", "")
add("I10", FIN_, "09 91 23", "Paint P-5 mezzanine doors and frames", len(DOORS_M), "EA",
    "drawn", f"{A220} new-door tags {', '.join(DOORS_M)} ({len(DOORS_M)}); {ADD} A-4.30..A-4.33 'DOOR P-5 / FRAME P-5'", "")
add("I11", FIN_, "06 22 13", "Planton poplar moulding over mezzanine doors, painted P-5", len(DOORS_M), "EA",
    "drawn", f"{ADD} A-4.31 note 'PROVIDE PLANTON MOULDING OVER DOOR'; one per mezzanine door ({len(DOORS_M)})", "LF per door not dimensioned (door widths per A-7.10 not issued)")
add("I12", FIN_, "06 22 13", "2 in wood frame cased openings", 4, "EA",
    "drawn", f"{A210} KN3 x3; {A220} KN3 x1; {ADD} A-4.31 '2\" WOOD FRAME CASED OPENING, TYP.'", "")
add("I13", FIN_, "09 77 30", "FRP on inside face of prep bar", 14 + 11 / 12 * 3.5, "SF",
    "inferred (explain)", f"{ADD} A-4.33 note 'PROVIDE FRP ON INSIDE FACE OF PREP BAR'; prep bar 14'-11\" ({A220} dim) x 42 in counter height (A-4.33) = {(14 + 11 / 12) * 3.5:.1f} SF", "")
add("I14", FIN_, "03 35 00", "Stain and seal (E) concrete columns ST-2 / SL-2", 16, "EA",
    "prior_estimate", f"{T1} L116 (model: IfcColumn 16); {ADD} A-4.20..A-4.34 '(E) CONCRETE COLUMN, CLEAN AND SEAL, TYP.'", "column surface area not stated")
add("I15", FIN_, "05 58 13", "Perforated metal enclosure floor to exposed ceiling at (E) plumbing lines around column", 2, "EA",
    "drawn", f"{A210} KN21 x1; {A220} KN23 x1", "")
add("I16", FIN_, "06 40 23", "Light-beam millwork fins with LED (two channels) and stage-wall millwork", None, "LS",
    "not quantifiable", f"{A210} KN20; {ADD} A-4.22A (not dimensioned in plan)", "")
add("I17", FIN_, "06 40 23", "Mezzanine stage decorative wood 4 in x 3 in with 1 W bulbs at 12 in o.c.", None, "LF",
    "not quantifiable", f"{ADD} A-4.30 details 8A/8B (stage not dimensioned)", "")
add("I18", FIN_, "09 91 23", "Paint P-3 wood frames at lobby arch and pop-up, soffits", FIN["P3"], "SF",
    "prior_estimate", f"{FIN_SRC}: P-3 6 + 29 = {FIN['P3']}", "")

# ============================================= EXTERIOR FINISHES =============================================
add("X01", EXT, "08 43 13", "Exterior tempered-glass storefront exit doors to match (E) entry doors, with panic hardware, closer, weatherstrip and threshold",
    EXT_DOORS, "EA", "drawn", f"{A401} KN5 at elevations 2 and 4 (2); {ST} p3 KN3 at elevation 7 (2)", "A-7.10 not issued")
add("X02", EXT, "08 43 13", "Fixed tempered insulated glass storefront adjacent to exit door (1704 N Vine) and (N) fixed glass (6263 Hollywood)", None, "SF",
    "not quantifiable", f"{ST} p3 KN4; {A401} KN4; {A210} KN6 (panel sizes not dimensioned)", "")
add("X03", EXT, "04 41 00", "Salvage and reset (E) granite base at new exit door bays", None, "LF",
    "not quantifiable", f"{A401} KN8 (not dimensioned)", "")
add("X04", EXT, "09 24 23", "New plaster wall to match (E) facade at exit door bays", None, "SF",
    "not quantifiable", f"{A401} KN9 (not dimensioned)", "")
add("X05", EXT, "07 42 13", "Aluminum metal panel, color to match (E) window frame", None, "SF",
    "not quantifiable", f"{A401} KN12 (not dimensioned)", "")
add("X06", EXT, "05 52 13", "1-1/2 in handrail at 34 in AFF at exterior step", None, "LF",
    "not quantifiable", f"{A401} KN7 (length not dimensioned)", "")

# ============================================= DOORS & HARDWARE =============================================
add("DR1", DOORS, "08 14 16", "New interior doors, frames and hardware (type per A-7.10 not issued)", len(DOORS_L1) + len(DOORS_M) - EXT_DOORS, "EA",
    "drawn", f"new-door tags: {A210} {', '.join(DOORS_L1)} ({len(DOORS_L1)}); {A220} {', '.join(DOORS_M)} ({len(DOORS_M)}); less {EXT_DOORS} exterior storefront doors (X01) = {len(DOORS_L1) + len(DOORS_M) - EXT_DOORS}",
    f"existing doors to remain: {', '.join(EXIST_DOORS)}; prior estimate carried 24 ({T1} L627)")
add("DR2", DOORS, "08 13 13", "1-hr fire-rated exit access door with panic hardware outside the rated stair shaft (1704 N Vine)", 1, "EA",
    "drawn", f"{ST} p3 KN5; p4 (A-6.10) KN5", "")
add("DR3", DOORS, "08 31 13", "Access doors in walls (Williams Bros.)", None, "EA",
    "not quantifiable", "mech/plumb drawings not issued", "")
add("DR4", DOORS, "08 91 26", "Door louver at mechanical room 5 door", 1, "EA",
    "drawn", f"{ADD} A-4.30 note 'LOUVER ON DOOR TO EXHAUST HOT AIR'", "size not given")

# ============================================= STAIRS & RAILING =============================================
add("S01", STAIRS, "05 51 13", "Stair 2 (exit stair, 1704 N Vine): shop-fabricated steel pan stair, concrete-filled pan treads, C12x20.7 stringers, picket rail",
    ST_RISERS, "RISER", "drawn", f"{ST} p5 (A-6.11): 11 risers @ 6 9/16 in, 10 treads @ 11 in; p9 (S-2.10) C12x20.7 stringers", "")
add("S02", STAIRS, "03 31 13", "Concrete fill in stair pans", ST_TREADS * (11 / 12) * 3.0, "SF",
    "inferred (explain)", f"10 treads x 11 in x 3'-0\" stair width ({ST} p4 A-6.10 dims) = {ST_TREADS * (11 / 12) * 3.0:.1f} SF", "")
add("S03", STAIRS, "05 12 23", "Landing beams HSS 8x4x1/4 (perimeter of 5'-0\" x 4'-0\" landing)", ST_HSS_LF, "LF",
    "inferred (explain)", f"{ST} p9 (S-2.10) HSS8x4x1/4 on all four sides; landing 5'-0\" x 4'-0\" per p4 (A-6.10) dims; LF = 2 x (5 + 4) = {ST_HSS_LF:.0f}", "")
add("S04", STAIRS, "05 12 23", "Landing posts HSS 4x4 (2 posts, floor to +6'-0\" landing)", 2 * ST_RISE_FT, "LF",
    "inferred (explain)", f"{ST} p10 (S-3.10) section 1: 2 HSS4x posts; height = landing +6'-0\" (A-6.11); LF = 2 x 6 = 12", "")
add("S05", STAIRS, "05 41 13", "Landing framing 800C162-54 joists @ 16 in o.c. with 800T162-54 track, 3/4 in Sure-Board decking", ST_LANDING_W * ST_LANDING_D, "SF",
    "inferred (explain)", f"{ST} p9 (S-2.10) joists/track; decking note 3; area = 5'-0\" x 4'-0\" = 20 SF", "")
add("S06", STAIRS, "05 05 23", "Base plates 8x8x1/4 with (4) 1/2 in x 4 in embedded anchors and post plates with (2) 1/2 in x 4 in threaded rods", 12, "EA",
    "drawn", f"{ST} p10 (S-3.10) details 3 (2 plates x 4 anchors), 4 and 5 (2 posts x 2 rods) = 8 + 4 = 12 anchors", "")
add("S07", STAIRS, "05 52 13", "1-1/2 in diameter metal handrails at 34-38 in, both sides, with 12 in top and TW+12 in bottom extensions", ST_RAIL_LF, "LF",
    "inferred (explain)", f"{ST} p5 (A-6.11) KN1; stringer length sqrt(9.167^2 + 6^2) = {ST_STRINGER_FT:.2f} ft; LF = 2 x ({ST_STRINGER_FT:.2f} + 1.0 + 1.917) = {ST_RAIL_LF:.1f}", "")
add("S08", STAIRS, "05 51 13", "Visual warning strips 2-4 in wide at top and bottom treads", 2, "EA",
    "drawn", f"{ST} p5 (A-6.11) KN2", "")
add("S09", STAIRS, "05 51 13", "Steel enclosure parallel to stringer closing gap to (E) wall", None, "LS",
    "not quantifiable", f"{ST} p4 (A-6.10) KN8", "")
add("S10", STAIRS, "05 51 13", "Stair 1 (interior, level 1 to mezzanine) and railing", None, "LS",
    "not quantifiable", f"{A210} KN5; A-6.10 / A-6.11 / A-6.12 of the main set not issued; mezzanine finish floor not dimensioned", "")
add("S11", STAIRS, "05 52 13", "Guardrail 42 in AFF at mezzanine edge", None, "LF",
    "not quantifiable", f"{A220} KN6 (A-4.15 not issued; LF not dimensioned)", "")
add("S12", STAIRS, "06 40 23", "(N) step to access adjacent tenant space from mezzanine", None, "LS",
    "not quantifiable", f"{A220} KN21", "")
add("S13", STAIRS, "05 12 23", "(N) structural posts per S sheets", 4, "EA",
    "drawn", f"{A210} KN12 x2; {A220} KN12 x2 (S sheets not issued)", "")
add("S14", STAIRS, "26 51 13", "LED insert in stair 2 step treads", None, "LS",
    "not quantifiable", f"{ADD} A-4.34 note", "")

# ============================================= OWNER-PROVIDED EQUIPMENT INSTALL =============================================
add("O01", OWNER, "12 30 00", "Reception desk (Natura Design Works Mila black tambour 36 x 190.7 x 44 in) - set in place", 1, "EA",
    "drawn", f"{ADD} A-4.20 lobby elevation note", "owner-provided")
add("O02", OWNER, "06 41 00", "2 in walnut shelves 18 in apart (lobby)", None, "LF",
    "not quantifiable", f"{ADD} A-4.20 (length not dimensioned)", "owner-provided")
add("O03", OWNER, "10 28 13", "60 x 48 in oblong mirrors (bronze glass lobby; clear glass green room)", 2, "EA",
    "drawn", f"{ADD} A-4.20 and A-4.21 notes", "owner-provided")
add("O04", OWNER, "10 28 13", "IBM Hollywood mirror Princess 60 x 45 in, green room", 1, "EA",
    "drawn", f"{ADD} A-4.21 note", "owner-provided")
add("O05", OWNER, "12 36 00", "60 x 18 in makeup counters, green room", 2, "EA",
    "drawn", f"{ADD} A-4.21 (two notes '60\"x18\" MAKEUP COUNTER')", "owner-provided")
add("O06", OWNER, "10 57 00", "Mercury Row Garfinkel wall 5-hook", 1, "EA",
    "drawn", f"{ADD} A-4.21 note", "owner-provided")
add("O07", OWNER, "08 50 00", "3'-0\" x 2'-8\" oblong window, green room", 1, "EA",
    "drawn", f"{ADD} A-4.21 note", "")
add("O08", OWNER, "11 40 00", "Foot rail from Kegworks at prep bar (by GC)", None, "LF",
    "not quantifiable", f"{ADD} A-4.33 note (length not dimensioned)", "")

# ============================================= LIGHTING =============================================
for tag in sorted(set(LIGHTS_L1) | set(LIGHTS_M)):
    n = LIGHTS_L1.get(tag, 0) + LIGHTS_M.get(tag, 0)
    add(f"L_{tag}", LIGHT, "26 51 13", f"New light fixtures type {tag} (A-3.70 schedule not issued)", n, "EA",
        "drawn", f"tags counted on {A312} ({LIGHTS_L1.get(tag, 0)}) and {A322} ({LIGHTS_M.get(tag, 0)}) text layers; matches {T1} L404-405", "fixture type unknown")
add("L_G", LIGHT, "26 51 13", "Decorative fixtures G1..G21", DECOR_L1 + DECOR_M, "EA",
    "drawn", f"G tags counted on {A312} ({DECOR_L1}) and {A322} ({DECOR_M}); matches {T1} L407-408", "")
add("L_EX", LIGHT, "26 52 13", "Exit signs and emergency lighting", None, "EA",
    "not quantifiable", f"{A312} / {A322} symbols not countable on the text layer; E sheets (plans) not issued", "")
add("L_SW", LIGHT, "26 27 26", "Switches, dimmers, dimming banks", None, "EA",
    "not quantifiable", f"{A312} / {A322} symbols (S, D, DB) not countable on the text layer", "")
add("L_RC", LIGHT, "26 27 26", "Receptacles called out on the interior elevations ('OUTLET, BLACK', 'POWER OUTLET @ 18\" AFF')", 8, "EA",
    "drawn", f"{ADD} A-4.20 (1), A-4.21 (1), A-4.23 (1), A-4.24 (2), A-4.25 (1), A-4.30 (1), A-4.31 (1)", "branch wiring, panels and E plans not issued")
add("L_LED", LIGHT, "26 51 13", "LED strip in base B-4 (mezzanine) and in light-beam millwork", FIN["B4_mezz"], "LF",
    "prior_estimate", f"base LF per F10; {ADD} A-4.30 'LED BASE P-5'", "")
add("L_BR", LIGHT, "26 05 00", "Branch circuits, panels, feeders, lighting controls", None, "LS",
    "not quantifiable", "E-2.0 / E-2.1 / E-2.2 are single line and existing panel schedules only; E plans not issued", "")

# ============================================= MECHANICAL =============================================
add("M01", MECH, "23 81 46", "Water-source heat pumps WSHP-1..6 and WSHP-8 (tonnage per M schedule not issued)", 7, "EA",
    "prior_estimate", f"{T1} (summary) equipment register WSHP-1..6, WSHP-8; {A220} KN14 'Mechanical HVAC units' x4 tags", "M sheets not in the bid documents on hand")
add("M02", MECH, "11 44 00", "Type I kitchen exhaust hood with fire suppression", 1, "EA",
    "drawn", f"{A210} KN8; {A312} KN7 (hood length: A-2.10 outline not dimensioned, scales to 13 ft; M-6 states 18'-3\" per {T1} summary)", "K and M sheets not issued")
add("M03", MECH, "23 31 13", "Grease duct in 1-hr rated shaft (room 29) with fire wrap", None, "LF",
    "not quantifiable", f"{A312} KN8; {A220} room 29 grease duct shaft 58 SF ({T2} L275); duct LF not drawn", "")
add("M04", MECH, "23 34 00", "Exhaust fan EF-2 and make-up air unit MUA", 2, "EA",
    "prior_estimate", f"{T1} (summary) equipment register EF-2, MUA riser", "capacities not available")
add("M05", MECH, "23 37 13", "Supply diffusers, return and exhaust grilles, linear diffusers", 45, "EA",
    "prior_estimate", f"{T1} L477 (23-040: 45 EA, M-1 air distribution; A-3.12 / A-3.22)", "sizes per M-1 not on hand")
add("M06", MECH, "23 31 13", "Ductwork, supply/return/exhaust, insulation", None, "LF",
    "not quantifiable", "M sheets not issued", "")
add("M07", MECH, "23 31 13", "Dishwasher exhaust duct from first floor through mezzanine", None, "LF",
    "not quantifiable", f"{A220} KN11", "")
add("M08", MECH, "23 34 23", "Restroom exhaust fans, switched with lights", 2, "EA",
    "drawn", f"{A322} KN6 x2 (men's 22, women's 23); {A512} keynote 1", "")
add("M09", MECH, "23 05 93", "Test and balance", None, "LS",
    "not quantifiable", "M sheets not issued", "")

# ============================================= PLUMBING =============================================
add("P01", PLUMB, "22 41 13", "Accessible water closets, mezzanine restrooms", 2, "EA",
    "drawn", f"{A512} KN2 (one per restroom, rooms 22 and 23); {A220} KN8", "")
add("P02", PLUMB, "22 41 16", "Lavatories K-2035-8 Pinoir vitreous china with metering faucets", 2, "EA",
    "drawn", f"{A220} 'K-2035-8 PINOIR LAVATORY' x2; {A512} KN8, KN9", "")
add("P03", PLUMB, "22 13 23", "Grease interceptor in 1-hr rated enclosure with 6 in clearance", 1, "EA",
    "drawn", f"{A210} KN14", "capacity (GPM) per P sheets not issued")
add("P04", PLUMB, "22 13 16", "Replace full 4 in sanitary main through kitchen from point of connection upstream of (E) restrooms", None, "LF",
    "not quantifiable", f"{A110} KN16 (P sheets not issued)", "")
add("P05", PLUMB, "22 13 19", "Floor sinks, floor drains and trenching for new kitchen", None, "EA",
    "not quantifiable", f"{A110} KN6 (count per P sheets not issued)", "")
add("P06", PLUMB, "22 11 00", "Water, waste, vent and gas rough-in to kitchen and bar equipment", None, "LS",
    "not quantifiable", "K and P sheets not issued", "")
add("P07", PLUMB, "22 33 00", "Water heater", None, "EA",
    "not quantifiable", "P sheets not issued", "")

# ============================================= LOW VOLTAGE =============================================
add("V01", LV, "28 46 00", "Fire alarm devices and connection to building system", None, "LS", "not quantifiable", "no FA drawings issued", "")
add("V02", LV, "27 41 00", "Sound system, AV, data and security", None, "LS", "not quantifiable", "no LV drawings issued (E-2.1 shows an existing 'Sound System' circuit only)", "")
add("V03", LV, "21 13 13", "Fire sprinkler head relocation / additions at new ceilings and walls", None, "EA",
    "not quantifiable", f"{A322} sprinkler head symbols not countable on the text layer; {A110} KN17 (E) riser to remain", "")

# ============================================= F&B EQUIPMENT =============================================
add("E01", FB, "11 40 00", "Foodservice equipment package: cooking line, refrigeration, prep, dish, walk-ins", None, "LS",
    "not quantifiable", f"{A210} KN7 (K sheets not issued)", "")
add("E02", FB, "11 40 00", "Bar equipment package (main bar and mezzanine prep bar)", None, "LS",
    "not quantifiable", f"{A220} KN7; {ADD} A-4.30 key plan items TS-23, TBB-24GAL-72, Q-270, 18-53C", "")
add("E03", FB, "11 40 00", "Stainless steel countertop on bar diewall at 42 in AFF", 21 + 9.5 / 12, "LF",
    "drawn", f"{A210} KN17 with dimension 21'-9 1/2\"", "")
add("E04", FB, "12 36 00", "Pick-up counter at 34 in AFF (A-5.20 not issued)", None, "LF",
    "not quantifiable", f"{A220} KN13", "")

# ============================================= OTHER REQUIRED SCOPE =============================================
add("G01", OTHER, "01 31 13", "Superintendent, full time", 30, "WK", "prior_estimate", f"{T1} L430 (01-020: 30 wk)", "duration assumed in prior estimate (RFI G-05)")
add("G02", OTHER, "01 31 13", "Project manager, 50%", 15, "WK", "prior_estimate", f"{T1} L429 (01-010: 15 wk)", "")
add("G03", OTHER, "01 31 13", "Project coordinator / document control, 50%", 15, "WK", "prior_estimate", f"{T1} L431 (01-030: 15 wk)", "")
add("G04", OTHER, "01 31 00", "Pre-construction: RFIs, submittals, sub buy-out, schedule", 1, "LS", "prior_estimate", f"{T1} L432", "")
add("G05", OTHER, "01 51 13", "Temporary power and lighting", 1, "LS", "prior_estimate", f"{T1} L433", "")
add("G06", OTHER, "01 52 13", "Temporary toilets, fencing, common-area and elevator protection (occupied building)", 1, "LS", "prior_estimate", f"{T1} L434", "")
add("G07", OTHER, "02 41 19", "Dumpsters / haul-off (non-demo)", 30, "WK", "prior_estimate", f"{T1} L435 (01-070: 30 wk)", "")
add("G08", OTHER, "01 74 13", "Daily clean-up during construction", 30 * 5, "DAY", "prior_estimate", f"{T1} L436 (01-080: 30 wk) x 5 days/wk = 150 days; floor area {GROSS_SF} SF ({T1} L437)", "")
add("G09", OTHER, "01 74 13", "Final / construction clean", GROSS_SF, "SF", "prior_estimate", f"{T1} L437 (7,141 SF gross)", "")
add("G10", OTHER, "01 54 00", "Small tools, consumables, PPE, SSSP, safety", 1, "LS", "prior_estimate", f"{T1} L438", "")
add("G11", OTHER, "01 71 23", "Survey / layout / as-built documentation", 1, "LS", "prior_estimate", f"{T1} L439", "")
add("G12", OTHER, "01 54 36", "Mobilization, loading-zone/street permits, hoisting and one crane day", 1, "LS", "prior_estimate", f"{T1} L440", "")
add("G13", OTHER, "01 41 26", "Permit expediting (fees excluded)", 1, "LS", "prior_estimate", f"{T1} L441", "")
add("G14", OTHER, "01 77 00", "Close-out: O&M manuals, commissioning support, warranties", 1, "LS", "prior_estimate", f"{T1} L442", "")
add("G15", OTHER, "14 12 10", "Dumbwaiter, 2 stops (A-6.30 not issued)", 1, "EA", "drawn", f"{A210} KN9; {A220} KN9", "")
add("G16", OTHER, "14 42 16", "ADA vertical wheelchair lift (A-6.20..A-6.22 not issued) - vendor quote (McKinley Equipment / Garaventa ROM on file)", 1, "EA",
    "drawn", f"{A210} KN10; {A220} KN10", "quote origin, not a book price")
add("G17", OTHER, "03 30 00", "ADA lift pit / shaft base: saw-cut, excavation, concrete, rebar", None, "LS", "not quantifiable", "A-6.21 and S sheets not issued", "")
add("G18", OTHER, "03 30 00", "Dumbwaiter pit, curb and floor openings at two levels", None, "LS", "not quantifiable", f"A-6.30 not issued; {A120} KN6", "")
add("G19", OTHER, "03 30 00", "Footing / anchor pads for new steel posts", None, "EA", "not quantifiable", "S sheets not issued", "")
add("G20", OTHER, "03 30 00", "Equipment and grease-interceptor housekeeping pads", None, "LS", "not quantifiable", "K/P sheets not issued", "")
add("G21", OTHER, "02 41 19", "Core drilling for MEP and GPR scan of slab before cutting", None, "LS", "not quantifiable", "M/P/E plans not issued", "")
add("G22", OTHER, "10 44 13", "Fire extinguishers and cabinets", 8, "EA", "prior_estimate", f"{T1} L476 (10-020: 8 EA); FE symbols not found on the A-2.10 / A-2.20 text layers (legend only)", "")
add("G23", OTHER, "10 28 13", "Grab bars 1-1/2 in dia SS, 36 in and 42 in, mezzanine restrooms", 4, "EA", "drawn", f"{A512} KN3, KN4 (one each per restroom x2)", "")
add("G24", OTHER, "10 28 13", "Surface-mounted toilet tissue dispensers", 2, "EA", "drawn", f"{A512} KN5 (x2 restrooms)", "")
add("G25", OTHER, "10 28 13", "Surface-mounted toilet seat cover dispensers", 2, "EA", "drawn", f"{A512} KN6", "")
add("G26", OTHER, "10 28 13", "Trash receptacles", 2, "EA", "drawn", f"{A512} KN10", "")
add("G27", OTHER, "10 28 13", "Power hand dryers (GC to coordinate power)", 2, "EA", "drawn", f"{A512} KN11", "")
add("G28", OTHER, "10 28 13", "Coat hooks on doors at 4'-0\" AFF (accessible)", 2, "EA", "drawn", f"{A512} KN13", "")
add("G29", OTHER, "10 28 13", "Surface-mounted mirrors, lowest reflective surface at 40 in max", 2, "EA", "drawn", f"{A512} KN14", "")
add("G30", OTHER, "10 14 23", "Toilet room identification signage (8 & 9 / A-5.10)", 2, "EA", "drawn", f"{A512} KN15", "")
add("G31", OTHER, "10 14 23", "Interior ADA room-identification and exit signage (other rooms)", None, "EA", "not quantifiable", "sign schedule not issued", "")
add("G32", OTHER, "07 84 13", "Firestopping and rated joints at penetrations of rated walls and shafts", None, "LS", "not quantifiable", "M/P/E plans not issued", "")
add("G33", OTHER, "06 10 53", "Rough carpentry, blocking and backing for millwork, accessories and equipment", None, "LS", "not quantifiable", "not quantifiable from the plans", "")
add("G34", OTHER, "02 82 00", "Hazardous materials survey (abatement excluded)", None, "LS", "not quantifiable", "prior estimate allowance only", "")
add("G35", OTHER, "09 29 10", "Finish mock-ups and sample approvals", None, "LS", "not quantifiable", f"{T1} summary (09-200)", "")
add("G36", OTHER, "10 21 13", "Toilet partitions", 0, "EA", "drawn", f"{A512} plan: single-occupancy restrooms 22 and 23, no partitions drawn", "none required")


def write(path=OUT):
    cols = ["item_id", "bid_letter_item", "division", "description", "qty", "unit", "qty_basis", "qty_source", "notes"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in ROWS:
            w.writerow(r)
    return len(ROWS)


if __name__ == "__main__":
    n = write()
    quantified = sum(1 for r in ROWS if r["qty"] != "")
    print(f"takeoff.csv written: {n} lines, {quantified} with a quantity, {n - quantified} not quantifiable -> {OUT}")
