"""Read table/column metadata from schema/001_schema.sql (the single source of truth)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = ROOT / "schema" / "001_schema.sql"

_SKIP = ("CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN", "CHECK")


@dataclass(frozen=True)
class Column:
    table: str
    name: str
    sql_type: str
    generated: bool
    references: tuple[str, str] | None = None

    @property
    def kind(self) -> str:
        t = self.sql_type.lower()
        if t.endswith("[]"):
            return "array"
        if t.startswith("numeric"):
            return "decimal"
        if t in ("bigint", "integer", "int"):
            return "int"
        if t == "boolean":
            return "bool"
        if t == "jsonb":
            return "json"
        if t == "date":
            return "date"
        return "text"  # text, id_t, origin_t, char(n), timestamptz (kept as ISO text) ...


def parse_schema(path: Path = SCHEMA_SQL) -> dict[str, list[Column]]:
    sql = path.read_text(encoding="utf-8")
    tables: dict[str, list[Column]] = {}
    for m in re.finditer(r"CREATE TABLE (\w+) \(\n(.*?)\n\);", sql, re.S):
        tname, body = m.group(1), m.group(2)
        lines = body.split("\n")
        cols: list[Column] = []
        for i, line in enumerate(lines):
            if not line.startswith("  ") or line.startswith("   "):
                continue
            stripped = line.strip()
            if stripped.startswith("--") or stripped.split()[0] in _SKIP:
                continue
            tok = stripped.split()
            name, sql_type = tok[0], tok[1].rstrip(",")
            if not re.fullmatch(r"[a-z_][a-z0-9_]*", name):
                continue
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            generated = ("GENERATED ALWAYS" in line) or (nxt.startswith("    ") and "GENERATED ALWAYS" in nxt)
            if sql_type.startswith("numeric") and "(" in sql_type and ")" not in sql_type:
                sql_type = "numeric"
            ref = re.search(r"REFERENCES (\w+)\((\w+)\)", line)
            cols.append(Column(tname, name, sql_type, bool(generated), (ref.group(1), ref.group(2)) if ref else None))
        tables[tname] = cols
    return tables


def table_names() -> list[str]:
    return list(parse_schema().keys())
