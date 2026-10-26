#!/usr/bin/env python3
"""Copy the finished book table into the repository data folder and write the XLSX for the office.

  python3 -I package.py <table_dir> <dest_dir> [--spot label=spot_dir ...]

Each --spot folder (sample.csv + sheet_*.png from spot_check.py, verdicts filled) is copied to <dest_dir>/spot_check/<label>/.
The spot_check folder is regenerated: what was there before is removed.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

README = (
    "Owl Tower book table: 2022 national bare costs read from the company's reference copy of the 2022 cost book, with derived Los Angeles latest-month estimates.",
    "status = verified: every printed number confirmed by all three readings (two OCR engines + the geometric reading) or computed by the book's arithmetic, "
    "no check open, money columns tied. machine_read: no check failed but a number rests on fewer readings. flagged: a check failed or a cell is unreadable.",
    "Only verified lines are verified. machine_read and flagged lines: read the line on book_page before use. No tolerance is attached to any number.",
    "*_la_latest = component x City Cost Index (LA, 2022) x BLS factor per component; derived, unreviewed. Not quotes, not observed 2026 prices.",
    "Column dictionary: COLUMNS.md. Report: extraction_report.md. Spot checks: spot_check/.",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("dest")
    ap.add_argument("--spot", action="append", default=[], help="label=directory of a spot-check sample")
    a = ap.parse_args()
    table, dest = Path(a.table), Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("book_lines_la_latest.csv", "book_lines_la_latest.json", "book_sections.csv", "build_report.json", "derive_report.json"):
        shutil.copy(table / name, dest / name)
    spot_root = dest / "spot_check"
    if spot_root.exists():
        shutil.rmtree(spot_root)
    for item in a.spot:
        label, src = item.split("=", 1)
        (spot_root / label).mkdir(parents=True, exist_ok=True)
        for p in Path(src).glob("*"):
            if p.is_file():
                shutil.copy(p, spot_root / label / p.name)
    rows = list(csv.DictReader((table / "book_lines_la_latest.csv").open(encoding="utf-8")))
    wb = Workbook()
    ws = wb.active
    ws.title = "lines"
    cols = ["cost_code", "division", "division_name", "section_id", "section_title", "line", "description", "description_path", "unit", "crew",
            "daily_output", "labor_hours", "material_2022", "labor_2022", "equipment_2022", "total_2022", "total_incl_op_2022",
            "material_add_pct", "labor_add_pct", "cci_row", "material_factor_id", "material_factor", "labor_factor", "equipment_factor",
            "material_la_latest", "labor_la_latest", "equipment_la_latest", "total_la_latest", "total_incl_op_la_latest", "latest_period",
            "status", "flags", "book_page", "ref_line"]
    ws.append(cols)
    num = {"daily_output", "labor_hours", "material_2022", "labor_2022", "equipment_2022", "total_2022", "total_incl_op_2022", "material_factor",
           "labor_factor", "equipment_factor", "material_la_latest", "labor_la_latest", "equipment_la_latest", "total_la_latest", "total_incl_op_la_latest",
           "book_page", "material_add_pct", "labor_add_pct"}
    for r in rows:
        out = []
        for c in cols:
            v = r.get(c)
            if v in (None, ""):
                out.append(None)
            elif c in num:
                try:
                    out.append(float(v))
                except ValueError:
                    out.append(v)
            else:
                out.append(v)
        ws.append(out)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(rows) + 1}"
    widths = {"description": 50, "description_path": 70, "section_title": 30, "flags": 30, "cost_code": 22, "division_name": 26}
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 12)
    ws2 = wb.create_sheet("sections")
    with (table / "book_sections.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            ws2.append(row)
    ws3 = wb.create_sheet("readme")
    for line in README:
        ws3.append([line])
    wb.save(dest / "book_lines_la_latest.xlsx")
    rep = json.loads((table / "build_report.json").read_text(encoding="utf-8"))
    print(f"packaged {len(rows)} rows; verified {rep.get('verified')} machine_read {rep.get('machine_read')} flagged {rep.get('flagged')} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
