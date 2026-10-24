#!/usr/bin/env python3
"""Price-update factors from a raw BLS/EIA fetch: index(latest) / index(base month), one line per series.

  python3 -I pipeline/scripts/price_update_factors.py [--raw data/raw_sources/bls_eia_2026-10-24] [--base 2022-01]

Reads the API response and the EIA spreadsheets exactly as fetched (nothing is typed in by hand) and writes
  data/derived/price_update_factors_<base>_<latest>.csv   one row per series: base value, latest value, factor, status of the latest point
  docs/price_update_factors.md                            the same table with the sources and the rules for applying the factors
A factor is a ratio of two published index values; it is not a price. Which series applies to which cost component is a
judgement that stays visible in the 'applies_to' column, so the reader can disagree with it.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parents[2]

# series id -> (short name, what it is a reasonable proxy for in a unit-cost book; blank = reference only)
APPLIES = {
    "WPUIP2300001": ("Inputs to construction industries, goods (PPI)", "material cost, default when no commodity series fits"),
    "WPU1022": ("Primary nonferrous metals (PPI)", "copper/aluminum content of wire, pipe, flashing: upper bound (raw metal, not finished product)"),
    "WPU1025": ("Nonferrous mill shapes (PPI)", "aluminum/copper products: sheet, extrusions, tube, wire rod"),
    "WPU1017": ("Steel mill products (PPI)", "rebar, structural steel, studs, decking"),
    "WPU081": ("Lumber (PPI)", "lumber, all"),
    "WPU0811": ("Softwood lumber (PPI)", "framing lumber"),
    "WPU133": ("Concrete products (PPI)", "precast, block, pipe"),
    "WPU1333": ("Ready-mix concrete (PPI)", "ready-mix concrete"),
    "WPU1332": ("Concrete pipe (PPI)", "concrete pipe"),
    "WPU137": ("Gypsum products (PPI)", "drywall, plaster"),
    "WPU0622": ("Paint materials (PPI)", "paint and coatings"),
    "WPU114": ("General purpose machinery and equipment (PPI)", "equipment ownership/rental component (not fuel)"),
    "WPU057303": ("No. 2 diesel fuel (PPI)", "equipment fuel component (producer price)"),
    "WPU0573": ("Light fuel oils (PPI)", "reference"),
    "CIU2012300000000I": ("ECI total compensation, private construction (NSA, current dollar)", "labor cost incl. benefits"),
    "CIU2022300000000I": ("ECI wages and salaries, private construction (NSA, current dollar)", "bare wages"),
    "CUUR0000SA0": ("CPI-U all items, U.S. city average (NSA)", "reference only: consumer prices, not construction"),
    "CUURS49ASA0": ("CPI-U all items, Los Angeles-Long Beach-Anaheim (NSA)", "reference only"),
}
EIA = {
    "eia_diesel_us_monthly.xls": ("EIA U.S. No. 2 diesel retail price, $/gal, monthly", "equipment fuel component (retail, national)"),
    "eia_diesel_california_monthly.xls": ("EIA California No. 2 diesel retail price, $/gal, monthly", "equipment fuel component (retail, California)"),
}


def q(x: Decimal, places: str = "0.0001") -> Decimal:
    return x.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def bls_rows(raw: Path, base: str) -> list[dict]:
    d = json.loads((raw / "bls_series_2021_2026.json").read_text(encoding="utf-8"))
    if d.get("status") != "REQUEST_SUCCEEDED":
        raise SystemExit(f"BLS response status {d.get('status')}: {d.get('message')}")
    by, bm = base.split("-")
    out = []
    for s in d["Results"]["series"]:
        sid = s["seriesID"]
        pts = {(p["year"], p["period"]): p for p in s["data"]}
        quarterly = any(k[1].startswith("Q") for k in pts)
        bkey = (by, f"Q0{(int(bm) - 1) // 3 + 1}" if quarterly else f"M{int(bm):02d}")
        if bkey not in pts:
            raise SystemExit(f"{sid}: no value for base period {bkey}")
        latest = s["data"][0]                                              # the API returns newest first
        notes = "; ".join(f["text"] for f in latest.get("footnotes", []) if f and f.get("text"))
        name, applies = APPLIES.get(sid, (sid, ""))
        bval, lval = Decimal(pts[bkey]["value"]), Decimal(latest["value"])
        out.append({"series_id": sid, "series": name, "applies_to": applies,
                    "base_period": f"{bkey[0]}-{bkey[1]}", "base_value": str(bval),
                    "latest_period": f"{latest['year']}-{latest['period']}", "latest_value": str(lval),
                    "factor": str(q(lval / bval)), "latest_status": "preliminary" if "Preliminary" in notes else "final",
                    "source": "BLS API v1, fetched 2026-10-24 (data/raw_sources/bls_eia_2026-10-24/bls_series_2021_2026.json)"})
    return out


def eia_rows(raw: Path, base: str) -> list[dict]:
    out = []
    for fname, (name, applies) in EIA.items():
        wb = xlrd.open_workbook(raw / fname)
        sh = wb.sheet_by_name("Data 1")
        vals = {}
        for r in range(3, sh.nrows):
            dv, pv = sh.cell_value(r, 0), sh.cell_value(r, 1)
            if isinstance(dv, float) and pv not in ("", None):
                vals[xlrd.xldate_as_datetime(dv, wb.datemode).strftime("%Y-%m")] = Decimal(str(pv))
        if base not in vals:
            raise SystemExit(f"{fname}: no value for {base}")
        last = max(vals)
        out.append({"series_id": fname, "series": name, "applies_to": applies, "base_period": base, "base_value": str(vals[base]),
                    "latest_period": last, "latest_value": str(vals[last]), "factor": str(q(vals[last] / vals[base])),
                    "latest_status": "as published (EIA monthly average)",
                    "source": f"EIA hist_xls, fetched 2026-10-24 (data/raw_sources/bls_eia_2026-10-24/{fname})"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw_sources" / "bls_eia_2026-10-24"))
    ap.add_argument("--base", default="2022-01")
    a = ap.parse_args()
    raw = Path(a.raw)
    rows = bls_rows(raw, a.base) + eia_rows(raw, a.base)
    latest = max(r["latest_period"] for r in rows if r["latest_period"].startswith("20") and "M" in r["latest_period"])
    cols = ["series_id", "series", "applies_to", "base_period", "base_value", "latest_period", "latest_value", "factor", "latest_status", "source"]
    import csv
    out_csv = ROOT / "data" / "derived" / f"price_update_factors_{a.base}_{latest.replace('M', '')}.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    md = [f"# Price-update factors, {a.base} → latest published ({latest.replace('M', '-')})", "",
          f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')} by `pipeline/scripts/price_update_factors.py` from the raw fetch in "
          "`data/raw_sources/bls_eia_2026-10-24/` (BLS API v1 response and EIA spreadsheets exactly as downloaded on 2026-10-24; "
          "`fetch_log.txt` holds the commands and SHA-256 of every file; `titles/series_titles.txt` holds the official series titles).", "",
          "**What a factor is.** `factor = index(latest) / index(base)`. It rescales a cost that was valid in the base month to the latest month "
          "for the thing the series measures. It is not a price, it is national (except the Los Angeles CPI and the California diesel price) and it "
          "says nothing about one supplier's quote. Apply at most one factor per cost component; never a material factor on a labor cost, never two "
          "factors on the same number, never a factor on a quote you already have for today.", "",
          "**How to apply to a unit cost from a 2022 book (national, bare costs as of January 2022):**", "",
          "* material cost × the commodity series that fits the item (steel, lumber, concrete, gypsum, paint, nonferrous metals); "
          "`WPUIP2300001` (inputs to construction, goods) when none fits;",
          "* labor cost × `CIU2012300000000I` (total compensation) when the book figure includes employer-paid benefits, else `CIU2022300000000I` (wages);",
          "* equipment cost: the ownership/rental part × `WPU114`, the fuel part × diesel (`WPU057303` producer price, or the EIA retail series);",
          "* then the location adjustment for Los Angeles from the book's own city cost index (material and installation separately) — not the CPI;",
          "* the CPI rows are reference only: consumer prices are not construction costs.", "",
          "The latest monthly PPI points are **preliminary** (BLS revises up to four months after first publication); ECI is quarterly, latest 2026-Q2.", "",
          "| series id | series | fits | base | base value | latest | latest value | **factor** | latest point |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| `{r['series_id']}` | {r['series']} | {r['applies_to']} | {r['base_period']} | {r['base_value']} | {r['latest_period']} | "
                  f"{r['latest_value']} | **{r['factor']}** | {r['latest_status']} |")
    md += ["", f"CSV: `{out_csv.relative_to(ROOT)}`.", ""]
    (ROOT / "docs" / "price_update_factors.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {out_csv.relative_to(ROOT)} and docs/price_update_factors.md ({len(rows)} series)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
