#!/usr/bin/env python3
"""Write filtered copies of the table for targeted spot checks (spot_check.py samples from a lines CSV).

  python3 -I sample_filters.py <table_dir> <parsed_dir> <out_dir>

Outputs in <out_dir>:
  template_verified.csv      verified rows of pages whose header was unreadable (HEADER_TEMPLATE)
  whole_hours_verified.csv   verified rows whose labor-hours are printed without decimals (2, 8, 16)
  short_tail_lines.csv       rows whose line number was restored from a two-digit tail (any status)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def main() -> int:
    table, parsed, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((table / "book_lines_la_latest.csv").open(encoding="utf-8")))
    cols = list(rows[0].keys())
    # original (pre-reconstruction) line tokens per page, in reading order, to find the two-digit tails
    short: set[tuple[str, int]] = set()
    for p in sorted(parsed.glob("p*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if not d.get("header_found"):
            continue
        for i, ln in enumerate(d["lines"]):
            if ln.get("line_partial") and ln.get("line") and len(ln["line"]) == 2:
                short.add((str(d["pdf_page"]), i))
    by_page_idx: dict[str, int] = {}
    sel = {"template_verified": [], "whole_hours_verified": [], "short_tail_lines": [], "crew_arithmetic_verified": [], "slip_moved": []}
    for r in rows:
        idx = by_page_idx.get(r["pdf_page"], 0)
        by_page_idx[r["pdf_page"]] = idx + 1
        flags = r["flags"].split(";")
        if r["status"] == "verified" and "HEADER_TEMPLATE" in flags:
            sel["template_verified"].append(r)
        if r["status"] == "verified" and r["labor_hours"] and "." not in r["labor_hours"]:
            sel["whole_hours_verified"].append(r)
        if (r["pdf_page"], idx) in short and "LINE_NUMBER_RECONSTRUCTED" in flags:
            sel["short_tail_lines"].append(r)
        if r["status"] == "verified" and "CREW_FROM_ARITHMETIC" in flags:
            sel["crew_arithmetic_verified"].append(r)
        if "COLUMN_SLIP_MOVED" in flags:
            sel["slip_moved"].append(r)
    for name, rs in sel.items():
        with (out / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rs)
        print(f"{name}: {len(rs)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
