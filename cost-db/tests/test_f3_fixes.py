"""Regression tests for the defects found by the independent re-check F3 (docs/independent_review_F3.md, ids F3-nn) and for the
fixes that F3's mutation analysis showed to have no failing test. All inputs are SYNTHETIC (TEST- ids)."""
import decimal
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "pipeline")]

from costdb.calc import Engine, RunParams  # noqa: E402
from tests.fixtures import synthetic as S  # noqa: E402

WI = S.WI
CON = "WI-CON-001"


def run(db, wi=WI, **kw):
    return Engine(db).unit_cost(wi, 1, S.params(**kw))


def codes(r):
    return {m["code"] for m in r.run["missing_inputs"]}


def line(r, kind, n=0):
    return [ln for ln in r.lines if ln["line_kind"] == kind][n]


def board(r):
    return [ln for ln in r.lines if ln["line_kind"] == "material" and "board" in ln["description"].lower()][0]


def obs(db, oid):
    return next(o for o in db["price_observations"] if o["observation_id"] == oid)


def row(db, table, key, val):
    return next(r for r in db[table] if r[key] == val)


def con_db(**eq):
    """WI-CON-001 labor + equipment lines resolvable: crew 2 finishers + 1 power trowel, 2000 SF/shift (other lines stay unresolved)."""
    db = S.real_db()
    S.validate_definitions(db)
    S.trust_regions(db)
    S.add_source(db)
    S.add_labor_actual(db, "TEST-LRT-CEM", "TR-CEM", 45)
    S.set_crew(db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False), ("equipment", "EQ-PTROWEL", 1, False)])
    S.set_productivity(db, CON, 2, 8, 2000)
    if eq is not None:
        S.add_equipment_rate(db, "TEST-EQR-1", "EQ-PTROWEL", **(eq or dict(rate_hr=25)))
    return db


class F302EngineTrustsOnlyFetchedSources(unittest.TestCase):
    def test_a_source_never_fetched_cannot_carry_a_verified_result(self):
        db = S.priced_drywall_db()
        row(db, "sources", "source_id", S.SRC)["verification_method"] = "search_snippet_only"
        r = run(db)
        self.assertEqual(r.status, "incomplete")
        self.assertIn("never fetched", " ".join(m["reason"] for m in r.run["missing_inputs"]))
        self.assertEqual(run(db, min_review="unreviewed").status, "complete")          # exploration may use snippet-level sources

    def test_a_crew_from_an_unfetched_source_is_refused(self):
        db = S.priced_drywall_db()
        S.add_source(db, "TEST-SRC-SNIPC", method="search_snippet_only", review="unreviewed")
        row(db, "crews", "crew_id", "CRW-DRY-HANG")["source_id"] = "TEST-SRC-SNIPC"
        r = run(db)
        self.assertIn("CREW_UNUSABLE", codes(r))


class F304DayRateFuel(unittest.TestCase):
    def test_fuel_is_added_on_the_day_rate_path_too(self):
        db = con_db(rate_hr=25, rate_day=150, fuel_included=False, fuel_cost=9)
        hourly = line(Engine(db).unit_cost(CON, 1, S.params()), "equipment")
        day = line(Engine(db).unit_cost(CON, 1, S.params(equipment_basis="rental_day")), "equipment")
        self.assertAlmostEqual(float(hourly["unit_cost"]), (25 + 9) * 8 / 2000, places=8)
        self.assertAlmostEqual(float(day["unit_cost"]), (150 + 9 * 8) / 2000, places=8)          # the review got 150/2000
        self.assertIn("FUEL_ADDED_SEPARATELY", day["warnings"])

    def test_day_rate_without_a_fuel_price_is_a_gap_and_unknown_fuel_is_flagged(self):
        db = con_db(rate_day=150, fuel_included=False)
        r = Engine(db).unit_cost(CON, 1, S.params(equipment_basis="rental_day"))
        self.assertIn("FUEL_NOT_PRICED", codes(r))
        db = con_db(rate_day=150, fuel_included=None)
        ln = line(Engine(db).unit_cost(CON, 1, S.params(equipment_basis="rental_day")), "equipment")
        self.assertIn("FUEL_INCLUSION_UNKNOWN", ln["warnings"])


class F305PinnedRates(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        S.add_labor_actual(self.db, "TEST-LRT-NEW", "TR-DRYW", 100)
        row(self.db, "labor_rates", "labor_rate_id", "TEST-LRT-NEW")["effective_from"] = date(2026, 6, 1)

    def pin(self, rid):
        for m in self.db["crew_members"]:
            if m["trade_code"] == "TR-DRYW":
                m["labor_rate_id"] = rid

    def test_unpinned_takes_the_newest_row_pinned_takes_the_pinned_one(self):
        self.assertEqual(run(self.db).run["labor_cost"], D("1.150000"))           # (2 x 100 + 30) x 8 / 1600
        self.pin("TEST-LRT-DRYW")
        r = run(self.db)
        self.assertEqual(r.run["labor_cost"], D("0.550000"))                      # the review: the pin was ignored
        self.assertTrue(any(i.get("pinned") for i in line(r, "labor")["inputs"]))
        self.assertIn("TEST-LRT-DRYW", [i["id"] for i in line(r, "labor")["inputs"]])

    def test_an_unusable_pin_is_never_replaced_by_an_automatic_pick(self):
        self.pin("TEST-LRT-DRYW")
        row(self.db, "labor_rates", "labor_rate_id", "TEST-LRT-DRYW")["review_status"] = "flagged"
        r = run(self.db)
        self.assertEqual(r.status, "incomplete")
        self.assertIn("LABOR_RATE_PIN_UNUSABLE", codes(r))
        self.pin("TEST-LRT-NOPE")
        self.assertIn("LABOR_RATE_PIN_UNKNOWN", codes(run(self.db)))

    def test_a_pinned_equipment_rate(self):
        db = con_db(rate_hr=25)
        S.add_equipment_rate(db, "TEST-EQR-2", "EQ-PTROWEL", rate_hr=40, effective_from=date(2026, 6, 1))
        self.assertAlmostEqual(float(line(Engine(db).unit_cost(CON, 1, S.params()), "equipment")["unit_cost"]), 40 * 8 / 2000, places=8)
        next(m for m in db["crew_members"] if m["member_kind"] == "equipment")["equipment_rate_id"] = "TEST-EQR-1"
        self.assertAlmostEqual(float(line(Engine(db).unit_cost(CON, 1, S.params()), "equipment")["unit_cost"]), 25 * 8 / 2000, places=8)


class F307F308RangesAndZeroPrices(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_a_zero_or_negative_price_is_not_a_price(self):
        for v in (D("0"), D("-3")):
            db = S.clone(self.db)
            obs(db, "TEST-OBS-BOARDA")["price_amount"] = v
            r = run(db)
            self.assertEqual(r.status, "incomplete")
            self.assertIn("PRICE_MISSING", codes(r))
            self.assertIn("out of range", " ".join(m["reason"] for m in r.run["missing_inputs"]))

    def test_waste_outside_zero_one_fails(self):
        for v in (D("5"), D("-0.5"), D("1")):
            db = S.clone(self.db)
            next(c for c in db["work_item_components"] if c["work_item_id"] == WI and "CAT-DRY-BRD" in (c["product_spec_key"] or ""))["waste_factor"] = v
            r = run(db)
            self.assertEqual(r.status, "failed", v)
            self.assertIn("WASTE_INVALID", codes(r))

    def test_negative_wage_daily_output_or_crew_shift_are_unusable(self):
        for table, key, val, fld, code in (("labor_rates", "labor_rate_id", "TEST-LRT-DRYW", "total_hr", "LABOR_RATE_MISSING"),
                                           ("productivity_observations", "work_item_id", WI, "daily_output", "PRODUCTIVITY_MISSING")):
            db = S.clone(self.db)
            row(db, table, key, val)[fld] = D("-5")
            if table == "labor_rates":
                row(db, table, key, val)["base_wage_hr"] = D("-5")
            r = run(db)
            self.assertEqual(r.status, "incomplete", fld)
            self.assertIn(code, codes(r))
            self.assertIsNone(r.run["direct_cost_total"])
        db = S.clone(self.db)
        row(db, "crews", "crew_id", "CRW-DRY-HANG")["shift_hours"] = D("30")
        self.assertIn("CREW_UNUSABLE", codes(run(db)))


class F309TierRanking(unittest.TestCase):
    def build(self, id_base, id_tier):
        db = S.priced_drywall_db()
        db.tables["price_observations"] = [o for o in db["price_observations"] if o["observation_id"] != "TEST-OBS-BOARDA"]
        S.add_obs(db, id_base, "TEST-PRD-BOARDA", "12.80", 32, "SF")                                   # 0.40 / SF
        S.add_obs(db, id_tier, "TEST-PRD-BOARDA", "9.60", 32, "SF")                                    # 0.30 / SF from 100 SF
        obs(db, id_tier)["qty_tier_min"] = D("100")
        return db

    def test_the_tier_that_applies_wins_whatever_the_ids(self):
        for ids in (("A1", "B2"), ("B2", "A1")):
            db = self.build("TEST-OBS-" + ids[0], "TEST-OBS-" + ids[1])
            big = run(db, quantity=D("5000"))
            self.assertAlmostEqual(float(board(big)["extended_cost"]), 1.1 * 0.30, places=8, msg=ids)
            self.assertIn("SEVERAL_PRICE_TIERS_ELIGIBLE", board(big)["warnings"])
            small = run(db, quantity=D("50"))
            self.assertAlmostEqual(float(board(small)["extended_cost"]), 1.1 * 0.40, places=8, msg=ids)
            self.assertAlmostEqual(float(board(run(db))["extended_cost"]), 1.1 * 0.40, places=8, msg=ids)       # no quantity: tier prices unusable


class F310AssumedFactorsAreFlagged(unittest.TestCase):
    def test_assumed_factor_marks_run_and_line(self):
        db = S.priced_drywall_db()
        S.add_factor(db, "TEST-ADJ-AF", "productivity_condition", "labor", "1.20", condition="occupied_building", origin="assumed")
        self.assertIn("CONDITION_FACTOR_UNUSABLE", codes(run(db, conditions=("occupied_building",))))               # strict: refused
        r = run(db, mode="with_assumptions", conditions=("occupied_building",))
        self.assertEqual(r.status, "complete")
        self.assertTrue(r.run["has_assumptions"])
        self.assertEqual(line(r, "labor")["origin_summary"], "assumed")
        self.assertIn("ASSUMED_FACTOR:TEST-ADJ-AF", line(r, "labor")["warnings"])

    def test_assumed_region_factor_and_assumed_product(self):
        db = S.priced_drywall_db()
        obs(db, "TEST-OBS-BOARDA")["region_id"] = "REG-CA-073"
        S.add_factor(db, "TEST-ADJ-R", "region", "material", "1.05", from_region="REG-CA-073", to_region="REG-CA-037", origin="assumed")
        r = run(db, mode="with_assumptions", use_region_factors=True)
        self.assertTrue(r.run["has_assumptions"])
        self.assertIn("ASSUMED_REGION_FACTOR:TEST-ADJ-R", board(r)["warnings"])
        db = S.priced_drywall_db()
        row(db, "products", "product_id", "TEST-PRD-BOARDA")["origin"] = "assumed"
        r2 = run(db, mode="with_assumptions")
        self.assertTrue(r2.run["has_assumptions"])
        self.assertIn("ASSUMED_PRODUCT:TEST-PRD-BOARDA", board(r2)["warnings"])
        self.assertEqual(run(db).status, "incomplete")


class F311StrictModeDoesNotReadAssumedReferenceData(unittest.TestCase):
    def build(self, trust=True):
        db = S.real_db()
        db.tables["burden_rates"] = []                       # the few real (unreviewed) burden rows would tie with the synthetic ones
        db.tables["labor_rates"] = []
        if trust:
            S.trust_regions(db)
        S.add_source(db)
        S.add_stat_wage(db, "TEST-W1", "TR-DRYW", 30)
        S.add_all_burdens(db)
        return db

    P = dict(labor_basis="stat_loaded", annual_paid_hours=D(2080))

    def test_unreviewed_assumed_hierarchy_is_not_followed_in_strict_mode(self):
        res = Engine(self.build(trust=False)).loaded_labor_rate("TR-DRYW", S.params(**self.P))
        self.assertEqual(res.status, "incomplete")                     # the wage sits at REG-MD-31084; the link LA -> MD is an unreviewed assumption
        self.assertIn("LABOR_RATE_MISSING", codes(res))
        self.assertEqual(Engine(self.build()).loaded_labor_rate("TR-DRYW", S.params(**self.P)).status, "complete")

    def test_exploration_modes_may_use_it(self):
        db = self.build(trust=False)
        res = Engine(db).loaded_labor_rate("TR-DRYW", S.params(mode="with_assumptions", min_review="unreviewed", **self.P))
        self.assertEqual(res.status, "complete", res.run["missing_inputs"])
        self.assertIn("RATE_FROM_ANCESTOR_REGION:REG-MD-31084", res.run["warnings"])

    def test_a_rejected_region_cuts_the_chain(self):
        db = self.build()
        row(db, "regions", "region_id", "REG-MD-31084")["review_status"] = "rejected"
        self.assertEqual(Engine(db).loaded_labor_rate("TR-DRYW", S.params(**self.P)).status, "incomplete")
        db = self.build()
        row(db, "regions", "region_id", "REG-CA-037")["review_status"] = "rejected"
        self.assertEqual(Engine(db).loaded_labor_rate("TR-DRYW", S.params(**self.P)).status, "incomplete")

    def test_unknown_state_makes_payroll_items_unresolvable_not_omitted(self):
        db = self.build()
        for r in db["regions"]:
            r["state_code"] = None
        res = Engine(db).loaded_labor_rate("TR-DRYW", S.params(**self.P))
        self.assertEqual(res.status, "incomplete")
        self.assertIn("REGION_STATE_UNKNOWN", codes(res))

    def test_a_rejected_equipment_type_is_not_used(self):
        db = con_db(rate_hr=25)
        row(db, "equipment_types", "equipment_type_code", "EQ-PTROWEL")["review_status"] = "rejected"
        r = Engine(db).unit_cost(CON, 1, S.params())
        self.assertIn("EQUIPMENT_TYPE_UNUSABLE", codes(r))

    def test_trades_that_are_rejected_are_not_used(self):
        db = S.priced_drywall_db()
        row(db, "trades", "trade_code", "TR-DRYW")["review_status"] = "rejected"
        self.assertIn("TRADE_UNUSABLE", codes(run(db)))


class F312EquipmentRateBasis(unittest.TestCase):
    def build(self):
        db = con_db(rate_hr=25)
        S.add_equipment_rate(db, "TEST-EQR-2", "EQ-PTROWEL", rate_hr=18, effective_from=date(2026, 6, 1))
        row(db, "equipment_rates", "equipment_rate_id", "TEST-EQR-2")["rate_basis"] = "dot_schedule"
        return db

    def test_different_bases_are_ambiguous_unless_named(self):
        db = self.build()
        r = Engine(db).unit_cost(CON, 1, S.params())
        self.assertIn("EQUIPMENT_RATE_AMBIGUOUS", codes(r))
        ln = line(Engine(db).unit_cost(CON, 1, S.params(equipment_rate_basis="rental_market")), "equipment")
        self.assertAlmostEqual(float(ln["unit_cost"]), 25 * 8 / 2000, places=8)
        self.assertEqual([i for i in ln["inputs"] if i["table"] == "equipment_rates"][0]["rate_basis"], "rental_market")
        ln = line(Engine(db).unit_cost(CON, 1, S.params(equipment_rate_basis="dot_schedule")), "equipment")
        self.assertAlmostEqual(float(ln["unit_cost"]), 18 * 8 / 2000, places=8)

    def test_capacities_are_not_interchangeable_either(self):
        db = con_db(rate_hr=25)
        row(db, "equipment_rates", "equipment_rate_id", "TEST-EQR-1")["capacity_raw"] = "36 in"
        S.add_equipment_rate(db, "TEST-EQR-2", "EQ-PTROWEL", rate_hr=30)
        row(db, "equipment_rates", "equipment_rate_id", "TEST-EQR-2")["capacity_raw"] = "48 in"
        self.assertIn("EQUIPMENT_RATE_AMBIGUOUS", codes(Engine(db).unit_cost(CON, 1, S.params())))
        ln = line(Engine(db).unit_cost(CON, 1, S.params(equipment_capacity="48 IN")), "equipment")
        self.assertAlmostEqual(float(ln["unit_cost"]), 30 * 8 / 2000, places=8)

    def test_equipment_hours_follow_a_productivity_condition(self):
        db = con_db(rate_hr=25)
        S.add_factor(db, "TEST-ADJ-E", "productivity_condition", "equipment", "1.20", condition="occupied_building")
        S.add_factor(db, "TEST-ADJ-L", "productivity_condition", "labor", "1.20", condition="occupied_building")
        r = Engine(db).unit_cost(CON, 1, S.params(conditions=("occupied_building",)))
        eq = line(r, "equipment")
        self.assertAlmostEqual(float(eq["quantity"]), 8 / 2000 * 1.2, places=9)                 # hours x rate = unit cost again
        self.assertAlmostEqual(float(eq["unit_cost"]), 25 * eq["quantity"].__float__(), places=8)


class F314F32PriceChoice(unittest.TestCase):
    def test_retail_promo_channel_is_a_promotion_even_without_the_flag(self):
        db = S.priced_drywall_db()
        obs(db, "TEST-OBS-BOARDA")["price_channel"] = "retail_promo"
        r = run(db)
        self.assertEqual(r.status, "incomplete")
        self.assertIn("promotional", " ".join(m["reason"] for m in r.run["missing_inputs"]))

    def test_a_quote_beats_a_newer_retail_price(self):
        db = S.priced_drywall_db()
        S.add_obs(db, "TEST-OBS-QUOTE", "TEST-PRD-BOARDA", "9.60", 32, "SF", channel="supplier_quote", observed=date(2026, 8, 1))   # 0.30, older
        r = run(db)
        self.assertAlmostEqual(float(board(r)["extended_cost"]), 1.1 * 0.30, places=8)
        self.assertEqual(r.lines[0]["inputs"][-1]["price_channel"], "supplier_quote")
        self.assertEqual(r.run["price_basis"], "mixed")                     # the screws are still retail

    def test_single_product_and_excluded_products_are_flagged(self):
        db = S.priced_drywall_db()
        self.assertIn("SINGLE_PRODUCT_PRICE", board(run(db))["warnings"])
        db = S.paint_db()
        row(db, "products", "product_id", "TEST-PRD-PB")["review_status"] = "flagged"
        ln = [x for x in Engine(db).unit_cost(S.PNT, 1, S.params()).lines if x["line_kind"] == "material"][0]
        self.assertIn("PRODUCTS_EXCLUDED:1", ln["warnings"])
        self.assertIn("SINGLE_PRODUCT_PRICE", ln["warnings"])


class F316RunIdIgnoresRowOrder(unittest.TestCase):
    def test_reversing_every_table_changes_nothing(self):
        db = S.paint_db()
        a = Engine(db).unit_cost(S.PNT, 1, S.params())
        db2 = S.clone(db)
        for t in ("products", "price_observations", "product_consumption", "crew_members", "labor_rates", "adjustment_factors", "work_item_components"):
            db2.tables[t].reverse()
        b = Engine(db2).unit_cost(S.PNT, 1, S.params())
        self.assertEqual((a.run["run_id"], a.run["direct_cost_total"]), (b.run["run_id"], b.run["direct_cost_total"]))
        self.assertEqual([x["formula"] for x in a.lines], [x["formula"] for x in b.lines])


class F317DuplicateComponents(unittest.TestCase):
    def test_a_repeated_labor_component_would_double_the_cost(self):
        db = S.priced_drywall_db()
        lab = next(c for c in db["work_item_components"] if c["work_item_id"] == WI and c["component_kind"] == "labor")
        dup = dict(lab)
        dup.update(component_id="TEST-WIC-DUPLAB", line_no=99, cost_tags=[])
        db["work_item_components"].append(dup)
        r = run(db)
        self.assertEqual(r.status, "failed")
        self.assertIn("DUPLICATE_COMPONENT", codes(r))

    def test_the_same_child_twice_in_an_assembly(self):
        db = S.assembly_db()
        db.add("assembly_components", {"assembly_component_id": "TEST-ASC-3", "assembly_id": "TEST-ASM-1", "assembly_version": 1, "line_no": 3,
                                       "work_item_id": "TEST-WI-9", "work_item_version": 1, "qty_per_assembly_unit": D("3"), "qty_unit_id": "EA",
                                       "qty_formula": "synthetic", "qty_origin": "derived", "cost_tags": [], "notes": None})
        r = Engine(db).assembly_cost("TEST-ASM-1", 1, S.params())
        self.assertEqual(r.status, "failed")
        self.assertIn("DUPLICATE_COMPONENT", codes(r))


class F319F320Parameters(unittest.TestCase):
    def test_engine_is_independent_of_the_ambient_decimal_precision(self):
        db = S.priced_drywall_db()
        want = run(db).run["direct_cost_total"]
        with decimal.localcontext() as ctx:
            ctx.prec = 12
            r = run(db)
            self.assertEqual(r.run["direct_cost_total"], want)
            self.assertEqual(Engine(db).labor_rate("TR-DRYW", S.params())["total_hr"], D("40"))

    def test_bad_parameters_are_refused(self):
        for bad in (dict(known_at=datetime(2026, 10, 24, 12)), dict(annual_paid_hours=D("Infinity")), dict(quantity=D("NaN")),
                    dict(annual_paid_hours=D("9000")), dict(equipment_rate_basis="made_up"), dict(equipment_capacity="  ")):
            with self.assertRaises(ValueError, msg=str(bad)):
                S.params(**bad)
        db = S.priced_drywall_db()
        with self.assertRaises(ValueError):
            Engine(db).unit_cost(WI, 1, S.params(region_id="REG-NOPE"))
        with self.assertRaises(ValueError):
            Engine(db).unit_cost(WI, 1, S.params(time_index_id="TEST-NO-SUCH-INDEX"))


class F325F327Diagnostics(unittest.TestCase):
    def test_an_unusable_assumption_says_why(self):
        db = S.priced_drywall_db()
        c = next(c for c in db["work_item_components"] if c["work_item_id"] == WI and "CAT-DRY-BRD" in (c["product_spec_key"] or ""))
        c.update(waste_factor=None, waste_origin=None, waste_basis=None)
        S.add_assumption(db, "TEST-ASU-BAD", "waste", f"waste:{c['component_id']}", "5")
        r = run(db, mode="with_assumptions")
        why = " ".join(m["reason"] for m in r.run["missing_inputs"] if m["code"] == "WASTE_MISSING")
        self.assertIn("TEST-ASU-BAD", why)
        self.assertIn("outside [0,1)", why)

    def test_coverage_in_an_incompatible_unit_says_why(self):
        db = S.paint_db()
        for c in db["product_consumption"]:
            c["coverage_unit_id"] = "LF"
        r = Engine(db).unit_cost(S.PNT, 1, S.params())
        why = " ".join(m["reason"] for m in r.run["missing_inputs"] if m["code"] == "CONSUMPTION_MISSING")
        self.assertIn("cannot be converted", why)

    def test_malformed_rows_give_a_data_error_not_a_traceback(self):
        for table, key, val, fld in (("price_observations", "observation_id", "TEST-OBS-BOARDA", "observed_at"),
                                     ("crews", "crew_id", "CRW-DRY-HANG", "shift_hours"),
                                     ("work_item_components", "work_item_id", WI, "qty_per_unit")):
            db = S.priced_drywall_db()
            row(db, table, key, val)[fld] = "oops" if fld != "observed_at" else None
            r = run(db)
            self.assertIn(r.status, ("failed", "incomplete"), fld)
            self.assertIsNone(r.run["direct_cost_total"], fld)

    def test_rate_inputs_carry_their_effective_period(self):
        db = S.priced_drywall_db()
        inp = [i for i in line(run(db), "labor")["inputs"] if i["table"] == "labor_rates"][0]
        self.assertEqual(inp["effective_from"], "2026-01-01")
        self.assertIn("effective_to", inp)


class F328ReviewIsAsOf(unittest.TestCase):
    def test_a_decision_recorded_after_known_at_does_not_exist_yet(self):
        db = S.priced_drywall_db()
        e = Engine(db)
        o = obs(db, "TEST-OBS-BOARDA")
        o["reviewed_at"] = "2026-10-24T00:00:00+00:00"
        self.assertIn("after known_at", e._why_not(o, S.params(as_of=date(2026, 10, 23))))
        self.assertIsNone(e._why_not(o, S.params(as_of=date(2026, 10, 23), known_at=date(2026, 10, 24))))
        self.assertIsNone(e._why_not(o, S.params(as_of=date(2026, 10, 23), min_review="unreviewed")))

    def test_definition_review_is_as_of_too(self):
        db = S.priced_drywall_db()
        row(db, "work_items", "work_item_id", WI)["reviewed_at"] = "2026-10-24T00:00:00+00:00"
        r = run(db, as_of=date(2026, 10, 23), known_at=date(2026, 10, 24))
        self.assertNotIn("DEFINITION_NOT_REVIEWED", codes(r))
        r2 = run(db, as_of=date(2026, 10, 23))
        self.assertIn("DEFINITION_NOT_REVIEWED", codes(r2))


# ------------------------------------------------------------------------------- surviving mutants of the F3 mutation analysis
class MutantSurvivors(unittest.TestCase):
    def paint_line(self, db, **kw):
        return [x for x in Engine(db).unit_cost(S.PNT, 1, S.params(**kw)).lines if x["line_kind"] == "material"][0]

    def test_coats_in_the_published_rate_divide_the_coverage(self):
        db = S.paint_db()
        db.tables["products"] = [p for p in db["products"] if p["product_id"] == "TEST-PRD-PA"]
        db.tables["product_consumption"] = [c for c in db["product_consumption"] if c["product_id"] == "TEST-PRD-PA"]
        con = db["product_consumption"][0]
        con.update(coverage_qty=D("350"), coats=D("2"))                        # 350 SF per gallon for TWO coats
        comp = next(c for c in db["work_item_components"] if c["work_item_id"] == S.PNT and c["qty_mode"] == "from_product_consumption")
        comp["coats_applied"] = D("2")
        self.assertAlmostEqual(float(self.paint_line(db)["extended_cost"]), 20 * 2 / (350 * 2) * 1.0, places=9)          # = $0.0571 per SF
        con["coats"] = D("1")                                                   # 350 SF per gallon PER COAT, apply 2 coats
        self.assertAlmostEqual(float(self.paint_line(db)["extended_cost"]), 20 * 2 / 350, places=9)

    def test_only_the_best_region_class_across_products_counts(self):
        db = S.paint_db()
        row(db, "price_observations", "observation_id", "TEST-OBS-PB")["region_id"] = "REG-US-CA"             # B has only a state-level price
        ln = self.paint_line(db, allow_ancestor_region_prices=True)
        self.assertAlmostEqual(float(ln["extended_cost"]), 0.05, places=9)                                  # A (exact) alone, not median(A, B)
        self.assertFalse(any(w.startswith("PRICE_FROM_ANCESTOR") for w in ln["warnings"]))

    def test_sub_region_prices_are_off_by_default(self):
        db = S.priced_drywall_db()
        r = run(db, region_id="REG-US")                                          # the LA price must not serve a national request
        self.assertTrue(any(m["code"] == "PRICE_MISSING" for m in r.run["missing_inputs"]))
        self.assertIn("region REG-CA-037 is inside REG-US", " ".join(m["reason"] for m in r.run["missing_inputs"] if m["code"] == "PRICE_MISSING"))

    def test_two_usable_condition_factors_with_different_values_are_ambiguous(self):
        db = S.priced_drywall_db()
        S.add_factor(db, "TEST-ADJ-C1", "productivity_condition", "labor", "1.20", condition="occupied_building")
        S.add_factor(db, "TEST-ADJ-C2", "productivity_condition", "labor", "1.50", condition="occupied_building")
        self.assertIn("CONDITION_FACTOR_AMBIGUOUS", codes(run(db, conditions=("occupied_building",))))

    def test_crew_equipment_that_no_component_prices_is_reported(self):
        db = S.priced_drywall_db()
        S.set_crew(db, "CRW-DRY-HANG", 8, [("labor", "TR-DRYW", 2, False), ("labor", "TR-LAB", 1, False), ("equipment", "EQ-SCAFF", 1, False)])
        r = run(db)
        self.assertIn("CREW_EQUIPMENT_NOT_COSTED:CRW-DRY-HANG:EQ-SCAFF", r.run["warnings"])

    def test_index_values_published_after_known_at_are_unknown(self):
        def build(vintage):
            db = S.priced_drywall_db()
            for o in db["price_observations"]:
                o["observed_at"] = date(2026, 1, 10)
                o["retrieved_at"] = "2026-01-11T00:00:00+00:00"
            S.add_index(db, "TEST-IDX-V", {date(2026, 1, 1): 100, date(2026, 10, 1): 125, date(2026, 9, 1): 120}, vintage=vintage)
            return db
        self.assertEqual(run(build(date(2026, 10, 20)), time_index_id="TEST-IDX-V").status, "complete")
        r = run(build(date(2026, 10, 30)), time_index_id="TEST-IDX-V")                # published after the as-of date
        self.assertEqual(r.status, "incomplete")
        self.assertIn("PRICE_MISSING", codes(r))
        self.assertEqual(run(build(date(2026, 10, 30)), time_index_id="TEST-IDX-V", known_at=date(2026, 11, 1)).status, "complete")

    def test_an_assumption_approved_after_known_at_is_unknown(self):
        db = S.priced_drywall_db()
        c = next(c for c in db["work_item_components"] if c["work_item_id"] == WI and "CAT-DRY-BRD" in (c["product_spec_key"] or ""))
        c.update(waste_factor=None, waste_origin=None, waste_basis=None)
        S.add_assumption(db, "TEST-ASU-LATE", "waste", f"waste:{c['component_id']}", "0.10")
        row(db, "assumptions", "assumption_id", "TEST-ASU-LATE")["approved_at"] = "2026-11-02T00:00:00+00:00"
        self.assertEqual(run(db, mode="with_assumptions").status, "incomplete")
        self.assertEqual(run(db, mode="with_assumptions", known_at=date(2026, 11, 3)).status, "complete")

    def test_norm_shift_must_match_the_crew_shift(self):
        db = S.priced_drywall_db()
        row(db, "productivity_observations", "work_item_id", WI)["shift_hours"] = D("10")
        r = run(db)
        self.assertEqual(r.status, "failed")
        self.assertIn("SHIFT_MISMATCH", codes(r))

    def test_engine_side_observation_guards(self):
        for label, change in (("currency", lambda o: o.update(currency="EUR")),
                              ("future", lambda o: o.update(observed_at=date(2026, 12, 1), retrieved_at="2026-12-01T00:00:00+00:00")),
                              ("pack", lambda o: o.update(pack_content_qty=D("16")))):
            db = S.priced_drywall_db()
            change(obs(db, "TEST-OBS-BOARDA"))
            r = run(db, known_at=date(2027, 1, 1) if label == "future" else None)
            self.assertIn("PRICE_MISSING", codes(r), label)
        db = S.priced_drywall_db()
        S.add_source(db, "TEST-SRC-MAN", reuse="restricted_no_automated_access")
        o = obs(db, "TEST-OBS-BOARDA")
        o.update(source_id="TEST-SRC-MAN", capture_method="licensed_feed")
        self.assertIn("PRICE_MISSING", codes(run(db)))
        o["capture_method"] = "manual_browser"
        self.assertEqual(run(db).status, "complete")

    def test_a_pinned_product_must_match_the_component_spec(self):
        db = S.priced_drywall_db()
        c = next(c for c in db["work_item_components"] if c["work_item_id"] == WI and "CAT-DRY-BRD" in (c["product_spec_key"] or ""))
        c["product_id"] = "TEST-PRD-SCREW"
        r = run(db)
        self.assertEqual(r.status, "failed")
        self.assertIn("PRODUCT_SPEC_MISMATCH", codes(r))

    def test_retired_and_not_yet_valid_definitions_have_different_run_ids(self):
        a, b = S.priced_drywall_db(), S.priced_drywall_db()
        row(a, "work_items", "work_item_id", WI)["status"] = "retired"
        row(b, "work_items", "work_item_id", WI)["valid_from"] = date(2030, 1, 1)
        self.assertNotEqual(run(a).run["run_id"], run(b).run["run_id"])

    def test_the_calc_version_changes_with_the_code(self):
        import costdb
        self.assertRegex(costdb.CALC_VERSION, r"^costdb-calc/\d+\.\d+\.\d+\+[0-9a-f]{8}$")
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "pipeline" / "costdb", tmp / "costdb", ignore=shutil.ignore_patterns("__pycache__"))
            with open(tmp / "costdb" / "calc.py", "a", encoding="utf-8") as fh:
                fh.write("\n# a fixed bug\n")
            out = subprocess.run([sys.executable, "-B", "-c", "import costdb; print(costdb.CALC_VERSION)"], capture_output=True, text=True,
                                 env={**os.environ, "PYTHONPATH": str(tmp)}, cwd=str(tmp))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertNotEqual(out.stdout.strip(), costdb.CALC_VERSION)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_importing_units_does_not_change_the_global_decimal_context(self):
        code = "import decimal; p = decimal.getcontext().prec; import costdb.units; assert decimal.getcontext().prec == p, decimal.getcontext().prec"
        out = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "pipeline")})
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
