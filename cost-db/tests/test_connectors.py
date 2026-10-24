"""Connector tests. All inputs are SYNTHETIC format fixtures; nothing here is market data."""
import csv
import io
import json
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from tests.fixtures import synthetic as S

ROOT = Path(__file__).resolve().parents[1]
import importlib.util


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "pipeline" / "connectors" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m          # dataclasses need the module registered
    spec.loader.exec_module(m)
    return m


retail = load("retail_capture_import")
bls = load("bls_api")
oews = load("oews_flatfile")
pdft = load("pdf_tables")
TODAY = date(2026, 10, 24)


def row(**over):
    m = S.pilot.MATS["gyp_half_reg_4x8"]
    base = {k: "" for k in retail.TEMPLATE_COLUMNS}
    base.update(retailer_source_id="SRC-LOWES-TERMS-OF-USE", retailer_sku="SKU-1", manufacturer="TESTBRAND", brand="TESTBRAND", mpn="TB-1",
              product_name="TEST gypsum board 1/2 x 4x8", category_id=m["cat"], spec_attributes_json=json.dumps(m["attrs"]),
              sale_unit_label="each sheet", pack_content_qty="32", pack_content_unit_id="SF", price_amount="12.98",
              original_price_text="$12.98", price_channel="retail_public", observed_date="2026-10-20",
              retrieved_at="2026-10-20T15:00:00+00:00", zip="90245", region_id="REG-CA-037", evidence_excerpt="TEST listing: $12.98 each",
              capture_method="manual_browser", captured_by="tester", availability="in_stock", delivery_included="false",
              sales_tax_included="false")
    base.update(over)
    return base


class RetailImportTest(unittest.TestCase):
    def setUp(self):
        self.db = S.real_db()

    def run_rows(self, *rows):
        return retail.import_capture(list(rows), self.db, today=TODAY)

    def test_valid_manual_row_is_imported_with_normalisation_and_warning(self):
        rep = self.run_rows(row())
        self.assertEqual(rep.rejected, [], rep.rejected)
        self.assertEqual((len(rep.accepted_products), len(rep.accepted_observations)), (1, 1))
        o = self.db["price_observations"][0]
        self.assertEqual(o["pack_content_qty"], D("32"))
        self.assertEqual(o["capture_method"], "manual_browser")
        self.assertEqual(self.db["products"][0]["spec_key"], S.pilot.MATS["gyp_half_reg_4x8"]["spec_key"])
        self.assertTrue(any("prohibited" in w for _, w in rep.warnings))     # terms warning for a prohibited-terms source

    def test_automated_capture_from_prohibited_source_is_refused(self):
        rep = self.run_rows(row(capture_method="official_api"))
        self.assertEqual(len(rep.accepted_observations), 0)
        self.assertIn("manual_browser", rep.rejected[0][1][0])

    def test_source_with_no_storage_terms_is_refused(self):
        rep = self.run_rows(row(retailer_source_id="SRC-FRED-API"))
        self.assertEqual(len(rep.accepted_observations), 0)
        self.assertTrue(any("restricted_no_storage" in e for e in rep.rejected[0][1]))

    def test_unqualified_ton_and_gal_are_refused(self):
        for u in ("TON", "GAL"):
            rep = self.run_rows(row(pack_content_unit_id=u))
            self.assertEqual(len(rep.accepted_observations), 0, u)
            self.assertTrue(any("unknown unit" in e for e in rep.rejected[0][1]))

    def test_missing_spec_attribute_rejected_never_guessed(self):
        attrs = dict(S.pilot.MATS["gyp_half_reg_4x8"]["attrs"]); attrs.pop("fire_rated_x")
        rep = self.run_rows(row(spec_attributes_json=json.dumps(attrs)))
        self.assertEqual(len(rep.accepted_observations), 0)
        self.assertTrue(any("fire_rated_x" in e for e in rep.rejected[0][1]))

    def test_excerpt_must_support_the_price(self):
        rep = self.run_rows(row(evidence_excerpt="TEST listing: now only $9.99"))
        self.assertTrue(any("evidence_excerpt" in e for e in rep.rejected[0][1]))

    def test_retail_price_cannot_be_contractor_cost(self):
        rep = self.run_rows(row(is_contractor_cost="true"))
        self.assertTrue(any("contractor" in e for e in rep.rejected[0][1]))

    def test_dates_and_required_fields(self):
        self.assertTrue(self.run_rows(row(observed_date="2026-12-01")).rejected)
        self.assertTrue(self.run_rows(row(retrieved_at="2026-10-19T00:00:00+00:00")).rejected)
        r = self.run_rows(row(captured_by=""))
        self.assertIn("captured_by", r.rejected[0][1][0])

    def test_same_mpn_with_different_pack_is_a_different_sku(self):
        self.assertEqual(self.run_rows(row()).rejected, [])
        rep = self.run_rows(row(retailer_sku="SKU-2", pack_content_qty="48", observed_date="2026-10-21",
                                retrieved_at="2026-10-21T09:00:00+00:00"))
        self.assertEqual(len(rep.accepted_observations), 0)
        self.assertIn("different configuration", rep.rejected[0][1][0])

    def test_observations_are_append_only_and_duplicates_skipped(self):
        self.run_rows(row())
        rep = self.run_rows(row())
        self.assertEqual(len(rep.skipped_duplicates), 1)
        self.assertEqual(len(self.db["price_observations"]), 1)
        rep2 = self.run_rows(row(observed_date="2026-10-22", price_amount="13.48", original_price_text="$13.48",
                                 evidence_excerpt="TEST listing: $13.48 each", retrieved_at="2026-10-22T10:00:00+00:00"))
        self.assertEqual(len(rep2.accepted_observations), 1)
        self.assertEqual(len(self.db["price_observations"]), 2)        # new price adds a row; the old one stays
        self.assertEqual(len(self.db["products"]), 1)

    def test_zip_map_fills_region(self):
        rep = retail.import_capture([row(region_id="")], self.db, today=TODAY, zip_map={"90245": "REG-CA-037"})
        self.assertEqual(rep.rejected, [])
        self.assertEqual(self.db["price_observations"][0]["region_id"], "REG-CA-037")

    def test_template_header_matches_importer(self):
        with open(ROOT / "templates" / "price_capture_template.csv", newline="", encoding="utf-8") as fh:
            self.assertEqual(next(csv.reader(fh)), retail.TEMPLATE_COLUMNS)


class BlsApiTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "tests" / "fixtures" / "bls_api_format_fixture.json").read_text())

    def test_limits_enforced_and_key_not_in_payload_without_key(self):
        with self.assertRaises(bls.BlsError):
            bls.build_payload([f"S{i:05d}AA" for i in range(26)], 2020, 2024, None)
        with self.assertRaises(bls.BlsError):
            bls.build_payload(["ABCDEF"], 2000, 2020, "k")
        p = bls.build_payload(["ABCDEF"], 2020, 2024, None)
        self.assertNotIn("registrationkey", p)
        self.assertEqual(sum(1 for _ in bls.batches([f"S{i:05d}AA" for i in range(120)], 2000, 2045, "k")), 3 * 3)

    def test_parse_and_convert(self):
        pts = bls.parse_response(self.data)
        self.assertEqual(len(pts), 6)
        rows = bls.to_index_values(pts, {"TESTSERIES01": "TEST-IDX-A", "TESTSERIES02": "TEST-IDX-B"}, date(2026, 10, 24),
                                   "2026-10-24T00:00:00+00:00", "fixture", None)
        by = {(r["index_id"], r["period_start"]): r for r in rows}
        self.assertEqual(by[("TEST-IDX-A", date(2026, 3, 1))]["value_status"], "preliminary")
        self.assertEqual(by[("TEST-IDX-A", date(2026, 2, 1))]["value_status"], "final")
        self.assertNotIn(("TEST-IDX-A", date(2026, 1, 1)), by)          # '-' = no data, never stored
        self.assertEqual(len(rows), 4)                                    # M13 (annual average) skipped
        self.assertEqual(by[("TEST-IDX-B", date(2025, 10, 1))]["value"], D("171.690"))
        self.assertEqual(by[("TEST-IDX-B", date(2025, 1, 1))]["value"], D("160.000"))

    def test_failed_response_raises(self):
        with self.assertRaises(bls.BlsError):
            bls.parse_response({"status": "REQUEST_NOT_PROCESSED", "message": ["limit"]})


class OewsTest(unittest.TestCase):
    CSV = ("AREA,AREA_TITLE,OCC_CODE,OCC_TITLE,H_MEAN,H_MEDIAN\n"
           "99999,Testville,47-2031,Carpenters,30.00,28.50\n"
           "99999,Testville,47-2081,Drywall installers,#,*\n"
           "99999,Testville,11-1011,Chief executives,90.00,80.00\n"
           "88888,Otherville,47-2031,Carpenters,31.00,29.00\n")

    def rows(self):
        return list(csv.DictReader(io.StringIO(self.CSV)))

    def test_parse_suppressed_censored_and_unmapped(self):
        out, notes = oews.parse_oews(self.rows(), {"47-2031": "TR-CARP", "47-2081": "TR-DRYW"}, {"99999": "REG-CA-037"},
                                     "SRC-TEST", date(2025, 5, 1), "oews_fixture.csv", None, "2026-10-24T00:00:00+00:00")
        self.assertEqual(len(out), 2)                                      # mean+median of carpenters only
        self.assertEqual({r["statistic"] for r in out}, {"mean", "median"})
        self.assertTrue(all(not r["includes_fringe"] and r["use_context"] == "statistical_reference" for r in out))
        self.assertEqual(len(notes), 2)                                    # '#' and '*' reported, not stored
        self.assertTrue(all("row 3" in n for n in notes))
        self.assertEqual({r["base_wage_hr"] for r in out}, {D("30.00"), D("28.50")})
        self.assertIn("oews_fixture.csv, data row 2", out[0]["source_locator"])

    def test_missing_columns_fail_loudly(self):
        bad = [{"AREA": "1", "AREA_TITLE": "x", "OCC_CODE": "47-2031", "H_MEAN": "1"}]       # H_MEDIAN absent
        with self.assertRaises(oews.OewsError):
            oews.parse_oews(bad, {}, {}, "SRC-TEST", date(2025, 5, 1), "f", None, "t")

    def test_deterministic_ids(self):
        a, _ = oews.parse_oews(self.rows(), {"47-2031": "TR-CARP"}, {"99999": "REG-CA-037"}, "SRC-TEST", date(2025, 5, 1), "f", None, "t")
        b, _ = oews.parse_oews(self.rows(), {"47-2031": "TR-CARP"}, {"99999": "REG-CA-037"}, "SRC-TEST", date(2025, 5, 1), "f", None, "t")
        self.assertEqual([r["labor_rate_id"] for r in a], [r["labor_rate_id"] for r in b])


class PdfToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            raise unittest.SkipTest("reportlab not installed")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pdf = Path(cls.tmp.name) / "synthetic_norms.pdf"
        data = [["Operation", "Crew", "Daily output", "Unit"], ["TEST hang board", "3", "1600", "SF"], ["TEST tape joints", "2", "900", "SF"]]
        t = Table(data)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
        SimpleDocTemplate(str(cls.pdf), pagesize=letter).build([t, Paragraph("Note: synthetic test table, not a real norm.", getSampleStyleSheet()["Normal"])])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_tables_notes_and_hash(self):
        tabs = pdft.extract_tables(self.pdf)
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0].rows[1], ["TEST hang board", "3", "1600", "SF"])
        self.assertEqual(tabs[0].page, 1)
        self.assertEqual(len(tabs[0].sha256), 64)
        self.assertTrue(any("synthetic test table" in n for n in tabs[0].notes_below))

    def test_qa_sample_renders_png_pages(self):
        tabs = pdft.extract_tables(self.pdf)
        man = pdft.qa_sample(self.pdf, tabs, Path(self.tmp.name) / "qa", n=3)
        self.assertEqual(len(man), 3)
        for m in man:
            p = Path(m["png"])
            self.assertTrue(p.exists() and p.stat().st_size > 1000)
        again = pdft.qa_sample(self.pdf, tabs, Path(self.tmp.name) / "qa2", n=3)
        self.assertEqual([(m["row"], m["col"]) for m in man], [(m["row"], m["col"]) for m in again])    # deterministic sample

    def test_reading_order_check_quiet_on_normal_pdf(self):
        self.assertEqual(pdft.words_in_reading_order_check(self.pdf), [])


if __name__ == "__main__":
    unittest.main()
