---
title: CEC — How to price a line
type: reference
tags: [estimating, rule]
source: Claude Estimator Construction
build: 2026-10-24
---
# How to price a line (the rule)

1. Find the line by `cost_code` (`OT-<section digits>-<line>`), by `section_id` + `line`, or by searching `description_path`. Check `unit` — the book's unit, not necessarily the takeoff unit.
2. Read `status`. **verified** → usable as a reference. **machine_read** and **flagged** → not verified: open `book_page` in the scan and read the line yourself before using any of its numbers; do not use them with an allowance or a tolerance instead. **percent_add** → an adjustment in % of another line, not a cost.
3. Take the **2022 national bare** columns when you want the book's own number (`material_2022`, `labor_2022`, `equipment_2022`, `total_2022`; `total_incl_op_2022` = with the installing contractor's O&P).
4. Take the **Los Angeles 2026-Q02** columns (`material_la_latest`, `labor_la_latest`, `equipment_la_latest`, `total_la_latest`) for a current budget-level number: component × City Cost Index (LA, book) × BLS factor of that component. The factors used are written on the line (`material_factor_id`, `labor_factor`, …). These are *derived* values: `origin = derived`, unreviewed.
5. Replace whatever you have better data for: a supplier quote replaces the material, the company's own crew cost / output replaces the labor (`labor_hours` × your loaded hourly rate is often the better path), a rental quote replaces the equipment.
6. Add what the book excludes: sales tax on material, delivery, general conditions, contingency, company overhead and profit (the `total_incl_op_*` columns carry only the *installing contractor's* O&P). Never apply a second location or time factor.

## Worked example

`OT-09291030-0590` — GYPSUM BOARD on walls & ceilings | 1/2" thick, on walls, standard, no finish included | Water resistant, no finish included | With compound skim coat (level 5 finish) (book page 336, unit S.F., crew —, 775 S.F./day, 0.021 labor-hours/S.F.)

| component | 2022 national | × CCI LA | × BLS factor | LA latest |
|---|---|---|---|---|
| material | $0.44 | 1.051 | 1.1712 (WPU137) | $0.54 |
| labor | $1.16 | 1.409 | 1.1718 (CIU2012300000000I) | $1.92 |
| equipment | — | 1.409 | 1.3350 (WPU114) | — |
| **total** | $1.60 | | | **$2.46** |

Back to [[Claude Estimator Construction]].
