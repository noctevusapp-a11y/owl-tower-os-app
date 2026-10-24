# Book table extraction report — Building Construction Costs with RSMeans data 2022 (company reference copy)

Generated 2026-10-24 19:40Z. Scripts: `cost-db/book_ocr/` (OCR, three-reading parser, table builder, derivation, spot check). Data: `cost-db/data/books/rsmeans_bcc_2022/`.

## 1. What was read

* Scan: 964 PDF pages (sha256 `9c5aee73…c075bc`), unit-price section PDF pages 24–750, split into 6 parts and transferred from the owner's Mac.
* Readings of every cell: tesseract 5.3 on the 360-dpi page (T, weight 1) **and** the scan's own text layer, a second engine (I, weight 1) **and** tesseract on the 600-dpi page, a second pass (H, weight 1) **and** a geometric reading of every number (G, weight 3: digit-glyph count and decimal-point position on the page image; it fixes the point of an OCR digit string, it does not invent digits). A value is kept only when the readings agree or the table's arithmetic selects it: `total = material + labor + equipment`; `labor-hours = crew labor-hours / daily output`; `labor = crew daily labor cost / output`; `total incl. O&P = 1.10 × material + crew O&P labor / output + 1.10 × equipment`.
* Second pass over the open lines (`second_pass.py`): a line whose crew cell is unreadable gets the crew only when exactly one crew of the crew table satisfies all identities of the line at once (labor-hours per day, bare daily labor cost, equipment printed iff the crew owns equipment, total incl. O&P where printed) — `CREW_FROM_ARITHMETIC`, 3640 lines; a reading under Equipment on a crew without equipment and nothing under Total is the total that slipped a column (`COLUMN_SLIP_MOVED`, 7 lines, the sum check decides); then every line is re-settled with the four readings.
* Table pages parsed: **692** (every unit-price table page of the scan; on 41 of them the column header was unreadable and the columns were fitted to the page's own number clusters, labelled by the anchors of the neighbouring same-side page: `HEADER_TEMPLATE`); pages without a table skipped: 35 (division intro, Division Notes, reference); sections: **1473**; printed lines: **29629** (priced lines 24117, description-only lines 4563, percentage-add lines 949).
* Crew table (book pages 749–785): 583 crews parsed, 568 pass every identity (member sums, labor-hours, cost per labor-hour); single-trade crews (`1 Carp` …) are built from the trade-rate table (inside back cover: 45 trades, 45 pass the row identities).
* City Cost Index, Los Angeles (900–902), book page 791: 20 rows read from a 300-dpi crop and checked against the image.
* A page that starts in the middle of a section takes the section id of the previous page (`SECTION_CARRIED`, 662 lines) only when its line numbers continue that section's numbering in order and the page's first printed section comes after it; otherwise the lines stay without a section (`SECTION_UNKNOWN`, 761 lines) and without a cost code.

## 2. Status of the priced lines (the rule)

A line is **verified** only when all of the following hold. Nothing else is called verified; no tolerance is attached to any number.

1. every printed number (output, hours, material, labor, equipment, total, total incl. O&P) is **confirmed**: two different engines read exactly the same value (the scan's text layer and tesseract; tesseract at 360 and 600 dpi count as one engine; the geometric reading fixes the decimal point but reads no digits), or an identity of the book determines it from confirmed cells — crew day (output × hours = crew labor-hours), crew labor (labor = crew daily cost / output), O&P (1.10 × M + crew O&P labor / output + 1.10 × E), sum (M + L + E = T): in each identity all cells but one confirm the last; a cell computed by the settle step has no reading and is confirmed only this way;
2. (contained in 1) a daily output / labor-hours pair without a known crew needs both numbers read by two engines: the crew-day rule alone (a multiple of 4 labor-hours) is too weak to decide between readings;
3. no check is open: the money cells add up, labor agrees with the crew's daily cost, output × hours is a crew-day, the line number is in the section's numbering order, the section id is known, the crew is read, total incl. O&P (where printed) agrees with the components;
4. the money columns are tied: the total was read (so `total = M + L + E` ties the cells to their columns) or the O&P value checks the row or the equipment cell is empty or confirmed by the crew's own equipment cost;
5. an equipment cost on a crew that owns no equipment fails the line (`EQUIP_WITHOUT_CREW_EQUIP`).

**machine_read**: no check failed, but at least one number rests on fewer readings than rule 1–2 demand (for example two readings agree and the third is absent) or the columns are not tied by rule 4. **flagged**: a check failed or a cell stayed unreadable; the values shown are the best readings. Both tiers are *not verified*: read the line on `book_page` before using it.

| status | lines | share of priced |
|---|---|---|
| verified | 11378 | 47.2% |
| machine_read | 3285 | 13.6% |
| flagged | 9454 | 39.2% |

Every verified and machine_read line carries a cost code (0 without one).

By division (verified / machine_read / flagged):

| division | verified | machine_read | flagged |
|---|---|---|---|
| 01 | 265 | 44 | 122 |
| 02 | 382 | 115 | 250 |
| 03 | 817 | 253 | 476 |
| 04 | 389 | 112 | 305 |
| 05 | 703 | 364 | 551 |
| 06 | 1114 | 245 | 689 |
| 07 | 346 | 193 | 671 |
| 08 | 803 | 206 | 787 |
| 09 | 837 | 452 | 614 |
| 10 | 626 | 99 | 306 |
| 11 | 573 | 98 | 360 |
| 12 | 285 | 37 | 180 |
| 13 | 328 | 96 | 242 |
| 14 | 122 | 25 | 111 |
| 21 | 61 | 3 | 20 |
| 22 | 441 | 93 | 346 |
| 23 | 468 | 110 | 409 |
| 26 | 964 | 116 | 290 |
| 27 | 17 | 26 | 23 |
| 28 | 100 | 12 | 32 |
| 31 | 611 | 278 | 499 |
| 32 | 426 | 119 | 290 |
| 33 | 541 | 162 | 350 |
| 34 | 60 | 5 | 38 |
| 35 | 7 | 3 | 6 |
| 41 | 37 | 0 | 19 |
| 44 | 53 | 14 | 35 |
| 46 | 0 | 5 | 7 |
| 48 | 2 | 0 | 6 |

Open flags (one line can carry several):

| flag | lines | meaning |
|---|---|---|
| `OUTPUT_HOURS_UNSETTLED` | 2952 | daily output × labor-hours is not a crew-day |
| `CREW_UNREAD` | 2376 | the crew cell is printed but unreadable |
| `MONEY_UNSETTLED` | 1586 | material/labor/equipment/total do not add up for any combination of readings |
| `WEAK_READING` | 1244 | a money cell kept on one reading only (prefix; the cells are named after the colon) |
| `LINE_NUMBER_MISSING` | 1129 | no reading caught the line number |
| `SECTION_ID_DOUBTFUL` | 1041 | the line numbering restarted under a section id: a new section began whose header line (id) was unreadable, so the lines from the restart on carried the previous id — they get no section id and no cost code |
| `OP_MISMATCH` | 1033 | total incl. O&P contradicts the components |
| `LABOR_CREW_MISMATCH` | 924 | labor ≠ crew daily cost / output |
| `SECTION_UNKNOWN` | 761 | no section id read on the page and none could be carried from the previous page: the line has no cost code |
| `OUTPUT_HOURS_MISSING` | 648 | a labor cost is printed but no output/hours were read |
| `LINE_ORDER` | 379 | line number out of the section's numbering order (misread) |
| `EQUIPMENT_DERIVED_FROM_SUM` | 265 | equipment computed as total − material − labor (no crew confirmation) |
| `EQUIP_WITHOUT_CREW_EQUIP` | 223 | an equipment cost on a crew that owns no equipment — the signature of the total slipping one column left |
| `OUTPUT_HOURS_AMBIGUOUS` | 173 | two output/hours pairs fit |
| `LINE_NUMBER_DUPLICATE` | 118 | another line carries the same section and line number without doubt: this line's cost code is removed (a code names one printed line) |
| `COST_MISSING` | 61 | a crew-day was printed but no cost was read |
| `MONEY_AMBIGUOUS` | 16 | two combinations add up equally well |

Informational flags (a cell computed from the others by the book's own rules, or a structural note): `OUTPUT_HOURS_CREW_CHECK` 13315, `LABOR_CREW_OK` 13277, `OP_CHECK_OK` 11199, `CREW_FROM_ARITHMETIC` 3640, `EQUIP_CREW_DIFFERS` 2436, `LINE_NUMBER_PARTIAL` 1909, `HEADER_TEMPLATE` 1727, `UNIT_UNREAD` 1051, `TOTAL_DERIVED_FROM_SUM` 967, `PERCENT_ADD` 949, `TOTAL_OP_UNREADABLE` 859, `SECTION_CARRIED` 662, `LABOR_DERIVED_FROM_SUM` 455, `MATERIAL_DERIVED_FROM_SUM` 425, `LINE_NUMBER_ASSUMED` 332, `LINE_NUMBER_RECONSTRUCTED` 276, `HOURS_DERIVED_FROM_CREW` 232, `CREW_UNKNOWN` 157, `OUTPUT_FROM_LABOR_CHECK` 123, `OUTPUT_DERIVED_FROM_LABOR` 79, `LABOR_DERIVED_FROM_CREW_SUM` 73, `MATERIAL_DERIVED_FROM_CREW_SUM` 68, `OUTPUT_DERIVED_FROM_CREW` 14, `COLUMN_SLIP_MOVED` 7, `MATERIAL_FROM_OP_CHECK` 3, `OUTPUT_FROM_CREW_CHECK` 1

## 3. Spot check against the page images

* **verified_final** sample (`spot_check/verified_final/`): 49 rows drawn and compared cell by cell against the page image; 47 of them are in the `verified` tier of this build — **47 of 47 fully correct**.
  * left the tier under the current rule: p537 22 42 33.20 0972 → flagged: ok
  * left the tier under the current rule: p73 03 11 13.65 1050 → flagged: ok
* **verified_round3** sample (`spot_check/verified_round3/`): 56 rows drawn and compared cell by cell against the page image; 50 of them are in the `verified` tier of this build — **50 of 50 fully correct**.
  * left the tier under the current rule: p654 31 23 23.20 1480 → machine_read: ok
  * left the tier under the current rule: p270 07 71 23.10 6300 → machine_read: ok
  * left the tier under the current rule: p226 06 25 13.10 2200 → machine_read: ok
  * left the tier under the current rule: p624 27 13 23.13 0080 → machine_read: ok
  * left the tier under the current rule: p87 03 21 05.10 1900 → flagged: ok
  * left the tier under the current rule: p346 09 22 36.23 4900 → machine_read: ok
* **verified_round2** sample (`spot_check/verified_round2/`): 46 rows drawn and compared cell by cell against the page image; 35 of them are in the `verified` tier of this build — **35 of 35 fully correct**.
  * left the tier under the current rule: p604 26 09 13.30 0220 → machine_read: ok
  * left the tier under the current rule: p480 13 24 16.50 2500 → machine_read: ok
  * left the tier under the current rule: p514 22 05 23.20 1270 → flagged: ok
  * left the tier under the current rule: p480 13 24 16.50 0400 → machine_read: wrong:hours (printed 14, table 44: two readings 14/44 both pass the crew-day rule without a crew) []
  * left the tier under the current rule: p474 13 05 05.70 0620 → machine_read: ok
  * left the tier under the current rule: p274 07 72 26.10 0450 → machine_read: ok
  * left the tier under the current rule: p210 06 16 36.10 3800 → machine_read: wrong:material,labor (printed M .44 L .75; material unread, labor derived from the sum) [LABOR_DERIVED_FROM_SUM]
  * left the tier under the current rule: p454 12 05 05.10 3130 → flagged: wrong:material,total (printed T 24.50 O&P 36; O&P slipped into the total column, material computed from it) [MONEY_UNSETTLED;OUTPUT_HOURS_CREW_CHECK;LABOR_CREW_OK;EQUIP_CREW_DIFFERS;EQUIP_WITHOUT_CREW_EQUIP]
  * left the tier under the current rule: p418 10 75 16.10 3400 → machine_read: ok
  * left the tier under the current rule: p637 31 22 13.20 0120 → machine_read: ok
  * left the tier under the current rule: p732 34 71 13.17 1400 → flagged: ok
* **verified_round1** sample (`spot_check/verified_round1/`): 39 rows drawn and compared cell by cell against the page image; 29 of them are in the `verified` tier of this build — **29 of 29 fully correct**.
  * left the tier under the current rule: p304 08 41 13.20 1650 → machine_read: ok
  * left the tier under the current rule: p304 08 41 13.20 2250 → machine_read: ok
  * left the tier under the current rule: p433 11 41 13.20 8410 → flagged: wrong:output,hours (printed 5.60 / 4.643; output token merged with the hours digits, hours derived from the crew) [HEADER_TEMPLATE;OUTPUT_HOURS_UNSETTLED;LABOR_CREW_OK;OP_CHECK_OK]
  * left the tier under the current rule: p274 07 72 26.10 0200 → flagged: ok
  * left the tier under the current rule: p85 03 15 19.30 0140 → flagged: ok
  * left the tier under the current rule: p169 05 42 23.50 1100 → machine_read: ok
  * left the tier under the current rule: p656 31 23 23.20 9230 → machine_read: ok
  * left the tier under the current rule: p200 06 11 10.14 0460 → flagged: ok
  * left the tier under the current rule: p474 13 05 05.70 0620 → machine_read: ok (final build: output 175 as printed, now machine_read)
  * left the tier under the current rule: p268 07 65 13.10 9300 → machine_read: ok
* **machine_read_final** sample (`spot_check/machine_read_final/`): 13 rows drawn and compared cell by cell against the page image; 7 of them are in the `machine_read` tier of this build — **6 of 7 fully correct**.
  * left the tier under the current rule: p70 03 11 13.35 2050 → flagged: wrong:output (printed 509, table 507) [OUTPUT_HOURS_AMBIGUOUS]
  * left the tier under the current rule: p151 05 12 23.75 7300 → verified: ok
  * left the tier under the current rule: p58 02 83 19.23 0220 → verified: ok
  * left the tier under the current rule: p599 26 05 90.10 3130 → verified: ok
  * left the tier under the current rule: p389 09 96 56.20 2500 → verified: ok
  * left the tier under the current rule: p487 13 34 19.50 7350 → verified: ok
* **machine_read_round1** sample (`spot_check/machine_read_round1/`): 11 rows drawn and compared cell by cell against the page image; 3 of them are in the `machine_read` tier of this build — **3 of 3 fully correct**.
  * left the tier under the current rule: p207 06 12 10.10 0530 → verified: ok
  * left the tier under the current rule: p637 31 14 13.23 1300 → verified: ok
  * left the tier under the current rule: p373 09 72 13.10 1600 → verified: ok
  * left the tier under the current rule: p674 32 12 16.13 0170 → verified: ok
  * left the tier under the current rule: p90 03 22 11.10 0600 → verified: ok
  * left the tier under the current rule: p51 02 42 10.20 4010 → verified: ok
  * left the tier under the current rule: p351 09 29 10.30 1800 → verified: ok
  * left the tier under the current rule: p731 34 71 13.17 2000 → verified: ok
* **header_template** sample (`spot_check/header_template/`): 11 rows drawn and compared cell by cell against the page image; 9 of them are in the `verified` tier of this build — **9 of 9 fully correct**.
  * left the tier under the current rule: p582 23 83 16.10 1640 → machine_read: ok
  * left the tier under the current rule: p61 02 87 19.10 0300 → machine_read: wrong:output,hours (printed 43 / .372; output token merged with the hours digits) [HEADER_TEMPLATE;OUTPUT_FROM_LABOR_CHECK;OP_CHECK_OK]
* **header_template_round1** sample (`spot_check/header_template_round1/`): 13 rows drawn and compared cell by cell against the page image; 11 of them are in the `verified` tier of this build — **11 of 11 fully correct**.
  * left the tier under the current rule: p79 03 15 05.80 0500 → flagged: wrong:material,total (printed 77 77 84.50; 7 read as 1 by both engines, O&P check lost) [HEADER_TEMPLATE;MATERIAL_DERIVED_FROM_SUM;OP_MISMATCH]
  * left the tier under the current rule: p435 11 44 13.10 7500 → machine_read: ok
* **whole_hours** sample (`spot_check/whole_hours/`): 12 rows drawn and compared cell by cell against the page image; 10 of them are in the `verified` tier of this build — **10 of 10 fully correct**.
  * left the tier under the current rule: p537 22 42 33.20 0880 → flagged: ok
  * left the tier under the current rule: p605 26 22 13.10 2700 → machine_read: ok
* **whole_hours_round1** sample (`spot_check/whole_hours_round1/`): 12 rows drawn and compared cell by cell against the page image; 6 of them are in the `verified` tier of this build — **6 of 6 fully correct**.
  * left the tier under the current rule: p276 07 81 16.10 0470 → flagged: ok
  * left the tier under the current rule: p528 22 13 29.14 0500 → flagged: ok
  * left the tier under the current rule: p466 12 56 43.10 1850 → flagged: ok
  * left the tier under the current rule: p418 10 75 16.10 0800 → machine_read: ok
  * left the tier under the current rule: p579 23 81 93.10 1060 → flagged: ok
  * left the tier under the current rule: p629 28 23 13.10 4200 → flagged: ok
* **crew_arithmetic** sample (`spot_check/crew_arithmetic/`): 14 rows drawn and compared cell by cell against the page image; 12 of them are in the `verified` tier of this build — **12 of 12 fully correct**.
  * left the tier under the current rule: p164 05 41 13.30 5330 → machine_read: ok
  * left the tier under the current rule: p272 07 71 23.30 5320 → machine_read: ok
* **crew_arithmetic_round1** sample (`spot_check/crew_arithmetic_round1/`): 16 rows drawn and compared cell by cell against the page image; 15 of them are in the `verified` tier of this build — **15 of 15 fully correct**.
  * left the tier under the current rule: p542 22 52 33.10 1500 → flagged: ok
* **unit_second_reading** sample (`spot_check/unit_second_reading/`): 11 rows drawn and compared cell by cell against the page image; 9 of them are in the `verified` tier of this build — **9 of 9 fully correct**.
  * left the tier under the current rule: p527 22 13 16.60 1400 → flagged: ok
  * left the tier under the current rule: p232 06 48 16.10 3600 → machine_read: ok
* **verified_v1** sample (`spot_check/verified_v1/`): 53 rows drawn and compared cell by cell against the page image; 38 of them are in the `verified` tier of this build — **38 of 38 fully correct**.
  * left the tier under the current rule: p317 08 71 20.15 2000 → flagged: ok
  * left the tier under the current rule: p653 31 23 23.20 1296 → machine_read: ok
  * left the tier under the current rule: p661 31 41 13.10 1600 → flagged: ok
  * left the tier under the current rule: p467 12 61 13.13 2200 → flagged: ok
  * left the tier under the current rule: p655 (no section) 1710 → machine_read: ok
  * left the tier under the current rule: p404 10 22 33.10 1500 → machine_read: ok
  * left the tier under the current rule: p552 23 13 13.23 3070 → flagged: ok
  * left the tier under the current rule: p557 (no section) 1000 → flagged: ok
  * left the tier under the current rule: p322 08 71 20.44 0610 → flagged: wrong:equipment,total (printed total 391.50 landed in the equipment column, total summed to 783; the line now fails EQUIP_WITHOUT_CREW_EQUIP and is flagged) [MONEY_UNSETTLED;HOURS_DERIVED_FROM_CREW;LABOR_CREW_OK]
  * left the tier under the current rule: p653 31 23 23.20 1240 → flagged: ok
  * left the tier under the current rule: p68 03 11 13.20 3000 → machine_read: ok
  * left the tier under the current rule: p535 22 41 39.10 2810 → machine_read: ok
  * left the tier under the current rule: p217 (no section) 2740 → flagged: ok
  * left the tier under the current rule: p192 06 05 23.60 6146 → flagged: ok
  * left the tier under the current rule: p589 26 05 19.20 0400 → machine_read: ok
* **machine_read_v1** sample (`spot_check/machine_read_v1/`): 25 rows drawn and compared cell by cell against the page image; 13 of them are in the `machine_read` tier of this build — **13 of 13 fully correct**.
  * left the tier under the current rule: p349 (no section) 1400 → verified: ok
  * left the tier under the current rule: p364 09 64 29.10 7600 → verified: ok
  * left the tier under the current rule: p90 03 21 21.11 0250 → verified: ok
  * left the tier under the current rule: p176 05 53 13.70 0438 → verified: ok
  * left the tier under the current rule: p659 31 25 14.16 1250 → verified: ok
  * left the tier under the current rule: p373 09 72 16.13 3000 → verified: ok
  * left the tier under the current rule: p683 32 31 13.25 0380 → verified: ok
  * left the tier under the current rule: p369 09 66 33.19 3500 → verified: ok
  * left the tier under the current rule: p308 08 51 66.10 0900 → verified: ok
  * left the tier under the current rule: p359 09 51 33.10 0140 → verified: ok
  * left the tier under the current rule: p337 09 01 90.93 0770 → verified: ok
  * left the tier under the current rule: p140 05 05 21.15 1935 → verified: ok
* **section_carried_v1** sample (`spot_check/section_carried_v1/`): 12 rows drawn and compared cell by cell against the page image; 9 of them are in the `verified` tier of this build — **9 of 9 fully correct**.
  * left the tier under the current rule: p651 31 23 23.20 0514 → machine_read: ok
  * left the tier under the current rule: p280 07 92 19.10 0045 → machine_read: ok
  * left the tier under the current rule: p651 31 23 23.20 0344 → machine_read: ok

"Fully correct" means every cell printed on the row strip (line number, description, crew, output, hours, unit, the money cells) matches the table. In the `section_carried` sample the carried section id is not visible on the strip: it rests on the numbering rule of section 1 (continuing line numbers, next printed section after it), not on an eye check.

Every wrong verified row found in a round became a rule before the next round, so the rows marked wrong above have left the tier (the slipped total, the merged output token, the output computed from rounded hours, the carried unit, the dropped O&P, the off-grid reading, the material pinned by a slipped O&P, the component derived beside an unread one, and the output/hours pair decided by weights alone). The one wrong verified row found first (page 322, 08 71 20.44 0610: the printed total 391.50 landed in the equipment column) is the reason for rules 4–5 above; it is flagged in this build. Residual error types that no arithmetic reaches: a digit misread identically by all readings, a value overlapped by the row above, the cut right edge of the scan (total incl. O&P).

## 4. Derived Los Angeles, latest-month values

* 22393 lines carry a 2022 cost; 22252 got a derived Los Angeles value for 2026-Q02 (11045 of them on verified lines).
* Formula per line: component × City Cost Index (LA, book 2022; material index for material, installation index for labor and equipment) × BLS factor (material: PPI series by material class; labor: ECI total compensation, construction; equipment: PPI machinery). Every factor is written next to the value. `origin = derived`, `review_status = unreviewed`.
* Not escalated separately: fuel inside the equipment cost (the fuel share of a crew's equipment cost is not published). Not applied: any company-specific markup, sales tax, delivery, quantity discounts, current supplier quotes.

## 5. Limits

* The 2022 values are what the book printed, read by machine: the verified set is machine-verified by the rule above, not human-verified line by line; the spot checks in section 3 are the only human-read sample.
* machine_read and flagged lines must be checked against the book page (`book_page`) before use.
* The crew id is confirmed by two identities only (labor-hours per day, daily labor cost). Crews that differ only in equipment (B-13 / B-13B / B-13C) satisfy both; between them the OCR text of the crew cell decides, and the printed equipment column does not reproduce the crew table closely enough to arbitrate (`EQUIP_CREW_DIFFERS` is informational). A crew suffix can therefore be wrong on a verified line while every number on it is right.
* Line numbers cut at the left edge of the scan (one or two leading digits lost) are restored only when exactly one value with that tail fits between the previous and the next fully read line numbers of the section (`LINE_NUMBER_RECONSTRUCTED`); otherwise the line keeps no number and is flagged (`LINE_NUMBER_MISSING`).
* Total incl. O&P is missing on right-hand pages where the scan cut the column; where the crew is known it can be recomputed by the formula above.
* Descriptions are OCR text (cleaned); `description_path` applies the book's indentation rule mechanically and can over-include a sibling line.
* The derived latest values are budget-level references, not prices observed in Los Angeles in 2026.
