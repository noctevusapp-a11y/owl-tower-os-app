#!/usr/bin/env python3
"""Generate reference CSVs: units, regions, categories, trades, equipment_types.

These are classification/definition tables, not market data:
  * units: exact rational conversion factors (computed with fractions.Fraction)
  * regions: identifiers entered from model knowledge -> origin=assumed, review_status=unreviewed
  * categories/trades/equipment_types: OWN codes authored for this project

Run:  python3 -I pipeline/scripts/gen_reference.py
"""
from __future__ import annotations

import csv
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = ROOT / "data" / "csv"


def write_csv(name: str, header: list[str], rows: list[dict]) -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_DIR / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in header})


# --------------------------------------------------------------------- units
# Exact definitions:
#   1 in = 0.0254 m (exact), 1 ft = 0.3048 m, 1 lb = 0.45359237 kg (exact)
#   1 US liquid gallon = 231 in^3 (exact); 1 CF = 1728 in^3
#   1 imperial gallon = 4.54609 L (exact); 1 in^3 = 16.387064 mL (exact)
#   short ton = 2000 lb, long ton = 2240 lb, metric ton = 1000 kg
#   1 refrigeration ton = 12,000 Btu/h (definition)  -> capacity, NOT a mass
LB_PER_KG = Fraction(100000000, 45359237)
CF_IN3 = 1728
CF_PER_GAL_US = Fraction(231, CF_IN3)
IN3_ML = Fraction(16387064, 1000000)           # mL per in^3
GAL_IMP_ML = Fraction(454609, 100)             # 4.54609 L = 4546.09 mL
CF_PER_GAL_IMP = (GAL_IMP_ML / IN3_ML) / CF_IN3


def unit(unit_id, base_code, qualifier, name, dim, base, factor, formula, definition):
    fixed = factor is not None
    return {
        "unit_id": unit_id, "base_code": base_code, "qualifier": qualifier, "name": name,
        "dimension": dim, "base_unit_id": base,
        "to_base_num": factor.numerator if fixed else None,
        "to_base_den": factor.denominator if fixed else None,
        "factor_formula": formula, "definition": definition,
        "is_fixed_conversion": "true" if fixed else "false",
    }


UNITS = [
    unit("EA", "EA", None, "each", "count", "EA", Fraction(1), "EA = 1 EA", "Single countable item."),
    unit("LF", "LF", None, "linear foot", "length", "LF", Fraction(1), "LF = 1 LF", "12 in."),
    unit("SF", "SF", None, "square foot", "area", "SF", Fraction(1), "SF = 1 SF", "144 in^2."),
    unit("SY", "SY", None, "square yard", "area", "SF", Fraction(9), "SY = 9 SF", "9 SF."),
    unit("CF", "CF", None, "cubic foot", "volume", "CF", Fraction(1), "CF = 1 CF", "1728 in^3."),
    unit("CY", "CY", None, "cubic yard", "volume", "CF", Fraction(27), "CY = 27 CF", "27 CF."),
    unit("LB", "LB", None, "pound (avoirdupois mass)", "mass", "LB", Fraction(1), "LB = 1 LB", "0.45359237 kg exactly."),
    unit("TON_SHORT", "TON", "short", "short ton (US ton)", "mass", "LB", Fraction(2000), "TON_SHORT = 2000 LB",
         "2000 lb. Default meaning of 'ton' for US bulk materials; always state the qualifier."),
    unit("TON_LONG", "TON", "long", "long ton", "mass", "LB", Fraction(2240), "TON_LONG = 2240 LB", "2240 lb."),
    unit("TON_METRIC", "TON", "metric", "metric tonne", "mass", "LB", Fraction(1000) * LB_PER_KG,
         "TON_METRIC = 1000 kg = 1000/0.45359237 LB", "1000 kg."),
    unit("TON_REFRIG", "TON", "refrigeration", "ton of refrigeration (cooling capacity)", "cooling_capacity", "TON_REFRIG",
         Fraction(1), "TON_REFRIG = 12000 Btu/h (capacity, not mass)",
         "HVAC cooling capacity: 12,000 Btu/h. Not convertible to mass units."),
    unit("GAL_US", "GAL", "us_liquid", "US liquid gallon", "volume", "CF", CF_PER_GAL_US, "GAL_US = 231/1728 CF",
         "231 in^3 = 3.785411784 L. Default for US paints, coatings, adhesives."),
    unit("GAL_IMP", "GAL", "imperial", "imperial gallon", "volume", "CF", CF_PER_GAL_IMP,
         "GAL_IMP = 4.54609 L / (16.387064 mL/in^3 * 1728 in^3/CF)", "4.54609 L. Not used for US products; present to detect mislabelled data."),
    unit("HR", "HR", None, "hour", "time", "HR", Fraction(1), "HR = 1 HR",
         "Context must say person-hour, crew-hour or equipment-hour; stored in separate fields, never mixed."),
    unit("DAY", "DAY", None, "work day / shift", "time", "HR", None, "DAY = shift_hours HR (shift length is a per-crew parameter)",
         "Not a fixed number of hours. Convert only through crews.shift_hours."),
]
UNIT_HEADER = ["unit_id", "base_code", "qualifier", "name", "dimension", "base_unit_id", "to_base_num", "to_base_den",
               "factor_formula", "definition", "is_fixed_conversion"]

# ------------------------------------------------------------------- regions
ASSUMED_BASIS = ("Identifier entered from model knowledge of Census FIPS / OMB CBSA delineations; "
                 "not yet checked against the official delineation file (see backlog BL-REF-001).")


def region(rid, level, name, parent, state, fips=None, cbsa=None, notes=None):
    return {"region_id": rid, "level": level, "name": name, "parent_region_id": parent, "state_code": state,
            "fips_code": fips, "cbsa_code": cbsa, "origin": "assumed", "assumption_basis": ASSUMED_BASIS,
            "review_status": "unreviewed", "notes": notes}


REGIONS = [
    region("REG-US", "country", "United States", None, None),
    region("REG-US-CA", "state", "California", "REG-US", "CA", "06"),
    region("REG-US-AZ", "state", "Arizona", "REG-US", "AZ", "04"),
    region("REG-US-NV", "state", "Nevada", "REG-US", "NV", "32"),
    region("REG-CA-037", "county", "Los Angeles County, CA", "REG-MD-31084", "CA", "06037", None, "Primary pilot region."),
    region("REG-CA-059", "county", "Orange County, CA", "REG-MSA-31080", "CA", "06059"),
    region("REG-CA-065", "county", "Riverside County, CA", "REG-MSA-40140", "CA", "06065"),
    region("REG-CA-071", "county", "San Bernardino County, CA", "REG-MSA-40140", "CA", "06071"),
    region("REG-CA-073", "county", "San Diego County, CA", "REG-US-CA", "CA", "06073"),
    region("REG-CA-111", "county", "Ventura County, CA", "REG-US-CA", "CA", "06111"),
    region("REG-AZ-013", "county", "Maricopa County, AZ", "REG-MSA-38060", "AZ", "04013"),
    region("REG-NV-003", "county", "Clark County, NV", "REG-MSA-29820", "NV", "32003"),
    region("REG-MSA-31080", "msa", "Los Angeles-Long Beach-Anaheim, CA (CBSA)", "REG-US-CA", "CA", None, "31080",
           "CBSA containing Los Angeles and Orange counties."),
    region("REG-MD-31084", "metro_division", "Los Angeles-Long Beach-Glendale, CA (Metropolitan Division)", "REG-MSA-31080", "CA",
           None, "31084", "Los Angeles County; the geography BLS OEWS uses for LA."),
    region("REG-MSA-40140", "msa", "Riverside-San Bernardino-Ontario, CA (CBSA)", "REG-US-CA", "CA", None, "40140"),
    region("REG-MSA-38060", "msa", "Phoenix-Mesa-Chandler, AZ (CBSA)", "REG-US-AZ", "AZ", None, "38060"),
    region("REG-MSA-29820", "msa", "Las Vegas-Henderson-Paradise, NV (CBSA)", "REG-US-NV", "NV", None, "29820"),
]
REGION_HEADER = ["region_id", "level", "name", "parent_region_id", "state_code", "fips_code", "cbsa_code", "origin",
                 "assumption_basis", "review_status", "notes"]

# ---------------------------------------------------------------- categories
# required_product_attributes = attributes that DEFINE material equivalence. Two products are only
# interchangeable (same spec_key) if ALL of these match. Anything omitted here is NOT assumed equal.
TOP = [
    ("CAT-DEM", "Demolition", False), ("CAT-CON", "Concrete", True), ("CAT-REB", "Reinforcement", True),
    ("CAT-FRM", "Framing", True), ("CAT-DRY", "Drywall", True), ("CAT-INS", "Insulation", True),
    ("CAT-ROF", "Roofing", False), ("CAT-WPF", "Waterproofing", False), ("CAT-DAW", "Doors and windows", False),
    ("CAT-FIN", "Finishes", False), ("CAT-FLR", "Flooring", False), ("CAT-PNT", "Painting", True),
    ("CAT-PLB", "Plumbing", False), ("CAT-HVC", "HVAC", True), ("CAT-ELE", "Electrical", False),
]
SUB = [
    # framing
    ("CAT-FRM-LBR", "CAT-FRM", "Dimensional lumber and engineered wood",
     ["product_type", "species_group", "grade", "nominal_size", "length_in", "treatment", "moisture_state"]),
    ("CAT-FRM-SHT", "CAT-FRM", "Structural sheathing panels (plywood, OSB)",
     ["panel_type", "thickness_in", "width_in", "length_in", "span_rating", "exposure_rating", "grade"]),
    ("CAT-FRM-LGS", "CAT-FRM", "Light-gauge steel framing members",
     ["member_type", "web_depth_in", "flange_width_in", "thickness_mils", "yield_strength_ksi", "length_in", "coating", "structural"]),
    ("CAT-FRM-FAS", "CAT-FRM", "Fasteners",
     ["fastener_type", "length_in", "diameter_or_gauge", "head_type", "thread_type", "finish_or_material", "drive"]),
    ("CAT-FRM-CON", "CAT-FRM", "Structural connectors and anchors",
     ["connector_type", "nominal_member_size", "steel_gauge", "finish"]),
    # drywall
    ("CAT-DRY-BRD", "CAT-DRY", "Gypsum board",
     ["board_type", "core_type", "thickness_in", "width_in", "length_in", "edge_type", "fire_rated_x", "moisture_or_mold_resistant"]),
    ("CAT-DRY-JNT", "CAT-DRY", "Joint compound",
     ["compound_type", "setting_or_drying", "container_gal", "weight_class"]),
    ("CAT-DRY-TAP", "CAT-DRY", "Joint tape and corner bead",
     ["product_type", "width_in", "length_ft", "material"]),
    # insulation
    ("CAT-INS-BAT", "CAT-INS", "Batt and roll insulation",
     ["material", "r_value", "nominal_thickness_in", "width_in", "facing", "cavity_nominal"]),
    # concrete
    ("CAT-CON-BAG", "CAT-CON", "Bagged concrete and mortar mixes",
     ["product_type", "compressive_strength_psi", "bag_weight_lb", "max_aggregate_in"]),
    ("CAT-CON-RMX", "CAT-CON", "Ready-mixed concrete (supplier quote basis)",
     ["strength_psi", "max_aggregate_in", "slump_in", "cement_type", "air_entrained", "admixtures", "delivery_basis"]),
    ("CAT-CON-ACC", "CAT-CON", "Concrete accessories",
     ["accessory_type", "size_text", "material", "standard"]),
    ("CAT-CON-FRM", "CAT-CON", "Formwork materials",
     ["product_type", "thickness_in", "width_in", "length_in", "grade"]),
    # reinforcement
    ("CAT-REB-BAR", "CAT-REB", "Reinforcing bar and welded wire reinforcement",
     ["product_type", "size_designation", "grade_or_gauge", "length_ft", "coating", "standard"]),
    ("CAT-REB-ACC", "CAT-REB", "Reinforcement accessories",
     ["accessory_type", "size_text", "material"]),
    # painting
    ("CAT-PNT-PNT", "CAT-PNT", "Finish paint",
     ["coating_type", "resin_base", "sheen", "exposure", "container_gal", "voc_g_per_l"]),
    ("CAT-PNT-PRM", "CAT-PNT", "Primer and sealer",
     ["coating_type", "resin_base", "sheen", "exposure", "container_gal", "voc_g_per_l"]),
    ("CAT-PNT-SUP", "CAT-PNT", "Painting supplies and sealants",
     ["supply_type", "size_text", "material", "grade_or_nap"]),
    # HVAC
    ("CAT-HVC-EQP", "CAT-HVC", "HVAC equipment (condensers, heat pumps, furnaces, air handlers)",
     ["equipment_type", "cooling_capacity_tons", "efficiency_seer2", "heating_type_or_rating", "voltage_v", "phase", "refrigerant", "configuration"]),
    ("CAT-HVC-DUC", "CAT-HVC", "Ductwork and fittings",
     ["duct_type", "size_in", "insulation_r_value", "material_or_gauge", "length_ft", "standard"]),
    ("CAT-HVC-REF", "CAT-HVC", "Refrigerant and line sets",
     ["product_type", "refrigerant_type", "size_text", "insulation", "length_ft_or_container_lb"]),
    ("CAT-HVC-CTL", "CAT-HVC", "Controls, thermostats and disconnects",
     ["product_type", "voltage_v", "amperage_a", "stages", "features"]),
    ("CAT-HVC-DIF", "CAT-HVC", "Registers, grilles and boots",
     ["product_type", "size_in", "material", "pattern"]),
    ("CAT-HVC-ACC", "CAT-HVC", "HVAC accessories (pads, hangers, mastic, tape, condensate)",
     ["accessory_type", "size_text", "material", "standard"]),
]
CAT_HEADER = ["category_id", "name", "parent_category_id", "description", "pilot", "required_product_attributes",
              "external_refs", "notes"]
CLASS_NOTE = ("Own code. External classifiers (CSI MasterFormat/UniFormat/OmniClass) are copyrighted by CSI: "
              "licence terms must be checked before any crosswalk (backlog BL-CLS-001).")


def categories():
    rows = []
    for cid, name, pilot in TOP:
        rows.append({"category_id": cid, "name": name, "parent_category_id": None, "description": None,
                     "pilot": "true" if pilot else "false", "required_product_attributes": "[]",
                     "external_refs": "{}", "notes": CLASS_NOTE})
    for cid, parent, name, attrs in SUB:
        rows.append({"category_id": cid, "name": name, "parent_category_id": parent, "description": None,
                     "pilot": "true", "required_product_attributes": json.dumps(attrs),
                     "external_refs": "{}", "notes": None})
    return rows


# -------------------------------------------------------------------- trades
# soc_code values come from model knowledge of the BLS Standard Occupational Classification (SOC 2018)
# and stay 'pending_verification' until matched against the OEWS file (agent A1 may confirm some).
TRADES = [
    ("TR-LAB", "Construction laborer", "47-2061"), ("TR-CARP", "Carpenter", "47-2031"),
    ("TR-DRYW", "Drywall installer", "47-2081"), ("TR-TAPE", "Drywall taper / finisher", "47-2082"),
    ("TR-PNT", "Painter, construction", "47-2141"), ("TR-PLB", "Plumber / pipefitter", "47-2152"),
    ("TR-ELE", "Electrician", "47-2111"), ("TR-HVAC", "HVAC / refrigeration mechanic-installer", "49-9021"),
    ("TR-CEM", "Cement mason / concrete finisher", "47-2051"), ("TR-REB", "Reinforcing iron / rebar worker", "47-2171"),
    ("TR-ROF", "Roofer", "47-2181"), ("TR-INS", "Insulation worker, floor/ceiling/wall", "47-2131"),
    ("TR-SHM", "Sheet metal worker", "47-2211"), ("TR-OPR", "Operating engineer / equipment operator", "47-2073"),
    ("TR-FLR", "Floor installer (non-carpet, non-tile)", "47-2042"), ("TR-TILE", "Tile and stone setter", "47-2044"),
    ("TR-GLZ", "Glazier", "47-2121"), ("TR-SUP", "Foreman / first-line supervisor", "47-1011"),
]
TRADE_HEADER = ["trade_code", "name", "soc_code", "soc_status", "description", "origin", "review_status", "notes"]

EQUIPMENT_TYPES = [
    ("EQ-SKID", "Skid-steer loader", True), ("EQ-MINIEX", "Mini excavator", True),
    ("EQ-CMIXER", "Portable concrete mixer", False), ("EQ-CVIB", "Concrete vibrator", False),
    ("EQ-PTROWEL", "Power trowel", False), ("EQ-CSAW", "Walk-behind concrete saw", False),
    ("EQ-BREAKER", "Demolition / breaker hammer", False), ("EQ-COMPR", "Air compressor", False),
    ("EQ-SCISSOR", "Scissor lift", False), ("EQ-BOOM", "Boom lift", False),
    ("EQ-SCAFF", "Scaffolding system", False), ("EQ-DUMPBIN", "Roll-off debris bin", False),
    ("EQ-HVACVAC", "Refrigerant vacuum pump", False), ("EQ-MLIFT", "Material / panel hoist", False),
    ("EQ-CPUMP", "Concrete pump", True), ("EQ-SPRAYER", "Airless sprayer", False),
]
EQ_HEADER = ["equipment_type_code", "name", "description", "typically_needs_operator", "origin", "review_status", "notes"]


def main() -> int:
    write_csv("units", UNIT_HEADER, UNITS)
    write_csv("regions", REGION_HEADER, REGIONS)
    write_csv("categories", CAT_HEADER, categories())
    write_csv("trades", TRADE_HEADER, [
        {"trade_code": c, "name": n, "soc_code": soc, "soc_status": "pending_verification", "description": None,
         "origin": "assumed", "review_status": "unreviewed",
         "notes": "SOC code from model knowledge; verify against BLS OEWS file."} for c, n, soc in TRADES])
    write_csv("equipment_types", EQ_HEADER, [
        {"equipment_type_code": c, "name": n, "description": None, "typically_needs_operator": "true" if op else "false",
         "origin": "assumed", "review_status": "unreviewed", "notes": "Own code; flag 'typically needs operator' is a planning hint only."}
        for c, n, op in EQUIPMENT_TYPES])
    print(f"units={len(UNITS)} regions={len(REGIONS)} categories={len(TOP)+len(SUB)} trades={len(TRADES)} "
          f"equipment_types={len(EQUIPMENT_TYPES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
