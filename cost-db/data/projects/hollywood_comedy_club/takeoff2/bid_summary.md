# Hollywood Comedy Club — bid assembly from the full-set takeoff

Inputs: priced_demo_struct_gc.csv, priced_equipment.csv, priced_mep.csv, equipment_web_prices.csv.
Every carried value has one origin (column `origin` in bid_lines.csv); nothing is averaged, allowed or assumed.

| origin | direct (USD) | lines |
|---|---:|---:|
| book_exact | 43727.56 | 22 |
| book_substitute | 134229.52 | 57 |
| web_list | 142546.45 | 52 |
| quote_required |  | 139 |
| not_quantified |  | 79 |
| owner / existing |  | 36 |

| | USD |
|---|---:|
| Direct carried (book exact + book substitute + web list) | 320503.53 |
| Contingency 4% | 12820.14 |
| Overhead 8% on (direct + contingency) | 26665.89 |
| Profit 7% on (direct + contingency + overhead) | 25199.27 |
| **Sell = direct x 1.201824** | **385188.83** |
| Book O&P extended (reference only, not added) | 199986.15 |
| Prior estimate sell 2026-10-20 (16 items) | 5081408 |

## By bid-letter item

| item | book exact | book substitute | web list | direct | sell | prior sell | priced | quote req. | not quantified | owner/existing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Demolition | 0.00 | 5678.91 | 0.00 | 5678.91 | 6825.05 | 258314 | 4 | 10 | 15 | 0 |
| Interior walls | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 408840 | 0 | 0 | 0 | 0 |
| Ceilings | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 84662 | 0 | 0 | 0 | 0 |
| Flooring | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 151468 | 0 | 0 | 0 | 0 |
| New Roofing | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 57688 | 0 | 0 | 0 | 0 |
| Interior finishes | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 524421 | 0 | 0 | 0 | 0 |
| Exterior finishes | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 94944 | 0 | 0 | 0 | 0 |
| Doors & Hardware | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 121504 | 0 | 0 | 0 | 0 |
| Stairs & railing | 0.00 | 21673.49 | 0.00 | 21673.49 | 26047.72 | 322960 | 11 | 7 | 5 | 0 |
| Owner-provided equipment install | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 23436 | 0 | 0 | 0 | 15 |
| Lighting | 67.92 | 51928.56 | 0.00 | 51996.48 | 62490.62 | 249377 | 9 | 18 | 4 | 1 |
| Mechanical | 0.00 | 5477.65 | 0.00 | 5477.65 | 6583.17 | 793677 | 9 | 25 | 18 | 2 |
| Plumbing | 17795.65 | 31695.13 | 0.00 | 49490.78 | 59479.21 | 266324 | 33 | 27 | 7 | 3 |
| Low Voltage | 0.00 | 65.61 | 0.00 | 65.61 | 78.85 | 84128 | 1 | 2 | 4 | 0 |
| F&B equipment | 0.00 | 0.00 | 142546.45 | 142546.45 | 171315.74 | 714484 | 52 | 30 | 0 | 0 |
| Other required scope | 25863.99 | 17710.17 | 0.00 | 43574.16 | 52368.47 | 925181 | 12 | 20 | 26 | 15 |

## Lines without a value (218)

| item | id | description | qty | unit | why |
|---|---|---|---:|---|---|
| Demolition | D-03 | Remove (E) kitchen equipment (KN4) - cooking line, tables, sinks, refrigeration, |  | EA | not_quantified: equipment count not derivable (K-sheets show new equipment only) |
| Demolition | D-04 | Remove (E) kitchen exhaust hood (KN5) with duct connection | 1 | EA | quote_required: the kitchen exhaust hood removal row is flagged |
| Demolition | D-06 | Remove (E) bar equipment and bar plumbing utilities (KN8); (E) lines to remain w |  | LS | not_quantified: bar equipment and plumbing utilities to remove not counted |
| Demolition | D-07 | Remove (E) decorative non-bearing walls around structural concrete columns (KN9  | 5 | EA | not_quantified: enclosure wall SF not dimensioned (about 3 ft square, height not stated) and construction not stated; 'TYP.' count unresolved (RFI) |
| Demolition | D-08 | Remove (E) ramp (KN10) | 66.67 | SF | quote_required: ramp construction (concrete vs framed) and height not stated; a removal row cannot be chosen |
| Demolition | D-09 | Remove (E) curved stair to mezzanine (KN11 / KN8 mezzanine) | 1 | EA | quote_required: no stair demolition row for a curved stair of unstated construction (the only verified stair removal row is wood stairs and stringers per riser; riser count not |
| Demolition | D-10 | Remove (E) raised platform with its steps (KN12) | 169.39 | SF | quote_required: platform construction and height not stated; a removal row cannot be chosen |
| Demolition | D-11 | Remove (E) booths (KN12) | 5 | EA | quote_required: no booth / fixed seating removal row (12 05 05 casework rows are flagged) |
| Demolition | D-12 | Remove (E) window: two panels of glass and frame at the Hollywood Blvd bay for t | 2 | EA | quote_required: aluminum window removal rows are flagged (p268, under an unreadable section header); panel heights not dimensioned |
| Demolition | D-13 | Remove (E) doors (KN19 first floor x2, KN12 mezzanine x3) | 5 | EA | quote_required: interior door removal rows are machine_read / flagged; door types not scheduled |
| Demolition | D-14 | Saw-cut and remove (E) concrete slab for the new 4 in sanitary main through the  | 43.42 | LF | not_quantified: trench width not dimensioned and (E) slab thickness 'match (E)' not stated: the slab removal volume, the saw-cut depth and the patch area cannot be computed |
| Demolition | D-15 | Saw-cut and remove (E) concrete slab for branch waste lines, floor sinks and flo |  | LF | not_quantified: branch trench LF per a scaled P-3 not taken; width and depth not dimensioned |
| Demolition | D-16 | Abandon and infill (E) floor sinks, floor drains and the (E) trench drain (P-3 ' | 7 | EA | quote_required: no floor sink / floor drain infill row; opening sizes not stated (slab infill detail 7/A-9.10) |
| Demolition | D-17 | Saw-cut and remove (E) mezzanine concrete floor for the dumbwaiter (A-1.20 KN6;  | 16.67 | SF | not_quantified: (E) waffle slab thickness not stated; the cutout rows are per C.F. |
| Demolition | D-18 | Remove (E) mezzanine concrete floor for the dishwasher exhaust (A-1.20 KN18) |  | SF | not_quantified: KN18 tag not located; size not stated |
| Demolition | D-19 | Fill (E) core-drilled floor opening for ductwork (A-1.20 KN19) | 1 | EA | not_quantified: core-drilled opening size not stated |
| Demolition | D-20 | Remove (E) ceiling coffers and mouldings in their entirety and expose the (E) st | 890.47 | SF | quote_required: coffer material not stated; the GWB ceiling demolition rows are flagged; the plaster-on-lath rows (verified) apply only if the coffers are plaster |
| Demolition | D-21 | Remove (E) light fixtures on the mezzanine ceiling (A-1.20 KN15) | 72 | EA | quote_required: fixture type not stated (symbol count only); the removal rows are by fixture type |
| Demolition | D-22 | Remove (E) mezzanine wall tagged KN13 (west side, north of the exit-stair limit  | 15.15 | LF | not_quantified: wall height not stated; the partition removal rows are per S.F. and the GWB-on-studs rows are flagged |
| Demolition | D-23 | Remove (E) shaft wall, mezzanine (A-1.20 KN4) | 13.38 | LF | not_quantified: wall height not stated; the partition removal rows are per S.F. and the GWB-on-studs rows are flagged |
| Demolition | D-24 | Dashed (demo linetype) double-line wall on A-1.20 inside the exit-stair limit of | 14.41 | LF | not_quantified: wall height not stated; the partition removal rows are per S.F. and the GWB-on-studs rows are flagged |
| Demolition | D-25 | Expose (E) concrete columns, GC to patch and repair (A-1.10 KN18 +TYP., A-1.20 K | 2 | EA | not_quantified: 'TYP.' not resolved to a column count and the enclosure surface is not stated |
| Demolition | D-26 | Patch and repair (E) terrazzo floor as required (A-1.10 KN14) |  | SF | not_quantified: terrazzo patch area not stated |
| Demolition | D-27 | Remove all (E) J-boxes and (E) conduit in their entirety (A-1.10 / A-1.20 genera |  | LS | not_quantified: J-box and conduit counts / LF not drawn |
| Demolition | D-29 | Construction waste hauling with at least 65% diversion by a City of Los Angeles  |  | CY | not_quantified: haul volume not derivable (thicknesses and heights not on the documents) |
| Other required scope | S-02 | Stair 1 stringers C12x20.7 (both flights, 2 stringers) | 31.57 | LF | quote_required: the C12x20.7 stringers are inside the pan-stair row priced on S-01 ('shop fabricated, steel stringers'); the separate channel line for C12 is not in the table a |
| Other required scope | S-04 | Stair 1 landing framing 800S162-54 joists @ 16 in o.c. with 800T162-54 track and | 16.25 | SF | quote_required: drawn: 800S162-54 joists @ 16" with 800T162-54 track and 3/4" Sure-Board decking; the book's stair landing row is a steel pan landing, a different system; Sure- |
| Other required scope | S-05 | Stair 1 landing posts HSS4x4x1/4 | 15.9 | LF | quote_required: no verified HSS 4x4 row in the book (05 12 23.17 carries 5x3, 8x4, 10x6 and 12x8 tubing only) |
| Other required scope | S-08 | ADA lift tieback posts HSS4x4x3/8 continuous, level 1 slab to the mezzanine box  | 18.17 | LF | quote_required: no verified HSS 4x4 row in the book; base plates 8 x 4 x 1/4 with (2) 1/2" x 3" embedded rods per 6/S-3.20 also without a matching anchor row |
| Other required scope | S-09 | ADA lift pit base and '(N) structural beam below' at the lift (A-6.21 KN12 'see  |  | LS | not_quantified: lift pit slab thickness / rebar and the '(N) structural beam below' are not detailed (RFI) |
| Other required scope | S-11 | Box beam (2) 1000S200-97 at the south edge of the mezzanine opening (S-2.20) | 17.45 | LF | quote_required: drawn: (2) 1000S200-97 = double 12 ga x 10" deep box beam; the double 12 ga line is not in the table (the double 14 ga x 10" line is machine_read) and the only  |
| Other required scope | S-14 | Dumbwaiter shaft stud-wall anchors: 1/2 in dia x 4 in embedded @ 24 in o.c. at t | 8 | EA | quote_required: drawn: 1/2" dia x 4" embedded threaded rods, drill and epoxy (Simpson SET-3G); the chemical-anchor lines of 05 05 19.10 are flagged / machine_read and start at  |
| Other required scope | S-15 | Sloped mezzanine floor for the exit-stair headroom clearance below (A-1.20 KN17) | 26.27 | SF | quote_required: sloped mezzanine floor: no structural detail on S-2.20 or the exit-stair S-sheets (RFI) |
| Other required scope | S-16 | Headers / beams at new wall openings |  | EA | not_quantified: header configurations 'see detail' on A-9.10 not read; count not stated |
| Other required scope | S-17 | Sure-Board shear walls (S-1.10 schedule marks 1-4) with S/HDU4 / S/HDU6 holdowns |  | LF | not_quantified: shear-wall marks and holdowns not legible at 110 dpi |
| Other required scope | S-18 | New stud walls 400S162-54 @ 16 in o.c. 'typ. all walls' (S-2.10 / S-2.20 legend) |  | LF | not_quantified: stud wall LF is on the architectural takeoff (interior partitions); stud size conflict 400S162-54 vs 362S162-54 is an RFI |
| Stairs & railing | X-02 | Exit stair stringers C12x20.7 (2) | 21.93 | LF | quote_required: the C12x20.7 stringers are inside the pan-stair row priced on X-01; the separate C12 channel line is not in the table and the nearest verified channel row is fi |
| Stairs & railing | X-05 | Exit-stair landing framing 800C162-54 joists @ 16 in o.c. with 800T162-54 track  | 20.0 | SF | quote_required: drawn: 800C162-54 joists with track and 3/4" Sure-Board decking; the book's stair landing row is a steel pan landing, a different system; joist LF not stated; S |
| Stairs & railing | X-06 | Exit-stair landing posts HSS4x4x1/4 (2), floor to the +6'-0" landing | 12.0 | LF | quote_required: no verified HSS 4x4 row in the book |
| Stairs & railing | X-10 | Steel enclosure parallel to the stringer closing the gap between the stringer an | 10.96 | LF | not_quantified: plate size of the stringer enclosure not stated |
| Stairs & railing | X-12 | Guard at the exit-stair landing / open side |  | LF | not_quantified: guard at the landing: picket guard vs wall-mounted rail not resolved (RFI 9); LF not dimensioned |
| Stairs & railing | X-13 | Visual warning strips 2-4 in wide at the top and bottom treads (A-6.10 KN2) | 10.0 | LF | quote_required: visual warning strips are not in the book |
| Stairs & railing | X-18 | Exit stair demolition: remove (E) exterior wall infill panels flanking the (E) s | 2 | EA | quote_required: removal of (E) exterior plaster wall infill panels (about 42 SF): the exterior stucco removal row is flagged |
| Stairs & railing | X-19 | Exit stair demolition: remove (E) glass storefront door (replaced in kind, KN2) | 1 | EA | quote_required: the storefront swing door removal row is flagged |
| Stairs & railing | X-20 | Exit stair demolition: remove the (E) door access to the main building (not code | 1 | EA | not_quantified: location, size and infill construction of the (E) door access to be removed are not detailed (RFI 14) |
| Stairs & railing | X-21 | Sidewalk work at the 1704 N Vine exit doors | 0 | LS | quote_required: sidewalk work at the Vine St doors: quantity 0 (the Hollywood Blvd bay items are in the architectural takeoff) |
| Stairs & railing | X-22 | Exit signs and egress signage for the new exit stair |  | EA | not_quantified: exit sign count not legible on the exit-analysis plan |
| Stairs & railing | X-23 | Finish paint / galvanizing of the exit-stair steel |  | SF | not_quantified: finish of the exit-stair steel not specified (RFI 10); SF not stated |
| Other required scope | G-03 | Mechanical, electrical, plumbing and fire-alarm permits pulled by others (A-0.00 | 0 | EA | quote_required: MEP and fire-alarm permits pulled by others (quantity 0) |
| Other required scope | G-04 | Modified fire-sprinkler and fire-life-safety plans submitted for review, approva | 1 | LS | quote_required: fire-sprinkler / FLS plan submittal by the fire sprinkler contractor: design and submittal service, no cost row; new vs modified NFPA-13 system is an RFI |
| Other required scope | G-05 | Cal/OSHA construction activity permit where required by CCR Title 8 sec. 341; se |  | EA | not_quantified: Cal/OSHA permit need depends on trench depth (not stated) |
| Other required scope | G-06 | DIG-ALERT 811 notification before excavation; locate (E) underground utilities | 1 | LS | quote_required: DIG-ALERT notification: no cost row |
| Other required scope | G-07 | Encroachment permit for any storage on public property; pedestrian protection an |  | EA | not_quantified: encroachment / pedestrian protection permits depend on the logistics plan |
| Other required scope | G-08 | Historic constraints: Mills Act contract (Yes) and Historic Preservation Review  | 1 | LS | not_quantified: historic facade protection extents not dimensioned; Mills Act / HPR compliance is a process item |
| Other required scope | G-10 | Construction waste management: at least 65% diversion, City of Los Angeles certi | 1 | LS | not_quantified: construction waste management: haul volume not derivable (D-29) |
| Other required scope | G-11 | Green building items called on the notes: MERV 13 filters before occupancy with  | 1 | LS | quote_required: green-building note items (MERV 13 filters before occupancy, O&M recommendations) have no cost row; fixtures are on the trade takeoffs |
| Other required scope | G-12 | Field verification of existing conditions and dimensions before bidding and befo | 1 | LS | quote_required: field verification of existing conditions: company lump-sum item, no matching row |
| Other required scope | G-13 | Shop drawings: structural steel by a LADBS-licensed fabricator, light-gage frami |  | EA | not_quantified: shop drawing package count not stated; no cost row |
| Other required scope | G-14 | Special inspection: epoxy / expansion anchors and dowels (continuous) - both per | 40 | EA | quote_required: special inspection rows of 01 45 23 (technician for inspection, bolting, welding) carry no cost in the table |
| Other required scope | G-15 | Special inspection: structural concrete with f'c > 2,500 psi (continuous, test p | 0 | LS | quote_required: no concrete specified above 2,500 psi (quantity 0); becomes required if the pan fill or pit slab is specified higher (RFI) |
| Other required scope | G-16 | Special inspection: Sure-Board floor sheathing (periodic); deputy inspection whe | 1574.37 | SF | quote_required: Sure-Board sheathing inspection: deputy inspection rows carry no cost; duration not stated |
| Other required scope | G-17 | Special inspection: welding per AWS D1.1 (in-progress visual, Q.C.-1 certified i |  | LS | not_quantified: welding / bolting inspection duration not stated; rows carry no cost |
| Other required scope | G-19 | Evidence of LA Research Reports / ICC listings kept at the site (Simpson anchors | 1 | LS | quote_required: LARR / ICC listing evidence on site: no cost row |
| Other required scope | G-20 | Protection of existing work to remain: (E) terrazzo floor, (E) restrooms (no cha | 1 | LS | not_quantified: protection extents (terrazzo, restrooms, riser cabinet, sidewalks, facade) not dimensioned |
| Other required scope | G-21 | Phasing / work inside the occupied 1704 N Vine restaurant (mezzanine dining room |  | WK | not_quantified: phasing / occupied-restaurant work: duration not stated |
| Other required scope | G-22 | Temporary facilities: water for dust control, pedestrian protection, temporary p |  | WK | not_quantified: temporary facilities: duration not stated (temporary utility rows carry no cost) |
| Other required scope | G-23 | Regular rubbish removal for all trades; turn the site over vacuum-clean includin | 7141 | SF | quote_required: final clean by the GC row is flagged; the daily cleanup row needs the duration (not stated) |
| Other required scope | G-24 | Supervision, project management, scheduling and coordination |  | WK | not_quantified: supervision / PM: duration not stated; field personnel rows are flagged |
| Other required scope | G-25 | Means, methods, sequencing; shores, braces and guys for construction loads; shor |  | LS | not_quantified: shoring at the waffle-floor cuts not detailed; shoring rows carry no cost |
| Other required scope | G-26 | Blocking, backing, hangers and supports for all fixtures, equipment, cabinetry a |  | LS | not_quantified: blocking and backing LF not quantifiable (fixture and equipment locations by others) |
| Other required scope | G-27 | Insurance and licensing evidence (workers' compensation certificates, contractor | 1 | LS | quote_required: insurance and licensing evidence: percentage / company item, no cost row |
| Other required scope | G-28 | Hazardous materials survey / abatement |  | LS | not_quantified: hazardous-materials survey not required by any document; owner to state |
| Other required scope | G-29 | Code data for the GC's compliance: Type IA, A-2, 12 stories plus 2 mezzanine lev | 1 | LS | quote_required: information row (code data), no work |
| F&B equipment | FE-1 | STORAGE SHELVING (existing storage area) | 1 | LOT | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-7 | WALK-IN COOLER (box) | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-8 | EVAPORATOR COIL (cooler) | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-9.1 | REFRIGERATION SYSTEM - cooler condensing unit | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-9.2 | REFRIGERATION SYSTEM - freezer condensing unit | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-10 | COOLER SHELVING | 1 | LOT | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-11 | WALK-IN FREEZER (box) | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-12 | EVAPORATOR COIL (freezer) | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-13 | FREEZER SHELVING | 3 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-16 | OVERSHELVES (prep table) | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-33 | OVERSHELF (over item 32/34) | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-34 | WORKCOUNTER | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-36 | SHELVING | 2 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-38 | WORKCOUNTER | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-39 | OVERSHELVES (over item 38) | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-40 | HOT FOOD WELL (countertop warmer) | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-41 | WORKTABLE | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-55 | FIRE SUPPRESSION SYSTE[M] (description clipped on K2.0) | 1 | EA | quote_required: CaptiveAire hood / fan / fire-system package by model (K7.0 / K7.1); vendor quote scope |
| F&B equipment | FE-56.1 | EXHAUST HOOD - Type I, Hood 1 - Left | 1 | EA | quote_required: CaptiveAire hood / fan / fire-system package by model (K7.0 / K7.1); vendor quote scope |
| F&B equipment | FE-56.2 | EXHAUST HOOD - Type I, Hood 1 - Right | 1 | EA | quote_required: CaptiveAire hood / fan / fire-system package by model (K7.0 / K7.1); vendor quote scope |
| F&B equipment | FE-57 | EXHAUST FAN SYSTEM (exhaust and make-up air fans) | 1 | LOT | quote_required: CaptiveAire hood / fan / fire-system package by model (K7.0 / K7.1); vendor quote scope |
| F&B equipment | FE-58 | WALL FLASHING (behind cooking line) | 1 | LOT | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-61 | SERVICE BAR TOP | 1 | LOT | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-84 | WORKCOUNTER (back bar) | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-94 | CLEAN DISHTABLE | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-97 | EXHAUST HOOD (TYPE 2) over dishmachine | 1 | EA | quote_required: CaptiveAire hood / fan / fire-system package by model (K7.0 / K7.1); vendor quote scope |
| F&B equipment | FE-100 | SOILED DISHTABLE (with pre-rinse sink) | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-101 | SORTING RACK SHELF (over soiled dishtable) | 1 | EA | quote_required: custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope |
| F&B equipment | FE-102 | REFRIGERATOR/HTD. CAB[INET] (description clipped on K2.0) | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| F&B equipment | FE-103 | SODA SYSTEM - FOR 2ND LEVEL | 1 | EA | quote_required: foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0 |
| Mechanical | M-001 | Water-source heat pump WSHP-1, -2, -3, -6, -7: vertical cabinet, 2400 CFM @ 0.7  | 5 | EA | quote_required: water-source heat pump rows of 23 81 46.10 are machine_read (1, 2 and 5 ton cooling; scheduled units are 6, 8 and 10 ton) |
| Mechanical | M-002 | Water-source heat pump WSHP-4, -5: vertical cabinet, 3400 CFM @ 0.7 in SP, 24 GP | 2 | EA | quote_required: water-source heat pump rows of 23 81 46.10 are machine_read (1, 2 and 5 ton cooling; scheduled units are 6, 8 and 10 ton) |
| Mechanical | M-003 | Water-source heat pump WSHP-8: horizontal cabinet, 4000 CFM @ 0.7 in SP, 124,000 | 1 | EA | quote_required: water-source heat pump rows of 23 81 46.10 are machine_read (1, 2 and 5 ton cooling; scheduled units are 6, 8 and 10 ton) |
| Mechanical | M-004 | Condenser (source) water piping, valves, hoses and strainers to 8 WSHP units (16 |  | LF | not_quantified: condenser-water loop source, routing and equipment not in the documents (RFI) |
| Mechanical | M-005 | Condensate and overflow drain lines from WSHP units to code-approved receptor wi | 8 | EA | not_quantified: condensate line LF not drawn (8 connections only); PVC rows are priced per L.F. |
| Mechanical | M-007 | Digital 7-day programmable thermostat 48 in AFF (one per zone) with remote senso |  | EA | not_quantified: thermostat / sensor count not drawn (8 WSHP zones scheduled); DDC sensor rows carry no cost |
| Mechanical | M-010 | New in-line exhaust fan EF-2 serving dishwash hood: 150 CFM @ 0.3 in SP, 3/4 HP  | 1 | EA | quote_required: drawn: in-line cabinet exhaust fan 150 CFM @ 0.3 in SP (Captive Aire SIF9DD-HE); the verified in-line centrifugal rows (OT-23341610-0260/-0280/-0300) carry no u |
| Mechanical | M-011 | New in-line exhaust fan EF-3 serving toilet exhaust: 150 CFM @ 0.3 in SP, 1/3 HP | 1 | EA | quote_required: drawn: in-line cabinet exhaust fan 150 CFM @ 0.3 in SP (Captive Aire SIF9DD-HE); the verified in-line centrifugal rows (OT-23341610-0260/-0280/-0300) carry no u |
| Mechanical | M-012 | Type I exhaust hood "Hood 1 - Left": 10 ft 1 in long x 54 in deep x 30 in high,  | 1 | EA | quote_required: CaptiveAire hood package (job 8710180) by KEC; kitchen hoods are not in the book (only the hood removal row, flagged) |
| Mechanical | M-013 | Type I exhaust hood "Hood 1 - Right": 8 ft 1 in long x 54 in deep, 225 CFM/ft, 1 | 1 | EA | quote_required: CaptiveAire hood package (job 8710180) by KEC; kitchen hoods are not in the book (only the hood removal row, flagged) |
| Mechanical | M-014 | Type II condensate hood "Hood 2" over dishmachine: 3 ft 6 in x 42 in x 12 in, 60 | 1 | EA | quote_required: CaptiveAire hood package (job 8710180) by KEC; kitchen hoods are not in the book (only the hood removal row, flagged) |
| Mechanical | M-015 | Type I hood length, both sections (10 ft 1 in + 8 ft 1 in; 18 ft 3 in overall wi | 18.17 | LF | quote_required: hood length line of the CaptiveAire package (M-012/M-013 carry the hoods); vendor quote scope |
| Mechanical | M-016 | Wall-mount utility cabinet 12 x 60 x 30 in with UL-300 "TANK" fire suppression s | 1 | EA | quote_required: CaptiveAire TANK fire-suppression cabinet, part of the hood package (K2.0 item 55); wet-chemical system rows of 21 22 16 are 250-1,200 lb cylinder clean-agent s |
| Mechanical | M-017 | Electric gas shut-off valve for hood fire system, 2.5 in, supplied with the Capt | 1 | EA | quote_required: electric gas valve supplied with the CaptiveAire package; installation by the plumber has no verified row |
| Mechanical | M-018 | Hood hanging: corner hanging angles, 4 per hood x 3 hoods, with 1/2 in-13 grade- | 12 | EA | not_quantified: hanger rod lengths not dimensioned; the only rod row is coil rod per L.F. (material only) |
| Mechanical | M-019 | Grease duct risers from Type-I hoods to collector, 16 ga welded (UMC ch 5/6): 16 | 10.4 | LF | quote_required: welded 16 ga grease duct is not in the book (23 31 13 carries only fittings add-percentages and a flexible-connection row) |
| Mechanical | M-020 | Grease duct collector and main from Hood 1-Right riser to the (E) fire-rated sha | 23.9 | LF | quote_required: welded 16 ga grease duct is not in the book (23 31 13 carries only fittings add-percentages and a flexible-connection row) |
| Mechanical | M-021 | Grease duct vertical in (E) fire-rated shaft from level 02 to roof, P.O.C. to (E | 62.0 | LF | quote_required: welded 16 ga grease duct is not in the book (23 31 13 carries only fittings add-percentages and a flexible-connection row) |
| Mechanical | M-022 | Field-applied fire-rated grease duct wrap on duct outside the rated shaft (riser | 34.3 | LF | quote_required: field-applied fire-rated grease duct wrap is not in the book (23 07 13 rows are FSK duct insulation wrap, a different product); SF not quantifiable (duct size n |
| Mechanical | M-024 | Supply duct WSHP-8, unit discharge to elbow (duct width scales to 37 in; depth a | 7.9 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-025 | Supply duct WSHP-8, kitchen trunk north-south, 2 round diffusers in lift-out acc | 23.1 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-026 | Exposed A/C supply duct below ceiling, east-west, 6 drops with diffusers (width  | 29.1 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-027 | Soffit supply duct from the exposed trunk south then east to the (E) men's restr | 36.8 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-028 | Exposed MUA supply duct below ceiling, west of the (E) MUA riser, 4 drops (width | 23.9 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-029 | MUA supply duct east of riser toward hoods (width scales to 19 in) | 7.1 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-030 | A/C supply under mezzanine level, dining: south run from SE riser with 2 drops ( | 101.9 | LF | not_quantified: duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 ro |
| Mechanical | M-031 | Supply/return/exhaust ductwork for WSHP-1 through WSHP-7, EF-2 and EF-3 (mezzani |  | LF | not_quantified: no mezzanine mechanical plan; LF not drawn |
| Mechanical | M-032 | Dishwasher (Hood 2 / EF-2) exhaust duct from first floor through mezzanine, galv |  | LF | not_quantified: no mezzanine mechanical plan; LF not drawn |
| Mechanical | M-033 | Duct insulation: 1 in ultralight wrap with vapor barrier on concealed supply/ret |  | SF | not_quantified: duct SF not quantifiable (sizes not labeled); duct wrap rows exist |
| Mechanical | M-036 | Air device C: modular core ceiling diffuser, (4) core 14 x 14 in, 15 x 15 in ope | 6 | EA | quote_required: scheduled: modular core diffuser (4) 14" x 14" core, 15" x 15" opening; the 14" x 14" rectangular ceiling diffuser line is machine_read |
| Mechanical | M-040 | Air outlets drawn on M-2 first-floor plan (untagged): MUA drops 4, kitchen A/C d | 23 | EA | quote_required: the 23 outlets drawn on M-2 carry no device tags (type and size cannot be read); the 16 scheduled devices are priced on M-034..M-039 and the drawn outlets overl |
| Mechanical | M-041 | Manual volume dampers with locking quadrant, one in each branch (round single bl |  | EA | not_quantified: damper count not drawn (15 drops drawn, branch count unknown) |
| Mechanical | M-042 | Fire dampers / fire-smoke dampers at duct penetrations of rated walls and ceilin |  | EA | not_quantified: fire / fire-smoke damper count not drawn |
| Mechanical | M-043 | Flexible duct branches, pre-insulated fiberglass K 0.24, 5 ft max, with spin-in  |  | LF | not_quantified: flexible duct LF not drawn |
| Mechanical | M-045 | Testing, adjusting and balancing by IMC to NEBB/AABC/TABB, report to architect;  | 1 | LS | quote_required: testing, adjusting and balancing rows of 23 05 93 are subcontractor-quote lines that carry no cost |
| Mechanical | M-046 | O&M manuals (3 copies) and 4 hours owner instruction (mechanical); same requirem | 2 | LS | quote_required: O&M manuals and owner instruction have no cost row |
| Mechanical | M-047 | Survey of (E) MUA-1 and EF-1 and all repairs/modifications to renew existing air | 1 | LS | not_quantified: design-build survey and repair of (E) MUA-1 / EF-1: scope undefined (ACCO assessment does not cover HVAC) |
| Mechanical | M-048 | Remove (E) kitchen hood and ductwork (IMC marks items; GC crew demolishes per M- | 1 | EA | quote_required: the kitchen exhaust hood removal row is flagged; duct LF to remove not drawn |
| Mechanical | M-050 | Air-device symbols drawn on the mezzanine attic RCP (supply diffuser / wall supp | 5 | EA | quote_required: untagged air-device symbols on the attic RCP (A-3.22): type and size not stated |
| Mechanical | M-051 | Vibration isolation hangers, factory 2 in deflection, (4) per in-line fan x 2 fa | 8 | EA | quote_required: vibration isolation hangers are not in the book (no row in division 23) |
| Mechanical | M-052 | Roof curbs, openings, flashings and platforms for mechanical equipment (by GC pe | 0 | EA | quote_required: no new roof curbs drawn (quantity 0) |
| Mechanical | M-053 | Refrigerant piping | 0 | LF | quote_required: no field refrigerant piping (quantity 0; WSHP factory charged) |
| Mechanical | M-054 | Hood control interlocks: EF-1 to MUA-1 via Accurex control system with extra con | 1 | LS | quote_required: Accurex / CaptiveAire CASlink hood control package; wiring by EC not quantifiable (no power plan) |
| Plumbing | P-009 | MS-1 floor-mount mop sink with vacuum-breaker faucet; 1/2 in H&CW, 2 in drain (t | 1 | EA | quote_required: foodservice fixture by model (Advance Tabco 9-OP-20, faucet conflict P-4 vs K2.0); quoted scope; the service-sink rough-in rows are flagged |
| Plumbing | P-010 | DM-1 dishmachine; 3/4 in HW, 2 in indirect waste to FS-1, 208V 20 A 3-ph direct | 1 | EA | quote_required: foodservice equipment by model (CMA EST / CMA-180C conflict); quoted scope; no dishmachine rough-in row; the water and waste connections are counted on P-064 /  |
| Plumbing | P-017 | Floor drain FD-1, 6 in round, 2 in no-hub outlet, with trap primer; 1/2 in CW to | 4 | EA | quote_required: the medium-duty cast iron floor drain line (7" top, 2" and 3" pipe size) is flagged; trap primers are on P-022 |
| Plumbing | P-018 | Floor sink FS-1, new, 8 in round, 2 in no-hub outlet, seepage flange, chip floor | 6 | EA | quote_required: no floor sink row in the book (22 13 19 carries floor drains only) |
| Plumbing | P-019 | Grease trap GT-1, floor mounted automatic grease recovery device, 35 GPM, in clo | 1 | EA | quote_required: grease interceptor rows by GPM (p514 lines 0150 / 0200 / 1060 / 1120) are flagged under an unreadable section header and carry no cost code; GT-1 is specified b |
| Plumbing | P-020 | Reduced-pressure backflow preventer BFP-1, 3/4 in, serving ice machines, combi o | 1 | EA | quote_required: the 3/4" reduced-pressure backflow preventer line is flagged (only the 2" and 6" lines are verified) |
| Plumbing | P-021 | Pressure-reducing valve 2-1/2 in on the domestic water service, located in basem | 1 | EA | quote_required: water pressure reducing valve rows of 22 05 23.20 stop at 1-1/2" (1/2", 1", 1-1/2" verified; 3/4" and 1-1/4" flagged); no 2-1/2" line in the table |
| Plumbing | P-022 | Trap primer connections, 1/2 in CW, with Watts LFTP300T (scullery PW-1 FD, KS-1  | 4 | EA | quote_required: no trap primer row in the book |
| Plumbing | P-023 | NEW 4 in sanitary main replacing the full main through the kitchen: POC-1 (new p | 48.2 | LF | quote_required: 4" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-024 | 4 in SAN scullery/bar branch from the 4 in end-of-line wall cleanout (19 -> 26 - | 40.6 | LF | quote_required: 4" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-025 | 3 in SAN: KS-1 3-comp header (12 DFU) and GT-1 / MS-1 run (4 DFU) | 16.5 | LF | quote_required: 3" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-026 | 2 in SAN branches, 1st level: PW-1/DM-1 (5 DFU), HS-1 (2 DFU), FD-1 (1 DFU), mez | 83.7 | LF | quote_required: 2" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-027 | 2 in SAN, mezzanine prep bar (7 -> 4 -> 2 DFU) from riser to BS-3, BS-4, FD-1 an | 29.9 | LF | quote_required: 2" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-028 | 4 in SAN (12 DFU), mezzanine restrooms to the 4 in riser down in wall | 13.6 | LF | quote_required: 4" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-029 | 3 in SAN (5 / 6 DFU) to WC-1 and L-1 each side of the mezzanine riser | 12.8 | LF | quote_required: 3" no-hub cast iron: P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an unreadabl |
| Plumbing | P-030 | Sanitary risers mezzanine to first level: 2 in SAN (7 DFU) from prep bar and 4 i | 2 | EA | not_quantified: riser heights not dimensioned; P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2" to 4160 4") are flagged under an |
| Plumbing | P-031 | Vent piping, new fixtures (2 in V.U.F. at bar x3, 2 in vent loop/island vent at  |  | LF | not_quantified: vent piping not routed on P-3 / P-4; LF not quantifiable |
| Plumbing | P-032 | Cleanouts: 4 in end-of-line wall cleanout at scullery; 2 in Y.C.O. x2 and 3 in C | 1 | EA | quote_required: 4" wall cleanout: the 3" and 4" cleanout lines (p502) are flagged without a cost code; the only verified cleanout row is a 2" round top recessed for terrazzo |
| Plumbing | P-033 | Points of connection to (E) sanitary: POC-1 (4 in from adjacent tenant upstream  | 2 | EA | quote_required: points of connection to the (E) sanitary have no row (tie-in labor only) |
| Plumbing | P-034 | Abandon (E) main sanitary waste line through kitchen; remove all (E) under-floor | 1 | LS | not_quantified: LF of (E) lines to remove not drawn |
| Plumbing | P-035 | Infill (E) floor drains, (E) floor sinks and (E) trench drain in the kitchen (IN | 9 | EA | quote_required: no floor drain / floor sink infill row; opening sizes not stated (slab infill per 7/A-9.10 is on D-16) |
| Plumbing | P-036 | Saw-cut, trench and backfill for new under-floor sanitary piping, 1st level (sum | 189.0 | LF | not_quantified: trench width and depth not dimensioned; split of trench vs hung pipe over the basement not derivable (ACCO); slab removal and patch areas not quantifiable |
| Plumbing | P-050 | H&CW and HWR risers: 1-1/2 in CW feed up to WH, 1-1/2 in HW riser up to mezzanin | 3 | EA | not_quantified: riser heights (1st level to mezzanine to 2nd-floor roof) not dimensioned |
| Plumbing | P-051 | (E) first-floor restroom CW and HW branch headers and fixture drops below the 2  | 41.3 | LF | quote_required: branch and drop sizes of the re-piped (E) restroom headers are not printed on P-2; a copper row cannot be chosen without the size |
| Plumbing | P-055 | HW to mezzanine lavatories beyond the 1 in HW (8 WSFU) label (size not re-labele | 27.5 | LF | quote_required: HW size beyond the 1" label is not re-labeled on P-4; a copper row cannot be chosen without the size |
| Plumbing | P-058 | Water filters: inline filter for ice machines 73/76, inline filter for combi ove | 3 | EA | quote_required: water filters are KEC items by model (Everpure EV9329-52 x2, Rational R295-CL); quoted scope |
| Plumbing | P-061 | 1-1/2 in natural gas (250 CFH) from the manifold west and south to the riser up  | 59 | LF | quote_required: the 1-1/2" black steel threaded line is flagged; the verified 1-1/2" line of 22 11 13.48 is grooved-joint pipe with ductile iron fittings, a different joining s |
| Plumbing | P-062 | 1 in gas drops with shut-off and quick disconnect to cook-line appliances (6 O.B | 7 | EA | not_quantified: drop lengths not dimensioned; quick disconnects and gas cocks have no verified row (P-7 1" drops vs K2.0 3/4" connections is an RFI) |
| Plumbing | P-063 | Seismic gas shut-off valve at meter manifold | 1 | EA | quote_required: seismic gas shut-off valve is not in the book; ACCO reports an existing approved seismic valve on the 3" main (RFI) |
| Plumbing | P-064 | Kitchen equipment indirect-waste connections "EXTEND I.W. TO F.S." (items 8, 12, | 21 | EA | quote_required: indirect-waste equipment connections (extend I.W. to floor sink) have no row; the floor sinks are on P-018 |
| Plumbing | P-065 | Kitchen equipment direct-waste connections (mop sink 2 in, grease interceptor 4  | 6 | EA | quote_required: the 6 direct-waste connections are inside the rough-in components priced on P-006 (3-comp sink), P-008 (hand sinks x3) and P-009 (mop sink) and the interceptor  |
| Plumbing | P-066 | Kitchen equipment water connections (HW and/or CW 1/2 in - 3/4 in): items 17, 20 | 24 | EA | quote_required: equipment water connections: 11 H&CW pairs are inside the rough-in components of P-006..P-016; the 12 CW-only equipment connections (items 45, 66 x3, 73, 75, 80 |
| Plumbing | P-068 | EXISTING CONDITION (ACCO): 6 in PVC backwater valve about 10 ft deep in the 1704 | 1 | EA | not_quantified: backwater valve repair not in the P-sheets; scope and whether it is in the bid are RFIs |
| Plumbing | P-070 | EXISTING CONDITION (ACCO): first-floor restroom flushometer valves and faucets n | 10 | EA | quote_required: flush-valve / faucet retrofit of the (E) first-floor restrooms is not called out on P-2 / P-3 (RFI); the waterless urinal rows are flagged / machine_read and th |
| Other required scope | E-011 | New electrical panels to manage lighting and sound in the main stage area and sp | 3 | EA | quote_required: rating, voltage, feeder and source of the 3 new lighting/sound panels not given (RFI); the verified NQ panelboard rows need the amperage and circuit count |
| Other required scope | E-012 | Feeders to the 3 new panels |  | LF | not_quantified: feeder sizes and lengths not given |
| Other required scope | E-013 | Rewire existing panels per the panel schedules (KA, KB, KC, CP, DP, HA): branch  | 6 | EA | not_quantified: rewiring of 6 existing panels: no power plan, circuit numbers, homeruns or device counts |
| Other required scope | E-016 | Hood electrical package wiring (electrician scope per M-7): 120V 15 A shunt-trip | 1 | LS | not_quantified: hood electrical package wiring: shunt-trip breaker, control panel feed and interlocks have no lengths or device counts (no power plan) |
| Other required scope | E-019 | Power connections to plumbing equipment: grease recovery device 115V 520 W (K2.0 | 3 | EA | not_quantified: power to the grease recovery device, HWR pump and water heater: circuit lengths and source not shown |
| Other required scope | E-020 | ADA vertical lift power: 20A/1P circuit "ADA LIFT" on (E) panel B (Vine) | 1 | EA | not_quantified: ADA lift circuit length and lift electrical data not in this scope |
| Other required scope | E-021 | Dumbwaiter power connection (2 stops, A-6.30) |  | EA | not_quantified: dumbwaiter circuit and panel not given (RFI) |
| Other required scope | E-023 | General-purpose receptacles, GFCI, switches and device boxes (plans) |  | EA | not_quantified: general receptacles, GFCI, switches and boxes: no power plan |
| Other required scope | E-024 | Power to hand dryers in mezzanine restrooms (GC to coordinate power) | 2 | EA | not_quantified: hand dryer circuits: lengths and source not shown; the dryers are on the architectural takeoff |
| Other required scope | E-025 | Electrical demolition: remove all (E) J-boxes and conduit in their entirety; rem | 1 | LS | not_quantified: electrical demolition counts and conduit LF not drawn; panel Dillons has no removal row |
| Lighting | E-103 | Type C1: LED single round ceiling pendant, 24 V DC, bronze, remote driver not in | 6 | EA | quote_required: decorative LED pendant (Panzeri Zero Round, 24 V DC with remote driver); no pendant of this kind in the book |
| Lighting | E-104 | Type C2: Round ceiling pendant with vintage LED A15 filament lamp E26; 3 W 2700K | 3 | EA | quote_required: decorative tassel pendant with filament lamp (Atolla); no fixture of this kind in the book |
| Lighting | E-105 | Type D1: LED wall light, indirect, color-select, TRIAC/ELV dimming, damp; 10 W 2 | 15 | EA | quote_required: decorative LED wall sconce (WAC Twist-N-Lite, color-select, TRIAC/ELV); no fixture of this kind in the book |
| Lighting | E-107 | Type G1: LED COB strip light at host ceiling, length 17 ft 6 in, in channel; 26. | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-108 | Type G2: LED strip west of comedy club ceiling, recessed in underside of mechani | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-109 | Type G3: LED strip south of comedy club ceiling, length 12 ft 0 in; 18.5 W 1644  | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-110 | Type G4: LED strip south and east of comedy club ceiling, length 45 ft 6 in; 70  | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-111 | Type G5: LED strip at main stage fin millwork, both sides, 17 ft 0 in each (18 x | 18 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-112 | Types G6-G11: baseboard LED strip in 4 in trimless recessed LED base channel (78 | 119 | LF | quote_required: CORE Lighting 24 V LED base strip in recessed trimless channel; LED tape / base strip is not in the book (G16-G18 lengths also not stated) |
| Lighting | E-113 | Type G12: LED strip at green room ceiling, recessed, length 10 ft 0 in; 15.3 W 1 | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-114 | Type G13: LED strip at main comedy stage back wall, length 23 ft 0 in; 35.2 W 31 | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-115 | Type G14: LED strip at main comedy stage back wall, length 27 ft 0 in; 41.5 W 37 | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-116 | Type G15: LED strip at main comedy stage back wall, length 33 ft 0 in; 50.5 W 45 | 1 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-117 | Types G16 (stair 1), G17 and G18 (stair 2): baseboard LED strip in trimless base | 3 | EA | quote_required: CORE Lighting 24 V LED base strip in recessed trimless channel; LED tape / base strip is not in the book (G16-G18 lengths also not stated) |
| Lighting | E-118 | Type G19: LED strip at stair 2 step, 5 ft 0 in each (11 x 5 = 55 LF), compatible | 11 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-119 | Type G20: LED strip at stair 2 step, 3 ft 9 in each (16 x 3.75 = 60 LF); 6 W 514 | 16 | EA | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-120 | Type G21: handrail LED, continuous strip at mechanical attic, 98 ft 0 in; GC to  | 98 | LF | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-121 | Omni Light True Series COB LED ribbon, total scheduled length (G1 17.5 + G2 20 + | 707 | LF | quote_required: Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book |
| Lighting | E-122 | 24 V DC LED drivers / power supplies for strip lights (CORE LSM25 30 ft max run, |  | EA | not_quantified: 24 V driver and remote driver counts not scheduled |
| Lighting | E-128 | Lighting control: dimming drive based on Lutron Athena control system; 0-10V con | 1 | LS | not_quantified: Lutron Athena dimming system: dimming bank and dimming switch counts not drawn (symbols in the legend only); 0-10 V control wire lengths unknown |
| Lighting | E-131 | Trim-kit schedule (A-3.70 title "Light Fixture Schedule, Trim Kit Schedule") |  | EA | not_quantified: trim-kit schedule named on A-3.70 is not drawn (RFI) |
| Lighting | E-132 | Lighting branch circuits and panel capacity for the new fixtures (A-3.70 total c |  | EA | not_quantified: lighting branch circuits and panel capacity: no lighting plan / circuiting issued |
| Low Voltage | LV-001 | Sound / AV system for main stage area and speakeasy |  | LS | not_quantified: sound / AV system not in the documents (power only on E-011) |
| Low Voltage | LV-003 | TV outlets / video distribution |  | EA | not_quantified: TV outlets / video distribution not in the documents |
| Low Voltage | LV-004 | Data / telecom cabling, network rack |  | EA | not_quantified: data / telecom cabling and network rack not in the documents |
| Low Voltage | LV-005 | Fire alarm interface for the hood fire-suppression system (alarm-contractor scop | 1 | LS | not_quantified: fire-alarm interface for the hood system: no fire-alarm device plan for the tenant space; alarm-contractor scope under separate permit |
| Low Voltage | LV-006 | Security / CCTV / access control | 0 | EA | quote_required: security / CCTV / access control: quantity 0 (none drawn) |
| Low Voltage | LV-007 | Hood control-panel remote monitoring (CASlink) via cellular or ethernet | 1 | EA | quote_required: CaptiveAire CASlink remote monitoring, part of the hood control package; ethernet drop not drawn |

## What the number is and is not

The sell figure covers only the lines with a documented price: the company's book (verified rows, Los Angeles latest index) where the book has the work, and published dealer/manufacturer prices for scheduled equipment models (material only). Every line listed under 'without a value' is still scope and still needs a vendor or subcontractor quote, or a quantity the documents do not give; they are not in the sell figure. The 2026-10-20 estimate is shown for orientation only; it was built before the schedules, MEP, plumbing and kitchen drawings were on hand.
