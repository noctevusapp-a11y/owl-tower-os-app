#!/usr/bin/env python3
"""Turn the 600-dpi OCR of a page into extra per-cell candidates for second_pass.py.

  python3 -I extra_reading.py <book_dir> <parsed_dir> <out_dir>

For every parsed line (its y-range and the page's column bounds/anchors are stored by the parser) the 600-dpi tokens whose
centre falls in the line's rows are assigned to columns like the parser does (centre in the column bounds; a numeric token's
right edge decides between money columns) and read with the same candidate rules. Source tag "H". The crew cell text is
kept too (for the arithmetic-checked crew identification).

Output: <out_dir>/p<page>.json = {"<line index>": {"<col>": [[value, how, "H"], ...], "crew_text": "..."}}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_unit_prices import NUM_COLS, MONEY, candidates, col_of, load_tess  # noqa: E402


def main() -> int:
    book, parsed, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    n_pages = n_lines = 0
    for p in sorted(parsed.glob("p*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        tsv = book / "ocr600" / p.with_suffix(".tsv").name
        if not d.get("header_found") or not tsv.exists() or not d.get("bounds"):
            continue
        w6, h6, toks = load_tess(tsv)
        if not w6 or not toks:
            continue                                            # OCR of this page incomplete
        W = d["page_size"][0]
        s = W / w6                                              # 600-dpi pixels -> the parser's 360-dpi coordinates
        for z in toks:
            for k in ("x0", "x1", "y0", "y1"):
                z[k] = z[k] * s
            z["_yc"] = (z["y0"] + z["y1"]) / 2
        bounds = {k: tuple(v) for k, v in d["bounds"].items()}
        anchors = d.get("anchors") or {}
        desc_end = d["desc_end"]
        res = {}
        for i, ln in enumerate(d["lines"]):
            if "y0" not in ln:
                continue
            row = [z for z in toks if ln["y0"] - 4 <= z["_yc"] <= ln["y1"] + 4]
            cells: dict[str, list] = {k: [] for k in bounds}
            for z in row:
                xc = (z["x0"] + z["x1"]) / 2
                if xc < desc_end:
                    continue
                k = col_of(xc, bounds)
                if anchors and k in MONEY and re.search(r"\d", z["t"]):
                    near = min(anchors.items(), key=lambda kv: abs(kv[1] - z["x1"]))
                    if near[0] in MONEY and abs(near[1] - z["x1"]) <= 70:
                        k = near[0]
                if k:
                    cells[k].append(z)
            entry = {}
            for k in NUM_COLS:
                raw = "".join(z["t"] for z in cells.get(k, []))
                if "%" in raw:
                    continue
                cs = [[str(v), how, "H"] for v, how in candidates(raw, k)]
                if cs:
                    entry[k] = cs
            crew_txt = " ".join(z["t"] for z in cells.get("crew", [])).strip(" |:;.,'‘’`\"~=_")
            if crew_txt:
                entry["crew_text"] = crew_txt
            unit_txt = " ".join(z["t"] for z in cells.get("unit", [])).strip(" |:;,'‘’`\"~=_")
            if unit_txt:
                entry["unit_text"] = unit_txt
            if entry:
                res[str(i)] = entry
                n_lines += 1
        (out / p.name).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        n_pages += 1
    print(f"extra readings: {n_pages} pages, {n_lines} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
