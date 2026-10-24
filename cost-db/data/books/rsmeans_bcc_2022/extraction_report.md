# Book table extraction report — Building Construction Costs with RSMeans data 2022 (company reference copy)

Generated 2026-10-24 15:07Z. Scripts: `cost-db/book_ocr/` (OCR, three-reading parser, table builder, derivation, spot check). Data: `cost-db/data/books/rsmeans_bcc_2022/`.

## 1. What was read

* Scan: 964 PDF pages (sha256 `9c5aee73…c075bc`), unit-price section PDF pages 24–750, split into 6 parts and transferred from the owner's Mac.
* OCR: tesseract 5.3 at 360 dpi (own run) **and** the scan's own text layer (a second engine) **and** a geometric reading of every number (digit-glyph count and decimal-point position on the page image). A value is kept only when the readings agree or the table's arithmetic selects it: `total = material + labor + equipment`; `labor-hours = crew labor-hours / daily output`; `labor = crew daily labor cost / output`; `total incl. O&P = 1.10 × material + crew O&P labor / output + 1.10 × equipment`.
* Table pages parsed: **651** of 689 unit-price pages (38 pages with a damaged header are not parsed); sections: **1337**; printed lines: **27296** (priced lines 22521, description-only lines 3900, percentage-add lines 875).
* Crew table (book pages 749–785): 583 crews parsed, 568 pass every identity (member sums, labor-hours, cost per labor-hour); single-trade crews (`1 Carp` …) are built from the trade-rate table (inside back cover: 45 trades, 45 pass the row identities).
* City Cost Index, Los Angeles (900–902), book page 791: 20 rows read from a 300-dpi crop and checked against the image.
* A page that starts in the middle of a section takes the section id of the previous page (`SECTION_CARRIED`, 570 lines) only when its line numbers continue that section's numbering in order and the page's first printed section comes after it; otherwise the lines stay without a section (`SECTION_UNKNOWN`, 1670 lines) and without a cost code.

## 2. Status of the priced lines (the rule)

A line is **verified** only when all of the following hold. Nothing else is called verified; no tolerance is attached to any number.

1. every printed money cell (material, labor, equipment, total) is confirmed by all three readings — both OCR engines and the geometric reading of the digits and the decimal point (evidence weight ≥ 4) — or is computed from the other cells by the book's arithmetic;
2. daily output and labor-hours are confirmed by at least two readings or by the crew rule (crew labor-hours / output);
3. no check is open: the money cells add up, labor agrees with the crew's daily cost, output × hours is a crew-day, the line number is in the section's numbering order, the section id is known, the crew is read, total incl. O&P (where printed) agrees with the components;
4. the money columns are tied: the total was read (so `total = M + L + E` ties the cells to their columns) or the O&P value checks the row or the equipment cell is empty or confirmed by the crew's own equipment cost;
5. an equipment cost on a crew that owns no equipment fails the line (`EQUIP_WITHOUT_CREW_EQUIP`).

**machine_read**: no check failed, but at least one number rests on fewer readings than rule 1–2 demand (for example two readings agree and the third is absent) or the columns are not tied by rule 4. **flagged**: a check failed or a cell stayed unreadable; the values shown are the best readings. Both tiers are *not verified*: read the line on `book_page` before using it.

| status | lines | share of priced |
|---|---|---|
| verified | 10630 | 47.2% |
| machine_read | 3347 | 14.9% |
| flagged | 8544 | 37.9% |

Every verified and machine_read line carries a cost code (0 without one).

By division (verified / machine_read / flagged):

| division | verified | machine_read | flagged |
|---|---|---|---|
| 01 | 258 | 31 | 102 |
| 02 | 245 | 100 | 162 |
| 03 | 690 | 349 | 549 |
| 04 | 363 | 96 | 359 |
| 05 | 673 | 319 | 633 |
| 06 | 1088 | 340 | 472 |
| 07 | 368 | 292 | 412 |
| 08 | 973 | 96 | 672 |
| 09 | 613 | 707 | 532 |
| 10 | 675 | 60 | 291 |
| 11 | 294 | 15 | 134 |
| 12 | 268 | 20 | 131 |
| 13 | 314 | 110 | 213 |
| 14 | 136 | 15 | 99 |
| 21 | 42 | 4 | 27 |
| 22 | 450 | 58 | 349 |
| 23 | 522 | 48 | 438 |
| 26 | 810 | 97 | 339 |
| 27 | 50 | 4 | 39 |
| 28 | 96 | 4 | 43 |
| 31 | 636 | 276 | 470 |
| 32 | 374 | 190 | 273 |
| 33 | 564 | 105 | 348 |
| 34 | 37 | 3 | 17 |
| 35 | 7 | 1 | 5 |
| 41 | 16 | 0 | 4 |
| 44 | 61 | 7 | 34 |
| 46 | 6 | 0 | 5 |
| 48 | 1 | 0 | 7 |

Open flags (one line can carry several):

| flag | lines | meaning |
|---|---|---|
| `CREW_UNREAD` | 2945 | the crew cell is printed but unreadable |
| `OUTPUT_HOURS_UNSETTLED` | 2478 | daily output × labor-hours is not a crew-day |
| `SECTION_UNKNOWN` | 1670 | no section id read on the page and none could be carried from the previous page: the line has no cost code |
| `WEAK_READING` | 1403 | a money cell kept on one reading only (prefix; the cells are named after the colon) |
| `MONEY_UNSETTLED` | 1287 | material/labor/equipment/total do not add up for any combination of readings |
| `OUTPUT_HOURS_MISSING` | 720 | a labor cost is printed but no output/hours were read |
| `LABOR_CREW_MISMATCH` | 699 | labor ≠ crew daily cost / output |
| `OP_MISMATCH` | 375 | total incl. O&P contradicts the components |
| `LINE_ORDER` | 327 | line number out of the section's numbering order (misread) |
| `EQUIP_WITHOUT_CREW_EQUIP` | 301 | an equipment cost on a crew that owns no equipment — the signature of the total slipping one column left |
| `EQUIPMENT_DERIVED_FROM_SUM` | 246 | equipment computed as total − material − labor (no crew confirmation) |
| `OUTPUT_HOURS_AMBIGUOUS` | 100 | two output/hours pairs fit |
| `LINE_NUMBER_MISSING` | 70 | no reading caught the line number |
| `COST_MISSING` | 63 | a crew-day was printed but no cost was read |
| `SECTION_ID_DOUBTFUL` | 62 | numbering restarted under the same section id (one id misread) |
| `MONEY_AMBIGUOUS` | 30 | two combinations add up equally well |

Informational flags (a cell computed from the others by the book's own rules, or a structural note): `EQUIP_CREW_DIFFERS` 1963, `HOURS_DERIVED_FROM_CREW` 1593, `LINE_NUMBER_PARTIAL` 1204, `TOTAL_DERIVED_FROM_SUM` 1106, `LINE_NUMBER_RECONSTRUCTED` 1013, `TOTAL_OP_UNREADABLE` 1004, `PERCENT_ADD` 875, `SECTION_CARRIED` 570, `LABOR_DERIVED_FROM_SUM` 400, `MATERIAL_DERIVED_FROM_SUM` 398, `CREW_UNKNOWN` 236, `OUTPUT_DERIVED_FROM_CREW` 167, `MATERIAL_DERIVED_FROM_CREW_SUM` 93, `OUTPUT_FROM_LABOR_CHECK` 75, `LABOR_DERIVED_FROM_CREW_SUM` 66, `OUTPUT_DERIVED_FROM_LABOR` 44, `MATERIAL_FROM_OP_CHECK` 2

## 3. Spot check against the page images

* **verified** sample (`spot_check/verified/`): 53 rows drawn and compared cell by cell against the page image; 48 of them are in the `verified` tier of this build — **48 of 48 fully correct**.
  * left the tier under the current rule: p577 (no section) 6100 → flagged: ok
  * left the tier under the current rule: p481 (no section) 2700 → flagged: ok
  * left the tier under the current rule: p557 (no section) 1000 → flagged: ok
  * left the tier under the current rule: p322 08 71 20.44 0610 → flagged: wrong:equipment,total (printed total 391.50 landed in the equipment column, total summed to 783; the line now fails EQUIP_WITHOUT_CREW_EQUIP and is flagged) [HOURS_DERIVED_FROM_CREW;TOTAL_DERIVED_FROM_SUM;EQUIP_CREW_DIFFERS;EQUIP_WITHOUT_CREW_EQUIP]
  * left the tier under the current rule: p217 (no section) 2740 → flagged: ok
* **machine_read** sample (`spot_check/machine_read/`): 25 rows drawn and compared cell by cell against the page image; 24 of them are in the `machine_read` tier of this build — **24 of 24 fully correct**.
  * left the tier under the current rule: p349 (no section) 1400 → flagged: ok
* **section_carried** sample (`spot_check/section_carried/`): 12 rows drawn and compared cell by cell against the page image; 12 of them are in the `verified` tier of this build — **12 of 12 fully correct**.

"Fully correct" means every cell printed on the row strip (line number, description, crew, output, hours, unit, the money cells) matches the table. In the `section_carried` sample the carried section id is not visible on the strip: it rests on the numbering rule of section 1 (continuing line numbers, next printed section after it), not on an eye check.

The one wrong verified row found (page 322, 08 71 20.44 0610: the printed total 391.50 landed in the equipment column) is the reason for rules 4–5 above; it is flagged in this build. Residual error types that no arithmetic reaches: a digit misread identically by all readings, a value overlapped by the row above, the cut right edge of the scan (total incl. O&P).

## 4. Derived Los Angeles, latest-month values

* 20913 lines carry a 2022 cost; 20798 got a derived Los Angeles value for 2026-Q02 (10296 of them on verified lines).
* Formula per line: component × City Cost Index (LA, book 2022; material index for material, installation index for labor and equipment) × BLS factor (material: PPI series by material class; labor: ECI total compensation, construction; equipment: PPI machinery). Every factor is written next to the value. `origin = derived`, `review_status = unreviewed`.
* Not escalated separately: fuel inside the equipment cost (the fuel share of a crew's equipment cost is not published). Not applied: any company-specific markup, sales tax, delivery, quantity discounts, current supplier quotes.

## 5. Limits

* The 2022 values are what the book printed, read by machine: the verified set is machine-verified by the rule above, not human-verified line by line; the spot checks in section 3 are the only human-read sample.
* machine_read and flagged lines must be checked against the book page (`book_page`) before use.
* 38 unit-price pages are not parsed (damaged column header); lines on them are absent, not approximated.
* Total incl. O&P is missing on right-hand pages where the scan cut the column; where the crew is known it can be recomputed by the formula above.
* Descriptions are OCR text (cleaned); `description_path` applies the book's indentation rule mechanically and can over-include a sibling line.
* The derived latest values are budget-level references, not prices observed in Los Angeles in 2026.
