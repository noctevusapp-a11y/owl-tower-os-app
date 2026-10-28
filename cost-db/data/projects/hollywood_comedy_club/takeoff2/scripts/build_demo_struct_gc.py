#!/usr/bin/env python3
"""Build takeoff2/demo_struct_gc.csv (demolition D-, structural S-, exit stair X-,
general conditions G-) for the Hollywood Comedy Club TI.

Every number below is either read from a document (cited in qty_source) or
computed here from such numbers (arithmetic shown in qty_source / notes).

Scale calibrations used
- Vector demo plans 03_Architectural_Plans_Demo_RCP.pdf p2 (A-1.10) / p3 (A-1.20):
  3/16" = 1'-0" -> 13.5 pt/ft. Checked: the "4'" dimension line on p3 measures
  54.0 pt (= 4.00 ft) and "21'-9 1/2"" on p4 measures 294.3 pt (= 21.80 ft).
  Dashed demo linework was chained with scripts/demo_chains.py and paired into
  double-line walls with scripts/demo_walls.py (chains_p*.csv, walls_p*.csv).
- Vector exit-stair A-2.10 (2604-260626-Exit_Stairs-PC_Submittal1.pdf p3):
  3/16" = 1'-0" -> 13.5 pt/ft; the 3'-0" door leaves measure 40.5 pt (= 3.00 ft).
- Raster S-2.10 / S-2.20 (kelly_img TI_p32-09 / -10, 110 dpi, 3/16" scale):
  20.625 px/ft. Checked: column bays 16.8 / 24.0 ft on the raster vs 16.4 /
  24.4 ft on the vector A-1.10.
"""
import csv, math, os

OUT = os.path.join(os.path.dirname(__file__), "..", "demo_struct_gc.csv")
DEMO = "03_Architectural_Plans_Demo_RCP.pdf"
TI6 = "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part06_p0011-0031.pdf"
TI7 = "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part07_p0032-0043.pdf"
XS = "2604-260626-Exit_Stairs-PC_Submittal1.pdf"
XC = "thatzhilariousstairSEcalcs260622.pdf (images STAIR_CALC-1..8)"
PT = 13.5  # pt/ft at 3/16" scale
PX = 20.625  # px/ft at 3/16" scale, 110 dpi

rows = []
def add(item_id, bli, div, desc, spec, qty, unit, basis, src, fb, ib, notes):
    if isinstance(qty, float):
        qty = round(qty, 2)
    rows.append(dict(item_id=item_id, bid_letter_item=bli, division=div, description=desc, spec_or_model=spec,
                     qty=qty, unit=unit, qty_basis=basis, qty_source=src, furnished_by=fb, installed_by=ib, notes=notes))

GC, SUB = "GC", "GC/demolition sub"
NQ = "not_quantifiable"

# ---------------------------------------------------------------- DEMOLITION
D = "Demolition"
# walk-in boxes (double dashed 4-in lines) on A-1.10, page coordinates in pt (unrotated)
boxA_w = (732 - 624) / PT; boxA_l = (771 - 571) / PT      # W10/W11 x W32-W54/W14-W33
boxC_w = 5.79; boxC_l = 5.59                                  # closed rectangle at display (680,977)
boxB_w = (1030 - 864) / PT; boxB_l = (770 - 571) / PT     # W13/W12 x W7/W8 (untagged)
add("D-01", D, "02 41 19", "Remove (E) walk-in coolers/freezers (KN4) - two dashed double-line (4 in panel) enclosures tagged KN4 in the (E) kitchen",
    "", 2, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN4 tags x2 at the enclosures; enclosure A {boxA_w:.1f} x {boxA_l:.1f} ft (walls W10/W11/W14/W32 of walls_p2.csv: x 624-732 pt, y 571-771 pt at 13.5 pt/ft), enclosure C {boxC_w:.2f} x {boxC_l:.2f} ft (closed rectangle, demo_rects.py)",
    "", SUB, f"Floor areas {boxA_w*boxA_l:.0f} SF and {boxC_w*boxC_l:.0f} SF. Refrigeration disconnect by trades. Z-check: enclosure A contains two floor-sink symbols and a dashed door swing")
add("D-02", D, "02 41 19", "Remove untagged dashed double-line enclosure in the (E) kitchen (walk-in or equipment enclosure)",
    "", 1, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) walls W13/W12/W7/W8 (walls_p2.csv): x 864-1030 pt, y 571-770 pt -> {boxB_w:.1f} x {boxB_l:.1f} ft = {boxB_w*boxB_l:.0f} SF",
    "", SUB, "No keynote tag on this enclosure; drawn in the demo (dashed) linetype - RFI whether it is a walk-in (KN4) or a partition")
add("D-03", D, "11 40 00", "Remove (E) kitchen equipment (KN4) - cooking line, tables, sinks, refrigeration, (E) water heater",
    "", "", "EA", NQ,
    f"{DEMO} p2 (A-1.10) KN4 'kitchen equipment & walk ins to be removed'; equipment drawn as dashed open outlines without an item schedule (demo_rects.py found no further closed outlines); ACCO findings p2 lists only the (E) gas water heater Bradford White BWCV0400",
    "", SUB, "Count not derivable; K-sheets show NEW equipment only (not demo). Gas/water/waste disconnects by trades")
add("D-04", D, "23 38 13", "Remove (E) kitchen exhaust hood (KN5) with duct connection",
    "", 1, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN5 tag x1 at display (1175,420) beside dashed outline W0 (walls_p2.csv) 23.1-26.7 ft long",
    "", SUB, "Hood length not dimensioned; the adjacent dashed double line is 23.06 ft on one face and 26.68 ft on the other")
bar_w = (1686 - 1512) / PT; bar_l = (714 - 442) / PT
chamfer = math.hypot(1553 - 1512, 714 - 631) / PT
bar_perim = bar_w + 2 * (631 - 442) / PT + 2 * chamfer + 7.04
bar_area = bar_w * bar_l - 2 * 0.5 * ((1553 - 1512) / PT) * ((714 - 631) / PT)
add("D-05", D, "06 05 05", "Remove (E) bar: die wall, back bar and bar top (KN8)",
    "", bar_perim, "LF", "inferred (arithmetic shown)",
    f"{DEMO} p2 (A-1.10) KN8; outer dashed outline (walls_p2.csv W5, W19, W24/W25, W40, chains c976, c1390, c1391): width (1686-1512)/13.5 = {bar_w:.1f} ft, length (714-442)/13.5 = {bar_l:.1f} ft, chamfered front corners {chamfer:.2f} ft each; perimeter = {bar_w:.1f} + 2 x {(631-442)/PT:.1f} + 2 x {chamfer:.2f} + 7.04 = {bar_perim:.1f} LF",
    "", SUB, f"Footprint {bar_area:.0f} SF (rectangle {bar_w:.1f} x {bar_l:.1f} less two chamfer triangles). Back bar run W19 = 9.33 ft is part of the perimeter")
add("D-06", D, "22 05 05", "Remove (E) bar equipment and bar plumbing utilities (KN8); (E) lines to remain where they cannot be removed (KN22)",
    "", "", "LS", NQ,
    f"{DEMO} p2 (A-1.10) KN8, KN22; ACCO findings p1: bar basement waste lines ~90% already ABS, tie to a 4 in POC; equipment count not drawn",
    "", SUB, "")
add("D-07", D, "02 41 19", "Remove (E) decorative non-bearing walls around structural concrete columns (KN9 first floor, KN7 mezzanine)",
    "", 5, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN9 tags x2 (+TYP.) at display (1770,676), (1540,1204); p3 (A-1.20) KN7 tags x3 (+TYP.) at (976,770), (1236,526), (1759,676); dashed enclosure linework found on 3 sides of columns (1272,311) p2 and (1272,1020) p3: 2.6-3.7 ft sides (demo chains ids 243/296/839 and 233/760/777)",
    "", SUB, "Enclosure about 3 ft square around 34-37 in octagonal columns (column symbol size from the vector). 'TYP.' on both tags: the owner should confirm whether all 17 (L1) / 18 (mezz) columns in the tenant area are enclosed (RFI). Height not stated")
ramp_w = (1356 - 1296) / PT; ramp_l = 15.0
add("D-08", D, "02 41 19", "Remove (E) ramp (KN10)",
    "", ramp_w * ramp_l, "SF", "inferred (arithmetic shown)",
    f"{DEMO} p2 (A-1.10) KN10 at display (1377,978); dashed outline walls_p2.csv W1 (15.48 ft, x=1356 pt) and W2/W3 (15.0 ft, x=1296-1298 pt): width (1356-1296)/13.5 = {ramp_w:.2f} ft x length 15.0 ft = {ramp_w*ramp_l:.1f} SF",
    "", SUB, "Ramp construction (concrete vs framed) and height not stated. The lower slab left after removal is filled per the '(N) 2,500 psi concrete fill at lower slab, 4 in, verify depth in field' detail on TI p36 (A-9.10) - thickness V.I.F.")
add("D-09", D, "02 41 19", "Remove (E) curved stair to mezzanine (KN11 / KN8 mezzanine)",
    "", 1, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN11 tag at display (1377,843) at the curved 'STAIR UP'; p3 (A-1.20) KN8 at (1246,770)",
    "", SUB, "A second KN11 tag at display (1540,1076) sits at the short 'STAIR UP' (3.84 ft runs) at the raised platform - counted with D-10. Stair size not dimensioned")
plat_l = (1748 - 1294) / PT; plat_d = (1244 - 1176) / PT
add("D-10", D, "06 05 05", "Remove (E) raised platform with its steps (KN12)",
    "", plat_l * plat_d, "SF", "inferred (arithmetic shown)",
    f"{DEMO} p2 (A-1.10) KN12 at display (1540,1140); dashed outline extents along the south wall: x 1294-1748 pt = {plat_l:.1f} ft (chains c1249/c1250/c1251 at y=1224 and c1271/c1272 at y=1244), depth y 1176-1244 pt = {plat_d:.1f} ft (chains c1191/c1192/c1197 at y=1176)",
    "", SUB, "Platform height and construction not stated")
add("D-11", D, "12 60 00", "Remove (E) booths (KN12)",
    "", 5, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) demo_rects.py: five closed dashed rectangles 2.50 x 4.00 ft at display y=1209 (x 1321, 1394, 1491, 1582, 1679)",
    "", SUB, "")
add("D-12", D, "08 05 05", "Remove (E) window: two panels of glass and frame at the Hollywood Blvd bay for the new exit door (KN13 first floor / KN9 mezzanine; A-4.01 KN13)",
    "", 2, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN13 'two panels of window glass & frame'; p3 (A-1.20) KN9; p8 (A-4.01) KN13 dashed box on elevation 1 (1/8 in scale = 9 pt/ft): 54.1 pt = 6.0 ft wide",
    "", SUB, "Panel heights not dimensioned (A-7.10 window types sheet, TI p33, not read - raster tiles). Granite base at this bay salvaged and reset (A-4.01 KN8) - LF not dimensioned")
add("D-13", D, "08 05 05", "Remove (E) doors (KN19 first floor x2, KN12 mezzanine x3)",
    "", 5, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN19 tags at display (677,239), (785,795); p3 (A-1.20) KN12 tags at (877,423), (877,770), (1236,660); door swing arc at KN19#2 radius 35.5 in (vec_survey arcs)",
    "", SUB, "Sizes not scheduled; one swing scales to a 3'-0\" leaf")
diag_ft = 43.42
add("D-14", D, "02 41 13", "Saw-cut and remove (E) concrete slab for the new 4 in sanitary main through the kitchen (KN6 / KN16) and patch per 6/A-9.10",
    "4 in slab 2,500 psi, #4 @ 16 in o.c. E.W., #4 dowels 8 in @ 16 in o.c. grouted into the (E) slab, 10-mil Stego vapor barrier, 2 in sand bed, backfill compacted to 90%",
    diag_ft, "LF", "drawn",
    f"{DEMO} p2 (A-1.10) KN16 dashed diagonal (chains 1310, 1329, 1332 at 133 deg, collinear extent 586 pt / 13.5 = {diag_ft:.1f} ft); patch detail 6 'UTILITY TRENCH PATCH' on {TI7} p5 (TI p36, A-9.10); P-3 (Addendum 2) 'GC to patch & repair (E) concrete floor where new plumbing lines occur'",
    "", SUB, "Trench width not dimensioned (detail shows 1'-0\" min lap only); slab thickness 'match (E) slab depth' V.I.F.; ACCO: kitchen is slab-on-grade (square floor sinks), round floor sinks are over the basement")
add("D-15", D, "02 41 13", "Saw-cut and remove (E) concrete slab for branch waste lines, floor sinks and floor drains in the kitchen (KN6 x2) and patch per 6/A-9.10",
    "", "", "LF", NQ,
    f"{DEMO} p2 (A-1.10) KN6 tags x2; branch runs only on ADD2 P-3 (raster, kelly_img ADD2_P-3): 4 in SAN (27, 35, 19, 26, 33, 68, 73, 12 DFU), 3 in SAN (12, 3, 4 DFU), 2 in SAN (5 WSFU, 3, 2, 1, 7, 5 DFU), 2 in V.U.F. x3 - lengths not dimensioned",
    "", SUB, "Measure from the plumbing takeoff once P-3 is scaled; KN6 says 'as required where (N) floor drain & sinks trenching require'")
add("D-16", D, "02 41 13", "Abandon and infill (E) floor sinks, floor drains and the (E) trench drain (P-3 'INFILL F.S.' / 'INFILL F.D.' / 'INFILL TRENCH DRAIN')",
    "", 7, "EA", "drawn",
    "ADD2 P-3 (kelly_img ADD2_P-3, raster): INFILL TRENCH DRAIN x1 (walk-in), INFILL F.D. x2, INFILL F.S. x4; also 'ABANDON EXISTING MAIN SANITARY WASTE LINE THROUGH KITCHEN'",
    "", SUB, "Raster count at 110 dpi; infill per 7/A-9.10 'SLAB IN FILL' (expanded metal lath) on TI p36")
dw_a = (4 + 2 / 12) * 4.0
add("D-17", D, "02 41 13", "Saw-cut and remove (E) mezzanine concrete floor for the dumbwaiter (A-1.20 KN6; A-6.30 KN1)",
    "", dw_a, "SF", "drawn",
    f"{TI7} p1 (A-6.30) demo plan: dashed boundary 4'-2\" x 4'-0\" = {dw_a:.2f} SF, 6 in V.I.F. from the (E) wall, 6'-2\" V.I.F. to the column; {DEMO} p3 (A-1.20) KN6 dims 4'-8\" x 4' (= 18.67 SF)",
    "", SUB, "Conflict: A-1.20 shows 4'-8\" x 4'-0\", A-6.30 shows 4'-2\" x 4'-0\" (larger-scale sheet used per A-0.11 note 9). (E) slab is a concrete waffle slab (A-6.30), thickness not stated")
add("D-18", D, "02 41 13", "Remove (E) mezzanine concrete floor for the dishwasher exhaust (A-1.20 KN18)",
    "", "", "SF", NQ,
    f"{DEMO} p3 (A-1.20) keynote 18 in the legend; no '18' tag found in the plan area of the text layer (tag census, scripts/sheet_overlay.py); size not stated",
    "", SUB, "unreadable on image TI_p11-04 (tag not located)")
add("D-19", D, "03 01 30", "Fill (E) core-drilled floor opening for ductwork (A-1.20 KN19)",
    "", 1, "EA", "drawn",
    f"{DEMO} p3 (A-1.20) KN19 tag at display (976,578)",
    "", SUB, "Opening size not stated; infill detail 7/A-9.10 'SLAB IN FILL' (TI p36)")
coffers = [(19.90, 11.92), (7.39, 11.92), (19.90, 11.36), (7.39, 11.36), (19.90, 9.35), (7.39, 9.35)]
cof_area = sum(a * b for a, b in coffers); cof_perim = sum(2 * (a + b) for a, b in coffers)
add("D-20", D, "09 05 05", "Remove (E) ceiling coffers and mouldings in their entirety and expose the (E) structural ceiling beams (A-1.20 KN14), mezzanine room 21",
    "", cof_area, "SF", "inferred (arithmetic shown)",
    f"{DEMO} p3 (A-1.20) KN14; six nested dashed rectangles (demo_rects.py, outer lines): 19.90 x 11.92, 7.39 x 11.92, 19.90 x 11.36, 7.39 x 11.36, 19.90 x 9.35, 7.39 x 9.35 ft = {cof_area:.1f} SF",
    "", SUB, f"Outer moulding perimeter {cof_perim:.0f} LF; three nested lines per coffer (three moulding steps) = {3*cof_perim:.0f} LF of moulding lines max. Coffer material not stated. Room M-21 floor area in the prior estimate 1,088 SF")
add("D-21", D, "26 05 05", "Remove (E) light fixtures on the mezzanine ceiling (A-1.20 KN15)",
    "", 72, "EA", "drawn",
    f"{DEMO} p3 (A-1.20) KN15; 72 closed 6-in-diameter polygon symbols inside the coffer region (display x 1280-1770, y 320-1210), counted by scripts (closed polygons >= 6 segments, 2-9 pt bbox)",
    "", SUB, "Symbol count; fixture type not stated")
wall13 = 7.37 + 7.78
add("D-22", D, "02 41 19", "Remove (E) mezzanine wall tagged KN13 (west side, north of the exit-stair limit of work)",
    "", wall13, "LF", "drawn",
    f"{DEMO} p3 (A-1.20) KN13 at display (877,680); walls_p3.csv W10 (7.37 ft, x=836 pt, y 452-552) + W8 (7.78 ft, x=824 pt, y 587-692) = {wall13:.2f} LF; overall extent (692-452)/13.5 = 17.8 ft including a 2.6 ft gap",
    "", SUB, "Drawn face spacing 10.0 in (W10) and 5.0 in (W8). Height not stated; mezzanine floor-to-ceiling at the exit stair is 7'-6 1/2\" (A-6.11)")
add("D-23", D, "02 41 19", "Remove (E) shaft wall, mezzanine (A-1.20 KN4)",
    "", 13.38, "LF", "drawn",
    f"{DEMO} p3 (A-1.20) KN4 at display (1236,423); walls_p3.csv W2: 13.38 ft at x=1178 pt, y 348-529, face spacing 4.0 in",
    "", SUB, "Height not stated")
add("D-24", D, "02 41 19", "Dashed (demo linetype) double-line wall on A-1.20 inside the exit-stair limit of work, not tagged",
    "", 14.41, "LF", "drawn",
    f"{DEMO} p3 (A-1.20) walls_p3.csv W1: 14.41 ft at x=830 pt, y 725-920, face spacing 6.0 in; lies south of the 'EXIT STAIR ... PERMIT# 26016-10000-18605' limit line",
    "", SUB, "No keynote; the exit-stair A-2.10 demo mezzanine plan shows no wall removal here - RFI which permit removes it")
add("D-25", D, "02 41 19", "Expose (E) concrete columns, GC to patch and repair (A-1.10 KN18 +TYP., A-1.20 KN11)",
    "", 2, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN18 tag x1 at display (1689,814) with 'TYP.'; p3 (A-1.20) KN11 tag x1 at (976,526)",
    "", SUB, "Tag instances only; 'TYP.' not resolved to a column count (RFI). Finish per Addendum 1 '(E) concrete column, clean and seal' is in the finishes takeoff")
add("D-26", D, "09 66 00", "Patch and repair (E) terrazzo floor as required (A-1.10 KN14)",
    "", "", "SF", NQ,
    f"{DEMO} p2 (A-1.10) KN14 tag at display (1769,391); extent not shown",
    "", GC, "")
add("D-27", D, "26 05 05", "Remove all (E) J-boxes and (E) conduit in their entirety (A-1.10 / A-1.20 general note 2)",
    "", "", "LS", NQ,
    f"{DEMO} p2, p3 general note 2; E demolition plans not issued",
    "", "electrical sub", "Note only - 'in its entirety' on both levels")
pit_sf = (55.375 / 12) * (54.875 / 12); pit_cf = pit_sf * 3.5 / 12
add("D-28", D, "02 41 13", "Saw-cut (E) slab on grade and demolish partial concrete waffle floor for the ADA lift pit (A-6.20 KN1, A-6.21 KN6)",
    "", pit_sf, "SF", "inferred (arithmetic shown)",
    f"{TI6} p20 (A-6.21) KN2: minimum pit area clearance 55-3/8 x 54-7/8 in = {pit_sf:.2f} SF; demo section dim 3 1/2 in deep; p19 (A-6.20) KN1 '(E) concrete slab on grade to be cut'",
    "", SUB, f"Volume {pit_sf:.2f} SF x 3.5/12 ft = {pit_cf:.2f} CF = {pit_cf/27:.2f} CY; recompact backfill soil as required (A-6.21 KN11, A-9.10)")
add("D-29", D, "02 41 19", "Construction waste hauling with at least 65% diversion by a City of Los Angeles certified hauler (A-1.10 / A-1.20 general note 1)",
    "", "", "CY", NQ,
    f"{DEMO} p2, p3 general note 1; derivable volumes only: lift pit {pit_cf/27:.2f} CY (D-28); dumbwaiter opening {dw_a:.1f} SF x slab thickness (not stated); ramp {ramp_w*ramp_l:.0f} SF x thickness (not stated); coffers {cof_area:.0f} SF (material not stated); walls {wall13+13.38+14.41:.1f} LF x height (not stated); bar {bar_perim:.0f} LF",
    "", SUB, "Total CY not derivable - thicknesses and heights are not on the documents")

# ---------------------------------------------------------------- STRUCTURAL
S = "Other required scope"
r1 = 14 * 6.8125; t1 = 13 * 11; f1 = math.hypot(r1, t1) / 12
r2 = 2 * 6.8125; t2 = 1 * 11; f2 = math.hypot(r2, t2) / 12
add("S-01", S, "05 51 13", "Stair 1 (interior, level 1 to mezzanine): shop-fabricated steel stair, 16 risers @ 6-13/16 in, 14 treads @ 11 in, 3'-9\" wide, intermediate landing",
    "Treads 2 in lightweight concrete on 12 ga metal pan, round nosing 1/2 in max radius, LED riser strip (A-6.12)",
    16, "RISER", "drawn",
    f"{TI6} p16 (A-6.10): '14 RISERS @ 6 13/16\", 13 TREADS @ 11\"' + '2 RISERS @ 6 13/16\", 1 TREADS @ 11\"', width 3'-9\"; p18 (A-6.12) tread detail",
    "", "misc. metals sub", f"Total rise 16 x 6.8125 in = {16*6.8125:.1f} in = {16*6.8125/12:.2f} ft (level 1 to mezzanine)")
add("S-02", S, "05 12 23", "Stair 1 stringers C12x20.7 (both flights, 2 stringers)",
    "ASTM A36 channel (S-0.10)", 2 * (f1 + f2), "LF", "inferred (arithmetic shown)",
    f"{TI7} p9 (S-2.10) 'C12x20.7' x2 at stair 1; geometry from A-6.10: flight 1 sqrt({r1:.1f}^2 + {t1}^2)/12 = {f1:.2f} ft, flight 2 sqrt({r2:.2f}^2 + {t2}^2)/12 = {f2:.2f} ft; 2 x ({f1:.2f} + {f2:.2f}) = {2*(f1+f2):.1f} LF",
    "", "misc. metals sub", f"Weight {2*(f1+f2)*20.7:.0f} lb")
land_a = 4 + 4 / 12; land_b = 3.75
add("S-03", S, "05 12 23", "Stair 1 landing beams HSS8x4x1/4 (four sides of the landing)",
    "ASTM A500 Gr B (S-0.10)", 2 * (land_a + land_b), "LF", "inferred (arithmetic shown)",
    f"{TI7} p9 (S-2.10) 'HSS8x4x1/4' labels on the landing (three legible + fourth side at the column); landing 4'-4\" x 3'-9\" from {TI6} p16 (A-6.10) dims '4'-4\"' and '3'-9\"'; 2 x (4.33 + 3.75) = {2*(land_a+land_b):.1f} LF",
    "", "misc. metals sub", f"Weight at 19.0 lb/ft = {2*(land_a+land_b)*19.0:.0f} lb; stringer-to-column saddle plates per 3/S-3.10 of the exit-stair set are not repeated on the TI S-3.20 detail 5 (1/4 in plates at stringer ends)")
nj = math.ceil(land_b / (16 / 12)) + 1
add("S-04", S, "05 41 13", "Stair 1 landing framing 800S162-54 joists @ 16 in o.c. with 800T162-54 track and 3/4 in Cemco Sure-Board 200S-F decking",
    "#8x2 in screws @ 4 in o.c. B.N. / 12 in o.c. F.N. (S-2.10 note 3)", land_a * land_b, "SF", "inferred (arithmetic shown)",
    f"{TI7} p9 (S-2.10) '800S162-54 @ 16\" O.C. TYP. U.N.O.' and note 3; landing 4.33 x 3.75 ft = {land_a*land_b:.1f} SF; joists {nj} x 4.33 ft = {nj*land_a:.1f} LF",
    "", "framing sub", "")
post_h = 14 * 6.8125 / 12
add("S-05", S, "05 12 23", "Stair 1 landing posts HSS4x4x1/4",
    "ASTM A500 Gr B", 2 * post_h, "LF", "inferred (arithmetic shown)",
    f"{TI7} p12 (S-3.20) detail 5: two 'HSS4x POST PER PLAN'; p9 (S-2.10) 'HSS4x4x1/4' x2; height to the landing = 14 risers x 6.8125 in = {post_h*12:.1f} in = {post_h:.2f} ft; 2 x {post_h:.2f} = {2*post_h:.2f} LF",
    "", "misc. metals sub", "On S-2.10 the two HSS4x4x1/4 labels sit on diagonal lines at the landing corners (post vs. kicker brace - RFI); detail 5/S-3.20 shows vertical posts")
add("S-06", S, "05 05 23", "Stair 1 post base plates 9 x 9 x 3/8 in with (4) 1/2 in dia x 4 in embedded threaded rods, drill and epoxy (5A/S-3.20)",
    "Simpson SET-3G (ESR 4057) per S-0.10", 2, "EA", "drawn",
    f"{TI7} p12 (S-3.20) detail 5 and 5A: '9\"x9\"x3/8\" PL', '(4) 1/2\"o x 4\" EMB. THREADED ROD', 'DRILL + EPOXY, TYP.'",
    "", "misc. metals sub", "8 anchors total; continuous special inspection for epoxy anchors (S-0.10)")
pan_sf = 14 * (11 / 12) * 3.75
add("S-07", S, "03 31 13", "Stair 1 concrete-filled pan treads: 2 in lightweight concrete on 12 ga metal pans",
    "", pan_sf, "SF", "inferred (arithmetic shown)",
    f"{TI6} p18 (A-6.12) detail 3: '2\" LIGHTWEIGHT CONCRETE ON 12GA METAL PANEL, TYP.'; 14 treads x 11/12 ft x 3.75 ft = {pan_sf:.1f} SF",
    "", "misc. metals sub", f"Volume {pan_sf:.1f} x 2/12 = {pan_sf*2/12:.1f} CF = {pan_sf*2/12/27:.2f} CY; landing deck is Sure-Board per S-2.10 note 3 (not concrete)")
lift_h = 16 * 6.8125 / 12
add("S-08", S, "05 12 23", "ADA lift tieback posts HSS4x4x3/8 continuous, level 1 slab to the mezzanine box beam (A-6.21 KN3; 6/S-3.20)",
    "ASTM A500 Gr B", 2 * lift_h, "LF", "inferred (arithmetic shown)",
    f"{TI7} p10 (S-2.20) 'HSS4X4X3/8\" MIN CONT.' x2 at the lift; p9 (S-2.10) 'HSS4x4x3/8 MIN' x2; height taken as level 1 to mezzanine = 16 risers x 6.8125 in = {lift_h:.2f} ft (stair 1, A-6.10); 2 x {lift_h:.2f} = {2*lift_h:.1f} LF",
    "", "misc. metals sub", "Detail 6/S-3.20: 8 x 4 x 1/4 in base plate with (2) 1/2 in dia x 3 in embedded threaded rods, drill + epoxy (2 plates, 4 rods); 8x8x54mil plate with (12) #10 SMS and 2x2x54mil x 8 in angles with (3) #10 SMS per leg at the box beam (2 EA); tieback spacing '4'-0\" MAX'. Mezzanine-to-attic extension not dimensioned")
add("S-09", S, "03 30 00", "ADA lift pit base and '(N) structural beam below' at the lift (A-6.21 KN12 'see S-2.10')",
    "", "", "LS", NQ,
    f"{TI6} p20 (A-6.21) KN12; {TI7} p9 (S-2.10) shows only the two HSS4x4x3/8 tiebacks and detail 6/S-3.20 at the lift - no beam or pit slab detail; pit 3 1/2 in deep (A-6.21 section)",
    "", "concrete sub", "RFI: pit slab thickness/rebar and the 'structural beam below'")
bb54 = (2440 - 1900) / PX + (1600 - 745) / PX + (2800 - 1900) / PX
bb97 = (2440 - 2080) / PX
add("S-10", S, "05 41 13", "Mechanical attic / mezzanine opening box beams (2) 1000S200-54, typ. U.N.O. (S-2.20)",
    "Cemco 1000S200-54, galvanized or rust-inhibitive paint (S-0.10)", bb54, "LF", "inferred (arithmetic shown)",
    f"{TI7} p10 (S-2.20) '(2) 1000S200-54 BOX BEAM TYP. U.N.O.'; raster lines at 20.625 px/ft on TI_p32-10: y=745 px line x 1900-2440 = {(2440-1900)/PX:.1f} ft, x=2440 px line y 745-1600 = {(1600-745)/PX:.1f} ft, north line y=480 px x 1900-2800 = {(2800-1900)/PX:.1f} ft; sum {bb54:.1f} LF",
    "", "framing sub", "Box-beam to (E) concrete column saddles per 4/S-3.10 (1/8 in saddle plate, (4) 1/2 in dia x 4 in embedded threaded rods) at each column on these lines - count not legible at 110 dpi (five column symbols on the measured lines)")
add("S-11", S, "05 41 13", "Box beam (2) 1000S200-97 at the south edge of the mezzanine opening (S-2.20)",
    "Cemco 1000S200-97", bb97, "LF", "inferred (arithmetic shown)",
    f"{TI7} p10 (S-2.20) '(2) 1000S200-97 BOX BEAM' at y=1600 px, x 2080-2440 px = {bb97:.1f} ft at 20.625 px/ft",
    "", "framing sub", "")
attic_n = ((2800 - 1900) / PX) * ((745 - 480) / PX); attic_e = ((2800 - 2440) / PX) * ((1900 - 745) / PX)
attic = attic_n + attic_e
add("S-12", S, "05 41 13", "Mechanical attic floor framing 800S162-54 joists @ 16 in o.c. with 3/4 in Cemco Sure-Board 200S-F decking (S-2.20; A-4.15)",
    "#8x2 in screws @ 4 in o.c. B.N., 12 in o.c. F.N. (S-2.10/S-2.20 note 3)", attic, "SF", "inferred (arithmetic shown)",
    f"{TI7} p10 (S-2.20) joist-extent arrows at 20.625 px/ft: north band 900 x 265 px = {attic_n:.0f} SF + east band 360 x 1155 px = {attic_e:.0f} SF = {attic:.0f} SF",
    "", "framing sub", f"Joists at 16 in: north band {math.ceil(900/PX/(4/3))} x {265/PX:.1f} ft + east band {math.ceil(1155/PX/(4/3))} x {360/PX:.1f} ft = {math.ceil(900/PX/(4/3))*265/PX + math.ceil(1155/PX/(4/3))*360/PX:.0f} LF; edge details 1, 2, 3/S-3.10 and 1, 2, 3/S-3.20 (bent-plate joist hangers, 400T125-54 / 1000T162-54 tracks); 6 x 2-1/2 x 1/4 in bent plate at the guardrail edge (1/S-3.10) LF not dimensioned")
add("S-13", S, "05 12 23", "Dumbwaiter opening beams W10x22 (3) framed to the (E) Wx beams (S-2.20; 4/S-3.20; 5/S-3.10)",
    "ASTM A992 Gr 50; 2-hr SFRM applied directly on the steel (A-6.30)", 2 * 4.85 + 9.9, "LF", "inferred (arithmetic shown)",
    f"{TI7} p10 (S-2.20) 'W10x22' x3 at the dumbwaiter (raster crop x 880-1350, y 1280-1620 px): two at 100 px = {100/PX:.2f} ft, one at 205 px = {205/PX:.1f} ft at 20.625 px/ft",
    "", "misc. metals sub", f"Weight {(2*4.85+9.9)*22:.0f} lb; A-6.30 calls these '(N) 10\"x22\" STEEL BEAM; SEE STRUCTURAL (S-2.20)'. Connections per 4/S-3.20 (bolted clip to the (E) Wx beam)")
add("S-14", S, "05 05 23", "Dumbwaiter shaft stud-wall anchors: 1/2 in dia x 4 in embedded @ 24 in o.c. at the bottom track (5/S-3.10)",
    "", 8, "EA", "inferred (arithmetic shown)",
    f"{TI7} p11 (S-3.10) detail 5 '1/2\"o x 4\" EMB. @ 24\" O.C.'; shaft perimeter 2 x (4.17 + 4.0) = 16.3 ft (A-6.30) / 2 ft = 8 anchors per level",
    "", "framing sub", "Shaft walls (3-5/8 in 20 ga @ 16 in, 5/8 in Type X each side, 1-hr, 400T200-54 top / 400T125-54 bottom tracks) are in the interior-walls takeoff")
add("S-15", S, "05 41 13", "Sloped mezzanine floor for the exit-stair headroom clearance below (A-1.20 KN17)",
    "", (84 / PT) * (57 / PT), "SF", "drawn",
    f"{DEMO} p3 (A-1.20) KN17 'line of sloped floor for the stair headroom clearance below' at display (660,526); dashed outline 84 x 57 pt = {84/PT:.1f} x {57/PT:.1f} ft",
    "", "framing sub", "No structural detail on S-2.20 or the exit-stair S-sheets - RFI (construction and which permit)")
add("S-16", S, "05 41 13", "Headers / beams at new wall openings",
    "", "", "EA", NQ,
    f"{TI7} p7 (S-1.10) typical panel elevation (header 'D' per schedule); no header sizes or opening marks on S-2.10 / S-2.20",
    "", "framing sub", "Header configurations 'see detail' on TI p36 (A-9.10) - not read")
add("S-17", S, "05 41 13", "Sure-Board shear walls (S-1.10 schedule marks 1-4) with S/HDU4 / S/HDU6 holdowns",
    "", "", "LF", NQ,
    f"{TI7} p7 (S-1.10) shear wall schedule; S-2.10 / S-2.20 legend symbols - no marks legible on kelly_img TI_p32-09 / TI_p32-10",
    "", "framing sub", "unreadable on image TI_p32-09 / TI_p32-10 (110 dpi)")
add("S-18", S, "05 41 13", "New stud walls 400S162-54 @ 16 in o.c. 'typ. all walls' (S-2.10 / S-2.20 legend)",
    "362S162-54 @ 16 in o.c. typical studs with 362T200-54 tracks per the S-1.10 schedule", "", "LF", NQ,
    f"{TI7} p9, p10 legend; p7 (S-1.10) schedule; wall LF is carried in the interior-walls takeoff",
    "", "framing sub", "Conflict: S-2.10 legend says 400S162-54, S-1.10 schedule says 362S162-54 - RFI")

# ---------------------------------------------------------------- EXIT STAIR
X = "Stairs & railing"
rise = 11 * 6.5625; run = 10 * 11; slope = math.hypot(rise, run) / 12
add("X-01", X, "05 51 13", "Exit stair 2 (1704 N Vine): 1-hr rated steel stair, 11 risers @ 6-9/16 in, 10 treads @ 11 in, 5'-0\" wide, concrete-filled pan treads",
    "", 11, "RISER", "drawn",
    f"{XS} p5 (A-6.11) '11 RISERS @ 6 9/16\"', '10 TREADS @ 11\"', '9'-2\"', '6'-0\"'; p4 (A-6.10) '1 1/2\" | 5'-0\" | 1 1/2\"' between stringers; p2 (A-0.20) provided exit width 60 in",
    "", "misc. metals sub", f"Rise {rise:.1f} in, run {run} in, slope length {slope:.2f} ft")
add("X-02", X, "05 12 23", "Exit stair stringers C12x20.7 (2)",
    "ASTM A36 (S-0.10)", 2 * slope, "LF", "inferred (arithmetic shown)",
    f"{XS} p9 (S-2.10) 'C12x20.7' x2; {XC} STAIR_CALC-3/4 'STRINGER-1 ... USE C12x20.7', span 11.0 ft; geometry sqrt({rise:.1f}^2 + {run}^2)/12 = {slope:.2f} ft x 2 = {2*slope:.1f} LF",
    "", "misc. metals sub", f"Weight {2*slope*20.7:.0f} lb; 1/4 in end plates per 5/S-3.10")
pan2 = 10 * (11 / 12) * 5.0
add("X-03", X, "03 31 13", "Concrete fill in the exit-stair pan treads",
    "", pan2, "SF", "inferred (arithmetic shown)",
    f"10 treads x 11/12 ft x 5.0 ft width ({XS} p4 A-6.10) = {pan2:.1f} SF",
    "", "misc. metals sub", f"Fill depth not stated on the exit-stair sheets (TI stair 1 uses 2 in lightweight: at 2 in the volume is {pan2*2/12/27:.2f} CY). Concrete > 2,500 psi would need continuous special inspection (S-0.10)")
add("X-04", X, "05 12 23", "Exit-stair landing beams HSS8x4x1/4 (perimeter of the 5'-0\" x 4'-0\" landing)",
    "ASTM A500 Gr B", 2 * (5 + 4), "LF", "inferred (arithmetic shown)",
    f"{XS} p9 (S-2.10) 'HSS8x4x1/4' on four sides; landing 5'-0\" x 4'-0\" from p4 (A-6.10) dims '5'-0\"' (x=859,y=720) and '4'-0\"' (x=798,y=699); 2 x (5 + 4) = 18 LF; {XC} STAIR_CALC-3/6 'LANDING BEAM-1 ... 6 ft span, USE HSS8x4x1/4'",
    "", "misc. metals sub", "Calc span 6.0 ft vs. drawn 5.0 ft (A-6.10 also shows 6'-3\" outside the landing) - weight at 19.0 lb/ft = 342 lb for 18 LF")
add("X-05", X, "05 41 13", "Exit-stair landing framing 800C162-54 joists @ 16 in o.c. with 800T162-54 track and 3/4 in Sure-Board decking",
    "", 20.0, "SF", "inferred (arithmetic shown)",
    f"{XS} p9 (S-2.10) '800C162-54 @ 16\" O.C.', '800T162-54'; note 3 floor decking 3/4 in Cemco Sure-Board 200S-F; 5 x 4 ft = 20 SF; joists {math.ceil(4/(4/3))+1} x 5 ft = {(math.ceil(4/(4/3))+1)*5} LF",
    "", "framing sub", "")
add("X-06", X, "05 12 23", "Exit-stair landing posts HSS4x4x1/4 (2), floor to the +6'-0\" landing",
    "ASTM A500 Gr B", 12.0, "LF", "inferred (arithmetic shown)",
    f"{XS} p10 (S-3.10) detail 1 'HSS4x POST PER PLAN' and detail 4; p9 (S-2.10) two post symbols with 'HSS4x4x1/4'; landing '+6'-0\" A.F.F.' (p4 A-6.10); 2 x 6.0 = 12.0 LF",
    "", "misc. metals sub", "")
add("X-07", X, "05 05 23", "Exit-stair post base plates 8 x 8 x 1/4 in with (2) 1/2 in dia x 4 in embedded threaded rods (4/S-3.10)",
    "", 2, "EA", "drawn",
    f"{XS} p10 (S-3.10) detail 4: '8\"' x '8\"', '1/4\" THICK PLATE', '(2) 1/2\"o X 4\" EMB. THREADED ROD'; one per post (X-06)",
    "", "misc. metals sub", "4 rods")
add("X-08", X, "05 05 23", "Exit-stair stringer base plates 1'-0\" x 4 in x 1/4 in with (2) 1/2 in dia x 4 in embedded threaded rods (5/S-3.10)",
    "", 2, "EA", "inferred (arithmetic shown)",
    f"{XS} p10 (S-3.10) detail 5: '1'-0\"', '1/4\" THICK PLATE', '(2) 1/2\"o X 4\" EMB. THREADED ROD'; one per stringer at the (E) slab = 2",
    "", "misc. metals sub", "4 rods")
add("X-09", X, "05 05 23", "Exit-stair landing/stringer saddle plates at the (E) concrete column 8 x 8 x 1/4 in with (4) 1/2 in dia x 4 in embedded anchors (3/S-3.10)",
    "", 2, "EA", "drawn",
    f"{XS} p10 (S-3.10) detail 3 shows two '8x8x1/4\" PL W/ (4) 1/2\"ox4\" EMB. ANCHORS' at the column",
    "", "misc. metals sub", "8 anchors; total embedded 1/2 in rods/anchors on the exit stair = 4 + 4 + 8 = 16 (continuous special inspection, S-0.10)")
add("X-10", X, "05 51 13", "Steel enclosure parallel to the stringer closing the gap between the stringer and the (E) wall (A-6.10 KN8)",
    "", slope, "LF", "inferred (arithmetic shown)",
    f"{XS} p4 (A-6.10) KN8; length taken as the stringer slope length {slope:.2f} ft",
    "", "misc. metals sub", "Plate size not stated")
hr = 2 * (slope + 1.0 + (11 + 12) / 12)
add("X-11", X, "05 52 13", "1-1/2 in dia metal handrails both sides at 34-38 in with 12 in horizontal top extension and TW+12 in (1'-11\") sloped bottom extension (A-6.10/A-6.11 KN1, general notes 3)",
    "", hr, "LF", "inferred (arithmetic shown)",
    f"{XS} p5 (A-6.11) KN1, '1'-0\"', '1'-11\" TW + 12\"'; 2 x ({slope:.2f} + 1.0 + 1.917) = {hr:.2f} LF",
    "", "misc. metals sub", "Wall-mounted (stair between the (E) wall and the new 1-hr wall); returns to the wall per general note 3")
add("X-12", X, "05 52 13", "Guard at the exit-stair landing / open side",
    "", "", "LF", NQ,
    f"{XS} p4 (A-6.10) general notes 8-9 (guard requirements); plans show the stair enclosed by walls on both sides (KN4, KN6) and 'OPEN' at the mezzanine plan bottom; A-6.11 sections draw pickets below the handrail",
    "", "misc. metals sub", "RFI: picket guard vs. wall-mounted rail")
add("X-13", X, "09 91 23", "Visual warning strips 2-4 in wide at the top and bottom treads (A-6.10 KN2)",
    "", 2 * 5.0, "LF", "inferred (arithmetic shown)",
    f"{XS} p4 (A-6.10) KN2 and general note 7 (full width of the step); 2 strips x 5.0 ft = 10 LF",
    "", "misc. metals sub", "")
l1 = 6 + 4 / 12 + 14 + 11 / 12 + 11 + 10.5 / 12 + 5 + 3 / 12
mz = 6 + 4 / 12 + 14 + 11 / 12 + 11 + 10.5 / 12 + 5.5 + 12 + 7.5 / 12 + 5 + 11 / 12
h1 = 9 + 6.5 / 12; h2 = 7 + 6.5 / 12
add("X-14", X, "09 21 16", "Exit-stair 1-hr rated enclosure walls: 6 in 16 ga steel studs @ 16 in o.c., 5/8 in Type X GWB each side, 4 in acoustic insulation (UL U404), wall note 1",
    "UL Des U404; studs per S-2.10", l1 + mz, "LF", "drawn",
    f"{XS} p3 (A-2.10) wall tag 1 runs: level 1 6'-4\" + 14'-11\" + 11'-10 1/2\" + 5'-3\" = {l1:.2f} LF; mezzanine 6'-4\" + 14'-11\" + 11'-10 1/2\" + 5'-6\" + 12'-7 1/2\" + 5'-11\" = {mz:.2f} LF",
    "", "drywall sub", f"Heights p5 (A-6.11): level 1 9'-6 1/2\" V.I.F., mezzanine 7'-6 1/2\"; wall area {l1:.2f} x {h1:.3f} + {mz:.2f} x {h2:.3f} = {l1*h1 + mz*h2:.0f} SF; GWB both faces {2*(l1*h1+mz*h2):.0f} SF; insulation {l1*h1+mz*h2:.0f} SF")
add("X-15", X, "08 43 13", "New tempered-glass storefront exit doors (2) to match the (E) door, with panic hardware, self-closing device, accessible hardware, exterior weatherstripping and threshold (A-2.10 KN3 / A-6.10 KN10)",
    "3'-0\" leaves", 2, "EA", "drawn",
    f"{XS} p3 (A-2.10) proposed 1st floor plan: two '3'-0\"' door leaves (vector 40.5 pt each at 13.5 pt/ft) at x 287-327.5 and 390.5-431 pt; p1 (A-0.00) 'scope includes two new storefront exit doors'",
    "", "glazing sub", "Height to match (E): the (E) door scales 6.9 ft on the demo elevation (chain W2 6.92 ft). Door schedule A-7.10 of the exit-stair set not issued")
fg_w = (390.5 - 327.5) / PT
add("X-16", X, "08 43 13", "Fixed tempered insulated-glass storefront panel between the exit doors, matching the (E) storefront (A-2.10 KN4 / A-6.10 KN11)",
    "", fg_w * 6.92, "SF", "inferred (arithmetic shown)",
    f"{XS} p3 (A-2.10) width between the door jambs (390.5 - 327.5) pt / 13.5 = {fg_w:.2f} ft (4'-8\"); height taken as the (E) door 6.92 ft (demo elevation chain W2) -> {fg_w*6.92:.1f} SF",
    "", "glazing sub", "Bay width overall 287-431 pt = 10.67 ft (10'-8\"). Transom above remains")
add("X-17", X, "08 13 13", "1-hr fire-rated exit access door with panic hardware outside the rated stair shaft, mezzanine vestibule (A-2.10 KN5 / A-6.10 KN5)",
    "", 1, "EA", "drawn",
    f"{XS} p3 (A-2.10) KN5 tag at the mezzanine vestibule; p4 (A-6.10) KN5",
    "", "door sub", "Size per A-7.10 of the exit-stair set (not issued)")
add("X-18", X, "02 41 19", "Exit stair demolition: remove (E) exterior wall infill panels flanking the (E) storefront door (A-2.10 demo elevation KN1 x2)",
    "", 2, "EA", "drawn",
    f"{XS} p3 (A-2.10) existing/demo exterior elevation 3: KN1 '(E) wall to be removed' x2; panel widths 3.0 ft (vector 40.5 pt at y=1367.5) x heights 6.88 / 7.13 ft (chains W3, W0)",
    "", SUB, f"About 2 x 3.0 x 7.0 = 42 SF of (E) exterior plaster wall (KN6)")
add("X-19", X, "02 41 19", "Exit stair demolition: remove (E) glass storefront door (replaced in kind, KN2)",
    "", 1, "EA", "drawn",
    f"{XS} p3 (A-2.10) demo elevation KN2; opening width = bay 10.67 ft - 2 x 3.0 ft = {10.67-6:.2f} ft (inferred), height 6.92 ft",
    "", SUB, "")
add("X-20", X, "02 41 19", "Exit stair demolition: remove the (E) door access to the main building (not code compliant) and infill",
    "", 1, "EA", "drawn",
    f"{XS} p2 (A-0.20) note '(E) DOOR ACCESS TO MAIN BUILDING TO BE REMOVED DUE TO (E) DOOR IS NOT CODE COMPLIANT'",
    "", SUB, "Location, size and infill construction not detailed - RFI")
add("X-21", X, "32 16 23", "Sidewalk work at the 1704 N Vine exit doors",
    "", 0, "LS", "drawn",
    f"{XS} p3 (A-2.10) / p4 (A-6.10): no sidewalk, curb or step work shown; KN3 threshold at the bottom of the door only; p2 (A-0.20) site plan shows the (E) sidewalk",
    "", GC, "The 7 in terrazzo step, granite base reset and handrail on A-4.01 belong to the Hollywood Blvd exit bay of the TI (exterior finishes takeoff)")
add("X-22", X, "10 14 23", "Exit signs and egress signage for the new exit stair",
    "", "", "EA", NQ,
    f"{XS} p2 (A-0.20) exit analysis plans at 1/8 in: exit-sign symbols present (one legible at the mezzanine exit door on kelly_img STAIR-02); sign schedule not issued",
    "", "electrical sub", "unreadable on image STAIR-02 for the remaining symbols")
add("X-23", X, "09 96 00", "Finish paint / galvanizing of the exit-stair steel",
    "", "", "SF", NQ,
    f"{XS} p6 (S-0.10): structural steel cleaned of rust, loose mill scale and oil after fabrication; light-gage exterior studs galvanized, interior studs galvanized or manufacturer's rust-inhibitive paint; no finish paint specified on A-6.10/A-6.11",
    "", "painting sub", "RFI finish (the TI stair 1 calls P-6 on A-6.12)")

# --------------------------------------------------------- GENERAL CONDITIONS
G = "Other required scope"
A011 = "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part01_p0001-0003.pdf p2 (A-0.11) general notes"
add("G-01", G, "01 41 26", "TI building permit: plan-check submittal 1 (2604-260819) under CUP ZA-2024-6542-CUB; change of use restaurant to club/restaurant; minor exterior work",
    "", 1, "EA", "drawn",
    "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part01_p0001-0003.pdf p1 (A-0.00) permit description 1; permit application no. blank on the S-0.10 structural observation form",
    "owner/architect", GC, "Prior permits on record: C of O 29356 (2006), 000014-20001-05459, 09016-10000-04328, 09016-10001-04328, 13016-10000-15189")
add("G-02", G, "01 41 26", "Exit-stair permit 26016-10000-18605 (separate permit, 1704 N Vine), improvement area 202 SF",
    "", 1, "EA", "drawn",
    f"{DEMO} p2 (A-1.10) KN15; {XS} p2 (A-0.20) 'Improvement Area: 202 sq. ft.', 'Interior SF: 200'",
    "owner/architect", GC, "")
add("G-03", G, "01 41 26", "Mechanical, electrical, plumbing and fire-alarm permits pulled by others (A-0.00 permit description 2-5)",
    "", 0, "EA", "drawn",
    "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part01_p0001-0003.pdf p1 (A-0.00) items 2-5",
    "others", "others", "Excluded from the GC permit scope by the documents")
add("G-04", G, "01 41 26", "Modified fire-sprinkler and fire-life-safety plans submitted for review, approval and permit; no framing/T-bar approvals before Fire Department sprinkler approval",
    "", 1, "LS", "drawn",
    f"{A011} 81, 82; A-0.00 'Sprinklers: Yes - New NFPA-13' vs. A-0.21 'YES EXISTING, COMPLIANCE WITH NFPA-13'",
    "fire sprinkler sub", "fire sprinkler sub", "Conflict new vs. existing NFPA-13 system - RFI")
add("G-05", G, "01 41 26", "Cal/OSHA construction activity permit where required by CCR Title 8 sec. 341; separate permit for trenches/excavations 5 ft or deeper",
    "", "", "EA", NQ,
    f"{A011} 22, 22.1",
    "", GC, "Trench depths not stated (the sanitary trench D-14 is under a slab on grade)")
add("G-06", G, "01 41 26", "DIG-ALERT 811 notification before excavation; locate (E) underground utilities",
    "", 1, "LS", "drawn",
    f"{A011} 22.2, 31",
    "", GC, "")
add("G-07", G, "01 41 26", "Encroachment permit for any storage on public property; pedestrian protection and street improvement permit from the jurisdiction",
    "", "", "EA", NQ,
    f"{A011} 35, 39",
    "", GC, "Need depends on the GC's logistics plan (Hollywood Blvd / Vine St sidewalks, Walk of Fame)")
add("G-08", G, "01 35 91", "Historic constraints: Mills Act contract (Yes) and Historic Preservation Review (Yes); preserve the (E) stone facade, decorative stone and granite base; 7 in step at the new door to preserve structural integrity",
    "", 1, "LS", "drawn",
    f"{TI6} p2 (A-0.21) 'Mills Act Contract: Yes', 'Historic Preservation Review: Yes'; {XS} p2 (A-0.20) same; {DEMO} p8 (A-4.01) KN1, KN2, KN6, KN8, KN10",
    "", GC, "No HPOZ; no other designation listed. Protection extents not dimensioned")
add("G-09", G, "01 35 43", "CUP approval letter conditions ZA-2024-6542-CUB (A-0.19)",
    "", 1, "LS", "drawn",
    "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part05_p0010-0010.pdf p1 (A-0.19) conditions 45-54 (MViP monitoring fees, complaint log, indemnification, 'all terms and conditions shall be fulfilled before the use may be established')",
    "owner", "owner", "Operational conditions - no construction quantities")
add("G-10", G, "01 74 19", "Construction waste management: at least 65% diversion, City of Los Angeles certified hauler, LA Green Building Code; universal waste notes",
    "", 1, "LS", "drawn",
    f"{DEMO} p2/p3 general note 1; part02 p2 (A-0.13) L.A. City Green notes; part03 p1 (A-0.14) universal waste notes",
    "", GC, "Haul volume not derivable (D-29)")
add("G-11", G, "01 81 13", "Green building items called on the notes: MERV 13 filters before occupancy with O&M recommendations; high-efficiency fixtures; lead-free potable fittings (AB 1953); ultra-flush water closets; A-0.13 GRN 15 items",
    "", 1, "LS", "drawn",
    f"{A011} 71, 88, 89; A-5.11/A-5.12 'lead free per CA AB 1953'; A-0.13 GRN 15 #7, 8, 10-13, 17-20, 24-30 referenced",
    "", "MEP subs", "")
add("G-12", G, "01 71 23", "Field verification of existing conditions and dimensions before bidding and before fabrication; report discrepancies in writing",
    "", 1, "LS", "drawn",
    f"{A011} 3, 4, 45; {TI7} p6 (S-0.10) 'contractor shall verify and be responsible for all dimensions'; V.I.F. items: 9'-6 1/2\" wall height (A-6.11), 6 in / 6'-2\" dumbwaiter offsets (A-6.30), slab depths (A-9.10)",
    "", GC, "")
add("G-13", G, "01 33 23", "Shop drawings: structural steel by a LADBS-licensed fabricator, light-gage framing, Sure-Board, stairs, storefront; architect/engineer review 7 working days; contractor stamp before submission",
    "", "", "EA", NQ,
    f"{A011} 6; {TI7} p6 (S-0.10) general and 'LADBS LICENSED FABRICATOR IS REQUIRED FOR STRUCTURAL STEEL FABRICATION'; {XS} p6 (S-0.10) same",
    "", GC, "Package count not stated")
add("G-14", G, "01 45 33", "Special inspection: epoxy / expansion anchors and dowels (continuous) - both permits",
    "Simpson SET-3G (ESR 4057), Strong-Bolt 2 (ESR 3037)", 8 + 4 + 4 + 8 + 16, "EA", "inferred (arithmetic shown)",
    f"{TI7} p6 (S-0.10) statement of special inspection; anchors counted: stair 1 base plates 8 (S-06) + lift tiebacks 4 (S-08) + dumbwaiter track 8/level (S-14, one level) + box-beam column saddles 4 per column (count not legible) + exit stair 16 (X-07/08/09) = 40 listed; {XS} p6 (S-0.10) same statement",
    "", "deputy inspector (owner)", "Column-saddle anchors (4 each, 4/S-3.10) excluded from the count - column count not legible. Duration not stated in the documents")
add("G-15", G, "01 45 33", "Special inspection: structural concrete with f'c > 2,500 psi (continuous, test per code)",
    "", 0, "LS", "drawn",
    f"{TI7} p6 (S-0.10); the only new concrete specified is the 2,500 psi trench patch / slab fill (A-9.10), which does not exceed 2,500 psi; pan-fill strength not stated",
    "", "deputy inspector (owner)", "Becomes required if the pan fill or pit slab is specified above 2,500 psi - RFI")
add("G-16", G, "01 45 33", "Special inspection: Sure-Board floor sheathing (periodic); deputy inspection where fastener spacing is 4 in o.c. or less",
    "", attic + land_a * land_b + 20.0, "SF", "inferred (arithmetic shown)",
    f"{TI7} p6 (S-0.10); sheathed areas: attic {attic:.0f} SF (S-12) + stair 1 landing {land_a*land_b:.1f} SF (S-04) + exit-stair landing 20 SF (X-05); edge nailing is #8 @ 4 in o.c. B.N. (S-2.10 note 3) - at the 4 in threshold",
    "", "deputy inspector (owner)", "Duration not stated in the documents")
add("G-17", G, "01 45 33", "Special inspection: welding per AWS D1.1 (in-progress visual, Q.C.-1 certified inspectors) and high-strength bolting",
    "", "", "LS", NQ,
    f"{TI7} p6 (S-0.10) 'Inspection' list; {XS} p6 (S-0.10) same; field welds: stringer/landing/post connections (S-3.20 det. 5, S-3.10 det. 1-5), lift tiebacks, W10x22 clips",
    "", "deputy inspector (owner)", "Duration not stated in the documents")
add("G-18", G, "01 45 23", "Structural observation program (LADBS form): structural observer Charles Tan, S.E. (Calif. reg. S4758); items checked: Others - gage metal; one program per permit",
    "", 2, "EA", "drawn",
    f"{TI7} p6 (S-0.10) and {XS} p6 (S-0.10) LADBS 'Structural Observation Program' forms; statement of responsibility to the LADBS inspectors before starting the seismic-force-resisting system (CBC 1704.4)",
    "owner (engineer)", GC, "Observations do not replace the deputy inspections (S-0.10 general)")
add("G-19", G, "01 45 33", "Evidence of LA Research Reports / ICC listings kept at the site (Simpson anchors, Cemco studs LARR 25821, Sure-Board LARR 25461, S/HDU LARR 25720, Simpson drop-in LARR 25682, PDP pins LARR 25469)",
    "", 1, "LS", "drawn",
    f"{TI7} p6 (S-0.10) general; p7 (S-1.10) LARR numbers",
    "", GC, "")
add("G-20", G, "01 56 00", "Protection of existing work to remain: (E) terrazzo floor, (E) restrooms (no changes), (E) fire sprinkler riser cabinet, (E) sidewalks incl. the adjoining property (inspect before and repair after), (E) stone facade and granite base",
    "", 1, "LS", "drawn",
    f"{DEMO} p2 (A-1.10) KN7, KN14, KN17, KN20; {A011} 34; A-4.01 KN1/2/6; S-0.10 'contractor shall protect all work, materials and equipment from damage'",
    "", GC, "Extents not dimensioned")
add("G-21", G, "01 35 13", "Phasing / work inside the occupied 1704 N Vine restaurant (mezzanine dining room N.I.C., permit 09016-10000-04328, occupant load 90) and next to the (E) retail at 1708 N Vine (N.I.C., permit 21016-10000-00251); maintain all (E) life-safety provisions during construction",
    "", "", "WK", NQ,
    f"{XS} p2 (A-0.20) and p3 (A-2.10) 'LIMIT OF WORK', N.I.C. labels, 'OCCUPANCY NUMBER BASED ON LATEST PERMIT: 90'; {A011} 49a; the exit stair is required because the 2nd exit of the (E) mezzanine dining room has been blocked (A-6.11 note)",
    "", GC, "duration not stated in the documents")
add("G-22", G, "01 51 00", "Temporary facilities: water for dust control, pedestrian protection, temporary power/toilets/fencing",
    "", "", "WK", NQ,
    f"{A011} 36 (water for dust control), 39 (pedestrian protection permit); no other temporary facilities called out",
    "", GC, "duration not stated in the documents")
add("G-23", G, "01 74 13", "Regular rubbish removal for all trades; turn the site over vacuum-clean including the bathrooms",
    "", 7141, "SF", "drawn",
    f"{A011} 12; TI floor area 7,141 SF (A-0.00 'T.I. Floor Area'); exit stair 202 SF (A-0.20)",
    "", GC, "Daily clean-up: duration not stated in the documents")
add("G-24", G, "01 31 13", "Supervision, project management, scheduling and coordination",
    "", "", "WK", NQ,
    "No schedule, milestones or contract duration in the bid documents on hand",
    "", GC, "duration not stated in the documents")
add("G-25", G, "01 65 00", "Means, methods, sequencing; shores, braces and guys for construction loads; shoring systems designed and stamped by a California-licensed civil engineer",
    "", "", "LS", NQ,
    f"{TI7} p6 and {XS} p6 (S-0.10) general",
    "", GC, "Needed where (E) waffle floor is cut (dumbwaiter, lift pit) - not detailed")
add("G-26", G, "06 10 53", "Blocking, backing, hangers and supports for all fixtures, equipment, cabinetry and furnishings; fire-retardant wood blocking; backing plates 4 in 16 ga (TI p36 detail 5); backing for dumbwaiter rail brackets and theatrical lighting J-boxes",
    "", "", "LS", NQ,
    f"{A011} 14, 15, 16; A-6.30 KN9 'wall backing provided by general contractor'; A-4.15 'J-BOX; PROVIDE AS REQ'D FOR FUTURE THEATRICAL LIGHTING'",
    "", GC, "")
add("G-27", G, "01 35 23", "Insurance and licensing evidence (workers' compensation certificates, contractor's license)",
    "", 1, "LS", "drawn",
    f"{A011} 51, 52",
    "", GC, "")
add("G-28", G, "02 82 00", "Hazardous materials survey / abatement",
    "", "", "LS", NQ,
    "Not mentioned in any bid document on hand",
    "", "", "Owner to state - no document requires it")
add("G-29", G, "01 41 00", "Code data for the GC's compliance: Type IA, A-2, 12 stories plus 2 mezzanine levels, occupant load 319 (TI) / 90 (1704 Vine restaurant), 2025 LABC/CBC/CPC/CMC/CEC/CGBC",
    "", 1, "LS", "drawn",
    "IFB__BandS_Plan_Check_-_TI__2604-260819-HW_Comedy-Submittal1_part01_p0001-0003.pdf p1 (A-0.00); A-0.21; exit-stair A-0.00/A-0.20",
    "", GC, "Information row")

with open(os.path.abspath(OUT), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["item_id", "bid_letter_item", "division", "description", "spec_or_model", "qty", "unit", "qty_basis", "qty_source", "furnished_by", "installed_by", "notes"])
    w.writeheader(); w.writerows(rows)
from collections import Counter
print("rows", len(rows), dict(Counter(r["item_id"][0] for r in rows)))
print("written", os.path.abspath(OUT))
