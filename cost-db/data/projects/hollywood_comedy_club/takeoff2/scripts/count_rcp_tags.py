"""Count light-fixture tags and switch symbols on the vector RCPs
(03_Architectural_Plans_Demo_RCP.pdf p6 = A-3.12 1st floor RCP, p7 = A-3.22 mezzanine RCP;
identical text to IFB Interior Design part01 p8/p9). The pages carry a /Rotate, so word boxes
are mapped through page.rotation_matrix before splitting plan area from the legend/keynote
column (displayed x >= 72% of the sheet width). Tags: A1, B1, C1, C2, D1, F1, G1..G21, X1, X2,
Y1, Y2, Y3; switch symbols: S, S3, S4, D, DB. Legend-column hits are listed separately.
Usage: python3 -I count_rcp_tags.py <pdf>
"""
import sys, re, collections, pymupdf
doc = pymupdf.open(sys.argv[1])
TAG = re.compile(r'^(A1|B1|C1|C2|D1|F1|G\d{1,2}|X1|X2|Y1|Y2|Y3)$')
SW = re.compile(r'^(S|S\d|D|DB|DB\d|D\d)$')
for pno, sheet in ((6, 'A-3.12 1st floor RCP'), (7, 'A-3.22 mezzanine RCP')):
    page = doc[pno - 1]
    M = page.rotation_matrix
    W = page.rect.width
    words = []
    for w in page.get_text("words"):
        p = pymupdf.Point(w[0], w[1]) * M
        words.append((p.x, p.y, w[4]))
    plan = [w for w in words if w[0] < W * 0.72]
    legend = [w for w in words if w[0] >= W * 0.72]
    c = collections.Counter(w[2] for w in plan if TAG.match(w[2]))
    cl = collections.Counter(w[2] for w in legend if TAG.match(w[2]))
    sw = collections.Counter(w[2] for w in plan if SW.match(w[2]))
    swl = collections.Counter(w[2] for w in legend if SW.match(w[2]))
    print(f"== {sheet} (PDF p{pno}), rotation {page.rotation}")
    print("  plan-area fixture tags:", dict(sorted(c.items())), " total", sum(c.values()))
    print("  legend-column fixture tags:", dict(sorted(cl.items())))
    print("  plan-area switch symbols:", dict(sorted(sw.items())))
    print("  legend-column switch symbols:", dict(sorted(swl.items())))
    print("  switch positions (displayed pt):", [(w[2], round(w[0]), round(w[1])) for w in plan if SW.match(w[2])])
    print("  (E) fixture tags:", [(w[2], round(w[0]), round(w[1])) for w in plan if w[2].startswith('(E)')])
