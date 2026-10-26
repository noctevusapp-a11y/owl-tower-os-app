"""The build pipeline end to end on a throw-away copy of the data: promotion, a second build, and refusal to write on errors."""
import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "pipeline")]

from costdb.store import Database  # noqa: E402
from tests.fixtures import synthetic as S  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_script", ROOT / "pipeline" / "scripts" / "build.py")
build_script = importlib.util.module_from_spec(_spec)
sys.modules["build_script"] = build_script
_spec.loader.exec_module(build_script)


def quiet_build(root, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return build_script.build(root, **kw)


def add_fetched_capture(db: Database, evidence=True):
    """A non-synthetic, fetched, open-licence source with one product and one observation (all unreviewed)."""
    db.add("sources", {"source_id": "SRC-BUILDTEST", "title": "Build test source", "owner": "tests", "source_kind": "manufacturer_doc", "url": "https://example.invalid/x",
                       "data_url": None, "data_provided": "one price", "geography": None, "period_covered": None, "edition": None, "access_format": None,
                       "requires_registration": None, "requires_payment": None, "access_notes": None, "reuse_status": "open_license", "reuse_terms": None,
                       "reuse_terms_url": None, "limitations": "test", "update_frequency": None, "quality_tier": "A", "reachability_from_build_env": "reachable",
                       "reachability_checked_at": None, "verification_method": "fetched_primary", "evidence_quote": "q", "evidence_url": "https://example.invalid/x",
                       "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "registered_at": date(2026, 10, 24), "notes": None})
    m = S.pilot.MATS["gyp_half_reg_4x8"]
    db.add("products", {"product_id": "PRD-BUILDTEST", "category_id": m["cat"], "name": "Build test board", "brand": "BT", "manufacturer": "BT", "mpn": "BT-1",
                        "description": None, "spec_attributes": m["attrs"], "spec_key": m["spec_key"], "standards": [], "sale_unit_label": m["sale"],
                        "content_qty": D("32"), "content_unit_id": "SF", "content_note": None, "source_id": "SRC-BUILDTEST", "source_locator": "p1" if evidence else None,
                        "evidence_excerpt": "x" if evidence else None, "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
                        "created_at": None, "notes": None})
    db.add("price_observations", {"observation_id": "OBS-BUILDTEST", "product_id": "PRD-BUILDTEST", "source_id": "SRC-BUILDTEST", "retailer_sku": "S1", "store_ref": "st",
                                  "zip": "90245", "region_id": "REG-CA-037", "observed_at": date(2026, 10, 20), "retrieved_at": "2026-10-20T15:00:00+00:00",
                                  "price_amount": D("12.98"), "currency": "USD", "original_price_text": "$12.98", "price_channel": "supplier_quote",
                                  "is_contractor_cost": True, "sold_as_label": "sheet", "pack_content_qty": D("32"), "pack_content_unit_id": "SF",
                                  "availability": "in_stock", "delivery_included": False, "sales_tax_included": False, "promo_flag": False, "qty_limit_text": None,
                                  "qty_tier_min": None, "url": None, "source_locator": "q1", "evidence_excerpt": "$12.98", "raw_file_sha256": None,
                                  "capture_method": "supplier_quote_document", "captured_by": "tests", "origin": "observed", "review_status": "unreviewed",
                                  "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="costdb_build_"))
        for d in ("data", "docs"):
            shutil.copytree(ROOT / d, self.tmp / d)
        self.csv = self.tmp / "data" / "csv"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mutate(self, fn):
        db = Database.load_csv_dir(self.csv)
        fn(db)
        db.write_csv_dir(self.csv)

    def test_real_data_builds_twice_and_reproduces_itself(self):
        self.assertEqual(quiet_build(self.tmp, skip_tests=True), 0)
        first = {p.name: p.read_bytes() for p in self.csv.glob("*.csv")}
        self.assertEqual(quiet_build(self.tmp, skip_tests=True), 0)
        self.assertEqual(first, {p.name: p.read_bytes() for p in self.csv.glob("*.csv")}, "a rebuild of unchanged data must be byte-identical")

    def test_promotion_then_a_second_build_does_not_crash(self):
        self.mutate(add_fetched_capture)
        self.assertEqual(quiet_build(self.tmp, skip_tests=True), 0)                    # build 1: promotes (review_events gets rows)
        st = json.loads((self.tmp / "data" / "json" / "pilot_status.json").read_text())
        self.assertEqual(st["promoted_to_validated"], {"price_observations": 1, "products": 1})
        db = Database.load_csv_dir(self.csv)
        self.assertEqual(len(db["review_events"]), 2)
        self.assertEqual({p["review_status"] for p in db["products"]}, {"validated"})
        self.assertEqual(quiet_build(self.tmp, skip_tests=True), 0)                    # build 2: used to die with KeyError('review_events')
        self.assertEqual(len(Database.load_csv_dir(self.csv)["review_events"]), 2, "nothing new to promote, no duplicate events")

    def test_a_row_without_evidence_is_not_promoted(self):
        self.mutate(lambda db: add_fetched_capture(db, evidence=False))
        self.assertEqual(quiet_build(self.tmp, skip_tests=True), 0)
        db = Database.load_csv_dir(self.csv)
        self.assertEqual({p["review_status"] for p in db["products"]}, {"unreviewed"})

    def test_errors_in_the_data_stop_the_build_before_anything_is_written(self):
        before_runs = (self.csv / "calculation_runs.csv").read_bytes()
        before_status = (self.tmp / "data" / "json" / "pilot_status.json").read_bytes()

        def bad(db):
            add_fetched_capture(db)
            db["sources"][-1]["verification_method"] = "search_snippet_only"                   # ...but a row claims to be validated from it
            db["price_observations"][-1].update(review_status="validated", reviewed_by="x", reviewed_at="2026-10-24T00:00:00+00:00")
        self.mutate(bad)
        before_runs = (self.csv / "calculation_runs.csv").read_bytes()
        self.assertEqual(quiet_build(self.tmp, skip_tests=True), 1)
        self.assertEqual((self.csv / "calculation_runs.csv").read_bytes(), before_runs)
        self.assertEqual((self.tmp / "data" / "json" / "pilot_status.json").read_bytes(), before_status)

    def test_run_policy_states_a_basis_for_every_result_affecting_parameter(self):
        pol = json.loads((ROOT / "data" / "run_policy.json").read_text())
        for k in build_script.NEEDS_BASIS:
            if k in pol["params"]:
                self.assertTrue(pol["basis"].get(k, "").strip(), k)
        params, _ = build_script.load_policy(ROOT)
        self.assertEqual((params.mode, params.min_review, params.annual_paid_hours), ("strict", "validated", D("2080")))
        pol["basis"].pop("annual_paid_hours")
        (self.tmp / "data" / "run_policy.json").write_text(json.dumps(pol))
        with self.assertRaises(SystemExit):
            build_script.load_policy(self.tmp)


if __name__ == "__main__":
    unittest.main()
