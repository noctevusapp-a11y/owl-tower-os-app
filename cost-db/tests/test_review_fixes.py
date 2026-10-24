"""Regression tests: one (or more) counter-example for every defect of the independent review F1 that concerned the
calculation engine (docs/independent_review_F1.md, ids F1-001 ...). Each test builds the failing scenario of the review
and asserts the corrected behaviour. All inputs are SYNTHETIC (TEST- ids); see tests/fixtures/synthetic.py."""
import sys
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "pipeline")]

from costdb.calc import Engine, RunParams, apply_markup  # noqa: E402
from tests.fixtures import synthetic as S  # noqa: E402

WI = S.WI


def run(db, **kw):
    return Engine(db).unit_cost(WI, 1, S.params(**kw))


def mat(r, n=0):
    return [ln for ln in r.lines if ln["line_kind"] == "material"][n]


def codes(r):
    return {m["code"] for m in r.run["missing_inputs"]}


def obs(db, oid):
    return next(o for o in db["price_observations"] if o["observation_id"] == oid)


def row(db, table, key, val):
    return next(r for r in db[table] if r[key] == val)


def comp(db, wi, needle):
    return next(c for c in db["work_item_components"] if c["work_item_id"] == wi and needle in (c["product_spec_key"] or c["description"]))


def board(r):
    return [ln for ln in r.lines if ln["line_kind"] == "material" and "board" in ln["description"].lower()][0]


class F001ConsumptionPairing(unittest.TestCase):
    def primer(self, db, **kw):
        return [ln for ln in Engine(db).unit_cost(S.PNT, 1, S.params(**kw)).lines if ln["line_kind"] == "material"][0]

    def test_each_coverage_is_paired_with_its_own_products_price(self):
        db = S.paint_db()
        r = Engine(db).unit_cost(S.PNT, 1, S.params())
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        self.assertEqual(mat(r)["extended_cost"], D("0.1250000000"))      # median(0.05, 0.20); the review got 0.075 or 0.15
        self.assertIn("MEDIAN_OF_2_PRODUCTS", mat(r)["warnings"])

    def test_result_does_not_depend_on_row_order_or_ids(self):
        db = S.paint_db()
        db.tables["product_consumption"].reverse()
        db.tables["products"].reverse()
        self.assertEqual(self.primer(db)["extended_cost"], D("0.1250000000"))
        for r_ in db["product_consumption"]:
            r_["consumption_id"] = "TEST-CON-" + {"TEST-CON-A": "Z", "TEST-CON-B": "A"}[r_["consumption_id"]]
        self.assertEqual(self.primer(db)["extended_cost"], D("0.1250000000"))

    def test_coverage_unit_is_converted_to_the_output_unit(self):
        db = S.paint_db()
        db.tables["products"] = [p for p in db["products"] if p["product_id"] != "TEST-PRD-PB"]
        db.tables["product_consumption"] = [c for c in db["product_consumption"] if c["product_id"] == "TEST-PRD-PA"]
        db["product_consumption"][0].update(coverage_qty=D("400"), coverage_unit_id="SY")        # 400 SY/gal = 3600 SF/gal
        # 1 / 3600 gal per SF x $20 = 0.0055555...
        self.assertAlmostEqual(float(self.primer(db)["extended_cost"]), 20 / 3600, places=9)

    def test_zero_coverage_or_coats_never_crash(self):
        db = S.paint_db()
        for fld in ("coverage_qty", "coats"):
            d2 = S.clone(db)
            for c in d2["product_consumption"]:
                c[fld] = D("0")
            r = Engine(d2).unit_cost(S.PNT, 1, S.params())
            self.assertEqual(r.status, "incomplete")
            self.assertIn("CONSUMPTION_MISSING", codes(r))

    def test_several_rows_need_a_selector(self):
        db = S.paint_db()
        db.tables["products"] = [p for p in db["products"] if p["product_id"] != "TEST-PRD-PB"]
        db.tables["product_consumption"] = []
        S.add_consumption(db, "TEST-CON-1", "TEST-PRD-PA", "new_drywall_primer", 400, "SF", film="thin")
        S.add_consumption(db, "TEST-CON-2", "TEST-PRD-PA", "new_drywall_primer", 200, "SF", film="thick")
        r = Engine(db).unit_cost(S.PNT, 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertIn("CONSUMPTION_AMBIGUOUS", codes(r))
        comp(db, S.PNT, "CAT-PNT-PRM")["consumption_selector"] = {"film_thickness": " THICK "}
        r2 = Engine(db).unit_cost(S.PNT, 1, S.params())
        self.assertEqual(r2.status, "complete", r2.run["missing_inputs"])
        self.assertAlmostEqual(float(mat(r2)["extended_cost"]), 20 / 200, places=9)
        comp(db, S.PNT, "CAT-PNT-PRM")["consumption_selector"] = {"bogus": "x"}
        self.assertEqual(Engine(db).unit_cost(S.PNT, 1, S.params()).status, "failed")

    def test_unusable_products_are_not_part_of_the_pool(self):
        db = S.paint_db()
        row(db, "products", "product_id", "TEST-PRD-PB")["review_status"] = "flagged"
        self.assertEqual(self.primer(db)["extended_cost"], D("0.0500000000"))
        self.assertNotIn("MEDIAN_OF_2_PRODUCTS", self.primer(db)["warnings"])

    def test_unit_cost_and_quantity_of_a_non_uniform_line_are_not_invented(self):
        db = S.paint_db()
        ln = self.primer(db)
        self.assertIsNone(ln["quantity"])        # two products consume different quantities: no single quantity exists
        tables = sorted(i["table"] for i in ln["inputs"])
        self.assertEqual(tables, ["price_observations", "price_observations", "product_consumption", "product_consumption", "work_item_components"])

    def test_a_consumption_row_from_a_restricted_source_is_unusable(self):
        db = S.paint_db()
        S.add_source(db, "TEST-SRC-LIC", reuse="licence_required")
        for c in db["product_consumption"]:
            c["source_id"] = "TEST-SRC-LIC"
        r = Engine(db).unit_cost(S.PNT, 1, S.params())
        self.assertEqual(r.status, "incomplete")
        self.assertIn("CONSUMPTION_MISSING", codes(r))


class F002StrictModeLeaks(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_rejected_or_flagged_source(self):
        for st in ("rejected", "flagged"):
            db = S.clone(self.db)
            row(db, "sources", "source_id", S.SRC)["review_status"] = st
            self.assertEqual(run(db).status, "incomplete", st)

    def test_rejected_or_unreviewed_crew(self):
        for st in ("rejected", "flagged", "unreviewed"):
            db = S.clone(self.db)
            row(db, "crews", "crew_id", "CRW-DRY-HANG")["review_status"] = st
            r = run(db)
            self.assertEqual(r.status, "incomplete", st)
            self.assertIn("CREW_UNUSABLE", codes(r))
        db = S.clone(self.db)
        row(db, "crews", "crew_id", "CRW-DRY-HANG")["review_status"] = "unreviewed"
        self.assertEqual(run(db, min_review="unreviewed").status, "complete")

    def test_flagged_or_unreviewed_product_even_when_pinned(self):
        for st in ("flagged", "unreviewed", "rejected"):
            db = S.clone(self.db)
            row(db, "products", "product_id", "TEST-PRD-BOARDA")["review_status"] = st
            self.assertEqual(run(db).status, "incomplete", st)
            comp(db, WI, "CAT-DRY-BRD")["product_id"] = "TEST-PRD-BOARDA"
            self.assertEqual(run(db).status, "incomplete", f"pinned {st}")

    def test_flagged_index_series_is_not_used(self):
        db = S.clone(self.db)
        obs(db, "TEST-OBS-BOARDA")["observed_at"] = date(2025, 6, 1)
        obs(db, "TEST-OBS-BOARDA")["retrieved_at"] = "2025-06-02T00:00:00+00:00"
        S.add_index(db, "TEST-IDX-1", {date(2025, 6, 1): 200, date(2026, 9, 1): 205, date(2026, 10, 1): 210})
        self.assertEqual(run(db, time_index_id="TEST-IDX-1").status, "complete")
        row(db, "indices", "index_id", "TEST-IDX-1")["review_status"] = "flagged"
        self.assertEqual(run(db, time_index_id="TEST-IDX-1", min_review="unreviewed").status, "incomplete")

    def test_rejected_assumption_is_not_used(self):
        db = S.clone(self.db)
        c = comp(db, WI, "CAT-DRY-BRD")
        c["waste_factor"] = None
        c["waste_origin"] = None
        c["waste_basis"] = None
        S.add_assumption(db, "TEST-ASU-1", "waste", f"waste:{c['component_id']}", "0.10")
        self.assertEqual(run(db, mode="with_assumptions").status, "complete")
        row(db, "assumptions", "assumption_id", "TEST-ASU-1")["review_status"] = "rejected"
        self.assertEqual(run(db, mode="with_assumptions").status, "incomplete")

    def test_a_record_whose_source_is_restricted_is_unusable(self):
        for reuse in ("prohibited", "restricted_no_storage", "licence_required"):
            db = S.clone(self.db)
            row(db, "sources", "source_id", S.SRC)["reuse_status"] = reuse
            self.assertEqual(run(db).status, "incomplete", reuse)


class F005FactorUsability(unittest.TestCase):
    def test_region_factor_from_a_prohibited_source_is_not_applied(self):
        db = S.priced_drywall_db()
        S.add_source(db, "TEST-SRC-PROH", reuse="prohibited")
        obs(db, "TEST-OBS-BOARDA")["region_id"] = "REG-CA-073"
        S.add_factor(db, "TEST-ADJ-R1", "region", "material", "2.00", from_region="REG-CA-073", to_region="REG-CA-037", source="TEST-SRC-PROH")
        r = run(db, use_region_factors=True)
        self.assertEqual(r.status, "incomplete")
        S.add_factor(db, "TEST-ADJ-R2", "region", "material", "1.05", from_region="REG-CA-073", to_region="REG-CA-037")
        r2 = run(db, use_region_factors=True)
        self.assertEqual(r2.status, "complete")
        self.assertAlmostEqual(float(board(r2)["extended_cost"]), 1.10 * 0.40 * 1.05, places=8)

    def test_newest_valid_factor_is_chosen_deterministically(self):
        db = S.priced_drywall_db()
        obs(db, "TEST-OBS-BOARDA")["region_id"] = "REG-CA-073"
        S.add_factor(db, "TEST-ADJ-R1", "region", "material", "1.50", from_region="REG-CA-073", to_region="REG-CA-037", valid_from=date(2026, 1, 1))
        S.add_factor(db, "TEST-ADJ-R2", "region", "material", "1.05", from_region="REG-CA-073", to_region="REG-CA-037", valid_from=date(2026, 6, 1))
        for _ in range(2):
            self.assertAlmostEqual(float(board(run(db, use_region_factors=True))["extended_cost"]), 1.10 * 0.40 * 1.05, places=8)
            db.tables["adjustment_factors"].reverse()


class F006RegionRanking(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        S.add_obs(self.db, "TEST-OBS-STATE", "TEST-PRD-BOARDA", "16.00", 32, "SF", region="REG-US-CA", observed=date(2026, 10, 1))   # 0.50/SF, newer

    def test_ancestor_price_is_off_by_default(self):
        self.assertAlmostEqual(float(board(run(self.db))["extended_cost"]), 1.10 * 0.40, places=8)

    def test_exact_region_beats_a_newer_ancestor_price(self):
        r = run(self.db, allow_ancestor_region_prices=True)
        self.assertAlmostEqual(float(board(r)["extended_cost"]), 1.10 * 0.40, places=8)
        self.assertNotIn("PRICE_FROM_ANCESTOR_REGION:REG-US-CA", board(r)["warnings"])

    def test_ancestor_price_is_flagged_and_records_its_region(self):
        del self.db.tables["price_observations"][[o["observation_id"] for o in self.db["price_observations"]].index("TEST-OBS-BOARDA")]
        r = run(self.db, allow_ancestor_region_prices=True)
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        self.assertIn("PRICE_FROM_ANCESTOR_REGION:REG-US-CA", board(r)["warnings"])
        self.assertEqual(board(r)["inputs"][-1]["region_id"], "REG-US-CA")
        self.assertEqual(run(self.db).status, "incomplete")

    def test_local_price_does_not_silently_serve_a_national_request(self):
        r = run(self.db, region_id="REG-US")
        self.assertEqual(r.status, "incomplete")
        r2 = run(self.db, region_id="REG-US", allow_subregion_prices=True)
        self.assertIn("PRICE_FROM_SUBREGION:REG-US-CA", board(r2)["warnings"])

    def test_retrieval_order_is_parsed_not_compared_as_text(self):
        db = S.priced_drywall_db()
        S.add_obs(db, "TEST-OBS-B2", "TEST-PRD-BOARDA", "16.00", 32, "SF", observed=date(2026, 9, 1))
        obs(db, "TEST-OBS-BOARDA")["retrieved_at"] = "2026-09-01T23:00:00-08:00"       # = 2026-09-02T07:00Z (later)
        obs(db, "TEST-OBS-B2")["retrieved_at"] = "2026-09-02T01:00:00+00:00"            # text sorts after, instant is earlier
        self.assertEqual(board(run(db))["inputs"][-1]["id"], "TEST-OBS-BOARDA")


class F007LaborSelection(unittest.TestCase):
    def setUp(self):
        self.db = S.real_db()
        S.add_source(self.db)
        S.add_all_burdens(self.db)

    def base(self, **kw):
        p = S.params(labor_basis="stat_loaded", annual_paid_hours=D(2080), **kw)
        return Engine(self.db).labor_rate("TR-DRYW", p)["components"]["base_wage"]

    def test_journeyman_straight_time_is_chosen_not_the_newest_row(self):
        S.add_stat_wage(self.db, "TEST-W1", "TR-DRYW", 30, effective_from=date(2026, 5, 1))
        S.add_stat_wage(self.db, "TEST-W2", "TR-DRYW", 12, apprentice=True, effective_from=date(2026, 6, 1))
        S.add_stat_wage(self.db, "TEST-W3", "TR-DRYW", 45, wage_basis="overtime_1_5x", effective_from=date(2026, 7, 1))
        self.assertEqual(self.base(), D(30))

    def test_two_classifications_are_ambiguous_until_one_is_named(self):
        from costdb.calc import Missing
        S.add_stat_wage(self.db, "TEST-W1", "TR-DRYW", 30, classification="Drywall installer")
        S.add_stat_wage(self.db, "TEST-W2", "TR-DRYW", 36, classification="Taper")
        with self.assertRaises(Missing) as ctx:
            self.base()
        self.assertEqual(ctx.exception.info["code"], "LABOR_RATE_AMBIGUOUS")
        self.assertEqual(self.base(classification="taper"), D(36))

    def test_prevailing_rows_are_selected_by_regime_and_wage_class(self):
        S.add_pw_rate(self.db, "TEST-PW-B", "TR-DRYW", 50, 20, project_type="building")
        S.add_pw_rate(self.db, "TEST-PW-H", "TR-DRYW", 60, 22, project_type="heavy")
        S.add_pw_rate(self.db, "TEST-PW-F", "TR-DRYW", 70, 25, project_type="building", rate_type="federal_wage_determination")
        kw = dict(labor_basis="prevailing_loaded", project_type="public_works", annual_paid_hours=D(2080))
        e = Engine(self.db)
        self.assertEqual(e.labor_rate("TR-DRYW", S.params(wage_class="building", **kw))["components"]["base_wage"], D(50))
        self.assertEqual(e.labor_rate("TR-DRYW", S.params(wage_class="heavy", **kw))["components"]["base_wage"], D(60))
        self.assertEqual(e.labor_rate("TR-DRYW", S.params(wage_class="building", wage_regime="federal", **kw))["components"]["base_wage"], D(70))

    def test_stat_wage_on_a_public_works_run_is_flagged(self):
        S.add_stat_wage(self.db, "TEST-W1", "TR-DRYW", 30)
        lr = Engine(self.db).labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", project_type="public_works", annual_paid_hours=D(2080)))
        self.assertIn("PUBLIC_WORKS_NOT_ON_PREVAILING_BASIS", lr["flags"])


class F008LoadedSourceRates(unittest.TestCase):
    def setUp(self):
        self.db = S.real_db()
        S.add_source(self.db)

    def test_fully_loaded_rate_uses_its_own_components(self):
        S.add_pw_rate(self.db, "TEST-PW", "TR-DRYW", 50, 20, payroll_tax=6, workers_comp=5, other=3, total=84, inc_pt=True, inc_wc=True)
        lr = Engine(self.db).labor_rate("TR-DRYW", S.params(labor_basis="prevailing_loaded", project_type="public_works", wage_class="building"))
        self.assertEqual(lr["total_hr"], D(84))          # the review got 70
        self.assertEqual(lr["components"]["other_employer_cost"], D(3))

    def test_total_that_contradicts_its_components_is_a_blocking_conflict(self):
        S.add_pw_rate(self.db, "TEST-PW", "TR-DRYW", 50, 20, payroll_tax=6, workers_comp=5, other=3, total=90, inc_pt=True, inc_wc=True)
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="prevailing_loaded", project_type="public_works", wage_class="building"))
        self.assertEqual(res.status, "failed")
        self.assertIn("LABOR_TOTAL_MISMATCH", codes(res))

    def test_included_but_unstated_component_needs_a_stated_total(self):
        S.add_pw_rate(self.db, "TEST-PW", "TR-DRYW", 50, 20, inc_pt=True, inc_wc=True)       # claims taxes/WC but states neither
        res = Engine(self.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="prevailing_loaded", project_type="public_works", wage_class="building"))
        self.assertEqual(res.status, "incomplete")
        self.assertTrue({"PAYROLL_TAX_HR_MISSING", "WORKERS_COMP_HR_MISSING"} <= codes(res))

    def test_omitted_burden_types_are_flagged_not_silently_dropped(self):
        S.add_stat_wage(self.db, "TEST-W1", "TR-DRYW", 30)
        S.add_all_burdens(self.db)
        e = Engine(self.db)
        p = S.params(labor_basis="stat_loaded", annual_paid_hours=D(2080))
        before = e.labor_rate("TR-DRYW", p)
        S.add_burden(self.db, "TEST-BRD-GL", "general_liability", "pct_of_wages", "0.02")
        S.add_burden(self.db, "TEST-BRD-OTH", "other", "per_hour", "1.50")
        after = e.labor_rate("TR-DRYW", p)
        self.assertEqual(before["total_hr"], after["total_hr"])
        self.assertTrue({"OMITTED_BURDEN:general_liability", "OMITTED_BURDEN:other"} <= set(after["flags"]))

    def test_payroll_types_depend_on_the_state(self):
        S.add_stat_wage(self.db, "TEST-W1", "TR-DRYW", 30, region="REG-US")
        S.add_all_burdens(self.db, with_ett=False)
        self.db.add("regions", {"region_id": "TEST-REG-AZ", "level": "state", "name": "TEST Arizona", "parent_region_id": "REG-US", "state_code": "AZ",
                                "fips_code": None, "cbsa_code": None, "origin": "assumed", "assumption_basis": "synthetic", "review_status": "unreviewed", "notes": None})
        kw = dict(labor_basis="stat_loaded", annual_paid_hours=D(2080))
        e = Engine(self.db)
        self.assertEqual(e.loaded_labor_rate("TR-DRYW", S.params(region_id="TEST-REG-AZ", **kw)).status, "complete")      # no ETT in AZ
        ca = e.loaded_labor_rate("TR-DRYW", S.params(region_id="REG-CA-037", **kw))
        self.assertEqual(ca.status, "incomplete")
        self.assertIn("PAYROLL_TAX_MISSING", codes(ca))


class F009BurdenSelection(unittest.TestCase):
    def setUp(self):
        self.db = S.real_db()
        S.add_source(self.db)
        S.add_stat_wage(self.db, "TEST-W1", "TR-DRYW", 30)
        S.add_all_burdens(self.db)
        self.p = S.params(labor_basis="stat_loaded", annual_paid_hours=D(2080))

    def test_newest_effective_row_wins_whatever_the_table_order(self):
        old = S.add_burden(self.db, "TEST-BRD-MED-OLD", "fica_medicare", "pct_of_wages", "0.0100", effective_from=date(2025, 1, 1), effective_to=None)
        new = row(self.db, "burden_rates", "burden_id", "TEST-BRD-MED")
        new["effective_to"] = None
        self.db.tables["burden_rates"].remove(old)
        self.db.tables["burden_rates"].insert(0, old)
        self.assertEqual(Engine(self.db).labor_rate("TR-DRYW", self.p)["components"]["fica_medicare"], D("0.0145") * 30)

    def test_exact_ties_are_ambiguous(self):
        from costdb.calc import Missing
        S.add_burden(self.db, "TEST-BRD-MED-2", "fica_medicare", "pct_of_wages", "0.0200")
        with self.assertRaises(Exception) as ctx:
            Engine(self.db).labor_rate("TR-DRYW", self.p)
        self.assertIn("BURDEN_AMBIGUOUS", {m.info["code"] for m in getattr(ctx.exception, "items", [ctx.exception]) if isinstance(m, Missing)})

    def test_a_trade_specific_national_row_does_not_beat_a_local_generic_row(self):
        row(self.db, "burden_rates", "burden_id", "TEST-BRD-BEN")["region_id"] = "REG-CA-037"
        S.add_burden(self.db, "TEST-BRD-BEN-NAT", "employer_benefits", "pct_of_wages", "0.10", trade="TR-DRYW", region="REG-US")
        self.assertEqual(Engine(self.db).labor_rate("TR-DRYW", self.p)["components"]["employer_benefits"], D("0.25") * 30)

    def test_workers_comp_class_code_selects_the_row(self):
        row(self.db, "burden_rates", "burden_id", "TEST-BRD-WC")["class_code"] = "5403"
        S.add_burden(self.db, "TEST-BRD-WC2", "workers_comp", "per_100_payroll", "12.00", class_code="5474")
        e = Engine(self.db)
        with self.assertRaises(Exception):
            e.labor_rate("TR-DRYW", self.p)
        self.assertEqual(e.labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", annual_paid_hours=D(2080), wc_class_code="5474"))["components"]["workers_comp"], D("0.12") * 30)


class F010ConditionFactors(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_unusable_factor_makes_the_run_incomplete(self):
        cases = {"unreviewed": dict(review="unreviewed"), "expired": dict(valid_to=date(2020, 1, 1)), "assumed": dict(origin="assumed")}
        for name, kw in cases.items():
            db = S.clone(self.db)
            S.add_factor(db, "TEST-ADJ-C", "productivity_condition", "labor", "1.20", condition="occupied_building", **kw)
            r = run(db, conditions=("occupied_building",))
            self.assertEqual(r.status, "incomplete", name)
            self.assertIn("CONDITION_FACTOR_UNUSABLE", codes(r), name)

    def test_condition_that_changes_no_line_is_missing(self):
        S.add_factor(self.db, "TEST-ADJ-C", "productivity_condition", "equipment", "1.20", condition="occupied_building")
        r = run(self.db, conditions=("occupied_building",))
        self.assertEqual(r.status, "incomplete")
        self.assertIn("CONDITION_FACTOR_MISSING", codes(r))

    def test_person_hours_follow_a_productivity_condition(self):
        S.add_factor(self.db, "TEST-ADJ-C", "productivity_condition", "labor", "1.20", condition="occupied_building")
        r = run(self.db, conditions=("occupied_building",))
        lab = [ln for ln in r.lines if ln["line_kind"] == "labor"][0]
        self.assertAlmostEqual(float(lab["quantity"]), 24 / 1600 * 1.2, places=9)
        self.assertEqual(r.run["labor_cost"], D("0.660000"))


class F011QuantityHandling(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_tier_price_needs_a_quantity_that_reaches_the_tier(self):
        S.add_obs(self.db, "TEST-OBS-TIER", "TEST-PRD-BOARDA", "1.00", 32, "SF", observed=date(2026, 10, 10))
        obs(self.db, "TEST-OBS-TIER")["qty_tier_min"] = D("100000")
        self.assertAlmostEqual(float(board(run(self.db))["extended_cost"]), 1.10 * 0.40, places=8)                       # no quantity: not used
        self.assertAlmostEqual(float(board(run(self.db, quantity=D("500")))["extended_cost"]), 1.10 * 0.40, places=8)       # too small
        big = run(self.db, quantity=D("200000"))
        self.assertAlmostEqual(float(board(big)["extended_cost"]), 1.10 * 1.00 / 32, places=8)
        self.assertTrue(any(w.startswith("QTY_TIER_PRICE") for w in board(big)["warnings"]))

    def test_quantity_factor_respects_validity(self):
        S.add_factor(self.db, "TEST-ADJ-Q", "quantity", "material", "0.90", qty_min=100, valid_to=date(2020, 1, 1))
        self.assertEqual(run(self.db, quantity=D("500")).run["material_cost"], D("0.449188"))
        S.add_factor(self.db, "TEST-ADJ-Q2", "quantity", "material", "0.90", qty_min=100)
        self.assertEqual(run(self.db, quantity=D("500")).run["material_cost"], (D("0.4491875") * D("0.9")).quantize(D("0.000001")))

    def test_overlapping_quantity_ranges_are_ambiguous(self):
        S.add_factor(self.db, "TEST-ADJ-Q1", "quantity", "material", "0.90", qty_min=100)
        S.add_factor(self.db, "TEST-ADJ-Q2", "quantity", "material", "0.80", qty_min=200)
        r = run(self.db, quantity=D("500"))
        self.assertEqual(r.status, "incomplete")
        self.assertIn("QUANTITY_FACTOR_AMBIGUOUS", codes(r))

    def test_assembly_children_get_their_own_quantity(self):
        db = S.assembly_db()
        S.add_factor(db, "TEST-ADJ-Q", "quantity", "material", "0.90", qty_min=15, qty_max=30)       # child needs 2 x 10 = 20 SF
        r = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params(quantity=D("10")))
        child = next(c for c in r.children if c.run["target_id"] == "WI-DRY-001")
        self.assertEqual(D(child.run["parameters"]["quantity"]), D(20))
        self.assertEqual(child.run["material_cost"], (D("0.4491875") * D("0.9")).quantize(D("0.000001")))
        r2 = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params(quantity=D("4")))                  # child needs 8 SF: outside the range
        self.assertEqual(next(c for c in r2.children if c.run["target_id"] == "WI-DRY-001").run["material_cost"], D("0.449188"))


class F012PricePolicy(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        S.add_product(self.db, "TEST-PRD-BOARDB", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-B", "TB-B-1")
        S.add_obs(self.db, "TEST-OBS-BOARDB", "TEST-PRD-BOARDB", "16.00", 32, "SF", observed=date(2026, 10, 1))      # 0.50/SF, later

    def test_policies(self):
        self.assertAlmostEqual(float(board(run(self.db))["extended_cost"]), 1.10 * 0.45, places=8)
        r = run(self.db, price_policy="latest")
        self.assertAlmostEqual(float(board(r)["extended_cost"]), 1.10 * 0.50, places=8)      # the review got 0.40 (first row)
        self.assertNotIn("MEDIAN_OF_2_PRODUCTS", board(r)["warnings"])

    def test_unknown_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            S.params(price_policy="bogus")


class F013RunIds(unittest.TestCase):
    def test_a_different_input_record_gives_a_different_run_id(self):
        db = S.priced_drywall_db()
        db2 = S.clone(db)
        o = obs(db2, "TEST-OBS-BOARDA")
        o["observation_id"] = "TEST-OBS-OTHER"
        self.assertNotEqual(run(db).run["run_id"], run(db2).run["run_id"])

    def test_different_gaps_give_different_run_ids(self):
        a = S.real_db()
        r1 = Engine(a).unit_cost(WI, 1, S.params(allow_synthetic=False))
        S.add_source(a)
        S.add_product(a, "TEST-PRD-BOARDA", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-A", "TB-A-1")
        S.add_obs(a, "TEST-OBS-BOARDA", "TEST-PRD-BOARDA", "12.80", 32, "SF")
        r2 = Engine(a).unit_cost(WI, 1, S.params())
        self.assertEqual((r1.status, r2.status), ("incomplete", "incomplete"))
        self.assertNotEqual(r1.run["run_id"], r2.run["run_id"])

    def test_same_data_same_id(self):
        db = S.priced_drywall_db()
        self.assertEqual(run(db).run["run_id"], run(S.clone(db)).run["run_id"])


class F014F015Assumptions(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        self.c = comp(self.db, WI, "CAT-DRY-BRD")
        self.c.update(waste_factor=None, waste_origin=None, waste_basis=None)
        self.ref = f"waste:{self.c['component_id']}"

    def waste_run(self):
        return run(self.db, mode="with_assumptions")

    def test_productivity_assumption_does_not_crash(self):
        row(self.db, "productivity_observations", "work_item_id", WI)["review_status"] = "unreviewed"
        wic = next(c for c in self.db["work_item_components"] if c["work_item_id"] == WI and c["component_kind"] == "labor")
        S.add_assumption(self.db, "TEST-ASU-P", "productivity", f"productivity:{wic['component_id']}", 1600, "SF")
        S.add_assumption(self.db, "TEST-ASU-W", "waste", self.ref, "0.10")
        r = self.waste_run()
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        self.assertTrue(r.run["has_assumptions"])
        self.assertIn("ASSUMED_PRODUCTIVITY", r.run["warnings"])
        self.assertEqual(r.run["direct_cost_total"], D("0.999188"))

    def test_text_only_negative_and_oversized_values_are_never_used(self):
        for kw in (dict(value=None, value_text="ten percent"), dict(value="-0.5"), dict(value="5"), dict(value="1")):
            db = S.clone(self.db)
            S.add_assumption(db, "TEST-ASU-X", "waste", self.ref, **kw)
            r = run(db, mode="with_assumptions")
            self.assertEqual(r.status, "incomplete", kw)

    def test_two_approved_assumptions_for_one_reference_are_ambiguous(self):
        S.add_assumption(self.db, "TEST-ASU-1", "waste", self.ref, "0.10")
        S.add_assumption(self.db, "TEST-ASU-2", "waste", self.ref, "0.90")
        r = self.waste_run()
        self.assertEqual(r.status, "incomplete")
        self.assertIn("ASSUMPTION_AMBIGUOUS", codes(r))

    def test_four_eyes_expiry_and_status_are_enforced(self):
        for name, kw in {"self approved": dict(approved_by="tests"), "no expiry": dict(expires_on=None), "expired": dict(expires_on=date(2020, 1, 1)),
                         "proposed only": dict(status="proposed"), "wrong type": None}.items():
            db = S.clone(self.db)
            if kw is None:
                S.add_assumption(db, "TEST-ASU-X", "productivity", self.ref, "0.10", "SF")
            else:
                S.add_assumption(db, "TEST-ASU-X", "waste", self.ref, "0.10", **kw)
            self.assertEqual(run(db, mode="with_assumptions").status, "incomplete", name)

    def test_strict_mode_reads_no_assumption(self):
        S.add_assumption(self.db, "TEST-ASU-1", "waste", self.ref, "0.10")
        self.assertEqual(run(self.db).status, "incomplete")

    def test_benefits_and_workers_comp_assumption_units(self):
        db = S.real_db()
        S.add_source(db)
        S.add_stat_wage(db, "TEST-W1", "TR-DRYW", 30)
        S.add_all_burdens(db)
        db.tables["burden_rates"] = [b for b in db["burden_rates"] if b["burden_type"] not in ("employer_benefits", "workers_comp")]
        e = Engine(db)
        p = S.params(labor_basis="stat_loaded", annual_paid_hours=D(2080), mode="with_assumptions")
        self.assertEqual(e.loaded_labor_rate("TR-DRYW", p).status, "incomplete")
        S.add_assumption(db, "TEST-ASU-B", "other", "burden:employer_benefits:TR-DRYW", "0.25")             # fraction of wages
        S.add_assumption(db, "TEST-ASU-WC", "other", "burden:workers_comp:TR-DRYW", "4.00", "HR")          # $4.00 per paid hour
        lr = e.labor_rate("TR-DRYW", p)
        self.assertEqual(lr["components"]["employer_benefits"], D("0.25") * 30)
        self.assertEqual(lr["components"]["workers_comp"], D("4.00"))                                     # the review: unit was ignored
        self.assertTrue({"ASSUMED_EMPLOYER_BENEFITS", "ASSUMED_WORKERS_COMP"} <= set(lr["flags"]))
        row(db, "assumptions", "assumption_id", "TEST-ASU-WC")["unit_id"] = "SF"
        self.assertEqual(e.loaded_labor_rate("TR-DRYW", p).status, "incomplete")


class F016Equipment(unittest.TestCase):
    CON = "WI-CON-001"

    def setUp(self):
        self.db = S.real_db()
        S.add_source(self.db)
        S.add_labor_actual(self.db, "TEST-LRT-CEM", "TR-CEM", 45)
        S.add_labor_actual(self.db, "TEST-LRT-OPR", "TR-OPR", 55)
        S.set_crew(self.db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False), ("equipment", "EQ-PTROWEL", 1, False)])
        S.set_productivity(self.db, self.CON, 2, 8, 2000)

    def crew3(self):
        S.set_crew(self.db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False), ("labor", "TR-OPR", 1, False), ("equipment", "EQ-PTROWEL", 1, False)])
        S.set_productivity(self.db, self.CON, 3, 8, 2000)

    def eq(self, **rate_kw):
        for r in list(self.db["equipment_rates"]):
            self.db.tables["equipment_rates"].remove(r)
        S.add_equipment_rate(self.db, "TEST-EQR-1", "EQ-PTROWEL", **rate_kw)
        r = Engine(self.db).unit_cost(self.CON, 1, S.params())
        return r, [ln for ln in r.lines if ln["line_kind"] == "equipment"][0]

    def test_fuel_is_added_when_the_rate_excludes_it(self):
        r, ln = self.eq(rate_hr=25, fuel_included=False, fuel_cost=9, delivery=75, min_rental="4 hours")
        self.assertAlmostEqual(float(ln["unit_cost"]), (25 + 9) * 8 / 2000, places=8)          # the review dropped the fuel
        flags = " ".join(ln["warnings"])
        self.assertIn("FUEL_ADDED_SEPARATELY", flags)
        self.assertIn("EQUIPMENT_DELIVERY_PICKUP_EXCLUDED:75", flags)
        self.assertIn("MIN_RENTAL_PERIOD_ASSUMED_MET:4 hours", flags)

    def test_unpriced_fuel_is_a_gap_not_a_flag(self):
        r, ln = self.eq(rate_hr=25, fuel_included=False)
        self.assertIsNone(ln["extended_cost"])
        self.assertIn("FUEL_NOT_PRICED", codes(r))

    def test_unknown_fuel_inclusion_is_flagged(self):
        r, ln = self.eq(rate_hr=25, fuel_included=None)
        self.assertIn("FUEL_INCLUSION_UNKNOWN", ln["warnings"])

    def test_equipment_component_needs_the_equipment_in_the_crew(self):
        S.set_crew(self.db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False)])
        r, ln = self.eq(rate_hr=25)
        self.assertIsNone(ln["extended_cost"])                                     # the review priced it at 0 / observed
        self.assertIn("CREW_NO_EQUIPMENT", codes(r))
        self.assertEqual(r.status, "failed")

    def test_operator_is_recognised_by_trade_not_only_by_the_flag(self):
        self.crew3()
        r, ln = self.eq(rate_hr=25, operator_included=True)
        self.assertIn("OPERATOR_DOUBLE_COUNT", codes(r))
        self.assertEqual(r.status, "failed")

    def test_equipment_that_needs_an_operator_nobody_priced_is_a_gap(self):
        S.set_crew(self.db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False), ("equipment", "EQ-CPUMP", 1, False)])
        wic = next(c for c in self.db["work_item_components"] if c["work_item_id"] == self.CON and c["component_kind"] == "equipment")
        wic["equipment_type_code"] = "EQ-CPUMP"
        S.add_equipment_rate(self.db, "TEST-EQR-2", "EQ-CPUMP", rate_hr=60, operator_included=False)
        r = Engine(self.db).unit_cost(self.CON, 1, S.params())
        self.assertIn("OPERATOR_NOT_PRICED", codes(r))
        self.assertEqual(r.status, "incomplete")

    def test_person_hours_use_member_hours(self):
        self.crew3()
        next(m for m in self.db["crew_members"] if m["trade_code"] == "TR-OPR")["hours_per_shift"] = D("10")
        r, ln = self.eq(rate_hr=25)
        lab = [x for x in r.lines if x["line_kind"] == "labor"][0]
        self.assertAlmostEqual(float(lab["quantity"]), (2 * 8 + 10) / 2000, places=9)      # the review reported 3 x 8 / 2000
        self.assertAlmostEqual(float(lab["unit_cost"]), (2 * 8 * 45 + 10 * 55) / 2000, places=8)
        self.assertEqual(lab["quantity_kind"], "person_hours")
        self.assertEqual(ln["quantity_kind"], "equipment_hours")

    def test_day_rate_is_charged_once_per_crew_shift_and_says_so(self):
        for r_ in list(self.db["equipment_rates"]):
            self.db.tables["equipment_rates"].remove(r_)
        S.add_equipment_rate(self.db, "TEST-EQR-1", "EQ-PTROWEL", rate_day=180)
        r = Engine(self.db).unit_cost(self.CON, 1, S.params(equipment_basis="rental_day"))
        ln = [x for x in r.lines if x["line_kind"] == "equipment"][0]
        self.assertAlmostEqual(float(ln["unit_cost"]), 180 / 2000, places=8)
        self.assertIn("DAY_RATE_ONE_DAY_PER_CREW_SHIFT", ln["warnings"])


class F017TimeIndex(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_labor_index_does_not_adjust_a_material_price(self):
        obs(self.db, "TEST-OBS-BOARDA")["observed_at"] = date(2025, 6, 1)
        obs(self.db, "TEST-OBS-BOARDA")["retrieved_at"] = "2025-06-02T00:00:00+00:00"
        S.add_index(self.db, "TEST-IDX-LAB", {date(2025, 6, 1): 100, date(2026, 9, 1): 140, date(2026, 10, 1): 150}, applies_to="labor")
        r = run(self.db, time_index_id="TEST-IDX-LAB")
        self.assertEqual(r.status, "failed")                      # a series of the wrong cost kind is a logical conflict
        self.assertIn("INDEX_APPLIES_TO_MISMATCH", codes(r))

    def test_recent_price_of_another_month_is_adjusted_too(self):
        obs(self.db, "TEST-OBS-BOARDA")["observed_at"] = date(2026, 1, 10)            # 287 days old: under any age limit
        obs(self.db, "TEST-OBS-BOARDA")["retrieved_at"] = "2026-01-11T00:00:00+00:00"
        S.add_index(self.db, "TEST-IDX-1", {date(2026, 1, 1): 100, date(2026, 9, 1): 120, date(2026, 10, 1): 125})
        r = run(self.db, time_index_id="TEST-IDX-1")
        self.assertAlmostEqual(float(board(r)["extended_cost"]), 1.10 * 0.40 * 1.25, places=8)
        self.assertIn("TIME_INDEXED_PRICE", board(r)["warnings"])

    def test_unpublished_as_of_month_falls_back_to_the_latest_published_period_and_says_so(self):
        obs(self.db, "TEST-OBS-BOARDA")["observed_at"] = date(2026, 1, 10)
        obs(self.db, "TEST-OBS-BOARDA")["retrieved_at"] = "2026-01-11T00:00:00+00:00"
        S.add_index(self.db, "TEST-IDX-1", {date(2026, 1, 1): 100, date(2026, 8, 1): 118, date(2026, 9, 1): 120})       # no October yet
        r = run(self.db, time_index_id="TEST-IDX-1")
        self.assertEqual(r.status, "complete", r.run["missing_inputs"])
        self.assertAlmostEqual(float(board(r)["extended_cost"]), 1.10 * 0.40 * 1.20, places=8)
        self.assertIn("INDEX_LATEST_PUBLISHED_PERIOD_USED:2026-09-01", board(r)["warnings"])

    def test_price_of_another_month_without_index_is_flagged(self):
        r = run(self.db)
        self.assertIn("PRICE_NOT_TIME_ADJUSTED", board(r)["warnings"])

    def test_index_values_published_after_known_at_are_not_used(self):
        obs(self.db, "TEST-OBS-BOARDA")["observed_at"] = date(2026, 1, 10)
        obs(self.db, "TEST-OBS-BOARDA")["retrieved_at"] = "2026-01-11T00:00:00+00:00"
        S.add_index(self.db, "TEST-IDX-1", {date(2026, 1, 1): 100, date(2026, 9, 1): 120, date(2026, 10, 1): 125}, vintage=date(2026, 10, 20))
        self.assertEqual(run(self.db, time_index_id="TEST-IDX-1", as_of=date(2026, 10, 15)).status, "incomplete")


class F018RetailBasis(unittest.TestCase):
    def test_retail_is_an_explicit_opt_in_recorded_on_the_run(self):
        db = S.priced_drywall_db()
        strict = RunParams(region_id=S.REGION, as_of=S.AS_OF, labor_basis="company_actual", allow_synthetic=True, run_at=S.RUN_AT)
        r = Engine(db).unit_cost(WI, 1, strict)
        self.assertEqual(r.status, "incomplete")
        self.assertIn("PRICE_MISSING", codes(r))
        r2 = run(db)
        self.assertEqual((r2.status, r2.run["price_basis"], r2.run["input_review_floor"]), ("complete", "retail_proxy", "validated"))
        with self.assertRaises(ValueError):
            RunParams(region_id=S.REGION, as_of=S.AS_OF, channels=("retail_public",))

    def test_contractor_quote_basis(self):
        db = S.priced_drywall_db()
        for o in db["price_observations"]:
            o["price_channel"] = "supplier_quote"
        r = Engine(db).unit_cost(WI, 1, RunParams(region_id=S.REGION, as_of=S.AS_OF, labor_basis="company_actual", allow_synthetic=True, run_at=S.RUN_AT))
        self.assertEqual(r.run["price_basis"], "contractor_quote")
        obs(db, "TEST-OBS-SCREW")["price_channel"] = "retail_public"
        r2 = run(db)
        self.assertEqual(r2.run["price_basis"], "mixed")

    def test_review_floor_is_recorded(self):
        db = S.priced_drywall_db()
        self.assertEqual(run(db, min_review="unreviewed").run["input_review_floor"], "unreviewed")

    def test_assembly_inherits_the_basis(self):
        r = Engine(S.assembly_db()).assembly_cost("TEST-ASM-1", 1, S.params())
        self.assertEqual(r.run["price_basis"], "retail_proxy")


class F019Markup(unittest.TestCase):
    def kw(self, **over):
        d = dict(overhead_pct=D("0.10"), overhead_basis="b", contingency_pct=D("0.05"), contingency_basis="b", profit_method="markup",
                 profit_value=D("0.10"), profit_basis="b")
        d.update(over)
        return d

    def test_price_is_kept_apart_from_direct_cost(self):
        r = run(S.priced_drywall_db())
        m = apply_markup(r, **self.kw())
        self.assertEqual(m.run["direct_cost_total"], r.run["direct_cost_total"])
        self.assertEqual(m.run["price_total"], (r.total * D("1.1") * D("1.05") * D("1.1")).quantize(D("0.000001")))
        self.assertTrue(all(ln["inputs"] for ln in m.lines))
        self.assertEqual(m.run["price_basis"], "retail_proxy")

    def test_out_of_range_percentages_are_refused(self):
        r = run(S.priced_drywall_db())
        for bad in (dict(overhead_pct=D("10")), dict(overhead_pct=D("-0.1")), dict(contingency_pct=D("1.5")), dict(profit_value=D("-2")),
                    dict(profit_method="margin", profit_value=D("1")), dict(profit_method="margin", profit_value=D("-0.5"))):
            with self.assertRaises(ValueError, msg=str(bad)):
                apply_markup(r, **self.kw(**bad))

    def test_basis_text_is_part_of_the_run_id(self):
        r = run(S.priced_drywall_db())
        self.assertNotEqual(apply_markup(r, **self.kw()).run["run_id"], apply_markup(r, **self.kw(overhead_basis="other basis")).run["run_id"])

    def test_markup_of_a_markup_is_refused(self):
        r = run(S.priced_drywall_db())
        with self.assertRaises(ValueError):
            apply_markup(apply_markup(r, **self.kw()), **self.kw())


class F036F037F038F040F041(unittest.TestCase):
    def test_run_params_are_validated(self):
        for bad in (dict(labor_basis="bogus"), dict(mode="Strict"), dict(min_review="x"), dict(price_policy="p"), dict(project_type="x"),
                    dict(burden_base="x"), dict(equipment_basis="x"), dict(wage_regime="x"), dict(wage_class="x"), dict(quantity=D("0")),
                    dict(annual_paid_hours=D("-1")), dict(max_price_age_days=-5), dict(channels=("nope",))):
            with self.assertRaises(ValueError, msg=str(bad)):
                S.params(**bad)

    def test_company_rate_that_includes_overhead_or_profit_is_unusable(self):
        db = S.priced_drywall_db()
        for flag in ("includes_overhead", "includes_profit"):
            d2 = S.clone(db)
            row(d2, "labor_rates", "labor_rate_id", "TEST-LRT-DRYW")[flag] = True
            r = run(d2)
            self.assertEqual(r.status, "incomplete", flag)
            self.assertIn("LABOR_RATE_MISSING", codes(r))

    def test_derived_loaded_rate_takes_region_and_period_from_the_governing_wage(self):
        db = S.real_db()
        S.add_source(db)
        S.add_stat_wage(db, "TEST-W1", "TR-DRYW", 30, region="REG-US-CA", effective_from=date(2026, 5, 1))
        S.add_all_burdens(db)
        res = Engine(db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", annual_paid_hours=D(2080)))
        self.assertEqual(res.status, "complete", res.run["missing_inputs"])
        lr = res.derived_rows["labor_rates"][0]
        self.assertEqual((lr["region_id"], lr["effective_from"]), ("REG-US-CA", date(2026, 5, 1)))
        self.assertIn("RATE_FROM_ANCESTOR_REGION:REG-US-CA", res.run["warnings"])
        self.assertEqual(lr["payroll_tax_hr"], lr["payroll_tax_hr"].quantize(D("0.0000000001")))

    def test_rows_retrieved_after_known_at_are_unknown_to_the_run(self):
        db = S.priced_drywall_db()
        obs(db, "TEST-OBS-BOARDA")["retrieved_at"] = "2026-10-23T12:00:00+00:00"
        self.assertEqual(run(db, as_of=date(2026, 9, 10)).status, "incomplete")      # the review: complete
        self.assertEqual(run(db, as_of=date(2026, 9, 10), known_at=date(2026, 10, 24)).status, "complete")
        self.assertEqual(run(db).status, "complete")

    def test_retired_future_and_unreviewed_definitions(self):
        for name, upd, code in (("retired", dict(status="retired"), "DEFINITION_RETIRED"), ("future", dict(valid_from=date(2030, 1, 1)), "DEFINITION_NOT_YET_VALID"),
                                ("rejected", dict(review_status="rejected"), "DEFINITION_REJECTED"), ("unreviewed", dict(review_status="unreviewed"), "DEFINITION_NOT_REVIEWED")):
            db = S.priced_drywall_db()
            row(db, "work_items", "work_item_id", WI).update(upd)
            r = run(db)
            self.assertIn(code, codes(r), name)
            self.assertNotEqual(r.status, "complete", name)
            self.assertEqual(r.status, "incomplete" if name == "unreviewed" else "failed", name)
        db = S.priced_drywall_db()
        row(db, "work_items", "work_item_id", WI)["review_status"] = "unreviewed"
        self.assertEqual(run(db, min_review="unreviewed").status, "complete")

    def test_optional_components_are_priced_only_when_selected(self):
        db = S.priced_drywall_db()
        comp(db, WI, "CAT-FRM-FAS")["is_optional"] = True
        r = run(db)
        self.assertEqual(r.run["material_cost"], D("0.440000"))
        self.assertTrue(any(w.startswith("OPTIONAL_COMPONENT_EXCLUDED") for w in r.run["warnings"]))
        self.assertEqual(run(db, include_optional=True).run["material_cost"], D("0.449188"))

    def test_duplicate_cost_tags_are_a_double_counting_failure(self):
        db = S.priced_drywall_db()
        for c in db["work_item_components"]:
            if c["work_item_id"] == WI and c["component_kind"] == "material":
                c["cost_tags"] = ["fasteners"]
        r = run(db)
        self.assertEqual(r.status, "failed")
        self.assertIn("DUPLICATE_COST_TAG", codes(r))

    def test_assembly_cost_tags_too(self):
        db = S.assembly_db()
        for c in db["assembly_components"]:
            c["cost_tags"] = ["x"]
        r = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params())
        self.assertEqual(r.status, "failed")
        self.assertIn("DUPLICATE_COST_TAG", codes(r))

    def test_work_item_without_priced_lines_is_not_a_zero_cost_result(self):
        db = S.priced_drywall_db()
        for c in db["work_item_components"]:
            if c["work_item_id"] == WI:
                c["is_optional"] = True
        r = run(db)
        self.assertEqual(r.status, "incomplete")
        self.assertIn("NO_COST_LINES", codes(r))


if __name__ == "__main__":
    unittest.main()
