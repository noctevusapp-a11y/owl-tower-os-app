#!/usr/bin/env python3
"""Load schema + all CSVs into a PostgreSQL database and run integrity checks.

Uses the standard libpq environment (PGHOST, PGPORT, PGUSER, PGDATABASE). With --recreate the target database
is dropped and recreated (use only on a scratch server).

  PGHOST=/var/tmp/owl_pgsock PGPORT=5544 PGUSER=postgres python3 -I pipeline/scripts/pg_import_check.py --recreate costdb_t
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb import pg  # noqa: E402
from costdb.schema_meta import parse_schema  # noqa: E402


def main() -> int:
    pg.check_order_complete()
    args = sys.argv[1:]
    recreate = "--recreate" in args
    names = [a for a in args if not a.startswith("--")]
    db = names[0] if names else os.environ.get("PGDATABASE", "costdb_test")
    if recreate:
        r = pg.run_psql(["-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {db}"])
        r2 = pg.run_psql(["-d", "postgres", "-c", f"CREATE DATABASE {db}"])
        if r2.returncode:
            print(r2.stderr); return 2
    for f in ("001_schema.sql", "002_seed_reference.sql"):
        p = ROOT / "schema" / f
        if p.exists():
            r = pg.run_psql(["-d", db, "-f", str(p)])
            if r.returncode:
                print(f"FAILED {f}:\n{r.stderr}"); return 2
    script = pg.copy_script(ROOT / "data" / "csv")
    r = pg.run_psql(["-d", db], script)
    if r.returncode:
        print("IMPORT FAILED:\n", r.stderr); return 3
    # row counts
    meta = parse_schema()
    q = " UNION ALL ".join(f"SELECT '{t}', count(*) FROM costdb.{t}" for t in pg.LOAD_ORDER)
    r = pg.run_psql(["-d", db, "-At", "-F", " ", "-c", q])
    counts = {l.split()[0]: int(l.split()[1]) for l in r.stdout.strip().splitlines()}
    print("imported rows:", {t: n for t, n in counts.items() if n})
    empty = [t for t in meta if counts.get(t, 0) == 0]
    print("empty tables (no real data yet):", ", ".join(empty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
