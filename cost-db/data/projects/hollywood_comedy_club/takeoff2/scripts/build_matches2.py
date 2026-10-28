#!/usr/bin/env python3
"""Writes the three mapping files read by price2.py:
   ../matches_mep.csv, ../matches_equipment.csv, ../matches_demo_struct_gc.csv

Every decision below was taken against book_lines_la_latest.csv (status, unit, description read for each code).
A component is priced only from a verified row; the exact difference to the drawn product is written in `reason`.
Factors are arithmetic expressions with the source of the conversion in parentheses (parsed by price2.py).

Run:  python3 -I build_matches2.py   (from any folder; writes next to the takeoff files)
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
# Book rows used (code, status read from the table on 2026-10-28)
# ---------------------------------------------------------------------------------------------------------------
CU = {"1/2": "OT-22111323-2140", "3/4": "OT-22111323-2180", "1": "OT-22111323-2200", "1-1/4": "OT-22111323-2220",
      "1-1/2": "OT-22111323-2240", "2": "OT-22111323-2260", "2-1/2": "OT-22111323-2280"}      # type L copper, solder joints, hangers 10' OC
CU_REASON = "P-1 materials table: copper type L; row is type L tubing with couplings and clevis hangers 10' OC (solder joints; joint method not stated on P-1)"
NOHUB_CAND = "p512 22 13 16.20 'PIPE, CAST IRON, Soil | No hub, couplings 10' OC' lines 4100-4160 (flagged, SECTION_ID_DOUBTFUL, no cost code)"
NOHUB_REASON = "P-1: no-hub cast iron; the no-hub cast iron soil pipe lines of the book (p512, lines 4100 1-1/2\" to 4160 4\") are flagged under an unreadable section header and carry no cost code"
WC, WC_RI = "OT-22411313-1140", "OT-22411313-1980"
LAV, LAV_RI = "OT-22441613-6000", "OT-22441613-6960"
SINK_RI = "OT-22411616-5790"
RECEPT = "OT-26272620-2460"
SWITCH = "OT-26272620-0200"
MOTOR120 = "OT-26058310-0020"
MOTOR230 = "OT-26058310-0110"
DISC30, DISC60 = "OT-26281620-0100", "OT-26281620-0200"
GWB_X = "OT-09291030-2150"
INSUL = "OT-07211620-1320"
PLATE14, PLATE38 = "OT-05122365-0100", "OT-05122365-0300"
HSS84 = "OT-05122317-5600"
PAN_STAIR = "OT-05511350-0200"
PAN_PLACE = "OT-03311370-6210"
RMX2500 = "OT-03311335-0100"
WALL_RAIL = "OT-05521350-0915"
SF_DOOR, SF_FRAME, CLOSER, THRESH = "OT-08431310-0020", "OT-08431310-0620", "OT-08712030-8030", "OT-08712065-0600"
PANIC_CAND = "OT-08712015-2250 (verified, average hardware set school exterior door incl. panic device - a hardware set, not a device)"
HM_DOOR, HM_FRAME_B = "OT-08131315-0080", "OT-08121313-5400"
ANCHOR_CAND = "OT-05051920-0600 (verified, 1/2\" x 2-1/16\" zinc expansion shield - a different product); OT-05051910-1430 (flagged, chemical anchor 3/4\" x 9-1/2\"); no 1/2\" chemical anchor line in the table"
ANCHOR_REASON = "drawn: 1/2\" dia x 4\" embedded threaded rods, drill and epoxy (Simpson SET-3G); the chemical-anchor lines of 05 05 19.10 are flagged / machine_read and start at 3/4\" dia; the only verified 1/2\" anchor is a zinc expansion shield, a different product"

# ===============================================================================================================
# MEP
# ===============================================================================================================
m = Map()

# ---- Mechanical
for k in ("M-001", "M-002", "M-003"):
    m.L(k, "book_row_not_verified",
        "water-source heat pump rows of 23 81 46.10 are machine_read (1, 2 and 5 ton cooling; scheduled units are 6, 8 and 10 ton)",
        "OT-23814610-2100 / -2140 / -2220 (machine_read, 1 / 2 / 5 ton)")
m.L("M-004", "not_quantified", "condenser-water loop source, routing and equipment not in the documents (RFI)")
m.L("M-005", "not_quantified", "condensate line LF not drawn (8 connections only); PVC rows are priced per L.F.", "OT-22111374-1860 (verified, PVC sch 40 1/2\", L.F.)")
m.C("M-006", "Duct smoke detector, duct type (Ea.) - device only", "OT-28461127-5400", "1", "substitute",
    "drawn: Air Products SL-2000-N ionization duct detector with sampling tubes and relay; row is a generic duct-type smoke detector; interlock wiring, relays and the GC access panel are not in the row")
m.L("M-007", "not_quantified", "thermostat / sensor count not drawn (8 WSHP zones scheduled); DDC sensor rows carry no cost", "OT-23092310-0130 (verified, space temperature sensor, no cost printed)")
m.L("M-008", "existing", "existing MUA-1 to remain; survey and repairs are carried on M-047")
m.L("M-009", "existing", "existing EF-1 to remain; survey and repairs are carried on M-047; EF-1 vs hood CFM conflict is an RFI")
for k in ("M-010", "M-011"):
    m.L(k, "book_row_not_matching",
        "drawn: in-line cabinet exhaust fan 150 CFM @ 0.3 in SP (Captive Aire SIF9DD-HE); the verified in-line centrifugal rows (OT-23341610-0260/-0280/-0300) carry no unit and start at 1,380 CFM; the only verified 150 CFM row is a pedestal utility set, a different fan type",
        "OT-23341410-7520 (verified, utility set pedestal 150 CFM 1/8 HP, Ea.); OT-23341610-0260 (verified, inline centrifugal 1,380 CFM, unit blank)")
for k in ("M-012", "M-013", "M-014"):
    m.L(k, "quote", "CaptiveAire hood package (job 8710180) by KEC; kitchen hoods are not in the book (only the hood removal row, flagged)", "OT-11050510-4750 (flagged, hood removal)")
m.L("M-015", "quote", "hood length line of the CaptiveAire package (M-012/M-013 carry the hoods); vendor quote scope")
m.L("M-016", "quote", "CaptiveAire TANK fire-suppression cabinet, part of the hood package (K2.0 item 55); wet-chemical system rows of 21 22 16 are 250-1,200 lb cylinder clean-agent systems, a different product")
m.L("M-017", "quote", "electric gas valve supplied with the CaptiveAire package; installation by the plumber has no verified row")
m.L("M-018", "not_quantified", "hanger rod lengths not dimensioned; the only rod row is coil rod per L.F. (material only)", "OT-03150530-5900 (verified, coil threaded rod 1/2\", L.F., material only)")
for k in ("M-019", "M-020", "M-021"):
    m.L(k, "not_in_book", "welded 16 ga grease duct is not in the book (23 31 13 carries only fittings add-percentages and a flexible-connection row)")
m.L("M-022", "not_in_book", "field-applied fire-rated grease duct wrap is not in the book (23 07 13 rows are FSK duct insulation wrap, a different product); SF not quantifiable (duct size not labeled)")
m.C("M-023", "Duct access door, insulated, 12\" x 18\" (Ea.)", "OT-23333313-1050", "1", "substitute",
    "drawn: tool-less grease-duct clean-out doors, size not given; row is an insulated duct access door 12\" x 18\" (not a grease-duct rated cleanout)")
for k in ("M-024", "M-025", "M-026", "M-027", "M-028", "M-029", "M-030"):
    m.L(k, "not_quantified", "duct depth and gauge not printed on M-2 (width scaled only); galvanized rectangular duct is priced per Lb. and the weight cannot be computed; the 23 31 13.13 rows on hand are fittings add-percentages only",
        "OT-23311313-1240 / -1244 / -1248 (percent_add)")
for k in ("M-031", "M-032"):
    m.L(k, "not_quantified", "no mezzanine mechanical plan; LF not drawn")
m.L("M-033", "not_quantified", "duct SF not quantifiable (sizes not labeled); duct wrap rows exist", "OT-23071310-3170 (verified, FSK wrap 1-1/2\" thick, S.F.); OT-23071310-3320 (verified, unfaced 1-1/2\")")
m.C("M-034", "Supply register, one or two way deflection, adjustable curved face bars, 24\" x 8\" (Ea.)", "OT-23371360-1340", "1", "substitute",
    "scheduled: Metal Aire VH double-deflection supply grille 24\" x 10\" with OBD; row is a 24\" x 8\" adjustable-bar supply register")
m.C("M-035", "Ceiling diffuser, aluminum, perforated, 24\" x 24\" lay-in panel, 24\" x 24\" (Ea.)", "OT-23371310-0620", "1", "substitute",
    "scheduled: Metal Aire 9000-6P modular core diffuser (4 cores 14\" x 14\") in a 2 x 2 T-bar panel with OBD; row is a perforated 24\" x 24\" lay-in diffuser with OBD")
m.L("M-036", "book_row_not_verified", "scheduled: modular core diffuser (4) 14\" x 14\" core, 15\" x 15\" opening; the 14\" x 14\" rectangular ceiling diffuser line is machine_read",
    "OT-23371310-1074 (machine_read, rectangular 1-4 way blow 14\" x 14\"); OT-23371310-1016 (verified, 10\" x 10\")")
m.C("M-037", "Ceiling diffuser, aluminum, rectangular, 1 to 4 way blow, 10\" x 10\" (Ea.)", "OT-23371310-1016", "1", "substitute",
    "scheduled: Metal Aire 9000-2 modular core diffuser (4 cores 10\" x 10\", 11\" x 11\" opening) with OBD; row is a rectangular 1-4 way blow aluminum diffuser 10\" x 10\" with OBD")
m.C("M-038", "Return register, ceiling or wall, fixed 45 deg face blades, 24\" x 36\" (Ea.)", "OT-23371360-5300", "1", "substitute",
    "scheduled: Metal Aire RH louvered return grille 36\" x 18\" with OBD; row is a 24\" x 36\" fixed-blade return register")
m.C("M-039", "Filter grille with filter, 24\" x 24\" (Ea.)", "OT-23371330-3060", "1", "substitute",
    "scheduled: Metal Aire RH-TB louvered return grille 22.5\" x 22.5\" in 2 x 2 T-bar with OBD; row is a 24\" x 24\" filter grille (with filter, no OBD)")
m.L("M-040", "spec_not_issued", "the 23 outlets drawn on M-2 carry no device tags (type and size cannot be read); the 16 scheduled devices are priced on M-034..M-039 and the drawn outlets overlap them (23 vs 16 is an RFI) - pricing both would double count")
m.L("M-041", "not_quantified", "damper count not drawn (15 drops drawn, branch count unknown)", "OT-23311622-6000 (verified, opposed blade 12\" x 12\", Ea.)")
m.L("M-042", "not_quantified", "fire / fire-smoke damper count not drawn", "OT-23331316-3240 (verified, fire damper curtain type 16\" x 14\")")
m.L("M-043", "not_quantified", "flexible duct LF not drawn", "OT-23334610-1940 / -1980 / -2040 (verified, flexible insulated duct 6\" / 8\" / 12\", L.F.)")
m.C("M-044", "Recessed access door for drywall, metal, 12\" x 24\" (Ea.)", "OT-08311310-4150", "1", "substitute",
    "drawn: Williams Bros WB DW 405 drywall access door (size per RCP notes, 12\" x 12\" minimum per M-1 C.7); row is a 12\" x 24\" recessed drywall door")
m.L("M-045", "not_in_book", "testing, adjusting and balancing rows of 23 05 93 are subcontractor-quote lines that carry no cost", "OT-23059310-3600 (verified, no cost printed)")
m.L("M-046", "not_in_book", "O&M manuals and owner instruction have no cost row")
m.L("M-047", "not_quantified", "design-build survey and repair of (E) MUA-1 / EF-1: scope undefined (ACCO assessment does not cover HVAC)")
m.L("M-048", "book_row_not_verified", "the kitchen exhaust hood removal row is flagged; duct LF to remove not drawn", "OT-11050510-4750 (flagged, hood removal); OT-23050510-1200 (verified, ductwork removal 10\" x 12\", L.F.)")
m.C("M-049", "Return / exhaust register, ceiling or wall, fixed 45 deg face blades, 6\" x 10\" (Ea.)", "OT-23371360-5060", "1", "substitute",
    "drawn: restroom exhaust diffuser switched with the lights, size not stated; row is a 6\" x 10\" fixed-blade return register; duct to EF-3 not drawn")
m.L("M-050", "spec_not_issued", "untagged air-device symbols on the attic RCP (A-3.22): type and size not stated")
m.L("M-051", "not_in_book", "vibration isolation hangers are not in the book (no row in division 23)")
m.L("M-052", "none_required", "no new roof curbs drawn (quantity 0)")
m.L("M-053", "none_required", "no field refrigerant piping (quantity 0; WSHP factory charged)")
m.L("M-054", "quote", "Accurex / CaptiveAire CASlink hood control package; wiring by EC not quantifiable (no power plan)")

# ---- Plumbing
m.L("P-001", "existing", "existing water heater to remain (model conflict P-4 vs K2.0 / P-6 is an RFI)")
m.C("P-002", "T&P relief valve, pressure & temperature, self-closing, ASME, threaded, 3/4\" (Ea.)", "OT-22052320-5640", "1", "substitute",
    "P-5 detail: T&P relief with 3/4\" copper discharge (valve size taken from the discharge size); row is a generic ASME T&P relief 3/4\"; the detail is titled for the existing heater and which trim is new is not stated", match="partial")
m.U("P-002", "Thermal expansion tank Watts PLT-12", "not_in_book", "no expansion tank row in the book (22 11 19 / 22 33 carry none)")
m.U("P-002", "Vacuum relief valve", "not_in_book", "vacuum breaker rows of 22 11 19.50 are headers / flagged without a verified line", "OT-22111950 (headers only)")
m.U("P-002", "Check valve 3/4\"", "book_row_not_verified", "the 3/4\" swing check valve line is flagged", "OT-22052320-1860 (flagged, check swing 3/4\"); OT-22052320-1870 (verified, size unreadable)")
m.U("P-002", "Backflow preventer on the CW supply", "book_row_not_verified", "size not stated on P-5; the 3/4\" and 1\" RP backflow lines are flagged (2\" verified)", "OT-22111938-4120 / -4140 (flagged); OT-22111938-4180 (verified, 2\")")
m.U("P-002", "Seismic straps (2) and sheet-metal enclosure with access door", "not_quantified", "strap and enclosure sizes not dimensioned; no verified row")
m.C("P-003", "Bronze body hot water circulator (add to water heater) (Ea.)", "OT-22343613-6960", "1", "substitute",
    "drawn: Grundfos 1/12 HP recirculation pump 115 V in a weatherproof enclosure at the WH; row is the book's 'bronze body hot water circulator, add' under commercial gas water heaters (HP and enclosure not stated)")
m.C("P-004", "Water closet, tank type, vitreous china, floor mounted, two piece, close coupled, 1.28 gpf, ADA, incl. seat and supply (Ea.)", WC, "1", "exact",
    "scheduled: Kohler K-3609-T floor-mounted tank type 1.28 gpf elongated with open-front seat (accessible restrooms); row = floor-mounted two-piece 1.28 gpf ADA tank type incl. seat and supply stop")
m.C("P-004", "Water closet rough-in, supply, waste and vent (Ea.)", WC_RI, "1", "exact", "rough-in for one floor-mounted water closet as drawn (2\" CW, 3\" drain, 2\" vent)")
m.C("P-005", "Lavatory, wall hung, vitreous china, 18\" x 15\", single bowl with backsplash, with trim (Ea.)", LAV, "1", "substitute",
    "scheduled: Kohler K-2035-8 Pinoir wall-hung vitreous china 20\" x 18\" with Sloan EBF-415 sensor faucet and temperature-balancing valve; row is an 18\" x 15\" wall-hung lavatory with standard trim (sensor faucet and TMV not in the row)")
m.C("P-005", "Lavatory rough-in, supply, waste and vent, wall hung (Ea.)", LAV_RI, "1", "exact", "rough-in for one wall-hung lavatory as drawn (1/2\" H&CW, 2\" drain, 1-1/2\" vent)")
# KEC-furnished fixtures: fixture = quote, rough-in from the book
m.U("P-006", "KS-1 three-compartment sink with faucets (KEC)", "quote", "foodservice fixture by model (John Boos 2PB1824-2D24 / GSW SE18183D20, model conflict P-4 vs K2.0); quoted scope", "OT-11481310-6750 (verified, pot sink 3 compartment, L.F.)")
m.C("P-006", "Sink rough-in, supply, waste and vent (Ea.)", SINK_RI, "1", "substitute",
    "row is the book's kitchen-sink rough-in (supply, waste and vent); drawn: 3/4\" H&CW, 3\" direct waste to the grease trap, 2\" vent - a larger commercial rough-in", match="partial")
m.U("P-007", "KS-2 two-compartment prep sink (existing, relocated)", "existing", "existing fixture relocated by KEC; no bid price")
m.C("P-007", "Sink rough-in, supply, waste and vent (Ea.)", SINK_RI, "1", "substitute",
    "row is the book's kitchen-sink rough-in; drawn: 1/2\" H&CW and 2\" indirect waste to (E) FS-1 (indirect waste, no direct vent)", match="partial")
m.U("P-008", "HS-1 wall-hung hand sinks (3) (KEC)", "quote", "foodservice fixture by model (GSW HS-1615S); quoted scope")
m.C("P-008", "Hand sink rough-in: lavatory rough-in, supply, waste and vent, wall hung (Ea.)", LAV_RI, "1", "substitute",
    "drawn: 1/2\" H&CW, 2\" drain, 1-1/2\" vent per wall-hung hand sink; the wall-hung lavatory rough-in row is applied (same connections, a lavatory row)")
m.U("P-009", "MS-1 floor mop sink with service faucet (KEC)", "quote", "foodservice fixture by model (Advance Tabco 9-OP-20, faucet conflict P-4 vs K2.0); quoted scope", "OT-22423910-3000 (verified, service sink faucet)")
m.U("P-009", "Mop sink rough-in", "book_row_not_verified", "the service-sink rough-in rows are flagged", "OT-22421640-6790 / -8980 (flagged, rough-in floor / wall service sinks)")
m.U("P-010", "DM-1 dishmachine (KEC)", "quote", "foodservice equipment by model (CMA EST / CMA-180C conflict); quoted scope", "OT-11481310-2720 (verified, dishwasher rack type 10-12 racks/hr, unit blank)")
m.U("P-010", "Dishmachine connections (3/4\" HW, 2\" indirect waste, 208 V)", "not_in_book", "no dishmachine rough-in row; the water and waste connections are counted on P-064 / P-066")
m.U("P-011", "PW-1 soiled dish table with pre-wash basin (KEC)", "quote", "custom stainless fabrication (K2.0 items 99, 100); quoted scope")
m.C("P-011", "Sink rough-in, supply, waste and vent (Ea.)", SINK_RI, "1", "substitute", "row is the book's kitchen-sink rough-in; drawn: 1/2\" H&CW, 3\" drain, 2\" vent", match="partial")
m.U("P-012", "BS-1 bar dump sink (KEC)", "quote", "foodservice fixture by model (Perlick TSF18DS; qty conflict with K2.0 item 63); quoted scope")
m.C("P-012", "Sink rough-in, supply, waste and vent (Ea.)", SINK_RI, "1", "substitute", "row is the book's kitchen-sink rough-in; drawn: 1/2\" H&CW, 2\" indirect waste, island vent per P-6 detail", match="partial")
m.U("P-013", "BS-2 bar hand sinks (2) (KEC)", "quote", "foodservice fixture by model (Perlick TSF12HS; qty conflict with K2.0 item 71); quoted scope")
m.C("P-013", "Hand sink rough-in: lavatory rough-in, supply, waste and vent, wall hung (Ea.)", LAV_RI, "1", "substitute",
    "drawn: 1/2\" H&CW, 2\" drain, 1-1/2\" vent per bar hand sink; the wall-hung lavatory rough-in row is applied")
m.U("P-014", "BS-3 mezzanine prep-bar 3-compartment sink (KEC)", "quote", "foodservice fixture by model (GSW SE10143DB5, item B1 not on K2.0); quoted scope")
m.C("P-014", "Sink rough-in, supply, waste and vent (Ea.)", SINK_RI, "1", "substitute", "row is the book's kitchen-sink rough-in; drawn: 1/2\" H&CW, 2\" direct drain, 1-1/2\" vent", match="partial")
m.U("P-015", "BS-4 mezzanine prep-bar hand sink (KEC)", "quote", "foodservice fixture by model (Krowne KR24-1C, item B3 not on K2.0); quoted scope")
m.C("P-015", "Hand sink rough-in: lavatory rough-in, supply, waste and vent, wall hung (Ea.)", LAV_RI, "1", "substitute", "drawn: hand sink with temperature-balancing valve; the wall-hung lavatory rough-in row is applied")
m.U("P-016", "BS-5 mezzanine dump sink (KEC)", "quote", "foodservice fixture by model (Krowne KR19-12DS, item B5 not on K2.0); quoted scope")
m.C("P-016", "Sink rough-in, supply, waste and vent (Ea.)", SINK_RI, "1", "substitute", "row is the book's kitchen-sink rough-in (supply, waste and vent); drawn: 2\" indirect waste only, no water", match="partial")
m.L("P-017", "book_row_not_verified", "the medium-duty cast iron floor drain line (7\" top, 2\" and 3\" pipe size) is flagged; trap primers are on P-022", "OT-22131913-2040 (flagged, floor drain medium duty CI 7\" top)")
m.L("P-018", "not_in_book", "no floor sink row in the book (22 13 19 carries floor drains only)", "OT-22131913-2040 (flagged, floor drain)")
m.L("P-019", "book_row_not_verified", "grease interceptor rows by GPM (p514 lines 0150 / 0200 / 1060 / 1120) are flagged under an unreadable section header and carry no cost code; GT-1 is specified by model (Thermaco Big Dipper W-350-IS, 35 GPM)",
    "p514 grease interceptor lines 0150 / 0200 / 1060 / 1120 (flagged, no cost code)")
m.L("P-020", "book_row_not_verified", "the 3/4\" reduced-pressure backflow preventer line is flagged (only the 2\" and 6\" lines are verified)", "OT-22111938-4120 (flagged, RP 3/4\"); OT-22111938-4180 (verified, 2\")")
m.L("P-021", "not_in_book", "water pressure reducing valve rows of 22 05 23.20 stop at 1-1/2\" (1/2\", 1\", 1-1/2\" verified; 3/4\" and 1-1/4\" flagged); no 2-1/2\" line in the table", "OT-22052320-6980 (verified, PRV 1-1/2\")")
m.L("P-022", "not_in_book", "no trap primer row in the book")
for k, size in (("P-023", "4\""), ("P-024", "4\""), ("P-025", "3\""), ("P-026", "2\""), ("P-027", "2\""), ("P-028", "4\""), ("P-029", "3\"")):
    m.L(k, "book_row_not_verified", f"{size} no-hub cast iron: " + NOHUB_REASON, NOHUB_CAND)
m.L("P-030", "not_quantified", "riser heights not dimensioned; " + NOHUB_REASON, NOHUB_CAND)
m.L("P-031", "not_quantified", "vent piping not routed on P-3 / P-4; LF not quantifiable", NOHUB_CAND)
m.L("P-032", "book_row_not_verified", "4\" wall cleanout: the 3\" and 4\" cleanout lines (p502) are flagged without a cost code; the only verified cleanout row is a 2\" round top recessed for terrazzo",
    "p502 CLEANOUTS 3\" / 4\" pipe size (flagged, no cost code); OT-22054810-1000 (verified, 2\" round top recessed for terrazzo)")
m.L("P-033", "not_in_book", "points of connection to the (E) sanitary have no row (tie-in labor only)")
m.L("P-034", "not_quantified", "LF of (E) lines to remove not drawn", "OT-22050510-2100 (verified, piping removal 4\"-6\", L.F.)")
m.L("P-035", "not_in_book", "no floor drain / floor sink infill row; opening sizes not stated (slab infill per 7/A-9.10 is on D-16)")
m.L("P-036", "not_quantified", "trench width and depth not dimensioned; split of trench vs hung pipe over the basement not derivable (ACCO); slab removal and patch areas not quantifiable",
    "OT-31231614-2250 (verified, 6\" wide trench and backfill 48\" deep, L.F.); OT-02411330-4310 (verified, slab on grade removal mesh reinforced, C.Y.)")
m.C("P-037", "Copper tubing type L, 2-1/2\" diameter, with couplings and clevis hangers 10' OC (L.F.)", CU["2-1/2"], "1", "exact", CU_REASON)
m.C("P-038", "Copper tubing type L, 2\" diameter (L.F.)", CU["2"], "1", "exact", CU_REASON)
m.C("P-039", "Copper tubing type L, 1-1/2\" diameter (L.F.)", CU["1-1/2"], "1", "exact", CU_REASON)
m.C("P-040", "Copper tubing type L, 1-1/2\" diameter (L.F.) - insulation on P-057", CU["1-1/2"], "1", "exact", CU_REASON)
m.C("P-041", "Copper tubing type L, 1-1/4\" diameter (L.F.) - insulation on P-057", CU["1-1/4"], "1", "exact", CU_REASON)
m.C("P-042", "Copper tubing type L, 1\" diameter (L.F.) - insulation on P-057", CU["1"], "1", "exact", CU_REASON)
m.C("P-043", "Copper tubing type L, 1\" diameter (L.F.)", CU["1"], "1", "exact", CU_REASON)
m.C("P-044", "Copper tubing type L, 3/4\" diameter (L.F.) - insulation on P-057", CU["3/4"], "1", "exact", CU_REASON)
m.C("P-045", "Copper tubing type L, 3/4\" diameter (L.F.)", CU["3/4"], "1", "exact", CU_REASON)
m.C("P-046", "Copper tubing type L, 1/2\" diameter (L.F.) - insulation on P-057", CU["1/2"], "1", "exact", CU_REASON)
m.C("P-047", "Copper tubing type L, 1/2\" diameter (L.F.)", CU["1/2"], "1", "exact", CU_REASON)
m.C("P-048", "Copper tubing type L, 1/2\" diameter (L.F.)", CU["1/2"], "1", "exact", CU_REASON + "; the Everpure filters are KEC items (P-058)")
m.C("P-049", "Copper tubing type L, 1/2\" diameter (L.F.) - insulation on P-057", CU["1/2"], "1", "substitute",
    CU_REASON + "; the circuit setters and access panels called out on the loop are not in the row", match="partial")
m.L("P-050", "not_quantified", "riser heights (1st level to mezzanine to 2nd-floor roof) not dimensioned", f"{CU['1-1/2']} / {CU['1/2']} (verified, type L 1-1/2\" / 1/2\", L.F.)")
m.L("P-051", "spec_not_issued", "branch and drop sizes of the re-piped (E) restroom headers are not printed on P-2; a copper row cannot be chosen without the size", f"{CU['1/2']} .. {CU['2']} (verified, type L by size)")
m.C("P-052", "Copper tubing type L, 1\" diameter (L.F.) - insulation on P-057", CU["1"], "1", "exact", CU_REASON)
m.C("P-053", "Copper tubing type L, 1\" diameter (L.F.)", CU["1"], "1", "exact", CU_REASON)
m.C("P-054", "Copper tubing type L, 3/4\" diameter (L.F.)", CU["3/4"], "1", "exact", CU_REASON)
m.L("P-055", "spec_not_issued", "HW size beyond the 1\" label is not re-labeled on P-4; a copper row cannot be chosen without the size", f"{CU['1/2']} .. {CU['1']} (verified, type L by size)")
m.C("P-056", "Copper tubing type L, 1/2\" diameter (L.F.) - insulation on P-057", CU["1/2"], "1", "substitute",
    CU_REASON + "; the circuit setter and access panel are not in the row", match="partial")
# P-057 insulation split by pipe size per the qty_source arithmetic of the takeoff line (327.2 LF)
m.C("P-057", "Pipe insulation, fiberglass with ASJ, 1\" wall, 1/2\" iron pipe size (L.F.) - the 1/2\" HW/HWR runs P-046 + P-049 + P-056 = 150.2 LF",
    "OT-22071910-6840", "150.2/327.2 (1/2\" runs 24.5 + 76.9 + 48.8 = 150.2 LF of the 327.2 LF summed in the takeoff qty_source)", "exact",
    "P-1 spec: 1\" fiberglass on all HW piping; row = fiberglass with all-service jacket, 1\" wall, 1/2\" pipe size; share of the line = the 1/2\" runs listed in the takeoff qty_source")
m.U("P-057", "Pipe insulation 1\" wall on 1\" pipe (P-042 54.7 + P-052 22.4 = 77.1 LF)", "book_row_not_verified", "the 1\" iron pipe size line is flagged", "OT-22071910-6870 (flagged, 1\" wall 1\" IPS)")
m.U("P-057", "Pipe insulation 1\" wall on 3/4\" pipe (P-044 32.0 LF)", "not_in_book", "no 3/4\" iron pipe size line in the table on hand (22 07 19.10 between lines 6840 and 6870 not captured)")
m.U("P-057", "Pipe insulation 1\" wall on 1-1/4\" pipe (P-041 4.0 LF)", "not_in_book", "no 1-1/4\" iron pipe size line in the table on hand")
m.U("P-057", "Pipe insulation 1\" wall on 1-1/2\" pipe (P-040 12.1 + P-050 HW connection 3.5 = 15.6 LF)", "not_in_book", "no 1-1/2\" iron pipe size line in the table on hand")
m.U("P-057", "Pipe insulation 1\" wall on pipe of unlabeled size (P-051 HW header 20.8 + P-055 27.5 = 48.3 LF)", "spec_not_issued", "pipe sizes not printed (see P-051, P-055)")
m.L("P-058", "quote", "water filters are KEC items by model (Everpure EV9329-52 x2, Rational R295-CL); quoted scope")
m.C("P-059", "Steel pipe, schedule 40, black, threaded, with couplings and clevis hangers 10' OC, 2-1/2\" diameter (L.F.)", "OT-22111344-0620", "1", "substitute",
    "P-1 spec: black steel sch 40 with butt-weld fittings for 2-1/2\" and larger; row is threaded with couplings (the welded 2-1/2\" line is not in the table; welded 2\" and 3\" lines are flagged / machine_read); riser to the basement not dimensioned")
m.C("P-060", "Steel pipe, schedule 40, black, threaded, with couplings and clevis hangers 10' OC, 2\" diameter (L.F.)", "OT-22111344-0610", "1", "exact",
    "P-1 spec: black steel sch 40, 150 lb malleable threaded fittings for 2\" and smaller; row = sch 40 black threaded 2\" with hangers; the 2\" electric shut-off valve is the hood-package valve (M-017); manifold sizing conflict P-7 plan vs riser diagram is an RFI")
m.L("P-061", "book_row_not_verified", "the 1-1/2\" black steel threaded line is flagged; the verified 1-1/2\" line of 22 11 13.48 is grooved-joint pipe with ductile iron fittings, a different joining system for gas",
    "OT-22111344-0600 (flagged, sch 40 black threaded 1-1/2\"); OT-22111348-1070 (verified, grooved joint 1-1/2\")")
m.L("P-062", "not_quantified", "drop lengths not dimensioned; quick disconnects and gas cocks have no verified row (P-7 1\" drops vs K2.0 3/4\" connections is an RFI)", "OT-22111348-1050 (verified, grooved 1\" black steel, L.F.)")
m.L("P-063", "not_in_book", "seismic gas shut-off valve is not in the book; ACCO reports an existing approved seismic valve on the 3\" main (RFI)")
m.L("P-064", "not_in_book", "indirect-waste equipment connections (extend I.W. to floor sink) have no row; the floor sinks are on P-018")
m.L("P-065", "none_required", "the 6 direct-waste connections are inside the rough-in components priced on P-006 (3-comp sink), P-008 (hand sinks x3) and P-009 (mop sink) and the interceptor drain on P-019; pricing them again would double count")
m.L("P-066", "not_in_book", "equipment water connections: 11 H&CW pairs are inside the rough-in components of P-006..P-016; the 12 CW-only equipment connections (items 45, 66 x3, 73, 75, 80, 82, 83, 103, 104, 105) have no row")
m.L("P-067", "existing", "existing-condition note (ACCO), no quantity")
m.L("P-068", "not_quantified", "backwater valve repair not in the P-sheets; scope and whether it is in the bid are RFIs")
m.L("P-069", "existing", "existing-condition note (ACCO), no quantity")
m.L("P-070", "book_row_not_verified", "flush-valve / faucet retrofit of the (E) first-floor restrooms is not called out on P-2 / P-3 (RFI); the waterless urinal rows are flagged / machine_read and there is no flush-valve retrofit row",
    "OT-22421316-8020 / -8030 (flagged, waterless urinal); OT-22421316-8220 (machine_read, ADA waterless urinal vitreous china)")

# ---- Electrical power
for k in ("E-001", "E-002", "E-003", "E-004", "E-005", "E-006"):
    m.L(k, "not_quantified", "existing panel to remain and be rewired: branch-circuit conduit / wire lengths and device counts are not in the documents (no power plan); circuits are counted only",
        "OT-26053313-5000 (verified, EMT 1/2\", L.F.); OT-26051990-0920 (verified, THWN #14 copper, unit blank)")
m.L("E-007", "not_in_book", "no panelboard removal row in 26 05 05.10 (conduit, wire, fixtures and transformers only); re-feed of the Dillons loads is an RFI", "OT-26050510-1340 (verified, transformer removal, a different item)")
for k in ("E-008", "E-009", "E-010"):
    m.L(k, "existing", "existing equipment, no new work indicated")
m.L("E-011", "spec_not_issued", "rating, voltage, feeder and source of the 3 new lighting/sound panels not given (RFI); the verified NQ panelboard rows need the amperage and circuit count",
    "OT-26241630-2050 (verified, NQ 4 wire 120/208 V 100 A main breaker 24 circuits, Ea.); OT-26241630-0850 (verified, 225 A main lugs 32 circuits, Ea.)")
m.L("E-012", "not_quantified", "feeder sizes and lengths not given")
m.L("E-013", "not_quantified", "rewiring of 6 existing panels: no power plan, circuit numbers, homeruns or device counts", "OT-26053313-5000 (verified, EMT 1/2\", L.F.)")
m.C("E-014", "Receptacle, duplex, 120 V, grounded, 15 A (Ea.) - device only, the 33 outlets at 120 V 1-ph", RECEPT, "33/36 (33 of the 36 K2.0 convenience outlets are 120 V 1-ph per the takeoff description)", "substitute",
    "K2.0 C.O. outlets at 120 V (amperage up to 20 A, NEMA 5-20P at item 54, drop cords at 17/18, dedicated isolated-ground circuits for POS); row is a 15 A duplex receptacle device only - box, conduit, wire and circuit are not quantifiable (no power plan)", match="partial")
m.U("E-014", "Receptacles at 208 V 1-ph (conveyor oven decks 26 A x2, cabinet 11 A) - 3 outlets", "not_in_book", "no 208 V / 30 A receptacle row verified except a dryer receptacle (a different device); circuits not quantifiable",
    "OT-26272620-2490 (verified, dryer receptacle 30 A)")
m.C("E-015", "Equipment connection, flexible conduit and fittings, 115 V 1 ph, up to 1 HP (Ea.) - the 10 items at 120 V", MOTOR120, "10/20 (10 of the 20 direct connections are 120 V per the takeoff description: items 7, 8, 11, 55, 56, 73, 76, 83, 97, 105)", "substitute",
    "row is a motor connection (flexible conduit and fittings) for a 115 V 1-phase motor up to 1 HP; the items are hard-wired equipment (lights, coils, fire system, hood lights, ice machines, tea maker, hood), not motors; branch circuits not quantifiable", match="partial")
m.C("E-015", "Equipment connection, flexible conduit and fittings, 230 V 3 ph, 3 HP motor (Ea.) - the 10 items at 208 V", MOTOR230, "10/20 (7 items at 208 V 1-ph: 6, 9, 12, 35 x3, 82; 3 items at 208 V 3-ph: 46, 57, 98)", "substitute",
    "row is a motor connection for a 230 V 3-phase 3 HP motor; the items are 208 V equipment (7 single-phase, 3 three-phase: combi 10.8 kW, exhaust fan system, dishmachine 20 A); branch circuits not quantifiable", match="partial")
m.L("E-016", "not_quantified", "hood electrical package wiring: shunt-trip breaker, control panel feed and interlocks have no lengths or device counts (no power plan)")
m.C("E-017", "Safety switch, general duty, 240 V, 3 pole, NEMA 1, fusible, 30 A (Ea.) - disconnects for the 7 WSHP with MOCP 25 A", DISC30, "7/8 (7 of the 8 units have MOCP 25 A per the M-1 schedule)", "substitute",
    "M-1 A.9: disconnect remote from each unit by EC, type (fused / non-fused, heavy duty) not stated; row is a general-duty fusible 30 A 3-pole switch; the branch circuits and feeders have no source panel (RFI) and are not quantifiable", match="partial")
m.C("E-017", "Safety switch, general duty, 240 V, 3 pole, NEMA 1, fusible, 60 A (Ea.) - disconnect for WSHP-8 (MOCP 60 A)", DISC60, "1/8 (WSHP-8 only, MOCP 60 A per the M-1 schedule)", "substitute",
    "disconnect type not stated; row is a general-duty fusible 60 A 3-pole switch; branch circuit not quantifiable", match="partial")
m.U("E-017", "Branch circuits to the 8 WSHP (MCA 21.2 / 31.0 / 44.3 A)", "not_quantified", "no circuits for the WSHP on any panel schedule and no power plan (RFI); lengths unknown")
m.C("E-018", "Motor connection, flexible conduit and fittings, 115 V 1 phase, up to 1 HP motor (Ea.) - EF-2 (3/4 HP) and EF-3 (1/3 HP)", MOTOR120, "1", "exact",
    "M-1: EF-2 3/4 HP and EF-3 1/3 HP at 115 V 1-ph; row = flexible conduit and fittings connection for a 115 V 1-phase motor up to 1 HP")
m.C("E-018", "Safety switch, general duty, 240 V, 3 pole, NEMA 1, fusible, 30 A (Ea.) - fan disconnects", DISC30, "1", "substitute",
    "disconnect type and poles not stated (single-phase fans would take a 2-pole switch); row is a 3-pole fusible 30 A switch", match="partial")
m.U("E-018", "Branch circuits and interlock / control wiring to EF-2 and EF-3", "not_quantified", "not on the panel schedules; lengths unknown")
m.L("E-019", "not_quantified", "power to the grease recovery device, HWR pump and water heater: circuit lengths and source not shown", f"{MOTOR120} (verified, 115 V equipment connection)")
m.L("E-020", "not_quantified", "ADA lift circuit length and lift electrical data not in this scope")
m.L("E-021", "not_quantified", "dumbwaiter circuit and panel not given (RFI)")
m.C("E-022", "Receptacle, duplex, 120 V, grounded, 15 A (Ea.) - device only", RECEPT, "1", "substitute",
    "elevations call 'OUTLET, BLACK' x6 and 'POWER OUTLET @ 18\" AFF' x2; colour and grade not fixed; row is a 15 A duplex device only - box, wiring and circuit not priced (no power plan)", match="partial")
m.L("E-023", "not_quantified", "general receptacles, GFCI, switches and boxes: no power plan")
m.L("E-024", "not_quantified", "hand dryer circuits: lengths and source not shown; the dryers are on the architectural takeoff")
m.L("E-025", "not_quantified", "electrical demolition counts and conduit LF not drawn; panel Dillons has no removal row",
    "OT-26050510-0200 (verified, EMT removal 1/2\"-1\", L.F.); OT-26050510-2100 (verified, recessed 2x2 fixture removal, Ea.)")

# ---- Lighting (fixtures priced only where the book has the same kind of fixture; otherwise quote)
m.C("E-101", "Interior LED downlight, recess mounted, 7.5\" diameter, 20 watts, incl. lamp and mounting hardware (Ea.)", "OT-26511355-0180", "1", "substitute",
    "scheduled: USAI Zepto 1\" aperture trimless recessed LED downlight 7 W 2700K with remote driver (2+ fixtures per driver, trim kit per a schedule not drawn); row is a 7.5\" diameter 20 W recessed LED downlight; remote drivers not in the row")
m.C("E-102", "Exterior LED fixture, wall mounted, indoor/outdoor, 66 watt (Ea.)", "OT-26562355-0120", "1", "substitute",
    "scheduled: Gotham EVO 4\" wall-mounted LED accent cylinder, tilt/rotate, 14 W 2700K warm dim, wet listed; row is a 66 W wall-mounted indoor/outdoor LED fixture (the 12 W and 32 W lines carry no unit); accent optics and warm-dim driver not in the row")
m.L("E-103", "quote", "decorative LED pendant (Panzeri Zero Round, 24 V DC with remote driver); no pendant of this kind in the book")
m.L("E-104", "quote", "decorative tassel pendant with filament lamp (Atolla); no fixture of this kind in the book")
m.L("E-105", "quote", "decorative LED wall sconce (WAC Twist-N-Lite, color-select, TRIAC/ELV); no fixture of this kind in the book")
m.C("E-106", "Interior LED troffer, recess mounted, 2' x 4', 3,200 lumens (Ea.)", "OT-26511355-1000", "1", "substitute",
    "scheduled: Oracle 2' x 2' flat LED panel 2,000 lm 19 W 3000K with recessed drywall flange kit and polycarbonate lens; row is a 2' x 4' 3,200 lm recessed LED troffer (grid mount, no flange kit); the 2' x 2' troffer line is not verified")
for k in ("E-107", "E-108", "E-109", "E-110", "E-111", "E-113", "E-114", "E-115", "E-116", "E-118", "E-119", "E-120", "E-121"):
    m.L(k, "quote", "Omni Light True Series COB LED ribbon in channel with 24 V power supplies; LED tape / strip lighting is not in the book")
for k in ("E-112", "E-117"):
    m.L(k, "quote", "CORE Lighting 24 V LED base strip in recessed trimless channel; LED tape / base strip is not in the book (G16-G18 lengths also not stated)")
m.L("E-122", "not_quantified", "24 V driver and remote driver counts not scheduled")
m.C("E-123", "Exit sign, LED with battery unit, single face, ceiling or wall mount (Ea.)", "OT-26521316-0240", "1", "substitute",
    "scheduled: Flamsted of Vermont Art Deco decorative exit sign, single face, 90-minute battery; row is a standard LED exit sign with battery unit, single face")
m.C("E-124", "Exit sign, LED with battery unit, single face, ceiling or wall mount (Ea.)", "OT-26521316-0240", "1", "substitute",
    "scheduled: Isolite ELT-EM red 8\" letters single face top mount black with 90-minute battery; row is a standard LED exit sign with battery unit, single face (finish and mounting not fixed in the row)")
m.C("E-125", "Emergency light unit, battery operated, twin sealed beam 25 W 6 V, lead battery (Ea.)", "OT-26521310-0500", "1", "substitute",
    "scheduled: Flamsted of Vermont Art Deco decorative emergency light 200 lm 4.8 W 90-minute battery, wall or pendant; row is a standard twin-head sealed beam emergency unit with lead battery")
m.C("E-126", "Emergency light unit, battery operated, twin sealed beam 25 W 6 V, lead battery (Ea.)", "OT-26521310-0500", "1", "substitute",
    "scheduled: Isolite MIGN2 recessed LED emergency light 814 lm with pre-ship back box; row is a surface twin-head sealed beam emergency unit (recessed housing / back box not in the row)")
m.C("E-127", "Emergency light unit, battery operated, twin sealed beam 25 W 6 V, nickel cadmium battery (Ea.)", "OT-26521310-0700", "1", "substitute",
    "scheduled: Lithonia ELM2 LED thermoplastic two-head emergency light with 90-minute ni-cad battery 120/277 V; row is a twin sealed-beam (not LED) unit with nickel cadmium battery")
m.L("E-128", "not_quantified", "Lutron Athena dimming system: dimming bank and dimming switch counts not drawn (symbols in the legend only); 0-10 V control wire lengths unknown", "OT-26272620-1650 (verified, dimmer switch 600 W 1 pole)")
m.C("E-129", "Toggle switch, quiet type, single pole (Ea.) - device only", SWITCH, "1", "exact",
    "drawn: single-pole switch 'S' at the green room and a switch controlling light and exhaust fan at each mezzanine restroom; row = single-pole quiet toggle switch; box, wiring and plate not priced (no power plan)")
m.L("E-130", "existing", "existing fixtures to remain in the (E) first-floor restrooms")
m.L("E-131", "not_quantified", "trim-kit schedule named on A-3.70 is not drawn (RFI)")
m.L("E-132", "not_quantified", "lighting branch circuits and panel capacity: no lighting plan / circuiting issued")

# ---- Low voltage
m.L("LV-001", "not_quantified", "sound / AV system not in the documents (power only on E-011)")
m.C("LV-002", "Receptacle, duplex, 120 V, grounded, 15 A (Ea.) - device only, one per POS terminal", RECEPT, "1", "substitute",
    "K2.0 item 68: dedicated isolated-ground circuit and J-box with communication cable per terminal; isolated-ground receptacles are not in the book; row is a standard 15 A duplex device only - circuit, J-box and cabling (owner vendor) not priced", match="partial")
m.L("LV-003", "not_quantified", "TV outlets / video distribution not in the documents", "OT-27413310-0200 (verified, master TV antenna system 12 outlets, per Outlet)")
m.L("LV-004", "not_quantified", "data / telecom cabling and network rack not in the documents")
m.L("LV-005", "not_quantified", "fire-alarm interface for the hood system: no fire-alarm device plan for the tenant space; alarm-contractor scope under separate permit",
    "OT-28461127-5400 (verified, duct smoke detector)")
m.L("LV-006", "none_required", "security / CCTV / access control: quantity 0 (none drawn)")
m.L("LV-007", "quote", "CaptiveAire CASlink remote monitoring, part of the hood control package; ethernet drop not drawn")

m.write("matches_mep.csv")

# ===============================================================================================================
# EQUIPMENT (K2.0 schedule): foodservice equipment by model is quoted scope; owner / vendor items carry no bid price;
# candidate_row names a verified book row of the same kind where one exists (for a later install-labor or budget check)
# ===============================================================================================================
e = Map()
EQ_CAND = {
    "FE-1": "OT-11413320-8740 (verified, galvanized flat 4-tier shelving 20\" x 6', Ea.)",
    "FE-4": "OT-11421010-8580 (verified, slicer with table)",
    "FE-5": "OT-11411320-4300 (verified, reach-in freezer 44 CF - refrigerator rows flagged)",
    "FE-7": "OT-11411320-8440 (verified, walk-in aluminum door & floor only no refrigeration 12' x 14' x 7'-6\")",
    "FE-10": "OT-11413320-8740 (verified, galvanized flat 4-tier shelving 20\" x 6')",
    "FE-11": "OT-11411320-4640 (verified, pre-fab freezer 8' x 16' with refrigeration)",
    "FE-13": "OT-11413320-8740 (verified, galvanized flat 4-tier shelving 20\" x 6')",
    "FE-22": "p514 grease interceptor lines (flagged, no cost code)",
    "FE-27": "OT-11441310-0300 (verified, bake oven gas two sections - a different oven type)",
    "FE-28": "OT-11461610-3300 (verified, food warmer counter 1.2 kW - a different product)",
    "FE-36": "OT-11413320-8735 (verified, galvanized flat 4-tier shelving 20\" x 4')",
    "FE-40": "OT-11461610-3300 (verified, food warmer counter 1.2 kW)",
    "FE-47": "OT-11441310-7150 (verified, range 6 burners 2 std ovens 24\" griddle 60\" wide)",
    "FE-49": "OT-11441310-1300 (verified, broiler without oven standard)",
    "FE-51": "OT-11441310-5300 (verified, griddle SS 24\" plate electric 208 V 3 ph 3' long - electric, drawn gas)",
    "FE-52": "OT-11441310-4750 (verified, fryer with twin baskets modular model)",
    "FE-53": "OT-11411320-4300 (verified, reach-in freezer 44 CF)",
    "FE-55": "OT-11050510-4255 (verified, removal of hood fire protection system - demolition only)",
    "FE-56.1": "OT-11050510-4750 (flagged, hood removal); no new kitchen hood row",
    "FE-56.2": "OT-11050510-4750 (flagged, hood removal); no new kitchen hood row",
    "FE-73": "OT-11468310-6050 (verified, ice cube maker 500 lb/day)",
    "FE-74": "OT-11468310-6160 (verified, ice storage bin 500 lb)",
    "FE-77": "OT-11468310-6160 (verified, ice storage bin 500 lb)",
    "FE-79": "OT-11411320-4300 (verified, reach-in freezer 44 CF)",
    "FE-82": "OT-11421010-1840 (verified, coffee brewer 5 burners)",
    "FE-83": "OT-11441310-6200 (verified, iced tea brewer)",
    "FE-88": "OT-11481310-6750 (verified, pot sink 3 compartment, L.F.)",
    "FE-97": "OT-11481310-2950 (verified, dishwasher hood canopy type, L.F.)",
    "FE-98": "OT-11481310-2720 (verified, dishwasher rack type 10-12 racks/hr, unit blank)",
    "FE-105": "OT-11468310-6050 (verified, ice cube maker 500 lb/day)",
    "FE-106": "OT-11468310-6160 (verified, ice storage bin 500 lb)",
    "FE-2": "OT-10511310-0120 (verified, steel locker 1-tier 18\" x 15\" x 72\", unit blank)",
}
with open(os.path.join(T2, "equipment.csv"), newline="") as f:
    for r in csv.DictReader(f):
        iid, fb, bli = r["item_id"], r["furnished_by"].lower(), r["bid_letter_item"].lower()
        cand = EQ_CAND.get(iid, "")
        if "existing to remain" in bli or fb.startswith("existing"):
            e.L(iid, "existing", "existing to remain (K2.0 remark); no bid price", cand)
        elif fb.startswith("owner") or fb.startswith("soda vendor"):
            e.L(iid, "owner_provided", f"furnished by {r['furnished_by'].split('(')[0].strip()} per the K2.0 remark; setting / connection labor has no verified row; installer {r['installed_by'][:60]}", cand)
        elif "custom st/st" in r["spec_or_model"].lower():
            e.L(iid, "quote", "custom-fabricated stainless steel (no cut sheet, no dimensions on the K-sheets); fabricator quote scope", cand)
        elif r["division"].startswith("23 38") or r["division"].startswith("21 23"):
            e.L(iid, "quote", "CaptiveAire hood / fan / fire-system package by model (K7.0 / K7.1); vendor quote scope", cand)
        elif iid == "FE-68.1":
            e.L(iid, "owner_provided", "J-box and communication cable per POS terminal: cabling by the owner's POS vendor; the EC circuit / J-box is counted on LV-002")
        else:
            e.L(iid, "quote", "foodservice equipment by make/model on K2.0 (another agent is collecting list prices); furnishing party not stated on K2.0", cand)
e.write("matches_equipment.csv")

# ===============================================================================================================
# DEMOLITION / STRUCTURAL / EXIT STAIR / GENERAL CONDITIONS
# ===============================================================================================================
d = Map()
WALKIN = "OT-11050510-4050"
d.C("D-01", "Selective demolition, food storage equipment, walk-in refrigerator/freezer (S.F.)", WALKIN, "151/2 (floor areas 119 + 32 = 151 SF per the takeoff notes, 2 enclosures)", "substitute",
    "row is the book's walk-in refrigerator/freezer removal per S.F.; the row does not state whether S.F. is floor or panel area - the floor areas of the two tagged enclosures (119 and 32 SF) are used; refrigeration disconnect by trades not in the row")
d.C("D-02", "Selective demolition, food storage equipment, walk-in refrigerator/freezer (S.F.)", WALKIN, "181 (12.3 x 14.7 ft = 181 SF per the takeoff qty_source)", "substitute",
    "untagged dashed enclosure (RFI: walk-in or partition); priced with the walk-in removal row on its 181 SF footprint as the takeoff treats it as a walk-in; the row does not state whether S.F. is floor or panel area")
d.L("D-03", "not_quantified", "equipment count not derivable (K-sheets show new equipment only)", "OT-11050510-4100 (verified, small countertop food prep equipment removal); OT-11050510-4052 (verified, SS shelving removal)")
d.L("D-04", "book_row_not_verified", "the kitchen exhaust hood removal row is flagged", "OT-11050510-4750 (flagged)")
d.C("D-05", "Selective demolition, millwork, counter top, straight runs (L.F.)", "OT-06050520-1500", "1", "substitute",
    "drawn: bar die wall, back bar and bar top removal (KN8); the row covers the counter top only, the die wall and back bar casework are not in it", match="partial")
d.L("D-06", "not_quantified", "bar equipment and plumbing utilities to remove not counted", "OT-22050510-2100 (verified, piping removal 4\"-6\", L.F.)")
d.L("D-07", "not_quantified", "enclosure wall SF not dimensioned (about 3 ft square, height not stated) and construction not stated; 'TYP.' count unresolved (RFI)", "OT-09050530-1000 (verified, GWB removal, S.F.)")
d.L("D-08", "spec_not_issued", "ramp construction (concrete vs framed) and height not stated; a removal row cannot be chosen", "OT-02411330-4310 (verified, slab on grade removal, C.Y.); OT-06050510-6160 (verified, plywood subfloor removal, S.F.)")
d.L("D-09", "not_in_book", "no stair demolition row for a curved stair of unstated construction (the only verified stair removal row is wood stairs and stringers per riser; riser count not drawn)", "OT-06050510-6200 (verified, wood stairs and stringers, Riser)")
d.L("D-10", "spec_not_issued", "platform construction and height not stated; a removal row cannot be chosen", "OT-06050510-6160 (verified, plywood subfloor removal, S.F.)")
d.L("D-11", "not_in_book", "no booth / fixed seating removal row (12 05 05 casework rows are flagged)", "OT-12050510-1100 (flagged, casework base cabinets)")
d.L("D-12", "book_row_not_verified", "aluminum window removal rows are flagged (p268, under an unreadable section header); panel heights not dimensioned", "p268 window demolition line 0200 (flagged, no cost code); OT-08050520-1040 (verified, remove and reset window to 3' x 3' - a different task)")
d.L("D-13", "book_row_not_verified", "interior door removal rows are machine_read / flagged; door types not scheduled", "OT-08050510-1020 (machine_read, interior wood door 3'-0\" x 7'-0\"); OT-08050510-2200 (verified, wood frame removal)")
d.L("D-14", "not_quantified", "trench width not dimensioned and (E) slab thickness 'match (E)' not stated: the slab removal volume, the saw-cut depth and the patch area cannot be computed",
    "OT-03811650-0800 (verified, concrete saw cutting per inch of depth, L.F.); OT-02411330-4310 (verified, slab removal, C.Y.); OT-03311335-0100 (verified, 2500 psi ready mix, C.Y.)")
d.L("D-15", "not_quantified", "branch trench LF per a scaled P-3 not taken; width and depth not dimensioned")
d.L("D-16", "not_in_book", "no floor sink / floor drain infill row; opening sizes not stated (slab infill detail 7/A-9.10)")
d.L("D-17", "not_quantified", "(E) waffle slab thickness not stated; the cutout rows are per C.F.", "OT-02411916-1000 (verified, concrete elevated slab bar reinforced under 6 C.F., C.F.)")
d.L("D-18", "not_quantified", "KN18 tag not located; size not stated")
d.L("D-19", "not_quantified", "core-drilled opening size not stated", "OT-03311325-0130 (verified, hand-mix concrete 3000 psi, C.F.)")
d.L("D-20", "book_row_not_verified", "coffer material not stated; the GWB ceiling demolition rows are flagged; the plaster-on-lath rows (verified) apply only if the coffers are plaster", "OT-09050510-0200 (flagged, GWB ceiling); OT-09050510-1000 (verified, plaster on wood lath, S.F.)")
d.L("D-21", "spec_not_issued", "fixture type not stated (symbol count only); the removal rows are by fixture type", "OT-26050510-2100 (verified, recessed 2x2 2-lamp, Ea.); OT-26050510-2200 (verified, surface 1x4, Ea.)")
for k in ("D-22", "D-23", "D-24"):
    d.L(k, "not_quantified", "wall height not stated; the partition removal rows are per S.F. and the GWB-on-studs rows are flagged", "OT-09050530-1000 (verified, GWB nailed or screwed, S.F.); OT-09050530-2300 (flagged, studs finished 2 sides)")
d.L("D-25", "not_quantified", "'TYP.' not resolved to a column count and the enclosure surface is not stated")
d.L("D-26", "not_quantified", "terrazzo patch area not stated")
d.L("D-27", "not_quantified", "J-box and conduit counts / LF not drawn", "OT-26050510-0200 (verified, EMT removal, L.F.)")
d.C("D-28", "Slab on grade removal, mesh reinforced (C.Y.)", "OT-02411330-4310", "3.5/12/27 (A-6.21 demo section: 3-1/2 in deep; C.Y. = S.F. x 3.5/12 ft / 27)", "substitute",
    "drawn: saw-cut (E) slab on grade and demolish partial concrete waffle floor 21.1 SF x 3-1/2 in deep (0.23 CY); row is slab-on-grade removal, mesh reinforced (reinforcing of the (E) slab not stated; the waffle-floor portion and saw cutting are not in the row); recompacted backfill not priced", match="partial")
d.L("D-29", "not_quantified", "haul volume not derivable (thicknesses and heights not on the documents)", "OT-02411919-0800 (verified, 30 CY dumpster weekly rental); OT-02411920-0300 (verified, dump charges rubbish, Ton)")

# ---- Structural
d.C("S-01", "Pan stairs, shop fabricated, steel stringers, metal pan tread for concrete infill, picket rail, 3'-6\" wide (Riser)", PAN_STAIR, "1", "substitute",
    "drawn: 3'-9\" wide stair, C12x20.7 stringers, 12 ga pans with 2\" lightweight fill, round nosing, LED riser strip (A-6.12), handrails per A-6.12; row is 3'-6\" wide with a picket rail; concrete fill priced on S-07, LED strip on the lighting takeoff")
d.L("S-02", "book_row_not_matching", "the C12x20.7 stringers are inside the pan-stair row priced on S-01 ('shop fabricated, steel stringers'); the separate channel line for C12 is not in the table and the nearest verified channel row is field-fabricated C8x11.5, a different member", "OT-05122340-0672 (verified, channel framing field fabricated C8x11.5, L.F.)")
d.C("S-03", "Structural tubing, rectangular, 8\" x 4\" x 3/8\" x 12'-0\" (Ea. = one 12'-0\" piece)", HSS84, "1/12 (piece length 12'-0\" printed on the row)", "substitute",
    "drawn: HSS8x4x1/4 landing beams; row is 8\" x 4\" x 3/8\" wall (wall thickness differs); factor 1/12 per L.F. (16.17 LF = 1.35 pieces); saddle plates per 3/S-3.10 not in the row")
d.L("S-04", "book_row_not_matching", "drawn: 800S162-54 joists @ 16\" with 800T162-54 track and 3/4\" Sure-Board decking; the book's stair landing row is a steel pan landing, a different system; Sure-Board is not in the book", "OT-05511350-1500 (verified, landing steel pan conventional, S.F.); OT-05421340-0330 (verified, 16 ga x 8\" joist material, L.F. - joist LF not stated)")
d.L("S-05", "not_in_book", "no verified HSS 4x4 row in the book (05 12 23.17 carries 5x3, 8x4, 10x6 and 12x8 tubing only)")
d.C("S-06", "Steel plate, shop fabricated, 3/8\" thick, for connections and stiffener plates - material only (S.F.)", PLATE38, "0.5625 (9 x 9 in plate = 81/144 S.F. per plate)", "substitute",
    "drawn: 9\" x 9\" x 3/8\" post base plates; row is 3/8\" shop-fabricated connection plate, material only (welding to the post and setting not in the row)", match="partial")
d.U("S-06", "Embedded threaded rods (4) 1/2\" dia x 4\", drill and epoxy, per plate (8 total)", "book_row_not_matching", ANCHOR_REASON, ANCHOR_CAND)
d.C("S-07", "Placing concrete, stair pan treads, flights in 1st floor level up/down from discharge point - labor only (S.F.)", PAN_PLACE, "1", "substitute",
    "row is the book's placing labor for pan-type stair fill (listed under '4\" deep' landings/flights, 1st floor level); drawn: 2\" lightweight fill, 14 treads = 48.1 SF; concrete material is the next component", match="partial")
d.C("S-07", "Ready-mix concrete, 2500 psi, delivered (C.Y.) - material only", RMX2500, "2/12/27 (A-6.12 detail 3: 2 in fill; C.Y. = S.F. x 2/12 ft / 27)", "substitute",
    "drawn: 2\" lightweight concrete on 12 ga pans, strength not stated; row is normal-weight ready mix at 2,500 psi (the strength A-9.10 names for the other slab fills; lightweight concrete is not in the book); 48.12 SF x 2/12/27 = 0.297 CY", match="partial")
d.L("S-08", "not_in_book", "no verified HSS 4x4 row in the book; base plates 8 x 4 x 1/4 with (2) 1/2\" x 3\" embedded rods per 6/S-3.20 also without a matching anchor row", ANCHOR_CAND)
d.L("S-09", "not_quantified", "lift pit slab thickness / rebar and the '(N) structural beam below' are not detailed (RFI)")
d.C("S-10", "Boxed header/beam, double, 16 ga x 10\" deep, floor framing (L.F.)", "OT-05421330-0310", "1", "exact",
    "drawn: (2) 1000S200-54 box beam = two 10\" deep 54 mil (16 ga) members boxed; row = double 16 ga x 10\" deep boxed beam of 05 42 13.30; column saddle plates and anchors per 4/S-3.10 not in the row (count not legible, S-10 notes)")
d.L("S-11", "book_row_not_matching", "drawn: (2) 1000S200-97 = double 12 ga x 10\" deep box beam; the double 12 ga line is not in the table (the double 14 ga x 10\" line is machine_read) and the only verified 12 ga boxed beam is a triple 12\" deep member, a different product",
    "OT-05421330-0400 (machine_read, double 14 ga x 10\"); OT-05421330-1510 (verified, triple 12 ga x 12\")")
JOIST_F = "1157/1538.12 (takeoff notes: joists @ 16\" = 33 x 12.8 ft + 42 x 17.5 ft = 1,157 LF over the 1,538.12 SF measured)"
d.C("S-12", "Joists, 2\" flange, 16 ga x 8\" deep, materials only (L.F.) - 800S162-54 joists, 1,157 LF", "OT-05421340-0330", JOIST_F, "exact",
    "drawn: 800S162-54 joists @ 16\" o.c. (8\" deep, 54 mil = 16 ga, 1-5/8\" flange); row = 16 ga x 8\" deep 2\"-flange joist, material only; LF from the takeoff notes")
d.C("S-12", "Installation of joists to band joists, beams and headers, labor only, 16 ga x 8\" deep (L.F.) - 1,157 LF", "OT-05421340-1330", JOIST_F, "exact",
    "installation labor for the 16 ga x 8\" joists; LF from the takeoff notes")
d.U("S-12", "3/4\" Cemco Sure-Board 200S-F decking, #8 screws @ 4\"/12\" (1,538 SF)", "not_in_book", "Sure-Board (cementitious-faced steel sheathing) is not in the book")
d.U("S-12", "Band joists / tracks 400T125-54, 1000T162-54, bent-plate hangers and the 6 x 2-1/2 x 1/4 bent plate at the guardrail edge", "not_quantified", "track and plate LF not dimensioned (S-12 notes)", "OT-05421325-0330 (verified, band joist track 16 ga x 8\", L.F.)")
d.C("S-13", "Structural steel member, W10x22, A992, shop fabricated, bolted connections (L.F.)", "OT-05122375-0700", "1", "exact",
    "drawn: W10x22 ASTM A992 Gr 50 (3 pieces, 19.6 LF, 431 lb) framed to the (E) beams with bolted clips per 4/S-3.20; row = W10x22 of 05 12 23.75 (shop fabricated for a 100-ton 1-2 story project, bolted connections - the productivity basis, not the product); the SFRM is the next component")
d.U("S-13", "2-hr SFRM applied directly on the W10x22 (A-6.30)", "not_quantified", "fireproofing is priced per S.F. of steel surface and the beam surface per L.F. is not stated on the documents; the verified 2-hour SFRM row is the exterior-use line", "OT-07811610-1551 (verified, sprayed cementitious fireproofing 2 hour rating exterior use, S.F.)")
d.L("S-14", "book_row_not_matching", ANCHOR_REASON + " (dumbwaiter shaft bottom track anchors @ 24\" o.c., 5/S-3.10)", ANCHOR_CAND)
d.L("S-15", "spec_not_issued", "sloped mezzanine floor: no structural detail on S-2.20 or the exit-stair S-sheets (RFI)")
d.L("S-16", "not_quantified", "header configurations 'see detail' on A-9.10 not read; count not stated", "OT-05421330-0300 (verified, boxed header double 16 ga x 8\", L.F.)")
d.L("S-17", "not_quantified", "shear-wall marks and holdowns not legible at 110 dpi")
d.L("S-18", "not_quantified", "stud wall LF is on the architectural takeoff (interior partitions); stud size conflict 400S162-54 vs 362S162-54 is an RFI")

# ---- Exit stair (1704 N Vine)
d.C("X-01", "Pan stairs, shop fabricated, steel stringers, metal pan tread for concrete infill, picket rail, 3'-6\" wide (Riser)", PAN_STAIR, "1", "substitute",
    "drawn: 5'-0\" wide 1-hr rated steel stair, C12x20.7 stringers, concrete-filled pans; row is 3'-6\" wide with a picket rail (handrails on X-11, fill on X-03)")
d.L("X-02", "book_row_not_matching", "the C12x20.7 stringers are inside the pan-stair row priced on X-01; the separate C12 channel line is not in the table and the nearest verified channel row is field-fabricated C8x11.5", "OT-05122340-0672 (verified, channel framing C8x11.5, L.F.)")
d.C("X-03", "Placing concrete, stair pan treads, flights in 1st floor level up/down from discharge point - labor only (S.F.)", PAN_PLACE, "1", "substitute",
    "row is the book's placing labor for pan-type stair fill; the fill depth is not stated on the exit-stair sheets so the concrete material cannot be quantified (next component)", match="partial")
d.U("X-03", "Concrete fill material for the exit-stair pans", "not_quantified", "fill depth and strength not stated on the exit-stair sheets (RFI 8)", "OT-03311335-0100 (verified, 2500 psi ready mix, C.Y.)")
d.C("X-04", "Structural tubing, rectangular, 8\" x 4\" x 3/8\" x 12'-0\" (Ea. = one 12'-0\" piece)", HSS84, "1/12 (piece length 12'-0\" printed on the row)", "substitute",
    "drawn: HSS8x4x1/4 landing beams 18 LF; row is 3/8\" wall; factor 1/12 per L.F. (1.5 pieces); landing size conflict 5'-0\" vs 6'-0\" calc span is an RFI")
d.L("X-05", "book_row_not_matching", "drawn: 800C162-54 joists with track and 3/4\" Sure-Board decking; the book's stair landing row is a steel pan landing, a different system; joist LF not stated; Sure-Board not in the book", "OT-05511350-1500 (verified, landing steel pan, S.F.)")
d.L("X-06", "not_in_book", "no verified HSS 4x4 row in the book")
d.C("X-07", "Steel plate, shop fabricated, 1/4\" thick, for connections and stiffener plates - material only (S.F.)", PLATE14, "64/144 (8 x 8 in plate = 64/144 S.F. per plate)", "substitute",
    "drawn: 8\" x 8\" x 1/4\" post base plates; row is 1/4\" shop-fabricated plate, material only (welding and setting not in the row)", match="partial")
d.U("X-07", "Embedded threaded rods (2) 1/2\" dia x 4\" per plate (4 total)", "book_row_not_matching", ANCHOR_REASON, ANCHOR_CAND)
d.C("X-08", "Steel plate, shop fabricated, 1/4\" thick - material only (S.F.)", PLATE14, "48/144 (1'-0\" x 4 in plate = 48/144 S.F. per plate)", "substitute",
    "drawn: 1'-0\" x 4\" x 1/4\" stringer base plates; row is 1/4\" shop-fabricated plate, material only", match="partial")
d.U("X-08", "Embedded threaded rods (2) 1/2\" dia x 4\" per plate (4 total)", "book_row_not_matching", ANCHOR_REASON, ANCHOR_CAND)
d.C("X-09", "Steel plate, shop fabricated, 1/4\" thick - material only (S.F.)", PLATE14, "64/144 (8 x 8 in saddle plate = 64/144 S.F. per plate)", "substitute",
    "drawn: 8\" x 8\" x 1/4\" saddle plates at the (E) column; row is 1/4\" shop-fabricated plate, material only", match="partial")
d.U("X-09", "Embedded anchors (4) 1/2\" dia x 4\" per plate (8 total)", "book_row_not_matching", ANCHOR_REASON, ANCHOR_CAND)
d.L("X-10", "not_quantified", "plate size of the stringer enclosure not stated", "OT-05122365-2210 (verified, 1/4\" steel plate welded in place, S.F.)")
d.C("X-11", "Wall rail, aluminum pipe, 1-1/2\" diameter, satin finish (L.F.)", WALL_RAIL, "1", "substitute",
    "drawn: 1-1/2\" diameter metal handrails both sides at 34-38\" with extensions, wall mounted, material and finish not stated (RFI 10); row is an aluminum satin wall rail 1-1/2\"")
d.L("X-12", "not_quantified", "guard at the landing: picket guard vs wall-mounted rail not resolved (RFI 9); LF not dimensioned", "OT-05521350-2050 (verified, 42\" high steel rail primed, L.F.)")
d.L("X-13", "not_in_book", "visual warning strips are not in the book")
d.U("X-14", "Metal studs 6\" 16 ga @ 16\" o.c. with track, 9'-6 1/2\" / 7'-6 1/2\" high", "book_row_not_verified",
    "drawn: 6\" 16 ga steel studs @ 16\" o.c.; the matching 05 41 13.30 line (10' high walls, 16 ga x 6\" wide, 16\" OC) is machine_read, the 8' high 16 ga x 6\" line is unverified too, and the 09 22 16.13 S.F. rows for 6\" studs are 25 ga",
    "OT-05411330-5400 (machine_read, 10' high 16 ga x 6\" 16\" OC, L.F.); OT-05411330-6410 (verified, 12' high 16 ga x 6\" 24\" OC, L.F.); OT-09221613-3410 (verified, 25 ga 6\" 12\" OC, S.F.)")
d.C("X-14", "5/8\" fire-resistant (Type X) GWB on walls, taped and finished level 4, both faces (S.F.)", GWB_X, "1595/95.54 (takeoff notes: wall area 797 SF one face, GWB both faces 1,595 SF, over 95.54 LF)", "exact",
    "drawn (wall note 1): 5/8\" Type X GWB each side; row = 5/8\" fire-resistant GWB taped and finished (level 4); area per the takeoff notes (level 1 38.38 LF x 9.542 ft + mezzanine 57.17 LF x 7.542 ft = 797 SF per face)")
d.C("X-14", "Mineral wool batts 3-1/2\" thick R15, wall or ceiling, as the 4\" acoustic insulation (S.F.)", INSUL, "797/95.54 (takeoff notes: 797 SF of wall over 95.54 LF)", "substitute",
    "drawn: 4\" acoustic insulation per UL Des U404, product not stated; row is 3-1/2\" R15 mineral wool batt")
d.C("X-15", "Aluminum-framed entrance door, 3' x 7' opening, clear anodized finish (Opng.)", SF_DOOR, "1", "substitute",
    "drawn: tempered-glass storefront exit doors 3'-0\" leaves to match the (E) door (height scales 6.9 ft; door schedule A-7.10 of the exit-stair set not issued); row is a stock clear-anodized aluminum entrance door 3' x 7'")
d.C("X-15", "Door frame for above doors, 3'-0\" x 7'-0\", bronze finish (Opng.)", SF_FRAME, "1", "substitute", "frame finish 'to match existing' not fixed; row is bronze finish")
d.U("X-15", "Panic hardware with accessible lever trim", "book_row_not_matching", "the only verified rows with a panic device are average hardware sets for school / motel doors, a different product", PANIC_CAND)
d.C("X-15", "Door closer, surface mounted, light duty, parallel arm, primed (Ea.)", CLOSER, "1", "substitute", "drawn: self-closing device; closer grade not fixed; row is light duty")
d.C("X-15", "Bronze panic threshold 5\" wide, 1/2\" thick (Ea.)", THRESH, "1", "substitute", "drawn: exterior weatherstripping and threshold; threshold type not fixed; weatherstripping has no verified row")
d.C("X-16", "Float glass, 1/4\" thick, clear, tempered (S.F.)", "OT-08811010-0800", "1", "substitute",
    "drawn: fixed tempered insulated-glass panel 4'-8\" x 6.92 ft matching the (E) storefront; row is 1/4\" monolithic tempered clear glass (insulated unit not in the verified rows); framing is the next component")
d.U("X-16", "Aluminum tube framing for the fixed panel", "not_quantified", "framing LF not dimensioned (4'-8\" wide bay, height taken from the (E) door; mullion layout not drawn)", "OT-08411320-0150 (verified, plain tube frame 1-3/4\" x 4\", L.F.)")
d.C("X-17", "Steel door, flush, 'B' label 90 min, full panel, 20 ga, 3'-0\" x 7'-0\" (Ea.)", HM_DOOR, "1", "substitute",
    "drawn: 1-hr fire-rated exit access door, size per A-7.10 of the exit-stair set (not issued); row is a 90-minute B-label 3'-0\" x 7'-0\" steel door")
d.C("X-17", "Hollow metal frame 14 ga, 'B' label, up to 5-3/4\" deep, 4'-0\" x 7'-0\" single (Ea.)", HM_FRAME_B, "1", "substitute", "size difference: row is a 4'-0\" wide labeled frame; door size not issued")
d.U("X-17", "Panic hardware on the rated exit access door", "book_row_not_matching", "the only verified rows with a panic device are average hardware sets for school / motel doors, a different product", PANIC_CAND)
d.L("X-18", "book_row_not_verified", "removal of (E) exterior plaster wall infill panels (about 42 SF): the exterior stucco removal row is flagged", "OT-09050530-0300 (flagged, exterior stucco 1\" over mesh, S.F.)")
d.L("X-19", "book_row_not_verified", "the storefront swing door removal row is flagged", "OT-08050510-3900 (flagged, storefront swing door)")
d.L("X-20", "not_quantified", "location, size and infill construction of the (E) door access to be removed are not detailed (RFI 14)")
d.L("X-21", "none_required", "sidewalk work at the Vine St doors: quantity 0 (the Hollywood Blvd bay items are in the architectural takeoff)")
d.L("X-22", "not_quantified", "exit sign count not legible on the exit-analysis plan", "OT-26521316-0240 (verified, LED exit sign with battery unit)")
d.L("X-23", "not_quantified", "finish of the exit-stair steel not specified (RFI 10); SF not stated", "OT-09912352-6550 (verified, pipe/steel primer spray, L.F.)")

# ---- General conditions
d.L("G-01", "not_in_book", "building permit fees are percentage rules of thumb in the book (01 41 26.50, percent_add), not a cost row; fee per the jurisdiction's schedule", "OT-01412650-0020 (percent_add)")
d.L("G-02", "not_in_book", "permit fee (separate permit 26016-10000-18605): percentage rule of thumb only in the book", "OT-01412650-0020 (percent_add)")
d.L("G-03", "none_required", "MEP and fire-alarm permits pulled by others (quantity 0)")
d.L("G-04", "not_in_book", "fire-sprinkler / FLS plan submittal by the fire sprinkler contractor: design and submittal service, no cost row; new vs modified NFPA-13 system is an RFI")
d.L("G-05", "not_quantified", "Cal/OSHA permit need depends on trench depth (not stated)")
d.L("G-06", "not_in_book", "DIG-ALERT notification: no cost row")
d.L("G-07", "not_quantified", "encroachment / pedestrian protection permits depend on the logistics plan")
d.L("G-08", "not_quantified", "historic facade protection extents not dimensioned; Mills Act / HPR compliance is a process item", "OT-01561610-1000 (verified, dust partition 6 mil poly on 1x3 frame, S.F.)")
d.L("G-09", "owner_provided", "CUP conditions are the owner's operational obligations; no construction quantity")
d.L("G-10", "not_quantified", "construction waste management: haul volume not derivable (D-29)", "OT-02411919-0800 (verified, 30 CY dumpster weekly rental, Week)")
d.L("G-11", "not_in_book", "green-building note items (MERV 13 filters before occupancy, O&M recommendations) have no cost row; fixtures are on the trade takeoffs")
d.L("G-12", "not_in_book", "field verification of existing conditions: company lump-sum item, no matching row")
d.L("G-13", "not_quantified", "shop drawing package count not stated; no cost row")
d.L("G-14", "not_in_book", "special inspection rows of 01 45 23 (technician for inspection, bolting, welding) carry no cost in the table", "OT-01452350-5650 (verified, technician inspection bolting, no cost printed)")
d.L("G-15", "none_required", "no concrete specified above 2,500 psi (quantity 0); becomes required if the pan fill or pit slab is specified higher (RFI)")
d.L("G-16", "not_in_book", "Sure-Board sheathing inspection: deputy inspection rows carry no cost; duration not stated")
d.L("G-17", "not_quantified", "welding / bolting inspection duration not stated; rows carry no cost", "OT-01452350-5790 (verified, technician inspection welding, no cost printed)")
d.L("G-18", "not_in_book", "structural observation by the engineer of record: professional service, no cost row")
d.L("G-19", "not_in_book", "LARR / ICC listing evidence on site: no cost row")
d.L("G-20", "not_quantified", "protection extents (terrazzo, restrooms, riser cabinet, sidewalks, facade) not dimensioned", "OT-01761320-0020 (verified, temporary floor protection 1/8\" hardboard, S.F.); OT-01562650-2200 (verified, sidewalk protection planks, S.F.)")
d.L("G-21", "not_quantified", "phasing / occupied-restaurant work: duration not stated")
d.L("G-22", "not_quantified", "temporary facilities: duration not stated (temporary utility rows carry no cost)", "OT-01562650-0200 (verified, rented chain link fence 6' high, L.F.)")
d.L("G-23", "book_row_not_verified", "final clean by the GC row is flagged; the daily cleanup row needs the duration (not stated)", "OT-01741320-0100 (flagged, final clean by GC, M.S.F.); OT-01741320-0050 (verified, continuous daily cleanup, M.S.F. per day)")
d.L("G-24", "not_quantified", "supervision / PM: duration not stated; field personnel rows are flagged", "OT-01311320-0240 (flagged, superintendent)")
d.L("G-25", "not_quantified", "shoring at the waffle-floor cuts not detailed; shoring rows carry no cost", "OT-01542370-0920 (verified, heavy duty shoring frames, no cost printed)")
d.L("G-26", "not_quantified", "blocking and backing LF not quantifiable (fixture and equipment locations by others)")
d.L("G-27", "not_in_book", "insurance and licensing evidence: percentage / company item, no cost row")
d.L("G-28", "not_quantified", "hazardous-materials survey not required by any document; owner to state")
d.L("G-29", "none_required", "information row (code data), no work")

d.write("matches_demo_struct_gc.csv")
