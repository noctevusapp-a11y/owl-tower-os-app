# STATUS — checkpoint and continuation point

Last build: **2026-10-24**. Machine-readable counts: `data/json/pilot_status.json`.

## Done and verified (by tests / independent review)

* Schema (28 tables) loads on PostgreSQL 16; every CHECK, FK and append-only trigger is exercised by `tests/test_postgres.py`.
* Exact unit system; `spec_key` equivalence; calculation engine (unit cost, assembly, loaded labor, markup vs margin, index/region/condition adjustments, strict vs assumption mode, deterministic run ids) — hand-computed expectations in `tests/test_calc.py`.
* Independent validator — each rule has a negative test (`tests/test_validate.py`); promotion gate refuses snippet-level evidence.
* Importers/parsers on **format fixtures** (retail capture, BLS API, OEWS table, PDF tables with page-image QA).
* Source register: 92 sources with owner, URL, data, geography, period, access, terms, limits, update frequency, reachability.
* 129 material spec lines, 25 work items (geometry-derived quantities with stored formulas), 10 assemblies.

## Collected from real sources

Almost nothing, by necessity: the build environment blocked every primary host. Imported (all `unreviewed`, search-summary evidence): 1 BLS OOH national carpenter median, 2 FICA items (IRS Pub. 15, 2026), 1 California ETT item, 4 index series *identifiers*. See `data/evidence_digest.csv` for the decision on each of the 87 numeric data points seen.

## Not done / missing

* All prices, waste factors, crew compositions, labor norms, equipment rates, manufacturer coverage → `docs/data_gaps_backlog.md`.
* DIR / SAM / Caltrans / USACE document extraction (formats unseen; see `pipeline/connectors/README.md`).
* Review of live retailer terms by a person.

## How to continue (in order)

1. Open network access (`docs/network_allowlist.md`) or run the connectors on an office machine. Register a free BLS API key (`BLS_API_KEY`).
2. Pull OEWS (May 2025) → `labor_rates`; payroll items (IRS/EDD) → `burden_rates`; PPI/ECI values from bls.gov → `index_values`. Mark each source `fetched_primary` and store file SHA-256s.
3. Capture material prices by hand for the 43 priority-1 spec lines (`templates/price_capture_template.csv`), then the other 86; add supplier quotes where the company has accounts.
4. Extract labor norms and crew compositions from NAVFAC P-405 / TM 3-34.41 / DOT guides with page images checked (`connectors/pdf_tables.py`); extract manufacturer coverage into `product_consumption`.
5. Provide company-specific burden items (workers' comp class rates, experience mod, UI rate, benefits).
6. `python3 -I pipeline/scripts/build.py` → review `docs/validation_report.md`, `docs/coverage_matrix.md`; promote only fetched-source records.
7. Resume at the first `incomplete` run in `data/csv/calculation_runs.csv`; its `missing_inputs` is the to-do list.

## Known open points

* Independent reviews: `docs/independent_review_F1.md` (code/arithmetic/definitions) and `docs/independent_review_F2.md` (source claims). Findings that were fixed are listed in the reviews' "resolution" sections; unresolved ones are in `docs/data_gaps_backlog.md` or noted below.
* The repository push from the cloud session was refused (GitHub App not installed for the organization); the work is committed locally on branch `claude/construction-cost-database-sv4dab`.
