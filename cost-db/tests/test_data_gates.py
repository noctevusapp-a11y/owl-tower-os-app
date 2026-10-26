"""Gates on the REAL data files in data/: nothing synthetic, nothing 'validated' without a fetched source, evidence matches numbers."""
import csv
import importlib.util
import re
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

from costdb.schema_meta import parse_schema
from costdb.store import Database
from tests.fixtures import synthetic as S

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "csv"


class DataGatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database.load_csv_dir()

    def test_no_synthetic_fixture_leaked_into_data(self):
        for p in CSV.glob("*.csv"):
            text = p.read_text(encoding="utf-8")
            self.assertNotIn("synthetic_test_fixture", text, p.name)
            self.assertFalse(re.search(r"(^|,)TEST-", text, re.M), f"{p.name} contains TEST- ids")
        for p in (ROOT / "data" / "json").glob("*.json"):
            self.assertNotIn("synthetic_test_fixture", p.read_text(encoding="utf-8"))

    def test_csv_files_match_the_schema_exactly(self):
        meta = parse_schema()
        for t, cols in meta.items():
            p = CSV / f"{t}.csv"
            self.assertTrue(p.exists(), f"missing {p.name}")
            with open(p, newline="", encoding="utf-8") as fh:
                header = next(csv.reader(fh))
            self.assertEqual(header, [c.name for c in cols if not c.generated], t)
        self.assertEqual({p.stem for p in CSV.glob("*.csv")}, set(meta))

    def test_validated_means_fetched_primary_with_hash(self):
        src = self.db.index("sources", "source_id")
        for t in ("price_observations", "labor_rates", "equipment_rates", "productivity_observations", "burden_rates", "index_values", "product_consumption"):
            for r in self.db[t]:
                if r["review_status"] == "validated":
                    s = src[r["source_id"]]
                    self.assertEqual(s["verification_method"], "fetched_primary", f"{t} validated from a source that was never fetched")
                    if "raw_file_sha256" in r:
                        self.assertTrue(r["raw_file_sha256"], f"{t} validated without a raw file hash")

    def test_every_source_is_search_level_until_a_file_is_fetched(self):
        # current state of the project: no primary document could be fetched from the build environment
        self.assertTrue(all(s["verification_method"] != "synthetic_test_fixture" for s in self.db["sources"]))
        fetched = [s["source_id"] for s in self.db["sources"] if s["verification_method"] == "fetched_primary"]
        for sid in fetched:
            self.assertTrue(any(r.get("raw_file_sha256") for t in ("labor_rates", "equipment_rates", "index_values") for r in self.db[t]
                                if r.get("source_id") == sid), f"{sid} marked fetched but no record carries a file hash")

    def test_imported_numbers_appear_in_their_evidence(self):
        for r in self.db["labor_rates"]:
            if r["origin"] == "observed":
                self.assertIn(f"{r['base_wage_hr']:.2f}", r["evidence_excerpt"])
        expect = {"fica_social_security": ["6.2%", "184,500"], "fica_medicare": ["1.45%"], "state_ett": ["0.1 percent", "$7,000"]}
        for b in self.db["burden_rates"]:
            for token in expect[b["burden_type"]]:
                self.assertIn(token, b["evidence_excerpt"], b["burden_id"])
        self.assertEqual(self.db["index_values"], [], "FRED terms: no index values may be stored from FRED pages")
        for i in self.db["indices"]:
            self.assertIn("FRED", i["notes"])

    def test_review_corrections_are_consistent_with_the_register(self):
        import json
        corr = json.loads((ROOT / "data" / "register_corrections.json").read_text(encoding="utf-8"))
        src = self.db.index("sources", "source_id")
        for c in corr["source_corrections"]:
            self.assertIn(c["source_id"], src, "correction points at an unknown source")
            row = src[c["source_id"]]
            for k, v in c["set"].items():
                self.assertEqual(row[k], v, f"{c['source_id']}.{k} was not corrected")
            self.assertIn("CORRECTION (reviewer", row["notes"])
            if c["set"].get("review_status") == "flagged":
                self.assertTrue(row["reviewed_by"])
        for s in src.values():
            if s["review_status"] == "flagged":
                self.assertTrue(s["reviewed_by"] and "CORRECTION" in s["notes"], s["source_id"])
        # values from FRED-type sources can never be data: no record may reference them
        banned = {sid for sid, s in src.items() if s["reuse_status"] in ("prohibited", "restricted_no_storage")}
        for t in ("labor_rates", "burden_rates", "equipment_rates", "productivity_observations", "price_observations", "products"):
            for r in self.db[t]:
                self.assertNotIn(r.get("source_id"), banned, t)
        with open(ROOT / "data" / "evidence_digest.csv", newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertIn("reviewer_note", rows[0])
        self.assertEqual(sum(1 for r in rows if r["reviewer_note"]), sum(len(v) for v in corr["digest_notes"].values()))
        voc = [r for r in rows if "EVEREST VOC" in r["topic"]]
        self.assertTrue(voc and "CONTRADICTED" in voc[0]["reviewer_note"])

    def test_no_numbers_were_invented_for_missing_inputs(self):
        for p in self.db["productivity_observations"]:
            self.assertEqual(p["origin"], "missing")
            for k in ("crew_size", "shift_hours", "daily_output", "person_hours_per_unit_reported"):
                self.assertIsNone(p[k])
        for c in self.db["crews"]:
            self.assertEqual(c["origin"], "missing"); self.assertIsNone(c["shift_hours"])
        self.assertEqual(self.db["crew_members"], [])
        for w in self.db["work_item_components"]:
            self.assertIsNone(w["waste_factor"], "waste factors must come with a source")
        self.assertEqual([], self.db["products"] + self.db["price_observations"] + self.db["equipment_rates"] + self.db["assumptions"])

    def test_capture_targets_cover_every_component_spec(self):
        targets = {t["spec_key"] for t in self.db["capture_targets"] if t["target_kind"] == "material"}
        self.assertGreaterEqual(len(targets), 100)
        self.assertEqual(len(targets), len([t for t in self.db["capture_targets"] if t["target_kind"] == "material"]))
        for c in self.db["work_item_components"]:
            if c["product_spec_key"]:
                self.assertIn(c["product_spec_key"], targets)
        pilot = [t for t in self.db["capture_targets"] if t["target_kind"] == "material"]
        self.assertTrue(all(t["status"] == "open" for t in pilot))

    def test_pilot_scope_counts(self):
        self.assertEqual(len(self.db["work_items"]), 25)
        self.assertEqual(len(self.db["assemblies"]), 10)
        cats = {w["category_id"] for w in self.db["work_items"]}
        self.assertEqual(cats, {"CAT-FRM", "CAT-DRY", "CAT-INS", "CAT-CON", "CAT-PNT", "CAT-HVC"})

    def test_quantities_match_independent_arithmetic(self):
        """Re-derive geometry quantities with exact fractions, independently of the generator."""
        q = {(c["work_item_id"], c["line_no"]): c for c in self.db["work_item_components"]}

        def val(w, n):
            return F(str(q[(w, n)]["qty_per_unit"]))

        def close(a, b):
            self.assertLess(abs(a - b), F(1, 10 ** 9), (a, b))
        # wall height: 92-5/8 in precut stud + 3 x 1.5 in plates = 97.125 in = 8.09375 ft (NOT a nominal 8 ft)
        h_ft = (F(92) + F(5, 8) + 3 * F(3, 2)) / 12
        self.assertEqual(h_ft, F(97125, 12000))
        studs_sf = F(12, 16) / h_ft                                  # studs per SF @16 in o.c.
        for w in ("WI-FRM-001", "WI-FRM-002"):
            close(val(w, 1), studs_sf)
            close(val(w, 2), 3 / h_ft)                                # bottom plate + double top plate per LF of wall
            close(val(w, 3), studs_sf * 4 + studs_sf)                 # 4 end nails per stud + 1 lamination nail per 16 in of top plate
        close(val("WI-FRM-003", 1), F(3, 4)); close(val("WI-FRM-003", 2), F(3, 4) / 12 * 2)
        close(val("WI-FRM-004", 2), F(64, 32))
        close(val("WI-FRM-005", 1), F(3, 4) / 10); close(val("WI-FRM-005", 2), F(1, 5)); close(val("WI-FRM-005", 3), F(3, 4) / 10 * 4)
        close(val("WI-FRM-006", 1), F(29, 2) / 16); close(val("WI-FRM-006", 2), F(3))
        # drywall: screws are counted with the fence-post rule at BOTH ends: lines = across // framing + 1, per line = along // spacing + 1
        def screws(across_in, along_in, framing_in, spacing_in):
            return (across_in // framing_in + 1) * (along_in // spacing_in + 1)
        close(val("WI-DRY-001", 2), F(screws(48, 96, 16, 16), 32))       # 4 x 8 sheet vertical on 16 in studs, screws @16: 28/32
        close(val("WI-DRY-002", 2), F(screws(48, 96, 16, 16), 32))
        close(val("WI-DRY-006", 2), F(screws(48, 96, 16, 16), 32))
        close(val("WI-DRY-003", 2), F(screws(144, 48, 16, 16), 48))      # 4 x 12 sheet horizontal: 10 lines x 4 = 40 per 48 SF
        close(val("WI-DRY-004", 2), F(screws(96, 48, 16, 12), 32))       # 4 x 8 ceiling sheet across 16 in joists, screws @12: 35/32
        close(val("WI-DRY-005", 1), F(12, 32))
        close(val("WI-INS-001", 1), F(15, 16))                           # 15 in batt in a 16 in pitch
        close(val("WI-CON-001", 1), F(4, 12) / 27); close(val("WI-CON-002", 1), F(6, 12) / 27)
        close(val("WI-CON-002", 3), F(3, 2)); close(val("WI-CON-003", 1), F(3, 2) / 27); close(val("WI-CON-004", 1), F(1, 4))
        close(val("WI-PNT-004", 1), F(3, 4) / 231)                 # 1/4" x 1/4" bead per LF in US gallons
        for a in self.db["assembly_components"]:                    # assembly quantities are whole faces / parameters
            self.assertIn(a["qty_per_assembly_unit"], {1, 2, 50})

    def test_scope_tokens_never_include_shared_activities(self):
        shared = {"mobilization", "daily_cleanup_and_protection", "overhead_and_profit", "supervision_and_general_conditions"}
        for w in self.db["work_items"]:
            self.assertFalse(shared & set(w["included_scope"]), w["work_item_id"])
            self.assertTrue(shared <= set(w["excluded_scope"]), w["work_item_id"])


class StorageTest(unittest.TestCase):
    def test_csv_round_trip_is_lossless(self):
        import tempfile
        db = S.priced_drywall_db()
        with tempfile.TemporaryDirectory() as d:
            db.write_csv_dir(Path(d))
            back = Database.load_csv_dir(Path(d))
        for t in db.meta:
            gen = {c.name for c in db.meta[t] if c.generated}
            a = [{k: v for k, v in r.items() if k not in gen and k != "created_at"} for r in db[t]]
            b = [{k: v for k, v in r.items() if k not in gen and k != "created_at"} for r in back[t]]
            self.assertEqual(a, b, t)

    def test_pg_array_literals(self):
        from costdb.store import format_pg_array, parse_pg_array
        for items in ([], ["a"], ["a", "b c", 'q"x', "d,e", "{x}"]):
            self.assertEqual(parse_pg_array(format_pg_array(items)), items)

    def test_every_column_is_documented_and_docs_are_current(self):
        from costdb.dictionary import describe
        for t, cols in parse_schema().items():
            for c in cols:
                self.assertTrue(describe(t, c.name), f"{t}.{c.name} undocumented")
        spec = importlib.util.spec_from_file_location("build_docs", ROOT / "pipeline" / "scripts" / "build_docs.py")
        m = importlib.util.module_from_spec(spec); sys.modules["build_docs"] = m; spec.loader.exec_module(m)
        sql, md = m.render()
        self.assertEqual((ROOT / "schema" / "003_comments.sql").read_text(encoding="utf-8"), sql, "run build_docs.py")
        self.assertEqual((ROOT / "docs" / "data_dictionary.md").read_text(encoding="utf-8"), md, "run build_docs.py")

    def test_ids_are_deterministic_and_well_formed(self):
        from costdb.ids import make_id
        self.assertEqual(make_id("PRD", "ACME ", " X-1"), make_id("PRD", "acme", "x-1"))
        self.assertNotEqual(make_id("PRD", "acme", "x-1"), make_id("PRD", "acme", "x-2"))
        db = Database.load_csv_dir()
        idre = re.compile(r"^[A-Z][A-Z0-9]{1,5}-[A-Za-z0-9._-]{1,80}$")
        for t, key in (("sources", "source_id"), ("work_items", "work_item_id"), ("assemblies", "assembly_id"), ("capture_targets", "target_id"),
                       ("work_item_components", "component_id"), ("crews", "crew_id"), ("regions", "region_id"), ("categories", "category_id")):
            for r in db[t]:
                self.assertRegex(r[key], idre)


if __name__ == "__main__":
    unittest.main()
