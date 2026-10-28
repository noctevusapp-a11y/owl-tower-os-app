"""Cut a 200-dpi sheet render into overlapping crops with a labelled 100-px grid so that
duct / pipe end points can be read off in page-pixel coordinates (used for LF measurement).
Usage: python3 -I grid_crops.py <page.jpg> <outdir> <tag> x0 y0 x1 y1 [crop=1300] [step=1100]
Page renders are 6800x4400 px = 34x22 in at 200 dpi; at 3/16"=1'-0" one foot = 37.5 px.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
src, outdir, tag = sys.argv[1:4]
x0, y0, x1, y1 = map(int, sys.argv[4:8])
crop = int(sys.argv[8]) if len(sys.argv) > 8 else 1300
step = int(sys.argv[9]) if len(sys.argv) > 9 else 1100
os.makedirs(outdir, exist_ok=True)
im = Image.open(src).convert('RGB')
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
except Exception:
    font = ImageFont.load_default()
n = 0
for cy in range(y0, y1, step):
    for cx in range(x0, x1, step):
        box = (cx, cy, min(cx + crop, im.width), min(cy + crop, im.height))
        c = im.crop(box)
        d = ImageDraw.Draw(c)
        for gx in range((box[0] // 100) * 100, box[2], 100):
            X = gx - box[0]
            if X < 0: continue
            d.line([(X, 0), (X, c.height)], fill=(255, 0, 0) if gx % 500 == 0 else (255, 160, 160), width=1)
            d.text((X + 2, 2), str(gx), fill=(200, 0, 0), font=font)
        for gy in range((box[1] // 100) * 100, box[3], 100):
            Y = gy - box[1]
            if Y < 0: continue
            d.line([(0, Y), (c.width, Y)], fill=(0, 0, 255) if gy % 500 == 0 else (160, 160, 255), width=1)
            d.text((2, Y + 2), str(gy), fill=(0, 0, 200), font=font)
        name = f"{tag}_x{cx}_y{cy}.jpg"
        c.save(os.path.join(outdir, name), quality=85)
        n += 1
print(n, 'crops in', outdir)
