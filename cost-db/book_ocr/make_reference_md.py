#!/usr/bin/env python3
"""Write the estimator-facing reference (for the bid-estimating skill) and the Obsidian note set from the finished table.

  python3 -I make_reference_md.py <table_dir> <factors.csv> <cci.csv> <trade_rates.csv> <crews_totals.csv> <out_dir>

Outputs in <out_dir>:
  claude-estimator-construction.md     the skill reference: how to price a line from the table, with the numbers of this build
  obsidian/Claude Estimator Construction/*.md   the same content as linked Obsidian notes (frontmatter + wikilinks)
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path


def main() -> int:
    table, factors_csv, cci_csv, trades_csv, crews_csv, out = (Path(a) for a in sys.argv[1:7])
    rows = list(csv.DictReader((table / "book_lines_la_latest.csv").open(encoding="utf-8")))
    rep = json.loads((table / "build_report.json").read_text(encoding="utf-8"))
    drep = json.loads((table / "derive_report.json").read_text(encoding="utf-8"))
    factors = list(csv.DictReader(factors_csv.open(encoding="utf-8")))
    cci = list(csv.DictReader(cci_csv.open(encoding="utf-8")))
    trades = list(csv.DictReader(trades_csv.open(encoding="utf-8")))
    crews = list(csv.DictReader(crews_csv.open(encoding="utf-8")))
    st = Counter(r["status"] for r in rows)
    priced = st["verified"] + st["machine_read"] + st["flagged"]
    by_div = defaultdict(lambda: Counter())
    names = {}
    for r in rows:
        if r["division"]:
            by_div[r["division"]][r["status"]] += 1
            names[r["division"]] = r["division_name"]
    latest = drep["latest_period"]
    today = date.today().isoformat()
    fid = {f["series_id"]: f for f in factors}
    ex = next((r for r in rows if r["status"] == "verified" and r["section_id"] == "09 29 10.30" and r.get("total_la_latest")), None) \
        or next((r for r in rows if r["status"] == "verified" and r.get("total_la_latest") and r["labor_2022"] and r["material_2022"]), None)

    def money(v):
        return f"${Decimal(v):,.2f}" if v not in (None, "") else "—"

    # ------------------------------------------------------------------ skill reference
    md = [f"# Claude Estimator Construction — Owl Tower cost table (book-derived), build {today}", "",
          "**What this is.** A machine-read copy of the unit-price section of the company's reference copy of *Building Construction Costs "
          "with RSMeans data 2022* (national bare costs, January 2022), with every line carrying a derived **Los Angeles, "
          f"{latest.replace('M', '-')}** estimate. Use it as the *reference layer* in the estimating sequence of the bid-estimating skill "
          "(step 4, unit pricing): it fills a line when no quote, no company actual and no observed price exists, and it benchmarks "
          "the numbers you do have. It is not a quote and not a substitute for the sub bids the skill requires.", "",
          "## Files", "",
          "| file | content |", "|---|---|",
          "| `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.xlsx` | the table for the office (sheet `lines`, filters on; `sections`; `readme`) |",
          "| `…/book_lines_la_latest.csv` / `.json` | the same table for the software |",
          "| `…/COLUMNS.md` | every column explained |", "| `…/extraction_report.md` | how it was read and checked, counts, limits |",
          "| `…/reference/crews_all_2022.csv`, `trade_rates_2022.csv`, `cci_los_angeles_2022.csv` | crews (labor-hours and daily cost per crew), trade rates, Los Angeles city cost index |",
          "| `cost-db/docs/price_update_factors.md` | the BLS/EIA factors 2022-01 → latest, with sources |", "",
          "## Numbers of this build", "",
          f"* {rep['pages']} table pages (all unit-price table pages of the scan; {rep.get('pages_template', 0)} with an unreadable header read through "
          f"the neighbouring page's column anchors), {rep['sections']} sections, {rep['lines']} printed lines; "
          f"**{priced} priced lines**: **{st['verified']} verified**, {st['machine_read']} machine_read (not verified), {st['flagged']} flagged (not verified), "
          f"{st['percent_add']} percentage-add lines, {st['header']} description-only lines.",
          f"* {drep['priced_latest']} lines carry a derived Los Angeles {latest.replace('M', '-')} value ({drep['verified_latest']} of them on verified lines).",
          f"* Crews: {len(crews)} (incl. {sum(1 for c in crews if c['crew_id'][0].isdigit() or c['crew_id'][0] == '.')} single-trade crews built from the trade-rate table); "
          f"trades: {len(trades)}.",
          "* **verified** means: every printed money cell carries evidence weight ≥ 4 for one value (the geometric reading of digits and decimal point, 3, "
          "plus at least one of the three OCR readings: 360-dpi tesseract, the scan's text layer, 600-dpi tesseract) or is computed by the book's "
          "arithmetic; output/hours confirmed by two readings or the crew rule; no check open; money columns tied; section id known. An unreadable crew "
          "cell is filled only when exactly one crew of the crew table satisfies the line's labor-hours, daily labor cost, equipment presence and O&P at "
          "once (`CREW_FROM_ARITHMETIC`). The spot-check results (rows read by eye against the page image) are in `extraction_report.md`, section 3. "
          "No tolerance is attached to any number: a number is verified or it is not.", "",
          "| division | verified | machine_read | flagged |", "|---|---|---|---|"]
    for d in sorted(by_div):
        md.append(f"| {d} {names[d]} | {by_div[d]['verified']} | {by_div[d]['machine_read']} | {by_div[d]['flagged']} |")
    md += ["", "## How to price a line (the rule)", "",
           "1. Find the line by `cost_code` (`OT-<section digits>-<line>`), by `section_id` + `line`, or by searching `description_path`. "
           "Check `unit` — the book's unit, not necessarily the takeoff unit.",
           "2. Read `status`. **verified** → usable as a reference. **machine_read** and **flagged** → not verified: open `book_page` in the scan and "
           "read the line yourself before using any of its numbers; do not use them with an allowance or a tolerance instead. "
           "**percent_add** → an adjustment in % of another line, not a cost.",
           "3. Take the **2022 national bare** columns when you want the book's own number (`material_2022`, `labor_2022`, `equipment_2022`, "
           "`total_2022`; `total_incl_op_2022` = with the installing contractor's O&P).",
           f"4. Take the **Los Angeles {latest.replace('M', '-')}** columns (`material_la_latest`, `labor_la_latest`, `equipment_la_latest`, `total_la_latest`) "
           "for a current budget-level number: component × City Cost Index (LA, book) × BLS factor of that component. The factors used are "
           "written on the line (`material_factor_id`, `labor_factor`, …). These are *derived* values: `origin = derived`, unreviewed.",
           "5. Replace whatever you have better data for: a supplier quote replaces the material, the company's own crew cost / output replaces "
           "the labor (`labor_hours` × your loaded hourly rate is often the better path), a rental quote replaces the equipment.",
           "6. Add what the book excludes: sales tax on material, delivery, general conditions, contingency, company overhead and profit "
           "(the `total_incl_op_*` columns carry only the *installing contractor's* O&P). Never apply a second location or time factor.", "",
           "## Worked example", ""]
    if ex:
        md += [f"`{ex['cost_code']}` — {ex['description_path']} (book page {ex['book_page']}, unit {ex['unit']}, crew {ex['crew'] or '—'}, "
               f"{ex['daily_output'] or '—'} {ex['unit']}/day, {ex['labor_hours'] or '—'} labor-hours/{ex['unit']})", "",
               "| component | 2022 national | × CCI LA | × BLS factor | LA latest |", "|---|---|---|---|---|",
               f"| material | {money(ex['material_2022'])} | {ex['cci_mat_la_2022'] or '—'} | {ex['material_factor']} ({ex['material_factor_id']}) | {money(ex['material_la_latest'])} |",
               f"| labor | {money(ex['labor_2022'])} | {ex['cci_inst_la_2022'] or '—'} | {ex['labor_factor']} ({ex['labor_factor_id']}) | {money(ex['labor_la_latest'])} |",
               f"| equipment | {money(ex['equipment_2022'])} | {ex['cci_inst_la_2022'] or '—'} | {ex['equipment_factor']} ({ex['equipment_factor_id']}) | {money(ex['equipment_la_latest'])} |",
               f"| **total** | {money(ex['total_2022'])} | | | **{money(ex['total_la_latest'])}** |", ""]
    md += ["## Factors (BLS/EIA, January 2022 → latest)", "", "| series | fits | factor |", "|---|---|---|"]
    for f in factors:
        md.append(f"| `{f['series_id']}` {f['series']} | {f['applies_to']} | **{f['factor']}** |")
    md += ["", "## Los Angeles City Cost Index (book, 2022, 900–902)", "", "| division | mat. | inst. | total |", "|---|---|---|---|"]
    for c in cci:
        md.append(f"| {c['division_code']} {c['division_name']} | {c['mat_index'] or '—'} | {c['inst_index']} | {c['total_index']} |")
    md += ["", "## Trade rates (book, 2022, union averages of 30 cities, $/h incl. fringes; with O&P)", "", "| abbr | trade | base | with O&P |", "|---|---|---|---|"]
    for t in trades:
        if t["abbr"] and not t["abbr"].startswith("*"):
            md.append(f"| {t['abbr']} | {t['trade']} | {t['base_hourly']} | {t['rate_op_hourly']} |")
    md += ["", "## Limits (read before quoting from this table)", "",
           "* Machine-read from a scan; verified means all three readings or the book's arithmetic confirm every number and the columns are tied — "
           "the random spot checks are in `spot_check/` and their results in `extraction_report.md`. machine_read and flagged lines are not cleaned up "
           "and are not verified; no error margin is attached to them or to anything else in the table.",
           "* 2022 national averages of union-wage cities; Los Angeles is applied through the book's own index; time through national BLS indices. "
           "No supplier, no quantity discount, no tax, no delivery, no company markup.",
           "* Equipment includes fuel in the book; fuel is not escalated separately (diesel rose faster than machinery).",
           "* Descriptions are OCR text; `description_path` applies the book's indentation rule mechanically.",
           "* The company's own observed prices, quotes and crew costs in the `costdb` database always outrank this table.", ""]
    out.mkdir(parents=True, exist_ok=True)
    (out / "claude-estimator-construction.md").write_text("\n".join(md), encoding="utf-8")

    # ------------------------------------------------------------------ obsidian notes
    ob = out / "obsidian" / "Claude Estimator Construction"
    ob.mkdir(parents=True, exist_ok=True)
    fm = lambda title, tags, extra="": f"---\ntitle: {title}\ntype: reference\ntags: [{tags}]\nsource: Claude Estimator Construction\nbuild: {today}\n{extra}---\n"
    home = [fm("Claude Estimator Construction", "moc, estimating, cost-data", "aliases: [CEC, Cost table]\n"),
            "# Claude Estimator Construction — Map of Content", "",
            "The company's book-derived unit-cost reference, read by machine from the 2022 cost book and brought to Los Angeles at the latest BLS month. "
            "Built and checked by Claude; the extraction method and the limits are in [[CEC — Method and limits]].", "",
            "## Use", "* [[CEC — How to price a line]] — the rule, with a worked example",
            "* [[CEC — Numbers of this build]] — counts by division, what is verified",
            "* `book_lines_la_latest.xlsx` (in this folder) — the table itself; `COLUMNS.md` — the columns", "",
            "## Reference data", "* [[CEC — Factors 2022 to latest]] — BLS/EIA factors with sources",
            "* [[CEC — Los Angeles City Cost Index 2022]]", "* [[CEC — Trade rates 2022]]", "* [[CEC — Method and limits]]", "",
            "## Where it lives", f"* Repository `owl-tower-os-app`, branch `claude/construction-cost-database-sv4dab`, folder `cost-db/data/books/rsmeans_bcc_2022/`.",
            "* Skill: the same reference is attached to the **bid-estimating** skill as `references/claude-estimator-construction.md`.", ""]
    (ob / "Claude Estimator Construction.md").write_text("\n".join(home), encoding="utf-8")

    def section(title: str, start_marker: str, end_marker: str | None, tags: str) -> None:
        text = "\n".join(md)
        a = text.index(start_marker)
        b = text.index(end_marker) if end_marker else len(text)
        body = text[a:b].strip()
        body = body.replace("## ", "# ", 1)
        (ob / f"{title}.md").write_text(fm(title, tags) + body + "\n\nBack to [[Claude Estimator Construction]].\n", encoding="utf-8")

    section("CEC — How to price a line", "## How to price a line (the rule)", "## Factors (BLS/EIA", "estimating, rule")
    section("CEC — Numbers of this build", "## Numbers of this build", "## How to price a line (the rule)", "estimating, status")
    section("CEC — Factors 2022 to latest", "## Factors (BLS/EIA", "## Los Angeles City Cost Index", "indices, bls")
    section("CEC — Los Angeles City Cost Index 2022", "## Los Angeles City Cost Index", "## Trade rates", "indices, los-angeles")
    section("CEC — Trade rates 2022", "## Trade rates", "## Limits (read before quoting", "labor, rates")
    section("CEC — Method and limits", "## Limits (read before quoting", None, "method, limits")
    print(f"wrote {out / 'claude-estimator-construction.md'} and {len(list(ob.glob('*.md')))} Obsidian notes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
