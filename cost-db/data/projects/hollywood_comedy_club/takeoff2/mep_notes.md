# Hollywood Comedy Club (Kelly Architects 2604) — MEP take-off notes

Companion to `mep.csv` (188 rows: M- 54, P- 70, E- 57 incl. lighting E-101..E-132, LV- 7).
Documents read: MEP progress set (M-1, M-2, M-4, M-6, M-7, E-2.0, E-2.1, E-2.2, P-6), Addendum 2 (P-1..P-7),
Addendum 3 (E-2.1 panel locations), A-3.70 (IFB 9/9/2026 and plan-check 8/18/2026 issues), RCPs A-3.12 / A-3.22
(vector text layer), K-sheets K1.0 / K2.0 / K7.0, ACCO plumbing site assessment, the 16 light-spec PDFs.
Scripts in `scripts/`: `extract_panels.py` + `panels_extracted.csv` (E-2.1/E-2.2 circuit rows from the text layer),
`summarize_panels.py`, `count_rcp_tags.py`, `grid_crops.py` (gridded 200-dpi crops), `measure_runs.py`
(pipe/duct LF from page-pixel segments), `calibrate_scale.py`, `build_mep_csv.py` (writes `mep.csv`).

## Scale calibration used for every measured LF
* P-2, P-3, P-4, P-7 (Addendum 2) and M-2 carry the plan-strip "SCALE: 3/16" = 1'-0"" (title blocks print
  1/4" = 1'-0", the sheet default). 3/16 in/ft at 200 dpi = **37.5 px/ft**. Checks: Hood 2 (3'-6" per M-6)
  measures 131 px = 3.49 ft on M-2; the P-7 gas run dimensioned 26'-0" measures 975 px = 26.0 ft.
* M-4 MECHANICAL BUILDING SECTION B is 1/8" = 1'-0" = **25 px/ft**.
* Vertical risers (basement-to-1st, 1st-to-mezzanine, mezzanine-to-2nd-floor roof) are not dimensioned on any
  sheet; they are listed as EA with "height not dimensioned" and are excluded from the LF totals.

## Sheets / data missing from the bid set (quantity cannot be derived)
1. No mezzanine mechanical plan (M-3) and no M-5: WSHP-1..7, EF-2, EF-3 locations, their ductwork, the
   dishwasher exhaust duct (A-2.20 KN11) and toilet exhaust duct are not drawn (rows M-031, M-032).
2. No condenser-water loop: M-1 schedules 8 water-source heat pumps at 50 F EWT (16/24/30 GPM) but no loop
   piping, pump, heat-rejection equipment or source is shown on any M- or P-sheet (M-004). RFI.
3. No electrical power or lighting plans: E-2.0 is an all-existing single line, E-2.1 is panel schedules /
   load calcs, E-2.2 is existing emergency panels. Receptacles, switches, homeruns, lighting circuits,
   feeders to the 3 new panels, dumbwaiter circuit and WSHP circuits are not quantifiable (E-012, E-021,
   E-023, E-132). Addendum 3 gives panel locations only.
4. A-3.70 note A refers to "EQ-2.10" for food-equipment power (not in the set; K2.0 used instead) and note D
   to "Electrical Dwgs for Transformer specifications" (none). The "Trim Kit Schedule" named in the A-3.70
   title is not drawn on either issue (E-131).
5. Mezzanine prep-bar equipment B1 / B3 / B5 (BS-3, BS-4, BS-5 on P-4) are not on the K2.0 first-level schedule.
6. M-2 prints no duct sizes and no air-device tags; widths were scaled off the drawing (M-024..M-030) and depths
   are unknown, so duct SF / insulation SF is not quantifiable (M-033).
7. Vent piping is not routed on P-3/P-4 (only "2" V.U.F." x3 and the island-vent detail) (P-031).
8. Hood fire-suppression permit is a deferred submittal by the fire installer (M-7); fire-alarm devices for the
   tenant space are not drawn (LV-005).

## Conflicts found between documents
* **WSHP count / tonnage**: M-1 schedule = 8 units (5 x 50VQP072 6-ton, 2 x 50VQP096 8-ton, 1 x 50HQP120
  10-ton; 56 tons nominal) vs M-1 Cal Green system description "(2) water source heat pump units ... 12-tons";
  A-2.20 KN14 tags 4 HVAC units (prior take-off M01 carried 7). WSHP-4/5 row repeats the 072 capacity/weight/MOCP.
  M-1 AIR BALANCE lists WSHP-8 at 2400 CFM vs 4000 CFM in the unit schedule; the balance totals do not sum.
* **Hood length**: M-6 10'-1" + 8'-1" = 18'-2" (18'-3" overall with the 1 in standoff) vs the M-2 outlines
  (scale to 6'-8" + 7'-6" = 14'-2") vs A-2.10 (about 13 ft).
* **EF-1 vs hoods**: Type-I exhaust 2773 + 1819 = 4592 CFM (M-6) vs (E) EF-1 3000 CFM @ 2.75" (M-1) and the M-1
  static calc at 2975 CFM; MUA-1 3600 CFM. M-1 plan-check note cites 1900 CFM "actual" kitchen exhaust.
* **Grease duct in shaft**: M-4 shows a P.O.C. to "(E) grease duct @ top of shaft" and an "existing fire rated
  shaft", with the section broken between levels 05 and 13; the drawn 62 LF is not the shaft height. M-1 static
  calc assumes 125 ft of 16 in duct + 350 ft of 48x18 duct. Whether the shaft duct is new or existing is an RFI.
* **Air devices**: 16 scheduled on M-1 (A3, B4, C6, D1, E1, F1) vs 23 untagged outlets drawn on M-2.
* **Gas valve**: M-7 2.5 in "SC ELECTRICAL" valve supplied by CaptiveAire vs P-7 "2" MECH./ELECT. ANSUL VALVE"
  on the 2 in (625 CFH) manifold; P-7 riser diagram sizes the manifold 1.5 / 1.25 / 1 in while the plan labels
  the whole 24 ft run 2 in; K2.0 appliance connections are 3/4 in vs 1 in drops on the riser diagram.
* **Water heater**: K2.0 #14, P-5, P-6 = A.O. Smith BTH-250 100 gal 250 MBH (existing on roof) vs P-4 fixture
  schedule BTH120 60 gal 120 MBH vs ACCO (June 2026) Bradford White BWCV0400 per the 2009 plans, not verified,
  replacement recommended. P-5 calc requires 320 GPH / 180 MBH minimum.
* **Water service**: P-1 sizing form "meter size 3"" (and "loss thru 2.0" meter") vs P-2 "(E) 2" water meter in
  sidewalk vault"; ACCO estimates 2.5 in copper, entry not verified.
* **Backflow**: P-4 schedules BFP-1 Wilkins 975XL 3/4 in; P-1 form states "backflow prevention device not
  required per rule 16-D"; P-1 plan-check note requires RP devices on carbonators.
* **Fixture models**: KS-1 John Boos 2PB1824-2D24 (P-4) vs GSW SE18183D20 (K2.0 #88); DM-1 CMA EST (P-4) vs
  CMA-180C (K2.0 #98); MS-1 faucet T&S B-0133-ADF-12B (P-4) vs B-0665-BSTR (K2.0 #20); L-1 basin Kohler K-2035-8
  (A-5.12) with Sloan EBF-415 faucet (P-4). Bar sinks: P-2 draws BS-1 x1 and BS-2 x2 vs K2.0 dump sink x2 / hand
  sink x1. WC-1 Kohler K-3609-T tank type (P-4) vs the P-1 form's flush-valve Caroma list (x6) and UR-1 x2.
* **Panel DP**: schedule 200 A bus MLO vs E-2.0 "(E) main switchboard DP 400 A" with "(E) 700A 3P" main and
  "800A" bus as printed; E-2.0 feeder 2 goes to "(E) panel DMA" (no schedule); feeder 7 "DW hood exhaust 50A/3P"
  vs DP ckt 12 "DM Hood Exhaust 20A/1P". Panel KA schedule descriptions (ice tea brewer, soup wells, mixer 60A/3P)
  do not match the K2.0 equipment, i.e. the schedules are the legacy tenant's loads to be "rewired".
* **Lighting counts** (A-3.70 IFB qty vs RCP tags): B1 33/28, F1 22/24, G20 16/15, X1 17/18, Y1 17/15, Y2 14/11,
  Y3 8/9, G21 16 (qty) vs one 98-ft run. Plan-check A-3.70 (8/18) differs again (A1 1, G1-G5 DiodeLED Valent,
  Y1 15, Y3 9, D1 TRIAC/ELV); the IFB issue was used.
* **Dillons panel**: to be removed (Addendum 3) but its 25 circuits (lighting, 7 TV-outlet lines, 3 POS lines,
  emergency lights, refrigerator, 220 V deep fryer) have no new home; the 3 new panels are for lighting and sound.

## Unreadable / incomplete cells
* P-4 VENT LINE DATA: pipe-size column cut off at the tile edge (ADD2_p04_t02) — FU/length pairs read only.
* K2.0 amps "*" at items 6, 9, 12, 57, 76, 97 (verify with owner / refrigeration / hood drawings).
* E-2.1 panel A: breaker sizes print "-" for all circuits; panel names are graphics (not in the text layer) and
  were mapped by position against the sheet image (row 1 KA/CP/HA, row 2 KB/Dillons/B, row 3 KC/DP/A).
* E-2.1 panel HA circuit "Switch - ?" (as printed). M-6 hood-table fine print read at tile resolution; the
  "430 SS where exposed" / option cells are as transcribed in scripts/build_mep_csv.py.
* A-3.70 G16-G18 catalog length "X'" (blank); G21 wattage "150w, 134234lm" as printed.
* C2 chandelier spec PDF is image-only (no text); the lamp PDF gives PLT-13401.

## RFIs recommended
1. Source, routing and equipment of the 50 F condenser-water loop for 8 WSHP units; confirm unit count/tonnage.
2. EF-1 3000 CFM vs 4592 CFM hood exhaust; MUA-1 3600 CFM; is EF-1 to be replaced?
3. Grease duct: new vs existing in the rated shaft; shaft height; cleanout count; wrap extent.
4. Electrical: issue power/lighting plans; circuits and feeders for 8 WSHP, EF-2/3, dumbwaiter, 3 new panels;
   re-feed of Dillons loads; DP/switchboard rating discrepancy; panel DMA.
5. Water heater: confirm existing model/condition (ACCO recommends replacement) and whether replacement is in scope.
6. First-floor (E) restrooms: is the flush-valve/faucet retrofit (ACCO item 3, P-1 fixture list) in the bid?
7. Backwater valve at 1704 N Vine (flapper lodged open) — repair in scope?
8. Water-service point of entry: open wall/floor to verify (ACCO item 4); meter 2 in vs 3 in.
9. Gas: new SoCalGas meter vs existing 3,000 CFH rotary meter; seismic valve new vs existing; gas-valve size.
10. Trim-kit schedule for A1; 24 V drivers / transformers for strip lights and pendants; reconcile fixture counts.
11. Bar sink counts (BS-1/BS-2) and mezzanine bar equipment schedule (B1/B3/B5).
12. Vent routing and tie-in to the (E) 4 in vent stack; trench vs hung pipe split over the basement.

## Method notes
* "drawn" LF rows list the page-pixel end points (scripts/measure_runs.py) so they can be re-measured.
* Panel circuit counts are "described circuit lines" (continuation rows of multi-pole breakers show "-");
  spares/spaces excluded; title-block text bleeding into the panel-A/B/EHB/EPB blocks was filtered.
* RCP tag counts come from the vector text layer after applying the page rotation (both RCP pages are rotated
  270 deg in the PDF); the IFB Interior Design p8/p9 RCPs carry identical tags.
* K2.0 connection counts are per schedule line x qty (conveyor oven counted as 2 circuits per its remark).
* No quantity was rounded, factored or allowed beyond what a sheet states; sums are shown in qty_source.
