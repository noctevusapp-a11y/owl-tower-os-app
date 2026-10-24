"""Generated reports: coverage matrix, data-gap backlog, validation report, pilot status. Pure functions over a Database."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .store import Database
from .validate import Issue, OBSERVED_TABLES

# Which trades / equipment types serve which category (used for coverage display only)
CAT_TRADES = {"CAT-FRM": ["TR-CARP", "TR-LAB"], "CAT-DRY": ["TR-DRYW", "TR-TAPE"], "CAT-INS": ["TR-INS"],
              "CAT-CON": ["TR-CEM", "TR-REB", "TR-LAB"], "CAT-PNT": ["TR-PNT"], "CAT-HVC": ["TR-HVAC", "TR-SHM"]}
CAT_EQUIP = {"CAT-CON": ["EQ-PTROWEL", "EQ-CVIB"], "CAT-HVC": ["EQ-HVACVAC"]}
REGION_COLS = [("LA County", "REG-CA-037"), ("Other SoCal", ["REG-CA-059", "REG-CA-065", "REG-CA-071", "REG-CA-073", "REG-CA-111"]),
               ("Arizona", "REG-US-AZ"), ("Nevada", "REG-US-NV")]


def _subtree(db: Database, root: str) -> set[str]:
    kids: dict[str, list[str]] = defaultdict(list)
    for r in db["regions"]:
        if r["parent_region_id"]:
            kids[r["parent_region_id"]].append(r["region_id"])
    out, stack = set(), [root]
    while stack:
        x = stack.pop()
        if x not in out:
            out.add(x)
            stack.extend(kids.get(x, []))
    return out


def region_sets(db: Database) -> dict[str, set[str]]:
    sets: dict[str, set[str]] = {}
    for name, roots in REGION_COLS:
        roots = roots if isinstance(roots, list) else [roots]
        sets[name] = set().union(*[_subtree(db, r) for r in roots])
    return sets


def _cell(rows: list[dict]) -> str:
    v = sum(1 for r in rows if r["review_status"] == "validated")
    u = sum(1 for r in rows if r["review_status"] == "unreviewed")
    return f"{v} / {u}" if rows else "—"


def counts(db: Database) -> dict[str, Any]:
    by_status: dict[str, Counter] = {t: Counter(r.get("review_status", "n/a") for r in db[t]) for t in OBSERVED_TABLES}
    by_origin: dict[str, Counter] = {t: Counter(r.get("origin", "n/a") for r in db[t]) for t in db.meta if db[t] and "origin" in db[t][0]}
    return {
        "unique_products": len(db["products"]),
        "price_observations": len(db["price_observations"]),
        "material_spec_lines_targeted": len([t for t in db["capture_targets"] if t["target_kind"] == "material"]),
        "material_spec_lines_captured": len({p["spec_key"] for p in db["products"]}),
        "work_items_defined": len(db["work_items"]),
        "assemblies_defined": len(db["assemblies"]),
        "labor_rates_observed": len([r for r in db["labor_rates"] if r["origin"] == "observed"]),
        "burden_rates_observed": len([r for r in db["burden_rates"] if r["origin"] == "observed"]),
        "equipment_rates_observed": len([r for r in db["equipment_rates"] if r["origin"] == "observed"]),
        "productivity_norms_observed": len([r for r in db["productivity_observations"] if r["origin"] == "observed"]),
        "productivity_norms_missing": len([r for r in db["productivity_observations"] if r["origin"] == "missing"]),
        "sources_registered": len(db["sources"]),
        "sources_fetched_primary": len([s for s in db["sources"] if s["verification_method"] == "fetched_primary"]),
        "sources_search_snippet_only": len([s for s in db["sources"] if s["verification_method"] == "search_snippet_only"]),
        "records_validated_total": sum(c.get("validated", 0) for c in by_status.values()),
        "runs_complete": len([r for r in db["calculation_runs"] if r["status"] == "complete"]),
        "runs_incomplete": len([r for r in db["calculation_runs"] if r["status"] == "incomplete"]),
        "runs_failed": len([r for r in db["calculation_runs"] if r["status"] == "failed"]),
    }


def coverage_matrix(db: Database) -> str:
    rs = region_sets(db)
    cats = [c for c in db["categories"] if c["parent_category_id"] is None]
    sub_by_parent: dict[str, set[str]] = defaultdict(set)
    for c in db["categories"]:
        if c["parent_category_id"]:
            sub_by_parent[c["parent_category_id"]].add(c["category_id"])
    prods = {p["product_id"]: p for p in db["products"]}
    md = ["# Coverage matrix", "",
          "Cell format: **validated / unreviewed** observed records (— = none). A cell is only meaningful for the region named; "
          "national or state-level rows are counted in the last column and are NOT local data. Counts are computed from `data/csv` at build time.", ""]
    # ---- materials
    md += ["## Materials — products and price observations", "",
           "Targets = material spec lines in `capture_targets`. Captured = distinct spec_keys with at least one product.", "",
           "| category | targets | captured | products | observations | " + " | ".join(n for n, _ in REGION_COLS) + " |", "|---|---|---|---|---|" + "---|" * len(REGION_COLS)]
    for c in cats:
        subs = sub_by_parent.get(c["category_id"], set())
        if not subs:
            continue
        tg = [t for t in db["capture_targets"] if t["target_kind"] == "material" and t["category_id"] in subs]
        pr = [p for p in db["products"] if p["category_id"] in subs]
        ob = [o for o in db["price_observations"] if prods.get(o["product_id"], {}).get("category_id") in subs]
        cells = [_cell([o for o in ob if o.get("region_id") in rs[n]]) for n, _ in REGION_COLS]
        md.append(f"| {c['category_id']} {c['name']} | {len(tg)} | {len({p['spec_key'] for p in pr})} | {len(pr)} | {len(ob)} | " + " | ".join(cells) + " |")
    md.append("")
    nonpilot = [c["category_id"] + " " + c["name"] for c in cats if not sub_by_parent.get(c["category_id"])]
    md += [f"Not in the pilot (no spec lines yet): {', '.join(nonpilot)}.", ""]
    # ---- labor / burden / equipment / productivity
    def per_cat(title, table, key_fn, code_map, note):
        md.extend([f"## {title}", "", note, "", "| category | records expected from | " + " | ".join(n for n, _ in REGION_COLS) + " | national / state fallback |",
                   "|---|---|" + "---|" * (len(REGION_COLS) + 1)])
        for c in cats:
            codes = code_map.get(c["category_id"])
            if not codes:
                continue
            rows = [r for r in db[table] if key_fn(r) in codes and r["origin"] == "observed"]
            local = [_cell([r for r in rows if r.get("region_id") in rs[n]]) for n, _ in REGION_COLS]
            allr = set().union(*rs.values())
            fb = _cell([r for r in rows if r.get("region_id") not in allr])
            md.append(f"| {c['category_id']} {c['name']} | {', '.join(codes)} | " + " | ".join(local) + f" | {fb} |")
        md.append("")
    per_cat("Labor — statistical wages / determinations / company rates", "labor_rates", lambda r: r["trade_code"], CAT_TRADES,
            "Rates by trade used in the category (all rate types together; see `labor_rates.rate_type`). Loaded employer cost additionally needs burden items (below).")
    per_cat("Equipment rates", "equipment_rates", lambda r: r["equipment_type_code"], CAT_EQUIP,
            "Only categories whose pilot work items name equipment are listed.")
    # productivity
    md += ["## Productivity norms (labor-hours)", "", "| category | work items | norms observed | norms missing |", "|---|---|---|---|"]
    for c in cats:
        subs = [w for w in db["work_items"] if w["category_id"] == c["category_id"]]
        if not subs:
            continue
        ids = {w["work_item_id"] for w in subs}
        po = [p for p in db["productivity_observations"] if p["work_item_id"] in ids]
        md.append(f"| {c['category_id']} {c['name']} | {len(subs)} | {len([p for p in po if p['origin'] == 'observed'])} | {len([p for p in po if p['origin'] == 'missing'])} |")
    md.append("")
    # burden
    md += ["## Employer burden items", "", "| burden type | records | regions |", "|---|---|---|"]
    types = ["employer_benefits", "fica_social_security", "fica_medicare", "futa", "state_ui", "state_ett", "workers_comp"]
    for t in types:
        rows = [b for b in db["burden_rates"] if b["burden_type"] == t and b["origin"] == "observed"]
        md.append(f"| {t} | {len(rows)} ({_cell(rows)} validated/unreviewed) | {', '.join(sorted({r['region_id'] for r in rows})) or '—'} |")
    md.append("")
    # cost components of the 25 work items
    md += ["## Cost-component readiness of the pilot work items", "",
           "How many of the work-item components can currently be priced (strict mode, LA County). Derived from the last calculation runs.", "",
           "| component kind | components defined | currently priced | blocked (missing input) |", "|---|---|---|---|"]
    runs = {(r["target_type"], r["target_id"]): r for r in db["calculation_runs"] if r["target_type"] == "unit_cost"}
    blocked_refs = {m.get("component_ref") for r in runs.values() for m in r["missing_inputs"]}
    for kind in ("material", "labor", "equipment", "other_direct"):
        comps = [c for c in db["work_item_components"] if c["component_kind"] == kind]
        if not comps:
            md.append(f"| {kind} | 0 | 0 | 0 |"); continue
        b = len([c for c in comps if c["component_id"] in blocked_refs])
        md.append(f"| {kind} | {len(comps)} | {len(comps) - b} | {b} |")
    md.append("")
    return "\n".join(md)


FILL_HINT = {
    "PRICE_MISSING": "Capture ≥1 real SKU matching the spec line (templates/price_capture_template.csv) in the target region.",
    "WASTE_MISSING": "Source a waste/loss factor for the line with a stated basis, or add an approved assumption.",
    "CREW_MISSING": "Extract a crew composition (trades, quantities, shift) from a documented norm source.",
    "PRODUCTIVITY_MISSING": "Extract a labor norm (document, edition, page, crew, daily output, conditions).",
    "CONSUMPTION_MISSING": "Extract manufacturer coverage with film thickness, coats and conditions; bind to a SKU.",
    "QUANTITY_MISSING": "Derive the quantity from geometry or manufacturer data.",
    "LABOR_RATE_MISSING": "Ingest OEWS wages (connectors/oews_flatfile.py) or company payroll rates.",
    "EQUIPMENT_RATE_MISSING": "Capture an equipment rate with operator/fuel treatment.",
    "DEFINITION_NOT_REVIEWED": "A person other than the author checks the work item's scope, specification and quantities and records the review (review_events); until then strict runs cannot complete.",
    "CONSUMPTION_AMBIGUOUS": "Add a consumption_selector (film thickness / substrate / method / conditions) to the work-item component, or supersede the wrong coverage row.",
    "BURDEN_AMBIGUOUS": "Two burden rows tie on region, trade and date: supersede one, or pass the workers' comp class code.",
    "LABOR_RATE_AMBIGUOUS": "Several wage rows tie: name the classification (RunParams.classification) or supersede the wrong row.",
    "PAYROLL_TAX_MISSING": "Capture the statutory employer payroll-tax rate (IRS / state agency) for the region.",
    "BENEFITS_MISSING": "Capture an employer-benefit ratio (ECEC) or the company's actual benefit cost.",
    "WORKERS_COMP_MISSING": "Enter the insurer-quoted workers' comp rate by class code (company specific).",
    "FUEL_NOT_PRICED": "Capture fuel_cost_hr for the equipment rate (rate excludes fuel).",
    "OPERATOR_NOT_PRICED": "Add an operator to the crew or choose an equipment rate that includes one.",
}


def missing_summary(db: Database) -> list[dict]:
    agg: dict[str, dict] = {}
    for r in db["calculation_runs"]:
        if r["target_type"] != "unit_cost":
            continue
        for m in r["missing_inputs"]:
            a = agg.setdefault(m["code"], {"code": m["code"], "count": 0, "items": set(), "fill": m.get("how_to_fill", "")})
            a["count"] += 1
            a["items"].add(m["needed"])
    return sorted(agg.values(), key=lambda a: -a["count"])


def backlog(db: Database, agent_gaps: dict[str, list[str]]) -> str:
    md = ["# Data-gap backlog", "",
          "Generated at build time from open `capture_targets`, the missing inputs reported by the strict calculation runs, and the gaps "
          "listed by the research agents. Priority 1 = blocks a pilot unit cost.", ""]
    md += ["## A. Blockers that are not data tasks (do these first)", "",
           "| # | action | why |", "|---|---|---|",
           "| A1 | **Open outbound network access** for the build environment to the hosts in `docs/network_allowlist.md` (or run the connectors on a machine with normal internet access). | Every primary source host was refused by the sandbox network policy on 2026-10-24; no primary document could be fetched, so nothing can be `validated`. |",
           "| A2 | Register a free **BLS API v2 key** (store as `BLS_API_KEY`; do not commit). | Index series and OEWS time series need the v2 limits (500 queries/day). Terms: cite source and access date. |",
           "| A3 | A person reads the **live Terms of Use / robots.txt** of Home Depot, Lowe's, Grainger, Ferguson, Sherwin-Williams and Dunn-Edwards before any price capture; record the outcome in `sources.reuse_status`. | Retailer terms were only seen as search snippets. Sources registered as `prohibited` (Lowe's, Ferguson snippets) are **refused by the importer whatever the capture method** until their live terms are read and the status is corrected; `restricted_no_automated_access` sources (Home Depot, Grainger, Sherwin-Williams) accept manual capture only. No scraping is implemented. |",
           "| A4 | Decide who captures retail prices **by hand** (office staff with a browser) and use `templates/price_capture_template.csv`. | The only compliant route for retailers without a licensed feed. |",
           "| A5 | Confirm whether the company will obtain **contractor (pro-account / supplier) quotes**; they are a separate price channel and the only valid contractor-cost evidence. | Retail prices must never be presented as contractor purchase cost. |",
           "| A7 | Name a **reviewer for the 25 work-item and 10 assembly definitions** (scope, specification, quantities, exclusions) and record the review. | Strict runs refuse unreviewed definitions (`DEFINITION_NOT_REVIEWED`); the definitions were written by the system and have not been checked by a person. |",
           "| A8 | A person **reviews the `regions` table** (parent links, `state_code`, the LA County → California → US chain) against the official delineation (OMB/BLS metropolitan areas, county FIPS) and records the review. | The region rows were written by the system (`origin = assumed`, `unreviewed`). Strict runs therefore cannot use ancestor-region rates (state or national rows for an LA County price) and cannot tell which state's payroll items apply (`REGION_STATE_UNKNOWN`); only exact-region rows are usable until the table is reviewed. |",
           "| A6 | Provide company-specific burden inputs: **workers' comp rate by class, experience mod, UI rate notice, benefit costs**, and (optionally) actual payroll rates by trade. | These are company-specific and cannot be found in public sources. |", ""]
    open_t = [t for t in db["capture_targets"] if t["status"] == "open"]
    kinds = Counter((t["target_kind"], t["pilot_priority"]) for t in open_t)
    md += ["## B. Open capture targets", "", "| kind | priority 1 | priority 2 | priority 3 |", "|---|---|---|---|"]
    for k in ("material", "labor", "burden", "equipment", "productivity", "index", "other"):
        md.append(f"| {k} | {kinds.get((k, 1), 0)} | {kinds.get((k, 2), 0)} | {kinds.get((k, 3), 0)} |")
    md += ["", "The full list with required attributes, recommended sources and the work items that need each line is `data/csv/capture_targets.csv`. "
           "Priority-1 material lines (needed by a pilot work item):", ""]
    p1 = [t for t in open_t if t["target_kind"] == "material" and t["pilot_priority"] == 1]
    md += ["| target | category | description | needed by |", "|---|---|---|---|"]
    for t in sorted(p1, key=lambda t: (t["category_id"], t["description"])):
        md.append(f"| `{t['target_id']}` | {t['category_id']} | {t['description']} | {t['required_by']} |")
    md += ["", "## C. Missing inputs reported by strict calculation runs", "",
           "Aggregated over all 25 work-item runs (LA County, as of the build date). Every run is `incomplete` and carries no total.", "",
           "| code | occurrences | distinct inputs | how to fill |", "|---|---|---|---|"]
    for a in missing_summary(db):
        md.append(f"| {a['code']} | {a['count']} | {len(a['items'])} | {FILL_HINT.get(a['code'], a['fill'])} |")
    md += ["", "## D. Gaps reported by the research agents (search-summary level)", ""]
    for ag, gaps in agent_gaps.items():
        md += [f"### Agent {ag}", ""] + [f"- {g}" for g in gaps] + [""]
    return "\n".join(md)


def validation_report(db: Database, issues: list[Issue], test_summary: str, build_ts: str) -> str:
    sev = Counter(i.severity for i in issues)
    md = ["# Validation report (automated)", "", f"Build timestamp: `{build_ts}`.", "",
          "## What was checked", "",
          "Rules in `pipeline/costdb/validate.py`: foreign keys and duplicate ids; source terms and verification status; product spec completeness and "
          "`spec_key` consistency; pack/unit/date/duplicate/outlier checks on price observations; labor layering (statistical vs prevailing vs loaded, "
          "double-counted fringe/payroll/workers' comp, public-works scope); crew operator double counting and equipment fuel; productivity "
          "reconciliation (reported vs crew×shift/output); work-item scope tokens and cost tags; work-item components against the specification the work item "
          "states; assembly inclusions/exclusions derived from the children, assembly specification against its component rows, scope overlap and unit "
          "consistency; assumptions (four eyes, expiry, uniqueness); validated records without a reviewer; stored calculation runs "
          "(inputs exist, no flagged inputs, strict runs without assumptions, retail basis only with opt-in, **re-computation reproduces stored totals**). "
          "Screening thresholds are a documented policy (`validate.DEFAULT_POLICY`), each with its basis.", "",
          "## Result on the real data", "",
          f"- issues: **{len(issues)}** (errors {sev.get('error', 0)}, warnings {sev.get('warning', 0)}, info {sev.get('info', 0)})", ""]
    if issues:
        md += ["| rule | severity | table | record | message |", "|---|---|---|---|---|"]
        for i in issues[:200]:
            md.append(f"| {i.rule_code} | {i.severity} | {i.record_table} | `{i.record_id}` | {i.message} |")
        md.append("")
    c = counts(db)
    md += ["**Reading this result:** zero issues means the data that exists is internally consistent — it does **not** mean the database is "
           "complete or verified. There are no price observations, equipment rates or productivity norms to check yet, and no source was fetched.", "",
           "## Records by review status", "", "| table | validated | unreviewed | flagged | rejected |", "|---|---|---|---|---|"]
    for t in OBSERVED_TABLES:
        cn = Counter(r["review_status"] for r in db[t])
        md.append(f"| {t} | {cn.get('validated', 0)} | {cn.get('unreviewed', 0)} | {cn.get('flagged', 0)} | {cn.get('rejected', 0)} |")
    md += ["", f"Validated records in total: **{c['records_validated_total']}**. Sources fetched from a primary host: **{c['sources_fetched_primary']}** of "
           f"{c['sources_registered']} (the rest are search-snippet level). The promotion gate refuses to validate anything whose source was not fetched.", "",
           "## Automated test suite", "", test_summary, "",
           "Tests cover: exact unit conversions; spec-key equivalence; hand-computed unit cost, labor, markup/margin, index and region adjustments; strict vs "
           "assumption modes; missing-input reporting; operator and benefit double counting; prevailing-wage refusal for private projects; assembly "
           "aggregation and scope overlap; every validator rule firing on broken data; promotion gate; retail-capture importer; BLS/OEWS/PDF parsers on "
           "format fixtures; PostgreSQL constraints, append-only triggers and CSV import; data gates on the real files. Synthetic fixtures live only in "
           "`tests/` and are rejected from `data/`.", ""]
    return "\n".join(md)
