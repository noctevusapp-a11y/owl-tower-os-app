#!/usr/bin/env python3
"""Crop the K2.0 equipment schedule (BIRD CAGE DRAWINGS 062626, page 4, 200-dpi render
<DOCS_ROOT>/kelly_tiles/K_p04.jpg) into readable strips so the schedule can be read
row by row. Output goes to the directory given as argv[1].

Column bands (full-resolution pixel x on the 7200x4800 render, measured on the page):
  item+description+qty+make/model+remarks : 2460-3900
  item no. column only                    : 2460-2900
  plumbing block                          : 3880-5010
  electrical block                        : 5000-6490
Row bands: header 200-380, body 370-4540 in four overlapping strips.
"""
import os
import sys

from PIL import Image

# DOCS_ROOT = the extraction folder that holds kelly_tiles/ and kelly_txt/ (set KELLY_DOCS_ROOT)
DOCS_ROOT = os.environ["KELLY_DOCS_ROOT"]
SRC = os.path.join(DOCS_ROOT, "kelly_tiles", "K_p04.jpg")
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
im = Image.open(SRC)

bands = [(200, 1300), (1250, 2350), (2300, 3400), (3350, 4560)]
cols = {
    "left": (2460, 3900),
    "plumb": (3880, 5010),
    "elec": (5000, 6490),
}
item_col = (2460, 2900)

for bi, (y0, y1) in enumerate(bands):
    # left block alone
    x0, x1 = cols["left"]
    im.crop((x0, y0, x1, y1)).save(os.path.join(out, f"K2_left_{bi}.png"))
    # item column stitched beside plumbing and electrical blocks
    for name in ("plumb", "elec"):
        x0, x1 = cols[name]
        a = im.crop((item_col[0], y0, item_col[1], y1))
        b = im.crop((x0, y0, x1, y1))
        w = a.width + b.width + 10
        canvas = Image.new("RGB", (w, y1 - y0), "white")
        canvas.paste(a, (0, 0))
        canvas.paste(b, (a.width + 10, 0))
        canvas.save(os.path.join(out, f"K2_{name}_{bi}.png"))

# header strip across the whole schedule
im.crop((2460, 200, 6490, 400)).save(os.path.join(out, "K2_header.png"))
# footer legend
im.crop((2460, 4460, 6490, 4560)).save(os.path.join(out, "K2_footer.png"))
print("done", out)
