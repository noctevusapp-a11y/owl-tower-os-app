# Book table extraction report — Building Construction Costs with RSMeans data 2022 (company reference copy)

Generated 2026-10-24 08:30Z. Scripts: `cost-db/book_ocr/` (OCR, three-reading parser, table builder, derivation, spot check). Data: `cost-db/data/books/rsmeans_bcc_2022/`.

## 1. What was read

* Scan: 964 PDF pages (sha256 `9c5aee73…c075bc`), unit-price section PDF pages 24–750, split into 6 parts and transferred from the owner's Mac.
* OCR: tesseract 5.3 at 360 dpi (own run) **and** the scan's own text layer (a second engine) **and** a geometric reading of every number (digit-glyph count and decimal-point position on the page image). A value is kept only when the readings agree or the table's arithmetic selects it: `total = material + labor + equipment`; `labor-hours = crew labor-hours / daily output`; `labor = crew daily labor cost / output`; `total incl. O&P = 1.10 × material + crew O&P labor / output + crew O&P equipment / output`.
* Table pages parsed: **651**; sections: **1337**; printed lines: **27296** (priced lines 22521, description-only lines 3900, percentage-add lines 875).
* Crew table (book pages 749–785): 583 crews parsed, 568 pass every identity (member sums, labor-hours, cost per labor-hour); single-trade crews (`1 Carp` …) are built from the trade-rate table (inside back cover: 45 trades, 45 pass the row identities).
* City Cost Index, Los Angeles (900–902), book page 791: 20 rows read from a 300-dpi crop and checked against the image.

## 2. Status of the priced lines

| status | lines | share |
|---|---|---|
| verified (every number supported by ≥ 2 readings or the arithmetic, no open check) | 15049 | 66.8% |
| flagged (a check failed or a cell stayed unreadable; values shown are best readings) | 7472 | 33.2% |

By division (verified / flagged):

| division | verified | flagged |
|---|---|---|
| 01 | 288 | 102 |
| 02 | 330 | 150 |
| 03 | 992 | 543 |
| 04 | 468 | 350 |
| 05 | 992 | 630 |
| 06 | 1422 | 467 |
| 07 | 636 | 380 |
| 08 | 1078 | 610 |
| 09 | 1302 | 527 |
| 10 | 763 | 263 |
| 11 | 297 | 134 |
| 12 | 312 | 107 |
| 13 | 424 | 213 |
| 14 | 165 | 82 |
| 21 | 46 | 27 |
| 22 | 529 | 317 |
| 23 | 566 | 409 |
| 26 | 883 | 320 |
| 27 | 54 | 39 |
| 28 | 100 | 43 |
| 31 | 849 | 445 |
| 32 | 565 | 272 |
| 33 | 590 | 323 |
| 34 | 40 | 17 |
| 35 | 8 | 5 |
| 41 | 16 | 4 |
| 44 | 68 | 34 |
| 46 | 6 | 5 |
| 48 | 1 | 7 |

Open flags (one line can carry several):

| flag | lines | meaning |
|---|---|---|
| `CREW_UNREAD` | 2945 | the crew cell is printed but unreadable |
| `OUTPUT_HOURS_UNSETTLED` | 2478 | daily output × labor-hours is not a crew-day |
| `MONEY_UNSETTLED` | 1287 | material/labor/equipment/total do not add up for any combination of readings |
| `LABOR_CREW_MISMATCH` | 699 | labor ≠ crew daily cost / output |
| `OP_MISMATCH` | 375 | total incl. O&P contradicts the components |
| `LINE_ORDER` | 317 | line number out of the section's numbering order (misread) |
| `OUTPUT_HOURS_AMBIGUOUS` | 100 | two output/hours pairs fit |
| `LINE_NUMBER_MISSING` | 70 | no reading caught the line number |
| `SECTION_ID_DOUBTFUL` | 62 | numbering restarted under the same section id (one id misread) |
| `MONEY_AMBIGUOUS` | 30 | two combinations add up equally well |

Informational flags (a cell computed from the others by the book's own rules): `EQUIP_CREW_DIFFERS` 1963, `HOURS_DERIVED_FROM_CREW` 1593, `LINE_NUMBER_PARTIAL` 1204, `TOTAL_DERIVED_FROM_SUM` 1106, `TOTAL_OP_UNREADABLE` 1004, `LINE_NUMBER_RECONSTRUCTED` 1002, `PERCENT_ADD` 875, `OUTPUT_HOURS_MISSING` 720, `WEAK_READING:total` 434, `LABOR_DERIVED_FROM_SUM` 400, `MATERIAL_DERIVED_FROM_SUM` 398, `WEAK_READING:labor` 351, `WEAK_READING:material` 296, `EQUIPMENT_DERIVED_FROM_SUM` 246, `CREW_UNKNOWN` 236, `OUTPUT_DERIVED_FROM_CREW` 167, `WEAK_READING:equipment` 105, `MATERIAL_DERIVED_FROM_CREW_SUM` 93, `WEAK_READING:labor,total` 88, `OUTPUT_FROM_LABOR_CHECK` 75, `LABOR_DERIVED_FROM_CREW_SUM` 66, `COST_MISSING` 63, `WEAK_READING:material,total` 58, `OUTPUT_DERIVED_FROM_LABOR` 44, `WEAK_READING:material,labor` 24, `WEAK_READING:material,labor,total` 14, `WEAK_READING:equipment,total` 11, `WEAK_READING:material,equipment` 9, `WEAK_READING:labor,equipment` 7, `WEAK_READING:labor,equipment,total` 4, `MATERIAL_FROM_OP_CHECK` 2, `WEAK_READING:material,equipment,total` 1, `WEAK_READING:material,labor,equipment,total` 1

## 3. Spot check against the page images

Random sample of verified rows cut out of the page images and compared cell by cell by the author: **40 of 42 rows fully correct** (see `spot_check/`). Residual error types seen: a digit misread identically by both OCR engines (1↔7), a value overlapped by the row above, the cut right edge of the scan (total incl. O&P). These survive only where no arithmetic check reaches the cell.

## 4. Derived Los Angeles, latest-month values

* 20392 lines carry a 2022 cost; 20277 got a derived Los Angeles value for 2026-Q02 (13446 of them on verified lines).
* Formula per line: component × City Cost Index (LA, book 2022; material index for material, installation index for labor and equipment) × BLS factor (material: PPI series by material class; labor: ECI total compensation, construction; equipment: PPI machinery). Every factor is written next to the value. `origin = derived`, `review_status = unreviewed`.
* Not escalated separately: fuel inside the equipment cost (diesel rose 1.7–1.85×; the fuel share is not published). Not applied: any company-specific markup, sales tax, delivery, quantity discounts, current supplier quotes.

## 5. Limits

* The 2022 values are what the book printed, read by machine: the verified set is machine-verified, not human-verified line by line.
* Lines marked flagged must be checked against the book page (`book_page`) before use.
* Total incl. O&P is missing on right-hand pages where the scan cut the column; where the crew is known it can be recomputed by the formula above.
* Descriptions are OCR text (cleaned); `description_path` applies the book's indentation rule mechanically and can over-include a sibling line.
* The derived latest values are budget-level references, not prices observed in Los Angeles in 2026.
