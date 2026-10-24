# Coverage matrix

Cell format: **validated / unreviewed** observed records (— = none). A cell is only meaningful for the region named; national or state-level rows are counted in the last column and are NOT local data. Counts are computed from `data/csv` at build time.

## Materials — products and price observations

Targets = material spec lines in `capture_targets`. Captured = distinct spec_keys with at least one product.

| category | targets | captured | products | observations | LA County | Other SoCal | Arizona | Nevada |
|---|---|---|---|---|---|---|---|---|
| CAT-CON Concrete | 14 | 0 | 0 | 0 | — | — | — | — |
| CAT-REB Reinforcement | 8 | 0 | 0 | 0 | — | — | — | — |
| CAT-FRM Framing | 33 | 0 | 0 | 0 | — | — | — | — |
| CAT-DRY Drywall | 15 | 0 | 0 | 0 | — | — | — | — |
| CAT-INS Insulation | 6 | 0 | 0 | 0 | — | — | — | — |
| CAT-PNT Painting | 23 | 0 | 0 | 0 | — | — | — | — |
| CAT-HVC HVAC | 30 | 0 | 0 | 0 | — | — | — | — |

Not in the pilot (no spec lines yet): CAT-DEM Demolition, CAT-ROF Roofing, CAT-WPF Waterproofing, CAT-DAW Doors and windows, CAT-FIN Finishes, CAT-FLR Flooring, CAT-PLB Plumbing, CAT-ELE Electrical.

## Labor — statistical wages / determinations / company rates

Rates by trade used in the category (all rate types together; see `labor_rates.rate_type`). Loaded employer cost additionally needs burden items (below).

| category | records expected from | LA County | Other SoCal | Arizona | Nevada | national / state fallback |
|---|---|---|---|---|---|---|
| CAT-CON Concrete | TR-CEM, TR-REB, TR-LAB | — | — | — | — | — |
| CAT-FRM Framing | TR-CARP, TR-LAB | — | — | — | — | 0 / 1 |
| CAT-DRY Drywall | TR-DRYW, TR-TAPE | — | — | — | — | — |
| CAT-INS Insulation | TR-INS | — | — | — | — | — |
| CAT-PNT Painting | TR-PNT | — | — | — | — | — |
| CAT-HVC HVAC | TR-HVAC, TR-SHM | — | — | — | — | — |

## Equipment rates

Only categories whose pilot work items name equipment are listed.

| category | records expected from | LA County | Other SoCal | Arizona | Nevada | national / state fallback |
|---|---|---|---|---|---|---|
| CAT-CON Concrete | EQ-PTROWEL, EQ-CVIB | — | — | — | — | — |
| CAT-HVC HVAC | EQ-HVACVAC | — | — | — | — | — |

## Productivity norms (labor-hours)

| category | work items | norms observed | norms missing |
|---|---|---|---|
| CAT-CON Concrete | 5 | 0 | 5 |
| CAT-FRM Framing | 6 | 0 | 6 |
| CAT-DRY Drywall | 6 | 0 | 6 |
| CAT-INS Insulation | 1 | 0 | 1 |
| CAT-PNT Painting | 4 | 0 | 4 |
| CAT-HVC HVAC | 3 | 0 | 3 |

## Employer burden items

| burden type | records | regions |
|---|---|---|
| employer_benefits | 0 (— validated/unreviewed) | — |
| fica_social_security | 1 (0 / 1 validated/unreviewed) | REG-US |
| fica_medicare | 1 (0 / 1 validated/unreviewed) | REG-US |
| futa | 0 (— validated/unreviewed) | — |
| state_ui | 0 (— validated/unreviewed) | — |
| state_ett | 1 (0 / 1 validated/unreviewed) | REG-US-CA |
| workers_comp | 0 (— validated/unreviewed) | — |

## Cost-component readiness of the pilot work items

How many of the work-item components can currently be priced (strict mode, LA County). Derived from the last calculation runs.

| component kind | components defined | currently priced | blocked (missing input) |
|---|---|---|---|
| material | 55 | 0 | 55 |
| labor | 25 | 0 | 25 |
| equipment | 4 | 0 | 4 |
| other_direct | 0 | 0 | 0 |
