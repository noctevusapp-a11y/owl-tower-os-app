#!/usr/bin/env python3
"""Second full-page OCR of the unit-price pages at 600 dpi (tesseract, psm 6): an additional reading of every cell.

  python3 -I ocr_pages_600.py <book_dir> <first> <last>      pages with an existing 360-dpi OCR only; resumable

Writes <book_dir>/ocr600/p<page>.tsv (tesseract TSV in 600-dpi pixel coordinates).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pymupdf
from PIL import Image

PARTS = [("rsmeans_part01_p0001-0164.pdf", 1, 164), ("rsmeans_part02_p0165-0340.pdf", 165, 340), ("rsmeans_part03_p0341-0526.pdf", 341, 526),
         ("rsmeans_part04_p0527-0711.pdf", 527, 711), ("rsmeans_part05_p0712-0847.pdf", 712, 847), ("rsmeans_part06_p0848-0964.pdf", 848, 964)]


def main() -> int:
    book = Path(sys.argv[1])
    first, last = int(sys.argv[2]), int(sys.argv[3])
    out = book / "ocr600"
    out.mkdir(exist_ok=True)
    docs = {}
    env = {**os.environ, "OMP_THREAD_LIMIT": "1"}
    n = 0
    for p in range(first, last + 1):
        if not (book / "ocr" / f"p{p:04d}.tsv").exists() or (out / f"p{p:04d}.tsv").exists():
            continue
        part = next((f for f, a, b in PARTS if a <= p <= b), None)
        if part is None:
            continue
        if part not in docs:
            docs[part] = pymupdf.open(book / "parts" / part)
        a = next(a for f, a, b in PARTS if f == part)
        pix = docs[part][p - a].get_pixmap(dpi=600, colorspace=pymupdf.csGRAY)
        png = out / f"p{p:04d}.png"
        Image.frombytes("L", (pix.width, pix.height), pix.samples).save(png)
        subprocess.run(["tesseract", str(png), str(out / f"p{p:04d}"), "--psm", "6", "tsv"], capture_output=True, env=env)
        png.unlink(missing_ok=True)
        n += 1
        if n % 25 == 0:
            print(f"  {n} pages", flush=True)
    print(f"done {n} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
