"""Writes rfq_packages.md: one section per quote package the bid needs, each listing the exact
takeoff lines (item_id, description, spec_or_model, qty, unit, sheet reference, price_status) that
the vendor or subcontractor must price. Lines come unchanged from priced_mep.csv,
priced_equipment.csv and priced_demo_struct_gc.csv; component rows are collapsed to one line per
item_id with the set of statuses. No prices, rates or margins appear in this file (client-facing).
Usage (from takeoff2/): python3 -I scripts/build_rfq_packages.py
"""
import csv, os, re, sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from rfi_data import RFIS  # noqa: E402

RFI_BY_NO = {r["no"]: r for r in RFIS}

SHEET_RE = re.compile(
    r"\b(?:A-\d\.\d{1,2}[A-Z]?|S-\d\.\d{1,2}|M-\d|P-\d|E-\d\.\d|K\d\.\d|KD|KN|A-0\.\d{2}|ENERCALC|ACCO|"
    r"Addendum ?\d|cut sheet book|K8\.\d|K7\.\d)\b")


def sheet_ref(src):
    """Short sheet reference derived from the takeoff qty_source text (de-duplicated, in order)."""
    seen = OrderedDict()
    for m in SHEET_RE.findall(src or ""):
        m = m.replace("Addendum", "Add.")
        seen.setdefault(m, None)
    out = ", ".join(seen.keys())
    return out if out else (src or "")[:60]


def load(path):
    rows = OrderedDict()
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            k = r["item_id"]
            if k not in rows:
                rows[k] = dict(r)
                rows[k]["_statuses"] = []
                rows[k]["_components"] = []
            rows[k]["_statuses"].append(r.get("price_status") or "arch takeoff (not yet priced)")
            if r.get("component"):
                rows[k]["_components"].append((r["component"], r["price_status"]))
    return rows


MEP = load(os.path.join(T2, "priced_mep.csv"))
EQ = load(os.path.join(T2, "priced_equipment.csv"))
DS = load(os.path.join(T2, "priced_demo_struct_gc.csv"))
ARCHT = load(os.path.join(T2, "arch.csv"))
ALL = {}
ALL.update(MEP); ALL.update(EQ); ALL.update(DS); ALL.update(ARCHT)

PRICED = {"priced_exact", "priced_substitute"}


def status_text(r):
    st = OrderedDict((s, None) for s in r["_statuses"])
    return " + ".join(st.keys())


def md(s):
    return (s or "").replace("|", "/").replace("\n", " ").strip()


def q(r):
    v = r["qty"]
    return v if v not in ("", None) else "-"


def table(ids, extra_note=None):
    lines = ["| item_id | description | spec_or_model | qty | unit | sheet reference | takeoff price status |",
             "|---|---|---|---|---|---|---|"]
    n = 0
    for i in ids:
        r = ALL[i]
        lines.append(f"| {i} | {md(r['description'])} | {md(r['spec_or_model'])} | {q(r)} | {r['unit'] or '-'} | "
                     f"{md(sheet_ref(r['qty_source']))} | {status_text(r)} |")
        n += 1
    if extra_note:
        lines.append("")
        lines.append(extra_note)
    return "\n".join(lines), n


def rfi_lines(nos):
    out = []
    for n in nos:
        r = RFI_BY_NO[n]
        out.append(f"- RFI {n:03d} ({r['importance']}): {r['subject']} - {r['sheets']}.")
    return "\n".join(out)


def ids_where(rows, pred):
    return [k for k, r in rows.items() if pred(k, r)]


def rng(prefix, a, b, width=3):
    return [f"{prefix}{i:0{width}d}" for i in range(a, b + 1)]


OUT = []
P = OUT.append
COUNTS = OrderedDict()

P("# Hollywood Comedy Club TI - request-for-quote packages (DRAFT)")
P("")
P("Owl Tower Construction Group, Inc. - bid on Kelly Architects job 2604, 6263 Hollywood Blvd, Los Angeles (bidding phase). "
  "Draft prepared 2026-10-28 from the takeoff2 files; nothing has been sent. Each package lists the exact takeoff lines a vendor or "
  "subcontractor must price, with the sheet reference each quantity was taken from and the takeoff price status "
  "(`quote` = vendor-quoted scope; `not_in_book` / `book_row_not_matching` / `book_row_not_verified` = no usable book row, "
  "needs a sub or vendor price; `not_quantified` = the documents do not give the quantity, the sub must quantify or the RFI must be "
  "answered; `spec_not_issued` = quantity on hand, product not stated; `existing` / `owner_provided` = no bid price, interface only). "
  "Quantities are the takeoff quantities as measured or scheduled - vendors must verify them against the sheets listed at the end of "
  "each package. This file carries no prices.")
P("")
P("Sheet-reference key: M-/P-/E- sheets are the IFB progress MEP set (9/9/2026), P-1..P-7 Addendum 2 (9/29/2026), Addendum 3 "
  "(10/6/2026, panel locations), K-sheets = health plan-check 'BIRD CAGE DRAWINGS 062626' (K0.0-K8.3, KD), A- and S- sheets = TI plan-check "
  "submittal 1 (8/19/2026) and the IFB interior design set, exit-stair set = 2604-260626-Exit_Stairs-PC_Submittal1 (separate permit "
  "26016-10000-18605), ACCO = plumbing site assessment (June 2026).")
P("")

# ------------------------------------------------------------------ A
P("## Package A - Foodservice equipment dealer (K2.0 schedule)")
P("")
P("Scope: furnish all K2.0 items that are not owner-, vendor- or existing-furnished, FOB job site, with freight, uncrating, setting in "
  "place, start-up and warranty registration priced as separate lines. Final utility connections are by the plumbing and electrical "
  "subcontractors (packages E and F). The hood / fire-suppression / fan lines and the walk-in / remote refrigeration lines are also issued as "
  "separate packages B and C - the dealer is asked to price them as separate line items so the bid can compare or delete them. "
  "Custom-fabricated stainless items (CUSTOM ST/ST) have no cut sheets and no dimensions on the K-sheets (RFI 029); the dealer or its "
  "fabricator is asked to quote them per shop drawing after RFI 029 is answered.")
P("")

WALKIN = {"FE-7", "FE-8", "FE-9.1", "FE-9.2", "FE-11", "FE-12"}
SHELVING = {"FE-1", "FE-10", "FE-13", "FE-26", "FE-36", "FE-89", "FE-92"}


def eq_cat(k, r):
    d = r["division"]
    if d == "11 44 00":
        return "A1 Cooking (11 44 00)"
    if d == "11 41 00":
        if k in WALKIN:
            return "A3 Walk-in box and remote refrigeration (11 41 00) - also package C"
        if k in SHELVING:
            return "A4 Shelving / storage / pot rack (11 41 00)"
        return "A2 Refrigeration, self-contained (11 41 00)"
    if d == "11 42 00":
        return "A5 Prep tables, work counters, slicer, processor (11 42 00)"
    if d == "11 48 00":
        return "A6 Dish / scullery / sinks / faucets (11 48 00)"
    if d == "11 46 00":
        return "A7 Bar (11 46 00)"
    if d == "11 47 00":
        return "A8 Ice machines, bins, filters (11 47 00)"
    if d in ("23 38 13", "21 23 00"):
        return "A9 Hoods, fans, fire system (23 38 13 / 21 23 00) - also package B"
    return "A10 Other (11 40 00)"


quote_eq = ids_where(EQ, lambda k, r: r["price_status"] == "quote")
cats = OrderedDict()
for k in quote_eq:
    cats.setdefault(eq_cat(k, EQ[k]), []).append(k)
total_a = 0
for cat in sorted(cats, key=lambda c: int(c.split()[0][1:])):
    P(f"### {cat} - {len(cats[cat])} lines")
    P("")
    t, n = table(cats[cat])
    total_a += n
    P(t)
    P("")
custom = [k for k in quote_eq if "CUSTOM ST/ST" in EQ[k]["spec_or_model"]]
P(f"Custom-fabricated stainless lines inside the groups above ({len(custom)}): " + ", ".join(custom) + ".")
P("")
excl = ids_where(EQ, lambda k, r: r["price_status"] in ("owner_provided", "existing"))
P(f"### Excluded from the dealer package - owner / vendor / existing ({len(excl)} lines, no bid price; setting and connections only)")
P("")
t, _ = table(excl)
P(t)
P("")
P("Documents the dealer must receive: K0.0 (environmental notes), K0.1 (existing equipment plan), K1.0 (equipment plan), K2.0 (schedule, both "
  "halves), K3.0 (plumbing rough-ins), K4.0 (electrical rough-ins), K5.0 (building conditions), KD details and 'Notes to General Contractor', "
  "K7.0 / K7.1 (hoods), K8.0-K8.3 (walk-in), P-6 (water heater calc), the 'Thatz Hilarious Cutsheet Book 061426' (132 pp), A-2.10 / A-2.20 "
  "(plan context), A-5.20 (mezzanine pick-up bar - unscheduled equipment, RFI 013).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([4, 9, 13, 14, 24, 25, 26, 29, 30, 35, 49, 51, 52]))
P("")
COUNTS["A Foodservice equipment dealer"] = total_a

# ------------------------------------------------------------------ B
P("## Package B - Kitchen hoods, exhaust / make-up air fans, fire suppression, hood controls (CaptiveAire job 8710180)")
P("")
P("Scope: furnish the hood package per M-6 / K7.0 / K7.1 (two Type-I sections and one Type-II condensate hood), the wall-mount utility "
  "cabinet with the TANK fire-suppression system and electrical package, the 2.5 in electric gas valve (installed by the plumber), hood hanging "
  "hardware, CASlink monitoring and the EF-1 / MUA-1 interlock controls; price the two Captive Aire SIF9DD-HE in-line fans (EF-2, EF-3) as an "
  "option. M-1 keeps EF-1 and MUA-1 as existing - any replacement fan or MUA is to be priced as a separate alternate pending RFI 008. "
  "Grease duct, duct wrap, fire-suppression installation and the deferred fire permit are by the mechanical and fire installers "
  "(package D and RFI 027). The hood lengths are in conflict between sheets (RFI 009): quote on the K7.0 lengths and state the per-foot adjustment.")
P("")
B_IDS = ["M-012", "M-013", "M-014", "M-015", "M-016", "M-017", "M-018", "M-054", "LV-007",
         "FE-55", "FE-56.1", "FE-56.2", "FE-57", "FE-97", "M-010", "M-011"]
t, n = table(B_IDS)
P(t)
P("")
P("Interfaces listed for information (not priced by this vendor): M-008 / M-009 existing MUA-1 and EF-1 (survey and repairs M-047 by the "
  "mechanical sub), E-016 hood electrical package wiring (electrician), LV-005 fire-alarm interface (alarm contractor), M-019..M-022 grease "
  "duct and wrap (mechanical sub), M-048 / D-04 removal of the existing hood (demolition).")
P("")
P("Documents the vendor must receive: M-1, M-2, M-4, M-6, M-7; K1.0, K2.0 (items 55, 56, 57, 97), K4.0, K5.0, K7.0, K7.1, KD details "
  "(remote fire pull, fire-system wiring schematic, hood rod hanger) and KN exhaust / make-up air notes; A-2.10 (cooking-line wall); "
  "Addendum 2 P-7 (gas manifold and valve).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([4, 8, 9, 11, 22, 27, 28, 30]))
P("")
COUNTS["B CaptiveAire hoods / fans / fire suppression / controls"] = n

# ------------------------------------------------------------------ C
P("## Package C - Walk-in cooler / freezer box and remote refrigeration (Arctic Q228534, Russell R-454A)")
P("")
P("Scope: furnish and install the combined cooler + freezer box per K8.0 / K8.1 (13'-3\" x 7'-8\" high, freezer with 4 in floor panels, "
  "doors, lights, accessories), the two Russell evaporator coils and two outdoor R-454A condensing units per K8.2 with A2L leak detection, "
  "valves and controls, refrigerant line sets, heater tape and start-up. The GC provides the 6 in roof platform (KN refrigeration note 12; "
  "M-052 carries no new curb or platform drawn) and the electrician the power and defrost wiring (E-015, KN refrigeration note 10 / electrical "
  "note 32); the plumber extends the coil condensate lines to floor sinks (P-064, KN plumbing note 12). K2.0 names 'AIRCOOLER' while the "
  "drawings are Arctic / Russell (RFI 026).")
P("")
C_IDS = ["FE-7", "FE-11", "FE-8", "FE-12", "FE-9.1", "FE-9.2"]
t, n = table(C_IDS)
P(t)
P("")
P("Related lines in other packages: FE-10 and FE-13 walk-in shelving (package A), E-015 refrigeration electrical connections (package F), "
  "P-064 indirect waste from the two coils and P-018 floor sinks (package E), M-052 roof platform (GC).")
P("")
P("Documents the vendor must receive: K1.0, K2.0 (items 7-13), K3.0, K4.0, K5.0, K8.0, K8.1, K8.2, K8.3, KD details and KN refrigeration / "
  "electrical / plumbing notes, A-2.10, roof plan or M-5 when issued (RFI 003).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([4, 26, 30]))
P("")
COUNTS["C Walk-in box and remote refrigeration"] = n

# ------------------------------------------------------------------ D
P("## Package D - HVAC / mechanical subcontractor (WSHP units, condenser-water loop, ductwork, grease duct, air devices, controls, TAB)")
P("")
P("Scope: all M-sheet work except the CaptiveAire package B. The mezzanine mechanical plan (M-3 / M-5) and the condenser-water loop are not "
  "in the set (RFIs 002, 003) and M-2 prints no duct sizes (RFI 012); the subcontractor is asked to price what is drawn, list the assumptions "
  "it needs for the undrawn mezzanine / attic work, and carry the design-build survey of the existing MUA-1 / EF-1 (M-047) as a separate line.")
P("")
D_GROUPS = OrderedDict([
    ("D1 Water-source heat pumps and loop", ["M-001", "M-002", "M-003", "M-004", "M-005", "M-053"]),
    ("D2 Controls, detectors, thermostats, interlocks", ["M-006", "M-007"]),
    ("D3 Existing air-moving equipment and new in-line fans", ["M-008", "M-009", "M-047", "M-010", "M-011", "M-051"]),
    ("D4 Grease duct, wrap, cleanouts, hood removal", ["M-019", "M-020", "M-021", "M-022", "M-023", "M-048"]),
    ("D5 Supply / MUA / exhaust ductwork and insulation", rng("M-0", 24, 33, width=2)),
    ("D6 Air devices", rng("M-0", 34, 40, width=2) + ["M-049", "M-050"]),
    ("D7 Dampers, flexible duct, access", ["M-041", "M-042", "M-043", "M-044"]),
    ("D8 TAB, O&M, curbs / platforms", ["M-045", "M-046", "M-052"]),
])
total_d = 0
for g, ids in D_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_d += n
    P(t)
    P("")
P("Ductwork drawn on M-2 (first floor): 230 LF in M-024..M-030 with scaled widths 16-42 in and no depths; mezzanine / attic ductwork "
  "(M-031, M-032) and insulation (M-033) have no quantity. Air devices: 16 scheduled (A3, B4, C6, D1, E1, F1) against 23 untagged outlets on "
  "M-2 and 5 symbols on A-3.22. Interfaces: E-017 / E-018 power to the 8 WSHP and EF-2 / EF-3 (electrician), M-005 condensate by the plumber, "
  "M-044 access panels by the GC, M-054 hood interlocks (package B).")
P("")
P("Documents the subcontractor must receive: M-1, M-2, M-4, M-6, M-7 (IFB progress MEP set); A-2.10, A-2.20, A-1.20 (KN18, KN19), A-3.12, "
  "A-3.22 (RCPs with air-device symbols), A-4.1x building sections for the attic; K7.0 / K7.1; Addendum 2 P-1 (materials), P-3 / P-4 "
  "(floor-sink receptors for condensate); ACCO assessment (note: it does not cover HVAC); M-3 / M-5 and the loop design when issued.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([2, 3, 7, 8, 9, 11, 12, 54]))
P("")
COUNTS["D HVAC / mechanical subcontractor"] = total_d

# ------------------------------------------------------------------ E
P("## Package E - Plumbing subcontractor (fixtures, sanitary, water, gas, grease interceptor, water heater trim)")
P("")
P("Scope: all Addendum 2 P-sheet work: new sanitary main and branches in no-hub cast iron below slab and in walls, vents, cleanouts, two points "
  "of connection, abandonment of the old lines, floor drains / floor sinks / trap primers, grease recovery device GT-1, 2-1/2 in PRV and the "
  "domestic water piping in type L copper with insulation, HWR pump, the water-heater trim per P-5, natural gas from the basement meter to the "
  "cook-line manifold with appliance drops and the hood gas valve (furnished by package B), and rough-in / final connection of the KEC-furnished "
  "fixtures and equipment. The existing water heater is scheduled to remain (model conflict, RFI 020); the subcontractor is asked to price a "
  "replacement per the P-5 calculation (320 GPH / 180 MBH minimum) as an alternate. Saw-cutting, trenching and slab patch are to be priced as "
  "separate lines (RFI 032) so they can be moved to the demolition / concrete package if needed.")
P("")
E_GROUPS = OrderedDict([
    ("E1 Water heater (existing), trim, HWR pump", ["P-001", "P-002", "P-003"]),
    ("E2 Plumbing fixtures (P-4 schedule) and the (E) restroom retrofit question", ["P-004", "P-005", "P-070"]),
    ("E3 KEC-furnished fixtures - rough-in and final connection by the plumber", rng("P-0", 6, 16, width=2)),
    ("E4 Drains, floor sinks, grease recovery device, backflow, PRV, trap primers", rng("P-0", 17, 22, width=2)),
    ("E5 Sanitary waste piping (no-hub cast iron)", rng("P-0", 23, 29, width=2)),
    ("E6 Sanitary risers, vents, cleanouts, points of connection, abandonment, infills, trenching", rng("P-0", 30, 36, width=2)),
    ("E7 Domestic cold water, hot water and HWR piping (type L copper)", rng("P-0", 37, 56, width=2)),
    ("E8 Pipe insulation and KEC water filters", ["P-057", "P-058"]),
    ("E9 Natural gas", rng("P-0", 59, 63, width=2) + ["M-017"]),
    ("E10 Kitchen equipment connections and WSHP condensate", ["P-064", "P-065", "P-066", "M-005"]),
    ("E11 Existing conditions reported by ACCO", ["P-067", "P-068", "P-069"]),
])
total_e = 0
for g, ids in E_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_e += n
    P(t)
    P("")

# pipe LF by size summary from the line descriptions
PIPE_RE = re.compile(r"^(?:NEW )?(\d(?:-\d/\d)?|\d/\d) in (SAN|sanitary|CW|HW|HWR|filtered CW|natural gas)\b")
pipes = OrderedDict()
unsized = []
for k in rng("P-0", 23, 29, width=2) + rng("P-0", 37, 56, width=2) + ["P-059", "P-060", "P-061"]:
    r = MEP[k]
    m = PIPE_RE.match(r["description"])
    if not m:
        unsized.append(k)
        continue
    size, sysname = m.group(1), m.group(2)
    sysname = {"sanitary": "SAN", "filtered CW": "CW"}.get(sysname, sysname)
    pipes.setdefault((sysname, size), []).append((k, float(r["qty"])))
P("### Pipe lengths by system and size (sum of the drawn runs above; risers excluded, heights not dimensioned - RFI 054)")
P("")
P("| system | size | LF | lines |")
P("|---|---|---|---|")
order = {"SAN": 0, "CW": 1, "HW": 2, "HWR": 3, "natural gas": 4}


def size_key(s):
    whole, _, frac = s.partition("-")
    if "/" in whole:
        a, b = whole.split("/"); return int(a) / int(b)
    v = int(whole)
    if frac:
        a, b = frac.split("/"); v += int(a) / int(b)
    return v


for (sysname, size), items in sorted(pipes.items(), key=lambda kv: (order[kv[0][0]], -size_key(kv[0][1]))):
    P(f"| {sysname} | {size} in | {sum(v for _, v in items):.1f} | {', '.join(f'{k} {v:g}' for k, v in items)} |")
P("")
P("Unsized or riser lines not in the table: " + ", ".join(unsized) + " (P-051, P-055 sizes not labeled - RFI 055); P-030, P-050 risers "
  "and P-031 vents (no LF - RFIs 031, 054); P-062 gas drops (7 EA, lengths not dimensioned).")
P("")
P("Documents the subcontractor must receive: Addendum 2 P-1 (notes, materials, sizing form), P-2 (first-floor water), P-3 (first-floor waste), "
  "P-4 (mezzanine plan, fixture schedule, vent line data), P-5 (water-heater detail and calc), P-6 (details, Big Dipper, island vent), P-7 (gas); "
  "P-1 plan-check notes; K2.0, K3.0, KD details and KN plumbing notes; A-5.12 (restroom fixture schedule); A-9.10 details 6 and 7; "
  "M-1 (condensate note B); M-7 (gas valve); ACCO plumbing site assessment (June 2026) with its plan-page findings.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([13, 14, 20, 21, 22, 23, 24, 27, 31, 32, 33, 34, 50, 54, 55]))
P("")
COUNTS["E Plumbing subcontractor"] = total_e

# ------------------------------------------------------------------ F
P("## Package F - Electrical subcontractor (distribution, branch circuits, equipment connections, lighting fixture package, controls)")
P("")
P("Scope: rewiring of the six existing panels per the E-2.1 schedules, removal of panel Dillons and re-feed of its loads, three new "
  "lighting / sound panels with feeders (Addendum 3), branch circuits and connections to the K2.0 kitchen equipment, the 8 WSHP units, EF-2 / "
  "EF-3, the hood electrical package, plumbing equipment, the ADA lift and dumbwaiter, general receptacles and switches, electrical demolition, "
  "and the furnishing and installation of the A-3.70 light fixture package with the Lutron Athena dimming system. No power or lighting plans "
  "are issued (RFIs 001, 017): the subcontractor is asked to price the connections and fixtures listed and to state the assumptions it carries "
  "for conduit, wire and devices until the plans arrive. The decorative and strip-light fixtures (C1, C2, D1, G1-G21) may also be quoted by a "
  "lighting representative as a separate fixture package.")
P("")
F_GROUPS = OrderedDict([
    ("F1 Existing panels to rewire, panel removal, new panels and feeders", rng("E-0", 1, 13, width=2)),
    ("F2 Equipment connections and branch circuits", rng("E-0", 14, 25, width=2) + ["LV-002"]),
    ("F3 Lighting controls, switching, drivers, trim kits, circuits", ["E-122", "E-128", "E-129", "E-131", "E-132", "X-22", "E-130"]),
])
total_f = 0
for g, ids in F_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_f += n
    P(t)
    P("")
P("### F4 Light fixture package by type (A-3.70 Issued for Bid 9/9/2026 quantities; RCP tag counts differ for seven types - RFI 018)")
P("")
P("Quantities are the IFB A-3.70 schedule quantities. RCP tag counts (A-3.12 + A-3.22) differ for: B1 28 tags (schedule 33), F1 24 (22), "
  "G20 15 (16), X1 18 (17), Y1 15 (17), Y2 11 (14), Y3 9 (8); G21 schedule qty 16 vs one 98-ft run drawn. The plan-check issue of A-3.70 "
  "(8/18/2026) also differs (A1 qty 1, G1-G5 DiodeLED Valent, Y1 15, Y3 9, D1 TRIAC/ELV). Vendors are asked to price the IFB quantities and "
  "give unit prices so the counts can be adjusted when RFI 018 is answered.")
P("")
P("| item_id | type | product (A-3.70 / cut sheet) | qty | unit | location / remarks | sheet reference | takeoff price status |")
P("|---|---|---|---|---|---|---|---|")
nf = 0
for k in [f"E-1{i:02d}" for i in range(1, 28)]:
    r = MEP[k]
    d = r["description"]
    m = re.match(r"^(Types? [A-Z0-9\-\s\(\)12]+?):\s*(.*)$", d)
    typ, rest = (m.group(1), m.group(2)) if m else (k, d)
    P(f"| {k} | {md(typ)} | {md(r['spec_or_model'])} | {q(r)} | {r['unit']} | {md(rest)} | {md(sheet_ref(r['qty_source']))} | {status_text(r)} |")
    nf += 1
total_f += nf
P("")
P("Strip-light totals: Omni Light True Series COB ribbon 707 LF scheduled (E-121: G1 17.5 + G2 20 + G3 12 + G4 45.5 + G5 306 + G12 10 + "
  "G13 23 + G14 27 + G15 33 + G19 55 + G20 60 + G21 98); CORE base channel strip 119 LF (E-112, G6-G11) plus G16-G18 with no length (E-117); "
  "24 V power supplies and remote drivers not scheduled (E-122). Existing fixtures to remain in the first-floor restrooms: (E)A2 x11, (E)Y3 x3 "
  "(E-130).")
P("")
P("Documents the subcontractor must receive: E-2.0, E-2.1, E-2.2 (IFB progress MEP set), Addendum 3 (panel locations and notes), A-3.70 "
  "(both issues: IFB 9/9/2026 and plan check 8/18/2026), A-3.12 and A-3.22 (RCPs with fixture tags and switch / DB legend), the 16 light-spec "
  "PDFs, A-5.12 (hand dryers), Addendum 1 interior elevations (outlets), K2.0 and K4.0 (equipment electrical data and rough-ins), KD fire-system "
  "wiring schematic and KN electrical notes, M-1 (WSHP and fan electrical data), M-7 (hood electrical package), P-6 (Big Dipper electrical), "
  "A-6.22 (lift electrical) and A-6.30 (dumbwaiter) when available, exit-stair A-0.20.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([1, 7, 10, 15, 16, 17, 18, 19, 27, 30, 47]))
P("")
COUNTS["F Electrical subcontractor (incl. lighting fixture package)"] = total_f

# ------------------------------------------------------------------ G
P("## Package G - Low voltage / AV / fire alarm")
P("")
P("What is drawn: almost nothing. The set contains no sound / AV, TV / video, data / telecom, security or fire-alarm device plan for the tenant "
  "space. The only low-voltage items in the documents are the three POS J-boxes with communication cable (K2.0 item 68, owner's terminals, "
  "conduit by the electrician per KN electrical note 14), the CASlink monitoring of the hood control panel (M-7, package B), and the hood "
  "fire-system interface to the building fire-alarm panel that M-7 assigns to an 'alarm contractor' (fire-alarm permit pulled by others per "
  "A-0.00). Addendum 3 says the three new panels 'manage lighting and sound', and the Dillons panel to be removed carries 7 TV-outlet and 3 POS "
  "circuit lines, so an AV / TV / data scope probably exists but is undocumented (RFI 010). Vendors are asked for a budget-level proposal with "
  "stated assumptions, not a firm price, until RFIs 010 and 028 are answered.")
P("")
G_IDS = ["LV-001", "LV-003", "LV-004", "LV-005", "LV-006", "LV-002", "FE-68.1", "LV-007"]
t, n = table(G_IDS)
P(t)
P("")
P("Documents the vendor must receive: M-7 (alarm-contractor requirements table, CASlink block), Addendum 3, E-2.1 (Dillons, KC and CP "
  "schedules showing the legacy TV / POS / sound circuits), E-2.2 (EPB fire-alarm terminal cabinet), K1.0 / K2.0 item 68, A-2.10 / A-2.20 "
  "(stage and speakeasy layout), RCPs A-3.12 / A-3.22.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([10, 28, 27]))
P("")
COUNTS["G Low voltage / AV / fire alarm"] = n

# ------------------------------------------------------------------ H
P("## Package H - Structural steel and light-gage framing (stair 1 steel, posts, HSS, plates, box beams, Sure-Board attic floor, dumbwaiter beams)")
P("")
P("Scope: LADBS-licensed fabricator for the structural steel (S-0.10) with shop drawings; light-gage framing sub for the Cemco box beams, "
  "attic floor joists and Sure-Board decking, landings, dumbwaiter shaft anchors, shear walls and typical studs. Epoxy anchors (Simpson SET-3G) "
  "and Sure-Board fastening at 4 in o.c. require continuous / deputy special inspection (G-14, G-16, package L). The exit stair at 1704 N Vine "
  "is a separate permit and a separate package (I); the interior partitions are in the architectural takeoff (pending).")
P("")
H_GROUPS = OrderedDict([
    ("H1 Stair 1 (interior, level 1 to mezzanine) steel, landing, posts, plates, pan fill", rng("S-", 1, 7, width=2)),
    ("H2 ADA lift tiebacks and pit", ["S-08", "S-09"]),
    ("H3 Mezzanine opening box beams and mechanical attic floor (Sure-Board)", ["S-10", "S-11", "S-12"]),
    ("H4 Dumbwaiter beams and shaft anchors", ["S-13", "S-14"]),
    ("H5 Sloped floor, headers, shear walls, typical studs", ["S-15", "S-16", "S-17", "S-18"]),
    ("H6 Misc. metals from the architectural takeoff: stair 1 handrails, warning strips, riser LED, overhead finish, attic guardrail and theatrical pipe rail", rng("A-", 194, 199)),
])
total_h = 0
for g, ids in H_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_h += n
    P(t)
    P("")
P("Related general-conditions lines (not priced by this sub, listed for coordination): G-13 shop drawings, G-14 epoxy-anchor inspection "
  "(40 counted anchors both permits), G-16 Sure-Board inspection (1,574 SF), G-17 welding inspection, G-18 structural observation (Charles Tan, "
  "S.E.), G-19 LARR / ICC evidence on site, D-17 / D-28 slab cuts (package K).")
P("")
P("Documents the subcontractor must receive: S-0.10 (general notes, special inspections), S-1.10, S-1.20 (schedules), S-2.10, S-2.20 (plans - "
  "vector files requested, RFI 044), S-3.10, S-3.20 (details); A-6.10 / A-6.11 / A-6.12 (stair 1), A-6.20 / A-6.21 / A-6.22 (ADA lift), A-6.30 "
  "(dumbwaiter), A-4.1x (attic sections), A-9.10 (typical details, backing), A-1.20 (KN17 sloped floor), A-2.10 / A-2.20.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([37, 38, 39, 41, 42, 44]))
P("")
COUNTS["H Structural steel and light-gage"] = total_h

# ------------------------------------------------------------------ I
P("## Package I - Exit stair at 1704 N Vine (separate permit 26016-10000-18605)")
P("")
P("Scope: the complete exit-stair package inside the occupied 1704 N Vine restaurant: demolition of the two exterior infill panels, the "
  "storefront door and the (E) door access; 1-hr rated steel stair with concrete-filled pans, HSS landing, posts, plates and epoxy anchors; "
  "handrails and guard; 1-hr stud / GWB enclosure walls; two new storefront exit doors with a fixed panel and a rated exit-access door with "
  "panic hardware; visual warning strips, exit signs and finish paint. Phasing inside the open restaurant (G-21) and the permit (G-02) are GC "
  "items. One bidder may take the whole package or the steel (misc. metals), drywall, glazing and door scopes may be split as shown by the "
  "installer column of the takeoff.")
P("")
I_IDS = rng("X-", 1, 23, width=2) + ["D-24", "G-02", "G-21"]
t, n = table(I_IDS)
P(t)
P("")
P("Documents the subcontractor must receive: the exit-stair set 2604-260626-Exit_Stairs-PC_Submittal1 in full (A-0.20 exit analysis, A-2.10 "
  "plans and demolition elevation, A-6.10 / A-6.11 stair plans and sections, S-0.10, S-1.10, S-2.10, S-3.10 and the ENERCALC pages); A-1.20 "
  "(KN17 sloped floor, limit of work); A-9.10 (typical details); stair 1 sheets A-6.10..A-6.12 for the P-6 steel finish reference.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([6, 40, 42, 43, 47, 48, 75]))
P("")
COUNTS["I Exit stair 1704 N Vine"] = n

# ------------------------------------------------------------------ J
P("## Package J - ADA vertical platform lift and dumbwaiter (vendor-furnished equipment)")
P("")
P("Equipment: (1) ADA vertical platform lift, level 1 to mezzanine, Garaventa Genesis Shaftway GVL-SW per A-6.21 / A-6.22 (A-6.22 "
  "specifies GVL-SW-120, A-6.21 KN2 calls GVL-SW-144 - RFI 072); the prior estimate carries a ROM from McKinley Equipment / Garaventa on file; "
  "power is the 20A/1P 'ADA LIFT' circuit on (E) panel B (E-2.1). (2) Dumbwaiter, Matot medium-duty car size K (36 x 38 x 48 in), floor "
  "mounted, 2 stops, per A-6.30, framed by three W10x22 beams at the mezzanine opening, with a 24 x 24 in UL-listed pit access door. The "
  "equipment lines (A-200..A-202) come from the architectural takeoff; the structural, demolition and electrical interface lines are listed "
  "with them so the vendor can confirm pit, shaft, opening, beam and power requirements.")
P("")
J_IDS = ["A-200", "A-201", "A-202", "S-08", "S-09", "D-28", "E-020", "S-13", "S-14", "D-17", "E-021"]
t, n = table(J_IDS)
P(t)
P("")
P("Vendor to confirm: lift model, pit depth and slab requirement (RFI 038), shaft / hoistway and tieback attachment (6/S-3.20), power and "
  "disconnect, LADBS elevator-division permit and inspection; dumbwaiter car size against the 4'-8\" x 4'-0\" vs 4'-2\" x 4'-0\" opening (RFI 037), "
  "rail bracket backing (G-26), 2-hr fireproofed beams, machine location and the circuit that no panel schedule carries (RFI 001).")
P("")
P("Documents the vendor must receive: A-6.20, A-6.21, A-6.22 (lift), A-6.30 (dumbwaiter), A-2.10 / A-2.20 (KN9, KN10), A-1.20 (KN6), S-2.10, "
  "S-2.20, 5/S-3.10, 6/S-3.20, E-2.1 (panel B).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([1, 37, 38, 72]))
P("")
COUNTS["J ADA lift (Garaventa GVL-SW) and dumbwaiter (Matot size K) with interface lines"] = n

# ------------------------------------------------------------------ K
P("## Package K - Demolition subcontractor (A-1.10 / A-1.20 demolition plans)")
P("")
P("Scope: selective interior demolition of the first floor and mezzanine per A-1.10 / A-1.20: walk-ins, kitchen equipment and hood, bar, "
  "column enclosures, ramp, raised platform and booths, curved stair, windows and doors, saw-cutting and slab removal for the new sanitary "
  "lines, floor-drain / floor-sink infills, dumbwaiter and lift-pit floor cuts, mezzanine ceiling coffers and 72 light fixtures, mezzanine "
  "walls, J-boxes and conduit (with the electrician), terrazzo protection and patching, and hauling with at least 65% diversion by a City of "
  "Los Angeles certified hauler. Trades disconnect their own utilities (M-1 note D, KN22). Several items have no construction or height stated "
  "(RFI 053) - a pre-bid site walk is recommended. Exit-stair demolition (X-18..X-20) is in package I.")
P("")
K_IDS = rng("D-", 1, 29, width=2) + ["M-048", "E-025", "P-034", "P-035", "G-10"]
t, n = table(K_IDS)
P(t)
P("")
P("Documents the subcontractor must receive: A-1.10 and A-1.20 (demolition plans with keynotes), A-6.20 / A-6.21 (lift pit cut), A-6.30 "
  "(dumbwaiter demolition plan), A-9.10 details 6 and 7 (trench patch, slab infill), Addendum 2 P-3 (infill F.D. / F.S. / trench drain, abandon "
  "notes), M-1 note D (hood and duct removal), K0.1 (existing equipment plan), exit-stair A-2.10 demolition elevation (for coordination), "
  "ACCO assessment (basement lines).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([32, 36, 37, 43, 45, 46, 53]))
P("")
COUNTS["K Demolition subcontractor"] = n

# ------------------------------------------------------------------ L
P("## Package L - Other quotes the priced files leave open")
P("")
L_GROUPS = OrderedDict([
    ("L1 Fire sprinkler / fire-life-safety contractor (design, submittal, permit, modifications or new NFPA-13 system - RFI 005)", ["G-04", "G-03"]),
    ("L2 Deputy inspection agency / testing laboratory and structural observation (both permits)", ["G-14", "G-15", "G-16", "G-17", "G-18"]),
    ("L3 Waste hauling with 65% diversion (City of Los Angeles certified hauler)", ["D-29", "G-10"]),
    ("L4 Painting (exit-stair steel finish, exposed duct painted flat black, trimless LED base channel)", ["X-23", "M-026", "E-112"]),
    ("L5 Concrete / slab work (lift pit, trench patch, pan fills) - may be carried by the plumber, demolition or steel subs", ["S-09", "D-14", "D-15", "D-16", "P-036", "S-07", "X-03"]),
    ("L6 Light-gage framing / drywall outside the structural package (typical studs - RFI 041; exit-stair rated walls)", ["S-18", "X-14", "S-04", "X-05"]),
    ("L7 Permits, fees and GC process items (not vendor quotes; listed so nothing is dropped)", ["G-01", "G-02", "G-05", "G-06", "G-07", "G-08", "G-11", "G-12", "G-13", "G-19", "G-20", "G-22", "G-23", "G-24", "G-25", "G-26", "G-27", "G-28"]),
])
total_l = 0
for g, ids in L_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_l += n
    P(t)
    P("")
P("Documents: L1 - A-0.00, A-0.21, the full architectural set and the (E) sprinkler riser data (RFI 005); L2 - S-0.10 special inspection "
  "list, S-2.10 / S-2.20, exit-stair S-0.10; L3 - A-1.10 / A-1.20 general note 1; L4 - exit-stair S-0.10, A-6.10..A-6.12, M-1 (duct paint note), "
  "A-3.70 (G6-G11 remarks); L5 - A-9.10 details 6 / 7, A-6.21, S-2.10, Addendum 2 P-3, stair sheets; L6 - S-1.10, S-2.10 / S-2.20 legend, "
  "exit-stair A-2.10 wall tag 1 (UL U404).")
P("")
P("Open RFIs that affect these items:")
P(rfi_lines([5, 6, 32, 38, 40, 41, 45, 47]))
P("")
COUNTS["L Other (sprinkler, inspection, hauling, painting, concrete, framing, GC items)"] = total_l

# ------------------------------------------------------------------ M (arch) millwork
P("## Package M - Millwork / casework and specialties (stages, light-beam fins, pick-up counter, bar opening, planton mouldings, reception, mirrors)")
P("")
P("Scope: architectural millwork per Addendum 1 (A-4.20..A-4.33), A-5.20 and A-2.10 / A-2.20 keynotes: two stage platforms with LVT tops, "
  "nine curved light-beam fins above the main stage (A-4.22A), the stainless pick-up counter and the 6 ft bar opening with KegWorks foot rail, "
  "planton poplar mouldings and 2 in wood frames at the mezzanine doors and cased openings, the lobby base cabinet and green-room make-up "
  "counter with stone tops, the bent-metal strip-light channel, drapery frames, and the specialties (reception desk, mirrors, hook rail, backing "
  "plates, FE cabinets, signage, restroom accessories). Several items may be owner-furnished (RFI 070). Strip lights inside the fins and bases "
  "are in the lighting package F; the WD-1 slat panelling and the poplar moulding grid over WC-8 are in the finishes package N.")
P("")
M_GROUPS = OrderedDict([
    ("M1 Stages, fins, pick-up counter, bar opening, mouldings, cabinets, frames", rng("A-", 171, 183)),
    ("M2 Specialties: reception desk, mirrors, hook rail, backing, FE cabinets, signage, restroom accessories", rng("A-", 184, 193)),
])
total_m = 0
for g, ids in M_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_m += n
    P(t)
    P("")
P("Documents the subcontractor must receive: Addendum 1 (9/21/2026) A-4.20..A-4.27 and A-4.30..A-4.34 (interior elevations, details 5/A-4.30, "
  "9/A-4.31, 2 and 8/A-4.33), A-4.22A (light-beam fin diagram and section), A-5.20 (pick-up counter details 1-3), A-2.10 / A-2.20 (KN13, KN18, "
  "KN22), A-3.22 (fin ceilings), A-5.12 (restroom accessories), 8 & 9/A-5.10 (signage), A-7.20 / A-7.21 (finish codes), A-9.10 detail 5 (backing).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([67, 68, 69, 70, 71, 66, 59]))
P("")
COUNTS["M Millwork / casework and specialties"] = total_m

# ------------------------------------------------------------------ N (arch) finishes
P("## Package N - Finishes subcontractor (wallcoverings WC-3 / WC-4 / WC-8, poplar moulding grid, WD-1, fabric panels, drapery, paint, FRP, wall tile)")
P("")
P("Scope: all wall and ceiling finishes of A-7.20 / A-7.21 as adjusted by the Addendum 1 elevations: Type II vinyl wallcoverings WC-3 (host and "
  "dining soffit ceilings), WC-8 (dining, green room, hallway 04, mechanical attic) with the stained poplar moulding grid and WD-1 slat "
  "panelling, WC-4 red vinyl (mezzanine), WT-1 / WT-2 wall tile, paints P-1..P-6 on walls, ceilings, doors, frames and the stair-1 steel, "
  "stain and seal of the exposed concrete, FRP in the kitchen zone, Tectum / velvet acoustic panels, TX-4 stage fabric, drapery sets, gold "
  "wallpaper / film / mirror. The 18 GA stainless hood wall lining WC-2 (A-161) is a fabricator item (see the custom stainless lines of "
  "package A). Finish conflicts between A-7.21 and the Addendum are listed in RFI 065; unlisted codes in RFI 066.")
P("")
N_GROUPS = OrderedDict([
    ("N1 Vinyl wallcoverings WC-3 / WC-8 / WC-4, poplar moulding grid, WD-1 slat panelling", rng("A-", 138, 150)),
    ("N2 Wall tile WT-1 / WT-2", ["A-151", "A-152"]),
    ("N3 Paint P-1..P-6, stain and seal, doors and frames", ["A-153", "A-154", "A-155", "A-156", "A-157", "A-158", "A-159", "A-169", "A-170"]),
    ("N4 FRP, stainless lining, acoustic panels, drapery, fabric, gold wallpaper / film / mirror", rng("A-", 160, 168)),
])
total_n = 0
for g, ids in N_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_n += n
    P(t)
    P("")
P("Documents the subcontractor must receive: A-7.20 (finish legend), A-7.21 (room finish schedule, ceiling heights, notes), A-2.75 / A-2.76 "
  "(finish plans), A-3.12 / A-3.22 (RCPs), Addendum 1 A-4.20..A-4.27 and A-4.30..A-4.34 (interior elevations), A-5.11 / A-5.12 (restroom "
  "elevations and tile), A-6.10..A-6.12 (stair 1, P-6), A-9.10 (details), the 16 finish cut sheets where available.")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([65, 66, 63, 69, 73, 59, 57]))
P("")
COUNTS["N Finishes subcontractor"] = total_n

# ------------------------------------------------------------------ O (arch) flooring
P("## Package O - Flooring (FL-2 epoxy, FL-4 / FL-5 carpet tile, FL-6 LVT, FL-7 / FL-8 tile, FL-9 terrazzo, SL-1 sealer, bases incl. the LED base)")
P("")
P("Scope: floor finishes per A-2.75 / A-2.76 and A-7.20 / A-7.21 with their bases: epoxy flooring and cove base in the kitchen zone, carpet "
  "tile in both dining rooms and on stair 1, LVT along the curved wall and on the stages, porcelain tile at the host and restrooms, black "
  "terrazzo at the exterior step (also package R), urethane sealer in the back-of-house rooms, MDF base B-4, tile cove base B-1, the B-5 LED "
  "light base (CORE channel - the LED strip and drivers are in the lighting package F) and transition strips. Floor preparation and moisture "
  "testing are not specified (RFI 064) and are to be priced as a separate line; trench patches and infills are in the demolition package K.")
P("")
O_IDS = rng("A-", 124, 137)
t, n = table(O_IDS)
P(t)
P("")
P("Documents the subcontractor must receive: A-2.75 / A-2.76 (floor finish plans with pattern layers and keynotes 1-2), A-7.20 / A-7.21, "
  "A-5.11 / A-5.12 (restroom tile and grout notes), A-6.10..A-6.12 (stair 1 treads), A-4.01 and A-7.20 FL-9 (terrazzo step), A-3.70 row G6-G11 "
  "(LED base channel), A-9.10 details 6 / 7 (slab patch interface).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([64, 63, 67, 59, 75, 74]))
P("")
COUNTS["O Flooring and bases"] = n

# ------------------------------------------------------------------ P (arch) drywall / framing
P("## Package P - Drywall / light-gage framing (walls by tag with LF and layers, CLG-1D ceilings, K-13, column enclosures)")
P("")
P("Scope: all new partitions of A-2.10 / A-2.20 by wall tag (types 1, 1A, 2, 3, 5, AC and the Day-2 walls) with their studs, GWB layers, "
  "insulation, sealant, Mold Tough and cement-board substitutions, furring and soffits; the CLG-1D GWB ceilings on new steel joists with the "
  "8'-0\" band fascia and the curved fin ceilings; cleaning / patching of the exposed concrete coffers and the K-13 spray-applied acoustical "
  "insulation; the perforated metal column enclosures (metal fabricator); access hatches; the GWB soffit under stair 1. The exit-stair "
  "enclosure walls (X-14) are in package I; the structural light-gage (box beams, attic floor, landings) in package H.")
P("")
P_GROUPS = OrderedDict([
    ("P1 Walls by tag - first floor (A-2.10)", rng("A-", 1, 15)),
    ("P2 Walls by tag - mezzanine / attic (A-2.20) incl. Day-2 walls", rng("A-", 16, 33)),
    ("P3 Wall assemblies: GWB by type, sheathing, insulation, studs, furring, sealant, substitutions", rng("A-", 34, 47)),
    ("P4 Low wall, column enclosures, furring / patch, beam soffit, hallway ceiling", rng("A-", 48, 52)),
    ("P5 Ceilings: CLG-1D, joists, fascia, CLG-1A refinish, CLG-3A clean / patch, K-13, fin ceilings, hatches", rng("A-", 112, 123) + ["A-197"]),
])
total_p = 0
for g, ids in P_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_p += n
    P(t)
    P("")
# wall LF by tag
WALL_RE = re.compile(r"^Wall type (1A|AC|\d)\b")
walls = OrderedDict()
for k in rng("A-", 1, 33):
    r = ARCHT[k]
    m = WALL_RE.match(r["description"])
    tag = m.group(1) if m else "Day-2 (untyped)"
    walls.setdefault(tag, []).append((k, float(r["qty"])))
LAYERS = {"1": "1-hr UL U404: 5/8 in Type X GWB 1 layer each side, 4 in acoustic batt",
          "1A": "2-hr: 6 in 20 GA studs, 5/8 in Type X GWB 2 layers each side",
          "2": "non-rated: 3-5/8 in 20 GA studs, 5/8 in Type X GWB 1 layer each side",
          "3": "1-hr exterior: 6 in 20 GA studs, 5/8 in Type X inside, 5/8 in DensGlass Gold + 2 layers felt outside",
          "5": "furring: 2 in steel hat channel, 5/8 in Type X GWB one side",
          "AC": "acoustic 1-hr UL U404: 400S162-54 studs, 5/8 in Type X GWB 2 layers each side, acoustical sealant both sides",
          "Day-2 (untyped)": "wall type not tagged (RFI 059)"}
P("### Wall length by tag (sum of the drawn runs above)")
P("")
P("| wall tag | LF | layers / assembly (wall notes A-2.10 / A-2.20) | lines |")
P("|---|---|---|---|")
for tag, items in walls.items():
    P(f"| {tag} | {sum(v for _, v in items):.1f} | {LAYERS.get(tag, '')} | {', '.join(k for k, _ in items)} |")
P("")
P("Documents the subcontractor must receive: A-2.10 / A-2.20 (plans with wall tags and wall notes 1, 1A, 2, 3, 5, AC; keynotes KN13, KN14, "
  "KN15, KN17, KN21, KN23), A-3.12 / A-3.22 (RCPs: CLG-1D zones, KN1 AC-1, KN3 edge of attic, CURVE UP fins), A-7.21 (ceiling types and "
  "heights), A-9.10 (details 4, 5 and typical partitions), Addendum 1 A-4.22A, A-4.30, A-4.31, S-1.10 / S-2.10 / S-2.20 (stud legend and "
  "schedule - RFI 041), A-6.11 KN9 (stair soffit), K5.0 (kitchen wall backing and curbs).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([41, 56, 57, 58, 59, 62, 69, 3]))
P("")
COUNTS["P Drywall / light-gage framing and ceilings"] = total_p

# ------------------------------------------------------------------ Q (arch) doors
P("## Package Q - Doors, frames, hardware (A-7.10 types, hardware sets HW-1..HW-10, tempered glass, louvers, thresholds, hatches)")
P("")
P("Scope: the A-7.10 door schedule - 29 new leaves / openings including 4 cased openings, 6 existing doors receiving new hardware or finish and "
  "4 existing doors to remain; hollow metal, wood and aluminum frames; aluminum / glass storefront doors 06 and the E01 pair hardware; Eliason-type "
  "pivot doors 07 / 08 / 17 / 26; hardware sets HW-1..HW-10 by door (counts in the lines); 7 louvered type-G doors; smoke seals, thresholds, "
  "rodent gaskets; window type A (also package R); ceiling access hatches (count open). Paint on doors and frames is in package N (A-170). "
  "Hardware gaps are listed in RFI 060.")
P("")
Q_GROUPS = OrderedDict([
    ("Q1 Doors and cased openings by number (A-7.10)", rng("A-", 53, 88)),
    ("Q2 Hardware sets, hinges, seals, louvers, frames, thresholds, window A, hatches", rng("A-", 89, 111)),
])
total_q = 0
for g, ids in Q_GROUPS.items():
    P(f"### {g} - {len(ids)} lines")
    P("")
    t, n = table(ids)
    total_q += n
    P(t)
    P("")
P("Documents the subcontractor must receive: A-7.10 (door, window and hardware schedules, door-type elevations detail 1, window types detail 4, "
  "header detail 6, threshold detail 7), A-2.10 / A-2.20 (door tags and swings), A-7.20 / A-7.21 (door finishes), Addendum 1 A-4.26, A-4.30..A-4.33 "
  "(frame colours and planton mouldings), A-4.01 (door 06 and window A), exit-stair A-2.10 for the related doors (package I).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([60, 61, 59, 65]))
P("")
COUNTS["Q Doors, frames and hardware"] = total_q

# ------------------------------------------------------------------ R (arch) exterior
P("## Package R - Storefront and exterior (Hollywood Blvd exit-door bay: door 06, window A, plaster, metal panel, granite, terrazzo step, handrails)")
P("")
P("Scope: the new exit-door bay in the former window opening on the Hollywood Blvd facade (A-4.01): aluminum / glass exit door 06 to match "
  "the (E) entry door, fixed acoustic storefront window A, new 1-hr exterior infill wall type 3 (framing in package P, lines A-011 / A-028), "
  "plaster to match the (E) facade, aluminum metal panel at the head, salvage and reset of the (E) granite base, the 7 in black terrazzo step to "
  "match the Walk of Fame sidewalk, two exterior handrails and patching of the (E) plaster / stone and storefront at the removed window. "
  "Historic facade constraints apply (Mills Act / HPR, G-08). The Vine St exit doors are in package I.")
P("")
R_IDS = rng("A-", 203, 210) + ["A-058", "A-108", "A-011", "A-028"]
t, n = table(R_IDS)
P(t)
P("")
P("Documents the subcontractor must receive: A-4.01 (exterior elevations 2-4, plan 5, keynotes KN4, KN5, KN7, KN8, KN9, KN12, KN13), A-7.10 "
  "(door 06, window A, detail 4), A-2.10 (wall type 3 note), A-7.20 (FL-9), A-0.00 / historic review conditions (G-08), demolition A-1.10 KN13 "
  "(window removal, D-12).")
P("")
P("Open RFIs that affect this package:")
P(rfi_lines([74, 61, 60, 63]))
P("")
COUNTS["R Storefront and exterior (Hollywood Blvd bay)"] = n

# ------------------------------------------------------------------ summary
P("## Package summary")
P("")
P("| package | lines listed |")
P("|---|---|")
for k, v in COUNTS.items():
    P(f"| {k} | {v} |")
P(f"| **total lines listed (lines shared between packages are counted in each)** | **{sum(COUNTS.values())}** |")
P("")
P("## Architectural RFIs — included")
P("")
P("The architectural takeoff (arch.csv, 210 lines; arch_notes.md) was issued after the first draft: its 21 RFIs are in rfi_list.csv as "
  "RFI 056-075 (arch RFI 1 on the stud size is merged into RFI 041) and its lines are in packages J (lift, dumbwaiter), H6 (stair 1 and "
  "attic rails), M (millwork and specialties), N (finishes), O (flooring), P (drywall / framing / ceilings), Q (doors) and R (exterior bay). "
  "arch.csv is not yet priced, so its lines show 'arch takeoff (not yet priced)' as status.")
P("")

out = os.path.join(T2, "rfq_packages.md")
with open(out, "w") as fh:
    fh.write("\n".join(OUT))
print("wrote", out)
for k, v in COUNTS.items():
    print(f"  {k}: {v}")
print("pipe table rows:", len(pipes), "unsized:", unsized)
