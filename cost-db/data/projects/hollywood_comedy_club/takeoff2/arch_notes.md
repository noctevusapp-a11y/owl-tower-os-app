# Hollywood Comedy Club (Kelly Architects 2604) - architectural takeoff notes

Companion to `arch.csv` (210 rows A-001..A-210, built by `scripts/build_arch.py`; every quantity and its arithmetic is in that
script and in the qty_source column). Blocks: Walls A-001..052, Doors/hardware/windows A-053..111, Ceilings A-112..123,
Floors/bases A-124..137, Wall finishes A-138..170, Millwork/specialties A-171..193, Stair/guardrail/lift/dumbwaiter A-194..202,
Exterior A-203..210. No prices. Scope of mep.csv, equipment.csv and demo_struct_gc.csv (demolition, structure, exit stair at
1704 N Vine, MEP, kitchen equipment) is not repeated.

## Documents used (the SHEET_INDEX page numbers are off for the schedule sheets)
- Vector plans with text: the vector plan set 03_Architectural_Plans_Demo_RCP.pdf (Drive export) p4 A-2.10, p5 A-2.20, p6 A-3.12, p7 A-3.22,
  p8 A-4.01, p9 A-5.12, p10 A-5.11 (IFB 9/9/2026 versions; wall notes and keynotes are on these sheets).
- Finish plans A-2.75 / A-2.76 = IFB Interior Design part01 p6 / p7 (text + vector pattern layers).
- A-7.10 door/window/hardware schedule = IFB part03 p12 (ID p35) and TI part07 p2 (TI p33): the schedule body is raster -
  read at 300 dpi (crops `scratchpad/arch2/A710_*.jpg`). A-7.20 = IFB part03 p13, A-7.21 = IFB part03 p14 (raster, 300 dpi crops).
  The TI set's A-7.10 (p15/p16 in SHEET_INDEX) is A-2.10/A-2.20; the tiles named TI_p15/TI_p16/TI32_p33-35 do not exist
  (TI32_p02/03/04 are A-7.10/A-7.20/A-7.21).
- Addendum 1 (9/21/2026) A-4.20..A-4.27 (half-size 11x17 pages, 13.5 pt/ft at the 3/8" elevations), A-4.30..A-4.34 (full size).
- A-6.10/6.11/6.12 stair, A-6.20/6.21/6.22 lift, A-6.30 dumbwaiter, A-5.20 pick-up counter, A-4.15 railing, A-9.10 details.

## Measurement methods and calibrations
- Scale 3/16" = 1'-0" = 13.5 pt/ft on the plans (calibrate_scale.py: printed 21'-9 1/2" = 294.3 pt, 4' = 54.0 pt); A-4.01 elevations
  1/2" = 1'-0" = 36 pt/ft (door 06 measures 3.0 x 7.75 ft against the scheduled 3'-0" x 7'-9"); Addendum half-size A-4.22
  13.5 pt/ft (12'-0" stage dim = 162 pt).
- Walls: `scripts/poche_walls.py` rasterises the gray new-wall poche (0.686 gray fills on layer a-poche, 54 px/ft), skeletonises
  each component for the centreline length and counts the dark cross-hatch strokes (legend "new full height wall to ceiling");
  wall-type ticks (layer A-Wall-Iden) are matched to the 8.8-pt tag text and attributed per skeleton pixel.
  `scripts/walls_by_tag.py` assigns the untagged components (rules in its docstring, component map `scripts/measure/walls_assigned.csv`;
  overlays `scratchpad/poche/poche_p4.png`, `poche_p5.png`). 18 small untagged slivers (0.4-2.2 LF, 13.3 LF total) are not carried.
- Rooms, ceiling zones, floor zones: `scripts/zones_raster.py` (flood fill from a seed with walls, columns, door leaves/swing chords,
  cased-opening chords and the wall poche as barriers; extra closing chords listed in the qty_source) and the earlier
  `scripts/rooms_raster.py`. Results in `scripts/measure/*.csv`. Perimeters follow door swing arcs where a leaf closes the opening
  (slight over-length); door widths are deducted from A-7.10 sizes in the finish rows.
- Floor tile zones (FL-7/8): the A-2.75 pattern hatch (layer a-new-pattern-floor) closed morphologically: host 112.2 SF,
  (E) restrooms 11+12 371.2 SF. FL-6 zone from the pattern-layer outline (11'-4 1/2" x 28'-0 1/2" chamfered) + the curved wall.
- Exposed coffer ceiling (CLG-3A) 1st floor = extents of the a-extg-ceiling grid on A-3.12 (x 1298-1586 / y 574-1035 pt + patch);
  the 8'-0" CLG-1D band = dining region - coffer grid.
- Heights: 1st-floor walls under the mezzanine/attic at 9'-1" floor-to-floor (A-6.10: 16 risers @ 6-13/16"); mezzanine walls at
  +/-7'-8" / +/-7'-10" (A-3.22); stair 1 shaft 18'-7.5"; finish heights = A-7.21 ceiling heights.

## Key totals
- New walls: type 1 244.7 LF, 1A 36.1, 2 320.5, 3 20.2, 5 (furring) 14.4, AC 283.2, Day-2 untyped 27.4 LF (919 LF without Day 2).
  Cross-hatched (full height) share: 1st floor 254 LF, mezzanine 275 LF.
- Doors: 29 new leaves/openings in the schedule incl. 4 cased openings, 6 (E) doors with new hardware/finish, 4 (E) doors to remain;
  HW-1 7, HW-2 3, HW-3 4, HW-4 11, HW-5 3, HW-6/7/8 4 each, HW-9 5, HW-10 11; 7 louvered doors; 1 window (type A = the fixed
  glass beside exit door 06).
- Ceilings: CLG-1D 3,050 SF (7'-6" 1,859 + 8'-0" band/host/green 1,070 + prep bar 121); CLG-1A refinish 417; CLG-3A clean/patch
  3,866 (916 1st floor + 2,950 mezzanine); K-13 3,773 SF gross coffer area; fin soffits 168 SF plan.
- Floors: FL-2 1,669 SF (B-2 357 LF), FL-4 1,988, FL-5 1,709, FL-6 1,365, FL-7/8 602, SL-1 140; B-4 863 LF, B-5 LED base 658 LF,
  B-1 272 LF, B-3 72 LF, transitions 135 LF.
- Wall finishes: WC-3 342 SF walls + 850 SF band ceilings; WC-8 5,618 SF (dining 2,418, green 308, hallway 04 1,104, attic 1,788);
  poplar moulding grid 3,939 LF; WD-1 209 SF; WC-4 5,187 SF; WT-1/2 290 SF (+510 SF at the (E) restrooms, RFI); WC-1 FRP 3,050 SF;
  WC-5/TX-2 panels 254 SF; P-1 2,368 SF walls + 1,741 SF ceilings; P-4 390 SF; 35 column-levels stain & seal.
- Specialties: lift GVL-SW-120, dumbwaiter Matot size K, guardrail 97.1 LF + lighting pipe 97.1 LF, stair-1 handrail 46.4 LF,
  9 light-beam fins, 2 stages, 3 drapery sets, reception desk, 3 mirrors, hook rail, make-up counter.

## Conflicts between sheets
1. Wall type 1 studs: A-2.10 "400S162-54" vs A-2.20 "3-5/8" 20 GA" (and S-1.10 362S162-54, S-2.x legend 400S162-54).
2. Hallway 04 wall finish: A-7.21 WC-3 vs Addendum 1 A-4.26 WC-8 + poplar moulding (Addendum used).
3. Door/frame finish: A-7.10 P-1 vs Addendum A-4.26 frames P-2 (1st floor) and A-4.30-33 frames P-5 / doors WC-4 (mezzanine).
4. ADA lift lobby walls: A-7.21 P-4 vs A-4.32 WC-4; lift model GVL-SW-120 (A-6.22) vs GVL-SW-144 (A-6.21 KN2); pit 55-3/8 x 54-7/8
   (KN2) vs shaftway 55-3/8 x 56-1/4 (spec).
5. Mezzanine restroom floor FL-3 (A-7.21) is NOT USED on A-7.20; A-2.76 shows FL-7/FL-8/GRT-1 (used). B-3 base NOT USED on A-7.20.
6. Grout 1/16" (A-5.11 note 1) vs 1/8" (A-5.12 note 1, A-7.20 GRT-1).
7. (E) restrooms 11/12/13: A-5.11 "no revision, reference only" vs A-7.21 new FL-7/8, B-1, WT-1&2 and A-5.11 new keynotes 13/15/16/21-23.
8. Pick-up counter height 34" AFF (A-5.20, A-2.20 KN13) vs bar opening countertop 42" AFF (Addendum A-4.33 det 2/8); opening
   36" (A-5.20) vs 6'-0" (A-4.33).
9. Light-beam fins: 9 on the A-4.22 elevation vs 8 "CURVE UP" zones on A-3.22.
10. Mezzanine stage height 6" AFF (A-2.20 KN22) vs 10" (A-4.30 det 5).
11. Window A glass printed GL-1 (A-7.20 GL-1 = gold mirror, 2nd level bar).
12. Mezzanine room numbers: A-2.20 grease duct shaft "30" / mech room 3 "29" vs A-7.21 29 grease duct shaft, 30 (E) electrical,
    28 mech room 3 (schedule numbering used). Day-2 rooms 34/35 and doors 18/39.
13. The 7'-9" / 8'-8" / 10'-4" fin heights on A-4.22 against the 15'-9" CLG-1D P-3 labels on A-3.22 (datum not stated).

## Unreadable / not located
- A-7.10 door schedule: no cell unreadable at 300 dpi; the hardware set of door 39 is blank; hinge finish "-" throughout;
  provided-by cells blank for HW-9/HW-10. Window tag (hexagon) not legible on A-2.10; the window is the A-4.01 KN4 fixed glass.
- A-7.20 action column: all rows read "GC"; the legend shading "owner to provide, GC to install" cannot be told from the print.
- A-3.12/A-3.22: no access-hatch symbols in the plan areas (legend only). No "FE" symbols in the plan areas (legend only).
- A-2.20: no outline for the mezzanine stage(s) KN22 (3 tags); low wall KN17 not drawn with a poche.
- A-2.10 KN15 furring extent, A-4.30 beam soffit length, A-4.31 hallway-opening GWB ceiling size: not dimensioned.
- TX-1, WC-7, GL-1, LM-1/LM-2, ST-2/SL-2, STN-2, HW-20/21/22, P-6: codes used on the Addendum/stair sheets without an A-7.20 entry
  (or listed without a location).
- Walk-in box footprints (inside the kitchen FL-2 / CLG-1D / FRP zones): not dimensioned on the K-sheet text.
- Hallway 35 wall length is derived from the merged hallway+restroom region (A-147 arithmetic); the flood leaks through doors 26/27.

## RFIs
1. Wall type 1 stud size/gauge (400S162-54 vs 3-5/8" 20 GA vs 362S162-54) and whether type 1A (2-hr) extends to the rated deck.
2. "Wet areas" for Mold Tough GWB; head-of-wall fire sealant at rated walls (only acoustical sealant is called).
3. KN21/KN23 perforated metal column enclosures "TYP." - how many columns; perforation pattern/gauge/finish.
4. Extent of KN15 furring (2 locations), A-4.30 beam enclosure soffit, A-4.31 hallway opening ceiling, A-2.20 KN17 24" low wall.
5. Day-2 scope (walls 27.4 LF, rooms 34/35, doors 18/39) - in the base bid?
6. Closers for the 14 doors marked self-closing whose hardware sets omit HW-4; HW-5 pull and HW-6 pivot products; cylinder count
   on the E01 pair; keyed lever (HW-9) on exit door 16; louvers in the 60-min doors 19/34/35/E38; hinges.
7. Window A: glass type (GL-1 printed), location confirmation (A-4.01 KN4 bay).
8. Ceiling joist spacing/gauge for CLG-1D; profile of the 8'-0" band edge (vertical fascia 89.6 LF x 8'-9" assumed);
   K-13 thickness/colour/NRC and the coffer module (net vs gross area).
9. (E) restrooms 11/12/13: are the scheduled new finishes/accessories in scope (A-5.11 says no revision)?
10. Floor prep/moisture testing; transition profiles; FL-9 terrazzo manufacturer; B-3 product; WT-1/WT-2 pattern split.
11. Hallway 04 finish (WC-3 vs WC-8); attic WC-8; door/frame colours (P-1 vs P-2/P-5); lift lobby P-4 vs WC-4.
12. WC-5 panel size/thickness and height (8'-0" vs 9'-1"); TX-4 product and fin panel sizes; TX-1 location; WC-6/WC-7 products;
    drapery HW-20/21 hardware, fullness and finished sizes.
13. Mezzanine stage size(s) and height; LED base perimeter around the stage; stage fascia finish; steps/ramp to the 18" stage.
14. Pick-up counter / bar opening: governing height (34" vs 42"), width (36" vs 6'-0"), countertop material; KegWorks rail model.
15. Fin count 9 vs 8 and the fin profile (side-face areas for P-3 / TX-4).
16. Reception desk, mirrors, hook rail, make-up counter, table lamp: furnished by owner or GC (A-7.20 legend unreadable).
17. FE cabinet locations; room sign type at the green room; restroom accessory manufacturers (none on A-5.12/A-7.20).
18. Lift model (120 vs 144) and the McKinley "elevator door" scope; dumbwaiter capacity within the 100-750 lb class; who installs.
19. P-6 stair paint; visual warning strip product on carpet treads; riser LED strip (not in the lighting schedule).
20. A-4.01: metal panel KN12 extent; plaster patch at the removed-window jambs; terrazzo landing thickness and Walk-of-Fame
    coordination; handrail material (match (E)); granite reuse location.
21. Stair 2 / 1704 N Vine finishes shown on Addendum A-4.34 (WC-4, B-4/P-5, LED tread inserts, ADA railing P-5) - which permit/bid.
