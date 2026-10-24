#!/usr/bin/env python3
"""Write the extraction report of the book table: what was read, how it was checked, what is derived, what is open.

  python3 -I report.py <table_dir> <crews_totals.csv> <trade_rates.csv> <spot_verdicts.csv> <out.md>

<spot_verdicts.csv> is the spot-check sample with the reviewer's verdict column filled (ok / wrong:<cells>).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    table, crews_csv, trades_csv, spot_csv, out = (Path(a) for a in sys.argv[1:6])
    rows = list(csv.DictReader((table / "book_lines_la_latest.csv").open(encoding="utf-8")))
    rep = json.loads((table / "build_report.json").read_text(encoding="utf-8"))
    drep = json.loads((table / "derive_report.json").read_text(encoding="utf-8"))
    crews = list(csv.DictReader(crews_csv.open(encoding="utf-8"))) if crews_csv.exists() else []
    trades = list(csv.DictReader(trades_csv.open(encoding="utf-8"))) if trades_csv.exists() else []
    spot = list(csv.DictReader(spot_csv.open(encoding="utf-8"))) if spot_csv.exists() else []
    st = Counter(r["status"] for r in rows)
    priced = [r for r in rows if r["status"] in ("verified", "flagged")]
    by_div = Counter((r["division"], r["status"]) for r in priced)
    divs = sorted({r["division"] for r in priced if r["division"]})
    flags = Counter()
    for r in rows:
        for f in r["flags"].split(";"):
            if f:
                flags[f] += 1
    open_flags = {"MONEY_UNSETTLED", "MONEY_AMBIGUOUS", "OUTPUT_HOURS_UNSETTLED", "OUTPUT_HOURS_AMBIGUOUS", "LABOR_CREW_MISMATCH", "EQUIP_CREW_MISMATCH",
                  "CREW_UNREAD", "LINE_NUMBER_MISSING", "LINE_ORDER", "SECTION_ID_DOUBTFUL", "OP_MISMATCH"}
    crews_ok = sum(1 for c in crews if c.get("checks_ok", "").lower() == "true")
    trades_ok = sum(1 for t in trades if t.get("checks_ok", "").lower() == "true")
    spot_ok = sum(1 for s in spot if s.get("reviewer_verdict", "").strip().lower().startswith("ok"))
    spot_n = sum(1 for s in spot if s.get("reviewer_verdict", "").strip())
    derived_verified = sum(1 for r in rows if r["status"] == "verified" and r.get("total_la_latest"))
    lines = [f"# Book table extraction report — Building Construction Costs with RSMeans data 2022 (company reference copy)", "",
             f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}. Scripts: `cost-db/book_ocr/` (OCR, three-reading parser, table builder, "
             "derivation, spot check). Data: `cost-db/data/books/rsmeans_bcc_2022/`.", "",
             "## 1. What was read", "",
             f"* Scan: 964 PDF pages (sha256 `9c5aee73…c075bc`), unit-price section PDF pages 24–750, split into 6 parts and transferred from the owner's Mac.",
             f"* OCR: tesseract 5.3 at 360 dpi (own run) **and** the scan's own text layer (a second engine) **and** a geometric reading of every number "
             "(digit-glyph count and decimal-point position on the page image). A value is kept only when the readings agree or the table's arithmetic "
             "selects it: `total = material + labor + equipment`; `labor-hours = crew labor-hours / daily output`; `labor = crew daily labor cost / output`; "
             "`total incl. O&P = 1.10 × material + crew O&P labor / output + crew O&P equipment / output`.",
             f"* Table pages parsed: **{rep['pages']}**; sections: **{rep['sections']}**; printed lines: **{rep['lines']}** "
             f"(priced lines {len(priced)}, description-only lines {st.get('header', 0)}, percentage-add lines {st.get('percent_add', 0)}).",
             f"* Crew table (book pages 749–785): {len(crews)} crews parsed, {crews_ok} pass every identity (member sums, labor-hours, cost per labor-hour); "
             f"single-trade crews (`1 Carp` …) are built from the trade-rate table (inside back cover: {len(trades)} trades, {trades_ok} pass the row identities).",
             f"* City Cost Index, Los Angeles (900–902), book page 791: 20 rows read from a 300-dpi crop and checked against the image.", "",
             "## 2. Status of the priced lines", "",
             f"| status | lines | share |", "|---|---|---|",
             f"| verified (every number supported by ≥ 2 readings or the arithmetic, no open check) | {st.get('verified', 0)} | {st.get('verified', 0) / max(1, len(priced)):.1%} |",
             f"| flagged (a check failed or a cell stayed unreadable; values shown are best readings) | {st.get('flagged', 0)} | {st.get('flagged', 0) / max(1, len(priced)):.1%} |", "",
             "By division (verified / flagged):", "", "| division | verified | flagged |", "|---|---|---|"]
    for d in divs:
        lines.append(f"| {d} | {by_div[(d, 'verified')]} | {by_div[(d, 'flagged')]} |")
    lines += ["", "Open flags (one line can carry several):", "", "| flag | lines | meaning |", "|---|---|---|"]
    meaning = {"MONEY_UNSETTLED": "material/labor/equipment/total do not add up for any combination of readings",
               "MONEY_AMBIGUOUS": "two combinations add up equally well", "OUTPUT_HOURS_UNSETTLED": "daily output × labor-hours is not a crew-day",
               "OUTPUT_HOURS_AMBIGUOUS": "two output/hours pairs fit", "LABOR_CREW_MISMATCH": "labor ≠ crew daily cost / output",
               "EQUIP_CREW_MISMATCH": "equipment ≠ crew equipment / output", "CREW_UNREAD": "the crew cell is printed but unreadable",
               "LINE_NUMBER_MISSING": "no reading caught the line number", "LINE_ORDER": "line number out of the section's numbering order (misread)",
               "SECTION_ID_DOUBTFUL": "numbering restarted under the same section id (one id misread)", "OP_MISMATCH": "total incl. O&P contradicts the components"}
    for f, n in sorted(flags.items(), key=lambda kv: -kv[1]):
        if f in open_flags:
            lines.append(f"| `{f}` | {n} | {meaning.get(f, '')} |")
    lines += ["", "Informational flags (a cell computed from the others by the book's own rules): " +
              ", ".join(f"`{f}` {n}" for f, n in sorted(flags.items(), key=lambda kv: -kv[1]) if f not in open_flags), "",
              "## 3. Spot check against the page images", "",
              (f"Random sample of verified rows cut out of the page images and compared cell by cell by the author: **{spot_ok} of {spot_n} rows fully correct** "
               f"(see `spot_check/`). " if spot_n else "Spot check sheets are in `spot_check/`; verdicts not yet recorded. ") +
              "Residual error types seen: a digit misread identically by both OCR engines (1↔7), a value overlapped by the row above, the cut right edge of the "
              "scan (total incl. O&P). These survive only where no arithmetic check reaches the cell.", "",
              "## 4. Derived Los Angeles, latest-month values", "",
              f"* {drep['priced_2022']} lines carry a 2022 cost; {drep['priced_latest']} got a derived Los Angeles value for {drep['latest_period']} "
              f"({derived_verified} of them on verified lines).",
              "* Formula per line: component × City Cost Index (LA, book 2022; material index for material, installation index for labor and equipment) "
              "× BLS factor (material: PPI series by material class; labor: ECI total compensation, construction; equipment: PPI machinery). "
              "Every factor is written next to the value. `origin = derived`, `review_status = unreviewed`.",
              "* Not escalated separately: fuel inside the equipment cost (diesel rose 1.7–1.85×; the fuel share is not published). Not applied: "
              "any company-specific markup, sales tax, delivery, quantity discounts, current supplier quotes.", "",
              "## 5. Limits", "",
              "* The 2022 values are what the book printed, read by machine: the verified set is machine-verified, not human-verified line by line.",
              "* Lines marked flagged must be checked against the book page (`book_page`) before use.",
              "* Total incl. O&P is missing on right-hand pages where the scan cut the column; where the crew is known it can be recomputed by the formula above.",
              "* Descriptions are OCR text (cleaned); `description_path` applies the book's indentation rule mechanically and can over-include a sibling line.",
              "* The derived latest values are budget-level references, not prices observed in Los Angeles in 2026.", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
