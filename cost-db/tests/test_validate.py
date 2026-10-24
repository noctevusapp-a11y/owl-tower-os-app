"""Negative tests: every validator rule must FIRE on deliberately broken (synthetic) data, and stay silent on clean data."""
import unittest
from datetime import date
from decimal import Decimal as D

from costdb.calc import Engine
from costdb.validate import promote_validated, validate
from tests.fixtures import synthetic as S

TODAY = date(2026, 10, 24)


def codes(db, production=False, engine=None):
    return {(i.rule_code, i.record_table) for i in validate(db, today=TODAY, production=production, engine=engine)}


def rule_codes(db, **kw):
    return {c for c, _ in codes(db, **kw)}


def obs(db, oid="TEST-OBS-BOARDA"):
    return next(o for o in db["price_observations"] if o["observation_id"] == oid)


def prod(db, pid="TEST-PRD-BOARDA"):
    return next(p for p in db["products"] if p["product_id"] == pid)


class CleanDataTest(unittest.TestCase):
    def test_real_dataset_has_no_errors(self):
        errs = [i for i in validate(S.real_db(), today=TODAY, production=True) if i.severity == "error"]
        self.assertEqual(errs, [], [f"{i.rule_code} {i.record_table} {i.record_id}" for i in errs[:5]])

    def test_clean_synthetic_db_has_no_errors_outside_production_gate(self):
        errs = [i for i in validate(S.priced_drywall_db(), today=TODAY, production=False) if i.severity == "error"]
        self.assertEqual(errs, [], [f"{i.rule_code} {i.record_id}" for i in errs[:5]])

    def test_synthetic_rows_are_rejected_in_production(self):
        c = rule_codes(S.priced_drywall_db(), production=True)
        self.assertIn("SRC_SYNTHETIC_IN_PRODUCTION", c)


class ProductRulesTest(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_spec_key_mismatch(self):
        prod(self.db)["spec_attributes"] = {**prod(self.db)["spec_attributes"], "thickness_in": 0.625}   # material change, key not updated
        self.assertIn("PRD_SPEC_KEY_MISMATCH", rule_codes(self.db))

    def test_missing_required_attribute(self):
        attrs = dict(prod(self.db)["spec_attributes"]); attrs.pop("edge_type")
        prod(self.db)["spec_attributes"] = attrs
        self.assertIn("PRD_ATTR_MISSING", rule_codes(self.db))

    def test_non_leaf_category(self):
        prod(self.db)["category_id"] = "CAT-DRY"
        self.assertIn("PRD_CATEGORY_NOT_LEAF", rule_codes(self.db))

    def test_duplicate_manufacturer_mpn(self):
        S.add_product(self.db, "TEST-PRD-DUP", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-A", "TB-A-1")
        self.assertIn("PRD_DUP_MPN", rule_codes(self.db))

    def test_unknown_unit(self):
        prod(self.db)["content_unit_id"] = "TON"          # unqualified ton is not a unit
        self.assertIn("UNIT_UNKNOWN", rule_codes(self.db))


class ObservationRulesTest(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()

    def test_pack_mismatch_means_different_sku(self):
        obs(self.db)["pack_content_qty"] = D("16")
        self.assertIn("OBS_PACK_MISMATCH", rule_codes(self.db))

    def test_future_and_retrieval_order(self):
        obs(self.db)["observed_at"] = date(2027, 1, 1)
        c = rule_codes(self.db)
        self.assertTrue({"OBS_FUTURE_DATE", "OBS_RETRIEVED_BEFORE_OBSERVED"} <= c, c)

    def test_retail_flagged_as_contractor_cost(self):
        obs(self.db)["is_contractor_cost"] = True
        self.assertIn("OBS_RETAIL_AS_CONTRACTOR", rule_codes(self.db))

    def test_stale_zero_noregion_duplicate_outlier(self):
        o = obs(self.db); o["observed_at"] = date(2025, 1, 1); o["retrieved_at"] = "2025-01-02T00:00:00+00:00"
        o["price_amount"] = D("0"); o["region_id"] = None
        c = rule_codes(self.db)
        self.assertTrue({"OBS_STALE", "OBS_PRICE_ZERO", "OBS_NO_REGION"} <= c, c)
        db = S.priced_drywall_db()
        S.add_obs(db, "TEST-OBS-DUP2", "TEST-PRD-BOARDA", "12.80", 32, "SF")      # identical product/store/day/price
        self.assertIn("OBS_DUP", rule_codes(db))
        db = S.priced_drywall_db()
        for i, (price, brand) in enumerate((("12.80", "A"), ("13.00", "B"), ("12.90", "C"), ("96.00", "D"))):
            pid = f"TEST-PRD-O{brand}"
            S.add_product(db, pid, "gyp_half_reg_4x8", 32, "SF", f"TESTBRAND-O{brand}", f"TO-{brand}")
            S.add_obs(db, f"TEST-OBS-O{brand}", pid, price, 32, "SF")
        self.assertIn("OBS_OUTLIER", rule_codes(db))


class LaborRulesTest(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        res = Engine(self.db).unit_cost(S.WI, 1, S.params())      # a real run row for derived records to point at
        self.db.add("calculation_runs", res.run)
        self.run_id = res.run["run_id"]

    def pw(self, rid="TEST-LRT-PW", ctx="public_works_only"):
        return self.db.add("labor_rates", {
            "labor_rate_id": rid, "rate_type": "prevailing_wage", "trade_code": "TR-DRYW", "classification_raw": "TEST", "soc_code": None,
            "statistic": "determined", "region_id": "REG-CA-037", "base_wage_hr": D("50"), "fringe_hr": D("20"), "fringe_breakdown": None,
            "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None, "total_hr": None, "includes_fringe": True,
            "includes_payroll_taxes": False, "includes_workers_comp": False, "wage_basis": "straight_time", "project_type": "building",
            "use_context": ctx, "apprentice": False, "determination_ref": "TEST", "effective_from": date(2026, 8, 22), "effective_to": None,
            "retrieved_at": S.RUN_AT, "derived_from": None, "calc_run_id": None, "source_id": S.SRC, "source_locator": "x",
            "evidence_excerpt": "x", "raw_file_sha256": None, "origin": "observed", "review_status": "unreviewed", "reviewed_by": None,
            "reviewed_at": None, "created_at": None, "notes": None})

    def loaded(self, rid, derived_from, fringe, total, tax="0", wc="0"):
        return self.db.add("labor_rates", {
            "labor_rate_id": rid, "rate_type": "loaded_employer_cost", "trade_code": "TR-DRYW", "classification_raw": "loaded", "soc_code": None,
            "statistic": "n/a", "region_id": "REG-CA-037", "base_wage_hr": D("50"), "fringe_hr": D(fringe), "fringe_breakdown": None,
            "payroll_tax_hr": D(tax), "workers_comp_hr": D(wc), "other_employer_cost_hr": D("0"), "total_hr": D(total), "includes_fringe": True,
            "includes_payroll_taxes": True, "includes_workers_comp": True, "wage_basis": "straight_time", "project_type": "n/a",
            "use_context": "employer_internal", "apprentice": False, "determination_ref": None, "effective_from": date(2026, 10, 1),
            "effective_to": None, "retrieved_at": None, "derived_from": derived_from, "calc_run_id": self.run_id, "source_id": None,
            "source_locator": None, "evidence_excerpt": None, "raw_file_sha256": None, "origin": "derived", "review_status": "unreviewed",
            "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})

    def test_prevailing_wage_must_stay_public_works_only(self):
        self.pw(ctx="statistical_reference")
        self.assertIn("LAB_PW_SCOPE", rule_codes(self.db))

    def test_stat_wage_cannot_include_fringe(self):
        self.db.add("labor_rates", {**{k: None for k in [c.name for c in self.db.meta["labor_rates"]]},
                                    "labor_rate_id": "TEST-LRT-BADSTAT", "rate_type": "stat_wage", "trade_code": "TR-CARP",
                                    "classification_raw": "x", "statistic": "mean", "region_id": "REG-US", "base_wage_hr": D("30"),
                                    "includes_fringe": True, "includes_payroll_taxes": False, "includes_workers_comp": False,
                                    "wage_basis": "straight_time", "project_type": "n/a", "use_context": "statistical_reference",
                                    "apprentice": False, "effective_from": date(2026, 5, 1), "origin": "observed", "review_status": "unreviewed"})
        self.assertIn("LAB_STAT_INCLUDES_FRINGE", rule_codes(self.db))

    def test_loaded_rate_double_fringe(self):
        self.pw()
        self.loaded("TEST-LRT-L1", ["TEST-LRT-PW"], fringe="27", total="77")           # source fringe is 20, loaded carries 27 -> double count
        self.assertIn("LAB_DOUBLE_FRINGE", rule_codes(self.db))

    def test_loaded_sum_arithmetic(self):
        self.pw()
        self.loaded("TEST-LRT-L2", ["TEST-LRT-PW"], fringe="20", total="80", tax="5")      # 50+20+5 = 75 != 80
        self.assertIn("LAB_LOADED_SUM", rule_codes(self.db))
        self.loaded("TEST-LRT-L3", ["TEST-LRT-PW"], fringe="20", total="75", tax="5")      # consistent and not double counted
        ok = [i for i in validate(self.db, today=TODAY, production=False) if i.record_id == "TEST-LRT-L3" and i.severity == "error"]
        self.assertEqual(ok, [])

    def test_percentage_stored_as_percent(self):
        self.db.add("burden_rates", {**{k: None for k in [c.name for c in self.db.meta["burden_rates"]]}, "burden_id": "TEST-BRD-BAD",
                                     "burden_type": "fica_medicare", "basis": "pct_of_wages", "rate": D("1.45"), "effective_from": date(2026, 1, 1),
                                     "origin": "observed", "review_status": "unreviewed", "source_id": S.SRC})
        self.assertIn("BRD_PCT_GT_1", rule_codes(self.db))


class CrewProductivityRulesTest(unittest.TestCase):
    def test_operator_double_count_in_pinned_rate(self):
        db = S.priced_drywall_db()
        db.add("equipment_rates", {**{k: None for k in [c.name for c in db.meta["equipment_rates"]]}, "equipment_rate_id": "TEST-EQR-9",
                                   "equipment_type_code": "EQ-PTROWEL", "description_raw": "t", "rate_basis": "rental_market",
                                   "rental_rate_hr": D("25"), "operator_included": True, "region_id": S.REGION, "effective_from": date(2026, 1, 1),
                                   "origin": "observed", "review_status": "unreviewed", "retrieved_at": S.RUN_AT, "source_id": S.SRC,
                                   "source_locator": "x", "evidence_excerpt": "x"})
        S.set_crew(db, "CRW-CON-FLAT", 8, [("labor", "TR-CEM", 2, False), ("labor", "TR-OPR", 1, True), ("equipment", "EQ-PTROWEL", 1, False)])
        for m in db["crew_members"]:
            if m["member_kind"] == "equipment":
                m["equipment_rate_id"] = "TEST-EQR-9"
        self.assertIn("CREW_OPERATOR_DOUBLE", rule_codes(db))

    def test_fuel_counted_twice(self):
        db = S.priced_drywall_db()
        db.add("equipment_rates", {**{k: None for k in [c.name for c in db.meta["equipment_rates"]]}, "equipment_rate_id": "TEST-EQR-F",
                                   "equipment_type_code": "EQ-SKID", "description_raw": "t", "rate_basis": "dot_schedule",
                                   "operating_cost_hr": D("10"), "fuel_cost_hr": D("4"), "fuel_included": True, "operator_included": False,
                                   "region_id": S.REGION, "effective_from": date(2026, 1, 1), "origin": "observed", "review_status": "unreviewed",
                                   "retrieved_at": S.RUN_AT, "source_id": S.SRC, "source_locator": "x", "evidence_excerpt": "x"})
        self.assertIn("EQP_FUEL_DOUBLE", rule_codes(db))

    def test_productivity_reconciliation(self):
        db = S.priced_drywall_db()
        for p in db["productivity_observations"]:
            if p["work_item_id"] == S.WI:
                p["person_hours_per_unit_reported"] = D("0.05")        # crew 3 x 8 h / 1600 SF = 0.015
        self.assertIn("PROD_RECON", rule_codes(db))

    def test_crew_size_mismatch(self):
        db = S.priced_drywall_db()
        for p in db["productivity_observations"]:
            if p["work_item_id"] == S.WI:
                p["crew_size"] = D("5")
        self.assertIn("CREW_SIZE_MISMATCH", rule_codes(db))


class DefinitionRulesTest(unittest.TestCase):
    def test_shared_activities_must_be_excluded(self):
        db = S.real_db()
        w = next(x for x in db["work_items"] if x["work_item_id"] == "WI-FRM-001")
        w["included_scope"] = w["included_scope"] + ["mobilization"]
        w["excluded_scope"] = [t for t in w["excluded_scope"] if t != "mobilization"]
        c = rule_codes(db)
        self.assertIn("WI_GLOBAL_SCOPE_INCLUDED", c)
        self.assertIn("WI_GLOBAL_SCOPE_NOT_EXCLUDED", c)

    def test_assembly_scope_overlap_unit_mismatch_and_empty_spec(self):
        db = S.real_db()
        for w in db["work_items"]:
            if w["work_item_id"] == "WI-DRY-005":
                w["included_scope"] = w["included_scope"] + ["board_material"]        # WI-DRY-001 already includes it
        for ac in db["assembly_components"]:
            if ac["assembly_id"] == "ASM-WALL-001" and ac["work_item_id"] == "WI-FRM-001":
                ac["qty_unit_id"] = "LF"                                                # SF work item, LF quantity
        for a in db["assemblies"]:
            if a["assembly_id"] == "ASM-WALL-002":
                a["spec_attributes"] = {}
        c = rule_codes(db)
        self.assertTrue({"ASM_SCOPE_OVERLAP", "ASM_UNIT_MISMATCH", "ASM_SPEC_EMPTY"} <= c, c)

    def test_broken_references_and_duplicate_ids(self):
        db = S.real_db()
        db["products"].append({**{c.name: None for c in db.meta["products"]}, "product_id": "TEST-PRD-X", "category_id": "CAT-NOPE", "name": "x",
                               "spec_attributes": {}, "spec_key": "k", "standards": [], "sale_unit_label": "x", "content_qty": D(1),
                               "content_unit_id": "EA", "source_id": "SRC-NOPE", "origin": "observed", "review_status": "unreviewed"})
        db["regions"].append(dict(db["regions"][0]))
        c = rule_codes(db)
        self.assertIn("FK_BROKEN", c)
        self.assertIn("ID_DUPLICATE", c)

    def test_waste_without_basis(self):
        db = S.real_db()
        w = next(x for x in db["work_item_components"] if x["work_item_id"] == "WI-FRM-001" and x["component_kind"] == "material")
        w["waste_factor"] = D("0.05"); w["waste_origin"] = "observed"; w["waste_basis"] = None
        self.assertIn("WI_WASTE_NO_BASIS", rule_codes(db))


class SourceRulesTest(unittest.TestCase):
    def test_prohibited_source_in_use_and_snippet_validation(self):
        db = S.priced_drywall_db()
        for s in db["sources"]:
            if s["source_id"] == S.SRC:
                s["reuse_status"] = "prohibited"
        c = rule_codes(db)
        self.assertIn("SRC_PROHIBITED_IN_USE", c)
        db = S.priced_drywall_db()
        # a snippet-only source whose records claim 'validated'
        S.add_source(db, "TEST-SRC-SNIP", method="search_snippet_only", review="unreviewed")
        for o in db["price_observations"]:
            o["source_id"] = "TEST-SRC-SNIP"
        self.assertIn("VALIDATED_FROM_SNIPPET", rule_codes(db))
        for s in db["sources"]:
            if s["source_id"] == "TEST-SRC-SNIP":
                s["review_status"] = "validated"
        self.assertIn("SRC_VALIDATED_WITHOUT_FETCH", rule_codes(db))


class NoStorageSourceRuleTest(unittest.TestCase):
    def test_records_from_restricted_no_storage_source_are_errors(self):
        db = S.priced_drywall_db()
        for s in db["sources"]:
            if s["source_id"] == S.SRC:
                s["reuse_status"] = "restricted_no_storage"
        self.assertIn("SRC_PROHIBITED_IN_USE", rule_codes(db))


class PromotionGateTest(unittest.TestCase):
    def test_only_fetched_primary_evidence_can_be_validated(self):
        db = S.priced_drywall_db()
        S.add_source(db, "TEST-SRC-SNIP", method="search_snippet_only", review="unreviewed")
        S.add_source(db, "TEST-SRC-FETCH", method="fetched_primary", review="unreviewed")
        S.add_product(db, "TEST-PRD-P1", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-P1", "TP-1")
        S.add_product(db, "TEST-PRD-P2", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-P2", "TP-2")
        a = S.add_obs(db, "TEST-OBS-P1", "TEST-PRD-P1", "12.00", 32, "SF", review="unreviewed", source="TEST-SRC-SNIP")
        b = S.add_obs(db, "TEST-OBS-P2", "TEST-PRD-P2", "12.50", 32, "SF", review="unreviewed", source="TEST-SRC-FETCH")
        issues = validate(db, today=TODAY, production=False)
        counts = promote_validated(db, issues, "tests", "2026-10-24T00:00:00+00:00")
        self.assertEqual(a["review_status"], "unreviewed", "snippet evidence must never be promoted")
        self.assertEqual(b["review_status"], "validated")
        self.assertEqual(counts.get("price_observations"), 1)

    def test_records_with_errors_are_not_promoted(self):
        db = S.priced_drywall_db()
        S.add_source(db, "TEST-SRC-FETCH", method="fetched_primary", review="unreviewed")
        S.add_product(db, "TEST-PRD-P2", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-P2", "TP-2")
        b = S.add_obs(db, "TEST-OBS-P2", "TEST-PRD-P2", "12.50", 32, "SF", review="unreviewed", source="TEST-SRC-FETCH")
        b["pack_content_qty"] = D("16")                                  # contradicts the product's pack -> OBS_PACK_MISMATCH (error)
        promote_validated(db, validate(db, today=TODAY, production=False), "tests", "2026-10-24T00:00:00+00:00")
        self.assertEqual(b["review_status"], "unreviewed")


class CalcRunRulesTest(unittest.TestCase):
    def test_stored_runs_are_recomputed_and_input_integrity_checked(self):
        db = S.priced_drywall_db()
        eng = Engine(db)
        res = eng.unit_cost(S.WI, 1, S.params())
        run = db.add("calculation_runs", res.run)
        lines = [db.add("calculation_run_lines", ln) for ln in res.lines]
        mine = lambda issues: [i for i in issues if i.record_id.startswith(run["run_id"]) or i.record_id == run["run_id"]]
        base = [i for i in validate(db, today=TODAY, production=False, engine=eng) if i.severity == "error"]
        self.assertEqual(base, [])
        run["direct_cost_total"] = D("9.999999")                                   # tamper with the stored total
        self.assertIn("CALC_NOT_REPRODUCIBLE", rule_codes(db, engine=eng))
        run["direct_cost_total"] = res.run["direct_cost_total"]
        run["missing_inputs"] = [{"x": 1}]
        self.assertIn("CALC_COMPLETE_HAS_MISSING", rule_codes(db))
        run["missing_inputs"] = []
        lines[0]["inputs"] = [{"table": "price_observations", "id": "TEST-OBS-GHOST"}]
        self.assertIn("CALC_INPUT_NOT_FOUND", rule_codes(db))
        lines[0]["inputs"] = res.lines[0]["inputs"]
        run["mode"] = "strict"; run["has_assumptions"] = True
        self.assertIn("CALC_STRICT_ASSUMED", rule_codes(db))


class ReviewFixRulesTest(unittest.TestCase):
    """Rules added after the independent review F1 (F1-004, 020, 023, 024, 025, 031, 039)."""

    def test_every_restricted_reuse_status_is_an_error_in_use_and_when_validated(self):
        for status in ("prohibited", "restricted_no_storage", "licence_required"):
            db = S.priced_drywall_db()
            for s in db["sources"]:
                if s["source_id"] == S.SRC:
                    s["reuse_status"] = status                       # the fixture source is also 'validated'
            c = rule_codes(db)
            self.assertTrue({"SRC_PROHIBITED_IN_USE", "SRC_PROHIBITED_VALIDATED"} <= c, (status, c))

    def test_one_issue_per_rule_and_labor_row(self):
        db = S.priced_drywall_db()
        for s in db["sources"]:
            if s["source_id"] == S.SRC:
                s["reuse_status"] = "prohibited"
        issues = [i for i in validate(db, today=TODAY, production=False) if i.rule_code == "SRC_PROHIBITED_IN_USE" and i.record_table == "labor_rates"]
        self.assertEqual(len(issues), len({i.record_id for i in issues}), "labor rows were reported twice")

    def test_validated_record_needs_a_named_reviewer(self):
        db = S.priced_drywall_db()
        obs(db)["reviewed_by"] = None
        self.assertIn("VALIDATED_WITHOUT_REVIEWER", rule_codes(db))

    def test_naive_retrieval_time_is_an_error(self):
        db = S.priced_drywall_db()
        obs(db)["retrieved_at"] = "2026-09-01T12:00:00"
        self.assertIn("OBS_NAIVE_TIMESTAMP", rule_codes(db))

    def test_thresholds_are_a_documented_configurable_policy(self):
        from costdb.validate import DEFAULT_POLICY
        db = S.priced_drywall_db()
        self.assertTrue(all(isinstance(v[1], str) and len(v[1]) > 20 for v in DEFAULT_POLICY.values()), "every threshold states its basis")
        self.assertNotIn("OBS_STALE", rule_codes(db))
        issues = validate(db, today=date(2026, 12, 31), production=False, policy={"price_stale_days": 30})
        stale = [i for i in issues if i.rule_code == "OBS_STALE"]
        self.assertTrue(stale)
        self.assertEqual(stale[0].details["threshold_days"], 30)

    def test_work_item_component_must_price_the_specification_it_states(self):
        db = S.priced_drywall_db()
        wic = next(c for c in db["work_item_components"] if c["work_item_id"] == S.WI and "CAT-DRY-BRD" in (c["product_spec_key"] or ""))
        wic["product_spec_key"] = S.pilot.MATS["gyp_58_x_4x8"]["spec_key"]           # the work item says 1/2 in regular, the component prices 5/8 Type X
        self.assertIn("WI_SPEC_COMPONENT_MISMATCH", rule_codes(db))
        db = S.priced_drywall_db()
        w = next(w for w in db["work_items"] if w["work_item_id"] == S.WI)
        w["spec_attributes"]["material_specs"][0]["attributes"]["thickness_in"] = 0.625          # attributes no longer reproduce the stated key
        self.assertIn("WI_SPEC_ATTRS_MISMATCH", rule_codes(db))
        db = S.priced_drywall_db()
        w = next(w for w in db["work_items"] if w["work_item_id"] == S.WI)
        w["spec_attributes"]["material_specs"].append({"line": 99, "attributes": {}, "spec_key": "x"})
        self.assertIn("WI_SPEC_ORPHAN", rule_codes(db))

    def test_assembly_spec_must_list_its_real_children(self):
        db = S.priced_drywall_db()
        a = next(a for a in db["assemblies"] if a["assembly_id"] == "ASM-WALL-001")
        a["spec_attributes"]["work_items"][1]["work_item_id"] = "WI-DRY-002"                    # spec says 5/8 board, components hang 1/2 in
        self.assertIn("ASM_SPEC_CHILD_MISMATCH", rule_codes(db))

    def test_assembly_inclusions_and_exclusions_are_checked_against_the_children(self):
        db = S.priced_drywall_db()
        a = next(a for a in db["assemblies"] if a["assembly_id"] == "ASM-WALL-001")
        a["included_scope"] = []
        self.assertIn("ASM_NO_INCLUSIONS", rule_codes(db))
        db = S.priced_drywall_db()
        a = next(a for a in db["assemblies"] if a["assembly_id"] == "ASM-WALL-001")
        a["included_scope"] = a["included_scope"] + ["gas_piping"]
        self.assertIn("ASM_INCLUDED_NOT_PRICED", rule_codes(db))
        db = S.priced_drywall_db()
        a = next(a for a in db["assemblies"] if a["assembly_id"] == "ASM-WALL-001")
        a["excluded_scope"] = [t for t in a["excluded_scope"] if t != "blocking"]
        self.assertIn("ASM_CHILD_EXCLUSION_NOT_SURFACED", rule_codes(db))

    def test_duplicate_cost_tags_are_errors_in_work_items_and_assemblies(self):
        db = S.priced_drywall_db()
        for c in db["work_item_components"]:
            if c["work_item_id"] == S.WI and c["component_kind"] == "material":
                c["cost_tags"] = ["fasteners"]
        self.assertIn("WI_DUP_TAG", rule_codes(db))
        db = S.priced_drywall_db()
        for c in db["assembly_components"]:
            if c["assembly_id"] == "ASM-WALL-001":
                c["cost_tags"] = ["x"]
        self.assertIn("ASM_DUP_TAG", rule_codes(db))
        sev = {i.severity for i in validate(db, today=TODAY, production=False) if i.rule_code == "ASM_DUP_TAG"}
        self.assertEqual(sev, {"error"})

    def test_assumption_rules(self):
        db = S.priced_drywall_db()
        S.add_assumption(db, "TEST-ASU-1", "waste", "waste:X", "0.1", approved_by="tests", expires_on=None)
        S.add_assumption(db, "TEST-ASU-2", "waste", "waste:Y", "0.1")
        S.add_assumption(db, "TEST-ASU-3", "waste", "waste:Y", "0.2")
        c = rule_codes(db)
        self.assertTrue({"ASU_NO_EXPIRY", "ASU_SELF_APPROVED", "ASU_DUPLICATE_APPROVED"} <= c, c)

    def test_run_level_rules(self):
        db = S.priced_drywall_db()
        eng = Engine(db)
        res = eng.unit_cost(S.WI, 1, S.params())
        run = db.add("calculation_runs", res.run)
        for ln in res.lines:
            db.add("calculation_run_lines", ln)
        self.assertEqual([i for i in validate(db, today=TODAY, production=False, engine=eng) if i.severity == "error"], [])
        run["parameters"] = {**run["parameters"], "accept_retail_proxy": False}
        self.assertIn("CALC_RETAIL_WITHOUT_OPT_IN", rule_codes(db))
        run["parameters"] = res.run["parameters"]
        run["input_review_floor"] = "unreviewed"
        self.assertIn("CALC_REVIEW_FLOOR_MISMATCH", rule_codes(db))
        run["input_review_floor"] = "validated"
        run["direct_cost_total"] = D("5.000000")
        self.assertIn("CALC_TOTAL_NOT_LINE_SUM", rule_codes(db))

    def test_run_that_uses_an_unapproved_assumption_is_an_error(self):
        db = S.priced_drywall_db()
        c = next(c for c in db["work_item_components"] if c["work_item_id"] == S.WI and "CAT-DRY-BRD" in (c["product_spec_key"] or ""))
        c.update(waste_factor=None, waste_origin=None, waste_basis=None)
        S.add_assumption(db, "TEST-ASU-W", "waste", f"waste:{c['component_id']}", "0.10")
        eng = Engine(db)
        res = eng.unit_cost(S.WI, 1, S.params(mode="with_assumptions"))
        self.assertEqual(res.status, "complete")
        run = db.add("calculation_runs", res.run)
        for ln in res.lines:
            db.add("calculation_run_lines", ln)
        next(a for a in db["assumptions"] if a["assumption_id"] == "TEST-ASU-W")["status"] = "rejected"
        self.assertIn("CALC_ASSUMPTION_NOT_APPROVED", rule_codes(db))


class PromotionGapsTest(unittest.TestCase):
    def setUp(self):
        self.db = S.priced_drywall_db()
        S.add_source(self.db, "TEST-SRC-FETCH", method="fetched_primary", review="unreviewed")
        S.add_source(self.db, "TEST-SRC-SNIP", method="search_snippet_only", review="unreviewed")
        self.when = "2026-10-24T00:00:00+00:00"

    def promote(self):
        return promote_validated(self.db, validate(self.db, today=TODAY, production=False), "tests", self.when)

    def test_index_values_inherit_the_source_of_their_series_and_are_logged(self):
        S.add_index(self.db, "TEST-IDX-A", {date(2026, 9, 1): 100}, review="unreviewed")
        S.add_index(self.db, "TEST-IDX-B", {date(2026, 9, 1): 100}, review="unreviewed")
        next(i for i in self.db["indices"] if i["index_id"] == "TEST-IDX-A")["source_id"] = "TEST-SRC-FETCH"
        next(i for i in self.db["indices"] if i["index_id"] == "TEST-IDX-B")["source_id"] = "TEST-SRC-SNIP"
        counts = self.promote()
        self.assertEqual(counts.get("index_values"), 1)
        st = {v["index_id"]: v["review_status"] for v in self.db["index_values"]}
        self.assertEqual(st, {"TEST-IDX-A": "validated", "TEST-IDX-B": "unreviewed"})
        ev = [e for e in self.db["review_events"] if e["record_table"] == "index_values"]
        self.assertEqual((len(ev), ev[0]["new_status"], ev[0]["changed_by"]), (1, "validated", "tests"))

    def test_products_without_evidence_are_not_promoted(self):
        for pid, ev in (("TEST-PRD-E1", "excerpt"), ("TEST-PRD-E2", None)):
            p = S.add_product(self.db, pid, "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-" + pid[-2:], "T-" + pid[-2:], source="TEST-SRC-FETCH")
            p.update(review_status="unreviewed", reviewed_by=None, reviewed_at=None, evidence_excerpt=ev)
        self.promote()
        st = {p["product_id"]: p["review_status"] for p in self.db["products"] if p["product_id"].startswith("TEST-PRD-E")}
        self.assertEqual(st, {"TEST-PRD-E1": "validated", "TEST-PRD-E2": "unreviewed"})

    def test_rows_of_a_source_that_bars_data_use_are_never_promoted(self):
        S.add_source(self.db, "TEST-SRC-LIC", method="fetched_primary", review="unreviewed", reuse="licence_required")
        S.add_product(self.db, "TEST-PRD-P1", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-P1", "TP-1")
        o = S.add_obs(self.db, "TEST-OBS-P1", "TEST-PRD-P1", "12.00", 32, "SF", review="unreviewed", source="TEST-SRC-LIC")
        self.promote()
        self.assertEqual(o["review_status"], "unreviewed")


if __name__ == "__main__":
    unittest.main()
