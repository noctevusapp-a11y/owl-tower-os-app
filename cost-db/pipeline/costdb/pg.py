"""PostgreSQL import helpers (psql \\copy). Dependency-safe load order for the CSV files."""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from .schema_meta import parse_schema

LOAD_ORDER = [
    "units", "regions", "categories", "trades", "equipment_types", "sources",
    "products", "product_consumption", "price_observations",
    "calculation_runs", "calculation_run_lines",
    "labor_rates", "burden_rates", "equipment_rates",
    "crews", "crew_members", "productivity_observations",
    "work_items", "work_item_components", "assemblies", "assembly_components",
    "bid_benchmarks", "indices", "index_values", "adjustment_factors", "assumptions",
    "capture_targets", "validation_issues", "review_events", "change_log",
]


def check_order_complete() -> None:
    tables = set(parse_schema())
    missing = tables - set(LOAD_ORDER)
    extra = set(LOAD_ORDER) - tables
    if missing or extra:
        raise RuntimeError(f"LOAD_ORDER mismatch: missing={sorted(missing)} extra={sorted(extra)}")


def copy_script(csv_dir: Path, schema: str = "costdb") -> str:
    """psql script: one transaction, \\copy every CSV that exists (generated columns excluded)."""
    meta = parse_schema()
    lines = ["BEGIN;", f"SET LOCAL search_path = {schema}, public;"]
    for t in LOAD_ORDER:
        p = csv_dir / f"{t}.csv"
        if not p.exists():
            continue
        with open(p, newline="", encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        gen = {c.name for c in meta[t] if c.generated}
        bad = [h for h in header if h in gen]
        if bad:
            raise RuntimeError(f"{p.name}: generated columns present in CSV: {bad}")
        cols = ",".join(header)
        lines.append(f"\\copy {t} ({cols}) FROM '{p}' WITH (FORMAT csv, HEADER true)")
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def run_psql(args: list[str], script: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-v", "ON_ERROR_STOP=1", "-q", *args], input=script, text=True, capture_output=True, env=env)

