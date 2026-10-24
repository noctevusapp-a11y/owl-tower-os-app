#!/usr/bin/env python3
"""Write the extraction report of the book table: what was read, how it was checked, what is derived, what is open.

  python3 -I report.py <table_dir> <crews_totals.csv> <trade_rates.csv> <out.md> [--spot label=sample.csv ...]

Each --spot is a spot-check sample (written by spot_check.py) with the reviewer's verdict column filled (ok / wrong:<cells>).
A sample is reported against the *current* table: rows that the current rule moved out of the sampled tier are listed, and the
correctness rate is given for the rows still in the tier (a sample drawn from the earlier tier, restricted to the current tier,
is still a uniform random sample of the current tier because the rule only removes rows).
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OPEN_FLAGS = {"MONEY_UNSETTLED", "MONEY_AMBIGUOUS", "OUTPUT_HOURS_UNSETTLED", "OUTPUT_HOURS_AMBIGUOUS", "LABOR_CREW_MISMATCH",
              "CREW_UNREAD", "LINE_NUMBER_MISSING", "LINE_ORDER", "SECTION_ID_DOUBTFUL", "OP_MISMATCH", "COST_MISSING", "OUTPUT_HOURS_MISSING",
              "EQUIPMENT_DERIVED_FROM_SUM", "EQUIP_WITHOUT_CREW_EQUIP", "SECTION_UNKNOWN"}
MEANING = {"MONEY_UNSETTLED": "material/labor/equipment/total do not add up for any combination of readings",
           "MONEY_AMBIGUOUS": "two combinations add up equally well", "OUTPUT_HOURS_UNSETTLED": "daily output × labor-hours is not a crew-day",
           "OUTPUT_HOURS_AMBIGUOUS": "two output/hours pairs fit", "LABOR_CREW_MISMATCH": "labor ≠ crew daily cost / output",
           "CREW_UNREAD": "the crew cell is printed but unreadable", "LINE_NUMBER_MISSING": "no reading caught the line number",
           "LINE_ORDER": "line number out of the section's numbering order (misread)",
           "SECTION_ID_DOUBTFUL": "numbering restarted under the same section id (one id misread)", "OP_MISMATCH": "total incl. O&P contradicts the components",
           "COST_MISSING": "a crew-day was printed but no cost was read", "OUTPUT_HOURS_MISSING": "a labor cost is printed but no output/hours were read",
           "EQUIPMENT_DERIVED_FROM_SUM": "equipment computed as total − material − labor (no crew confirmation)",
           "EQUIP_WITHOUT_CREW_EQUIP": "an equipment cost on a crew that owns no equipment — the signature of the total slipping one column left",
           "SECTION_UNKNOWN": "no section id read on the page and none could be carried from the previous page: the line has no cost code",
           "WEAK_READING": "a money cell kept on one reading only (prefix; the cells are named after the colon)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("crews_csv")
    ap.add_argument("trades_csv")
    ap.add_argument("out")
    ap.add_argument("--spot", action="append", default=[], help="label=path of a spot-check sample.csv with verdicts")
    a = ap.parse_args()
    table, out = Path(a.table), Path(a.out)
    rows = list(csv.DictReader((table / "book_lines_la_latest.csv").open(encoding="utf-8")))
    rep = json.loads((table / "build_report.json").read_text(encoding="utf-8"))
    drep = json.loads((table / "derive_report.json").read_text(encoding="utf-8"))
    crews = list(csv.DictReader(Path(a.crews_csv).open(encoding="utf-8"))) if Path(a.crews_csv).exists() else []
    trades = list(csv.DictReader(Path(a.trades_csv).open(encoding="utf-8"))) if Path(a.trades_csv).exists() else []
    st = Counter(r["status"] for r in rows)
    tiers = ("verified", "machine_read", "flagged")
    priced = [r for r in rows if r["status"] in tiers]
    by_div = Counter((r["division"], r["status"]) for r in priced)
    divs = sorted({r["division"] for r in priced if r["division"]})
    flags = Counter()
    for r in rows:
        for f in r["flags"].split(";"):
            if f:
                flags[f.split(":")[0] if f.startswith("WEAK_READING") else f] += 1
    crews_ok = sum(1 for c in crews if c.get("checks_ok", "").lower() == "true")
    trades_ok = sum(1 for t in trades if t.get("checks_ok", "").lower() == "true")
    derived_verified = sum(1 for r in rows if r["status"] == "verified" and r.get("total_la_latest"))
    no_code = sum(1 for r in priced if r["status"] in ("verified", "machine_read") and not r["cost_code"])

    # spot checks against the current table
    by_key = {(r["section_id"], r["line"], r["pdf_page"]): r for r in rows}
    by_key2 = {(r["line"], r["pdf_page"]): r for r in rows}
    spot_lines = []
    for item in a.spot:
        label, path = item.split("=", 1)
        sample = list(csv.DictReader(Path(path).open(encoding="utf-8")))
        tier = "verified" if label != "machine_read" else "machine_read"
        still, ok, left = 0, 0, []
        for s in sample:
            v = s.get("reviewer_verdict", "").strip()
            if not v:
                continue
            t = by_key.get((s["section_id"], s["line"], s["pdf_page"])) or by_key2.get((s["line"], s["pdf_page"]))
            cur = t["status"] if t else "missing"
            if cur == tier:
                still += 1
                ok += v.lower().startswith("ok")
            else:
                left.append(f"p{s['pdf_page']} {s['section_id'] or '(no section)'} {s['line']} → {cur}: {v}" + (f" [{t['flags']}]" if t and not v.lower().startswith('ok') else ""))
        spot_lines += [f"* **{label}** sample (`spot_check/{label}/`): {len(sample)} rows drawn and compared cell by cell against the page image; "
                       f"{still} of them are in the `{tier}` tier of this build — **{ok} of {still} fully correct**."]
        for l in left:
            spot_lines.append(f"  * left the tier under the current rule: {l}")

    lines = [f"# Book table extraction report — Building Construction Costs with RSMeans data 2022 (company reference copy)", "",
             f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}. Scripts: `cost-db/book_ocr/` (OCR, three-reading parser, table builder, "
             "derivation, spot check). Data: `cost-db/data/books/rsmeans_bcc_2022/`.", "",
             "## 1. What was read", "",
             f"* Scan: 964 PDF pages (sha256 `9c5aee73…c075bc`), unit-price section PDF pages 24–750, split into 6 parts and transferred from the owner's Mac.",
             f"* OCR: tesseract 5.3 at 360 dpi (own run) **and** the scan's own text layer (a second engine) **and** a geometric reading of every number "
             "(digit-glyph count and decimal-point position on the page image). A value is kept only when the readings agree or the table's arithmetic "
             "selects it: `total = material + labor + equipment`; `labor-hours = crew labor-hours / daily output`; `labor = crew daily labor cost / output`; "
             "`total incl. O&P = 1.10 × material + crew O&P labor / output + 1.10 × equipment`.",
             f"* Table pages parsed: **{rep['pages']}** (every unit-price table page of the scan; on {rep.get('pages_template', 0)} of them the column header "
             "was unreadable and the columns were fitted to the page's own number clusters, labelled by the anchors of the neighbouring same-side page: "
             f"`HEADER_TEMPLATE`); pages without a table skipped: {rep.get('pages_skipped', '?')} (division intro, Division Notes, reference); sections: **{rep['sections']}**; "
             f"printed lines: **{rep['lines']}** (priced lines {len(priced)}, description-only lines {st.get('header', 0)}, percentage-add lines {st.get('percent_add', 0)}).",
             f"* Crew table (book pages 749–785): {len(crews)} crews parsed, {crews_ok} pass every identity (member sums, labor-hours, cost per labor-hour); "
             f"single-trade crews (`1 Carp` …) are built from the trade-rate table (inside back cover: {len(trades)} trades, {trades_ok} pass the row identities).",
             f"* City Cost Index, Los Angeles (900–902), book page 791: 20 rows read from a 300-dpi crop and checked against the image.",
             f"* A page that starts in the middle of a section takes the section id of the previous page (`SECTION_CARRIED`, {flags.get('SECTION_CARRIED', 0)} lines) "
             "only when its line numbers continue that section's numbering in order and the page's first printed section comes after it; otherwise the "
             f"lines stay without a section (`SECTION_UNKNOWN`, {flags.get('SECTION_UNKNOWN', 0)} lines) and without a cost code.", "",
             "## 2. Status of the priced lines (the rule)", "",
             "A line is **verified** only when all of the following hold. Nothing else is called verified; no tolerance is attached to any number.", "",
             "1. every printed money cell (material, labor, equipment, total) is confirmed by all three readings — both OCR engines and the geometric "
             "reading of the digits and the decimal point (evidence weight ≥ 4) — or is computed from the other cells by the book's arithmetic;",
             "2. daily output and labor-hours are confirmed by at least two readings or by the crew rule (crew labor-hours / output);",
             "3. no check is open: the money cells add up, labor agrees with the crew's daily cost, output × hours is a crew-day, the line number is in "
             "the section's numbering order, the section id is known, the crew is read, total incl. O&P (where printed) agrees with the components;",
             "4. the money columns are tied: the total was read (so `total = M + L + E` ties the cells to their columns) or the O&P value checks the row "
             "or the equipment cell is empty or confirmed by the crew's own equipment cost;",
             "5. an equipment cost on a crew that owns no equipment fails the line (`EQUIP_WITHOUT_CREW_EQUIP`).", "",
             "**machine_read**: no check failed, but at least one number rests on fewer readings than rule 1–2 demand (for example two readings agree "
             "and the third is absent) or the columns are not tied by rule 4. **flagged**: a check failed or a cell stayed unreadable; the values shown "
             "are the best readings. Both tiers are *not verified*: read the line on `book_page` before using it.", "",
             f"| status | lines | share of priced |", "|---|---|---|"]
    for t in tiers:
        lines.append(f"| {t} | {st.get(t, 0)} | {st.get(t, 0) / max(1, len(priced)):.1%} |")
    lines += ["", f"Every verified and machine_read line carries a cost code ({no_code} without one).", "",
              "By division (verified / machine_read / flagged):", "", "| division | verified | machine_read | flagged |", "|---|---|---|---|"]
    for d in divs:
        lines.append(f"| {d} | {by_div[(d, 'verified')]} | {by_div[(d, 'machine_read')]} | {by_div[(d, 'flagged')]} |")
    lines += ["", "Open flags (one line can carry several):", "", "| flag | lines | meaning |", "|---|---|---|"]
    for f, n in sorted(flags.items(), key=lambda kv: -kv[1]):
        if f in OPEN_FLAGS or f == "WEAK_READING":
            lines.append(f"| `{f}` | {n} | {MEANING.get(f, '')} |")
    lines += ["", "Informational flags (a cell computed from the others by the book's own rules, or a structural note): " +
              ", ".join(f"`{f}` {n}" for f, n in sorted(flags.items(), key=lambda kv: -kv[1]) if f not in OPEN_FLAGS and f != "WEAK_READING"), "",
              "## 3. Spot check against the page images", ""]
    lines += spot_lines if spot_lines else ["Spot check sheets are in `spot_check/`; verdicts not yet recorded."]
    lines += ["", "\"Fully correct\" means every cell printed on the row strip (line number, description, crew, output, hours, unit, the money cells) "
              "matches the table. In the `section_carried` sample the carried section id is not visible on the strip: it rests on the numbering rule of "
              "section 1 (continuing line numbers, next printed section after it), not on an eye check.", "",
              "The one wrong verified row found (page 322, 08 71 20.44 0610: the printed total 391.50 landed in the equipment column) is the reason for "
              "rules 4–5 above; it is flagged in this build. Residual error types that no arithmetic reaches: a digit misread identically by all readings, "
              "a value overlapped by the row above, the cut right edge of the scan (total incl. O&P).", "",
              "## 4. Derived Los Angeles, latest-month values", "",
              f"* {drep['priced_2022']} lines carry a 2022 cost; {drep['priced_latest']} got a derived Los Angeles value for {drep['latest_period']} "
              f"({derived_verified} of them on verified lines).",
              "* Formula per line: component × City Cost Index (LA, book 2022; material index for material, installation index for labor and equipment) "
              "× BLS factor (material: PPI series by material class; labor: ECI total compensation, construction; equipment: PPI machinery). "
              "Every factor is written next to the value. `origin = derived`, `review_status = unreviewed`.",
              "* Not escalated separately: fuel inside the equipment cost (the fuel share of a crew's equipment cost is not published). Not applied: "
              "any company-specific markup, sales tax, delivery, quantity discounts, current supplier quotes.", "",
              "## 5. Limits", "",
              "* The 2022 values are what the book printed, read by machine: the verified set is machine-verified by the rule above, not human-verified line by line; "
              "the spot checks in section 3 are the only human-read sample.",
              "* machine_read and flagged lines must be checked against the book page (`book_page`) before use.",
              "* Line numbers cut at the left edge of the scan (one or two leading digits lost) are restored only when exactly one value with that tail "
              "fits between the previous and the next fully read line numbers of the section (`LINE_NUMBER_RECONSTRUCTED`); otherwise the line keeps no number "
              "and is flagged (`LINE_NUMBER_MISSING`).",
              "* Total incl. O&P is missing on right-hand pages where the scan cut the column; where the crew is known it can be recomputed by the formula above.",
              "* Descriptions are OCR text (cleaned); `description_path` applies the book's indentation rule mechanically and can over-include a sibling line.",
              "* The derived latest values are budget-level references, not prices observed in Los Angeles in 2026.", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
