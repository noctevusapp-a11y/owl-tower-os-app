# Hollywood Comedy Club TI - book-priced estimate (Los Angeles, latest index month)

Internal working document. Project: Comedy club interior package, 6263 Hollywood Blvd, Los Angeles (Kelly Architects job 2604, owner Meco Properties); exit stair at 1704 N Vine St priced from its own PC submittal. Prepared 2026-10-24 from the bid documents on hand and the transcripts of the prior estimate session (2026-10-20). Price source: `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.csv`, rows with `status = verified` only, columns `*_la_latest` (period 2026-Q02). Nothing was sent to anyone.

## 1. Totals in three tiers

**The exact tier is the only one priced from the book without an assumption**: the verified row describes the specified work and the product, size and type as the issued sheets fix it (same unit or an exact stated conversion). **The substitute tier prices a different or unspecified product** (product, size, gauge, type or finish system not fixed by the issued sheets or differing from the row, or part coverage); it is shown for decision only, and the exact difference is written in the `reason` column of every such row. Everything else is unpriced.

| tier | material | labor | equipment | **direct (bare)** | book O&P extended (ref.) | **sell = direct x 1.201824** | components |
|---|---:|---:|---:|---:|---:|---:|---:|
| priced_exact | 6,849 | 60,128 | 6,555 | **73,533** | 104,202 (0 rows without a book O&P value) | **88,373** | 4 |
| priced_substitute | 141,241 | 120,874 | 213 | **262,328** | 237,186 (20 rows without a book O&P value) | **315,272** | 46 |
| **combined (exact + substitute)** | 148,090 | 181,003 | 6,768 | **335,861** | 341,388 | **403,646** | 50 |

Unpriced: **134 takeoff lines with no price at all** and **7 unpriced components** inside lines that carry other priced components (listed in section 4 and in `unpriced_items.csv`).

Company markup arithmetic on the combined bare direct (applied once, the same way as the prior estimate; the per-tier sell figures use the same factor on each tier's own direct):

| | amount (USD) |
|---|---|
| Combined bare direct | 335,861 |
| Contingency 4% = 335,861 x 0.04 | 13,434 |
| Overhead 8% = 335,861 x 1.04 x 0.08 | 27,944 |
| Profit 7% = 335,861 x 1.04 x 1.08 x 0.07 | 26,407 |
| **Sell = direct x 1.04 x 1.08 x 1.07 = direct x 1.201824** | **403,646** |

Exact figures (cents) as summed from `estimate_la_latest.csv`: exact direct 73532.65 / sell 88373.30; substitute direct 262328.22 / sell 315272.35; combined direct 335860.87 / sell 403645.65; book O&P extended exact 104201.82, substitute 237185.98. These equal the values written by `price.py` (`_totals.json`) and the `summary_by_item` sheet of the xlsx; the equality of all three totals is asserted when this file is built.

The book's own `total_incl_op` column (installing contractor's O&P) is reported for reference only and is not added anywhere, so O&P is not double-counted.

Lines: 173 takeoff lines; 38 carry at least one priced component (4 exact + 46 substitute components, since walls, ceilings, doors and fixtures are priced as components); 134 lines are fully unpriced; 1 line (toilet partitions) carries a drawn quantity of 0. Substitute components by match: substitute 42; partial 4 ('partial' = the row covers part of the component only).

## 2. Totals by bid-letter item, side by side with the prior estimate

Prior sell values are the 16 item totals of the 2026-10-20 estimate (base bid 5,081,410; direct 4,228,081; sell factor 1.2018). Sell columns here are the item's bare direct of that tier x 1.201824. The difference to the prior sell is the scope the book could not price plus price differences on the priced lines; it is not a saving.

| Bid-letter item | exact direct | exact sell | substitute direct | substitute sell | combined sell | prior sell | book O&P ext. (ref.) | lines with a price | unpriced lines | unpriced comps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Demolition | 0 | 0 | 371 | 446 | 446 | 258,314 | 0 | 1 | 15 | 0 |
| Interior walls | 2,237 | 2,688 | 132,662 | 159,436 | 162,124 | 408,840 | 154,809 | 3 | 6 | 2 |
| Ceilings | 0 | 0 | 12,120 | 14,566 | 14,566 | 84,662 | 9,065 | 4 | 4 | 1 |
| Flooring | 0 | 0 | 5,609 | 6,741 | 6,741 | 151,468 | 2,666 | 3 | 10 | 0 |
| New Roofing | 0 | 0 | 0 | 0 | 0 | 57,688 | 0 | 0 | 1 | 0 |
| Interior finishes | 0 | 0 | 16,036 | 19,273 | 19,273 | 524,421 | 11,531 | 8 | 10 | 0 |
| Exterior finishes | 0 | 0 | 11,964 | 14,379 | 14,379 | 94,944 | 14,146 | 1 | 5 | 1 |
| Doors & Hardware | 0 | 0 | 33,487 | 40,246 | 40,246 | 121,504 | 158 | 3 | 1 | 2 |
| Stairs & railing | 0 | 0 | 8,967 | 10,776 | 10,776 | 322,960 | 1,214 | 3 | 11 | 0 |
| Owner-provided equipment install | 0 | 0 | 0 | 0 | 0 | 23,436 | 0 | 0 | 8 | 0 |
| Lighting | 0 | 0 | 175 | 210 | 210 | 249,377 | 255 | 1 | 16 | 0 |
| Mechanical | 0 | 0 | 5,582 | 6,709 | 6,709 | 793,677 | 6,900 | 2 | 7 | 0 |
| Plumbing | 4,253 | 5,111 | 1,246 | 1,497 | 6,608 | 266,324 | 7,004 | 2 | 5 | 1 |
| Low Voltage | 0 | 0 | 0 | 0 | 0 | 84,128 | 0 | 0 | 3 | 0 |
| F&B equipment | 0 | 0 | 0 | 0 | 0 | 714,484 | 0 | 0 | 4 | 0 |
| Other required scope | 67,043 | 80,574 | 34,108 | 40,992 | 121,566 | 925,181 | 133,640 | 7 | 28 | 0 |
| **Total** | **73,533** | **88,373** | **262,328** | **315,272** | **403,646** | **5,081,410** | **341,388** | **38** | **134** | **7** |

Note: the prior session adopted the tag-based wall takeoff on 2026-10-20 (transcript mac_session_page1.txt L355, L718-721: direct 4,193,926 / base 5,040,361). The 5,081,410 figure above is the base bid as issued before that change, as instructed.

## 3. Coverage

- Exact tier: sell 88,373 = 1.7% of the prior base bid; direct 73,533 = 1.7% of the prior direct. This is the share of the prior scope the book prices without an assumption.
- Combined (exact + substitute): sell 403,646 = 7.9% of the prior base bid; direct 335,861 = 7.9% of the prior direct.
- 3 of the 16 bid-letter items carry an exact-tier price: Interior walls, Plumbing, Other required scope. 12 carry any book price; 4 carry none: New Roofing, Owner-provided equipment install, Low Voltage, F&B equipment.
- Unpriced lines and components by status: not_quantified 61; not_in_book 33; spec_not_issued 22; book_row_not_verified 9; book_row_not_matching 9; owner_provided 6; quote 1.
- Largest gaps between the prior sell and the combined sell, by bid-letter item (prior sell minus combined sell): Other required scope 803,615; Mechanical 786,968; F&B equipment 714,484; Interior finishes 505,148; Stairs & railing 312,184.
- No cost code used in this estimate is carried by more than one row of the table.
- Book table on hand: one cost code per printed line; a line under an unreadable section header carries no section id and no cost code (flagged); a code shared by two printed lines stays only on the undoubted one. 4 components of this estimate changed against the previous table because of that: I02 (poplar crown molding): priced_substitute (OT-06221330-2510, verified in the previous table) -> book_row_not_verified (p203 line 2510 is flagged and carries no cost code); G28 (robe hook OT-10281313-4400): cost_code_duplicated (code shared with a flagged towel-bar row) -> priced_substitute (the code is now carried by the verified robe-hook row only); P03 (grease interceptor (candidate only)): candidate OT-22131913-0150 / -0200 / -1060 / -1120 (verified) -> candidate p514 lines 0150 / 0200 / 1060 / 1120 (flagged, no cost code); line stays spec_not_issued; D10 (aluminum window removal (candidate only)): candidate OT-08050510-0200 (machine_read window row sharing the code with a flagged door row) -> candidate p268 window line 0200 (flagged, no cost code); line stays book_row_not_verified.

## 4. Unpriced lines and components

Status values: `not_quantified` = the quantity cannot be read from the documents on hand (reason names the missing sheet or dimension); `spec_not_issued` = quantity known but the product/type is on a schedule that was not issued, so no row can be selected; `not_in_book` = no verified row describes the work; `book_row_not_matching` = the nearest verified row is a different kind of work or product (candidate given, its numbers not used); `book_row_not_verified` = the only matching rows are machine_read or flagged (candidates given, numbers not used); `cost_code_duplicated` = the code is carried by more than one verified row; `owner_provided` = owner-furnished item; `quote` = vendor quote origin. `scope` = line (the whole takeoff line is unpriced) or component (one component of a line that has other priced components).

| item | scope | bid-letter item | description / component | qty | unit | status | reason | candidate row |
|---|---|---|---|---:|---|---|---|---|
| D01 | line | Demolition | Strip (E) kitchen: equipment, walk-ins, hood and ducts (disconnect by trades) | 1340 | SF | not_in_book | equipment count per K sheets not issued; the only hood-removal row is flagged | OT-11050510-4750 (flagged) |
| D03 | line | Demolition | Remove (E) raised platforms, booths and ramp |  | LS | not_quantified | not dimensioned on A-1.10 |  |
| D04 | line | Demolition | Remove (E) curved stair to mezzanine | 1 | EA | not_in_book | no stair demolition row in the book |  |
| D05 | line | Demolition | Remove (E) decorative non-bearing walls around structural columns |  | LS | not_quantified | wall SF not dimensioned on A-1.10 / A-1.20 |  |
| D06 | line | Demolition | Remove (E) partitions and shaft wall |  | LS | not_quantified | wall LF not dimensioned on A-1.10 / A-1.20 |  |
| D07 | line | Demolition | Remove (E) ceiling coffers and mouldings, expose (E) structural beams (mezzanine) | 1088 | SF | book_row_not_verified | coffer material not stated; GWB ceiling demolition row is flagged; plaster-on-lath row (OT-09050510-1000, verified) would apply only if the coffers are plaster | OT-09050510-0200 (flagged) |
| D08 | line | Demolition | Saw-cut and remove (E) concrete floor for trenching, floor drains/sinks, dumbwaiter and dishwasher exhaust |  | LS | not_quantified | trench and opening dimensions per P sheets not issued | OT-02411916-0020 (verified, C.F.) |
| D09 | line | Demolition | Fill (E) core-drilled floor opening for ductwork | 1 | EA | not_in_book | no floor-opening patch row; opening size not stated |  |
| D10 | line | Demolition | Remove two panels of (E) window glass and frame for new exit door(s) | 2 | EA | book_row_not_verified | aluminum window removal rows are flagged (p268 'Aluminum, including trim, to 12 S.F.' sits under an unreadable section header and carries no cost code) | p268 window demolition line 0200 (flagged, no cost code) |
| D11 | line | Demolition | Remove (E) doors | 5 | EA | book_row_not_verified | interior door removal rows are machine_read / flagged | OT-08050510-1020 (machine_read) |
| D12 | line | Demolition | Remove (E) light fixtures on mezzanine ceiling |  | LS | not_quantified | fixture count not shown on A-1.20 |  |
| D13 | line | Demolition | Remove all (E) J-boxes and conduit in their entirety |  | LS | not_quantified | not quantifiable |  |
| D14 | line | Demolition | Remove (E) bar plumbing utilities; (E) lines to remain if they cannot be removed |  | LS | not_quantified | not quantifiable |  |
| D15 | line | Demolition | Patch and repair (E) terrazzo floor as required |  | LS | not_quantified | extent not shown |  |
| D16 | line | Demolition | Expose (E) concrete columns; patch and repair |  | LS | not_quantified | count not shown |  |
| W02 | component | Interior walls | New wall class B (tags 1A (2-hr), 3 (1-hr exterior plaster)): LF x average height = SF of wall (one face) -> Metal studs 6" 20 ga 16" OC (type 1A / type 3) | 1952 | SF | book_row_not_matching | drawn: 6" 20 ga studs 16" OC; nearest verified row OT-09221613-3410 is 25 ga 6" studs 12" OC under the 16' high 25 ga group; the 20 ga 6" rows carry an unreadable unit | OT-09221613-3410 (verified, 25 ga 12" OC); OT-09221613-3490 (verified, unit unreadable) |
| W03 | line | Interior walls | New wall class C (tags shaft/enclosure walls with no tag): LF x average height = SF of wall (one face) | 280 | SF | spec_not_issued | shaft/enclosure assembly per A-6.xx / S sheets not issued |  |
| W04 | line | Interior walls | Wall type AC: second layer of 5/8 in Type X each side (in addition to class A base assembly) |  | SF | not_quantified | AC-tagged LF not separable from the class A total |  |
| W05 | line | Interior walls | Wall type 3 exterior side: 5/8 in DensGlass, 2 layers felt, 1 in exterior plaster |  | SF | not_quantified | type 3 LF not separable from the class B total | OT-09242340-1000 (stucco 3 coats, verified, S.Y.); OT-09242340-1900 (mesh wired to steel, verified) |
| W06 | line | Interior walls | Furr out and patch (E) wall for a continuous smooth surface |  | LS | not_quantified | not dimensioned |  |
| W07 | line | Interior walls | Low wall 24 in tall around sloped ceiling (mezzanine) |  | LF | not_quantified | not dimensioned |  |
| W08 | component | Interior walls | Exit stair 1-hr enclosure walls (1704 N Vine): 6 in 16 ga studs 16 in o.c., 5/8 in Type X each side, 4 in acoustic insulation (UL U404) -> Metal studs 6" 16 ga 16" OC (exit stair 1-hr wall) | 553.65 | SF | book_row_not_matching | drawn: 6" 16 ga studs 16" OC; nearest verified S.F. row OT-09221613-3410 is 25 ga 6" 12" OC; the 16 ga rows in 05 41 13 are priced per stud (Ea.) | OT-09221613-3410 (verified, 25 ga 12" OC); OT-05411310-0330 (verified, 16 ga 6" wide, Ea.) |
| W09 | line | Interior walls | Level 5 skim coat premium in public patron areas (dining, vestibules, restrooms) |  | SF | not_quantified | public / back-of-house wall split not separable |  |
| C01 | component | Ceilings | CLG-1D: new 5/8 in Firecode 30 GWB on new steel joists (3-5/8 in under 4 ft span, 6 in elsewhere), smooth washable finish -> New steel ceiling joists 3-5/8" (span under 4') / 6" with track | 2114 | SF | book_row_not_matching | drawn: GWB on new steel joists; nearest verified row OT-09222613-3400 is suspended 1-5/8" carrier channels, a different framing system | OT-09222613-3400 (verified, suspended channels) |
| C03 | line | Ceilings | Mezzanine curved soffits CLG-1D at 15'-9" with P-3 (8 locations) |  | SF | not_quantified | soffits not dimensioned |  |
| C06 | line | Ceilings | K-13 spray-applied acoustical insulation within (E) concrete coffers (no K-13 on ribs) | 4623 | SF | not_in_book | no K-13 / spray cellulose acoustic insulation row in the book |  |
| C07 | line | Ceilings | Access hatches in GWB ceilings (Williams Bros. WB DW 405 / DWAL 414) |  | EA | not_quantified | hatch count not shown | OT-08311310-4150 (verified, recessed drywall door 12x24) |
| C08 | line | Ceilings | Frame around (E) ceiling beams and new soffit at hallway openings (mezzanine) |  | LS | not_quantified | not dimensioned |  |
| F01 | line | Flooring | Floor finish, dining 02 (level 1) - finish code not issued | 1925 | SF | spec_not_issued | floor finish code not issued (A-2.75 / A-7.20) |  |
| F02 | line | Flooring | Floor finish, hallway 04 (level 1) - finish code not issued | 210 | SF | spec_not_issued | floor finish code not issued (A-2.75 / A-7.20) |  |
| F03 | line | Flooring | Lobby/host floor tile FL-7 / FL-8 checkerboard with GRT-1 and green room FL-4 | 227 | SF | spec_not_issued | lobby tile (FL-7/FL-8) and green room FL-4 areas not separable; tile product per A-7.20 not issued | OT-09311310-3300 (verified porcelain tile) |
| F04 | line | Flooring | Floor finish, kitchen, dry storage, wait station - finish not issued | 1530 | SF | spec_not_issued | kitchen floor finish not issued (quarry tile / epoxy TBD in prior estimate) | OT-09321610-0900 (quarry tile 6x6, verified); OT-09672323-1500 (epoxy topping 1/4", verified) |
| F05 | line | Flooring | Floor finish, mezzanine dining 2 and hallway 35 - finish not issued | 1791 | SF | spec_not_issued | floor finish code not issued (A-2.76 / A-7.20) |  |
| F07 | line | Flooring | Stage millwork platform, level 1, 18 in AFF with LVT FL-6 | 104.0 | SF | not_in_book | custom millwork platform with LVT; no verified platform or LVT row |  |
| F08 | line | Flooring | Stage millwork platform, mezzanine, 6 in AFF with LVT FL-6 |  | SF | not_quantified | not dimensioned |  |
| F10 | line | Flooring | LED base B-4 with P-5, mezzanine, lift lobbies and stair 2 (4 in, straight sections only) | 545 | LF | not_in_book | LED base profile not in the book |  |
| F12 | line | Flooring | Floor preparation, leveling and moisture mitigation |  | LS | not_quantified | no finish plan issued |  |
| F13 | line | Flooring | 7 in terrazzo step at new exit door to match (E) sidewalk terrazzo |  | LF | not_quantified | length not dimensioned |  |
| R01 | line | New Roofing | Roof penetrations, curbs and flashing at grease duct and rooftop equipment |  | LS | not_quantified | no roof plan or M sheets issued |  |
| I02 | line | Interior finishes | Poplar moulding grid 1/2 in x 1/4 in stained to match WC-8, at 1'-8" W x 2'-4" H o.c. | 2044.8 | LF | book_row_not_verified | drawn: 1/2" x 1/4" poplar strip stained to match WC-8; the only poplar crown row (p203 line 2510, 'Crown, 5/8" x 5/8", poplar', formerly OT-06221330-2510) is flagged in the replaced table (SECTION_ID_DOUBTFUL, no cost code, no total); the verified poplar rows of 06 22 13.30 (lines 0455-0575) are casing profiles 3/4" x 2-1/2" to 9-1/2", a different product | p203 line 2510 (flagged, no cost code); OT-06221330-0575 (verified, casing 3/4" x 2-1/2" poplar, not matching) |
| I05 | line | Interior finishes | TX-4 fabric-wrapped 2 in acoustic panels at main stage wall | 611 | SF | book_row_not_matching | TX-4 fabric-wrapped 2" acoustic panels: drawn: 2" acoustic panels with orange fabric stretched over them (A-4.22A); nearest verified row OT-09841310-1000 sits under 'FIXED PANELS, perforated steel facing' (mineral fiberboard, fabric covered, 3/4" thick, concealed spline), a different product | OT-09841310-1000 (verified) |
| I06 | line | Interior finishes | TX-2 drapery with HW-20 / HW-21 hardware (lobby arch, green room window, main room) | 22 | SF | not_in_book | drapery fabric not in the book (hardware rods only) | OT-12221610-4040 (traverse rod, verified) |
| I07 | line | Interior finishes | WD-1 wood paneling, main room | 145 | SF | not_in_book | no verified wood paneling row (hardboard paneling only) |  |
| I11 | line | Interior finishes | Planton poplar moulding over mezzanine doors, painted P-5 | 14 | EA | not_quantified | moulding LF per door not dimensioned (A-7.10 not issued) |  |
| I12 | line | Interior finishes | 2 in wood frame cased openings | 4 | EA | not_in_book | no verified casing / cased-opening row |  |
| I14 | line | Interior finishes | Stain and seal (E) concrete columns ST-2 / SL-2 | 16 | EA | not_quantified | column surface area not stated; sealer material carried in C05 |  |
| I15 | line | Interior finishes | Perforated metal enclosure floor to exposed ceiling at (E) plumbing lines around column | 2 | EA | not_in_book | custom perforated metal enclosure |  |
| I16 | line | Interior finishes | Light-beam millwork fins with LED (two channels) and stage-wall millwork |  | LS | not_quantified | custom millwork, not dimensioned |  |
| I17 | line | Interior finishes | Mezzanine stage decorative wood 4 in x 3 in with 1 W bulbs at 12 in o.c. |  | LF | not_quantified | not dimensioned |  |
| X01 | component | Exterior finishes | Exterior tempered-glass storefront exit doors to match (E) entry doors, with panic hardware, closer, weatherstrip and threshold -> Panic exit device with accessible lever trim | 4 | EA | book_row_not_matching | drawn: panic hardware and accessible hardware on exterior exit doors (submittal KN3, A-4.01 KN5); the only verified rows with a panic device are average hardware sets for school / motel doors (OT-08712015-2250, 'Door'), a different product | OT-08712015-2250 (verified, hardware set) |
| X02 | line | Exterior finishes | Fixed tempered insulated glass storefront adjacent to exit door (1704 N Vine) and (N) fixed glass (6263 Hollywood) |  | SF | not_quantified | panel sizes not dimensioned | OT-08811010-0800 (1/4" tempered glass, verified); OT-08411320-0150 (tube framing, verified) |
| X03 | line | Exterior finishes | Salvage and reset (E) granite base at new exit door bays |  | LF | not_quantified | not dimensioned |  |
| X04 | line | Exterior finishes | New plaster wall to match (E) facade at exit door bays |  | SF | not_quantified | not dimensioned | OT-09242340-1000 (stucco, verified) |
| X05 | line | Exterior finishes | Aluminum metal panel, color to match (E) window frame |  | SF | not_quantified | not dimensioned |  |
| X06 | line | Exterior finishes | 1-1/2 in handrail at 34 in AFF at exterior step |  | LF | not_quantified | not dimensioned | OT-05521350-0915 (wall rail, verified) |
| DR1 | component | Doors & Hardware | New interior doors, frames and hardware (type per A-7.10 not issued) -> Hinges, closers and remaining hardware per A-7.10 | 22 | EA | book_row_not_matching | hardware sets per A-7.10 not issued; no verified hinge row; OT-08712030-8030 is a surface closer under the 'electronic closer-holder' heading and is not a hinge set | OT-08712030-8030 (verified, closer) |
| DR2 | component | Doors & Hardware | 1-hr fire-rated exit access door with panic hardware outside the rated stair shaft (1704 N Vine) -> Panic hardware on the rated exit access door | 1 | EA | book_row_not_matching | drawn: panic hardware (submittal KN5); the only verified panic rows are average hardware sets for school / motel doors (OT-08712015-2250), a different product | OT-08712015-2250 (verified, hardware set) |
| DR3 | line | Doors & Hardware | Access doors in walls (Williams Bros.) |  | EA | not_quantified | count per mech/plumb drawings not issued | OT-08311310-4150 (verified) |
| S02 | line | Stairs & railing | Concrete fill in stair pans | 27.5 | SF | not_in_book | no verified stair-pan concrete fill row |  |
| S04 | line | Stairs & railing | Landing posts HSS 4x4 (2 posts, floor to +6'-0" landing) | 12.0 | LF | not_in_book | no verified HSS 4x4 row |  |
| S05 | line | Stairs & railing | Landing framing 800C162-54 joists @ 16 in o.c. with 800T162-54 track, 3/4 in Sure-Board decking | 20.0 | SF | not_in_book | landing joists are listed per stud (Ea.) only; Sure-Board decking not in the book |  |
| S06 | line | Stairs & railing | Base plates 8x8x1/4 with (4) 1/2 in x 4 in embedded anchors and post plates with (2) 1/2 in x 4 in threaded rods | 12 | EA | book_row_not_matching | Embedded anchors 1/2" x 4" and threaded rods at base plates: drawn: 1/2" x 4" embedded anchors / threaded rods (S-3.10); nearest verified row OT-05051920-0600 is a 1/2" x 2-1/16" zinc expansion shield, a different product | OT-05051920-0600 (verified, expansion shield) |
| S08 | line | Stairs & railing | Visual warning strips 2-4 in wide at top and bottom treads | 2 | EA | not_in_book | visual warning strip not in the book |  |
| S09 | line | Stairs & railing | Steel enclosure parallel to stringer closing gap to (E) wall |  | LS | not_quantified | not dimensioned |  |
| S10 | line | Stairs & railing | Stair 1 (interior, level 1 to mezzanine) and railing |  | LS | not_quantified | A-6.10/11/12 of the main set not issued; riser count unknown |  |
| S11 | line | Stairs & railing | Guardrail 42 in AFF at mezzanine edge |  | LF | not_quantified | LF not dimensioned; A-4.15 not issued | OT-05521350-2050 (42" steel rail, verified) |
| S12 | line | Stairs & railing | (N) step to access adjacent tenant space from mezzanine |  | LS | not_quantified | not dimensioned |  |
| S13 | line | Stairs & railing | (N) structural posts per S sheets | 4 | EA | spec_not_issued | post sizes per S sheets not issued |  |
| S14 | line | Stairs & railing | LED insert in stair 2 step treads |  | LS | not_quantified | not dimensioned |  |
| O01 | line | Owner-provided equipment install | Reception desk (Natura Design Works Mila black tambour 36 x 190.7 x 44 in) - set in place | 1 | EA | owner_provided | owner-provided item; setting/installation labor has no verified row |  |
| O02 | line | Owner-provided equipment install | 2 in walnut shelves 18 in apart (lobby) |  | LF | owner_provided | owner-provided item; setting/installation labor has no verified row |  |
| O03 | line | Owner-provided equipment install | 60 x 48 in oblong mirrors (bronze glass lobby; clear glass green room) | 2 | EA | owner_provided | owner-provided item; setting/installation labor has no verified row |  |
| O04 | line | Owner-provided equipment install | IBM Hollywood mirror Princess 60 x 45 in, green room | 1 | EA | owner_provided | owner-provided item; setting/installation labor has no verified row |  |
| O05 | line | Owner-provided equipment install | 60 x 18 in makeup counters, green room | 2 | EA | owner_provided | owner-provided item; setting/installation labor has no verified row |  |
| O06 | line | Owner-provided equipment install | Mercury Row Garfinkel wall 5-hook | 1 | EA | owner_provided | owner-provided item; setting/installation labor has no verified row |  |
| O07 | line | Owner-provided equipment install | 3'-0" x 2'-8" oblong window, green room | 1 | EA | spec_not_issued | window type per A-7.10 not issued |  |
| O08 | line | Owner-provided equipment install | Foot rail from Kegworks at prep bar (by GC) |  | LF | not_quantified | length not dimensioned |  |
| L_A1 | line | Lighting | New light fixtures type A1 (A-3.70 schedule not issued) | 11 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_B1 | line | Lighting | New light fixtures type B1 (A-3.70 schedule not issued) | 28 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_C1 | line | Lighting | New light fixtures type C1 (A-3.70 schedule not issued) | 6 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_C2 | line | Lighting | New light fixtures type C2 (A-3.70 schedule not issued) | 3 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_D1 | line | Lighting | New light fixtures type D1 (A-3.70 schedule not issued) | 15 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_F1 | line | Lighting | New light fixtures type F1 (A-3.70 schedule not issued) | 24 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_X1 | line | Lighting | New light fixtures type X1 (A-3.70 schedule not issued) | 18 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_X2 | line | Lighting | New light fixtures type X2 (A-3.70 schedule not issued) | 3 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_Y1 | line | Lighting | New light fixtures type Y1 (A-3.70 schedule not issued) | 15 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_Y2 | line | Lighting | New light fixtures type Y2 (A-3.70 schedule not issued) | 11 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_Y3 | line | Lighting | New light fixtures type Y3 (A-3.70 schedule not issued) | 9 | EA | spec_not_issued | fixture type per A-3.70 not issued |  |
| L_G | line | Lighting | Decorative fixtures G1..G21 | 62 | EA | spec_not_issued | decorative fixtures per A-3.70 not issued |  |
| L_EX | line | Lighting | Exit signs and emergency lighting |  | EA | not_quantified | symbols not countable; E plans not issued | OT-26521316-0200 (LED exit sign, verified); OT-26521310-0900 (emergency unit, verified) |
| L_SW | line | Lighting | Switches, dimmers, dimming banks |  | EA | not_quantified | symbols not countable | OT-26272620-0200 (switch), OT-26272620-1650 (dimmer), verified |
| L_LED | line | Lighting | LED strip in base B-4 (mezzanine) and in light-beam millwork | 545 | LF | not_in_book | LED tape / base strip not in the book |  |
| L_BR | line | Lighting | Branch circuits, panels, feeders, lighting controls |  | LS | not_quantified | E plans not issued |  |
| M01 | line | Mechanical | Water-source heat pumps WSHP-1..6 and WSHP-8 (tonnage per M schedule not issued) | 7 | EA | book_row_not_verified | water-source heat pump rows are machine_read; tonnage per M schedule not issued | OT-23814610-2100 / -2140 / -2220 (machine_read) |
| M02 | line | Mechanical | Type I kitchen exhaust hood with fire suppression | 1 | EA | not_in_book | Type I kitchen hood not in the book (removal row only, flagged) | OT-11050510-4750 (flagged, removal) |
| M03 | line | Mechanical | Grease duct in 1-hr rated shaft (room 29) with fire wrap |  | LF | not_quantified | duct LF not drawn; fire wrap not in the book |  |
| M04 | line | Mechanical | Exhaust fan EF-2 and make-up air unit MUA | 2 | EA | spec_not_issued | capacities not available | OT-23733910-0100..0300 (make-up air by MBH, verified) |
| M06 | line | Mechanical | Ductwork, supply/return/exhaust, insulation |  | LF | not_quantified | M sheets not issued |  |
| M07 | line | Mechanical | Dishwasher exhaust duct from first floor through mezzanine |  | LF | not_quantified | M sheets not issued |  |
| M09 | line | Mechanical | Test and balance |  | LS | not_quantified | M sheets not issued |  |
| P02 | component | Plumbing | Lavatories K-2035-8 Pinoir vitreous china with metering faucets -> Lavatory K-2035-8 Pinoir, wall-hung vitreous china 20" x 18", with metering faucet | 2 | EA | book_row_not_matching | drawn: wall-hung lavatory K-2035-8 Pinoir (A-2.20, A-5.12 KN8, KN9); nearest verified row OT-22441613-2900 is a vanity-top vitreous china 20" x 16" bowl, a different mounting; the wall-hung rows are not verified | OT-22441613-2900 (verified, vanity top) |
| P03 | line | Plumbing | Grease interceptor in 1-hr rated enclosure with 6 in clearance | 1 | EA | spec_not_issued | interceptor capacity (GPM) per P sheets not issued; in the replaced table the grease interceptor rows (p514 lines 0150 / 0200 / 1060 / 1120, by GPM) are flagged under an unreadable section header and carry no cost code | p514 lines 0150 / 0200 / 1060 / 1120 (flagged, no cost code) |
| P04 | line | Plumbing | Replace full 4 in sanitary main through kitchen from point of connection upstream of (E) restrooms |  | LF | not_quantified | LF per P sheets not issued |  |
| P05 | line | Plumbing | Floor sinks, floor drains and trenching for new kitchen |  | EA | not_quantified | count per P sheets not issued |  |
| P06 | line | Plumbing | Water, waste, vent and gas rough-in to kitchen and bar equipment |  | LS | not_quantified | K / P sheets not issued |  |
| P07 | line | Plumbing | Water heater |  | EA | not_quantified | P sheets not issued |  |
| V01 | line | Low Voltage | Fire alarm devices and connection to building system |  | LS | not_quantified | no FA drawings issued |  |
| V02 | line | Low Voltage | Sound system, AV, data and security |  | LS | not_quantified | no LV drawings issued |  |
| V03 | line | Low Voltage | Fire sprinkler head relocation / additions at new ceilings and walls |  | EA | not_quantified | head count not countable; F sheets not issued | OT-21131350-3730 (sprinkler head, verified) |
| E01 | line | F&B equipment | Foodservice equipment package: cooking line, refrigeration, prep, dish, walk-ins |  | LS | not_in_book | quote required (K sheets not issued) |  |
| E02 | line | F&B equipment | Bar equipment package (main bar and mezzanine prep bar) |  | LS | not_in_book | quote required |  |
| E03 | line | F&B equipment | Stainless steel countertop on bar diewall at 42 in AFF | 21.79 | LF | not_in_book | no verified stainless steel countertop row |  |
| E04 | line | F&B equipment | Pick-up counter at 34 in AFF (A-5.20 not issued) |  | LF | not_quantified | A-5.20 not issued |  |
| G01 | line | Other required scope | Superintendent, full time | 30 | WK | book_row_not_verified | field personnel rows are flagged | OT-01311320-0240 (superintendent, header/flagged) |
| G02 | line | Other required scope | Project manager, 50% | 15 | WK | book_row_not_verified | field personnel rows are flagged | OT-01311320-0180 (project manager, flagged) |
| G03 | line | Other required scope | Project coordinator / document control, 50% | 15 | WK | not_in_book | no coordinator row |  |
| G04 | line | Other required scope | Pre-construction: RFIs, submittals, sub buy-out, schedule | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G05 | line | Other required scope | Temporary power and lighting | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G06 | line | Other required scope | Temporary toilets, fencing, common-area and elevator protection (occupied building) | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G09 | line | Other required scope | Final / construction clean | 7141 | SF | book_row_not_verified | final clean by GC row is flagged | OT-01741320-0100 (flagged) |
| G10 | line | Other required scope | Small tools, consumables, PPE, SSSP, safety | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G11 | line | Other required scope | Survey / layout / as-built documentation | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G12 | line | Other required scope | Mobilization, loading-zone/street permits, hoisting and one crane day | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G13 | line | Other required scope | Permit expediting (fees excluded) | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G14 | line | Other required scope | Close-out: O&M manuals, commissioning support, warranties | 1 | LS | not_in_book | company lump-sum item; no matching verified row (temporary utility rows carry no cost) |  |
| G15 | line | Other required scope | Dumbwaiter, 2 stops (A-6.30 not issued) | 1 | EA | book_row_not_verified | electric dumbwaiter rows are flagged | OT-14121010-0020 (flagged) |
| G16 | line | Other required scope | ADA vertical wheelchair lift (A-6.20..A-6.22 not issued) - vendor quote (McKinley Equipment / Garaventa ROM on file) | 1 | EA | quote | vendor quote origin (McKinley Equipment e-mail, Garaventa ROM on file); not a book price |  |
| G17 | line | Other required scope | ADA lift pit / shaft base: saw-cut, excavation, concrete, rebar |  | LS | not_quantified | drawings not issued |  |
| G18 | line | Other required scope | Dumbwaiter pit, curb and floor openings at two levels |  | LS | not_quantified | drawings not issued |  |
| G19 | line | Other required scope | Footing / anchor pads for new steel posts |  | EA | not_quantified | drawings not issued |  |
| G20 | line | Other required scope | Equipment and grease-interceptor housekeeping pads |  | LS | not_quantified | drawings not issued |  |
| G21 | line | Other required scope | Core drilling for MEP and GPR scan of slab before cutting |  | LS | not_quantified | drawings not issued |  |
| G23 | line | Other required scope | Grab bars 1-1/2 in dia SS, 36 in and 42 in, mezzanine restrooms | 4 | EA | not_in_book | the only verified grab-bar row (install only) carries no unit and is not usable; material rows not verified | OT-10281313-9996 (unit blank) |
| G24 | line | Other required scope | Surface-mounted toilet tissue dispensers | 2 | EA | not_in_book | no verified toilet tissue dispenser row |  |
| G25 | line | Other required scope | Surface-mounted toilet seat cover dispensers | 2 | EA | not_in_book | verified row OT-10281313-6050 carries unit S.F. (misread) and is not usable | OT-10281313-6050 (unit unreadable) |
| G26 | line | Other required scope | Trash receptacles | 2 | EA | not_in_book | verified row OT-10281313-8100 carries no unit and is not usable | OT-10281313-8100 (unit blank) |
| G31 | line | Other required scope | Interior ADA room-identification and exit signage (other rooms) |  | EA | not_quantified | sign schedule not issued |  |
| G32 | line | Other required scope | Firestopping and rated joints at penetrations of rated walls and shafts |  | LS | not_quantified | penetrations per M/P/E plans not issued |  |
| G33 | line | Other required scope | Rough carpentry, blocking and backing for millwork, accessories and equipment |  | LS | not_quantified | not quantifiable |  |
| G34 | line | Other required scope | Hazardous materials survey (abatement excluded) |  | LS | not_in_book | survey service, no row |  |
| G35 | line | Other required scope | Finish mock-ups and sample approvals |  | LS | not_quantified | not quantifiable |  |

## 5. Open items, RFIs and missing documents

Documents not in the bid set on hand (every line that depends on them is unpriced or in the substitute tier): A-7.10 door and window schedule; A-7.20 / A-7.21 finish schedules; A-2.75 / A-2.76 floor finish plans; A-3.70 light fixture schedule; A-4.15 railing details; A-5.20 enlarged bar plan; A-6.10 / A-6.11 / A-6.12 stair 1; A-6.20 / A-6.21 / A-6.22 ADA lift; A-6.30 dumbwaiter; A-9.10 details; S sheets of the main set; M, P, E (plans), K (foodservice) sheets; Addendum #2.

Open items found in the documents on hand:
- Wall type AC (2 layers each side) and type 3 (exterior plaster) cannot be separated from the class A / class B wall totals; class A studs are priced for types 1 / 2 (substitute), the board as 5/8" Type X each side (exact), class B board as 2 layers each side (substitute: thickness not stated for 1A). The 6" 20 ga / 16 ga studs of class B and of the exit stair walls have no matching verified row (unpriced). AC tags: 8 on A-2.10, 4 on A-2.20; type 3 tags: 4 on A-2.10, 2 on A-2.20.
- Wall heights are the prior estimate's class averages (13.5 / 16.4 / 14.0 ft); the mezzanine finish floor is not dimensioned (model used +9 ft; A-4.34 shows a stair landing at +6'-0"; A-6.11 of the main set not issued).
- Level 5 gypsum finish in public areas (A-2.10 / A-2.20 note) is not separable from the level 4 total.
- The dining room 8'-0" CLG-1D perimeter band on A-3.12 and the mezzanine curved soffits (8 x 15'-9") are not measured; the CLG-1D steel joist framing has no matching verified row (suspended-channel rows are a different system).
- Kitchen hood length: the A-2.10 hood outline is not dimensioned and scales to 13 ft, while M-6 states 18'-3" (prior session finding); M sheets not on hand.
- Stage height: 6 in (A-2.20 keynote 22) vs 10 in (Addendum A-4.30 note 5).
- Poplar moulding at WC-8 is printed 1/2 in x 1/4 in on the Addendum (not 3/4 x 3/4); the only poplar crown row in the book (p203 line 2510) is flagged and carries no cost code in the table on hand, so the moulding is unpriced.
- Lobby floor tile FL-7 / FL-8 vs green room FL-4: the 227 SF group cannot be split without A-2.75.
- Door schedule A-7.10 not issued: 26 new door tags are drawn (12 on A-2.10, 14 on A-2.20); 22 interior leaves are priced in the substitute tier as a steel B-label door in a 4'-0" wide hollow metal frame with a keyed lever lockset; hinges, closers and the rest of the hardware sets are unpriced; panic devices on the 5 exit doors have no matching verified row (hardware-set rows are a different product).
- Exit stair submittal: landing framing (800C162-54 joists, Sure-Board decking), HSS 4x4 posts, pan concrete fill, embedded anchors and the steel enclosure at the stringer have no matching verified row; HSS 8x4 is priced from the 3/8 in wall, 12'-0" piece row (drawn 1/4 in); the pan-stair row is 3'-6" wide with a picket rail (drawn 3'-0").
- Grease interceptor capacity, 4 in sanitary main length, floor sinks/drains, water heater: P sheets not issued (the interceptor rows on p514 are flagged and carry no cost code in the table on hand). The wall-hung lavatory K-2035-8 has no matching verified row (vanity-top rows are a different mounting); only its rough-in is exact.
- WSHP-1..6, WSHP-8, EF-2, MUA: equipment schedule not on hand; the water-source heat pump rows are machine_read.
- Light fixture types (143 tagged fixtures + 62 decorative G fixtures): A-3.70 not issued.
- FE cabinets: 8 carried from the prior estimate; no FE symbols are placed on the A-2.10 / A-2.20 text layers (legend only).
- Restroom accessories: toilet tissue dispenser, seat cover dispenser and waste receptacle rows are verified but carry no usable unit; grab bar material rows are not verified; the robe hook, hand dryer and mirror rows are substitutes (products per A-7.20 not issued).
- Dumbwaiter rows in the book are flagged; the ADA lift is a vendor quote (McKinley Equipment e-mail, Garaventa) and is not priced from the book.
- General conditions: field personnel rows (project manager, superintendent) are flagged in the book; the final-clean row is flagged; temporary utility rows carry no cost. Only continuous daily cleanup (exact) and dumpster rental (substitute: size assumed) are priced.

## 6. Method notes

- Quantities: `takeoff.csv` lists every line with `qty_basis` = drawn (read from a sheet on hand, sheet and keynote cited), prior_estimate (carried from the 2026-10-20 session, transcript file and line cited), inferred (explain) (an arithmetic identity of cited numbers, written out in `qty_source`), or not quantifiable (the dimension or count is on a sheet not issued). No allowances, waste factors, tolerances or ranges were applied.
- Room areas are the prior session's measurements from A-2.10 / A-2.20 (mac_session_page2.txt L265-294); the architect's gross area is 7,141 SF (mac_session_page1.txt L437); the room table sums to 7,908 SF.
- Walls: LF by drawn wall-type tag (A 921 / B 119 / C 20) adopted by the prior session on 2026-10-20; SF = LF x class average height; priced as components on the one-face SF: studs (S.F.), gypsum board per layer (factor 2 for both sides, 4 for two layers each side), batt insulation (S.F.).
- Wall finishes: SF by finish code read by the prior session from the Addendum 1 elevations (mac_session_page2.txt L65-77).
- Light fixture tags were recounted on the RCP text layers this session and match the prior session's counts; new-door tags were read from the plan vectors this session (ovals with 2-digit marks).
- The exit stair (1704 N Vine) is quantified from the PC submittal: 11 risers, 10 treads at 11 in, landing at +6'-0", wall runs and heights as dimensioned.
- Tier test applied to every component: exact only when the verified row is the specified work and product as the issued sheets fix it; substitute when the kind of work matches but the product, size, gauge, type or finish system is not fixed or differs, or the row covers part of the component (match = partial); a row for a different kind of work or product is not used (book_row_not_matching, candidate recorded). Two conversions rest on text printed on the book row itself: the sealer coverage (350 S.F. per gallon in the row's description path) and the HSS piece length (12'-0" in the row's description).
- Cost codes: the book is loaded with all rows per code; a code is used only if exactly one row carries it with status verified and that row's own description matches the pattern recorded for the component (asserted); any other row with the same code is recorded in the reason column.
- Every priced row records cost_code, ref_line, book_page, description_path, book unit, the unit check, the conversion factor, latest_period and the five LA latest-month unit costs; `price.py` asserts that every priced cost code exists in the table with status verified, that it carries a unit and a total, and that material + labor + equipment = total.
- Regenerate: `python3 -I scripts/takeoff.py && python3 -I scripts/price.py [book csv path] && python3 -I scripts/build_outputs.py` from the project folder.
