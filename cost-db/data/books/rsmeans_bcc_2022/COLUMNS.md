# Column dictionary — `book_lines_la_latest.csv` / `.json`

One row per printed line of the unit-price section of *Building Construction Costs with RSMeans data 2022* (the company's
reference copy, 964-page scan), read by two OCR engines plus a geometric reading of every number and settled by the table's
own arithmetic. 2022 values are the book's national bare costs; the `*_la_latest` columns are the company's own derived
estimate for Los Angeles at the latest published index month. Nothing in this table was typed in by hand.

| column | meaning |
|---|---|
| `cost_code` | Owl Tower cost code: `OT-<section digits>-<line>` (e.g. `OT-0922361-30020` is section 09 22 36.13, line 0020). Stable; use this in the software |
| `division`, `division_name` | MasterFormat division number of the section and its standard name |
| `section_id`, `section_title` | the section the line belongs to, as printed (`09 22 36.13 Gypsum Lath`) |
| `line` | the four-digit line number inside the section as printed; `ref_line` = `section_id` + line, for finding the line in the book |
| `description` | the line's own text as printed (OCR-cleaned); `description_path` = the full description obtained by the book's rule "read up through the indents" (ancestors joined with ` | `); `level` = indentation level |
| `crew` | crew code (`1 Carp`, `C-14A`); `crew_source` = `printed` on this line or `carried` from the line above (the book prints it once); `crew_labor_hours_per_day` from the crew table |
| `daily_output` | units installed per crew-day; `labor_hours` = labor-hours per unit (= crew labor-hours / daily output) |
| `unit` | unit of measure as printed (`S.F.`, `L.F.`, `Ea.` ...); `unit_source` printed / carried |
| `material_2022`, `labor_2022`, `equipment_2022`, `total_2022`, `total_incl_op_2022` | the book's 2022 national bare costs per unit and the total including the installing contractor's overhead and profit, as printed (USD). `total_2022` is the printed sum of the three components. `total_incl_op_2022` is empty where the scan's right edge cut the column |
| `ref_note` | the book's reference-section pointer printed on the line (e.g. `R092000-50`) |
| `book_page`, `pdf_page` | where the line is printed (book page = PDF page − 14) |
| `status` | `verified`: every number is supported by at least two of the three readings or by the arithmetic (total = sum; labor = crew cost / output; hours = crew hours / output) and no check failed; `flagged`: a check failed or a cell stayed unreadable — the values shown are the best readings and need a human look; `header`: a description-only line (no cost) |
| `flags` | semicolon list: `*_DERIVED_FROM_SUM` / `*_DERIVED_FROM_CREW*` / `OUTPUT_DERIVED_FROM_LABOR` (a cell computed from the others — informational), `LINE_NUMBER_RECONSTRUCTED` (thousands digit cut at the page edge, restored from the numbering order), `MONEY_UNSETTLED`, `OUTPUT_HOURS_UNSETTLED`, `LABOR_CREW_MISMATCH`, `EQUIP_CREW_MISMATCH`, `CREW_UNKNOWN`, `LINE_NUMBER_MISSING`, `LINE_ORDER`, `TOTAL_OP_IMPLAUSIBLE` (open problems) |
| `conf` | JSON: per numeric cell, the evidence weight behind the kept value (tesseract 1, text layer 1, geometry 3 for the decimal point; ≥ 2 means independent agreement) |
| `cci_row`, `cci_mat_la_2022`, `cci_inst_la_2022` | the book's City Cost Index row used for Los Angeles (900–902) and its material / installation index ÷ 100 |
| `material_factor_id`, `material_factor` | BLS PPI series chosen for the line's material (by division/section and words in the description; see `derive_report.json`) and its value latest ÷ January 2022 |
| `labor_factor_id`, `labor_factor` | ECI total compensation, private construction (`CIU2012300000000I`), latest ÷ 2022-Q1 |
| `equipment_factor_id`, `equipment_factor` | PPI general purpose machinery (`WPU114`), latest ÷ January 2022 (fuel is inside the book's equipment cost and is not escalated separately) |
| `material_la_latest`, `labor_la_latest`, `equipment_la_latest` | component × CCI (LA, 2022) × BLS factor — a derived estimate, `origin = derived`, unreviewed |
| `total_la_latest` | sum of the three derived components (only when every printed component could be derived) |
| `total_incl_op_la_latest` | `total_la_latest` × (`total_incl_op_2022` ÷ `total_2022`), i.e. the book's own markup ratio for the line — a derived estimate |
| `latest_period`, `latest_basis` | the index month the factors end at and the one-line formula |

**What the derived columns are not.** They are not quotes, not Los Angeles prices observed in 2026, and not the book's
prices. They rescale a national 2022 bare cost by the book's location index and by national BLS indices, one factor per
component. Use them as a budget-level reference and replace them with observed prices, quotes and the company's own labor
rates where those exist (that is what the `costdb` database is for).
