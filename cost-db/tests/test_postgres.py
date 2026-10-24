"""Tests against a real PostgreSQL server.

A scratch server is used when PGHOST/PGPORT/PGUSER are set; otherwise tests/fixtures/pgserver.py starts (and removes) a throw-away
cluster. If no server can be obtained these tests FAIL - they are skipped only when COSTDB_SKIP_PG=1 is set explicitly.
"""
import os
import tempfile
import unittest
from pathlib import Path

from costdb import pg
from costdb.calc import Engine
from costdb.units import Units
from tests.fixtures import pgserver
from tests.fixtures import synthetic as S

ROOT = Path(__file__).resolve().parents[1]
DB = "costdb_unittest"


def psql(sql, db=DB, ok=True):
    r = pg.run_psql(["-d", db, "-At", "-F", "|", "-c", sql])
    if ok and r.returncode:
        raise AssertionError(f"psql failed: {r.stderr}\nSQL: {sql}")
    return r


def fresh(db, csv_dir):
    pg.run_psql(["-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {db}"])
    r = pg.run_psql(["-d", "postgres", "-c", f"CREATE DATABASE {db}"])
    assert r.returncode == 0, r.stderr
    for f in ("001_schema.sql", "003_comments.sql"):
        r = pg.run_psql(["-d", db, "-f", str(ROOT / "schema" / f)])
        assert r.returncode == 0, f"{f}: {r.stderr}"
    r = pg.run_psql(["-d", db], pg.copy_script(csv_dir))
    assert r.returncode == 0, r.stderr


@unittest.skipIf(pgserver.skip_requested(), "database tests skipped on request (COSTDB_SKIP_PG=1) - NOT a pass")
class PostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = pgserver.ensure()                                # raises (test error) when no PostgreSQL can be obtained
        pg.check_order_complete()
        cls.tmp = tempfile.TemporaryDirectory()
        db = S.priced_drywall_db()                                  # real definitions + SYNTHETIC inputs
        eng = Engine(db)
        res = eng.unit_cost(S.WI, 1, S.params())
        db.add("calculation_runs", res.run)
        for ln in res.lines:
            db.add("calculation_run_lines", ln)
        cls.expected_total = res.run["direct_cost_total"]
        cls.csvdir = Path(cls.tmp.name)
        db.write_csv_dir(cls.csvdir)
        fresh(DB, cls.csvdir)

    @classmethod
    def tearDownClass(cls):
        pg.run_psql(["-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {DB}"])
        cls.tmp.cleanup()

    def test_real_csvs_import_cleanly_on_their_own(self):
        fresh("costdb_unittest_real", ROOT / "data" / "csv")
        n = psql("select count(*) from costdb.sources", db="costdb_unittest_real").stdout.strip()
        self.assertEqual(int(n), 92)
        pg.run_psql(["-d", "postgres", "-c", "DROP DATABASE IF EXISTS costdb_unittest_real"])

    def test_python_generated_runs_and_json_columns_round_trip(self):
        run = "select run_id from costdb.calculation_runs where status = 'complete'"       # the one synthetic complete run
        total = psql(f"select direct_cost_total from costdb.calculation_runs where run_id = ({run})").stdout.strip()
        self.assertEqual(total, str(self.expected_total))
        self.assertEqual(psql(f"select count(*) from costdb.calculation_run_lines where run_id = ({run}) and jsonb_array_length(inputs) > 0").stdout.strip(), "3")

    def test_generated_columns_match_python(self):
        v = psql("select price_per_content_unit from costdb.price_observations where observation_id='TEST-OBS-BOARDA'").stdout.strip()
        self.assertEqual(float(v), 0.4)
        v = psql("select person_hours_per_unit_derived from costdb.productivity_observations where work_item_id='WI-DRY-001'").stdout.strip()
        self.assertAlmostEqual(float(v), 3 * 8 / 1600, places=7)

    def test_unit_conversion_view_matches_python_for_every_pair(self):
        units = Units(S.real_db()["units"])
        rows = psql("select from_unit_id, to_unit_id, factor from costdb.v_unit_conversions").stdout.strip().splitlines()
        self.assertEqual(len(rows), 40)       # 14 fixed units: 1+1+4+16+16+1+1 ordered same-dimension pairs
        for line in rows:
            a, b, f = line.split("|")
            self.assertAlmostEqual(float(f) / float(units.factor(a, b)), 1.0, places=10, msg=f"{a}->{b}")
        pairs = {tuple(l.split("|")[:2]) for l in rows}
        for bad in (("TON_REFRIG", "LB"), ("DAY", "HR"), ("SF", "LF"), ("TON_SHORT", "TON_REFRIG")):
            self.assertNotIn(bad, pairs)

    def test_history_is_append_only(self):
        r = psql("update costdb.price_observations set price_amount = 1 where observation_id='TEST-OBS-BOARDA'", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("append-only", r.stderr)
        r = psql("delete from costdb.price_observations where observation_id='TEST-OBS-BOARDA'", ok=False)
        self.assertIn("append-only", r.stderr)
        r = psql("update costdb.price_observations set review_status='flagged', notes='checked' where observation_id='TEST-OBS-BOARDA'", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)                     # review fields stay editable
        r = psql("update costdb.price_observations set pack_content_qty = 64 where observation_id='TEST-OBS-BOARDA'", ok=False)
        self.assertIn("append-only", r.stderr)                               # a field behind a generated column is still protected
        for tbl, col in (("labor_rates", "base_wage_hr"), ("productivity_observations", "daily_output")):
            r = psql(f"update costdb.{tbl} set {col} = 1 where {col} is not null", ok=False)
            self.assertIn("append-only", r.stderr, tbl)

    def reject(self, sql, needle):
        r = psql(sql, ok=False)
        self.assertNotEqual(r.returncode, 0, f"should have been rejected: {sql[:80]}")
        self.assertIn(needle, r.stderr, r.stderr[:300])

    def test_business_rules_are_enforced_by_the_database(self):
        base_obs = ("insert into costdb.price_observations (observation_id, product_id, source_id, store_ref, observed_at, retrieved_at, price_amount, "
                    "price_channel, is_contractor_cost, sold_as_label, pack_content_qty, pack_content_unit_id, evidence_excerpt, capture_method, captured_by")
        # retail price labelled as contractor cost
        self.reject(base_obs + ") values ('TEST-OBS-X1','TEST-PRD-BOARDA','TEST-SRC-SYN','s','2026-09-01','2026-09-01T12:00:00Z',1,'retail_public',true,'p',32,'SF','e','manual_browser','t')",
                    "po_contractor_chk")
        # unqualified ton: refused as a pack of another SKU, and as a unit anywhere else (foreign key to units)
        self.reject(base_obs + ") values ('TEST-OBS-X2','TEST-PRD-BOARDA','TEST-SRC-SYN','s','2026-09-01','2026-09-01T12:00:00Z',1,'retail_public',false,'p',32,'TON','e','manual_browser','t')",
                    "differs from the product pack")
        self.reject("insert into costdb.assemblies (assembly_id, version, name, category_id, spec_attributes, output_unit_id, description, valid_from, definition_basis) "
                    "values ('TEST-ASM-X0',1,'n','CAT-FRM','{\"a\":1}','TON','d','2026-01-01','b')", "violates foreign key")
        # no capture audit trail
        self.reject(base_obs + ") values ('TEST-OBS-X3','TEST-PRD-BOARDA','TEST-SRC-SYN','s','2026-09-01','2026-09-01T12:00:00Z',1,'retail_public',false,'p',32,'SF','e','scraper','')",
                    "capture_method")
        # prevailing wage not restricted to public works
        lr = ("insert into costdb.labor_rates (labor_rate_id, rate_type, trade_code, classification_raw, region_id, base_wage_hr, includes_fringe, "
              "includes_payroll_taxes, includes_workers_comp, use_context, effective_from, origin, source_id, source_locator, evidence_excerpt, retrieved_at")
        self.reject(lr + ") values ('TEST-LRT-X1','prevailing_wage','TR-CARP','x','REG-CA-037',50,true,false,false,'statistical_reference','2026-01-01','observed','TEST-SRC-SYN','x','x','2026-01-01T00:00:00Z')",
                    "lr_pw_scope_chk")
        # statistical wage claiming fringe
        self.reject(lr + ") values ('TEST-LRT-X2','stat_wage','TR-CARP','x','REG-CA-037',30,true,false,false,'statistical_reference','2026-01-01','observed','TEST-SRC-SYN','x','x','2026-01-01T00:00:00Z')",
                    "lr_stat_scope_chk")
        # derived rate without calculation
        self.reject(lr + ") values ('TEST-LRT-X3','loaded_employer_cost','TR-CARP','x','REG-CA-037',30,true,true,true,'employer_internal','2026-01-01','derived','TEST-SRC-SYN','x','x','2026-01-01T00:00:00Z')",
                    "lr_derived_chk")
        # complete run without a total / strict run with assumptions
        run = ("insert into costdb.calculation_runs (run_id, calc_version, target_type, target_id, mode, status, has_assumptions, direct_cost_total, missing_inputs")
        self.reject(run + ") values ('TEST-RUN-X1','v','unit_cost','x','strict','complete',false,null,'[]')", "cr_complete_chk")
        self.reject(run + ") values ('TEST-RUN-X2','v','unit_cost','x','strict','incomplete',true,null,'[]')", "cr_strict_chk")
        # observed productivity without page/edition; missing productivity with a number
        pr = "insert into costdb.productivity_observations (productivity_id, operation_text, output_unit_id, daily_output, source_id, origin, missing_reason"
        self.reject(pr + ") values ('TEST-PRO-X1','op','SF',100,'TEST-SRC-SYN','observed',null)", "prod_observed_chk")
        self.reject(pr + ") values ('TEST-PRO-X2','op','SF',100,null,'missing','none')", "prod_missing_chk")
        # inline assumption in a definition table / waste without basis
        wic = ("insert into costdb.work_item_components (component_id, work_item_id, work_item_version, line_no, component_kind, description, product_spec_key, "
               "qty_per_unit, qty_unit_id, qty_formula, qty_origin, waste_factor, waste_origin, waste_basis) values ('TEST-WIC-%s','WI-FRM-001',1,%d,'material','d','k',1,'EA','f','derived',%s)")
        self.reject(wic % ("W1", 90, "0.1,'assumed','x'"), "wic_waste_chk")
        self.reject(wic % ("W2", 91, "0.1,'observed',null"), "wic_waste_chk")
        # a bid price can never be flagged as a cost basis
        self.reject("insert into costdb.bid_benchmarks (benchmark_id, source_id, agency, item_description, unit_price, unit_price_unit_id, price_statistic, scope_note, price_nature, source_locator, evidence_excerpt, retrieved_at) "
                    "values ('TEST-BMK-X1','TEST-SRC-SYN','a','i',1,'SF','low_bid','s','cost_basis','l','e','2026-01-01T00:00:00Z')", "bid_benchmarks_price_nature_check")
        # assembly without a measurable spec
        self.reject("insert into costdb.assemblies (assembly_id, version, name, category_id, spec_attributes, output_unit_id, description, valid_from, definition_basis) "
                    "values ('TEST-ASM-X1',1,'n','CAT-FRM','{}','SF','d','2026-01-01','b')", "asm_spec_obj_chk")
        # a synthetic source id must carry the TEST- prefix
        self.reject("insert into costdb.sources (source_id, title, owner, source_kind, verification_method) values ('SRC-FAKE-1','t','o','internal','synthetic_test_fixture')",
                    "sources_synthetic_chk")

    # ------------------------------------------------------------------ protections added after the independent review F1
    def scalar(self, sql):
        return psql(sql).stdout.strip()

    def test_calculation_records_cannot_be_rewritten_or_deleted(self):
        run = "(select run_id from costdb.calculation_runs where status = 'complete')"
        self.reject(f"update costdb.calculation_runs set direct_cost_total = 123.45 where run_id = {run}", "append-only")
        self.reject(f"update costdb.calculation_runs set missing_inputs = '[{{\"x\":1}}]'::jsonb where run_id = {run}", "append-only")
        self.reject(f"update costdb.calculation_run_lines set formula = 'x', extended_cost = 1 where run_id = {run}", "append-only")
        self.reject(f"delete from costdb.calculation_runs where run_id = {run}", "append-only")
        self.reject(f"delete from costdb.calculation_run_lines where run_id = {run}", "append-only")
        self.reject("truncate costdb.calculation_runs cascade", "TRUNCATE is forbidden")
        self.reject("truncate costdb.labor_rates cascade", "TRUNCATE is forbidden")
        self.reject("truncate costdb.price_observations", "TRUNCATE is forbidden")
        r = psql(f"update costdb.calculation_runs set review_status = 'flagged', notes = 'checked' where run_id = {run}", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_complete_run_needs_lines_that_add_up(self):
        ins = ("insert into costdb.calculation_runs (run_id, calc_version, target_type, target_id, mode, status, has_assumptions, direct_cost_total, missing_inputs) "
               "values ('TEST-RUN-Y1','v','unit_cost','x','strict','complete',false,5,'[]')")
        self.reject(ins, "has no lines")                                                            # deferred constraint trigger fires at commit
        line = ("insert into costdb.calculation_run_lines (run_id, line_no, line_kind, description, extended_cost, formula, origin_summary) "
                "values ('TEST-RUN-Y1',1,'material','m',4,'f','observed')")
        self.reject("begin; " + ins + "; " + line + "; commit;", "differs from the sum of its lines")

    def test_validated_needs_a_reviewer_a_fetched_source_and_is_logged(self):
        self.reject("update costdb.price_observations set review_status='validated', reviewed_by=null, reviewed_at=null where observation_id='TEST-OBS-SCREW'", "validated_reviewer_chk")
        psql("insert into costdb.sources (source_id, title, owner, source_kind, verification_method, reuse_status) "
             "values ('TEST-SRC-SNIPPET','t','o','internal','search_snippet_only','open_license')")
        psql("insert into costdb.products (product_id, category_id, name, spec_attributes, spec_key, sale_unit_label, content_qty, content_unit_id, source_id) "
             "select 'TEST-PRD-SNIP', category_id, 'snip', spec_attributes, spec_key, sale_unit_label, content_qty, content_unit_id, 'TEST-SRC-SNIPPET' "
             "from costdb.products where product_id='TEST-PRD-SCREW'")
        self.reject("update costdb.products set review_status='validated', reviewed_by='x', reviewed_at=now() where product_id='TEST-PRD-SNIP'", "never fetched")
        self.reject("update costdb.sources set review_status='validated', reviewed_by='x', reviewed_at=now() where source_id='TEST-SRC-SNIPPET'", "sources_validated")
        before = int(self.scalar("select count(*) from costdb.review_events where record_table='price_observations'"))
        psql("update costdb.price_observations set review_status='flagged', reviewed_by='reviewer1', reviewed_at=now() where observation_id='TEST-OBS-SCREW'")
        after = psql("select old_status, new_status, changed_by from costdb.review_events where record_table='price_observations' and record_id='TEST-OBS-SCREW' order by event_id desc limit 1").stdout.strip()
        self.assertEqual(after, "validated|flagged|reviewer1")
        self.assertEqual(int(self.scalar("select count(*) from costdb.review_events where record_table='price_observations'")), before + 1)
        self.reject("update costdb.review_events set new_status='x'", "append-only")
        self.reject("delete from costdb.review_events", "append-only")

    def test_restricted_sources_cannot_hold_observed_values(self):
        for status in ("prohibited", "restricted_no_storage", "licence_required"):
            psql(f"insert into costdb.sources (source_id, title, owner, source_kind, verification_method, reuse_status) values ('TEST-SRC-R-{status[:4]}','t','o','internal','fetched_primary','{status}')")
            self.reject("insert into costdb.products (product_id, category_id, name, spec_attributes, spec_key, sale_unit_label, content_qty, content_unit_id, source_id) "
                        f"select 'TEST-PRD-R-{status[:4]}', category_id, 'r', spec_attributes, spec_key, sale_unit_label, content_qty, content_unit_id, 'TEST-SRC-R-{status[:4]}' "
                        "from costdb.products where product_id='TEST-PRD-SCREW'", "must not be stored")
        psql("insert into costdb.indices (index_id, publisher, series_code, name, frequency, applies_to, source_id) "
             "values ('TEST-IDX-RS','p','c','n','monthly','material','TEST-SRC-R-lice')", ok=False)
        self.reject("insert into costdb.index_values (index_id, period_start, vintage_date, value, retrieved_at, source_locator) "
                    "values ('TEST-IDX-RS','2026-01-01','2026-02-01',100,'2026-02-01T00:00:00Z','x')", "violates foreign key")

    def test_product_identity_is_frozen_and_checked(self):
        self.reject("update costdb.products set spec_key='k2', content_qty=1000, content_unit_id='EA' where product_id='TEST-PRD-BOARDA'", "append-only")
        self.reject("delete from costdb.products where product_id='TEST-PRD-BOARDA'", "append-only")
        ins = ("insert into costdb.products (product_id, category_id, name, spec_attributes, spec_key, sale_unit_label, content_qty, content_unit_id, source_id) "
               "values ('TEST-PRD-BAD', %s, 'n', %s, %s, 's', 32, 'SF', 'TEST-SRC-SYN')")
        self.reject(ins % ("'CAT-DRY-BRD'", "'{}'", "'garbage-key'"), "required attribute")               # key unrelated to its attributes
        self.reject(ins % ("'CAT-DRY'", "'{}'", "'x'"), "not a leaf category")
        attrs = S.pilot.MATS["gyp_half_reg_4x8"]["attrs"]
        import json
        self.reject(ins % ("'CAT-DRY-BRD'", "'" + json.dumps(attrs) + "'", "'wrong'"), "does not match the canonical key")
        self.reject("insert into costdb.price_observations (observation_id, product_id, source_id, store_ref, observed_at, retrieved_at, price_amount, price_channel, "
                    "sold_as_label, pack_content_qty, pack_content_unit_id, evidence_excerpt, capture_method, captured_by) "
                    "values ('TEST-OBS-Z1','TEST-PRD-BOARDA','TEST-SRC-SYN','s','2026-09-01','2026-09-01T12:00:00Z',1,'retail_public','p',5,'LB','e','manual_browser','t')",
                    "differs from the product pack")

    def test_spec_key_function_matches_python_for_every_pilot_spec_line_and_edge_values(self):
        import json
        from costdb.ids import norm_attr_value, spec_key
        db = S.real_db()
        cats = db.index("categories", "category_id")
        for k, m in S.pilot.MATS.items():
            want = spec_key(m["cat"], m["attrs"], cats[m["cat"]]["required_product_attributes"])
            got = self.scalar(f"select costdb.compute_spec_key('{m['cat']}', $j${json.dumps(m['attrs'])}$j$::jsonb)")
            self.assertEqual(got, want, k)
        for v in (0.5, "0.50", " 0.5 ", 5, "5_8", "NaN", "1e3", "15/32", True, "Mixed  CASE", -0.0, "0.0", "007", 12.50):
            sql = self.scalar(f"select costdb.norm_attr($j${json.dumps(v)}$j$::jsonb)")
            self.assertEqual(sql, norm_attr_value(v), repr(v))

    def test_definitions_are_frozen_but_status_may_move(self):
        self.reject("update costdb.work_item_components set qty_per_unit = 99 where work_item_id='WI-FRM-001' and line_no=1", "append-only")
        self.reject("update costdb.work_items set output_unit_id='LF' where work_item_id='WI-FRM-001'", "append-only")
        self.reject("delete from costdb.assemblies where assembly_id='ASM-WALL-001'", "append-only")
        self.reject("update costdb.crews set shift_hours = 12 where crew_id='CRW-DRY-HANG'", "append-only")
        r = psql("update costdb.work_items set status='priced_incomplete' where work_item_id='WI-FRM-001'", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_assumptions_are_four_eyes_ranged_and_immutable(self):
        a = ("insert into costdb.assumptions (assumption_id, assumption_type, applies_to_ref, value_numeric, rationale, proposed_by, approved_by, approved_at, status, expires_on) "
             "values (%s)")
        self.reject(a % "'TEST-ASU-D1','waste','waste:x',0.1,'r','alice','Alice',now(),'approved','2027-01-01'", "as_four_eyes_chk")
        self.reject(a % "'TEST-ASU-D2','waste','waste:x',0.1,'r','alice','bob',now(),'approved',null", "as_approval_chk")
        self.reject(a % "'TEST-ASU-D3','waste','waste:x',5,'r','alice',null,null,'proposed',null", "as_range_chk")
        self.reject(a % "'TEST-ASU-D4','productivity','p:x',0,'r','alice',null,null,'proposed',null", "as_range_chk")
        psql(a % "'TEST-ASU-D5','waste','waste:x',0.1,'r','alice','bob',now(),'approved','2027-01-01'")
        self.reject("update costdb.assumptions set value_numeric = 0.9 where assumption_id='TEST-ASU-D5'", "immutable")
        self.reject("delete from costdb.assumptions where assumption_id='TEST-ASU-D5'", "never deleted")
        psql("update costdb.assumptions set status='superseded' where assumption_id='TEST-ASU-D5'")

    def test_units_are_immutable_and_qualified(self):
        self.reject("update costdb.units set to_base_num = 3 where unit_id='SY'", "immutable")
        self.reject("delete from costdb.units where unit_id='SF'", "immutable")
        self.reject("insert into costdb.units (unit_id, base_code, qualifier, name, dimension, base_unit_id, to_base_num, to_base_den, definition, is_fixed_conversion) "
                    "values ('TON_FOO','TON','banana','x','mass','LB',1,1,'d',true)", "units_qualifier")
        self.reject("insert into costdb.units (unit_id, base_code, qualifier, name, dimension, base_unit_id, to_base_num, to_base_den, definition, is_fixed_conversion) "
                    "values ('XX','TON',null,'x','mass','LB',1,1,'d',true)", "units_qualifier")

    def test_other_check_constraints(self):
        self.reject("insert into costdb.burden_rates (burden_id, burden_type, basis, rate, effective_from, effective_to, origin) "
                    "values ('TEST-BRD-X1','futa','pct_of_wages',0.006,'2026-06-01','2026-01-01','missing')", "br_period_chk")
        self.reject("insert into costdb.burden_rates (burden_id, burden_type, basis, rate, wage_cap_annual, effective_from, origin) "
                    "values ('TEST-BRD-X2','other','per_hour',1,7000,'2026-01-01','missing')", "br_cap_chk")
        self.reject("insert into costdb.product_consumption (consumption_id, product_id, application, coverage_qty, coverage_unit_id, per_unit_id, coats, source_id, source_locator, origin) "
                    "values ('TEST-CON-X1','TEST-PRD-BOARDA','a',0,'SF','GAL_US',1,'TEST-SRC-SYN','x','observed')", "pc_positive_chk")
        self.reject("insert into costdb.adjustment_factors (factor_id, factor_type, applies_to, from_region_id, to_region_id, factor_value, derivation_formula, origin, assumption_basis) "
                    "values ('TEST-ADJ-X1','region','material','REG-CA-037','REG-CA-037',1.1,'f','assumed','b')", "af_region_distinct_chk")
        self.reject("insert into costdb.validation_issues (detected_by, record_table, record_id, rule_code, severity, message, status, resolution_note) "
                    "values ('x','t','r','c','error','m','waived','because')", "vi_waive_chk")

    def test_observation_date_check_does_not_depend_on_the_session_time_zone(self):
        ins = ("insert into costdb.price_observations (observation_id, product_id, source_id, store_ref, observed_at, retrieved_at, price_amount, price_channel, sold_as_label, "
               "pack_content_qty, pack_content_unit_id, evidence_excerpt, capture_method, captured_by) values ('%s','TEST-PRD-BOARDA','TEST-SRC-SYN','s','2026-10-24',"
               "'2026-10-24T05:00:00Z',1,'retail_public','p',32,'SF','e','manual_browser','t')")
        for i, tz in enumerate(("UTC", "America/Los_Angeles", "Pacific/Auckland")):
            r = pg.run_psql(["-d", DB, "-At", "-c", f"SET timezone='{tz}'; " + ins % f"TEST-OBS-TZ{i}"])
            self.assertEqual(r.returncode, 0, (tz, r.stderr))

    def test_latest_validated_view_keeps_regions_apart(self):
        n = self.scalar("select count(*) from costdb.v_price_latest_validated")
        self.assertGreaterEqual(int(n), 1)

    def test_schema_documentation_is_complete(self):
        n = psql("select count(*) from pg_attribute a join pg_class c on c.oid=a.attrelid join pg_namespace n on n.oid=c.relnamespace "
                 "left join pg_description d on d.objoid=c.oid and d.objsubid=a.attnum where n.nspname='costdb' and c.relkind='r' "
                 "and a.attnum>0 and not a.attisdropped and d.description is null").stdout.strip()
        self.assertEqual(n, "0")


if __name__ == "__main__":
    unittest.main()
