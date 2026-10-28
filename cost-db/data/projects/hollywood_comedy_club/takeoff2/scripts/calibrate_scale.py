"""Scale calibration for the raster P-/M-sheets: the architectural A-2.10 (vector, same 34x22 in
sheet, same 3/16"=1'-0" plan scale) carries dimension strings between column grid lines.
Prints the grid-bubble numbers and dimension strings in the top band of A-2.10 with x positions
(PDF points, 72/in) so that px/ft on the 200-dpi renders can be checked against the drawn text.
Usage: python3 -I calibrate_scale.py <arch pdf>
"""
import sys, re, pymupdf
doc = pymupdf.open(sys.argv[1])
page = doc[3]  # A-2.10
words = page.get_text("words")
dim = re.compile(r"^\d+'-\d+(\s?\d/\d)?\"?$|^\d+'-\d+\"$|^\d+'$")
grid = re.compile(r"^(1|2|3|4|4\.5|5|6|A|B|C|D|E|F)$")
print("== dimension strings on A-2.10 (x, y in pt):")
for w in sorted(words, key=lambda w: (round(w[1]/20), w[0])):
    if dim.match(w[4]):
        print(f"  {w[4]:>12}  x={w[0]:7.1f} y={w[1]:7.1f}")
print("== grid-like single tokens (top band y<260 or left band x<300):")
for w in sorted(words, key=lambda w: (w[1], w[0])):
    if grid.match(w[4]) and (w[1] < 260 or w[0] < 300 or w[0] > 1900):
        print(f"  {w[4]:>4}  x={w[0]:7.1f} y={w[1]:7.1f}")
print("== scale strings:")
for w in words:
    if 'SCALE' in w[4].upper():
        line = [v[4] for v in words if abs(v[1]-w[1]) < 3 and v[0] >= w[0]][:6]
        print("  ", ' '.join(line), f"at x={w[0]:.0f} y={w[1]:.0f}")
