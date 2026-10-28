"""Debug render of wall-related CAD layers on A-2.10 (p4) and A-2.20 (p5) of the vector PDF
03_Architectural_Plans_Demo_RCP.pdf, to identify which layers carry the new walls before measuring.
Usage: python3 -I wall_debug_render.py <pdf> <out_dir>
"""
import sys, fitz
from PIL import Image, ImageDraw
pdf, out = sys.argv[1], sys.argv[2]
d = fitz.open(pdf)
COLORS = {
 'a-new-wall': (255,0,0), 'i-new-wall': (255,0,255), 'a-new-wall-low': (255,140,0),
 'a-new-bar-diewall': (128,0,128), 'i-new-poche': (0,0,255), 'a-poche': (0,160,0),
 'a-extg-wall': (150,150,150), 'a-extg-partition': (120,120,200), 'A-Wall-Iden': (0,200,200),
}
ZOOM = 2.0
for pn in (4,5):
    p = d[pn-1]
    pix = p.get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM))
    im = Image.frombytes('RGB',[pix.width,pix.height],pix.samples).convert('RGBA')
    ov = Image.new('RGBA', im.size, (255,255,255,0)); dr = ImageDraw.Draw(ov)
    M = p.rotation_matrix * fitz.Matrix(ZOOM,ZOOM)   # unrotated drawing coords -> rendered pixmap coords
    def T(pt):
        q = fitz.Point(pt)*M; return (q.x,q.y)
    for x in p.get_drawings():
        L = (x.get('layer') or '').split('|')[-1]
        if L not in COLORS: continue
        col = COLORS[L]
        if x['type']=='fs' or x['type']=='f':
            for it in x['items']:
                if it[0]=='l': dr.line([T(it[1]),T(it[2])], fill=col+(255,), width=3)
                elif it[0]=='re':
                    r=it[1]; pts=[T((r.x0,r.y0)),T((r.x1,r.y0)),T((r.x1,r.y1)),T((r.x0,r.y1))]; dr.polygon(pts, fill=col+(110,))
                elif it[0]=='qu':
                    q=it[1]; pts=[T(q.ul),T(q.ur),T(q.lr),T(q.ll)]; dr.polygon(pts, fill=col+(110,))
                elif it[0]=='c':
                    dr.line([T(it[1]),T(it[4])], fill=col+(255,), width=2)
        else:
            for it in x['items']:
                if it[0]=='l': dr.line([T(it[1]),T(it[2])], fill=col+(255,), width=2)
                elif it[0]=='c': dr.line([T(it[1]),T(it[4])], fill=col+(255,), width=2)
                elif it[0]=='re':
                    r=it[1]; pts=[T((r.x0,r.y0)),T((r.x1,r.y0)),T((r.x1,r.y1)),T((r.x0,r.y1)),T((r.x0,r.y0))]; dr.line(pts, fill=col+(255,), width=2)
                elif it[0]=='qu':
                    q=it[1]; pts=[T(q.ul),T(q.ur),T(q.lr),T(q.ll),T(q.ul)]; dr.line(pts, fill=col+(255,), width=2)
    im = Image.alpha_composite(im, ov).convert('RGB')
    im.save(f'{out}/walls_p{pn}.png')
    print(pn, im.size)
