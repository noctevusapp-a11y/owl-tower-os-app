#!/usr/bin/env python3
"""Parse a BLS OEWS table (CSV or XLSX from the OEWS download pages) into labor_rates rows.

UNTESTED AGAINST A REAL OEWS FILE (bls.gov blocked in the build sandbox). Column names are matched
case-insensitively and the parser FAILS LOUDLY when a required column is missing rather than guessing.
Expected columns (names as recalled from the OEWS data layout; research agent A1 could not confirm them):
  AREA, AREA_TITLE, OCC_CODE, OCC_TITLE, H_MEAN, H_MEDIAN   (optionally H_PCT10..H_PCT90, TOT_EMP, O_GROUP)

Rules:
  * wages are HOURLY MEAN / MEDIAN excluding employer-paid benefits (rate_type=stat_wage, includes_fringe=false)
  * '*' (not available) and '#' (wage at or above the top-code) are NOT stored as numbers — a censored value is not a value
  * only occupations mapped through trades.soc_code and areas mapped through area_map are imported
  * each row keeps file name, row number and a JSON excerpt of the source row as evidence
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb.ids import make_id  # noqa: E402

REQUIRED = {"AREA", "AREA_TITLE", "OCC_CODE", "H_MEAN", "H_MEDIAN"}
STATS = {"H_MEAN": "mean", "H_MEDIAN": "median", "H_PCT10": "p10", "H_PCT25": "p25", "H_PCT75": "p75", "H_PCT90": "p90"}


class OewsError(RuntimeError):
    pass


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as fh:
            return [{(k or "").strip().upper(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        header = [str(h).strip().upper() if h is not None else "" for h in next(it)]
        return [{header[i]: ("" if v is None else str(v).strip()) for i, v in enumerate(row)} for row in it]
    raise OewsError(f"unsupported file type {path.suffix}")


def _wage(v: str) -> Optional[Decimal]:
    if v in ("", "*", "**", "#", "-"):
        return None
    try:
        d = Decimal(v.replace(",", "").replace("$", ""))
    except InvalidOperation:
        return None
    return d if d > 0 else None


def parse_oews(rows: list[dict], trade_by_soc: dict[str, str], region_by_area: dict[str, str], source_id: str,
               reference_period: date, file_name: str, sha256: Optional[str], retrieved_at: str,
               statistics: Iterable[str] = ("H_MEAN", "H_MEDIAN")) -> tuple[list[dict], list[str]]:
    if not rows:
        raise OewsError("no rows")
    missing = REQUIRED - set(rows[0].keys())
    if missing:
        raise OewsError(f"required column(s) missing: {sorted(missing)}; refusing to guess a layout")
    out, notes = [], []
    for i, r in enumerate(rows, start=2):
        trade = trade_by_soc.get(r["OCC_CODE"])
        region = region_by_area.get(r["AREA"])
        if trade is None or region is None:
            continue
        for col in statistics:
            if col not in r:
                continue
            w = _wage(r[col])
            if w is None:
                notes.append(f"row {i} {r['OCC_CODE']} {r['AREA_TITLE']} {col}: '{r[col]}' not stored (suppressed/censored)")
                continue
            excerpt = json.dumps({k: r[k] for k in ("AREA", "AREA_TITLE", "OCC_CODE", "OCC_TITLE", col) if k in r}, sort_keys=True)
            out.append({
                "labor_rate_id": make_id("LRT", "oews", source_id, region, trade, STATS[col], reference_period.isoformat()),
                "rate_type": "stat_wage", "trade_code": trade,
                "classification_raw": f"{r.get('OCC_TITLE', r['OCC_CODE'])} ({r['AREA_TITLE']})", "soc_code": r["OCC_CODE"],
                "statistic": STATS[col], "region_id": region, "base_wage_hr": w, "fringe_hr": None, "fringe_breakdown": None,
                "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None, "total_hr": None,
                "includes_fringe": False, "includes_payroll_taxes": False, "includes_workers_comp": False,
                "wage_basis": "straight_time", "project_type": "n/a", "use_context": "statistical_reference", "apprentice": False,
                "determination_ref": None, "effective_from": reference_period, "effective_to": None, "retrieved_at": retrieved_at,
                "derived_from": None, "calc_run_id": None, "source_id": source_id,
                "source_locator": f"{file_name}, data row {i}", "evidence_excerpt": excerpt, "raw_file_sha256": sha256,
                "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "created_at": None,
                "notes": "OEWS wages exclude employer-paid benefits, overtime, shift differentials and nonproduction bonuses."})
    return out, notes


if __name__ == "__main__":
    print(__doc__)
