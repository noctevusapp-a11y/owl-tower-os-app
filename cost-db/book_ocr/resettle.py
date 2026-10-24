#!/usr/bin/env python3
"""Re-run the settling logic on already parsed pages from the stored raw candidates (no OCR, no rendering).

  python3 -I resettle.py <parsed_dir> <out_dir> --crews crews.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_unit_prices import NUM_COLS, settle  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parsed_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--crews", default=None)
    a = ap.parse_args()
    crews = {}
    if a.crews:
        with open(a.crews, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                crews[r["crew_id"]] = {k: (float(v) if v not in ("", None) else None) for k, v in r.items() if k not in ("crew_id", "notes", "checks_ok", "page_pdf")}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(Path(a.parsed_dir).glob("p*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for ln in d.get("lines", []):
            raw = ln.get("raw", {})
            cands = {k: [(Decimal(v), how, src) for v, how, src in raw.get(k, [])] for k in NUM_COLS}
            keep = [f for f in ln["flags"] if f in ("CREW_UNREAD", "CREW_UNKNOWN", "PERCENT_ADD", "LINE_NUMBER_PARTIAL", "LINE_NUMBER_MISSING")]
            crew_row = crews.get(ln["crew"]) if ln.get("crew") else None
            vals, confs, flags = settle(cands, crew_row)
            if ln.get("percent"):
                flags = [f for f in flags if f not in ("MONEY_UNSETTLED", "TOTAL_DERIVED_FROM_SUM")]
            for k in NUM_COLS:
                ln[k] = str(vals[k]) if vals[k] is not None else None
            ln["conf"] = {k: confs[k] for k in NUM_COLS if confs[k] is not None}
            ln["flags"] = list(dict.fromkeys(keep + flags))
            n += 1
        (out / p.name).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print(f"re-settled {n} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
