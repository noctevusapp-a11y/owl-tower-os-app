#!/usr/bin/env python3
"""Merge the per-page parse results into one line-item table with the description hierarchy, our own cost codes and a
verification status per row.

  python3 -I build_book_table.py <parsed_dir> <out_dir> [--crews crews_2022_totals.csv]

Steps
  1. pages in order; sections whose division digit was cut at the page edge get the division of the surrounding sections
  2. partial line numbers (left edge cut) get their thousands digit from the numbering order inside the section
  3. description hierarchy: "read up through the indents" (the book's own rule) -> description_path
  4. cost code  OT-<section digits>-<line>  (ours; the book's line id stays in ref_line for traceability)
  5. status: verified (every number settled by at least two readings or the table arithmetic, no open flag) / flagged
Outputs: book_lines.csv, book_lines.json, book_sections.csv, build_report.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

DIVISION_NAMES = {
    "01": "General Requirements", "02": "Existing Conditions", "03": "Concrete", "04": "Masonry", "05": "Metals",
    "06": "Wood, Plastics & Composites", "07": "Thermal & Moisture Protection", "08": "Openings", "09": "Finishes", "10": "Specialties",
    "11": "Equipment", "12": "Furnishings", "13": "Special Construction", "14": "Conveying Equipment", "21": "Fire Suppression",
    "22": "Plumbing", "23": "Heating, Ventilating & Air Conditioning", "25": "Integrated Automation", "26": "Electrical",
    "27": "Communications", "28": "Electronic Safety & Security", "31": "Earthwork", "32": "Exterior Improvements", "33": "Utilities",
    "34": "Transportation", "35": "Waterway & Marine Construction", "41": "Material Processing & Handling Equipment",
    "44": "Pollution Control Equipment", "46": "Water & Wastewater Equipment", "48": "Electrical Power Generation"}
VALID_DIVS = set(DIVISION_NAMES)
OPEN_FLAGS = {"MONEY_UNSETTLED", "MONEY_AMBIGUOUS", "OUTPUT_HOURS_UNSETTLED", "OUTPUT_HOURS_AMBIGUOUS", "LABOR_CREW_MISMATCH",
              "EQUIP_CREW_MISMATCH", "CREW_UNREAD", "LINE_NUMBER_MISSING", "LINE_ORDER", "SECTION_ID_DOUBTFUL"}
INFO_FLAGS = {"MATERIAL_DERIVED_FROM_SUM", "LABOR_DERIVED_FROM_SUM", "EQUIPMENT_DERIVED_FROM_SUM", "TOTAL_DERIVED_FROM_SUM",
              "HOURS_DERIVED_FROM_CREW", "OUTPUT_DERIVED_FROM_CREW", "OUTPUT_FROM_LABOR_CHECK", "MATERIAL_DERIVED_FROM_CREW_SUM",
              "OUTPUT_DERIVED_FROM_LABOR", "LABOR_DERIVED_FROM_CREW_SUM", "LINE_NUMBER_PARTIAL", "LINE_NUMBER_RECONSTRUCTED"}
DESC_FIXES = [(r"\b1b\.", "lb."), (r"\bIb\.", "lb."), (r"\b1bs\.", "lbs."), (r"(\d)\s*0C\b", r"\1 OC"), (r"\b0\.C\.", "O.C."), ("’", "'"), ("‘", "'"),
              ("”", '"'), ("“", '"'), ("″", '"'), ("—", "-"), ("–", "-"), (r"\s+,", ","), (r"\s{2,}", " "), (r"^[\s\-=~_.|:;'\"]+", ""), (r"[\s\-=~_|:;'\"]+$", "")]


def fix_desc(s: str) -> str:
    for pat, rep in DESC_FIXES:
        s = re.sub(pat, rep, s)
    return s.strip()


def better_desc(a: str, b: str | None) -> str:
    """Prefer the reading with more letters and fewer stray symbols."""
    if not b:
        return a
    def score(s):
        letters = sum(ch.isalpha() for ch in s)
        junk = sum(ch in "|~_=`^{}[]<>" for ch in s)
        return letters - 3 * junk
    return a if score(a) >= score(b) else b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parsed_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--crews", default=None)
    a = ap.parse_args()
    pages = []
    for p in sorted(Path(a.parsed_dir).glob("p*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("header_found"):
            pages.append(d)
    crews = {}
    if a.crews and Path(a.crews).exists():
        with open(a.crews, encoding="utf-8") as f:
            crews = {r["crew_id"]: r for r in csv.DictReader(f)}

    # ---- 1. sections: fix uncertain divisions from the surrounding certain ones with the same second pair
    all_sections = [s for pg in pages for s in pg["sections"]]
    for i, s in enumerate(all_sections):
        if s.get("division_uncertain"):
            pair = s["section_id"][3:5]
            cands = []
            for j in list(range(i - 1, max(-1, i - 12), -1)) + list(range(i + 1, min(len(all_sections), i + 12))):
                t = all_sections[j]
                if not t.get("division_uncertain") and t["section_id"][3:5] == pair and t["section_id"][:2] in VALID_DIVS:
                    cands.append(t["section_id"][:2])
                    break
            if cands:
                s["section_id_fixed"] = cands[0] + s["section_id"][2:]
            elif s["section_id"][:2] in VALID_DIVS:
                s["section_id_fixed"] = s["section_id"]
            else:
                s["section_id_fixed"] = None
        else:
            s["section_id_fixed"] = s["section_id"] if s["section_id"][:2] in VALID_DIVS else None
    fix_map = {(s["pdf_page"], s["section_id"]): s["section_id_fixed"] for s in all_sections}
    titles = {}
    for s in all_sections:
        if s["section_id_fixed"]:
            titles.setdefault(s["section_id_fixed"], s["title"])

    # ---- 2. lines in order: robust numbering check (longest increasing run per section; the rest are misreads), partial numbers
    items = []
    for pg in pages:
        for ln in pg["lines"]:
            sec = fix_map.get((pg["pdf_page"], ln["section_id"])) if ln["section_id"] else None
            if sec is None and ln["section_id"]:
                sec = next((s["section_id_fixed"] for s in all_sections if s["section_id"] == ln["section_id"] and s["section_id_fixed"]), None)
            items.append({"ln": ln, "sec": sec, "line_no": ln["line"], "order_bad": False})
    # group by section in reading order (sections can continue over pages but never interleave)
    groups: dict[str, list[int]] = {}
    run_of: dict[str, int] = {}
    last_in_sec: dict[str, int] = {}
    for i, it in enumerate(items):
        if it["sec"] and it["line_no"] and not it["ln"].get("line_partial"):
            v = int(it["line_no"])
            prev = last_in_sec.get(it["sec"])
            if prev is not None and v <= 300 and prev - v >= 1000:
                run_of[it["sec"]] = run_of.get(it["sec"], 0) + 1          # numbering restarts: a new section whose id was misread as this one
                it["restart"] = True
            last_in_sec[it["sec"]] = v
            groups.setdefault(f"{it['sec']}#{run_of.get(it['sec'], 0)}", []).append(i)
    for sec, idxs in groups.items():
        vals = [int(items[i]["line_no"]) for i in idxs]
        # longest strictly increasing subsequence (O(n log n)) - everything outside it is a misread number
        import bisect
        tails, tails_idx, prev = [], [], [-1] * len(vals)
        for k, v in enumerate(vals):
            pos = bisect.bisect_left(tails, v)
            if pos == len(tails):
                tails.append(v)
                tails_idx.append(k)
            else:
                tails[pos] = v
                tails_idx[pos] = k
            prev[k] = tails_idx[pos - 1] if pos else -1
        keep = set()
        k = tails_idx[-1] if tails_idx else -1
        while k != -1:
            keep.add(k)
            k = prev[k]
        for k, i in enumerate(idxs):
            if k not in keep:
                items[i]["order_bad"] = True
    # partial numbers: the thousands digit from the neighbours that are in order
    last_ok: dict[str, int] = {}
    for it in items:
        sec, ln = it["sec"], it["ln"]
        if not sec:
            continue
        if ln.get("line_partial") and it["line_no"]:
            prev = last_ok.get(sec)
            tail = int(it["line_no"][-3:])
            cand = tail if prev is None else next((k * 1000 + tail for k in range(0, 10) if k * 1000 + tail > prev), None)
            if cand is not None:
                it["line_no"] = f"{cand:04d}"
                it["reconstructed"] = True
            else:
                it["line_no"] = None
        elif it["line_no"] and not it["order_bad"]:
            last_ok[sec] = int(it["line_no"])

    rows = []
    stack_by_section: dict[str, list[tuple[int, str]]] = {}
    report = Counter()
    for it in items:
        ln, sec, line_no = it["ln"], it["sec"], it["line_no"]
        flags = [f for f in ln["flags"] if f != "LINE_ORDER"]
        if it.get("reconstructed"):
            flags.append("LINE_NUMBER_RECONSTRUCTED")
        if ln.get("line_partial") and line_no is None:
            flags.append("LINE_NUMBER_MISSING")
        if it["order_bad"]:
            flags.append("LINE_ORDER")
        if it.get("restart"):
            flags.append("SECTION_ID_DOUBTFUL")                 # the numbering restarted under the same section id: one of the two ids is misread
        desc = fix_desc(better_desc(ln["description"] or "", ln.get("description_alt")))
        indent = ln.get("indent_px")
        path = []
        if sec is not None and indent is not None:
            st = stack_by_section.setdefault(sec, [])
            while st and st[-1][0] >= indent - 25:
                st.pop()
            path = [d for _, d in st]
            st.append((indent, desc))
        open_flags = [f for f in flags if f in OPEN_FLAGS]
        has_cost = any(ln[k] is not None for k in ("material", "labor", "equipment", "total"))
        status = "header" if not has_cost and ln["output"] is None else ("flagged" if open_flags else "verified")
        cost_code = f"OT-{sec.replace(' ', '').replace('.', '')}-{line_no}" if sec and line_no else None
        crew = crews.get(ln["crew"]) if ln["crew"] else None
        pg_no = ln["pdf_page"]
        rows.append({
            "cost_code": cost_code, "division": sec[:2] if sec else None, "division_name": DIVISION_NAMES.get(sec[:2]) if sec else None,
            "section_id": sec, "section_title": titles.get(sec) if sec else None, "line": line_no, "ref_line": (sec + " " + line_no) if sec and line_no else None,
            "description": desc, "description_path": " | ".join(path + [desc]) if path else desc, "level": len(path),
            "crew": ln["crew"], "crew_source": ln["crew_source"], "daily_output": ln["output"], "labor_hours": ln["hours"], "unit": ln["unit"],
            "unit_source": ln["unit_source"], "material_2022": ln["material"], "labor_2022": ln["labor"], "equipment_2022": ln["equipment"],
            "total_2022": ln["total"], "total_incl_op_2022": ln["total_op"], "ref_note": ln.get("ref_note"),
            "book_page": pg_no - 14, "pdf_page": pg_no, "status": status, "flags": ";".join(flags),
            "conf": json.dumps(ln.get("conf", {})),
            "crew_labor_hours_per_day": crew["labor_hours_per_day"] if crew else None})
        report[status] += 1
        for f in flags:
            report["flag:" + f] += 1

    # ---- 3. write
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys()) if rows else []
    with (out / "book_lines.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    (out / "book_lines.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    with (out / "book_sections.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section_id", "title", "division", "division_name", "first_pdf_page", "division_uncertain_raw"])
        seen = set()
        for s in all_sections:
            if s["section_id_fixed"] and s["section_id_fixed"] not in seen:
                seen.add(s["section_id_fixed"])
                w.writerow([s["section_id_fixed"], s["title"], s["section_id_fixed"][:2], DIVISION_NAMES.get(s["section_id_fixed"][:2]), s["pdf_page"],
                            s.get("division_raw") if s.get("division_uncertain") else ""])
    rep = {"pages": len(pages), "lines": len(rows), "sections": len(seen), **{k: v for k, v in sorted(report.items())}}
    (out / "build_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if not k.startswith("flag:")}, indent=1))
    print({k: v for k, v in rep.items() if k.startswith("flag:")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
