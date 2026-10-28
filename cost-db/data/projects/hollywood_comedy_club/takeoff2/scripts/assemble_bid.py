#!/usr/bin/env python3
"""Assemble the Hollywood Comedy Club bid from the priced takeoff files.

  python3 -I assemble_bid.py <takeoff2_dir> [--prior prior_items.csv]

Reads every priced_*.csv in the folder (output of price2.py: one row per takeoff line x book component), the equipment web
prices (equipment_web_prices.csv) and writes:
  bid_lines.csv       one row per takeoff line: value carried, origin of the value, components behind it
  bid_by_item.csv     the 16 bid-letter items: direct by origin, sell, counts of unpriced lines
  bid_assembly.xlsx   the same as sheets, plus the unpriced list
  bid_summary.md      totals, markup arithmetic, what is and is not in the number

Origins of a carried value (one per line; never mixed inside a line without saying so):
  book_exact        verified book row(s) that are the specified work and product (bare direct, LA latest columns)
  book_substitute   verified book row(s) for the same work with a product/size/type the documents do not fix or that differs
  web_list          published dealer/manufacturer price for the scheduled model (material only; freight, tax, install excluded)
                    plus the book's labor component when a verified installation row was matched (shown separately)
  quote_required    no documented price: vendor quote needed (listed, not valued)
  owner / existing  no bid value
  not_quantified    the documents do not give the quantity (listed, not valued)
Company markup is applied once, on the sum of carried direct values: contingency 4%, overhead 8%, profit 7%, compounded
(1.04 x 1.08 x 1.07 = 1.201824), the same way as the 2026-10-20 estimate. The book's O&P column is shown for reference only.
No allowance, percentage or tolerance is added anywhere.
"""
from __future__ import annotations

import csv
import glob
import os
import sys
from collections import OrderedDict, defaultdict
from decimal import Decimal, ROUND_HALF_UP

ITEMS = ["Demolition", "Interior walls", "Ceilings", "Flooring", "New Roofing", "Interior finishes", "Exterior finishes",
         "Doors & Hardware", "Stairs & railing", "Owner-provided equipment install", "Lighting", "Mechanical", "Plumbing",
         "Low Voltage", "F&B equipment", "Other required scope"]
PRIOR_SELL = {"Demolition": 258314, "Interior walls": 408840, "Ceilings": 84662, "Flooring": 151468, "New Roofing": 57688,
              "Interior finishes": 524421, "Exterior finishes": 94944, "Doors & Hardware": 121504, "Stairs & railing": 322960,
              "Owner-provided equipment install": 23436, "Lighting": 249377, "Mechanical": 793677, "Plumbing": 266324,
              "Low Voltage": 84128, "F&B equipment": 714484, "Other required scope": 925181}
MARKUP = (Decimal("1.04"), Decimal("1.08"), Decimal("1.07"))
FACTOR = MARKUP[0] * MARKUP[1] * MARKUP[2]


def D(x):
    try:
        return Decimal(str(x).replace(",", "")) if str(x).strip() not in ("", "None") else None
    except Exception:
        return None


def q2(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def item_of(name: str) -> str:
    n = (name or "").strip()
    if n in ITEMS:
        return n
    low = n.lower()
    if "owner" in low:
        return "Owner-provided equipment install"
    if "electrical" in low or "other" in low or "existing" in low:
        return "Other required scope"
    if "f&b" in low or "equipment" in low:
        return "F&B equipment"
    return "Other required scope"


def main() -> int:
    d = sys.argv[1]
    priced_files = sorted(glob.glob(os.path.join(d, "priced_*.csv")))
    web = {}
    wp = os.path.join(d, "equipment_web_prices.csv")
    if os.path.exists(wp):
        for r in csv.DictReader(open(wp, encoding="utf-8")):
            web[r["item_id"]] = r
    lines: "OrderedDict[str, dict]" = OrderedDict()
    for f in priced_files:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            key = r["item_id"]
            ln = lines.setdefault(key, {"item_id": key, "source_file": os.path.basename(f), "bid_letter_item": item_of(r["bid_letter_item"]),
                                        "takeoff_item": r["bid_letter_item"], "division": r.get("division", ""), "description": r["description"],
                                        "spec_or_model": r.get("spec_or_model", ""), "qty": r.get("qty", ""), "unit": r.get("unit", ""),
                                        "qty_basis": r.get("qty_basis", ""), "furnished_by": r.get("furnished_by", ""),
                                        "comps": [], "statuses": set()})
            ln["comps"].append(r)
            ln["statuses"].add(r.get("price_status", ""))
    out_rows = []
    by_item = {k: defaultdict(Decimal) for k in ITEMS}
    counts = {k: defaultdict(int) for k in ITEMS}
    unpriced = []
    for key, ln in lines.items():
        exact = sum((D(c["ext_total"]) or Decimal(0)) for c in ln["comps"] if c.get("price_status") == "priced_exact")
        subst = sum((D(c["ext_total"]) or Decimal(0)) for c in ln["comps"] if c.get("price_status") == "priced_substitute")
        labor_book = sum((D(c["ext_labor"]) or Decimal(0)) for c in ln["comps"] if c.get("price_status", "").startswith("priced"))
        op_ref = sum((D(c["ext_total_incl_op"]) or Decimal(0)) for c in ln["comps"] if c.get("price_status", "").startswith("priced"))
        w = web.get(key)
        web_ext = D(w["extended_usd"]) if w else None
        statuses = ln["statuses"]
        origin, value, note = None, Decimal(0), ""
        fb = (ln["furnished_by"] or "").lower()
        if "owner" in fb or "existing" in fb or statuses & {"owner_provided", "existing"}:
            origin, note = "owner / existing", "no bid value (furnished by owner / existing to remain); installation labor only where priced"
            value = exact + subst
            if value:
                origin = "book_substitute" if subst else "book_exact"
                note = "installation only; the item itself is owner-furnished / existing"
        elif web_ext is not None:
            # the web price replaces any book material price for the same model; book labor is kept when a verified install row was matched
            install_comps = [c for c in ln["comps"] if c.get("price_status", "").startswith("priced") and "install" in (c.get("component", "") + c.get("book_description_path", "")).lower()]
            lab = sum((D(c["ext_total"]) or Decimal(0)) for c in install_comps)
            origin, value = "web_list", web_ext + lab
            note = f"{w['price_kind']} {w['vendor']} {w['date_checked']} model {w['matched_model']}; freight, tax, start-up excluded" + (f"; + book installation {q2(lab)}" if lab else "")
        elif exact or subst:
            if exact and not subst:
                origin, value = "book_exact", exact
            elif subst and not exact:
                origin, value = "book_substitute", subst
            else:
                origin, value, note = "book_substitute", exact + subst, f"exact {q2(exact)} + substitute {q2(subst)}"
            unp = [c for c in ln["comps"] if not c.get("price_status", "").startswith("priced")]
            if unp:
                note = (note + "; " if note else "") + f"{len(unp)} component(s) without price: " + "; ".join(f"{c.get('component') or c.get('description')} ({c.get('price_status')})" for c in unp)[:300]
        else:
            st = sorted(statuses)
            if "not_quantified" in statuses or not str(ln["qty"]).strip():
                origin = "not_quantified"
            elif statuses & {"quote", "not_in_book", "book_row_not_matching", "book_row_not_verified"}:
                origin = "quote_required"
            else:
                origin = "quote_required"
            note = "; ".join(sorted({(c.get("reason") or c.get("price_status") or "") for c in ln["comps"]}))[:400]
            unpriced.append((ln["bid_letter_item"], key, ln["description"], ln["qty"], ln["unit"], origin, note))
        item = ln["bid_letter_item"]
        by_item[item][origin] += value
        by_item[item]["op_ref"] += op_ref
        counts[item][origin] += 1
        out_rows.append({"item_id": key, "bid_letter_item": item, "takeoff_item": ln["takeoff_item"], "division": ln["division"],
                         "description": ln["description"], "spec_or_model": ln["spec_or_model"], "qty": ln["qty"], "unit": ln["unit"],
                         "qty_basis": ln["qty_basis"], "furnished_by": ln["furnished_by"], "origin": origin,
                         "value_direct": str(q2(value)) if value else "", "book_exact": str(q2(exact)) if exact else "",
                         "book_substitute": str(q2(subst)) if subst else "", "web_list_material": str(q2(web_ext)) if web_ext is not None else "",
                         "book_op_reference": str(q2(op_ref)) if op_ref else "", "components": len(ln["comps"]),
                         "cost_codes": "; ".join(c["cost_code"] for c in ln["comps"] if c.get("cost_code")), "note": note, "source_file": ln["source_file"]})
    # ---- write
    cols = list(out_rows[0].keys()) if out_rows else []
    with open(os.path.join(d, "bid_lines.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)
    origins = ["book_exact", "book_substitute", "web_list"]
    tot = defaultdict(Decimal)
    item_rows = []
    for it in ITEMS:
        direct = sum(by_item[it][o] for o in origins)
        row = {"bid_letter_item": it, "book_exact": q2(by_item[it]["book_exact"]), "book_substitute": q2(by_item[it]["book_substitute"]),
               "web_list": q2(by_item[it]["web_list"]), "direct_carried": q2(direct), "sell": q2(direct * FACTOR),
               "book_op_reference": q2(by_item[it]["op_ref"]), "prior_sell_2026_10_20": PRIOR_SELL[it],
               "lines_priced": counts[it]["book_exact"] + counts[it]["book_substitute"] + counts[it]["web_list"],
               "lines_quote_required": counts[it]["quote_required"], "lines_not_quantified": counts[it]["not_quantified"],
               "lines_owner_existing": counts[it]["owner / existing"]}
        item_rows.append(row)
        for k, v in row.items():
            if isinstance(v, (Decimal, int)) and k != "bid_letter_item":
                tot[k] += Decimal(v)
    with open(os.path.join(d, "bid_by_item.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(item_rows[0].keys()))
        w.writeheader()
        w.writerows(item_rows)
        w.writerow({"bid_letter_item": "TOTAL", **{k: q2(v) if isinstance(v, Decimal) else v for k, v in tot.items()}})
    direct = tot["direct_carried"]
    c = direct * (MARKUP[0] - 1)
    o = direct * MARKUP[0] * (MARKUP[1] - 1)
    p = direct * MARKUP[0] * MARKUP[1] * (MARKUP[2] - 1)
    sell = direct * FACTOR
    md = ["# Hollywood Comedy Club — bid assembly from the full-set takeoff", "",
          f"Inputs: {', '.join(os.path.basename(x) for x in priced_files)}" + (", equipment_web_prices.csv" if web else "") + ".",
          "Every carried value has one origin (column `origin` in bid_lines.csv); nothing is averaged, allowed or assumed.", "",
          "| origin | direct (USD) | lines |", "|---|---:|---:|"]
    for o_ in origins + ["quote_required", "not_quantified", "owner / existing"]:
        md.append(f"| {o_} | {q2(tot.get(o_, Decimal(0))) if o_ in origins else ''} | {sum(counts[i][o_] for i in ITEMS)} |")
    md += ["", "| | USD |", "|---|---:|", f"| Direct carried (book exact + book substitute + web list) | {q2(direct)} |",
           f"| Contingency 4% | {q2(c)} |", f"| Overhead 8% on (direct + contingency) | {q2(o)} |", f"| Profit 7% on (direct + contingency + overhead) | {q2(p)} |",
           f"| **Sell = direct x {FACTOR}** | **{q2(sell)}** |", f"| Book O&P extended (reference only, not added) | {q2(tot['book_op_reference'])} |",
           f"| Prior estimate sell 2026-10-20 (16 items) | {sum(PRIOR_SELL.values())} |", "",
           "## By bid-letter item", "", "| item | book exact | book substitute | web list | direct | sell | prior sell | priced | quote req. | not quantified | owner/existing |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in item_rows:
        md.append(f"| {r['bid_letter_item']} | {r['book_exact']} | {r['book_substitute']} | {r['web_list']} | {r['direct_carried']} | {r['sell']} | {r['prior_sell_2026_10_20']} | {r['lines_priced']} | {r['lines_quote_required']} | {r['lines_not_quantified']} | {r['lines_owner_existing']} |")
    md += ["", f"## Lines without a value ({len(unpriced)})", "", "| item | id | description | qty | unit | why |", "|---|---|---|---:|---|---|"]
    for it, key, desc, qty, unit, origin, note in unpriced:
        md.append(f"| {it} | {key} | {desc[:80]} | {qty} | {unit} | {origin}: {note[:160]} |")
    md += ["", "## What the number is and is not", "",
           "The sell figure covers only the lines with a documented price: the company's book (verified rows, Los Angeles latest index) "
           "where the book has the work, and published dealer/manufacturer prices for scheduled equipment models (material only). "
           "Every line listed under 'without a value' is still scope and still needs a vendor or subcontractor quote, or a quantity the "
           "documents do not give; they are not in the sell figure. The 2026-10-20 estimate is shown for orientation only; it was built "
           "before the schedules, MEP, plumbing and kitchen drawings were on hand."]
    open(os.path.join(d, "bid_summary.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
        wb = Workbook()
        ws = wb.active
        ws.title = "Bid by item"
        ws.append(list(item_rows[0].keys()))
        for r in item_rows:
            ws.append([float(v) if isinstance(v, Decimal) else v for v in r.values()])
        ws.append(["TOTAL"] + [float(tot[k]) if k in tot else "" for k in list(item_rows[0].keys())[1:]])
        for c_ in ws[1]:
            c_.font = Font(bold=True)
        ws2 = wb.create_sheet("Lines")
        ws2.append(cols)
        for r in out_rows:
            ws2.append([r[k] for k in cols])
        ws3 = wb.create_sheet("Without value")
        ws3.append(["item", "id", "description", "qty", "unit", "origin", "why"])
        for u in unpriced:
            ws3.append(list(u))
        ws4 = wb.create_sheet("Markup")
        for row in (["Direct carried", float(q2(direct))], ["Contingency 4%", float(q2(c))], ["Overhead 8%", float(q2(o))],
                    ["Profit 7%", float(q2(p))], ["Sell", float(q2(sell))], ["Factor", float(FACTOR)], ["Book O&P reference", float(q2(tot["book_op_reference"]))]):
            ws4.append(row)
        wb.save(os.path.join(d, "bid_assembly.xlsx"))
    except ImportError:
        pass
    print(f"lines {len(out_rows)} | direct {q2(direct)} | sell {q2(sell)} | without value {len(unpriced)} | files {len(priced_files)} web {len(web)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
