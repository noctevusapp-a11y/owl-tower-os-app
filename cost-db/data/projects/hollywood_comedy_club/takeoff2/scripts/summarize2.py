#!/usr/bin/env python3
"""Writes ../pricing2_notes.md from the four priced files (counts by price_status, totals by tier and by bid-letter
item, every unpriced line and component with its reason) plus the estimator's judgment calls written below.

Run:  python3 -I summarize2.py   (after price2.py has written priced_mep.csv, priced_equipment.csv, priced_demo_struct_gc.csv, priced_arch.csv)
"""
import csv
import os
from collections import OrderedDict, defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.dirname(HERE)
FILES = OrderedDict([("mep", "priced_mep.csv"), ("equipment", "priced_equipment.csv"), ("demo_struct_gc", "priced_demo_struct_gc.csv"), ("arch", "priced_arch.csv")])
PRICED = ("priced_exact", "priced_substitute")
STATUS_ORDER = ["priced_exact", "priced_substitute", "book_row_not_matching", "book_row_not_verified", "not_in_book", "not_quantified",
                "spec_not_issued", "owner_provided", "existing", "quote", "none_required", "carried_elsewhere"]


def money(x):
    return f"{x:,.2f}"


def load(name):
    with open(os.path.join(T2, name), newline="") as f:
        return list(csv.DictReader(f))


out = []
P = out.append
P("# Hollywood Comedy Club TI - book pricing of the takeoff2 files (Los Angeles, latest index month)")
P("")
P("Internal working document, prepared 2026-10-28 (arch section added 2026-10-29) for the Owl Tower estimating file. Price source: `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.csv`, "
  "rows with `status = verified` only, columns `*_la_latest` (period 2026-Q02). The same rules as the first estimate (`scripts/price.py`, `summary.md` sections 1 and 6) were "
  "applied: a line is priced only from a verified row, machine_read / flagged rows are reported as candidates with the price empty, no allowances, no percentages, no tolerances, "
  "no second location or time factor, every unit conversion written out with its source, bare M / L / E kept separate, the book O&P column reported for reference only and never added. "
  "Nothing was sent to anyone; no file outside `takeoff2/` was written.")
P("")
P("Files: `scripts/price2.py` (engine, usage `python3 -I price2.py <takeoff.csv> <matches.csv> <book.csv> <out_priced.csv>`), `scripts/build_matches2.py` (writes the three "
  "mapping files `matches_mep.csv`, `matches_equipment.csv`, `matches_demo_struct_gc.csv`), `scripts/build_matches_arch.py` (writes `matches_arch.csv`), `scripts/summarize2.py` (this file). "
  "Outputs `priced_mep.csv`, `priced_equipment.csv`, `priced_demo_struct_gc.csv`, `priced_arch.csv` carry the columns of `../estimate_la_latest.csv` plus `spec_or_model`, `furnished_by`, `installed_by`.")
P("")
P("**Tiers.** `priced_exact`: the verified row is the specified work and the product / size / type as the documents fix it (same unit or an exact stated conversion). "
  "`priced_substitute`: same kind of work, product / size / type not fixed or differing (the exact difference is in `reason`; `match` = substitute, or partial when the row covers "
  "part of the component). `book_row_not_matching`: the only candidate row is a different kind of work. `book_row_not_verified`: the matching row is machine_read / flagged (or sits "
  "under an unreadable section header without a cost code). `not_in_book`, `not_quantified` (takeoff qty empty or the dimension needed for the book unit is not on the documents), "
  "`spec_not_issued` (quantity on hand but the product / construction needed to choose a row is not stated), `owner_provided` / `existing` (no bid price), `quote` (vendor-quoted "
  "scope: the CaptiveAire hood package, foodservice equipment by model, LED strip and decorative fixtures, and in arch.csv the manufacturer-specific lift, dumbwaiter, Eliason doors, "
  "LED base channel, custom millwork and the furniture / mirrors whose furnished-by is not stated), `none_required` (quantity 0 or covered by another line, stated), "
  "`carried_elsewhere` (arch.csv only: an aggregate or duplicate takeoff row whose scope is priced in the rows named in `reason`, kept at no price so nothing is counted twice).")
P("")

grand = defaultdict(lambda: defaultdict(Decimal))
unpriced_sections = []
for key, fn in FILES.items():
    rows = load(fn)
    lines = OrderedDict()
    for r in rows:
        lines.setdefault(r["item_id"], []).append(r)
    counts_rows = defaultdict(int)
    counts_lines = defaultdict(set)
    for r in rows:
        counts_rows[r["price_status"]] += 1
        counts_lines[r["price_status"]].add(r["item_id"])
    tiers = {k: dict(material=Decimal(0), labor=Decimal(0), equipment=Decimal(0), direct=Decimal(0), op=Decimal(0), no_op=0, n=0) for k in PRICED}
    by_item = defaultdict(lambda: defaultdict(Decimal))
    for r in rows:
        if r["price_status"] in PRICED:
            s = tiers[r["price_status"]]
            s["n"] += 1
            for c in ("material", "labor", "equipment"):
                s[c] += Decimal(r["ext_" + c])
            s["direct"] += Decimal(r["ext_total"])
            if r["ext_total_incl_op"]:
                s["op"] += Decimal(r["ext_total_incl_op"])
            else:
                s["no_op"] += 1
            by_item[r["bid_letter_item"]][r["price_status"]] += Decimal(r["ext_total"])
            grand[r["price_status"]]["direct"] += Decimal(r["ext_total"])
            grand[r["price_status"]]["op"] += Decimal(r["ext_total_incl_op"] or 0)
    priced_lines = counts_lines["priced_exact"] | counts_lines["priced_substitute"]
    P(f"## {key}: `{fn}` ({len(lines)} takeoff lines, {len(rows)} output rows, {len(priced_lines)} lines with at least one priced component)")
    P("")
    P("| price_status | output rows | takeoff lines |")
    P("|---|---:|---:|")
    for st in STATUS_ORDER:
        if counts_rows.get(st):
            P(f"| {st} | {counts_rows[st]} | {len(counts_lines[st])} |")
    P("")
    P("Totals by tier (bare direct, USD; book O&P extended for reference only):")
    P("")
    P("| tier | components | material | labor | equipment | **direct (bare)** | book O&P ext. (ref.) |")
    P("|---|---:|---:|---:|---:|---:|---:|")
    for k, s in tiers.items():
        P(f"| {k} | {s['n']} | {money(s['material'])} | {money(s['labor'])} | {money(s['equipment'])} | **{money(s['direct'])}** | "
          f"{money(s['op'])} ({s['no_op']} rows without a book O&P value) |")
    d = tiers["priced_exact"]["direct"] + tiers["priced_substitute"]["direct"]
    P(f"| combined | {tiers['priced_exact']['n'] + tiers['priced_substitute']['n']} | | | | **{money(d)}** | |")
    P("")
    if by_item:
        P("Direct by bid-letter item:")
        P("")
        P("| bid_letter_item | exact direct | substitute direct |")
        P("|---|---:|---:|")
        for k, v in by_item.items():
            P(f"| {k} | {money(v['priced_exact'])} | {money(v['priced_substitute'])} |")
        P("")
    sec = []
    sec.append(f"### {key}: unpriced lines and components")
    sec.append("")
    sec.append("| item | scope | price_status | qty | unit | description | reason | candidate_row |")
    sec.append("|---|---|---|---:|---|---|---|---|")
    for r in rows:
        if r["price_status"] in PRICED:
            continue
        scope = "line" if r["component"] == "" else "component"
        desc = r["description"] if scope == "line" else r["description"][:60] + " / " + r["component"]
        desc = desc.replace("|", "/")
        sec.append(f"| {r['item_id']} | {scope} | {r['price_status']} | {r['qty']} | {r['unit']} | {desc[:140]} | {r['reason'].replace('|', '/')} | {r['candidate_row'].replace('|', '/')} |")
    sec.append("")
    unpriced_sections.append("\n".join(sec))

P("## All four files together")
P("")
ex, su = grand["priced_exact"]["direct"], grand["priced_substitute"]["direct"]
P(f"Exact direct {money(ex)}; substitute direct {money(su)}; combined {money(ex + su)} (book O&P extended: exact {money(grand['priced_exact']['op'])}, "
  f"substitute {money(grand['priced_substitute']['op'])}). The company markup (contingency 4%, overhead 8%, profit 7%, applied once on the bare direct, factor 1.201824 as in "
  "summary.md section 1) is not applied here; the quote tiers (equipment, hoods, lift, dumbwaiter, millwork, decorative lighting) are still open, so a sell figure would be premature.")
P("")

P("## arch.csv - judgment calls to review")
P("")
for s in [
    "**Walls priced on the drawn rows, not the aggregates.** A-001..A-032 carry the components (studs, GWB per layer, batt, sealant, sheathing, felt) with the LF x height conversion of each row's own notes "
    "(9.08 / 7.67 / 7.83 ft); the inferred aggregate rows A-034..A-045 are `carried_elsewhere`. Sum check: the GWB SF priced in the wall rows equals the aggregate rows (4051 + 1313 + 5273 + 9511 + 276 SF) to the rounding of the takeoff.",
    "**16 ga studs priced per L.F. of wall (05 41 13.30, 10' high, 16 ga x 4\", 16\" OC), 20 ga studs per S.F. (09 22 16.13, 16'-high group).** The 16 ga row carries a 10'-0\" wall where the drawn walls are 7'-8\" to 9'-1\" (more stud per LF than drawn) "
    "and excludes headers / bridging; the 20 ga 6\" studs of types 1A / 3 use the 12\" OC line because the 16\" OC line is not verified (16\" OC drawn). Both are substitutes; no 8' or 10' high 20 ga line is verified.",
    "**Two-layer walls (1A, AC).** Face layers exact with the taped-and-finished Type X row (level 4 or 5 per the A-2.10 finish note, assigned per wall by room); base layers priced with the same finished row as a substitute "
    "because the fire-resistant no-finish line is not verified - the finishing labor of the base layers (2 x 2378 + 2 x 328 SF) is an overstatement to net out if a no-finish price is agreed.",
    "**Mold Tough (A-046) double counts 778 SF.** The wet-area substitution is priced at the full mold-resistant row while the same SF is already in the wall rows at the Type X rate (A-010, A-026, A-027, A-032); "
    "net 778 SF x the Type X row once the wet-area extent is fixed (takeoff RFI). Cement board (A-047, 420 SF) is unpriced - every 09 28 13 row is flagged.",
    "**CLG-1D framing with the suspended-ceiling carrier row (partial).** The joists are 3-5/8\" / 6\" CFS with no spacing or gauge (RFI), so no joist LF can be derived; the 1-1/2\" carrier / 7/8\" furring S.F. row stands in for the framing (10,491 on 3050 SF). "
    "The board is the fire-resistant GWB on ceilings level 5 row for an Ultralight Firecode 30 panel (not Type X). The fascia (A-117, 784 SF if vertical) is priced as a 3-5/8\" stud drop wall with level 5 soffit GWB - RFI vertical vs sloped.",
    "**Catwalk guardrail and lighting pipe (A-198, A-199: 39,607 substitute, the largest stair / lift items).** The stainless cable-mesh guardrail uses the stainless 3-rail pipe railing row (238.44 / LF, posts 5' OC, no mesh); "
    "the theatrical pipe uses the 42\" steel bracketed handrail row (169.46 / LF). Both are `partial`; a railing fabricator's quote should replace them.",
    "**Floors.** FL-2 Onyx quartz epoxy priced with the troweled quartz-epoxy 'maximum' line (15.60 / SF, 26,036 - the single largest arch component); its 6\" epoxy cove base (357 LF) is not in the book. "
    "Carpet tile 1 m x 1 m priced with the 24\" x 24\" hard-back row per S.Y. (1/9); LVT plank with the 1/8\" premium vinyl tile row; 12\" x 12\" porcelain with the 1\" x 1\" porcelain mosaic row (no verified 12\" porcelain floor line). "
    "WT-1 / WT-2 5\" x 6\" tile with the 6\" x 4-1/4\" wall tile row - A-152 (510 SF, 12,011) sits in the (E) restrooms that A-5.11 says are not revised (RFI before carrying it).",
    "**Wallcoverings.** Type II vinyls (WC-3, WC-8) are exact with the type 2 row; the WC-4 'red vinyl wallpaper' is 3M DI-NOC architectural film, priced with the type 1 vinyl wallcovering row as a substitute (5,187 SF, 14,212). "
    "The poplar moulding grid (3939 LF) uses the 1/2\" x 3/4\" poplar shoe row; its stain has no L.F. basis and is unpriced.",
    "**Doors and hardware.** Wood solid-core doors (10 leaves) are `book_row_not_verified` - the flush solid-core rows of 08 14 are flagged or carry no unit. HM 60-min doors use the 90-min B-label 20 ga 3'-0\" x 7'-0\" row "
    "(doors 05 and 27 are 8'-0\" high); HM frames the 14 ga B-label 4'-0\" x 7'-0\" row (as in demo_struct_gc). Panic devices (HW-1, 7) are priced with the rim device row here (7,982) although the X-15 / X-17 panics of demo_struct_gc "
    "were left as candidates - align the two files one way or the other. Wood frames and the drapery frames are priced per L.F. of pine jamb stock from the scheduled opening sizes (244.67 LF / 14 frames; 49.3 LF / 3 frames).",
    "**Window type A counted once.** A-108 (door block) carries the storefront tube framing per L.F. of perimeter and the 1\" insulating unit per S.F.; A-203 (exterior block) is `carried_elsewhere`, as are A-209 (= door 06) and A-068 (door 16, exit-stair permit file).",
    "**Quotes and unspecified products.** Lift GVL-SW-120, Matot dumbwaiter, 4 Eliason doors with frames and pivots, LED base channel (657.7 LF), stage platform, fins, stage frame, bar opening, lobby cabinet, strip-light channel, WD-1 slats, "
    "foot rail, reception desk and the three mirrors are `quote` (22 lines). P-4 metallic paint, P-6, TX-4, WC-6, ST-2 / SL-2, B-3, HW-5 pull, the perforated column enclosures and the riser LED are `spec_not_issued` (9).",
    "**Statuses added for this file.** `carried_elsewhere` (22 lines) is new in price2.py; it names the rows that carry the price. Nothing in the file is priced twice except the Mold Tough overlap stated above.",
]:
    P(f"- {s}")
P("")

P("## mep / equipment / demo_struct_gc - judgment calls to review")
P("")
for s in [
    "**Lighting priced from the book (E-101, E-102, E-106, E-123..E-127, 51,929 substitute).** The rule applied: a fixture is priced where the book has the same kind of fixture, otherwise quote. "
    "B1 (Gotham EVO 4\" wall-mounted accent cylinder, 33 EA) was priced with the only verified wall-mounted LED fixture row (66 W indoor/outdoor, 464.02 Ea.) - 15,313, the single largest "
    "substitute component of the MEP file; if the architectural accent cylinder is considered a decorative product like C1 / C2 / D1 it belongs in the quote tier instead. "
    "The Art Deco exit signs and emergency lights (Flamsted of Vermont, X1 / Y1) are decorative products priced with standard LED exit / twin-beam emergency rows; the recessed Isolite "
    "Y2 is priced with a surface twin-beam row. F1 2' x 2' panels are priced with the 2' x 4' LED troffer row because the 2' x 2' line is not verified.",
    "**W10x22 dumbwaiter beams (S-13) marked exact.** The row (05 12 23.75 W10x22) is the same member and grade; its printed basis is a 100-ton 1-2 story project with bolted connections, "
    "here 3 pieces / 431 lb framed to the (E) beams. The product matches; the productivity basis does not describe a 3-piece job. Move to substitute if the basis is read as part of the product.",
    "**Attic floor joists (S-12) priced per LF from the takeoff notes.** The line is 1,538.12 SF; the joist length 1,157 LF comes from the takeoff notes (33 x 12.8 ft + 42 x 17.5 ft), "
    "written as factor 1157/1538.12. Material and installation rows for 16 ga x 8\" joists are exact; the Sure-Board decking (not in the book) and the tracks / hangers (LF not dimensioned) are unpriced components, "
    "so the line is priced for its joists only (23,221 of the 29,086 exact direct of this file).",
    "**Walk-in removals (D-01, D-02) per S.F.** The row 'Food storage equipment, walk-in refrigerator/freezer' is per S.F. without saying floor or panel area; the floor areas of the takeoff "
    "(119 + 32 SF tagged; 181 SF untagged, RFI whether it is a walk-in) were used. Substitute, flagged.",
    "**Stair pan fill (S-07) material at 2,500 psi.** The fill strength is not stated; the 2,500 psi ready-mix row was used because A-9.10 names 2,500 psi for the other slab fills and S-0.10 "
    "triggers special inspection above 2,500 psi. Lightweight concrete is not in the book. The exit-stair fill (X-03) has no depth and only the placing labor is priced.",
    "**Fixture rough-ins for KEC-furnished sinks (P-006..P-016).** The fixtures themselves are quote (foodservice items by model); the book's kitchen-sink rough-in (1,455.30 Ea.) and wall-hung "
    "lavatory rough-in (1,905.41 Ea.) were applied as substitutes to the 3-comp sink, prep sink, dish table, dump sinks and hand sinks. The rough-in rows carry residential-type connections; the commercial "
    "3\" direct waste of KS-1 and the indirect wastes differ. P-065 / P-066 (equipment waste and water connections) are therefore not priced again (none_required / not_in_book) to avoid a double count.",
    "**Pipe insulation (P-057) split by size.** Only the 1/2\" IPS line of 22 07 19.10 (1\" wall) is verified; the 1\" line is flagged and the 3/4\", 1-1/4\" and 1-1/2\" lines are not in the table. "
    "The 327.2 LF line was split per its own qty_source arithmetic: 150.2 LF priced exact, 177.0 LF unpriced in five components.",
    "**Gas 2-1/2\" (P-059) threaded instead of butt-weld.** P-1 specifies butt-weld fittings at 2-1/2\" and larger; the welded 2-1/2\" line is not in the table, so the threaded 2-1/2\" row was used as substitute. "
    "The 1-1/2\" gas line (P-061, 59 LF) is unpriced because its threaded row is flagged (the verified 1-1/2\" row of 22 11 13.48 is grooved-joint pipe).",
    "**Electrical connections priced as devices / connections only (E-014, E-015, E-017, E-018, E-022, E-129, LV-002).** No power plan exists, so only the device or the equipment connection is priced "
    "(receptacle 15 A duplex, motor-connection flexible conduit rows, fusible safety switches); boxes, conduit, wire and circuits are unpriced components. The 208 V equipment connections use the 230 V 3-phase 3 HP motor row.",
    "**Air devices.** Scheduled devices A-F (16) are priced with the nearest verified register / diffuser rows (sizes differ, written in reason) except C (14\" x 14\" line machine_read). The 23 untagged "
    "outlets drawn on M-2 (M-040) and the 5 attic symbols (M-050) are spec_not_issued; pricing them would double count the schedule.",
    "**Statuses beyond the task list.** `spec_not_issued` (10 rows across the files) and `none_required` (8 rows) were kept from the first estimate's status set: the former for lines that have a quantity but no "
    "product / construction to choose a row with (D-08, D-10, D-21, E-011, M-040, M-050, P-051, P-055, S-15, P-057 part), the latter for quantity-0 lines and for P-065 whose connections are inside priced rough-ins.",
    "**Equipment file.** All 82 foodservice items are `quote` (list prices being collected by another agent), 15 owner / vendor items `owner_provided`, the existing water heater `existing`. `candidate_row` names a verified book "
    "row of the same kind where one exists (range, fryer, broiler, ice maker, bins, dishwasher hood per LF, 3-compartment pot sink per LF, walk-in box, galvanized shelving, slicer, coffee / tea brewers) for a later install-labor or budget check.",
    "**Table gaps that drive the unpriced total.** No-hub cast iron soil pipe (p512, flagged, no cost code), grease duct and fire wrap (not in the book), WSHP rows (machine_read), kitchen hoods (not in the book), floor sinks and trap primers "
    "(not in the book), floor drains / backflow 3/4\" / grease interceptor (flagged), galvanized ductwork by weight (duct depths not printed), chemical anchors 1/2\" (not in the table), HSS 4x4 (not in the book), Sure-Board (not in the book).",
]:
    P(f"- {s}")
P("")
P("## Ten largest unpriced items by apparent scope (no book price; order is the estimator's judgment of scope, not a dollar ranking)")
P("")
for s in [
    "Water-source heat pumps M-001..M-003: 8 units, 56 tons nominal (rows machine_read; loop piping / source M-004 not in the documents).",
    "CaptiveAire hood package M-012..M-017 with the fan lot, fire-suppression cabinet, gas valve and controls (FE-55..FE-57, FE-97, M-054, LV-007): quote.",
    "Foodservice equipment schedule: 82 quote lines (cooking line, refrigeration, walk-in box and remote refrigeration, bar underbar, dishmachine, custom stainless).",
    "Grease duct risers, collector and shaft duct 96 LF with fire wrap (M-019..M-022) and the hood / duct removal (M-048, D-04): not in the book / flagged.",
    "Sanitary no-hub cast iron 245 LF below slab and in walls (P-023..P-029) with risers, vents, cleanouts, trenching and slab patch (P-030..P-036, D-14, D-15): flagged rows / not quantified.",
    "Electrical distribution: rewiring of 6 existing panels (116 circuits, E-001..E-006, E-013), 3 new panels and feeders (E-011, E-012), WSHP / fan / equipment branch circuits (E-015..E-021 components), demolition (E-025): no power plan.",
    "LED strip lighting 707 LF Omni + 119 LF CORE base channel + G16-G18 (E-107..E-121) and the decorative pendants / sconces C1, C2, D1 (E-103..E-105): quote; 24 V drivers and Lutron Athena controls not quantifiable.",
    "Supply / MUA ductwork 230 LF drawn on M-2 (M-024..M-030) plus the undrawn mezzanine ductwork and insulation (M-031..M-033): duct depths and gauges not printed.",
    "Mezzanine ceiling coffer removal 890 SF (D-20), 72 light fixtures (D-21), walls 43 LF (D-22..D-24), kitchen equipment and bar removals (D-03, D-06): material / type not stated or rows flagged.",
    "Sure-Board decking 1,538 SF and tracks (S-12 components), LGS landings (S-04, X-05), HSS 4x4 posts and tiebacks (S-05, S-08, X-06), base-plate epoxy anchors (S-06, S-14, X-07..X-09): not in the book / no matching row.",
]:
    P(f"- {s}")
P("")
P("Also unpriced with real scope: water heater trim, backflow preventer, PRV, grease trap, floor drains and floor sinks (P-002 parts, P-017..P-022); gas 1-1/2\" and the appliance drops (P-061, P-062); "
  "exit-stair 1-hr wall studs (X-14 component), storefront panel framing (X-16), panic hardware (X-15, X-17); the duration-driven general conditions (G-21..G-25) and the permits / inspections that have no cost row.")
P("")
P("Largest unpriced arch.csv items by apparent scope: the Garaventa lift (A-200) and Matot dumbwaiter (A-201); the 4 Eliason doors with frames and pivots (A-059, A-060, A-069, A-077, A-094, A-106 part); "
  "the 10 solid-core wood doors (rows not verified); the LED base channel 657.7 LF (A-134) and riser LED (A-196); K-13 spray acoustical 3773 SF (A-121, not in the book); the stage platform, 9 light-beam fins, stage frame, bar opening and lobby cabinet (A-171..A-180); "
  "WD-1 slat panelling 209 SF (A-144); epoxy cove base 357 LF (A-125); P-4 metallic paint 390 SF (A-157); cement board 420 SF (A-047); hinges, gaskets, cylinders, exit-device trim and louvers (A-090, A-091, A-099, A-100, A-103, A-111); "
  "the Day-2 walls (A-033) and every 'not quantifiable' RFI line (A-048..A-052, A-109, A-110, A-123, A-130, A-132, A-161, A-164, A-167, A-168, A-172, A-179, A-190, A-193, A-205, A-210).")
P("")
P("## Method notes")
P("")
for s in [
    "Quantities are those of the takeoff2 files, unchanged; where a book unit needs a conversion the factor is an arithmetic expression whose source is written in parentheses (parsed and re-printed in `unit_check`).",
    "Conversions used: HSS 8x4 pieces 1/12 per LF (piece length printed on the row); plate S.F. from the plate sizes on S-3.10 / S-3.20; stair pan fill 2/12/27 CY per SF (A-6.12 depth); lift pit 3.5/12/27 (A-6.21 depth); "
    "walk-in S.F. from the takeoff floor areas; joist LF 1157/1538.12 and exit-stair wall S.F. 1595/95.54 and 797/95.54 from the takeoff notes; insulation and electrical shares from the takeoff qty_source counts.",
    "Conversions used in arch.csv: wall S.F. = LF x 9.08 / 7.67 / 7.83 ft (heights in each wall row's notes) x sides x layers; felt per Sq. = S.F. / 100 x 2 layers; carpet and stucco 1/9 (S.F. to S.Y.); sealer 1/350 gal per S.F. "
    "(printed on the row); frame L.F. from the scheduled opening sizes (2 jambs + head); window perimeter and area from the 3'-10\" x 8'-1\" schedule size; fascia 8.75 SF per LF (16'-9\" - 8'-0\"); counter 5.833 x 1.5 ft; handrails 3.125 ft each; "
    "HM / aluminum frame shares 5/7 and 2/6 from the takeoff counts.",
    "Every priced row records cost_code, ref_line, book_page, description_path, book unit, unit_check, factor, book_qty, latest_period and the five LA latest-month unit costs; `price2.py` asserts the code is carried by exactly one verified row, "
    "that it has a unit and a total, that M + L + E = T, that book_qty reproduces the extension, that every takeoff line is in the output and that every unpriced row has a status and a reason.",
    "No cost code used is carried by more than one row of the table (no duplicate-code note was raised).",
    "Regenerate: `python3 -I scripts/build_matches2.py && python3 -I scripts/build_matches_arch.py && for f in mep equipment demo_struct_gc arch; do python3 -I scripts/price2.py $f.csv matches_$f.csv <book csv> priced_$f.csv; done && python3 -I scripts/summarize2.py` from the takeoff2 folder.",
]:
    P(f"- {s}")
P("")
P("## Unpriced lines and components (complete lists)")
P("")
for sec in unpriced_sections:
    P(sec)

with open(os.path.join(T2, "pricing2_notes.md"), "w") as f:
    f.write("\n".join(out) + "\n")
print("written", os.path.join(T2, "pricing2_notes.md"), len(out), "lines")
