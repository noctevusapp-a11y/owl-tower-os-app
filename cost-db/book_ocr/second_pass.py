#!/usr/bin/env python3
"""Second pass over parsed pages: resolve open lines by the book's own arithmetic, then re-settle.

  python3 -I second_pass.py <parsed_dir> <out_dir> --crews crews_all.csv [--extra extra_candidates_dir]

1. Crew from arithmetic. A line whose crew cell is unreadable (or names an unknown crew) gets the crew that is the ONLY one
   in the crew table satisfying both identities of the book at once:
       daily output x labor-hours = crew labor-hours per day        (hours are printed to 3 decimals)
       labor cost x daily output  = crew bare daily labor cost      (labor is printed on the book's rounding grid)
   Both the output/hours pair and the labor cost must already be settled (two readings or the arithmetic). When several
   crews fit, the OCR text of the crew cell decides only if it matches exactly one of them within one edit; otherwise the
   line keeps CREW_UNREAD. Flag: CREW_FROM_ARITHMETIC.
2. Column slip. When the crew owns no equipment, nothing was read under Total and something was read under Equipment, the
   Equipment reading is the printed total that slipped one column (the right edge of the scan): its candidates move to Total
   and the sum check decides (M + L = T). Flag: COLUMN_SLIP_MOVED.
3. Extra candidates (optional): per page JSON {"<line index>": {"<col>": [[value, how, src], ...]}} from another reading
   are appended to the stored raw candidates before settling.
4. Re-settle every line from its (updated) raw candidates with the (updated) crew.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_unit_prices import NUM_COLS, settle, weights, rstep, book_round, normalise_unit, _lev  # noqa: E402


def strong_value(cands: list, min_w: float = 2.0):
    w = weights(cands)
    good = sorted(((ww, v) for v, ww in w.items() if ww >= min_w), reverse=True)
    if good and (len(good) == 1 or good[0][0] > good[1][0]):
        return good[0][1]
    return None


def identify_crew(ln: dict, cands: dict, crews: dict, known_ids: list[str], extra_text: str | None = None) -> tuple[str | None, str]:
    """The unique crew consistent with the line's settled output, hours and labor cost; '' when none or not unique."""
    out = Decimal(ln["output"]) if ln.get("output") else None
    hrs = Decimal(ln["hours"]) if ln.get("hours") else None
    lab = Decimal(ln["labor"]) if ln.get("labor") else None
    conf = ln.get("conf", {})
    # the pair must be settled on its own (two readings each, or the 4k crew-day rule chose it); labor by two readings
    if out is None or hrs is None or lab is None or out <= 0:
        return None, "missing"
    if (conf.get("output") or 0) < 2.0 or (conf.get("hours") or 0) < 2.0 or (conf.get("labor") or 0) < 2.0:
        return None, "weak"
    lh_obs = out * hrs
    daily_obs = lab * out
    tol_lh = out * Decimal("0.0005") + Decimal("0.02")
    tol_daily = out * rstep(lab) / 2 + Decimal("0.011")
    equip = Decimal(ln["equipment"]) if ln.get("equipment") else None
    mat = Decimal(ln["material"]) if ln.get("material") else Decimal(0)
    top = Decimal(ln["total_op"]) if ln.get("total_op") and (conf.get("total_op") or 0) >= 2.0 else None
    fits = []
    for cid, c in crews.items():
        lh = c.get("labor_hours_per_day")
        dl = c.get("bare_labor_daily")
        if lh is None or dl is None:
            continue
        if abs(lh_obs - Decimal(str(lh))) > tol_lh or abs(daily_obs - Decimal(str(dl))) > tol_daily:
            continue
        # the book prints an equipment cost exactly when the crew owns equipment
        if ((c.get("bare_equip_daily") or 0) > 0) != (equip is not None):
            continue
        # total incl. O&P = 1.10 x material + crew O&P labor / output + 1.10 x equipment, on the book's rounding grid
        if top is not None and c.get("op_labor_daily") is not None:
            exp = Decimal("1.10") * mat + Decimal(str(c["op_labor_daily"])) / out + Decimal("1.10") * (equip or Decimal(0))
            if abs(exp - top) > rstep(top) / 2 + Decimal("0.011") + top * Decimal("0.002"):
                continue
        fits.append(cid)
    if len(fits) == 1:
        return fits[0], "unique"
    if len(fits) > 1:
        for txt_src, how in ((ln.get("crew_raw"), "text"), (extra_text, "text")):
            if not txt_src:
                continue
            txt = re.sub(r"[^A-Za-z0-9-]", "", txt_src).lower()
            close = [cid for cid in fits if _lev(txt, cid.replace(" ", "").lower()) <= 1]
            if len(close) == 1:
                return close[0], how
    return None, "ambiguous" if fits else "none"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parsed_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--crews", required=True)
    ap.add_argument("--extra", default=None)
    a = ap.parse_args()
    crews = {}
    with open(a.crews, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            crews[r["crew_id"]] = {k: (float(v) if v not in ("", None) else None) for k, v in r.items()
                                   if k not in ("crew_id", "notes", "checks_ok", "page_pdf")}
    known_ids = list(crews)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stats = {"lines": 0, "crew_found": 0, "crew_found_by_text": 0, "crew_ambiguous": 0, "slip_moved": 0, "extra_lines": 0,
             "open_before": 0, "open_after": 0}
    OPEN = {"MONEY_UNSETTLED", "MONEY_AMBIGUOUS", "OUTPUT_HOURS_UNSETTLED", "OUTPUT_HOURS_AMBIGUOUS", "LABOR_CREW_MISMATCH", "CREW_UNREAD",
            "OP_MISMATCH", "EQUIPMENT_DERIVED_FROM_SUM"}
    for p in sorted(Path(a.parsed_dir).glob("p*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        extra = {}
        if a.extra and (Path(a.extra) / p.name).exists():
            extra = json.loads((Path(a.extra) / p.name).read_text(encoding="utf-8"))
        for i, ln in enumerate(d.get("lines", [])):
            stats["lines"] += 1
            raw = ln.get("raw", {})
            cands = {k: [(Decimal(v), how, src) for v, how, src in raw.get(k, [])] for k in NUM_COLS}
            for k in ("material", "labor", "equipment", "total_op"):
                # a printed component or O&P value above $5 always sits on the book's rounding grid: a reading off it is a misread
                cands[k] = [(v, how, src) for v, how, src in cands[k] if v <= 5 or book_round(v) == v]
            if str(i) in extra:
                for k, lst in extra[str(i)].items():
                    if k not in cands or not cands[k]:
                        continue                               # the second reading confirms or arbitrates a cell; it never adds one alone
                    existing = {v: how for v, how, src in cands[k]}
                    for v, how, src in lst:
                        dv = Decimal(v)
                        if dv == 0 or dv not in existing:
                            continue                           # the second reading only confirms a value the first readings proposed
                        if existing[dv] == "count_mismatch":
                            how = "count_mismatch"             # the geometry saw another number of digits than this string has
                        cands[k].append((dv, how, src))
                stats["extra_lines"] += 1
            flags_before = set(ln["flags"])
            stats["open_before"] += bool(flags_before & OPEN or any(f.startswith("WEAK_READING") for f in flags_before))
            keep = [f for f in ln["flags"] if f in ("PERCENT_ADD", "LINE_NUMBER_PARTIAL", "LINE_NUMBER_MISSING", "HEADER_TEMPLATE",
                                                    "CREW_FROM_ARITHMETIC", "COLUMN_SLIP_MOVED", "UNIT_UNREAD")]
            crew_id = ln.get("crew")
            crew_row = crews.get(crew_id) if crew_id else None
            unread = "CREW_UNREAD" in flags_before or "CREW_UNKNOWN" in flags_before
            if (crew_row is None) and not ln.get("percent"):
                cid, how = identify_crew(ln, cands, crews, known_ids, extra.get(str(i), {}).get("crew_text"))
                if cid:
                    crew_id, crew_row = cid, crews[cid]
                    ln["crew"], ln["crew_source"] = cid, "arithmetic"
                    keep.append("CREW_FROM_ARITHMETIC")
                    stats["crew_found"] += 1
                    stats["crew_found_by_text"] += how == "text"
                    unread = False
                elif how == "ambiguous":
                    stats["crew_ambiguous"] += 1
            # column slip: zero-equipment crew, nothing under Total, something under Equipment, labor read (the sum check decides)
            if crew_row is not None and (crew_row.get("bare_equip_daily") or 0) == 0 and not cands["total"] and cands["equipment"] \
                    and cands["labor"] and not ln.get("percent"):
                cands["total"], cands["equipment"] = cands["equipment"], []
                keep.append("COLUMN_SLIP_MOVED")
                stats["slip_moved"] += 1
            # a unit cell with text that the first readings could not turn into a unit: the extended unit table, then the
            # 600-dpi reading (accepted only when the first readings' text is a close OCR shape of it); else not carried
            if ln.get("unit_source") in ("carried", None) and ln.get("unit_raw") and re.search(r"[A-Za-z]{2,}", ln["unit_raw"]) \
                    and not re.fullmatch(r"[\s|'\"‘’“”″lIi1!jt]{0,3}", ln["unit_raw"]):
                u = normalise_unit(ln["unit_raw"])
                src = "printed"
                if u is None:
                    h_txt = extra.get(str(i), {}).get("unit_text")
                    uh = normalise_unit(h_txt) if h_txt else None
                    if uh and _lev(re.sub(r"[^A-Za-z%]", "", ln["unit_raw"]).upper(), re.sub(r"[^A-Za-z%]", "", uh).upper()) <= 2:
                        u, src = uh, "second_reading"
                if u:
                    ln["unit"], ln["unit_source"] = u, src
                    stats["unit_recovered"] = stats.get("unit_recovered", 0) + 1
                else:
                    ln["unit"], ln["unit_source"] = None, None
                    keep.append("UNIT_UNREAD")
                    stats["unit_unread"] = stats.get("unit_unread", 0) + 1
            vals, confs, flags = settle(cands, crew_row)
            if ln.get("percent"):
                flags = [f for f in flags if f not in ("MONEY_UNSETTLED", "TOTAL_DERIVED_FROM_SUM")]
            if unread:
                flags.append("CREW_UNREAD" if "CREW_UNREAD" in flags_before else "CREW_UNKNOWN")
            for k in NUM_COLS:
                ln[k] = str(vals[k]) if vals[k] is not None else None
            ln["conf"] = {k: confs[k] for k in NUM_COLS if confs[k] is not None}
            ln["raw"] = {k: [(str(v), how, src) for v, how, src in cands[k]] for k in NUM_COLS if cands[k]}
            ln["flags"] = list(dict.fromkeys(keep + flags))
            fa = set(ln["flags"])
            stats["open_after"] += bool(fa & OPEN or any(f.startswith("WEAK_READING") for f in fa))
        (out / p.name).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
