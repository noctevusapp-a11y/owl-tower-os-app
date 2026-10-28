#!/usr/bin/env python3
"""Build takeoff2/equipment.csv for the Hollywood Comedy Club (Kelly Architects 2604) from the
health plan-check K-sheets ("BIRD CAGE DRAWINGS 062626", Fred Schmid & Associates) and the
"Thatz Hilarious Cutsheet Book 061426".

Every value below was read from the documents named in qty_source / notes:
  K2.0 equipment schedule   = <DOCS_ROOT>/kelly_tiles/K_p04.jpg (tiles t01/t02 rows 1-57,
                              t11/t12 rows 58-106; crops made by crop_k_schedule.py)
  K1.0 equipment plan       = K_p02.jpg (tiles t00/t01/t10/t11)
  K3.0 plumbing plan        = K_p05.jpg;  K4.0 electrical plan = K_p06.jpg
  K7.0 / K7.1 hood drawings = K_p09.jpg / K_p10.jpg (CaptiveAire job 8710180)
  K8.0-K8.3 walk-in         = K_p11.jpg, K_p12.jpg, K13_p01.jpg, K13_p02.jpg (Arctic Q228534)
  KD / KN notes             = K13_p04.jpg / K13_p05.jpg
  Cut sheet book pages      = <DOCS_ROOT>/kelly_txt/IFB__Health_Plan_Check__Thatz_Hilarious_
                              CutsheetBook_-_061426_part0*.txt (page numbers are book pages)
The schedule has NO furnished-by / installed-by columns; those two fields carry the REMARKS text
where the schedule gives one ("BY OWNER", "BY SODA VENDOR", "EXISTING RELOCATED", "EXISTING TO
REMAIN") and "not stated on K2.0" otherwise. Nothing is priced here.
"""
import csv
import os
import sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(OUT_DIR, "equipment.csv")

K2 = "K2.0 schedule (K_p04"
PLAN = "K1.0 plan (K_p02"
CS = "cut sheet book p."

# tile of the K2.0 row: rows 1-57 sit in the upper tiles, 58-106 in the lower tiles
def k2(item):
    n = int(str(item).split(".")[0])
    return f"{K2}_t01/t02)" if n <= 57 else f"{K2}_t11/t12)"

NS = "not stated on K2.0 (schedule has no furnished-by / installed-by columns)"
FB = "F&B equipment"
OP = "Owner-provided equipment install"

rows = []

def add(item, bid, div, desc, model, qty, unit, basis, src, furn, inst, notes):
    rows.append({
        "item_id": f"FE-{item}",
        "bid_letter_item": bid,
        "division": div,
        "description": desc,
        "spec_or_model": model,
        "qty": qty,
        "unit": unit,
        "qty_basis": basis,
        "qty_source": src,
        "furnished_by": furn,
        "installed_by": inst,
        "notes": notes,
    })

# ---------------------------------------------------------------- storage / walk-in / prep
add(1, FB, "11 41 00", "STORAGE SHELVING (existing storage area)", "METRO #MQ21XXQ (K2.0); cut sheet stamped Metro MQ2148G MetroMax Q 21x48 polymer grid shelf", 1, "LOT", "scheduled",
    f"{k2(1)}; {PLAN}_t00) item 1 in EXISTING STORAGE AREA, 6 units drawn; {CS}11-12",
    NS, NS, "No utilities. K2.0 model MQ21XXQ is a size placeholder (XX); cut sheet p11-12 shows MQ2148G (21x48) shelves, posts not called out. Plan draws 6 shelving units in the existing storage area (K_p02_t00); LOT not broken down.")
add(2, OP, "10 51 13", "EMPLOYEE LOCKERS", "no make/model on K2.0", 5, "EA", "scheduled",
    f"{k2(2)}; {PLAN}_t00) item 2 drawn as one bank north of cooler", "owner (K2.0 remark: EXISTING RELOCATED)", NS,
    "No utilities. Existing lockers relocated; no cut sheet.")
add(3, FB, "11 42 00", "SLICER STAND", "NEW AGE #98000 (cut sheet: New Age 98000 aluminum slicer stand 23-1/4 x 31-1/4 x 26 in, four 5 in swivel casters with brake)", 1, "EA", "scheduled",
    f"{k2(3)}; {PLAN}_t01) item 3; {CS}13", NS, NS, "No utilities. Cut sheet p13 lists 98000 as 23-1/4 W x 31-1/4 H x 26 D, 44 lb.")
add(4, FB, "11 42 00", "FOOD SLICER", "GLOBE #G12 (cut sheet: Globe G12 12 in manual slicer, 1/2 HP, 115-60-1, 3 A, NEMA 5-15, 25 x 25.25 x 17.25 in, 54 lb)", 1, "EA", "scheduled",
    f"{k2(4)}; {PLAN}_t01) item 4; {CS}14-15", NS, NS, "Electrical per K2.0: 120 V, 6.0 A, 1 ph, convenience outlet (C.O.). Cut sheet p15 rates it 3 A. Cord and plug NEMA 5-15.")
add(5, FB, "11 41 00", "REFRIGERATOR (reach-in)", "ATOSA #MBF8005GR (cut sheet: Atosa MBF8005GR 2-door reach-in refrigerator, 43.2 cu ft, 6 shelves, 115/60/1, 3.2 A, 1/5 HP, R290, NEMA 5-15P, approx. 51 x 31 x 81 in)", 1, "EA", "scheduled",
    f"{k2(5)}; {PLAN}_t01) item 5; {CS}16-17", NS, NS, "Electrical per K2.0: 120 V, 3.2 A, 1 ph, C.O., SELF-CONTAINED. Dimensions on cut sheet p17 (text layer partly garbled: '51 x31 x81').")
add(6, OP, "11 42 00", "FLOOR MIXER", "no make/model on K2.0", 1, "EA", "scheduled",
    f"{k2(6)}; {PLAN}_t01) item 6 in PREP", "owner (K2.0 remark: EXISTING RELOCATED)", NS,
    "Electrical per K2.0: 208 V, amps '*', 1 ph, direct connection, remark VERIFY W/OWNER. Load unreadable/not given (asterisk). No cut sheet.")
add(7, FB, "11 41 00", "WALK-IN COOLER (box)", "AIRCOOLER (K2.0); walk-in drawings K8.0-K8.3 are by Arctic Walk-in Coolers and Freezers, dwg Q228534, 6/4/2026", 1, "EA", "scheduled",
    f"{k2(7)}; {PLAN}_t00) item 7; K8.0 plan (K_p11), K8.1 elevation (K_p12), K8.2 (K13_p01), K8.3 (K13_p02)", NS, NS,
    "Electrical per K2.0: 120 V, 5.0 A, 1 ph, direct, COOLER LIGHTS. K8.3: field connection 120V/60/1, 15 A circuit required for lights. Box per K8.0/K8.1: combined cooler+freezer box 13'-3\" [159 in] long x 7'-8\" [92 in] high (84 in ID, 88 in wall panels); cooler 7'-2\" [86 in] x 9'-8\" ID, 6'-6\" ID clear, NO FLOOR PANELS, door DW2 34 x 78 in; sits on grade (K8.1 note). K8.2 panel construction: Type II Class I urethane core 4 in walls/ceiling, 26 ga Acrylume/G90 galvanized stucco embossed in/out; door hardware per K8.2 (cam-lift hinge 1255, closer 1094, handle 1229C key lock, 36 in 16 ga SS kickplates, LED vapor light w/ night light, light switch/thermometer); accessories list on K8.2 (34 ft screed/track, 2 EA 4 ft LED, 18 ft closure panel, 10 ft 1x5 trim, 1 air curtain, 10 ft 4 in flat trim, 41 ft 6 in cove base int, 18 ft 8 in cove base ext). K2.0 make 'AIRCOOLER' does not match the Arctic drawings - query. Refrigeration (items 8/9/12) by refrigeration contractor per KN FIXTURE REFRIGERATION NOTES 7-8 (K13_p05); condensing units are OUTDOOR per K8.2 - roof platform by GC (KN refrig. note 12).")
add(8, FB, "11 41 00", "EVAPORATOR COIL (cooler)", "AIRCOOLER (K2.0); K8.2 refrigeration spec COOLER #1: Russell coil RAL6A081ADARSF, 115/1/60, MCA 20, 1 fan, 15-1/2 x 27-1/8 x 18-1/8 in, 47 lb", 1, "EA", "scheduled",
    f"{k2(8)}; {PLAN}_t00) item 8; K8.2 refrigeration specifications table (K13_p01)", NS, NS,
    "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S. Electrical per K2.0: 120 V, 3.0 A, 1 ph, direct. KN plumbing note 12: 1 in insulated copper condensate line from coil to floor sink; heater tape by refrigeration contractor (KN refrig. note 13). Requires refrigeration subcontract (lines, valves per KN refrig. note 7).")
add("9.1", FB, "11 41 00", "REFRIGERATION SYSTEM - cooler condensing unit", "K2.0 item 9 'AIRCOOLER' 1 EA; K8.2 COOLER #1 R-454A air-cooled 35 F OUTDOOR: Russell C/U RFON100M4ADANT, 1 HP, 208-230/1/60, MCA 15, 27-7/8 x 28-1/4 x 18-3/4 in, 195 lb, 9,154 BTUH; with A2L leak detector, CSOV check valve, EcoNet control, fixed high/adj. low pressure control, liquid line w/ sealed filter + sight glass, SSOV isolation valve, standard receiver", 1, "EA", "scheduled",
    f"{k2(9)} (item 9 qty 1); K8.2 refrigeration specifications table (K13_p01) lists two condensing units", NS, NS,
    "K2.0 item 9 is one line 'REFRIGERATION SYSTEM 1 AIRCOOLER', 208 V, amps '*', 1 ph, direct, SEE REFRIGERATION DRAWING; K8.2 splits it into a cooler C/U and a freezer C/U, so two sub-rows. Outdoor units: GC provides 6 in high roof platform with galvanized sheet metal top (KN refrig. note 12, exhaust/MUA note 3); EC provides power at compressor rack with disconnects (KN refrig. note 6); refrigeration contractor supplies/installs compressors, lines, fittings, valves and welded angle iron rack (KN refrig. notes 7-8). Refrigeration subcontract required.")
add("9.2", FB, "11 41 00", "REFRIGERATION SYSTEM - freezer condensing unit", "K8.2 FREEZER #1 R-454A air-cooled -10 F OUTDOOR: Russell C/U RFON160L4ADA, 1-1/2 HP, 208-230/1/60, MCA 15, 26-1/4 x 28-1/4 x 18-3/4 in, 195 lb, 4,941 BTUH; with A2L leak detector, CSOV check valve, EcoNet control, liquid line w/ sealed filter + sight glass, SSOV isolation valve, standard receiver, 1 year labor warranty", 1, "EA", "scheduled",
    "K8.2 refrigeration specifications table (K13_p01); K2.0 item 9 qty 1 covers both units", NS, NS,
    "See FE-9.1. Freezer blower coil defrost: EC provides 4- or 5-wire to 7-wire service from freezer compressor and time clock (KN refrig. note 10). Refrigeration subcontract required.")
add(10, FB, "11 41 00", "COOLER SHELVING", "METRO #MQ18XXG (K2.0; XX = length placeholder, no cut sheet in book)", 1, "LOT", "scheduled",
    f"{k2(10)}; {PLAN}_t00) item 10, 5 shelving units drawn in COOLER", NS, NS, "No utilities. No cut sheet for MQ18XXG; lengths not given. Plan (K_p02_t00) draws 5 units in the cooler.")
add(11, FB, "11 41 00", "WALK-IN FREEZER (box)", "AIRCOOLER (K2.0); Arctic dwg Q228534 K8.0-K8.3", 1, "EA", "scheduled",
    f"{k2(11)}; {PLAN}_t00) item 11; K8.0 (K_p11), K8.1 (K_p12), K8.2 (K13_p01)", NS, NS,
    "Electrical per K2.0: 120 V, 3.0 A, 1 ph, direct, FREEZER LIGHTS. Freezer per K8.0: 4'-5\" [53 in] x 6'-11\" [83 in] (6'-3\" ID), WITH FLOOR PANELS (4 in heavy-duty floor w/ 3/4 in plywood subfloor, .100 smooth aluminum NSF interior per K8.2), interior ramp, door DW2 34 x 78 in with heated pressure relief port 1825 (115 V), door frame heater and thermostat PEPI-B (DW1 items per K8.2). Same box as FE-7; see FE-7 for panel/accessory data. Freezer floor: K0.0 detail D 'WALK-IN BOX FLOOR'; KN curb note 6: wall base at walk-in cooler and freezer 9 in high. Sprinkler heads in freezer protected against freezing by GC (KN GC note 18).")
add(12, FB, "11 41 00", "EVAPORATOR COIL (freezer)", "AIRCOOLER (K2.0); K8.2 FREEZER #1: Russell coil ASLA RAS6E052DDARSF, 208-230/1/60, MCA 15, 2 fans, 39 x 54-5/16 x 10 in, 95 lb", 1, "EA", "scheduled",
    f"{k2(12)}; {PLAN}_t00) item 12; K8.2 (K13_p01)", NS, NS,
    "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S. Electrical per K2.0: 208 V, amps '*', 1 ph, direct, SEE REFRIGERATION DRAWINGS (K8.2 gives MCA 15 at 208-230/1/60). Heater tape on freezer drain by refrigeration contractor, hook-up by EC (KN refrig. note 13; KN elec. note 32). Refrigeration subcontract required.")
add(13, FB, "11 41 00", "FREEZER SHELVING", "METRO #MQ18XXG (K2.0; no cut sheet)", 3, "EA", "scheduled",
    f"{k2(13)}; {PLAN}_t00) item 13, 3 units drawn in FZR.", NS, NS, "No utilities. Lengths not given (XX placeholder).")
add(14, "existing to remain (no bid scope on K2.0)", "22 34 00", "HOT WATER HEATER (existing on roof)", "A.O. SMITH #BTH250 (100 GAL... clipped on K2.0); cut sheet: A.O. Smith Cyclone Mxi BTH-250, 100 gal, 250,000 BTU/h input, 3/4 in NPT gas, 1-1/2 in NPT water, 3/4 in NPT drain, 120 V-60 Hz 5.0 A", 1, "EA", "scheduled",
    f"{k2(14)}; not on K1.0 plan (on roof); {CS}5-10 and 18-23 (duplicated); P-6 water heater calc (K13_p03)", "existing to remain (K2.0 remark: EXISTING TO REMAIN; plumbing remark EXISTING ON ROOF)", "existing",
    "Plumbing per K2.0: CW 1-1/2 in, gas conn 3/4 in, 250 MBTU, I.W. 3/4 in, EXISTING ON ROOF. P-6 (K13_p03) water heater calc: 320 gal/hr required by health, actual 582 gal/hr at 50 F rise, 250,000 BTUH actual input. No new equipment; listed for the utility totals only.")
add(16, FB, "11 42 00", "OVERSHELVES (prep table)", "CUSTOM ST/ST", 1, "EA", "scheduled",
    f"{k2(16)}; {PLAN}_t01) item 16 over prep table 17", NS, NS, "No utilities. Custom-fabricated stainless steel (no cut sheet; fabricator shop drawings per KD). Wall backing/cantilever supports by GC (KN GC notes 4-5; KD wall backing details).")
add(17, OP, "11 42 00", "PREP TABLE W/SINKS", "CUSTOM ST/ST (existing relocated)", 1, "EA", "scheduled",
    f"{k2(17)}; {PLAN}_t01) item 17 in PREP; K3.0 (K_p05) stub-up at 17", "owner (K2.0 remark: EXISTING RELOCATED)", NS,
    "Plumbing per K2.0: HW 1/2 in, CW 1/2 in, I.W. 1-1/2 in, EXTEND I.W. TO F.S. (K3.0 shows STUB UP at item 17). Electrical per K2.0: 120 V, 11.8 A, 1 ph, C.O., DROP CORD ASSEMBLY. Existing custom stainless table relocated; faucet not separately scheduled.")
add(18, FB, "11 42 00", "FOOD PROCESSOR", "ROBOT COUPE #CL50E (cut sheet: Robot Coupe CL50E vegetable prep machine, 1.5 HP, 120V/60/1, 12 A, NEMA 5-15P, 23-7/16 x 13-1/2 x 14-3/4 in, 41 lb)", 1, "EA", "scheduled",
    f"{k2(18)}; {PLAN}_t01) item 18; {CS}24-26", NS, NS, "Electrical per K2.0: 120 V, 12.0 A, 1 ph, C.O., DROP CORD ASSEMBLY. Countertop unit on prep table 17.")
add(19, FB, "11 48 00", "MOP SINK", "ADVANCE #9-OP-20 (cut sheet: Advance Tabco 9-OP-20 floor mop sink, 16 ga 304 SS, bowl 16 x 20 x 6 in, OA 21 x 25 x 10 in, K-16 free-flow drain fits 2 in waste, 33 lb)", 1, "EA", "scheduled",
    f"{k2(19)}; {PLAN}_t00) item 19; K3.0 (K_p05) STUB UP at 19; {CS}27-28", NS, NS,
    "Plumbing per K2.0: direct waste 2 in, TRAP BELOW FLOOR. K0.0 note J: GC to provide single compartment janitorial sink with hot and cold water (item 19). GC furnish/install per K0.0 wording - confirm against KEC package.")
add(20, FB, "11 48 00", "SERVICE FAUCET (mop sink)", "T & S #B-0665-BSTR (cut sheet: T&S B-0665-BSTR 8 in wall-mount service sink faucet, Eterna cartridges w/ spring checks, lever handles, rough chrome, 1/2 in NPT vacuum breaker, 1/2 in NPT female inlets, built-in service stops)", 1, "EA", "scheduled",
    f"{k2(20)}; {PLAN}_t00) item 20; K3.0 (K_p05) +36 in at 20; {CS}29-30", NS, NS, "Plumbing per K2.0: HW 1/2 in, CW 1/2 in. K3.0 rough-in height +36 in.")
add(21, FB, "11 48 00", "MOP HANGER/SHELF", "ADVANCE #K245 (cut sheet: Advance Tabco K-245 8 x 24 in 18 ga 430 SS utility shelf with mop hangers and rag hooks)", 1, "EA", "scheduled",
    f"{k2(21)}; {PLAN}_t00) item 21; {CS}31", NS, NS, "No utilities. Wall backing by GC (KD wall backing details, KN GC note 4).")
add(22, FB, "11 48 00", "GREASE INTERCEPTOR (automatic, point source)", "BIG DIPPER #W-350-IS (cut sheet: Thermaco Big Dipper W-350-IS automatic grease interceptor, 304 SS bright finish, 35 GPM, 70+ lb grease, 2.5 gal solids strainer, 115 VAC 520 W 4.5 A, 3 in pipe inlet/outlet, footprint 34.4 x 17.5 in, 23.4 in high)", 1, "EA", "scheduled",
    f"{k2(22)}; {PLAN}_t00) item 22 at freezer/scullery wall; K3.0 (K_p05) 'VFY. W/ PLUMBER' at 22/88; {CS}32-33", NS, NS,
    "Plumbing per K2.0: direct waste 4 in, TRAP BELOW FLOOR; receives item 88 three-compartment sink (K2.0 item 88 remark DIRECT WASTE TO ITEM #22). Electrical per K2.0: 120 V, 4.0 A, 1 ph, C.O. K3.0 flags 'VFY. W/ PLUMBER' at the interceptor. Cut sheet p32 lists 3 in inlet/outlet vs 4 in on K2.0 - query.")
# ---------------------------------------------------------------- cooking line / kitchen
add(25, FB, "11 41 00", "REFRIGERATED PIZZA TAB[LE] (description clipped on K2.0)", "ATOSA #MPF8202GR (cut sheet: Atosa MPF8202GR 2-door refrigerated pizza prep table, 67 x 33.1 x 44 in, 18.5 cu ft, 4 shelves, 115/60/1, 2.8 A, 1/5 HP, R290, NEMA 5-15P, 335 lb)", 1, "EA", "scheduled",
    f"{k2(25)}; {PLAN}_t01) item 25 in COOKING; {CS}34-35", NS, NS, "Electrical per K2.0: 120 V, 2.8 A, 1 ph, C.O., SELF-CONTAINED. K4.0 (K_p06) outlet +12 in.")
add(26, FB, "11 41 00", "WALL SHELVES (over item 25)", "GSW #WS-W1660 (cut sheet: GSW WS-W1660 16 x 60 in 18 ga SS wall shelf, 2 in rear upturn, 3 brackets, 395 lb capacity)", 2, "EA", "scheduled",
    f"{k2(26)}; {PLAN}_t01) one bubble 26 over item 25 (double tier not distinguishable); {CS}36-37", NS, NS, "No utilities. Wall backing by GC (KD wall backing detail 1/2 'double shelf / single shelf').")
add(27, FB, "11 44 00", "CONVEYOR OVEN (VENTLE[SS]) (description clipped on K2.0)", "OVENTION #S1200, DOUBLE STACK (cut sheet: Ovention Shuttle S1200 ventless precision impingement oven, 50.03 W x 31.11 D x 20.24 H in w/ 4 in legs, 180 lb each; US: 208 VAC 60 Hz 1 ph 24 A NEMA 6-30P, max input 6.3 kW, or 208-240 VAC 26/29 A; internal catalytic filtration)", 1, "EA", "scheduled",
    f"{k2(27)}; {PLAN}_t01) item 27 in COOKING; {CS}38-39", NS, NS,
    "Electrical per K2.0: 208 V, 26.0 A, 1 ph, C.O., EACH DECK REQUIRES SEPARATE CIRCUIT (remark DOUBLE STACK = 2 decks, so 2 circuits; K2.0 lists the amps once). K4.0 (K_p06) shows outlets at +30 in and +54 in at item 27. Ventless per model name - no hood over it on K1.0.")
add(28, FB, "11 44 00", "HEATED CABINET", "CRESCOR #H-135-WSUA-11 (cut sheet: Cres Cor H-135-WSUA-11 AquaTemp insulated hot cabinet, 2000 W, 120 V 60 Hz 1 ph 16 A on 20 A service, 6 ft 14/3 cord, 25-3/4 W x 33-1/2 D x 69-3/4 H in, 5 in casters, 225 lb)", 3, "EA", "scheduled",
    f"{k2(28)}; {PLAN}_t01) three bubbles 28 (one at cooking line, two in kitchen); {CS}40-41", NS, NS, "Electrical per K2.0 (per unit): 120 V, 16.0 A, 1 ph, C.O. Three units = three 20 A circuits. K4.0 stub-down/+48 in outlets at 28.")
add(29, FB, "11 42 00", "WORKTABLE", "GSW #WT-PB3060 (cut sheet: GSW WT-PB3060 30 x 60 x 35 in work table, 4 in rear upturn, 18 ga 430 SS undershelf, 201 SS legs, 88 lb)", 2, "EA", "scheduled",
    f"{k2(29)}; {PLAN}_t01) two bubbles 29 in PREP; {CS}42-43", NS, NS, "Electrical per K2.0: 120 V, 11.8 A, 1 ph, C.O., FIXTURE MOUNTED DCO (duplex convenience outlet mounted on the table). Knock-down table.")
add(30, FB, "11 41 00", "REFRIGERATED STAND (chef base)", "ATOSA #MGF8450GR (cut sheet: Atosa MGF8450GR 2-drawer refrigerated chef base, 7.7 cu ft, 48.4 x 33 x 26.6 in, 115/60/1, 2.3 A, 1/7 HP, R290, NEMA 5-15P, 220 lb)", 1, "EA", "scheduled",
    f"{k2(30)}; {PLAN}_t01) item 30 under item 27; {CS}44-45", NS, NS, "Electrical per K2.0: 120 V, 2.3 A, 1 ph, C.O., SELF-CONTAINED.")
add(31, FB, "11 48 00", "HAND SINK", "GSW #HS-1615S (cut sheet: GSW HS-1615S wall-mount hand sink 15-1/4 x 15-3/4 x 13-3/8 in, bowl 9-3/4 x 12-1/2 x 5-5/8 in, 7-3/4 in backsplash, 4 in faucet centers, 1-1/2 in NPS drain)", 2, "EA", "scheduled",
    f"{k2(31)}; {PLAN}_t01) two bubbles 31 (prep area, cooking line by item 55); K3.0 (K_p05) +14/+16 in at both; {CS}46-47", NS, NS,
    "Plumbing per K2.0 (each): HW 1/2 in, CW 1/2 in, direct waste 1-1/2 in, DIRECT WASTE. Faucet not separately scheduled (K0.0 note L: hand sink with hot/cold water under pressure, soap and towel dispensers, items 31/71). Wall backing by GC (KD detail 6 'hand sink').")
add(32, FB, "11 41 00", "REFRIGERATED TABLE (sandwich/salad)", "ATOSA #MSF8302GR (cut sheet: Atosa MSF8302GR 2-door refrigerated sandwich/salad table w/ 9-1/4 in cutting board, 6 in deep pans, 13.4 cu ft, 115/60/1, R290, NEMA 5-15P; dimensions in text layer garbled - approx 48 x 30 x 41 in per model row)", 1, "EA", "scheduled",
    f"{k2(32)}; {PLAN}_t01) item 32 in KITCHEN; {CS}48-49", NS, NS, "Electrical per K2.0: 120 V, 2.3 A, 1 ph, C.O., SELF-CONTAINED. K4.0 +12 in outlet.")
add(33, FB, "11 42 00", "OVERSHELF (over item 32/34)", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(33)}; {PLAN}_t01) item 33", NS, NS, "No utilities. Custom-fabricated stainless steel; no cut sheet.")
add(34, FB, "11 42 00", "WORKCOUNTER", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(34)}; {PLAN}_t01) item 34 next to 32", NS, NS, "No utilities. Custom-fabricated stainless steel; no cut sheet; dimensions not given on K-sheets.")
add(35, FB, "11 44 00", "HEAT LAMPS (strip heaters)", "HATCO #GRAH-48D3 (cut sheet: Hatco Glo-Ray GRAH-48D high-watt double aluminum strip heater, 48 W x 15 D x 2.5 H in with 3 in spacer, 200 V 2034 W 11.0 A / 220 V 2200 W 10.0 A; 36 in flexible conduit with leads)", 3, "EA", "scheduled",
    f"{k2(35)}; {PLAN}_t01) three bubbles 35 (pass shelf/work counters); K4.0 +50 in at 35; {CS}50-53", NS, NS,
    "Electrical per K2.0 (each): 208 V, 10.6 A, 1 ph, direct connection. Mounting on custom overshelves 33/39 - remote switch box (RMB) option not called out.")
add(36, FB, "11 41 00", "SHELVING", "METRO #14XXFG (K2.0; cut sheet stamped Metro 1436FG Super Erecta 14 x 36 in galvanized flat shelf)", 2, "EA", "scheduled",
    f"{k2(36)}; {PLAN}_t01) one bubble 36 in KITCHEN; {CS}54-55", NS, NS, "No utilities. XX placeholder on K2.0; cut sheet p55 row 1436FG; posts not called out.")
add(37, FB, "11 41 00", "REFRIGERATED TABLE (sandwich/salad, 3 door)", "ATOSA #MSF8304GR (cut sheet p49 row within item 32 sheet: MSF8304GR 3-door, 21.1 cu ft, 3 shelves, 115/60/1, R290)", 1, "EA", "scheduled",
    f"{k2(37)}; {PLAN}_t01) item 37 in KITCHEN; {CS}48-49 (row MSF8304GR)", NS, NS, "Electrical per K2.0: 120 V, 2.8 A, 1 ph, C.O., SELF-CONTAINED. No dedicated cut sheet; model appears in the MSF830x table.")
add(38, FB, "11 42 00", "WORKCOUNTER", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(38)}; {PLAN}_t01) item 38; K4.0 +48 in at 38", NS, NS,
    "Electrical per K2.0: 120 V, 11.8 A, 1 ph, C.O., WALL MOUNTED DCO. Custom-fabricated stainless steel; no cut sheet; dimensions not given.")
add(39, FB, "11 42 00", "OVERSHELVES (over item 38)", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(39)}; {PLAN}_t01) item 39", NS, NS, "No utilities. Custom-fabricated stainless steel; carries heat lamps 35.")
add(40, FB, "11 44 00", "HOT FOOD WELL (countertop warmer)", "WELLS #TMPT (cut sheet: Wells TMPT countertop food warmer, deep-drawn SS pan, 4 in legs; 120 V cord-connected - wattage row not legible in text layer)", 1, "EA", "scheduled",
    f"{k2(40)}; {PLAN}_t01) item 40 on counter 38; K4.0 +48 in at 40; {CS}56-57", NS, NS, "Electrical per K2.0: 120 V, 15.0 A, 1 ph, C.O.")
add(41, FB, "11 42 00", "WORKTABLE", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(41)}; {PLAN}_t01) item 41 at south end of cooking line", NS, NS, "No utilities. Custom-fabricated stainless steel; dimensions not given.")
add(45, FB, "11 44 00", "WATER FILTER (for combi oven)", "RATIONAL #R295-CL (K2.0); cut sheet: RATIONAL R295-CLX, art. 1900.1158US, 3/4 in MNPT in/out, 10 gpm, 108,000 gal, 24-5/8 in H", 1, "EA", "scheduled",
    f"{k2(45)}; {PLAN}_t01) item 45 on wall north of combi 46; {CS}58-59", NS, NS, "Plumbing per K2.0: CW 1/2 in. Model suffix differs (R295-CL vs R295-CLX) - query.")
add(46, OP, "11 44 00", "COMBI-OVEN (existing relocated)", "RATIONAL #I COMBI CLASSIC (cell highlighted yellow on K2.0; model size not given)", 1, "EA", "scheduled",
    f"{k2(46)}; {PLAN}_t01) item 46 at north end of main cooking line; K3.0 (K_p05) +68 in at 46 (two taps); K4.0 +48 in at 46", "owner (K2.0 remark: EXISTING RELOCATED)", NS,
    "Electrical per K2.0: 208 V, 10.8 KW, 3 ph, direct, EACH DECK (3-phase direct connection). Plumbing columns blank on K2.0 but K3.0 (K_p05) shows two rough-ins tagged 46 at +68 in - query water/drain for the combi. No cut sheet. Under Type I hood 1 (left).")
add(47, FB, "11 44 00", "6 O.B. RANGE W/CONV. OV[EN] (description clipped on K2.0)", "IMPERIAL #IR-6-C (cut sheet: Imperial Pro Series IR-6-C 36 in 6 open-burner gas range with 26-1/2 in convection oven, 1/2 hp blower, 36 x 31-1/2 x 56-1/2 in, 3/4 in gas manifold, 5.0 in WC NG, quick disconnect and flex hose option, 6 in casters option)", 1, "EA", "scheduled",
    f"{k2(47)}; {PLAN}_t01) item 47; K3.0 gas +27 in at 47; {CS}60-61", NS, NS,
    "Plumbing per K2.0: gas conn 3/4 in, 198 MBTU, W/QUICK DISCONNECT. Electrical per K2.0: 120 V, 5.0 A, 1 ph, C.O. (oven blower). Under Type I hood 1.")
add(48, FB, "11 44 00", "CHEESEMELTER", "ATOSA #ATCM-36 (cut sheet: Atosa ATCM-36 36 in infrared cheesemelter, two 21,500 BTU ceramic burners = 43,000 BTU, 36 x 18 x 17.33 in, wall or range mount, 95 lb)", 1, "EA", "scheduled",
    f"{k2(48)}; {PLAN}_t01) item 48 over range 47; {CS}62-63", NS, NS, "Plumbing per K2.0: gas conn 3/4 in, 43 MBTU. Range-mounted over 47 (Imperial lists reinforcement channels for cheese melter mounting). Under Type I hood 1.")
add(49, FB, "11 44 00", "CHARBROILER", "ATOSA #ATRC-36 (cut sheet: Atosa ATRC-36 36 in countertop radiant charbroiler, 35,000 BTU SS burners, 3/4 in NPT rear gas connection and regulator, 158.7 lb)", 1, "EA", "scheduled",
    f"{k2(49)}; {PLAN}_t01) item 49 on stand 50; K3.0 gas +27 in at 49; {CS}64-65", NS, NS, "Plumbing per K2.0: gas conn 3/4 in, 105 MBTU, W/QUICK DISCONNECT. Under Type I hood 1.")
add(50, FB, "11 41 00", "REFRIGERATED STAND (chef base, 72 in)", "ATOSA #MGF8453GR (cut sheet p45 row within item 30 sheet: MGF8453GR 4-drawer chef base, 12.1 cu ft, 72-1/2 x 33 x 26.6 in, 115/60/1, 2.3 A, 1/7 HP, R290, 300 lb)", 1, "EA", "scheduled",
    f"{k2(50)}; {PLAN}_t01) item 50 under 49/51; K4.0 +12 in at 50; {CS}44-45 (row MGF8453GR)", NS, NS, "Electrical per K2.0: 120 V, 2.3 A, 1 ph, C.O., SELF-CONTAINED.")
add(51, FB, "11 44 00", "GRIDDLE RANGE (countertop griddle)", "ATOSA #ATTG-36 (cut sheet: Atosa ATTG-36 36 in countertop griddle, 1 in polished steel plate, 25,000 BTU per 12 in section (3 sections), 36 x 28.6 x 15.2 in, 3/4 in NPT rear gas, 229 lb)", 1, "EA", "scheduled",
    f"{k2(51)}; {PLAN}_t01) item 51 on stand 50; K3.0 gas +27 in at 51; {CS}66-67", NS, NS, "Plumbing per K2.0: gas conn 3/4 in, 75 MBTU, W/QUICK DISCONNECT. Under Type I hood 1.")
add(52, FB, "11 44 00", "FRYERS", "ATOSA #ATFS-40 (K2.0); cut sheet: Atosa ATFS-40ES-NG 40 lb gas fryer, SS tank, millivolt T-stat, 3/4 in NPT rear gas and regulator, 4 casters, 15-1/2 x 30-1/8 x 44-1/4 in, 131 lb", 2, "EA", "scheduled",
    f"{k2(52)}; {PLAN}_t01) one bubble 52, two fryers drawn; K3.0 gas +12 in at 52 (two taps); {CS}68-69", NS, NS,
    "Plumbing per K2.0 (per line): gas conn 3/4 in, 102 MBTU, W/QUICK DISCONNECT; K3.0 shows two gas taps at +12 in, so 2 x 102 MBTU. Under Type I hood 1 (right).")
add(53, FB, "11 41 00", "WORKTOP FREEZER", "TRUE #TWT-27F-HC (cut sheet: True TWT-27F-HC solid door worktop freezer, 27-5/8 L x 30-1/8 D x 33-3/8 H in, 1/4 HP, 115/60/1, 2.3 A, NEMA 5-15P, 7 ft cord, R290, 210 lb)", 1, "EA", "scheduled",
    f"{k2(53)}; {PLAN}_t01) item 53 at south end of cooking line; K4.0 +12 in at 53; {CS}70-71", NS, NS, "Electrical per K2.0: 120 V, 5.0 A, 1 ph, C.O., SELF-CONTAINED (cut sheet rates 2.3 A).")
add(54, FB, "11 44 00", "FRY DUMP (crisp 'n hold)", "CARTER-HOFFMANN #CNH18 (cut sheet: Carter-Hoffmann CNH18 crisp n hold fry dump, 120 V 1820 W 15.1 A 60 Hz 1 ph, NEMA 5-20P, 6 ft cord, 17-3/4 H x 29 W x 17-9/16 D in, 3 sections, 67 lb)", 1, "EA", "scheduled",
    f"{k2(54)}; {PLAN}_t01) item 54 on worktop freezer 53; K4.0 +48 in at 54; {CS}72-73", NS, NS, "Electrical per K2.0: 120 V, 15.1 A, 1 ph, C.O. (20 A circuit, NEMA 5-20P).")
# ---------------------------------------------------------------- hoods / fire / fans
add(55, FB, "21 23 00", "FIRE SUPPRESSION SYSTE[M] (description clipped on K2.0)", "CAPTIVE AIRE (K7.0: fire system piping YES on Hood 1-Left and Hood 1-Right; wall-mount utility cabinet 12 x 60 x 30 in, fire system type TANK FS, size 4.0/4.0/4.0 (gal), electrical model SC-311110MA, switches 1 light + 1 fan, 440 lb; K7.1 'WALL MOUNT UC LEFT JOB# 8710180' 60 in wide)", 1, "EA", "scheduled",
    f"{k2(55)}; {PLAN}_t01) item 55 at cooking-line wall north of 46; K7.0 hood information / wall-mount utility cabinet tables (K_p09); K7.1 (K_p10)", NS, NS,
    "Electrical per K2.0: 120 V, 20.0 A, 1 ph, direct, UNINTERRUPTED SERVICE. K4.0 note at 55: 'TO EXHAUST AND MAKE-UP AIR FAN SYSTEMS, FANS TO BE INTERLOCKED'. KD 'WIRING SCHEMATIC FIRE SYS.' and KN elec. note 31: electrical contactors for cooking equipment shut-down by EC; KD remote fire pull detail (4/0 box, 1/2 in EMT, 48 in AFF). K7.1 'cabinet to be hung by others'. K7.0 note: operation verified by factory service technician, fire system hooked up and armed. Gas shut-off valve interconnection by plumber (gas valve not scheduled). Fire suppression trade (wet chemical) + EC interconnect.")
add("56.1", FB, "23 38 13", "EXHAUST HOOD - Type I, Hood 1 - Left", "CAPTIVE AIRE (K7.0 hood 1: model 5412 SND-2, 10'-1\" long, 600 deg max, Type I, heavy duty, 275 CFM/ft, 2,773 CFM exhaust, riser 14 x 16 x 4 in, 430 SS where exposed, 7 Captrate Solo filters 20 x 16 in (85% at 7 microns), 3 recessed round LED lights, no wire guard, hanging weight 385 lb; options: left end standoff (fin/slp) 1 in wide 54 in long insulated, balance dampers, left wall as end panel)", 1, "EA", "scheduled (K2.0 item 56 qty 1; K7.0/K7.1 show Hood 1 as two sections, split here)",
    f"{k2(56)}; {PLAN}_t01) item 56/57 bubble at main cooking line; K7.0 hood information tables (K_p09, crop K70_hood_info); K7.1 plan view hood #1 (K_p10)", NS, NS,
    "Electrical per K2.0 item 56: 120 V, 6.0 A, 1 ph, direct, HOOD LIGHTS, WIRE THRU SWITCH. K7.1: hood #1 10'-1\" nom (10'-2\" overall), 54 in deep, 24 in high (12 in nom lower front), 80 in to bottom of hood (27 in min to 48 in max equipment), overall Hood 1 = 18'-3\" long (left 10'-1\" + right 8'-1\"). Clearance to combustibles (K7.0): top 18 in, front 0 in, back 18 in, left 0 in, right 18 in. KD hood rod hanger detail: structural member by GC 2'-0\" above hood, 1/2 in all-thread by hood installer, FSEC to provide one hanger rod per 4 ft of hood. K7.0 note: walls within 18 in of Type I hood must be metal stud and sheetrock. Needs mechanical sub for ducts/fan/MUA (KN exhaust notes 1-6: GC shafts and roof openings, EC power/switches on roof, plumber gas/water on roof). 'Equipment by others' per K7.1.")
add("56.2", FB, "23 38 13", "EXHAUST HOOD - Type I, Hood 1 - Right", "CAPTIVE AIRE (K7.0 hood 2: model 5412 SND-2, 8'-1\" long, 600 deg max, Type I, heavy duty, 225 CFM/ft, 1,819 CFM exhaust, riser 12 x 12 x 4 in, 430 SS where exposed, 6 Captrate Solo filters 20 x 16 in, 3 recessed round LED lights, hanging weight 377 lb; options: balance dampers, riser sensor install 6 in plenum, right vertical end panel 27 in top width / 21 in bottom width / 68 in high insulated 430 SS)", 1, "EA", "scheduled (K2.0 item 56 qty 1; split per K7.0/K7.1)",
    "K7.0 hood information tables (K_p09); K7.1 plan/section hood #2 (K_p10)", NS, NS,
    "Same K2.0 line as FE-56.1 (hood lights load counted once on item 56). K7.1 section: right vertical end panel with adjustable legs and gas chase cut-out (gas and power lines). Total Type I exhaust: 2,773 + 1,819 = 4,592 CFM (K7.0).")
add(57, FB, "23 38 13", "EXHAUST FAN SYSTEM (exhaust and make-up air fans)", "CAPTIVE AIRE (K2.0: 1 LOT, SEE HOOD DRAWINGS) - fan/MUA models are NOT on K7.0/K7.1 (hood sheets only); not in the cut sheet book", 1, "LOT", "scheduled",
    f"{k2(57)}; {PLAN}_t01) bubble 57 56 at cooking line; K7.0/K7.1 (K_p09/K_p10) carry no fan schedule", NS, NS,
    "Electrical per K2.0: 208 V, amps '*', 3 ph, direct, SEE HOOD DRAWINGS (no fan data on K7.0/K7.1 - unreadable/absent). K4.0 note: exhaust and MUA fans to be interlocked (with item 55). KN exhaust/MUA notes: GC provides shafts/openings and roof curbs/platforms (notes 1-3), EC provides roof power, disconnects and switch boxes (notes 4-5), plumber provides roof gas/water/drain (note 6). Mechanical (sheet metal) subcontract for duct and fans; fan selection to be taken from the MEP set (M-sheets) - outside the K package.")
add(58, FB, "23 38 13", "WALL FLASHING (behind cooking line)", "CUSTOM ST/ST", 1, "LOT", "scheduled",
    f"{k2(58)}; {PLAN}_t01) bubble 58 at east wall of main cooking line; K0.0 room finish schedule 'STAINLESS STEEL ... BEHIND COOKING LINE WALL'", NS, NS,
    "No utilities. Custom-fabricated stainless steel wall flashing; extent not dimensioned on K-sheets (plan length of main cooking line wall only). K0.0 finish schedule marks stainless steel walls behind the cooking line; K5.0 shows non-combustible wall legend at the line.")
# ---------------------------------------------------------------- service bar #1
add(61, FB, "11 46 00", "SERVICE BAR TOP", "CUSTOM ST/ST", 1, "LOT", "scheduled",
    f"{k2(61)}; {PLAN}_t01) bubble 61 at east end of SERVICE BAR #1", NS, NS,
    "No utilities. Custom-fabricated stainless steel bar top over the Perlick underbar run (items 62-71); length not dimensioned on K1.0. A-5.20 shows a separate stainless pick-up counter (WC-2, 34 in AFF) at the mezzanine pick-up bar - architectural keynote 1, not this item.")
add(62, FB, "11 46 00", "CORNER DRAINBOARD", "PERLICK #TS90LIC (cut sheet: Perlick TS90LIC Top Shelf 90 deg left inside corner drainboard, 24 x 18-9/16 in, all SS, 6 in backsplash, 1-1/2 in NPS male drain, 50 lb)", 1, "EA", "scheduled",
    f"{k2(62)}; {PLAN}_t01) item 62 at bar corner; {CS}74-76", NS, NS, "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S.")
add(63, FB, "11 46 00", "DUMP SINK", "PERLICK #TSF18DS (K2.0); cut sheet: Perlick TSF18DS-TR Top Shelf 18 x 24 in storage cabinet with sink and 5 in trash chute, 14 x 10 x 9 in bowl, 1-1/2 in NPS male drain, 50 lb; plus 934GN-LF gooseneck faucet (hot/cold, 9/16-24 thread, 2.2 GPM), 7055-48 wet waste box and 7054R accessory pages", 2, "EA", "scheduled",
    f"{k2(63)}; {PLAN}_t01) two bubbles 63; K3.0 +10 in at 63 (two); {CS}77-88", NS, NS,
    "Plumbing per K2.0 (each): HW 1/2 in, CW 1/2 in, I.W. 1-1/2 in, EXTEND I.W. TO F.S. Cut sheet model carries '-TR' trash-chute suffix not on K2.0 - query.")
add(64, OP, "11 46 00", "TRASH CAN", "no make/model on K2.0", 2, "EA", "scheduled", f"{k2(64)}; {PLAN}_t01) two bubbles 64 under bar", "owner (K2.0 remark: BY OWNER)", "owner", "No utilities; owner-furnished loose item.")
add(65, FB, "11 46 00", "ICE BIN (underbar ice chest with cold plate)", "PERLICK #TSD30IC10 (cut sheet: Perlick TSD30IC10 30 in ice chest with 10-circuit cold plate, 100 lb ice, SS front/sides, 6 in backsplash, 1-1/2 in NPS male drain, 5/16 in OD SS cold plate connections)", 3, "EA", "scheduled",
    f"{k2(65)}; {PLAN}_t01) three bubbles 65; K3.0 +10 in at 65 (three); {CS}89-90", NS, NS,
    "Plumbing per K2.0 (each): I.W. 1 in, EXTEND I.W. TO F.S. KD indirect waste detail 1: GC to insulate drain lines from ice bins. Soda lines to cold plate by soda vendor (item 81).")
add(66, FB, "11 46 00", "SODA GUN & HOLDER", "PERLICK #TSF4SGB (cut sheet: Perlick TSF4SGB 4 in wide Top Shelf soda gun bracket cabinet, 24 in deep, SS, integrated drip cup to waste; gun supplied by soda vendor)", 3, "EA", "scheduled",
    f"{k2(66)}; {PLAN}_t01) three bubbles 66; K3.0 +10 in at 66; K4.0 +39 in at 66; {CS}91-92", NS, NS,
    "Plumbing per K2.0 (each): CW 1/2 in. Electrical per K2.0 (each): 120 V, 2.0 A, 1 ph, C.O., VERIFY W/SODA VENDOR. Soda gun itself and lines by soda vendor (items 80/81 remarks).")
add(67, FB, "11 46 00", "DRAINBOARD", "PERLICK #TSD21 (K2.0); cut sheet stamped Perlick TSF21DB Top Shelf full-depth drainboard 21 x 24 in (TSF series sheet lists 12-48 in widths), 1-1/2 in NPS male drain", 2, "EA", "scheduled",
    f"{k2(67)}; {PLAN}_t01) two bubbles 67; K3.0 +10 in at 67; {CS}93-95", NS, NS, "Plumbing per K2.0 (each): I.W. 1 in, EXTEND I.W. TO F.S. K2.0 model TSD21 vs cut sheet TSF21DB - query.")
add(68, OP, "11 40 00", "POS TERMINALS", "no make/model on K2.0", 3, "EA", "scheduled", f"{k2(68)}; {PLAN}_t01) three bubbles 68; K4.0 +39 in at 68 (three)", "owner (K2.0 remark: BY OWNER)", "owner",
    "Electrical per K2.0 (each): 120 V, 5.0 A, 1 ph, C.O., DEDICATED CIRCUIT, ISOLATED GROUND. Owner-furnished; EC provides outlets (K4.0 cash register outlet symbol).")
add("68.1", OP, "27 15 00", "POS TERMINALS - J-box / communication cable (second line under item 68 on K2.0)", "K2.0 continuation line: VOLT column 'J-BOX', remark 'COMMUNICATION CABLE'", 3, "EA", "inferred (one per POS terminal; K2.0 gives no qty on the continuation line)",
    f"{k2(68)} unnumbered continuation row under item 68", "owner (POS vendor, by owner)", "EC conduit per KN elec. note 14 (telephone, sound, computer, POS conduits by EC)",
    "Low-voltage: J-box and communication cable per POS terminal. KN elec. note 14: EC runs conduits for POS systems as indicated on the fixture electrical plan.")
add(69, FB, "11 46 00", "BOTTLE HOLDER (liquor step)", "PERLICK #TS18LS (cut sheet: Perlick TS18LS 18 in Top Shelf liquor step, 25 bottles, SS, 6 in backsplash, 35 lb)", 1, "EA", "scheduled", f"{k2(69)}; {PLAN}_t01) item 69; {CS}96-97", NS, NS, "No utilities.")
add(70, FB, "11 46 00", "BOTTLE HOLDER (liquor step)", "PERLICK #TS12LS (cut sheet p97 row: TS12LS 12 in, 15 bottles, 30 lb)", 1, "EA", "scheduled", f"{k2(70)}; {PLAN}_t01) item 70; {CS}96-97 (row TS12LS)", NS, NS, "No utilities. No dedicated cut sheet; model appears in the TS12/18/24LS table.")
add(71, FB, "11 46 00", "HAND SINK (underbar)", "PERLICK #TSF12HS (cut sheet: Perlick TSF12HS Top Shelf full-depth hand sink 12 x 24 in, 10 x 14 x 9 in bowl, faucet included with leads, 1-1/2 in NPS male drain, 1/2 in IPS water shanks with 18 in braided supplies, 50 lb)", 1, "EA", "scheduled",
    f"{k2(71)}; {PLAN}_t01) item 71 at west end of bar; K3.0 +10 in at 71; {CS}98-103", NS, NS, "Plumbing per K2.0: HW 1/2 in, CW 1/2 in, I.W. 1-1/2 in, EXTEND I.W. TO F.S. (K0.0 note L lists hand sinks 31/71 with soap and towel dispensers).")
add(73, OP, "11 47 00", "ICE MACHINE (bar, existing relocated)", "HOSHIZAKI #KM-520MAJ (K2.0); cut sheet in book is Hoshizaki KM-520MAJ-E (export model, 220-240V/50/1, Type G plug, R-404A) - not the US unit", 1, "EA", "scheduled",
    f"{k2(73)}; {PLAN}_t11) item 73 at back bar; K3.0 +72 in at 73/74; K4.0 +76 in at 73; {CS}104-105", "owner (K2.0 remark: EXISTING RELOCATED)", NS,
    "Plumbing per K2.0: CW 1/2 in, I.W. 1 in, EXTEND I.W. TO F.S. Electrical per K2.0: 120 V, 10.6 A, 1 ph, direct, VERIFY W/OWNER. Water via filter 75. Cut sheet does not match the scheduled US model - query.")
add(74, OP, "11 47 00", "ICE BIN (for item 73, existing relocated)", "HOSHIZAKI #B-300SF (no cut sheet; listed only as a compatible bin on p104)", 1, "EA", "scheduled",
    f"{k2(74)}; {PLAN}_t11) item 74 under 73; {CS}104 (mention only)", "owner (K2.0 remark: EXISTING RELOCATED)", NS, "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S.")
add(75, FB, "11 47 00", "WATER FILTER (for ice machines 73 and 76)", "K2.0 make/model cell blank; remark 'EVEROURE #EV9329-52' [sic]; cut sheet: Everpure (Pentair) High Flow CSR Twin 7FC system, part EV9329-72, 5.0 gpm, 50,000 gal, 3/4 in FNPT in/out, 25.25 H x 25.5 W x 6.75 D in, 42 lb operating", 1, "EA", "scheduled",
    f"{k2(75)}; {PLAN}_t11) item 75 between 73 and 76; K3.0 +72 in at 75; {CS}106-107", NS, NS,
    "Plumbing per K2.0: CW 1/2 in, WATER FOR ITEMS #73 & #76. Part number differs (EV9329-52 on K2.0 vs EV9329-72 on cut sheet) - query. KN plumbing note 19: plumber connects filtering equipment.")
add(76, OP, "11 47 00", "ICE MACHINE (bar, existing relocated)", "no make/model on K2.0", 1, "EA", "scheduled", f"{k2(76)}; {PLAN}_t11) item 76; K3.0 +72 in; K4.0 +76 in at 76", "owner (K2.0 remark: EXISTING RELOCATED)", NS,
    "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S. (no CW column entry; water via filter 75 per item 75 remark). Electrical per K2.0: 120 V, amps '*', 1 ph, direct, VERIFY W/OWNER. Load not given.")
add(77, OP, "11 47 00", "ICE BIN (for item 76, existing relocated)", "no make/model on K2.0", 1, "EA", "scheduled", f"{k2(77)}; {PLAN}_t11) item 77", "owner (K2.0 remark: EXISTING RELOCATED)", NS, "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S.")
add(78, FB, "11 41 00", "SLIDING DOOR REFRIGERA[TOR] (description clipped on K2.0)", "ATOSA #MCF8727GR (cut sheet: Atosa MCF8727GR 2 sliding glass door merchandiser refrigerator, black exterior/SS interior, 44.9 cu ft, 8 shelves, 54.4 x 29.7 x 81.2 in, 115/60/1, 4.2 A, 1/4 HP, R290, NEMA 5-15P, 456 lb)", 2, "EA", "scheduled",
    f"{k2(78)}; {PLAN}_t11) two bubbles 78 at back bar; K4.0 +48 in at 78 (two); {CS}108-109", NS, NS, "Electrical per K2.0 (each): 120 V, 2.1 A, 1 ph, C.O., SELF-CONTAINED (cut sheet rates 4.2 A).")
add(79, FB, "11 41 00", "REACH IN FREEZER (glass door)", "ATOSA #MCF8720GR (cut sheet: Atosa MCF8720GR 1 glass door freezer, black exterior/SS interior, 19.4 cu ft, 4 shelves, 27 x 31.5 x 81.2 in, 115/60/1, 2.1 A, 1/2 HP, R290, NEMA 5-15P, 309 lb)", 1, "EA", "scheduled",
    f"{k2(79)}; {PLAN}_t11) item 79 at back bar; K4.0 +48 in at 79; {CS}110-111", NS, NS, "Electrical per K2.0: 120 V, 2.1 A, 1 ph, C.O., SELF-CONTAINED.")
add(80, OP, "11 46 00", "SODA/ICE DISPENSER", "ENDURO #250 (K2.0); cut sheet: Cornelius Enduro 250 post-mix ice drink dispenser, part 0528452, 250 lb ice, 115 V/60 Hz/3.5 A, 0.75 in PVC NPT drain, 30 in wide, approx 39-5/8 in tall on 4 in legs, plus 30 x 30 x 30 in stand", 1, "EA", "scheduled",
    f"{k2(80)}; {PLAN}_t11) item 80 at bar; K3.0 +12 in at 80; K4.0 +12 in at 80; {CS}112-114", "soda vendor (K2.0 remark: BY SODA VENDOR)", NS,
    "Plumbing per K2.0: CW 1/2 in, I.W. 1 in, EXTEND I.W. TO F.S. Electrical per K2.0: 120 V, 5.0 A, 1 ph, C.O., VERIFY W/SODA VENDOR. Vendor-furnished; rough-ins in base contract.")
add(81, OP, "11 46 00", "SODA SYSTEM (bar 1st level)", "no make/model on K2.0", 1, "LOT", "scheduled", f"{k2(81)}; {PLAN}_t11) item 81 at bar; K4.0 +12 in at 81", "soda vendor (K2.0 remark: BY SODA VENDOR)", "soda vendor",
    "Electrical per K2.0: 120 V, 6.0 A, 1 ph, C.O., VERIFY W/SODA VENDOR. EC provides conduit for remote CO2/syrup/beer lines (KN refrig. note 5, note 11: runs max 45 ft, 3 bends, 12 x 12 x 4 pull boxes). KN plumbing note 20: water to coffee makers not off softeners.")
add(82, OP, "11 46 00", "COFFEE MAKER", "no make/model on K2.0", 1, "EA", "scheduled", f"{k2(82)}; {PLAN}_t11) item 82; K3.0 +48 in at 82; K4.0 +12 in at 82", "owner (K2.0 remark: BY OWNER)", NS,
    "Plumbing per K2.0: CW 1/2 in. Electrical per K2.0: 208 V, 23.2 A, 1 ph, direct, VERIFY W/OWNER. Owner-furnished; rough-ins in base contract.")
add(83, OP, "11 46 00", "TEA MAKER", "no make/model on K2.0", 1, "EA", "scheduled", f"{k2(83)}; {PLAN}_t11) item 83; K3.0 +48 in at 83; K4.0 +48 in at 83", "owner (K2.0 remark: BY OWNER)", NS,
    "Plumbing per K2.0: CW 1/2 in. Electrical per K2.0: 120 V, 13.8 A, 1 ph, direct, VERIFY W/OWNER. Owner-furnished; rough-ins in base contract.")
add(84, FB, "11 46 00", "WORKCOUNTER (back bar)", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(84)}; {PLAN}_t11) item 84 at back bar under 82/83; K4.0 +48 in at 84", NS, NS,
    "No utilities on K2.0 (K4.0 shows an outlet +48 in at 84). Custom-fabricated stainless steel; dimensions not given.")
add(85, FB, "11 41 00", "REACH IN REFRIGERATOR (glass door)", "ATOSA #MCF8705GR (cut sheet: Atosa MCF8705GR 1 glass door reach-in refrigerator, SS exterior/interior, 19.1 cu ft, 4 shelves, 27 x 31.7 x 83.1 in, 115/60/1, 2.1 A, 1/7 HP, R290, NEMA 5-15P, 293 lb)", 1, "EA", "scheduled",
    f"{k2(85)}; {PLAN}_t11) item 85 at east end of back bar; K4.0 +48 in at 85; {CS}115-116", NS, NS, "Electrical per K2.0: 120 V, 2.1 A, 1 ph, C.O., SELF-CONTAINED.")
# ---------------------------------------------------------------- scullery / dish
add(88, FB, "11 48 00", "THREE COMPARTMENT SIN[K] (description clipped on K2.0)", "GSW #SE18183D20 (cut sheet: GSW SE18183D20 three-compartment sink, 18 ga SS, bowls 18 x 18 x 12 in, two 20 in drainboards, OA 24 x 94-3/8 x 45 in, 8 in faucet centers, strainers 3-5/8 in, 93 lb)", 1, "EA", "scheduled",
    f"{k2(88)}; {PLAN}_t00) item 88 at scullery north wall; K3.0 (K_p05) +10 in at 88 and 22/88 'VFY. W/ PLUMBER'; {CS}117-118", NS, NS,
    "Plumbing per K2.0: direct waste 2 in, DIRECT WASTE TO ITEM #22 (grease interceptor). Faucets items 90 and 91. K0.0 note K: utensil/pot wash sink item 88, 3-compartment, drainboards each at least as large as largest compartment. Water heater calc P-6 lists a 24 x 18 (3) comp. sink at 57 GPH and an 18 x 18 (2) comp. sink at 10 GPH - the second sink is not on K2.0 (see notes).")
add(89, FB, "11 41 00", "WALL SHELVES (over 3-comp sink)", "GSW #WS-W1236 (cut sheet p36-37 row within item 26 sheet: WS-W1236 12 x 36 in 18 ga SS wall shelf, 300 lb)", 2, "EA", "scheduled", f"{k2(89)}; {PLAN}_t00) one bubble 89 over sink 88; {CS}36-37 (row WS-W1236)", NS, NS, "No utilities. Wall backing by GC.")
add(90, FB, "11 48 00", "PRE-RINSE FAUCET (3-comp sink)", "T & S #B-0133-ADF12-B (cut sheet: T&S B-0133-ADF12-B EasyInstall 8 in wall-mount pre-rinse unit, quarter-turn Eterna cartridges, 12 in add-on swing nozzle, 44 in flexible SS hose, 1.15 GPM spray valve, 6 in wall bracket, 1/2 in NPT female inlets)", 1, "EA", "scheduled",
    f"{k2(90)}; {PLAN}_t00) item 90 at sink 88; K3.0 +10/+12 in at 90; {CS}119-120", NS, NS, "Plumbing per K2.0: HW 1/2 in, CW 1/2 in.")
add(91, FB, "11 48 00", "SINK FAUCET (3-comp sink)", "T &S #B-0230 (cut sheet: T&S B-0230 8 in wall-mount mixing faucet, quarter-turn Eterna cartridges, lever handles, 18 in swivel nozzle, 1/2 in NPT female inlets)", 1, "EA", "scheduled",
    f"{k2(91)}; {PLAN}_t00) item 91 at sink 88; K3.0 +12 in at 91; {CS}121-122", NS, NS, "Plumbing per K2.0: HW 1/2 in, CW 1/2 in.")
add(92, FB, "11 41 00", "POT/UTENSIL RACK (wall mount)", "GSW #PR-WM4 (cut sheet: GSW PR-WM4 double wall-mount pot rack, 304 SS 10 ga flat bar, 11-3/4 x 46 x 11-3/4 in, 4 brackets, pot hooks included, 22 lb)", 1, "EA", "scheduled",
    f"{k2(92)}; {PLAN}_t00) item 92 over sink 88 (west end); {CS}123-124", NS, NS, "No utilities. Wall backing by GC (KD wall backing detail 4 'utensil/pot rack/shelving').")
add(93, FB, "11 48 00", "HAND SINK (scullery)", "GSW #HS-1615S (same cut sheet as item 31: 15-1/4 x 15-3/4 x 13-3/8 in, 1-1/2 in NPS drain)", 1, "EA", "scheduled",
    f"{k2(93)}; {PLAN}_t00) item 93 at scullery west wall; K3.0 +14/+16 in at 93; {CS}46-47", NS, NS, "Plumbing per K2.0: HW 1/2 in, CW 1/2 in, direct waste 1-1/2 in, DIRECT WASTE.")
add(94, FB, "11 48 00", "CLEAN DISHTABLE", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(94)}; {PLAN}_t00) item 94 at dishmachine 98 (west wall)", NS, NS,
    "No utilities. Custom-fabricated stainless steel; length not dimensioned on K1.0. CMA 180-C is a corner machine (cut sheet p130) - clean table at 90 deg to soiled table 100. Sleeves/cantilever brackets by FSEC, installed by GC (KN curb notes 12-13).")
add(95, FB, "11 48 00", "SLANT RACK SHELF (tubular wall-mount drainage shelf)", "GSW #WS-WD1648 (cut sheet: GSW WS-WD1648 tubular wall-mount drainage shelf, 1-5/8 in SS tubing, 16 x 48 x 9 in, 3 brackets, 33 lb)", 1, "EA", "scheduled (K2.0 qty 1; K1.0 carries TWO bubbles 95 - scullery and service bar)",
    f"{k2(95)}; {PLAN}_t00) bubble 95 at scullery west wall AND (K_p02_t01) second bubble 95 at service bar near 83/84; {CS}125", NS, NS,
    "No utilities. Plan count (2) exceeds schedule qty (1) - query whether a second shelf is intended at the back bar. Wall backing by GC.")
add(96, FB, "11 48 00", "GLASS RACK DOLLIES", "CAMBRO #CD2020110 (cut sheet: Cambro CD2020 Camdolly for 20 x 20 in racks, color 110 black, 300 lb, 22-1/2 x 22-1/2 x 8-1/4 in, four 3 in swivel casters)", 3, "EA", "scheduled",
    f"{k2(96)}; {PLAN}_t00) one bubble 96 at scullery (dollies drawn stacked under shelf 95); {CS}126-128", NS, NS, "No utilities. Loose/mobile item; smallwares-type but scheduled, so kept.")
add(97, FB, "23 38 13", "EXHAUST HOOD (TYPE 2) over dishmachine", "CAPTIVE AIRE (K7.0 hood 3 'Hood 2': model 4212 VHB-G, 3'-6\" long, 700 deg, Type II, 171 CFM/ft, 600 CFM exhaust, riser 10 in dia x 4 in, 430 SS 100%, no filters, 0 lights, no fire system, hanging weight 102 lb; K7.0 plan/section: 42 x 42 in, 10 in riser, 3/4 in perimeter gutter drain)", 1, "EA", "scheduled",
    f"{k2(97)}; {PLAN}_t10) item 97 over dishmachine 98 in SCULLERY; K7.0 hood information tables and plan/section view hood #3 (K_p09)", NS, NS,
    "Electrical per K2.0: 120 V, amps '*', 1 ph, direct, INTERCONNECT WITH ITEM #98. Clearance to combustibles 18 in all sides except front 0 in (K7.0 hood 2 row). K4.0 note 'TO DISHWASH HOOD FAN'. Mechanical sub for duct and fan (fan not on K7.0).")
add(98, FB, "11 48 00", "DISHMACHINE", "CMA #CMA-180C (cut sheet: CMA Dishmachines 180-C single-tank high-temperature corner door-type dishwasher, 25 D x 25-1/2 W x 78-79 H in, 20 x 20 racks, 17-1/2 in clearance, .82 gal/rack, 1 HP wash pump; electrical table: 208 V 3 ph 24 A, 480 V 3 ph 10 A, with booster 208 V 1 ph 78 A; water inlet 3/4 in, drain 2 in, rinse 20 +5 psi, 338 lb)", 1, "EA", "scheduled",
    f"{k2(98)}; {PLAN}_t10) item 98 in SCULLERY corner; K3.0 +72/+14/+16 in at 98 area; K4.0 +66 in at 98; {CS}129-130", NS, NS,
    "Plumbing per K2.0: HW 3/4 in, I.W. 2 in, EXTEND I.W. TO F.S. Electrical per K2.0: 208 V, 20.0 A, 3 ph, direct (cut sheet lists 24 A at 208/3). K0.0 note U: dishwasher w/ booster heater +180 F (booster not separately scheduled - if built-in booster, cut sheet 208/1 78 A applies; query). KN plumbing note 18: 180 F recirculating line, 20 psi regulator and temperature gauge by plumber.")
add(99, FB, "11 48 00", "PRE-RINSE FAUCET (soiled dishtable)", "T & S #B-0133-ADF12-B (same cut sheet as item 90)", 1, "EA", "scheduled", f"{k2(99)}; {PLAN}_t10) item 99 at soiled dishtable sink; K3.0 +12 in at 99; {CS}119-120", NS, NS, "Plumbing per K2.0: HW 1/2 in, CW 1/2 in.")
add(100, FB, "11 48 00", "SOILED DISHTABLE (with pre-rinse sink)", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(100)}; {PLAN}_t10) item 100 in SCULLERY (long table with sink); K3.0 +14/+16 in at 100", NS, NS,
    "Plumbing per K2.0: I.W. 1-1/2 in, EXTEND I.W. TO F.S. (pre-rinse sink drain). Custom-fabricated stainless steel; length not dimensioned on K1.0. Sleeves/cantilever brackets by FSEC, installed by GC (KN curb notes 12-13).")
add(101, FB, "11 48 00", "SORTING RACK SHELF (over soiled dishtable)", "CUSTOM ST/ST", 1, "EA", "scheduled", f"{k2(101)}; {PLAN}_t10) item 101 over table 100", NS, NS, "No utilities. Custom-fabricated stainless steel.")
# ---------------------------------------------------------------- 2nd-level support items (listed on K2.0, drawn near scullery)
add(102, FB, "11 40 00", "REFRIGERATOR/HTD. CAB[INET] (description clipped on K2.0)", "RDH132WUT-HHS (K2.0 gives model only, no manufacturer; no cut sheet - book page stamped 'Item #104' is an Atosa MGF8401GR undercounter refrigerator and does not match)", 1, "EA", "scheduled",
    f"{k2(102)}; {PLAN}_t10) item 102 south of scullery by dumbwaiter wall; K4.0 +48 in at 102", NS, NS,
    "Electrical per K2.0: 208 V, 11.0 A, 1 ph, C.O. Manufacturer and cut sheet missing - query (model string RDH132WUT-HHS unmatched in the book).")
add(103, FB, "11 46 00", "SODA SYSTEM - FOR 2ND LEVEL", "no make/model on K2.0", 1, "EA", "scheduled", f"{k2(103)}; {PLAN}_t10) item 103 south of scullery; K3.0 +72 in at 103; K4.0 +76 in at 103", "not stated on K2.0 (remark column says only FOR 2ND LEVEL; electrical remark VERIFY W/SODA VENDOR; items 80/81 carry BY SODA VENDOR, this line does not)", NS,
    "Plumbing per K2.0: CW 1/2 in. Electrical per K2.0: 120 V, 6.0 A, 1 ph, C.O., VERIFY W/SODA VENDOR. Serves the mezzanine prep-bar (A-5.20); equipment on the mezzanine itself is not on K2.0. Query whether this is soda-vendor scope like 80/81.")
add(104, FB, "11 47 00", "WATER FILTER - FOR ITEM 103 & 105", "EVERPURE #EV9329-52 (K2.0; same part no. as item 75 remark; cut sheet for item 75 shows EV9329-72; book page stamped Item #104 is an unrelated Atosa MGF8401GR)", 1, "EA", "scheduled",
    f"{k2(104)}; {PLAN}_t10) item 104 by 103; K3.0 +72 in at 104; {CS}106-107 (by part no.), 131-132 (mis-stamped)", NS, NS, "Plumbing per K2.0: CW 1/2 in. Remark 'FOR ITEM !03 & 105' [sic]. Part number discrepancy as item 75 - query.")
add(105, FB, "11 47 00", "ICE MACHINE (2nd level service)", "HOSHIZAKI #KM-520MAJ (new; cut sheet in book is the KM-520MAJ-E export model - see item 73)", 1, "EA", "scheduled",
    f"{k2(105)}; {PLAN}_t10) item 105 at scullery south wall; K3.0 +72 in at 105/106; K4.0 +76 in at 105; {CS}104-105", NS, NS,
    "Plumbing per K2.0: CW 1/2 in, I.W. 1 in, EXTEND I.W. TO F.S. Electrical per K2.0: 120 V, 10.6 A, 1 ph, direct. No EXISTING remark, so new unit. US model data (production, amps) not in book - query.")
add(106, FB, "11 47 00", "ICE BIN (for item 105)", "HOSHIZAKI #B-300SF (no cut sheet; compatible-bin mention on p104 only)", 1, "EA", "scheduled", f"{k2(106)}; {PLAN}_t10) item 106 under 105; {CS}104 (mention only)", NS, NS, "Plumbing per K2.0: I.W. 1 in, EXTEND I.W. TO F.S.")

# ---------------------------------------------------------------- write
fields = ["item_id", "bid_letter_item", "division", "description", "spec_or_model", "qty", "unit",
          "qty_basis", "qty_source", "furnished_by", "installed_by", "notes"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("rows written:", len(rows), "->", OUT)

# ---------------------------------------------------------------- utility arithmetic (K2.0 readable values only)
# (item, qty, volts, amps or None, kw or None, phase)
elec = [
    (4, 1, 120, 6.0, None, 1), (5, 1, 120, 3.2, None, 1), (7, 1, 120, 5.0, None, 1), (8, 1, 120, 3.0, None, 1),
    (11, 1, 120, 3.0, None, 1), (17, 1, 120, 11.8, None, 1), (18, 1, 120, 12.0, None, 1), (22, 1, 120, 4.0, None, 1),
    (25, 1, 120, 2.8, None, 1), (27, 1, 208, 26.0, None, 1), (28, 3, 120, 16.0, None, 1), (29, 2, 120, 11.8, None, 1),
    (30, 1, 120, 2.3, None, 1), (32, 1, 120, 2.3, None, 1), (35, 3, 208, 10.6, None, 1), (37, 1, 120, 2.8, None, 1),
    (38, 1, 120, 11.8, None, 1), (40, 1, 120, 15.0, None, 1), (46, 1, 208, None, 10.8, 3), (47, 1, 120, 5.0, None, 1),
    (50, 1, 120, 2.3, None, 1), (53, 1, 120, 5.0, None, 1), (54, 1, 120, 15.1, None, 1), (55, 1, 120, 20.0, None, 1),
    (56, 1, 120, 6.0, None, 1), (66, 3, 120, 2.0, None, 1), (68, 3, 120, 5.0, None, 1), (73, 1, 120, 10.6, None, 1),
    (78, 2, 120, 2.1, None, 1), (79, 1, 120, 2.1, None, 1), (80, 1, 120, 5.0, None, 1), (81, 1, 120, 6.0, None, 1),
    (82, 1, 208, 23.2, None, 1), (83, 1, 120, 13.8, None, 1), (85, 1, 120, 2.1, None, 1), (98, 1, 208, 20.0, None, 3),
    (102, 1, 208, 11.0, None, 1), (103, 1, 120, 6.0, None, 1), (105, 1, 120, 10.6, None, 1),
]
unreadable = [(6, 208, 1), (9, 208, 1), (12, 208, 1), (57, 208, 3), (76, 120, 1), (97, 120, 1)]
gas = [(14, 1, 250, "existing water heater on roof"), (47, 1, 198, ""), (48, 1, 43, ""), (49, 1, 105, ""), (51, 1, 75, ""), (52, 2, 102, "two fryers, K3.0 shows two taps")]
iw = [(8, 1, '1"'), (12, 1, '1"'), (14, 1, '3/4"'), (17, 1, '1-1/2"'), (62, 1, '1"'), (63, 2, '1-1/2"'), (65, 3, '1"'), (67, 2, '1"'),
      (71, 1, '1-1/2"'), (73, 1, '1"'), (74, 1, '1"'), (76, 1, '1"'), (77, 1, '1"'), (80, 1, '1"'), (98, 1, '2"'), (100, 1, '1-1/2"'),
      (105, 1, '1"'), (106, 1, '1"')]
direct = [(19, 1, '2"'), (22, 1, '4"'), (31, 2, '1-1/2"'), (88, 1, '2"'), (93, 1, '1-1/2"')]

summary = []
def line(s):
    summary.append(s)
    print(s)

line("\n== ELECTRICAL (K2.0 readable values; '*' lines excluded) ==")
for v, ph in [(120, 1), (208, 1), (208, 3)]:
    sel = [e for e in elec if e[2] == v and e[5] == ph and e[3] is not None]
    per_line = sum(e[3] for e in sel)
    ext = sum(e[3] * e[1] for e in sel)
    terms = " + ".join(f"{e[3]}" + (f"x{e[1]}" if e[1] > 1 else "") for e in sel)
    kva = ext * v / 1000 * (1.732 if ph == 3 else 1)
    line(f"{v} V {ph}-ph: {len(sel)} lines, as listed {per_line:.1f} A; extended by qty {ext:.1f} A = {terms}; "
         f"{'~' if ph == 3 else ''}{kva:.1f} kVA")
line("208 V 3-ph kW line: item 46 combi 10.8 KW (each deck, qty 1) = 10.8 kW -> 10,800 / (208 x 1.732) = %.1f A" % (10800 / (208 * 1.732)))
line("unreadable/'*' electrical lines excluded: " + ", ".join(f"item {i} ({v} V {p}-ph)" for i, v, p in unreadable))
line("\n== GAS (MBTU) ==")
g_lines = sum(g[2] for g in gas)
g_ext = sum(g[2] * g[1] for g in gas)
g_new_ext = sum(g[2] * g[1] for g in gas if g[0] != 14)
line("as listed per line incl. existing water heater: " + " + ".join(str(g[2]) for g in gas) + f" = {g_lines} MBTU")
line("extended by qty incl. water heater: " + " + ".join(f"{g[2]}" + (f"x{g[1]}" if g[1] > 1 else "") for g in gas) + f" = {g_ext} MBTU")
line(f"new cooking equipment only (items 47, 48, 49, 51, 52x2): 198 + 43 + 105 + 75 + 102x2 = {g_new_ext} MBTU/h")
line("\n== WASTE ==")
line(f"indirect waste (I.W.) lines: {len(iw)}; connections extended by qty: {sum(q for _, q, _ in iw)} "
     f"(incl. item 14 existing heater 3/4 in); new I.W. connections: {sum(q for i, q, _ in iw if i != 14)}")
line("I.W. by size: " + ", ".join(f"{s}: {sum(q for _, q, t in iw if t == s)}" for s in ['3/4"', '1"', '1-1/2"', '2"']))
line(f"direct waste lines: {len(direct)}; connections: {sum(q for _, q, _ in direct)} "
     "(19 mop sink 2 in, 22 interceptor 4 in, 31 hand sinks 1-1/2 in x2, 88 3-comp 2 in to #22, 93 hand sink 1-1/2 in)")
with open(os.path.join(OUT_DIR, "scripts", "utility_totals.txt"), "w") as f:
    f.write("\n".join(summary) + "\n")
