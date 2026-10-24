# Independent review F1 - code, arithmetic, schema and data consistency

Reviewer: Agent F1 (independent; did not write the system). Date: 2026-10-24. Scope: `schema/`, `pipeline/`, `data/csv`, `tests/`, `docs/source_findings.md`. All results below were produced by running the code (test suite, a scratch PostgreSQL 16 database `f1_review`, ~60 counter-examples on the synthetic fixtures); scripts are in `/tmp/claude-0/f1/` (scratch, not part of the repository). Machine-readable list: `data/raw_agent_returns/agent_F1_findings.json` (ids F1-001 ... F1-042).

**Snapshot note.** The repository was changed while this review ran (F2 fix round at 02:39:19, PG-test fix 02:39:55, data rebuild 02:40:12). File:line references and results are for the 02:40 snapshot; the full suite (114 tests, `PGHOST=/var/tmp/owl_pgsock PGPORT=5544 PGUSER=postgres python3 -B tests/run_tests.py`) is green on it, and every counter-example was re-run on it. My first PG run (before 02:39:55) had one failure (`test_python_generated_runs_and_json_columns_round_trip`: expected 3 lines with inputs, found 39) - fixed since; it shows the tests are coupled to the committed data.

**Result in one line:** 42 defects - 3 critical, 21 major, 18 minor. Verdicts: R1 PASS-with-caveats, R2 PASS-with-caveats, R3 FAIL, R4 PASS-with-caveats, R5 PASS-with-caveats, R6 PASS-with-caveats, R7 FAIL, R8 PASS-with-caveats, R9 FAIL, R10 PASS-with-caveats.

## 1. Summary verdict per rule

| # | verdict | one-line reason |
|---|---|---|
| 1 | **PASS WITH CAVEATS** | No numeric value in data/csv lacks a source or an explicit missing/assumed flag (25/25 productivity rows and all crews are origin=missing, waste is NULL, no prices); quantities are geometry-derived with stored formulas, but several derivations are questionable (fence-post screw count, batt width, stud stack: F1-026), the 50 LF duct is a parameter labelled 'derived' (F1-027), spec_keys add attributes the work-item spec never states (F1-028), and the 4 imported wage/burden rows are origin='observed' although only a search-tool paraphrase was seen. |
| 2 | **PASS WITH CAVEATS** | All 14 fixed conversion factors (7 non-trivial, 7 base) re-derived exactly, DAY correctly not fixed; TON/GAL are always qualified in the units table; but bare 'tons/gal' in attribute names, 'HR' for three different hour kinds, and an unprotected units table (F1-029, F1-032). |
| 3 | **FAIL** | Spec-key equivalence and pack/unit separation work, but coverage-based quantities (5 of 25 work items) bind one product's spread rate to the median price of all products and ignore coverage unit/film thickness (F1-001), strict mode prices flagged/unreviewed products (F1-002), and retail-as-contractor is only a warning string (F1-018). |
| 4 | **PASS WITH CAVEATS** | Layers are separate, formulas are implemented as specified, PW refused for private projects, no double-add of included fringe; but rate-class selection ignores apprentice/overtime/project type (F1-007), loaded source rates lose components (F1-008), burden ties/class codes (F1-009), person-hours ignore member hours (F1-036). |
| 5 | **PASS WITH CAVEATS** | Schema separates rental/fuel/delivery/minimum/operator and operator double counting is blocked when flagged; engine drops fuel_cost_hr, min rental and delivery, prices equipment to $0 when the crew has none, operator detection relies on a self-declared flag (F1-016). |
| 6 | **PASS WITH CAVEATS** | Direct-cost sum, overhead/contingency/profit and markup vs margin formulas verified by hand; but the markup run stores price in direct_cost_total, accepts negative/oversized percentages (F1-019), and hard-coded default thresholds (F1-039). |
| 7 | **FAIL** | Measurable specs, units, quantities and version links exist, but included_scope is empty on all 10 assemblies and exclusions are copy-pasted wall tokens (F1-024); cost_tags/spec contradictions are not validated (F1-023). |
| 8 | **PASS WITH CAVEATS** | Observation date, effective period and retrieval time are separate fields; index adjustments keep original price, dates, index values, vintages and formula; regional factors are opt-in and never applied to local prices; bid data never reach the engine; but ancestor prices beat local ones and are unflagged (F1-006), index applies_to/flagged series ignored (F1-017, F1-002), retrieved_at ignored for as-of (F1-040). |
| 9 | **FAIL** | Stable ids and source/status columns exist, but calculation runs/lines and product/definition rows are mutable or deletable (F1-003, F1-021), run_id does not cover input records (F1-013), review decisions are overwritten (F1-020), several tables carry no origin/status (units, categories, capture_targets, crew_members, components). |
| 10 | **PASS WITH CAVEATS** | Currently true: 0 validated records of 92 sources (all search_snippet_only), verified in data/csv and pilot_status.json. The mechanism is weak: no DB-level gate (F1-020), strict mode ignores flagged/rejected non-observation records (F1-002), licence_required not blocked (F1-004), promotion has gaps (F1-025). |

What I could positively confirm: unit table exact (all 14 fixed factors re-derived, DAY correctly non-fixed); 129 capture-target spec_keys recompute from `categories.required_product_attributes`, are unique, `required_by` and priority agree exactly with the work-item components (43 priority-1 lines used, 86 unused); every productivity row/crew/equipment component pair is consistent (unit, crew, work item); the 25 productivity rows are all `origin=missing` with NULL numbers, all crews `missing`, no waste factor anywhere; no `bid_benchmarks` or FRED value reaches the engine; strict mode never accepts an assumed crew/price/waste; PW rates are refused for private runs; `docs/data_dictionary.md` and `schema/003_comments.sql` are current (test); markup/margin, labor-burden and cap formulas match my hand calculations (UI cap: 0.034 x 7000/2080 = 0.1144/h).

## 2. Defects found

Severity: **critical** = wrong or unverifiable result produced silently in the default/strict configuration, or the database allows a state the rules forbid and that falsifies results; **major** = wrong result in a realistic configuration, crash, or a documented guarantee that does not hold; **minor** = hygiene, edge case, documentation.

Reproductions use this prelude (synthetic fixtures; baseline total 0.997875):

```python
# run from /home/user/owl-tower-os-app/cost-db
import sys; sys.path[:0] = ['.', 'pipeline']
from datetime import date; from decimal import Decimal as D
from tests.fixtures import synthetic as S
from costdb.calc import Engine, apply_markup
WI = S.WI                                             # WI-DRY-001 (real definition), synthetic inputs
def run(db, **kw): return Engine(db).unit_cost(WI, 1, S.params(**kw))
def mat(r): return [l for l in r.lines if l['line_kind'] == 'material'][0]
db = S.priced_drywall_db()                            # baseline: complete, total 0.997875 (material 0.447875, labor 0.55)
```

### Critical (3)

#### F1-001 - Manufacturer-coverage quantity: wrong pairing with price, no unit conversion, arbitrary row, divide-by-zero

- **Severity:** critical &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 876-896 (called from 701-702)
- **What is wrong:** Manufacturer-coverage quantity (5 of the 25 pilot work items: joint compound, primer, wall paint, ceiling paint, curing compound) is wrong or non-deterministic. (a) _consumption_qty takes the lowest consumption_id among ALL products that share the spec_key (line 886) but the line is then priced with the MEDIAN price of all those products, so one product's spread rate is multiplied by another product's price; (b) coverage_unit_id is never converted to the work item's output unit (line 890 uses cov as if it were already per output unit); (c) coverage_qty = 0 or coats = 0 raises decimal.DivisionByZero (schema allows both, schema 228/233); (d) film_thickness / substrate_condition / application_method / conditions on the consumption row are never matched to anything on the component, so two rows for different film thickness are 'alternatives' picked by hash order; (e) products that are flagged/rejected are included in the product set (lines 879-882).
- **Reproduction / counter-example:**

```
db = S.real_db(); S.add_source(db)
S.add_product(db,'TEST-PRD-PA','prm_pva_5',5,'GAL_US','A','A-1'); S.add_obs(db,'TEST-OBS-PA','TEST-PRD-PA','100',5,'GAL_US')   # $20/gal
S.add_product(db,'TEST-PRD-PB','prm_pva_5',5,'GAL_US','B','B-1'); S.add_obs(db,'TEST-OBS-PB','TEST-PRD-PB','200',5,'GAL_US')   # $40/gal
S.add_labor_actual(db,'TEST-LRT-PNT','TR-PNT',40); S.set_crew(db,'CRW-PNT',8,[('labor','TR-PNT',2,False)])
S.set_productivity(db,'WI-PNT-001',2,8,2000); S.set_waste(db,'WI-PNT-001',{'CAT-PNT-PRM':(0.0,'t')})
# two product_consumption rows (application='new_drywall_primer', coats=1, coverage_unit SF): TEST-CON-A -> product A 400 SF/gal, TEST-CON-B -> product B 200 SF/gal
# true cost per SF: A 0.05, B 0.20, median 0.125.  Engine extended_cost = 0.0750 ; after renaming the ids so that B's row sorts first = 0.1500.
# same data with coverage_unit_id='SY' (400 SY/gal) on this SF work item: material qty 0.0025 (correct 0.0225).  coverage_qty=0 or coats=0: decimal.DivisionByZero.
```

- **Suggested fix:** Pair coverage with the same product that is priced: per product compute cost per output unit = (price per pack / pack content) x (product units per output unit) and take the median of THOSE; require exactly one usable consumption row per (product, application) or add film_thickness/conditions selectors on the component and fail when ambiguous; convert coverage_unit_id to wi.output_unit_id with Units.factor; add CHECK (coverage_qty > 0 AND coats > 0 AND per_qty > 0) on product_consumption; filter products through the same usability test as observations; add tests (none exist for this path).

#### F1-002 - Strict mode ignores flagged/rejected sources, crews, indices, assumptions, products

- **Severity:** critical &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 189-201 (_usable), 208-217 (_approved_assumption), 218-237 (_index_value), 246/250 (products), 545-558 (_crew_costs)
- **What is wrong:** Strict-mode leak. methodology.md section 1 promises 'flagged and rejected records are never used by any calculation', but review_status is only honoured for the row that is passed through _usable() (observations, labor/burden/equipment rates, productivity, consumption). It is ignored for: sources (a rejected source's rows stay usable), crews, indices (data/csv/indices.csv already contains ECICONWAG with review_status=flagged by reviewer F2; a flagged series with validated values still adjusts prices), approved assumptions (assumptions.review_status), and products (only 'rejected' is excluded at line 250; pinned products at 246 are not checked at all, so unreviewed and flagged products are priced in strict/validated mode).
- **Reproduction / counter-example:**

```
for s in db['sources']: s['review_status'] = 'rejected'          # source with all inputs
print(run(db).status, run(db).run['direct_cost_total'])          # complete 0.997875  (expected: incomplete)
# crew review_status='rejected' -> complete ; product review_status='flagged' or 'unreviewed' -> complete 0.997875
# index series review_status='flagged' (validated values) with time_index_id=... -> complete, TIME_INDEXED_PRICE
# approved assumption with review_status='rejected' -> complete
```

- **Suggested fix:** One helper usable(row, params) applied to every referenced table (sources, products, crews, indices, assumptions, factors, work items); in strict mode require validated for products/crews/indices as well; a record whose source is flagged/rejected is unusable; add a test per table.

#### F1-003 - calculation_runs / calculation_run_lines are rewritable and deletable (a run can be turned 'complete' with an invented total)

- **Severity:** critical &nbsp; **Area:** schema
- **Where:** `schema/001_schema.sql` : 311-345 (calculation_runs/lines, no trigger; line 342 ON DELETE CASCADE; cr_complete_chk 336)
- **What is wrong:** Calculation records are not protected. calculation_runs and calculation_run_lines have no append-only trigger, lines cascade-delete with their run, and cr_complete_chk only requires a non-null total and an empty missing_inputs array: an incomplete run can be rewritten into a 'complete' run with an invented total and no lines, and formula/inputs/parameters/calc_version of an existing run can be edited. This violates rule 9 (calculation records link to inputs, formula and version; history never overwritten).
- **Reproduction / counter-example:**

```
-- PostgreSQL, data/csv loaded
update costdb.calculation_runs set status='complete', direct_cost_total=123.45, missing_inputs='[]' where run_id=(select run_id from costdb.calculation_runs limit 1);   -- UPDATE 1
update costdb.calculation_run_lines set formula='x', inputs='[]'::jsonb, extended_cost=1 where line_no=1;                                                              -- UPDATE
delete from costdb.calculation_runs where run_id=(select run_id from costdb.calculation_runs limit 1);                                                                -- DELETE 1, 4 lines cascade
```

- **Suggested fix:** BEFORE UPDATE/DELETE/TRUNCATE triggers on both tables (only review_status/reviewed_*/notes updatable); replace ON DELETE CASCADE with RESTRICT; deferred constraint trigger: a 'complete' run must have >= 1 line and direct_cost_total equal to the sum of its component lines; NOT NULL calc_version and code_ref for non-test runs.

### Major (21)

#### F1-004 - licence_required (and restricted_no_storage when validated) not blocked consistently; importer admits what validate rejects

- **Severity:** major &nbsp; **Area:** calc/validate
- **Where:** `pipeline/costdb/calc.py; pipeline/costdb/validate.py; pipeline/connectors/retail_capture_import.py` : calc.py:30,197; validate.py:133,146; retail_capture_import.py:156-165
- **What is wrong:** Regression introduced by the F2 enum change: reuse_status 'licence_required' (now used by the three CSI sources) is blocked nowhere. NO_DATA_USE = ('prohibited','restricted_no_storage') so a licence_required source is a usable calculation input; validate.py raises SRC_PROHIBITED_IN_USE only for prohibited/restricted_no_storage and SRC_PROHIBITED_VALIDATED only for 'prohibited' (a validated restricted_no_storage or licence_required source is accepted); the importer accepts licence_required with no warning, and accepts 'prohibited' sources with capture_method=manual_browser (validate.py then flags every such row as an error and the engine ignores it, so the importer admits rows that the rest of the system rejects).
- **Reproduction / counter-example:**

```
for s in db['sources']:
    if s['source_id'] == S.SRC: s['reuse_status'] = 'licence_required'
run(db).status                                   # complete 0.997875 ; validate(db, production=False) -> no issue
# source 'restricted_no_storage' + review_status='validated' -> no SRC_PROHIBITED_VALIDATED
```

- **Suggested fix:** Define the restricted-status sets once (e.g. costdb/enums.py) and import them in calc, validate, importer and tests; decide explicitly whether licence_required means 'no data use until licence recorded'; make the importer refuse prohibited/restricted_no_storage regardless of capture_method.

#### F1-005 - Region/condition/quantity factor rows bypass the usability test

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 345-360 (_region_factor), 650-678 (_adjust_factors)
- **What is wrong:** Region, condition and quantity factor rows never pass through _usable(): the factor's source (prohibited, restricted_no_storage, synthetic fixture, flagged) is not checked. A factor from a prohibited source is applied in a strict run.
- **Reproduction / counter-example:**

```
S.add_source(db, 'SRC-PROH', method='fetched_primary', review='validated', reuse='prohibited')
# adjustment_factors row: region REG-CA-073 -> REG-CA-037, material, 2.00, source_id='SRC-PROH', review_status='validated'; the board observation is re-labelled REG-CA-073
run(db, use_region_factors=True)                 # complete; board unit price 0.80 (= 0.40 x 2.00), warnings REGION_FACTOR_APPLIED
```

- **Suggested fix:** Call the shared usability test on the factor row (and its source) in _region_factor and _adjust_factors; also pick the best factor deterministically (latest valid_from) instead of table order.

#### F1-006 - Region rank is not used for ranking; ancestor prices win silently

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 263-270, 290-292
- **What is wrong:** Region ranking is computed but not used for ranking. rank only decides accept/reject; with allow_ancestor_region_prices=True the newest observation wins regardless of specificity, so a newer state-level price silently overrides an exact-region price; an ancestor-region price carries no flag and the line input does not record region/zip/store (labor has RATE_FROM_ANCESTOR_REGION, materials have no equivalent). A sub-region observation counts as rank 0 for a parent target (documented, but not visible on the line). Latest-selection compares str(retrieved_at) (mixed offsets mis-order) and ties are broken by table order.
- **Reproduction / counter-example:**

```
S.add_obs(db,'TEST-OBS-STATE','TEST-PRD-BOARDA','16.00',32,'SF',region='REG-US-CA',observed=date(2026,10,1))   # 0.50/SF, newer, ancestor of LA
mat(run(db, allow_ancestor_region_prices=True))['unit_cost']      # 0.50 (local LA price is 0.40); warnings only ['RETAIL_PRICE_NOT_CONTRACTOR_COST']
mat(run(db, region_id='REG-US'))['unit_cost']                     # 0.40: an LA price silently serves a national (REG-US) request
```

- **Suggested fix:** Sort candidates by (rank asc, observed_at desc, retrieved_at desc as parsed datetime, observation_id); add PRICE_FROM_ANCESTOR_REGION:<id> and PRICE_FROM_SUBREGION flags; store region_id, zip, store_ref, retrieved_at, sales_tax/delivery flags in the line input.

#### F1-007 - Labor rate selection ignores apprentice, overtime, project type and classification

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 402-415
- **What is wrong:** labor_rate() chooses by (region rank, effective_from) only. labor_rates.apprentice, wage_basis (overtime_1_5x/2x), project_type (building/residential/heavy/highway), classification_raw and use_context are never consulted; 'prevailing_wage' and 'federal_wage_determination' are merged and the later effective_from wins whatever the regime. A DIR/SAM determination file will contain apprentice steps and overtime-group rows for every craft, so the journeyman straight-time rate is picked by luck.
- **Reproduction / counter-example:**

```
# three stat_wage rows, TR-DRYW, same region and statistic: 30.00 (journeyman, straight_time, 2026-05-01), 12.00 (apprentice=True, 2026-06-01), 45.00 (wage_basis='overtime_1_5x', 2026-07-01)
Engine(db).labor_rate('TR-DRYW', S.params(labor_basis='stat_loaded', annual_paid_hours=D(2080)))['components']['base_wage']   # 45
```

- **Suggested fix:** Filter on apprentice=False, wage_basis='straight_time' and a required project_type; add a classification selector parameter; raise Missing('LABOR_RATE_AMBIGUOUS') when more than one candidate remains at equal rank/effective_from; keep state and federal regimes separate.

#### F1-008 - Fully loaded source rates lose their own tax/WC/other components; some burden types can never be costed

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 436-493 (and 33)
- **What is wrong:** A fully loaded source rate is under-costed. When includes_payroll_taxes / includes_workers_comp is true the engine skips the burden but never adds the record's own payroll_tax_hr / workers_comp_hr / other_employer_cost_hr / total_hr: only base_wage_hr (+ fringe_hr) enters the total. other_employer_cost_hr and the burden types general_liability and other can never reach a cost and are not flagged. BURDEN_PAYROLL_TAX_TYPES hard-codes five types including state_ett for every region, so an Arizona/Nevada run can never complete unless a zero-rate 'observed' row is invented.
- **Reproduction / counter-example:**

```
# prevailing_wage row (use_context public_works_only): base 50, fringe 20, payroll_tax_hr 6, workers_comp_hr 5, other_employer_cost_hr 3, total_hr 84, includes_fringe/payroll_taxes/workers_comp all true
Engine(db).labor_rate('TR-DRYW', S.params(labor_basis='prevailing_loaded', project_type='public_works'))['total_hr']    # 70, not 84
# adding burden rows general_liability 2% and other $1.50/h to a complete stat_loaded rate leaves total_hr unchanged (42.33298...) and unflagged
```

- **Suggested fix:** When includes_x is true use that record's x_hr (or total_hr) and fail if it is absent; cost 'other' and 'general_liability' rows or emit an explicit OMITTED_BURDEN flag; make applicable burden types region-dependent data instead of a constant.

#### F1-009 - Burden selection ignores effective_from ties and class codes

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 363-376
- **What is wrong:** Burden selection ignores effective_from when several rows are in period (effective_to is optional) and ignores class_code. Ties go to table order, so a superseded open-ended rate can win; a trade-specific NATIONAL row beats a generic local row; workers' comp rows for different class codes are indistinguishable.
- **Reproduction / counter-example:**

```
# 2025 Medicare 1.00% row (effective_to NULL) listed BEFORE the 2026 1.45% row, base wage $30
Engine(db).labor_rate('TR-DRYW', S.params(labor_basis='stat_loaded', annual_paid_hours=D(2080)))['components']['fica_medicare']   # 0.3000 (1.00%), correct 0.4350
```

- **Suggested fix:** Score = (region rank, trade specificity, -effective_from) and raise on remaining ties; add class_code to the selection parameters for workers_comp.

#### F1-010 - A requested job condition is silently dropped when its factor exists but is unusable

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 650-668 (esp. 665)
- **What is wrong:** A requested job condition is silently dropped when a factor exists but is unusable. The code raises CONDITION_FACTOR_MISSING only if NO factor with that condition_desc exists (elif not anyhit); if one exists but is unreviewed, expired, assumed (in strict mode) or defined for another cost kind, hits is empty and the condition is ignored. methodology.md section 8 says a requested condition 'is a missing input, never silently ignored'.
- **Reproduction / counter-example:**

```
# factor(productivity_condition, labor, 1.20, 'occupied_building') with review_status='unreviewed' | valid_to=2020-01-01 | origin='assumed' (strict)
run(db, conditions=('occupied_building',)).run['labor_cost']      # 0.550000 in all three cases (status complete; 0.66 expected or an incomplete run)
```

- **Suggested fix:** If any factor with the tag exists for this kind but none is usable, raise Missing('CONDITION_FACTOR_UNUSABLE') naming the reason; model 'not applicable to this kind' explicitly instead of by absence.

#### F1-011 - Quantity tiers and quantity factors: tier price accepted without quantity, expired factor applied, wrong quantity for assembly children

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 261, 669-678, 916
- **What is wrong:** Quantity handling. (a) A price with qty_tier_min (e.g. a pallet/contractor-volume price) is accepted when RunParams.quantity is omitted (line 261 only filters when quantity is given); (b) quantity factors ignore valid_from/valid_to (conditions at 659-660 check them) and region, and the first matching range wins; (c) assembly_cost passes the assembly quantity to every child work item, so tier/quantity factors are chosen on the wrong quantity.
- **Reproduction / counter-example:**

```
S.add_obs(db,'TEST-OBS-TIER','TEST-PRD-BOARDA','1.00',32,'SF',observed=date(2026,10,10)); (that observation: qty_tier_min=100000)
mat(run(db))['unit_cost']                                          # 0.03125 ($1.00 / 32 SF) although the price needs a 100,000-unit order
# quantity factor 0.90 with valid_to=2020-01-01 and RunParams(quantity=500): material_cost 0.403088 (applied)
```

- **Suggested fix:** Exclude tier prices unless quantity is given and >= qty_tier_min (or flag QTY_TIER_PRICE_UNVERIFIED); apply the same validity tests to quantity factors; compute child quantity = assembly quantity x qty_per_assembly_unit.

#### F1-012 - price_policy unvalidated; 'latest' returns the first product

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 321, 341-342
- **What is wrong:** price_policy is not validated: any string other than 'median_of_latest_per_product' silently takes prices[0], i.e. the first product in table order (not the latest); the MEDIAN_OF_n_PRODUCTS flag is still emitted.
- **Reproduction / counter-example:**

```
# two products, B observed later at 0.50/SF, A at 0.40/SF
[mat(run(db, price_policy=p))['unit_cost'] for p in ('median_of_latest_per_product','latest','bogus')]   # [0.45, 0.40, 0.40]
```

- **Suggested fix:** Enumerate allowed policies, reject others in RunParams.__post_init__, implement a real 'latest' (max observed_at, retrieved_at) and flag correctly.

#### F1-013 - run_id does not cover input records or missing inputs (PK collision, build.py drops the second run)

- **Severity:** major &nbsp; **Area:** calc/build
- **Where:** `pipeline/costdb/calc.py; pipeline/scripts/build.py` : calc.py:811, 860, 943, 971-972 (fingerprint/run_id); build.py:57-59
- **What is wrong:** run_id is a hash of target, parameters, calc version and only [component_id, resulting cost] of the RESOLVED lines. methodology.md says it covers 'the exact input values': it does not. The same cost from a different observation gives the same run_id (calculation_runs PK collision; build.py silently keeps the first and drops the second); two incomplete runs with different missing_inputs share an id as long as no line resolved (e.g. before/after one price was captured).
- **Reproduction / counter-example:**

```
# db2 = clone of db where TEST-OBS-BOARDA is replaced by another store's observation of the same price
run(db).run['run_id'] == Engine(db2).unit_cost(WI,1,S.params()).run['run_id']        # True, inputs differ (TEST-OBS-BOARDA vs TEST-OBS-OTHER)
# real data, no prices vs one board price captured: both runs 'incomplete', both RUN-87e6ae280f37, missing lists differ
```

- **Suggested fix:** Include in the fingerprint every input id + value (use the line inputs) and the sorted missing_inputs codes/refs; keep calc_version bound to code (git sha) so a fixed bug changes ids.

#### F1-014 - with_assumptions crashes on a productivity assumption (4-tuple vs 5-tuple)

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 616-618 vs 824
- **What is wrong:** with_assumptions mode crashes on an approved productivity assumption: _daily_output returns a 4-tuple on the assumption path (lines 616-618) but unit_cost unpacks 5 values (line 824) -> ValueError. The path is untested (only the waste assumption is).
- **Reproduction / counter-example:**

```
# productivity observation unreviewed + approved assumption 'productivity:<labor component id>' = 1600 SF
run(db, mode='with_assumptions')      # ValueError: not enough values to unpack (expected 5, got 4)
```

- **Suggested fix:** Return (daily, inputs, flags, 'assumed', None); add tests for every assumption type (productivity, price, labor_rate, equipment_rate, crew, quantity, waste, benefits, workers' comp).

#### F1-015 - Assumption handling: crash on value_text, unit semantics, no range checks, duplicates, self-approval

- **Severity:** major &nbsp; **Area:** calc/schema
- **Where:** `pipeline/costdb/calc.py; schema/001_schema.sql` : calc.py:460, 485, 208-217; schema 805-824
- **What is wrong:** Assumption handling. value_text-only approved assumption (allowed by as_value_chk) crashes with decimal.InvalidOperation (D('None')); the benefits assumption treats ANY unit_id as $/h (line 460) while the workers'-comp assumption always multiplies by wages and ignores unit (line 485); no sign/range checks (waste -0.5 -> quantity 0.5; waste 5 -> 6.0x; a zero productivity assumption would divide by zero, by reading - the path currently crashes earlier, F1-014); several approved rows for one ref -> first wins silently; assumptions.review_status ignored; approved_by may equal proposed_by.
- **Reproduction / counter-example:**

```
# approved waste assumption applies_to_ref='waste:<component_id>': value_text='ten percent', value_numeric NULL -> run(db, mode='with_assumptions') raises decimal.InvalidOperation
# value_numeric=-0.5 -> complete, material qty 0.5 ; value_numeric=5 -> complete, qty 6.0 ; two approved rows (0.1, 0.9) -> first wins
```

- **Suggested fix:** Validate assumption type/unit/range on read (units conversion like prices), require value_numeric for numeric uses, uniqueness of approved assumption per ref, approved_by <> proposed_by, expiry required, review_status honoured.

#### F1-016 - Equipment: fuel, minimum rental and delivery dropped; $0 equipment line; operator detection depends on a flag

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 496-542, 563-600 (583, 592-596)
- **What is wrong:** Equipment omissions. (a) fuel_cost_hr is never added: rate with fuel_included=False and fuel_cost_hr present is costed without fuel and without a flag (FUEL_NOT_PRICED only when fuel_cost_hr is NULL, line 521); (b) min_rental_period and delivery_pickup_cost are never priced (static flag only); (c) an 'equipment' component whose crew has no equipment member prices to 0 with origin 'observed' and no warning; (d) operator double count is detected only via the self-declared crew_members.is_operator flag (a TR-OPR labor member with is_operator=false plus an operator-included rate passes silently); OPERATOR_NOT_PRICED is only a flag; (e) (by reading) rental_day charges one day rate per crew-shift regardless of shifts needed.
- **Reproduction / counter-example:**

```
# rental 25/h, fuel_included=False, fuel_cost_hr=9, delivery 75, min rental '4 hours', crew 1x PTROWEL:  equipment unit_cost 0.1000 (= 25*8/2000); fuel 9*8/2000 = 0.036 absent; warnings ['EQUIPMENT_DELIVERY_AND_MOBILIZATION_EXCLUDED']
# WI-CON-001 with a crew that has labor members only: equipment line unit_cost 0, origin 'observed', warnings []
# crew [TR-CEM x2, TR-OPR x1 (is_operator False), PTROWEL] + rate operator_included=True: no OPERATOR_DOUBLE_COUNT
```

- **Suggested fix:** Add fuel_cost_hr when fuel_included is false (or fail when unknown); price or fail on min rental/delivery when flagged; raise CREW_NO_EQUIPMENT for an equipment component without equipment members; detect operator labor by trade_code (TR-OPR) as well; treat OPERATOR_NOT_PRICED/FUEL_NOT_PRICED as incomplete, not as a flag.

#### F1-017 - Time index: applies_to ignored, applied only to old prices, no fallback for unpublished months

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 218-237, 275-289
- **What is wrong:** Time-index logic. indices.applies_to is never compared with the cost kind (a LABOR index adjusts a MATERIAL price: 0.40 -> 0.60); an index is applied only when the price is older than max_price_age_days, so a 287-day-old price with time_index_id supplied is left unadjusted and unflagged; frequency 'other' is treated as annual; the index value for the as_of month is normally unpublished (PPI/ECI lag), so INDEX_VALUE_MISSING with no fallback to the latest published period; flagged index series are used (F1-002).
- **Reproduction / counter-example:**

```
# index applies_to='labor' (values 100 -> 150), time_index_id given, board price observed 2025-06-01
mat(run(db, time_index_id='TEST-IDX-LAB'))['unit_cost']           # 0.60, 'TIME_INDEXED_PRICE'
# price observed 2026-01-10 (287 days) + time_index_id: unit_cost 0.40, no TIME_INDEXED_PRICE
```

- **Suggested fix:** Require idx.applies_to in (kind,'all'); when time_index_id is supplied adjust every price whose month differs from the as_of month (store the base month used); define a documented fallback to the latest published index period with a flag.

#### F1-018 - Retail/ancestor/stale/unreviewed basis is only a warning string; status and mode do not show it

- **Severity:** major &nbsp; **Area:** calc/build
- **Where:** `pipeline/costdb/calc.py` : 32, 330-336, 965-970; RunParams.min_review (62)
- **What is wrong:** Rule 3/8 'never presented as contractor cost' is met only by a warning string. DEFAULT_CHANNELS includes retail_public, a run built from retail prices has status 'complete', mode 'strict' and a plain direct_cost_total; the same is true for a national wage used in an LA run (RATE_FROM_ANCESTOR_REGION), STALE_RATE, SALES_TAX_UNKNOWN_OR_INCLUDED, OPERATOR_NOT_PRICED. mode='strict' with min_review='unreviewed' produces a run indistinguishable (mode/status/warnings) from a validated-only run; only the parameters JSON differs.
- **Reproduction / counter-example:**

```
r = run(db); (r.status, r.run['mode'], r.run['direct_cost_total'], r.run['warnings'])      # ('complete','strict',0.997875,['RETAIL_PRICE_NOT_CONTRACTOR_COST'])
run(db, min_review='unreviewed')                                                           # (after un-validating an observation) same shape: strict/complete, warnings only retail
```

- **Suggested fix:** Add structured run columns (price_basis retail|quote|mixed, min_review, region_fallback, input_review_floor) and a status such as 'complete_proxy_basis'; make retail an explicit opt-in channel (allow_retail_proxy=True).

#### F1-019 - Markup run stores the PRICE in direct_cost_total; no range checks; fingerprint misses the basis

- **Severity:** major &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 1052-1110 (1070-1081, 1091-1092, 1100, 1106)
- **What is wrong:** Markup run: the PRICE (incl. overhead, contingency, profit) is stored in calculation_runs.direct_cost_total and mode is 'with_assumptions', so any consumer of 'direct_cost_total' reads a price as a direct cost; component columns are NULL. No range checks: profit_value -2 -> price -1.15, margin -0.5 accepted, overhead_pct=10 (meaning 10%) -> price 72.4; the fingerprint (line 1091) omits the basis texts, so runs differing only in stated basis share a run_id; only the first line carries inputs.
- **Reproduction / counter-example:**

```
m = apply_markup(run(db), overhead_pct=D('0.10'), overhead_basis='b', contingency_pct=D('0.05'), contingency_basis='b', profit_method='markup', profit_value=D('0.10'), profit_basis='b')
m.run['direct_cost_total']        # 1.267800  (direct is 0.997875)
apply_markup(run(db), overhead_pct=D('10'), ..., profit_method='markup', profit_value=D('0.10'), ...).run['direct_cost_total']   # 72.445725
```

- **Suggested fix:** Store price in a dedicated column (price_total) and leave direct_cost_total as the base run's direct cost; validate 0 <= pct < 1 (or require explicit ranges), margin < 1; include the basis strings and base-run line ids in the fingerprint.

#### F1-020 - Rule 10 is not enforced by the database (validated without reviewer or fetched source; no review history)

- **Severity:** major &nbsp; **Area:** schema/validate
- **Where:** `schema/001_schema.sql; pipeline/costdb/validate.py` : all review_status columns; validate.py:129-153, 422-443
- **What is wrong:** Rule 10 is enforced only in Python. The database accepts review_status='validated' with no reviewer, no reviewed_at and on a source whose verification_method is search_snippet_only (observations, labor rates, sources themselves); the append-only trigger lets review_status be flipped freely and keeps no review history (each flip overwrites the previous decision). promote_validated mutates in-memory rows and build.py rewrites the CSV, so the status history exists only in git.
- **Reproduction / counter-example:**

```
update costdb.price_observations set review_status='validated' where observation_id='OBS-X1';      -- UPDATE 1 (source is search_snippet_only, reviewed_by NULL)
update costdb.sources set review_status='validated' where source_id='SRC-XSNIP';                   -- UPDATE 1 with verification_method='search_snippet_only'
```

- **Suggested fix:** CHECK (review_status <> 'validated' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)); constraint trigger requiring source.verification_method='fetched_primary' for validated observed rows; add a review_events (append-only) table.

#### F1-021 - Product identity and 'versioned' definition tables are editable in place

- **Severity:** major &nbsp; **Area:** schema
- **Where:** `schema/001_schema.sql` : 191-222 (products), 537-600 (work_items/components), 648-690 (assemblies/components), 516 (crew_members), 770-824 (factors/assumptions)
- **What is wrong:** Identity and 'versioned' definition tables are editable in place. products has no protection, so spec_key / content_qty / spec_attributes can be rewritten and every existing price observation silently re-maps to another spec line (v_price_history joins the live product); work_items, work_item_components, assemblies, assembly_components, crews, crew_members, adjustment_factors, assumptions can be changed without a new version (work-item quantity 0.09375 -> 99 accepted), which defeats 'links to versioned unit costs' and run reproducibility.
- **Reproduction / counter-example:**

```
update costdb.products set spec_key='k2', content_qty=1000, content_unit_id='EA', spec_attributes='{"thickness_in":0.625}' where product_id='PRD-X1';   -- UPDATE 1; v_price_history now reports 'k2' for old observations
update costdb.work_item_components set qty_per_unit=99 where work_item_id='WI-FRM-001' and line_no=1;                                              -- UPDATE 1
```

- **Suggested fix:** Apply forbid_history_rewrite (review fields/notes only) to products and to every versioned definition table; new content = new version row; add FK/trigger preventing a calc run from referencing an edited version.

#### F1-022 - spec_key / pack / leaf-category consistency is not a database constraint

- **Severity:** major &nbsp; **Area:** schema
- **Where:** `schema/001_schema.sql` : 191-222, 262-300
- **What is wrong:** The material-equivalence and pack rules are not database constraints: a product with spec_key unrelated to its attributes ('garbage-key', spec_attributes {}), a product in a non-leaf category (CAT-DRY), and a price observation whose pack content differs from the product's pack (5 LB vs 32 SF) are all accepted; only validate.py (run after load) can notice.
- **Reproduction / counter-example:**

```
insert into costdb.products (...,category_id,spec_attributes,spec_key,content_qty,content_unit_id,...) values (...,'CAT-DRY-BRD','{}','garbage-key',32,'SF',...);   -- INSERT 0 1
insert into costdb.price_observations (...,pack_content_qty,pack_content_unit_id,...) values (...,5,'LB',...);                                              -- INSERT 0 1 (product pack is 32 SF)
```

- **Suggested fix:** Constraint trigger: product.category must have required_product_attributes, every required attribute present, spec_key recomputed in SQL (or generated column); observation pack (qty, unit) must equal products.content_qty/unit (or reference a pack-size table).

#### F1-023 - Validator cannot detect component-vs-spec, assembly-vs-children or cost_tag contradictions

- **Severity:** major &nbsp; **Area:** validate
- **Where:** `pipeline/costdb/validate.py` : 312-381 (check_work_items, check_assemblies)
- **What is wrong:** The validator cannot see contradictions between a definition and what it prices (rules 3 and 7): a work item whose spec says '1/2 in regular board' but whose component points at the 5/8 in Type X spec_key produces 0 issues; an assembly whose spec says 5/8 Type X while its children hang 1/2 in regular produces 0 issues; cost_tags on assembly_components are never examined (the double-count control exists only for included_scope tokens and, as a warning, inside one work item).
- **Reproduction / counter-example:**

```
# WI-DRY-001 material component re-pointed to MATS['gyp_58_x_4x8']['spec_key'] -> validate(db) == []
# ASM-WALL-001 spec_attributes['board'] = '5/8 in Type X ...' while children are WI-DRY-001 -> validate(db) == []; cost_tags=['fasteners'] on several assembly components -> []
```

- **Suggested fix:** Derive a machine-checkable spec map per work item (attribute -> spec_key attribute) and compare; require assembly spec attributes to be derived from the children (or compare); turn WI_DUP_TAG into an error and extend it to assembly components.

#### F1-024 - Assemblies have no inclusions; exclusions are copy-pasted wall tokens; HVAC assembly is not a closed system

- **Severity:** major &nbsp; **Area:** data
- **Where:** `data/csv/assemblies.csv; pipeline/costdb/validate.py` : assemblies.csv all 10 rows (included_scope/excluded_scope); validate.py:358-380
- **What is wrong:** Rule 7 requires inclusions/exclusions on every assembly. included_scope is the empty array for all 10 assemblies; excluded_scope is the same four wall tokens (base_trim, corners_and_intersections, openings_headers_and_door_frames, electrical_and_mechanical_rough_in) on every assembly, including slabs, the footing and the HVAC system where they are meaningless, while the real exclusions sit only on the child work items (e.g. 11 or more child-level exclusions per assembly are not surfaced: subgrade preparation, forms, curing, gas piping, flue venting, power wiring, condensate, refrigerant charge ...). ASM-HVAC-001 is named 'Residential 3-ton split-system install' but excludes gas piping, flue, condensate, power wiring and charge; nothing on the assembly says so.
- **Reproduction / counter-example:**

```
python3 - <<'EOF'   # (summary of data/csv/assemblies.csv)
# all 10 rows: included_scope == [] ; ASM-SLAB-001/002, ASM-FTG-001, ASM-HVAC-001 excluded_scope contains base_trim, corners_and_intersections, ...
EOF
```

- **Suggested fix:** Generate assembly included_scope as the union of child included tokens and excluded_scope as child exclusions not covered by another child (plus assembly-level exclusions); add a validator rule ASM_NO_INCLUSIONS and ASM_EXCLUSION_NOT_APPLICABLE.

### Minor (18)

#### F1-025 - Validator/promotion defects (duplicate issues, index_values never promotable, products promoted without evidence)

- **Severity:** minor &nbsp; **Area:** validate
- **Where:** `pipeline/costdb/validate.py` : 140, 397, 427-437, 383-411
- **What is wrong:** Validator/promotion defects: check_sources iterates labor_rates twice (OBSERVED_TABLES already contains it) so every issue on a labor row is duplicated; promote_validated can never promote index_values (no source_id column, line 433) and promotes products without any evidence_excerpt/source_locator (evidence test at 437 skips products, product_consumption, bid_benchmarks, index_values); check_calculation_runs skips 'assumptions' inputs (397) so an unknown assumption id is not detected, and recomputation runs only when an engine object is passed.
- **Reproduction / counter-example:**

```
validate(): SRC_PROHIBITED_IN_USE appears twice for one labor_rates row.  promote_validated(): product with source_locator=None and evidence_excerpt=None -> review_status 'validated'; index_values stay 'unreviewed'.
```

- **Suggested fix:** De-duplicate the table list; give index_values a derived source via indices.source_id; require evidence fields for every promoted table; check assumption inputs and approval status.

#### F1-026 - Questionable quantity derivations (fence-post, batt width, stud stack, missing fasteners, 10 ft wall, nail type)

- **Severity:** minor &nbsp; **Area:** data
- **Where:** `data/csv/work_item_components.csv; data/csv/work_items.csv` : WI-DRY-001/002/003 L2; WI-DRY-004 L2; WI-INS-001 L1; WI-FRM-001/002; WI-FRM-003
- **What is wrong:** Questionable quantity derivations (see arithmetic table): (1) drywall screws use 96/16 = 6 fasteners per 8 ft line but 48/16 + 1 = 4 lines, i.e. a fence-post +1 is applied to lines and not to fasteners per line: counting a screw at both ends gives 0.875/SF (walls, stored 0.75) and 1.125/SF (ceilings @12 in, stored 1.0); (2) R-13 batt: 1.0 SF of batt per SF of wall, but a 15 in batt in 16 in pitch consumes 15/16 = 0.9375 SF (the cavity is 14.5/16 = 0.906); (3) 'wall_height_ft: 8' with 92-5/8 in precut studs and three 1.5 in plates is a 97.125 in (8.09 ft) wall, so studs/SF (0.09375) is about 1.2% high for an 8 ft wall; (4) the scope says 'erect' but no bottom-plate-to-floor fasteners are quantified or excluded; (5) the 16d nail is hard-wired to a vinyl-coated 3-1/4 x 0.148 sinker while WI-FRM-004 explicitly says 'common'; (6) ASM-WALL-004 pairs a 10 ft steel-stud wall with WI-DRY-003, whose spec is 4x8 sheets: a 10 ft wall needs 4x10/4x12 board or horizontal hanging with butt joints and cut waste; neither the work item nor the assembly says which, and the (missing) waste factor would have to carry it; (7) WI-CON-003 describes 'two continuous bars on supports' while bar_supports_and_ties are excluded.
- **Reproduction / counter-example:**

```
arithmetic with Fractions in this report (section 'Arithmetic re-derivation')
```

- **Suggested fix:** Decide and document the fence-post convention; derive batt quantity from batt width / stud pitch; add stud-length/plate stack to the spec check; add the missing fasteners or exclude them explicitly.

#### F1-027 - Duplicate/irrelevant scope tokens; 50 LF duct labelled 'derived'

- **Severity:** minor &nbsp; **Area:** data
- **Where:** `data/csv/work_items.csv; data/csv/assembly_components.csv` : WI-PNT-004, WI-HVC-001..003 excluded_scope; ASM-HVAC-001 line 3
- **What is wrong:** Hygiene in definitions: duplicate tokens inside excluded_scope (permits_and_inspections twice on WI-HVC-001/002/003, surface_repair_and_patching twice on WI-PNT-004); copy-pasted irrelevant exclusions on HVC-003 (refrigerant_charge_beyond_factory, crane_or_rigging...). The '50 LF' of duct in ASM-HVAC-001 is a chosen spec parameter but is stored with qty_origin='derived' because assembly_components.qty_origin cannot be 'assumed'.
- **Reproduction / counter-example:**

```
python: [t for t in set(w['excluded_scope']) if w['excluded_scope'].count(t) > 1] for WI-HVC-001 -> ['permits_and_inspections']
```

- **Suggested fix:** Deduplicate; allow origin 'assumed'/'specified' on assembly_components or record the 50 LF in assemblies.spec_attributes with a basis.

#### F1-028 - Spec attributes absent from work-item specs, insufficient required attributes, copy-pasted capture-target sources

- **Severity:** minor &nbsp; **Area:** data
- **Where:** `data/csv/capture_targets.csv; data/csv/categories.csv` : TGT-2df95f5456, TGT-20edaf015f, TGT-5cd3255c4f, TGT-77f0fb2078, TGT-0e6e446bba; CAT-FRM-CON, CAT-PNT-*
- **What is wrong:** Spec/equivalence completeness and targets. (a) spec_key attributes appear that the work item's own spec_attributes do not state (WI-CON-001: slump 4 in, cement type II, no air, no admixtures; WI-HVC-001: SEER2 14.3, voltage 208/230, phase 1, split_outdoor, cooling_only), so the measurable spec is incomplete relative to what is priced; (b) required attributes are insufficient to stop non-equivalence: CAT-FRM-CON (joist hangers: no load rating/model/ICC-ES), CAT-PNT-* (no solids by volume/product tier, which drive coverage and price), CAT-FRM-FAS (no standard/coating class); (c) all five manufacturer-coverage targets (including curing compound, primer, paint) recommend SRC-USG-JOINT-COMPOUND-FAQ and SRC-DUNNEDWARDS-PDS-LIBRARY, and all 25 productivity targets recommend the same four old/highway sources although finding A2 says no free current building-trade norms were confirmed; (d) capture_targets has no origin/review_status/source columns; 86 of 129 material targets are required by no work item (priority 2).
- **Reproduction / counter-example:**

```
grep the capture_targets rows named above; compare WI-HVC-001 spec_attributes with its component spec_keys.
```

- **Suggested fix:** Add the spec attributes to the work item (or drop them from the key); extend required attributes; fix recommended sources per target; add origin/review_status to capture_targets.

#### F1-029 - Unqualified tons/gal in attributes, one HR unit for three hour kinds, rounded quantities

- **Severity:** minor &nbsp; **Area:** data/docs
- **Where:** `data/csv/work_items.csv; pipeline/costdb/dictionary.py; docs/methodology.md` : spec attributes capacity_tons, cooling_capacity_tons, container_gal; calc.py:856
- **What is wrong:** Rule 2 caveats: methodology.md says TON and GAL 'are never used bare', but spec attribute names/values use bare tons and gallons (capacity_tons, cooling_capacity_tons=3, container_gal=5/4.5) with no qualifier (refrigeration ton, US gallon) in the attribute; calculation_run_lines uses quantity_unit_id 'HR' for person-hours (labor), crew-hours (equipment) and nothing else distinguishes them except line_kind and formula text; numeric(24,10) rounding means stored quantities (e.g. 1/81 CY = 0.0123456790) are not the exact rationals the formulas state.
- **Reproduction / counter-example:**

```
see categories.csv CAT-HVC-EQP required_product_attributes ['cooling_capacity_tons', ...]
```

- **Suggested fix:** Rename to cooling_capacity_ton_refrig / container_gal_us (or store a qualifier attribute); add quantity_basis ('person_hour','crew_hour','equipment_hour') to calculation_run_lines; store qty as numerator/denominator or document tolerance.

#### F1-030 - Source register / findings inconsistencies

- **Severity:** minor &nbsp; **Area:** sources
- **Where:** `docs/source_findings.md; data/csv/regions.csv; data/csv/sources.csv; docs/methodology.md` : source_findings.md:25, 240, 11; regions.csv:15; sources.csv rows SRC-BLS-API-V2 / SRC-BLS-PUBLIC-DATA-API / SRC-BLS-PPI-CONSTRUCTION-INPUTS / SRC-BLS-OEWS-LA-MAY2025-NR; methodology.md section 10
- **What is wrong:** Internal inconsistencies in the source register and findings: (1) source_findings.md:25 says the example ECEC id 'CMU2010000000000D ... is not 17 characters' but it has exactly 17 characters (same text in agent_A1_labor_indices.json); (2) regions.csv:15 states MD 31084 is 'the geography BLS OEWS uses for LA' and SRC-BLS-OEWS-LA-MAY2025-NR says it is 'used for LA County trade wages', while finding A1 (source_findings.md:15) and the limitations of SRC-BLS-OEWS-MAY2025 say the division table was not located/confirmed; the labor capture targets are nevertheless addressed to REG-MD-31084; (3) the same BLS API FAQ page is registered twice with different reuse_status and tier (SRC-BLS-API-V2 permitted_with_attribution/B vs SRC-BLS-PUBLIC-DATA-API unknown_needs_check/A), SRC-BLS-PPI-CONSTRUCTION-INPUTS depends on 'see SRC-BLS-PUBLIC-DATA-API' (copyright page NOT seen), and source_findings.md:240 (A3 gap) says the BLS copyright page was not seen while line 11 (A1) and most BLS rows say it was; (4) indices.csv leaves base_period and seasonal_adjustment NULL (the facts are only in notes) although rule 8 asks for series metadata; (5) methodology.md section 10 still says CSI terms are recorded as 'prohibited' (register now: licence_required).
- **Reproduction / counter-example:**

```
grep -n CMU2010000000000D docs/source_findings.md ; python3 -c "print(len('CMU2010000000000D'))" -> 17
```

- **Suggested fix:** Correct the finding; mark the geography note as an assumption; merge or cross-reference the duplicate BLS API entries; fill base_period/seasonal_adjustment; update methodology section 10.

#### F1-031 - Retail importer: corrections impossible, weak price match, naive timestamps; hard-coded e-mail

- **Severity:** minor &nbsp; **Area:** connectors
- **Where:** `pipeline/connectors/retail_capture_import.py; pipeline/connectors/bls_api.py` : retail_capture_import.py:134-141, 158-165, 205-209; bls_api.py:66
- **What is wrong:** Importer: the observation id excludes price and retrieved_at, so a same-day recapture at a different price (or a correction of a wrong entry) is dropped as a 'duplicate' and the correct value cannot be recorded in an append-only table; the price-in-evidence test is a substring test ('2.50' passes for '$12.50'); naive retrieved_at timestamps are accepted (interpreted in the server time zone by PostgreSQL); prohibited-source rows are accepted with a warning (see F1-004). bls_api.py hard-codes a personal e-mail address in the User-Agent; index_values PK allows only one vintage per day.
- **Reproduction / counter-example:**

```
import_capture([row(price 12.80), row(price 11.80, later same day)])  -> second row: skipped_duplicates=['OBS-56f8695fdf'], only 12.80 stored
price_amount '2.50' with evidence_excerpt 'Now only $12.50 per sheet' -> accepted
```

- **Suggested fix:** Add price (and retrieved_at hour) to the id or add a 'supersedes_observation_id'; tokenise the price match; require tz-aware timestamps; make the contact address configuration.

#### F1-032 - Schema protection gaps (TRUNCATE, notes, units, missing CHECKs, waived errors)

- **Severity:** minor &nbsp; **Area:** schema
- **Where:** `schema/001_schema.sql` : 45-62 (forbid_history_rewrite), 64-84 (units), 361-445
- **What is wrong:** Protection gaps: TRUNCATE bypasses every append-only trigger (including 'TRUNCATE labor_rates CASCADE' wiping crew_members); notes is mutable on protected tables although the trigger message says only review fields; units is unprotected (to_base_num editable: SY->SF factor became 3 in v_unit_conversions), qualifier is free text (TON_FOO/'banana' accepted), base_unit_id may point to a different dimension; labor_rates has no check that total_hr equals its components or that includes_* flags agree with which component columns are filled, stat_wage may carry includes_payroll_taxes, burden_rates accepts effective_to < effective_from and wage_cap_annual on a per_hour basis; product_consumption allows coverage_qty/coats = 0; adjustment_factors allows a region factor from a region to itself and a time_index factor whose index.applies_to differs; validation_issues allows 'waived' on an error with free-text note only; assumptions allow self-approval.
- **Reproduction / counter-example:**

```
see pgtests.py results in this review (each statement returned ALLOWED).
```

- **Suggested fix:** BEFORE TRUNCATE triggers; remove notes from mutable list on observation tables or add notes_history; add the missing CHECKs/triggers; restrict qualifiers to an enum and verify dimension equality.

#### F1-033 - po_dates_chk depends on session TimeZone; v_price_latest_validated collapses NULL regions

- **Severity:** minor &nbsp; **Area:** schema
- **Where:** `schema/001_schema.sql` : 299 (po_dates_chk), 887-892 (v_price_latest_validated)
- **What is wrong:** po_dates_chk uses retrieved_at::date, which depends on the session TimeZone: the same row (observed_at 2026-10-24, retrieved_at 2026-10-24T05:00:00Z) is accepted under UTC and rejected under America/Los_Angeles; validate.py and the importer use yet other date semantics. v_price_latest_validated uses DISTINCT ON (product_id, region_id): rows with NULL region (zip/store only) from different cities collapse into one 'latest', MSRP/quote/retail channels and units are not separated.
- **Reproduction / counter-example:**

```
SET timezone='America/Los_Angeles'; insert observation (observed_at '2026-10-24', retrieved_at '2026-10-24T05:00:00Z') -> violates po_dates_chk; with timezone 'UTC' accepted.
```

- **Suggested fix:** Compare retrieved_at with (observed_at + 1 day) at timestamptz level or store an explicit retrieval date; add channel/unit/region-NOT-NULL conditions to the view or drop it.

#### F1-034 - spec_key normalisation quirks and 40-bit ids

- **Severity:** minor &nbsp; **Area:** ids
- **Where:** `pipeline/costdb/ids.py; pipeline/connectors/retail_capture_import.py` : ids.py:14-19, 22-34; importer 184-186, 207-209
- **What is wrong:** norm_attr_value quirks: Decimal accepts underscores so '5_8' normalises to '58' (different specs share a key); 'NaN'/'nan' raise TypeError instead of SpecError; fractions and decimals never merge ('15/32' vs 0.46875) so a correctly captured SKU can miss its target (false negative). make_id keeps 40 bits of SHA-1: on collision the importer treats a different observation as a duplicate (skipped) or merges two products with equal spec/pack.
- **Reproduction / counter-example:**

```
norm_attr_value('5_8') == '58'; norm_attr_value('NaN') -> TypeError: bad operand type for abs(): 'str'
```

- **Suggested fix:** Reject non-numeric forms explicitly (regex), normalise fractions, use >= 16 hex chars or detect collisions against the natural key.

#### F1-035 - calc_version is static, code_ref NULL on every run

- **Severity:** minor &nbsp; **Area:** calc/build
- **Where:** `pipeline/costdb/__init__.py; pipeline/scripts/build.py` : __init__.py:3-4; build.py:46
- **What is wrong:** calc_version is the static string 'costdb-calc/0.1.0' and every stored run has code_ref NULL (Engine(db, code_ref=None)), so a run does not identify the code that produced it; bugs fixed in calc.py do not change run ids.
- **Reproduction / counter-example:**

```
data/csv/calculation_runs.csv: calc_version 'costdb-calc/0.1.0', code_ref empty on all 35 runs.
```

- **Suggested fix:** Set code_ref to the git sha (or hash of calc.py) at build; include it in the fingerprint.

#### F1-036 - Person-hours per unit ignore member hours_per_shift

- **Severity:** minor &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 566, 574-577, 842-843
- **What is wrong:** Person-hours per unit on the labor line is crew_size x shift / daily output and ignores crew_members.hours_per_shift, while the cost uses member hours: a laborer working 10 h on an 8 h shift costs 0.5875/SF but is reported as 0.015 person-h/SF (true 0.01625).
- **Reproduction / counter-example:**

```
crew [TR-DRYW x2 8 h, TR-LAB x1 hours_per_shift=10], norm 1600 SF/shift: labor_cost 0.5875, labor line quantity 0.0150000000
```

- **Suggested fix:** Sum qty x hours over labor members for person-hours; keep crew-hours separate.

#### F1-037 - company_actual rates may include overhead/profit; derived loaded-rate row misattributes region/period

- **Severity:** minor &nbsp; **Area:** calc/schema
- **Where:** `pipeline/costdb/calc.py; schema/001_schema.sql` : calc.py:436-441; schema 361-412
- **What is wrong:** Rule 4 separation of overhead/profit: company_actual rates return total_hr regardless of the includes_* flags and the schema has no includes_overhead / includes_profit flag, so a billing-type company rate can be loaded and then marked up again by apply_markup. The derived loaded_employer_cost row (calc.py:1020-1034) takes region_id = run region even when the inputs came from an ancestor region, sets effective_from = as_of instead of the inputs' period, and for an assumed total stores base_wage_hr = 0 with includes_* all true.
- **Reproduction / counter-example:**

```
see calc.py:1020-1034
```

- **Suggested fix:** Add includes_overhead/includes_profit (must be false for use as a cost) and copy region/period from the governing input.

#### F1-038 - RunParams not validated (KeyError, 'Strict')

- **Severity:** minor &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 399-401, 61-64
- **What is wrong:** Parameter validation: labor_basis='bogus' raises KeyError; mode='Strict' is accepted, stored and would violate the DB CHECK only at load time; price_policy unchecked (F1-012); RunParams is not validated at all.
- **Reproduction / counter-example:**

```
run(db, labor_basis='bogus') -> KeyError: 'bogus' ; run(db, mode='Strict').run['mode'] -> 'Strict'
```

- **Suggested fix:** Validate enumerations in __post_init__.

#### F1-039 - Hard-coded default thresholds without basis; global Decimal context

- **Severity:** minor &nbsp; **Area:** calc/validate
- **Where:** `pipeline/costdb/calc.py; pipeline/costdb/validate.py; pipeline/costdb/units.py` : calc.py:65,74; validate.py:199,224,239,306; units.py:9
- **What is wrong:** Universal defaults without a stated basis (rule 6): max_price_age_days=365, max_rate_age_days=800, outlier 3x/(1/3) of median, 1% productivity reconciliation tolerance, STALE thresholds (365/800 days) are constants in code; the 365-day default EXCLUDES prices (unless a time index is supplied). units.py sets the global Decimal context precision (getcontext().prec = 40) at import time, a side effect on every other Decimal user in the process.
- **Reproduction / counter-example:**

```
grep the constants.
```

- **Suggested fix:** Move thresholds to a documented policy table with basis text; use a local decimal context.

#### F1-040 - as_of reproducibility: retrieved_at not filtered

- **Severity:** minor &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 259 (observations), 366-368, 403-406, 499-502
- **What is wrong:** As-of reproducibility: observations, labor, burden and equipment rows are selected by observed_at/effective period only; retrieved_at is not compared with as_of, so a re-run 'as of' 2026-09-10 uses a row retrieved on 2026-10-23 (only index values honour vintage_date). Together with F1-013 the same parameters can give different results after back-filling data.
- **Reproduction / counter-example:**

```
run(db, as_of=date(2026,9,10)) with the board observation retrieved_at 2026-10-23 -> complete
```

- **Suggested fix:** Add an optional knowledge_date parameter (default = as_of) and filter on retrieved_at/created_at.

#### F1-041 - work item status/valid_from/is_optional never consulted

- **Severity:** minor &nbsp; **Area:** calc
- **Where:** `pipeline/costdb/calc.py` : 772-874 (unit_cost) / work_items.status, valid_from, is_optional
- **What is wrong:** work_items.status ('retired'), valid_from, supersedes_version and work_item_components.is_optional are never consulted: a retired work item version or one whose valid_from is in the future is costed as 'complete'; components flagged is_optional are always included.
- **Reproduction / counter-example:**

```
WI-DRY-001 status='retired', valid_from=2030-01-01 -> run complete 0.997875; all material components is_optional=True -> material_cost still 0.447875
```

- **Suggested fix:** Refuse retired/not-yet-valid versions (or flag); price optional components only when selected.

#### F1-042 - Test-suite weaknesses

- **Severity:** minor &nbsp; **Area:** tests
- **Where:** `tests/*.py` : see section 'Weak or missing tests'
- **What is wrong:** Test-suite weaknesses: 7 PostgreSQL tests are skipped unless PGHOST/PGPORT is set; the first PG run in this review failed (test_python_generated_runs_and_json_columns_round_trip asserted 3 lines with inputs but the real data contributes 39 calc lines; fixed in the 02:39 test update) which shows coupling to the committed data; several data gates are vacuous on the current empty tables (validated-means-fetched, no-invented-numbers); test_quantities_match_independent_arithmetic re-uses the generator's own fence-post convention and covers about 20 of the 48 fixed-mode quantities; none of the defects F1-001 to F1-019 is caught by an existing test.
- **Reproduction / counter-example:**

```
python3 -B tests/run_tests.py (114 tests, 7 skipped without PG; OK with PG after the fix)
```

- **Suggested fix:** Add the tests listed in 'Weak or missing tests'; make PG tests run in CI; add property tests for selection logic.

## 3. Weak or missing tests

`python3 -B tests/run_tests.py`: 114 tests, OK (7 skipped without PostgreSQL; all pass with it). Read critically:

| area | gap |
|---|---|
| pipeline/costdb/calc.py _consumption_qty / qty_mode=from_product_consumption | No test at all (grep 'consumption' in tests/ finds only a fixture field). 5 of 25 work items depend on it. Would have caught F1-001 (pairing, unit, zero coverage). |
| with_assumptions mode | Only a waste assumption is exercised (test_assumed_waste_refused_in_strict_and_flagged_in_assumption_mode). Productivity (crashes, F1-014), price, labor_rate, equipment_rate, quantity, benefits, workers' comp assumptions and value_text/units/sign/expiry/duplicate-approval cases are untested (F1-015). |
| Region selection | test_region_factor_only_for_foreign_prices_never_twice covers one foreign and one local price; nothing for allow_ancestor_region_prices, ancestor vs local recency, sub-region observations, REG-US target (F1-006). |
| Review-status handling | Tests flip only the observation's review_status; no test flips sources, products, crews, indices, assumptions, factors (F1-002, F1-005); no test for licence_required/restricted_no_storage in calc/validate (F1-004). |
| Labor selection | No test with several rows per trade (apprentice, overtime, project_type, determination vs federal), no burden tie/class_code test, no per_hour basis, wage_plus_fringe, general_liability/other (F1-007..009); no test where includes_payroll_taxes/workers_comp is true with component columns filled (F1-008). |
| Equipment | Only the operator double-count and one hourly-rate case; no fuel, min-rental, delivery, rental_day, equipment component without equipment member, OPERATOR_NOT_PRICED, TR-OPR operator without is_operator (F1-016). |
| Adjustments | Conditions: only the 'no factor exists' and 'valid factor' cases; no unreviewed/expired/assumed/other-kind factor (F1-010). No quantity-tier or quantity-factor test, no factor validity window, no flagged factor source (F1-005, F1-011). |
| Time index | One happy-path test; nothing for applies_to mismatch, young price with time_index_id, quarterly/'other' frequency, missing as_of-month value, flagged index (F1-017). |
| Run identity | test_reproducible_run_id checks that a changed PRICE changes the id; nothing checks that a different record with the same value, or a different missing set, changes it (F1-013). |
| price_policy / RunParams validation | No test for any value other than the default (F1-012, F1-038). |
| Markup | Hand-computed example only; no negative/oversized input, no header semantics test - the test asserts the price is stored in direct_cost_total, thereby encoding F1-019 as expected behaviour. |
| Assembly | No test that children receive their own quantity (tier/quantity factors), no cost_tags overlap, no assembly spec vs child spec (F1-011, F1-023); real-data assembly test only checks that the missing codes are present. |
| Validator | Each rule has a firing test (good), but there are no tests for rules that do not exist (spec contradiction, assembly inclusions), duplicate-issue emission (F1-025) or the promotion gate for index_values/products without evidence. |
| PostgreSQL | Constraint tests cover 11 CHECKs and append-only on 3-4 tables; none for TRUNCATE, calculation_runs/lines, products, definition tables, units, validated-without-reviewer, spec_key/pack consistency, session TimeZone (F1-003, F1-020..022, F1-032, F1-033). 7 tests are skipped unless PGHOST is set. |
| Data gates | test_validated_means_fetched_primary_with_hash, test_no_numbers_were_invented_for_missing_inputs and similar pass vacuously on empty tables; test_quantities_match_independent_arithmetic reuses the generator's formulas (e.g. F(4*6,32) for screws) so it cannot detect convention errors (F1-026) and covers about 20 of the 48 fixed-mode quantities; assembly quantities are asserted as the set {1,2,50} without checking each against its work item. |
| Connectors | Importer tests do not cover same-day recapture, substring price match, naive timestamps, licence_required/prohibited manual capture (F1-031); OEWS parser untested against duplicate (area, occupation, industry) rows or O_GROUP. |

## 4. Arithmetic re-derivation

Derived independently with `fractions.Fraction` from the stated spec (not from the generator's formulas). Unit factors:

| unit | stored (num / den) | my value | match |
|---|---|---|---|
| SY | 9 / 1 | 9 (3 ft x 3 ft) | yes |
| CY | 27 / 1 | 27 (3^3 CF) | yes |
| TON_SHORT | 2000 / 1 | 2000 lb | yes |
| TON_LONG | 2240 / 1 | 2240 lb | yes |
| TON_METRIC | 100000000000 / 45359237 | 1000 kg / 0.45359237 kg per lb = 10^11/45359237 = 2204.62262185 | yes |
| GAL_US | 77 / 576 CF | 231 in^3 / 1728 in^3 per CF = 231/1728 = 77/576 | yes |
| GAL_IMP | 284130625 / 1769802912 CF | 4.54609 L / (1728 x 16.387064 mL = 28.316846592 L per CF) = 284130625/1769802912 (computed with Fractions, two routes) | yes |
| EA, LF, SF, CF, LB, HR, TON_REFRIG (bases) | 1 / 1 | 1 / 1 | yes |
| DAY | not fixed (NULL) | shift length is crew-specific | yes |

Quantities per unit (`work_item_components.qty_per_unit`) and assembly factors:

| item | stored | my value | match | note |
|---|---|---|---|---|
| WI-FRM-001 L1 studs per SF (16 in o.c., 8 ft) | 0.09375 | 0.09375 | yes | (12/16)/8 |
| WI-FRM-001 L2 plate LF per SF (1 bottom + 2 top) | 0.375 | 0.375 | yes | 3/8 |
| WI-FRM-001 L3 16d nails per SF | 0.46875 | 0.46875 | yes | 4 x 3/32 + (12/16)/8; bottom-plate-to-floor nails not counted (F1-026) |
| WI-FRM-002 L1 studs per SF 2x6 | 0.09375 | 0.09375 | yes |  |
| WI-FRM-003 L1 joist LF per SF (2x10 @16) | 0.75 | 0.75 | yes | 12/16, independent of span |
| WI-FRM-003 L2 hangers per SF (2 per joist, 12 ft span) | 0.125 | 0.125 | yes | 2 x 0.75/12 |
| WI-FRM-004 L1 sheathing SF per SF | 1 | 1 | yes |  |
| WI-FRM-004 L2 8d nails per SF | 2.0 | 2.0 | yes | (24 ft x 12/6 + 2 x 8 ft x 12/12)/32 |
| WI-FRM-005 L1 steel studs per SF (16 in o.c., 10 ft) | 0.075 | 0.075 | yes |  |
| WI-FRM-005 L2 track LF per SF | 0.2 | 0.2 | yes | 2/10 |
| WI-FRM-005 L3 #8 screws per SF | 0.3 | 0.3 | yes | 4 x 0.075 |
| WI-FRM-006 L1 blocking stock LF per LF (14.5 in @16) | 0.90625 | 0.90625 | yes | (16-1.5)/16 |
| WI-FRM-006 L2 16d nails per LF (4 per block) | 3 | 3 | yes | 4 x 12/16 |
| WI-DRY-001 L2 screws per SF, formula as stored (4 lines x 96/16)/32 | 0.75 | 0.75 | yes | same convention as the generator; WI-DRY-002/003 use the identical formula |
| WI-DRY-001 L2 screws per SF counting both ends of each line (4 x (96/16+1))/32 | 0.75 | 0.875 | NO | fence-post inconsistency, F1-026 |
| WI-DRY-004 L2 ceiling screws per SF, formula as stored (4 x 96/12)/32 | 1.0 | 1.0 | yes |  |
| WI-DRY-004 L2 counting both ends (4 x (96/12+1))/32 | 1.0 | 1.125 | NO | fence-post inconsistency, F1-026 |
| WI-DRY-005 L1 tape LF per SF (12 ft shared joint per sheet / 32 SF) | 0.375 | 0.375 | yes |  |
| WI-INS-001 L1 batt SF per SF wall (15 in batt, 16 in pitch) | 1.0 | 0.9375 | NO | 15/16; cavity 14.5/16 = 0.906; F1-026 |
| WI-CON-001 L1 CY per SF, 4 in slab | 0.0123456790 | 0.0123456790 (1/81) | yes | rounded to 10 dp |
| WI-CON-001 L4 chairs per SF @48 in each way | 0.0625 | 0.0625 | yes | 1/16 |
| WI-CON-002 L1 CY per SF, 6 in slab | 0.0185185185 | 0.0185185185 (1/54) | yes |  |
| WI-CON-002 L3 rebar LF per SF #4 @16 each way | 1.5 | 1.5 | yes | 2 x 12/16 (laps in waste) |
| WI-CON-002 L4 chairs per SF | 0.0625 | 0.0625 | yes |  |
| WI-CON-003 L1 CY per LF, 18 x 12 in footing | 0.0555555556 | 0.0555555556 (1/18) | yes | 1.5 CF/27 |
| WI-CON-003 L2 rebar LF per LF (2 bars) | 2 | 2 | yes |  |
| WI-CON-004 L1 J-bolts per LF @48 in | 0.25 | 0.25 | yes | 12/48 |
| WI-PNT-004 L1 caulk US gal per LF, 1/4 x 1/4 x 12 in | 0.0032467532 | 0.0032467532 (0.75/231) | yes |  |
| Stud stack: 92.625 in stud + 3 x 1.5 in plates vs 'wall_height_ft 8' | 96 in implied | 97.125 in (8.094 ft) | NO | 1.2% taller than the stated 8 ft, F1-026 |
| Assembly factors: 16 components x 2 faces (ASM-WALL-001..004: DRY, DRY-005, PNT-001, PNT-002) | 2 SF per SF | 2 (one layer/finish per face) | yes | all other assembly qty = 1 SF/SF or 1 LF/LF or 1 EA |
| ASM-HVAC-001 duct qty | 50 LF per EA | 50 (spec parameter, not derivable) | n/a | chosen parameter labelled 'derived', F1-027 |

Engine arithmetic checked by hand and re-run (all match; the project's own tests assert the same values): WI-DRY-001 total 0.997875 (board 1.1 x 0.40, screws 0.75 x 1.05 x 0.01, labor 880/1600); person-hours 3 x 8/1600 = 0.015; stat-loaded labor 42.33298...; markup 115.50 x 1.10 = 127.05 and 115.50 / 0.90 = 128.333...; index adjustment 0.40 x 210/200 = 0.42; SY->SF pack conversion 3.60/3/9 per SF.

## 5. Things I could not verify

- Every external fact (SOC codes, FIPS/CBSA codes, IRS 2026 wage base 184,500, EDD ETT 0.1% on 7,000, BLS OOH carpenter median 60,580 / 29.12, PPI/ECI series ids and base periods, Caltrans/USACE/DIR/SAM statements): network is blocked; I could only check internal consistency and compare with my own knowledge (SOC, FIPS, CBSA, 2026 SS base and 1982=100 for WPUID612 all agree with what I know, but this is not verification).
- Construction-practice judgments in F1-026 (fence-post screw count, batt width vs pitch, 16d sinker vs common, 8 ft vs 97-1/8 in wall) are from memory of IRC/GA-216-type practice, not from a cited standard.
- I did not run pipeline/scripts/build.py (it rewrites data/ and docs/); I did not run gen_pilot_definitions.py / gen_reference.py / build_docs.py; the pdf_tables connector (pdfplumber/pypdfium2) and openpyxl OEWS path were not exercised; BLS API client and OEWS parser were read, not run against real files.
- Supabase specifics (RLS, PostgREST exposure of schema costdb, PgBouncer) and PostgreSQL versions other than the scratch 16 server.
- The repository changed while I was reviewing (bulk update at 02:39:19 by the F2 fix round: reuse_status enum, NO_DATA_USE, validator, importer, tests; PG test fixed 02:39:55; data rebuilt 02:40:12). Line numbers and results refer to that snapshot; I re-ran the test suite (114 tests OK with PG) and all counter-examples on it. No git commands were used, so I cannot say which lines the fix round touched beyond what I diffed by hand (validate.py old copy).
- Concurrency/performance (O(n*m) scans in calc/validate), time-zone behaviour of the Python code on a non-UTC host, and Windows path handling.
- Whether 'search-summary' evidence quotes match the live pages (by design nobody could open them).

## 6. Housekeeping

The only files written by this review are this report, `data/raw_agent_returns/agent_F1_findings.json` and scratch files under `/tmp/claude-0/f1/`; the scratch PostgreSQL database `f1_review` was dropped at the end. No git command was run; no repository file other than the two outputs was modified.
