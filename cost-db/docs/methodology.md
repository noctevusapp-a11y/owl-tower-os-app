# Methodology

How the Owl Tower cost database turns sourced data into unit costs and assemblies, and the rules that stop it from inventing or double-counting anything. Everything here is implemented in `pipeline/costdb/` (engine `calc.py`, shared enumerations `enums.py`, rules `validate.py`) and the PostgreSQL schema `schema/001_schema.sql`, and is exercised by `tests/` — including one regression test for every defect that the independent reviews found (`tests/test_review_fixes.py`).

## 1. Two independent status axes

| axis | values | question it answers |
|---|---|---|
| **origin** | `observed` · `derived` · `assumed` · `missing` | where did the value come from? |
| **review_status** | `unreviewed` · `validated` · `flagged` · `rejected` | what did the independent check conclude? |

* `observed` – read from a source record (price listing, wage table, norm table). `derived` – computed by a stored calculation run. `assumed` – an expert proposal (only in the `assumptions` table). `missing` – looked for and not found; the value fields are `NULL` and nothing is inferred.
* **`validated` is hard to get, and the database enforces it, not only Python.** The promotion gate (`validate.promote_validated`) requires: no error-level validation issue, a source that was really *fetched* (`verification_method = fetched_primary`) whose terms allow data use, and every evidence field the table needs (`validate.EVIDENCE_FIELDS`). `index_values` inherit the source of their series. In PostgreSQL a `validated` row must also carry `reviewed_by` and `reviewed_at` (CHECK), must come from a fetched source (trigger `check_source_usable`, `check_index_value_source`), and every change of `review_status` is written to the append-only `review_events` log (who, when, old, new). Evidence seen only in search-result summaries can never be promoted.
* `flagged` and `rejected` records are never used by any calculation — **in any table the engine reads**: observations, products, sources, crews, indices and index values, labor/burden/equipment rates, productivity norms, coverage rows, factors, assumptions and the work-item/assembly definitions themselves. One function (`Engine._why_not`) applies the same usability test to all of them, so a rule cannot be remembered for one table and forgotten for another.
* **Restricted sources.** `enums.NO_DATA_USE = (prohibited, restricted_no_storage, licence_required)`: values from such a source are never stored (importer, DB trigger), never promoted and never used in a calculation; `restricted_no_automated_access` allows only manual capture. The set is defined once and imported by the engine, validator, importer and tests.

## 2. Calculation modes, run status, run records

| mode | inputs allowed | typical use |
|---|---|---|
| `strict` (default) | observed/derived records that are `validated` (`min_review='validated'`), **no assumption of any kind** | the verified part of the database |
| `with_assumptions` | the same, plus **approved**, unexpired, four-eyes (`approved_by ≠ proposed_by`), unique-per-reference rows of `assumptions` of the right type, unit and range | explicit what-if calculations; the run is flagged `has_assumptions` |

`min_review='unreviewed'` additionally accepts unreviewed observed records (exploration; never for the verified part); it is recorded on the run as `input_review_floor`.

| status | meaning |
|---|---|
| `complete` | every input resolved; totals stored |
| `incomplete` | at least one input missing; **no total is stored**; `missing_inputs` lists each gap with code, reason and how to fill it |
| `failed` | a logical conflict (operator counted twice, norm observed for another crew size, scope overlap or duplicate cost tag in an assembly, public-works rate for a private project, wrong index series, retired or rejected definition, contradictory source rate) |

* **Definitions are gated too.** A work item or assembly that is `retired`, not yet valid at `as_of`, or flagged/rejected makes the run `failed`; an unreviewed definition makes it `incomplete` (`DEFINITION_NOT_REVIEWED`): a person other than the author must check scope, specification and quantities before a strict result can be called verified. Components flagged `is_optional` are priced only with `include_optional=True` and are listed in the warnings otherwise.
* `run_id` is a deterministic hash of target, parameters, calc version (a hash of the code that computes) and **every line with its inputs and every missing input**. The same data reproduces the same id; a different observation, rate or gap gives a different one. Every line stores quantity, unit, `quantity_kind` (`material_qty` · `person_hours` · `crew_hours` · `equipment_hours` · `work_item_qty`), unit cost, a readable formula and the ids of all input records. Calculation runs and lines are append-only in the database (a `complete` run must have lines that add up to its total, checked at commit).
* **`RunParams` are validated** (unknown enumeration values, non-positive quantities, retail channels without opt-in … raise immediately). Result-affecting thresholds have **no hidden defaults**: `max_price_age_days`, `max_rate_age_days` are off unless set; validator screening thresholds are a documented policy (`validate.DEFAULT_POLICY`, each with its basis) that never changes a calculation.
* **Knowledge date.** Rows retrieved after `known_at` (default: `as_of`) are unknown to the run, so re-running an old `as_of` after back-filling data does not use the back-filled rows.

## 3. Units

Only ids from `units`. **`TON` and `GAL` are never used bare**: `TON_SHORT` (2000 lb), `TON_LONG` (2240 lb), `TON_METRIC` (1000 kg), `TON_REFRIG` (12,000 Btu/h, a *capacity*, not convertible to mass), `GAL_US` (231 in³), `GAL_IMP`; spec attributes use the qualified names (`cooling_capacity_ton_refrig`, `container_gal_us`). The qualifier is an enumerated CHECK that rejects a bare TON/GAL (NULL-safe) and the table is immutable after load. Factors are exact integer ratios (e.g. `GAL_US = 231/1728 CF`). `DAY` has no fixed conversion to `HR`: it is the crew's shift length. Original units and the conversion are preserved: a price observation keeps the pack content in the listing's own unit; the engine converts with `price_per_qty_unit = price_per_content_unit / m`. The three kinds of hours are different quantities (`quantity_kind`) even though all use the unit `HR`.

## 4. Materials

* A **product** is a manufacturer part. Interchangeability is decided only by **`spec_key`**, built from the attributes the *category* declares required (`categories.required_product_attributes`). Thickness, grade, gauge, fire rating, voltage, capacity, container size etc. are part of the key where they matter; a missing required attribute makes the record impossible to create — equivalence is never guessed. The same key is recomputed **in SQL** (`compute_spec_key`) and a trigger refuses a product whose key does not match its attributes, a product in a non-leaf category, and an observation whose pack differs from its product's pack (a different pack is a different SKU). Products are append-only. Python and SQL normalisation are tested for equality on every pilot spec line and on edge values (`'5_8'`, `'NaN'`, `'1e3'` are strings, never numbers).
* **Pack price → unit price → installed system** are separate: `price_amount` is the price of one sale unit; `price_per_content_unit = price_amount / pack_content_qty` (generated column); an installed system exists only as an assembly of work items.
* **Retail ≠ contractor cost; retail is an explicit opt-in.** Default channels are `public_price_list`, `pro_account_quote`, `distributor_quote`, `supplier_quote`. Retail channels need `RunParams.accept_retail_proxy=True`; the run then records `price_basis = retail_proxy` (or `mixed`), and the lines carry `RETAIL_PRICE_NOT_CONTRACTOR_COST`. `is_contractor_cost` is allowed only for quote channels. Unknown tax/delivery inclusion is flagged. Promotional prices and MSRP are excluded by default.
* **Which price?** Per product: the best usable observation — ranked by region class (exact region first), then newest `observed_at`, newest `retrieved_at` (parsed as an instant), then id. Across the products of one `spec_key` only the best region class present is kept, then the **median of per-product costs** (`price_policy='median_of_latest_per_product'`) or the single latest (`'latest'`). Quantity-tier prices (`qty_tier_min`, in pack-content units) are used only when `RunParams.quantity` shows the order reaches the tier. Every used observation is listed on the line with region, store, retrieval time, tax/delivery flags and age.
* **Coverage** (spread rate, yield) lives in `product_consumption` with film thickness, coats in the rate and conditions. **Each product's coverage is paired with that same product's price**: `product quantity per output unit = coats_applied × per_qty / (coverage × [coverage unit → output unit] × coats_in_rate)`, cost per product, then the median of those costs. Several usable coverage rows for one product/application that differ in film thickness or conditions are ambiguous: the run is incomplete until the component carries a `consumption_selector` (or the wrong row is superseded). A line whose products consume different quantities has no single quantity, so none is invented.
* **Waste**: purchased quantity = `qty × (1 + waste_factor)`. There is **no default waste**; a missing waste factor is a missing input. A waste factor needs a stated basis; an assumed one lives in `assumptions` (`waste:<component_id>`, a fraction in [0,1)).

## 5. Labor (separate layers, never mixed)

| layer | table / type | contains | applies to |
|---|---|---|---|
| statistical wage | `labor_rates.rate_type = stat_wage` (BLS OEWS, EDD) | hourly mean/median **excluding employer benefits**, overtime, differentials | private work (reference level) |
| prevailing wage | `prevailing_wage` (CA DIR), `federal_wage_determination` (DOL/SAM) | base + fringe (+ stated payroll tax, workers' comp, other) as determined | **public works only** |
| company actual | `company_actual` | the company's own total hourly cost; **must not include overhead or profit** (`includes_overhead/profit` rows are refused as cost inputs) | the company's projects |
| burden items | `burden_rates` | FICA, FUTA, UI, ETT, workers' comp, employer benefits — percent, per hour or per $100 payroll, with annual wage caps | added only where the wage layer does not already include them |
| loaded employer cost | `loaded_employer_cost` (always `derived`) | base + fringe + payroll taxes + workers' comp + other, with `derived_from` and `calc_run_id`; region and period are those of the governing wage record | costing |

* **Selecting a rate.** Only straight-time, non-apprentice rows; for prevailing wages the regime (`wage_regime` state/federal) and project class (`wage_class`) must match; `classification` picks one classification when a source lists several. Best = nearest region (exact, then ancestors), then newest period; a tie between rows that differ in value is `LABOR_RATE_AMBIGUOUS`, never a silent pick. A statistical or company rate used on a `public_works` run is flagged `PUBLIC_WORKS_NOT_ON_PREVAILING_BASIS`.
* **No double counting.** `includes_fringe / includes_payroll_taxes / includes_workers_comp` on the source rate decide what the engine may still add. A source that says it includes a component uses **that record's own stated amount** (`fringe_hr`, `payroll_tax_hr`, `workers_comp_hr`, `other_employer_cost_hr`); if it claims to include a component and states none, only a fully loaded record with a stated total is accepted (`LOADED_RATE_NOT_ITEMIZED`), a stated total that contradicts its components is a `failed` conflict. Percent-of-wages items apply to `base_wage` (`burden_base='wage_plus_fringe'` is selectable and recorded).
* **Burdens.** Best burden row = nearest region, then trade-specific over generic, then newest effective date; a tie with different values is `BURDEN_AMBIGUOUS` (workers' comp: pass `wc_class_code`). The payroll-tax types required depend on the state of the region (`enums.BASE_PAYROLL_TYPES` + e.g. CA ETT), so an Arizona run does not need a California item. `general_liability` and `other` burdens are never added silently: they are reported as `OMITTED_BURDEN:<type>` (they usually belong to overhead).
* **Annual wage caps.** UI/ETT/FUTA apply only to the first part of annual wages: the hourly equivalent is `rate × min(cap, hourly × annual_paid_hours) / annual_paid_hours`. `annual_paid_hours` must be passed explicitly.
* **Public works are not applied to private projects automatically**: `labor_basis='prevailing_loaded'` with `project_type='private'` ends as `failed / PW_NOT_APPLICABLE`.

All hourly rates are per *paid* hour; non-productive paid time is not modelled (known limitation).

## 6. Productivity, crews and equipment

```
person-hours per unit = Σ over labor members (persons × hours) / daily output      (= crew size × shift / output for a uniform crew)
crew-hours per unit   = shift hours / daily output
equipment-hours/unit  = Σ over the component's equipment members (qty × hours) / daily output
labor cost per unit   = crew labor cost per shift / daily output
equipment cost/unit   = cost of the component's equipment members per shift / daily output
crew labor cost/shift = Σ over members (persons × hours × loaded rate)
```

* A norm is stored with document, edition, page, table, context, crew, shift, daily output, conditions, included and excluded operations. When only person-hours/unit is printed, `daily output = crew size × shift / person-hours` is derived under the *costing crew* and flagged. Labor is **never reconstructed from a finished price**. Crew size and person-hours come from the crew's composition, not from the members whose rate happened to resolve.
* A norm recorded for another work item, crew, crew size or shift makes the run **fail** (`PRODUCTIVITY_WORK_ITEM_MISMATCH`, `CREW_MISMATCH`, `SHIFT_MISMATCH`). A productivity condition factor scales cost **and** reported person-hours.
* If no norm exists: `origin = missing`, all numbers `NULL`. Expert proposals go to `assumptions` (`productivity:<component_id>`, with a unit convertible to the work-item unit).
* **Equipment.** An equipment component is bound to an equipment type that must be a member of its crew (`CREW_NO_EQUIPMENT`, otherwise it would cost 0). Rental/ownership/operating are separate from fuel (`fuel_included=false` adds `fuel_cost_hr`; no fuel price = `FUEL_NOT_PRICED` gap; unknown = `FUEL_INCLUSION_UNKNOWN` flag). A day rate (`equipment_basis='rental_day'`) is charged once per crew shift and says so. **Delivery/pickup and mobilization are not part of unit cost**: the amount found on the rate is shown as `EQUIPMENT_DELIVERY_PICKUP_EXCLUDED:<amount>`, the minimum rental period as `MIN_RENTAL_PERIOD_ASSUMED_MET`. Operators are recognised by the `is_operator` flag **or** the operator trade `TR-OPR`; an operator-inclusive rate plus an operator in the crew is `failed / OPERATOR_DOUBLE_COUNT`; a machine that normally needs an operator, a rate without one and no operator in the crew is `OPERATOR_NOT_PRICED` (a gap, not a flag). Crew equipment that no component of the work item prices is reported (`CREW_EQUIPMENT_NOT_COSTED`).

## 7. Unit costs and assemblies

```
unit cost (direct) = Σ materials [qty × (1+waste) × price]   (median of per-product costs)
                   + labor [crew labor/shift ÷ daily output]
                   + equipment [cost of the component's equipment/shift ÷ daily output]
                   + other direct
```

* Each **work item** has a measurable spec (`spec_attributes`, including `material_specs`: one entry per material line with its attributes and `spec_key`), an output unit, and explicit `included_scope` / `excluded_scope`. The validator re-derives each `spec_key` from the stated attributes and checks that the priced component is the one the work item describes. Shared activities — `mobilization`, `daily_cleanup_and_protection`, `supervision_and_general_conditions`, `sales_tax_and_delivery`, `permits_and_inspections`, `overhead_and_profit` — are **excluded in every work item**. Quantities per unit come from stated geometry with the derivation in `qty_formula` (screws: fence-post count at both ends of every fastener line; studs per SF from the true wall height 97.125 in = 92-5/8 in stud + 3 × 1.5 in plates; batts: 15 in batt in a 16 in pitch = 15/16).
* An **assembly** needs a measurable spec, exact work-item *versions* and non-empty `included_scope` **derived from its children** (the union of what they price), with the children's exclusions surfaced in its `excluded_scope`; its `spec_attributes.work_items` must equal its component rows (validator `ASM_*` rules). Two children claiming the same scope token, or the same `cost_tag` on two components (work item or assembly), make the run `failed`. Each child is priced for its **own quantity** (assembly quantity × quantity per assembly unit). `price_basis` of an assembly is the union of its children's.
* **Overhead, contingency and profit are shown separately**, with a stated basis for every percentage (no defaults), as fractions in [0,1] (`10` meaning 10 % is refused; margin < 1):

```
overhead    = direct × oh
contingency = (direct + overhead) × ct
cost        = direct + overhead + contingency
markup m :  price = cost × (1 + m)           margin g :  price = cost / (1 − g)    (g < 1)
m = g / (1 − g)    g = m / (1 + m)           e.g. 25 % markup = 20 % margin; 10 % markup = 9.09 % margin
```
The markup run stores the price in `price_total`; `direct_cost_total` stays the base run's direct cost; the basis texts are part of the run id.

## 8. Region and date

* Three separate dates: price **observation** date, rate **effective period**, and our **retrieval** time (`known_at` filters on it).
* **Region (materials):** exact region first. A price from an *ancestor* region (e.g. California for a county) is used only with `allow_ancestor_region_prices=True`; one from a *sub-region* (a city for a county, a county for a country) only with `allow_subregion_prices=True`; both are ranked after exact prices and flagged with the region id (`PRICE_FROM_ANCESTOR_REGION:<id>`, `PRICE_FROM_SUBREGION:<id>`). Prices of unrelated regions are used only with `use_region_factors=True` **and** an explicit usable factor `from_region → to_region` (newest valid; no chaining). **A local price never receives a regional factor.** Prices with only a ZIP/store and no region are unusable. Labor/equipment/burden rates may come from the target region or an ancestor (never a smaller area) and record `RATE_FROM_ANCESTOR_REGION:<id>`.
* **Time:** with `time_index_id`, **every** price whose index period differs from the as-of period is adjusted: `price_to = price_from × index_to / index_from`, storing both dates, periods, values, vintages and formula (`TIME_INDEXED_PRICE`). The index must exist, be usable, and apply to the cost kind (a labor index cannot adjust a material price: `failed`). If the as-of period is not yet published the latest published period is used and flagged `INDEX_LATEST_PUBLISHED_PERIOD_USED`. Without an index a price of another month is flagged `PRICE_NOT_TIME_ADJUSTED`; `max_price_age_days` excludes older prices only when the user sets it. Index values carry a `vintage_date` and `known_at` is honoured; indices are never prices of products.
* **Conditions** (occupied building, height, …) need an explicit factor that is usable (reviewed, valid at as-of, allowed source). A requested condition whose factor exists but is unusable is `CONDITION_FACTOR_UNUSABLE`; one that changes no cost line anywhere is `CONDITION_FACTOR_MISSING`. **Quantity factors** are chosen on the target's own quantity, respect validity, and overlapping ranges are ambiguous.
* **Bid prices** (Caltrans, ADOT, NDOT, county bid tabs) are stored in `bid_benchmarks` with a scope note and never feed a calculation.

## 9. Confidence is described, not scored

No percentage is ever assigned. `v_price_confidence_facets` exposes three facts per price: the **source quality tier** (A official dataset with method · B official publication · C manufacturer documentation · D retailer listing · E secondary/aggregator · X unclassified), the **age in days**, and whether the **spec match** is recorded. Every run also lists its flags and records `price_basis` and `input_review_floor`.

## 10. Source handling and compliance

* Order of attempt: official API → CSV/XLSX → open catalogue → HTML → PDF. Respect robots.txt, rate limits and terms; **never** bypass a CAPTCHA, login or paywall; open no paid accounts, buy no data, contact no supplier on the company's behalf.
* Retailer prices are captured by a person or a licensed/official feed (`capture_method`, `captured_by` mandatory). The importer refuses every source in `NO_DATA_USE` whatever the capture method, accepts `restricted_no_automated_access` sources only as `manual_browser` (with a warning), requires the price to appear in the evidence as a whole number token (`$12.50` does not support `2.50`), requires a time zone on `retrieved_at`, and builds observation ids from price and retrieval time so a correction is a new observation, not a silent duplicate. No scraper exists in this repository.
* FRED terms bar storing FRED content, so only BLS series *identifiers* seen on FRED are stored; values must be ingested from bls.gov. The BLS contact address is configuration (`COSTDB_CONTACT`), not code.
* PDF extraction: a text layer does not prove correct column order. `connectors/pdf_tables.py` extracts tables with page numbers and trailing notes, renders sampled cells as highlighted page images for comparison, and warns when the text layer jumps right-to-left on a line.
* Classification: **own stable codes only** (`CAT-`, `TR-`, `EQ-`, work item and assembly codes). CSI MasterFormat/UniFormat/OmniClass are CSI-licensed: the register records them as `licence_required` and nothing from them is used until a licence exists. RSMeans line numbers and descriptions are not used.

## 11. Known limitations (read before relying on any number)

1. No primary source could be fetched when this pilot was built; every register entry is search-summary level. Nothing is `validated`.
2. Quantities are derived from the stated geometry only; corners, openings, laps, blocking, bottom-plate fasteners and similar adders are explicitly excluded in each work item.
3. Waste, labor norms and crew compositions are missing everywhere — runs are `incomplete` by design; the 25 work-item and 10 assembly **definitions have not been reviewed by a person** (strict runs say so).
4. The `median across products` policy needs at least one validated observation; with a single SKU the "median" is that SKU's price.
5. Rates are per *paid* hour (§5); equipment delivery/mobilization and minimum-rental charges are not in unit cost; the job-level items (mobilization, general conditions, permits, tax, overhead, profit) are added once, outside the unit costs.
6. Region identifiers (FIPS/CBSA) and SOC codes were entered from model knowledge and are marked `assumed / pending_verification`.
7. The engine has been exercised on synthetic inputs and on the empty real data; it has not yet been run on a real, populated price set.
