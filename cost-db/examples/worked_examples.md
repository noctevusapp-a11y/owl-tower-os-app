# Worked examples

> **SYNTHETIC INPUTS — NOT MARKET DATA.** Sections 1–6b use invented round numbers (a $12.80 sheet, a $40/h crew rate ...) so every figure can be checked by hand. They show the *method*, not Los Angeles prices. They live in `tests/fixtures/` and can never enter `data/` (tests and the validator reject them). Section 7 uses the real data and shows what the engine refuses to compute without sourced inputs.

Regenerate: `python3 examples/run_examples.py`.

## 1. Unit cost — hang 1/2 in regular gypsum board on wood studs (`WI-DRY-001`, per SF)

Real work-item definition; synthetic prices, waste factors and labor data.

| input | synthetic value |
|---|---|
| board pack | 4x8 sheet = 32 SF at $12.80 → $0.40/SF; waste 10 % |
| screws | box of 500 at $5.00 → $0.01 each; 0.875 screws/SF (from geometry: 4 fastener lines × 7 screws per 4x8 sheet, screw at both ends, 28 ÷ 32 SF); waste 5 % |
| crew | 2 × drywall installer at $40/h + 1 laborer at $30/h, 8 h shift |
| norm | 1,600 SF per crew-day |
| run options | strict mode; `accept_retail_proxy=True` (the synthetic prices are labelled retail; retail is never used unless asked for); company labor rate |

**Result** — status `complete`, unit `SF`

| # | kind | description | quantity (incl. waste; labor = person-hours) | unit | unit cost | per unit of result | origin |
|---|---|---|---|---|---|---|---|
| 1 | material | Gypsum board 1/2 in regular 4x8 | 1.1 | SF | 0.4 | 0.440000 | mixed |
| 2 | material | Coarse-thread drywall screws #6 x 1-1/4 in | 0.91875 | EA | 0.01 | 0.009188 | mixed |
| 3 | labor | Labor: Hang 1/2 in regular gypsum board on wood studs @16 in, walls | 0.015 | HR | 0.55 | 0.550000 | observed |

Hand check:

```
board   = 1 SF × (1 + 0.10) × (12.80 / 32)          = 0.44
screws  = 0.875 EA × (1 + 0.05) × (5.00 / 500)        = 0.0091875
labor   = (2×40 + 1×30) × 8 h / 1600 SF = 880 / 1600  = 0.55
total                                                  = 0.9991875 per SF (stored rounded to 6 decimals: 0.999188)
person-hours per SF = 3 × 8 / 1600 = 0.015;  crew-hours per SF = 8 / 1600 = 0.005
```

Engine: `direct_cost_total = 0.999188`  · run id `RUN-108a79791e25` (deterministic) · warnings: PRICE_NOT_TIME_ADJUSTED, RETAIL_PRICE_NOT_CONTRACTOR_COST

Run basis recorded on the run: `price_basis = retail_proxy`, `input_review_floor = validated`.
The retail-price warning is deliberate: this is not a contractor purchase price.

## 2. Overhead, contingency, profit — markup versus margin

With a direct cost of $100.00 (round number for the example), overhead 10 % of direct, contingency 5 % of (direct + overhead). The price goes to `price_total`; `direct_cost_total` keeps the direct cost, and percentages outside 0–1 (e.g. `10` meaning 10 %) are refused:

| step | markup 10 % | margin 10 % |
|---|---|---|
| Direct cost | 100.00 | 100.00 |
| Overhead (0.10) - example only | 10.00 | 10.00 |
| Contingency (0.05) - example only | 5.50 | 5.50 |
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

The same board price observed 2025-06-01 is 510 days old. With an explicit age limit of 365 days and no index the run is `incomplete` (`PRICE_MISSING`); without any limit the price would be used unadjusted and flagged `PRICE_NOT_TIME_ADJUSTED`. With a synthetic monthly index series (200 in 2025-06, 205 in 2026-09, 210 in 2026-10) the engine adjusts EVERY price whose month differs from the as-of month, stores both dates, the series, both index values and the formula on the line (if the as-of month is not yet published it falls back to the latest published period and says so with `INDEX_LATEST_PUBLISHED_PERIOD_USED`). The series must apply to the same cost kind (a labor index cannot adjust a material price):

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
| 1 | assembly_component | Hang 1/2 in regular gypsum board on wood studs @16 in, walls | 2 | SF | 0.999188 | 1.998376 | derived |
| 2 | assembly_component | TEST widget install | 3 | EA | 2 | 6.000000 | derived |

```
2 × 0.999188 + 3 × 2.00 = 7.998376
```

A second work item that claims the same included-scope token as the first turns the run into `failed / SCOPE_OVERLAP` (double counting), see `tests/test_calc.py::test_scope_overlap_is_a_double_counting_failure`. Each child is priced for its OWN quantity (assembly quantity × quantity per assembly unit), so quantity tiers and quantity factors are chosen on the right number.

## 6b. Coverage-based material: each spread rate is paired with ITS OWN product's price

`WI-PNT-001` — prime new gypsum board, one coat of PVA primer. The quantity of primer comes from the manufacturer's spread rate, not from a typed number. Synthetic: product A $100 per 5 US gal ($20/gal) covers 400 SF/gal; product B $200 per 5 US gal ($40/gal) covers 200 SF/gal; both are the same spec line.

```
A: 1/400 gal/SF × $20 = 0.05 $/SF
B: 1/200 gal/SF × $40 = 0.20 $/SF
line = median of the two paired costs = 0.125 $/SF
```

Engine: material line `extended_cost = 0.1250000000`, `quantity = None` (none: the two products consume different quantities), warnings ['MEDIAN_OF_2_PRODUCTS', 'PRICE_NOT_TIME_ADJUSTED', 'RETAIL_PRICE_NOT_CONTRACTOR_COST']. A coverage given in SY (or any other area unit) is converted to the work item's SF; several coverage rows that differ in film thickness need a `consumption_selector`, otherwise the run is incomplete (`CONSUMPTION_AMBIGUOUS`).

## 7. The real pilot data: what the engine refuses to compute

`ASM-WALL-001` — interior partition, 2x4 wood studs @16 in, 1/2 in regular gypsum each side, Level 4, primer + 2 eggshell coats each side (per SF of wall), Los Angeles County, strict mode, real data (no synthetic input).

Status: **`incomplete`**, total: **None** (none is stored). Missing inputs reported: **37**

| code | count |
|---|---|
| WASTE_MISSING | 9 |
| PRICE_MISSING | 9 |
| DEFINITION_NOT_REVIEWED | 6 |
| CREW_MISSING | 5 |
| PRODUCTIVITY_MISSING | 5 |
| CONSUMPTION_MISSING | 3 |

First items:

- `ASM-WALL-001` **DEFINITION_NOT_REVIEWED** — assembly ASM-WALL-001 v1: definition review_status=unreviewed: scope, specification and quantities have not been checked by a reviewer
- `ASC-675dc69f6a11>WI-FRM-001` **DEFINITION_NOT_REVIEWED** — work item WI-FRM-001 v1: definition review_status=unreviewed: scope, specification and quantities have not been checked by a reviewer
- `ASC-675dc69f6a11>WIC-447321943cb9` **WASTE_MISSING** — waste factor for 2x4 precut studs: no waste/loss factor recorded (zero is only acceptable with a stated basis)
- `ASC-675dc69f6a11>WIC-447321943cb9` **PRICE_MISSING** — validated price observation for spec CAT-FRM-LBR|grade=stud|length_in=92.625|moisture_state=kd|nominal_size=2x4|product_type=precut_stud|species_group=df-l|treatment=none: no usable product or observation exists
- `ASC-675dc69f6a11>WIC-97ede1d1b637` **WASTE_MISSING** — waste factor for 2x4 plate stock (1 bottom + 2 top): no waste/loss factor recorded (zero is only acceptable with a stated basis)
- `ASC-675dc69f6a11>WIC-97ede1d1b637` **PRICE_MISSING** — validated price observation for spec CAT-FRM-LBR|grade=#2|length_in=96|moisture_state=kd|nominal_size=2x4|product_type=dimension_lumber|species_group=df-l|treatment=none: no usable product or observation exists

Each gap names what to capture; closing the gaps (prices, waste factors, crew and norm, manufacturer coverage) turns the run `complete` without any code change.

