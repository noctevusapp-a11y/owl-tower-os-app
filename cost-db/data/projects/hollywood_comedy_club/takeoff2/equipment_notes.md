# F&B equipment schedule - notes (Hollywood Comedy Club, Kelly Architects 2604)

Companion to `equipment.csv` (98 rows). Built from the health plan-check K-sheets "BIRD CAGE DRAWINGS 062626" (Fred Schmid & Associates LLC, owner 33 Taps LLC, project name on the K-sheets "BIRD CAGE" / "THATZ HILARIOUS", dated 06/26/26) and the "Thatz Hilarious Cutsheet Book 061426" (132 pp). Nothing in this folder is priced; the CSV is the list that quotes will be requested against. Scripts: `scripts/crop_k_schedule.py` (schedule crops), `scripts/crop_k_details.py` (hood / walk-in / plan / notes crops), `scripts/cutsheet_digest.py` (cut sheet text digest), `scripts/build_equipment.py` (writes the CSV and `scripts/utility_totals.txt`).

## 1. Sheet map (17 pages, no text layer except p8)

| render | sheet | content |
|---|---|---|
| K_p01 | K0.0 | Environmental general notes, room finish schedule, foodservice index |
| K_p02 | K1.0 | Equipment plan, 1,654 SF, item bubbles 1-106 |
| K_p03 | K0.1 | Existing equipment plan |
| K_p04 | K2.0 | Equipment schedule 1st level (item, description, qty, make/model, remarks; plumbing HW/CW/gas conn/MBTU/waste dir./I.W./remarks; electrical volt/kW/amps/HP/ph/conn dir./C.O./remarks) |
| K_p05 | K3.0 | Equipment plumbing plan (rough-in heights) |
| K_p06 | K4.0 | Equipment electrical plan (rough-in heights) |
| K_p07 | K5.0 | Building conditions plan (curbs, wall backing, duct collars) |
| K_p08 | A-3.12 | Kelly ceiling finish plan (food service area drywall ceiling, flat panel LED) - only page with a text layer |
| K_p09 / K_p10 | K7.0 / K7.1 | CaptiveAire exhaust hood drawings, job 8710180, 6/4/2026 |
| K_p11 / K_p12 / K13_p01 / K13_p02 | K8.0-K8.3 | Arctic walk-in cooler/freezer drawings Q228534, 6/4/2026 (plan, elevation, panel spec + refrigeration spec, details, wiring) |
| K13_p03 | P-6 | Kelly existing water heater spec and water heater calc |
| K13_p04 | KD | Equipment details (wall shelf, remote fire pull, fire-system wiring, CSR wiring, indirect waste, floor sink, concrete base, wall backing, hood rod hanger) |
| K13_p05 | KD (notes) | Notes to general contractor, fixture plumbing / electrical / refrigeration / curb and wall backing / exhaust and make-up air notes |

## 2. Legend of codes as printed on K2.0 (footer, tile K_p04_t11/t12)

> K.E.C. - KITCHEN EQUIPMENT CONTRACTOR, G.C. - GENERAL CONTRACTOR, OWN. - OWNER, P.C. - PLUMBING CONTRACTOR, E.C. - ELECTRICAL CONTRACTOR, O - OUTLET, C.O. - CONVENIENCE OUTLET, DIRECT - DIRECT CONNECTION
> I.W. - INDIRECT WASTE, F.D. - FLOOR DRAIN, F.S. - FLOOR SINK, R.D. - ROOF DRAIN, F.T. - FLOOR TROUGH

**The schedule has no furnished-by / installed-by columns.** The legend defines K.E.C., G.C. and OWN. but no row carries those codes. KN "Notes to General Contractor" 12 ("provide and install all items noted G.C. on fixture equipment schedules") and 23 ("install all items listed in schedule by food service equipment cont'r* symbol, i.e. provided by food service equipment contractor, installed by general contractor") refer to symbols that do not appear on K2.0. The CSV therefore fills `furnished_by` / `installed_by` only from the REMARKS column text (BY OWNER, BY SODA VENDOR, EXISTING RELOCATED, EXISTING TO REMAIN) and writes "not stated on K2.0" everywhere else. `bid_letter_item` = "Owner-provided equipment install" only where the remark says BY OWNER, BY SODA VENDOR or EXISTING RELOCATED; item 14 (existing water heater to remain) is tagged "existing to remain (no bid scope on K2.0)".

Who furnishes what, as far as K2.0 says:
- Owner (BY OWNER): 64 trash cans (2), 68 POS terminals (3) + J-box/comm cable line, 82 coffee maker, 83 tea maker.
- Owner existing, relocated (EXISTING RELOCATED): 2 lockers (5), 6 floor mixer, 17 prep table w/ sinks, 46 Rational combi, 73 ice machine + 74 bin, 76 ice machine + 77 bin.
- Soda vendor (BY SODA VENDOR): 80 soda/ice dispenser, 81 soda system (1 LOT). Item 103 soda system "FOR 2ND LEVEL" carries no vendor remark (electrical remark VERIFY W/SODA VENDOR) - query.
- Existing to remain: 14 A.O. Smith BTH-250 water heater on roof.
- Everything else (82 rows): no furnishing party stated. The "ENVIRONMENTAL NOTES" on K0.0 assign the janitorial sink (item 19) and hand sinks (31/71) to "GEN. CONTR." / "K.E.C." in the plan-check guide wording (notes J and L) - treat as scope questions, not as a furnishing column.
- Trades named in the KD/KN notes (K13_p05) regardless of who furnishes: plumbing and electrical rough-ins, final connections, curbs, backing, cantilever supports, shafts, roof curbs/platforms by GC and subs (GC notes 1-5, 13, 16); refrigeration compressors, lines, valves and rack by the fixture refrigeration contractor (refrig. notes 7-8); hood hanger rods by hood installer (KD hood rod hanger detail); fire-system contactors and shunt-trip interconnect by EC (KD wiring schematic, elec. note 31).

## 3. Counts by category (rows = CSV lines; EA counts use scheduled qty)

| category (division used) | rows | units | items |
|---|---|---|---|
| Cooking (11 44 00) | 12 | 17 EA | 27 conveyor oven (double stack), 28 heated cabinets x3, 35 heat lamps x3, 40 hot food well, 45 combi water filter, 46 combi (existing), 47 range, 48 cheesemelter, 49 charbroiler, 51 griddle, 52 fryers x2, 54 fry dump |
| Refrigeration, self-contained (11 41 00 part) | 10 | 11 EA | 5, 25, 30, 32, 37, 50, 53, 78 x2, 79, 85 |
| Walk-ins and remote refrigeration (11 41 00 part) | 6 | 1 combined box (cooler, no floor + freezer, with floor), 2 evaporator coils, 2 condensing units | 7, 8, 9.1, 9.2, 11, 12 (Arctic box Q228534; Russell R-454A outdoor C/Us per K8.2) |
| Shelving / storage (11 41 00 part) | 7 | 2 LOT + 9 EA | 1 (lot), 10 (lot), 13 x3, 26 x2, 36 x2, 89 x2, 92 pot rack |
| Hoods, fans, fire system (23 38 13 / 21 23 00) | 6 | 3 hoods (Type I 10'-1" + 8'-1" = 18'-3", Type II 3'-6"), 1 fan lot, 1 fire system, 1 flashing lot | 55, 56.1, 56.2, 57, 58, 97 |
| Dish / scullery / sinks / faucets (11 48 00) | 16 | 17 EA | 19, 20, 21, 22, 31 x2, 88, 90, 91, 93, 94, 95, 96 x3, 98, 99, 100, 101 |
| Prep tables, work counters, slicer, mixer, processor (11 42 00) | 12 | 13 EA | 3, 4, 6, 16, 17, 18, 29 x2, 33, 34, 38, 39, 41 |
| Bar (11 46 00) | 16 | 1 LOT + 22 EA | 61 bar top lot, 62, 63 x2, 64 x2, 65 x3, 66 x3, 67 x2, 69, 70, 71, 80, 81 (lot), 82, 83, 84, 103 |
| Ice (11 47 00) | 8 | 8 EA | 73, 74, 75, 76, 77, 104, 105, 106 |
| Other | 5 | - | 2 lockers (10 51 13), 14 water heater (22 34 00), 68 POS + 68.1 comm (11 40 00 / 27 15 00), 102 refrigerator/heated cabinet model RDH132WUT-HHS (11 40 00, no manufacturer) |

Custom-fabricated stainless steel (CUSTOM ST/ST on K2.0, no cut sheets, no dimensions on the K-sheets): 16, 17 (existing), 33, 34, 38, 39, 41, 58 wall flashing, 61 service bar top, 84, 94 clean dishtable, 100 soiled dishtable, 101 sorting shelf = 13 lines. Plan lengths are not dimensioned on K1.0; fabricator shop drawings govern (KD).

Smallwares: none are scheduled and none were added. The only loose items on K2.0 are the owner's trash cans (64) and the Cambro glass-rack dollies (96, kept because scheduled). Pages 1-4 of the cut sheet book (Elite Lighting 22-FPL1-LED 2x2 flat panel, fixture type F1) are a lighting cut sheet, not equipment, and are excluded.

Spare numbers on K2.0 (no row written): 15, 23, 24, 42, 43, 44, 59, 60, 72, 86, 87 (11). Scheduled items = 106 - 11 = 95; CSV rows = 95 + 3 sub-rows (9.2 second condensing unit per K8.2, 56.2 second Type I hood section per K7.0, 68.1 POS J-box/communication line) = 98.

Rows that need a mechanical / refrigeration / fire subcontract regardless of who buys the equipment: walk-in refrigeration 8, 9.1, 9.2, 12 (refrigeration contractor, outdoor C/Us on a GC roof platform); hoods 56.1, 56.2, 97 and fan lot 57 (sheet-metal/mechanical: ducts, shafts, roof curbs, exhaust and MUA fans - fan models are not in the K package); fire system 55 (wet-chemical contractor + EC shunt-trip/contactor interconnect + plumber gas valve).

## 4. Plan vs schedule vs cut sheets

Plan bubbles without a schedule line: none. Every bubble on K1.0 (K_p02) from 1 to 106 has a K2.0 row; the 11 spare numbers do not appear on the plan.

Schedule lines not located on K1.0: 9 refrigeration system (outdoor condensing units per K8.2 - roof, no bubble), 14 water heater (existing on roof).

Quantity differences plan vs schedule:
- 95 slant rack shelf: scheduled 1, drawn twice (scullery west wall, K_p02_t00; and at the service bar next to 83/84, K_p02_t01).
- 2 lockers: scheduled 5, drawn as one bank; 1 storage shelving: 1 LOT, 6 units drawn; 10 cooler shelving: 1 LOT, 5 units drawn; 13 freezer shelving: 3, 3 drawn.
- 26, 36, 89 shelves scheduled 2 each, one bubble each (double tier not distinguishable on the plan).
- 52 fryers: one bubble, two units drawn and two gas taps on K3.0 - matches qty 2.
- All other multi-quantity items (28 x3, 29 x2, 31 x2, 35 x3, 63 x2, 64 x2, 65 x3, 66 x3, 67 x2, 68 x3, 78 x2, 96 x3) match the plan.

Equipment on the architectural sheets that has no K-schedule line:
- Mezzanine PREP-BAR (room 24) on A-5.20 "PICK-UP BAR TOP PLAN" (scratch render A520-15 from BandS part06 p15) and Addendum 1 bar elevations: units tagged Q-270, 18-53C, TBB-24GAL-72, 32-ST, a multi-compartment sink and a hand sink, with keynote 2 "Kitchen equipment; see K-sheets for more information". K2.0 is titled "EQUIPMENT SCHEDULE 1ST LEVEL"; K1.0 draws the first floor only; the only mezzanine-related lines are 102-106 ("FOR 2ND LEVEL" on 103, filter 104 "FOR ITEM 103 & 105"), which K1.0 places on the first floor south of the scullery. The mezzanine bar equipment itself is unscheduled.
- A-5.20 keynote 1: stainless-steel pick-up counter at 34 in AFF (WC-2) - architectural millwork, not on K2.0 (prior takeoff line E04).
- A-2.20 keynote 27 "(N) Bar equipment" (mezzanine) - same gap.
- P-6 water heater calc (K13_p03) lists an "18 x 18 (2) comp. sink", a "bar triple sink", 3 bar dump sinks, 2 bar hand sinks, 8 hand sinks/lavatories and a "glass washer" (20 GPH). K2.0 has 2 dump sinks (63), 1 bar hand sink (71), no 2-compartment sink, no bar triple sink and no glass washer. These probably belong to the mezzanine bar; confirm.

Cut sheet coverage: pages stamped Item #1, 3, 4, 5, 14, 18, 19, 20, 21, 22, 25, 26, 27, 28, 29, 30, 31, 32, 35, 36, 40, 45, 47, 48, 49, 51, 52, 53, 54, 62, 63, 65, 66, 67, 69, 71, 73, 75, 78, 79, 80, 85, 88, 90, 91, 92, 95, 96, 98, 104 (50 items; 14 is printed twice, p5-10 and p18-23). Items that rely on another item's sheet: 37 (p49 table), 50 (p45 table), 70 (p97 table), 89 (p36-37 table), 93 and 99 (same models as 31 and 90), 74/106 (B-300SF mentioned on p104 only). No cut sheet at all: 2, 6, 7-13 (walk-in: K8 sheets instead), 16, 17, 33, 34, 38, 39, 41, 46, 55-58 (hoods: K7 sheets), 61, 64, 68, 76, 77, 81-84, 94, 97 (K7.0 hood 2), 100-103, 105 (uses 73's sheet).

Model-number differences K2.0 vs cut sheet (all listed in the CSV `spec_or_model`): 1 MQ21XXQ vs MQ2148G; 36 14XXFG vs 1436FG; 45 R295-CL vs R295-CLX; 52 ATFS-40 vs ATFS-40ES-NG; 63 TSF18DS vs TSF18DS-TR (+ 934GN-LF faucet, 7055-48, 7054R pages); 67 TSD21 vs TSF21DB; 73/105 KM-520MAJ vs KM-520MAJ-E (export 220-240 V/50 Hz model in the book); 75 "EVEROURE #EV9329-52" (remark column) vs Everpure High Flow CSR Twin 7FC, part EV9329-72; 104 EV9329-52 vs book page stamped "Item #104" = Atosa MGF8401GR undercounter refrigerator (unrelated); 80 ENDURO #250 vs Cornelius 0528452 Enduro 250 (same product). Amp differences K2.0 vs cut sheet: 4 (6.0 vs 3 A), 22 (4.0 vs 4.5 A), 53 (5.0 vs 2.3 A), 78 (2.1 vs 4.2 A), 98 (20.0 vs 24 A at 208/3), 35 (10.6 A at 208 V vs 11.0 A at 200 V / 10.0 A at 220 V).

## 5. Readability

All 106 K2.0 rows were legible in the 200-dpi crops of K_p04 (tiles t01/t02 for rows 1-57, t11/t12 for rows 58-106). Nothing had to be guessed; the following are limits of the drawing, not of the scan:
- Description cells clipped by the column width on K2.0 itself (K_p04_t01/t11): 14 "A.O. SMITH #BTH250 (100 GAL", 25 "REFRIGERATED PIZZA TAB", 27 "CONVEYOR OVEN (VENTLE", 47 "6 O.B. RANGE W/CONV. OV", 55 "FIRE SUPPRESSION SYSTE", 78 "SLIDING DOOR REFRIGERA", 88 "THREE COMPARTMENT SIN", 102 "REFRIGERATOR/HTD. CAB". The CSV keeps the printed text and marks "(clipped on K2.0)".
- Electrical amps printed as "*" (value not given) on K_p04_t02/t12: 6 floor mixer (208 V), 9 refrigeration system (208 V), 12 freezer coil (208 V), 57 exhaust fan system (208 V 3 ph), 76 ice machine (120 V), 97 Type II hood (120 V). K8.2 (K13_p01) supplies MCA for 9 and 12; nothing supplies 6, 57, 76, 97.
- Placeholder models: 1 MQ21XXQ, 10 and 13 MQ18XXG, 36 14XXFG (XX = length). Model without manufacturer: 102 RDH132WUT-HHS. Make "AIRCOOLER" (7, 8, 9, 11, 12) vs Arctic on K8.0-K8.3. Item 46 model cell is highlighted yellow on the sheet ("RATIONAL #I COMBI CLASSIC", size not given).
- Typos as printed: 75 "EVEROURE", 104 "FOR ITEM !03 & 105", K4.0 title "EQUIPMENT WLECTRICAL PLAN".
- Cut sheet text layer: Atosa dimension strings are partly garbled (fractions lost), e.g. item 5 "51 x31 x81"; Wells TMPT (item 40) ratings row not legible in text; Hoshizaki p104 is metric/export data. Not re-read from images.

## 6. Utilities summary (K2.0 readable values only; arithmetic in `scripts/utility_totals.txt`)

Electrical, per K2.0 amps column, lines with a number only ("*" lines excluded):
- 120 V 1-ph: 33 lines. As listed 231.5 A. Extended by scheduled qty: 6.0 + 3.2 + 5.0 + 3.0 + 3.0 + 11.8 + 12.0 + 4.0 + 2.8 + 16.0x3 + 11.8x2 + 2.3 + 2.3 + 2.8 + 11.8 + 15.0 + 5.0 + 2.3 + 5.0 + 15.1 + 20.0 + 6.0 + 2.0x3 + 5.0x3 + 10.6 + 2.1x2 + 2.1 + 5.0 + 6.0 + 13.8 + 2.1 + 6.0 + 10.6 = **291.4 A** = 291.4 x 0.120 = **35.0 kVA**.
- 208 V 1-ph: 4 lines (27, 35 x3, 82, 102). As listed 70.8 A; extended 26.0 + 10.6x3 + 23.2 + 11.0 = **92.0 A** = 92.0 x 0.208 = **19.1 kVA**. Item 27 is a double stack with "each deck requires separate circuit" but only one 26.0 A value is printed; if both decks draw 26 A the 208 V 1-ph figure rises by 26.0 A.
- 208 V 3-ph: item 98 dishmachine 20.0 A = 20 x 208 x 1.732 / 1000 = **7.2 kVA**; item 46 combi printed as **10.8 kW** (each deck, qty 1) = 10,800 / (208 x 1.732) = 30.0 A.
- Total connected, readable lines: 35.0 + 19.1 + 7.2 kVA + 10.8 kW = **~72.1 kVA/kW** (kVA and kW added as printed; no power factor applied).
- Not included (no value on K2.0): 6, 9, 12, 57, 76, 97. From K8.2 instead: cooler C/U 208-230/1/60 MCA 15; freezer C/U 208-230/1/60 MCA 15; freezer coil 208-230/1/60 MCA 15; cooler coil 115/1/60 MCA 20 (the schedule's 3.0 A for item 8). From K8.3: walk-in lights 120 V/60/1 on a 15 A circuit. Hood lights: 3 + 3 recessed round LED (K7.0) on item 56's 6.0 A line.
- Circuits called out: 28 heated cabinets 20 A service each (cut sheet), 54 NEMA 5-20P, 68 POS dedicated isolated-ground circuits x3, 55 fire system uninterrupted service, 27 two circuits.

Gas (K2.0 MBTU column, all 3/4 in connections):
- As listed per line: 250 (14, existing heater) + 198 (47) + 43 (48) + 105 (49) + 75 (51) + 102 (52) = 773 MBTU.
- Extended by qty: 250 + 198 + 43 + 105 + 75 + 102x2 = 875 MBTU.
- **New cooking equipment only: 198 + 43 + 105 + 75 + 102 x 2 = 625 MBTU/h** (6 appliance connections, 4 marked W/QUICK DISCONNECT: 47, 49, 51, 52). Existing water heater 250 MBTU on the roof stays.

Waste:
- Indirect waste (I.W. column): 18 lines; extended by qty **22 connections**: 1 x 3/4 in (14, existing heater), 15 x 1 in (8, 12, 62, 65 x3, 67 x2, 73, 74, 76, 77, 80, 105, 106), 5 x 1-1/2 in (17, 63 x2, 71, 100), 1 x 2 in (98). **New indirect waste connections excluding the existing heater: 21**, all "EXTEND I.W. TO F.S." (floor sinks per K3.0 / plumbing contract; floor sink count belongs to the P-sheet takeoff).
- Direct waste: 5 lines, 6 connections: 19 mop sink 2 in and 22 interceptor 4 in (trap below floor), 31 hand sinks 1-1/2 in x2, 93 hand sink 1-1/2 in, 88 three-compartment sink 2 in DIRECT WASTE TO ITEM #22.
- Water: HW+CW pairs 1/2 in at 17, 20, 31 x2, 63 x2, 71, 90, 91, 93, 99 (11 pairs); CW only 1/2 in at 45, 66 x3, 73, 75, 80, 82, 83, 103, 104, 105 (12); HW 3/4 in at 98; CW 1-1/2 in at 14 (existing).

Exhaust (K7.0): Type I hood 1 = 2,773 + 1,819 = 4,592 CFM at 275/225 CFM/ft; Type II hood 2 = 600 CFM. Make-up air not stated on the K-sheets.

## 7. Questions for the kitchen consultant (Fred Schmid & Associates)

1. K2.0 has no furnished-by / installed-by columns and no K.E.C./G.C. symbols although the legend and KN notes 12/23 refer to them. Please issue the F/I split (KEC furnish + install, KEC furnish / GC install, owner, vendor) for all 95 items.
2. Mezzanine prep-bar equipment (A-5.20 tags Q-270, 18-53C, TBB-24GAL-72, 32-ST, sinks; A-2.20 keynote 27; P-6 calc "bar triple sink", "glass washer", "18 x 18 2-comp sink") is not on K2.0 "1st level". Will a 2nd-level K schedule be issued, or is the mezzanine bar outside the KEC package?
3. Items 102-106 "FOR 2ND LEVEL": K1.0 places them on the first floor south of the scullery (by the dumbwaiter). Confirm location and what 102 (RDH132WUT-HHS, no manufacturer, no cut sheet) is.
4. Make "AIRCOOLER" on items 7-12 vs Arctic drawings Q228534 (K8.0-K8.3): which manufacturer is specified, and are the Russell R-454A outdoor condensing units (K8.2) in the KEC package together with the roof platform, line sets and A2L leak detection?
5. Item 57 exhaust fan system "SEE HOOD DRAWINGS": K7.0/K7.1 carry no exhaust fan, MUA unit or utility-cabinet fan data (electrical 208 V 3 ph "*"). Please provide the CaptiveAire fan/MUA schedule or confirm it is on the M-sheets and in the mechanical package.
6. Item 55 fire suppression: K7.0 shows a 4.0/4.0/4.0 gal tank system in a 60 in wall-mount utility cabinet "to be hung by others". Confirm gas valve, remote pull station (KD detail) and shunt-trip/contactors scope split (KEC vs EC vs plumber).
7. Model/part mismatches between K2.0 and the cut sheet book: 1, 36, 45, 52, 63 (-TR trash chute), 67 (TSD21 vs TSF21DB), 73/105 (KM-520MAJ vs export KM-520MAJ-E sheet), 75/104 (EV9329-52 vs EV9329-72; "Item #104" page is an Atosa MGF8401GR). Which governs?
8. Item 46 Rational iCombi Classic (existing relocated, cell highlighted on K2.0): size/model, and water/drain requirements (K2.0 plumbing blank; K3.0 shows two +68 in rough-ins).
9. Item 98 CMA-180C: built-in booster or external (K0.0 note U says booster +180 F)? The cut sheet gives 208/3 24 A without booster or 208/1 78 A with booster; K2.0 says 208/3 20 A.
10. Item 27 Ovention S1200 double stack: two 26 A circuits (one per deck) confirmed?
11. Item 95 slant rack shelf: scheduled 1, drawn twice (scullery and back bar).
12. Item 22 Big Dipper W-350-IS: K2.0 4 in waste vs 3 in inlet/outlet on the cut sheet; K3.0 note "VFY. W/ PLUMBER".
13. Items 6, 76, 97: electrical loads not given ("*"); 76 has no CW entry although 75 says it feeds 73 and 76.
14. Custom stainless items (16, 33, 34, 38, 39, 41, 58, 61, 84, 94, 100, 101): no dimensions on the K-sheets - shop drawings or lengths needed for the fabrication quotes.
15. Items 19 (mop sink) and 31/71 (hand sinks): K0.0 notes J and L word them as GC / KEC scope respectively - confirm against the KEC package.
16. Item 2 lockers (5, existing relocated) and item 1 shelving in the "EXISTING STORAGE AREA": is the storage area inside the TI scope?

## 8. Division mapping used in the CSV

11 40 00 general (68 POS, 102 unidentified); 11 41 00 food storage (shelving, walk-ins, remote refrigeration, reach-ins, refrigerated tables and bases, pot rack); 11 42 00 food preparation (slicer, stand, mixer, processor, prep/work tables and counters, overshelves); 11 44 00 food cooking (ranges, griddle, charbroiler, cheesemelter, fryers, combi + filter, conveyor oven, heated cabinets, heat lamps, hot well, fry dump); 11 46 00 food dispensing / bar (Perlick underbar, bar top, soda, coffee/tea, back-bar counter, trash cans); 11 47 00 ice machines, bins and their filters; 11 48 00 cleaning and disposal (dishmachine, dishtables, sinks, faucets, mop sink, interceptor, rack shelf, dollies); 23 38 13 commercial kitchen hoods (hoods, fan lot, wall flashing); 21 23 00 wet-chemical fire-extinguishing system; 22 34 00 existing gas water heater; 10 51 13 lockers; 27 15 00 POS communication cabling.
