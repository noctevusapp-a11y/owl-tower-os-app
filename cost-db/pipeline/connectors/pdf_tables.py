#!/usr/bin/env python3
"""Extract tables from text-layer PDFs and produce page-image evidence for spot checks.

A text layer does NOT guarantee correct column order (rotated pages, multi-column layouts, overlapping text boxes).
Therefore this tool never emits numbers without a QA sheet:
  1. extract_tables(): pdfplumber tables per page + page number + the text lines found just below each table (notes)
  2. qa_sample(): picks cells deterministically (seeded) and renders a PNG crop of the page with the cell highlighted,
     so a reviewer (or a vision-capable agent) can compare the PNG with the extracted text
  3. words_in_reading_order_check(): flags pages where the text-layer reading order disagrees with left-to-right
     column geometry (a cheap automatic warning, not a substitute for the visual check)

Each extracted norm must be stored with document, edition, page and context (see productivity_observations).
"""
from __future__ import annotations

import hashlib
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExtractedTable:
    pdf: str
    sha256: str
    page: int                                  # 1-based
    index: int
    bbox: tuple[float, float, float, float]
    rows: list[list[Optional[str]]]
    notes_below: list[str] = field(default_factory=list)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_tables(pdf_path: Path, pages: Optional[list[int]] = None) -> list[ExtractedTable]:
    import pdfplumber
    digest = sha256_file(pdf_path)
    out: list[ExtractedTable] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            if pages and pno not in pages:
                continue
            for ti, tbl in enumerate(page.find_tables()):
                rows = [[(c.strip() if isinstance(c, str) else c) for c in row] for row in tbl.extract()]
                x0, top, x1, bottom = tbl.bbox
                below = page.crop((0, bottom, page.width, min(page.height, bottom + 60))).extract_text() or ""
                notes = [ln.strip() for ln in below.splitlines() if ln.strip()]
                out.append(ExtractedTable(str(pdf_path.name), digest, pno, ti, (x0, top, x1, bottom), rows, notes))
    return out


def qa_sample(pdf_path: Path, tables: list[ExtractedTable], out_dir: Path, n: int = 5, seed: int = 20261024,
              dpi: int = 110) -> list[dict]:
    """Render page images with sampled cells highlighted. Returns a manifest (png path, page, row, col, extracted text)."""
    import pdfplumber
    import pypdfium2 as pdfium
    from PIL import ImageDraw
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    cells = [(t, r, c) for t in tables for r, row in enumerate(t.rows) for c, v in enumerate(row) if v]
    rng.shuffle(cells)
    manifest = []
    doc = pdfium.PdfDocument(str(pdf_path))
    with pdfplumber.open(pdf_path) as pdf:
        for t, r, c in sorted(cells[:n], key=lambda x: (x[0].page, x[1], x[2])):
            page = pdf.pages[t.page - 1]
            tbl = page.find_tables()[t.index]
            cell_bbox = tbl.rows[r].cells[c] if r < len(tbl.rows) and c < len(tbl.rows[r].cells) else None
            scale = dpi / 72.0
            img = doc[t.page - 1].render(scale=scale).to_pil().convert("RGB")
            if cell_bbox:
                d = ImageDraw.Draw(img)
                x0, top, x1, bottom = cell_bbox
                d.rectangle([x0 * scale, top * scale, x1 * scale, bottom * scale], outline=(220, 0, 0), width=3)
            png = out_dir / f"{pdf_path.stem}_p{t.page}_t{t.index}_r{r}_c{c}.png"
            img.save(png)
            manifest.append({"png": str(png), "pdf": pdf_path.name, "page": t.page, "table": t.index, "row": r, "col": c,
                             "extracted_text": t.rows[r][c]})
    return manifest


def words_in_reading_order_check(pdf_path: Path, tol: float = 2.0) -> list[dict]:
    """Warn when text-layer order jumps backwards inside the same visual line (columns interleaved or reversed)."""
    import pdfplumber
    warnings = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
            for a, b in zip(words, words[1:]):
                same_line = abs(a["top"] - b["top"]) <= tol
                if same_line and b["x0"] + tol < a["x0"]:
                    warnings.append({"page": pno, "before": a["text"], "after": b["text"],
                                     "note": "text layer jumps right-to-left on one line; verify column order on the page image"})
                    break
    return warnings


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
