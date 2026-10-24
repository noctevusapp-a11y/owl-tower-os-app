# Validation report (automated)

Build timestamp: `2026-10-24T00:00:00+00:00`.

## What was checked

Rules in `pipeline/costdb/validate.py`: foreign keys and duplicate ids; source terms and verification status; product spec completeness and `spec_key` consistency; pack/unit/date/duplicate/outlier checks on price observations; labor layering (statistical vs prevailing vs loaded, double-counted fringe/payroll/workers' comp, public-works scope); crew operator double counting and equipment fuel; productivity reconciliation (reported vs crew×shift/output); work-item scope tokens and cost tags; work-item components against the specification the work item states; assembly inclusions/exclusions derived from the children, assembly specification against its component rows, scope overlap and unit consistency; assumptions (four eyes, expiry, uniqueness); validated records without a reviewer; stored calculation runs (inputs exist, no flagged inputs, strict runs without assumptions, retail basis only with opt-in, **re-computation reproduces stored totals**). Screening thresholds are a documented policy (`validate.DEFAULT_POLICY`), each with its basis.

## Result on the real data

- issues: **0** (errors 0, warnings 0, info 0)

**Reading this result:** zero issues means the data that exists is internally consistent — it does **not** mean the database is complete or verified. There are no price observations, equipment rates or productivity norms to check yet, and no source was fetched.

## Records by review status

| table | validated | unreviewed | flagged | rejected |
|---|---|---|---|---|
| price_observations | 0 | 0 | 0 | 0 |
| labor_rates | 0 | 1 | 0 | 0 |
| equipment_rates | 0 | 0 | 0 | 0 |
| productivity_observations | 0 | 25 | 0 | 0 |
| burden_rates | 0 | 3 | 0 | 0 |
| index_values | 0 | 0 | 0 | 0 |
| product_consumption | 0 | 0 | 0 | 0 |
| bid_benchmarks | 0 | 0 | 0 | 0 |
| products | 0 | 0 | 0 | 0 |

Validated records in total: **0**. Sources fetched from a primary host: **0** of 92 (the rest are search-snippet level). The promotion gate refuses to validate anything whose source was not fetched.

## Automated test suite

`python3 tests/run_tests.py` → **Ran 309 tests in 21.261s, ALL PASSED**   
(The PostgreSQL tests start their own throw-away cluster; `PGHOST`/`PGPORT`/`PGUSER` select an existing scratch server; `COSTDB_SKIP_PG=1` skips them knowingly.)

Tests cover: exact unit conversions; spec-key equivalence; hand-computed unit cost, labor, markup/margin, index and region adjustments; strict vs assumption modes; missing-input reporting; operator and benefit double counting; prevailing-wage refusal for private projects; assembly aggregation and scope overlap; every validator rule firing on broken data; promotion gate; retail-capture importer; BLS/OEWS/PDF parsers on format fixtures; PostgreSQL constraints, append-only triggers and CSV import; data gates on the real files. Synthetic fixtures live only in `tests/` and are rejected from `data/`.
