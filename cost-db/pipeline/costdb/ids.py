"""Stable identifiers and the canonical material equivalence key (spec_key)."""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping


def _norm_part(p: object) -> str:
    return re.sub(r"\s+", " ", str(p).strip().lower())


def make_id(prefix: str, *parts: object, length: int = 10) -> str:
    """Deterministic id: PREFIX-<first `length` hex of sha1 over normalised parts>.

    The same natural key always yields the same id, so re-importing never duplicates records."""
    digest = hashlib.sha1("|".join(_norm_part(p) for p in parts).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:length]}"


def norm_attr_value(v: object) -> str:
    """Normalise an attribute value for comparison: numbers lose trailing zeros ('0.50' == '0.5')."""
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v).strip().lower()
    s = re.sub(r"\s+", " ", s)
    try:
        d = Decimal(s)
        n = d.normalize()
        # avoid scientific notation
        return format(n, "f") if n == n.to_integral() or abs(n.as_tuple().exponent) < 12 else str(n)
    except (InvalidOperation, ValueError):
        return s


class SpecError(ValueError):
    pass


def spec_key(category_id: str, attrs: Mapping[str, object], required: Iterable[str]) -> str:
    """Canonical equivalence key built ONLY from the category's required attributes.

    Two products share a spec_key iff every required attribute matches after normalisation.
    Missing/blank required attributes raise SpecError: we never guess an equivalence."""
    parts = []
    missing = []
    for name in sorted(required):
        val = attrs.get(name)
        if val is None or str(val).strip() == "" or str(val).strip().lower() in {"unspecified", "unknown", "n/a", "tbd"}:
            missing.append(name)
            continue
        parts.append(f"{name}={norm_attr_value(val)}")
    if missing:
        raise SpecError(f"{category_id}: required attribute(s) missing: {', '.join(missing)}")
    return category_id + "|" + "|".join(parts)
