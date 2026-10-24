#!/usr/bin/env python3
"""Hollywood Comedy Club TI - build summary.md from estimate_la_latest.csv and verify the three tier totals.

Run:  python3 -I build_outputs.py       (after takeoff.py and price.py)
"""
import csv, json, os, sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import takeoff as TO

EST = os.path.join(PROJ, "estimate_la_latest.csv")
UNP = os.path.join(PROJ, "unpriced_items.csv")
TOT = os.path.join(PROJ, "_totals.json")
OUT = os.path.join(PROJ, "summary.md")

ITEMS = ["Demolition", "Interior walls", "Ceilings", "Flooring", "New Roofing", "Interior finishes", "Exterior finishes",
         "Doors & Hardware", "Stairs & railing", "Owner-provided equipment install", "Lighting", "Mechanical", "Plumbing",
         "Low Voltage", "F&B equipment", "Other required scope"]
# prior estimate sell values by bid-letter item (session 2026-10-20; base bid 5,081,410; direct 4,228,081)
PRIOR_SELL = {"Demolition": 258314, "Interior walls": 408840, "Ceilings": 84662, "Flooring": 151468, "New Roofing": 57688,
              "Interior finishes": 524421, "Exterior finishes": 94944, "Doors & Hardware": 121504, "Stairs & railing": 322960,
              "Owner-provided equipment install": 23436, "Lighting": 249377, "Mechanical": 793677, "Plumbing": 266324,
              "Low Voltage": 84128, "F&B equipment": 714484, "Other required scope": 925181}
PRIOR_BASE = 5081410
PRIOR_DIRECT = 4228081
CONT, OH, PROF = Decimal("0.04"), Decimal("0.08"), Decimal("0.07")
F = (1 + CONT) * (1 + OH) * (1 + PROF)
TIER_STATUS = {"exact": "priced_exact", "substitute": "priced_substitute"}

rows = list(csv.DictReader(open(EST, newline="")))
unp = list(csv.DictReader(open(UNP, newline="")))
tot = json.load(open(TOT))


def dollars(x):
    return "{:,}".format(int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))


def sellof(d):
    return (d * F).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---- recompute the three totals from the CSV and verify against price.py's totals (exact, in cents)
sums = {k: {t: dict(m=Decimal(0), l=Decimal(0), e=Decimal(0), t=Decimal(0), op=Decimal(0), n=0) for t in TIER_STATUS} for k in ITEMS}
for r in rows:
    for tier, st in TIER_STATUS.items():
        if r["price_status"] == st:
            s = sums[r["bid_letter_item"]][tier]
            s["m"] += Decimal(r["ext_material"]); s["l"] += Decimal(r["ext_labor"]); s["e"] += Decimal(r["ext_equipment"]); s["t"] += Decimal(r["ext_total"]); s["n"] += 1
            if r["ext_total_incl_op"]:
                s["op"] += Decimal(r["ext_total_incl_op"])
direct = {tier: sum(sums[k][tier]["t"] for k in ITEMS) for tier in TIER_STATUS}
book_op = {tier: sum(sums[k][tier]["op"] for k in ITEMS) for tier in TIER_STATUS}
for tier in TIER_STATUS:
    assert direct[tier] == Decimal(tot[tier]["direct"]), (tier, direct[tier], tot[tier]["direct"])
    assert sellof(direct[tier]) == Decimal(tot[tier]["sell"]), tier
    assert book_op[tier] == Decimal(tot[tier]["book_op"]), tier
    assert sum(sums[k][tier]["m"] for k in ITEMS) == Decimal(tot[tier]["material"])
    assert sum(sums[k][tier]["l"] for k in ITEMS) == Decimal(tot[tier]["labor"])
    assert sum(sums[k][tier]["e"] for k in ITEMS) == Decimal(tot[tier]["equipment"])
    for k in ITEMS:
        assert sums[k][tier]["t"] == Decimal(tot["items"][k][tier]["direct"]), (k, tier)
combined = direct["exact"] + direct["substitute"]
assert combined == Decimal(tot["combined"]["direct"])
assert sellof(combined) == Decimal(tot["combined"]["sell"])
assert book_op["exact"] + book_op["substitute"] == Decimal(tot["combined"]["book_op"])
contingency = (combined * CONT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
overhead = (combined * (1 + CONT) * OH).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
profit = (combined * (1 + CONT) * (1 + OH) * PROF).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
assert contingency == Decimal(tot["combined"]["contingency"]) and overhead == Decimal(tot["combined"]["overhead"]) and profit == Decimal(tot["combined"]["profit"])

n_lines = len(TO.ROWS)
lines_with_price = {r["item_id"] for r in rows if r["price_status"] in TIER_STATUS.values()}
unp_lines = [r for r in unp if r["scope"] == "line"]
unp_comps = [r for r in unp if r["scope"] == "component"]
assert len(unp_lines) == tot["n_unpriced_lines"] and len(unp_comps) == tot["n_unpriced_components"]
assert len(lines_with_price) + len(unp_lines) + sum(1 for r in rows if r["price_status"] == "none_required") == n_lines
rows_wo_op = {tier: sum(1 for r in rows if r["price_status"] == st and not r["ext_total_incl_op"]) for tier, st in TIER_STATUS.items()}
match_counts = {}
for r in rows:
    if r["price_status"] == "priced_substitute":
        match_counts[r["match"]] = match_counts.get(r["match"], 0) + 1
status_counts = {}
for r in unp:
    status_counts[r["price_status"]] = status_counts.get(r["price_status"], 0) + 1
period = next(r["latest_period"] for r in rows if r["latest_period"])
n_ex = tot["exact"]["components"]; n_su = tot["substitute"]["components"]

L = []
A = L.append
A("# Hollywood Comedy Club TI - book-priced estimate (Los Angeles, latest index month)")
A("")
A(f"Internal working document. Project: Comedy club interior package, 6263 Hollywood Blvd, Los Angeles (Kelly Architects job 2604, owner Meco Properties); exit stair at 1704 N Vine St priced from its own PC submittal. Prepared 2026-10-24 from the bid documents on hand and the transcripts of the prior estimate session (2026-10-20). Price source: `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.csv`, rows with `status = verified` only, columns `*_la_latest` (period {period}). Nothing was sent to anyone.")
A("")
A("## 1. Totals in three tiers")
A("")
A("**The exact tier is the only one priced from the book without an assumption**: the verified row describes the specified work and the product, size and type as the issued sheets fix it (same unit or an exact stated conversion). **The substitute tier prices a different or unspecified product** (product, size, gauge, type or finish system not fixed by the issued sheets or differing from the row, or part coverage); it is shown for decision only, and the exact difference is written in the `reason` column of every such row. Everything else is unpriced.")
A("")
A("| tier | material | labor | equipment | **direct (bare)** | book O&P extended (ref.) | **sell = direct x 1.201824** | components |")
A("|---|---:|---:|---:|---:|---:|---:|---:|")
for tier in ("exact", "substitute"):
    T = tot[tier]
    A(f"| priced_{tier} | {dollars(T['material'])} | {dollars(T['labor'])} | {dollars(T['equipment'])} | **{dollars(T['direct'])}** | {dollars(T['book_op'])} ({T['rows_without_op']} rows without a book O&P value) | **{dollars(T['sell'])}** | {T['components']} |")
A(f"| **combined (exact + substitute)** | {dollars(Decimal(tot['exact']['material']) + Decimal(tot['substitute']['material']))} | {dollars(Decimal(tot['exact']['labor']) + Decimal(tot['substitute']['labor']))} | {dollars(Decimal(tot['exact']['equipment']) + Decimal(tot['substitute']['equipment']))} | **{dollars(combined)}** | {dollars(tot['combined']['book_op'])} | **{dollars(tot['combined']['sell'])}** | {n_ex + n_su} |")
A("")
A(f"Unpriced: **{len(unp_lines)} takeoff lines with no price at all** and **{len(unp_comps)} unpriced components** inside lines that carry other priced components (listed in section 4 and in `unpriced_items.csv`).")
A("")
A("Company markup arithmetic on the combined bare direct (applied once, the same way as the prior estimate; the per-tier sell figures use the same factor on each tier's own direct):")
A("")
A("| | amount (USD) |")
A("|---|---|")
A(f"| Combined bare direct | {dollars(combined)} |")
A(f"| Contingency 4% = {dollars(combined)} x 0.04 | {dollars(contingency)} |")
A(f"| Overhead 8% = {dollars(combined)} x 1.04 x 0.08 | {dollars(overhead)} |")
A(f"| Profit 7% = {dollars(combined)} x 1.04 x 1.08 x 0.07 | {dollars(profit)} |")
A(f"| **Sell = direct x 1.04 x 1.08 x 1.07 = direct x {F}** | **{dollars(tot['combined']['sell'])}** |")
A("")
A(f"Exact figures (cents) as summed from `estimate_la_latest.csv`: exact direct {direct['exact']} / sell {tot['exact']['sell']}; substitute direct {direct['substitute']} / sell {tot['substitute']['sell']}; combined direct {combined} / sell {tot['combined']['sell']}; book O&P extended exact {book_op['exact']}, substitute {book_op['substitute']}. These equal the values written by `price.py` (`_totals.json`) and the `summary_by_item` sheet of the xlsx; the equality of all three totals is asserted when this file is built.")
A("")
A("The book's own `total_incl_op` column (installing contractor's O&P) is reported for reference only and is not added anywhere, so O&P is not double-counted.")
A("")
A(f"Lines: {n_lines} takeoff lines; {len(lines_with_price)} carry at least one priced component ({n_ex} exact + {n_su} substitute components, since walls, ceilings, doors and fixtures are priced as components); {len(unp_lines)} lines are fully unpriced; 1 line (toilet partitions) carries a drawn quantity of 0. Substitute components by match: " + "; ".join(f"{k} {v}" for k, v in sorted(match_counts.items(), key=lambda x: -x[1])) + " ('partial' = the row covers part of the component only).")
A("")
A("## 2. Totals by bid-letter item, side by side with the prior estimate")
A("")
A("Prior sell values are the 16 item totals of the 2026-10-20 estimate (base bid 5,081,410; direct 4,228,081; sell factor 1.2018). Sell columns here are the item's bare direct of that tier x 1.201824. The difference to the prior sell is the scope the book could not price plus price differences on the priced lines; it is not a saving.")
A("")
A("| Bid-letter item | exact direct | exact sell | substitute direct | substitute sell | combined sell | prior sell | book O&P ext. (ref.) | lines with a price | unpriced lines | unpriced comps |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for k in ITEMS:
    ex, su = sums[k]["exact"]["t"], sums[k]["substitute"]["t"]
    it = tot["items"][k]
    A(f"| {k} | {dollars(ex)} | {dollars(sellof(ex))} | {dollars(su)} | {dollars(sellof(su))} | {dollars(sellof(ex + su))} | {PRIOR_SELL[k]:,} | {dollars(sums[k]['exact']['op'] + sums[k]['substitute']['op'])} | {len(it['lines_with_price'])} | {len(it['lines_unpriced'])} | {it['unpriced_components']} |")
A(f"| **Total** | **{dollars(direct['exact'])}** | **{dollars(tot['exact']['sell'])}** | **{dollars(direct['substitute'])}** | **{dollars(tot['substitute']['sell'])}** | **{dollars(tot['combined']['sell'])}** | **{PRIOR_BASE:,}** | **{dollars(tot['combined']['book_op'])}** | **{len(lines_with_price)}** | **{len(unp_lines)}** | **{len(unp_comps)}** |")
A("")
A("Note: the prior session adopted the tag-based wall takeoff on 2026-10-20 (transcript mac_session_page1.txt L355, L718-721: direct 4,193,926 / base 5,040,361). The 5,081,410 figure above is the base bid as issued before that change, as instructed.")
A("")
A("## 3. Coverage")
A("")
cov = lambda x, base: (Decimal(str(x)) / Decimal(base) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
items_ex = [k for k in ITEMS if sums[k]["exact"]["t"] > 0]
items_any = [k for k in ITEMS if sums[k]["exact"]["t"] + sums[k]["substitute"]["t"] > 0]
A(f"- Exact tier: sell {dollars(tot['exact']['sell'])} = {cov(tot['exact']['sell'], PRIOR_BASE)}% of the prior base bid; direct {dollars(direct['exact'])} = {cov(direct['exact'], PRIOR_DIRECT)}% of the prior direct. This is the share of the prior scope the book prices without an assumption.")
A(f"- Combined (exact + substitute): sell {dollars(tot['combined']['sell'])} = {cov(tot['combined']['sell'], PRIOR_BASE)}% of the prior base bid; direct {dollars(combined)} = {cov(combined, PRIOR_DIRECT)}% of the prior direct.")
A(f"- {len(items_ex)} of the 16 bid-letter items carry an exact-tier price: {', '.join(items_ex)}. {len(items_any)} carry any book price; {16 - len(items_any)} carry none: {', '.join(k for k in ITEMS if k not in items_any)}.")
A(f"- Unpriced lines and components by status: " + "; ".join(f"{k} {v}" for k, v in sorted(status_counts.items(), key=lambda x: -x[1])) + ".")
gap = sorted(((PRIOR_SELL[k] - int(sellof(sums[k]["exact"]["t"] + sums[k]["substitute"]["t"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)), k) for k in ITEMS), reverse=True)
A("- Largest gaps between the prior sell and the combined sell, by bid-letter item (prior sell minus combined sell): " + "; ".join(f"{k} {g:,}" for g, k in gap[:5]) + ".")
dups = tot.get("duplicate_cost_codes_seen", {})
if dups:
    A(f"- Duplicate cost codes met while pricing ({len(dups)}): " + "; ".join(f"{cc}: {d}" for cc, d in dups.items()) + ". Each was used only because exactly one of its rows is verified and that row's description matches the component; the duplicate is recorded in the row's reason.")
else:
    A("- No cost code used in this estimate is carried by more than one row of the table.")
chg = tot.get("changed_by_table_replacement", [])
if chg:
    A(f"- Book table on hand: one cost code per printed line; a line under an unreadable section header carries no section id and no cost code (flagged); a code shared by two printed lines stays only on the undoubted one. {len(chg)} components of this estimate changed against the previous table because of that: " + "; ".join(f"{c['item_id']} ({c['component']}): {c['before']} -> {c['after']}" for c in chg) + ".")
A("")
A("## 4. Unpriced lines and components")
A("")
A("Status values: `not_quantified` = the quantity cannot be read from the documents on hand (reason names the missing sheet or dimension); `spec_not_issued` = quantity known but the product/type is on a schedule that was not issued, so no row can be selected; `not_in_book` = no verified row describes the work; `book_row_not_matching` = the nearest verified row is a different kind of work or product (candidate given, its numbers not used); `book_row_not_verified` = the only matching rows are machine_read or flagged (candidates given, numbers not used); `cost_code_duplicated` = the code is carried by more than one verified row; `owner_provided` = owner-furnished item; `quote` = vendor quote origin. `scope` = line (the whole takeoff line is unpriced) or component (one component of a line that has other priced components).")
A("")
A("| item | scope | bid-letter item | description / component | qty | unit | status | reason | candidate row |")
A("|---|---|---|---|---:|---|---|---|---|")
for r in unp:
    desc = r["description"] if r["scope"] == "line" else r["description"] + " -> " + r["component"]
    A(f"| {r['item_id']} | {r['scope']} | {r['bid_letter_item']} | {desc} | {r['qty']} | {r['unit']} | {r['price_status']} | {r['reason']} | {r['candidate_row']} |")
A("")
A("## 5. Open items, RFIs and missing documents")
A("")
A("Documents not in the bid set on hand (every line that depends on them is unpriced or in the substitute tier): A-7.10 door and window schedule; A-7.20 / A-7.21 finish schedules; A-2.75 / A-2.76 floor finish plans; A-3.70 light fixture schedule; A-4.15 railing details; A-5.20 enlarged bar plan; A-6.10 / A-6.11 / A-6.12 stair 1; A-6.20 / A-6.21 / A-6.22 ADA lift; A-6.30 dumbwaiter; A-9.10 details; S sheets of the main set; M, P, E (plans), K (foodservice) sheets; Addendum #2.")
A("")
A("Open items found in the documents on hand:")
A("- Wall type AC (2 layers each side) and type 3 (exterior plaster) cannot be separated from the class A / class B wall totals; class A studs are priced for types 1 / 2 (substitute), the board as 5/8\" Type X each side (exact), class B board as 2 layers each side (substitute: thickness not stated for 1A). The 6\" 20 ga / 16 ga studs of class B and of the exit stair walls have no matching verified row (unpriced). AC tags: 8 on A-2.10, 4 on A-2.20; type 3 tags: 4 on A-2.10, 2 on A-2.20.")
A("- Wall heights are the prior estimate's class averages (13.5 / 16.4 / 14.0 ft); the mezzanine finish floor is not dimensioned (model used +9 ft; A-4.34 shows a stair landing at +6'-0\"; A-6.11 of the main set not issued).")
A("- Level 5 gypsum finish in public areas (A-2.10 / A-2.20 note) is not separable from the level 4 total.")
A("- The dining room 8'-0\" CLG-1D perimeter band on A-3.12 and the mezzanine curved soffits (8 x 15'-9\") are not measured; the CLG-1D steel joist framing has no matching verified row (suspended-channel rows are a different system).")
A("- Kitchen hood length: the A-2.10 hood outline is not dimensioned and scales to 13 ft, while M-6 states 18'-3\" (prior session finding); M sheets not on hand.")
A("- Stage height: 6 in (A-2.20 keynote 22) vs 10 in (Addendum A-4.30 note 5).")
A("- Poplar moulding at WC-8 is printed 1/2 in x 1/4 in on the Addendum (not 3/4 x 3/4); the only poplar crown row in the book (p203 line 2510) is flagged and carries no cost code in the table on hand, so the moulding is unpriced.")
A("- Lobby floor tile FL-7 / FL-8 vs green room FL-4: the 227 SF group cannot be split without A-2.75.")
A("- Door schedule A-7.10 not issued: 26 new door tags are drawn (12 on A-2.10, 14 on A-2.20); 22 interior leaves are priced in the substitute tier as a steel B-label door in a 4'-0\" wide hollow metal frame with a keyed lever lockset; hinges, closers and the rest of the hardware sets are unpriced; panic devices on the 5 exit doors have no matching verified row (hardware-set rows are a different product).")
A("- Exit stair submittal: landing framing (800C162-54 joists, Sure-Board decking), HSS 4x4 posts, pan concrete fill, embedded anchors and the steel enclosure at the stringer have no matching verified row; HSS 8x4 is priced from the 3/8 in wall, 12'-0\" piece row (drawn 1/4 in); the pan-stair row is 3'-6\" wide with a picket rail (drawn 3'-0\").")
A("- Grease interceptor capacity, 4 in sanitary main length, floor sinks/drains, water heater: P sheets not issued (the interceptor rows on p514 are flagged and carry no cost code in the table on hand). The wall-hung lavatory K-2035-8 has no matching verified row (vanity-top rows are a different mounting); only its rough-in is exact.")
A("- WSHP-1..6, WSHP-8, EF-2, MUA: equipment schedule not on hand; the water-source heat pump rows are machine_read.")
A("- Light fixture types (143 tagged fixtures + 62 decorative G fixtures): A-3.70 not issued.")
A("- FE cabinets: 8 carried from the prior estimate; no FE symbols are placed on the A-2.10 / A-2.20 text layers (legend only).")
A("- Restroom accessories: toilet tissue dispenser, seat cover dispenser and waste receptacle rows are verified but carry no usable unit; grab bar material rows are not verified; the robe hook, hand dryer and mirror rows are substitutes (products per A-7.20 not issued).")
A("- Dumbwaiter rows in the book are flagged; the ADA lift is a vendor quote (McKinley Equipment e-mail, Garaventa) and is not priced from the book.")
A("- General conditions: field personnel rows (project manager, superintendent) are flagged in the book; the final-clean row is flagged; temporary utility rows carry no cost. Only continuous daily cleanup (exact) and dumpster rental (substitute: size assumed) are priced.")
A("")
A("## 6. Method notes")
A("")
A("- Quantities: `takeoff.csv` lists every line with `qty_basis` = drawn (read from a sheet on hand, sheet and keynote cited), prior_estimate (carried from the 2026-10-20 session, transcript file and line cited), inferred (explain) (an arithmetic identity of cited numbers, written out in `qty_source`), or not quantifiable (the dimension or count is on a sheet not issued). No allowances, waste factors, tolerances or ranges were applied.")
A("- Room areas are the prior session's measurements from A-2.10 / A-2.20 (mac_session_page2.txt L265-294); the architect's gross area is 7,141 SF (mac_session_page1.txt L437); the room table sums to 7,908 SF.")
A("- Walls: LF by drawn wall-type tag (A 921 / B 119 / C 20) adopted by the prior session on 2026-10-20; SF = LF x class average height; priced as components on the one-face SF: studs (S.F.), gypsum board per layer (factor 2 for both sides, 4 for two layers each side), batt insulation (S.F.).")
A("- Wall finishes: SF by finish code read by the prior session from the Addendum 1 elevations (mac_session_page2.txt L65-77).")
A("- Light fixture tags were recounted on the RCP text layers this session and match the prior session's counts; new-door tags were read from the plan vectors this session (ovals with 2-digit marks).")
A("- The exit stair (1704 N Vine) is quantified from the PC submittal: 11 risers, 10 treads at 11 in, landing at +6'-0\", wall runs and heights as dimensioned.")
A("- Tier test applied to every component: exact only when the verified row is the specified work and product as the issued sheets fix it; substitute when the kind of work matches but the product, size, gauge, type or finish system is not fixed or differs, or the row covers part of the component (match = partial); a row for a different kind of work or product is not used (book_row_not_matching, candidate recorded). Two conversions rest on text printed on the book row itself: the sealer coverage (350 S.F. per gallon in the row's description path) and the HSS piece length (12'-0\" in the row's description).")
A("- Cost codes: the book is loaded with all rows per code; a code is used only if exactly one row carries it with status verified and that row's own description matches the pattern recorded for the component (asserted); any other row with the same code is recorded in the reason column.")
A("- Every priced row records cost_code, ref_line, book_page, description_path, book unit, the unit check, the conversion factor, latest_period and the five LA latest-month unit costs; `price.py` asserts that every priced cost code exists in the table with status verified, that it carries a unit and a total, and that material + labor + equipment = total.")
A("- Regenerate: `python3 -I scripts/takeoff.py && python3 -I scripts/price.py [book csv path] && python3 -I scripts/build_outputs.py` from the project folder.")
A("")
open(OUT, "w").write("\n".join(L))
print(f"summary.md written -> {OUT}; exact {direct['exact']} / {tot['exact']['sell']}; substitute {direct['substitute']} / {tot['substitute']['sell']}; combined {combined} / {tot['combined']['sell']}; unpriced lines {len(unp_lines)}, components {len(unp_comps)}")
