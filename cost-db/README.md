# Owl Tower Cost Database — independent construction cost database (pilot)

An independent, source-traceable cost database for Owl Tower Construction Group, functionally comparable to a unit-cost book (materials, labor, equipment, unit costs, assemblies, regional/time adjustments) — built from free public sources. **It is a pilot infrastructure, not a replacement for RSMeans.** It does not copy RSMeans or any proprietary classification.

> **Кратко по-русски.** Это рабочая основа независимой базы затрат: схема PostgreSQL/Supabase, движок расчётов, валидатор, импортёры и реестр из 92 источников. **Реальных цен, норм труда и ставок для Лос-Анджелеса в базе пока нет**: среда, где сделан пилот, не пропускала ни одного первичного источника (BLS, DIR, SAM.gov, Caltrans, Home Depot и т. д.), а выдумывать числа запрещено. Поэтому все 35 расчётов (25 операций и 10 сборок) честно получают статус `incomplete` и перечень недостающего; проверенных (`validated`) записей — 0. Что нужно сделать, чтобы данные пошли, — в `docs/network_allowlist.md` и `docs/data_gaps_backlog.md`.

## Current state (build of 2026-10-24) — read this first

| | count | note |
|---|---|---|
| sources in the register | 92 | all at **search-summary level**; 0 fetched from a primary host (network policy) |
| unique products / price observations | **0 / 0** | no retailer price was captured: the compliant route is manual capture or a licensed feed |
| material spec lines to collect (targets) | 129 | 44 are needed by a pilot work item |
| work items (unit-cost operations) defined | 25 | framing 6 · drywall 6 · insulation 1 · concrete 5 · painting 4 · HVAC 3 |
| assemblies defined | 10 | walls, ceiling, slabs, footing, HVAC package — each with a measurable spec |
| labor / burden / equipment / norms observed | 1 / 3 / 0 / 0 | one national BLS median (carpenter), FICA ×2, CA ETT — all `unreviewed`, search-snippet evidence |
| calculation runs (strict, LA County) | 35 | **0 complete · 35 incomplete · 0 failed** — each lists exactly what is missing (prices, waste, crews, norms, coverage, and that the work-item definitions still await a human review) |
| records `validated` | **0** | the promotion gate refuses anything whose source was not fetched |
| automated tests | 309 (30 run against a real PostgreSQL that the test harness starts itself) | pass; see `docs/validation_report.md`. Includes a regression test per defect of the independent reviews F1 and F3 and tests added for every mutant that survived the mutation analysis |

The database **does not contain a single estimated or remembered market number.** Where a value is needed and not found it is `origin = missing` and calculations stop with a precise missing-input list.

## Boundaries of applicability

* **Geography:** Los Angeles County / Southern California first; regions for AZ, NV and other states are modelled (`regions`), but there is no data for them.
* **Scope:** pilot categories only — framing, drywall, insulation, concrete, reinforcement, painting, HVAC. Demolition, roofing, waterproofing, doors/windows, finishes, flooring, plumbing and electrical have category codes but no work items, products or rates.
* **What a unit cost means here:** direct cost per unit of a precisely specified operation under normal-access, unoccupied, new-work conditions. Corners, openings, laps, blocking, mobilization, cleanup, supervision, tax, delivery, permits, overhead and profit are **explicitly excluded** from each work item and must be added separately.
* **Prices:** retail prices are not contractor purchase prices: they are **off unless a run asks for them** (`accept_retail_proxy=True`), and such a run records `price_basis = retail_proxy`. Bid prices are benchmarks only. Index values adjust old prices; they are not prices.
* **Labor:** statistical wages exclude employer-paid benefits and need burden items; prevailing/federal wages are for public works only; all rates are per paid hour.
* **Not legal, engineering or code advice.** Specs (fastener spacing, nailing, slab reinforcement ...) are scope definitions for costing; the engineer/estimator must confirm them against project requirements and the governing code.
* **Not a RSMeans replacement:** no thousands of items, no regional city index tables, no historical series. It is the method plus a first, empty-by-honesty slice.

## What is in this directory

| path | content |
|---|---|
| `schema/001_schema.sql` | PostgreSQL 14+/Supabase schema, schema `costdb`: 30 tables, constraints, append-only triggers, views |
| `schema/003_comments.sql` | `COMMENT ON` for every table and column (generated) · `002` is intentionally absent: reference rows are imported from `data/csv` |
| `data/csv/*.csv` | one CSV per table, ready for `\copy` (load order: `costdb/pg.py`); empty tables carry headers only |
| `data/json/costdb.json` | the same data as one JSON; `source_register.json`, `pilot_status.json` |
| `data/source_register.csv` · `docs/source_register.md` | source register (owner, URL, data, geography, period, access, terms, limits, update frequency, verification, reachability) |
| `data/evidence_digest.csv` | every numeric data point the research agents saw, with the import decision and reason |
| `data/raw_agent_returns/` | raw returns of the research and review agents + host reachability test |
| `docs/data_dictionary.md` | every column of every table (generated from one dictionary) |
| `docs/methodology.md` | formulas, layers, statuses, double-counting rules, limitations |
| `docs/validation_report.md` | automated validation + test results · `independent_review_F1.md` (code/arithmetic/schema, 42 findings), `independent_review_F2.md` (source claims), `independent_review_F3.md` (re-check of the F1 fixes, 34 further findings, with the resolution table and the mutation re-run) |
| `docs/coverage_matrix.md` | categories × regions × cost components |
| `docs/data_gaps_backlog.md` | what is missing, how to fill it, what blocks it |
| `docs/network_allowlist.md` | hosts to open, in order of value |
| `docs/update_recommendations.md` | refresh cadence per data type |
| `examples/worked_examples.md` | reproducible unit-cost / labor / markup / index / assembly examples (**synthetic inputs, clearly marked**) and the real-data refusal |
| `templates/price_capture_template.csv` | header of the manual price-capture sheet |
| `pipeline/` | `costdb/` (engine, validator, units, store), `connectors/`, `scripts/` |
| `tests/` | 309 tests; synthetic fixtures live only here; `test_review_fixes.py` holds the counter-example of every engine defect found by review F1, `test_f3_fixes.py` those of review F3 and the mutation survivors |

## How to use

```bash
# rebuild everything derived (validation, strict calculations, CSV/JSON, reports)
python3 -I pipeline/scripts/build.py

# run the tests (the PostgreSQL tests start a throw-away cluster themselves; PGHOST/PGPORT/PGUSER select an existing scratch server;
# they FAIL, not skip, when no PostgreSQL can be obtained - COSTDB_SKIP_PG=1 skips them knowingly)
python3 tests/run_tests.py

# load into PostgreSQL / Supabase
psql -f schema/001_schema.sql  &&  psql -f schema/003_comments.sql
python3 -I pipeline/scripts/pg_import_check.py <database>      # loads data/csv with \copy in dependency order

# capture prices by hand, then validate/normalise them
cp templates/price_capture_template.csv my_capture.csv         # fill one row per listing seen
python3 -I pipeline/connectors/retail_capture_import.py my_capture.csv --write
python3 -I pipeline/scripts/build.py
```

Generators that rebuild the inputs: `gen_reference.py` (units, regions, categories, trades, equipment types), `ingest_agent_returns.py` (source register + the few imported data rows), `gen_pilot_definitions.py` (spec lines, work items, assemblies), `build_docs.py`, `build_register_md.py`.

Supabase notes: tables live in schema `costdb` (add it to *Exposed schemas* for the API); enable row-level security according to your policy — none is configured here.

## The design in five lines

1. `origin` (observed / derived / assumed / missing) and `review_status` (unreviewed / validated / flagged / rejected) are separate on every record; only validated, observed/derived data feed strict calculations.
2. History is append-only (database triggers); a new observation never overwrites an old one.
3. Materials are equivalent only if every category-required attribute matches (`spec_key`); packs, units and prices are normalised with exact conversions; `TON` and `GAL` are always qualified.
4. Labor is layered (wage → fringe → payroll taxes → workers' comp → overhead → profit); the engine adds only what the source rate does not already contain, and refuses public-works rates on private projects.
5. Every calculation stores inputs, formulas and a deterministic id; an incomplete calculation stores **no total**.
6. One usability test is applied to every record the engine reads; flagged/rejected records, restricted sources and unreviewed definitions never produce a verified result, and the database itself (not only Python) refuses `validated` without a reviewer and a fetched source.

## Independent verification

The system was built by one process and then attacked by independent reviewers who had not written it: **F2** checked the source claims (22 corrections applied), **F1** audited code, arithmetic, schema and data (42 findings: 3 critical, 21 major, 18 minor — all reproduced; the engine was rewritten and every finding has a regression test or a documented decision, see the *Resolution* section of `docs/independent_review_F1.md`), **F3** re-checked the fixes and found 34 further findings (13 major; all but a few residual limits fixed, see the *Resolution* section of `docs/independent_review_F3.md`). The F3 fixes themselves were verified by the author's tests and a mutation re-run (148 mutants executed in two rounds; after the added tests every one is killed by a test, except the calc-version-fingerprint mutant, which the harness itself pins), **not** by a further independent code review. Reviewers' raw findings are in `data/raw_agent_returns/`.
