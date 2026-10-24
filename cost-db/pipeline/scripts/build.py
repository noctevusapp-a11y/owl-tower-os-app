#!/usr/bin/env python3
"""Full rebuild of derived artifacts from the CSV tables.

  1. load data/csv            2. validate (production gate)         3. strict calculations for all 25 work items + 10 assemblies
  4. write all CSV tables     5. write data/json/costdb.json        6. write reports (coverage, backlog, validation, status)

Run:  python3 -I pipeline/scripts/build.py [--skip-tests]
Prerequisite generators (run once, or when their inputs change):
  gen_reference.py, ingest_agent_returns.py, gen_pilot_definitions.py, build_docs.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb import BUILD_TS, CALC_VERSION  # noqa: E402
from costdb.calc import Engine, RunParams  # noqa: E402
from costdb.report import backlog, counts, coverage_matrix, validation_report  # noqa: E402
from costdb.store import Database  # noqa: E402
from costdb.validate import promote_validated, validate  # noqa: E402

AS_OF = date.fromisoformat(BUILD_TS[:10])
REGION = "REG-CA-037"


def git_ref() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or None
    except OSError:
        return None


def main() -> int:
    skip_tests = "--skip-tests" in sys.argv
    db = Database.load_csv_dir()
    db.tables["calculation_runs"] = []
    db.tables["calculation_run_lines"] = []
    db.tables["validation_issues"] = []

    # ---- strict calculations for the whole pilot: expected to be INCOMPLETE until data exists; the runs document exactly why
    eng = Engine(db, code_ref=None)
    params = RunParams(region_id=REGION, as_of=AS_OF, mode="strict", min_review="validated", labor_basis="stat_loaded",
                       project_type="private", run_at=BUILD_TS)
    seen: set[str] = set()
    results = []
    for w in db["work_items"]:
        results.append(eng.unit_cost(w["work_item_id"], w["version"], params))
    for a in db["assemblies"]:
        results.append(eng.assembly_cost(a["assembly_id"], a["version"], params))
    for res in results:
        for r in res.flatten():
            if r.run["run_id"] in seen:
                continue
            seen.add(r.run["run_id"])
            db.add("calculation_runs", r.run)
            for ln in r.lines:
                db.add("calculation_run_lines", ln)

    # ---- validation (production gate: synthetic fixtures are errors) and strict promotion
    issues = validate(db, today=AS_OF, production=True, engine=eng)
    promoted = promote_validated(db, issues, "costdb.build", BUILD_TS)
    for i in issues:
        row = i.as_row("costdb.build")
        row["detected_at"] = BUILD_TS
        db.add("validation_issues", row)
    errors = [i for i in issues if i.severity == "error"]

    # ---- write data
    db.write_csv_dir(ROOT / "data" / "csv")
    db.write_json(ROOT / "data" / "json" / "costdb.json")
    sources = [s for s in db["sources"]]
    (ROOT / "data" / "json" / "source_register.json").write_text(
        json.dumps(db.to_json_obj()["sources"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "data" / "source_register.csv").write_text((ROOT / "data" / "csv" / "sources.csv").read_text(encoding="utf-8"), encoding="utf-8")

    # ---- reports
    if skip_tests:
        test_summary = "_(test run skipped in this build)_"
    else:
        r = subprocess.run([sys.executable, "-B", str(ROOT / "tests" / "run_tests.py")], capture_output=True, text=True, cwd=ROOT)
        tail = (r.stderr or r.stdout).strip().splitlines()
        ran = next((l for l in tail if l.startswith("Ran ")), "Ran ? tests")
        ok = "OK" in tail[-1] if tail else False
        skipped = next((l for l in tail if "skipped" in l), "")
        test_summary = (f"`python3 tests/run_tests.py` → **{ran}, {'ALL PASSED' if ok else 'FAILURES — see output'}** {skipped}  \n"
                        f"(PostgreSQL tests run only when `PGHOST`/`PGPORT`/`PGUSER` point to a scratch server.)")
        if not ok:
            print(r.stderr[-3000:])
    gaps = {}
    for p in sorted((ROOT / "data" / "raw_agent_returns").glob("agent_A*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        gaps[d["agent"]] = d["gaps"]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "coverage_matrix.md").write_text(coverage_matrix(db), encoding="utf-8")
    (ROOT / "docs" / "data_gaps_backlog.md").write_text(backlog(db, gaps), encoding="utf-8")
    (ROOT / "docs" / "validation_report.md").write_text(validation_report(db, issues, test_summary, BUILD_TS), encoding="utf-8")
    c = counts(db)
    c.update({"build_timestamp": BUILD_TS, "calc_version": CALC_VERSION, "validation_errors": len(errors), "validation_issues": len(issues),
              "promoted_to_validated": promoted, "region": REGION, "as_of": AS_OF.isoformat(), "git_ref": git_ref()})
    (ROOT / "data" / "json" / "pilot_status.json").write_text(json.dumps(c, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: c[k] for k in ("unique_products", "price_observations", "material_spec_lines_targeted", "work_items_defined",
                                       "assemblies_defined", "runs_complete", "runs_incomplete", "runs_failed", "records_validated_total",
                                       "validation_errors", "validation_issues")}, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
