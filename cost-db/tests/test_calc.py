"""Engine tests. Inputs are SYNTHETIC (see fixtures/synthetic.py); expected values are computed here independently."""
import unittest
from datetime import date
from decimal import Decimal as D

from costdb.calc import Engine, RunParams, apply_markup, margin_to_markup, markup_to_margin, median
from costdb.ids import SpecError, spec_key
from costdb.units import UnitError, Units
from tests.fixtures import synthetic as S

WI = S.WI
EXPECTED_DRY001 = D("0.997875")


def comp(db, wi, needle):
    return next(c for c in db["work_item_components"] if c["work_item_id"] == wi and needle in (c["product_spec_key"] or c["description"]))


class UnitsTest(unittest.TestCase):
    def setUp(self):
        self.u = Units(S.real_db()["units"])

    def test_exact_factors(self):
        self.assertEqual(self.u.convert(D(1), "SY", "SF"), D(9))
        self.assertEqual(self.u.convert(D(1), "CY", "CF"), D(27))
        self.assertEqual(self.u.convert(D(1), "TON_SHORT", "LB"), D(2000))
        self.assertEqual(self.u.convert(D(1), "TON_LONG", "LB"), D(2240))
        self.assertAlmostEqual(float(self.u.convert(D(1), "TON_METRIC", "LB")), 2204.62262185, places=6)
        self.assertAlmostEqual(float(self.u.convert(D(1), "GAL_US", "CF")), 231 / 1728, places=12)
        self.assertAlmostEqual(float(self.u.convert(D(1), "GAL_IMP", "GAL_US")), 1.2009499255, places=9)
        self.assertAlmostEqual(float(self.u.convert(D(100), "SF", "SY")), 100 / 9, places=10)

    def test_ton_and_gal_are_always_qualified(self):
        for bad in ("TON", "GAL"):
            self.assertNotIn(bad, self.u)
        self.assertEqual(self.u.dimension("TON_REFRIG"), "cooling_capacity")

    def test_incompatible_conversions_refused(self):
        for a, b in (("TON_REFRIG", "LB"), ("TON_SHORT", "TON_REFRIG"), ("SF", "LF"), ("DAY", "HR"), ("HR", "DAY"), ("EA", "LF")):
            with self.assertRaises(UnitError, msg=f"{a}->{b}"):
                self.u.convert(D(1), a, b)


class SpecKeyTest(unittest.TestCase):
    REQ = ["a", "b"]

    def test_normalisation(self):
        self.assertEqual(spec_key("C", {"a": "0.50", "b": " X "}, self.REQ), spec_key("C", {"a": 0.5, "b": "x"}, self.REQ))

    def test_missing_attribute_is_never_guessed(self):
        for bad in ({"a": 1}, {"a": 1, "b": ""}, {"a": 1, "b": "unknown"}, {"a": 1, "b": "n/a"}):
            with self.assertRaises(SpecError):
                spec_key("C", bad, self.REQ)

    def test_material_differences_make_different_keys(self):
        db = S.real_db()
        m = S.pilot.MATS
        self.assertNotEqual(m["gyp_half_reg_4x8"]["spec_key"], m["gyp_58_x_4x8"]["spec_key"])        # thickness / fire rating
        self.assertNotEqual(m["gyp_half_reg_4x8"]["spec_key"], m["gyp_half_reg_4x12"]["spec_key"])    # length
        self.assertNotEqual(m["ds_coarse_125"]["spec_key"], m["ds_fine_125"]["spec_key"])             # thread
        self.assertNotEqual(m["lgs_stud_362_18"]["spec_key"], m["lgs_stud_362_30"]["spec_key"])       # gauge
        self.assertNotEqual(m["pnt_int_egg_5"]["spec_key"], m["pnt_int_egg_1"]["spec_key"])           # container
        self.assertEqual(len({v["spec_key"] for v in m.values()}), len(m), "every spec line must be unique")


class UnitCostTest(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        self.eng = Engine(self.db)

    def test_hand_computed_total(self):
        r = self.eng.unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        self.assertEqual(r.run["direct_cost_total"], EXPECTED_DRY001)
        self.assertEqual(r.run["material_cost"], D("0.447875"))
        self.assertEqual(r.run["labor_cost"], D("0.550000"))
        self.assertEqual(r.run["equipment_cost"], D("0.000000"))
        by_kind = {ln["line_kind"]: ln for ln in r.lines}
        self.assertIn("person-hours/unit = 3×8/1600", by_kind["labor"]["formula"])
        self.assertEqual(sum(ln["extended_cost"] for ln in r.lines), D("0.9978750000"))

    def test_every_line_has_formula_and_traceable_inputs(self):
        r = self.eng.unit_cost(WI, 1, S.params())
        for ln in r.lines:
            self.assertTrue(ln["formula"])
            self.assertTrue(ln["inputs"], f"line {ln['line_no']} has no input references")
        mat = [ln for ln in r.lines if ln["line_kind"] == "material"][0]
        self.assertEqual(mat["inputs"][-1]["table"], "price_observations")
        self.assertIn(mat["inputs"][-1]["id"], {"TEST-OBS-BOARDA", "TEST-OBS-SCREW"})

    def test_retail_flag_and_tax_flags(self):
        r = self.eng.unit_cost(WI, 1, S.params())
        w = " ".join(r.run["warnings"])
        self.assertIn("RETAIL_PRICE_NOT_CONTRACTOR_COST", w)

    def test_reproducible_run_id(self):
        a = self.eng.unit_cost(WI, 1, S.params()).run["run_id"]
        b = Engine(S.clone(self.db)).unit_cost(WI, 1, S.params()).run["run_id"]
        self.assertEqual(a, b)
        o = next(x for x in self.db["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
        o["price_amount"] = D("13.00")
        self.assertNotEqual(a, Engine(self.db).unit_cost(WI, 1, S.params()).run["run_id"])

    def test_unreviewed_inputs_not_used_in_strict(self):
        o = next(x for x in self.db["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
        o["review_status"] = "unreviewed"
        r = self.eng.unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertIsNone(r.run["direct_cost_total"])
        self.assertIn("PRICE_MISSING", {m["code"] for m in r.run["missing_inputs"]})
        r2 = self.eng.unit_cost(WI, 1, S.params(min_review="unreviewed"))
        self.assertEqual(r2.status, "complete")

    def test_flagged_and_rejected_never_used(self):
        o = next(x for x in self.db["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
        for st in ("flagged", "rejected"):
            o["review_status"] = st
            self.assertEqual(self.eng.unit_cost(WI, 1, S.params(min_review="unreviewed")).status, "incomplete")

    def test_synthetic_inputs_blocked_unless_allowed(self):
        r = self.eng.unit_cost(WI, 1, S.params(allow_synthetic=False))
        self.assertEqual(r.status, "incomplete")

    def test_prohibited_source_never_used(self):
        for s in self.db["sources"]:
            if s["source_id"] == S.SRC:
                s["reuse_status"] = "prohibited"
        self.assertEqual(self.eng.unit_cost(WI, 1, S.params()).status, "incomplete")

    def test_promo_and_wrong_channel_excluded(self):
        o = next(x for x in self.db["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
        o["promo_flag"] = True
        self.assertEqual(self.eng.unit_cost(WI, 1, S.params()).status, "incomplete")
        o["promo_flag"] = False; o["price_channel"] = "manufacturer_msrp"
        self.assertEqual(self.eng.unit_cost(WI, 1, S.params()).status, "incomplete")

    def test_missing_waste_blocks_result(self):
        comp(self.db, WI, "CAT-DRY-BRD")["waste_factor"] = None
        r = self.eng.unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertIn("WASTE_MISSING", {m["code"] for m in r.run["missing_inputs"]})

    def test_assumed_waste_refused_in_strict_and_flagged_in_assumption_mode(self):
        c = comp(self.db, WI, "CAT-DRY-BRD")
        c["waste_origin"] = "assumed"
        r = self.eng.unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertIn("WASTE_ASSUMED", {m["code"] for m in r.run["missing_inputs"]})
        r2 = self.eng.unit_cost(WI, 1, S.params(mode="with_assumptions"))
        self.assertEqual(r2.status, "incomplete")      # an assumption mode still needs an APPROVED assumption row
        c["waste_factor"] = None; c["waste_origin"] = None; c["waste_basis"] = None
        self.db.add("assumptions", {"assumption_id": "TEST-ASU-W1", "assumption_type": "waste", "applies_to_ref": f"waste:{c['component_id']}",
                                    "value_numeric": D("0.10"), "value_text": None, "unit_id": None, "rationale": "synthetic",
                                    "proposed_by": "tests", "proposed_at": None, "approved_by": "tests", "approved_at": "2026-10-24T00:00:00+00:00",
                                    "status": "approved", "expires_on": None, "origin": "assumed", "review_status": "unreviewed", "notes": None})
        r3 = Engine(self.db).unit_cost(WI, 1, S.params(mode="with_assumptions"))
        self.assertEqual(r3.status, "complete")
        self.assertTrue(r3.run["has_assumptions"])
        self.assertEqual(r3.run["direct_cost_total"], EXPECTED_DRY001)
        self.assertIn("assumed", {ln["origin_summary"] for ln in r3.lines})
        r4 = Engine(self.db).unit_cost(WI, 1, S.params(mode="strict"))
        self.assertEqual(r4.status, "incomplete")      # strict mode ignores the assumption table entirely

    def test_median_of_two_products(self):
        S.add_product(self.db, "TEST-PRD-BOARDB", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-B", "TB-B-1")
        S.add_obs(self.db, "TEST-OBS-BOARDB", "TEST-PRD-BOARDB", "16.00", 32, "SF")     # 0.50/SF vs 0.40/SF -> median 0.45
        r = Engine(self.db).unit_cost(WI, 1, S.params())
        mat = [ln for ln in r.lines if ln["line_kind"] == "material"][0]
        self.assertEqual(mat["unit_cost"], D("0.45"))
        self.assertIn("MEDIAN_OF_2_PRODUCTS", mat["warnings"])
        self.assertEqual(median([D(1), D(2), D(9)]), D(2))

    def test_latest_observation_wins_and_history_preserved(self):
        S.add_obs(self.db, "TEST-OBS-BOARDNEW", "TEST-PRD-BOARDA", "14.40", 32, "SF", observed=date(2026, 10, 1))   # 0.45/SF
        r = Engine(self.db).unit_cost(WI, 1, S.params())
        self.assertEqual([ln for ln in r.lines if ln["line_kind"] == "material"][0]["unit_cost"], D("0.45"))
        self.assertEqual(len([o for o in self.db["price_observations"] if o["product_id"] == "TEST-PRD-BOARDA"]), 2)

    def test_pack_unit_conversion_sy_to_sf(self):
        # same board priced per square YARD pack: 3.5556 SY/pack would be odd; use content 3 SY at $3.60 -> 1.20/SY -> 0.1333/SF
        for p in self.db["products"]:
            if p["product_id"] == "TEST-PRD-BOARDA":
                p["content_qty"] = D("3"); p["content_unit_id"] = "SY"
        for o in self.db["price_observations"]:
            if o["observation_id"] == "TEST-OBS-BOARDA":
                o["pack_content_qty"] = D("3"); o["pack_content_unit_id"] = "SY"; o["price_amount"] = D("3.60")
        r = Engine(self.db).unit_cost(WI, 1, S.params())
        mat = [ln for ln in r.lines if ln["line_kind"] == "material"][0]
        self.assertAlmostEqual(float(mat["unit_cost"]), 3.60 / 3 / 9, places=8)

    def test_unit_dimension_mismatch_is_reported(self):
        for p in self.db["products"]:
            if p["product_id"] == "TEST-PRD-BOARDA":
                p["content_unit_id"] = "LF"
        for o in self.db["price_observations"]:
            if o["observation_id"] == "TEST-OBS-BOARDA":
                o["pack_content_unit_id"] = "LF"
        r = Engine(self.db).unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertTrue(any("unit mismatch" in m["reason"] for m in r.run["missing_inputs"]))

    def test_stale_price_needs_index_and_formula_is_exact(self):
        o = next(x for x in self.db["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
        o["observed_at"] = date(2025, 6, 1); o["retrieved_at"] = "2025-06-02T00:00:00+00:00"
        self.assertEqual(Engine(self.db).unit_cost(WI, 1, S.params()).status, "incomplete")
        self.db.add("indices", {"index_id": "TEST-IDX-1", "publisher": "TEST", "series_code": "T1", "name": "synthetic", "base_period": None,
                                "frequency": "monthly", "seasonal_adjustment": None, "geography": None, "applies_to": "material",
                                "source_id": S.SRC, "origin": "observed", "review_status": "validated", "reviewed_by": None,
                                "reviewed_at": None, "notes": None})
        for per, val in ((date(2025, 6, 1), "200"), (date(2026, 10, 1), "210")):
            self.db.add("index_values", {"index_id": "TEST-IDX-1", "period_start": per, "vintage_date": date(2026, 10, 20), "value": D(val),
                                         "value_status": "final", "retrieved_at": "2026-10-20T00:00:00+00:00", "source_locator": "synthetic",
                                         "raw_file_sha256": None, "origin": "observed", "review_status": "validated", "reviewed_by": None,
                                         "reviewed_at": None, "notes": None})
        r = Engine(self.db).unit_cost(WI, 1, S.params(time_index_id="TEST-IDX-1"))
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        mat = [ln for ln in r.lines if ln["line_kind"] == "material"][0]
        # board 0.40 x 210/200 = 0.42 ; line = 1.10 x 0.42 = 0.462
        self.assertAlmostEqual(float(mat["extended_cost"]), 1.10 * 0.40 * 210 / 200, places=8)
        adj = mat["inputs"][-1]["adjustments"]["time_index"]
        self.assertEqual((D(adj["index_from"]), D(adj["index_to"]), adj["from_date"], adj["to_date"]), (D(200), D(210), "2025-06-01", "2026-10-24"))
        self.assertIn("TIME_INDEXED_PRICE", mat["warnings"])

    def test_region_factor_only_for_foreign_prices_never_twice(self):
        o = next(x for x in self.db["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
        o["region_id"] = "REG-CA-073"                      # San Diego price, no LA price
        self.assertEqual(Engine(self.db).unit_cost(WI, 1, S.params()).status, "incomplete")
        self.db.add("adjustment_factors", {"factor_id": "TEST-ADJ-R1", "factor_type": "region", "applies_to": "material",
                                           "from_region_id": "REG-CA-073", "to_region_id": "REG-CA-037", "factor_value": D("1.05"),
                                           "qty_min": None, "qty_max": None, "condition_desc": None, "valid_from": None, "valid_to": None,
                                           "index_id": None, "derivation_formula": "synthetic", "input_refs": [], "source_id": S.SRC,
                                           "assumption_basis": None, "calc_run_id": None, "origin": "observed", "review_status": "validated",
                                           "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})
        self.assertEqual(Engine(self.db).unit_cost(WI, 1, S.params()).status, "incomplete")   # factors are opt-in
        r = Engine(self.db).unit_cost(WI, 1, S.params(use_region_factors=True))
        self.assertEqual(r.status, "complete")
        mat = [ln for ln in r.lines if ln["line_kind"] == "material"][0]
        self.assertAlmostEqual(float(mat["extended_cost"]), 1.10 * 0.40 * 1.05, places=8)
        self.assertIn("REGION_FACTOR_APPLIED", mat["warnings"])
        # a LOCAL (LA) price exists too -> local price wins and NO factor is applied
        S.add_obs(self.db, "TEST-OBS-BOARDLA", "TEST-PRD-BOARDA", "12.80", 32, "SF", observed=date(2026, 9, 2))
        r2 = Engine(self.db).unit_cost(WI, 1, S.params(use_region_factors=True))
        mat2 = [ln for ln in r2.lines if ln["line_kind"] == "material"][0]
        self.assertAlmostEqual(float(mat2["extended_cost"]), 1.10 * 0.40, places=8)
        self.assertNotIn("REGION_FACTOR_APPLIED", mat2["warnings"])

    def test_condition_factor_must_exist_and_is_applied_to_labor_only_where_defined(self):
        r = Engine(self.db).unit_cost(WI, 1, S.params(conditions=("occupied_building",)))
        self.assertEqual(r.status, "incomplete")
        self.assertIn("CONDITION_FACTOR_MISSING", {m["code"] for m in r.run["missing_inputs"]})
        self.db.add("adjustment_factors", {"factor_id": "TEST-ADJ-C1", "factor_type": "productivity_condition", "applies_to": "labor",
                                           "from_region_id": None, "to_region_id": None, "factor_value": D("1.20"), "qty_min": None,
                                           "qty_max": None, "condition_desc": "occupied_building", "valid_from": None, "valid_to": None,
                                           "index_id": None, "derivation_formula": "synthetic", "input_refs": [], "source_id": S.SRC,
                                           "assumption_basis": None, "calc_run_id": None, "origin": "observed", "review_status": "validated",
                                           "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})
        r2 = Engine(self.db).unit_cost(WI, 1, S.params(conditions=("occupied_building",)))
        self.assertEqual(r2.status, "complete")
        self.assertEqual(r2.run["labor_cost"], D("0.660000"))      # 0.55 x 1.20
        self.assertEqual(r2.run["material_cost"], D("0.447875"))   # materials untouched

    def test_shift_and_crew_mismatch_are_blocking(self):
        for p in self.db["productivity_observations"]:
            if p["work_item_id"] == WI:
                p["crew_size"] = D("4")
        r = Engine(self.db).unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "failed")
        self.assertIn("CREW_MISMATCH", {m["code"] for m in r.run["missing_inputs"]})

    def test_productivity_from_reported_person_hours(self):
        for p in self.db["productivity_observations"]:
            if p["work_item_id"] == WI:
                p["daily_output"] = None; p["crew_size"] = None; p["shift_hours"] = None
                p["person_hours_per_unit_reported"] = D("0.015")
        r = Engine(self.db).unit_cost(WI, 1, S.params())
        self.assertEqual(r.status, "complete")
        self.assertEqual(r.run["labor_cost"], D("0.550000"))       # 3 persons x 8 h / 0.015 ph/SF = 1600 SF/day
        lab = [ln for ln in r.lines if ln["line_kind"] == "labor"][0]
        self.assertIn("DAILY_OUTPUT_DERIVED_FROM_REPORTED_PERSON_HOURS", lab["warnings"])

    def test_missing_productivity_and_crew_blocks_labor_but_never_invents(self):
        db = S.real_db()
        r = Engine(db).unit_cost(WI, 1, S.params(allow_synthetic=False, labor_basis="stat_loaded"))
        self.assertEqual(r.status, "incomplete")
        self.assertIsNone(r.run["direct_cost_total"])
        self.assertTrue(all(ln["extended_cost"] is None for ln in r.lines if ln["origin_summary"] == "missing"))
        codes = {m["code"] for m in r.run["missing_inputs"]}
        self.assertTrue({"PRICE_MISSING", "WASTE_MISSING", "CREW_MISSING"} <= codes, codes)


class LaborRateTest(unittest.TestCase):
    def setUp(self):
        self.db = S.real_db()
        S.add_source(self.db)
        self.base = dict(use_context="statistical_reference")

    def stat_rate(self, trade="TR-DRYW", base="30", region="REG-MD-31084"):
        self.db.add("labor_rates", {
            "labor_rate_id": f"TEST-LRT-S{trade[-3:]}", "rate_type": "stat_wage", "trade_code": trade, "classification_raw": "TEST",
            "soc_code": None, "statistic": "mean", "region_id": region, "base_wage_hr": D(base), "fringe_hr": None, "fringe_breakdown": None,
            "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None, "total_hr": None, "includes_fringe": False,
            "includes_payroll_taxes": False, "includes_workers_comp": False, "wage_basis": "straight_time", "project_type": "n/a",
            "use_context": "statistical_reference", "apprentice": False, "determination_ref": None, "effective_from": date(2026, 5, 1),
            "effective_to": None, "retrieved_at": S.RUN_AT, "derived_from": None, "calc_run_id": None, "source_id": S.SRC,
            "source_locator": "synthetic", "evidence_excerpt": "synthetic", "raw_file_sha256": None, "origin": "observed",
            "review_status": "validated", "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})

    def burden(self, bid, btype, basis, rate, cap=None, trade=None):
        self.db.add("burden_rates", {"burden_id": bid, "burden_type": btype, "basis": basis, "rate": D(rate), "wage_cap_annual": D(cap) if cap else None,
                                     "class_code": None, "trade_code": trade, "region_id": "REG-US", "effective_from": date(2026, 1, 1),
                                     "effective_to": date(2026, 12, 31), "retrieved_at": S.RUN_AT, "source_id": S.SRC, "source_locator": "synthetic",
                                     "evidence_excerpt": "synthetic", "origin": "observed", "review_status": "validated", "reviewed_by": None,
                                     "reviewed_at": None, "created_at": None, "notes": None})

    def all_burdens(self):
        self.burden("TEST-BRD-BEN", "employer_benefits", "pct_of_wages", "0.25")
        self.burden("TEST-BRD-SS", "fica_social_security", "pct_of_wages", "0.062", "200000")
        self.burden("TEST-BRD-MED", "fica_medicare", "pct_of_wages", "0.0145")
        self.burden("TEST-BRD-FUTA", "futa", "pct_of_wages", "0.006", "7000")
        self.burden("TEST-BRD-UI", "state_ui", "pct_of_wages", "0.034", "7000")
        self.burden("TEST-BRD-ETT", "state_ett", "pct_of_wages", "0.001", "7000")
        self.burden("TEST-BRD-WC", "workers_comp", "per_100_payroll", "8.00")

    def test_stat_loaded_every_component_by_hand(self):
        self.stat_rate(); self.all_burdens()
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", annual_paid_hours=D("2080")))
        self.assertEqual(res.status, "complete", res.run["missing_inputs"])
        ah, base = D(2080), D(30)
        expected = (base + D("0.25") * base + D("0.062") * min(D(200000), base * ah) / ah + D("0.0145") * base
                    + D("0.006") * D(7000) / ah + D("0.034") * D(7000) / ah + D("0.001") * D(7000) / ah + D("0.08") * base)
        self.assertAlmostEqual(float(res.run["labor_cost"]), float(expected), places=5)
        row = res.derived_rows["labor_rates"][0]
        self.assertEqual(row["origin"], "derived")
        self.assertEqual(row["rate_type"], "loaded_employer_cost")
        parts = sum(D(row[k] or 0) for k in ("base_wage_hr", "fringe_hr", "payroll_tax_hr", "workers_comp_hr", "other_employer_cost_hr"))
        self.assertAlmostEqual(float(parts), float(row["total_hr"]), places=8)
        self.assertTrue(any("RATE_FROM_ANCESTOR_REGION" in w for w in res.run["warnings"]))   # metro-division rate used for the county

    def test_capped_burden_needs_paid_hours(self):
        self.stat_rate(); self.all_burdens()
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded"))
        self.assertEqual(res.status, "incomplete")
        self.assertIn("ANNUAL_HOURS_MISSING", {m["code"] for m in res.run["missing_inputs"]})

    def test_missing_burden_blocks_loaded_rate(self):
        self.stat_rate()
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", annual_paid_hours=D("2080")))
        self.assertEqual(res.status, "incomplete")
        self.assertIn("BENEFITS_MISSING", {m["code"] for m in res.run["missing_inputs"]})

    def test_prevailing_wage_refused_for_private_projects(self):
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="prevailing_loaded", project_type="private"))
        self.assertEqual(res.status, "failed")
        self.assertIn("PW_NOT_APPLICABLE", {m["code"] for m in res.run["missing_inputs"]})

    def test_prevailing_wage_does_not_add_benefits_twice(self):
        self.db.add("labor_rates", {
            "labor_rate_id": "TEST-LRT-PW", "rate_type": "prevailing_wage", "trade_code": "TR-DRYW", "classification_raw": "TEST", "soc_code": None,
            "statistic": "determined", "region_id": "REG-CA-037", "base_wage_hr": D("50"), "fringe_hr": D("20"), "fringe_breakdown": None,
            "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None, "total_hr": None, "includes_fringe": True,
            "includes_payroll_taxes": False, "includes_workers_comp": False, "wage_basis": "straight_time", "project_type": "building",
            "use_context": "public_works_only", "apprentice": False, "determination_ref": "TEST-DET", "effective_from": date(2026, 8, 22),
            "effective_to": date(2027, 2, 21), "retrieved_at": S.RUN_AT, "derived_from": None, "calc_run_id": None, "source_id": S.SRC,
            "source_locator": "synthetic", "evidence_excerpt": "synthetic", "raw_file_sha256": None, "origin": "observed",
            "review_status": "validated", "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})
        self.all_burdens()
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="prevailing_loaded", project_type="public_works",
                                                                     annual_paid_hours=D("2080")))
        self.assertEqual(res.status, "complete", res.run["missing_inputs"])
        descs = {ln["description"] for ln in res.lines}
        self.assertNotIn("employer_benefits", descs)                 # fringe already inside the determination
        self.assertIn("fringe_in_source", descs)
        ah = D(2080)
        expected = (D(50) + D(20) + D("0.062") * D(50) + D("0.0145") * D(50) + (D("0.006") + D("0.034") + D("0.001")) * D(7000) / ah + D("0.08") * D(50))
        self.assertAlmostEqual(float(res.run["labor_cost"]), float(expected), places=5)

    def test_ui_cap_makes_hourly_cost_tiny_not_a_flat_percentage(self):
        self.stat_rate(); self.all_burdens()
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", annual_paid_hours=D("2080")))
        ui = next(ln for ln in res.lines if ln["description"] == "state_ui")
        self.assertAlmostEqual(float(ui["unit_cost"]), 0.034 * 7000 / 2080, places=8)
        self.assertLess(float(ui["unit_cost"]), 0.034 * 30 / 5)    # nowhere near 3.4% of wages


class CrewEquipmentTest(unittest.TestCase):
    def test_operator_cannot_be_counted_in_labor_and_equipment(self):
        db = S.real_db()
        S.add_source(db)
        S.add_labor_actual(db, "TEST-LRT-CEM", "TR-CEM", 45)
        S.add_labor_actual(db, "TEST-LRT-OPR", "TR-OPR", 55)
        S.set_crew(db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False), ("labor", "TR-OPR", 1, True), ("equipment", "EQ-PTROWEL", 1, False)])
        S.set_productivity(db, "WI-CON-001", 3, 8, 2000)
        db.add("equipment_rates", {
            "equipment_rate_id": "TEST-EQR-1", "equipment_type_code": "EQ-PTROWEL", "description_raw": "TEST", "make_model_raw": None,
            "capacity_raw": None, "rate_basis": "rental_market", "ownership_cost_hr": None, "operating_cost_hr": None, "fuel_cost_hr": None,
            "rental_rate_hr": D("25"), "rental_rate_day": None, "rental_rate_week": None, "rental_rate_month": None, "min_rental_period": None,
            "delivery_pickup_cost": None, "fuel_included": True, "operator_included": True, "region_id": S.REGION,
            "effective_from": date(2026, 1, 1), "effective_to": None, "retrieved_at": S.RUN_AT, "source_id": S.SRC,
            "source_locator": "synthetic", "evidence_excerpt": "synthetic", "raw_file_sha256": None, "origin": "observed",
            "review_status": "validated", "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})
        r = Engine(db).unit_cost("WI-CON-001", 1, S.params())
        self.assertEqual(r.status, "failed")
        self.assertIn("OPERATOR_DOUBLE_COUNT", {m["code"] for m in r.run["missing_inputs"]})
        # same equipment rate WITHOUT operator -> no conflict (labor/equipment lines resolve; other inputs still missing)
        db["equipment_rates"][0]["operator_included"] = False
        r2 = Engine(db).unit_cost("WI-CON-001", 1, S.params())
        self.assertNotIn("OPERATOR_DOUBLE_COUNT", {m["code"] for m in r2.run["missing_inputs"]})
        eq = [ln for ln in r2.lines if ln["line_kind"] == "equipment"][0]
        self.assertAlmostEqual(float(eq["unit_cost"]), 25 * 8 / 2000, places=8)       # $200/shift ÷ 2000 SF
        lab = [ln for ln in r2.lines if ln["line_kind"] == "labor"][0]
        self.assertAlmostEqual(float(lab["unit_cost"]), (2 * 45 + 55) * 8 / 2000, places=8)


class AssemblyTest(unittest.TestCase):
    def build(self):
        db = S.priced_drywall_db()
        # one synthetic material-only work item priced $2.00 each, waste 0
        db.add("work_items", {"work_item_id": "TEST-WI-9", "version": 1, "name": "TEST widget install", "category_id": "CAT-FRM",
                              "spec_attributes": {"widget": "synthetic"}, "output_unit_id": "EA", "description": "synthetic",
                              "included_scope": ["widget_material"], "excluded_scope": [], "conditions": None, "status": "defined",
                              "valid_from": S.AS_OF, "supersedes_version": None, "definition_basis": "synthetic", "origin": "assumed",
                              "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})
        m = S.pilot.MATS["hurricane_tie"]
        S.add_product(db, "TEST-PRD-WIDGET", "hurricane_tie", 1, "EA", "TESTBRAND-W", "TW-1")
        S.add_obs(db, "TEST-OBS-WIDGET", "TEST-PRD-WIDGET", "2.00", 1, "EA")
        db.add("work_item_components", {"component_id": "TEST-WIC-9", "work_item_id": "TEST-WI-9", "work_item_version": 1, "line_no": 1,
                                        "component_kind": "material", "description": "widget", "product_spec_key": m["spec_key"], "product_id": None,
                                        "qty_mode": "fixed", "qty_per_unit": D("1"), "qty_unit_id": "EA", "qty_formula": "1 per EA",
                                        "qty_origin": "derived", "waste_factor": D("0"), "waste_origin": "observed", "waste_basis": "TEST",
                                        "crew_id": None, "productivity_id": None, "consumption_application": None, "coats_applied": None,
                                        "cost_tags": ["widget"], "is_optional": False, "notes": None})
        db.add("assemblies", {"assembly_id": "TEST-ASM-1", "version": 1, "name": "TEST assembly", "category_id": "CAT-FRM",
                              "spec_attributes": {"synthetic": True}, "output_unit_id": "SF", "description": "synthetic",
                              "included_scope": [], "excluded_scope": [], "conditions": None, "status": "defined", "valid_from": S.AS_OF,
                              "supersedes_version": None, "definition_basis": "synthetic", "origin": "assumed", "review_status": "unreviewed",
                              "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})
        for i, (wid, qty, unit) in enumerate((("WI-DRY-001", "2", "SF"), ("TEST-WI-9", "3", "EA")), 1):
            db.add("assembly_components", {"assembly_component_id": f"TEST-ASC-{i}", "assembly_id": "TEST-ASM-1", "assembly_version": 1,
                                           "line_no": i, "work_item_id": wid, "work_item_version": 1, "qty_per_assembly_unit": D(qty),
                                           "qty_unit_id": unit, "qty_formula": "synthetic", "qty_origin": "derived", "cost_tags": [], "notes": None})
        return db

    def test_assembly_total_is_sum_of_versioned_unit_costs(self):
        db = self.build()
        r = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params())
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        self.assertEqual(r.run["direct_cost_total"], D("2") * EXPECTED_DRY001 + D("3") * D("2.00"))
        self.assertEqual(len(r.children), 2)
        self.assertEqual({c.run["target_id"] for c in r.children}, {"WI-DRY-001", "TEST-WI-9"})
        self.assertAlmostEqual(float(r.run["material_cost"] + r.run["labor_cost"] + r.run["equipment_cost"] + r.run["other_direct_cost"]),
                               float(r.run["direct_cost_total"]), places=6)

    def test_scope_overlap_is_a_double_counting_failure(self):
        db = self.build()
        for w in db["work_items"]:
            if w["work_item_id"] == "TEST-WI-9":
                w["included_scope"] = ["board_material"]          # WI-DRY-001 already includes it
        r = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params())
        self.assertEqual(r.status, "failed")
        self.assertTrue(any("SCOPE_OVERLAP" in w for w in r.run["warnings"]))

    def test_incomplete_child_makes_assembly_incomplete_without_total(self):
        db = self.build()
        for o in db["price_observations"]:
            if o["observation_id"] == "TEST-OBS-WIDGET":
                o["review_status"] = "unreviewed"
        r = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertIsNone(r.run["direct_cost_total"])
        self.assertTrue(any(">" in m["component_ref"] for m in r.run["missing_inputs"]))

    def test_real_pilot_assembly_reports_exactly_what_is_missing(self):
        r = Engine(S.real_db()).assembly_cost("ASM-WALL-001", 1, S.params(allow_synthetic=False, labor_basis="stat_loaded"))
        self.assertEqual(r.status, "incomplete")
        self.assertIsNone(r.run["direct_cost_total"])
        codes = {m["code"] for m in r.run["missing_inputs"]}
        self.assertTrue({"PRICE_MISSING", "WASTE_MISSING", "CREW_MISSING", "CONSUMPTION_MISSING"} <= codes, codes)


class MarkupTest(unittest.TestCase):
    def make(self):
        db = S.priced_drywall_db()
        r = Engine(db).unit_cost(WI, 1, S.params())
        r.run["direct_cost_total"] = D("100.000000")           # use a round direct cost for the hand calculation
        return r

    def test_markup_vs_margin(self):
        r = self.make()
        kw = dict(overhead_pct=D("0.10"), overhead_basis="test", contingency_pct=D("0.05"), contingency_basis="test", profit_basis="test")
        a = apply_markup(r, profit_method="markup", profit_value=D("0.10"), **kw)
        b = apply_markup(r, profit_method="margin", profit_value=D("0.10"), **kw)
        # overhead 10.00 ; contingency (100+10) x 5% = 5.50 ; cost 115.50
        self.assertEqual(a.run["direct_cost_total"], D("127.050000"))                       # 115.5 x 1.10
        self.assertEqual(b.run["direct_cost_total"], (D("115.5") / D("0.9")).quantize(D("0.000001")))   # 115.5 / 0.90
        kinds = [ln["line_kind"] for ln in a.lines]
        self.assertEqual(kinds, ["subtotal", "overhead", "contingency", "subtotal", "profit", "subtotal"])
        self.assertAlmostEqual(float(markup_to_margin(D("0.25"))), 0.20, places=12)
        self.assertAlmostEqual(float(margin_to_markup(D("0.20"))), 0.25, places=12)

    def test_no_default_percentages_and_no_markup_on_incomplete(self):
        r = self.make()
        with self.assertRaises(ValueError):
            apply_markup(r, overhead_pct=D("0.1"), overhead_basis="", contingency_pct=D("0"), contingency_basis="x",
                         profit_method="markup", profit_value=D("0.1"), profit_basis="x")
        inc = Engine(S.real_db()).unit_cost(WI, 1, S.params(allow_synthetic=False))
        with self.assertRaises(ValueError):
            apply_markup(inc, overhead_pct=D("0.1"), overhead_basis="x", contingency_pct=D("0"), contingency_basis="x",
                         profit_method="markup", profit_value=D("0.1"), profit_basis="x")
        with self.assertRaises(ValueError):
            apply_markup(r, overhead_pct=D("0.1"), overhead_basis="x", contingency_pct=D("0"), contingency_basis="x",
                         profit_method="margin", profit_value=D("1.0"), profit_basis="x")


if __name__ == "__main__":
    unittest.main()
