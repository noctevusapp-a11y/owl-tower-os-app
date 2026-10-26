#!/usr/bin/env python3
"""Generate docs/source_register.md (human-readable view of data/csv/sources.csv).  Run: python3 -I pipeline/scripts/build_register_md.py"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb.store import Database  # noqa: E402

TIER = {"A": "A official dataset with method", "B": "B official publication", "C": "C manufacturer doc", "D": "D retailer listing",
        "E": "E secondary", "X": "X unclassified"}
GROUPS = [("Labor, wages and employer burden", ("BLS-OE", "BLS-OOH", "DIR-", "SAM-", "DOL-", "EDD-", "IRS-", "WCIRB", "CDI-", "NVLC", "AZAG", "EPI-")),
          ("Price indices and APIs", ("BLS-API", "BLS-PUBLIC", "BLS-PPI", "BLS-ECI", "BLS-ECEC", "FRED", "AGC-", "USGS")),
          ("Equipment, productivity and public bid data", ("CALTRANS", "USACE", "NAVFAC", "JOINT-", "DTIC", "ARMY", "FHWA", "UTCTR", "SCWS", "ADOT", "NDOT", "TXDOT", "ORDOT",
                                                          "LACDPW", "TORRANCE", "GARDENA", "SBCO", "SDUSD", "OMNICOST", "IEEE", "NREL", "TECHCLEAN")),
          ("Manufacturer documentation and standards", ("USG", "NATGYP", "DUNNEDWARDS", "QUIKRETE", "JM-", "ASTM", "NIST", "WWPA", "AHRI", "RETAIL-JOINT")),
          ("Retailers, distributors, rental and purchasing programs", ("HOMEDEPOT", "LOWES", "GRAINGER", "FERGUSON", "SHERWIN", "SUNBELT", "UNITEDRENTALS", "IMPACT",
                                                                       "SOURCEWELL", "GSA-", "CADGS")),
          ("Classification systems", ("CSI-", "UNSPSC", "CENSUS"))]


def group_of(sid: str) -> str:
    for name, keys in GROUPS:
        if any(k in sid for k in keys):
            return name
    return "Other"


def main() -> int:
    db = Database.load_csv_dir()
    rows = sorted(db["sources"], key=lambda s: (group_of(s["source_id"]), s["source_id"]))
    c = Counter(s["reuse_status"] for s in rows)
    md = ["# Source register", "",
          f"{len(rows)} sources, generated from `data/csv/sources.csv` (same content as `data/source_register.csv` / `.json`). "
          "**Every entry is search-summary level**: the build environment could not open any of these hosts, so no document was actually fetched "
          "(`verification_method`). Treat reuse statuses as leads to confirm at the source, not as legal conclusions.", "",
          "| reuse status | sources |", "|---|---|"] + [f"| {k} | {v} |" for k, v in c.most_common()]
    md += ["", "Columns: owner · data · geography · period · access · terms · limitations · update frequency · quality tier · reachability from the build environment. "
           "Full text of every field (including the evidence quote and URL) is in the CSV.", ""]
    cur = None
    for s in rows:
        g = group_of(s["source_id"])
        if g != cur:
            cur = g
            md += ["", f"## {g}", "", "| id | owner / title | data · geography · period | access | reuse status — terms | limitations | update | tier | reach |",
                   "|---|---|---|---|---|---|---|---|---|"]
        def cut(x, n=170):
            x = (x or "").replace("|", "/").replace("\n", " ")
            return x if len(x) <= n else x[: n - 1] + "…"
        access = f"{s['access_format'] or '?'}{', registration' if s['requires_registration'] else ''}{', PAYMENT' if s['requires_payment'] else ''}"
        reach = "blocked" if s["reachability_from_build_env"] == "blocked_by_network_policy" else "not tested"
        md.append(f"| `{s['source_id']}` | **{cut(s['owner'], 60)}** — {cut(s['title'], 90)}<br>[{cut(s['url'], 55)}]({s['url']}) | "
                  f"{cut(s['data_provided'], 150)} · {cut(s['geography'], 50)} · {cut(s['period_covered'], 40)} | {access} | "
                  f"**{s['reuse_status']}** — {cut(s['reuse_terms'], 140)} | {cut(s['limitations'], 120)} | {cut(s['update_frequency'], 45)} | "
                  f"{s['quality_tier']} | {reach} |")
    md += ["", "Tier legend: " + "; ".join(TIER.values()) + ".", ""]
    (ROOT / "docs" / "source_register.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote docs/source_register.md ({len(rows)} sources, {len(md)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
