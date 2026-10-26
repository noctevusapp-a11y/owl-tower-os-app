#!/usr/bin/env python3
"""Resumable OCR of scanned PDF parts: one TSV (word boxes + confidence) and one TXT per page.

  python3 ocr_pages.py <out_dir> <part.pdf> [<part.pdf> ...]   [--dpi 300] [--workers 4] [--psm 6]

The page number inside the book is taken from the part file name (rsmeans_partNN_pAAAA-BBBB.pdf) when present,
otherwise pages are numbered from 1 within the part. Already-finished pages (TSV present and non-empty) are skipped,
so an interrupted run can simply be restarted.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pymupdf

RANGE_RE = re.compile(r"_p(\d{3,5})-(\d{3,5})\.pdf$", re.I)


def page_jobs(parts: list[Path]) -> list[tuple[Path, int, int]]:
    jobs = []
    for part in parts:
        doc = pymupdf.open(part)
        m = RANGE_RE.search(part.name)
        first = int(m.group(1)) if m else 1
        for i in range(doc.page_count):
            jobs.append((part, i, first + i))
        doc.close()
    return jobs


def ocr_one(part: Path, index: int, book_page: int, out: Path, dpi: int, psm: int) -> tuple[int, str]:
    tsv = out / f"p{book_page:04d}.tsv"
    txt = out / f"p{book_page:04d}.txt"
    if tsv.exists() and tsv.stat().st_size > 0 and txt.exists():
        return book_page, "skip"
    doc = pymupdf.open(part)
    page = doc[index]
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    with tempfile.TemporaryDirectory() as td:
        img = Path(td) / "page.png"
        pix.save(img)
        doc.close()
        base = Path(td) / "ocr"
        cmd = ["tesseract", str(img), str(base), "--psm", str(psm), "-c", "preserve_interword_spaces=1", "tsv", "txt"]
        # one OpenMP thread per process: several multi-threaded tesseracts on 4 cores stall for minutes per page
        r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, OMP_THREAD_LIMIT="1"))
        if r.returncode:
            return book_page, "ERROR " + r.stderr.strip()[-200:]
        (out / f"p{book_page:04d}.tsv.tmp").write_bytes((base.with_suffix(".tsv")).read_bytes())
        txt.write_bytes((base.with_suffix(".txt")).read_bytes())
    os.replace(out / f"p{book_page:04d}.tsv.tmp", tsv)
    return book_page, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--psm", type=int, default=6)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    jobs = page_jobs([Path(p) for p in a.parts])
    print(f"{len(jobs)} pages in {len(a.parts)} part(s) -> {out}", flush=True)
    done = skipped = errors = 0
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(ocr_one, part, i, bp, out, a.dpi, a.psm) for part, i, bp in jobs]
        for f in as_completed(futs):
            bp, st = f.result()
            if st == "ok":
                done += 1
            elif st == "skip":
                skipped += 1
            else:
                errors += 1
                print(f"page {bp}: {st}", flush=True)
            if (done + skipped + errors) % 25 == 0:
                print(f"  {done + skipped + errors}/{len(jobs)} (ocr {done}, skipped {skipped}, errors {errors})", flush=True)
    print(f"finished: ocr {done}, skipped {skipped}, errors {errors}", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
