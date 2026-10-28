#!/usr/bin/env python3
"""Crop detail regions from the 200-dpi K-sheet renders so the small tables can be read:
  K7.0 hood information tables (K_p09), K8.0 walk-in plan (K_p11), K8.2 refrigeration
  specification table + accessories (K13_p01), K1.0 equipment plan kitchen area (K_p02),
  KN notes columns (K13_p05). Output directory = argv[1].
Pixel boxes are on the 7200x4800 renders (K13_p03 is 6800x4400 but is not used here).
"""
import os
import sys

from PIL import Image

# DOCS_ROOT = the extraction folder that holds kelly_tiles/ and kelly_txt/ (set KELLY_DOCS_ROOT)
T = os.path.join(os.environ["KELLY_DOCS_ROOT"], "kelly_tiles") + os.sep
out = sys.argv[1]
os.makedirs(out, exist_ok=True)

crops = {
    # K7.0 hood information / filters / options / utility cabinet tables
    "K70_hood_info": ("K_p09.jpg", (1260, 440, 4720, 1360)),
    "K70_hood_opts": ("K_p09.jpg", (1260, 1300, 4720, 2000)),
    "K70_notes": ("K_p09.jpg", (5000, 3400, 5950, 4000)),
    # K8.0 walk-in plan
    "K80_plan": ("K_p11.jpg", (1400, 1300, 4700, 3700)),
    # K8.2 refrigeration spec table + accessories + panel construction
    "K82_refrig": ("K13_p01.jpg", (560, 2080, 2650, 2560)),
    "K82_access": ("K13_p01.jpg", (560, 1140, 2650, 1520)),
    "K82_panel": ("K13_p01.jpg", (560, 420, 3500, 1130)),
    # K1.0 plan, kitchen area (two halves for legibility)
    "K10_plan_W": ("K_p02.jpg", (2000, 600, 3500, 2950)),
    "K10_plan_E": ("K_p02.jpg", (3300, 600, 4500, 2950)),
    # KN notes columns
    "KN_gc": ("K13_p05.jpg", (580, 540, 1740, 4360)),
    "KN_plumb": ("K13_p05.jpg", (1740, 540, 2880, 4360)),
    "KN_elec": ("K13_p05.jpg", (2880, 540, 4020, 4360)),
    "KN_elec2_curb": ("K13_p05.jpg", (4020, 540, 5140, 4360)),
    "KN_refrig_hood": ("K13_p05.jpg", (5140, 540, 6260, 4360)),
}
for name, (src, box) in crops.items():
    im = Image.open(T + src)
    c = im.crop(box)
    c.save(os.path.join(out, name + ".png"))
    print(name, c.size)
