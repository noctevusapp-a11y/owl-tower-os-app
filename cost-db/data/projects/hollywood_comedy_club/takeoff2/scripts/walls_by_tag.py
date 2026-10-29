"""Wall-type assignment of the poche components measured by poche_walls.py (same mask parameters), with two merged
components split by sub-box, and the LF summary by page / wall tag / hatched (full height) used in arch.csv.

Assignment rules (every component >= 0.4 LF and >= 2.5 in drawn thickness inside the tenant plan area):
  * tick tag from poche_walls.py where the component carries an 'A-Wall-Iden' tick (tick label checked on the overlay
    crops poche/p4_*.jpg, poche/p5_*.jpg);
  * untagged components take the tag of the wall line they continue (same line, split only by a door or tick), or the
    tag printed on that enclosure (dumbwaiter / grease interceptor / grease duct shaft / ADA lift = '1' per A-6.30 note 4,
    A-2.10 KN14, A-3.12 KN8; mezzanine restroom and mechanical-room walls = '2' per their ticks);
  * dropped: gray items that are not stud walls (dumbwaiter car, ADA-lift pit hatch, the two diagonal strips in the
    N.I.C. retail shop, stair tread edges, equipment, exit-stair walls under permit 26016-10000-18605).
Day-2 walls (layer 2604-FP-02_Day2) are summed separately.
Usage: python3 -I walls_by_tag.py <pdf> <outdir>
"""
import sys, csv, math, collections, pymupdf, numpy as np, cv2
from skimage.morphology import skeletonize
PT_PER_FT = 13.5; Z = 4.0; PX_PER_FT = PT_PER_FT * Z
pdf, out = sys.argv[1], sys.argv[2]
EXCL = {4: [(343, 930, 612, 1290), (1690, 1355, 1840, 1395)], 5: [(343, 938, 720, 1290), (1690, 1355, 1840, 1395)]}
# component -> (tag, reason)   ('X' = dropped, 'D2' = Day-2)
ASSIGN = {
 4: {1774: ('1', 'stair 1 enclosure, tick 1'), 1999: ('1', 'stair 1 enclosure L, hatched, continues 1774'),
     2211: ('1', 'door 05 jamb piece, tick 1'), 2384: ('1', 'door 05 jamb piece, same line'), 2476: ('1', 'between doors 05/06, tick 1'),
     2477: ('1', 'between doors 05/06, same line'), 1944: ('3', 'exterior infill at removed window (A-4.01 KN9/13), tick 3'),
     1985: ('3', 'same exterior infill line'), 2616: ('3', 'exterior infill piece below door 06, tick 3'),
     2609: ('SPLIT', 'top run = stair-1 south wall (tick 1 at its west end); vertical run along storefront = 2 TYP.'),
     1879: ('AC', 'tick AC (wall around column at hallway 04)'), 1780: ('1A', 'tick 1A, 6 in stud (kitchen east wall)'),
     2854: ('1A', 'same line as 1780 south of the 1A tick (6 in stud jog at kitchen doors)'),
     1934: ('X', 'diagonal strip inside (E) retail shop N.I.C.'), 2931: ('X', 'diagonal strip inside (E) retail shop N.I.C.'),
     3283: ('2', 'kitchen-vestibule / wait-station L wall, untagged; nearest tags 2 (667,732) and 2 (745,856)'),
     4438: ('TICKS', 'tick split: 1 = grease-interceptor 1-hr shaft (KN14), 2 = wait-station wall'),
     3094: ('2', 'straight wall x=1260, tick 2 line'), 3556: ('2', 'straight wall x=1260'), 4206: ('2', 'tick 2'), 4528: ('2', 'straight wall x=1260'),
     2370: ('TICKS', 'tick split: 2 = straight wall x=1260 top run, AC = curved acoustic wall'),
     4739: ('AC', 'tick AC, curved wall south run'), 5524: ('AC', 'curved wall piece at (E) bar, same line as 4739'),
     5565: ('AC', 'tick AC, ADA lift'), 6143: ('TICKS', 'tick split: 1 = lift shaft, AC = lift lobby wall'),
     6090: ('1', 'tick 1, KN13 wall filling (E) opening at ADA lift'), 6409: ('X', 'ADA-lift pit/platform hatch (17 LF inside a 4x4 ft box)'),
     4001: ('2', 'kitchen/hallway wall piece between doors 07-08, tag 2 (1185,748)'), 4415: ('2', 'same wall'), 4535: ('2', 'tick 2'),
     5374: ('1', 'dumbwaiter shaft west wall, tick 1 (A-6.30 note 4: 1-hr)'), 5509: ('1', 'dumbwaiter shaft'), 5510: ('1', 'dumbwaiter shaft'),
     5381: ('1', 'tick 1, hatched (wait station / hallway)'), 5435: ('X', 'dumbwaiter car symbol'),
     3760: ('2', 'tick 2, storefront-line wall east'), 4531: ('2', 'storefront-line wall east, same line'),
     5757: ('2', 'tick 2'), 5842: ('2', 'storefront-line wall at host/green-room junction'), 6157: ('2', 'tick 2'), 6462: ('2', 'same line'),
     5182: ('AC', 'tick AC host north wall'), 5183: ('AC', 'tick AC host north wall'), 5352: ('AC', 'host west wall, AC tick at its north end (1682,873)'),
     5864: ('AC', 'tick AC host/green-room partition'), 6164: ('AC', 'green-room west wall above AC tick (1650,1196)'), 6461: ('AC', 'green-room west wall below that tick'),
     6679: ('2', 'south storefront lining wall, hatched; tick 2 on 6681'), 6681: ('2', 'tick 2'), 6674: ('2', 'south storefront lining wall'), 6682: ('2', 'same'),
     2105: ('X', '2.5 in exterior finish piece beside door 06 (plaster/metal panel, A-4.01)'), 2189: ('X', 'dry-storage shelving edge'),
     1941: ('X', '2 in line at stair 1 (not a stud wall)'), 1792: ('X', 'thin'), 2803: ('X', 'thin equipment edge'), 4093: ('X', 'thin equipment edge')},
 5: {1748: ('1', 'stair 1 enclosure, tick 1'), 1840: ('1', 'tick 1'), 1847: ('1', 'stair 1 enclosure L, hatched, continues 1840'),
     1968: ('1', 'tick 1, stair 1 enclosure'), 1692: ('1', 'mech room 3 west wall, tick 1'), 1916: ('1', 'mech room 3 wall, same line as 1692'),
     2094: ('2', 'tick 2 mech room 3'), 1751: ('3', 'exterior infill line at NE corner (same line as A-2.10 1944)'), 1785: ('3', 'tick 3'),
     2263: ('3', 'tick 3'), 2408: ('3', 'tick 3'), 2490: ('2', 'tick 2 storefront-line wall east'), 2910: ('2', 'same line'), 3462: ('2', 'same line, hatched'),
     5215: ('2', 'tick 2'), 5426: ('2', 'storefront-line wall + mech room 2 north wall, tick 2 at (1795,1134)'), 5469: ('2', 'tick 2'),
     5459: ('2', 'mech room 1/2 wall piece at door 30'), 5614: ('2', 'tick 2 wall between mech rooms 1 and 2'),
     6032: ('2', 'south storefront lining wall under mech room 1, hatched (A-2.10 line tagged 2)'), 6033: ('2', 'same, under mech room 2'),
     1738: ('2', 'west edge wall above the tick 2 (651,461)'), 2582: ('2', 'tick 2'), 2027: ('D2', 'Day-2 layer: BOH 34 partition'),
     2929: ('D2', 'Day-2 layer: 11-9 long wall with 1-6 radius ends at dining 2'),
     2034: ('1', 'grease duct shaft 29 curved enclosure (A-3.12 KN8 1-hr shaft); tick 1 on 2558'), 1824: ('1', 'grease duct shaft east wall'),
     2558: ('1', 'tick 1'), 2553: ('AC', 'tick AC curved acoustic wall'), 3979: ('AC', 'tick AC'), 4929: ('AC', 'same line at ADA lift'),
     5069: ('AC', 'tick AC ADA lift'), 5648: ('1', 'tick 1 lift shaft'), 5462: ('1', 'tick 1, hatched, lift shaft / mech room 1 west'),
     5799: ('X', 'ADA-lift pit/platform hatch'), 3454: ('SPLIT', 'west edge wall (1 per tag 1|E at 653,623) + mech room 5 enclosure (1, tick 1 at door 35) + long hallway/prep-bar wall (AC tick 792,761)'),
     4413: ('1', 'tick 1 west edge wall'), 3665: ('1', 'door 35 jamb piece'), 4718: ('1', 'tick 1 dumbwaiter shaft'), 4864: ('1', 'dumbwaiter shaft'),
     4837: ('1', 'dumbwaiter shaft north wall to tick 2 (753,920)'), 4839: ('2', 'tick 2'), 4770: ('2', 'curved wall end at door 26 (prep bar)'),
     4799: ('X', 'dumbwaiter car symbol'), 4720: ('2', 'restroom 22/23 west + south walls (6 in stud), tags 2'), 4991: ('2', 'restroom 23 east wall'),
     4803: ('2', 'tick 2'), 4722: ('2', 'tick 2'), 4681: ('2', 'tick 2'), 4703: ('2', 'restroom 22 north wall west part'), 5168: ('2', 'restroom south wall east part'),
     5173: ('2', 'same'), 5217: ('2', 'wall x=1255 above tick 2'), 5277: ('2', 'tick 2'), 5180: ('5', 'type 5 furring line, tick 5 on 5181'), 5181: ('5', 'tick 5'),
     5971: ('X', 'outside tenant (retail shop corner)'), 5466: ('X', 'thin'), 5960: ('X', 'thin'), 6103: ('X', 'thin'), 1691: ('X', 'thin'), 3385: ('X', 'tiny'), 3455: ('X', 'tiny')}
}
SPLITBOX = {(4, 2609): [('1', (1700, 440, 1810, 462))], (5, 3454): [('1', (610, 620, 640, 840)), ('1', (640, 650, 730, 790))]}
SPLITREST = {(4, 2609): '2', (5, 3454): 'AC'}
summary = collections.defaultdict(float); hatched = collections.defaultdict(float)
rows_out = []
for pn in (4, 5):
    p = pymupdf.open(pdf)[pn - 1]
    M = p.rotation_matrix * pymupdf.Matrix(Z, Z)
    pix = p.get_pixmap(matrix=pymupdf.Matrix(Z, Z))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    r, g, b = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
    gray = ((r > 150) & (r < 200) & (abs(r - g) < 6) & (abs(g - b) < 6)).astype(np.uint8)
    for (x0, y0, x1, y1) in EXCL[pn]: cv2.rectangle(gray, (int(x0 * Z), int(y0 * Z)), (int(x1 * Z), int(y1 * Z)), 0, -1)
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(gray, connectivity=8)
    comp = {int(r_['comp']): r_ for r_ in csv.DictReader(open(f'{out}/walls_p{pn}.csv'))}
    for cid, rec in comp.items():
        L = float(rec['len_ft']); t = float(rec['thick_in']); h = int(rec['hatch'])
        if cid in ASSIGN[pn]:
            tag, why = ASSIGN[pn][cid]
        elif t < 2.5 or L < 0.4:
            tag, why = 'X', 'thin / short'
        else:
            tag, why = '?', 'UNASSIGNED'
        if tag == 'TICKS':
            for part in rec['split'].split(';'):
                k, v = part.split('='); v = float(v)
                rows_out.append([pn, cid, k, round(v, 2), t, h, why]); summary[(pn, k)] += v
                if h: hatched[(pn, k)] += v
            continue
        if tag == 'SPLIT':
            x, y, w, hh = stats[cid, 0], stats[cid, 1], stats[cid, 2], stats[cid, 3]
            sub = (lab[y:y + hh, x:x + w] == cid); sk = skeletonize(sub)
            ys, xs = np.nonzero(sk); pts = set(zip(ys.tolist(), xs.tolist()))
            per = collections.defaultdict(float)
            for (yy, xx) in pts:
                step = 0.0
                if (yy, xx + 1) in pts: step += 1
                if (yy + 1, xx) in pts: step += 1
                if (yy + 1, xx + 1) in pts and (yy, xx + 1) not in pts and (yy + 1, xx) not in pts: step += math.sqrt(2)
                if (yy + 1, xx - 1) in pts and (yy, xx - 1) not in pts and (yy + 1, xx) not in pts: step += math.sqrt(2)
                if step == 0: continue
                X, Y = (xx + x) / Z, (yy + y) / Z
                tg = SPLITREST[(pn, cid)]
                for (bt, (bx0, by0, bx1, by1)) in SPLITBOX[(pn, cid)]:
                    if bx0 <= X <= bx1 and by0 <= Y <= by1: tg = bt; break
                per[tg] += step
            for k, v in per.items():
                v /= PX_PER_FT; rows_out.append([pn, cid, k, round(v, 2), t, h, why]); summary[(pn, k)] += v
                if h: hatched[(pn, k)] += v
            continue
        rows_out.append([pn, cid, tag, round(L, 2), t, h, why])
        if tag not in ('X',):
            summary[(pn, tag)] += L
            if h: hatched[(pn, tag)] += L
with open(f'{out}/walls_assigned.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['page', 'comp', 'tag', 'len_ft', 'thick_in', 'hatch', 'reason']); w.writerows(rows_out)
print('LF by page / tag (hatched = full-height cross-hatch share):')
for (pn, tg), v in sorted(summary.items()):
    print(f'  A-2.{10 if pn == 4 else 20}  {tg:>3}: {v:7.2f} LF   hatched {hatched[(pn, tg)]:7.2f}')
tot = collections.defaultdict(float)
for (pn, tg), v in summary.items(): tot[tg] += v
print('TOTAL:', {k: round(v, 1) for k, v in sorted(tot.items())})
unassigned = [r_ for r_ in rows_out if r_[2] == '?']
print('unassigned:', unassigned)
