#!/usr/bin/env python3
"""Generate the PILOT definition tables (no market data):

  capture_targets            what still has to be collected (materials / labor / equipment / productivity / ...)
  crews, productivity_observations   explicit origin='missing' placeholders (never invented numbers)
  work_items, work_item_components   25 unit-cost operations with measurable specs
  assemblies, assembly_components    10 assemblies composed of versioned work items

Quantities per unit come from GEOMETRY of the stated spec (exact fractions, formula text stored).
Waste factors, labor norms, crew compositions and manufacturer coverage are NOT invented: they are left
missing and show up as 'missing_inputs' in every calculation run.

Run:  python3 -I pipeline/scripts/gen_pilot_definitions.py
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb.ids import make_id, spec_key  # noqa: E402
from costdb.schema_meta import parse_schema  # noqa: E402
from costdb.store import Database, format_value  # noqa: E402

CSV_DIR = ROOT / "data" / "csv"
VALID_FROM = "2026-10-24"
BASIS = ("Owl Tower pilot scope definition v1 (authored 2026-10-24). Quantities are derived from the stated geometry; "
         "not copied from any commercial cost book. The estimator/engineer must confirm the spec against project "
         "requirements and the governing code before use.")

# ---------------------------------------------------------------- category attribute requirements
CATS = {r["category_id"]: json.loads(r["required_product_attributes"])
        for r in csv.DictReader(open(CSV_DIR / "categories.csv", encoding="utf-8"))}

# =================================================================== MATERIAL SPEC LINES
MATS: dict[str, dict] = {}


def mat(key: str, cat: str, desc: str, attrs: dict, sale: str):
    assert key not in MATS, key
    MATS[key] = {"key": key, "cat": cat, "desc": desc, "attrs": attrs, "sale": sale,
                 "spec_key": spec_key(cat, attrs, CATS[cat])}


def lumber(key, nominal, length_in, grade, desc, treatment="none", moisture="KD", ptype="dimension_lumber"):
    mat(key, "CAT-FRM-LBR", desc, {"product_type": ptype, "species_group": "DF-L", "grade": grade, "nominal_size": nominal,
                                   "length_in": length_in, "treatment": treatment, "moisture_state": moisture}, "each piece")


lumber("stud_2x4_92", "2x4", 92.625, "stud", "2x4 precut stud 92-5/8 in, DF-L, stud grade, kiln-dried", ptype="precut_stud")
lumber("lbr_2x4_96", "2x4", 96, "#2", "2x4x8 ft DF-L #2 and better, kiln-dried")
lumber("lbr_2x4_120", "2x4", 120, "#2", "2x4x10 ft DF-L #2 and better, kiln-dried")
lumber("lbr_2x4_144", "2x4", 144, "#2", "2x4x12 ft DF-L #2 and better, kiln-dried")
lumber("stud_2x6_92", "2x6", 92.625, "stud", "2x6 precut stud 92-5/8 in, DF-L, stud grade, kiln-dried", ptype="precut_stud")
lumber("lbr_2x6_96", "2x6", 96, "#2", "2x6x8 ft DF-L #2 and better, kiln-dried")
lumber("lbr_2x6_144", "2x6", 144, "#2", "2x6x12 ft DF-L #2 and better, kiln-dried")
lumber("lbr_2x8_144", "2x8", 144, "#2", "2x8x12 ft DF-L #2 and better, kiln-dried")
lumber("lbr_2x10_144", "2x10", 144, "#2", "2x10x12 ft DF-L #2 and better, kiln-dried")
lumber("lbr_2x12_144", "2x12", 144, "#2", "2x12x12 ft DF-L #2 and better, kiln-dried")
lumber("pt_2x4_96", "2x4", 96, "#2", "2x4x8 ft DF-L pressure-treated UC4A (sill plate)", treatment="PT_UC4A", moisture="KDAT")
lumber("pt_2x6_96", "2x6", 96, "#2", "2x6x8 ft DF-L pressure-treated UC4A (sill plate)", treatment="PT_UC4A", moisture="KDAT")

for key, ptype, th, span, desc in [
        ("ply_15_32", "plywood", "15/32", "32/16", "Plywood sheathing 15/32 in 4x8, Exposure 1, CD, span rating 32/16"),
        ("ply_19_32", "plywood", "19/32", "40/20", "Plywood sheathing 19/32 in 4x8, Exposure 1, CD, span rating 40/20"),
        ("ply_23_32", "plywood", "23/32", "48/24", "Plywood sheathing 23/32 in 4x8, Exposure 1, CD, span rating 48/24"),
        ("osb_7_16", "osb", "7/16", "24/16", "OSB sheathing 7/16 in 4x8, Exposure 1, span rating 24/16"),
        ("osb_23_32", "osb", "23/32", "48/24", "OSB sheathing 23/32 in 4x8, Exposure 1, span rating 48/24")]:
    mat(key, "CAT-FRM-SHT", desc, {"panel_type": ptype, "thickness_in": th, "width_in": 48, "length_in": 96, "span_rating": span,
                                   "exposure_rating": "Exposure 1", "grade": "CD" if ptype == "plywood" else "sheathing"}, "each sheet")

for key, member, depth, flange, mils, desc in [
        ("lgs_stud_362_18", "stud", 3.625, 1.625, 18, "Steel stud 3-5/8 in x 1-5/8 in, 18 mil (25 ga), 10 ft, nonstructural"),
        ("lgs_track_362_18", "track", 3.625, 1.25, 18, "Steel track 3-5/8 in x 1-1/4 in, 18 mil (25 ga), 10 ft, nonstructural"),
        ("lgs_stud_362_30", "stud", 3.625, 1.625, 30, "Steel stud 3-5/8 in x 1-5/8 in, 30 mil (20 ga), 10 ft, nonstructural"),
        ("lgs_track_362_30", "track", 3.625, 1.25, 30, "Steel track 3-5/8 in x 1-1/4 in, 30 mil (20 ga), 10 ft, nonstructural"),
        ("lgs_stud_600_18", "stud", 6.0, 1.625, 18, "Steel stud 6 in x 1-5/8 in, 18 mil (25 ga), 10 ft, nonstructural"),
        ("lgs_track_600_18", "track", 6.0, 1.25, 18, "Steel track 6 in x 1-1/4 in, 18 mil (25 ga), 10 ft, nonstructural")]:
    mat(key, "CAT-FRM-LGS", desc, {"member_type": member, "web_depth_in": depth, "flange_width_in": flange,
                                   "thickness_mils": mils, "yield_strength_ksi": 33, "length_in": 120,
                                   "coating": "G40" if mils == 18 else "G60", "structural": "no"}, "each piece")

for key, ftype, length, dia, head, thread, finish, drive, desc in [
        ("ds_coarse_125", "drywall_screw", 1.25, "#6", "bugle", "coarse", "phosphate", "phillips", "Drywall screw #6 x 1-1/4 in, coarse thread (wood)"),
        ("ds_coarse_1625", "drywall_screw", 1.625, "#6", "bugle", "coarse", "phosphate", "phillips", "Drywall screw #6 x 1-5/8 in, coarse thread (wood)"),
        ("ds_fine_125", "drywall_screw", 1.25, "#6", "bugle", "fine", "phosphate", "phillips", "Drywall screw #6 x 1-1/4 in, fine thread (steel)"),
        ("ds_fine_1625", "drywall_screw", 1.625, "#6", "bugle", "fine", "phosphate", "phillips", "Drywall screw #6 x 1-5/8 in, fine thread (steel)"),
        ("nail_16d", "nail", 3.25, "0.148 in", "flat", "smooth", "vinyl_coated", "not_applicable", "16d sinker nail 3-1/4 in x 0.148 in"),
        ("nail_8d", "nail", 2.5, "0.131 in", "flat", "smooth", "bright", "not_applicable", "8d common nail 2-1/2 in x 0.131 in"),
        ("sd_pan_8", "self_drilling_screw", 0.5, "#8", "pan", "fine", "zinc_plated", "phillips", "Self-drilling pan-head screw #8 x 1/2 in (steel framing)")]:
    mat(key, "CAT-FRM-FAS", desc, {"fastener_type": ftype, "length_in": length, "diameter_or_gauge": dia, "head_type": head,
                                   "thread_type": thread, "finish_or_material": finish, "drive": drive}, "box/package with stated count")

for key, ctype, size, desc in [("hanger_2x6", "joist_hanger_face_mount", "2x6", "Face-mount joist hanger for 2x6, 18 ga, G90"),
                               ("hanger_2x10", "joist_hanger_face_mount", "2x10", "Face-mount joist hanger for 2x10, 18 ga, G90"),
                               ("hurricane_tie", "hurricane_tie", "2x", "Hurricane / rafter tie for 2x members, 18 ga, G90")]:
    mat(key, "CAT-FRM-CON", desc, {"connector_type": ctype, "nominal_member_size": size, "steel_gauge": "18", "finish": "G90"}, "each")

for key, btype, core, th, length, fire, mr, desc in [
        ("gyp_half_reg_4x8", "gypsum_wallboard", "standard", 0.5, 96, "no", "no", "Gypsum board 1/2 in x 4x8, regular core, tapered edge"),
        ("gyp_half_reg_4x12", "gypsum_wallboard", "standard", 0.5, 144, "no", "no", "Gypsum board 1/2 in x 4x12, regular core, tapered edge"),
        ("gyp_58_x_4x8", "gypsum_wallboard", "type_x", 0.625, 96, "yes", "no", "Gypsum board 5/8 in x 4x8, Type X, tapered edge"),
        ("gyp_58_x_4x12", "gypsum_wallboard", "type_x", 0.625, 144, "yes", "no", "Gypsum board 5/8 in x 4x12, Type X, tapered edge"),
        ("gyp_half_mr_4x8", "moisture_resistant_gypsum", "moisture_resistant", 0.5, 96, "no", "yes", "Moisture-/mold-resistant gypsum board 1/2 in x 4x8"),
        ("gyp_58_x_mr_4x8", "moisture_resistant_gypsum", "type_x", 0.625, 96, "yes", "yes", "Moisture-/mold-resistant Type X board 5/8 in x 4x8"),
        ("gyp_half_lite_4x8", "gypsum_wallboard", "lightweight", 0.5, 96, "no", "no", "Lightweight gypsum board 1/2 in x 4x8, tapered edge"),
        ("gyp_quarter_flex_4x8", "flexible_gypsum", "standard", 0.25, 96, "no", "no", "Flexible gypsum board 1/4 in x 4x8")]:
    mat(key, "CAT-DRY-BRD", desc, {"board_type": btype, "core_type": core, "thickness_in": th, "width_in": 48, "length_in": length,
                                   "edge_type": "tapered", "fire_rated_x": fire, "moisture_or_mold_resistant": mr}, "each sheet")

mat("jnt_ap_std_45", "CAT-DRY-JNT", "All-purpose pre-mixed joint compound, 4.5 gal, standard weight",
    {"compound_type": "all_purpose", "setting_or_drying": "drying", "container_gal": 4.5, "weight_class": "standard"}, "pail")
mat("jnt_ap_lite_45", "CAT-DRY-JNT", "All-purpose pre-mixed joint compound, 4.5 gal, lightweight",
    {"compound_type": "all_purpose", "setting_or_drying": "drying", "container_gal": 4.5, "weight_class": "lightweight"}, "pail")
mat("jnt_top_lite_45", "CAT-DRY-JNT", "Topping compound, 4.5 gal, lightweight",
    {"compound_type": "topping", "setting_or_drying": "drying", "container_gal": 4.5, "weight_class": "lightweight"}, "pail")
mat("tape_paper_500", "CAT-DRY-TAP", "Paper joint tape 2-1/16 in x 500 ft",
    {"product_type": "joint_tape", "width_in": 2.0625, "length_ft": 500, "material": "paper"}, "roll")
mat("tape_mesh_300", "CAT-DRY-TAP", "Fiberglass mesh joint tape 1-7/8 in x 300 ft",
    {"product_type": "joint_tape", "width_in": 1.875, "length_ft": 300, "material": "fiberglass_mesh"}, "roll")
mat("bead_steel_8", "CAT-DRY-TAP", "Galvanized steel corner bead 1-1/4 in x 8 ft",
    {"product_type": "corner_bead", "width_in": 1.25, "length_ft": 8, "material": "galvanized_steel"}, "each piece")
mat("bead_paper_8", "CAT-DRY-TAP", "Paper-faced metal corner bead 1-1/4 in x 8 ft",
    {"product_type": "corner_bead", "width_in": 1.25, "length_ft": 8, "material": "paper_faced_metal"}, "each piece")

for key, material, r, th, width, facing, cavity, desc in [
        ("bat_fg_r13_kf", "fiberglass", 13, 3.5, 15, "kraft", "2x4", "Fiberglass batt R-13, 3-1/2 in, 15 in wide, kraft-faced (2x4)"),
        ("bat_fg_r13_uf", "fiberglass", 13, 3.5, 15, "unfaced", "2x4", "Fiberglass batt R-13, 3-1/2 in, 15 in wide, unfaced (2x4)"),
        ("bat_fg_r19_uf", "fiberglass", 19, 6.25, 15, "unfaced", "2x6", "Fiberglass batt R-19, 6-1/4 in, 15 in wide, unfaced (2x6)"),
        ("bat_fg_r21_kf", "fiberglass", 21, 5.5, 15, "kraft", "2x6", "Fiberglass batt R-21, 5-1/2 in, 15 in wide, kraft-faced (2x6)"),
        ("bat_mw_r15_uf", "mineral_wool", 15, 3.5, 15.25, "unfaced", "2x4", "Mineral-wool batt R-15, 3-1/2 in, 15-1/4 in wide, unfaced (2x4)"),
        ("bat_fg_r11_uf", "fiberglass", 11, 3.5, 15, "unfaced", "2x4", "Fiberglass sound batt R-11, 3-1/2 in, 15 in wide, unfaced (2x4)")]:
    mat(key, "CAT-INS-BAT", desc, {"material": material, "r_value": r, "nominal_thickness_in": th, "width_in": width,
                                   "facing": facing, "cavity_nominal": cavity}, "bag/package with stated coverage")

for key, ptype, strength, bag, agg, desc in [
        ("bag_conc_4000_80", "concrete_mix", 4000, 80, 0.75, "Bagged concrete mix, 4000 psi, 80 lb"),
        ("bag_conc_4000_60", "concrete_mix", 4000, 60, 0.75, "Bagged concrete mix, 4000 psi, 60 lb"),
        ("bag_fastset_50", "fast_setting_concrete", 4000, 50, 0.75, "Fast-setting concrete mix, 50 lb"),
        ("bag_grout_50", "nonshrink_grout", 7000, 50, "not_applicable", "Non-shrink grout, 50 lb"),
        ("bag_mortar_s_60", "mortar_mix_type_s", 1800, 60, "not_applicable", "Type S mortar mix, 60 lb")]:
    mat(key, "CAT-CON-BAG", desc, {"product_type": ptype, "compressive_strength_psi": strength, "bag_weight_lb": bag,
                                   "max_aggregate_in": agg}, "bag")

for key, strength, agg, desc in [("rmx_3000", 3000, 0.75, "Ready-mix concrete 3000 psi, 3/4 in agg, 4 in slump, Type II"),
                                 ("rmx_4000", 4000, 0.75, "Ready-mix concrete 4000 psi, 3/4 in agg, 4 in slump, Type II"),
                                 ("rmx_5000", 5000, 0.75, "Ready-mix concrete 5000 psi, 3/4 in agg, 4 in slump, Type II"),
                                 ("rmx_3000_pea", 3000, 0.375, "Ready-mix concrete 3000 psi pea-gravel pump mix, 3/8 in agg")]:
    mat(key, "CAT-CON-RMX", desc, {"strength_psi": strength, "max_aggregate_in": agg, "slump_in": 4 if agg == 0.75 else 5,
                                   "cement_type": "II", "air_entrained": "no", "admixtures": "none",
                                   "delivery_basis": "delivered_per_cy_supplier_quote"}, "cubic yard (quote)")

for key, atype, size, material, std, desc in [
        ("acc_vapor_10mil", "vapor_retarder", "10 mil x 10 ft x 100 ft roll", "polyethylene", "ASTM E1745", "Under-slab vapor retarder 10 mil, roll"),
        ("acc_exp_joint", "expansion_joint_filler", "1/2 in x 4-1/2 in x 10 ft", "bituminous_fiber", "ASTM D1751", "Expansion joint filler 1/2 in x 4-1/2 in x 10 ft"),
        ("acc_cure_5gal", "curing_compound", "5 gal pail", "resin_based_clear", "ASTM C309", "Concrete curing compound, 5 gal pail"),
        ("acc_anchor_bolt", "anchor_bolt_j", "1/2 in x 10 in with nut and washer", "carbon_steel", "ASTM F1554 Gr 36", "J anchor bolt 1/2 in x 10 in with nut and washer")]:
    mat(key, "CAT-CON-ACC", desc, {"accessory_type": atype, "size_text": size, "material": material, "standard": std}, "roll/pail/each")
mat("frm_plyform_34", "CAT-CON-FRM", "Form plywood 23/32 in x 4x8, B-B Plyform Class I",
    {"product_type": "form_plywood", "thickness_in": "23/32", "width_in": 48, "length_in": 96, "grade": "B-B Plyform Class I"}, "each sheet")

for key, size, grade, length, desc in [("reb_3_20", "#3", "Grade 60", 20, "Rebar #3 Grade 60, 20 ft"),
                                       ("reb_4_20", "#4", "Grade 60", 20, "Rebar #4 Grade 60, 20 ft"),
                                       ("reb_5_20", "#5", "Grade 60", 20, "Rebar #5 Grade 60, 20 ft"),
                                       ("reb_4_10", "#4", "Grade 60", 10, "Rebar #4 Grade 60, 10 ft")]:
    mat(key, "CAT-REB-BAR", desc, {"product_type": "rebar", "size_designation": size, "grade_or_gauge": grade, "length_ft": length,
                                   "coating": "uncoated", "standard": "ASTM A615"}, "each bar")
mat("wwr_66_w14", "CAT-REB-BAR", "Welded wire reinforcement 6x6-W1.4xW1.4, 5x10 ft sheet",
    {"product_type": "welded_wire_reinforcement", "size_designation": "6x6-W1.4xW1.4 (5x10 ft sheet)", "grade_or_gauge": "W1.4",
     "length_ft": 10, "coating": "uncoated", "standard": "ASTM A1064"}, "each sheet")
mat("tie_wire", "CAT-REB-ACC", "Rebar tie wire, 16 gauge annealed, coil",
    {"accessory_type": "tie_wire", "size_text": "16 gauge coil", "material": "annealed_steel"}, "coil")
mat("chair_2in", "CAT-REB-ACC", "Bar/mesh support chair 2 in height, plastic",
    {"accessory_type": "bar_chair", "size_text": "2 in height", "material": "plastic"}, "package with stated count")
mat("chair_3in", "CAT-REB-ACC", "Bar support chair 3 in height, plastic",
    {"accessory_type": "bar_chair", "size_text": "3 in height", "material": "plastic"}, "package with stated count")

for key, ctype, resin, sheen, exposure, gal, voc, desc in [
        ("pnt_int_flat_1", "wall_paint", "acrylic_latex", "flat", "interior", 1, "<=50", "Interior acrylic latex wall paint, flat, 1 gal"),
        ("pnt_int_egg_1", "wall_paint", "acrylic_latex", "eggshell", "interior", 1, "<=50", "Interior acrylic latex wall paint, eggshell, 1 gal"),
        ("pnt_int_semi_1", "wall_paint", "acrylic_latex", "semi_gloss", "interior", 1, "<=50", "Interior acrylic latex paint, semi-gloss, 1 gal"),
        ("pnt_int_flat_5", "wall_paint", "acrylic_latex", "flat", "interior", 5, "<=50", "Interior acrylic latex wall paint, flat, 5 gal"),
        ("pnt_int_egg_5", "wall_paint", "acrylic_latex", "eggshell", "interior", 5, "<=50", "Interior acrylic latex wall paint, eggshell, 5 gal"),
        ("pnt_int_semi_5", "wall_paint", "acrylic_latex", "semi_gloss", "interior", 5, "<=50", "Interior acrylic latex paint, semi-gloss, 5 gal"),
        ("pnt_ceil_flat_5", "ceiling_paint", "acrylic_latex", "flat", "interior", 5, "<=50", "Interior ceiling paint, flat, 5 gal"),
        ("pnt_ext_satin_5", "wall_paint", "acrylic_latex", "satin", "exterior", 5, "<=50", "Exterior acrylic latex paint, satin, 5 gal"),
        ("pnt_ext_satin_1", "wall_paint", "acrylic_latex", "satin", "exterior", 1, "<=50", "Exterior acrylic latex paint, satin, 1 gal"),
        ("pnt_ext_elast_5", "elastomeric", "acrylic", "flat", "exterior", 5, "<=50", "Exterior elastomeric coating, flat, 5 gal"),
        ("pnt_ext_semi_1", "trim_paint", "acrylic_latex", "semi_gloss", "exterior", 1, "<=50", "Exterior acrylic trim paint, semi-gloss, 1 gal")]:
    mat(key, "CAT-PNT-PNT", desc, {"coating_type": ctype, "resin_base": resin, "sheen": sheen, "exposure": exposure,
                                   "container_gal": gal, "voc_g_per_l": voc}, "pail/can")
for key, ctype, resin, exposure, gal, voc, desc in [
        ("prm_pva_5", "primer", "pva", "interior", 5, "<=50", "PVA drywall primer, 5 gal"),
        ("prm_pva_1", "primer", "pva", "interior", 1, "<=50", "PVA drywall primer, 1 gal"),
        ("prm_bond_1", "bonding_primer", "acrylic", "interior", 1, "<=100", "Acrylic bonding primer, 1 gal"),
        ("prm_ext_5", "primer", "acrylic", "exterior", 5, "<=100", "Exterior acrylic primer, 5 gal"),
        ("prm_stain_1", "stain_blocking_primer", "water_based", "interior", 1, "<=100", "Stain-blocking primer, water-based, 1 gal")]:
    mat(key, "CAT-PNT-PRM", desc, {"coating_type": ctype, "resin_base": resin, "sheen": "flat", "exposure": exposure,
                                   "container_gal": gal, "voc_g_per_l": voc}, "pail/can")
for key, stype, size, material, grade, desc in [
        ("sup_caulk", "caulk", "10.1 fl oz cartridge", "acrylic_latex_siliconized", "paintable", "Paintable siliconized acrylic latex caulk, 10.1 fl oz"),
        ("sup_tape", "painters_tape", "1.88 in x 60 yd", "paper_masking", "multi_surface", "Painter's masking tape 1.88 in x 60 yd"),
        ("sup_roller_38", "roller_cover", "9 in", "polyester", "3/8 in nap", "Roller cover 9 in, 3/8 in nap"),
        ("sup_roller_12", "roller_cover", "9 in", "polyester", "1/2 in nap", "Roller cover 9 in, 1/2 in nap"),
        ("sup_drop", "drop_cloth", "9 ft x 12 ft", "canvas", "standard", "Canvas drop cloth 9x12 ft"),
        ("sup_spackle", "spackling", "1 qt", "lightweight_vinyl", "interior", "Lightweight spackling compound, 1 qt"),
        ("sup_sponge", "sanding_sponge", "medium/fine", "foam_abrasive", "drywall", "Drywall sanding sponge, medium/fine")]:
    mat(key, "CAT-PNT-SUP", desc, {"supply_type": stype, "size_text": size, "material": material, "grade_or_nap": grade}, "each/pack")

NA = "not_applicable"
for key, etype, tons, seer, heat, volts, phase, ref, conf, desc in [
        ("eqp_ac_25", "ac_condenser", 2.5, 14.3, "cooling_only", "208/230", 1, "R-454B", "split_outdoor", "AC condenser 2.5 ton, 14.3 SEER2, R-454B"),
        ("eqp_ac_30", "ac_condenser", 3.0, 14.3, "cooling_only", "208/230", 1, "R-454B", "split_outdoor", "AC condenser 3 ton, 14.3 SEER2, R-454B"),
        ("eqp_ac_40", "ac_condenser", 4.0, 14.3, "cooling_only", "208/230", 1, "R-454B", "split_outdoor", "AC condenser 4 ton, 14.3 SEER2, R-454B"),
        ("eqp_hp_30", "heat_pump_condenser", 3.0, 15.2, "heat_pump", "208/230", 1, "R-454B", "split_outdoor", "Heat pump condenser 3 ton, 15.2 SEER2, R-454B"),
        ("eqp_furn_80", "gas_furnace", NA, NA, "80_afue_80000_btuh", "120", 1, NA, "upflow", "Gas furnace 80,000 Btu/h input, 80% AFUE, upflow"),
        ("eqp_coil_30", "evaporator_coil", 3.0, NA, NA, NA, NA, "R-454B", "cased_a_coil", "Cased evaporator coil 3 ton, R-454B"),
        ("eqp_ah_30", "air_handler", 3.0, NA, "electric_heat_5kw", "208/230", 1, "R-454B", "multiposition", "Air handler 3 ton with 5 kW electric heat"),
        ("eqp_rtu_50", "packaged_rooftop_unit", 5.0, 14.0, "gas_heat_120kbtuh", "208/230", 3, "R-454B", "single_package", "Packaged rooftop unit 5 ton, gas heat (quote)")]:
    mat(key, "CAT-HVC-EQP", desc, {"equipment_type": etype, "cooling_capacity_tons": tons, "efficiency_seer2": seer,
                                   "heating_type_or_rating": heat, "voltage_v": volts, "phase": phase, "refrigerant": ref,
                                   "configuration": conf}, "each")
for key, dtype, size, r, mat_, length, desc in [
        ("duc_flex_6", "flexible_duct_insulated", 6, 6, "polyethylene_jacket", 25, "Insulated flexible duct 6 in, R-6, 25 ft"),
        ("duc_flex_8", "flexible_duct_insulated", 8, 6, "polyethylene_jacket", 25, "Insulated flexible duct 8 in, R-6, 25 ft"),
        ("duc_flex_10", "flexible_duct_insulated", 10, 6, "polyethylene_jacket", 25, "Insulated flexible duct 10 in, R-6, 25 ft"),
        ("duc_rigid_6", "rigid_round_duct", 6, "none", "26_gauge_galvanized", 5, "Rigid round galvanized duct 6 in, 26 ga, 5 ft"),
        ("duc_rigid_8", "rigid_round_duct", 8, "none", "26_gauge_galvanized", 5, "Rigid round galvanized duct 8 in, 26 ga, 5 ft")]:
    mat(key, "CAT-HVC-DUC", desc, {"duct_type": dtype, "size_in": size, "insulation_r_value": r, "material_or_gauge": mat_,
                                   "length_ft": length, "standard": "UL 181" if "flexible" in dtype else NA}, "each length")
for key, ptype, rt, size, ins, qty, desc in [
        ("ref_ls_38_34_25", "line_set", NA, "3/8 in liquid x 3/4 in suction", "insulated_1_2_in_wall", 25, "Copper line set 3/8 x 3/4 in, 25 ft, insulated"),
        ("ref_ls_38_78_25", "line_set", NA, "3/8 in liquid x 7/8 in suction", "insulated_1_2_in_wall", 25, "Copper line set 3/8 x 7/8 in, 25 ft, insulated"),
        ("ref_r410a_25", "refrigerant", "R-410A", "25 lb cylinder", NA, 25, "Refrigerant R-410A, 25 lb cylinder (certified buyers only)"),
        ("ref_r454b_25", "refrigerant", "R-454B", "25 lb cylinder", NA, 25, "Refrigerant R-454B, 25 lb cylinder (certified buyers only)")]:
    mat(key, "CAT-HVC-REF", desc, {"product_type": ptype, "refrigerant_type": rt, "size_text": size, "insulation": ins,
                                   "length_ft_or_container_lb": qty}, "each")
for key, ptype, volts, amps, stages, feat, desc in [
        ("ctl_tstat_prog", "thermostat", "24", NA, "1H/1C", "programmable_7_day", "Programmable thermostat 24 V, 1H/1C"),
        ("ctl_tstat_smart", "thermostat", "24", NA, "2H/2C", "wifi_smart", "Wi-Fi smart thermostat 24 V, 2H/2C"),
        ("ctl_disc_60", "ac_disconnect", "240", 60, NA, "non_fused_pullout", "AC disconnect 60 A, 240 V, non-fused pull-out"),
        ("ctl_whip_6", "ac_whip", "240", 60, NA, "6ft_flexible_conduit", "AC whip 60 A, 6 ft flexible conduit")]:
    mat(key, "CAT-HVC-CTL", desc, {"product_type": ptype, "voltage_v": volts, "amperage_a": amps, "stages": stages,
                                   "features": feat}, "each")
for key, ptype, size, material, pattern, desc in [
        ("dif_floor_4x10", "floor_register", "4x10", "steel", "louvered", "Floor register 4x10 in, steel"),
        ("dif_ceil_12", "ceiling_diffuser", "12x12", "steel", "louvered_face", "Ceiling diffuser 12x12 in, steel"),
        ("dif_ret_20", "return_grille", "20x20", "steel", "filter_grille", "Return-air filter grille 20x20 in, steel"),
        ("dif_boot_6", "register_boot", "6 in round", "galvanized_steel", "90_degree", "Register boot 6 in round, 90 degree")]:
    mat(key, "CAT-HVC-DIF", desc, {"product_type": ptype, "size_in": size, "material": material, "pattern": pattern}, "each")
for key, atype, size, material, std, desc in [
        ("acc_pad_36", "condenser_pad", "36x36x3 in", "polyethylene_composite", NA, "Condenser pad 36x36x3 in, composite"),
        ("acc_mastic_1", "duct_mastic", "1 gal", "water_based", "UL 181", "Duct sealant mastic, water-based, 1 gal"),
        ("acc_foiltape", "foil_tape", "2.5 in x 60 yd", "aluminum_foil", "UL 181B-FX", "Aluminum foil tape 2.5 in x 60 yd, UL 181B-FX"),
        ("acc_strap", "hanger_strap", "1 in x 100 ft", "perforated_galvanized", NA, "Perforated galvanized hanger strap 1 in x 100 ft"),
        ("acc_condpump", "condensate_pump", "115 V 1/30 hp", "polymer", NA, "Condensate pump 115 V")]:
    mat(key, "CAT-HVC-ACC", desc, {"accessory_type": atype, "size_text": size, "material": material, "standard": std}, "each/roll")


# ============================================================================ WORK ITEMS
COMMON_EXCL = ["mobilization", "daily_cleanup_and_protection", "supervision_and_general_conditions",
               "sales_tax_and_delivery", "permits_and_inspections", "overhead_and_profit"]
NORMAL = ("Normal-access, unoccupied, new-work conditions at or below 10 ft working height; straight time; "
          "no hazardous materials; materials staged within 100 ft of the work. Other conditions need explicit adjustment factors.")

WORK_ITEMS: list[dict] = []
CREWS: dict[str, dict] = {}


def crew(cid, name, category, intended):
    CREWS.setdefault(cid, {"crew_id": cid, "name": name, "category_id": category,
                           "description": f"Intended trades: {intended}. Composition, sizes and shift length NOT yet sourced."})


def wi(wid, name, cat, unit, spec, desc, included, excluded, crew_id, comps, conditions=NORMAL, labor_desc=None,
       equipment=None):
    WORK_ITEMS.append({"id": wid, "name": name, "cat": cat, "unit": unit, "spec": spec, "desc": desc, "included": included,
                       "excluded": COMMON_EXCL + excluded, "crew": crew_id, "comps": comps, "conditions": conditions,
                       "labor_desc": labor_desc or name, "equipment": equipment or []})


def M(mat_key, desc, qty, unit, formula, tags, kind="material", mode="fixed", app=None, coats=None, origin="derived"):
    return {"kind": kind, "desc": desc, "mat": mat_key, "qty": qty, "unit": unit, "formula": formula, "tags": tags,
            "mode": mode, "app": app, "coats": coats, "origin": origin}


def MISSING(mat_key, desc, why, tags, unit=None, kind="material"):
    return {"kind": kind, "desc": desc, "mat": mat_key, "qty": None, "unit": unit, "formula": f"MISSING: {why}", "tags": tags,
            "mode": "fixed", "app": None, "coats": None, "origin": "missing"}


# ---- FRAMING ---------------------------------------------------------------------------------
crew("CRW-FRM-WOOD", "Wood framing crew (wall/floor)", "CAT-FRM", "carpenters, laborer")
crew("CRW-FRM-STEEL", "Light-gauge steel framing crew", "CAT-FRM", "carpenters/metal-stud framers, laborer")
crew("CRW-DRY-HANG", "Drywall hanging crew", "CAT-DRY", "drywall installers, laborer")
crew("CRW-DRY-FINISH", "Drywall taping/finishing crew", "CAT-DRY", "tapers/finishers")
crew("CRW-INS", "Insulation installation crew", "CAT-INS", "insulation workers")
crew("CRW-CON-FLAT", "Concrete flatwork crew", "CAT-CON", "cement masons, laborers, equipment operator as needed")
crew("CRW-CON-FOOT", "Footing/foundation crew", "CAT-CON", "carpenters, rebar workers, cement masons, laborers")
crew("CRW-CON-CURE", "Curing/sealing application crew", "CAT-CON", "laborer")
crew("CRW-PNT", "Painting crew", "CAT-PNT", "painters")
crew("CRW-HVAC-SPLIT", "HVAC split-system installation crew", "CAT-HVC", "HVAC mechanics, helper")
crew("CRW-HVAC-DUCT", "HVAC duct installation crew", "CAT-HVC", "sheet-metal/HVAC installers, helper")

wall_h = F(8)  # ft
for wid, nm, stud_key, plate_key, stud_nom in [("WI-FRM-001", "Frame wood stud wall 2x4 @16 in o.c., 8 ft high", "stud_2x4_92", "lbr_2x4_96", "2x4"),
                                               ("WI-FRM-002", "Frame wood stud wall 2x6 @16 in o.c., 8 ft high", "stud_2x6_92", "lbr_2x6_96", "2x6")]:
    studs_per_lf = F(12, 16)
    wi(wid, nm, "CAT-FRM", "SF",
       {"stud_nominal": stud_nom, "species_group": "DF-L", "stud_spacing_in": 16, "wall_height_ft": 8, "stud_length_in": 92.625,
        "bottom_plates": 1, "top_plates": 2, "unit_basis": "SF of wall face area (length x height)",
        "nailing": "2 x 16d each stud end; top-plate lamination 1 x 16d @16 in"},
       "Layout, cut, assemble and erect a single-story wood stud partition with one bottom plate and doubled top plate.",
       ["wall_layout", "stud_and_plate_materials", "stud_and_plate_nailing", "erect_plumb_and_line_labor"],
       ["corners_and_channels", "openings_headers_cripples", "blocking", "fireblocking", "sheathing",
        "temporary_bracing_materials", "small_tools_and_nailers"],
       "CRW-FRM-WOOD",
       [M(stud_key, f"{stud_nom} precut studs", studs_per_lf / wall_h, "EA",
          "(12 in/ft ÷ 16 in o.c.) studs per LF of wall ÷ 8 ft wall height = 0.09375 studs per SF of wall", ["stud"]),
        M(plate_key, f"{stud_nom} plate stock (1 bottom + 2 top)", F(3) / wall_h, "LF",
          "3 plates × 1 LF per LF of wall ÷ 8 ft wall height = 0.375 LF per SF of wall", ["plate"]),
        M("nail_16d", "16d nails, stud ends and top-plate lamination", studs_per_lf / wall_h * 4 + studs_per_lf / wall_h, "EA",
          "studs/SF × 4 end nails + 1 lamination nail per 16 in of top plate (0.75 per LF ÷ 8 ft) = 0.46875 per SF", ["fastener"]),
        ])

wi("WI-FRM-003", "Frame wood floor joists 2x10 @16 in o.c., 12 ft span, face-mount hangers", "CAT-FRM", "SF",
   {"joist_nominal": "2x10", "species_group": "DF-L", "joist_spacing_in": 16, "span_ft": 12,
    "unit_basis": "SF of floor area", "hangers": "2 face-mount hangers per joist"},
   "Install floor joists between supports using face-mount hangers; rim/band joist not included.",
   ["joist_materials", "hanger_materials", "joist_layout_and_install_labor"],
   ["rim_and_band_joists", "blocking_and_bridging", "subfloor", "openings_and_trimmers", "beams_and_girders"],
   "CRW-FRM-WOOD",
   [M("lbr_2x10_144", "2x10 joist stock", F(12, 16), "LF",
      "(12 in/ft ÷ 16 in o.c.) = 0.75 LF of joist per SF of floor (independent of span)", ["joist"]),
    M("hanger_2x10", "Joist hangers (2 per joist)", F(12, 16) / 12 * 2, "EA",
      "joists per SF = 0.75/12 ft span = 0.0625; × 2 hangers = 0.125 per SF", ["hanger"]),
    MISSING("nail_16d", "Hanger fasteners (per hanger manufacturer schedule)",
            "fastener count per hanger comes from the connector manufacturer's installation table", ["hanger_fasteners"], "EA")])

wi("WI-FRM-004", "Install plywood wall sheathing 15/32 in, 8d nails @6 in edge / 12 in field", "CAT-FRM", "SF",
   {"panel": "15/32 in plywood CD Exposure 1, 4x8", "framing_spacing_in": 16, "edge_nail_spacing_in": 6, "field_nail_spacing_in": 12,
    "unit_basis": "SF of sheathed wall area", "nail": "8d common"},
   "Install structural wall sheathing panels vertically over 16 in o.c. framing; nailing as stated (verify against shear-wall schedule).",
   ["panel_material", "panel_nails", "panel_cut_and_fit_labor"],
   ["openings_cutouts_beyond_waste", "shear_wall_hardware", "weather_barrier", "framing"],
   "CRW-FRM-WOOD",
   [M("ply_15_32", "Plywood sheathing 4x8", F(1), "SF", "1 SF of panel per SF of wall (panel content = 32 SF/sheet)", ["panel"]),
    M("nail_8d", "8d nails: edges 6 in o.c., field 12 in o.c.", F(64, 32), "EA",
      "per sheet: perimeter 24 ft × 12/6 = 48 edge nails + 2 intermediate studs × 8 ft × 12/12 = 16 field nails = 64 per 32 SF = 2.0 per SF",
      ["fastener"])])

wi("WI-FRM-005", "Frame steel-stud partition 3-5/8 in 18 mil @16 in o.c., 10 ft high", "CAT-FRM", "SF",
   {"stud": "3-5/8 in x 1-5/8 in, 18 mil (25 ga), 33 ksi, nonstructural", "track": "3-5/8 in x 1-1/4 in, 18 mil",
    "stud_spacing_in": 16, "wall_height_ft": 10, "screws": "2 x #8 pan-head per stud end", "unit_basis": "SF of wall face area"},
   "Install top and bottom track and friction-fit/screwed studs for a nonstructural steel-stud partition.",
   ["wall_layout", "stud_and_track_materials", "stud_to_track_screws", "install_labor"],
   ["door_and_window_framing", "deflection_track_and_bracing", "blocking_backing", "gypsum_board"],
   "CRW-FRM-STEEL",
   [M("lgs_stud_362_18", "Steel studs", F(12, 16) / 10, "EA", "(12/16) studs per LF ÷ 10 ft wall height = 0.075 studs per SF", ["stud"]),
    M("lgs_track_362_18", "Steel track (top + bottom)", F(2, 10), "LF", "2 LF of track per LF of wall ÷ 10 ft = 0.2 LF per SF", ["track"]),
    M("sd_pan_8", "Self-drilling pan-head screws", F(12, 16) / 10 * 4, "EA", "studs per SF 0.075 × 4 screws (2 per end) = 0.3 per SF", ["fastener"])])

wi("WI-FRM-006", "Install 2x4 flat blocking between studs @16 in o.c.", "CAT-FRM", "LF",
   {"blocking": "2x4 DF-L flat, cut to 14.5 in between studs @16 in o.c.", "nails": "4 x 16d per block (end-nailed)",
    "unit_basis": "LF of blocking line"},
   "Cut and install flat 2x4 blocking in a single horizontal row between studs.",
   ["blocking_materials", "blocking_nails", "blocking_install_labor"],
   ["backing_for_specific_fixtures", "fireblocking_rated", "framing"],
   "CRW-FRM-WOOD",
   [M("lbr_2x4_96", "2x4 blocking stock", F(29, 2) / 16, "LF", "block length 14.5 in ÷ 16 in o.c. = 0.90625 LF of stock per LF of line", ["blocking"]),
    M("nail_16d", "16d nails, 4 per block", F(12, 16) * 4, "EA", "blocks per LF = 12/16 = 0.75 × 4 nails = 3 per LF", ["fastener"])])

# ---- DRYWALL ---------------------------------------------------------------------------------


def screws_per_sf(frame_sp: int, fast_sp: int) -> F:
    """screws per SF for 4x8 board: (48/frame_sp + 1) lines × (96/fast_sp) per line ÷ 32 SF."""
    return (F(48, frame_sp) + 1) * F(96, fast_sp) / 32


def hang(wid, nm, board, screw, frame_sp, fast_sp, framing, location, crew_id="CRW-DRY-HANG", board_desc="", screw_desc=""):
    s = screws_per_sf(frame_sp, fast_sp)
    wi(wid, nm, "CAT-DRY", "SF",
       {"board": board_desc, "layers": 1, "framing": framing, "framing_spacing_in": frame_sp, "fastener_spacing_in": fast_sp,
        "location": location, "sheet_size": "4x8 ft", "unit_basis": "SF of board face installed"},
       "Cut, hang and screw-attach one layer of gypsum board; no taping or finishing.",
       ["board_material", "board_screws", "cut_hang_and_fasten_labor"],
       ["taping_and_finishing", "corner_bead", "openings_cutouts_beyond_waste", "blocking_and_backing", "acoustic_sealant"],
       crew_id,
       [M(board, board_desc, F(1), "SF", "1 SF of board per SF installed (board content = 32 SF per 4x8 sheet)", ["board"]),
        M(screw, screw_desc, s, "EA",
          f"per sheet: (48/{frame_sp} + 1) lines × (96/{fast_sp}) screws per line = {float((F(48, frame_sp) + 1) * F(96, fast_sp))} ÷ 32 SF = {float(s)} per SF",
          ["fastener"])])


hang("WI-DRY-001", "Hang 1/2 in regular gypsum board on wood studs @16 in, walls", "gyp_half_reg_4x8", "ds_coarse_125", 16, 16,
     "wood studs", "walls", board_desc="Gypsum board 1/2 in regular 4x8", screw_desc="Coarse-thread drywall screws #6 x 1-1/4 in")
hang("WI-DRY-002", "Hang 5/8 in Type X gypsum board on wood studs @16 in, walls", "gyp_58_x_4x8", "ds_coarse_1625", 16, 16,
     "wood studs", "walls", board_desc="Gypsum board 5/8 in Type X 4x8", screw_desc="Coarse-thread drywall screws #6 x 1-5/8 in")
hang("WI-DRY-003", "Hang 5/8 in Type X gypsum board on 25-ga steel studs @16 in, walls", "gyp_58_x_4x8", "ds_fine_125", 16, 16,
     "steel studs 18 mil", "walls", crew_id="CRW-DRY-HANG", board_desc="Gypsum board 5/8 in Type X 4x8",
     screw_desc="Fine-thread drywall screws #6 x 1-1/4 in")
hang("WI-DRY-004", "Hang 1/2 in regular gypsum board on wood ceiling framing @16 in", "gyp_half_reg_4x8", "ds_coarse_125", 16, 12,
     "wood joists/furring", "ceilings", board_desc="Gypsum board 1/2 in regular 4x8",
     screw_desc="Coarse-thread drywall screws #6 x 1-1/4 in")
hang("WI-DRY-006", "Hang 1/2 in moisture-resistant gypsum board on wood studs @16 in, walls", "gyp_half_mr_4x8", "ds_coarse_125", 16, 16,
     "wood studs", "walls (wet areas, not tile backer)", board_desc="Moisture/mold-resistant gypsum board 1/2 in 4x8",
     screw_desc="Coarse-thread drywall screws #6 x 1-1/4 in")

wi("WI-DRY-005", "Tape and finish gypsum board to Level 4 (tape + 3 coats compound), walls and ceilings", "CAT-DRY", "SF",
   {"finish_level": "Level 4", "tape": "paper, embedded", "coats": 3, "joint_compound": "all-purpose, standard weight, 4.5 gal pail",
    "joint_layout": "all sheet edges taped (upper bound of joint length)", "unit_basis": "SF of board face finished"},
   "Embed tape and apply three coats of compound with sanding between coats; finish prepared for paint primer.",
   ["joint_tape_material", "joint_compound_material", "taping_finishing_and_sanding_labor"],
   ["corner_bead_and_trim", "texture_finishes", "primer_and_paint", "sanding_abrasives", "board_hanging"],
   "CRW-DRY-FINISH",
   [M("tape_paper_500", "Paper joint tape", F(12, 32), "LF",
      "4x8 sheet: half the 24 ft perimeter is a joint with another sheet = 12 LF ÷ 32 SF = 0.375 LF per SF (upper bound: every edge taped)", ["tape"]),
    M("jnt_ap_std_45", "All-purpose joint compound (manufacturer coverage, 3 coats)", None, "GAL_US",
      "coats_applied / (coverage SF per container × coats in rate) × container size — from product_consumption", ["compound"],
      mode="from_product_consumption", app="level_4_finish_tape_and_3_coats", coats=3)])

wi("WI-INS-001", "Install R-13 kraft-faced fiberglass batt in 2x4 wall cavities @16 in", "CAT-INS", "SF",
   {"batt": "R-13, 3-1/2 in, 15 in wide, kraft-faced", "cavity": "2x4 @16 in o.c.", "unit_basis": "SF of wall area"},
   "Fit and staple kraft-faced batts into 2x4 wall cavities.",
   ["batt_material", "fit_and_staple_labor"],
   ["staples_and_stapling_hardware", "vapor_barrier_sealing", "fireblocking", "openings_and_penetrations_beyond_waste"],
   "CRW-INS",
   [M("bat_fg_r13_kf", "Fiberglass batt R-13 kraft-faced", F(1), "SF",
      "1 SF of batt coverage per SF of wall (coverage per package comes from the product listing)", ["batt"])])

# ---- CONCRETE ----------------------------------------------------------------------------------
cy_per_sf_4 = F(4, 12) / 27
cy_per_sf_6 = F(6, 12) / 27
EXCL_SLAB = ["subgrade_preparation_and_compaction", "edge_forms", "control_and_expansion_joints", "curing", "concrete_pump",
             "testing_and_special_inspection", "sealers_and_hardeners", "excavation_and_haul"]
wi("WI-CON-001", "Place and finish 4 in slab-on-grade, 4000 psi, WWR 6x6-W1.4xW1.4 on chairs, vapor retarder, broom finish", "CAT-CON", "SF",
   {"thickness_in": 4, "concrete": "4000 psi, 3/4 in agg, supplier quote basis", "reinforcement": "6x6-W1.4xW1.4 WWR on 2 in chairs @48 in o.c. each way",
    "vapor_retarder": "10 mil under slab", "finish": "broom", "unit_basis": "SF of slab"},
   "Place, screed, float and broom-finish a 4 in slab over prepared subgrade including vapor retarder and mesh.",
   ["concrete_material", "vapor_retarder_material", "mesh_material", "chair_material", "placing_screeding_finishing_labor",
    "mesh_and_vapor_retarder_placement_labor"],
   EXCL_SLAB, "CRW-CON-FLAT",
   [M("rmx_4000", "Ready-mix concrete 4000 psi", cy_per_sf_4, "CY", "(4 in ÷ 12 in/ft) ft × 1 SF ÷ 27 CF/CY = 1/81 CY per SF", ["concrete"]),
    M("acc_vapor_10mil", "Vapor retarder 10 mil", F(1), "SF", "1 SF per SF of slab (lap allowance belongs in the waste factor)", ["vapor"]),
    M("wwr_66_w14", "Welded wire reinforcement", F(1), "SF", "1 SF per SF of slab (laps in waste factor)", ["mesh"]),
    M("chair_2in", "Mesh chairs @48 in o.c. each way", F(1, 16), "EA", "1 chair per (4 ft × 4 ft) = 1/16 per SF", ["chair"])],
   equipment=[("EQ-PTROWEL", "Power trowel (finishing)")])

wi("WI-CON-002", "Place and finish 6 in reinforced slab-on-grade, 4000 psi, #4 @16 in o.c. each way, vapor retarder, broom finish",
   "CAT-CON", "SF",
   {"thickness_in": 6, "concrete": "4000 psi, 3/4 in agg, supplier quote basis", "reinforcement": "#4 Gr60 @16 in o.c. each way on 3 in chairs @48 in o.c.",
    "vapor_retarder": "10 mil under slab", "finish": "broom", "unit_basis": "SF of slab"},
   "Place, screed, float and broom-finish a 6 in reinforced slab including bar placement and ties.",
   ["concrete_material", "vapor_retarder_material", "rebar_material", "chair_material", "tie_wire_material",
    "placing_screeding_finishing_labor", "rebar_placement_and_tying_labor"],
   EXCL_SLAB, "CRW-CON-FLAT",
   [M("rmx_4000", "Ready-mix concrete 4000 psi", cy_per_sf_6, "CY", "(6 in ÷ 12) ft × 1 SF ÷ 27 = 1/54 CY per SF", ["concrete"]),
    M("acc_vapor_10mil", "Vapor retarder 10 mil", F(1), "SF", "1 SF per SF of slab", ["vapor"]),
    M("reb_4_20", "Rebar #4, both directions", F(2) * F(12, 16), "LF", "2 directions × (12 in/ft ÷ 16 in o.c.) = 1.5 LF per SF (laps in waste factor)", ["rebar"]),
    M("chair_3in", "Bar chairs @48 in o.c. each way", F(1, 16), "EA", "1 per 4 ft × 4 ft = 1/16 per SF", ["chair"]),
    MISSING("tie_wire", "Tie wire at bar intersections", "wire length per tie is not published in any collected source; intersections = 0.5625 per SF",
            ["tie_wire"], "LB")],
   equipment=[("EQ-PTROWEL", "Power trowel (finishing)")])

wi("WI-CON-003", "Place continuous strip footing 18 in x 12 in, 4000 psi, 2 #4 continuous, earth-formed", "CAT-CON", "LF",
   {"width_in": 18, "depth_in": 12, "concrete": "4000 psi, 3/4 in agg, supplier quote basis", "reinforcement": "2 x #4 continuous, Gr60",
    "forming": "earth-formed (neat excavation)", "unit_basis": "LF of footing"},
   "Place and consolidate concrete in an excavated footing trench with two continuous bars on supports.",
   ["concrete_material", "rebar_material", "placing_and_vibrating_labor", "rebar_placement_labor"],
   ["excavation_and_haul", "forms", "bar_supports_and_ties", "anchor_bolts", "keyways", "curing", "testing_and_special_inspection"],
   "CRW-CON-FOOT",
   [M("rmx_4000", "Ready-mix concrete 4000 psi", F(3, 2) * 1 / 27, "CY", "(1.5 ft × 1.0 ft) per LF ÷ 27 CF/CY = 1/18 CY per LF", ["concrete"]),
    M("reb_4_20", "Rebar #4, 2 continuous", F(2), "LF", "2 bars × 1 LF per LF of footing (laps in waste factor)", ["rebar"])],
   equipment=[("EQ-CVIB", "Concrete vibrator")])

wi("WI-CON-004", "Set 1/2 in x 10 in J anchor bolts in wet footing @48 in o.c.", "CAT-CON", "LF",
   {"anchor": "1/2 in x 10 in J-bolt with nut and washer", "spacing_in": 48, "unit_basis": "LF of footing"},
   "Set anchor bolts to template in freshly placed footing.",
   ["anchor_bolt_material", "anchor_bolt_setting_labor"],
   ["template_fabrication", "sill_plate_and_drilling", "washers_beyond_supplied", "testing"],
   "CRW-CON-FOOT",
   [M("acc_anchor_bolt", "J anchor bolts", F(12, 48), "EA", "12 in/ft ÷ 48 in o.c. = 0.25 bolts per LF of footing", ["anchor_bolt"])])

wi("WI-CON-005", "Apply resin-based curing compound to concrete slab, spray, 1 coat", "CAT-CON", "SF",
   {"compound": "resin-based clear, ASTM C309 class, 5 gal pail", "coats": 1, "method": "pump-up sprayer",
    "unit_basis": "SF of slab surface"},
   "Apply a uniform curing membrane immediately after finishing.",
   ["curing_compound_material", "application_labor"],
   ["concrete_placing_and_finishing", "sealers_and_hardeners", "wet_curing_and_blankets", "protection_barricades"],
   "CRW-CON-CURE",
   [M("acc_cure_5gal", "Curing compound (manufacturer coverage)", None, "GAL_US",
      "coats_applied / (coverage SF per gal × coats in rate) — from product_consumption", ["compound"],
      mode="from_product_consumption", app="spray_applied_curing_membrane", coats=1)])

# ---- PAINTING ----------------------------------------------------------------------------------
EXCL_PNT = ["masking_and_protection_materials", "surface_repair_and_patching", "sanding_abrasives", "rollers_brushes_and_small_tools",
            "scaffolding_above_10_ft", "color_matching_charges"]
wi("WI-PNT-001", "Prime new gypsum board, 1 coat PVA primer, roller", "CAT-PNT", "SF",
   {"substrate": "new Level-4 gypsum board", "coats": 1, "product": "PVA drywall primer, 5 gal", "method": "roller", "unit_basis": "SF of surface"},
   "Apply one coat of PVA primer by roller on finished, sanded and dusted gypsum board.", ["primer_material", "primer_application_labor"],
   EXCL_PNT + ["finish_coats"], "CRW-PNT",
   [M("prm_pva_5", "PVA primer (manufacturer spread rate)", None, "GAL_US",
      "coats_applied / (coverage SF per gal × coats in rate) — from product_consumption", ["primer"],
      mode="from_product_consumption", app="new_drywall_primer", coats=1)])
wi("WI-PNT-002", "Paint interior walls, 2 coats eggshell acrylic latex over primed gypsum board, roller", "CAT-PNT", "SF",
   {"substrate": "primed gypsum board", "coats": 2, "product": "interior acrylic latex eggshell, 5 gal", "method": "roller (cut-in by brush)",
    "unit_basis": "SF of wall surface"},
   "Cut in and roll two finish coats on primed walls.", ["wall_finish_material", "wall_finish_application_labor"],
   EXCL_PNT + ["primer"], "CRW-PNT",
   [M("pnt_int_egg_5", "Eggshell wall paint (manufacturer spread rate)", None, "GAL_US",
      "coats_applied / (coverage SF per gal × coats in rate) — from product_consumption", ["finish_paint"],
      mode="from_product_consumption", app="interior_finish_over_primed_drywall", coats=2)])
wi("WI-PNT-003", "Paint interior ceilings, 2 coats flat ceiling paint over primed gypsum board, roller", "CAT-PNT", "SF",
   {"substrate": "primed gypsum board", "coats": 2, "product": "interior ceiling paint flat, 5 gal", "method": "roller", "unit_basis": "SF of ceiling"},
   "Roll two finish coats on primed ceilings.", ["ceiling_finish_material", "ceiling_finish_application_labor"],
   EXCL_PNT + ["primer"], "CRW-PNT",
   [M("pnt_ceil_flat_5", "Flat ceiling paint (manufacturer spread rate)", None, "GAL_US",
      "coats_applied / (coverage SF per gal × coats in rate) — from product_consumption", ["finish_paint"],
      mode="from_product_consumption", app="interior_finish_over_primed_drywall", coats=2)])
wi("WI-PNT-004", "Caulk trim and joints with paintable acrylic latex, 1/4 in x 1/4 in bead", "CAT-PNT", "LF",
   {"caulk": "paintable siliconized acrylic latex, 10.1 fl oz cartridge", "bead": "1/4 in x 1/4 in", "unit_basis": "LF of joint"},
   "Gun and tool a 1/4 in bead at trim-to-wall joints.", ["caulk_material", "caulking_labor"],
   EXCL_PNT + ["joint_backer_rod", "surface_repair_and_patching"], "CRW-PNT",
   [M("sup_caulk", "Acrylic latex caulk", F(3, 4) / 231, "GAL_US",
      "bead volume 0.25 in × 0.25 in × 12 in = 0.75 in³ per LF ÷ 231 in³ per US gal = 0.003247 gal per LF", ["caulk"])])

# ---- HVAC ---------------------------------------------------------------------------------------
EXCL_HVAC = ["power_wiring_and_electrical_connections", "permits_and_inspections", "startup_testing_and_balancing_report",
             "refrigerant_charge_beyond_factory", "demolition_of_existing_equipment", "crane_or_rigging", "structural_supports_and_curbs"]
wi("WI-HVC-001", "Install 3-ton split-system AC condenser on pad with 25 ft line set, disconnect and whip", "CAT-HVC", "EA",
   {"capacity_tons": 3.0, "type": "AC condenser, split outdoor", "refrigerant": "R-454B", "line_set": "3/8 x 7/8 in, 25 ft insulated",
    "pad": "36x36x3 in composite", "disconnect": "60 A non-fused with 6 ft whip", "unit_basis": "EA complete outdoor installation"},
   "Set condenser on pad, run and braze line set, mount disconnect and whip, evacuate and release charge.",
   ["condenser_equipment", "pad_material", "line_set_material", "disconnect_and_whip_material", "set_connect_evacuate_labor"],
   EXCL_HVAC + ["indoor_unit_and_coil", "thermostat_and_controls", "ductwork"],
   "CRW-HVAC-SPLIT",
   [M("eqp_ac_30", "AC condenser 3 ton", F(1), "EA", "1 condenser per installation", ["condenser"]),
    M("acc_pad_36", "Condenser pad", F(1), "EA", "1 pad per installation", ["pad"]),
    M("ref_ls_38_78_25", "Line set 25 ft", F(1), "EA", "1 line set per installation (additional length excluded)", ["line_set"]),
    M("ctl_disc_60", "AC disconnect 60 A", F(1), "EA", "1 per installation", ["disconnect"]),
    M("ctl_whip_6", "AC whip 6 ft", F(1), "EA", "1 per installation", ["whip"])],
   equipment=[("EQ-HVACVAC", "Refrigerant vacuum pump")])
wi("WI-HVC-002", "Install 80,000 Btu/h gas furnace with 3-ton cased evaporator coil and programmable thermostat", "CAT-HVC", "EA",
   {"furnace": "80,000 Btu/h input, 80% AFUE, upflow", "coil": "3 ton cased A-coil, R-454B", "thermostat": "programmable 24 V 1H/1C",
    "unit_basis": "EA complete indoor installation"},
   "Set furnace and coil, connect supply/return plenums at the equipment collars, mount and wire thermostat to the equipment terminals.",
   ["furnace_equipment", "coil_equipment", "thermostat_material", "set_connect_labor"],
   EXCL_HVAC + ["gas_piping", "flue_venting", "condensate_drain_and_pump", "plenum_fabrication", "outdoor_unit", "ductwork"],
   "CRW-HVAC-SPLIT",
   [M("eqp_furn_80", "Gas furnace 80 kBtu/h", F(1), "EA", "1 furnace per installation", ["furnace"]),
    M("eqp_coil_30", "Evaporator coil 3 ton", F(1), "EA", "1 coil per installation", ["coil"]),
    M("ctl_tstat_prog", "Programmable thermostat", F(1), "EA", "1 thermostat per installation", ["thermostat"])])
wi("WI-HVC-003", "Install 8 in insulated flexible duct R-6, supported and connected", "CAT-HVC", "LF",
   {"duct": "8 in insulated flex, R-6, 25 ft lengths", "connections": "mastic + mechanical fastener at each end of a 25 ft length",
    "unit_basis": "LF of installed duct"},
   "Cut, stretch, connect and support flexible duct between plenum/boot connections.",
   ["duct_material", "install_labor"],
   EXCL_HVAC + ["boots_registers_and_grilles", "plenum_fabrication", "hanger_strap_material", "sealant_mastic_material", "foil_tape_material"],
   "CRW-HVAC-DUCT",
   [M("duc_flex_8", "Insulated flex duct 8 in", F(1), "LF", "1 LF of duct per LF installed (cut-off waste in waste factor)", ["duct"])])

assert len(WORK_ITEMS) == 25, len(WORK_ITEMS)

# ====================================================================================== ASSEMBLIES
EXCL_ASM = ["corners_and_intersections", "openings_headers_and_door_frames", "base_trim", "electrical_and_mechanical_rough_in",
            "mobilization", "daily_cleanup_and_protection", "overhead_and_profit"]
ASSEMBLIES = [
    ("ASM-WALL-001", "Interior partition, 2x4 wood studs @16 in, 8 ft, 1/2 in regular gypsum each side, Level 4, primer + 2 eggshell coats each side",
     "CAT-FRM", "SF",
     {"framing": "2x4 DF-L studs @16 in o.c., 1 bottom + 2 top plates", "height_ft": 8, "board": "1/2 in regular, 1 layer each side",
      "finish": "Level 4 each side", "paint": "1 PVA primer + 2 eggshell coats each side", "insulation": "none", "unit_basis": "SF of wall (L x H)"},
     [("WI-FRM-001", 1, "1 SF of wall per SF of wall"), ("WI-DRY-001", 2, "2 faces × 1 SF of board per SF of wall"),
      ("WI-DRY-005", 2, "2 faces × 1 SF of finish per SF of wall"), ("WI-PNT-001", 2, "2 faces primed"), ("WI-PNT-002", 2, "2 faces painted")]),
    ("ASM-WALL-002", "Interior partition as WALL-001 plus R-13 kraft-faced batt in the cavity", "CAT-FRM", "SF",
     {"framing": "2x4 DF-L studs @16 in o.c., 1 bottom + 2 top plates", "height_ft": 8, "board": "1/2 in regular, 1 layer each side",
      "finish": "Level 4 each side", "paint": "1 PVA primer + 2 eggshell coats each side", "insulation": "R-13 kraft-faced batt", "unit_basis": "SF of wall (L x H)"},
     [("WI-FRM-001", 1, "1 SF per SF"), ("WI-INS-001", 1, "1 SF of cavity per SF of wall"), ("WI-DRY-001", 2, "2 faces"),
      ("WI-DRY-005", 2, "2 faces"), ("WI-PNT-001", 2, "2 faces"), ("WI-PNT-002", 2, "2 faces")]),
    ("ASM-WALL-003", "Interior partition, 2x6 wood studs @16 in, 8 ft, 5/8 in Type X each side, Level 4, primer + 2 eggshell coats each side",
     "CAT-FRM", "SF",
     {"framing": "2x6 DF-L studs @16 in o.c., 1 bottom + 2 top plates", "height_ft": 8, "board": "5/8 in Type X, 1 layer each side",
      "finish": "Level 4 each side", "paint": "1 PVA primer + 2 eggshell coats each side", "insulation": "none", "unit_basis": "SF of wall (L x H)"},
     [("WI-FRM-002", 1, "1 SF per SF"), ("WI-DRY-002", 2, "2 faces"), ("WI-DRY-005", 2, "2 faces"), ("WI-PNT-001", 2, "2 faces"),
      ("WI-PNT-002", 2, "2 faces")]),
    ("ASM-WALL-004", "Steel-stud partition 3-5/8 in 18 mil @16 in, 10 ft, 5/8 in Type X each side, Level 4, primer + 2 eggshell coats each side",
     "CAT-FRM", "SF",
     {"framing": "steel studs 3-5/8 in 18 mil @16 in o.c., top and bottom track", "height_ft": 10, "board": "5/8 in Type X, 1 layer each side, fine-thread screws",
      "finish": "Level 4 each side", "paint": "1 PVA primer + 2 eggshell coats each side", "insulation": "none", "unit_basis": "SF of wall (L x H)"},
     [("WI-FRM-005", 1, "1 SF per SF"), ("WI-DRY-003", 2, "2 faces"), ("WI-DRY-005", 2, "2 faces"), ("WI-PNT-001", 2, "2 faces"),
      ("WI-PNT-002", 2, "2 faces")]),
    ("ASM-WALL-005", "Exterior wall shell: 2x6 wood studs @16 in, 8 ft, with 15/32 in plywood sheathing on the outside face",
     "CAT-FRM", "SF",
     {"framing": "2x6 DF-L studs @16 in o.c., 1 bottom + 2 top plates", "height_ft": 8, "sheathing": "15/32 in plywood CD Exposure 1, 8d @6/12",
      "weather_barrier": "excluded", "cladding": "excluded", "unit_basis": "SF of wall (L x H)"},
     [("WI-FRM-002", 1, "1 SF per SF"), ("WI-FRM-004", 1, "1 SF of sheathing per SF of wall")]),
    ("ASM-CEIL-001", "Gypsum ceiling: 1/2 in regular board on wood framing, Level 4, primer + 2 coats flat ceiling paint",
     "CAT-DRY", "SF",
     {"substrate": "wood joists/furring @16 in o.c. (framing excluded)", "board": "1/2 in regular, 1 layer", "fastener_spacing_in": 12,
      "finish": "Level 4", "paint": "1 PVA primer + 2 flat ceiling coats", "unit_basis": "SF of ceiling"},
     [("WI-DRY-004", 1, "1 SF per SF"), ("WI-DRY-005", 1, "1 SF per SF"), ("WI-PNT-001", 1, "1 coat primer"), ("WI-PNT-003", 1, "2 finish coats (inside item)")]),
    ("ASM-SLAB-001", "Slab-on-grade 4 in, 4000 psi, WWR on chairs, vapor retarder, broom finish, spray curing compound", "CAT-CON", "SF",
     {"thickness_in": 4, "concrete": "4000 psi", "reinforcement": "6x6-W1.4xW1.4 WWR", "vapor_retarder": "10 mil", "finish": "broom",
      "curing": "resin-based spray membrane", "subgrade": "excluded", "unit_basis": "SF of slab"},
     [("WI-CON-001", 1, "1 SF per SF"), ("WI-CON-005", 1, "1 SF per SF")]),
    ("ASM-SLAB-002", "Slab-on-grade 6 in, 4000 psi, #4 @16 in each way, vapor retarder, broom finish, spray curing compound", "CAT-CON", "SF",
     {"thickness_in": 6, "concrete": "4000 psi", "reinforcement": "#4 Gr60 @16 in o.c. each way", "vapor_retarder": "10 mil", "finish": "broom",
      "curing": "resin-based spray membrane", "subgrade": "excluded", "unit_basis": "SF of slab"},
     [("WI-CON-002", 1, "1 SF per SF"), ("WI-CON-005", 1, "1 SF per SF")]),
    ("ASM-FTG-001", "Continuous footing 18 in x 12 in, 4000 psi, 2 #4 continuous, J anchor bolts @48 in", "CAT-CON", "LF",
     {"width_in": 18, "depth_in": 12, "concrete": "4000 psi", "reinforcement": "2 x #4 continuous", "anchors": "1/2 in x 10 in J-bolts @48 in o.c.",
      "forming": "earth-formed", "unit_basis": "LF of footing"},
     [("WI-CON-003", 1, "1 LF per LF"), ("WI-CON-004", 1, "1 LF per LF")]),
    ("ASM-HVAC-001", "Residential 3-ton split-system install: outdoor AC condenser set + 80 kBtu/h furnace and coil + 50 LF 8 in flex duct",
     "CAT-HVC", "EA",
     {"capacity_tons": 3.0, "outdoor": "AC condenser 3 ton with 25 ft line set, pad, disconnect, whip", "indoor": "80 kBtu/h gas furnace + 3 ton coil + programmable thermostat",
      "duct": "50 LF of 8 in insulated flex", "unit_basis": "EA system"},
     [("WI-HVC-001", 1, "1 outdoor set"), ("WI-HVC-002", 1, "1 indoor set"), ("WI-HVC-003", 50, "50 LF of duct (spec parameter)")]),
]
assert len(ASSEMBLIES) == 10


# ====================================================================================== OUTPUT
def dstr(f: F) -> Decimal:
    return (Decimal(f.numerator) / Decimal(f.denominator)).quantize(Decimal("0.0000000001"))


def main() -> int:
    schema = parse_schema()
    db = Database()

    # ---- which spec lines are referenced by work items (priority 1)
    used = {c["mat"] for w in WORK_ITEMS for c in w["comps"] if c["mat"]}
    unused = set(MATS) - used
    for key, m in MATS.items():
        db.add("capture_targets", {
            "target_id": make_id("TGT", "material", key), "target_kind": "material", "category_id": m["cat"],
            "description": m["desc"], "spec_attributes": m["attrs"], "spec_key": m["spec_key"],
            "preferred_sale_unit": m["sale"], "pilot_priority": 1 if key in used else 2,
            "required_by": ", ".join(sorted(w["id"] for w in WORK_ITEMS if any(c["mat"] == key for c in w["comps"]))) or None,
            "recommended_source_ids": [], "status": "open", "blocked_reason": None,
            "notes": "Capture ≥1 real SKU matching EVERY required attribute (price per sale unit, pack content, ZIP/store, date, availability). "
                     "Retail terms: see source register; capture only where site rules allow."})

    # ---- non-material targets
    trades_used = ["TR-CARP", "TR-LAB", "TR-DRYW", "TR-TAPE", "TR-PNT", "TR-HVAC", "TR-CEM", "TR-REB", "TR-INS", "TR-SHM", "TR-OPR"]
    for t in trades_used:
        db.add("capture_targets", {"target_id": make_id("TGT", "labor_stat", t), "target_kind": "labor", "category_id": None,
                                   "description": f"Statistical wage (mean and median) for {t}, Los Angeles-Long Beach-Glendale MD (REG-MD-31084)",
                                   "spec_attributes": {"trade_code": t, "statistic": ["mean", "median"], "region_id": "REG-MD-31084"},
                                   "spec_key": None, "preferred_sale_unit": None, "pilot_priority": 1, "required_by": "all labor lines",
                                   "recommended_source_ids": ["SRC-BLS-OEWS-MAY2025", "SRC-BLS-OE-FLATFILES", "SRC-EDD-OEWS-LMI"],
                                   "status": "open", "blocked_reason": "BLS/EDD hosts blocked by sandbox network policy; run the connector from an unrestricted host",
                                   "notes": "OEWS wages exclude employer-paid benefits; burden items are separate targets."})
        db.add("capture_targets", {"target_id": make_id("TGT", "labor_pw", t), "target_kind": "labor", "category_id": None,
                                   "description": f"Prevailing wage determination (base + fringe breakdown) for {t}, Southern California — PUBLIC WORKS context only",
                                   "spec_attributes": {"trade_code": t, "use_context": "public_works_only"}, "spec_key": None,
                                   "preferred_sale_unit": None, "pilot_priority": 3, "required_by": "public-works pricing only",
                                   "recommended_source_ids": ["SRC-DIR-PWD-GENERAL-2026-2", "SRC-SAM-DBA-WAGE-DETS"], "status": "open",
                                   "blocked_reason": "dir.ca.gov / sam.gov blocked by sandbox network policy", "notes": "PDF tables: extract and spot-check against page images."})
    for btype, desc, srcs, prio in [
            ("employer_benefits", "Employer-paid benefits ratio for construction (ECEC) or company benefit cost", ["SRC-BLS-ECEC"], 1),
            ("futa", "FUTA employer rate and wage base (IRS primary source)", ["SRC-IRS-PUB15-2026"], 1),
            ("state_ui", "California UI employer rate (company-specific experience rate) and wage base", ["SRC-EDD-PAYROLL-RATES-2026"], 1),
            ("workers_comp", "Workers' compensation rate per $100 payroll by trade class (insurer-quoted; WCIRB pure premiums are advisory)",
             ["SRC-WCIRB-CLASS-USRP", "SRC-CDI-WC-ADVISORY-2026-09"], 1)]:
        db.add("capture_targets", {"target_id": make_id("TGT", "burden", btype), "target_kind": "burden", "category_id": None,
                                   "description": desc, "spec_attributes": {"burden_type": btype}, "spec_key": None,
                                   "preferred_sale_unit": None, "pilot_priority": prio, "required_by": "loaded labor rates",
                                   "recommended_source_ids": srcs, "status": "open", "blocked_reason": None,
                                   "notes": "Company-specific values (experience mod, UI rate) must come from the company's own notices."})
    for etype, name in [("EQ-PTROWEL", "power trowel"), ("EQ-CVIB", "concrete vibrator"), ("EQ-HVACVAC", "refrigerant vacuum pump")]:
        db.add("capture_targets", {"target_id": make_id("TGT", "equipment", etype), "target_kind": "equipment", "category_id": None,
                                   "description": f"Hourly or daily rate for {name} in Southern California; state operator/fuel treatment",
                                   "spec_attributes": {"equipment_type_code": etype}, "spec_key": None, "preferred_sale_unit": None,
                                   "pilot_priority": 2, "required_by": ", ".join(w["id"] for w in WORK_ITEMS if any(e[0] == etype for e in w["equipment"])),
                                   "recommended_source_ids": ["SRC-CALTRANS-EQRR-2026-27", "SRC-USACE-EP1110-1-8-VOL07-2016"], "status": "open",
                                   "blocked_reason": None, "notes": "Rental-company rates: human capture only, per site terms."})
    for w in WORK_ITEMS:
        db.add("capture_targets", {"target_id": make_id("TGT", "productivity", w["id"]), "target_kind": "productivity",
                                   "category_id": w["cat"], "description": f"Labor norm (crew, shift, daily output, conditions) for: {w['name']}",
                                   "spec_attributes": {"work_item_id": w["id"], "output_unit": w["unit"]}, "spec_key": None,
                                   "preferred_sale_unit": None, "pilot_priority": 1, "required_by": w["id"],
                                   "recommended_source_ids": ["SRC-NAVFAC-P405-1996", "SRC-JOINT-TM3-34-41-2021", "SRC-UTCTR-HYPRIS-0-4416", "SRC-DTIC-AD0666236"],
                                   "status": "open", "blocked_reason": None,
                                   "notes": "Record document, edition, page, table, crew, shift and included/excluded operations; check page image."})
    for code, name in [("PPI", "BLS PPI series for lumber, gypsum, ready-mix, steel, paint — identifiers to verify"),
                       ("ECI", "BLS ECI construction wages/total compensation values")]:
        db.add("capture_targets", {"target_id": make_id("TGT", "index", code), "target_kind": "index", "category_id": None,
                                   "description": name, "spec_attributes": {}, "spec_key": None, "preferred_sale_unit": None,
                                   "pilot_priority": 2, "required_by": "time adjustment of old prices", "recommended_source_ids": ["SRC-BLS-PPI", "SRC-BLS-ECI", "SRC-BLS-API-V2"],
                                   "status": "open", "blocked_reason": "values must be ingested from bls.gov, not FRED (FRED terms)", "notes": None})
    db.add("capture_targets", {"target_id": make_id("TGT", "other", "waste"), "target_kind": "other", "category_id": None,
                               "description": "Waste/loss factors per material line (cut loss, laps, spillage) with a stated source or approved assumption",
                               "spec_attributes": {}, "spec_key": None, "preferred_sale_unit": None, "pilot_priority": 1,
                               "required_by": "every material component", "recommended_source_ids": [], "status": "open",
                               "blocked_reason": None, "notes": "No universal percentage is assumed; each line needs its own basis."})
    for key, app in [("jnt_ap_std_45", "level_4_finish_tape_and_3_coats"), ("prm_pva_5", "new_drywall_primer"),
                     ("pnt_int_egg_5", "interior_finish_over_primed_drywall"), ("pnt_ceil_flat_5", "interior_finish_over_primed_drywall"),
                     ("acc_cure_5gal", "spray_applied_curing_membrane")]:
        db.add("capture_targets", {"target_id": make_id("TGT", "consumption", key, app), "target_kind": "other", "category_id": MATS[key]["cat"],
                                   "description": f"Manufacturer coverage for {MATS[key]['desc']} — application '{app}' with film thickness, coats and conditions",
                                   "spec_attributes": {"application": app}, "spec_key": MATS[key]["spec_key"], "preferred_sale_unit": None,
                                   "pilot_priority": 1, "required_by": ", ".join(w["id"] for w in WORK_ITEMS if any(c["mat"] == key and c["mode"] == "from_product_consumption" for c in w["comps"])),
                                   "recommended_source_ids": ["SRC-USG-JOINT-COMPOUND-FAQ", "SRC-DUNNEDWARDS-PDS-LIBRARY"], "status": "open",
                                   "blocked_reason": None, "notes": "Needs a SKU-bound product row first; then product_consumption."})

    # ---- crews (missing) and productivity (missing)
    for c in CREWS.values():
        db.add("crews", {"crew_id": c["crew_id"], "name": c["name"], "description": c["description"], "category_id": c["category_id"],
                         "shift_hours": None, "source_id": None, "source_locator": None, "assumption_basis": None, "origin": "missing",
                         "review_status": "unreviewed", "notes": "Placeholder: composition not found in any collected source."})
    for w in WORK_ITEMS:
        db.add("productivity_observations", {
            "productivity_id": make_id("PRO", w["id"]), "work_item_id": w["id"], "operation_text": w["labor_desc"],
            "category_id": w["cat"], "output_unit_id": w["unit"], "crew_id": w["crew"],
            "missing_reason": ("No verified labor-hour norm located yet. Candidate free sources (contents NOT verified): "
                               "NAVFAC P-405 (1996), TM 3-34.41 (2021), TxDOT HyPRIS, FHWA T 5080.15. See backlog."),
            "origin": "missing", "review_status": "unreviewed",
            "notes": "origin=missing: no value is stored and none is inferred from prices."})

    # ---- work items and components
    for w in WORK_ITEMS:
        db.add("work_items", {"work_item_id": w["id"], "version": 1, "name": w["name"], "category_id": w["cat"],
                              "spec_attributes": w["spec"], "output_unit_id": w["unit"], "description": w["desc"],
                              "included_scope": w["included"], "excluded_scope": w["excluded"], "conditions": w["conditions"],
                              "status": "defined", "valid_from": VALID_FROM, "supersedes_version": None, "definition_basis": BASIS,
                              "origin": "assumed", "review_status": "unreviewed", "notes": None})
        line = 0
        pid = make_id("PRO", w["id"])
        for c in w["comps"]:
            line += 1
            spec = MATS[c["mat"]]["spec_key"]
            qty_fixed = c["qty"] is not None and c["mode"] == "fixed"
            db.add("work_item_components", {
                "component_id": make_id("WIC", w["id"], line), "work_item_id": w["id"], "work_item_version": 1, "line_no": line,
                "component_kind": c["kind"], "description": c["desc"], "product_spec_key": spec, "product_id": None,
                "qty_mode": c["mode"], "qty_per_unit": dstr(c["qty"]) if qty_fixed else None,
                "qty_unit_id": c["unit"] if (qty_fixed or c["mode"] == "from_product_consumption") else c["unit"],
                "qty_formula": c["formula"] if qty_fixed or c["mode"] == "from_product_consumption" else None,
                "qty_origin": c["origin"] if c["mode"] == "fixed" else "derived", "waste_factor": None, "waste_origin": None,
                "waste_basis": None, "crew_id": None, "productivity_id": None, "consumption_application": c["app"],
                "coats_applied": Decimal(str(c["coats"])) if c["coats"] else None, "cost_tags": c["tags"], "is_optional": False,
                "notes": ("quantity not derivable from collected sources" if c["origin"] == "missing" else None)})
        line += 1
        db.add("work_item_components", {
            "component_id": make_id("WIC", w["id"], line), "work_item_id": w["id"], "work_item_version": 1, "line_no": line,
            "component_kind": "labor", "description": f"Labor: {w['labor_desc']}", "product_spec_key": None, "product_id": None,
            "qty_mode": "from_productivity", "qty_per_unit": None, "qty_unit_id": "HR", "qty_formula": None, "qty_origin": "missing",
            "waste_factor": None, "waste_origin": None, "waste_basis": None, "crew_id": w["crew"], "productivity_id": pid,
            "consumption_application": None, "coats_applied": None, "cost_tags": ["labor"], "is_optional": False,
            "notes": "labor cost/unit = crew labor cost per shift ÷ daily output"})
        for etype, ename in w["equipment"]:
            line += 1
            db.add("work_item_components", {
                "component_id": make_id("WIC", w["id"], line), "work_item_id": w["id"], "work_item_version": 1, "line_no": line,
                "component_kind": "equipment", "description": f"Equipment: {ename} ({etype})", "product_spec_key": None, "product_id": None,
                "qty_mode": "from_productivity", "qty_per_unit": None, "qty_unit_id": "HR", "qty_formula": None, "qty_origin": "missing",
                "waste_factor": None, "waste_origin": None, "waste_basis": None, "crew_id": w["crew"], "productivity_id": pid,
                "consumption_application": None, "coats_applied": None, "cost_tags": ["equipment_" + etype.lower()], "is_optional": False,
                "notes": "equipment cost/unit = crew equipment cost per shift ÷ daily output; operator accounted in labor OR rate, never both"})

    # ---- assemblies
    for aid, name, cat, unit, spec, comps in ASSEMBLIES:
        db.add("assemblies", {"assembly_id": aid, "version": 1, "name": name, "category_id": cat, "spec_attributes": spec,
                              "output_unit_id": unit, "description": name, "included_scope": [], "excluded_scope": EXCL_ASM,
                              "conditions": NORMAL, "status": "defined", "valid_from": VALID_FROM, "supersedes_version": None,
                              "definition_basis": BASIS, "origin": "assumed", "review_status": "unreviewed", "notes": None})
        for i, (wid, qty, why) in enumerate(comps, 1):
            wiu = next(w["unit"] for w in WORK_ITEMS if w["id"] == wid)
            db.add("assembly_components", {"assembly_component_id": make_id("ASC", aid, i), "assembly_id": aid, "assembly_version": 1,
                                           "line_no": i, "work_item_id": wid, "work_item_version": 1,
                                           "qty_per_assembly_unit": Decimal(qty), "qty_unit_id": wiu, "qty_formula": why,
                                           "qty_origin": "derived", "cost_tags": [], "notes": None})

    # ---- write only the tables owned by this generator
    owned = ("capture_targets", "crews", "productivity_observations", "work_items", "work_item_components", "assemblies",
             "assembly_components")
    for t in owned:
        use = [c for c in schema[t] if not c.generated]
        with open(CSV_DIR / f"{t}.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh, lineterminator="\n")
            wr.writerow([c.name for c in use])
            for r in db[t]:
                wr.writerow([format_value(c, r.get(c.name)) for c in use])
    print({t: len(db[t]) for t in owned}, "| material spec lines:", len(MATS), "priority-1:", len(used), "unused-by-pilot:", len(unused))
    return 0


if __name__ == "__main__":
    sys.exit(main())
