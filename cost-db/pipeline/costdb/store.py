"""CSV <-> typed in-memory tables, JSON export. CSV is the canonical interchange format.

Conventions (identical for Python and PostgreSQL \\copy ... CSV HEADER):
  * header row required; empty field = NULL
  * booleans: true/false; dates: YYYY-MM-DD; timestamps: ISO-8601 text
  * jsonb columns hold JSON text; text[] columns hold PostgreSQL array literals, e.g. {a,b}
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from . import BUILD_TS
from .schema_meta import Column, parse_schema

ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = ROOT / "data" / "csv"


def parse_pg_array(s: str) -> list[str]:
    s = s.strip()
    if not (s.startswith("{") and s.endswith("}")):
        raise ValueError(f"not a PostgreSQL array literal: {s!r}")
    inner = s[1:-1]
    if inner == "":
        return []
    out, cur, in_q, esc = [], [], False, False
    for ch in inner:
        if esc:
            cur.append(ch); esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            in_q = not in_q
        elif ch == "," and not in_q:
            out.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def format_pg_array(items: Iterable[str]) -> str:
    def q(x: str) -> str:
        if re.search(r'[\s,{}"\\]', x) or x == "":
            return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return x
    return "{" + ",".join(q(str(i)) for i in items) + "}"


def parse_value(col: Column, raw: str | None) -> Any:
    if raw is None or raw == "":
        return None
    k = col.kind
    if k == "decimal":
        return Decimal(raw)
    if k == "int":
        return int(raw)
    if k == "bool":
        if raw.lower() not in ("true", "false"):
            raise ValueError(f"{col.table}.{col.name}: bad boolean {raw!r}")
        return raw.lower() == "true"
    if k == "json":
        return json.loads(raw)
    if k == "array":
        return parse_pg_array(raw)
    if k == "date":
        return date.fromisoformat(raw)
    return raw


def format_value(col: Column, v: Any) -> str:
    if v is None:
        return BUILD_TS if col.name == "created_at" else ""
    k = col.kind
    if k == "bool":
        return "true" if v else "false"
    if k == "json":
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    if k == "array":
        return format_pg_array(v)
    if k == "decimal":
        return format(Decimal(v), "f")
    if k == "date":
        return v.isoformat() if hasattr(v, "isoformat") else str(v)
    return str(v)


@dataclass
class Database:
    """All tables as lists of typed dict rows."""
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    meta: dict[str, list[Column]] = field(default_factory=parse_schema)

    def __post_init__(self):
        for t in self.meta:
            self.tables.setdefault(t, [])

    def __getitem__(self, name: str) -> list[dict[str, Any]]:
        return self.tables[name]

    def index(self, table: str, *keys: str) -> dict:
        out = {}
        for r in self.tables[table]:
            k = tuple(r[x] for x in keys) if len(keys) > 1 else r[keys[0]]
            out[k] = r
        return out

    def add(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        cols = {c.name for c in self.meta[table]}
        unknown = set(row) - cols
        if unknown:
            raise KeyError(f"{table}: unknown column(s) {sorted(unknown)}")
        full = {c.name: row.get(c.name) for c in self.meta[table]}
        self.tables[table].append(full)
        return full

    # ------------------------------------------------------------- csv
    @classmethod
    def load_csv_dir(cls, directory: Path = CSV_DIR) -> "Database":
        db = cls()
        for table, cols in db.meta.items():
            p = directory / f"{table}.csv"
            if not p.exists():
                continue
            with open(p, newline="", encoding="utf-8") as fh:
                rd = csv.DictReader(fh)
                header = rd.fieldnames or []
                names = {c.name for c in cols}
                bad = [h for h in header if h not in names]
                if bad:
                    raise ValueError(f"{p.name}: unknown column(s) {bad}")
                by_name = {c.name: c for c in cols}
                for raw in rd:
                    row = {c.name: None for c in cols}
                    for h in header:
                        row[h] = parse_value(by_name[h], raw[h])
                    db.tables[table].append(row)
        return db

    def write_csv_dir(self, directory: Path = CSV_DIR, include_generated: bool = False) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        for table, cols in self.meta.items():
            use = [c for c in cols if include_generated or not c.generated]
            with open(directory / f"{table}.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, lineterminator="\n")
                w.writerow([c.name for c in use])
                for r in self.tables.get(table, []):
                    w.writerow([format_value(c, r.get(c.name)) for c in use])

    # ------------------------------------------------------------ json
    def to_json_obj(self) -> dict[str, Any]:
        def enc(v):
            if isinstance(v, Decimal):
                return format(v, "f")
            if isinstance(v, date):
                return v.isoformat()
            return v
        return {t: [{k: enc(v) for k, v in r.items()} for r in rows] for t, rows in self.tables.items()}

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        obj = {
            "_meta": {"format": "owl-tower-costdb/1", "tables": {t: len(r) for t, r in self.tables.items()},
                      "note": "decimals are strings to avoid float rounding; see docs/data_dictionary.md"},
            **self.to_json_obj(),
        }
        path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
