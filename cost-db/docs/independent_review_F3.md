> **Provenance note.** This is the verbatim report of reviewer F3 (an agent that did not write the system), copied into the repository. File paths of the form `/tmp/claude-0/f3/...` refer to the reviewer's scratch directory; the reproduction scripts it cites are copied to `data/raw_agent_returns/f3_repro/` (`repro_pg.sh` needs `PGHOST/PGPORT/PGUSER` of a scratch server; the Python ones run as `PYTHONPATH=pipeline:. python3 -B N_python.py`). The machine-readable list is `data/raw_agent_returns/agent_F3_findings.json`. The author's response is the *Resolution* section at the end of this file; where it disagrees with a verdict above, the reviewer's text stands until a further review says otherwise.

# Independent review F3 - re-check of the F1 fixes and search for new defects

Reviewer: Agent F3 (independent; did not write the system and did not write F1). Date: 2026-10-24. Repository snapshot: bf5dad1 (code and data); HEAD moved to 066c70a (docs only: README, STATUS, methodology, worked examples, author's resolution table) while the review ran - code, schema, data and tests are byte-identical, the suite was re-run on HEAD (229 tests OK).

Method: every F1 counter-example was re-run against the rewritten code with the synthetic fixtures (tests/fixtures/synthetic.py) and, for database findings, against a scratch PostgreSQL 16.15 loaded with schema/001_schema.sql, 003_comments.sql and data/csv; nothing in the repository, its docs or commit messages was taken as proof. Scripts and logs are in /tmp/claude-0/f3/ (t0NN.py = F1 re-checks, repro/ = new-defect reproductions, mut/ = mutation tests). The original repository was never modified: every mutation ran in a throw-away copy.

## 1. Result in one paragraph

Of the 42 F1 findings, **29 are FIXED, 13 are PARTIALLY FIXED, 0 are NOT FIXED**, 0 not applicable. The engine rewrite is largely sound: two of the three critical F1 defects (F1-001, F1-003) are fully fixed, F1-002 is fixed for every table F1 named but the same class survives for regions and equipment types, and 106 of 124 deliberate re-introductions of fixed engine/validator/importer defects are caught by the test suite. I found **34 new defects: 0 critical, 13 major, 21 minor**. The major ones fall in four groups: (a) the database gates can still be bypassed or opened with one statement (F3-01 pg_temp shadow table, F3-02 crews ungated, F3-03 mutable sources/indices); (b) the Python path accepts data that PostgreSQL would reject and then produces silent 'complete' results (F3-07 zero price, F3-08 no range checks, F3-09 arbitrary tier choice); (c) engine paths that still lose or misreport information (F3-04 day-rate fuel, F3-05 ignored rate pins, F3-10 assumed factors unflagged, F3-11 assumed/rejected regions read in strict mode, F3-12 equipment rate basis ignored); (d) F3-13: the build pipeline crashes on its second run after the first promotion, and F3-06: the new assembly scope statements contradict themselves. Nothing in the real data (0 prices, 35 incomplete strict runs, 0 validated records) is wrong because of these defects; they matter as soon as real data is entered.

**What holds up (checked by running it):**

- The suite is green at both commits (229 tests; the PostgreSQL tests start their own cluster).
- generator and build are reproducible: gen_pilot_definitions.py run in a copy reproduces every committed definition CSV byte-identically; build.py reproduces the 35 committed runs (ids, lines, missing inputs) and all reports (only code_ref differs because the copy has no git); examples/run_examples.py reproduces worked_examples.md exactly.
- The real data are internally consistent: with a generic synthetic price/crew/productivity set (t_e2e.py) all 25 work items and all 10 assemblies price to status complete (units convert, components resolve, equipment belongs to its crew), and each assembly total equals the sum of quantity x child cost; 129 capture-target spec_keys recompute in Python and in SQL; 23 fixed quantities re-derive exactly with Fractions; validate() on the real data returns no issue.
- The real strict runs are honest: 35 runs, all incomplete, 0 totals stored, gaps = missing waste / price / crew / norm / coverage / definition review; nothing in data/csv is validated and no number has been invented.
- Hand arithmetic matches: unit cost 0.999188, loaded labor 42.3330 (UI cap 0.114423/h), markup 127.05 vs margin 128.33, index 0.40 x 210/200 = 0.42, SY/GAL_IMP conversions, per-product coverage pairing.

## 2. Verdict per F1 finding

| id | F1 sev | verdict | evidence (command / outcome) | residual / why not fully fixed |
|---|---|---|---|---|
| F1-001 | critical | **FIXED** | t001.py/t001c.py on paint_db: material 0.125 = median(0.05, 0.20) of per-product costs, unchanged when ids are renamed; coverage in SY on an SF item -> 0.102778 = median(0.005556, 0.20) (correct); rate for 2 coats @175 SF/gal -> qty 0.005714 = 2/350; GAL_IMP coverage converted; coverage 0 / coats 0 -> product dropped, no DivisionByZero; flagged product leaves the pool. | No test fails if the coats_in_rate divisor is removed (mutant F001f survives). A product dropped for bad coverage leaves a one-product 'median' with no flag (F3-29). |
| F1-002 | critical | **PARTIALLY FIXED** | t002.py: source rejected/flagged, crew rejected/unreviewed, product flagged/unreviewed (also when pinned), index flagged, assumption rejected -> every run incomplete (PRICE_MISSING / CREW_UNUSABLE / INDEX_UNUSABLE / WASTE_MISSING); strict mode never reads an assumption. | Every table named by F1 is now gated. The class (a rejected/flagged row that the engine reads is still used) persists for regions (a region with review_status='rejected' still carries the ancestor wage into a strict run: F3-11) and for equipment_types (typically_needs_operator is read without any status test). The engine also trusts review_status alone: the DB/validator holes that let a row become 'validated' wrongly are F3-01/02/03. |
| F1-003 | critical | **FIXED** | pg003.sql on the real CSVs: UPDATE (status/total/lines), DELETE, TRUNCATE (also TRUNCATE sources/regions/units/trades/categories ... CASCADE) all rejected by triggers; a complete run without lines is rejected at commit. | A fabricated complete run with an invented line (inputs []) can still be INSERTed and passes validate() without an engine (F3-21). |
| F1-004 | major | **PARTIALLY FIXED** | t004.py: licence_required, restricted_no_storage, prohibited -> engine run incomplete, SRC_PROHIBITED_IN_USE (+SRC_PROHIBITED_VALIDATED when validated); t031.py: importer refuses SRC-LOWES (prohibited), SRC-FRED-API, SRC-CSI-MASTERFORMAT-TERMS whatever the capture method. | Not consistent for crews: a crew from a prohibited source is refused by the engine but neither flagged by the validator (SOURCE_TABLES lacks crews) nor refused by the database source gate (F3-02). |
| F1-005 | major | **FIXED** | t005.py: region factor of a prohibited source -> PRICE_MISSING (factor not applied); with two valid factors the newest valid_from (3.00) wins deterministically; condition/quantity factors use the same _factor_issue. | - |
| F1-006 | major | **FIXED** | t005.py/t006b.py: exact LA price 0.40 beats a newer state price 0.50 even with allow_ancestor_region_prices=True; ancestor/sub-region prices are off by default and flagged PRICE_FROM_ANCESTOR_REGION:<id> with region in the line input; retrieved_at parsed as instant (mixed offsets). | Ties among equally old observations are broken by observation id; for tier prices that is arbitrary (F3-09). Mutants F006b (best class across products) and F006d (sub-region default) survive. |
| F1-007 | major | **FIXED** | t007.py: with 30 (journeyman) / 12 (apprentice) / 45 (overtime) rows the base wage is 30 (total 42.3330); two classifications -> LABOR_RATE_AMBIGUOUS until RunParams.classification is set; PW rows picked by wage_regime and wage_class; private + prevailing -> failed PW_NOT_APPLICABLE. | - |
| F1-008 | major | **FIXED** | t008.py: PW row base 50 + fringe 20 + payroll tax 6 + WC 5 + other 3 -> total_hr 84 (was 70); total 99 vs components 84 -> LABOR_TOTAL_MISMATCH (blocking); stated-total-only rows flagged LOADED_RATE_NOT_ITEMIZED; general_liability/other rows flagged OMITTED_BURDEN (not costed: the author's documented decision); state_ett only for CA. | - |
| F1-009 | major | **FIXED** | t009.py: 2025 Medicare 1.00% listed before 2026 1.45% -> 0.4350 (was 0.30); local generic row beats national trade-specific row; value ties -> BURDEN_AMBIGUOUS; wc_class_code selects the row; UI cap 0.114423/h. | - |
| F1-010 | major | **FIXED** | t010.py: unreviewed / expired / not-yet-valid / assumed(strict) factor -> CONDITION_FACTOR_UNUSABLE (incomplete); no factor or other-kind only -> CONDITION_FACTOR_MISSING; two different usable values -> CONDITION_FACTOR_AMBIGUOUS. | Mutant F010c (ambiguity check removed) survives. |
| F1-011 | major | **FIXED** | t011.py: tier price (min 100000) ignored without RunParams.quantity (0.40) and used at 200000 (0.03125, QTY_TIER_PRICE flag); expired quantity factor not applied, upper bound exclusive; assembly children get their own quantity (1200 SF / 1800 EA). | Which of two eligible tier prices is used is arbitrary (F3-09). |
| F1-012 | major | **FIXED** | t012.py: median_of_latest_per_product 0.45, latest 0.50, 'bogus' -> ValueError. | - |
| F1-013 | major | **FIXED** | t013.py: same price from another observation id/store/retrieved_at -> different run_id; quantity change -> different; real incomplete runs with different gaps -> different ids; build.py run in a copy reproduces all 35 committed run ids, lines and CSVs byte-identically (only code_ref differs: the copy has no git). | run_id depends on physical row order of products/observations (F3-16); the 'gaps' part of the fingerprint is untested (mutant F013b survives; partly redundant with the UNRESOLVED line text). |
| F1-014 | major | **FIXED** | t014.py: approved productivity assumption 1600 SF -> complete 0.999188, has_assumptions=True; strict -> incomplete PRODUCTIVITY_MISSING. | - |
| F1-015 | major | **PARTIALLY FIXED** | t014.py: value_text-only, waste -0.5 / 5 / 1, two approved rows, approver == proposer (case/space variants), expired, no expiry, 'proposed' all refused; benefits/WC assumption units honoured. | The same class (no sign/range check) is still reproducible for the primary field: component waste_factor 5 -> complete 2.409188, -0.5 -> 0.209188, negative price/wage/daily output -> complete (F3-08). Waste assumption unit not checked; an unusable assumption is reported as plain WASTE_MISSING without the reason (F3-25). |
| F1-016 | major | **PARTIALLY FIXED** | t016.py (hourly basis): fuel 9 added (0.136 = (25+9)*8/2000), FUEL_NOT_PRICED is a gap, equipment component without crew member -> CREW_NO_EQUIPMENT, TR-OPR operator by trade -> OPERATOR_DOUBLE_COUNT, operator needed and absent -> gap; delivery and minimum rental are flagged with their amounts, not priced (documented decision). | rental_day path never adds fuel and never flags it (F3-04: 0.075 vs hourly 0.136 for the same rate). Equipment hours are not scaled by a productivity_condition factor although the cost is (F3-24). |
| F1-017 | major | **FIXED** | t017.py: labor index on a material price -> failed INDEX_APPLIES_TO_MISMATCH; 287-day-old price indexed 0.40 -> 0.42; unpublished as-of month -> fallback to latest published period, flagged INDEX_LATEST_PUBLISHED_PERIOD_USED; quarterly ok; frequency 'other' -> INDEX_FREQUENCY_UNSUPPORTED. | The test for 'index values published after known_at are not used' is vacuous (all other inputs are also unknown at that as_of); mutant F017d survives. |
| F1-018 | major | **FIXED** | t018.py: retail needs accept_retail_proxy=True (RunParams refuses otherwise; observation excluded with reason); run stores price_basis retail_proxy / contractor_quote / mixed and input_review_floor; assembly inherits the basis. | A retail_promo-channel row with promo_flag=False is treated as ordinary retail (F3-14). |
| F1-019 | major | **FIXED** | t019.py: direct_cost_total 0.999188, price_total 1.269468 (hand: 1.2694684); margin price 1.282291; overhead 10, profit -2, margin 1, contingency -0.1 refused; basis text changes the run id; markup of markup refused. | - |
| F1-020 | major | **PARTIALLY FIXED** | pg020.sql: validated without reviewer -> CHECK; validated from snippet-only source -> trigger (observations, index_values, sources); every review_status change logged in review_events. | Bypassable: pg_temp shadow table defeats the source gate and the review log (F3-01); crews are not gated at all (F3-02); sources.verification_method / indices.source_id are mutable and unlogged (F3-03). |
| F1-021 | major | **FIXED** | pg021.sql: UPDATE of products (spec_key/content/attributes/name), work_item_components, work_items, assemblies, assembly_components, crews, crew_members, DELETE of components all rejected; only review fields/notes (and work_items.status) may change. | categories, regions, trades, equipment_types, indices, sources remain editable (F3-03, F3-22). No PG test fails if the assembly_components, adjustment_factors or crew_members triggers are removed (mutants survive). |
| F1-022 | major | **FIXED** | pg022.sql: 'garbage-key' product, product in non-leaf category CAT-DRY, observation of 5 LB for a 32 SF product -> all rejected by triggers; compute_spec_key equals Python on all 129 capture targets (psql check). | Python/SQL normalisation still differs on padded numeric strings, NBSP and 'İ' (F3-18). |
| F1-023 | major | **PARTIALLY FIXED** | t023.py: component re-pointed to the 5/8 spec -> WI_SPEC_COMPONENT_MISMATCH; child swapped -> ASM_SPEC_CHILD_MISMATCH; duplicate cost tags -> ASM_DUP_TAG; material_specs attribute tweak -> WI_SPEC_ATTRS_MISMATCH. | The exact F1 counter-example still returns []: assembly spec_attributes['board'] changed to '5/8 in Type X' while the children hang 1/2 in regular -> validate() == [] (only the work_items list is compared, not the descriptive text). |
| F1-024 | major | **PARTIALLY FIXED** | tdata.py/tdata3.py: included_scope is now 7-16 tokens per assembly (derived from the children); excluded_scope no longer copy-pasted. | excluded_scope lists tokens the assembly itself prices, e.g. ASM-WALL-004 excludes gypsum_board, taping_and_finishing, primer, finish_coats, board_hanging while pricing them; ASM-HVAC-001 excludes ductwork, indoor_unit_and_coil, thermostat_and_controls, outdoor_unit while pricing them (F3-06). |
| F1-025 | minor | **FIXED** | t025b.py: one SRC_PROHIBITED_IN_USE per labor row (was two); index_values promotable through their series source; a product without source_locator/evidence is not promoted; assumption inputs checked in check_calculation_runs. | New promotion gaps: F3-15. |
| F1-026 | minor | **FIXED** | t026.py re-derives 23 fixed quantities with Fractions independent of the tests: screws 0.875 / 0.8333 / 1.09375 per SF (fence-post at both ends), batt 15/16, wall 97.125 in = 8.09375 ft, bottom-plate fasteners explicit exclusion, 10 ft wall uses 4x12 board, bar supports excluded in WI-CON-003 - all match. | - |
| F1-027 | minor | **PARTIALLY FIXED** | tdata2.py: no duplicate tokens in any work item or assembly. | ASM-HVAC-001 line 3 (50 LF duct) still has qty_origin='derived' (the schema does not allow another value); the formula text says 'spec parameter'. |
| F1-028 | minor | **PARTIALLY FIXED** | t028.py: material_specs now state every priced attribute; material targets no longer carry copy-pasted recommended sources; capture_targets has origin/review_status. | All 25 productivity targets still recommend the same four 1996-2021 sources; CAT-FRM-CON still has no load rating, CAT-PNT-* no solids/tier (the author documents these as open). |
| F1-029 | minor | **FIXED** | No bare TON/GAL attribute remains (cooling_capacity_ton_refrig, container_gal_us); calculation_run_lines.quantity_kind = person_hours / equipment_hours / material_qty (seen on the synthetic-fixture run lines; real runs are unresolved); 10-dp rounding is documented in the author's resolution table and the exact rationals are in qty_formula. | - |
| F1-030 | minor | **FIXED** | grep/CSV checks: correction note on the 17-character ECEC id, geography notes marked ASSUMED, duplicate BLS API entries cross-referenced, indices carry base_period/seasonal_adjustment, methodology section 10 says licence_required. | - |
| F1-031 | minor | **FIXED** | t031.py: same-day recapture at another price -> new observation; price 2.50 vs excerpt '$12.50' refused; naive/date-only/invalid-offset timestamps refused; prohibited/no-storage/licence sources refused; BLS User-Agent contact comes from COSTDB_CONTACT. | The token match is still weak (price 5 is accepted for 'Item 5 of 10: $12.98'); see F3-23. |
| F1-032 | minor | **PARTIALLY FIXED** | pg032.sql: bare TON/GAL/'banana' qualifier, wrong-dimension base unit, per_hour cap, effective_to < from, coverage/coats 0, self region factor, waived error, self-approval, out-of-range assumptions all rejected; TRUNCATE guarded; units immutable. | notes is still mutable on protected tables; labor_rates total_hr 999 vs components 81 inserted without error; includes_* flags vs filled component columns unchecked in the DB (the engine checks them). |
| F1-033 | minor | **PARTIALLY FIXED** | pg033.sql: the F1 row is accepted under UTC, America/Los_Angeles and Pacific/Kiritimati. | v_price_latest_validated is keyed on COALESCE(region, zip, store) but still mixes retail, quote and MSRP channels and units into one 'latest'. |
| F1-034 | minor | **PARTIALLY FIXED** | '5_8' stays '5_8', 'NaN' -> 'nan' (no TypeError); ids are 12 hex and the importer rejects id collisions of different content (code read, not provoked). | '15/32' vs 0.46875 are still different keys (false negatives only; the author documents it); new Python-vs-SQL divergences on padded numeric strings (F3-18). |
| F1-035 | minor | **FIXED** | CALC_VERSION = costdb-calc/0.2.0+<sha1 of calc.py, units.py, ids.py, enums.py>; all 35 committed runs carry the current version and code_ref 'dbfb63f+uncommitted'; build.py reproduces the committed run ids. | No test fails if the fingerprint is removed (mutant F035 survives). |
| F1-036 | minor | **FIXED** | t036.py: crew with one member at 10 h -> labor 0.5875, person-hours 0.01625 (was 0.015). | - |
| F1-037 | minor | **FIXED** | t036.py: company rate with includes_overhead -> unusable; derived loaded_employer_cost row carries REG-MD-31084 and 2026-05-01 from the governing wage record. | - |
| F1-038 | minor | **FIXED** | t012.py: bogus labor_basis, 'Strict', unknown channel, negative age, quantity 0, str as_of, 'Private' all raise ValueError at construction. | Edge cases accepted: known_at as datetime, annual_paid_hours=Infinity, unknown region_id (F3-20). |
| F1-039 | minor | **FIXED** | No result-affecting default threshold in calc.py (max ages default None); validator thresholds live in DEFAULT_POLICY with stated bases; units.py uses a local Context. | The engine itself depends on the ambient Decimal context (F3-19); no test guards the units-module context regression (mutant survives). |
| F1-040 | minor | **FIXED** | t040.py: as_of 2026-09-10 with rows retrieved 2026-10-23 -> incomplete; with known_at=2026-10-24 -> complete. | known_at compares UTC dates; review decisions and definitions are not 'as of' (F3-28). |
| F1-041 | minor | **FIXED** | t041.py: retired -> failed DEFINITION_RETIRED; valid_from 2030 -> failed; unreviewed -> incomplete DEFINITION_NOT_REVIEWED; flagged -> failed; optional components excluded unless include_optional. | - |
| F1-042 | minor | **PARTIALLY FIXED** | 229 tests pass; database tests start their own server and fail (not skip) without one; one regression class per F1 engine finding; independent arithmetic. Mutation test (one reverted fix per copy, original untouched): 124 engine/validator/importer mutants -> 106 killed (one of them, IDS-NORM, only when the PostgreSQL tests run), 18 survive; 50 schema mutants -> 36 killed, 14 survive (17 raw survivors; 3 were redundant/ill-formed and are killed once re-formulated). | See section 4 of the report: fixes without a failing test, and the false claim in STATUS.md that every protection trigger is exercised. |

Counts: FIXED 29, PARTIALLY FIXED 13, NOT FIXED 0, NOT APPLICABLE 0.

Partially fixed: F1-002, F1-004, F1-015, F1-016, F1-020, F1-023, F1-024, F1-027, F1-028, F1-032, F1-033, F1-034, F1-042.

## 3. New defects

Severity as in F1: critical = wrong or unverifiable result produced silently in the default/strict configuration, or the database allows a state the rules forbid that falsifies results; major = wrong result in a realistic configuration, crash, or a documented guarantee that does not hold; minor = hygiene or edge case. I found no new critical defect.

| id | severity | area | title |
|---|---|---|---|
| F3-01 | major | schema | Any session can defeat the database gates (validated-needs-fetch, restricted-source, spec/pack integrity, review log) with a TEMP table that shadows a bare table name |
| F3-02 | major | schema/validate | crews are outside the source gate and outside the validator's source checks: a crew can be 'validated' from a never-fetched or prohibited source |
| F3-03 | major | schema | sources and indices are mutable and unlogged: one UPDATE of sources.verification_method (or indices.source_id / sources.reuse_status) opens every gate; fetched_primary requires no evidence |
| F3-04 | major | calc | equipment_basis='rental_day' drops fuel silently (fuel_included=False and fuel_cost_hr known are ignored, no flag): F1-016(a) persists on the day-rate path |
| F3-05 | major | calc | crew_members.labor_rate_id / equipment_rate_id ('pinned rate, overrides resolution' per the data dictionary) are never read by the engine |
| F3-06 | major | data | Assembly excluded_scope lists tokens the assembly itself prices (the F1-024 'derive exclusions from children' rule is token-name based) |
| F3-07 | major | calc/validate | A zero price is a valid, complete, strict input (material priced at $0, validator only warns) |
| F3-08 | major | calc/validate | No range validation outside the database: component waste_factor, prices, wages, daily output accept sign/size errors (class of F1-015 persists for the primary fields) |
| F3-09 | major | calc | Among eligible observations the price is chosen by recency/id, not by the applicable quantity tier: base and bulk prices captured the same day give a result that depends on the observation ids |
| F3-10 | major | calc | with_assumptions: an origin='assumed' factor or product is used but the run is not flagged has_assumptions and the line says origin 'observed' |
| F3-11 | major | calc | Strict mode reads the ASSUMED, unreviewed region hierarchy: wages of REG-MD-31084 are applied to LA County on the strength of an unverified parent link |
| F3-12 | major | calc | Equipment rate selection ignores rate_basis and capacity: a newer DOT/USACE ownership schedule silently replaces a rental-market rate (class of F1-007 for equipment) |
| F3-13 | major | validate/build | validate() (and therefore pipeline/scripts/build.py) crashes with KeyError('review_events') as soon as the review_events table has a row - i.e. on the second build after the first promotion |
| F3-14 | minor | calc/enums | A retail_promo-channel observation with promo_flag=False is used as an ordinary retail price |
| F3-15 | minor | validate | promote_validated gaps: rows of a flagged/rejected source or of a rejected product are promoted; raw file hash not required; unknown_needs_check sources pass |
| F3-16 | minor | calc | run_id depends on the physical row order of products/observations/coverage rows |
| F3-17 | minor | calc/validate | No duplicate-component guard: a second labor component for the same crew/productivity, or the same child twice in an assembly, doubles the cost silently |
| F3-18 | minor | ids/schema | Python and SQL spec_key normalisation still differ on padded numeric strings, NBSP and some Unicode |
| F3-19 | minor | calc | The engine depends on the ambient Decimal context (crashes below ~16 digits of precision) |
| F3-20 | minor | calc | RunParams edge cases: known_at accepts a datetime, annual_paid_hours/quantity accept Infinity (capped burdens become 0), region_id is not checked against regions |
| F3-21 | minor | validate | Validator cannot detect a fabricated 'complete' run (lines without inputs) and does not notice stored runs whose inputs were later flagged |
| F3-22 | minor | schema | Other mutable/unlogged state: categories (spec_key definition), regions (hierarchy), trades, equipment_types, assumption approval fields, notes and reviewed_by |
| F3-23 | minor | connectors/schema | Importer: price token check still weak; observation id uses the local offset string; no zip<->region cross-check; scale beyond the column accepted (12.98765 stored as 12.9877) |
| F3-24 | minor | calc | A productivity_condition factor scales labor hours but not equipment hours (hours x rate != unit cost) |
| F3-25 | minor | calc | Diagnostics hide why a candidate was unusable: an approved-but-invalid assumption is reported as plain WASTE_MISSING; CONSUMPTION_MISSING gives no per-row reasons |
| F3-26 | minor | docs/tests | STATUS.md overstates: '28 tables' (29 exist) and 'every CHECK, FK and protection trigger ... is exercised by tests/test_postgres.py' (14 schema mutants survive) |
| F3-27 | minor | calc | The engine raises tracebacks (not run statuses) on malformed in-memory rows: observed_at/effective_from None, shift_hours None, retrieved_at text, daily_output 0 |
| F3-28 | minor | calc | known_at semantics: UTC calendar date only; review decisions and definitions are not 'as of' |
| F3-29 | minor | calc | No flag when only one product contributes to a 'median' line or when products were dropped for unusable inputs |
| F3-30 | minor | calc | Line inputs for labor/burden/equipment rates omit the effective period (age of the rate is invisible on the run) |
| F3-31 | minor | build | build.py computes and writes runs and data even when validation reports errors (exit code 1 only) |
| F3-32 | minor | calc | With accept_retail_proxy=True a newer retail price overrides an older contractor quote of the same product (no channel ranking) |
| F3-33 | minor | build | build.py cannot supply annual_paid_hours (or classification, wage_class, known_at, accept_retail_proxy): strict runs with real, capped burdens can never complete |
| F3-34 | minor | connectors | OEWS parser has no industry/ownership/occupation-group handling: two rows for one (area, occupation) produce the same labor_rate_id with different wages |

### F3-01 (major) - Any session can defeat the database gates (validated-needs-fetch, restricted-source, spec/pack integrity, review log) with a TEMP table that shadows a bare table name

- **Area:** schema  **Verified by:** run
- **Where:** `schema/001_schema.sql:1176-1184 (ALTER FUNCTION ... SET search_path = costdb, pg_catalog); functions read bare names at 104-118, 121-133, 166-175, 224-239, 346-353, 445-454, 517-531, 87-100 (log_review_change INSERT INTO review_events), 991-1001`
- **What is wrong:** The F1 fix pins the functions' search_path to 'costdb, pg_catalog' and the comment says this prevents hijacking by a shadow table. It does not: PostgreSQL searches pg_temp FIRST for relations unless it is listed explicitly (last). A session (default PUBLIC TEMP privilege) that creates `temp table sources(source_id, reuse_status, verification_method)` makes check_source_usable read the temp table: a snippet-only source passes as 'fetched_primary', a prohibited source as 'open_license', and a `temp table review_events` swallows the review log (the real log gets no row). Verified: OBS-A1 validated from a never-fetched source, OBS-A2 inserted from a prohibited source, status change of OBS-A1 logged nowhere. No test shadows a table.
- **Reproduction:**

```
Control (rejected): insert validated observation from snippet-only source -> ERROR cannot be validated.
Attack (accepted): create temp table sources (source_id text, reuse_status text, verification_method text); insert into sources values ('SRC-XSNIP','open_license','fetched_primary'); insert the same validated observation -> INSERT 0 1.
Full script: cd /tmp/claude-0/f3/repro && bash repro_pg.sh   (section F3-01; needs PGHOST/PGPORT/PGUSER of a scratch server)
```

- **Suggested fix:** Pin as `SET search_path = pg_catalog, costdb, pg_temp` (pg_temp last) or schema-qualify every table reference inside the functions; REVOKE TEMP ON DATABASE from the application roles; add a PG test that creates a shadow temp table and expects the gate to still fire.

### F3-02 (major) - crews are outside the source gate and outside the validator's source checks: a crew can be 'validated' from a never-fetched or prohibited source

- **Area:** schema/validate  **Verified by:** run
- **Where:** `schema/001_schema.sql:1168-1171 (source_gate trigger list has no 'crews'); pipeline/costdb/validate.py:33 (SOURCE_TABLES), 160-198; calc.py:355-365 (_source_issue never looks at verification_method)`
- **What is wrong:** crews carry source_id/review_status and strict runs require a validated crew, but check_source_usable is not attached to crews and the validator's VALIDATED_FROM_SNIPPET / SRC_PROHIBITED_IN_USE loops skip them. The engine then trusts review_status alone. Verified in PostgreSQL: crew validated from a snippet-only source (insert accepted) and validate() returns no issue for a validated crew whose source is a prohibited snippet-only source.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && bash repro_pg.sh   (section F3-02)
python: db = S.priced_drywall_db(); S.add_source(db,'SRC-SNIPX',method='search_snippet_only',review='unreviewed',reuse='prohibited'); crew CRW-DRY-HANG.source_id='SRC-SNIPX'; validate(db, production=False) -> no issue for CRW-DRY-HANG
```

- **Suggested fix:** Add 'crews' to the DB gate list and to validator SOURCE_TABLES/OBSERVED handling; make the engine's _source_issue require verification_method in (fetched_primary, synthetic fixture when allowed) whenever min_review='validated'.

### F3-03 (major) - sources and indices are mutable and unlogged: one UPDATE of sources.verification_method (or indices.source_id / sources.reuse_status) opens every gate; fetched_primary requires no evidence

- **Area:** schema  **Verified by:** run
- **Where:** `schema/001_schema.sql:268-310 (sources: no append-only, no review log for verification_method/reuse_status), 915-932 (indices), 1150-1155 (log list covers review_status only), 104-133 (gates read the live row)`
- **What is wrong:** The validated-needs-fetch gate evaluates the CURRENT source row at write time of the dependent row. `update sources set verification_method='fetched_primary'` (no evidence_url/quote needed, nothing logged) lets observations be validated; resetting it afterwards leaves them validated with a snippet-only source. Likewise `update sources set reuse_status='open_license'` turns a prohibited source usable (verified: an observation was inserted from the prohibited source while it was flipped, then the flag was flipped back and the stored value stayed), and `update indices set source_id=<fetched source>` lets index_values be validated against a series that is later repointed back. Verified for all three.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && bash repro_pg.sh   (section F3-03); index variant: see pg_idx.sql in /tmp/claude-0/f3 (validated index value, then repoint indices.source_id)
```

- **Suggested fix:** Make sources/indices append-only (new row/version for a changed fetch status or terms) or log every change of verification_method/reuse_status/source_id in review_events; require evidence_url + evidence_quote (and a file hash) for fetched_primary; re-check dependants when a source is downgraded.

### F3-04 (major) - equipment_basis='rental_day' drops fuel silently (fuel_included=False and fuel_cost_hr known are ignored, no flag): F1-016(a) persists on the day-rate path

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:1183-1189 (day-rate branch returns before the fuel handling at 1190-1207)`
- **What is wrong:** For the same equipment_rates row (rental 25/h, day 150, fuel_included=False, fuel_cost_hr=9) the hourly basis gives 0.136 $/SF with FUEL_ADDED_SEPARATELY; the rental_day basis gives 0.075 with no fuel and no FUEL_* flag or gap.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-04)
```

- **Suggested fix:** Apply the same fuel logic (add fuel_cost_hr * hours, or gap FUEL_NOT_PRICED / flag FUEL_INCLUSION_UNKNOWN) on the day-rate path; add a test.

### F3-05 (major) - crew_members.labor_rate_id / equipment_rate_id ('pinned rate, overrides resolution' per the data dictionary) are never read by the engine

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:1223-1260 (rates resolved by trade/equipment type only); docs/data_dictionary.md:435-436; validate.py:339-345 does honour the pin for CREW_OPERATOR_DOUBLE`
- **What is wrong:** A crew member pinned to a $100/h rate while the automatic selection prefers a newer $40/h row is costed at $40; the pinned id does not even appear in the line inputs. The validator reasons about pinned equipment rates that the engine ignores.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-05: labor cost 0.55, 1.15 if the pin were honoured)
```

- **Suggested fix:** Implement the pin (and still apply usability/region/period checks to the pinned row) or remove the columns and the documentation.

### F3-06 (major) - Assembly excluded_scope lists tokens the assembly itself prices (the F1-024 'derive exclusions from children' rule is token-name based)

- **Area:** data  **Verified by:** run
- **Where:** `pipeline/scripts/gen_pilot_definitions.py:808-811 (carried = child exclusions whose token is not an included token); data/csv/assemblies.csv; validate.py:503-506 (ASM_CHILD_EXCLUSION_NOT_SURFACED requires the contradiction)`
- **What is wrong:** A child excludes what a sibling prices under another token name, and the generator surfaces it as an assembly exclusion. ASM-WALL-004 (included: board_material, primer_material, joint_compound_material ...) excludes gypsum_board, taping_and_finishing, primer, primer_and_paint, finish_coats, board_hanging; ASM-WALL-001..003 exclude board_hanging, finish_coats, primer, taping_and_finishing; ASM-CEIL-001 the same; ASM-HVAC-001 (prices condenser, furnace, coil, thermostat, 50 LF duct) excludes outdoor_unit, indoor_unit_and_coil, thermostat_and_controls, ductwork. A reader who trusts the exclusion list will add these items again (double count) or distrust the assembly. The validator rule enforces the contradictory behaviour and no rule compares meaning.
- **Reproduction:**

```
python: db=S.real_db(); a=[x for x in db['assemblies'] if x['assembly_id']=='ASM-WALL-004'][0]; set(a['excluded_scope']) & {'gypsum_board','taping_and_finishing','primer','finish_coats','board_hanging','primer_and_paint'}  -> all six present while the assembly's children price board hanging, finishing, priming and painting. (tdata3.py in /tmp/claude-0/f3)
```

- **Suggested fix:** Give each exclusion token a semantic key shared with the inclusion token that covers it (e.g. a scope-token map) and surface only exclusions not covered by a sibling; add a validator rule that fails when an excluded token maps to an included one.

### F3-07 (major) - A zero price is a valid, complete, strict input (material priced at $0, validator only warns)

- **Area:** calc/validate  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:545-642 (no price > 0 test); validate.py:250-251 (OBS_PRICE_ZERO is a warning); schema CHECK price_amount >= 0; importer accepts '0'`
- **What is wrong:** A validated observation with price_amount 0 gives a $0.00 board line and a complete strict run 0.559188 instead of 0.999188; nothing in the run says why. A zero price is almost always 'no price shown / free item', i.e. a missing number encoded as a value.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-07)
```

- **Suggested fix:** Exclude price_amount <= 0 in _best_observation (reason 'zero price'), make OBS_PRICE_ZERO an error, reject 0 in the importer and CHECK (price_amount > 0).

### F3-08 (major) - No range validation outside the database: component waste_factor, prices, wages, daily output accept sign/size errors (class of F1-015 persists for the primary fields)

- **Area:** calc/validate  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:733-741 (_waste: no range test on c['waste_factor']), 623-624 (price), 1315-1326 and 1483 (daily output), 1041-1075 (wages); pipeline/costdb/validate.py (no range rule); build.py never loads PostgreSQL`
- **What is wrong:** The CSV -> Python build path does not enforce the schema CHECKs: waste_factor 5 -> material cost 2.409188 (6x quantity), -0.5 -> 0.209188, negative wage -> 0.199188, negative daily output -> total -175.55, all 'complete' with an empty validator report. Only the PostgreSQL CHECKs reject them, and the pipeline's build never touches PostgreSQL.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-08)
```

- **Suggested fix:** Mirror the CHECK ranges in the engine (usability test: waste in [0,1), price >= 0 (> 0), wage >= 0, daily output > 0, quantities > 0, shift in (0,24]) and add a validator rule per CHECK; add a test that loads every fixture through both.

### F3-09 (major) - Among eligible observations the price is chosen by recency/id, not by the applicable quantity tier: base and bulk prices captured the same day give a result that depends on the observation ids

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:577-582 (tier eligibility), 638-642 (sort = region class, observed_at, retrieved_at, id)`
- **What is wrong:** Product with a $0.40/SF shelf price and a $0.30/SF price valid from 3200 SF (same day, same retrieved_at): at RunParams.quantity=5000 the engine returns 0.30 or 0.40 depending only on which observation_id sorts first. Even with different retrieved_at the newest capture wins, not the tier that applies.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-09: ids A1/B2 -> 0.40, B2/A1 -> 0.30)
```

- **Suggested fix:** Rank eligible candidates of the same store/day by tier applicability (largest qty_tier_min <= need), then recency; flag when several tiers were eligible.

### F3-10 (major) - with_assumptions: an origin='assumed' factor or product is used but the run is not flagged has_assumptions and the line says origin 'observed'

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:376 (_why_not lets origin=assumed rows through in with_assumptions), 1417-1426 and 1492-1494 (has_assumptions/origin_summary ignore factors and products), 884-886`
- **What is wrong:** Documented guarantee (methodology section 2): 'the run is flagged has_assumptions'. An assumed productivity_condition factor changes labor_cost 0.55 -> 0.66 with has_assumptions=False and labor line origin_summary='observed'; an assumed region factor/product gives 'mixed' or 'observed' and has_assumptions=False.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-10)
```

- **Suggested fix:** Include the origin of every factor and product (and region factor) in the line origin summary and in any_assumed.

### F3-11 (major) - Strict mode reads the ASSUMED, unreviewed region hierarchy: wages of REG-MD-31084 are applied to LA County on the strength of an unverified parent link

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:312-352 (_chain/_rank_up/_price_region_class take regions without any usability test); data/csv/regions.csv (REG-CA-037 origin=assumed, review_status=unreviewed, 'not yet checked against the official delineation file')`
- **What is wrong:** A hard rule says strict mode must not read assumptions. The ancestor relation REG-CA-037 -> REG-MD-31084 -> REG-MSA-31080 -> ... is stored as assumed/unreviewed and drives which wage/burden rows qualify; a strict run with a validated REG-MD-31084 wage completes (flagged RATE_FROM_ANCESTOR_REGION). The flag is visible, but the assumption is read silently. Worse, methodology section 1 promises that flagged/rejected records are never used 'in any table the engine reads': a region row with review_status='rejected' is followed just the same (verified: REG-CA-037 and REG-MD-31084 set to rejected, strict run still uses the REG-MD-31084 wage); the same holds for equipment_types (a rejected row still decides OPERATOR_NOT_PRICED; /tmp/claude-0/f3/t_new14.py).
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py   (section F3-11); rejected-region variant: /tmp/claude-0/f3/t_new11.py
```

- **Suggested fix:** Apply _why_not to every region on the chain in strict mode (stop the chain at an unreviewed/assumed link) or require review of the hierarchy before strict runs may use ancestors.

### F3-12 (major) - Equipment rate selection ignores rate_basis and capacity: a newer DOT/USACE ownership schedule silently replaces a rental-market rate (class of F1-007 for equipment)

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:1137-1171 (_equipment_rate scores rows by region rank and effective_from only; rate_basis, capacity_raw, make_model_raw never read); line input at 1181-1182 does not record rate_basis`
- **What is wrong:** Two usable rows for EQ-PTROWEL: rental_market 25/h (effective 2026-01-01) and dot_schedule 18/h (2026-06-01): the engine uses 18 (equipment 0.072 $/SF instead of 0.100) with no flag and without recording the basis; with equal effective dates it reports EQUIPMENT_RATE_AMBIGUOUS, so the choice is decided by an accident of dates. The pilot's own source plan (A2: DOT equipment schedules) will put both kinds of rows in the table. Rows for different capacities of one equipment type compete the same way.
- **Reproduction:**

```
python: /tmp/claude-0/f3/t_new10.py
```

- **Suggested fix:** Add RunParams.equipment_rate_basis (and a capacity selector) and filter on them; record rate_basis on the line input; ambiguity when several bases remain.

### F3-13 (major) - validate() (and therefore pipeline/scripts/build.py) crashes with KeyError('review_events') as soon as the review_events table has a row - i.e. on the second build after the first promotion

- **Area:** validate/build  **Verified by:** run
- **Where:** `pipeline/costdb/validate.py:78-91 (pk_of has no entry for review_events) used by check_foreign_keys at 146-153; pipeline/scripts/build.py:62-70 (validate runs on the loaded CSVs, review_events.csv is not reset)`
- **What is wrong:** promote_validated appends review_events rows and build.py writes them to data/csv/review_events.csv; the next build loads them and validate() raises. Verified end to end in a copy: populate one fetched source + product + observation (unreviewed) -> build #1 promotes both and exits 0; build #2 dies with KeyError: 'review_events'. No test loads a non-empty review_events table into validate(); the promotion path has never been run twice because nothing in the real data is promotable yet.
- **Reproduction:**

```
bash /tmp/claude-0/f3/repro/populate_and_build_twice.sh   (build #1 exit 0 with 2 promotions, build #2: KeyError: 'review_events', exit 1)
```

- **Suggested fix:** Add review_events (event_id or the natural key) to pk_of / skip the table in the duplicate-key loop; add a test that builds twice (or validates after promote_validated).

### F3-14 (minor) - A retail_promo-channel observation with promo_flag=False is used as an ordinary retail price

- **Area:** calc/enums  **Verified by:** run
- **Where:** `pipeline/costdb/enums.py:20 and calc.py:562-565 (effective_channels adds both retail channels; only promo_flag is tested); importer does not tie channel to promo_flag`
- **What is wrong:** Methodology: 'Promotional prices and MSRP are excluded by default.' accept_retail_proxy=True admits channel retail_promo; promo is excluded only via the separate promo_flag column, which the importer leaves False when blank.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-14] (complete, 0.40)
```

- **Suggested fix:** Treat channel retail_promo as promo (exclude unless explicitly requested) or enforce promo_flag=True for that channel (CHECK + importer).

### F3-15 (minor) - promote_validated gaps: rows of a flagged/rejected source or of a rejected product are promoted; raw file hash not required; unknown_needs_check sources pass

- **Area:** validate  **Verified by:** run
- **Where:** `pipeline/costdb/validate.py:606-635, 35-38 (EVIDENCE_FIELDS has no raw_file_sha256)`
- **What is wrong:** A 'validated' price is produced from a rejected source and a rejected product; methodology/test name 'with hash' but promotion requires only an evidence excerpt; records of a source whose reuse terms were never read (unknown_needs_check) are promoted.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-15] -> {'price_observations': 1}, raw_file_sha256 None
```

- **Suggested fix:** Check source.review_status and product status, require the hash where the table has one, and require a source whose terms are known for 'validated'.

### F3-16 (minor) - run_id depends on the physical row order of products/observations/coverage rows

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:870-885 (inputs/formula text follow table order), 1605-1609`
- **What is wrong:** Same data, tables listed in reverse order -> different run_id (and different formula text for a median line). After a PostgreSQL round trip without ORDER BY the 'same data reproduces the same id' promise fails.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-16] (False)
```

- **Suggested fix:** Sort candidates (and inputs) by a stable key before building lines/ids.

### F3-17 (minor) - No duplicate-component guard: a second labor component for the same crew/productivity, or the same child twice in an assembly, doubles the cost silently

- **Area:** calc/validate  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:1388-1395 and 1544-1555 (only identical cost_tags / scope tokens of DIFFERENT work items are detected); validate.py:402-410, 475-492`
- **What is wrong:** WI-DRY-001 with a copied labor component (cost_tags []) -> labor 1.10 instead of 0.55; ASM with TEST-WI-9 listed twice -> 13.998 instead of 7.998; validator silent. The real data is unaffected (generator tags labor/equipment components).
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-17]
```

- **Suggested fix:** Validator rule + engine failure for duplicate (crew, productivity_id) labor components in one work item and duplicate (work_item, version) in one assembly.

### F3-18 (minor) - Python and SQL spec_key normalisation still differ on padded numeric strings, NBSP and some Unicode

- **Area:** ids/schema  **Verified by:** run
- **Where:** `pipeline/costdb/ids.py:22-34 vs schema/001_schema.sql:214-222`
- **What is wrong:** ' 5.50' -> Python '5.5', SQL '5.50'; 'a\u00a0b' -> Python 'a b', SQL keeps NBSP; 'İ' lower() differs. A SQL-side key and a Python-side key for the same spec can differ (loud when a Python key is loaded, silent for SQL-only users). Equal on all 129 pilot specs.
- **Reproduction:**

```
bash /tmp/claude-0/f3/repro/norm_diff.sh <db with the costdb schema>   (prints py= / sql= for ' 5.50', NBSP, 'İ')
```

- **Suggested fix:** Strip before the numeric test in SQL (btrim first), normalise Unicode whitespace and case identically on both sides, and add the failing values to the equality test.

### F3-19 (minor) - The engine depends on the ambient Decimal context (crashes below ~16 digits of precision)

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:49-54 (quantize at 10 dp) and all Decimal arithmetic`
- **What is wrong:** decimal.getcontext().prec = 12 (a common 'money' setting in host applications) -> InvalidOperation in unit_cost; units.py was fixed to a local Context but calc.py was not.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-19]
```

- **Suggested fix:** Run calculations inside decimal.localcontext(Context(prec=40, rounding=ROUND_HALF_UP)).

### F3-20 (minor) - RunParams edge cases: known_at accepts a datetime, annual_paid_hours/quantity accept Infinity (capped burdens become 0), region_id is not checked against regions

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:126-159`
- **What is wrong:** known_at=datetime(...) passes (a datetime is a date) and later breaks comparisons; annual_paid_hours=Decimal('Infinity') gives min(cap, wages)/inf = 0 for UI/ETT/FUTA; a mistyped region_id yields an 'incomplete' run with misleading price reasons instead of a parameter error.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-20]
```

- **Suggested fix:** Reject datetimes and non-finite numbers, bound annual_paid_hours (e.g. <= 8784) and check region_id against the regions table in Engine.

### F3-21 (minor) - Validator cannot detect a fabricated 'complete' run (lines without inputs) and does not notice stored runs whose inputs were later flagged

- **Area:** validate  **Verified by:** run
- **Where:** `pipeline/costdb/validate.py:539-594 (CALC_INPUT_FLAGGED reads the status copied into the line input, not the current row; no rule requires inputs on cost lines; recomputation only with an engine)`
- **What is wrong:** A complete run with one invented line (formula 'invented', inputs []) and total 123.45 passes validate() without engine and is accepted by PostgreSQL; a stored strict run whose price observation was later flagged still validates clean and stays 'complete'.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-21]
```

- **Suggested fix:** Add CALC_LINE_NO_INPUTS (error) and re-check the CURRENT review_status/source of every input; mark runs stale when an input is flagged.

### F3-22 (minor) - Other mutable/unlogged state: categories (spec_key definition), regions (hierarchy), trades, equipment_types, assumption approval fields, notes and reviewed_by

- **Area:** schema  **Verified by:** run
- **Where:** `schema/001_schema.sql:183-263, 1036-1045 (assumptions: status/approved_by/approved_at/expires_on editable), 45-60 (notes/reviewed_by mutable)`
- **What is wrong:** update categories set required_product_attributes=...; update regions set parent_region_id=null; update indices set applies_to='all' all succeed unlogged. An approved assumption's approver/expiry can be rewritten (an expired assumption revived) with no history; reviewed_by of a validated row can be overwritten (verified: 'someone else', 0 review_events). 'A person other than the author' for definitions is not enforceable (no author column). review_events can be forged by a plain INSERT (verified: an event 'Alice (forged)' was accepted), so the log is append-only but not tamper-evident.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && bash repro_pg.sh   (section F3-22)
```

- **Suggested fix:** Protect and log these tables/columns like the others (or version them).

### F3-23 (minor) - Importer: price token check still weak; observation id uses the local offset string; no zip<->region cross-check; scale beyond the column accepted (12.98765 stored as 12.9877)

- **Area:** connectors/schema  **Verified by:** run
- **Where:** `pipeline/connectors/retail_capture_import.py:99-103 (price_tokens), 205-209 (oid), 168-172 (region_id from row beats zip_map), schema price_amount numeric(14,4)`
- **What is wrong:** price 5 with excerpt 'Item 5 of 10: $12.98' and price 8 for '... 4x8 sheet $12.98' are accepted; the same instant written with another UTC offset gets a different id and is imported twice (verified: 2 observations); the engine uses 12.98765 while PostgreSQL stores 12.9877 (recomputation from the database differs).
- **Reproduction:**

```
python: t031.py in /tmp/claude-0/f3 (cases 'price 5 vs unrelated token'); psql: see repro_pg.sh section F3-23
```

- **Suggested fix:** Require a currency-marked token near the price, normalise retrieved_at to UTC in the id, cross-check region_id against the zip map, reject scale beyond the column scale.

### F3-24 (minor) - A productivity_condition factor scales labor hours but not equipment hours (hours x rate != unit cost)

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:1485-1491`
- **What is wrong:** labor hours/unit 0.0096 with cost x1.2; equipment hours/unit stays 0.004 while the equipment cost is x1.2.
- **Reproduction:**

```
cd /tmp/claude-0/f3/repro && PYTHONDONTWRITEBYTECODE=1 python3 -B N_python.py  [section F3-24]
```

- **Suggested fix:** Scale equipment hours for productivity_condition factors too.

### F3-25 (minor) - Diagnostics hide why a candidate was unusable: an approved-but-invalid assumption is reported as plain WASTE_MISSING; CONSUMPTION_MISSING gives no per-row reasons

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:744 and 816-818`
- **What is wrong:** waste assumption 5 -> missing reason 'no waste/loss factor recorded'; coverage in LF on an SF item -> 'no usable product_consumption record for any usable product' (the unit reason is dropped).
- **Reproduction:**

```
python: /tmp/claude-0/f3/t_new9.py
```

- **Suggested fix:** Pass the _assumption_issue / Excluded reasons into the Missing reason, as PRICE_MISSING already does.

### F3-26 (minor) - STATUS.md overstates: '28 tables' (29 exist) and 'every CHECK, FK and protection trigger ... is exercised by tests/test_postgres.py' (14 schema mutants survive)

- **Area:** docs/tests  **Verified by:** run
- **Where:** `STATUS.md (Done and verified, first bullet); tests/test_postgres.py`
- **What is wrong:** See section 4: no PG test fails when the assembly_components, adjustment_factors, crew_members, calculation_runs/lines TRUNCATE, index_values source gate, unit base-dimension trigger, factor/index applies_to trigger, lr_stat_burden/lr_ovh_profit/cr_markup/cr_floor/wic_consumption/sources_validated_terms checks are removed.
- **Reproduction:**

```
psql: select count(*) from pg_tables where schemaname='costdb' -> 29; mutation logs: /tmp/claude-0/f3/mut/results_schema_all.json
```

- **Suggested fix:** Correct the text; add the missing tests.

### F3-27 (minor) - The engine raises tracebacks (not run statuses) on malformed in-memory rows: observed_at/effective_from None, shift_hours None, retrieved_at text, daily_output 0

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:557, 637, 1226, 1483, 987`
- **What is wrong:** TypeError / ValueError / decimal.InvalidOperation / DivisionByZero. PostgreSQL forbids these rows, but CSV-loaded data is not checked (F3-08).
- **Reproduction:**

```
python: /tmp/claude-0/f3/t_fuzz.py
```

- **Suggested fix:** Validate rows once on load (shared with F3-08) and fail with a data error naming the row.

### F3-28 (minor) - known_at semantics: UTC calendar date only; review decisions and definitions are not 'as of'

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:70-80, 391-396`
- **What is wrong:** A Pacific-time retrieval at 23:30 on 10-23 (= 10-24 UTC) is unknown to a run as_of 10-23; reviewed_at/review_status are read as of today, so re-running an old as_of uses today's review decisions without saying so.
- **Reproduction:**

```
python: /tmp/claude-0/f3/t040.py (third case)
```

- **Suggested fix:** Document or implement business-time-zone dates and a review-as-of rule (reviewed_at <= known_at).

### F3-29 (minor) - No flag when only one product contributes to a 'median' line or when products were dropped for unusable inputs

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:858-861 (MEDIAN flag only when len(cands) > 1); reasons for dropped products are discarded when the line resolves`
- **What is wrong:** Product B flagged/with bad coverage -> the line silently becomes product A alone (0.37 total instead of 0.445) with no flag.
- **Reproduction:**

```
python: /tmp/claude-0/f3/t001.py (flagged B case)
```

- **Suggested fix:** Flag SINGLE_PRODUCT_PRICE / PRODUCTS_EXCLUDED:<n> and list the exclusion reasons on the line.

### F3-30 (minor) - Line inputs for labor/burden/equipment rates omit the effective period (age of the rate is invisible on the run)

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:1041-1043, 951-952, 1181-1182`
- **What is wrong:** Observations record observed_at/retrieved_at/age_days; rate inputs record only id/region/classification. Without max_rate_age_days (default None) a very old rate is used with no age on the record.
- **Reproduction:**

```
python: /tmp/claude-0/f3/t_new9.py (prints the labor_rates input keys)
```

- **Suggested fix:** Record effective_from/effective_to/retrieved_at on rate inputs.

### F3-31 (minor) - build.py computes and writes runs and data even when validation reports errors (exit code 1 only)

- **Area:** build  **Verified by:** code reading
- **Where:** `pipeline/scripts/build.py:57-95`
- **What is wrong:** Runs are computed before validate(); CSV/JSON are written unconditionally; a validated-from-snippet row would already have produced a 'complete' run in data/csv/calculation_runs.csv before the error is reported.
- **Reproduction:**

```
code reading only (not run)
```

- **Suggested fix:** Validate first; refuse to write runs when error-level issues exist.

### F3-32 (minor) - With accept_retail_proxy=True a newer retail price overrides an older contractor quote of the same product (no channel ranking)

- **Area:** calc  **Verified by:** run
- **Where:** `pipeline/costdb/calc.py:638-642 (sort key has no channel term), 562-563`
- **What is wrong:** pro_account_quote 0.30 $/SF (Aug) vs retail_public 0.40 (Oct): the run uses 0.40 and records price_basis retail_proxy. Contractor cost data is discarded in favour of the proxy; the basis is flagged but the better datum is not preferred.
- **Reproduction:**

```
python: /tmp/claude-0/f3/t_new12.py
```

- **Suggested fix:** Rank channels (quote < public list < retail) before recency, or exclude retail when a usable quote exists.

### F3-33 (minor) - build.py cannot supply annual_paid_hours (or classification, wage_class, known_at, accept_retail_proxy): strict runs with real, capped burdens can never complete

- **Area:** build  **Verified by:** run + code reading
- **Where:** `pipeline/scripts/build.py:51-53 (the one RunParams used for all 25 + 10 runs)`
- **What is wrong:** The real burden rows already include capped items (Social Security 184,500; California ETT 7,000); calc.py raises ANNUAL_HOURS_MISSING for every trade unless RunParams.annual_paid_hours is set, and build.py has no way to set it. The first populated build will therefore report the same gap for every labor line however much data exists.
- **Reproduction:**

```
python: t009.py in /tmp/claude-0/f3 ('no annual hours -> ANNUAL_HOURS_MISSING'); code reading of build.py
```

- **Suggested fix:** Read run parameters (with stated bases) from a policy file or command line; record them on the run.

### F3-34 (minor) - OEWS parser has no industry/ownership/occupation-group handling: two rows for one (area, occupation) produce the same labor_rate_id with different wages

- **Area:** connectors  **Verified by:** run
- **Where:** `pipeline/connectors/oews_flatfile.py:80-110 (id = hash of source, region, trade, statistic, reference period)`
- **What is wrong:** A file that contains cross-industry and industry-specific rows (NAICS/I_GROUP/OWN_CODE columns, as the OEWS state/national files do) yields ids that collide (30.10 vs 45.55 for the same drywall installer mean); the collision is caught later by validate() (ID_DUPLICATE) only if nothing is silently dropped first, and the industry is not recorded on the row. The module header admits it is untested against a real file; the F1 test-gap note (duplicate rows, O_GROUP) still stands.
- **Reproduction:**

```
python: /tmp/claude-0/f3/t_oews.py
```

- **Suggested fix:** Filter on cross-industry/all-ownership/detailed rows explicitly (or put industry in the id and classification), fail on duplicate keys, and test with a realistic layout.

## 4. Test-suite assessment (mutation style)

Method: for each fix a one-line reversal was applied to a copy of the repository and the suite was run (/tmp/claude-0/f3/mut/mutate.py, mut_schema.py; logs run_all.log, results_schema_all.json). Python-side: 124 mutants of calc.py / validate.py / importer / enums / ids / units; schema-side: 50 mutants of schema/001_schema.sql run against tests/test_postgres.py.

**Killed:** 106 of 124 Python mutants (105 directly, IDS-NORM only when the PostgreSQL tests run) and 36 of 50 schema mutants (33 + 3 that were redundant or ill-formed on the first try: the two units-qualifier CHECKs back each other up, and my first timezone mutant kept the one-day slack; re-formulated they are killed). Almost every F1 fix has a pointed regression test that fails when it is reverted.

**Fixes or guards with NO failing test (the mutant survives):**

| fix / guard | F1 id | note |
|---|---|---|
| coats_in_rate divisor in the coverage formula (calc.py:703) | F1-001 | tests only use coats_in_rate=1; the engine is correct today (my t001c: 2 coats @175 SF/gal -> 0.005714) |
| best region class kept across products (calc.py:855-856) | F1-006 | no test mixes an exact-region product with an ancestor-region product |
| sub-region prices excluded by default (calc.py:595-598) | F1-006 | only the ancestor default is tested |
| CONDITION_FACTOR_AMBIGUOUS / duplicate-value check | F1-010 |  |
| missing-input list in the run_id fingerprint (calc.py:1607) | F1-013 | partly redundant: unresolved lines already carry the codes; retired vs not-yet-valid definitions (no lines) differ only by gaps |
| CREW_EQUIPMENT_NOT_COSTED warning (calc.py:1516) | F1-016 |  |
| index values published after known_at / vintage filter (calc.py:470) | F1-017/040 | the existing test is vacuous: at that as_of every other input (labor, crew) is also unknown, so the run is incomplete anyway |
| assumption approved after known_at | F1-040 |  |
| CALC_VERSION includes the code fingerprint (__init__.py) | F1-035 | no test that the version changes with the code |
| units.py must not change the global Decimal context | F1-039 |  |
| engine SHIFT_MISMATCH (norm shift vs crew shift) | - | methodology promises it; only CREW_MISMATCH is tested |
| currency != USD excluded | - |  |
| engine pack-mismatch exclusion (observation pack vs product pack) | F1-022 | database and validator are tested, the engine's own check is not |
| engine manual-capture-only exclusion | F1-004 | importer side is tested |
| observation dated after as_of excluded (calc.py:557) | - | a basic time-travel guard |
| pinned product spec_key vs component spec_key | - |  |
| (redundant) STRICT-ASSUMED-LEAK-guard, QTY-assumed-inline | - | equivalent or defence in depth; not counted as gaps |
| PG: assembly_components, adjustment_factors, crew_members append-only triggers | F1-021 | only work_items/assemblies/components/crews/products are exercised |
| PG: TRUNCATE guard on calculation_runs / calculation_run_lines | F1-003/032 |  |
| PG: index_values source gate (check_index_value_source, both rules) | F1-020 | the Python promotion test exists, the database gate is untested |
| PG: unit base-dimension constraint trigger | F1-032 |  |
| PG: af_index_integrity trigger (factor index applies_to) | F1-017/032 |  |
| validate() on a database whose review_events table is non-empty (build #2) | F1-025 | see F3-13: no test runs the promotion path twice |
| PG: lr_stat_burden_chk, lr_ovh_profit_chk, cr_markup_chk, cr_floor_chk, sources_validated_terms_chk, wic_consumption_chk | F1-018/019/032/037 | CHECKs that can be dropped without any test noticing |

Other test observations: STATUS.md says every protection trigger is exercised by the PostgreSQL tests - the table above shows it is not (F3-26). Several data gates (test_validated_means_fetched_primary_with_hash, test_no_numbers_were_invented_for_missing_inputs) still pass vacuously on empty tables; the PostgreSQL tests now fail instead of skip when no server exists (F1-042 fixed in that respect); the independent arithmetic test now covers about 30 quantities and uses its own fence-post counting (I re-derived 23 with Fractions: all match).

## 5. What I could not verify

- External facts (wages, FICA/UI/ETT rates, SOC/FIPS/CBSA codes, reuse terms of the 92 sources): no network access and no primary document is in the repository; I only checked internal consistency.
- PostgreSQL versions other than 16.15, roles/privileges/RLS/Supabase exposure. The schema defines no roles; the table owner or a superuser can disable every trigger (`set session_replication_role = replica` made an append-only UPDATE succeed in my scratch server) - protections are against mistakes, not against the owner.
- Locale-dependent `lower()` in compute_spec_key on locales other than C.UTF-8.
- Importer id collisions of different content (code read, not provoked); the BLS and PDF connectors (not run) and the OEWS parser (only on a two-row fixture, t_oews.py); concurrency and performance.
- Mutation analysis uses one-line reversals; an equivalent mutant can hide a real gap and a surviving mutant can be redundant (I re-checked three).
- F3-31 (build.py ordering) is from code reading only.
- Housekeeping: a scratch PostgreSQL cluster was run from /var/tmp/f3_pg (the postgres OS user cannot traverse /tmp/claude-0, whose mode became 0700); it is stopped and deleted at the end of the review. The repository under /home/user/owl-tower-os-app was not modified (git status clean).

## 6. Files

- /tmp/claude-0/f3/F3_report.md (this file), /tmp/claude-0/f3/F3_findings.json
- /tmp/claude-0/f3/t0*.py, t_*.py, pg0*.sql: F1 re-checks; /tmp/claude-0/f3/repro/N_python.py, repro_pg.sh, norm_diff.sh: reproductions of the new defects; /tmp/claude-0/f3/mut/: mutation harness and logs.

---

# Resolution (author's response, added after the review)

Status after the remediation round that followed F3. Regression tests: `tests/test_f3_fixes.py` (TF), `test_postgres.py` (PG), `test_validate.py`, `test_connectors.py`, `test_build.py`. **The new code has not yet been re-reviewed by a person other than the author** (see the end of this section).

| id | status | what was done | test |
|---|---|---|---|
| F3-01 | fixed | function `search_path` is `pg_catalog, costdb, pg_temp` (temp schema last) | PG a_temp_table_cannot_shadow… (source gate and review log) |
| F3-02 | fixed | `crews` behind the database source gate and in the validator's source checks (also `adjustment_factors`); the engine itself requires a *fetched* source whenever the review floor is `validated` | PG crews_are_behind…, TF F302… |
| F3-03 | fixed against mistakes | `fetched_primary` needs `evidence_url` + `evidence_quote` (CHECK); a source cannot be downgraded/restricted while dependants rest on it; index series are frozen; every UPDATE/DELETE of sources, regions, categories, trades, equipment types and assumption approvals is written to the append-only `change_log` (old + new row); a changed reviewer is logged even with an unchanged status. **Residual:** the table owner/superuser can disable triggers (`session_replication_role = replica`) and can insert forged log rows: the protections guard against mistakes and make tampering visible, not impossible | PG sources_cannot_be_flipped…, index_series_are_frozen…, a_changed_reviewer…, assumption_approvals… |
| F3-04 | fixed | the fuel rule is shared by the hourly and the day-rate path | TF F304 (2) |
| F3-05 | fixed | `crew_members.labor_rate_id` / `equipment_rate_id` are honoured; a pinned row still has to be usable, in period and in region and is never replaced by an automatic pick (`*_PIN_UNUSABLE` / `*_PIN_UNKNOWN`); recorded on the line input | TF F305 (3) |
| F3-06 | fixed | `costdb/scope.py` maps an exclusion to the inclusion tokens that price it (e.g. `gypsum_board` ← `board_material`); the generator surfaces only exclusions no sibling covers and the validator fails an assembly that excludes what its children price (`ASM_SCOPE_CONTRADICTION`) | test_validate, test_data_gates |
| F3-07 | fixed | price > 0 in the schema CHECK, the engine, the importer; `OBS_PRICE_ZERO` is an error | TF F307F308, PG, test_connectors |
| F3-08 | fixed | the schema CHECK ranges are mirrored in the engine (`calc.RANGES`: prices, wages, burdens, equipment rates, norms, crews, members, factors, index values, coverage, waste) and in the validator (`RANGE_VIOLATION`) | TF F307F308 (3), test_validate |
| F3-09 | fixed | candidates rank by region class → channel → applicable tier → recency → id; `SEVERAL_PRICE_TIERS_ELIGIBLE` is flagged | TF F309 |
| F3-10 | fixed | assumed factors, region factors and products set `has_assumptions`, the line origin and a flag | TF F310 (2) |
| F3-11 | fixed | a region's parent link is followed only from a usable region row (strict mode never follows the unreviewed/assumed hierarchy; a rejected row cuts the chain); the state for payroll items must come from a usable row (`REGION_STATE_UNKNOWN`, never silently "no extra items"); flagged/rejected trades and equipment types are refused. **Consequence:** until the region table is reviewed against the official delineation, strict runs cannot use ancestor-region wages — listed in the backlog | TF F311 (6) |
| F3-12 | fixed | rows of different `rate_basis`/capacity are ambiguous unless `equipment_rate_basis` / `equipment_capacity` name one; basis recorded on the line | TF F312 (3) |
| F3-13 | fixed | event tables get a natural key in `pk_of`; `build` validates first, promotes, then computes | test_build (promotion then second build; byte-identical rebuild) |
| F3-14 | fixed | channel `retail_promo` is a promotion (engine, CHECK `po_promo_chk`, importer, validator) | TF F314, PG, test_connectors |
| F3-15 | fixed | promotion also needs a source that is not flagged/rejected and whose terms were read (`unknown_needs_check` is not enough), a usable product, and the file hash for dataset/document tables. A hand-captured retail price has no file to hash: excerpt + url + captured_by are its evidence (methodology wording corrected) | test_validate PromotionGaps |
| F3-16 | fixed | every grouped index is sorted by primary key; the run id ignores row order | TF F316 |
| F3-17 | fixed | duplicate labor/equipment components and duplicate children are `failed` in the engine and errors in the validator | TF F317 (2), test_validate |
| F3-18 | fixed | attribute text must be ASCII (anything else is refused on both sides); trimming, whitespace and lower-casing use one explicit rule in Python and SQL (`translate`, not locale `lower()`); padded numbers normalise alike | PG spec_key_function… (edge values) |
| F3-19 | fixed | public engine entry points run in their own Decimal context | TF F319 |
| F3-20 | fixed | `known_at` rejects datetimes; non-finite numbers and more than 8784 paid hours are refused; an unknown region or index is a parameter error | TF F319F320 |
| F3-21 | fixed | `CALC_LINE_NO_INPUTS`; `CALC_INPUT_NOW_UNUSABLE` marks a complete run stale when an input has since been flagged/rejected or its source restricted | test_validate |
| F3-22 | fixed | see F3-03 (change log); `reviewed_by` changes are logged. No author column exists, so "a person other than the author" for definitions is a process rule, not a database rule | PG |
| F3-23 | fixed | `$`-marked amounts are the prices when present; id from the UTC instant; zip ↔ region cross-check; scale beyond the column refused | test_connectors |
| F3-24 | fixed | a productivity condition scales equipment hours as it scales labor hours | TF F312 |
| F3-25 | fixed | unusable assumptions and unusable coverage rows state why in the missing-input reason | TF F325F327 |
| F3-26 | fixed | README/STATUS corrected (30 tables; claims limited to what the tests exercise); tests added for the schema mutants that survived | PG (9 new) |
| F3-27 | fixed | malformed in-memory rows become a `DATA_ERROR` of that component (run `failed`), not a traceback | TF F325F327 |
| F3-28 | partly | a review decision recorded after `known_at` is treated as not yet made (rows and definitions); dates remain UTC calendar dates — documented, no business-time-zone logic | TF F328 (2) |
| F3-29 | fixed | `SINGLE_PRODUCT_PRICE`, `PRODUCTS_EXCLUDED:<n>` | TF F314F32 |
| F3-30 | fixed | labor, burden and equipment inputs carry effective_from/to and retrieval time | TF F325F327 |
| F3-31 | fixed | the build validates the data first and refuses to compute or write on error-level issues, and again after the runs | test_build |
| F3-32 | fixed | quote channels rank before lists before retail at equal region class | TF F314F32 |
| F3-33 | fixed | `data/run_policy.json` supplies the run parameters (e.g. `annual_paid_hours`), each result-affecting one with its stated basis, stored in every run | test_build |
| F3-34 | fixed | industry/ownership/occupation-group rows are filtered when the layout columns exist; conflicting duplicates stop the import | test_connectors |

**F1 findings the reviewer rated PARTIALLY FIXED** — F1-002, 004, 020 (closed by F3-01/02/03/11), 015 (F3-08), 016 (F3-04), 024 (F3-06), 032 (new CHECK `lr_total_chk`; `notes` stays mutable by design), 042 (tests for the surviving mutants added). **Still open:** F1-023 (an assembly's *descriptive* text, e.g. `spec_attributes.board`, is free text and is not machine-compared with its children; only the `work_items` list is), F1-027 (the `qty_origin` of the 50 LF duct parameter stays `derived`; the schema has no value for "specified"), F1-028 (connector/paint required attributes cannot be tightened without inventing the company's spec), F1-033 (the convenience view still mixes channels), F1-034 (`15/32` and `0.46875` remain different keys; false negatives only).

**Verification of this round.** The author re-ran the reviewer's mutation harness against the fixed code (result below) — that measures the tests, it is not an independent review of the new code.

**Mutation re-run (author, scratch harness, PostgreSQL tests off for speed).** Counting a mutant as killed only when a test other than the harness-specific `test_the_calc_version_changes_with_the_code` fails (the harness pins `CALC_VERSION`, so that one test fails in every mutant):

| round | mutants | killed at once | survivors → action |
|---|---|---|---|
| reviewer's list re-run on the fixed code | 124 | 101 | 18 patterns no longer exist (the code they mutated was rewritten; re-created as round 2); 5 survived: `F035` (the calc-version fingerprint — it is the pinned value in the harness itself; its test passes on the real code), `F040a` (`known_at` row filter — the existing test had become vacuous because review is now as-of too), `F001c`, `STRICT-ASSUMED-LEAK-guard`, `QTY-assumed-inline` (defence-in-depth guards pre-empted by other checks). Tests added for the last four; all four now killed |
| round 2: current text of the 18 lost patterns + new F3 features (pins, channel/tier ranking, usability of index values, region/definition review as-of, crew checks, importer id) | 42 | 33 | 9 survived (`index value usability`, `vintage_date alone`, `wage statistic`, `crew without labor`, `origin=missing`, importer observation id × 2, pinned apprentice / overtime row × 2) → one test each in `tests/test_f3_fixes.py::MutantSurvivorsRound2` / `test_connectors.py`; all nine now killed |

Remaining limitation of this check: it measures the tests of the code the author wrote; the F3 fixes have **not** had an independent code review of their own. Whole suite after this round: 309 tests, all passing (30 against a real PostgreSQL).
