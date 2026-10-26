#!/usr/bin/env python3
"""Full rebuild of derived artifacts from the CSV tables.

  1. load data/csv + data/run_policy.json
  2. validate the DATA (production gate) - error-level issues stop the build BEFORE anything is computed or written
  3. promote: observed records whose source was really fetched (and that carry their evidence) become 'validated'
  4. strict calculations for all work items + assemblies (parameters from data/run_policy.json, each with its stated basis)
  5. validate again, now including the stored runs (inputs exist, totals reproduce by recomputation) - errors stop the build
  6. write all CSV tables, data/json/costdb.json, reports (coverage, backlog, validation, status)

Run:  python3 -I pipeline/scripts/build.py [--skip-tests]
Prerequisite generators (run once, or when their inputs change):
  gen_reference.py, ingest_agent_returns.py, gen_pilot_definitions.py, build_docs.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb import BUILD_TS, CALC_VERSION  # noqa: E402
from costdb.calc import Engine, RunParams  # noqa: E402
from costdb.report import backlog, counts, coverage_matrix, validation_report  # noqa: E402
from costdb.store import Database  # noqa: E402
from costdb.validate import promote_validated, validate  # noqa: E402

AS_OF = date.fromisoformat(BUILD_TS[:10])
# Result-affecting parameters that must carry a stated basis in data/run_policy.json (no universal default without a reason).
NEEDS_BASIS = ("annual_paid_hours", "labor_statistic", "burden_base", "price_policy", "labor_basis", "min_review")


def git_ref(root: Path = ROOT) -> str | None:
    """Short commit id of the code that produced the build; '+uncommitted' when pipeline/ or schema/ differ from it."""
    try:
        sha = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        if not sha:
            return None
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "pipeline", "schema"], capture_output=True, text=True).stdout.strip()
        return sha + ("+uncommitted" if dirty else "")
    except OSError:
        return None


def load_policy(root: Path) -> tuple[RunParams, dict]:
    pol = json.loads((root / "data" / "run_policy.json").read_text(encoding="utf-8"))
    raw = dict(pol["params"])
    missing = [k for k in NEEDS_BASIS if k in raw and not str(pol.get("basis", {}).get(k, "")).strip()]
    if missing:
        raise SystemExit(f"data/run_policy.json: no stated basis for {missing}")
    for k in ("annual_paid_hours", "quantity"):
        if raw.get(k) is not None:
            raw[k] = Decimal(str(raw[k]))
    if raw.get("known_at"):
        raw["known_at"] = date.fromisoformat(raw["known_at"])
    for k in ("channels", "conditions"):
        if k in raw:
            raw[k] = tuple(raw[k])
    return RunParams(region_id=pol["region_id"], as_of=AS_OF, run_at=BUILD_TS, **raw), pol


def build(root: Path = ROOT, skip_tests: bool = False) -> int:
    db = Database.load_csv_dir(root / "data" / "csv")
    db.tables["calculation_runs"] = []
    db.tables["calculation_run_lines"] = []
    db.tables["validation_issues"] = []
    params, policy = load_policy(root)

    # ---- 2. validate the data before anything is derived from it
    issues = validate(db, today=AS_OF, production=True)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        print(f"BUILD STOPPED: {len(errors)} error-level validation issue(s) in the data; nothing was computed or written:")
        for i in errors[:25]:
            print(f"  {i.rule_code} {i.record_table} {i.record_id}: {i.message}")
        return 1

    # ---- 3. promotion (before the runs, so the runs see the new statuses)
    promoted = promote_validated(db, issues, "costdb.build", BUILD_TS)

    # ---- 4. strict calculations for the whole pilot: expected to be INCOMPLETE until data exists; the runs document exactly why
    eng = Engine(db, code_ref=git_ref(root))
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

    # ---- 5. validate again, including the stored runs (recomputation must reproduce every complete run)
    issues = validate(db, today=AS_OF, production=True, engine=eng)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        print(f"BUILD STOPPED: {len(errors)} error-level validation issue(s) after the calculations; nothing was written:")
        for i in errors[:25]:
            print(f"  {i.rule_code} {i.record_table} {i.record_id}: {i.message}")
        return 1
    for i in issues:
        row = i.as_row("costdb.build")
        row["detected_at"] = BUILD_TS
        db.add("validation_issues", row)

    # ---- 6. write data and reports
    db.write_csv_dir(root / "data" / "csv")
    db.write_json(root / "data" / "json" / "costdb.json")
    (root / "data" / "json" / "source_register.json").write_text(
        json.dumps(db.to_json_obj()["sources"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "data" / "source_register.csv").write_text((root / "data" / "csv" / "sources.csv").read_text(encoding="utf-8"), encoding="utf-8")
    if skip_tests:
        test_summary = "_(test run skipped in this build)_"
    else:
        r = subprocess.run([sys.executable, "-B", str(root / "tests" / "run_tests.py")], capture_output=True, text=True, cwd=root)
        tail = (r.stderr or r.stdout).strip().splitlines()
        ran = next((l for l in tail if l.startswith("Ran ")), "Ran ? tests")
        ok = "OK" in tail[-1] if tail else False
        skipped = next((l for l in tail if "skipped" in l), "")
        test_summary = (f"`python3 tests/run_tests.py` → **{ran}, {'ALL PASSED' if ok else 'FAILURES — see output'}** {skipped}  \n"
                        f"(The PostgreSQL tests start their own throw-away cluster; `PGHOST`/`PGPORT`/`PGUSER` select an existing scratch server; "
                        f"`COSTDB_SKIP_PG=1` skips them knowingly.)")
        if not ok:
            print(r.stderr[-3000:])
    gaps = {}
    for p in sorted((root / "data" / "raw_agent_returns").glob("agent_A*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        gaps[d["agent"]] = d["gaps"]
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "coverage_matrix.md").write_text(coverage_matrix(db), encoding="utf-8")
    (root / "docs" / "data_gaps_backlog.md").write_text(backlog(db, gaps), encoding="utf-8")
    (root / "docs" / "validation_report.md").write_text(validation_report(db, issues, test_summary, BUILD_TS), encoding="utf-8")
    c = counts(db)
    c.update({"build_timestamp": BUILD_TS, "calc_version": CALC_VERSION, "validation_errors": len(errors), "validation_issues": len(issues),
              "promoted_to_validated": promoted, "region": params.region_id, "as_of": AS_OF.isoformat(), "git_ref": git_ref(root),
              "run_policy": {k: policy["params"][k] for k in sorted(policy["params"])}})
    (root / "data" / "json" / "pilot_status.json").write_text(json.dumps(c, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: c[k] for k in ("unique_products", "price_observations", "material_spec_lines_targeted", "work_items_defined",
                                       "assemblies_defined", "runs_complete", "runs_incomplete", "runs_failed", "records_validated_total",
                                       "validation_errors", "validation_issues")}, indent=1))
    return 0


def main() -> int:
    return build(ROOT, skip_tests="--skip-tests" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())
