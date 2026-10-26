"""Exact unit conversion using the rational factors stored in the units table."""
from __future__ import annotations

from decimal import Context, Decimal
from fractions import Fraction
from typing import Iterable, Mapping

_CTX = Context(prec=40)       # local context: importing this module never changes global Decimal behaviour


class UnitError(ValueError):
    pass


class Units:
    def __init__(self, rows: Iterable[Mapping[str, object]]):
        self._u = {r["unit_id"]: r for r in rows}

    def __contains__(self, unit_id: str) -> bool:
        return unit_id in self._u

    def get(self, unit_id: str) -> Mapping[str, object]:
        try:
            return self._u[unit_id]
        except KeyError as e:
            raise UnitError(f"unknown unit '{unit_id}'") from e

    def dimension(self, unit_id: str) -> str:
        return self.get(unit_id)["dimension"]  # type: ignore[return-value]

    def factor(self, from_unit: str, to_unit: str) -> Fraction:
        """Exact multiplier m such that qty_to = qty_from * m."""
        f, t = self.get(from_unit), self.get(to_unit)
        if from_unit == to_unit:
            return Fraction(1)
        if f["dimension"] != t["dimension"] or f["base_unit_id"] != t["base_unit_id"]:
            raise UnitError(f"cannot convert {from_unit} ({f['dimension']}) to {to_unit} ({t['dimension']})")
        for u, r in ((from_unit, f), (to_unit, t)):
            if not r["is_fixed_conversion"] or r["to_base_num"] is None:
                raise UnitError(f"{u} has no fixed conversion (e.g. DAY depends on crew shift length)")
        return (Fraction(int(f["to_base_num"]), int(f["to_base_den"]))
                / Fraction(int(t["to_base_num"]), int(t["to_base_den"])))

    def convert(self, qty: Decimal, from_unit: str, to_unit: str) -> Decimal:
        m = self.factor(from_unit, to_unit)
        return _CTX.divide(_CTX.multiply(Decimal(qty), Decimal(m.numerator)), Decimal(m.denominator))

    def compatible(self, a: str, b: str) -> bool:
        try:
            self.factor(a, b)
            return True
        except UnitError:
            return False
