# Worked examples

> **SYNTHETIC INPUTS — NOT MARKET DATA.** Sections 1–6 use invented round numbers (a $12.80 sheet, a $40/h crew rate ...) so every figure can be checked by hand. They show the *method*, not Los Angeles prices. They live in `tests/fixtures/` and can never enter `data/` (tests and the validator reject them). Section 7 uses the real data and shows what the engine refuses to compute without sourced inputs.

Regenerate: `python3 examples/run_examples.py`.

## 1. Unit cost — hang 1/2 in regular gypsum board on wood studs (`WI-DRY-001`, per SF)

Real work-item definition; synthetic prices, waste factors and labor data.

| input | synthetic value |
|---|---|
| board pack | 4x8 sheet = 32 SF at $12.80 → $0.40/SF; waste 10 % |
| screws | box of 500 at $5.00 → $0.01 each; 0.75 screws/SF (from geometry); waste 5 % |
| crew | 2 × drywall installer at $40/h + 1 laborer at $30/h, 8 h shift |
| norm | 1,600 SF per crew-day |

**Result** — status `complete`, unit `SF`

| # | kind | description | quantity (incl. waste; labor = person-hours) | unit | unit cost | per unit of result | origin |
|---|---|---|---|---|---|---|---|
| 1 | material | Gypsum board 1/2 in regular 4x8 | 1.1 | SF | 0.4 | 0.440000 | mixed |
| 2 | material | Coarse-thread drywall screws #6 x 1-1/4 in | 0.7875 | EA | 0.01 | 0.007875 | mixed |
| 3 | labor | Labor: Hang 1/2 in regular gypsum board on wood studs @16 in, walls | 0.015 | HR | 0.55 | 0.550000 | observed |

Hand check:

```
board   = 1 SF × (1 + 0.10) × (12.80 / 32)          = 0.44
screws  = 0.75 EA × (1 + 0.05) × (5.00 / 500)         = 0.007875
labor   = (2×40 + 1×30) × 8 h / 1600 SF = 880 / 1600  = 0.55
total                                                  = 0.997875 per SF
person-hours per SF = 3 × 8 / 1600 = 0.015;  crew-hours per SF = 8 / 1600 = 0.005
```

Engine: `direct_cost_total = 0.997875`  · run id `RUN-10370fdc3506` (deterministic) · warnings: RETAIL_PRICE_NOT_CONTRACTOR_COST

The retail-price warning is deliberate: this is not a contractor purchase price.

## 2. Overhead, contingency, profit — markup versus margin

With a direct cost of $100.00 (round number for the example), overhead 10 % of direct, contingency 5 % of (direct + overhead):

| step | markup 10 % | margin 10 % |
|---|---|---|
| Direct cost | 100.00 | 100.00 |
| Overhead (0.10) | 10.00 | 10.00 |
| Contingency (0.05) | 5.50 | 5.50 |
| Cost incl. overhead and contingency | 115.50 | 115.50 |
| Profit | 11.55 | 12.83 |
| Price | 127.05 | 128.33 |

```
markup m = 10 %:  price = cost × (1 + m)  = 115.50 × 1.10   = 127.05
margin g = 10 %:  price = cost / (1 − g)  = 115.50 / 0.90   = 128.33
a 25 % markup is a 20 % margin;  a 20 % margin needs a 25 % markup
```

Each percentage must be passed with a stated basis; there are no defaults.

## 3. Loaded labor rate from layered inputs (statistical wage + burdens)

Synthetic: wage $30.00/h (metro-division level, used for the county and flagged), benefits 25 % of wages, Social Security 6.2 % (cap $200,000), Medicare 1.45 %, FUTA 0.6 % / CA UI 3.4 % / ETT 0.1 % each on the first $7,000, workers' comp $8.00 per $100 payroll, 2,080 paid hours per year.

| component | $/paid hour |
|---|---|
| base_wage | 30.0000 |
| employer_benefits | 7.5000 |
| fica_social_security | 1.8600 |
| fica_medicare | 0.4350 |
| futa | 0.0202 |
| state_ui | 0.1144 |
| state_ett | 0.0034 |
| workers_comp | 2.4000 |
| **loaded total** | **42.3330** |

Note the capped items: UI = 0.034 × 7,000 / 2,080 = $0.1144/h — a cap makes the hourly cost tiny, it is **not** 3.4 % of wages. Warnings: RATE_FROM_ANCESTOR_REGION:REG-MD-31084.

## 4. Prevailing wage is not applied to private projects

Requesting `labor_basis='prevailing_loaded'` with `project_type='private'` → status `failed`, code `PW_NOT_APPLICABLE`: *prevailing/federal wage rates apply to public works only; this run is project_type='private'*

For a public-works run the determination already contains fringe, so the engine adds payroll taxes and workers' comp but **not** employer benefits again (see `tests/test_calc.py::test_prevailing_wage_does_not_add_benefits_twice`).

## 5. Bringing an old price forward with an index

The same board price observed 2025-06-01 is 510 days old (limit 365). Without an index the run is `incomplete` (`PRICE_MISSING`). With a synthetic monthly index series (200 in 2025-06, 210 in 2026-10) the engine stores both dates, the series, both index values and the formula on the line:

```
price_to = price_from × index_to / index_from = 0.40 × 210 / 200 = 0.42 per SF
line = 1 SF × (1 + 0.10) × 0.42 = 0.462000
```

The index is an input to a conversion, never a price in itself; a regional factor is never applied to an already-local price.

## 6. Assembly from versioned unit costs

Synthetic assembly = 2.0 SF of `WI-DRY-001` + 3 EA of a synthetic $2.00 widget work item, per SF.

**Result** — status `complete`, unit `SF`

| # | kind | description | quantity (incl. waste; labor = person-hours) | unit | unit cost | per unit of result | origin |
|---|---|---|---|---|---|---|---|
| 1 | assembly_component | Hang 1/2 in regular gypsum board on wood studs @16 in, walls | 2 | SF | 0.997875 | 1.995750 | derived |
| 2 | assembly_component | TEST widget install | 3 | EA | 2 | 6.000000 | derived |

```
2 × 0.997875 + 3 × 2.00 = 7.995750
```

A second work item that claims the same included-scope token as the first turns the run into `failed / SCOPE_OVERLAP` (double counting), see `tests/test_calc.py::test_scope_overlap_is_a_double_counting_failure`.

## 7. The real pilot data: what the engine refuses to compute

`ASM-WALL-001` — interior partition, 2x4 wood studs @16 in, 1/2 in regular gypsum each side, Level 4, primer + 2 eggshell coats each side (per SF of wall), Los Angeles County, strict mode, real data (no synthetic input).

Status: **`incomplete`**, total: **None** (none is stored). Missing inputs reported: **31**

| code | count |
|---|---|
| WASTE_MISSING | 9 |
| PRICE_MISSING | 9 |
| CREW_MISSING | 5 |
| PRODUCTIVITY_MISSING | 5 |
| CONSUMPTION_MISSING | 3 |

First items:

- `ASC-675dc69f6a>WIC-447321943c` **WASTE_MISSING** — waste factor for 2x4 precut studs: no waste/loss factor recorded (zero is only acceptable with a stated basis)
- `ASC-675dc69f6a>WIC-447321943c` **PRICE_MISSING** — validated price observation for spec CAT-FRM-LBR|grade=stud|length_in=92.625|moisture_state=kd|nominal_size=2x4|product_type=precut_stud|species_group=df-l|treatment=none: no observation exists
- `ASC-675dc69f6a>WIC-97ede1d1b6` **WASTE_MISSING** — waste factor for 2x4 plate stock (1 bottom + 2 top): no waste/loss factor recorded (zero is only acceptable with a stated basis)
- `ASC-675dc69f6a>WIC-97ede1d1b6` **PRICE_MISSING** — validated price observation for spec CAT-FRM-LBR|grade=#2|length_in=96|moisture_state=kd|nominal_size=2x4|product_type=dimension_lumber|species_group=df-l|treatment=none: no observation exists
- `ASC-675dc69f6a>WIC-5c3b587d46` **WASTE_MISSING** — waste factor for 16d nails, stud ends and top-plate lamination: no waste/loss factor recorded (zero is only acceptable with a stated basis)
- `ASC-675dc69f6a>WIC-5c3b587d46` **PRICE_MISSING** — validated price observation for spec CAT-FRM-FAS|diameter_or_gauge=0.148 in|drive=not_applicable|fastener_type=nail|finish_or_material=vinyl_coated|head_type=flat|length_in=3.25|thread_type=smooth: no observation exists

Each gap names what to capture; closing the gaps (prices, waste factors, crew and norm, manufacturer coverage) turns the run `complete` without any code change.

