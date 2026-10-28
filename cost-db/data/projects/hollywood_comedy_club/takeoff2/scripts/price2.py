#!/usr/bin/env python3
"""Hollywood Comedy Club TI - price a takeoff2 file from the company's book-derived cost table.

Usage:  python3 -I price2.py <takeoff.csv> <matches.csv> <book.csv> <out_priced.csv>

The takeoff file carries one line per item (columns item_id, bid_letter_item, division, description, spec_or_model,
qty, unit, qty_basis, qty_source, furnished_by, installed_by, notes). The matches file is the hand-built mapping of
every takeoff line to zero or more book components:

    item_id, component, cost_code, factor, tier, match, reason, candidate_row, price_status_override

  * a row with a cost_code is a PRICED component: tier = exact | substitute (match = exact | substitute | partial,
    default = tier); factor converts the takeoff quantity into the book quantity (book_qty = qty x factor) and is
    written as a number or an arithmetic expression of numbers (e.g. "1/12", "2/12/27", "1595/95.54") optionally
    followed by a parenthesised note that names the source of the conversion; component = the component text
  * a row without a cost_code is an UNPRICED component (or the whole line when component is empty):
    price_status_override = the price_status, reason = why, candidate_row = the nearest book row(s) if any
  * a takeoff line whose qty is empty is written as not_quantified whatever the mapping says (an override is kept
    only when it is one of the no-price statuses: owner_provided, existing, quote, none_required)

Rules applied (the owner's standing rules, the same as scripts/price.py of the first estimate):
  1. a component is priced ONLY from a row with status = verified; the Los Angeles latest-month columns are used
     (material_la_latest, labor_la_latest, equipment_la_latest, total_la_latest, total_incl_op_la_latest)
  2. a machine_read / flagged row is never used as a price: it is reported as candidate_row with the price empty
  3. no invented numbers, no allowances, no tolerances; every unit conversion is written out (factor / unit_check)
  4. no second location or time factor: the *_la_latest columns already carry the LA index and BLS escalation
  5. bare components are kept separate; the book O&P column is reported for reference only

Assertions (a failure is a hard stop, nothing is written):
  * every priced cost_code exists in the table exactly once with status = verified (all rows per code are loaded;
    a code carried by any other row is reported in the reason column - the defensive duplicate check)
  * the verified row carries a unit and a total_la_latest, and material + labor + equipment = total (to the cent)
  * book_qty is written with enough digits that book_qty x unit price reproduces the extension to the cent
  * every takeoff line appears in the output at least once; every unpriced row carries a price_status and a reason
  * every mapping row names a takeoff line of the file (no orphan decisions)
"""
import csv
import os
import re
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

PRICED = ("priced_exact", "priced_substitute")
NO_PRICE_STATUSES = ("owner_provided", "existing", "quote", "none_required")
UNPRICED_STATUSES = ("book_row_not_matching", "book_row_not_verified", "not_in_book", "not_quantified",
                     "spec_not_issued", "owner_provided", "existing", "quote", "none_required")
UNIT_ALIAS = {"SF": "S.F.", "LF": "L.F.", "EA": "Ea.", "RISER": "Riser", "WK": "Week", "DAY": "Day", "LS": "L.S.",
              "GAL": "Gal.", "MSF": "M.S.F.", "OPNG": "Opng.", "SET": "Set", "CY": "C.Y.", "LOT": "Lot"}
EACH_UNITS = {"Ea.", "Door", "Opng.", "Set", "Riser"}

EST_COLS = ["item_id", "bid_letter_item", "division", "description", "component", "qty", "unit", "qty_basis", "qty_source",
            "cost_code", "ref_line", "book_page", "book_description_path", "book_unit", "unit_check", "factor", "book_qty",
            "latest_period", "material_la_latest", "labor_la_latest", "equipment_la_latest", "total_la_latest", "total_incl_op_la_latest",
            "ext_material", "ext_labor", "ext_equipment", "ext_total", "ext_total_incl_op",
            "price_status", "match", "candidate_row", "reason", "takeoff_notes",
            "spec_or_model", "furnished_by", "installed_by"]
MATCH_COLS = ["item_id", "component", "cost_code", "factor", "tier", "match", "reason", "candidate_row", "price_status_override"]


def D(x):
    return Decimal(x) if x not in ("", None) else None


def q2(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_factor(text):
    """'1', '1/12', '2/12/27', '0.5625 (9 x 9 in plate = 81/144 S.F.)' -> (Decimal, expression, note)."""
    text = (text or "").strip()
    if text == "":
        return Decimal(1), "1", ""
    note = ""
    m = re.match(r"^([0-9.*/ ]+?)\s*(\((.*)\))?\s*$", text)
    if not m:
        raise SystemExit(f"factor '{text}' is not a number or an expression of numbers with * and /")
    expr = m.group(1).replace(" ", "")
    if m.group(3):
        note = m.group(3).strip()
    tokens = re.findall(r"[0-9.]+|[*/]", expr)
    if not tokens or not re.fullmatch(r"[0-9.]+", tokens[0]) or "".join(tokens) != expr:
        raise SystemExit(f"factor '{text}' could not be parsed")
    value = Decimal(tokens[0])
    i = 1
    while i < len(tokens):
        op, num = tokens[i], tokens[i + 1]
        value = value * Decimal(num) if op == "*" else value / Decimal(num)
        i += 2
    return value, expr, note


def factor_text(value, expr):
    if value == value.to_integral_value():
        return str(int(value))
    return f"{value:.6f}" if expr != f"{value:.6f}" else expr


def unit_check(takeoff_unit, book_unit, fvalue, expr, note):
    tu = UNIT_ALIAS.get(takeoff_unit.upper(), takeoff_unit)
    if fvalue == 1 and tu.lower().rstrip(".") == book_unit.lower().rstrip("."):
        return "same unit"
    if fvalue == 1 and tu in EACH_UNITS and book_unit in EACH_UNITS:
        return f"each-type units (takeoff {tu} = book {book_unit})"
    s = f"converted: book qty = takeoff qty x {expr}"
    if note:
        s += f" ({note})"
    return s


def empty_book():
    return dict(cost_code="", ref_line="", book_page="", book_description_path="", book_unit="", unit_check="", factor="", book_qty="",
                latest_period="", material_la_latest="", labor_la_latest="", equipment_la_latest="", total_la_latest="",
                total_incl_op_la_latest="", ext_material="", ext_labor="", ext_equipment="", ext_total="", ext_total_incl_op="")


def load_book(path):
    rows = defaultdict(list)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r["cost_code"]:
                rows[r["cost_code"]].append(r)
    return rows


def main(argv):
    if len(argv) != 5:
        raise SystemExit(__doc__)
    takeoff_path, matches_path, book_path, out_path = argv[1:5]
    with open(takeoff_path, newline="") as f:
        takeoff = list(csv.DictReader(f))
    with open(matches_path, newline="") as f:
        rd = csv.DictReader(f)
        missing_cols = [c for c in MATCH_COLS if c not in rd.fieldnames]
        assert not missing_cols, f"matches file lacks columns {missing_cols}"
        matches = list(rd)
    book = load_book(book_path)

    by_item = defaultdict(list)
    for m in matches:
        by_item[m["item_id"]].append(m)
    takeoff_ids = [t["item_id"] for t in takeoff]
    assert len(takeoff_ids) == len(set(takeoff_ids)), "duplicate item_id in the takeoff file"
    missing = [i for i in takeoff_ids if i not in by_item]
    assert not missing, f"takeoff lines without a mapping decision: {missing}"
    extra = [i for i in by_item if i not in set(takeoff_ids)]
    assert not extra, f"mapping decisions without a takeoff line: {extra}"

    out = []
    dup_notes = {}
    for t in takeoff:
        base = dict(item_id=t["item_id"], bid_letter_item=t["bid_letter_item"], division=t["division"], description=t["description"],
                    qty=t["qty"], unit=t["unit"], qty_basis=t["qty_basis"], qty_source=t["qty_source"], takeoff_notes=t["notes"],
                    spec_or_model=t.get("spec_or_model", ""), furnished_by=t.get("furnished_by", ""), installed_by=t.get("installed_by", ""))
        comps = by_item[t["item_id"]]
        qty_empty = t["qty"].strip() == ""
        for c in comps:
            cc = c["cost_code"].strip()
            status_ovr = c["price_status_override"].strip()
            if cc == "" or qty_empty:
                if qty_empty:
                    status = status_ovr if status_ovr in NO_PRICE_STATUSES else "not_quantified"
                    reason = c["reason"].strip() or "quantity not determinable"
                    if cc:
                        reason = "takeoff quantity empty; " + reason
                    cand = c["candidate_row"].strip() or (cc if cc else "")
                else:
                    status, reason, cand = status_ovr, c["reason"].strip(), c["candidate_row"].strip()
                assert status in UNPRICED_STATUSES, f"{t['item_id']}: price_status '{status}' is not one of {UNPRICED_STATUSES}"
                assert reason, f"{t['item_id']}: unpriced row without a reason"
                out.append(dict(base, component=c["component"].strip(), **empty_book(), price_status=status, match="",
                                candidate_row=cand, reason=reason))
                continue
            tier = c["tier"].strip()
            assert tier in ("exact", "substitute"), f"{t['item_id']}: tier '{tier}' must be exact or substitute"
            match = c["match"].strip() or tier
            assert match in ("exact", "substitute", "partial"), f"{t['item_id']}: match '{match}'"
            assert not (tier == "exact" and match != "exact"), f"{t['item_id']}: an exact component cannot be partial/substitute"
            allrows = book.get(cc, [])
            assert allrows, f"{t['item_id']}: cost code {cc} is not carried by any row of the table on hand; reclassify the component"
            ver = [b for b in allrows if b["status"] == "verified"]
            assert len(ver) == 1, f"{t['item_id']}: cost code {cc} is carried by {len(ver)} verified rows (of {len(allrows)}); it cannot be used"
            dup = ""
            if len(allrows) > 1:
                dup = f"cost code appears on {len(allrows)} rows of the table: " + "; ".join(
                    f"[{b['status']}, unit '{b['unit'] or '-'}'] {b['description'][:60]}" for b in allrows)
                dup_notes[cc] = dup
            b = ver[0]
            assert b["unit"] != "", f"{t['item_id']}: {cc} has no unit"
            assert b["total_la_latest"] != "", f"{t['item_id']}: {cc} has no total_la_latest"
            fval, fexpr, fnote = parse_factor(c["factor"])
            qty = Decimal(t["qty"])
            bq = qty * fval
            m_, l_, e_ = (D(b["material_la_latest"]) or Decimal(0), D(b["labor_la_latest"]) or Decimal(0), D(b["equipment_la_latest"]) or Decimal(0))
            tot, op = D(b["total_la_latest"]), D(b["total_incl_op_la_latest"])
            assert q2(m_ + l_ + e_) == q2(tot), f"{cc}: components {m_}+{l_}+{e_} do not sum to total {tot}"
            # book_qty: the fewest decimals that still reproduce the extension to the cent
            bq_text = str(q2(bq)) if q2(bq) == bq else f"{bq:.6f}"
            assert q2(Decimal(bq_text) * tot) == q2(bq * tot), f"{t['item_id']}: book_qty {bq_text} does not reproduce the extension"
            reason = c["reason"].strip()
            assert reason, f"{t['item_id']}: priced component without a reason"
            out.append(dict(base, component=c["component"].strip(), cost_code=cc, ref_line=b["ref_line"], book_page=b["book_page"],
                            book_description_path=b["description_path"], book_unit=b["unit"],
                            unit_check=unit_check(t["unit"], b["unit"], fval, fexpr, fnote), factor=factor_text(fval, fexpr), book_qty=bq_text,
                            latest_period=b["latest_period"], material_la_latest=str(m_), labor_la_latest=str(l_), equipment_la_latest=str(e_),
                            total_la_latest=str(tot), total_incl_op_la_latest=(str(op) if op is not None else ""),
                            ext_material=str(q2(bq * m_)), ext_labor=str(q2(bq * l_)), ext_equipment=str(q2(bq * e_)), ext_total=str(q2(bq * tot)),
                            ext_total_incl_op=(str(q2(bq * op)) if op is not None else ""),
                            price_status=("priced_exact" if tier == "exact" else "priced_substitute"), match=match, candidate_row="",
                            reason=reason + ("; " + dup if dup else "")))

    seen = {r["item_id"] for r in out}
    assert seen == set(takeoff_ids), "a takeoff line is missing from the output"
    for r in out:
        assert r["price_status"], f"{r['item_id']}: row without price_status"
        assert r["reason"], f"{r['item_id']}: row without reason"

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EST_COLS)
        w.writeheader()
        for r in out:
            w.writerow(r)

    # summary to stdout
    counts = defaultdict(int)
    lines_by_status = defaultdict(set)
    for r in out:
        counts[r["price_status"]] += 1
        lines_by_status[r["price_status"]].add(r["item_id"])
    tiers = {k: dict(material=Decimal(0), labor=Decimal(0), equipment=Decimal(0), direct=Decimal(0), book_op=Decimal(0), rows_without_op=0, n=0)
             for k in PRICED}
    for r in out:
        if r["price_status"] in PRICED:
            s = tiers[r["price_status"]]
            s["n"] += 1
            s["material"] += Decimal(r["ext_material"]); s["labor"] += Decimal(r["ext_labor"]); s["equipment"] += Decimal(r["ext_equipment"])
            s["direct"] += Decimal(r["ext_total"])
            if r["ext_total_incl_op"]:
                s["book_op"] += Decimal(r["ext_total_incl_op"])
            else:
                s["rows_without_op"] += 1
    print(f"{os.path.basename(takeoff_path)}: {len(takeoff)} takeoff lines -> {len(out)} output rows; "
          f"lines with a priced component {len(lines_by_status['priced_exact'] | lines_by_status['priced_substitute'])}")
    for k in sorted(counts):
        print(f"  {k:24s} rows {counts[k]:4d}  lines {len(lines_by_status[k]):4d}")
    for k, s in tiers.items():
        print(f"  {k}: components {s['n']}  M {s['material']}  L {s['labor']}  E {s['equipment']}  direct {s['direct']}  "
              f"book O&P ext {s['book_op']} ({s['rows_without_op']} rows without a book O&P value)")
    for cc, d in dup_notes.items():
        print("  duplicate code seen:", cc, d[:160])
    print("written:", out_path)


if __name__ == "__main__":
    main(sys.argv)
