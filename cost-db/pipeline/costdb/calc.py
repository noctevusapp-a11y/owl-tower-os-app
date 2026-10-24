"""Calculation engine: unit costs, assemblies, loaded labor rates, markup/margin.

Principles (docs/methodology.md):
  * A result is only produced when EVERY required input resolves to a usable record.
    Otherwise the run is status='incomplete' with an explicit missing_inputs list and NO total.
  * ONE usability test (`Engine._why_not`) is applied to every record the engine reads - observations, products,
    sources, crews, indices, index values, rates, burdens, productivity, consumption, factors. A flagged/rejected
    record, a record of a restricted source (`enums.NO_DATA_USE`), a synthetic fixture (unless allowed), an
    origin='assumed' record in strict mode, or a record below the requested review floor is never used.
  * strict mode reads no assumption at all. with_assumptions mode may use APPROVED, unexpired, four-eyes assumptions
    of the right type; the run is flagged. Failed = a logical conflict (double counting, prevailing wage on a private
    project, crew/shift mismatch ...), not just missing data.
  * Retail prices are an explicit opt-in (`accept_retail_proxy`) and are recorded on the run (`price_basis`).
  * Every cost line stores quantity, unit, unit cost, formula text and the exact input record ids.
  * run_id = hash(target, parameters, calc version, EVERY line with its inputs, every missing input): the same data
    and parameters give the same id; a different input record or a different gap gives a different one.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from typing import Any, Optional

from . import CALC_VERSION
from .enums import (ALL_CHANNELS, BASE_PAYROLL_TYPES, BURDEN_BASES, DEFAULT_CHANNELS, EQUIPMENT_BASES,
                    FLAGGED_ONLY_BURDENS, LABOR_BASES, LABOR_STATISTICS, LIST_CHANNELS, MANUAL_ONLY, MIN_REVIEWS,
                    MODES, NO_DATA_USE, PRICE_POLICIES, PROJECT_TYPES, RETAIL_CHANNELS, STATE_PAYROLL_EXTRA,
                    WAGE_CLASSES, WAGE_REGIMES)
from .ids import make_id
from .store import Database
from .units import UnitError, Units

D = Decimal
Q10 = D("0.0000000001")
Q6 = D("0.000001")
CONSUMPTION_SELECTOR_KEYS = ("film_thickness", "substrate_condition", "application_method", "conditions")
OPERATOR_TRADES = ("TR-OPR",)
LABOR_BASIS_TYPES = {"stat_loaded": ("stat_wage",), "company_actual": ("company_actual",)}


def _d(x: Any) -> Decimal:
    return x if isinstance(x, Decimal) else D(str(x))


def q10(x: Decimal) -> Decimal:
    return x.quantize(Q10, rounding=ROUND_HALF_UP)


def q6(x: Decimal) -> Decimal:
    return x.quantize(Q6, rounding=ROUND_HALF_UP)


def _frac(m: Fraction) -> Decimal:
    return D(m.numerator) / D(m.denominator)


def median(vals: list[Decimal]) -> Decimal:
    s = sorted(vals)
    n = len(s)
    if n == 0:
        raise ValueError("median of empty list")
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def _ts(x: Any) -> Optional[datetime]:
    """Timestamp text/datetime -> aware UTC datetime (a naive value is read as UTC)."""
    if x is None or x == "":
        return None
    if isinstance(x, datetime):
        dt = x
    else:
        dt = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm(s: Any) -> str:
    return " ".join(str(s).strip().lower().split())


def _inp(table: str, rid: str, fld: str, value: Any, unit: Optional[str] = None, origin: str = "observed", **extra) -> dict:
    d = {"table": table, "id": rid, "field": fld, "value": "" if value is None else str(value), "unit": unit, "origin": origin}
    d.update(extra)
    return d


# ---------------------------------------------------------------------------------------------------- parameters
@dataclass
class RunParams:
    region_id: str
    as_of: date
    mode: str = "strict"                        # strict | with_assumptions
    min_review: str = "validated"               # validated | unreviewed
    price_policy: str = "median_of_latest_per_product"
    channels: tuple[str, ...] = DEFAULT_CHANNELS
    accept_retail_proxy: bool = False            # retail channels are opt-in; recorded on the run as price_basis
    max_price_age_days: Optional[int] = None     # no universal default: older prices are excluded only when this is set
    time_index_id: Optional[str] = None          # index series used to bring a price of another period to the as_of period
    use_region_factors: bool = False             # allow prices of unrelated regions + an explicit region factor
    allow_ancestor_region_prices: bool = False   # e.g. a California price for a county run (flagged, ranked after exact)
    allow_subregion_prices: bool = False         # e.g. a city price for a county run (flagged, ranked after exact)
    labor_basis: str = "stat_loaded"             # stat_loaded | prevailing_loaded | company_actual
    labor_statistic: str = "mean"
    project_type: str = "private"                # private | public_works
    wage_regime: str = "state"                   # prevailing basis only: state (DIR) | federal (SAM)
    wage_class: str = "n/a"                      # prevailing basis: building | residential | heavy | highway
    classification: Optional[str] = None         # exact classification_raw to pick when a source lists several
    wc_class_code: Optional[str] = None          # workers' comp class code to pick when several exist
    burden_base: str = "base_wage"               # base_wage | wage_plus_fringe
    annual_paid_hours: Optional[Decimal] = None  # needed when a burden has an annual wage cap
    max_rate_age_days: Optional[int] = None      # stale-rate flag only when set
    equipment_basis: str = "hourly"              # hourly | rental_day
    conditions: tuple[str, ...] = ()
    quantity: Optional[Decimal] = None           # quantity of the TARGET (work-item or assembly output unit)
    include_optional: bool = False               # components flagged is_optional are priced only when True
    known_at: Optional[date] = None              # rows retrieved after this date are unknown to the run (default: as_of)
    allow_synthetic: bool = False                # test fixtures only
    run_at: Optional[str] = None                 # fix for reproducible example output

    def __post_init__(self):
        def need(ok: bool, msg: str):
            if not ok:
                raise ValueError(msg)

        need(isinstance(self.region_id, str) and bool(self.region_id), "region_id is required")
        need(isinstance(self.as_of, date) and not isinstance(self.as_of, datetime), "as_of must be a date")
        need(self.mode in MODES, f"mode must be one of {MODES}, got {self.mode!r}")
        need(self.min_review in MIN_REVIEWS, f"min_review must be one of {MIN_REVIEWS}, got {self.min_review!r}")
        need(self.price_policy in PRICE_POLICIES, f"price_policy must be one of {PRICE_POLICIES}, got {self.price_policy!r}")
        need(self.labor_basis in LABOR_BASES, f"labor_basis must be one of {LABOR_BASES}, got {self.labor_basis!r}")
        need(self.labor_statistic in LABOR_STATISTICS, f"labor_statistic must be one of {LABOR_STATISTICS}")
        need(self.project_type in PROJECT_TYPES, f"project_type must be one of {PROJECT_TYPES}")
        need(self.wage_regime in WAGE_REGIMES, f"wage_regime must be one of {WAGE_REGIMES}")
        need(self.wage_class in WAGE_CLASSES, f"wage_class must be one of {WAGE_CLASSES}")
        need(self.burden_base in BURDEN_BASES, f"burden_base must be one of {BURDEN_BASES}")
        need(self.equipment_basis in EQUIPMENT_BASES, f"equipment_basis must be one of {EQUIPMENT_BASES}")
        self.channels = tuple(self.channels)
        bad = [c for c in self.channels if c not in ALL_CHANNELS]
        need(not bad, f"unknown price channel(s) {bad}")
        need(not (set(self.channels) & set(RETAIL_CHANNELS)) or self.accept_retail_proxy,
             "retail channels need accept_retail_proxy=True (retail price is not contractor cost)")
        self.conditions = tuple(sorted(set(self.conditions)))
        for name in ("annual_paid_hours", "quantity"):
            v = getattr(self, name)
            if v is not None:
                v = _d(v)
                need(v > 0, f"{name} must be > 0")
                setattr(self, name, v)
        for name in ("max_price_age_days", "max_rate_age_days"):
            v = getattr(self, name)
            need(v is None or (isinstance(v, int) and not isinstance(v, bool) and v >= 0), f"{name} must be a non-negative integer or None")
        need(self.known_at is None or isinstance(self.known_at, date), "known_at must be a date or None")
        need(self.classification is None or bool(str(self.classification).strip()), "classification must be non-empty or None")

    @property
    def known(self) -> date:
        return self.known_at or self.as_of

    @property
    def effective_channels(self) -> tuple[str, ...]:
        extra = RETAIL_CHANNELS if self.accept_retail_proxy else ()
        return tuple(sorted(set(self.channels) | set(extra)))

    def canonical(self) -> str:
        def enc(o):
            if isinstance(o, Decimal):
                return str(o)
            if isinstance(o, (date, datetime)):
                return o.isoformat()
            if isinstance(o, tuple):
                return list(o)
            raise TypeError(type(o))
        d = asdict(self)
        d.pop("run_at")
        return json.dumps(d, sort_keys=True, default=enc)

    @classmethod
    def from_canonical(cls, d: dict, run_at: Optional[str] = None) -> "RunParams":
        """Exact inverse of canonical(): rebuild the parameters stored on a calculation run."""
        d = dict(d)
        d["as_of"] = date.fromisoformat(d["as_of"])
        if d.get("known_at"):
            d["known_at"] = date.fromisoformat(d["known_at"])
        for k in ("annual_paid_hours", "quantity"):
            if d.get(k) is not None:
                d[k] = D(d[k])
        d["channels"] = tuple(d["channels"])
        d["conditions"] = tuple(d["conditions"])
        return cls(run_at=run_at, **d)


class Missing(Exception):
    """Raised while resolving one input when it cannot be resolved honestly."""

    def __init__(self, code: str, needed: str, reason: str, hint: str = "", blocking: bool = False):
        super().__init__(f"{code}: {needed} - {reason}")
        self.info = {"code": code, "needed": needed, "reason": reason, "how_to_fill": hint}
        self.blocking = blocking


class MultiMissing(Exception):
    """Several independent inputs of ONE component are unresolved; all are reported, none is hidden behind another."""

    def __init__(self, items: list):
        super().__init__("; ".join(str(i) for i in items))
        self.items = items


class Excluded(Exception):
    """One candidate (a product or an observation) is skipped for a stated reason; this is not an error of the run."""


@dataclass
class RunResult:
    run: dict
    lines: list[dict]
    children: list["RunResult"] = field(default_factory=list)
    derived_rows: dict[str, list[dict]] = field(default_factory=dict)

    def flatten(self) -> list["RunResult"]:
        out = [self]
        for c in self.children:
            out.extend(c.flatten())
        return out

    @property
    def status(self) -> str:
        return self.run["status"]

    @property
    def total(self) -> Optional[Decimal]:
        """Direct cost (never a price)."""
        return self.run.get("direct_cost_total")

    @property
    def price(self) -> Optional[Decimal]:
        return self.run.get("price_total")


def _missing_info(m: Missing, ref: str) -> dict:
    info = dict(m.info)
    info["component_ref"] = ref
    info["blocking"] = m.blocking
    return info


def _price_basis_of(channel: Optional[str]) -> str:
    if channel in RETAIL_CHANNELS:
        return "retail_proxy"
    if channel in ("pro_account_quote", "distributor_quote", "supplier_quote"):
        return "contractor_quote"
    if channel in LIST_CHANNELS or channel == "manufacturer_msrp":
        return "public_list"
    return "mixed"


def _combine_basis(bases: set) -> str:
    bases = set(bases)
    if not bases:
        return "none"
    return next(iter(bases)) if len(bases) == 1 else "mixed"


class Engine:
    def __init__(self, db: Database, calc_version: str = CALC_VERSION, code_ref: Optional[str] = None):
        self.db = db
        self.calc_version = calc_version
        self.code_ref = code_ref
        self._refresh()

    # ------------------------------------------------------------------------------- indexes (rebuilt per call)
    def _refresh(self) -> None:
        db = self.db

        def group(table: str, key) -> dict:
            out: dict = {}
            for r in db[table]:
                out.setdefault(key(r), []).append(r)
            return out

        self.units = Units(db["units"])
        self._chains: dict[str, list[str]] = {}
        self._regions = {r["region_id"]: r for r in db["regions"]}
        self._sources = {r["source_id"]: r for r in db["sources"]}
        self._products = {r["product_id"]: r for r in db["products"]}
        self._products_by_key = group("products", lambda r: r["spec_key"])
        self._obs = group("price_observations", lambda r: r["product_id"])
        self._consumption = group("product_consumption", lambda r: r["product_id"])
        self._crews = {r["crew_id"]: r for r in db["crews"]}
        self._members = group("crew_members", lambda r: r["crew_id"])
        self._equip_types = {r["equipment_type_code"]: r for r in db["equipment_types"]}
        self._prod_obs = {r["productivity_id"]: r for r in db["productivity_observations"]}
        self._labor = group("labor_rates", lambda r: r["trade_code"])
        self._burden = group("burden_rates", lambda r: r["burden_type"])
        self._equip_rates = group("equipment_rates", lambda r: r["equipment_type_code"])
        self._indices = {r["index_id"]: r for r in db["indices"]}
        self._index_values = group("index_values", lambda r: r["index_id"])
        self._factors = list(db["adjustment_factors"])
        self._assumptions = group("assumptions", lambda r: r["applies_to_ref"])
        self._wis = {(r["work_item_id"], r["version"]): r for r in db["work_items"]}
        self._wi_comps = group("work_item_components", lambda r: (r["work_item_id"], r["work_item_version"]))
        self._asms = {(r["assembly_id"], r["version"]): r for r in db["assemblies"]}
        self._asm_comps = group("assembly_components", lambda r: (r["assembly_id"], r["assembly_version"]))

    # ------------------------------------------------------------------------------------------------ regions
    def _chain(self, region_id: str) -> list[str]:
        if region_id in self._chains:
            return self._chains[region_id]
        chain, seen = [], set()
        cur: Optional[str] = region_id
        while cur and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            row = self._regions.get(cur)
            cur = row["parent_region_id"] if row else None
        self._chains[region_id] = chain
        return chain

    def _state_code(self, region_id: str) -> Optional[str]:
        for r in self._chain(region_id):
            row = self._regions.get(r)
            if row and row.get("state_code"):
                return row["state_code"]
        return None

    def _rank_up(self, row_region: Optional[str], target: str) -> Optional[int]:
        """Rate/burden regions: 0 = exact region, n = n-th ancestor of the target. A rate for a SMALLER area is never
        stretched over a larger one, and an unrelated region is never used. None region = nationwide, least specific."""
        if row_region is None:
            return 99
        chain = self._chain(target)
        return chain.index(row_region) if row_region in chain else None

    def _price_region_class(self, row_region: Optional[str], target: str) -> Optional[tuple[int, int]]:
        """(class, n): 0 exact, 1 sub-region (the row's region lies inside the target), 2 ancestor (covers the target)."""
        if row_region is None:
            return None
        if row_region == target:
            return (0, 0)
        tchain = self._chain(target)
        if row_region in tchain:
            return (2, tchain.index(row_region))
        rchain = self._chain(row_region)
        if target in rchain:
            return (1, rchain.index(target))
        return None

    # ----------------------------------------------------------------------------------------------- usability
    def _source_issue(self, sid: str, p: RunParams) -> Optional[str]:
        src = self._sources.get(sid)
        if src is None:
            return f"source {sid} not in sources"
        if src["review_status"] in ("flagged", "rejected"):
            return f"source {sid} is {src['review_status']}"
        if src["reuse_status"] in NO_DATA_USE:
            return f"source {sid} reuse_status={src['reuse_status']}: its values are never calculation inputs"
        if src["verification_method"] == "synthetic_test_fixture" and not p.allow_synthetic:
            return f"source {sid} is a synthetic test fixture"
        return None

    def _why_not(self, row: dict, p: RunParams) -> Optional[str]:
        """The ONE usability test. Returns the reason a record may not be used, or None."""
        st = row.get("review_status")
        if st in ("flagged", "rejected"):
            return f"review_status={st}"
        if p.min_review == "validated" and st != "validated":
            return f"review_status={st} (floor: validated)"
        if row.get("origin") == "missing":
            return "origin=missing"
        if row.get("origin") == "assumed" and p.mode != "with_assumptions":
            return "origin=assumed (strict mode accepts no assumptions)"
        sid = row.get("source_id")
        if sid:
            why = self._source_issue(sid, p)
            if why:
                return why
        return None

    @staticmethod
    def _in_period(row: dict, as_of: date) -> bool:
        if row["effective_from"] > as_of:
            return False
        return row.get("effective_to") is None or row["effective_to"] >= as_of

    @staticmethod
    def _known(row: dict, p: RunParams) -> Optional[str]:
        ts = _ts(row.get("retrieved_at"))
        if ts is not None and ts.date() > p.known:
            return f"retrieved {ts.date().isoformat()}, after known_at {p.known.isoformat()}"
        return None

    # -------------------------------------------------------------------------------------------- assumptions
    def _assumption_issue(self, a: dict, types: tuple, p: RunParams) -> Optional[str]:
        if a["status"] != "approved":
            return f"status={a['status']}"
        if a["assumption_type"] not in types:
            return f"assumption_type {a['assumption_type']} (need {'/'.join(types)})"
        if a.get("review_status") in ("flagged", "rejected"):
            return f"review_status={a['review_status']}"
        if not a.get("expires_on"):
            return "no expiry date"
        if a["expires_on"] < p.as_of:
            return f"expired {a['expires_on'].isoformat()}"
        if not a.get("approved_by") or not a.get("approved_at"):
            return "not approved by a named person"
        if _norm(a["approved_by"]) == _norm(a["proposed_by"]):
            return "approved by its proposer (four eyes required)"
        at = _ts(a["approved_at"])
        if at is not None and at.date() > p.known:
            return "approved after known_at"
        if a.get("value_numeric") is None:
            return "no numeric value"
        v = _d(a["value_numeric"])
        if a["assumption_type"] == "waste":
            if not (D(0) <= v < D(1)):
                return f"waste {v} outside [0,1)"
        elif a["assumption_type"] in ("productivity", "material_price", "labor_rate", "equipment_rate", "factor") and v <= 0:
            return f"value {v} must be > 0"
        elif a["assumption_type"] == "other" and v < 0:
            return f"value {v} must be >= 0"
        return None

    def _assumption(self, ref: str, types: tuple, p: RunParams) -> Optional[dict]:
        """The single approved, unexpired, four-eyes assumption for `ref`; None in strict mode or when there is none."""
        if p.mode != "with_assumptions":
            return None
        ok = [a for a in self._assumptions.get(ref, []) if self._assumption_issue(a, types, p) is None]
        if len(ok) > 1:
            raise Missing("ASSUMPTION_AMBIGUOUS", ref, f"{len(ok)} approved assumptions for the same reference ({', '.join(sorted(a['assumption_id'] for a in ok))})",
                          "supersede all but one", blocking=False)
        return ok[0] if ok else None

    @staticmethod
    def _assumption_input(a: dict, unit: Optional[str] = None) -> dict:
        return _inp("assumptions", a["assumption_id"], "value_numeric", a["value_numeric"], unit or a.get("unit_id"), "assumed",
                    approved_by=a.get("approved_by"), expires_on=a["expires_on"].isoformat() if a.get("expires_on") else None)

    # ---------------------------------------------------------------------------------------------- index lookup
    @staticmethod
    def _period_start(freq: str, d: date) -> date:
        if freq == "monthly":
            return date(d.year, d.month, 1)
        if freq == "quarterly":
            return date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
        if freq == "annual":
            return date(d.year, 1, 1)
        raise Missing("INDEX_FREQUENCY_UNSUPPORTED", f"frequency '{freq}'", "only monthly, quarterly and annual series can adjust a price")

    def _index_series(self, index_id: str, kind: str, p: RunParams) -> dict:
        idx = self._indices.get(index_id)
        if idx is None:
            raise Missing("INDEX_UNKNOWN", f"index {index_id}", "index series not in indices table")
        why = self._why_not(idx, p)
        if why:
            raise Missing("INDEX_UNUSABLE", f"index {index_id}", why)
        k = "material" if kind == "other_direct" else kind
        if idx["applies_to"] not in ("all", k):
            raise Missing("INDEX_APPLIES_TO_MISMATCH", f"index {index_id}", f"series applies to '{idx['applies_to']}', cost component is '{k}'", blocking=True)
        return idx

    def _index_value(self, idx: dict, d: date, p: RunParams, allow_fallback: bool = False) -> tuple[Decimal, dict]:
        start = self._period_start(idx["frequency"], d)
        vals = [v for v in self._index_values.get(idx["index_id"], [])
                if self._why_not(v, p) is None and v["vintage_date"] <= p.known and self._known(v, p) is None]
        exact = [v for v in vals if v["period_start"] == start]
        fallback = False
        if exact:
            v = max(exact, key=lambda r: r["vintage_date"])
        elif allow_fallback and any(r["period_start"] < start for r in vals):
            last = max(r["period_start"] for r in vals if r["period_start"] < start)
            v = max((r for r in vals if r["period_start"] == last), key=lambda r: r["vintage_date"])
            fallback = True
        else:
            raise Missing("INDEX_VALUE_MISSING", f"{idx['index_id']} value for {start.isoformat()}",
                          "no usable index value (review floor, vintage <= known_at)", "capture index series values")
        return _d(v["value"]), {"index_id": idx["index_id"], "period_start": v["period_start"].isoformat(), "requested_period": start.isoformat(),
                                "vintage_date": v["vintage_date"].isoformat(), "value_status": v["value_status"], "fallback_to_latest_published": fallback}

    # ----------------------------------------------------------------------------------------- factor selection
    def _factor_issue(self, f: dict, kind: str, p: RunParams) -> Optional[str]:
        why = self._why_not(f, p)
        if why:
            return why
        if f.get("valid_from") and f["valid_from"] > p.as_of:
            return f"valid from {f['valid_from'].isoformat()}"
        if f.get("valid_to") and f["valid_to"] < p.as_of:
            return f"valid to {f['valid_to'].isoformat()}"
        return None

    def _region_factor(self, from_region: str, to_region: str, kind: str, p: RunParams) -> Optional[dict]:
        ok = [f for f in self._factors if f["factor_type"] == "region" and f["applies_to"] == kind
              and f["from_region_id"] == from_region and f["to_region_id"] == to_region and self._factor_issue(f, kind, p) is None]
        if not ok:
            return None
        return sorted(ok, key=lambda f: (f.get("valid_from") or date.min, f["factor_id"]))[-1]

    def _adjust_factors(self, kind: str, p: RunParams, applied: Optional[set] = None) -> list[dict]:
        """Condition and quantity factors for ONE cost component. A requested condition whose factor for this cost kind
        exists but is unusable is a missing input - never silently dropped."""
        out: list[dict] = []
        for tag in p.conditions:
            mine = [f for f in self._factors if f["factor_type"] in ("conditions", "productivity_condition")
                    and f["condition_desc"] == tag and f["applies_to"] == kind]
            if not mine:
                continue
            ok = [f for f in mine if self._factor_issue(f, kind, p) is None]
            if not ok:
                why = "; ".join(f"{f['factor_id']}: {self._factor_issue(f, kind, p)}" for f in mine[:3])
                raise Missing("CONDITION_FACTOR_UNUSABLE", f"factor for condition '{tag}' ({kind})", why,
                              "validate the factor, correct its validity period, or remove the condition")
            distinct = {(f["factor_type"], f["factor_value"]) for f in ok}
            if len(distinct) > 1:
                raise Missing("CONDITION_FACTOR_AMBIGUOUS", f"factor for condition '{tag}' ({kind})",
                              f"{len(ok)} usable factors with different values: {', '.join(sorted(f['factor_id'] for f in ok))}",
                              "supersede all but one")
            out.append(sorted(ok, key=lambda f: (f.get("valid_from") or date.min, f["factor_id"]))[-1])
            if applied is not None:
                applied.add(tag)
        if p.quantity is not None:
            hits = []
            for f in self._factors:
                if f["factor_type"] != "quantity" or f["applies_to"] != kind or self._factor_issue(f, kind, p) is not None:
                    continue
                lo = _d(f["qty_min"]) if f["qty_min"] is not None else D(0)
                hi = _d(f["qty_max"]) if f["qty_max"] is not None else None
                if lo <= p.quantity and (hi is None or p.quantity < hi):
                    hits.append(f)
            if len(hits) > 1:
                raise Missing("QUANTITY_FACTOR_AMBIGUOUS", f"quantity factor for {p.quantity} ({kind})",
                              f"{len(hits)} overlapping usable ranges: {', '.join(sorted(f['factor_id'] for f in hits))}", "fix the quantity ranges")
            out.extend(hits)
        return out

    @staticmethod
    def _factor_input(f: dict) -> dict:
        return _inp("adjustment_factors", f["factor_id"], "factor_value", f["factor_value"], None, f["origin"], factor_type=f["factor_type"])

    # ------------------------------------------------------------------------------------------- material pricing
    def _best_observation(self, prod: dict, qty_unit: str, need_qty: Optional[Decimal], kind: str, p: RunParams, reasons: list):
        """The best usable observation of ONE product, priced per `qty_unit`; None when there is none."""
        found = []
        idx = None
        if p.time_index_id:
            idx = self._index_series(p.time_index_id, kind, p)        # a wrong/unusable index series fails the component
        for o in self._obs.get(prod["product_id"], []):
            oid = o["observation_id"]
            try:
                why = self._why_not(o, p)
                if why:
                    raise Excluded(why)
                if o["observed_at"] > p.as_of:
                    raise Excluded(f"observed {o['observed_at'].isoformat()} after as_of")
                kn = self._known(o, p)
                if kn:
                    raise Excluded(kn)
                if o["price_channel"] not in p.effective_channels:
                    raise Excluded(f"channel {o['price_channel']} not accepted" + (" (retail needs accept_retail_proxy=True)" if o["price_channel"] in RETAIL_CHANNELS else ""))
                if o["promo_flag"]:
                    raise Excluded("promotional price")
                if o.get("currency") not in (None, "USD"):
                    raise Excluded(f"currency {o.get('currency')}")
                if _d(o["pack_content_qty"]) != _d(prod["content_qty"]) or o["pack_content_unit_id"] != prod["content_unit_id"]:
                    raise Excluded("pack differs from the product's pack (different SKU?)")
                src = self._sources[o["source_id"]]
                if src["reuse_status"] in MANUAL_ONLY and o["capture_method"] != "manual_browser":
                    raise Excluded(f"source {src['source_id']} allows manual capture only")
                try:
                    m = self.units.factor(o["pack_content_unit_id"], qty_unit)
                except UnitError as e:
                    raise Excluded(f"unit mismatch ({e})")
                if o.get("qty_tier_min") is not None:
                    if need_qty is None:
                        raise Excluded(f"quantity-tier price (min {o['qty_tier_min']} {o['pack_content_unit_id']}) needs RunParams.quantity")
                    need_content = need_qty / _frac(m)
                    if need_content < _d(o["qty_tier_min"]):
                        raise Excluded(f"order of {q6(need_content)} {o['pack_content_unit_id']} is below the tier minimum {o['qty_tier_min']}")
                cls = self._price_region_class(o.get("region_id"), p.region_id)
                adj: dict[str, Any] = {}
                flags: list[str] = []
                if cls is None:
                    if not p.use_region_factors or o.get("region_id") is None:
                        raise Excluded(f"region {o.get('region_id')} (zip/store only: {o.get('zip')}/{o.get('store_ref')}) is not within {p.region_id}")
                    f = self._region_factor(o["region_id"], p.region_id, kind, p)
                    if f is None:
                        raise Excluded(f"no usable region factor {o['region_id']}->{p.region_id}")
                    adj["region_factor"] = {"factor_id": f["factor_id"], "factor_value": str(f["factor_value"])}
                    cls = (3, 0)
                    flags.append("REGION_FACTOR_APPLIED")
                elif cls[0] == 1:
                    if not p.allow_subregion_prices:
                        raise Excluded(f"region {o['region_id']} is inside {p.region_id} (allow_subregion_prices=False)")
                    flags.append(f"PRICE_FROM_SUBREGION:{o['region_id']}")
                elif cls[0] == 2:
                    if not p.allow_ancestor_region_prices:
                        raise Excluded(f"region {o['region_id']} covers {p.region_id} (allow_ancestor_region_prices=False)")
                    flags.append(f"PRICE_FROM_ANCESTOR_REGION:{o['region_id']}")
                age = (p.as_of - o["observed_at"]).days
                if idx is not None:
                    if self._period_start(idx["frequency"], o["observed_at"]) != self._period_start(idx["frequency"], p.as_of):
                        try:
                            i_now, m_now = self._index_value(idx, p.as_of, p, allow_fallback=True)
                            i_then, m_then = self._index_value(idx, o["observed_at"], p)
                        except Missing as mm:
                            raise Excluded(f"{mm.info['code']}: {mm.info['needed']}")
                        adj["time_index"] = {"index_id": idx["index_id"], "from_date": o["observed_at"].isoformat(), "to_date": p.as_of.isoformat(),
                                             "index_from": str(i_then), "index_to": str(i_now), "period_from": m_then["period_start"],
                                             "period_to": m_now["period_start"], "vintage_from": m_then["vintage_date"],
                                             "vintage_to": m_now["vintage_date"], "factor": str(i_now / i_then),
                                             "formula": "price_to = price_from * index_to / index_from"}
                        flags.append("TIME_INDEXED_PRICE")
                        if m_now["fallback_to_latest_published"]:
                            flags.append(f"INDEX_LATEST_PUBLISHED_PERIOD_USED:{m_now['period_start']}")
                elif p.max_price_age_days is not None and age > p.max_price_age_days:
                    raise Excluded(f"{age} days old (max {p.max_price_age_days}), no time index supplied")
                elif (o["observed_at"].year, o["observed_at"].month) != (p.as_of.year, p.as_of.month):
                    flags.append("PRICE_NOT_TIME_ADJUSTED")
                per_content = _d(o["price_amount"]) / _d(o["pack_content_qty"])
                price = per_content / _frac(m)
                if "region_factor" in adj:
                    price *= _d(adj["region_factor"]["factor_value"])
                if "time_index" in adj:
                    price *= _d(adj["time_index"]["factor"])
                if o["price_channel"] in RETAIL_CHANNELS:
                    flags.append("RETAIL_PRICE_NOT_CONTRACTOR_COST")
                if o.get("sales_tax_included") is not False:
                    flags.append("SALES_TAX_UNKNOWN_OR_INCLUDED")
                if o.get("delivery_included") is not False:
                    flags.append("DELIVERY_UNKNOWN_OR_INCLUDED")
                if o.get("qty_tier_min") is not None:
                    flags.append(f"QTY_TIER_PRICE:{o['qty_tier_min']}")
                rts = _ts(o["retrieved_at"]) or datetime.min.replace(tzinfo=timezone.utc)
                found.append({"obs": o, "price": price, "per_content": per_content, "adj": adj, "flags": flags, "cls": cls, "age": age,
                              "sort": (cls, -o["observed_at"].toordinal(), -rts.timestamp(), oid)})
            except Excluded as e:
                reasons.append(f"{oid}: {e}")
        return min(found, key=lambda x: x["sort"]) if found else None

    def _product_pool(self, c: dict, p: RunParams) -> tuple[str, list[dict], list[str]]:
        reasons: list[str] = []
        if c.get("product_id"):
            pid = c["product_id"]
            prod = self._products.get(pid)
            if prod is None:
                raise Missing("PRODUCT_UNKNOWN", pid, "pinned product not in products table")
            if c.get("product_spec_key") and c["product_spec_key"] != prod["spec_key"]:
                raise Missing("PRODUCT_SPEC_MISMATCH", f"{pid} vs {c['product_spec_key']}",
                              "the pinned product's spec_key differs from the component's required spec_key", blocking=True)
            key, pool = prod["spec_key"], [prod]
        else:
            key = c["product_spec_key"]
            pool = self._products_by_key.get(key, [])
        usable = []
        for prod in pool:
            why = self._why_not(prod, p)
            if why:
                reasons.append(f"product {prod['product_id']}: {why}")
            else:
                usable.append(prod)
        return key, usable, reasons

    def _consumption_qty(self, c: dict, prod: dict, out_unit: str, p: RunParams):
        """Product quantity per unit of OUTPUT for the SAME product that is priced:
        qty = coats_applied * per_qty / (coverage * [coverage_unit -> output unit] * coats_in_rate)."""
        pid = prod["product_id"]
        app = c["consumption_application"]
        sel = c.get("consumption_selector") or {}
        bad = [k for k in sel if k not in CONSUMPTION_SELECTOR_KEYS]
        if bad:
            raise Missing("CONSUMPTION_SELECTOR_INVALID", c["component_id"], f"unknown selector key(s) {bad}; allowed: {CONSUMPTION_SELECTOR_KEYS}", blocking=True)
        rows = [r for r in self._consumption.get(pid, []) if r["application"] == app]
        ok, why_not = [], []
        for r in rows:
            why = self._why_not(r, p)
            if why:
                why_not.append(f"{r['consumption_id']}: {why}")
                continue
            mism = [k for k, v in sel.items() if r.get(k) is None or _norm(r[k]) != _norm(v)]
            if mism:
                why_not.append(f"{r['consumption_id']}: selector mismatch on {mism}")
                continue
            ok.append(r)
        if not ok:
            raise Excluded(f"no usable product_consumption for application '{app}'" + (f" ({'; '.join(why_not[:2])})" if why_not else ""))
        if len(ok) > 1:
            raise Missing("CONSUMPTION_AMBIGUOUS", f"coverage of {pid} / {app}",
                          f"{len(ok)} usable consumption rows ({', '.join(sorted(r['consumption_id'] for r in ok))}) differ in film thickness / conditions",
                          "add consumption_selector to the work-item component or supersede the wrong row")
        r = ok[0]
        cov, k, n, per = _d(r["coverage_qty"]), _d(r["coats"]), _d(c["coats_applied"]), _d(r["per_qty"])
        if cov <= 0 or k <= 0 or per <= 0 or n <= 0:
            raise Excluded(f"{r['consumption_id']}: coverage, coats and per_qty must be positive")
        try:
            m = self.units.factor(r["coverage_unit_id"], out_unit)
        except UnitError as e:
            raise Excluded(f"{r['consumption_id']}: coverage unit {r['coverage_unit_id']} cannot be converted to {out_unit} ({e})")
        mult = _frac(m)
        qty = n * per / (cov * mult * k)
        formula = (f"coats_applied {n} x per_qty {per} {r['per_unit_id']} / (coverage {cov} {r['coverage_unit_id']} "
                   f"x [{r['coverage_unit_id']}->{out_unit}] {mult} x coats_in_rate {k})")
        inp = _inp("product_consumption", r["consumption_id"], "coverage_qty", cov, r["coverage_unit_id"], "observed",
                   per_unit=r["per_unit_id"], film_thickness=r["film_thickness"], coats_in_rate=str(k), conditions=r["conditions"],
                   review_status=r["review_status"], product_id=pid)
        return qty, r["per_unit_id"], formula, "derived", inp

    def _fixed_qty(self, c: dict, p: RunParams):
        """(qty, unit, formula, origin, inputs) of a fixed-quantity component, or raises Missing."""
        if c["qty_origin"] == "assumed":
            raise Missing("QUANTITY_ASSUMED", f"quantity per unit for {c['description']}",
                          "an inline assumed quantity is not accepted; record it in the assumptions table (quantity:<component_id>)")
        if c["qty_origin"] == "missing" or c["qty_per_unit"] is None:
            a = self._assumption(f"quantity:{c['component_id']}", ("other",), p)
            if a is None:
                raise Missing("QUANTITY_MISSING", f"quantity per unit for {c['description']}", "quantity not derivable from any collected source",
                              "derive from geometry/manufacturer data or add an approved assumption")
            unit = a.get("unit_id") or c.get("qty_unit_id")
            if unit is None:
                raise Missing("QUANTITY_UNIT_MISSING", c["description"], "assumed quantity has no unit")
            if _d(a["value_numeric"]) <= 0:
                raise Missing("QUANTITY_INVALID", c["description"], "assumed quantity must be > 0", blocking=True)
            return _d(a["value_numeric"]), unit, f"assumption {a['assumption_id']}", "assumed", [self._assumption_input(a, unit)]
        if _d(c["qty_per_unit"]) <= 0:
            raise Missing("QUANTITY_INVALID", c["description"], f"qty_per_unit {c['qty_per_unit']} must be > 0", blocking=True)
        if c.get("qty_unit_id") is None:
            raise Missing("QUANTITY_UNIT_MISSING", c["description"], "component has no quantity unit")
        return _d(c["qty_per_unit"]), c["qty_unit_id"], c["qty_formula"], c["qty_origin"], []

    def _waste(self, c: dict, p: RunParams):
        if c["waste_factor"] is not None:
            if c["waste_origin"] not in ("observed", "derived"):
                raise Missing("WASTE_ASSUMED", f"waste factor for {c['description']}",
                              "waste factor is not observed/derived; an assumed value belongs in the assumptions table",
                              "source the waste factor or add an approved assumption (waste:<component_id>)")
            w = _d(c["waste_factor"])
            return w, "observed" if c["waste_origin"] == "observed" else "derived", \
                [_inp("work_item_components", c["component_id"], "waste_factor", w, None, c["waste_origin"], basis=c["waste_basis"])]
        a = self._assumption(f"waste:{c['component_id']}", ("waste",), p)
        if a is None:
            raise Missing("WASTE_MISSING", f"waste factor for {c['description']}", "no waste/loss factor recorded (zero is only acceptable with a stated basis)",
                          "record waste_factor with waste_basis, or an approved assumption")
        return _d(a["value_numeric"]), "assumed", [self._assumption_input(a, "fraction")]

    def _material_component(self, c: dict, kind: str, wi: dict, p: RunParams, collect: list, applied: set):
        """Resolve quantity, waste and price of one material-like component. EVERY gap is collected, none is hidden."""
        out_unit = wi["output_unit_id"]
        consumption = c["qty_mode"] == "from_product_consumption"
        # ---- waste
        waste, worigin, winput = None, "observed", []
        try:
            waste, worigin, winput = self._waste(c, p)
        except Missing as m:
            collect.append(m)
        # ---- fixed quantity (common to all products)
        fixed = None
        if not consumption:
            try:
                fixed = self._fixed_qty(c, p)
            except Missing as m:
                collect.append(m)
        # ---- conditions / quantity factors
        factors: list = []
        try:
            factors = self._adjust_factors(kind, p, applied)
        except Missing as m:
            collect.append(m)
        # ---- products
        key, pool, reasons = None, [], []
        try:
            key, pool, reasons = self._product_pool(c, p)
        except Missing as m:
            collect.append(m)
        cands: list[dict] = []
        sel_missing = False
        cons_gap = price_gap = False
        for prod in pool:
            try:
                if consumption:
                    try:
                        qty, qunit, qformula, qorigin, qin = self._consumption_qty(c, prod, out_unit, p)
                    except Excluded:
                        cons_gap = True
                        raise
                    qinputs = [qin]
                elif fixed is not None:
                    qty, qunit, qformula, qorigin, qinputs = fixed
                else:
                    qty = None
                    qunit = c.get("qty_unit_id")
                    qformula, qorigin, qinputs = None, "observed", []
                if qunit is None:
                    reasons.append(f"product {prod['product_id']}: no quantity unit")
                    continue
                need = None
                if p.quantity is not None and qty is not None and waste is not None:
                    need = p.quantity * qty * (1 + waste)
                best = self._best_observation(prod, qunit, need, kind, p, reasons)
                if best is None:
                    price_gap = True
                    continue
                best.update({"prod": prod, "qty": qty, "unit": qunit, "qformula": qformula, "qorigin": qorigin, "qinputs": qinputs})
                cands.append(best)
            except Excluded as e:
                reasons.append(f"product {prod['product_id']}: {e}")
            except Missing as m:
                if not any(x.info["code"] == m.info["code"] and x.info["needed"] == m.info["needed"] for x in collect):
                    collect.append(m)
                sel_missing = True
        price_assumption = None
        if not cands and not sel_missing and key is not None:
            if consumption and (cons_gap or not pool):
                collect.append(Missing("CONSUMPTION_MISSING", f"manufacturer coverage for {key} / {c['consumption_application']}",
                                       "no usable product_consumption record for any usable product",
                                       "extract spread rate with film thickness, coats and conditions from the product data sheet"))
            if not consumption or price_gap or not pool:
                qu = fixed[1] if fixed else c.get("qty_unit_id")
                try:
                    a = self._assumption(f"price:{key}", ("material_price",), p)
                except Missing as m:
                    collect.append(m)
                    a = None
                if a is not None and not consumption and qu is not None:
                    if a.get("unit_id") is None or not self.units.compatible(a["unit_id"], qu):
                        collect.append(Missing("ASSUMPTION_UNIT", f"price:{key}", "approved price assumption has no unit compatible with the quantity unit"))
                    else:
                        price_assumption = a
                elif a is not None and consumption:
                    collect.append(Missing("ASSUMPTION_UNIT", f"price:{key}", "an assumed price cannot be combined with a coverage-based quantity (no product to pair the coverage with)"))
                if price_assumption is None and not any(m.info["code"] in ("ASSUMPTION_UNIT", "ASSUMPTION_AMBIGUOUS") for m in collect):
                    collect.append(Missing("PRICE_MISSING", f"validated price observation for spec {key}",
                                           "; ".join(reasons[:3]) if reasons else "no usable product or observation exists",
                                           f"capture price for spec_key {key} in {p.region_id} (templates/price_capture_template.csv)"))
        if collect or waste is None or (fixed is None and not consumption):
            return None
        if price_assumption is not None:
            a = price_assumption
            m = self.units.factor(a["unit_id"], fixed[1])
            price = _d(a["value_numeric"]) / _frac(m)
            qty, qunit, qformula, qorigin, qinputs = fixed
            eff = qty * (1 + waste)
            cost = eff * price
            for f in factors:
                cost *= _d(f["factor_value"])
            adj_note = "".join(f" x {f['factor_value']} [{f['factor_id']}]" for f in factors)
            origins = {qorigin, "assumed", worigin}
            return {"qty": eff, "unit": qunit, "price": price, "cost": cost, "uniform": True, "basis": "assumed",
                    "formula": f"{qformula} = {qty} {qunit}/unit x (1+{waste}) x ${q10(price)}/{qunit} [ASSUMED PRICE]{adj_note}",
                    "inputs": qinputs + winput + [self._assumption_input(a)] + [self._factor_input(f) for f in factors],
                    "summary": "assumed", "flags": ["ASSUMED_PRICE"]}
        # ---- best region class across products, then policy
        best_cls = min(x["cls"] for x in cands)
        cands = [x for x in cands if x["cls"] == best_cls]
        flags: list[str] = []
        if p.price_policy == "latest":
            cands = [min(cands, key=lambda x: x["sort"][1:])]
        elif len(cands) > 1:
            flags.append(f"MEDIAN_OF_{len(cands)}_PRODUCTS")
        for x in cands:
            eff = x["qty"] * (1 + waste)
            x["eff"] = eff
            x["cost"] = eff * x["price"]
            for f in factors:
                x["cost"] *= _d(f["factor_value"])
            flags += x["flags"]
        inputs: list = list(winput)
        for x in cands:
            o = x["obs"]
            inputs += x["qinputs"]
            inp = _inp("price_observations", o["observation_id"], "price_amount/pack_content_qty", x["per_content"], o["pack_content_unit_id"], "observed",
                       observed_at=o["observed_at"].isoformat(), retrieved_at=str(o["retrieved_at"]), price_channel=o["price_channel"],
                       region_id=o.get("region_id"), zip=o.get("zip"), store_ref=o.get("store_ref"), review_status=o["review_status"],
                       sales_tax_included=o.get("sales_tax_included"), delivery_included=o.get("delivery_included"),
                       age_days=x["age"], product_id=x["prod"]["product_id"], price_per_qty_unit=str(x["price"]))
            if x["adj"]:
                inp["adjustments"] = json.loads(json.dumps(x["adj"], default=str))
            inputs.append(inp)
        inputs += [self._factor_input(f) for f in factors]
        adj_note = "".join(f" x {f['factor_value']} [{f['factor_id']}]" for f in factors)
        uniform = len({(x["eff"], x["unit"]) for x in cands}) == 1
        origins = {x["qorigin"] for x in cands} | {worigin, "observed"}
        summary = "assumed" if "assumed" in origins else ("mixed" if len(origins) > 1 else next(iter(origins)))
        basis = _combine_basis({_price_basis_of(x["obs"]["price_channel"]) for x in cands})
        if uniform:
            x0 = cands[0]
            price = median([x["price"] for x in cands]) if len(cands) > 1 else x0["price"]
            cost = x0["eff"] * price
            for f in factors:
                cost *= _d(f["factor_value"])
            formula = f"{x0['qformula']} = {x0['qty']} {x0['unit']}/unit x (1+{waste}) x ${q10(price)}/{x0['unit']}{adj_note}"
            return {"qty": x0["eff"], "unit": x0["unit"], "price": price, "cost": cost, "uniform": True, "basis": basis, "formula": formula,
                    "inputs": inputs, "summary": summary, "flags": sorted(set(flags))}
        cost = median([x["cost"] for x in cands]) if len(cands) > 1 else cands[0]["cost"]
        parts = "; ".join(f"{x['prod']['product_id']}: {x['qty']} {x['unit']} x (1+{waste}) x ${q10(x['price'])} = ${q10(x['cost'])}" for x in cands)
        return {"qty": None, "unit": None, "price": None, "cost": cost, "uniform": False, "basis": basis,
                "formula": f"median of per-product costs ({len(cands)} products, each coverage paired with its own price){adj_note}: {parts}",
                "inputs": inputs, "summary": summary, "flags": sorted(set(flags))}

    # ------------------------------------------------------------------------------------------------ labor rate
    def _burden_pick(self, btype: str, trade: str, p: RunParams) -> list[dict]:
        """Best-scoring group of usable burden rows: score = (region rank, trade specificity, -effective_from)."""
        best_score, group = None, []
        for b in self._burden.get(btype, []):
            if b["origin"] != "observed" or self._why_not(b, p) or self._known(b, p):
                continue
            if b.get("trade_code") not in (None, trade) or not self._in_period(b, p.as_of):
                continue
            if p.wc_class_code is not None and btype == "workers_comp" and b.get("class_code") != p.wc_class_code:
                continue
            rank = self._rank_up(b.get("region_id"), p.region_id)
            if rank is None:
                continue
            score = (rank, 0 if b.get("trade_code") == trade else 1, -b["effective_from"].toordinal())
            if best_score is None or score < best_score:
                best_score, group = score, [b]
            elif score == best_score:
                group.append(b)
        return group

    def _burden_row(self, btype: str, trade: str, p: RunParams) -> Optional[dict]:
        group = self._burden_pick(btype, trade, p)
        if not group:
            return None
        sig = {(b["basis"], b["rate"], b.get("wage_cap_annual"), b.get("class_code")) for b in group}
        if len(sig) > 1:
            raise Missing("BURDEN_AMBIGUOUS", f"{btype} for {trade} in {p.region_id}",
                          f"{len(group)} rows tie on region/trade/effective date with different values ({', '.join(sorted(b['burden_id'] for b in group))})",
                          "set RunParams.wc_class_code (workers' comp) or supersede the wrong row")
        return sorted(group, key=lambda b: b["burden_id"])[0]

    def _burden_hourly(self, b: dict, wages_hr: Decimal, p: RunParams) -> Decimal:
        rate = _d(b["rate"])
        if b["basis"] == "per_hour":
            return rate
        pct = rate if b["basis"] == "pct_of_wages" else rate / D(100)
        cap = b.get("wage_cap_annual")
        if cap is None:
            return pct * wages_hr
        if p.annual_paid_hours is None:
            raise Missing("ANNUAL_HOURS_MISSING", "annual_paid_hours parameter",
                          f"burden {b['burden_type']} has an annual wage cap; hourly equivalent needs paid hours per year",
                          "pass RunParams.annual_paid_hours with a stated basis")
        annual_wages = wages_hr * p.annual_paid_hours
        return pct * min(_d(cap), annual_wages) / p.annual_paid_hours

    @staticmethod
    def _burden_input(b: dict) -> dict:
        return _inp("burden_rates", b["burden_id"], "rate", b["rate"], b["basis"], "observed", review_status=b["review_status"],
                    burden_type=b["burden_type"], region_id=b.get("region_id"), class_code=b.get("class_code"))

    def _payroll_types(self, p: RunParams) -> tuple[str, ...]:
        state = self._state_code(p.region_id)
        return BASE_PAYROLL_TYPES + STATE_PAYROLL_EXTRA.get(state or "", ())

    def _labor_candidate(self, trade: str, p: RunParams, want: tuple, reasons: list) -> tuple[Optional[dict], int]:
        best_score, group = None, []
        for r in self._labor.get(trade, []):
            rid = r["labor_rate_id"]
            why = None
            if r["rate_type"] not in want:
                continue
            if r["origin"] != "observed":
                why = f"origin={r['origin']}"
            elif self._why_not(r, p):
                why = self._why_not(r, p)
            elif self._known(r, p):
                why = self._known(r, p)
            elif not self._in_period(r, p.as_of):
                why = "outside its effective period"
            elif r["apprentice"]:
                why = "apprentice step"
            elif r["wage_basis"] not in ("straight_time", "n/a"):
                why = f"wage_basis={r['wage_basis']}"
            elif p.labor_basis == "stat_loaded" and r["statistic"] != p.labor_statistic:
                why = f"statistic={r['statistic']} (need {p.labor_statistic})"
            elif r["project_type"] != p.wage_class:
                why = f"project_type={r['project_type']} (need wage_class {p.wage_class})"
            elif (r["includes_overhead"] or r["includes_profit"]):
                why = "rate includes overhead/profit; marking it up again would double count"
            elif p.classification is not None and _norm(r["classification_raw"]) != _norm(p.classification):
                why = f"classification '{r['classification_raw']}'"
            else:
                rank = self._rank_up(r["region_id"], p.region_id)
                if rank is None:
                    why = f"region {r['region_id']} is not {p.region_id} or an ancestor"
                else:
                    score = (rank, -r["effective_from"].toordinal())
                    if best_score is None or score < best_score:
                        best_score, group = score, [r]
                    elif score == best_score:
                        group.append(r)
                    continue
            reasons.append(f"{rid}: {why}")
        if not group:
            return None, 0
        sig = {(r["classification_raw"], r["base_wage_hr"], r["fringe_hr"], r["total_hr"]) for r in group}
        if len(sig) > 1:
            raise Missing("LABOR_RATE_AMBIGUOUS", f"rate for {trade} in {p.region_id}",
                          f"{len(group)} candidate rows tie ({'; '.join(sorted(r['classification_raw'] + ' ' + str(r['base_wage_hr']) for r in group))})",
                          "set RunParams.classification (exact classification_raw) or supersede the wrong row")
        return sorted(group, key=lambda r: r["labor_rate_id"])[0], best_score[0]

    def labor_rate(self, trade: str, p: RunParams) -> dict:
        self._refresh()
        return self._labor_rate(trade, p)

    def _labor_rate(self, trade: str, p: RunParams) -> dict:
        """Loaded employer cost per paid hour for a trade, built from separately sourced components."""
        basis = p.labor_basis
        if basis == "prevailing_loaded" and p.project_type != "public_works":
            raise Missing("PW_NOT_APPLICABLE", f"prevailing wage for {trade}",
                          "prevailing/federal wage rates apply to public works only; this run is project_type='private'",
                          "use labor_basis='stat_loaded' or 'company_actual' for private projects", blocking=True)
        if basis == "prevailing_loaded":
            want = ("prevailing_wage",) if p.wage_regime == "state" else ("federal_wage_determination",)
        else:
            want = LABOR_BASIS_TYPES[basis]
        reasons: list[str] = []
        rec, rank = self._labor_candidate(trade, p, want, reasons)
        flags: list[str] = []
        if p.project_type == "public_works" and basis != "prevailing_loaded":
            flags.append("PUBLIC_WORKS_NOT_ON_PREVAILING_BASIS")
        if rec is None:
            a = self._assumption(f"labor_rate:{trade}:{p.region_id}", ("labor_rate",), p)
            if a is not None:
                if a.get("unit_id") not in (None, "HR"):
                    raise Missing("ASSUMPTION_UNIT", f"labor_rate:{trade}", "approved labor-rate assumption must be $/HR")
                return {"total_hr": _d(a["value_numeric"]), "components": {"assumed_total": _d(a["value_numeric"])},
                        "inputs": [self._assumption_input(a, "HR")], "flags": flags + ["ASSUMED_LABOR_RATE"], "origin": "assumed",
                        "governing": {"region_id": p.region_id, "effective_from": p.as_of, "effective_to": None}}
            raise Missing("LABOR_RATE_MISSING", f"{basis} rate for {trade} in {p.region_id}",
                          f"no usable {'/'.join(want)} record" + (f" ({'; '.join(reasons[:3])})" if reasons else ""),
                          f"capture {'OEWS/DIR/SAM' if basis != 'company_actual' else 'company payroll'} rate for {trade}")
        if rank:
            flags.append(f"RATE_FROM_ANCESTOR_REGION:{rec['region_id']}")
        if p.max_rate_age_days is not None and (p.as_of - rec["effective_from"]).days > p.max_rate_age_days:
            flags.append("STALE_RATE")
        inputs = [_inp("labor_rates", rec["labor_rate_id"], "base_wage_hr/fringe_hr/total_hr", rec["base_wage_hr"], "HR", "observed",
                       review_status=rec["review_status"], rate_type=rec["rate_type"], statistic=rec["statistic"], region_id=rec["region_id"],
                       classification=rec["classification_raw"])]
        governing = {"region_id": rec["region_id"], "effective_from": rec["effective_from"], "effective_to": rec.get("effective_to")}
        if basis == "company_actual":
            if rec.get("total_hr") is None:
                raise Missing("COMPANY_TOTAL_MISSING", f"total_hr for {rec['labor_rate_id']}", "company_actual rate needs total_hr")
            return {"total_hr": _d(rec["total_hr"]), "components": {"company_actual_total": _d(rec["total_hr"])}, "inputs": inputs,
                    "flags": flags, "origin": "observed", "governing": governing}
        base = _d(rec["base_wage_hr"])
        comps: dict[str, Decimal] = {"base_wage": base}
        inc_f, inc_t, inc_w = bool(rec["includes_fringe"]), bool(rec["includes_payroll_taxes"]), bool(rec["includes_workers_comp"])
        inc_all = inc_f and inc_t and inc_w
        parts = ((inc_f, "fringe_hr", "fringe_in_source"), (inc_t, "payroll_tax_hr", "payroll_tax_in_source"),
                 (inc_w, "workers_comp_hr", "workers_comp_in_source"))
        gaps = [col for inc, col, _ in parts if inc and rec.get(col) is None]
        if gaps:
            # the record claims to include a component but does not state it: only a fully loaded record with a stated total is usable
            if inc_all and rec.get("total_hr") is not None and _d(rec["total_hr"]) >= base:
                comps = {"base_wage": base, "loaded_total_in_source": _d(rec["total_hr"]) - base}
                flags.append("LOADED_RATE_NOT_ITEMIZED")
            else:
                raise MultiMissing([Missing(f"{col.upper()}_MISSING", f"{col} for {rec['labor_rate_id']}",
                                            "record says it includes this component but states none") for col in gaps])
        else:
            for inc, col, name in parts:
                if inc:
                    comps[name] = _d(rec[col])
            if rec.get("other_employer_cost_hr") is not None:
                comps["other_employer_cost"] = _d(rec["other_employer_cost_hr"])
            if inc_all and rec.get("total_hr") is not None:
                stated, summed = _d(rec["total_hr"]), sum(comps.values(), D(0))
                if abs(stated - summed) > D("0.0005"):
                    raise Missing("LABOR_TOTAL_MISMATCH", rec["labor_rate_id"], f"total_hr {stated} differs from the sum of its components {q10(summed)}", blocking=True)
        wages_for_pct = base + (comps.get("fringe_in_source", D(0)) if p.burden_base == "wage_plus_fringe" else D(0))
        origin = "observed"
        collected: list[Missing] = []

        def burden(btype: str, name: str, assumption_ok: bool, ref_kind: str):
            nonlocal origin
            try:
                b = self._burden_row(btype, trade, p)
            except Missing as m:
                collected.append(m)
                return
            if b is not None:
                try:
                    comps[name] = self._burden_hourly(b, wages_for_pct, p)
                except Missing as m:
                    collected.append(m)
                    return
                inputs.append(self._burden_input(b))
                return
            a = None
            if assumption_ok:
                try:
                    a = self._assumption(f"burden:{btype}:{trade}", ("other",), p)
                except Missing as m:
                    collected.append(m)
                    return
            if a is None:
                collected.append(Missing(ref_kind + "_MISSING", f"{btype} for {trade} in {p.region_id}", "no usable burden_rates record" +
                                         ("" if not assumption_ok else " and no approved assumption"),
                                         f"capture {btype} (IRS/EDD/insurer/ECEC or company cost)"))
                return
            v = _d(a["value_numeric"])
            if a.get("unit_id") == "HR":
                comps[name] = v
            elif a.get("unit_id") is None and D(0) <= v <= D(1):
                comps[name] = v * wages_for_pct
            else:
                collected.append(Missing("ASSUMPTION_UNIT", f"burden:{btype}:{trade}", "burden assumption must be $/HR (unit HR) or a fraction of wages in [0,1] (no unit)"))
                return
            inputs.append(self._assumption_input(a, "$/HR" if a.get("unit_id") == "HR" else "fraction_of_wages"))
            flags.append("ASSUMED_" + btype.upper())
            origin = "assumed"

        if not inc_f:
            burden("employer_benefits", "employer_benefits", True, "BENEFITS")
        if not inc_t:
            for t in self._payroll_types(p):
                burden(t, t, False, "PAYROLL_TAX")
        if not inc_w:
            burden("workers_comp", "workers_comp", True, "WORKERS_COMP")
        if collected:
            raise MultiMissing(collected)
        for t in FLAGGED_ONLY_BURDENS:
            try:
                if self._burden_pick(t, trade, p):
                    flags.append(f"OMITTED_BURDEN:{t}")
            except Missing:
                pass
        total = sum(comps.values(), D(0))
        return {"total_hr": total, "components": comps, "inputs": inputs, "flags": flags, "origin": origin, "governing": governing}

    # ---------------------------------------------------------------------------------------------- equipment
    def _equipment_rate(self, etype: str, p: RunParams) -> dict:
        best_score, group, reasons = None, [], []
        for r in self._equip_rates.get(etype, []):
            why = None
            if r["origin"] != "observed":
                why = f"origin={r['origin']}"
            elif self._why_not(r, p):
                why = self._why_not(r, p)
            elif self._known(r, p):
                why = self._known(r, p)
            elif not self._in_period(r, p.as_of):
                why = "outside its effective period"
            else:
                rank = self._rank_up(r["region_id"], p.region_id)
                if rank is None:
                    why = f"region {r['region_id']} is not {p.region_id} or an ancestor"
                else:
                    score = (rank, -r["effective_from"].toordinal())
                    if best_score is None or score < best_score:
                        best_score, group = score, [r]
                    elif score == best_score:
                        group.append(r)
                    continue
            reasons.append(f"{r['equipment_rate_id']}: {why}")
        if not group:
            a = self._assumption(f"equipment_rate:{etype}:{p.region_id}", ("equipment_rate",), p)
            if a is not None:
                return {"basis": "hour", "rate": _d(a["value_numeric"]), "operator_included": False, "fuel_added": D(0),
                        "inputs": [self._assumption_input(a, "HR")], "flags": ["ASSUMED_EQUIPMENT_RATE"], "origin": "assumed"}
            raise Missing("EQUIPMENT_RATE_MISSING", f"{etype} rate in {p.region_id}", "no usable equipment_rates record" +
                          (f" ({'; '.join(reasons[:3])})" if reasons else ""), f"capture rental/owned rate for {etype}")
        if len({(r["rate_basis"], r["rental_rate_hr"], r["rental_rate_day"], r["ownership_cost_hr"], r["operating_cost_hr"], r["operator_included"]) for r in group}) > 1:
            raise Missing("EQUIPMENT_RATE_AMBIGUOUS", f"{etype} rate in {p.region_id}",
                          f"{len(group)} rows tie ({', '.join(sorted(r['equipment_rate_id'] for r in group))})", "supersede the wrong row")
        r = sorted(group, key=lambda x: x["equipment_rate_id"])[0]
        flags: list[str] = []
        if best_score[0]:
            flags.append(f"RATE_FROM_ANCESTOR_REGION:{r['region_id']}")
        if r.get("delivery_pickup_cost") is not None:
            flags.append(f"EQUIPMENT_DELIVERY_PICKUP_EXCLUDED:{r['delivery_pickup_cost']}")
        else:
            flags.append("EQUIPMENT_DELIVERY_UNKNOWN_EXCLUDED")
        if r.get("min_rental_period"):
            flags.append(f"MIN_RENTAL_PERIOD_ASSUMED_MET:{r['min_rental_period']}")
        inp = _inp("equipment_rates", r["equipment_rate_id"], "rate", "", "HR", "observed", review_status=r["review_status"],
                   operator_included=r["operator_included"], region_id=r["region_id"])
        if p.equipment_basis == "rental_day":
            if r["rental_rate_day"] is None:
                raise Missing("EQUIPMENT_DAY_RATE_MISSING", f"day rate for {etype}", "record has no rental_rate_day")
            inp.update(field="rental_rate_day", value=str(r["rental_rate_day"]), unit="DAY")
            flags.append("DAY_RATE_ONE_DAY_PER_CREW_SHIFT")
            return {"basis": "day", "rate": _d(r["rental_rate_day"]), "operator_included": r["operator_included"], "fuel_added": D(0),
                    "inputs": [inp], "flags": flags, "origin": "observed"}
        fuel = D(0)
        if r["rental_rate_hr"] is not None:
            rate = _d(r["rental_rate_hr"])
            inp["field"] = "rental_rate_hr"
        elif r["ownership_cost_hr"] is not None and r["operating_cost_hr"] is not None:
            rate = _d(r["ownership_cost_hr"]) + _d(r["operating_cost_hr"])
            inp["field"] = "ownership_cost_hr+operating_cost_hr"
        else:
            raise Missing("EQUIPMENT_HOURLY_BASIS_MISSING", f"hourly basis for {etype}", "need rental_rate_hr or ownership+operating hourly components")
        if r["fuel_included"] is False:
            if r.get("fuel_cost_hr") is None:
                raise Missing("FUEL_NOT_PRICED", f"fuel for {etype}", "the rate excludes fuel and no fuel_cost_hr is recorded", "capture fuel_cost_hr")
            fuel = _d(r["fuel_cost_hr"])
            flags.append("FUEL_ADDED_SEPARATELY")
        elif r["fuel_included"] is None:
            flags.append("FUEL_INCLUSION_UNKNOWN")
        elif r.get("fuel_cost_hr") is not None:
            flags.append("CHECK_FUEL_NOT_DOUBLE_COUNTED")
        inp["value"] = str(rate + fuel)
        return {"basis": "hour", "rate": rate + fuel, "operator_included": r["operator_included"], "fuel_added": fuel, "inputs": [inp],
                "flags": flags, "origin": "observed"}

    # ------------------------------------------------------------------------------------- crew & productivity
    def _crew_costs(self, crew_id: str, p: RunParams) -> dict:
        crew = self._crews.get(crew_id)
        if crew is None:
            raise Missing("CREW_UNKNOWN", crew_id, "crew not in crews table")
        if crew["origin"] == "missing":
            raise Missing("CREW_MISSING", f"composition of {crew_id}", "crew composition not found in any source", "capture crew composition")
        why = self._why_not(crew, p)
        if why:
            raise Missing("CREW_UNUSABLE", f"composition of {crew_id}", why,
                          "run with_assumptions or source it" if crew["origin"] == "assumed" else "validate the crew record")
        members = sorted(self._members.get(crew_id, []), key=lambda m: m["crew_member_id"])
        if not members:
            raise Missing("CREW_EMPTY", crew_id, "crew has no members")
        shift = _d(crew["shift_hours"])
        issues: list[tuple[str, Missing]] = []
        flags: list[str] = ["ASSUMED_CREW"] if crew["origin"] == "assumed" else []
        lab, eq = [], []
        operator_in_labor = any(m["is_operator"] or m["trade_code"] in OPERATOR_TRADES for m in members if m["member_kind"] == "labor")
        rate_cache: dict[str, Any] = {}
        for m in members:
            hrs = _d(m["hours_per_shift"]) if m["hours_per_shift"] is not None else shift
            qty = _d(m["quantity"])
            if m["member_kind"] == "labor":
                t = m["trade_code"]
                if t not in rate_cache:
                    try:
                        rate_cache[t] = self._labor_rate(t, p)
                    except MultiMissing as mm:
                        rate_cache[t] = mm
                    except Missing as mi:
                        rate_cache[t] = mi
                lr = rate_cache[t]
                if isinstance(lr, MultiMissing):
                    issues += [("labor", x) for x in lr.items]
                    continue
                if isinstance(lr, Missing):
                    issues.append(("labor", lr))
                    continue
                lab.append({"member": m, "qty": qty, "hrs": hrs, "lr": lr, "cost": qty * hrs * lr["total_hr"]})
            else:
                et = m["equipment_type_code"]
                try:
                    er = self._equipment_rate(et, p)
                except Missing as mi:
                    issues.append((f"equipment:{et}", mi))
                    continue
                per = qty * (hrs * er["rate"] if er["basis"] != "day" else er["rate"])
                eq.append({"member": m, "qty": qty, "hrs": hrs, "er": er, "cost": per, "etype": et})
        for e in eq:
            et = e["etype"]
            if e["er"]["operator_included"] and operator_in_labor:
                issues.append((f"equipment:{et}", Missing("OPERATOR_DOUBLE_COUNT", f"{et} in {crew_id}",
                               "equipment rate includes the operator and the crew also lists an operator as labor",
                               "remove the operator from crew labor or use a rate that excludes the operator", blocking=True)))
            elif (not e["er"]["operator_included"]) and not operator_in_labor and self._equip_types.get(et, {}).get("typically_needs_operator"):
                issues.append((f"equipment:{et}", Missing("OPERATOR_NOT_PRICED", f"operator for {et} in {crew_id}",
                               "the equipment rate excludes the operator, the type normally needs one and the crew has none",
                               "add an operator to the crew or use a rate that includes one")))
        # crew size and person-hours come from the composition itself, never from the members whose rate happened to resolve
        lab_members = [m for m in members if m["member_kind"] == "labor"]
        crew_size = sum((_d(m["quantity"]) for m in lab_members), D(0))
        person_hours = sum((_d(m["quantity"]) * (_d(m["hours_per_shift"]) if m["hours_per_shift"] is not None else shift) for m in lab_members), D(0))
        return {"crew": crew, "shift": shift, "crew_size": crew_size, "labor": lab, "equip": eq, "issues": issues, "flags": flags,
                "labor_per_shift": sum((x["cost"] for x in lab), D(0)),
                "person_hours_per_shift": person_hours,
                "labor_origin": "assumed" if any(x["lr"]["origin"] == "assumed" for x in lab) or crew["origin"] == "assumed" else "observed",
                "operator_in_labor": operator_in_labor}

    def _daily_output(self, comp: dict, wi: dict, ci: Optional[dict], p: RunParams):
        """(daily output in the work-item unit per crew shift, inputs, flags, origin)."""
        out_unit = wi["output_unit_id"]
        prod = self._prod_obs.get(comp["productivity_id"])
        if prod is None:
            raise Missing("PRODUCTIVITY_UNKNOWN", comp["productivity_id"], "productivity record not found")
        why = None if prod["origin"] != "missing" else "norm not found in any source (origin=missing)"
        why = why or self._why_not(prod, p) or self._known(prod, p)
        if why:
            a = self._assumption(f"productivity:{comp['component_id']}", ("productivity",), p)
            if a is not None:
                if a.get("unit_id") is None or not self.units.compatible(a["unit_id"], out_unit):
                    raise Missing("ASSUMPTION_UNIT", f"productivity:{comp['component_id']}", "assumed output needs a unit convertible to the work-item unit")
                daily = _d(a["value_numeric"]) * _frac(self.units.factor(a["unit_id"], out_unit))
                return daily, [self._assumption_input(a)], ["ASSUMED_PRODUCTIVITY"], "assumed"
            raise Missing("PRODUCTIVITY_MISSING", f"labor norm {comp['productivity_id']} for '{wi['name']}'", why,
                          "extract norm from a government manual / DOT guide with page reference")
        if prod.get("work_item_id") not in (None, wi["work_item_id"]):
            raise Missing("PRODUCTIVITY_WORK_ITEM_MISMATCH", comp["productivity_id"], f"norm belongs to {prod['work_item_id']}, not {wi['work_item_id']}", blocking=True)
        if prod.get("crew_id") not in (None, comp["crew_id"]):
            raise Missing("CREW_MISMATCH", f"{comp['productivity_id']} vs {comp['crew_id']}", f"norm was recorded for crew {prod['crew_id']}", blocking=True)
        try:
            mult = _frac(self.units.factor(prod["output_unit_id"], out_unit))
        except UnitError as e:
            raise Missing("PRODUCTIVITY_UNIT", comp["productivity_id"], f"output unit mismatch: {e}", blocking=True)
        flags: list[str] = []
        if prod["daily_output"] is not None:
            if ci is not None:
                if prod["crew_size"] is not None and _d(prod["crew_size"]) != ci["crew_size"]:
                    raise Missing("CREW_MISMATCH", f"{comp['productivity_id']} vs {ci['crew']['crew_id']}",
                                  f"norm was observed for crew size {prod['crew_size']} but costing crew has {ci['crew_size']}", blocking=True)
                if prod["shift_hours"] is not None and _d(prod["shift_hours"]) != ci["shift"]:
                    raise Missing("SHIFT_MISMATCH", f"{comp['productivity_id']} vs {ci['crew']['crew_id']}",
                                  f"norm shift {prod['shift_hours']} h vs crew shift {ci['shift']} h", blocking=True)
            daily = _d(prod["daily_output"]) * mult
            value = prod["daily_output"]
        else:
            if ci is None:
                raise Missing("CREW_UNRESOLVED", f"crew for {comp['productivity_id']}", "the norm is stated in person-hours and needs the costing crew")
            if ci["crew_size"] <= 0:
                raise Missing("CREW_NO_LABOR", f"crew {ci['crew']['crew_id']}", "person-hour norm needs at least one labor member", blocking=True)
            if prod["crew_size"] is not None and _d(prod["crew_size"]) != ci["crew_size"]:
                raise Missing("CREW_MISMATCH", f"{comp['productivity_id']} vs {ci['crew']['crew_id']}",
                              f"norm was observed for crew size {prod['crew_size']} but costing crew has {ci['crew_size']}", blocking=True)
            pph = _d(prod["person_hours_per_unit_reported"]) / mult
            daily = ci["crew_size"] * ci["shift"] / pph
            flags.append("DAILY_OUTPUT_DERIVED_FROM_REPORTED_PERSON_HOURS")
            value = prod["person_hours_per_unit_reported"]
        inp = [_inp("productivity_observations", prod["productivity_id"], "daily_output", value, prod["output_unit_id"], "observed",
                    source_doc=prod["source_doc"], source_edition=prod["source_edition"], source_page=prod["source_page"],
                    review_status=prod["review_status"])]
        return daily, inp, flags, "observed"

    # ------------------------------------------------------------------------------------------ definitions
    def _definition_issues(self, row: dict, what: str, p: RunParams) -> list[Missing]:
        ref = f"{row.get('work_item_id') or row.get('assembly_id')} v{row['version']}"
        out = []
        if row["status"] == "retired":
            out.append(Missing("DEFINITION_RETIRED", f"{what} {ref}", "this version is retired", "use the current version", blocking=True))
        if row["valid_from"] > p.as_of:
            out.append(Missing("DEFINITION_NOT_YET_VALID", f"{what} {ref}", f"valid from {row['valid_from'].isoformat()}, after as_of", blocking=True))
        if row["review_status"] in ("flagged", "rejected"):
            out.append(Missing("DEFINITION_REJECTED", f"{what} {ref}", f"review_status={row['review_status']}", blocking=True))
        elif p.min_review == "validated" and row["review_status"] != "validated":
            out.append(Missing("DEFINITION_NOT_REVIEWED", f"{what} {ref}",
                               f"definition review_status={row['review_status']}: scope, specification and quantities have not been checked by a reviewer",
                               "record an independent review (review_events) or run with min_review='unreviewed'"))
        return out

    # ------------------------------------------------------------------------------------------------ unit cost
    def unit_cost(self, work_item_id: str, version: int, p: RunParams) -> RunResult:
        self._refresh()
        applied: set = set()
        res = self._unit_cost(work_item_id, version, p, applied)
        return self._require_conditions(res, p, applied)

    def _require_conditions(self, res: RunResult, p: RunParams, applied: set) -> RunResult:
        """A requested condition that changed no cost line anywhere is a missing input, never silently ignored."""
        unapplied = [t for t in p.conditions if t not in applied]
        if not unapplied or res.run["status"] == "failed":
            return res
        for t in unapplied:
            res.run["missing_inputs"].append(_missing_info(Missing("CONDITION_FACTOR_MISSING", f"factor for condition '{t}'",
                                             "no usable factor changes any cost line of this run; a requested job condition is never silently ignored",
                                             "source a conditions factor for the affected cost kind or remove the condition"), res.run["target_id"]))
        run = res.run
        run.update(status="incomplete", material_cost=None, labor_cost=None, equipment_cost=None, other_direct_cost=None, direct_cost_total=None)
        run["run_id"] = self._run_id(run["target_type"], run["target_id"], run["target_version"], p, res.lines, run["missing_inputs"])
        for ln in res.lines:
            ln["run_id"] = run["run_id"]
        return res

    def _unit_cost(self, work_item_id: str, version: int, p: RunParams, applied: set) -> RunResult:
        wi = self._wis.get((work_item_id, version))
        if wi is None:
            raise KeyError(f"work item {work_item_id} v{version} not found")
        comps = sorted(self._wi_comps.get((work_item_id, version), []), key=lambda c: c["line_no"])
        lines: list[dict] = []
        missing: list[dict] = []
        warnings: list[str] = []
        bases: set = set()
        totals = {"material": D(0), "labor": D(0), "equipment": D(0), "other_direct": D(0)}
        any_assumed = False
        for m in self._definition_issues(wi, "work item", p):
            missing.append(_missing_info(m, work_item_id))
        if any(m["blocking"] for m in missing):
            return self._finish("unit_cost", work_item_id, version, p, wi["output_unit_id"], lines, missing, warnings, totals, any_assumed, bases)
        seen: dict[str, str] = {}
        for c in comps:
            for t in c["cost_tags"] or []:
                if t in seen and seen[t] != c["component_id"]:
                    missing.append(_missing_info(Missing("DUPLICATE_COST_TAG", f"cost tag '{t}'", f"on {seen[t]} and {c['component_id']}: double-counting suspicion",
                                                         "keep the tag on one component", blocking=True), c["component_id"]))
                seen.setdefault(t, c["component_id"])

        def add_missing(c: dict, items: list):
            reasons = []
            for m in items:
                missing.append(_missing_info(m, c["component_id"]))
                reasons.append(f"{m.info['code']}: {m.info['needed']}")
            lines.append({"line_no": len(lines) + 1, "line_kind": c["component_kind"], "component_ref": c["component_id"],
                          "description": c["description"], "quantity": None, "quantity_unit_id": None, "quantity_kind": "none", "unit_cost": None,
                          "extended_cost": None, "formula": "UNRESOLVED " + " | ".join(reasons), "inputs": [], "origin_summary": "missing", "warnings": []})

        crew_cache: dict[str, Any] = {}
        for c in comps:
            kind = c["component_kind"]
            if c["is_optional"] and not p.include_optional:
                warnings.append(f"OPTIONAL_COMPONENT_EXCLUDED:{c['component_id']}")
                continue
            if kind in ("material", "other_direct"):
                collect: list[Missing] = []
                res = self._material_component(c, kind, wi, p, collect, applied)
                if res is None:
                    add_missing(c, collect)
                    continue
                if res["summary"] == "assumed":
                    any_assumed = True
                if res["basis"] != "none":
                    bases.add(res["basis"])
                totals[kind] += q10(res["cost"])
                lines.append({"line_no": len(lines) + 1, "line_kind": kind, "component_ref": c["component_id"], "description": c["description"],
                              "quantity": q10(res["qty"]) if res["uniform"] else None, "quantity_unit_id": res["unit"] if res["uniform"] else None,
                              "quantity_kind": "material_qty" if res["uniform"] else "none",
                              "unit_cost": q10(res["price"]) if res["uniform"] else None, "extended_cost": q10(res["cost"]),
                              "formula": res["formula"], "inputs": res["inputs"], "origin_summary": res["summary"], "warnings": res["flags"]})
                continue
            # ---- labor / equipment: crew composition and productivity are resolved independently
            errs: list[Missing] = []
            ci = None
            cached = crew_cache.get(c["crew_id"])
            if cached is None:
                try:
                    cached = ("ok", self._crew_costs(c["crew_id"], p))
                except Missing as m:
                    cached = ("err", [m])
                crew_cache[c["crew_id"]] = cached
            if cached[0] == "ok":
                ci = cached[1]
                scope = "labor" if kind == "labor" else f"equipment:{c['equipment_type_code']}"
                errs += [m for sc, m in ci["issues"] if sc == scope]
                if kind == "equipment" and not [e for e in ci["equip"] if e["etype"] == c["equipment_type_code"]] \
                        and not any(sc == scope for sc, _ in ci["issues"]):
                    errs.append(Missing("CREW_NO_EQUIPMENT", f"{c['equipment_type_code']} in {c['crew_id']}",
                                        "the equipment component's type is not a member of its crew", "add the equipment to the crew composition or fix the component", blocking=True))
                if kind == "labor" and not ci["labor"] and not any(sc == "labor" for sc, _ in ci["issues"]):
                    errs.append(Missing("CREW_NO_LABOR", c["crew_id"], "the crew has no labor member", blocking=True))
            else:
                errs += cached[1]
            daily = None
            dinputs: list = []
            dflags: list = []
            dorigin = "observed"
            try:
                daily, dinputs, dflags, dorigin = self._daily_output(c, wi, ci, p)
            except Missing as m:
                errs.append(m)
            adj: list = []
            try:
                adj = self._adjust_factors(kind, p, applied)
            except Missing as m:
                errs.append(m)
            if errs or ci is None or daily is None:
                add_missing(c, errs)
                continue
            if kind == "labor":
                per_shift = ci["labor_per_shift"]
                members = ci["labor"]
                hours_per_shift = ci["person_hours_per_shift"]
                ins = [x for mem in members for x in ([_inp("crew_members", mem["member"]["crew_member_id"], "quantity x hours", f"{mem['qty']}x{mem['hrs']}", "HR",
                                                              "observed", trade=mem["member"]["trade_code"], rate_total_hr=str(mem["lr"]["total_hr"]),
                                                              rate_components={k: str(v) for k, v in mem["lr"]["components"].items()})] + mem["lr"]["inputs"])]
                mflags = [f for mem in members for f in mem["lr"]["flags"]] + ci["flags"]
                origin = ci["labor_origin"]
            else:
                members = [e for e in ci["equip"] if e["etype"] == c["equipment_type_code"]]
                per_shift = sum((e["cost"] for e in members), D(0))
                hours_per_shift = sum((e["qty"] * (e["hrs"] if e["er"]["basis"] != "day" else ci["shift"]) for e in members), D(0))
                ins = [x for e in members for x in ([_inp("crew_members", e["member"]["crew_member_id"], "quantity x hours", f"{e['qty']}x{e['hrs']}", "HR", "observed",
                                                            equipment_type=e["etype"], rate=str(e["er"]["rate"]), rate_basis=e["er"]["basis"])] + e["er"]["inputs"])]
                mflags = [f for e in members for f in e["er"]["flags"]] + ci["flags"]
                origin = "assumed" if any(e["er"]["origin"] == "assumed" for e in members) or ci["crew"]["origin"] == "assumed" else "observed"
            unit_cost = per_shift / daily
            hours_scale = D(1)
            for f in adj:
                unit_cost *= _d(f["factor_value"])
                if f["factor_type"] == "productivity_condition" and kind == "labor":
                    hours_scale *= _d(f["factor_value"])
            adj_note = "".join(f" x {f['factor_value']} [{f['factor_id']}]" for f in adj)
            hours_per_unit = hours_per_shift / daily * hours_scale
            ch = ci["shift"] / daily
            summary = "assumed" if (origin == "assumed" or dorigin == "assumed") else "observed"
            if summary == "assumed":
                any_assumed = True
            totals[kind] += q10(unit_cost)
            if kind == "labor":
                label = (f"person-hours/unit = sum(member qty x hours) {hours_per_shift} / {q10(daily)}"
                         f"{' x ' + str(hours_scale) if hours_scale != 1 else ''} = {q10(hours_per_unit)}; crew-hours/unit = {q10(ch)}")
                qk = "person_hours"
            else:
                label = f"equipment-hours/unit = sum(member qty x hours) {hours_per_shift} / {q10(daily)} = {q10(hours_per_unit)}; crew-hours/unit = {q10(ch)}"
                qk = "equipment_hours"
            formula = (f"crew {kind} cost/shift ${q10(per_shift)} / daily output {q10(daily)} {wi['output_unit_id']} = ${q10(unit_cost)}/{wi['output_unit_id']}{adj_note}; {label}")
            lines.append({"line_no": len(lines) + 1, "line_kind": kind, "component_ref": c["component_id"], "description": c["description"],
                          "quantity": q10(hours_per_unit), "quantity_unit_id": "HR", "quantity_kind": qk, "unit_cost": q10(unit_cost),
                          "extended_cost": q10(unit_cost), "formula": formula,
                          "inputs": ins + dinputs + [self._factor_input(f) for f in adj], "origin_summary": summary,
                          "warnings": sorted(set(dflags + mflags))})
        # a crew's equipment that no equipment component prices is under-costing: say so
        for cid, cached in crew_cache.items():
            if cached[0] != "ok":
                continue
            costed = {c["equipment_type_code"] for c in comps if c["component_kind"] == "equipment" and c["crew_id"] == cid}
            for e in cached[1]["equip"]:
                if e["etype"] not in costed:
                    warnings.append(f"CREW_EQUIPMENT_NOT_COSTED:{cid}:{e['etype']}")
        return self._finish("unit_cost", work_item_id, version, p, wi["output_unit_id"], lines, missing, warnings, totals, any_assumed, bases)

    # ------------------------------------------------------------------------------------------------ assembly
    def assembly_cost(self, assembly_id: str, version: int, p: RunParams) -> RunResult:
        self._refresh()
        applied: set = set()
        res = self._assembly_cost(assembly_id, version, p, applied)
        return self._require_conditions(res, p, applied)

    def _assembly_cost(self, assembly_id: str, version: int, p: RunParams, applied: set) -> RunResult:
        asm = self._asms.get((assembly_id, version))
        if asm is None:
            raise KeyError(f"assembly {assembly_id} v{version} not found")
        comps = sorted(self._asm_comps.get((assembly_id, version), []), key=lambda c: c["line_no"])
        lines: list[dict] = []
        missing: list[dict] = []
        warnings: list[str] = []
        children: list[RunResult] = []
        bases: set = set()
        totals = {"material": D(0), "labor": D(0), "equipment": D(0), "other_direct": D(0)}
        any_assumed = False
        for m in self._definition_issues(asm, "assembly", p):
            missing.append(_missing_info(m, assembly_id))
        if any(m["blocking"] for m in missing):
            return self._finish("assembly", assembly_id, version, p, asm["output_unit_id"], lines, missing, warnings, totals, any_assumed, bases)
        scope_owner: dict[str, str] = {}
        tag_owner: dict[str, str] = {}
        for c in comps:
            wi = self._wis[(c["work_item_id"], c["work_item_version"])]
            for t in wi["included_scope"] or []:
                if t in scope_owner and scope_owner[t] != wi["work_item_id"]:
                    missing.append(_missing_info(Missing("SCOPE_OVERLAP", f"scope '{t}'", f"claimed by both {scope_owner[t]} and {wi['work_item_id']}: double counting",
                                                         "remove the scope from one work item", blocking=True), c["assembly_component_id"]))
                scope_owner.setdefault(t, wi["work_item_id"])
            for t in c["cost_tags"] or []:
                if t in tag_owner and tag_owner[t] != c["assembly_component_id"]:
                    missing.append(_missing_info(Missing("DUPLICATE_COST_TAG", f"cost tag '{t}'", f"on {tag_owner[t]} and {c['assembly_component_id']}: double-counting suspicion",
                                                         "keep the tag on one component", blocking=True), c["assembly_component_id"]))
                tag_owner.setdefault(t, c["assembly_component_id"])
        for c in comps:
            wi = self._wis[(c["work_item_id"], c["work_item_version"])]
            try:
                mult = _frac(self.units.factor(c["qty_unit_id"], wi["output_unit_id"]))
            except UnitError as e:
                missing.append({"code": "ASSEMBLY_UNIT", "needed": c["assembly_component_id"], "reason": str(e), "how_to_fill": "fix qty_unit_id",
                                "component_ref": c["assembly_component_id"], "blocking": True})
                continue
            qty = _d(c["qty_per_assembly_unit"]) * mult
            child_p = replace(p, quantity=(p.quantity * qty) if p.quantity is not None else None)
            child = self._unit_cost(c["work_item_id"], c["work_item_version"], child_p, applied)
            children.append(child)
            bases.update(x for x in [child.run["price_basis"]] if x != "none")
            if child.status != "complete":
                for m in child.run["missing_inputs"]:
                    mm = dict(m)
                    mm["component_ref"] = f"{c['assembly_component_id']}>{m['component_ref']}"
                    missing.append(mm)
                lines.append({"line_no": len(lines) + 1, "line_kind": "assembly_component", "component_ref": c["assembly_component_id"],
                              "description": wi["name"], "quantity": q10(qty), "quantity_unit_id": wi["output_unit_id"], "quantity_kind": "work_item_qty",
                              "unit_cost": None, "extended_cost": None, "formula": f"child run {child.run['run_id']} is {child.status}",
                              "inputs": [_inp("calculation_runs", child.run["run_id"], "direct_cost_total", "", None, "derived")],
                              "origin_summary": "missing", "warnings": []})
                continue
            ext = qty * child.total
            for k, fn in (("material", "material_cost"), ("labor", "labor_cost"), ("equipment", "equipment_cost"), ("other_direct", "other_direct_cost")):
                totals[k] += q10(qty * _d(child.run[fn] or 0))
            if child.run["has_assumptions"]:
                any_assumed = True
            lines.append({"line_no": len(lines) + 1, "line_kind": "assembly_component", "component_ref": c["assembly_component_id"],
                          "description": wi["name"], "quantity": q10(qty), "quantity_unit_id": wi["output_unit_id"], "quantity_kind": "work_item_qty",
                          "unit_cost": child.total, "extended_cost": q10(ext),
                          "formula": f"{c['qty_formula']} = {qty} {wi['output_unit_id']} x unit cost ${child.total}/{wi['output_unit_id']} (run {child.run['run_id']})",
                          "inputs": [_inp("calculation_runs", child.run["run_id"], "direct_cost_total", child.total, None, "derived")],
                          "origin_summary": "assumed" if child.run["has_assumptions"] else "derived", "warnings": child.run["warnings"]})
        res = self._finish("assembly", assembly_id, version, p, asm["output_unit_id"], lines, missing, warnings, totals, any_assumed, bases)
        res.children = children
        return res

    # ---------------------------------------------------------------------------------------------------- finish
    @staticmethod
    def _flat_warnings(lines: list[dict], warnings: list[str]) -> list[str]:
        out = list(warnings)
        for ln in lines:
            for w in ln.get("warnings", []):
                if isinstance(w, str) and w not in out:
                    out.append(w)
        return out

    def _run_id(self, target_type, target_id, version, p: RunParams, lines: list[dict], missing: list[dict]) -> str:
        core = [{k: ln.get(k) for k in ("component_ref", "quantity", "quantity_unit_id", "unit_cost", "extended_cost", "formula", "inputs", "warnings")} for ln in lines]
        gaps = sorted((m["code"], m["component_ref"], m["needed"]) for m in missing)
        fp = hashlib.sha1(json.dumps([core, gaps], sort_keys=True, default=str).encode()).hexdigest()
        return make_id("RUN", target_type, target_id, version, p.canonical(), self.calc_version, fp, length=12)

    def _finish(self, target_type, target_id, version, p: RunParams, unit, lines, missing, warnings, totals, any_assumed, bases) -> RunResult:
        blocking = [m for m in missing if m["blocking"]]
        priced = [ln for ln in lines if ln.get("extended_cost") is not None]
        if not missing and not priced:
            missing = missing + [_missing_info(Missing("NO_COST_LINES", f"{target_type} {target_id}", "the definition produced no priced line (all components optional or none defined)",
                                                       "define components or pass include_optional=True"), target_id)]
        status = "failed" if blocking else ("incomplete" if missing else "complete")
        if p.mode == "strict" and any_assumed:
            status = "failed"
            warnings = warnings + ["ASSUMED_INPUT_LEAKED_INTO_STRICT_RUN"]
        complete = status == "complete"
        material, labor, equip, other = (q6(totals[k]) for k in ("material", "labor", "equipment", "other_direct"))
        direct = q6(sum(totals.values(), D(0)))
        for i, ln in enumerate(lines, 1):
            ln["line_no"] = i
        run_id = self._run_id(target_type, target_id, version, p, lines, missing)
        run_at = p.run_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        run = {"run_id": run_id, "run_at": run_at, "calc_version": self.calc_version, "target_type": target_type, "target_id": target_id,
               "target_version": version, "mode": p.mode, "parameters": json.loads(p.canonical()), "status": status,
               "has_assumptions": bool(any_assumed), "result_unit_id": unit,
               "material_cost": material if complete else None, "labor_cost": labor if complete else None,
               "equipment_cost": equip if complete else None, "other_direct_cost": other if complete else None,
               "direct_cost_total": direct if complete else None, "missing_inputs": missing, "warnings": self._flat_warnings(lines, warnings),
               "code_ref": self.code_ref, "price_basis": _combine_basis(bases), "input_review_floor": p.min_review, "price_total": None,
               "origin": "derived", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "notes": None}
        for ln in lines:
            ln["run_id"] = run_id
        return RunResult(run=run, lines=lines)

    # ------------------------------------------------------------------------------------------ loaded labor rate
    def loaded_labor_rate(self, trade: str, p: RunParams) -> RunResult:
        """Derived labor_rates row (rate_type=loaded_employer_cost) with every component traceable."""
        self._refresh()
        missing, lines, warnings = [], [], []
        totals = {"material": D(0), "labor": D(0), "equipment": D(0), "other_direct": D(0)}
        derived: dict[str, list[dict]] = {}
        lr = None
        try:
            lr = self._labor_rate(trade, p)
        except MultiMissing as mm:
            missing += [_missing_info(m, trade) for m in mm.items]
        except Missing as m:
            missing.append(_missing_info(m, trade))
        any_assumed = False
        if lr:
            any_assumed = lr["origin"] == "assumed"
            for n, (k, v) in enumerate(lr["components"].items(), 1):
                lines.append({"line_no": n, "line_kind": "labor", "component_ref": trade, "description": k, "quantity": D(1), "quantity_unit_id": "HR",
                              "quantity_kind": "person_hours", "unit_cost": q10(v), "extended_cost": q10(v), "formula": f"{k} per paid hour",
                              "inputs": lr["inputs"] if n == 1 else [], "origin_summary": "assumed" if lr["origin"] == "assumed" else "observed",
                              "warnings": lr["flags"] if n == 1 else []})
            totals["labor"] = lr["total_hr"]
            warnings += lr["flags"]
        res = self._finish("labor_loaded", trade, None, p, "HR", lines, missing, warnings, totals, any_assumed, set())
        if lr and res.status == "complete":
            comps = lr["components"]
            gov = lr["governing"]
            payroll = sum((v for k, v in comps.items() if k in BASE_PAYROLL_TYPES + tuple(t for ts in STATE_PAYROLL_EXTRA.values() for t in ts)), D(0)) + \
                comps.get("payroll_tax_in_source", D(0))
            rid = make_id("LRT", trade, gov["region_id"], gov["effective_from"].isoformat(), res.run["run_id"], length=10)
            derived["labor_rates"] = [{
                "labor_rate_id": rid, "rate_type": "loaded_employer_cost", "trade_code": trade,
                "classification_raw": f"Loaded employer cost for {trade} ({p.labor_basis})", "soc_code": None, "statistic": "n/a",
                "region_id": gov["region_id"], "base_wage_hr": q10(comps["base_wage"]) if "base_wage" in comps else None,
                "fringe_hr": q10(comps.get("fringe_in_source", D(0)) + comps.get("employer_benefits", D(0))), "fringe_breakdown": None,
                "payroll_tax_hr": q10(payroll), "workers_comp_hr": q10(comps.get("workers_comp", D(0)) + comps.get("workers_comp_in_source", D(0))),
                "other_employer_cost_hr": q10(comps.get("other_employer_cost", D(0))), "total_hr": q10(lr["total_hr"]),
                "includes_fringe": True, "includes_payroll_taxes": True, "includes_workers_comp": True, "includes_overhead": False,
                "includes_profit": False, "wage_basis": "straight_time", "project_type": p.wage_class if p.wage_class != "n/a" else "n/a",
                "use_context": "employer_internal", "apprentice": False, "determination_ref": None, "effective_from": gov["effective_from"],
                "effective_to": gov["effective_to"], "retrieved_at": None, "derived_from": [i["id"] for i in lr["inputs"]],
                "calc_run_id": res.run["run_id"], "source_id": None, "source_locator": None, "evidence_excerpt": None, "raw_file_sha256": None,
                "origin": "derived", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None, "created_at": None,
                "notes": f"derived by costdb.calc.loaded_labor_rate; region/period are those of the governing wage record (burden inputs may cover other periods); flags: {', '.join(lr['flags']) or 'none'}"}]
        res.derived_rows = derived
        return res


# ------------------------------------------------------------------------------------------ markup / margin
def markup_to_margin(m: Decimal) -> Decimal:
    """margin g = m / (1 + m)"""
    return m / (1 + m)


def margin_to_markup(g: Decimal) -> Decimal:
    """markup m = g / (1 - g)"""
    if g >= 1:
        raise ValueError("margin must be < 1")
    return g / (1 - g)


def _fraction_param(name: str, v: Any, hi: Decimal = D(1), hi_inclusive: bool = True) -> Decimal:
    try:
        v = _d(v)
    except Exception:
        raise ValueError(f"{name} must be a number") from None
    if v < 0 or v > hi or (v == hi and not hi_inclusive):
        raise ValueError(f"{name}={v} is outside [0, {hi}{']' if hi_inclusive else ')'}; percentages are fractions (0.10 means 10%)")
    return v


def apply_markup(base: RunResult, *, overhead_pct: Decimal, overhead_basis: str, contingency_pct: Decimal,
                 contingency_basis: str, profit_method: str, profit_value: Decimal, profit_basis: str,
                 run_at: Optional[str] = None, calc_version: str = CALC_VERSION) -> RunResult:
    """Show overhead, contingency and profit SEPARATELY on top of direct cost.

      overhead     = direct x oh
      contingency  = (direct + overhead) x ct
      cost         = direct + overhead + contingency
      profit_markup: price = cost x (1 + m)        profit_margin: price = cost / (1 - g)
    No default percentages exist: each must be passed with a stated basis. The base run's direct cost stays in
    direct_cost_total; the price goes to price_total."""
    for name, basis in (("overhead", overhead_basis), ("contingency", contingency_basis), ("profit", profit_basis)):
        if not basis or not basis.strip():
            raise ValueError(f"{name} percentage needs a stated basis (no universal default)")
    if base.run["target_type"] == "markup":
        raise ValueError("markup cannot be applied to a markup run")
    if base.run["status"] != "complete" or base.total is None:
        raise ValueError("cannot apply markup to an incomplete/failed run")
    if profit_method not in ("markup", "margin"):
        raise ValueError("profit_method must be 'markup' or 'margin'")
    overhead_pct = _fraction_param("overhead_pct", overhead_pct)
    contingency_pct = _fraction_param("contingency_pct", contingency_pct)
    profit_value = _fraction_param("profit_value", profit_value, hi=D(1), hi_inclusive=(profit_method == "markup"))
    direct = _d(base.total)
    overhead = direct * overhead_pct
    cont = (direct + overhead) * contingency_pct
    cost = direct + overhead + cont
    if profit_method == "markup":
        price = cost * (1 + profit_value)
        pformula = f"price = cost x (1 + markup {profit_value})"
    else:
        price = cost / (1 - profit_value)
        pformula = f"price = cost / (1 - margin {profit_value})"
    profit = price - cost
    base_in = _inp("calculation_runs", base.run["run_id"], "direct_cost_total", direct, None, "derived")
    rows = [
        ("subtotal", "Direct cost", direct, f"direct cost from run {base.run['run_id']}", "derived"),
        ("overhead", f"Overhead ({overhead_pct}) - {overhead_basis}", overhead, f"{direct} x {overhead_pct}", "assumed"),
        ("contingency", f"Contingency ({contingency_pct}) - {contingency_basis}", cont, f"({direct} + {q10(overhead)}) x {contingency_pct}", "assumed"),
        ("subtotal", "Cost incl. overhead and contingency", cost, "direct + overhead + contingency", "derived"),
        ("profit", f"Profit by {profit_method} {profit_value} - {profit_basis}", profit, pformula, "assumed"),
        ("subtotal", "Price", price, "cost + profit", "derived"),
    ]
    params = {"overhead_pct": str(overhead_pct), "overhead_basis": overhead_basis, "contingency_pct": str(contingency_pct),
              "contingency_basis": contingency_basis, "profit_method": profit_method, "profit_value": str(profit_value), "profit_basis": profit_basis}
    fp = hashlib.sha1(json.dumps([str(direct), params, [ln["extended_cost"] and str(ln["extended_cost"]) for ln in base.lines]], sort_keys=True).encode()).hexdigest()
    run_id = make_id("RUN", "markup", base.run["run_id"], fp, calc_version, length=12)
    lines = [{"run_id": run_id, "line_no": i, "line_kind": k, "component_ref": None, "description": d, "quantity": None, "quantity_unit_id": None,
              "quantity_kind": "none", "unit_cost": None, "extended_cost": q10(v), "formula": f, "inputs": [base_in], "origin_summary": o, "warnings": []}
             for i, (k, d, v, f, o) in enumerate(rows, 1)]
    run = {"run_id": run_id, "run_at": run_at or datetime.now(timezone.utc).isoformat(timespec="seconds"), "calc_version": calc_version,
           "target_type": "markup", "target_id": base.run["run_id"], "target_version": None, "mode": "with_assumptions", "parameters": params,
           "status": "complete", "has_assumptions": True, "result_unit_id": base.run["result_unit_id"],
           "material_cost": base.run["material_cost"], "labor_cost": base.run["labor_cost"], "equipment_cost": base.run["equipment_cost"],
           "other_direct_cost": base.run["other_direct_cost"], "direct_cost_total": base.run["direct_cost_total"], "missing_inputs": [],
           "warnings": ["MARKUP_PERCENTAGES_ARE_POLICY_INPUTS"] + [w for w in base.run["warnings"] if w not in ("MARKUP_PERCENTAGES_ARE_POLICY_INPUTS",)],
           "code_ref": base.run.get("code_ref"), "price_basis": base.run["price_basis"], "input_review_floor": base.run["input_review_floor"],
           "price_total": q6(price), "origin": "derived", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
           "notes": f"price shown separately from direct cost; direct={q6(direct)} overhead={q6(overhead)} contingency={q6(cont)} profit={q6(profit)}"}
    return RunResult(run=run, lines=lines, children=[base])
