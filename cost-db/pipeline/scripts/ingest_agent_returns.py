#!/usr/bin/env python3
"""Ingest raw research-agent returns into the canonical CSV tables.

Inputs : data/raw_agent_returns/agent_A*.json   (search-snippet-level evidence; NEVER fetched primary data)
Outputs: data/csv/sources.csv, labor_rates.csv, burden_rates.csv, indices.csv
         data/evidence_digest.csv   (every numeric data point with an explicit import decision)
         docs/source_findings.md    (every finding with its evidence URL)

Import policy (docs/methodology.md §Evidence):
  * every source is stored with verification_method=search_snippet_only -> can never be promoted to 'validated'
    by the automated promoter; a human/agent must fetch the primary document first.
  * values from sources whose terms forbid storage (FRED) are NOT stored; only series identifiers are.
  * secondary/aggregator values (EPI, ustax.tools, single-author indices) are NOT stored as data.
  * a number is imported only when its literal digits appear in the quoted evidence AND it maps to a table row
    with all mandatory fields (trade, region, period, unit, source locator).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb.ids import make_id  # noqa: E402
from costdb.schema_meta import parse_schema  # noqa: E402
from costdb.store import Database  # noqa: E402

RAW = ROOT / "data" / "raw_agent_returns"
CSV_DIR = ROOT / "data" / "csv"
TODAY = "2026-10-24"
RETRIEVED = "2026-10-24T00:00:00+00:00"
SEARCH_NOTE = ("Obtained through a web-search result summary; the primary page could not be fetched from the build "
               "environment (network policy). Not eligible for 'validated' until the primary document is read.")


def load_returns() -> list[dict]:
    out = []
    for p in sorted(RAW.glob("agent_A*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def literal_ok(dp: dict) -> bool:
    lit, q = norm(dp["value_literal"]), norm(dp["evidence_quote"])
    nums = re.findall(r"\d[\d,\.]*", lit)
    return lit in q or all(n.strip(".,") in q for n in nums)


# decisions for numeric data points: (agent, index) -> (disposition, reason)
def disposition(agent: str, idx: int, dp: dict) -> tuple[str, str]:
    url = dp.get("evidence_url", "")
    host = urlparse(url).hostname or ""
    key = (agent, idx)
    imports = {
        ("A1", 6): ("imported:labor_rates", "BLS OOH carpenter median hourly equivalent (national, May 2025)"),
        ("A1", 29): ("imported:burden_rates", "IRS Pub 15 (2026) employer Social Security rate and wage base"),
        ("A1", 30): ("imported:burden_rates", "IRS Pub 15 (2026) employer Medicare rate"),
        ("A1", 32): ("imported:burden_rates", "California EDD ETT rate and wage limit, 2026"),
    }
    if key in imports:
        return imports[key]
    if "fred.stlouisfed.org" in host:
        return "not_imported:fred_terms", "FRED terms bar storing/caching FRED content; only the BLS series identifier is kept"
    if "epi.org" in host or "ustax.tools" in host:
        return "not_imported:secondary_source", "secondary reproduction; replace with the primary BLS/IRS figure"
    if "ieee-dataport" in host:
        return "not_imported:derived_index_unknown_license", "single-author derived index, licence for this record not seen"
    if agent == "A3" and "BLS" not in dp["source_id"] and any(
            k in dp["source_id"] for k in ("USG", "NATGYP", "DUNNEDWARDS", "QUIKRETE", "JM-", "ASTM", "NIST", "WWPA", "RETAIL")):
        return ("candidate:product_spec_or_consumption",
                "manufacturer/standard specification; becomes product_consumption/products data once a purchasable SKU is bound")
    if agent == "A1" and idx in (0, 1, 2, 3, 4, 5, 7):
        return "not_imported:no_trade_or_region_fit", "all-occupation or group-level wage; not a trade rate for a cost region"
    if agent == "A1" and idx in (33,):
        return "not_imported:range_not_a_rate", "UI rate depends on the employer's experience rating; a range is not a rate"
    if agent == "A1" and idx in (34,):
        return "not_applicable:employee_side", "SDI is employee withholding, not employer burden"
    if agent == "A1" and idx in (35, 36, 37):
        return "reference_only", "workers' comp advisory figures are averages; actual cost is insurer/class/experience specific"
    return "reference_only", "process/limit/structure information, not a cost input"


def main() -> int:
    returns = load_returns()
    db = Database()
    schema = parse_schema()

    # ---------------------------------------------------------- sources
    hosts_blocked = {}
    reach = ROOT.parent  # unused; reachability results are stored in the repo (see below)
    reach_file = RAW / "host_reachability_2026-10-24.tsv"
    if reach_file.exists():
        for line in reach_file.read_text().splitlines():
            h, code = line.split()
            hosts_blocked[h] = code == "000"
    seen: dict[str, dict] = {}
    for r in returns:
        for s in r["sources"]:
            if s["source_id"] in seen:
                raise SystemExit(f"duplicate source_id across agents: {s['source_id']}")
            seen[s["source_id"]] = s
    for sid in sorted(seen):
        s = seen[sid]
        host = urlparse(s.get("url") or "").hostname
        blocked = hosts_blocked.get(host)
        row = {
            "source_id": sid, "title": s["title"], "owner": s["owner"], "source_kind": s["source_kind"],
            "url": s.get("url"), "data_url": s.get("data_url"), "data_provided": s.get("data_provided"),
            "geography": s.get("geography"), "period_covered": s.get("period_covered"), "edition": s.get("edition"),
            "access_format": s.get("access_format"), "requires_registration": s.get("requires_registration"),
            "requires_payment": s.get("requires_payment"), "access_notes": s.get("access_notes"),
            "reuse_status": s["reuse_status"], "reuse_terms": s.get("reuse_terms"),
            "reuse_terms_url": s.get("reuse_terms_url"), "limitations": s.get("limitations"),
            "update_frequency": s.get("update_frequency"), "quality_tier": s["quality_tier"],
            "reachability_from_build_env": "blocked_by_network_policy" if blocked else "not_tested",
            "reachability_checked_at": date.fromisoformat(TODAY) if blocked is not None else None,
            "verification_method": s["verification_method"], "evidence_quote": s.get("evidence_quote"),
            "evidence_url": s.get("evidence_url"), "origin": "observed", "review_status": "unreviewed",
            "reviewed_by": None, "reviewed_at": None, "registered_at": date.fromisoformat(TODAY),
            "notes": SEARCH_NOTE if s["verification_method"] == "search_snippet_only" else
            "Recalled from model knowledge; not confirmed by any search result.",
        }
        db.add("sources", row)

    # --------------------------------------------- independent-review corrections (agent F2)
    corr_path = ROOT / "data" / "register_corrections.json"
    corrections = json.loads(corr_path.read_text(encoding="utf-8")) if corr_path.exists() else {}
    by_id = {r["source_id"]: r for r in db["sources"]}
    for c in corrections.get("source_corrections", []):
        row = by_id[c["source_id"]]                       # KeyError = a correction points at a source that does not exist
        for k, v in c["set"].items():
            row[k] = v
        if c.get("append_notes"):
            row["notes"] = (row["notes"] + "\n" if row["notes"] else "") + c["append_notes"]
        if "review_status" in c["set"] or c["set"].get("review_status") == "flagged":
            row["reviewed_by"] = c.get("reviewer", corrections.get("reviewer", "reviewer"))
            row["reviewed_at"] = RETRIEVED

    # ------------------------------------------------- selected data rows
    a1 = next(r for r in returns if r["agent"] == "A1")
    dps = a1["data_points"]

    def dec(x):
        from decimal import Decimal
        return Decimal(x)

    carp = dps[6]
    assert "29.12" in carp["evidence_quote"] and "$60,580" in carp["evidence_quote"]
    db.add("labor_rates", {
        "labor_rate_id": make_id("LRT", "stat_wage", "TR-CARP", "REG-US", "median", "2025-05"),
        "rate_type": "stat_wage", "trade_code": "TR-CARP",
        "classification_raw": "Carpenters (BLS Occupational Outlook Handbook, national)", "soc_code": "47-2031",
        "statistic": "median", "region_id": "REG-US", "base_wage_hr": dec("29.12"), "fringe_hr": None,
        "fringe_breakdown": None, "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None,
        "total_hr": None, "includes_fringe": False, "includes_payroll_taxes": False, "includes_workers_comp": False,
        "wage_basis": "straight_time", "project_type": "n/a", "use_context": "statistical_reference",
        "apprentice": False, "determination_ref": None, "effective_from": date(2025, 5, 1), "effective_to": None,
        "retrieved_at": RETRIEVED, "derived_from": None, "calc_run_id": None, "source_id": "SRC-BLS-OOH-2025",
        "source_locator": "BLS OOH 'Carpenters' page, Pay section (reference period May 2025) — search summary",
        "evidence_excerpt": carp["evidence_quote"], "raw_file_sha256": None, "origin": "observed",
        "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "created_at": None,
        "notes": "NATIONAL median, not Los Angeles; 'hourly equivalent' is BLS's own conversion of the annual median "
                 "(2,080 h convention). Wages exclude employer-paid benefits. " + SEARCH_NOTE})

    def burden(btype, rate, cap, region, src, dp_idx, cls_note):
        dp = dps[dp_idx]
        db.add("burden_rates", {
            "burden_id": make_id("BRD", btype, region, "2026"), "burden_type": btype, "basis": "pct_of_wages",
            "rate": dec(rate), "wage_cap_annual": dec(cap) if cap else None, "class_code": None, "trade_code": None,
            "region_id": region, "effective_from": date(2026, 1, 1), "effective_to": date(2026, 12, 31),
            "retrieved_at": RETRIEVED, "source_id": src,
            "source_locator": cls_note, "evidence_excerpt": dp["evidence_quote"], "origin": "observed",
            "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "created_at": None,
            "notes": "rate stored as a fraction (0.062 = 6.2%). " + SEARCH_NOTE})

    burden("fica_social_security", "0.062", "184500", "REG-US", "SRC-IRS-PUB15-2026", 29,
           "IRS Publication 15 (2026), Social Security wage base and employer rate — search summary")
    burden("fica_medicare", "0.0145", None, "REG-US", "SRC-IRS-PUB15-2026", 30,
           "IRS Publication 15 (2026), Medicare employer rate — search summary")
    burden("state_ett", "0.001", "7000", "REG-US-CA", "SRC-EDD-PAYROLL-RATES-2026", 32,
           "California EDD, Rates and Withholding, ETT — search summary")

    # index SERIES definitions only (identifiers, no FRED-hosted values)
    series = [
        ("WPUID612", "PPI: Materials and components for construction (intermediate demand)", "SRC-BLS-PPI", "material",
         "identifier seen on a FRED page, verify at bls.gov", "1982=100", "not seasonally adjusted"),
        ("WPU1017", "PPI: Steel mill products", "SRC-BLS-PPI", "material",
         "identifier seen on a FRED page, verify at bls.gov", "1982=100", "not seasonally adjusted"),
        ("ECICONWAG", "ECI: Wages and salaries, private industry, construction", "SRC-BLS-ECI", "labor",
         "identifier seen on a FRED page, verify at bls.gov", "Dec 2005=100", "seasonally adjusted"),
        ("CIU2012300000000I", "ECI: Total compensation, private industry, construction", "SRC-BLS-ECI", "labor",
         "identifier seen on a FRED page, verify at bls.gov", "Dec 2005=100", "not seasonally adjusted"),
    ]
    for code, name, src, applies, note, base, sa in series:
        db.add("indices", {
            "index_id": make_id("IDX", "BLS", code), "publisher": "BLS", "series_code": code, "name": name,
            "base_period": base, "frequency": "quarterly" if code.startswith(("ECI", "CIU")) else "monthly",
            "seasonal_adjustment": sa, "geography": "United States", "applies_to": applies, "source_id": src,
            "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
            "notes": note + ". No index VALUES stored: FRED terms prohibit caching; ingest values from BLS directly."})

    for ic in corrections.get("index_corrections", []):
        for row in db["indices"]:
            if row["series_code"] == ic["series_code"]:
                row["review_status"] = ic["review_status"]
                row["reviewed_by"] = corrections.get("reviewer", "reviewer"); row["reviewed_at"] = RETRIEVED
                row["notes"] = row["notes"] + " " + ic["note"]

    # --------------------------------------------- write CSVs (only the tables this script owns)
    owned = ("sources", "labor_rates", "burden_rates", "indices")
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    from costdb.store import format_value
    for t in owned:
        use = [c for c in schema[t] if not c.generated]
        with open(CSV_DIR / f"{t}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow([c.name for c in use])
            for r in db[t]:
                w.writerow([format_value(c, r.get(c.name)) for c in use])

    # ------------------------------------------------------------- evidence digest
    with open(ROOT / "data" / "evidence_digest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["agent", "idx", "topic", "geography", "period", "value_literal", "unit", "source_id", "evidence_url",
                    "evidence_quote", "literal_check_pass", "disposition", "disposition_reason", "reviewer_note"])
        rnotes = corrections.get("digest_notes", {})
        counts: dict[str, int] = {}
        for r in returns:
            for i, dp in enumerate(r["data_points"]):
                disp, reason = disposition(r["agent"], i, dp)
                counts[disp] = counts.get(disp, 0) + 1
                w.writerow([r["agent"], i, dp["topic"], dp["geography"], dp["period"], dp["value_literal"], dp["unit"],
                            dp["source_id"], dp["evidence_url"], dp["evidence_quote"], "yes" if literal_ok(dp) else "NO",
                            disp, reason, rnotes.get(r["agent"], {}).get(str(i), "")])

    # --------------------------------------------------------------- findings digest
    lines = ["# Source research findings (search-summary level)", "",
             "Every statement below was produced by a research agent from **web-search result summaries only**; the primary "
             "pages could not be opened from the build environment. Treat each as a lead to verify, not as a verified fact. "
             "`prior_knowledge_unverified` means the agent believed it from memory and no search confirmed it.", ""]
    for r in returns:
        lines += [f"## Agent {r['agent']} — {len(r['findings'])} findings, {r['search_count']} searches", ""]
        for f in r["findings"]:
            lines.append(f"- **{f['topic']}** — {f['statement']}  \n  _verification:_ `{f['verification_method']}` · "
                         f"[evidence]({f['evidence_url']})")
        lines += ["", f"### Agent {r['agent']} — gaps", ""] + [f"- {g}" for g in r["gaps"]]
        lines += ["", f"### Agent {r['agent']} — blocked or unverifiable", ""] + [f"- {g}" for g in r["blocked_or_unverifiable"]] + [""]
    if corrections.get("finding_notes"):
        lines += ["## Reviewer corrections to the findings above", ""] + [f"- {n}" for n in corrections["finding_notes"]] + [""]
    (ROOT / "docs" / "source_findings.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"sources={len(db['sources'])} labor_rates={len(db['labor_rates'])} burden_rates={len(db['burden_rates'])} "
          f"indices={len(db['indices'])}")
    print("data-point dispositions:", json.dumps(counts, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
