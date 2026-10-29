"""Render a PDF page at <dpi> and save crops given as fractions of the displayed page (x0,y0,x1,y1 in 0..1).
usage: crop.py <pdf> <page> <dpi> <out_prefix> [name:x0,y0,x1,y1 ...] ; with no boxes saves the full page."""
import sys, pymupdf
from PIL import Image
pdf, pn, dpi, pref = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
p = pymupdf.open(pdf)[pn-1]
pix = p.get_pixmap(dpi=dpi)
im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
W, H = im.size
if len(sys.argv) == 5:
    im.save(f'{pref}_full.jpg', quality=85); print(pref, W, H); sys.exit()
for a in sys.argv[5:]:
    name, box = a.split(':'); x0, y0, x1, y1 = [float(v) for v in box.split(',')]
    c = im.crop((int(x0*W), int(y0*H), int(x1*W), int(y1*H)))
    c.save(f'{pref}_{name}.jpg', quality=88); print(name, c.size)
