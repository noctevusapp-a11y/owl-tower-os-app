# Claude Estimator Construction — Owl Tower cost table (book-derived), build 2026-10-24

**What this is.** A machine-read copy of the unit-price section of the company's reference copy of *Building Construction Costs with RSMeans data 2022* (national bare costs, January 2022), with every line carrying a derived **Los Angeles, 2026-Q02** estimate. Use it as the *reference layer* in the estimating sequence of the bid-estimating skill (step 4, unit pricing): it fills a line when no quote, no company actual and no observed price exists, and it benchmarks the numbers you do have. It is not a quote and not a substitute for the sub bids the skill requires.

## Files

| file | content |
|---|---|
| `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.xlsx` | the table for the office (sheet `lines`, filters on; `sections`; `readme`) |
| `…/book_lines_la_latest.csv` / `.json` | the same table for the software |
| `…/COLUMNS.md` | every column explained |
| `…/extraction_report.md` | how it was read and checked, counts, limits |
| `…/reference/crews_all_2022.csv`, `trade_rates_2022.csv`, `cci_los_angeles_2022.csv` | crews (labor-hours and daily cost per crew), trade rates, Los Angeles city cost index |
| `cost-db/docs/price_update_factors.md` | the BLS/EIA factors 2022-01 → latest, with sources |

## Numbers of this build

* 651 table pages, 1337 sections, 27296 printed lines; **22521 priced lines**: **15049 verified** (67%), 7472 flagged (check the book page before use), 875 percentage-add lines, 3900 description-only lines.
* 20277 lines carry a derived Los Angeles 2026-Q02 value (13446 of them verified).
* Crews: 961 (incl. 378 single-trade crews built from the trade-rate table); trades: 45.

| division | verified | flagged |
|---|---|---|
| 01 General Requirements | 288 | 102 |
| 02 Existing Conditions | 330 | 150 |
| 03 Concrete | 992 | 543 |
| 04 Masonry | 468 | 350 |
| 05 Metals | 992 | 630 |
| 06 Wood, Plastics & Composites | 1422 | 467 |
| 07 Thermal & Moisture Protection | 636 | 380 |
| 08 Openings | 1078 | 610 |
| 09 Finishes | 1302 | 527 |
| 10 Specialties | 763 | 263 |
| 11 Equipment | 297 | 134 |
| 12 Furnishings | 312 | 107 |
| 13 Special Construction | 424 | 213 |
| 14 Conveying Equipment | 165 | 82 |
| 21 Fire Suppression | 46 | 27 |
| 22 Plumbing | 529 | 317 |
| 23 Heating, Ventilating & Air Conditioning | 566 | 409 |
| 26 Electrical | 883 | 320 |
| 27 Communications | 54 | 39 |
| 28 Electronic Safety & Security | 100 | 43 |
| 31 Earthwork | 849 | 445 |
| 32 Exterior Improvements | 565 | 272 |
| 33 Utilities | 590 | 323 |
| 34 Transportation | 40 | 17 |
| 35 Waterway & Marine Construction | 8 | 5 |
| 41 Material Processing & Handling Equipment | 16 | 4 |
| 44 Pollution Control Equipment | 68 | 34 |
| 46 Water & Wastewater Equipment | 6 | 5 |
| 48 Electrical Power Generation | 1 | 7 |

## How to price a line (the rule)

1. Find the line by `cost_code` (`OT-<section digits>-<line>`), by `section_id` + `line`, or by searching `description_path`. Check `unit` — the book's unit, not necessarily the takeoff unit.
2. Read `status`. **verified** → usable as a reference. **flagged** → open `book_page` in the scan and read the line yourself; the values shown are the best readings, one of them may be wrong. **percent_add** → an adjustment in % of another line, not a cost.
3. Take the **2022 national bare** columns when you want the book's own number (`material_2022`, `labor_2022`, `equipment_2022`, `total_2022`; `total_incl_op_2022` = with the installing contractor's O&P).
4. Take the **Los Angeles 2026-Q02** columns (`material_la_latest`, `labor_la_latest`, `equipment_la_latest`, `total_la_latest`) for a current budget-level number: component × City Cost Index (LA, book) × BLS factor of that component. The factors used are written on the line (`material_factor_id`, `labor_factor`, …). These are *derived* values: `origin = derived`, unreviewed.
5. Replace whatever you have better data for: a supplier quote replaces the material, the company's own crew cost / output replaces the labor (`labor_hours` × your loaded hourly rate is often the better path), a rental quote replaces the equipment.
6. Add what the book excludes: sales tax on material, delivery, general conditions, contingency, company overhead and profit (the `total_incl_op_*` columns carry only the *installing contractor's* O&P). Never apply a second location or time factor.

## Worked example

`OT-09291030-0115` — GYPSUM BOARD on walls & ceilings | 1/4" thick, on walls or ceilings, flexible, no finish included (book page 336, unit S.F., crew —, 1050 S.F./day, 0.015 labor-hours/S.F.)

| component | 2022 national | × CCI LA | × BLS factor | LA latest |
|---|---|---|---|---|
| material | $0.32 | 1.051 | 1.1712 (WPU137) | $0.39 |
| labor | $0.86 | 1.409 | 1.1718 (CIU2012300000000I) | $1.42 |
| equipment | — | 1.409 | 1.3350 (WPU114) | — |
| **total** | $1.18 | | | **$1.81** |

## Factors (BLS/EIA, January 2022 → latest)

| series | fits | factor |
|---|---|---|
| `WPU1022` Primary nonferrous metals (PPI) | copper/aluminum content of wire, pipe, flashing: upper bound (raw metal, not finished product) | **2.0528** |
| `WPU1025` Nonferrous mill shapes (PPI) | aluminum/copper products: sheet, extrusions, tube, wire rod | **1.4209** |
| `WPU1017` Steel mill products (PPI) | rebar, structural steel, studs, decking | **0.8801** |
| `WPU0811` Softwood lumber (PPI) | framing lumber | **0.6004** |
| `WPU081` Lumber (PPI) | lumber, all | **0.6985** |
| `WPU133` Concrete products (PPI) | precast, block, pipe | **1.3271** |
| `WPU1332` Concrete pipe (PPI) | concrete pipe | **1.3981** |
| `WPU1333` Ready-mix concrete (PPI) | ready-mix concrete | **1.2768** |
| `WPU137` Gypsum products (PPI) | drywall, plaster | **1.1712** |
| `WPU0622` Paint materials (PPI) | paint and coatings | **1.1876** |
| `WPU114` General purpose machinery and equipment (PPI) | equipment ownership/rental component (not fuel) | **1.3350** |
| `WPU0573` Light fuel oils (PPI) | reference | **1.8588** |
| `WPU057303` No. 2 diesel fuel (PPI) | equipment fuel component (producer price) | **1.8488** |
| `WPUIP2300001` Inputs to construction industries, goods (PPI) | material cost, default when no commodity series fits | **1.2120** |
| `CIU2012300000000I` ECI total compensation, private construction (NSA, current dollar) | labor cost incl. benefits | **1.1718** |
| `CIU2022300000000I` ECI wages and salaries, private construction (NSA, current dollar) | bare wages | **1.1860** |
| `CUUR0000SA0` CPI-U all items, U.S. city average (NSA) | reference only: consumer prices, not construction | **1.1984** |
| `CUURS49ASA0` CPI-U all items, Los Angeles-Long Beach-Anaheim (NSA) | reference only | **1.1910** |
| `eia_diesel_us_monthly.xls` EIA U.S. No. 2 diesel retail price, $/gal, monthly | equipment fuel component (retail, national) | **1.6893** |
| `eia_diesel_california_monthly.xls` EIA California No. 2 diesel retail price, $/gal, monthly | equipment fuel component (retail, California) | **1.6777** |

## Los Angeles City Cost Index (book, 2022, 900–902)

| division | mat. | inst. | total |
|---|---|---|---|
| 015433 Contractor Equipment | — | 106.5 | 106.5 |
| 0241, 31-34 Site & Infrastructure, Demolition | 108.4 | 111.3 | 110.4 |
| 0310 Concrete Forming & Accessories | 99.2 | 140.9 | 132.8 |
| 0320 Concrete Reinforcing | 101.1 | 130.5 | 110.5 |
| 0330 Cast-in-Place Concrete | 110.9 | 131.3 | 117.9 |
| 03 Concrete | 109.6 | 134.8 | 119.7 |
| 04 Masonry | 96.2 | 139.3 | 123.4 |
| 05 Metals | 104.5 | 118.5 | 107.8 |
| 06 Wood, Plastics & Composites | 100.6 | 140.0 | 116.9 |
| 07 Thermal & Moisture Protection | 91.6 | 133.2 | 109.8 |
| 08 Openings | 97.8 | 137.1 | 107.3 |
| 0920 Plaster & Gypsum Board | 105.1 | 140.9 | 127.4 |
| 0950, 0980 Ceilings & Acoustic Treatment | 112.0 | 140.9 | 130.7 |
| 0960 Flooring | 110.6 | 119.8 | 113.4 |
| 0970, 0990 Wall Finishes & Painting/Coating | 98.7 | 121.8 | 112.8 |
| 09 Finishes | 106.8 | 135.1 | 122.2 |
| COVERS Divs. 10-14, 25, 28, 41, 43, 44, 46 | 100.0 | 118.8 | 104.1 |
| 21, 22, 23 Fire Suppression, Plumbing & HVAC | 100.6 | 128.6 | 112.1 |
| 26, 27, 3370 Electrical, Communications & Util. | 94.4 | 130.0 | 111.6 |
| MF2018 Weighted Average | 102.0 | 129.6 | 113.2 |

## Trade rates (book, 2022, union averages of 30 cities, $/h incl. fringes; with O&P)

| abbr | trade | base | with O&P |
|---|---|---|---|
| Skwk | Skilled Workers Average (35 trades) | 58.90 | 88.45 |
| Clab | Common Building Laborers | 45.60 | 67.90 |
| Asbe | Asbestos/Insulation Workers/Pipe Coverers | 63.05 | 96.45 |
| Boil | Boilermakers | 70.50 | 105.25 |
| Bric | Bricklayers | 55.25 | 82.90 |
| Brhe | Bricklayer Helpers | 45.00 | 67.55 |
| Carp | Carpenters | 56.30 | 83.80 |
| Cefi | Cement Finishers | 53.15 | 77.75 |
| Elec | Electricians | 66.20 | 98.40 |
| Elev | Elevator Constructors | 93.55 | 138.50 |
| Eqhv | Equipment Operators, Crane or Shovel | 63.40 | 94.35 |
| Eqmd | Equipment Operators, Medium Equipment | 60.40 | 89.85 |
| Eqlt | Equipment Operators, Light Equipment | 57.00 | 84.80 |
| Eqol | Equipment Operators, Oilers | 54.00 | 80.35 |
| Eqmm | Equipment Operators, Master Mechanics | 63.50 | 94.50 |
| Glaz | Glaziers | 54.00 | 80.25 |
| Lath | Lathers | 56.00 | 81.75 |
| Marb | Marble Setters | 55.05 | 82.60 |
| Mill | Millwrights | 60.55 | 87.50 |
| Mstz | Mosaic & Terrazzo Workers | 53.40 | 78.00 |
| Pord | Painters, Ordinary | 47.80 | 70.85 |
| Psst | Painters, Structural Steel | 48.90 | 78.05 |
| Pape | Paper Hangers | 48.05 | 71.20 |
| Pile | Pile Drivers | 58.20 | 90.05 |
| Plas | Plasterers | 51.40 | 76.40 |
| Plah | Plasterer Helpers | 45.85 | 68.15 |
| Plum | Plumbers | 69.80 | 104.10 |
| Rodm | Rodmen (Reinforcing) | 60.70 | 90.65 |
| Rofc | Roofers, Composition | 49.60 | 80.40 |
| Rots | Roofers, Tile & Slate | 49.60 | 80.40 |
| Rohe | Roofers, Helpers (Composition) | 37.25 | 60.40 |
| Shee | Sheet Metal Workers | 67.55 | 101.75 |
| Spri | Sprinkler Installers | 68.55 | 102.30 |
| Stpi | Steamfitters or Pipefitters | 70.35 | 104.90 |
| Ston | Stone Masons | 55.60 | 83.45 |
| Sswk | Structural Steel Workers | 61.85 | 95.25 |
| Tilf | Tile Layers | 53.15 | 77.65 |
| Tilh | Tile Layers Helpers | 42.80 | 62.55 |
| Trlt | Truck Drivers, Light | 50.40 | 75.30 |
| Trhv | Truck Drivers, Heavy | 53.05 | 79.25 |
| Sswl | Welders, Structural Steel | 61.95 | 95.40 |
| Wrck | *Wrecking | 45.60 | 68.90 |

## Limits (read before quoting from this table)

* Machine-read from a scan; verified means two independent readings or the table arithmetic agree — a random spot check is in `spot_check/` and the rate of fully correct rows is in `extraction_report.md`. Flagged lines are not cleaned up.
* 2022 national averages of union-wage cities; Los Angeles is applied through the book's own index; time through national BLS indices. No supplier, no quantity discount, no tax, no delivery, no company markup.
* Equipment includes fuel in the book; fuel is not escalated separately (diesel rose faster than machinery).
* Descriptions are OCR text; `description_path` applies the book's indentation rule mechanically.
* The company's own observed prices, quotes and crew costs in the `costdb` database always outrank this table.
