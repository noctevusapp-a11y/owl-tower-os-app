#!/usr/bin/env python3
"""Random spot check of the parsed table against the page images.

  python3 -I spot_check.py <book_lines.csv> <parsed_dir> <parts_dir> <out_dir> [--n 40] [--seed 1] [--status verified]

Picks n random rows with the given status, cuts the printed row out of the page image (full width, ~150 dpi) and writes
contact sheets (10 rows per sheet) with the parsed values printed under each crop, plus sample.csv listing the rows so a
reviewer can mark each one right/wrong. The parsed row is located by the y of its line-number token in the OCR word boxes.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont


def parts_map(parts_dir: Path) -> dict:
    out = {}
    for p in sorted(parts_dir.glob("*.pdf")):
        m = re.search(r"_p(\d{4})-(\d{4})\.pdf$", p.name)
        if m:
            out[(int(m.group(1)), int(m.group(2)))] = p
    return out


def page_doc(pmap: dict, pdf_page: int):
    for (a, b), path in pmap.items():
        if a <= pdf_page <= b:
            return pymupdf.open(path), pdf_page - a
    raise KeyError(pdf_page)


def row_y(ocr_dir: Path, pdf_page: int, line: str, desc: str) -> tuple[int, int, int] | None:
    """(y0, y1, image_height) of the printed row: the line-number token followed by the first word of the description."""
    tsv = ocr_dir / f"p{pdf_page:04d}.tsv"
    words = []
    h = 0
    with tsv.open(encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["level"] == "1":
                h = int(r["height"])
            if r["level"] == "5" and r["text"].strip():
                words.append((int(r["left"]), int(r["top"]), int(r["width"]), int(r["height"]), r["text"].strip()))
    first = (desc.split() or [""])[0][:4].lower()
    cands = [w for w in words if w[0] < 230 and (w[4] == line or (line and w[4] == line[-3:] and w[0] < 60))]
    best = None
    for w in cands:
        yc = w[1] + w[3] / 2
        same = [z for z in words if abs(z[1] + z[3] / 2 - yc) < 18 and z[0] > w[0] + 30]
        if not first or any(z[4][:4].lower() == first for z in same):
            best = w
            break
    if best is None:
        return None                                            # no row with this number AND this description: skip rather than show a neighbour
    return best[1] - 8, best[1] + best[3] + 8, h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines_csv")
    ap.add_argument("ocr_dir")
    ap.add_argument("parts_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--status", default="verified")
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(a.lines_csv, encoding="utf-8")) if r["status"] == a.status and r["line"]]
    random.seed(a.seed)
    sample = random.sample(rows, min(a.n, len(rows)))
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pmap = parts_map(Path(a.parts_dir))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15) if Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf").exists() else ImageFont.load_default()
    sheets = []
    crops = []
    for i, r in enumerate(sample):
        p = int(r["pdf_page"])
        doc, idx = page_doc(pmap, p)
        pg = doc[idx]
        yy = row_y(Path(a.ocr_dir), p, r["line"] if not r["flags"] or "LINE_NUMBER_RECONSTRUCTED" not in r["flags"] else r["line"][-3:], r["description"])
        if yy is None:
            continue
        y0, y1, h = yy
        scale = pg.rect.height / h
        clip = pymupdf.Rect(0, max(0, y0 * scale - 2), pg.rect.width, min(pg.rect.height, y1 * scale + 2))
        pix = pg.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY, clip=clip)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        text = (f"#{i + 1} p{p} {r['section_id']} {r['line']} | crew {r['crew'] or '-'} out {r['daily_output'] or '-'} hrs {r['labor_hours'] or '-'} "
                f"{r['unit'] or '-'} | M {r['material_2022'] or '-'} L {r['labor_2022'] or '-'} E {r['equipment_2022'] or '-'} T {r['total_2022'] or '-'} "
                f"O&P {r['total_incl_op_2022'] or '-'} | {r['flags']}")
        crops.append((img, text, r))
    W = max(c[0].width for c in crops) if crops else 1200
    per = 10
    for s in range(0, len(crops), per):
        chunk = crops[s:s + per]
        H = sum(c[0].height + 26 for c in chunk) + 10
        sheet = Image.new("L", (W, H), 255)
        dr = ImageDraw.Draw(sheet)
        y = 5
        for img, text, r in chunk:
            sheet.paste(img, (0, y))
            y += img.height
            dr.text((4, y + 2), text[:230], fill=0, font=font)
            y += 26
        name = out / f"sheet_{s // per + 1:02d}.png"
        sheet.save(name)
        sheets.append(name)
    with (out / "sample.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["no", "pdf_page", "section_id", "line", "crew", "daily_output", "labor_hours", "unit", "material_2022", "labor_2022", "equipment_2022", "total_2022", "total_incl_op_2022", "flags", "reviewer_verdict"])
        for i, (img, text, r) in enumerate(crops, 1):
            w.writerow([i, r["pdf_page"], r["section_id"], r["line"], r["crew"], r["daily_output"], r["labor_hours"], r["unit"], r["material_2022"], r["labor_2022"], r["equipment_2022"], r["total_2022"], r["total_incl_op_2022"], r["flags"], ""])
    print(f"{len(crops)} rows on {len(sheets)} sheet(s) in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
