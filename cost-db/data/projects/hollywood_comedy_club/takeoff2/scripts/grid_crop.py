#!/usr/bin/env python3
"""Crop a raster sheet and overlay a labelled pixel grid (original-image pixel
coordinates) so positions can be read off the image for calibrated scaling.
Sheets are 34x22 in plotted 1:1 and rendered at 110 dpi, so a 3/16"=1'-0"
plan is 20.625 px/ft (checked against the 16'-0" column bays on S-2.20).

usage: grid_crop.py <in_jpg> <out_jpg> x0 y0 x1 y1 [step_px] [scale]
"""
import sys
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7]); step = int(sys.argv[7]) if len(sys.argv) > 7 else 100
scale = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
im = Image.open(src).convert("RGB").crop((x0, y0, x1, y1))
if scale != 1.0: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
dr = ImageDraw.Draw(im); f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
gx = (x0 // step + 1) * step
while gx < x1:
    X = (gx - x0) * scale; dr.line([(X, 0), (X, im.height)], fill=(0, 120, 255), width=1); dr.text((X + 2, 2), str(gx), fill=(0, 90, 220), font=f); gx += step
gy = (y0 // step + 1) * step
while gy < y1:
    Y = (gy - y0) * scale; dr.line([(0, Y), (im.width, Y)], fill=(0, 120, 255), width=1); dr.text((2, Y + 2), str(gy), fill=(0, 90, 220), font=f); gy += step
im.save(out, quality=88); print(out, im.size)
