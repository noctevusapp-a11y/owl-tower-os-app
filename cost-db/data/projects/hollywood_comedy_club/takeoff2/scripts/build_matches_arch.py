#!/usr/bin/env python3
"""Writes ../matches_arch.csv, the mapping file read by price2.py for arch.csv (A-001..A-210).

Every decision below was taken against book_lines_la_latest.csv (status, unit, description read for each code on
2026-10-29). A component is priced only from a verified row; the exact difference to the drawn product is written
in `reason`. Factors are arithmetic expressions with the source of the conversion in parentheses (parsed by price2.py).

Structure of the wall pricing: the drawn wall rows A-001..A-032 are priced as components (studs, GWB per layer, batt
insulation, sealant, sheathing, felt) with the LF -> SF conversion taken from each row's own notes (LF x height);
the inferred aggregate rows A-034..A-045 (GWB SF, insulation SF, stud LF, furring, sealant) are therefore written as
`carried_elsewhere` so that nothing is counted twice. The same for the CLG-1D ceiling rows A-112..A-114 (framing +
board priced there; A-115 / A-116 carried) and for the duplicate frontage rows A-203 / A-209 (= A-108 / A-058).

Run:  python3 -I build_matches_arch.py   (from any folder; writes next to the takeoff files)
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.dirname(HERE)
COLS = ["item_id", "component", "cost_code", "factor", "tier", "match", "reason", "candidate_row", "price_status_override"]


class Map:
    def __init__(self):
        self.rows = []

    def C(self, item, comp, cc, factor, tier, reason, match=""):
        """priced component"""
        self.rows.append(dict(item_id=item, component=comp, cost_code=cc, factor=factor, tier=tier, match=match or tier,
                              reason=reason, candidate_row="", price_status_override=""))

    def U(self, item, comp, status, reason, candidate=""):
        """unpriced component (comp empty = the whole line)"""
        self.rows.append(dict(item_id=item, component=comp, cost_code="", factor="", tier="", match="", reason=reason,
                              candidate_row=candidate, price_status_override=status))

    def L(self, item, status, reason, candidate=""):
        """whole line unpriced"""
        self.U(item, "", status, reason, candidate)

    def write(self, name):
        path = os.path.join(T2, name)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            for r in self.rows:
                w.writerow(r)
        print("written", path, len(self.rows), "rows")


# ---------------------------------------------------------------------------------------------------------------
# Book rows used (code, status read from the table on 2026-10-29) - all verified
# ---------------------------------------------------------------------------------------------------------------
STUD16_4 = "OT-05411330-5370"      # 05 41 13.30 framing stud walls w/ top & bottom track, 10' high, 16 ga x 4" wide, studs 16" OC, L.F.
STUD20_358 = "OT-09221613-3360"    # 09 22 16.13 non-load bearing galv., 16' high group, 20 ga 3-5/8" wide, 16" OC, S.F.
STUD20_6 = "OT-09221613-3410"      # 09 22 16.13 non-load bearing galv., 16' high group, 20 ga 6" wide, 12" OC, S.F.
GWB_X_L4 = "OT-09291030-2150"      # 5/8" fire resistant GWB on walls, taped and finished (level 4), S.F.
GWB_X_L5 = "OT-09291030-2195"      # 5/8" fire resistant GWB on walls, with compound skim coat (level 5), S.F.
GWB_MOLD_L4 = "OT-09291030-2520"   # 5/8" mold resistant GWB on walls, taped and finished (level 4), S.F.
GWB_CLG_X_L5 = "OT-09291030-3690"  # fire resistant GWB on ceilings, level 5, S.F.
GWB_SOF_L4 = "OT-09291030-3550"    # GWB on beams, columns or soffits, taped and finished (level 4), S.F.
GWB_SOF_L5 = "OT-09291030-3590"    # GWB on beams, columns or soffits, level 5, S.F.
INSUL = "OT-07211610-4420"         # blanket insulation for walls, foil faced fiberglass 3-1/2" thick R13, 15" wide, S.F.
SEALANT = "OT-07921910-0035"       # acoustical sealant, elastomeric, cartridges, in place (1/4" x 1/2" line; description OCR-damaged), L.F.
GYP_SHEATH = "OT-06164310-0020"    # gypsum sheathing, weatherproof, 1/2" thick, S.F.
FELT = "OT-07251010-2200"          # weather barriers, asphalt felt vapor barrier, for all other decks, Sq. (100 S.F.)
CLG_FRAME = "OT-09222613-3300"     # suspended ceilings incl. carriers, 1-1/2" carriers 24" OC with 7/8" channels 16" OC, S.F.
HM_FIRE_DOOR = "OT-08131315-0080"  # metal fire door, steel flush B label 90 min, full panel 20 ga, 3'-0" x 7'-0", Ea.
HM_FRAME_B = "OT-08121313-5400"    # standard HM frame 14 ga, B label, up to 5-3/4" deep, 4'-0" x 7'-0" single, Ea.
SF_DOOR = "OT-08431310-0020"       # aluminum-framed entrance door, 3' x 7' opening, clear anodized, Opng.
SF_FRAME = "OT-08431310-0620"      # door frame for above doors 3'-0" x 7'-0", bronze finish, Opng.
WD_FRAME = "OT-06481610-3000"      # interior wood door jamb and frames, pine 11/16" x 3-5/8" deep, L.F.
PANIC_RIM = "OT-08712036-0060"     # single door exit only, rim device, wide stile, standard duty US28, Ea.
CLOSER_HD = "OT-08712030-8080"     # door closer, universal heavy duty, regular arm, Ea.
PUSH_PLATE = "OT-08712055-0100"    # push plate 0.050 thick aluminum, 4" x 16", Ea.
KICK_PLATE = "OT-08712095-1830"    # kick plate aluminum .050", 10" x 26", Ea.
LEVER_KEYED = "OT-08712040-0500"   # lockset standard duty, lever handled, keyed, single cylinder function, Ea.
PRIVACY = "OT-08712040-0100"       # lockset standard duty, non-keyed, privacy, Ea.
THRESH = "OT-08712065-0600"        # threshold, bronze panic threshold 5" wide 1/2" thick, Ea.
TUBE_FRAME = "OT-08411320-0150"    # tube framing for window walls and storefronts, plain tube frame mill finish 1-3/4" x 4", L.F.
INSUL_GLASS = "OT-08813010-0800"   # reduce heat transfer glass, 1" insulating unit with 1/4" tempered lites, S.F.
PAINT_WALL = "OT-09912372-1670"    # painting walls complete incl. surface prep, primer & 2 coats finish on drywall or plaster, roller, S.F.
PAINT_FRAME_LF = "OT-09911370-0140"  # door frames & trim only, brushwork, primer & 2 coats exterior latex, L.F.
PAINT_DOOR_EA = "OT-09912335-0140"   # doors flush both sides incl. frame & trim, roll & brush, primer & 2 coats latex, Ea.
WASH_MASONRY = "OT-09019094-0750"  # surface preparation, walls wash, masonry brick & block smooth, S.F. (labor only)
QUARTZ_EPOXY = "OT-09672626-1000"  # quartz flooring, epoxy with colored quartz chips broadcast 3/8" thick, troweled, maximum, S.F.
CARPET_TILE = "OT-09681310-1180"   # carpet tile tufted nylon 24" x 24" hard back (35 oz. line), S.Y.
VINYL_TILE = "OT-09651919-7600"    # vinyl tile flooring 1/8" thick, premium colors / patterns, S.F.
PORC_1X1 = "OT-09311310-3300"      # thin-set ceramic tile, porcelain type, 1 color, color group 2, 1" x 1", S.F.
SEALER_WB = "OT-03051320-1660"     # sealer, water based, 350 S.F./gal., 5 gallon pail, Gal. (material only)
POPLAR_BASE = "OT-06221315-5105"   # moldings base, classic profile 5/8" x 5-1/2", poplar, L.F.
POPLAR_SHOE = "OT-06221315-5325"   # moldings, shoe 1/2" x 3/4", poplar, L.F.
TILE_COVE_6 = "OT-09311310-1600"   # thin-set ceramic tile, sanitary cove base 6" x 6" high, L.F.
VINYL_WC_T2 = "OT-09721613-3300"   # flexible vinyl wall covering, fabric-backed, medium weight type 2 (20-24 oz./S.Y.), S.F.
VINYL_WC_T1 = "OT-09721613-3000"   # flexible vinyl wall covering, fabric-backed, lightweight type 1 (12-15 oz./S.Y.), S.F.
WALL_TILE_6X4 = "OT-09311310-5500" # thin-set ceramic tile, walls interior, 6" x 4-1/4" tile, S.F.
FRP_SMOOTH = "OT-09773010-0030"    # FRP panels .090" thick on walls, adhesive mounted, smooth surface, S.F.
FABRIC_PANEL = "OT-09841310-1000"  # fixed panels, mineral fiberboard fabric covered 30" x 108", 3/4" thick, concealed spline, wall mounted, S.F.
TRAVERSE_ROD = "OT-12221610-4000"  # drapery hardware, traverse rods adjustable 28" to 48", Ea.
SS_COUNTER = "OT-12361610-3200"    # stainless steel countertops, custom, S.F.
QUARTZ_TOP = "OT-12366119-0100"    # quartz agglomerate countertops 25" wide, 4" backsplash, color group A, minimum, L.F.
HOOK_STRIP = "OT-10281313-2600"    # hat and coat strip, stainless steel, 4 hook, 36" long, Ea.
SIGN = "OT-10142313-2070"          # engraved panel signage interior, stock acrylic 2-sided with mounting bracket, 3" x 12", Ea.
GRAB36 = "OT-10281313-1300"        # grab bar straight 1-1/2" diameter stainless steel, 36" long, Ea.
GRAB42 = "OT-10281313-1310"        # grab bar straight 1-1/2" diameter stainless steel, 42" long, Ea.
HAND_DRYER = "OT-10281313-2300"    # hand dryer, surface mounted, electric, 115 volt 20 amp, Ea.
ROBE_HOOK = "OT-10281313-4400"     # robe hook, heavy duty, concealed mounting, Ea.
WALL_RAIL = "OT-05521350-0915"     # wall rail, aluminum pipe 1-1/2" diameter, satin finish, L.F.
SS_RAIL_3 = "OT-05521350-0760"     # railings pipe shop fabricated 3'-6" high posts 5' OC, stainless steel 3 rail 1-1/2" diam. #4 finish, L.F.
RAIL_42_STEEL = "OT-05521350-2050" # attached handrail on brackets, 42" high steel, primed, straight & level, L.F.
ACCESS_FIRE = "OT-08311310-1250"   # framed access door, fire rated with lock, metal, 24" x 36", Ea.
STUCCO = "OT-09242340-1000"        # stucco with bonding agent, 3 coats, on walls, no mesh included, S.Y.
TERR_TREAD = "OT-09661630-2700"    # terrazzo precast, 2" thick treads, straight, L.F.
TERR_RISER = "OT-09661630-3000"    # terrazzo precast, stair risers 1" thick to 6" high, straight sections, L.F.

CB_CAND = "OT-09281310-9150 (flagged, cementitious backer board 1/2\" on walls); all 09 28 13 rows are flagged / machine_read"
LIFT_CAND = "OT-14421610-8000 (flagged, wheelchair lift minimum); OT-14421310-8900 (verified, stair lift maximum - an inclined lift, a different product)"
DW_CAND = "OT-14121010-0020 (flagged, electric dumbwaiter 2 stop up to 75 lb); OT-14121010-0100 (flagged, 76 lb and up, no unit)"
WD_DOOR_CAND = ("OT-08141620-5260 (flagged, custom architectural B label flush birch solid core 3'-0\" x 7'-0\"); OT-08143320-1360 (verified, residential flush "
                "birch solid core 1-3/4\" x 7'-0\" x 2'-8\" - no unit printed); the verified 08 14 rows with a unit are carved stile-and-rail or closet doors")
HW_LOUVER_CAND = "OT-08912610-0050 (verified, steel louver 12\" x 12\" powder coat); OT-08912610-0320 (verified, 10\" x 16\" painted); no fire-rated door louver line"

m = Map()

# ===============================================================================================================
# WALLS A-001..A-052
# ===============================================================================================================
# item: (wall type, LF, height ft, finish level) - LF and height from arch.csv (qty / notes "LF x height = SF")
WALLS = {
    "A-001": ("1", 32.4, 9.08, 5), "A-002": ("1", 17.5, 9.08, 4), "A-003": ("1", 11.4, 9.08, 4), "A-004": ("1", 7.2, 9.08, 5),
    "A-005": ("1", 24.1, 9.08, 5), "A-006": ("1A", 36.1, 9.08, 5), "A-007": ("2", 34.2, 9.08, 5), "A-008": ("2", 16.0, 9.08, 5),
    "A-009": ("2", 28.0, 9.08, 5), "A-010": ("2", 33.4, 9.08, 4), "A-011": ("3", 5.4, 9.08, 5), "A-012": ("AC", 63.5, 9.08, 5),
    "A-013": ("AC", 7.6, 9.08, 5), "A-014": ("AC", 21.2, 9.08, 5), "A-015": ("AC", 35.9, 9.08, 5), "A-016": ("1", 30.4, 7.67, 5),
    "A-017": ("1", 7.8, 7.67, 4), "A-018": ("1", 22.7, 7.83, 5), "A-019": ("1", 41.3, 7.83, 5), "A-020": ("1", 11.5, 7.83, 4),
    "A-021": ("1", 38.4, 7.83, 5), "A-022": ("2", 41.5, 7.67, 4), "A-023": ("2", 16.5, 7.67, 4), "A-024": ("2", 20.8, 7.67, 4),
    "A-025": ("2", 19.8, 7.83, 4), "A-026": ("2", 105.0, 7.83, 5), "A-027": ("2", 5.3, 7.83, 5), "A-028": ("3", 14.8, 7.67, 5),
    "A-029": ("5", 14.4, 7.83, 5), "A-030": ("AC", 90.5, 7.83, 5), "A-031": ("AC", 13.7, 7.83, 5), "A-032": ("AC", 50.8, 7.83, 5),
}
HEIGHT_SRC = {9.08: "9'-1\" floor-to-floor under the (E) mezzanine per the takeoff notes (A-6.10/A-6.11)",
              7.67: "+/-7'-8\" to the (E) waffle slab per the takeoff notes (A-3.22)",
              7.83: "+/-7'-10\" to the (E) waffle slab per the takeoff notes (A-3.22)"}
LEVEL_NOTE = {4: "level 4 row (BOH per the A-2.10 gyp board finish note)", 5: "level 5 skim-coat row (patron area per the A-2.10 gyp board finish note)"}


def h_note(h, extra=""):
    return f"SF per LF of wall = {h} ft height, {HEIGHT_SRC[h]}{extra}"


for item, (wt, lf, h, lvl) in WALLS.items():
    gwb = GWB_X_L5 if lvl == 5 else GWB_X_L4
    if wt in ("1", "AC"):
        m.C(item, "Steel studs 400S162-54 (4\" x 16 ga) @ 16\" o.c. with top and bottom track (L.F. of wall)", STUD16_4, "1", "substitute",
            f"wall note: 400S162-54 16 ga studs @ 16\" o.c.; row is 05 41 13.30 stud walls with top & bottom track, 16 ga x 4\" wide, studs 16\" OC, "
            f"priced per L.F. of wall for a 10'-0\" high wall - the drawn wall is {h} ft high ({HEIGHT_SRC[h]}), so the row carries more stud length per LF than drawn; "
            "the row excludes headers, bridging and bracing (A-9.10 1-1/2\" x 16 ga bridging straps and door box headers are not priced)"
            + ("; A-2.20 note 1 prints 3-5/8\" 20 GA for the same tag - conflict carried in the takeoff" if wt == "1" else ""))
    elif wt == "2":
        m.C(item, "Steel studs 3-5/8\" 20 ga @ 16\" o.c. (S.F. of wall)", STUD20_358, f"{h} ({h_note(h)})", "substitute",
            f"wall note 2: 3-5/8\" 20 GA studs @ 16\" o.c.; row is 09 22 16.13 non-load-bearing 20 ga 3-5/8\" studs 16\" OC priced per S.F. of wall in the "
            f"16'-high group (the drawn wall is {h} ft high; the 8' and 12' high groups carry no verified 20 ga 3-5/8\" row); track included, no headers / bridging"
            + ("; the two plumbing-wall runs labelled 6\" STUD are not separable (takeoff notes) and are priced at 3-5/8\"" if item == "A-026" else ""))
    elif wt in ("1A", "3"):
        m.C(item, "Steel studs 6\" 20 ga @ 16\" o.c. (S.F. of wall)", STUD20_6, f"{h} ({h_note(h)})", "substitute",
            f"wall note {wt}: 6\" 20 GA studs @ 16\" o.c.; the only verified 20 ga 6\" rows are 12\" OC (used) and 24\" OC in the 16'-high group of 09 22 16.13 "
            f"(the 16\" OC line is not verified; the 20'-high 20 ga rows carry a '%' unit); drawn wall {h} ft high")
    elif wt == "5":
        m.U(item, "2\" steel hat-channel furring on the (E) wall", "not_in_book",
            "wall note 5: 2\" steel (hat channel) furring attached directly to the (E) wall; the table carries no metal furring row (the 09 22 36 rows on hand are gypsum "
            "and metal lath); furring LF also listed in A-044")
    # gypsum board
    if wt in ("1", "2"):
        m.C(item, "GWB 5/8\" Type X, 1 layer each side, taped and finished", gwb, f"{h}*2 ({h_note(h, ' x 2 sides x 1 layer')})", "exact",
            f"wall note: 5/8\" Type X GWB each side; row is 5/8\" fire-resistant GWB on walls, {LEVEL_NOTE[lvl]}; no deduction for door openings (as the takeoff)")
    elif wt in ("1A", "AC"):
        m.C(item, "GWB 5/8\" Type X face layer each side (2 of 4 layers), taped and finished", gwb, f"{h}*2 ({h_note(h, ' x 2 sides x 1 face layer')})", "exact",
            f"wall note {wt}: 2 layers 5/8\" Type X each side; face layers priced with the 5/8\" fire-resistant GWB on walls row, {LEVEL_NOTE[lvl]}")
        m.C(item, "GWB 5/8\" Type X base layer each side (2 of 4 layers)", gwb, f"{h}*2 ({h_note(h, ' x 2 sides x 1 base layer')})", "substitute",
            f"base layers need no taping / finishing; the 5/8\" fire-resistant no-finish row is not verified, so the taped-and-finished {LEVEL_NOTE[lvl]} is used - finishing labor in the row exceeds the base-layer work")
    elif wt == "3":
        m.C(item, "GWB 5/8\" Type X interior face, 1 layer, taped and finished", gwb, f"{h} ({h_note(h, ' x 1 side x 1 layer')})", "exact",
            f"wall note 3: 5/8\" Type X GWB inside; row is 5/8\" fire-resistant GWB on walls, {LEVEL_NOTE[lvl]}")
        m.C(item, "Exterior gypsum sheathing 5/8\" DensGlass Gold (exterior face)", GYP_SHEATH, f"{h} ({h_note(h, ' x 1 exterior face')})", "substitute",
            "wall note 3: 5/8\" Dens-Glass Gold; row is weatherproof gypsum sheathing 1/2\" thick (5/8\" glass-mat sheathing not in the table); also listed in A-039")
        m.C(item, "Two layers of felt over the sheathing", FELT, f"{h}*2/100 ({h_note(h, ' x 2 layers; 1 Sq. = 100 S.F.')})", "substitute",
            "wall note 3: 2 layers felt; row is asphalt felt vapor barrier for roof decks per Sq. (100 S.F.) applied here to a wall; the 1\" exterior plaster is priced in A-204")
    elif wt == "5":
        m.C(item, "GWB 5/8\" Type X, 1 side on the furring, taped and finished", gwb, f"{h} ({h_note(h, ' x 1 side x 1 layer')})", "exact",
            f"wall note 5: 5/8\" Type X GWB on 1 side; row is 5/8\" fire-resistant GWB on walls, {LEVEL_NOTE[lvl]}")
    # insulation
    if wt in ("1", "2", "AC"):
        m.C(item, "Acoustic batt insulation 4\" R-13 in the stud cavity", INSUL, f"{h} ({h_note(h, ' x 1 cavity')})", "substitute",
            "A-9.10 detail 4: 4\" fiberglass batt, one side paper, R-13; row is foil-faced fiberglass 3-1/2\" thick R13, 15\" wide (4\" / kraft-faced R-13 not in the table); also listed in A-040")
    # sealant
    if wt == "AC":
        m.C(item, "Continuous acoustical sealant at the ceiling line, both sides", SEALANT, "2 (L.F. of wall x 2 sides at the ceiling line, wall note AC)", "substitute",
            "wall note AC: continuous acoustical sealant at ceiling, bead size not stated; row is acoustical sealant, elastomeric, cartridges, in place (1/4\" x 1/2\" line of 07 92 19.10; "
            "its description is OCR-damaged in the table); also listed in A-045; head-of-wall fire sealant at rated walls is not called out (takeoff RFI)")

m.L("A-033", "not_quantified", "Day-2 mezzanine walls 27.4 LF without a wall type or height (takeoff RFI); no SF basis for studs / board and the Day-2 scope is not confirmed in the base bid")
for k, txt in (("A-034", "type-1 GWB 4051 SF"), ("A-035", "type-1A GWB 1313 SF"), ("A-036", "type-2 GWB 5273 SF"), ("A-037", "type-AC GWB 9511 SF"),
               ("A-038", "type-3 / type-5 GWB 276 SF")):
    m.L(k, "carried_elsewhere", f"aggregate of the wall rows: the {txt} is priced per layer in the GWB components of the wall rows A-001..A-032 (sum of LF x height x layers); no price here to avoid a double count")
m.L("A-039", "carried_elsewhere", "aggregate: the DensGlass sheathing and the 2 layers of felt are priced in the type-3 wall rows A-011 and A-028 (163 SF)")
m.L("A-040", "carried_elsewhere", "aggregate: the 4\" R-13 batt is priced in the type-1, type-2 and type-AC wall rows (7040 SF) with the 3-1/2\" R13 foil-faced row")
m.L("A-041", "carried_elsewhere", "aggregate: the 400S162-54 studs (527.7 LF) are priced per L.F. of wall in the type-1 and type-AC wall rows with OT-05411330-5370")
m.L("A-042", "carried_elsewhere", "aggregate: the 3-5/8\" 20 ga studs (320.5 LF) are priced per S.F. in the type-2 wall rows with OT-09221613-3360")
m.L("A-043", "carried_elsewhere", "aggregate: the 6\" 20 ga studs (56.4 LF) are priced per S.F. in the type-1A and type-3 wall rows with OT-09221613-3410 (12\" OC row)")
m.L("A-044", "carried_elsewhere", "aggregate: the 2\" furring is an unpriced (not_in_book) component of the type-5 wall row A-029")
m.L("A-045", "carried_elsewhere", "aggregate: the acoustical sealant (566.2 LF) is priced per L.F. x 2 in the type-AC wall rows with OT-07921910-0035")
m.C("A-046", "Mold Tough GWB 5/8\" substitution to 4'-0\" at wet areas", GWB_MOLD_L4, "1", "substitute",
    "USG Mold Tough 5/8\" Type X; row is 5/8\" mold-resistant GWB on walls, taped and finished level 4 (the mold-resistant fire-rated line is not in the table). OVERLAP: this 778 SF is a "
    "substitution within the Type X SF already priced in the wall rows A-010, A-026, A-027 and A-032; both are priced at the full row rate, so 778 SF x the Type X row (OT-09291030-2150 / -2195) "
    "is counted twice until the wet-area extent is fixed (takeoff RFI)")
m.L("A-047", "book_row_not_verified", "1/2\" cement backer board behind WT-1 / WT-2 (420 SF): every 09 28 13 row of the table is flagged or machine_read; substitution within the GWB SF of A-026", CB_CAND)
m.L("A-048", "not_quantified", "24\" low wall at the sloped stair-landing ceiling: extent not drawn (takeoff RFI)")
m.L("A-049", "spec_not_issued", "perforated metal column enclosures: pattern, gauge and finish not specified and the column count is 'TYP.' (RFI); no row can be chosen; a custom sheet-metal fabrication to be quoted once specified")
m.L("A-050", "not_quantified", "furr-out and patch of the (E) wall at two KN15 locations: extent not drawn (RFI)")
m.L("A-051", "not_quantified", "soffit / wall around the (E) ceiling beam: beam length and soffit extent not dimensioned (Addendum 1 A-4.30, RFI)")
m.L("A-052", "not_quantified", "GWB ceiling above the hallway opening: no dimensions on A-4.31 (RFI)")

# ===============================================================================================================
# DOORS A-053..A-111
# ===============================================================================================================
m.L("A-053", "existing", "(E) pair E01 to remain (provided-by '-'); the new hardware HW-1, 2, 4 and 5 is priced in the hardware-set rows A-089..A-093")
for k in ("A-054", "A-055", "A-056", "A-074"):
    m.L(k, "carried_elsewhere", "cased opening (type D): the 2\" wood frame is priced in A-105 (L.F. of frame) and its P-1 paint in A-170; no leaf")
m.C("A-057", "Door 05: single flush metal door 3'-0\" x 8'-0\", 60 min", HM_FIRE_DOOR, "1", "substitute",
    "scheduled: metal door 3'-0\" x 8'-0\" x 1-3/4\", 60-minute rated, in an aluminum frame (frame in A-106); row is steel flush B-label 90-minute door, full panel 20 ga, 3'-0\" x 7'-0\" "
    "(8'-0\" high fire-door line not in the table; gauge not scheduled); panic / closer / threshold in the hardware rows")
m.C("A-058", "Door 06: single full-lite aluminum / glass exterior door 3'-0\" x 7'-9\"", SF_DOOR, "1", "substitute",
    "scheduled: aluminum / glass door 3'-0\" x 7'-9\" x 1-3/4\", 6\" stile, 12\" bottom rail, design and finish to match the (E) entry (A-4.01 KN5); row is aluminum-framed entrance door "
    "3' x 7' opening, clear anodized (height 7'-9\" and the matching finish not in the row; glazing per the row); frame in A-106, hardware HW-1, 2, 4, 5 and the rodent gasket in the hardware rows")
for k, d in (("A-059", "07"), ("A-060", "08"), ("A-069", "17"), ("A-077", "26")):
    m.L(k, "quote", f"door {d}: Eliason-type aluminum double-acting pivot door with 4\" x 4\" window, 3'-0\" x 7'-0\" - a manufacturer's product (door, frame and pivots as a unit); "
        "the book's commercial aluminum doors (OT-08131610-5150, verified, flush 3'-6\" x 7'-0\" single swing) are a different product", "OT-08131610-5150 (verified, commercial aluminum flush door 3'-6\" x 7'-0\" single, no glazing - swing door, not a pivot door)")
for k, d in (("A-061", "E09"), ("A-062", "E10"), ("A-063", "E11"), ("A-064", "E12")):
    m.L(k, "existing", f"(E) wood door {d} to remain (furnished Owner (E) door); E12 deadbolt in A-102")
m.L("A-065", "existing", "(E) cased opening E13 to remain")
m.L("A-066", "existing", "(E) metal door E14 in aluminum frame to remain; the new hardware set HW-1, 3 and 4 is priced in A-089, A-091 and A-092")
WD_DOORS = {"A-067": "15 (recessed panel with mirror insert per A-4.21)", "A-070": "18 (Day 2)", "A-073": "22", "A-075": "24", "A-076": "25", "A-079": "28",
            "A-080": "29 (louvered, type G)", "A-081": "30 (louvered, type G)", "A-082": "31 (louvered, type G)", "A-088": "39 (Day 2)"}
for k, d in WD_DOORS.items():
    m.L(k, "book_row_not_verified", f"wood door {d}: solid core flush wood door 3'-0\" x 7'-0\" x 1-3/4\" in a wood frame (frame in A-105); the flush solid-core wood door rows of 08 14 16 are "
        "flagged and the verified residential flush birch door row carries no unit; the verified wood-door rows with a unit are carved stile-and-rail or closet doors (a different product); "
        "louver in A-103, paint in A-170, hardware in the HW rows", WD_DOOR_CAND)
m.L("A-068", "carried_elsewhere", "door 16 (exit stair 2 exterior door) is carried in demo_struct_gc.csv (X- rows, exit-stair permit); listed in arch.csv for its hardware set only, which is priced in the HW rows")
for k, d, extra in (("A-071", "19", "louvered type G, louver in A-103"), ("A-072", "21", "type C with panic device"), ("A-085", "34", "louvered type G in a 60-min shaft door - takeoff RFI"),
                    ("A-086", "35", "louvered type G, 60 min - takeoff RFI")):
    m.C(k, f"Door {d}: hollow metal flush door 3'-0\" x 7'-0\", 60 min", HM_FIRE_DOOR, "1", "substitute",
        f"scheduled: hollow metal door 3'-0\" x 7'-0\" x 1-3/4\", 60-minute rated, HM frame (frame in A-104); row is steel flush B-label 90-minute door, full panel 20 ga, 3'-0\" x 7'-0\" "
        f"(60-minute line not in the table; door gauge not scheduled); {extra}; paint in A-170, hardware in the HW rows")
m.C("A-078", "Door 27: hollow metal flush door 3'-0\" x 8'-0\", 60 min", HM_FIRE_DOOR, "1", "substitute",
    "scheduled: hollow metal door 3'-0\" x 8'-0\" x 1-3/4\", 60-minute rated, HM frame (frame in A-104), provided-by '-' (door into exit stair 2, see demo_struct_gc.csv X- rows for the stair permit scope); "
    "row is steel flush B-label 90-minute door 20 ga 3'-0\" x 7'-0\" (8'-0\" high line not in the table)")
for k, d in (("A-083", "E32"), ("A-084", "E33"), ("A-087", "E38")):
    m.L(k, "existing", f"(E) hollow metal door {d} to remain; new hardware in the HW rows and P-1 paint in A-170")
# hardware sets
m.C("A-089", "HW-1 panic exit device (7)", PANIC_RIM, "1", "substitute",
    "scheduled: Harney Hardware PE5500 series panic exit device, UL fire rated, grade 1, 32\" wide with 84\" vertical rod, powder-coated bronze; row is single-door exit-only RIM device, wide stile, "
    "standard duty, US28 aluminum finish (vertical-rod devices of 08 71 20.36 carry no unit; no fire-rated line) - 3 of the 7 (doors 05, 21, 27) need the fire-rated version; door 27 is under the exit-stair permit (6 if excluded)")
m.L("A-090", "not_in_book", "HW-2 rim lock cylinder (Harney PENCYSC1): no cylinder line in the table (08 71 20.40 carries only a flagged 're-core cylinder' add); one per active leaf assumed by the takeoff (RFI)")
m.L("A-091", "not_in_book", "HW-3 exit-device lever trim, storeroom / keyed function (Harney PEL8001SRB): no outside-trim line for exit devices in the table; the lever lockset rows are a different product",
    "OT-08712040-0500 (verified, lever lockset keyed - a complete lockset, not exit-device trim)")
m.C("A-092", "HW-4 surface closer (11)", CLOSER_HD, "1", "substitute",
    "scheduled: LCN 4040XP series surface closer, matte black; row is universal heavy-duty surface closer, regular arm (arm type and the matte black finish are not in the row); the 14 self-closing "
    "doors without HW-4 in their set are not priced (takeoff RFI)")
m.L("A-093", "spec_not_issued", "HW-5 pull handle: manufacturer, model and finish are '-' on the hardware schedule (product to be selected, RFI)",
    "OT-08712055-2000 (verified, pull handle and push bar, bronze, Ea.); OT-08712055-0980 (verified, pull plate 3\" x 12\" aluminum)")
m.L("A-094", "quote", "HW-6 pivot set for the Eliason-type doors: the pivots are part of the door manufacturer's package (doors 07, 08, 17, 26 are quote rows); no pivot-set line in the table")
m.C("A-095", "HW-7 commercial push plate (4)", PUSH_PLATE, "1", "substitute",
    "scheduled: Deltana commercial push plate 3.5\" x 15\", black; row is push plate 0.050\" thick aluminum 4\" x 16\" (size and black finish differ)")
m.C("A-096", "HW-8 commercial kick plate 10\" x 32\" (4)", KICK_PLATE, "1", "substitute",
    "scheduled: Deltana commercial kick plate 10\" x 32\", black; row is aluminum .050\" kick plate 10\" x 26\" (the stainless 10\" x 30\" / 10\" x 34\" lines carry no unit; 10\" x 32\" not in the table; black finish not in the row)")
m.C("A-097", "HW-9 keyed entry lever (5)", LEVER_KEYED, "1", "exact",
    "scheduled: Schlage F51 Elan keyed entry lever, aged bronze; row is standard-duty lockset, lever handled, keyed, single cylinder function (finish not stated in the row); the keyed lever on exit door 16 is a takeoff RFI")
m.C("A-098", "HW-10 storeroom function lever lock (11)", LEVER_KEYED, "1", "substitute",
    "scheduled: Schlage F80 Elan single-cylinder storeroom lever, aged bronze; row is standard-duty lever lockset, keyed, single cylinder (entry function - storeroom function and finish differ)")
m.L("A-099", "not_quantified", "hinges: type and finish '-' for every door and no count per door (RFI); the book hinge rows are material-only per pair",
    "OT-08712090-1000 (verified, full mortise high frequency steel base 4-1/2\" x 4-1/2\" USP, per Pr., material only)")
m.L("A-100", "book_row_not_verified", "smoke seal / weather gasketing at 15 doors: the door weatherstripping rows of 08 71 25 are flagged; no smoke-seal line",
    "08 71 25 'Threshold weatherstripping, vinyl' and 'Bottom protection, rubber' (flagged, Opng.)")
m.C("A-101", "Thumb-turn privacy function at restroom / green room doors (3)", PRIVACY, "1", "substitute",
    "scheduled: thumb latch on the inside (privacy) at 3 doors, product not specified; row is a complete standard-duty privacy lockset (door 15 already carries a keyed lever HW-9 - how the thumb turn is provided is a takeoff RFI)")
m.L("A-102", "book_row_not_matching", "double-cylinder deadbolt at (E) door E12: the matching row OT-08712041-1010 (tubular deadlock, double cylinder) is verified but carries no unit and cannot be extended; whether the bolt is new is a takeoff RFI",
    "OT-08712041-1010 (verified, no unit)")
m.L("A-103", "book_row_not_matching", "door louvers in the 7 type-G doors: louver size is not given on A-7.10 and 4 of the doors are 60-minute rated (fire-rated louvers are not in the table); the steel louver rows need a size", HW_LOUVER_CAND)
m.C("A-104", "Hollow metal frames, 60-min label, for doors 19, 21, 27, 34, 35 (5 of the 7 counted)", HM_FRAME_B, "5/7 (takeoff notes: corrected count 5 HM frames + 2 aluminum frames)", "substitute",
    "scheduled: welded HM frames 2\" face (header detail 6/A-7.10) for 3'-0\" x 7'-0\" doors (door 27: 3'-0\" x 8'-0\"); row is 14 ga B-label HM frame up to 5-3/4\" deep, 4'-0\" x 7'-0\" single "
    "(the 3'-0\" x 7'-0\" B-label single is not in the table; width and the 8'-0\" height differ); sealant and anchors per the detail not priced")
m.U("A-104", "Aluminum frames for doors 05 and E14 (2 of the 7 counted)", "carried_elsewhere", "door 05 frame is priced in A-106 (aluminum frames); E14 is an (E) door and frame")
m.C("A-105", "Wood door frames 2\" typ., 10 wood doors + 4 cased openings (L.F. of jamb and head)", WD_FRAME,
    "244.67/14 (frame L.F. = 2 jambs + head: ten 3'-0\" x 7'-0\" doors 15/18/22/24/25/28/29/30/31/39 = 17 LF each = 170; cased openings 02 and 03 at 3'-0\" x 8'-0\" = 19 LF each = 38; 04 at 3'-8\" x 8'-0\" = 19.67; 23 at 3'-0\" x 7'-0\" = 17; total 244.67 LF for 14 frames)",
    "substitute", "scheduled: 2\" wood frames, species not stated, painted P-1 (paint in A-170); row is interior wood door frame, pine 11/16\" x 3-5/8\" deep, per L.F. (2\" frame stock not in the table); the planton mouldings are A-178")
m.C("A-106", "Aluminum storefront-type frames for doors 05 and 06 (2 of 6)", SF_FRAME, "2/6 (takeoff: 6 aluminum frames = doors 05, 06, 07, 08, 17, 26; 05 and 06 are swing doors, the other 4 are Eliason pivot doors)", "substitute",
    "scheduled: aluminum frames 2\" typ.; row is aluminum door frame for 3'-0\" x 7'-0\" entrance doors, bronze finish (door 05 is 8'-0\" high and 60-minute rated - an aluminum frame cannot carry the rating, takeoff conflict; door 06 is 7'-9\")")
m.U("A-106", "Frames of the 4 Eliason-type doors 07, 08, 17, 26", "quote", "the Eliason door comes with its own frame (takeoff: 'confirm'); priced with the door quote rows A-059, A-060, A-069, A-077")
m.C("A-107", "Door thresholds (29)", THRESH, "1", "substitute",
    "A-2.75/A-2.76 KN2 and detail 7/A-7.10: threshold at each door, 1/4\" max exterior / 1/2\" max interior, profile not specified; row is bronze panic threshold 5\" wide x 1/2\" thick (an exterior-type product; interior saddles are not in the table)")
m.C("A-108", "Aluminum storefront frame, 2\" face, 3'-10\" x 8'-1\" fixed unit (L.F. of perimeter)", TUBE_FRAME, "23.833 (perimeter 2 x (3'-10\" + 8'-1\") = 2 x (3.833 + 8.083) ft per the A-7.10 window schedule)", "substitute",
    "scheduled: Arcadia TC470 STC acoustic storefront frame, 2\" face, 5\" sill, finish P-2; row is plain aluminum tube framing 1-3/4\" x 4\", mill finish (acoustic / thermally improved system and the P-2 finish not in the table)")
m.C("A-108", "Insulated laminated glass unit 1-1/8\" (S.F.)", INSUL_GLASS, "3.833*8.083 (3'-10\" x 8'-1\" per the A-7.10 window schedule, V.I.F.)", "substitute",
    "scheduled: 1-1/8\" insulated unit, 3/8\" .030 laminated - 1/2\" air - 1/4\" .030 laminated, 40 STC; row is 1\" insulating unit with 1/4\" tempered lites, heat-reflective (laminated acoustic unit not in the table); GL-1 printed on the schedule is a takeoff RFI")
m.L("A-109", "not_quantified", "access hatches in drywall ceilings (Williams Bros. WB DW 405): specification only, locations not shown (RFI)", "OT-08311310-4150 (verified, recessed door for drywall, metal 12\" x 24\")")
m.L("A-110", "not_quantified", "access hatches in tile ceilings (Williams Bros. WB DWAL 414): no location (RFI)", "OT-08311310-3100 (verified, recessed door for acoustic tile 12\" x 12\")")
m.L("A-111", "not_in_book", "rodent-proof hard rubber door-bottom gasket at 3 exterior doors (A-7.10 detail 7): no door-bottom gasket line with a verified status (08 71 25 rows flagged)")

# ===============================================================================================================
# CEILINGS A-112..A-123
# ===============================================================================================================
for k, where, lvl_txt in (("A-112", "kitchen zone, dry storage, hallway 04 at 7'-6\"", "the row is the level 5 skim-coat line; BOH rooms (kitchen, storage) are level 4 per the A-2.10 note"),
                          ("A-113", "8'-0\" dining soffit band, host, green room", "level 5 patron areas per the A-2.10 note"),
                          ("A-114", "prep bar 24 at 7'-6\"", "the row is the level 5 skim-coat line; the prep bar is BOH (level 4)")):
    m.C(k, f"CLG-1D steel ceiling framing ({where})", CLG_FRAME, "1", "substitute",
        "ceiling type CLG-1D: (N) cold-formed steel joists 3-5/8\" (spans < 4'-0\") / 6\" elsewhere, spacing and gauge not stated (takeoff RFI); row is suspended GWB ceiling framing, 1-1/2\" carrier channels "
        "24\" OC with 7/8\" furring channels 16\" OC, per S.F. - a different framing system of the same function (joist LF cannot be derived without a spacing); also listed in A-115", match="partial")
    m.C(k, f"CLG-1D 5/8\" Ultralight Firecode 30 GWB, smooth washable finish ({where})", GWB_CLG_X_L5, "1", "substitute",
        f"ceiling type CLG-1D: USG Sheetrock Ultralight Firecode 30 5/8\" (a 30-minute lightweight panel, not Type X); row is fire-resistant GWB on ceilings with compound skim coat (level 5); {lvl_txt}; "
        "finishes (P-1 / P-2 / WC-3 / WC-6 / WC-8 / P-4) in the finish rows; also listed in A-116")
m.L("A-115", "carried_elsewhere", "aggregate: the CLG-1D framing (3050 SF) is priced in A-112, A-113 and A-114 with the suspended ceiling carrier row (partial substitute)")
m.L("A-116", "carried_elsewhere", "aggregate: the CLG-1D board (3050 SF) is priced in A-112, A-113 and A-114 with the fire-resistant GWB on ceilings level 5 row")
m.C("A-117", "Fascia GWB on the vertical face between the 8'-0\" soffit and the 16'-9\" waffle", GWB_SOF_L5, "8.75 (vertical face 16'-9\" - 8'-0\" = 8'-9\" = 8.75 ft per LF of edge, takeoff notes; RFI vertical vs sloped)", "substitute",
    "A-3.12 KN3 edge of attic: GWB face 8'-9\" tall, no section on the A-sheets (RFI); row is GWB on beams, columns or soffits with level 5 skim coat (Type X not stated for the fascia)")
m.C("A-117", "Fascia framing, 3-5/8\" 20 ga studs (S.F. of face)", STUD20_358, "8.75 (same 8'-9\" face per LF of edge)", "substitute",
    "framing of the fascia is not detailed ('GWB on steel framing'); row is 09 22 16.13 non-load-bearing 20 ga 3-5/8\" studs 16\" OC per S.F. (16'-high group) used as a vertical drop wall", match="partial")
m.C("A-118", "CLG-1A (E) GWB ceiling repaint, primer & 2 coats", PAINT_WALL, "1", "substitute",
    "A-7.21 ceiling 'Extg' for rooms 11/12/13, finish not scheduled (takeoff: patch and repaint); row is painting walls complete incl. surface prep, primer & 2 coats on drywall, roller - a wall row applied "
    "to a ceiling (no verified ceiling line in 09 91 23.72); A-5.11 'no revision to existing restrooms' conflict is a takeoff RFI")
m.U("A-118", "Patching of the (E) GWB ceiling", "not_quantified", "patch extent not quantifiable (takeoff: patch and repaint); no basis for the 09 01 70 repair rows")
for k, where in (("A-119", "1st floor dining 02 and stair 1"), ("A-120", "mezzanine / attic rooms")):
    m.C(k, f"CLG-3A cleaning of the (E) exposed concrete waffle ({where})", WASH_MASONRY, "1", "substitute",
        "A-3.12 KN1: GC to clean and patch (E) surfaces as required; row is surface preparation, walls, wash, masonry brick & block smooth (labor only) - a wall-washing row applied to a concrete coffered ceiling; "
        "no concrete-ceiling cleaning row in the table", match="partial")
    m.U(k, "Patching of the (E) concrete surfaces", "not_quantified", "extent 'as required' (A-3.12 KN1), not quantifiable; the concrete patching row of the table (OT-03013062-2200, walls 3/4\" deep incl. chipping and epoxy grout) needs an area",
        "OT-03013062-2200 (verified, concrete patching walls 3/4\" deep, S.F.)")
m.U("A-120", "Stain & seal of the (E) concrete beams and slab at dining 2, hallway 35 and BOH (1604 SF of the 2950 SF, Addendum 1)", "spec_not_issued",
    "Addendum 1 A-4.30/31/33 'stained & sealed, typ.' - the ST-2 / SL-2 tags are not listed on A-7.20 (product unknown, RFI); the book's dye / stain row is for polished concrete floors",
    "OT-03354310-0300 (verified, spray-on dye or stain 1 coat, polished concrete floors, M.S.F.)")
m.L("A-121", "not_in_book", "K-13 spray-applied cellulose acoustical insulation in the coffers (3773 SF gross, net coffer area smaller, thickness / colour / NRC not specified - RFI): the table has no sprayed cellulose acoustical row "
    "(07 21 29 sprayed-on rows are fiberglass and flagged; 07 21 26 blown cellulose is for attics and flagged; 09 81 cellulose fiber board is machine_read)",
    "OT-07212910-3355 (verified, sprayed-on fiberglass 5-1/2\" thick, vertical - a thermal insulation, different product)")
m.C("A-122", "Curved GWB soffits of the 8 fins and the stage arch, painted P-3 (plan projection SF)", GWB_SOF_L5, "1", "substitute",
    "A-3.22 '15'-9\" CLG-1D P-3 CURVE UP': GWB on the fin framing (fins are A-174, quote); row is GWB on beams, columns or soffits with level 5 skim coat, flat; the quantity is the plan projection - the developed curved area is larger (takeoff notes); P-3 paint in A-156")
m.L("A-123", "not_quantified", "ceiling access hatches: specification only, no count or locations (RFI)", "OT-08311310-4150 (verified, recessed door for drywall 12\" x 24\")")

# ===============================================================================================================
# FLOORS A-124..A-137
# ===============================================================================================================
m.C("A-124", "FL-2 epoxy quartz flooring (Onyx Quartz Moonlight)", QUARTZ_EPOXY, "1", "substitute",
    "A-7.20 FL-2: Onyx Concrete Coatings epoxy 'Quartz Moonlight', system thickness not stated; row is quartz flooring, epoxy with colored quartz chips broadcast 3/8\" thick, troweled, 'maximum' line "
    "(the broadcast lines of 09 67 26.26 are flagged); the lift-car floor and the (E) storage floor are excluded per the takeoff; substrate prep is A-132")
m.L("A-125", "not_in_book", "B-2 epoxy cove base 6\" high with 3/8\" radius (Onyx, 357.2 LF): no epoxy / resinous cove base line in the table (09 65 / 09 66 cove rows are vinyl, zinc-strip and terrazzo bases)")
for k, fl, prod, n in (("A-126", "FL-4", "Milliken ACU180-169-27 Red", "185"), ("A-127", "FL-5", "Milliken SOC169 Resonate", "159")):
    m.C(k, f"{fl} carpet tile 1 m x 1 m (S.Y.)", CARPET_TILE, "1/9 (S.F. to S.Y.)", "substitute",
        f"A-7.20 {fl}: {prod} carpet tile 1 m x 1 m ({n} tiles before cutting, takeoff), face weight / backing not stated; row is tufted nylon carpet tile 24\" x 24\" hard back (35 oz. line of 09 68 13.10) per S.Y."
        + ("; stair 1 treads / risers / landing are in the SF per the takeoff; stair 2 (exit-stair permit) and the Day-2 rooms 34 / 35 are flagged in the takeoff notes" if k == "A-127" else ""))
m.C("A-128", "FL-6 LVT plank 6\" x 48\" x 0.1\"", VINYL_TILE, "1", "substitute",
    "A-7.20 FL-6: Armstrong LVT J5240 Parallel USA20 Golden Sand 6\" x 48\" x 0.1\" plank; row is vinyl tile flooring 12\" x 12\" 1/8\" thick, premium colors / patterns (luxury vinyl plank not in the table); "
    "the stage tops are included in the SF per the takeoff (mezzanine stage outline RFI)")
m.C("A-129", "FL-7 / FL-8 porcelain floor tile 12\" x 12\" checker with GRT-1 grout", PORC_1X1, "1", "substitute",
    "A-7.20: Crossville Color Blox 2.0 12\" x 12\" porcelain in two colours (checker), Custom #60 charcoal grout 1/8\"; row is thin-set porcelain-type ceramic tile 1\" x 1\" mosaic, 1 color, color group 2 "
    "(no verified 12\" x 12\" porcelain floor line; the 12\" x 12\" line of the table is a wall-tile row); the A-7.21 FL-3 / A-5.11 'no revision' conflicts are takeoff RFIs")
m.L("A-130", "not_quantified", "FL-9 black terrazzo entry step / stair 2 slab: not quantifiable in SF (takeoff); the exterior step is priced per LF in A-207")
m.C("A-131", "SL-1 clear sealer on the (E) sealed concrete (material, Gal.)", SEALER_WB, "1/350 (350 S.F. per gallon printed on the row)", "substitute",
    "A-7.20 SL-1: Monopole 3900 Permaseal urethane sealer; row is water-based concrete sealer 350 S.F./gal., 5 gallon pail - material only, no application labor in the row; the urethane product is not in the table")
m.L("A-132", "not_quantified", "floor preparation / levelling / moisture testing under the new finishes: not specified and no area (RFI)", "OT-09651010-4000 (verified, latex underlayment 1/8\" cementitious, Gal.)")
m.C("A-133", "B-4 base 9/16\" x 5-1/4\" MDF, paint grade (L.F.)", POPLAR_BASE, "1", "substitute",
    "A-7.20 B-4: MDF base 9/16\" x 5-1/4\" painted P-2; row is base molding classic profile 5/8\" x 5-1/2\", poplar (MDF base not in the table; size differs)")
m.C("A-133", "P-2 paint on the B-4 base, primer & 2 coats (L.F.)", PAINT_FRAME_LF, "1", "substitute",
    "A-7.20 P-2 Dunn-Edwards DEA002 on the base; row is door frames & trim only, brushwork, primer & 2 coats exterior latex per L.F. (an exterior-latex trim row; no interior trim L.F. line verified)")
m.L("A-134", "quote", "B-5 LED light base: CORE Lighting ALP-2500TL aluminum LED channel base 4\" high painted P-5 (657.7 LF, faceted at the curved walls) - a manufacturer's lighting-channel product not in the table; the LED strip and drivers are in mep.csv")
m.C("A-135", "B-1 ceramic cove base 6\" x 8\" top set, 3/8\" radius (L.F.)", TILE_COVE_6, "1", "substitute",
    "A-7.20 B-1: Daltile S-3619 6\" x 8\" cove base; row is thin-set sanitary cove base 6\" x 6\" high (6\" x 8\" unit not in the table); the (E) restroom scope conflict (A-5.11) is a takeoff RFI")
m.L("A-136", "spec_not_issued", "B-3 base at restrooms 22/23 (72.4 LF): 'NOT USED' on A-7.20, product unknown (takeoff RFI: probably the B-1 Daltile cove)", "OT-09311310-1600 (verified, sanitary cove base 6\" x 6\" high, L.F.)")
m.L("A-137", "book_row_not_matching", "transition strips between floor finishes (134.7 LF, flush profile not specified): the vinyl transition strip rows OT-09651337-0235 / -0255 are verified but carry no unit",
    "OT-09651337-0235 (verified, vinyl transition strip carpet to various materials, no unit); OT-09651337-0255 (verified, various to various, no unit)")

# ===============================================================================================================
# WALL FINISHES A-138..A-170
# ===============================================================================================================
m.C("A-138", "WC-3 Type II vinyl wallcovering, host walls", VINYL_WC_T2, "1", "exact",
    "A-7.20 WC-3: Calico Wallpaper 1205 Pyrite Type II vinyl 51\" wide; row is fabric-backed vinyl wall covering, medium weight type 2 (20-24 oz./S.Y.) incl. adhesive and hanging; no pattern repeat / waste added (takeoff)")
m.C("A-139", "WC-3 Type II vinyl on the CLG-1D soffit band ceilings", VINYL_WC_T2, "1", "substitute",
    "A-7.21 ceiling finish WC-3 at 8'-0\" (ceiling application of a Type II vinyl - takeoff: confirm with the architect); row is type 2 vinyl wall covering on walls")
for k, where in (("A-140", "dining 02 walls"), ("A-141", "green room 03"), ("A-142", "hallway 04 (Addendum 1 A-4.26; A-7.21 lists WC-3 - RFI)"), ("A-143", "mechanical attic 25 (a walnut vinyl in a mechanical attic - RFI)")):
    m.C(k, f"WC-8 Type II vinyl wallcovering, {where}", VINYL_WC_T2, "1", "exact",
        "A-7.20 WC-8: MDC Wall BBWR11 Special Walnut Type II vinyl 54\" wide; row is fabric-backed vinyl wall covering, medium weight type 2 (20-24 oz./S.Y.); SF gross of the (E) column faces per the takeoff")
m.L("A-144", "quote", "WD-1 poplar slat panelling 1\" x 1/2\" strips stained ST-1 over WC-8 at the stage walls (209 SF): custom millwork, slat spacing not given (RFI); no wood slat / board panelling row in the table (06 25 rows are hardboard panelling)")
m.C("A-145", "Poplar moulding grid 1/2\" x 1/4\" at 1'-8\" x 2'-4\" o.c. over WC-8 (L.F.)", POPLAR_SHOE, "1", "substitute",
    "Addendum 1: 1/2\" x 1/4\" poplar strips stained ST-1 (walnut) in a grid; row is shoe molding 1/2\" x 3/4\", poplar (the 1/2\" x 1/4\" strip is not in the table); the attic WC-8 has no grid (takeoff)")
m.U("A-145", "Stain ST-1 on the poplar grid", "book_row_not_matching", "stain / seal rows of the table are per S.F. of broad surface (wood frames / trusses); a 1/2\" strip has no S.F. basis on the documents",
    "OT-09912352-7260 (verified, stain brushwork wipe off on trusses and wood frames, S.F.)")
for k, where in (("A-146", "dining 2 incl. vestibule"), ("A-147", "hallway 35 (Day 2 - confirm base bid)"), ("A-148", "BOH 34 (Day 2)"), ("A-149", "stair 1 shaft walls full height"), ("A-150", "ADA lift vestibule at the mezzanine")):
    m.C(k, f"WC-4 red vinyl architectural film, {where}", VINYL_WC_T1, "1", "substitute",
        "A-7.20 WC-4: Calico / 3M DI-NOC HG-1511 red vinyl 48\" wide - a self-adhesive vinyl film; row is fabric-backed vinyl wall covering, lightweight type 1 (12-15 oz./S.Y.), paste-hung (adhesive film not in the table); no waste added (takeoff)")
for k, where in (("A-151", "mezzanine restrooms 22/23, 4'-0\" wainscot"), ("A-152", "(E) restrooms 11/12/13, 4'-0\" assumed (A-5.11 'no revision to existing restrooms' conflict - RFI before pricing)")):
    m.C(k, f"WT-1 / WT-2 ceramic wall tile 5\" x 6\" with GRT-1 grout, {where}", WALL_TILE_6X4, "1", "substitute",
        "A-7.20: Tile-Shop Verso 5\" x 6\" black matte / white glossy, Custom #60 grout 1/8\"; row is thin-set ceramic wall tile 6\" x 4-1/4\" (5\" x 6\" not in the table); WT-1 / WT-2 split not stated (RFI); backer board in A-047")
m.C("A-153", "P-1 paint on GWB walls, primer & 2 coats", PAINT_WALL, "1", "exact",
    "A-7.20 P-1 Dunn-Edwards DEHW05 water-based acrylic semi-gloss, 2 coats over primer (A-7.21 notes 2 and 7); row is painting walls complete incl. surface prep, primer & 2 coats finish on drywall, roller")
m.C("A-154", "P-1 paint on the CLG-1D ceilings of the kitchen zone, storage and prep bar", PAINT_WALL, "1", "substitute",
    "A-7.21 ceiling P-1 semi-gloss washable; row is the walls-complete primer & 2 coats on drywall row applied to a ceiling (no verified ceiling line in 09 91 23.72)")
m.C("A-155", "P-2 paint on the hallway 04 CLG-1D ceiling", PAINT_WALL, "1", "substitute",
    "A-7.21 ceiling P-2 Dunn-Edwards DEA002 black semi-gloss; row is the walls-complete primer & 2 coats on drywall row applied to a ceiling; the P-2 bases are priced in A-133, the lobby wood frames in A-183 / A-170 (frame colour conflict RFI)")
m.C("A-156", "P-3 paint on the curved fin soffits (plan projection SF)", PAINT_WALL, "1", "substitute",
    "A-3.22 CLG-1D P-3 Bright Mango; row is the walls-complete primer & 2 coats on drywall row applied to curved soffits; plan-projection area (fin side faces need the fin profile - RFI); the strip-light channel and drapery frames in P-3 are A-182 / A-183")
m.L("A-157", "book_row_not_matching", "P-4 Modern Masters metallic paint 'Brass Monkey' (390 SF): a decorative metallic coating system; the table carries only standard latex and clear glaze coating rows; the WC-4 / P-4 conflict at the mezzanine lift lobby is a takeoff RFI",
    "OT-09912372-1670 (verified, walls primer & 2 coats latex on drywall); OT-09912372-3600 (verified, glaze coating 3 coats spray, clear)")
m.C("A-158", "P-5 paint on 17 mezzanine door frames / mouldings, primer & 2 coats (L.F. of frame)", PAINT_FRAME_LF, "17 (jambs 2 x 7'-0\" + head 3'-0\" = 17 LF per 3'-0\" x 7'-0\" frame)", "substitute",
    "Addendum 1 A-4.30..A-4.33 'FRAME P-5' Dunn-Edwards DEA106 (A-7.10 schedules P-1 - RFI); row is door frames & trim only, brushwork, primer & 2 coats exterior latex per L.F.; the bar-opening panelling and LED channel counted in the 17 are not frames")
m.L("A-159", "spec_not_issued", "P-6 on the stair 1 steel (63.7 LF): P-6 is not listed on A-7.20 - product / colour unknown, shop primer vs field paint unknown (RFI)",
    "OT-09911342-0310 (verified, stair stringers exterior metal, roll & brush zinc chromate to 14\", each coat, L.F.)")
m.C("A-160", "WC-1 FRP panels on GWB, full height", FRP_SMOOTH, "1", "substitute",
    "A-7.20 WC-1: Marlite P-100 FRP white (P-100 is the pebbled / embossed standard panel), size TBD, LA County Health approved; row is FRP panels .090\" thick on walls, adhesive mounted, smooth surface "
    "(the embossed adhesive-mounted line is not verified); full height to 7'-6\" assumed by the takeoff; mouldings not priced")
m.L("A-161", "not_quantified", "WC-2 custom 18 ga brushed stainless sheet lining behind the hoods and at the pick-up counter border (21.7 LF): SF not computable without the lining height (takeoff)",
    "OT-10262313-1775 (verified, stainless steel wall protection 16 ga 48\" x 36\" screwed to studs, S.F.)")
m.C("A-162", "WC-5 Tectum acoustic panels wrapped in TX-2 velvet, full height of the curved wall", FABRIC_PANEL, "1", "substitute",
    "A-7.20 WC-5 Armstrong Tectum White TWH wrapped in Carnegie 6506/10 Pigment velvet (TX-2), thickness / panel size not specified; row is fabric-covered mineral fiberboard acoustic panels 30\" x 108\" x 3/4\", concealed spline, "
    "wall mounted (a wood-fiber Tectum panel with a custom velvet wrap is not in the table); 8'-0\" vs 9'-1\" height is a takeoff RFI")
m.C("A-163", "Drapery hardware HW-20 / HW-21: traverse rod per set (3)", TRAVERSE_ROD, "1", "substitute",
    "HW-20 / HW-21 are not in the A-7.10 hardware schedule (track / rod / rings unspecified - RFI); row is adjustable traverse rod 28\" to 48\" for the 3'-0\" openings; the 2\" painted wood frames are A-183")
m.U("A-163", "TX-2 velvet drapery panels (3 sets)", "not_quantified", "fabric yardage not computable: fullness, finished length and lining not given (takeoff); Carnegie 6506/10 velvet 54\" wide; the two elevations at opening 02 may be one drapery (2 sets if so)",
    "OT-11614310-1000 (verified, stage curtains velour medium weight, S.F.)")
m.L("A-164", "not_quantified", "TX-1 Architex 'Annie' velvet drapery '2nd level': location and size not shown (RFI)")
m.L("A-165", "spec_not_issued", "TX-4 fabric at the stage arch panel and stretched over the fin panels (182 SF): product cells blank on A-7.20 (RFI); fin panel sizes not given")
m.L("A-166", "spec_not_issued", "WC-6 gold wallpaper on the host ceiling and the entry transom (131 SF): manufacturer / model blank on A-7.20 (RFI); transom size not given",
    "OT-09722310-3700 (verified, wallpaper average workmanship solid pattern low cost paper, S.F.)")
m.L("A-167", "not_quantified", "WC-7 gold window film: area unknown and the entry graphic may be owner artwork (RFI)", "OT-08871310-1120 (verified, solar film on glass silver 35% VLT, S.F.)")
m.L("A-168", "not_quantified", "GL-1 Altered Glass 'Nugold' gold mirror at the 2nd level bar: no size or location (RFI)", "OT-08831310-0200 (verified, mirror 1/4\" plate glass polished edge, S.F.)")
m.L("A-169", "spec_not_issued", "stain & seal of the (E) concrete columns (35 EA, SF not computed - heights vary): ST-2 / SL-2 are not listed on A-7.20 (product unknown, RFI); the beam / slab stain & seal is a component of A-120")
m.C("A-170", "Paint P-1 on doors and frames, both sides, primer & 2 coats (22 openings)", PAINT_DOOR_EA, "1", "substitute",
    "A-7.10 finish column P-1 for 18 wood / HM doors and 4 cased openings; row is interior latex, doors flush both sides incl. frame & trim, primer & 2 coats, per door - the 4 cased openings have no leaf (frame only), "
    "and the Addendum shows P-2 / P-5 frames and WC-4 / WC-8 door faces (colour conflict RFI)")

# ===============================================================================================================
# MILLWORK A-171..A-183
# ===============================================================================================================
m.L("A-171", "quote", "main stage platform 12'-0\" x 6'-8\" curved front, 18\" high, millwork framing not detailed, fascia finish not stated (RFI): custom millwork to be quoted; the FL-6 top is in A-128",
    "OT-11612310-7100 (verified, band risers steel frame plywood deck, no unit); OT-11612310-5100 (verified, portable stage with steps 16\" high, Ea. - a portable product)")
m.L("A-172", "not_quantified", "mezzanine stage platform(s) 6\" high: size not identified on A-2.20 (3 KN22 tags, RFI)")
m.L("A-173", "quote", "stage decorative wood frame 4\" x 3\" curved top, painted P-2, with 1 W bulbs @ 12\" o.c. (22.8 LF): custom millwork with integrated lamp holders; lamps / wiring in mep.csv")
m.L("A-174", "quote", "light-beam fins above the main stage (9 per A-4.22 / 8 per A-3.22 - RFI): curved full-height 8\" acoustic-core fins with drywall faces, jogs and bolted lighting channels per A-4.22A - custom millwork / framing assembly; the fin soffit GWB is A-122 and the P-3 paint A-156")
m.C("A-175", "Stainless steel pick-up counter 5'-10\" x 1'-6\" at 34\" AFF (S.F.)", SS_COUNTER, "8.75 (5'-10\" x 1'-6\" = 5.833 x 1.5 ft per A-5.20)", "substitute",
    "A-5.20: custom 18 ga stainless counter with WC-2 stainless border at the 36\" opening; row is stainless steel countertop, custom, per S.F. (the border / opening lining and the wall support are not in the row); "
    "Addendum 1 A-4.33 draws the same opening 6'-0\" wide at 42\" AFF - takeoff RFI which governs")
m.L("A-176", "quote", "bar opening at the prep bar / dining 2 (Addendum 1 A-4.33): low wall countertop at 42\" AFF of unspecified material (RFI), 6\" x 2\" wood frame and 6\" x 1\" wood panelling painted P-5 - custom millwork; the low wall framing is not typed")
m.L("A-177", "quote", "KegWorks bar foot rail 6'-0\" (A-4.33 det 8): manufacturer's product, model / finish / brackets not stated (RFI)")
m.L("A-178", "quote", "planton poplar mouldings over / around 5 mezzanine doors (9/A-4.31: three 2\" steps with R1/2\", 6\" total), painted P-5: a custom built-up profile, LF per door not dimensioned (RFI); paint P-5 counted in A-158")
m.L("A-179", "not_quantified", "2\" wood frame cased openings at the 3 mezzanine hallway arches (A-4.31 / A-4.32): arch dimensions not given and the arches are not in the A-7.10 cased-opening list (RFI)",
    "OT-06481610-3000 (verified, interior wood door frame pine 11/16\" x 3-5/8\", L.F.)")
m.L("A-180", "quote", "lobby base cabinet 2'-10\" high with LM-2 laminate, STN-2 stone top, HW-7 pulls and 2\" walnut shelves (A-4.20): LM-2 / STN-2 / HW-22 are unlisted codes and the cabinet width is not dimensioned (RFI) - custom millwork")
m.C("A-181", "Green room make-up counter 60\" x 18\" Silestone top (L.F.)", QUARTZ_TOP, "5 (60\" counter length = 5 LF per A-4.21)", "substitute",
    "A-7.20 STN-1 Cosentino Silestone 'Ethereal Haze' 1.2 cm; row is quartz agglomerate countertop 25\" wide with 4\" backsplash, color group A, minimum (18\" deep, no backsplash, 1.2 cm and the colour group differ); "
    "support brackets / base not detailed (takeoff); outlet and switch in mep.csv")
m.L("A-182", "quote", "2\" x 18 ga bent metal channel for the strip light at the lobby ceiling edge, painted P-3 (17.3 LF): a custom sheet-metal fabrication not in the table; the strip light is in mep.csv")
m.C("A-183", "2\" painted wood frames around the 3 drapery openings (L.F. of frame)", WD_FRAME, "49.3/3 (takeoff notes: opening 02 = 19 LF per side x 2 sides + green room window 3'-0\" x 2'-8\" = 11.3 LF; 49.3 LF for 3 frames)", "substitute",
    "A-4.20 / A-4.21 / A-4.23: 2\" wood frame, species not stated, painted P-3; row is interior wood door frame, pine 11/16\" x 3-5/8\" deep, per L.F. (2\" frame stock not in the table)")
m.C("A-183", "P-3 paint on the drapery frames, primer & 2 coats (L.F.)", PAINT_FRAME_LF, "49.3/3 (same 49.3 LF of frame for 3 openings)", "substitute",
    "P-3 Dunn-Edwards DE5195 Bright Mango; row is door frames & trim only, brushwork, primer & 2 coats exterior latex per L.F. (exterior-latex trim row)")

# ===============================================================================================================
# SPECIALTIES A-184..A-193
# ===============================================================================================================
m.L("A-184", "quote", "reception desk Natura Design Works 'Mila' black tambour 36\" x 190.7\" x 44\" H: a furniture product, furnished-by not stated (A-7.20 does not list it - RFI owner vs GC); installation only if owner-furnished")
m.L("A-185", "quote", "oblong mirror 60\" x 48\" tempered bronze glass in a walnut-stained frame (lobby): custom framed mirror, furnished-by not stated (RFI); the book mirror rows are unframed plate glass", "OT-08831310-0200 (verified, mirror 1/4\" plate glass polished edge, no frame, S.F.)")
m.L("A-186", "quote", "oblong mirror 60\" x 48\" tempered clear glass in a walnut-stained frame (green room): custom framed mirror, furnished-by not stated (RFI)", "OT-08831310-0200 (verified, mirror 1/4\" plate glass polished edge, no frame, S.F.)")
m.L("A-187", "quote", "IBM Mirror 'Hollywood Mirror Princess' 60\" x 45\" lighted make-up mirror: a manufacturer's lighted product, furnished-by not stated (RFI); power in mep.csv")
m.C("A-188", "Wall hook rail, 5 hooks (Mercury Row 'Garfinkel')", HOOK_STRIP, "1", "substitute",
    "A-4.21 elevation 4: Mercury Row Garfinkel 5-hook wall rail, furnished-by not stated (RFI); row is hat and coat strip, stainless steel, 4 hook, 36\" long (a decorative 5-hook retail rail differs)")
m.L("A-189", "not_in_book", "steel backing plates 4\" x 16 ga spanning 3 studs / nested 3-5/8\" x 16 ga studs behind fixtures over 50 lb (A-9.10 det 5 and note), 20 locations: no steel backing-plate or nested-stud line in the table (06 11 blocking rows are wood, per M.B.F.)",
    "OT-06111002-2740 (verified, miscellaneous wood blocking to steel construction, M.B.F. - a different material)")
m.L("A-190", "not_quantified", "fire extinguishers and cabinets: locations not shown (fire-department requirement, RFI); the kitchen K-class unit is in equipment.csv",
    "OT-10441353-1100 (verified, fire extinguisher cabinet 8\" x 12\" x 27\" steel door, Ea.); OT-10441613-2100 (verified, ABC 20 lb portable, Ea.)")
m.C("A-191", "Toilet room identification signage per 8 & 9/A-5.10 (2 restrooms)", SIGN, "1", "substitute",
    "A-5.12 KN15: ADA / Title 24 geometric door symbol + wall sign per 8 & 9/A-5.10 at restrooms 22/23; row is engraved panel signage, stock acrylic 2-sided with bracket, 3\" x 12\" (one sign per room priced; "
    "the geometric door symbol and the green room 'ROOM SIGN' (A-4.23) are not priced - type not specified)")
# A-192: qty 2 EA = 2 restrooms; per-item counts from the takeoff notes, one of each per restroom
m.C("A-192", "Grab bar 1-1/2\" dia x 36\" (KN3), 1 per restroom", GRAB36, "1 (takeoff notes: 2 x 36\" for 2 restrooms)", "exact",
    "A-5.12 KN3: 1-1/2\" dia grab bar 36\" at 2'-9\" AFF, manufacturer not specified; row is grab bar straight 1-1/2\" diameter stainless steel 36\" long")
m.C("A-192", "Grab bar 1-1/2\" dia x 42\" (KN4), 1 per restroom", GRAB42, "1 (takeoff notes: 2 x 42\" for 2 restrooms)", "exact",
    "A-5.12 KN4: 1-1/2\" dia grab bar 42\" at 2'-9\" AFF; row is grab bar straight 1-1/2\" diameter stainless steel 42\" long")
m.U("A-192", "Surface-mounted toilet tissue dispenser (KN5), 1 per restroom", "book_row_not_verified", "the toilet tissue dispenser line of 10 28 13.13 is flagged and prints an S.F. unit",
    "OT-10281313-4240 (flagged, toilet tissue dispenser plastic twin / jumbo double roll, unit printed S.F.)")
m.U("A-192", "Surface-mounted seat cover dispenser (KN6), 1 per restroom", "book_row_not_matching", "the verified seat cover dispenser row prints an S.F. unit for an each item and cannot be extended",
    "OT-10281313-6050 (verified, toilet seat cover dispenser stainless steel surface mounted, unit printed S.F.)")
m.U("A-192", "Partition-mounted TP / seat cover / sanitary combo unit (KN7), 1 per restroom", "book_row_not_matching", "a combination unit duplicating KN5 / KN6 (takeoff RFI); the table has single-function dispensers only",
    "OT-10281313-4220 (verified, napkin / tampon dispenser semirecessed, Ea.)")
m.U("A-192", "Trash receptacle (KN10), 1 per restroom", "book_row_not_matching", "the waste receptacle rows of 10 28 13.13 (13 / 36 gallon stainless) carry no unit", "OT-10281313-8100 (verified, waste receptacle stainless with top 36 gallon, no unit)")
m.C("A-192", "Power hand dryer (KN11), 1 per restroom", HAND_DRYER, "1 (takeoff notes: 2 hand dryers for 2 restrooms)", "exact",
    "A-5.12 KN11: power hand dryer, manufacturer not specified; row is hand dryer surface mounted electric 115 V 20 A; power in mep.csv")
m.C("A-192", "Coat hook on the door (KN13), 1 per restroom", ROBE_HOOK, "1 (takeoff notes: 2 coat hooks for 2 restrooms)", "exact",
    "A-5.12 KN13: coat hook on door at 4'-0\" AFF at ADA stalls, product not specified; row is robe hook, heavy duty, concealed mounting")
m.U("A-192", "Surface mirror, 1 per restroom", "book_row_not_matching", "mirror size not stated on A-5.12 / A-7.20; the mirror rows need a size", "OT-10281313-3200 (verified, mirror with stainless 3/4\" frame 48\" x 24\", Ea.); OT-08831310-0200 (verified, 1/4\" plate mirror, S.F.)")
m.L("A-193", "not_quantified", "new accessories at the (E) restrooms (8 EA mixed: recessed towel dispenser / waste receptacle KN13, baby changing station KN15, coat hooks KN16): the takeoff gives no per-item split of the 8, "
    "and A-5.11 'no revision to existing restrooms' conflicts with the keynotes (RFI); book rows exist per item",
    "OT-10281313-0610 (verified, towel dispenser and waste receptacle 18 gal, Ea.); OT-10281313-0400 (verified, changing station horizontal wall mounted plastic, Ea.); OT-10281313-4400 (verified, robe hook, Ea.)")

# ===============================================================================================================
# STAIR / LIFT A-194..A-202
# ===============================================================================================================
m.C("A-194", "Stair 1 handrails 1-1/2\" dia, both sides, with extensions (L.F.)", WALL_RAIL, "1", "substitute",
    "A-6.10 KN5: 1-1/2\" dia metal handrail at 34\"-38\" AFF with 12\" top and one-tread bottom extensions, finish not specified (P-6 on the stair steel is a separate RFI); row is wall rail, aluminum pipe 1-1/2\" diameter, "
    "satin finish, on brackets (material 'metal' not fixed; brackets not specified)")
m.L("A-195", "not_in_book", "visual warning strips 2\" wide at the top and bottom treads (15 LF): on FL-5 carpet treads the strip must be a carpet / insert product (takeoff RFI); no contrasting-strip line in the table")
m.L("A-196", "spec_not_issued", "LED strip for riser illumination at stair 1 (60 LF): not in the A-3.70 lighting schedule or mep.csv, product unknown (RFI); carried for the architectural channel / length")
m.C("A-197", "GWB soffit under the stair 1 flights and landing", GWB_SOF_L4, "1", "substitute",
    "A-6.11 KN9 '(N) overhead finish': GWB on the stair framing, finish not specified; row is GWB on beams, columns or soffits, taped and finished level 4 (board type / finish level not stated)")
m.C("A-198", "Catwalk guardrail 42\" high, 1-1/2\" stainless rail and posts @ 48\" o.c. with X-Tend cable mesh (L.F.)", SS_RAIL_3, "1", "substitute",
    "A-4.15: grade 304 stainless 1-1/2\" round top rail on 1-1/2\" posts @ 48\" o.c., Carl Stahl X-Tend cable mesh infill, 4\" x 1-1/2\" brackets, 29 posts (takeoff); row is shop-fabricated pipe railing 3'-6\" high, posts 5' OC, "
    "stainless steel 3 rail 1-1/2\" diam. #4 finish (cable mesh infill, 48\" post spacing and the beam brackets are not in the row)", match="partial")
m.C("A-199", "Theatrical lighting pipe rail 1-1/2\" with 1-1/2\" supports @ 48\" o.c. and 4\" x 4\" brackets (L.F.)", RAIL_42_STEEL, "1", "substitute",
    "A-4.15 detail 2: 1-1/2\" metal round pipe rail on 1-1/2\" round supports @ 48\" o.c. bracketed to the box beam, lights by owner; row is attached handrail on brackets, 42\" high steel, primed, straight & level "
    "(a single pipe on stand-off supports differs from a bracketed handrail; J-boxes in mep.csv)", match="partial")
m.L("A-200", "quote", "Garaventa Genesis Shaftway GVL-SW-120 vertical platform lift, 2 stops, 105\" travel + 3-1/2\" pit, 750 lb, 39\" x 52\" platform, with doors by McKinley Elevator (A-6.21 KN4) - a manufacturer's unit to be quoted "
    "(A-6.21 prints GVL-SW-144 and a different pit - RFI); the wheelchair lift rows of 14 42 16 are flagged; electrical, backing, tiebacks and pit in mep.csv / demo_struct_gc.csv", LIFT_CAND)
m.L("A-201", "quote", "Matot medium-duty dumbwaiter, car size K 36\" x 38\" x 48\", 2 stops, winding drum 50 fpm, stainless bi-parting doors - a manufacturer's unit to be quoted (capacity beyond the 100-750 lb class not stated); "
    "the electric dumbwaiter rows of 14 12 10 are flagged; beams, floor cut and access-door framing in demo_struct_gc.csv", DW_CAND)
m.C("A-202", "24\" x 24\" UL-listed access door at the dumbwaiter pit", ACCESS_FIRE, "1", "substitute",
    "A-6.30 cross-section: 24\" x 24\" UL listed access door, manufacturer not specified, rating to match the 1-hr shaft (takeoff); row is framed access door, fire rated with lock, metal, 24\" x 36\" (the fire-rated 24\" x 24\" line is not in the table; "
    "the verified 24\" x 24\" line OT-08311310-6250 is a non-rated metal door)")

# ===============================================================================================================
# EXTERIOR A-203..A-210
# ===============================================================================================================
m.L("A-203", "carried_elsewhere", "the same unit as window type A: frame and glass are priced in A-108 (takeoff: one unit total, not two)")
m.C("A-204", "Exterior plaster 1\" to match the (E) facade (S.Y.)", STUCCO, "1/9 (S.F. to S.Y.)", "substitute",
    "A-4.01 KN9 / wall note 3: 1\" exterior plaster over 2 layers felt on DensGlass, texture to match the (E) facade; row is stucco with bonding agent, 3 coats on walls, no mesh included (7/8\" standard; 1\" thickness and the matching texture "
    "are not in the row; no lath is called out on the documents and none is priced - RFI); felt and sheathing are in the type-3 wall rows A-011 / A-028")
m.L("A-205", "not_quantified", "aluminum metal panel at the new door bay head, colour to match the (E) window frame (A-4.01 KN12): extent not dimensioned (RFI)")
m.L("A-206", "not_in_book", "salvage and reset of the (E) granite base at the new door bay (7.33 LF, A-4.01 KN8): no granite or stone reset / salvage line in the table (04 43 rows are new bluestone, limestone, marble, slate)")
m.C("A-207", "Terrazzo step tread, black to match the Walk of Fame (L.F.)", TERR_TREAD, "1", "substitute",
    "A-4.01 KN10 / A-2.75 KN4: 7\" entry step in FL-9 black terrazzo matching the (E) sidewalk, manufacturer TBD; row is precast terrazzo 2\" thick tread, straight (cast-in-place matching terrazzo not in the table); "
    "the 7'-4\" x 5'-0\" landing topping (36.6 SF if finished, takeoff) and the slab repour (A-2.75 KN5, thickness not given) are not priced")
m.C("A-207", "Terrazzo step riser 7\" (L.F.)", TERR_RISER, "1", "substitute",
    "7\" step riser in black terrazzo; row is precast terrazzo stair riser 1\" thick to 6\" high, straight (7\" riser not in the table)")
m.C("A-208", "Exterior step handrails 1-1/2\" dia @ 34\" AFF, 2 each 3'-1 1/2\" (L.F.)", WALL_RAIL, "3.125 (3'-1 1/2\" = 3.125 ft per handrail, takeoff notes)", "substitute",
    "A-4.01 KN7: 1-1/2\" dia handrail each side of the recess, material / finish to match the (E) entry (not stated); row is wall rail, aluminum pipe 1-1/2\" diameter, satin finish, on brackets")
m.L("A-209", "carried_elsewhere", "exterior exit door 06: the door is priced in A-058, its frame in A-106 and its hardware in the HW rows (listed in the exterior block for completeness, takeoff)")
m.L("A-210", "not_quantified", "patch of the (E) plaster / stone at the removed window jambs and head and the (E) storefront glass & mullion repair (Addendum 1 A-4.34): no extent (RFI)")

m.write("matches_arch.csv")
