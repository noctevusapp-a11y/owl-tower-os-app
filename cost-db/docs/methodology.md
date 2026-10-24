# Methodology

How the Owl Tower cost database turns sourced data into unit costs and assemblies, and the rules that stop it from inventing or double-counting anything. Everything here is implemented in `pipeline/costdb/` and exercised by `tests/`.

## 1. Two independent status axes

| axis | values | question it answers |
|---|---|---|
| **origin** | `observed` · `derived` · `assumed` · `missing` | where did the value come from? |
| **review_status** | `unreviewed` · `validated` · `flagged` · `rejected` | what did the independent check conclude? |

* `observed` – read from a source record (price listing, wage table, norm table). `derived` – computed by a stored calculation run. `assumed` – an expert proposal (only in the `assumptions` table). `missing` – looked for and not found; the value fields are `NULL` and nothing is inferred.
* **`validated` is hard to get.** Automated rules must pass **and** the source must have been *fetched* (`sources.verification_method = fetched_primary`) **and** the record must carry its evidence excerpt (and a raw-file hash where the table has one). Evidence seen only in search-result summaries can never be promoted (`validate.promote_validated`, enforced again by `tests/test_data_gates.py`).
* `flagged` and `rejected` records are never used by any calculation.

## 2. Calculation modes and run status

| mode | inputs allowed | typical use |
|---|---|---|
| `strict` (default) | observed/derived records that are `validated` (`min_review='validated'`) | the verified part of the database |
| `with_assumptions` | the same, plus **approved** rows of `assumptions` (`status='approved'`, not expired) | explicit what-if calculations; the run is flagged `has_assumptions` |

`min_review='unreviewed'` additionally accepts unreviewed observed records (for exploration; never for the verified part).

| status | meaning |
|---|---|
| `complete` | every input resolved; totals stored |
| `incomplete` | at least one input missing; **no total is stored**; `missing_inputs` lists each gap with reason and how to fill it |
| `failed` | a logical conflict (operator counted twice, norm observed for a different crew size, assembly scope overlap, public-works rate requested for a private project) |

`run_id` is a deterministic hash of target, parameters, calc version and the exact input values, so the same data always reproduces the same id and a changed input produces a new one. Every line stores quantity, unit, unit cost, a readable formula and the ids of all input records.

## 3. Units

Only ids from `units`. **`TON` and `GAL` are never used bare**: `TON_SHORT` (2000 lb), `TON_LONG` (2240 lb), `TON_METRIC` (1000 kg), `TON_REFRIG` (12,000 Btu/h, a *capacity*, not convertible to mass), `GAL_US` (231 in³), `GAL_IMP`. Factors are exact integer ratios (e.g. `GAL_US = 231/1728 CF`, `TON_METRIC = 100000000000/45359237 LB`). `DAY` has no fixed conversion to `HR`: it is the crew's shift length. Original units and the conversion are preserved: a price observation keeps the pack content in the listing's own unit; the engine converts with `price_per_qty_unit = price_per_content_unit / m` where `m` converts quantity from the content unit to the component unit.

## 4. Materials

* A **product** is a manufacturer part. Interchangeability is decided only by **`spec_key`**, built from the attributes the *category* declares required (`categories.required_product_attributes`). Thickness, grade, gauge, fire rating, voltage, capacity, container size etc. are part of the key where they matter; a missing required attribute makes the record impossible to create — equivalence is never guessed.
* **Pack price → unit price → installed system** are separate: `price_amount` is the price of one sale unit; `price_per_content_unit = price_amount / pack_content_qty` (generated column); an installed system exists only as an assembly of work items.
* **Retail ≠ contractor cost.** `price_channel` records the channel; `is_contractor_cost` is allowed only for quote channels. Every run that uses a retail price carries `RETAIL_PRICE_NOT_CONTRACTOR_COST`; unknown tax/delivery inclusion is flagged (`SALES_TAX_UNKNOWN_OR_INCLUDED`, `DELIVERY_UNKNOWN_OR_INCLUDED`). Promotional prices (`promo_flag`) and MSRP are excluded by default.
* **Which price?** For one `spec_key`: the latest eligible observation per product (validated, in the region, channel allowed, not older than `max_price_age_days` unless time-indexed), then the **median across products** (one vote per product, so many observations of one SKU do not outweigh the market). All used observation ids are listed on the line.
* **Coverage** (spread rate, yield) lives in `product_consumption` together with film thickness, coats in the rate and conditions. For a work item that applies `N` coats where the rate refers to `K` coats: `product quantity per unit of area = N × per_qty / (coverage × K)`.
* **Waste**: purchased quantity = `qty × (1 + waste_factor)`. There is **no default waste**; a missing waste factor is a missing input. A waste factor needs a stated basis; an assumed one lives in `assumptions` (`waste:<component_id>`).

## 5. Labor (separate layers, never mixed)

| layer | table / type | contains | applies to |
|---|---|---|---|
| statistical wage | `labor_rates.rate_type = stat_wage` (BLS OEWS, EDD) | hourly mean/median **excluding employer benefits**, overtime, differentials | private work (reference level) |
| prevailing wage | `prevailing_wage` (CA DIR), `federal_wage_determination` (DOL/SAM) | base + fringe breakdown as determined | **public works only** (`use_context = public_works_only`, DB check + engine refusal) |
| company actual | `company_actual` | the company's own total hourly cost | the company's projects |
| burden items | `burden_rates` | FICA, FUTA, UI, ETT, workers' comp, employer benefits — percent, per hour or per $100 payroll, with annual wage caps | added only where the wage layer does not already include them |
| loaded employer cost | `loaded_employer_cost` (always `derived`) | base + fringe + payroll taxes + workers' comp + other, with `derived_from` and `calc_run_id` | costing |

**No double counting.** `includes_fringe / includes_payroll_taxes / includes_workers_comp` on the source rate decide what the engine may still add: a prevailing determination (fringe included) never receives `employer_benefits` again; a statistical wage (no fringe) must receive a benefits item or the run is incomplete. Percent-of-wages items apply to `base_wage` (`burden_base='base_wage'`; `wage_plus_fringe` is selectable and recorded).

**Annual wage caps.** UI/ETT/FUTA apply only to the first part of annual wages (e.g. a $7,000 cap): the hourly equivalent is `rate × min(cap, hourly × annual_paid_hours) / annual_paid_hours`, so the cost is *not* a flat percentage of every hour. `annual_paid_hours` must be passed explicitly (missing input otherwise).

**Public works are not applied to private projects automatically**: `labor_basis='prevailing_loaded'` with `project_type='private'` ends as `failed / PW_NOT_APPLICABLE`.

All hourly rates are per *paid* hour. Non-productive paid time (holidays, weather, travel) is not modelled; if a norm's shift hours are productive hours the difference must be introduced as an explicit factor or in overhead. This is a known limitation, not hidden.

## 6. Productivity, crews and equipment

Three different hours are never mixed:

```
person-hours per unit = crew size × shift hours / daily output
crew-hours per unit   = shift hours / daily output
equipment-hours/unit  = equipment quantity × hours used per shift / daily output
labor cost per unit   = crew labor cost per shift / daily output
equipment cost/unit   = crew equipment cost per shift / daily output
crew labor cost/shift = Σ over members (persons × hours × loaded rate)
```

* A norm is stored with document, edition, page, table, context, crew, shift, daily output, conditions, included and excluded operations (`productivity_observations`). When only person-hours/unit is printed, `daily output = crew size × shift / person-hours` is derived under the *costing crew* and flagged. Labor is **never reconstructed from a finished price**.
* If a norm was observed for a different crew size or shift than the crew used for costing the run **fails** (`CREW_MISMATCH` / `SHIFT_MISMATCH`).
* If no norm exists: `origin = missing`, all numbers `NULL`, `missing_reason` required. Expert proposals go to `assumptions` (`productivity:<component_id>`).
* **Equipment:** rental, ownership, operating, fuel, delivery, minimum rental and `operator_included` are separate fields. If the rate includes the operator and the crew also lists an operator as labor the run **fails** (`OPERATOR_DOUBLE_COUNT`); an operator-needing machine whose rate excludes the operator without an operator in the crew is flagged (`OPERATOR_NOT_PRICED`). Delivery and mobilization are **not** part of hourly unit-cost rates (`EQUIPMENT_DELIVERY_AND_MOBILIZATION_EXCLUDED`).

## 7. Unit costs and assemblies

```
unit cost (direct) = Σ materials [qty × (1+waste) × price]   (price median of latest per product)
                   + labor [crew labor/shift ÷ daily output]
                   + equipment [crew equipment/shift ÷ daily output]
                   + other direct
```

* Each **work item** has a measurable spec (`spec_attributes`), an output unit, and explicit `included_scope` / `excluded_scope`. Shared activities — `mobilization`, `daily_cleanup_and_protection`, `supervision_and_general_conditions`, `sales_tax_and_delivery`, `permits_and_inspections`, `overhead_and_profit` — are **excluded in every work item**, so they can only be added once, at job level. Quantities per unit come from the stated geometry with the derivation stored in `qty_formula` (e.g. studs per SF = (12 in/ft ÷ 16 in o.c.) ÷ wall height).
* An **assembly** needs a non-empty measurable spec, quantities per assembly unit and exact work-item *versions*. Two work items in one assembly that both claim the same included-scope token make the assembly run `failed` (`SCOPE_OVERLAP`). There are no generic "average wall" assemblies.
* **Overhead, contingency and profit are shown separately** and only with a stated basis for every percentage (no defaults):

```
overhead    = direct × oh
contingency = (direct + overhead) × ct
cost        = direct + overhead + contingency
markup m :  price = cost × (1 + m)           margin g :  price = cost / (1 − g)    (g < 1)
m = g / (1 − g)    g = m / (1 + m)           e.g. 25 % markup = 20 % margin; 10 % markup = 9.09 % margin
```

## 8. Region and date

* Three separate dates: price **observation** date, rate **effective period**, and our **retrieval** time.
* **Region:** a material price is used if its region is the target region or inside it. Prices from other regions are used only with `use_region_factors=True` **and** an explicit factor `from_region → to_region` (no chaining). **A local price never receives a regional factor.** Labor/equipment/burden rates may come from the target region or an ancestor (county → metro division → CBSA → state → nation) and the line records `RATE_FROM_ANCESTOR_REGION:<id>`; a rate for a *smaller* area is never stretched over a larger one. Materials, labor and equipment have separate factors (`adjustment_factors.applies_to`).
* **Time:** a price older than `max_price_age_days` (default 365) is unusable unless a time index is supplied: `price_to = price_from × index_to / index_from`, storing original price, both dates, series, both index values, vintages and the formula on the line (`TIME_INDEXED_PRICE`). Index values carry a `vintage_date`; revisions add rows. Indices are never prices of specific products.
* **Conditions** (occupied building, height, ...) need an explicit factor; a requested condition without a factor is a missing input, never silently ignored.
* **Bid prices** (Caltrans, ADOT, NDOT, county bid tabs) are stored in `bid_benchmarks` with a scope note and never feed a calculation.

## 9. Confidence is described, not scored

No percentage is ever assigned. `v_price_confidence_facets` exposes three facts per price: the **source quality tier** (A official dataset with method · B official publication · C manufacturer documentation · D retailer listing · E secondary/aggregator · X unclassified), the **age in days**, and whether the **spec match** is recorded. Every run also lists its flags.

## 10. Source handling and compliance

* Order of attempt: official API → CSV/XLSX → open catalogue → HTML → PDF. Respect robots.txt, rate limits and terms; **never** bypass a CAPTCHA, login or paywall; open no paid accounts, buy no data, contact no supplier on the company's behalf.
* Retailer prices are captured by a person or a licensed/official feed (`capture_method`, `captured_by` are mandatory). The importer refuses automated capture where the source terms are `prohibited`/`restricted_no_automated_access`. No scraper exists in this repository.
* FRED terms bar storing FRED content, so only BLS series *identifiers* seen on FRED are stored; values must be ingested from bls.gov.
* PDF extraction: a text layer does not prove correct column order. `connectors/pdf_tables.py` extracts tables with page numbers and trailing notes, renders sampled cells as highlighted page images for comparison, and warns when the text layer jumps right-to-left on a line.
* Classification: **own stable codes only** (`CAT-`, `TR-`, `EQ-`, work item and assembly codes). CSI MasterFormat/UniFormat/OmniClass numbers and titles are CSI-licensed; the register records their licence terms as prohibited until a licence exists. RSMeans line numbers and descriptions are not used. Crosswalks to public systems (SOC for trades, NAICS) are optional later work.

## 11. Known limitations (read before relying on any number)

1. No primary source could be fetched when this pilot was built; every register entry is search-summary level. Nothing is `validated`.
2. Quantities are derived from the stated geometry only; corners, openings, laps, blocking and similar adders are explicitly excluded in each work item.
3. Waste, labor norms and crew compositions are missing everywhere — runs are `incomplete` by design.
4. The `median across products` policy needs at least one validated observation; with a single SKU the "median" is that SKU's price.
5. Burdens use `base_wage` as the percentage base; rates per *paid* hour (see §5).
6. Region identifiers (FIPS/CBSA) and SOC codes were entered from model knowledge and are marked `assumed / pending_verification`.
