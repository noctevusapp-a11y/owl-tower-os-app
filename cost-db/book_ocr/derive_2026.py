#!/usr/bin/env python3
"""Bring the 2022 national bare costs of the book table to Los Angeles, latest published month, one factor per component.

  python3 -I derive_2026.py <book_lines.csv> <factors.csv> <cci_los_angeles.csv> <out_dir>

For every line:
  material_la_latest  = material_2022 x CCI_mat(division group)/100 x PPI factor of the material class
  labor_la_latest     = labor_2022    x CCI_inst(division group)/100 x ECI total-compensation factor (construction)
  equipment_la_latest = equipment_2022 x CCI_inst(division group)/100 x PPI machinery factor
  total_la_latest     = the sum of the three
  total_incl_op_la_latest = total_la_latest x (total_incl_op_2022 / total_2022) when the book printed both

Every factor used is written next to the result (columns *_factor_id / *_factor), so a reader can disagree with the
mapping. The location index (City Cost Index for Los Angeles, from the book) is applied once, before the time factors; the time
factors are national (BLS). The material class is chosen by division/section and by words in the description (copper, aluminum,
duct, rebar ...): a judgement, listed in MATERIAL_CLASS below. The equipment factor is the machinery index only - the book's
equipment cost includes fuel, whose share is not published, so fuel is not escalated separately (diesel rose faster).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

Q = Decimal("0.01")

# (regex on section id, regex on description path) -> material series. First match wins. Order matters.
MATERIAL_CLASS = [
    (r"^03 (30|31|35|37|39)", None, "WPU1333"),                        # cast-in-place concrete: ready-mix
    (r"^03 (11|15)", None, "WPU081"),                                   # formwork: lumber and plywood
    (r"^03 (21|22|23|24)", None, "WPU1017"),                            # reinforcing: steel mill products
    (r"^03 (41|45|47|48)", None, "WPU133"),                             # precast: concrete products
    (r"^04", None, "WPU133"),                                           # masonry units: concrete products (block) - brick not separately fetched
    (r"^05", None, "WPU1017"),                                          # structural/misc. metals: steel mill products
    (r"^06 (11|13|15|17|18)", None, "WPU0811"),                         # wood framing: softwood lumber
    (r"^06 16", None, "WPU081"),                                        # sheathing: lumber (plywood/OSB not separately fetched)
    (r"^08 (41|43|44|51|63)", None, "WPU1025"),                         # aluminum entrances, storefronts, curtain wall, windows: nonferrous mill shapes
    (r"^09 (21|22|23|24|26|28|29)", None, "WPU137"),                    # plaster and gypsum board
    (r"^09 9", None, "WPU0622"),                                        # paints and coatings
    (r"^22", r"copper|brass|bronze", "WPU1025"),                         # copper tube, brass valves
    (r"^22", r"cast iron|steel|black iron|galvanized", "WPU1017"),
    (r"^23", r"duct|sheet metal|galvanized", "WPU1017"),                 # ductwork: galvanized sheet is a steel mill product
    (r"^23", r"copper", "WPU1025"),
    (r"^26", r"copper|aluminum|wire|cable|bus", "WPU1025"),               # conductors and bus: nonferrous mill shapes
    (r"^26", r"conduit|emt|rigid|steel|strut|channel", "WPU1017"),
    (r"^33", r"concrete pipe|rcp", "WPU1332"),
    (r"^33", r"concrete", "WPU133"),
    (r"^(31|32|33)", r"steel|rebar|pipe pile|sheet pil", "WPU1017"),
    (r".", None, "WPUIP2300001"),                                       # everything else: inputs to construction industries, goods
]
LABOR_SERIES = "CIU2012300000000I"          # ECI total compensation, private construction (the book's base rates include fringes)
EQUIP_SERIES = "WPU114"                     # general purpose machinery and equipment (fuel share not published: not separately escalated)

# section -> City Cost Index row of the book (Los Angeles column)
def cci_row(section_id: str) -> str:
    d, s = section_id[:2], section_id[3:5]
    if d == "01":
        return "015433" if section_id.startswith("01 54") else "MF2018"
    if d == "02":
        return "0241, 31-34" if s == "41" else "MF2018"
    if d == "03":
        return {"11": "0310", "15": "0310", "21": "0320", "22": "0320", "23": "0320", "24": "0320", "30": "0330", "31": "0330", "35": "0330", "37": "0330", "39": "0330"}.get(s, "03")
    if d in ("04", "05", "06", "07", "08"):
        return d
    if d == "09":
        if s in ("21", "22", "23", "24", "25", "26", "28", "29"):
            return "0920"
        if s in ("51", "53", "54", "56", "57", "58", "80", "81", "82", "83", "84"):
            return "0950, 0980"
        if s.startswith("6"):
            return "0960"
        if s.startswith("7") or s.startswith("9"):
            return "0970, 0990"
        return "09"
    if d in ("10", "11", "12", "13", "14", "25", "28", "41", "43", "44", "46"):
        return "COVERS"
    if d in ("21", "22", "23"):
        return "21, 22, 23"
    if d in ("26", "27") or section_id.startswith("33 7"):
        return "26, 27, 3370"
    if d in ("31", "32", "33", "34"):
        return "0241, 31-34"
    return "MF2018"


def material_series(section_id: str, path: str) -> str:
    low = (path or "").lower()
    for sec_re, desc_re, series in MATERIAL_CLASS:
        if re.match(sec_re, section_id) and (desc_re is None or re.search(desc_re, low)):
            return series
    return "WPUIP2300001"


def d(x):
    return Decimal(x) if x not in (None, "") else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines_csv")
    ap.add_argument("factors_csv")
    ap.add_argument("cci_csv")
    ap.add_argument("out_dir")
    a = ap.parse_args()
    factors = {}
    with open(a.factors_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            factors[r["series_id"]] = r
    cci = {}
    with open(a.cci_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cci[r["division_code"]] = r
    latest = factors[LABOR_SERIES]["latest_period"]
    rows_out = []
    counts = {"priced_2022": 0, "priced_latest": 0, "verified_latest": 0}
    with open(a.lines_csv, encoding="utf-8") as f:
        src = list(csv.DictReader(f))
    for r in src:
        o = dict(r)
        sec = r["section_id"] or ""
        m, l, e = d(r["material_2022"]), d(r["labor_2022"]), d(r["equipment_2022"])
        if not sec or (m is None and l is None and e is None):
            rows_out.append(o)
            continue
        counts["priced_2022"] += 1
        row = cci.get(cci_row(sec))
        ms = material_series(sec, r["description_path"])
        fm, fl, fe = Decimal(factors[ms]["factor"]), Decimal(factors[LABOR_SERIES]["factor"]), Decimal(factors[EQUIP_SERIES]["factor"])
        cm = Decimal(row["mat_index"]) / 100 if row and row["mat_index"] else None
        ci = Decimal(row["inst_index"]) / 100 if row and row["inst_index"] else None
        o.update({"cci_row": row["division_code"] if row else None, "cci_mat_la_2022": str(cm) if cm else None, "cci_inst_la_2022": str(ci) if ci else None,
                  "material_factor_id": ms, "material_factor": str(fm), "labor_factor_id": LABOR_SERIES, "labor_factor": str(fl),
                  "equipment_factor_id": EQUIP_SERIES, "equipment_factor": str(fe), "latest_period": latest})
        ml = (m * cm * fm).quantize(Q, rounding=ROUND_HALF_UP) if m is not None and cm is not None else None
        ll = (l * ci * fl).quantize(Q, rounding=ROUND_HALF_UP) if l is not None and ci is not None else None
        el = (e * ci * fe).quantize(Q, rounding=ROUND_HALF_UP) if e is not None and ci is not None else None
        parts = [x for x in (ml, ll, el) if x is not None]
        missing = (m is not None and ml is None) or (l is not None and ll is None) or (e is not None and el is None)
        tl = sum(parts) if parts and not missing else None
        t22, top22 = d(r["total_2022"]), d(r["total_incl_op_2022"])
        topl = (tl * top22 / t22).quantize(Q, rounding=ROUND_HALF_UP) if tl is not None and t22 and top22 else None
        o.update({"material_la_latest": str(ml) if ml is not None else None, "labor_la_latest": str(ll) if ll is not None else None,
                  "equipment_la_latest": str(el) if el is not None else None, "total_la_latest": str(tl) if tl is not None else None,
                  "total_incl_op_la_latest": str(topl) if topl is not None else None,
                  "latest_basis": "2022 national bare cost x LA city cost index (book) x BLS factor per component; origin=derived, unreviewed"})
        if tl is not None:
            counts["priced_latest"] += 1
            if r["status"] == "verified":
                counts["verified_latest"] += 1
        rows_out.append(o)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cols = list(rows_out[0].keys())
    for r in rows_out:
        for k in r:
            if k not in cols:
                cols.append(k)
    for r in rows_out:
        for k in cols:
            r.setdefault(k, None)
    with (out / "book_lines_la_latest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows_out)
    (out / "book_lines_la_latest.json").write_text(json.dumps(rows_out, ensure_ascii=False), encoding="utf-8")
    (out / "derive_report.json").write_text(json.dumps({**counts, "latest_period": latest, "labor_series": LABOR_SERIES, "equipment_series": EQUIP_SERIES,
                                                        "material_classes": [(a_, b_, c_) for a_, b_, c_ in MATERIAL_CLASS]}, indent=1), encoding="utf-8")
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
