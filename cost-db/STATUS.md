# STATUS — checkpoint and continuation point

Last build: **2026-10-24**. Machine-readable counts: `data/json/pilot_status.json`.

## Done and verified (by tests / independent review)

* Schema (30 tables) loads on PostgreSQL 16; every CHECK, FK and protection trigger (append-only history incl. calculation runs, products and versioned definitions, TRUNCATE guards, review log, validated-needs-reviewer, source gates, spec-key/pack integrity, NULL-safe unit qualifiers) is exercised by `tests/test_postgres.py` against a real server (started by the test harness).
* Exact unit system; `spec_key` equivalence (Python and SQL agree on every pilot spec line); calculation engine **rewritten after independent review F1** (one usability test for every record, per-product coverage pairing, region-ranked price selection, labor/burden/equipment selection rules, assumption rules, definition gating, full-input run ids) — hand-computed expectations in `tests/test_calc.py`, regression counter-examples in `tests/test_review_fixes.py` (F1) and `tests/test_f3_fixes.py` (F3: pinned rates, day-rate fuel, range checks, channel/tier ranking, region-chain usability, equipment basis, as-of review). 309 tests pass (30 against a real PostgreSQL); a mutation analysis of the tests was run twice and every surviving mutant got a test.
* Independent validator — each rule has a negative test (`tests/test_validate.py`); promotion gate refuses snippet-level evidence, restricted sources and rows without evidence, and logs every promotion in `review_events`.
* Importers/parsers on **format fixtures** (retail capture, BLS API, OEWS table, PDF tables with page-image QA).
* Source register: 92 sources with owner, URL, data, geography, period, access, terms, limits, update frequency, reachability.
* 129 material spec lines (44 needed by a pilot work item), 25 work items (geometry-derived quantities with stored formulas, re-derived independently in `tests/test_data_gates.py`), 10 assemblies with inclusions/exclusions derived from their children.

## Collected from real sources

Almost nothing, by necessity: the build environment blocked every primary host. Imported (all `unreviewed`, search-summary evidence): 1 BLS OOH national carpenter median, 2 FICA items (IRS Pub. 15, 2026), 1 California ETT item, 4 index series *identifiers*. See `data/evidence_digest.csv` for the decision on each of the 87 numeric data points seen.

## Not done / missing

* All prices, waste factors, crew compositions, labor norms, equipment rates, manufacturer coverage → `docs/data_gaps_backlog.md`.
* DIR / SAM / Caltrans / USACE document extraction (formats unseen; see `pipeline/connectors/README.md`).
* Review of live retailer terms by a person.
* **A person must review the `regions` table** (parents, state codes): it is `assumed/unreviewed`, so strict runs cannot use ancestor-region rates and cannot choose state payroll items until it is reviewed (backlog A8).
* **A person other than the author must review the 25 work-item and 10 assembly definitions** (scope, specification, quantities, exclusions) and record it; until then every strict run reports `DEFINITION_NOT_REVIEWED`.
* The engine has never run on a real populated price set (none exists yet); first real captures will exercise paths that only synthetic data has covered.

## How to continue (in order)

1. Open network access (`docs/network_allowlist.md`) or run the connectors on an office machine. Register a free BLS API key (`BLS_API_KEY`).
2. Pull OEWS (May 2025) → `labor_rates`; payroll items (IRS/EDD) → `burden_rates`; PPI/ECI values from bls.gov → `index_values`. Mark each source `fetched_primary` and store file SHA-256s.
3. Capture material prices by hand for the 44 priority-1 spec lines (`templates/price_capture_template.csv`), then the other 86; add supplier quotes where the company has accounts.
4. Extract labor norms and crew compositions from NAVFAC P-405 / TM 3-34.41 / DOT guides with page images checked (`connectors/pdf_tables.py`); extract manufacturer coverage into `product_consumption`.
5. Provide company-specific burden items (workers' comp class rates, experience mod, UI rate, benefits).
6. `python3 -I pipeline/scripts/build.py` → review `docs/validation_report.md`, `docs/coverage_matrix.md`; promote only fetched-source records.
7. Resume at the first `incomplete` run in `data/csv/calculation_runs.csv`; its `missing_inputs` is the to-do list.

## Known open points

* Independent reviews: `docs/independent_review_F1.md` (code/arithmetic/definitions; resolution section at the end), `docs/independent_review_F2.md` (source claims), `docs/independent_review_F3.md` (re-check of the fixes). Unresolved findings are listed in their resolution sections and in `docs/data_gaps_backlog.md`.
* The F3 fixes were checked by the author's tests and mutation re-run only — no second independent code review of them exists. Residual F3 limits: a database owner/superuser can still disable triggers (F3-03; protection is against ordinary roles and mistakes), and `known_at` is a UTC calendar date (F3-28).
* `index_values` allows one vintage per series, period and day; a second revision on the same day needs a different `vintage_date` (documented limitation).
* The repository push from the cloud session was refused (GitHub App not installed for the organization); the work is committed locally on branch `claude/construction-cost-database-sv4dab`.
