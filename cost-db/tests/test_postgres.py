"""Tests against a real PostgreSQL server (skipped unless PGHOST/PGPORT/PGUSER point to a scratch server).

  PGHOST=/var/tmp/owl_pgsock PGPORT=5544 PGUSER=postgres python3 tests/run_tests.py
"""
import os
import tempfile
import unittest
from pathlib import Path

from costdb import pg
from costdb.calc import Engine
from costdb.units import Units
from tests.fixtures import synthetic as S

ROOT = Path(__file__).resolve().parents[1]
HAVE_PG = bool(os.environ.get("PGHOST") or os.environ.get("PGPORT"))
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


@unittest.skipUnless(HAVE_PG, "no PostgreSQL server configured")
class PostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        total = psql("select direct_cost_total from costdb.calculation_runs").stdout.strip()
        self.assertEqual(total, str(self.expected_total))
        self.assertEqual(psql("select count(*) from costdb.calculation_run_lines where jsonb_array_length(inputs) > 0").stdout.strip(), "3")

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
        # unqualified ton / unknown unit
        self.reject(base_obs + ") values ('TEST-OBS-X2','TEST-PRD-BOARDA','TEST-SRC-SYN','s','2026-09-01','2026-09-01T12:00:00Z',1,'retail_public',false,'p',32,'TON','e','manual_browser','t')",
                    "violates foreign key")
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
        self.reject("update costdb.work_item_components set waste_factor=0.1, waste_origin='assumed', waste_basis='x' where line_no=1 and work_item_id='WI-FRM-001'", "wic_waste_chk")
        self.reject("update costdb.work_item_components set waste_factor=0.1, waste_origin='observed', waste_basis=null where line_no=1 and work_item_id='WI-FRM-001'", "wic_waste_chk")
        # a bid price can never be flagged as a cost basis
        self.reject("insert into costdb.bid_benchmarks (benchmark_id, source_id, agency, item_description, unit_price, unit_price_unit_id, price_statistic, scope_note, price_nature, source_locator, evidence_excerpt, retrieved_at) "
                    "values ('TEST-BMK-X1','TEST-SRC-SYN','a','i',1,'SF','low_bid','s','cost_basis','l','e','2026-01-01T00:00:00Z')", "bid_benchmarks_price_nature_check")
        # assembly without a measurable spec
        self.reject("insert into costdb.assemblies (assembly_id, version, name, category_id, spec_attributes, output_unit_id, description, valid_from, definition_basis) "
                    "values ('TEST-ASM-X1',1,'n','CAT-FRM','{}','SF','d','2026-01-01','b')", "asm_spec_obj_chk")
        # a synthetic source id must carry the TEST- prefix
        self.reject("insert into costdb.sources (source_id, title, owner, source_kind, verification_method) values ('SRC-FAKE-1','t','o','internal','synthetic_test_fixture')",
                    "sources_synthetic_chk")

    def test_schema_documentation_is_complete(self):
        n = psql("select count(*) from pg_attribute a join pg_class c on c.oid=a.attrelid join pg_namespace n on n.oid=c.relnamespace "
                 "left join pg_description d on d.objoid=c.oid and d.objsubid=a.attnum where n.nspname='costdb' and c.relkind='r' "
                 "and a.attnum>0 and not a.attisdropped and d.description is null").stdout.strip()
        self.assertEqual(n, "0")


if __name__ == "__main__":
    unittest.main()
