"""Build closed wall-footprint faces from the wall-face polylines on A-2.10 (p4) / A-2.20 (p5) of
03_Architectural_Plans_Demo_RCP.pdf with shapely polygonize, keep faces that are mostly bounded by new-wall
layers and are thin (wall-like), and write a debug overlay. Usage: python3 -I wall_faces_test.py <pdf> <outdir>"""
import sys, fitz, math
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
from PIL import Image, ImageDraw
pdf,out=sys.argv[1],sys.argv[2]
d=fitz.open(pdf)
NEW=('a-new-wall','i-new-wall','a-new-wall-low')
BND=NEW+('a-extg-wall','a-extg-partition','a-ex-wall','a-extg-wall-low','a-new-structural','a-extg-struct')
def segs(x):
    pts=[]
    def add(p):
        if not pts or abs(pts[-1]-p)>0.01: pts.append(p)
    out=[]
    for it in x['items']:
        if it[0]=='l': out.append([(it[1].x,it[1].y),(it[2].x,it[2].y)])
        elif it[0]=='c':
            p0,p1,p2,p3=it[1],it[2],it[3],it[4]; pts=[p0]
            for k in range(1,9):
                t=k/8; pts.append(p0*(1-t)**3+p1*3*t*(1-t)**2+p2*3*t*t*(1-t)+p3*t**3)
            out.append([(q.x,q.y) for q in pts])
        elif it[0]=='re':
            r=it[1]; out.append([(r.x0,r.y0),(r.x1,r.y0),(r.x1,r.y1),(r.x0,r.y1),(r.x0,r.y0)])
        elif it[0]=='qu':
            q=it[1]; out.append([(q.ul.x,q.ul.y),(q.ur.x,q.ur.y),(q.lr.x,q.lr.y),(q.ll.x,q.ll.y),(q.ul.x,q.ul.y)])
    return out
for pn in (4,5):
    p=d[pn-1]; dr=p.get_drawings()
    lines=[]; newlines=[]
    for x in dr:
        L=(x.get('layer') or '').split('|')[-1]
        if L in BND and x['type']=='s':
            for s in segs(x):
                ls=LineString(s)
                if ls.length<0.01: continue
                lines.append(ls)
                if L in NEW: newlines.append(ls)
    u=unary_union(lines)
    faces=list(polygonize(u))
    newu=unary_union(newlines)
    keep=[]
    for f in faces:
        A=f.area; P=f.length
        if A<1 or A>8000: continue
        # thickness estimate for a chain: solve 2t^2 - P t + 2A = 0
        disc=P*P-16*A
        t=(P-math.sqrt(disc))/4 if disc>0 else 2*A/P
        if t>14: continue   # thicker than ~1 ft => not a wall
        # share of boundary on new-wall layers
        b=f.exterior
        inter=b.intersection(newu.buffer(0.3))
        share=inter.length/b.length if b.length else 0
        if share<0.45: continue
        keep.append((f,t,share))
    print(pn,'faces',len(faces),'kept',len(keep),'sum centerline ft %.1f'%(sum(f.area/t for f,t,s in keep)/13.5))
    # debug overlay
    ZOOM=2.0
    pix=p.get_pixmap(matrix=fitz.Matrix(ZOOM,ZOOM)); im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples).convert('RGBA')
    ov=Image.new('RGBA',im.size,(255,255,255,0)); drw=ImageDraw.Draw(ov)
    M=p.rotation_matrix*fitz.Matrix(ZOOM,ZOOM)
    def T(pt): q=fitz.Point(pt)*M; return (q.x,q.y)
    for i,(f,t,s) in enumerate(keep):
        col=(255,0,0,120) if s>0.7 else (255,140,0,120)
        drw.polygon([T(c) for c in f.exterior.coords], fill=col, outline=(0,0,255,255))
        c=f.representative_point(); drw.text(T((c.x,c.y)), str(i), fill=(0,0,0,255))
    Image.alpha_composite(im,ov).convert('RGB').save(f'{out}/faces_p{pn}.png')
    import pickle; pickle.dump([(list(f.exterior.coords),t,s) for f,t,s in keep], open(f'{out}/faces_p{pn}.pkl','wb'))
