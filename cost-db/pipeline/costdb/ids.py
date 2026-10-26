"""Stable identifiers and the canonical material equivalence key (spec_key)."""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping


def _norm_part(p: object) -> str:
    return re.sub(r"\s+", " ", str(p).strip().lower())


def make_id(prefix: str, *parts: object, length: int = 12) -> str:
    """Deterministic id: PREFIX-<first `length` hex of sha1 over normalised parts>.

    The same natural key always yields the same id, so re-importing never duplicates records."""
    digest = hashlib.sha1("|".join(_norm_part(p) for p in parts).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:length]}"


_NUM_RE = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
_WS = " \t\n\r\f\v"
_WS_RE = re.compile(r"[ \t\n\r\f\v]+")
_BAD_RE = re.compile(r"[^\x20-\x7E\x09-\x0D]")
_UPPER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def norm_attr_value(v: object) -> str:
    """Normalise an attribute value for comparison. MUST stay identical to costdb.norm_attr() in schema/001_schema.sql.

    Plain decimal numbers lose trailing zeros ('0.50' == '0.5'; padded ' 5.50 ' too). Everything else is trimmed, has its
    whitespace collapsed (only space, tab, LF, CR, FF, VT count) and is lower-cased (ASCII letters only, so no locale can differ).
    Only plain decimals are numbers: 'NaN', '1_0', '1e3' are ordinary strings. Attribute text must be plain ASCII (write 1/2 in,
    not a vulgar-fraction character): anything else is refused rather than normalised differently in two places."""
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        s = format(Decimal(str(v)), "f")
    elif _BAD_RE.search(s):
        raise SpecError(f"attribute value {s!r} contains non-ASCII or control characters")
    t = s.strip(_WS)
    if _NUM_RE.match(t):
        d = Decimal(t)
        if d == 0:
            return "0"
        return format(d.normalize(), "f")
    return _WS_RE.sub(" ", t).translate(_UPPER)


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
