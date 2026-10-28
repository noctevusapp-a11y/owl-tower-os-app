#!/usr/bin/env python3
"""Digest the Thatz Hilarious Cutsheet Book (061426) text layer into a per-page extract:
page number, the "Item #" marker, the header line (manufacturer / model as the book's
stamp prints it) and every line that carries a dimension, electrical, gas or plumbing
value. Output: argv[1] (a text file). Input text files are pdftotext -layout output,
pages separated by form feed, in <DOCS_ROOT>/kelly_txt/.
"""
import glob
import os
import re
import sys

# DOCS_ROOT = the extraction folder that holds kelly_tiles/ and kelly_txt/ (set KELLY_DOCS_ROOT)
SRC = sorted(glob.glob(os.path.join(
    os.environ["KELLY_DOCS_ROOT"], "kelly_txt",
    "IFB__Health_Plan_Check__Thatz_Hilarious_CutsheetBook_-_061426_part0*.txt")))
KEY = re.compile(
    r"(?i)(volt|amp|watt|\bkw\b|\bhp\b|btu|phase|\bph\b|nema|plug|cord|hz|"
    r"\bgas\b|drain|inlet|water|cold|hot|psi|gpm|gal|"
    r"width|depth|height|dimension|overall|\bw\s*x\s*d|\d+\s*[\"”]|\bmm\b|lbs|weight|"
    r"model|item\s*#|qty|quantity|capacity|cfm|door|shelf|shelves|compressor|refrigerant|"
    r"r-?\d{3}|stainless|galvanized|caster|legs)")
out = open(sys.argv[1], "w")
for f in SRC:
    m = re.search(r"p(\d{4})-(\d{4})", f)
    start, end = int(m.group(1)), int(m.group(2))
    pages = open(f, errors="replace").read().split("\f")
    for i, p in enumerate(pages):
        n = start + i
        if n > end:
            break
        lines = [re.sub(r"\s{2,}", "  ", l.strip()) for l in p.splitlines() if l.strip()]
        items = sorted(set(re.findall(r"(?i)item\s*#\s*(\d{1,3})", p)))
        out.write(f"\n===== CUTSHEET PAGE {n}  item_markers={items}\n")
        if lines:
            out.write("HDR: " + lines[0][:200] + "\n")
        seen = 0
        for l in lines[1:]:
            if KEY.search(l) and len(l) < 260:
                out.write("  " + l + "\n")
                seen += 1
                if seen > 45:
                    out.write("  ...\n")
                    break
out.close()
print("written", sys.argv[1])
