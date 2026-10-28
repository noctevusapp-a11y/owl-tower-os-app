# Hollywood Comedy Club (Kelly Architects 2604) - demolition / structural / exit stair / general conditions takeoff notes

Companion to `demo_struct_gc.csv` (built by `scripts/build_demo_struct_gc.py`; every quantity and its arithmetic is in that script).
Prefixes: D- demolition (29 rows), S- structural (18), X- exit stair 1704 N Vine (23), G- general conditions (29). No prices.

## Measurement methods and calibrations
- Vector demo plans `03_Architectural_Plans_Demo_RCP.pdf` p2 (A-1.10) and p3 (A-1.20): 3/16" = 1'-0" = 13.5 pt/ft.
  Calibration: the "4'" dimension line on p3 = 54.0 pt (4.00 ft); "21'-9 1/2"" on p4 = 294.3 pt (21.80 ft).
  Dashed (demo) linework was chained (`scripts/demo_chains.py` -> `chains_p2/p3.csv`), paired into double-line walls
  (`scripts/demo_walls.py` -> `walls_p2/p3.csv`), closed rectangles found with `scripts/demo_rects.py`, keynote tags
  located from the text layer and checked on the overlays made by `scripts/sheet_overlay.py`.
- Vector exit-stair set `2604-260626-Exit_Stairs-PC_Submittal1.pdf` p3 (A-2.10): 13.5 pt/ft; the two 3'-0" door leaves
  measure 40.5 pt each. Its S-sheets (p6-p10) are vector but have no text layer; the landing was taken from the A-6.10 dims.
- Raster S-2.10 / S-2.20 (`kelly_img/TI_p32-09.jpg`, `TI_p32-10.jpg`, 110 dpi, 3/16" scale): 20.625 px/ft.
  Check: column bays 16.8 / 24.0 ft on the raster vs 16.4 / 24.4 ft on the vector A-1.10 (`scripts/grid_crop.py` crops).
- Sheet identification correction: TI part07 p36 is a typical-details sheet (A-9.10: backing, gypsum partitions, utility
  trench patch 6, slab infill 7, 2,500 psi fill at lower slab); p37 = S-0.10 general notes; p38 = S-1.10; p39 = S-1.20;
  p40 = S-2.10; p41 = S-2.20; p42 = S-3.10; p43 = S-3.20 (SHEET_INDEX.md lists "S-0.01" - the sheet is numbered S-0.10).

## Key totals
- Demolition: walk-ins 2 EA tagged (+1 untagged 12.3 x 14.7 ft enclosure); bar die wall / back bar 61.6 LF (footprint 241 SF);
  ramp 66.7 SF; raised platform 169 SF + 5 booths; 2 window panels (6.0 ft bay) + 5 doors; sanitary-main trench 43.4 LF;
  7 floor sink/drain infills (P-3); dumbwaiter floor cut 16.7 SF; ceiling coffers 890 SF (294 LF outer moulding, 3 nested
  lines); 72 mezzanine ceiling light fixtures; mezzanine walls 15.2 + 13.4 (+14.4 untagged) LF; lift pit cut 21.1 SF x 3-1/2"
  (0.23 CY); 5 column-enclosure removals by tag (TYP. unresolved).
- Structural: stair 1 (16 risers, 3'-9" wide) C12x20.7 31.6 LF, HSS8x4x1/4 16.2 LF, 2 HSS4x4x1/4 posts 15.9 LF with 9x9x3/8
  plates / 8 epoxy rods, pan fill 48.1 SF; lift tiebacks 2 x HSS4x4x3/8 (18.2 LF); box beams (2)1000S200-54 111 LF and
  (2)1000S200-97 17.5 LF; attic floor 800S162-54 @ 16" + 3/4" Sure-Board 1,538 SF; dumbwaiter W10x22 x3 = 19.6 LF with 2-hr SFRM.
- Exit stair: 11 risers / 10 treads, 5'-0" wide; C12x20.7 21.9 LF; pan fill 45.8 SF; HSS8x4x1/4 18 LF; 2 posts 12 LF; 16
  embedded 1/2" rods on 6 plates; handrails 27.8 LF; 1-hr walls 95.5 LF / 797 SF (GWB 1,595 SF); 2 storefront doors 3'-0" +
  4'-8" fixed panel (32 SF); 1 rated exit-access door; demo 2 wall panels + 1 storefront door + 1 interior door.
- General conditions: 2 permits (TI, exit stair 26016-10000-18605), MEP/FA permits by others, FLS/sprinkler plan submittal,
  Mills Act + Historic Preservation Review, 65% diversion with a City-certified hauler, special inspections (40 counted epoxy
  anchors, 1,574 SF Sure-Board, welding, concrete only if > 2,500 psi), 2 structural observation programs, 7,141 SF final clean.

## Special-inspection and observation list (S-0.10 of both permits, identical text)
1. Placing of structural concrete with f'c > 2,500 psi - continuous (test per code). None specified above 2,500 psi
   (A-9.10 trench patch and slab fill are 2,500 psi); stair pan-fill and lift-pit strengths not stated -> RFI.
2. Expansion anchors and epoxy anchors/dowels - continuous; test per manufacturer. Counted: stair 1 base plates 8, lift
   tiebacks 4, dumbwaiter track 8 (one level), exit stair 16 = 40; box-beam column saddles (4 each, 4/S-3.10) not counted
   (column count not legible on the 110-dpi S-2.20).
3. Sure-Board floor sheathing, roof sheathing and wall panels - periodic; deputy inspector required where fastener spacing
   is 4" o.c. or less (edge nailing is #8 @ 4" o.c. per S-2.10 note 3). Areas: attic 1,538 SF, stair 1 landing 16 SF,
   exit-stair landing 20 SF.
4. Inspection list: concrete placement; bolting with high-tensile bolts; expansion anchors; epoxy anchors/dowels; foundation
   excavation check before concrete; in-progress visual welding inspection per AWS D1.1-2010 by Q.C.-1 certified inspectors.
5. Structural observation program (LADBS form) - observer Charles Tan, S.E. (S4758); item checked "Others: gage metal";
   statement of responsibility to LADBS before starting the seismic-force-resisting system (CBC 1704.4). One form per permit.
6. LADBS-licensed fabricator required for structural steel; LA Research Reports / ICC listings kept at the site; shop
   drawings reviewed in 7 working days; shoring designed and stamped by a California-licensed civil engineer where needed.

## Conflicts found
- Dumbwaiter floor opening: A-1.20 dims 4'-8" x 4'-0"; A-6.30 demo plan 4'-2" x 4'-0" (used, larger scale governs per A-0.11 note 9).
- Dumbwaiter beams: A-6.30 "(N) 10"x22" steel beam, see S-2.20"; S-2.20 shows W10x22 x3 (used) and S-3.10 det. 5 "W10x per plan".
- Exit-stair landing: A-6.10 dims 5'-0" x 4'-0" (used) vs ENERCALC landing beam span 6.0 ft and a 6'-3" dim outside the landing.
- Stair 1 posts: S-2.10 places the two "HSS4x4x1/4" labels on diagonal lines at the landing corners; 5/S-3.20 draws vertical posts.
- Typical studs: S-2.10/S-2.20 legend "400S162-54 @ 16" typ. all walls" vs S-1.10 schedule "362S162-54 @ 16"" ground and second levels.
- Sprinklers: A-0.00 "Yes - New NFPA-13" vs A-0.21 "Yes existing, compliance with NFPA-13".
- Exterior exit doors: the prior estimate carried 4; A-4.01 elevations 3 and 4 are section cuts of elevation 2 (one door on
  Hollywood Blvd); the exit-stair set adds two doors on Vine St -> 3 exterior exit doors in total.
- Column enclosures (KN9 / KN7) and column exposure (KN18 / KN11) carry "TYP." - tag instances used (5 and 2); 17 / 18
  column symbols exist in the tenant area on A-1.10 / A-1.20.

## Unreadable / not located
- A-1.20 KN18 (concrete floor removal for the dishwasher exhaust): keynote in the legend, no "18" tag found in the plan text layer (image TI_p11-04).
- Sure-Board shear-wall marks and holdown symbols on S-2.10 / S-2.20: not legible at 110 dpi (images TI_p32-09 / TI_p32-10).
- Exit-sign symbols on the exit-stair A-0.20 exit-analysis plans at 1/8": one legible (mezzanine exit door), others not (image STAIR-02).
- A-7.10 window types (TI p33) and the door schedule: raster tiles only, not read - window panel heights and door sizes not taken.
- A-1.20 dashed double line at display x=1274 (seven 2.5-3.1 ft segments, 20.3 LF, 4" face spacing) next to the coffers: unidentified, untagged, not carried.

## RFIs
1. KN9 / KN7 "TYP.": which columns carry decorative enclosures to be removed (5 tagged; 17 / 18 columns exist)?
2. KN18 / KN11 column exposure "TYP.": how many columns?
3. Untagged dashed enclosure 12.3 x 14.7 ft in the (E) kitchen (D-02): walk-in or partition?
4. A-1.20 dashed wall W1 (14.4 LF) inside the exit-stair limit of work (D-24): removed under which permit?
5. Dumbwaiter opening size (4'-8" vs 4'-2") and beam type (10x22 plate beam vs W10x22).
6. ADA lift pit: slab thickness/rebar and the "(N) structural beam below" (A-6.21 KN12) - not on S-2.10.
7. Stair 1 landing supports: posts or kicker braces; landing size 4'-4" x 3'-9".
8. Exit-stair landing size 5'-0" x 4'-0" vs the 6'-0" calc span; pan-fill concrete depth and strength (special inspection if > 2,500 psi).
9. Exit-stair guard: picket guard shown in the A-6.11 sections vs walls on both sides in plan.
10. Finish paint for the exit-stair steel (not specified; stair 1 calls P-6).
11. Typical stud size: 400S162-54 (plan legend) vs 362S162-54 (S-1.10 schedule).
12. New sprinkler system vs modification of the existing NFPA-13 system.
13. Sloped mezzanine floor for the exit-stair headroom (A-1.20 KN17, 26 SF): construction and permit.
14. (E) door access to the main building to be removed (exit-stair A-0.20): location, size, infill.
15. Trench widths for the new sanitary main and branches (A-9.10 detail 6 gives no width); branch lengths from a scaled P-3.
16. Box-beam column-saddle count (4/S-3.10) and the attic joist extents - confirm on a vector S-2.20.
17. Hazardous-materials survey: not required by any document on hand - owner to state.
18. Schedule / duration: no schedule or contract duration in the documents; all duration-driven general-conditions rows are not_quantifiable.

## Scope boundaries used
- Interior partitions (incl. the dumbwaiter shaft walls and all 400S162-54 walls), finishes, MEP, kitchen equipment supply,
  the Hollywood Blvd exterior door bay finishes (7" terrazzo step, granite reset, handrail, plaster, metal panel) are in the
  other takeoffs; only their demolition, structural support and general-conditions obligations appear here.
- Exit-stair demolition rows are X-18 .. X-20 (separate permit); everything under permit 26016-10000-18605 is prefixed X-.
