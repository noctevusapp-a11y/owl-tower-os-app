"""Calculation engine: unit costs, assemblies, loaded labor rates, markup/margin.

Principles (docs/methodology.md):
  * A result is only produced when EVERY required input resolves to a usable record.
    Otherwise the run is status='incomplete' with an explicit missing_inputs list and NO total.
  * strict mode: only observed/derived records whose review_status is acceptable (default: validated).
    with_assumptions mode: approved rows of the assumptions table may fill gaps; the run is flagged.
  * flagged/rejected records are never used.
  * Every cost line stores quantity, unit, unit cost, formula text and the exact input record ids.
  * Same data + same parameters + same calc version => same run_id (deterministic, reproducible).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from . import CALC_VERSION
from .ids import make_id
from .store import Database
from .units import Units, UnitError

D = Decimal
Q10 = D("0.0000000001")
Q6 = D("0.000001")

RETAIL_CHANNELS = {"retail_public", "retail_promo"}
DEFAULT_CHANNELS = ("retail_public", "public_price_list", "supplier_quote", "pro_account_quote", "distributor_quote")
BURDEN_PAYROLL_TAX_TYPES = ("fica_social_security", "fica_medicare", "futa", "state_ui", "state_ett")


def _d(x: Any) -> Decimal:
    return x if isinstance(x, Decimal) else D(str(x))


def q10(x: Decimal) -> Decimal:
    return x.quantize(Q10, rounding=ROUND_HALF_UP)


def q6(x: Decimal) -> Decimal:
    return x.quantize(Q6, rounding=ROUND_HALF_UP)


def median(vals: list[Decimal]) -> Decimal:
    s = sorted(vals)
    n = len(s)
    if n == 0:
        raise ValueError("median of empty list")
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


@dataclass
class RunParams:
    region_id: str
    as_of: date
    mode: str = "strict"                        # strict | with_assumptions
    min_review: str = "validated"               # validated | unreviewed
    price_policy: str = "median_of_latest_per_product"
    channels: tuple[str, ...] = DEFAULT_CHANNELS
    max_price_age_days: Optional[int] = 365
    time_index_id: Optional[str] = None          # index series used to bring OLD prices to as_of
    use_region_factors: bool = False             # allow prices from other regions + explicit region factor
    allow_ancestor_region_prices: bool = False
    labor_basis: str = "stat_loaded"             # stat_loaded | prevailing_loaded | company_actual
    labor_statistic: str = "mean"
    project_type: str = "private"                # private | public_works
    burden_base: str = "base_wage"               # base_wage | wage_plus_fringe
    annual_paid_hours: Optional[Decimal] = None  # needed when a burden has an annual wage cap
    max_rate_age_days: Optional[int] = 800
    equipment_basis: str = "hourly"              # hourly | rental_day
    conditions: tuple[str, ...] = ()
    quantity: Optional[Decimal] = None
    allow_synthetic: bool = False                # test fixtures only
    run_at: Optional[str] = None                 # fix for reproducible example output

    def canonical(self) -> str:
        def enc(o):
            if isinstance(o, (Decimal,)):
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
        for k in ("annual_paid_hours", "quantity"):
            if d.get(k) is not None:
                d[k] = D(d[k])
        d["channels"] = tuple(d["channels"])
        d["conditions"] = tuple(d["conditions"])
        return cls(run_at=run_at, **d)


class MultiMissing(Exception):
    """Several independent inputs of ONE component are unresolved; all are reported, none is hidden behind another."""

    def __init__(self, items: list):
        super().__init__("; ".join(str(i) for i in items))
        self.items = items


class Missing(Exception):
    """Raised while pricing one component when an input cannot be resolved honestly."""

    def __init__(self, code: str, needed: str, reason: str, hint: str = "", blocking: bool = False):
        super().__init__(f"{code}: {needed} — {reason}")
        self.info = {"code": code, "needed": needed, "reason": reason, "how_to_fill": hint}
        self.blocking = blocking


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
        return self.run.get("direct_cost_total")


class Engine:
    def __init__(self, db: Database, calc_version: str = CALC_VERSION, code_ref: Optional[str] = None):
        self.db = db
        self.units = Units(db["units"])
        self.calc_version = calc_version
        self.code_ref = code_ref
        self._regions = db.index("regions", "region_id")
        self._sources = db.index("sources", "source_id")
        self._products = db.index("products", "product_id")
        self._crews = db.index("crews", "crew_id")
        self._equip_types = db.index("equipment_types", "equipment_type_code")
        self._prod_obs = db.index("productivity_observations", "productivity_id")

    # ------------------------------------------------------------- helpers
    def _region_chain(self, region_id: str) -> list[str]:
        chain, seen = [], set()
        cur: Optional[str] = region_id
        while cur and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            row = self._regions.get(cur)
            cur = row["parent_region_id"] if row else None
        return chain

    def _region_rank(self, row_region: Optional[str], target: str) -> Optional[int]:
        """0 = same/descendant region, n>0 = n-th ancestor of target, None = unrelated."""
        if row_region is None:
            return None
        if target in self._region_chain(row_region):
            return 0
        chain = self._region_chain(target)
        if row_region in chain:
            return chain.index(row_region)
        return None

    def _rank_up(self, row_region: Optional[str], target: str) -> Optional[int]:
        """Rate/burden regions: 0 = exact region, n = n-th ancestor of the target. A rate for a SMALLER area is never
        stretched over a larger one, and an unrelated region is never used."""
        if row_region is None:
            return 99                     # nationwide item with no region: least specific
        chain = self._region_chain(target)
        return chain.index(row_region) if row_region in chain else None

    def _usable(self, row: dict, p: RunParams) -> bool:
        if row.get("review_status") in ("flagged", "rejected"):
            return False
        if p.min_review == "validated" and row.get("review_status") != "validated":
            return False
        sid = row.get("source_id")
        if sid and sid in self._sources:
            src = self._sources[sid]
            if src["reuse_status"] == "prohibited":
                return False
            if src["verification_method"] == "synthetic_test_fixture" and not p.allow_synthetic:
                return False
        return True

    def _in_period(self, row: dict, as_of: date) -> bool:
        if row["effective_from"] > as_of:
            return False
        return row.get("effective_to") is None or row["effective_to"] >= as_of

    def _approved_assumption(self, ref: str, p: RunParams) -> Optional[dict]:
        if p.mode != "with_assumptions":
            return None
        for a in self.db["assumptions"]:
            if a["applies_to_ref"] == ref and a["status"] == "approved":
                if a.get("expires_on") and a["expires_on"] < p.as_of:
                    continue
                return a
        return None

    def _index_value(self, index_id: str, d: date, p: RunParams) -> tuple[Decimal, dict]:
        idx = self.db.index("indices", "index_id").get(index_id)
        if not idx:
            raise Missing("INDEX_UNKNOWN", f"index {index_id}", "index series not in indices table")
        if idx["frequency"] == "monthly":
            start = date(d.year, d.month, 1)
        elif idx["frequency"] == "quarterly":
            start = date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
        else:
            start = date(d.year, 1, 1)
        cands = [v for v in self.db["index_values"]
                 if v["index_id"] == index_id and v["period_start"] == start and v["vintage_date"] <= p.as_of
                 and v.get("review_status") not in ("flagged", "rejected")
                 and (p.min_review == "unreviewed" or v.get("review_status") == "validated")]
        if not cands:
            raise Missing("INDEX_VALUE_MISSING", f"{index_id} value for {start.isoformat()}",
                          "no usable index value (validated, vintage <= as_of)", "capture index series values")
        v = sorted(cands, key=lambda r: r["vintage_date"])[-1]
        return _d(v["value"]), {"index_id": index_id, "period_start": start.isoformat(),
                                "vintage_date": v["vintage_date"].isoformat(), "value_status": v["value_status"]}

    # ------------------------------------------------------ material pricing
    def _material_unit_price(self, comp: dict, p: RunParams, qty_unit: str, kind: str):
        """Return (price per qty_unit, inputs, flags, origin_summary)."""
        if comp.get("product_id"):
            pid = comp["product_id"]
            if pid not in self._products:
                raise Missing("PRODUCT_UNKNOWN", pid, "pinned product not in products table")
            key = self._products[pid]["spec_key"]
            prods = [self._products[pid]]
        else:
            key = comp["product_spec_key"]
            prods = [r for r in self.db["products"] if r["spec_key"] == key and r.get("review_status") != "rejected"]
        flags: list[str] = []
        picked: list[tuple[dict, Decimal, dict]] = []   # (obs, price per qty unit, adjustments)
        reasons: list[str] = []
        for prod in prods:
            best = None
            for o in self.db["price_observations"]:
                if o["product_id"] != prod["product_id"] or not self._usable(o, p):
                    continue
                if o["observed_at"] > p.as_of or o["price_channel"] not in p.channels or o["promo_flag"]:
                    continue
                if p.quantity is not None and o.get("qty_tier_min") is not None and _d(o["qty_tier_min"]) > p.quantity:
                    continue
                rank = self._region_rank(o.get("region_id"), p.region_id)
                adjustments: dict[str, Any] = {}
                if rank is None or (rank != 0 and not p.allow_ancestor_region_prices):
                    if not p.use_region_factors or o.get("region_id") is None:
                        reasons.append(f"{o['observation_id']}: region {o.get('region_id')} not within {p.region_id}")
                        continue
                    f = self._region_factor(o["region_id"], p.region_id, kind, p)
                    if f is None:
                        reasons.append(f"{o['observation_id']}: no usable region factor {o['region_id']}->{p.region_id}")
                        continue
                    adjustments["region_factor"] = f
                age = (p.as_of - o["observed_at"]).days
                if p.max_price_age_days is not None and age > p.max_price_age_days:
                    if p.time_index_id is None:
                        reasons.append(f"{o['observation_id']}: {age} days old, no time index supplied")
                        continue
                    try:
                        i_now, m_now = self._index_value(p.time_index_id, p.as_of, p)
                        i_then, m_then = self._index_value(p.time_index_id, o["observed_at"], p)
                    except Missing as m:
                        reasons.append(f"{o['observation_id']}: {m.info['code']}")
                        continue
                    adjustments["time_index"] = {"index_id": p.time_index_id, "from_date": o["observed_at"].isoformat(),
                                                 "to_date": p.as_of.isoformat(), "index_from": str(i_then),
                                                 "index_to": str(i_now), "vintage_from": m_then["vintage_date"],
                                                 "vintage_to": m_now["vintage_date"], "factor": i_now / i_then,
                                                 "formula": "price_to = price_from * index_to / index_from"}
                key_sort = (o["observed_at"], str(o["retrieved_at"]))
                if best is None or key_sort > best[0]:
                    best = (key_sort, o, adjustments)
            if best:
                _, o, adjustments = best
                per_content = _d(o["price_amount"]) / _d(o["pack_content_qty"])
                try:
                    m = self.units.factor(o["pack_content_unit_id"], qty_unit)
                except UnitError as e:
                    reasons.append(f"{o['observation_id']}: unit mismatch ({e})")
                    continue
                price = per_content / (D(m.numerator) / D(m.denominator))
                if "region_factor" in adjustments:
                    price *= _d(adjustments["region_factor"]["factor_value"])
                if "time_index" in adjustments:
                    price *= adjustments["time_index"]["factor"]
                picked.append((o, price, adjustments))
        if not picked:
            a = self._approved_assumption(f"price:{key}", p)
            if a is not None:
                if a["unit_id"] is None or not self.units.compatible(a["unit_id"], qty_unit):
                    raise Missing("ASSUMPTION_UNIT", f"price:{key}", "approved assumption has no compatible unit")
                m = self.units.factor(a["unit_id"], qty_unit)
                price = _d(a["value_numeric"]) / (D(m.numerator) / D(m.denominator))
                return price, [{"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                                "value": str(a["value_numeric"]), "unit": a["unit_id"], "origin": "assumed"}], \
                    ["ASSUMED_PRICE"], "assumed"
            raise Missing("PRICE_MISSING", f"validated price observation for spec {key}",
                          "; ".join(reasons[:3]) if reasons else "no observation exists",
                          f"capture price for spec_key {key} in {p.region_id} (templates/price_capture_template.csv)")
        prices = [x[1] for x in picked]
        price = median(prices) if p.price_policy == "median_of_latest_per_product" else prices[0]
        inputs = []
        for o, pr, adj in picked:
            inp = {"table": "price_observations", "id": o["observation_id"], "field": "price_amount/pack_content_qty",
                   "value": str(_d(o["price_amount"]) / _d(o["pack_content_qty"])), "unit": o["pack_content_unit_id"],
                   "observed_at": o["observed_at"].isoformat(), "price_channel": o["price_channel"],
                   "review_status": o["review_status"], "origin": "observed", "price_per_qty_unit": str(pr)}
            if adj:
                inp["adjustments"] = json.loads(json.dumps(adj, default=str))
            inputs.append(inp)
            if o["price_channel"] in RETAIL_CHANNELS or (o["price_channel"] == "retail_public"):
                flags.append("RETAIL_PRICE_NOT_CONTRACTOR_COST")
            if o.get("sales_tax_included") is not False:
                flags.append("SALES_TAX_UNKNOWN_OR_INCLUDED")
            if o.get("delivery_included") is not False:
                flags.append("DELIVERY_UNKNOWN_OR_INCLUDED")
            if "time_index" in adj:
                flags.append("TIME_INDEXED_PRICE")
            if "region_factor" in adj:
                flags.append("REGION_FACTOR_APPLIED")
        if len(picked) > 1:
            flags.append(f"MEDIAN_OF_{len(picked)}_PRODUCTS")
        return price, inputs, sorted(set(flags)), "observed"

    def _region_factor(self, from_region: str, to_region: str, kind: str, p: RunParams) -> Optional[dict]:
        for f in self.db["adjustment_factors"]:
            if f["factor_type"] != "region" or f["applies_to"] != kind:
                continue
            if f["from_region_id"] != from_region or f["to_region_id"] != to_region:
                continue
            if f.get("review_status") in ("flagged", "rejected"):
                continue
            if p.min_review == "validated" and f.get("review_status") != "validated":
                continue
            if f["origin"] == "assumed" and p.mode != "with_assumptions":
                continue
            if (f.get("valid_from") and f["valid_from"] > p.as_of) or (f.get("valid_to") and f["valid_to"] < p.as_of):
                continue
            return f
        return None

    # ------------------------------------------------------------- labor rate
    def _burden_rows(self, btype: str, trade: str, p: RunParams) -> Optional[dict]:
        best = None
        for b in self.db["burden_rates"]:
            if b["burden_type"] != btype or b["origin"] != "observed" or not self._usable(b, p):
                continue
            if b.get("trade_code") not in (None, trade) or not self._in_period(b, p.as_of):
                continue
            rank = self._rank_up(b.get("region_id"), p.region_id)
            if rank is None:
                continue
            score = (0 if b.get("trade_code") == trade else 1, rank)
            if best is None or score < best[0]:
                best = (score, b)
        return best[1] if best else None

    def _burden_hourly(self, b: dict, base_hr: Decimal, wages_hr: Decimal, p: RunParams) -> Decimal:
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

    def labor_rate(self, trade: str, p: RunParams) -> dict:
        """Loaded employer cost per paid hour for a trade, built from separately sourced components."""
        basis = p.labor_basis
        if basis == "prevailing_loaded" and p.project_type != "public_works":
            raise Missing("PW_NOT_APPLICABLE", f"prevailing wage for {trade}",
                          "prevailing/federal wage rates apply to public works only; this run is project_type='private'",
                          "use labor_basis='stat_loaded' or 'company_actual' for private projects", blocking=True)
        want_types = {"stat_loaded": ("stat_wage",), "prevailing_loaded": ("prevailing_wage", "federal_wage_determination"),
                      "company_actual": ("company_actual",)}[basis]
        best = None
        for r in self.db["labor_rates"]:
            if r["trade_code"] != trade or r["rate_type"] not in want_types or r["origin"] != "observed":
                continue
            if not self._usable(r, p) or not self._in_period(r, p.as_of):
                continue
            if basis == "stat_loaded" and r["statistic"] != p.labor_statistic:
                continue
            rank = self._rank_up(r["region_id"], p.region_id)
            if rank is None:
                continue
            if best is None or rank < best[0] or (rank == best[0] and r["effective_from"] > best[1]["effective_from"]):
                best = (rank, r)
        if best is None:
            a = self._approved_assumption(f"labor_rate:{trade}:{p.region_id}", p)
            if a is not None:
                return {"total_hr": _d(a["value_numeric"]), "components": {"assumed_total": _d(a["value_numeric"])},
                        "inputs": [{"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                                    "value": str(a["value_numeric"]), "unit": "HR", "origin": "assumed"}],
                        "flags": ["ASSUMED_LABOR_RATE"], "origin": "assumed"}
            raise Missing("LABOR_RATE_MISSING", f"{basis} rate for {trade} in {p.region_id}",
                          f"no usable {'/'.join(want_types)} record (origin=observed, review>={p.min_review})",
                          f"capture {'OEWS/DIR/SAM' if basis != 'company_actual' else 'company payroll'} rate for {trade}")
        rank, rec = best
        flags: list[str] = []
        if rank:
            flags.append(f"RATE_FROM_ANCESTOR_REGION:{rec['region_id']}")
        if p.max_rate_age_days is not None and (p.as_of - rec["effective_from"]).days > p.max_rate_age_days:
            flags.append("STALE_RATE")
        inputs = [{"table": "labor_rates", "id": rec["labor_rate_id"], "field": "base_wage_hr/fringe_hr/total_hr",
                   "value": str(rec["base_wage_hr"]), "unit": "HR", "origin": "observed",
                   "review_status": rec["review_status"], "rate_type": rec["rate_type"], "statistic": rec["statistic"]}]
        base = _d(rec["base_wage_hr"])
        comps: dict[str, Decimal] = {"base_wage": base}
        fringe_included = bool(rec["includes_fringe"])
        if basis == "company_actual":
            if rec.get("total_hr") is None:
                raise Missing("COMPANY_TOTAL_MISSING", f"total_hr for {rec['labor_rate_id']}", "company_actual rate needs total_hr")
            return {"total_hr": _d(rec["total_hr"]), "components": {"company_actual_total": _d(rec["total_hr"])},
                    "inputs": inputs, "flags": flags, "origin": "observed"}
        if fringe_included:
            if rec.get("fringe_hr") is None:
                raise Missing("FRINGE_MISSING", f"fringe_hr for {rec['labor_rate_id']}", "record says it includes fringe but has none")
            comps["fringe_in_source"] = _d(rec["fringe_hr"])
        wages_for_pct = base + (comps.get("fringe_in_source", D(0)) if p.burden_base == "wage_plus_fringe" else D(0))
        # What still has to be added? only components the source rate does NOT already include.
        add_benefits = not fringe_included
        add_taxes = not rec["includes_payroll_taxes"]
        add_wc = not rec["includes_workers_comp"]
        origin = "observed"
        if add_benefits:
            b = self._burden_rows("employer_benefits", trade, p)
            if b is None:
                a = self._approved_assumption(f"burden:employer_benefits:{trade}", p)
                if a is None:
                    raise Missing("BENEFITS_MISSING", f"employer benefits for {trade}",
                                  "source wage excludes employer-paid benefits and no benefits rate (burden_rates/assumption) exists",
                                  "capture ECEC-based ratio or company benefit cost")
                comps["employer_benefits"] = _d(a["value_numeric"]) * wages_for_pct if a["unit_id"] is None else _d(a["value_numeric"])
                inputs.append({"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                               "value": str(a["value_numeric"]), "unit": "fraction_of_wages", "origin": "assumed"})
                flags.append("ASSUMED_BENEFITS"); origin = "assumed"
            else:
                comps["employer_benefits"] = self._burden_hourly(b, base, wages_for_pct, p)
                inputs.append({"table": "burden_rates", "id": b["burden_id"], "field": "rate", "value": str(b["rate"]),
                               "unit": b["basis"], "origin": "observed", "review_status": b["review_status"]})
        if add_taxes:
            for t in BURDEN_PAYROLL_TAX_TYPES:
                b = self._burden_rows(t, trade, p)
                if b is None:
                    raise Missing("PAYROLL_TAX_MISSING", f"{t} rate for {p.region_id}", "no usable burden_rates record",
                                  f"capture {t} (IRS/EDD)")
                comps[t] = self._burden_hourly(b, base, wages_for_pct, p)
                inputs.append({"table": "burden_rates", "id": b["burden_id"], "field": "rate", "value": str(b["rate"]),
                               "unit": b["basis"], "origin": "observed", "review_status": b["review_status"]})
        if add_wc:
            b = self._burden_rows("workers_comp", trade, p)
            if b is None:
                a = self._approved_assumption(f"burden:workers_comp:{trade}", p)
                if a is None:
                    raise Missing("WORKERS_COMP_MISSING", f"workers' comp rate for {trade}",
                                  "no usable burden_rates record; actual premium is company/insurer specific",
                                  "enter insurer-quoted rate or WCIRB-based figure with source")
                comps["workers_comp"] = _d(a["value_numeric"]) * wages_for_pct
                inputs.append({"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                               "value": str(a["value_numeric"]), "unit": "fraction_of_wages", "origin": "assumed"})
                flags.append("ASSUMED_WORKERS_COMP"); origin = "assumed"
            else:
                comps["workers_comp"] = self._burden_hourly(b, base, wages_for_pct, p)
                inputs.append({"table": "burden_rates", "id": b["burden_id"], "field": "rate", "value": str(b["rate"]),
                               "unit": b["basis"], "origin": "observed", "review_status": b["review_status"]})
        total = sum(comps.values(), D(0))
        return {"total_hr": total, "components": comps, "inputs": inputs, "flags": flags, "origin": origin}

    def _equipment_rate(self, etype: str, p: RunParams) -> dict:
        best = None
        for r in self.db["equipment_rates"]:
            if r["equipment_type_code"] != etype or r["origin"] != "observed" or not self._usable(r, p):
                continue
            if not self._in_period(r, p.as_of):
                continue
            rank = self._rank_up(r["region_id"], p.region_id)
            if rank is None:
                continue
            if best is None or rank < best[0] or (rank == best[0] and r["effective_from"] > best[1]["effective_from"]):
                best = (rank, r)
        if best is None:
            a = self._approved_assumption(f"equipment_rate:{etype}:{p.region_id}", p)
            if a is not None:
                return {"basis": "hourly", "rate": _d(a["value_numeric"]), "operator_included": False,
                        "inputs": [{"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                                    "value": str(a["value_numeric"]), "unit": "HR", "origin": "assumed"}],
                        "flags": ["ASSUMED_EQUIPMENT_RATE"], "origin": "assumed"}
            raise Missing("EQUIPMENT_RATE_MISSING", f"{etype} rate in {p.region_id}", "no usable equipment_rates record",
                          f"capture rental/owned rate for {etype}")
        rank, r = best
        flags = ["EQUIPMENT_DELIVERY_AND_MOBILIZATION_EXCLUDED"]
        if rank:
            flags.append(f"RATE_FROM_ANCESTOR_REGION:{r['region_id']}")
        if r["fuel_included"] is False and r.get("fuel_cost_hr") is None:
            flags.append("FUEL_NOT_PRICED")
        inp = [{"table": "equipment_rates", "id": r["equipment_rate_id"], "field": "rate", "value": "", "unit": "HR",
                "origin": "observed", "review_status": r["review_status"], "operator_included": r["operator_included"]}]
        if p.equipment_basis == "rental_day":
            if r["rental_rate_day"] is None:
                raise Missing("EQUIPMENT_DAY_RATE_MISSING", f"day rate for {etype}", "record has no rental_rate_day")
            inp[0]["field"] = "rental_rate_day"; inp[0]["value"] = str(r["rental_rate_day"]); inp[0]["unit"] = "DAY"
            return {"basis": "day", "rate": _d(r["rental_rate_day"]), "operator_included": r["operator_included"],
                    "inputs": inp, "flags": flags, "origin": "observed"}
        if r["rental_rate_hr"] is not None:
            rate = _d(r["rental_rate_hr"]); inp[0]["field"] = "rental_rate_hr"
        elif r["ownership_cost_hr"] is not None and r["operating_cost_hr"] is not None:
            rate = _d(r["ownership_cost_hr"]) + _d(r["operating_cost_hr"]); inp[0]["field"] = "ownership_cost_hr+operating_cost_hr"
            if r["fuel_cost_hr"] is not None and r["fuel_included"]:
                flags.append("CHECK_FUEL_NOT_DOUBLE_COUNTED")
        else:
            raise Missing("EQUIPMENT_HOURLY_BASIS_MISSING", f"hourly basis for {etype}",
                          "need rental_rate_hr or ownership+operating hourly components")
        inp[0]["value"] = str(rate)
        return {"basis": "hour", "rate": rate, "operator_included": r["operator_included"], "inputs": inp,
                "flags": flags, "origin": "observed"}

    # ------------------------------------------------------- crew & productivity
    def _crew_costs(self, comp: dict, wi: dict, p: RunParams) -> dict:
        crew = self._crews.get(comp["crew_id"])
        if crew is None:
            raise Missing("CREW_UNKNOWN", comp["crew_id"], "crew not in crews table")
        if crew["origin"] == "missing":
            raise Missing("CREW_MISSING", f"composition of {crew['crew_id']}", "crew composition not found in any source",
                          "capture crew composition")
        if crew["origin"] == "assumed" and p.mode != "with_assumptions":
            raise Missing("CREW_ASSUMED", f"composition of {crew['crew_id']}",
                          "crew composition is an assumption; strict mode does not accept it", "run with_assumptions or source it")
        shift = _d(crew["shift_hours"])
        members = [m for m in self.db["crew_members"] if m["crew_id"] == crew["crew_id"]]
        if not members:
            raise Missing("CREW_EMPTY", crew["crew_id"], "crew has no members")
        labor_cost = D(0); equip_cost = D(0)
        labor_inputs, equip_inputs, flags = [], [], []
        labor_origin = equip_origin = "observed"
        crew_size = D(0)
        operator_in_labor = False
        eq_rates: list[tuple[dict, dict]] = []
        for m in members:
            hrs = _d(m["hours_per_shift"]) if m["hours_per_shift"] is not None else shift
            qty = _d(m["quantity"])
            if m["member_kind"] == "labor":
                crew_size += qty
                if m["is_operator"]:
                    operator_in_labor = True
                lr = self.labor_rate(m["trade_code"], p)
                labor_cost += qty * hrs * lr["total_hr"]
                labor_inputs.append({"crew_member": m["crew_member_id"], "trade": m["trade_code"], "qty": str(qty),
                                     "hours": str(hrs), "rate_total_hr": str(lr["total_hr"]),
                                     "rate_components": {k: str(v) for k, v in lr["components"].items()}})
                labor_inputs.extend(lr["inputs"]); flags += lr["flags"]
                if lr["origin"] == "assumed":
                    labor_origin = "assumed"
            else:
                er = self._equipment_rate(m["equipment_type_code"], p)
                eq_rates.append((m, er))
                per = qty * (hrs * er["rate"] if er["basis"] != "day" else er["rate"])
                equip_cost += per
                equip_inputs.append({"crew_member": m["crew_member_id"], "equipment_type": m["equipment_type_code"],
                                     "qty": str(qty), "hours": str(hrs), "rate": str(er["rate"]), "rate_basis": er["basis"]})
                equip_inputs.extend(er["inputs"]); flags += er["flags"]
                if er["origin"] == "assumed":
                    equip_origin = "assumed"
        for m, er in eq_rates:
            if er["operator_included"] and operator_in_labor:
                raise Missing("OPERATOR_DOUBLE_COUNT", f"{m['equipment_type_code']} in {crew['crew_id']}",
                              "equipment rate includes the operator and the crew also lists an operator as labor",
                              "remove the operator from crew labor or use a rate that excludes the operator", blocking=True)
            if (not er["operator_included"]) and not operator_in_labor and \
                    self._equip_types.get(m["equipment_type_code"], {}).get("typically_needs_operator"):
                flags.append(f"OPERATOR_NOT_PRICED:{m['equipment_type_code']}")
        return {"crew": crew, "shift": shift, "crew_size": crew_size, "labor_per_shift": labor_cost,
                "equip_per_shift": equip_cost, "labor_inputs": labor_inputs, "equip_inputs": equip_inputs,
                "flags": sorted(set(flags)), "labor_origin": labor_origin, "equip_origin": equip_origin}

    def _daily_output(self, comp: dict, wi: dict, crew_info: dict, p: RunParams):
        """Return (daily_output in work-item unit per crew shift, inputs, flags, origin, ph_per_unit)."""
        prod = self._prod_obs.get(comp["productivity_id"])
        out_unit = wi["output_unit_id"]
        crew_size, shift = (crew_info["crew_size"], crew_info["shift"]) if crew_info else (None, None)
        if prod is None:
            raise Missing("PRODUCTIVITY_UNKNOWN", comp["productivity_id"], "productivity record not found")
        if prod["origin"] == "missing" or not self._usable(prod, p):
            a = self._approved_assumption(f"productivity:{comp['component_id']}", p)
            if a is not None:
                if a["unit_id"] is None or not self.units.compatible(a["unit_id"], out_unit):
                    raise Missing("ASSUMPTION_UNIT", f"productivity:{comp['component_id']}", "assumed output needs a unit")
                daily = _d(a["value_numeric"]) * D(self.units.factor(a["unit_id"], out_unit).numerator) / \
                    D(self.units.factor(a["unit_id"], out_unit).denominator)
                return daily, [{"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                                "value": str(a["value_numeric"]), "unit": a["unit_id"], "origin": "assumed"}], \
                    ["ASSUMED_PRODUCTIVITY"], "assumed"
            reason = "norm not found in any source (origin=missing)" if prod["origin"] == "missing" else \
                f"record not usable (review_status={prod['review_status']}, need >= {p.min_review})"
            raise Missing("PRODUCTIVITY_MISSING", f"labor norm {comp['productivity_id']} for '{wi['name']}'", reason,
                          "extract norm from a government manual / DOT guide with page reference")
        try:
            m = self.units.factor(prod["output_unit_id"], out_unit)
        except UnitError as e:
            raise Missing("PRODUCTIVITY_UNIT", comp["productivity_id"], f"output unit mismatch: {e}", blocking=True)
        mult = D(m.numerator) / D(m.denominator)
        flags: list[str] = []
        if crew_info is None:       # crew itself is unresolved: that gap is reported by the caller
            raise Missing("CREW_UNRESOLVED", f"crew for {comp['productivity_id']}", "norm exists but the costing crew could not be resolved")
        if prod["crew_size"] is not None and _d(prod["crew_size"]) != crew_size:
            raise Missing("CREW_MISMATCH", f"{comp['productivity_id']} vs {crew_info['crew']['crew_id']}",
                          f"norm was observed for crew size {prod['crew_size']} but costing crew has {crew_size}", blocking=True)
        if prod["shift_hours"] is not None and _d(prod["shift_hours"]) != shift:
            raise Missing("SHIFT_MISMATCH", f"{comp['productivity_id']} vs {crew_info['crew']['crew_id']}",
                          f"norm shift {prod['shift_hours']} h vs crew shift {shift} h", blocking=True)
        if prod["daily_output"] is not None:
            daily = _d(prod["daily_output"]) * mult
        else:
            pph = _d(prod["person_hours_per_unit_reported"]) / mult   # per work-item unit
            daily = crew_size * shift / pph
            flags.append("DAILY_OUTPUT_DERIVED_FROM_REPORTED_PERSON_HOURS")
        inp = [{"table": "productivity_observations", "id": prod["productivity_id"], "field": "daily_output",
                "value": str(prod["daily_output"]) if prod["daily_output"] is not None else str(prod["person_hours_per_unit_reported"]),
                "unit": prod["output_unit_id"], "source_doc": prod["source_doc"], "source_edition": prod["source_edition"],
                "source_page": prod["source_page"], "origin": "observed", "review_status": prod["review_status"]}]
        return daily, inp, flags, "observed", None

    # --------------------------------------------------------------- adjustments
    def _adjust_factors(self, kind: str, p: RunParams) -> list[dict]:
        """Condition and quantity factors for one cost component. Requested conditions must resolve."""
        out = []
        for tag in p.conditions:
            hits = [f for f in self.db["adjustment_factors"]
                    if f["factor_type"] in ("conditions", "productivity_condition") and f["condition_desc"] == tag
                    and f["applies_to"] == kind and f.get("review_status") not in ("flagged", "rejected")
                    and (p.min_review == "unreviewed" or f.get("review_status") == "validated")
                    and not (f["origin"] == "assumed" and p.mode != "with_assumptions")
                    and not (f.get("valid_from") and f["valid_from"] > p.as_of)
                    and not (f.get("valid_to") and f["valid_to"] < p.as_of)]
            anyhit = [f for f in self.db["adjustment_factors"]
                      if f["factor_type"] in ("conditions", "productivity_condition") and f["condition_desc"] == tag]
            if hits:
                out.append(hits[0])
            elif not anyhit:
                raise Missing("CONDITION_FACTOR_MISSING", f"factor for condition '{tag}' ({kind})",
                              "requested job condition has no adjustment factor; it is never silently ignored",
                              "source a conditions factor or remove the condition")
        if p.quantity is not None:
            for f in self.db["adjustment_factors"]:
                if f["factor_type"] == "quantity" and f["applies_to"] == kind and f.get("review_status") not in ("flagged", "rejected") \
                        and (p.min_review == "unreviewed" or f.get("review_status") == "validated") \
                        and not (f["origin"] == "assumed" and p.mode != "with_assumptions"):
                    lo = f["qty_min"] if f["qty_min"] is not None else D(0)
                    hi = f["qty_max"]
                    if _d(lo) <= p.quantity and (hi is None or p.quantity < _d(hi)):
                        out.append(f)
                        break
        return out

    # ------------------------------------------------------------------ unit cost
    @staticmethod
    def _summarize(origins: set) -> str:
        origins = set(origins)
        if "assumed" in origins:
            return "assumed"
        if len(origins) > 1:
            return "mixed"
        return next(iter(origins)) if origins else "observed"

    def _material_component(self, c: dict, kind: str, p: RunParams, collect: list):
        """Resolve quantity, waste and price of one material-like component; every failure is collected, not raised."""
        qty = qformula = None
        qinputs: list = []
        qorigin = "observed"
        qty_unit = c["qty_unit_id"]
        waste = None
        winput: list = []
        # ---- quantity
        try:
            if c["qty_mode"] == "from_product_consumption":
                qty, qinputs, qformula, qorigin = self._consumption_qty(c, p)
                qty_unit = qinputs[0]["per_unit"]
            elif c["qty_origin"] == "assumed":
                raise Missing("QUANTITY_ASSUMED", f"quantity per unit for {c['description']}",
                              "an inline assumed quantity is not accepted; record it in the assumptions table (quantity:<component_id>)")
            elif c["qty_origin"] == "missing" or c["qty_per_unit"] is None:
                a = self._approved_assumption(f"quantity:{c['component_id']}", p)
                if a is None:
                    raise Missing("QUANTITY_MISSING", f"quantity per unit for {c['description']}",
                                  "quantity not derivable from any collected source",
                                  "derive from geometry/manufacturer data or add an approved assumption")
                qty, qformula, qorigin = _d(a["value_numeric"]), f"assumption {a['assumption_id']}", "assumed"
                qinputs = [{"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric",
                            "value": str(a["value_numeric"]), "unit": a["unit_id"], "origin": "assumed"}]
                qty_unit = a["unit_id"] or qty_unit
            else:
                qty, qformula, qorigin = _d(c["qty_per_unit"]), c["qty_formula"], c["qty_origin"]
        except Missing as m:
            collect.append(m)
        # ---- waste
        try:
            if c["waste_factor"] is not None:
                if c["waste_origin"] not in ("observed", "derived"):
                    raise Missing("WASTE_ASSUMED", f"waste factor for {c['description']}",
                                  "waste factor is not observed/derived; an assumed value belongs in the assumptions table",
                                  "source the waste factor or add an approved assumption (waste:<component_id>)")
                waste = _d(c["waste_factor"])
                winput = [{"table": "work_item_components", "id": c["component_id"], "field": "waste_factor", "value": str(waste),
                           "origin": c["waste_origin"], "basis": c["waste_basis"]}]
            else:
                a = self._approved_assumption(f"waste:{c['component_id']}", p)
                if a is None:
                    raise Missing("WASTE_MISSING", f"waste factor for {c['description']}",
                                  "no waste/loss factor recorded (zero is only acceptable with a stated basis)",
                                  "record waste_factor with waste_basis, or an approved assumption")
                waste = _d(a["value_numeric"])
                winput = [{"table": "assumptions", "id": a["assumption_id"], "field": "value_numeric", "value": str(waste), "origin": "assumed"}]
        except Missing as m:
            collect.append(m)
        # ---- price (needs only the unit; works even when quantity/waste are missing so ALL gaps are reported)
        price = None
        pinputs: list = []
        pflags: list = []
        porigin = "observed"
        try:
            if qty_unit is None:
                raise Missing("QUANTITY_UNIT_MISSING", c["description"], "component has no quantity unit")
            price, pinputs, pflags, porigin = self._material_unit_price(c, p, qty_unit, kind)
        except Missing as m:
            collect.append(m)
        factors: list = []
        try:
            factors = self._adjust_factors(kind, p)
        except Missing as m:
            collect.append(m)
        if collect or qty is None or waste is None or price is None:
            return None
        eff_qty = qty * (1 + waste)
        unit_cost = eff_qty * price
        adj_note = ""
        for f in factors:
            unit_cost *= _d(f["factor_value"]); adj_note += f" × {f['factor_value']} [{f['factor_id']}]"
            pinputs.append({"table": "adjustment_factors", "id": f["factor_id"], "field": "factor_value",
                            "value": str(f["factor_value"]), "origin": f["origin"]})
        origins = {qorigin, porigin, winput[0]["origin"]}
        summary = self._summarize({o if o != "derived" else "derived" for o in origins})
        formula = f"{qformula} = {qty} {qty_unit}/unit × (1+{waste}) × ${q10(price)}/{qty_unit}{adj_note}"
        return {"qty": eff_qty, "unit": qty_unit, "price": price, "cost": unit_cost, "formula": formula,
                "inputs": qinputs + winput + pinputs, "summary": summary, "flags": pflags}

    def unit_cost(self, work_item_id: str, version: int, p: RunParams) -> RunResult:
        wi = self.db.index("work_items", "work_item_id", "version").get((work_item_id, version))
        if wi is None:
            raise KeyError(f"work item {work_item_id} v{version} not found")
        comps = sorted([c for c in self.db["work_item_components"]
                        if c["work_item_id"] == work_item_id and c["work_item_version"] == version], key=lambda c: c["line_no"])
        lines: list[dict] = []
        missing: list[dict] = []
        warnings: list[str] = []
        totals = {"material": D(0), "labor": D(0), "equipment": D(0), "other_direct": D(0)}
        crew_cache: dict[str, Any] = {}
        fingerprint: list[Any] = []
        any_assumed = False

        def add_missing(c: dict, items: list):
            reasons = []
            for m in items:
                info = dict(m.info); info["component_ref"] = c["component_id"]; info["blocking"] = m.blocking
                missing.append(info); reasons.append(f"{m.info['code']}: {m.info['needed']}")
            lines.append({"line_no": len(lines) + 1, "line_kind": c["component_kind"], "component_ref": c["component_id"],
                          "description": c["description"], "quantity": None, "quantity_unit_id": None, "unit_cost": None,
                          "extended_cost": None, "formula": "UNRESOLVED " + " | ".join(reasons), "inputs": [],
                          "origin_summary": "missing", "warnings": [m.info["reason"] for m in items]})

        for c in comps:
            kind = c["component_kind"]
            if kind in ("material", "other_direct"):
                collect: list[Missing] = []
                res = self._material_component(c, kind, p, collect)
                if res is None:
                    add_missing(c, collect)
                    continue
                if res["summary"] == "assumed":
                    any_assumed = True
                totals[kind] += q10(res["cost"])
                lines.append({"line_no": len(lines) + 1, "line_kind": kind, "component_ref": c["component_id"],
                              "description": c["description"], "quantity": q10(res["qty"]), "quantity_unit_id": res["unit"],
                              "unit_cost": q10(res["price"]), "extended_cost": q10(res["cost"]), "formula": res["formula"],
                              "inputs": res["inputs"], "origin_summary": res["summary"], "warnings": res["flags"]})
                fingerprint.append([c["component_id"], str(res["cost"])])
                continue
            # ---- labor / equipment: crew composition and productivity are resolved independently
            errs: list[Missing] = []
            ci = None
            try:
                if c["crew_id"] not in crew_cache:
                    crew_cache[c["crew_id"]] = self._crew_costs(c, wi, p)
                ci = crew_cache[c["crew_id"]]
            except Missing as m:
                errs.append(m)
            daily = None
            try:
                daily, dinputs, dflags, dorigin, _ = self._daily_output(c, wi, ci, p)
            except Missing as m:
                errs.append(m)
            if errs or ci is None or daily is None:
                add_missing(c, errs)
                continue
            per_shift = ci["labor_per_shift"] if kind == "labor" else ci["equip_per_shift"]
            unit_cost = per_shift / daily
            adj_note = ""
            extra_inputs = []
            try:
                adj = self._adjust_factors(kind, p)
            except Missing as m:
                add_missing(c, [m]); continue
            for f in adj:
                unit_cost *= _d(f["factor_value"]); adj_note += f" × {f['factor_value']} [{f['factor_id']}]"
                extra_inputs.append({"table": "adjustment_factors", "id": f["factor_id"], "field": "factor_value",
                                     "value": str(f["factor_value"]), "origin": f["origin"]})
            ph = ci["crew_size"] * ci["shift"] / daily
            ch = ci["shift"] / daily
            ins = (ci["labor_inputs"] if kind == "labor" else ci["equip_inputs"]) + dinputs + extra_inputs
            origin = ci["labor_origin"] if kind == "labor" else ci["equip_origin"]
            summary = "assumed" if (origin == "assumed" or dorigin == "assumed" or ci["crew"]["origin"] == "assumed") else "observed"
            if summary == "assumed":
                any_assumed = True
            totals[kind] += q10(unit_cost)
            label = (f"person-hours/unit = {ci['crew_size']}×{ci['shift']}/{q10(daily)} = {q10(ph)}; "
                     f"crew-hours/unit = {q10(ch)}") if kind == "labor" else \
                f"crew-hours/unit = {ci['shift']}/{q10(daily)} = {q10(ch)} (equipment-hours = member qty × hours × this)"
            formula = (f"crew {kind} cost/shift ${q10(per_shift)} / daily output {q10(daily)} {wi['output_unit_id']}"
                       f" = ${q10(unit_cost)}/{wi['output_unit_id']}{adj_note}; {label}")
            lines.append({"line_no": len(lines) + 1, "line_kind": kind, "component_ref": c["component_id"],
                          "description": c["description"], "quantity": q10(ph if kind == "labor" else ch),
                          "quantity_unit_id": "HR", "unit_cost": q10(unit_cost), "extended_cost": q10(unit_cost),
                          "formula": formula, "inputs": ins, "origin_summary": summary,
                          "warnings": sorted(set(dflags + ci["flags"]))})
            fingerprint.append([c["component_id"], str(unit_cost)])
        # same cost tag twice inside one work item = double-count suspicion
        seen: dict[str, str] = {}
        for c in comps:
            for t in c["cost_tags"] or []:
                if t in seen and seen[t] != c["component_id"]:
                    warnings.append(f"DUPLICATE_COST_TAG '{t}' on {seen[t]} and {c['component_id']}: check for double counting")
                seen.setdefault(t, c["component_id"])
        blocking = [m for m in missing if m["blocking"]]
        status = "failed" if blocking else ("incomplete" if missing else "complete")
        if p.mode == "strict" and any_assumed:
            status = "failed"; warnings.append("assumed input leaked into strict run")
        return self._finish(
            "unit_cost", work_item_id, version, p, wi["output_unit_id"], lines, missing, warnings, totals, status, any_assumed,
            fingerprint)

    def _consumption_qty(self, c: dict, p: RunParams):
        """Quantity per unit from manufacturer coverage: gal/SF = coats_applied / (coverage × K) × per_qty."""
        key = c["product_spec_key"]
        prods = {r["product_id"] for r in self.db["products"] if r["spec_key"] == key}
        rows = [r for r in self.db["product_consumption"]
                if r["product_id"] in prods and r["application"] == c["consumption_application"]
                and r["origin"] == "observed" and self._usable(r, p)]
        if not rows:
            raise Missing("CONSUMPTION_MISSING", f"manufacturer coverage for {key} / {c['consumption_application']}",
                          "no usable product_consumption record", "extract spread rate with film thickness, coats and conditions from the product data sheet")
        r = sorted(rows, key=lambda x: x["consumption_id"])[0]
        cov = _d(r["coverage_qty"]); k = _d(r["coats"]); n = _d(c["coats_applied"])
        per = _d(r["per_qty"])
        # product units consumed per unit of output quantity (output unit == coverage unit)
        qty = n * per / (cov * k)
        formula = f"coats_applied {n} × per_qty {per} / (coverage {cov} {r['coverage_unit_id']} × coats_in_rate {k})"
        inp = [{"table": "product_consumption", "id": r["consumption_id"], "field": "coverage_qty", "value": str(cov),
                "unit": r["coverage_unit_id"], "per_unit": r["per_unit_id"], "film_thickness": r["film_thickness"],
                "coats_in_rate": str(k), "conditions": r["conditions"], "origin": "observed",
                "review_status": r["review_status"]}]
        return qty, inp, formula, "derived"

    # ------------------------------------------------------------------ assembly
    def assembly_cost(self, assembly_id: str, version: int, p: RunParams) -> RunResult:
        asm = self.db.index("assemblies", "assembly_id", "version").get((assembly_id, version))
        if asm is None:
            raise KeyError(f"assembly {assembly_id} v{version} not found")
        comps = sorted([c for c in self.db["assembly_components"]
                        if c["assembly_id"] == assembly_id and c["assembly_version"] == version], key=lambda c: c["line_no"])
        lines, missing, warnings, children = [], [], [], []
        totals = {"material": D(0), "labor": D(0), "equipment": D(0), "other_direct": D(0)}
        any_assumed = False
        fingerprint = []
        scope_owner: dict[str, str] = {}
        wis = self.db.index("work_items", "work_item_id", "version")
        for c in comps:
            wi = wis[(c["work_item_id"], c["work_item_version"])]
            for t in wi["included_scope"] or []:
                if t in scope_owner and scope_owner[t] != wi["work_item_id"]:
                    warnings.append(f"SCOPE_OVERLAP '{t}' claimed by both {scope_owner[t]} and {wi['work_item_id']}: double counting")
                scope_owner.setdefault(t, wi["work_item_id"])
            child = self.unit_cost(c["work_item_id"], c["work_item_version"], p)
            children.append(child)
            try:
                mult = self.units.factor(c["qty_unit_id"], wi["output_unit_id"])
            except UnitError as e:
                missing.append({"code": "ASSEMBLY_UNIT", "needed": c["assembly_component_id"], "reason": str(e),
                                "how_to_fill": "fix qty_unit_id", "component_ref": c["assembly_component_id"], "blocking": True})
                continue
            qty = _d(c["qty_per_assembly_unit"]) * D(mult.numerator) / D(mult.denominator)
            if child.status != "complete":
                for m in child.run["missing_inputs"]:
                    mm = dict(m); mm["component_ref"] = f"{c['assembly_component_id']}>{m['component_ref']}"
                    missing.append(mm)
                lines.append({"line_no": len(lines) + 1, "line_kind": "assembly_component", "component_ref": c["assembly_component_id"],
                              "description": wi["name"], "quantity": q10(qty), "quantity_unit_id": wi["output_unit_id"],
                              "unit_cost": None, "extended_cost": None,
                              "formula": f"child run {child.run['run_id']} is {child.status}",
                              "inputs": [{"table": "calculation_runs", "id": child.run["run_id"], "field": "direct_cost_total",
                                          "value": "", "origin": "derived"}], "origin_summary": "missing", "warnings": []})
                continue
            ext = qty * child.total
            for k, field_name in (("material", "material_cost"), ("labor", "labor_cost"), ("equipment", "equipment_cost"),
                                  ("other_direct", "other_direct_cost")):
                totals[k] += q10(qty * _d(child.run[field_name] or 0))
            if child.run["has_assumptions"]:
                any_assumed = True
            fingerprint.append([c["assembly_component_id"], child.run["run_id"]])
            lines.append({"line_no": len(lines) + 1, "line_kind": "assembly_component", "component_ref": c["assembly_component_id"],
                          "description": wi["name"], "quantity": q10(qty), "quantity_unit_id": wi["output_unit_id"],
                          "unit_cost": child.total, "extended_cost": q10(ext),
                          "formula": f"{c['qty_formula']} = {qty} {wi['output_unit_id']} × unit cost ${child.total}/{wi['output_unit_id']} (run {child.run['run_id']})",
                          "inputs": [{"table": "calculation_runs", "id": child.run["run_id"], "field": "direct_cost_total",
                                      "value": str(child.total), "origin": "derived"}],
                          "origin_summary": "assumed" if child.run["has_assumptions"] else "derived",
                          "warnings": child.run["warnings"]})
        blocking = [m for m in missing if m.get("blocking")] or [w for w in warnings if w.startswith("SCOPE_OVERLAP")]
        status = "failed" if blocking else ("incomplete" if missing else "complete")
        res = self._finish("assembly", assembly_id, version, p, asm["output_unit_id"], lines, missing, warnings, totals,
                           status, any_assumed, fingerprint)
        res.children = children
        return res

    # ------------------------------------------------------------------- finish
    def _finish(self, target_type, target_id, version, p: RunParams, unit, lines, missing, warnings, totals, status,
                any_assumed, fingerprint) -> RunResult:
        complete = status == "complete"
        material, labor, equip, other = (q6(totals[k]) for k in ("material", "labor", "equipment", "other_direct"))
        direct = q6(totals["material"] + totals["labor"] + totals["equipment"] + totals["other_direct"])
        all_warn = list(warnings)
        for ln in lines:
            for w in ln.get("warnings", []):
                if isinstance(w, str) and w.isupper() or (isinstance(w, str) and ":" in w and w.split(":")[0].isupper()):
                    if w not in all_warn:
                        all_warn.append(w)
        fp = hashlib.sha1(json.dumps(fingerprint, sort_keys=True, default=str).encode()).hexdigest()
        run_id = make_id("RUN", target_type, target_id, version, p.canonical(), self.calc_version, fp, length=12)
        run_at = p.run_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        run = {"run_id": run_id, "run_at": run_at, "calc_version": self.calc_version, "target_type": target_type,
               "target_id": target_id, "target_version": version, "mode": p.mode, "parameters": json.loads(p.canonical()),
               "status": status, "has_assumptions": bool(any_assumed), "result_unit_id": unit,
               "material_cost": material if complete else None, "labor_cost": labor if complete else None,
               "equipment_cost": equip if complete else None, "other_direct_cost": other if complete else None,
               "direct_cost_total": direct if complete else None, "missing_inputs": missing, "warnings": all_warn,
               "code_ref": self.code_ref, "origin": "derived", "review_status": "unreviewed", "reviewed_by": None,
               "reviewed_at": None, "notes": None}
        for i, ln in enumerate(lines, 1):
            ln["run_id"] = run_id
            ln["line_no"] = i
        return RunResult(run=run, lines=lines)

    # ------------------------------------------------------------ loaded labor rate
    def loaded_labor_rate(self, trade: str, p: RunParams) -> RunResult:
        """Derived labor_rates row (rate_type=loaded_employer_cost) with every component traceable."""
        missing, lines, warnings = [], [], []
        totals = {"material": D(0), "labor": D(0), "equipment": D(0), "other_direct": D(0)}
        derived: dict[str, list[dict]] = {}
        try:
            lr = self.labor_rate(trade, p)
        except Missing as m:
            info = dict(m.info); info["component_ref"] = trade; info["blocking"] = m.blocking
            missing.append(info)
            lr = None
        status = "complete"
        any_assumed = False
        if lr:
            any_assumed = lr["origin"] == "assumed"
            n = 0
            for k, v in lr["components"].items():
                n += 1
                lines.append({"line_no": n, "line_kind": "labor", "component_ref": trade, "description": k, "quantity": D(1),
                              "quantity_unit_id": "HR", "unit_cost": q10(v), "extended_cost": q10(v),
                              "formula": f"{k} per paid hour", "inputs": lr["inputs"] if n == 1 else [],
                              "origin_summary": "assumed" if lr["origin"] == "assumed" else "observed", "warnings": lr["flags"] if n == 1 else []})
            totals["labor"] = lr["total_hr"]
            warnings += lr["flags"]
        else:
            status = "failed" if any(m.get("blocking") for m in missing) else "incomplete"
        res = self._finish("labor_loaded", trade, None, p, "HR", lines, missing, warnings, totals, status, any_assumed,
                           [[trade, str(lr["total_hr"]) if lr else "missing"]])
        if lr and status == "complete":
            base_ids = [i["id"] for i in lr["inputs"]]
            comps = lr["components"]
            rid = make_id("LRT", trade, p.region_id, p.as_of.isoformat(), res.run["run_id"], length=10)
            derived["labor_rates"] = [{
                "labor_rate_id": rid, "rate_type": "loaded_employer_cost", "trade_code": trade,
                "classification_raw": f"Loaded employer cost for {trade} ({p.labor_basis})", "soc_code": None,
                "statistic": "n/a", "region_id": p.region_id, "base_wage_hr": q10(comps.get("base_wage", D(0))),
                "fringe_hr": q10(comps.get("fringe_in_source", comps.get("employer_benefits", D(0)))),
                "fringe_breakdown": None,
                "payroll_tax_hr": q10(sum((v for k, v in comps.items() if k in BURDEN_PAYROLL_TAX_TYPES), D(0))),
                "workers_comp_hr": q10(comps.get("workers_comp", D(0))), "other_employer_cost_hr": D(0),
                "total_hr": q10(lr["total_hr"]), "includes_fringe": True, "includes_payroll_taxes": True,
                "includes_workers_comp": True, "wage_basis": "straight_time", "project_type": "n/a",
                "use_context": "employer_internal", "apprentice": False, "determination_ref": None,
                "effective_from": p.as_of, "effective_to": None, "retrieved_at": None, "derived_from": base_ids,
                "calc_run_id": res.run["run_id"], "source_id": None, "source_locator": None, "evidence_excerpt": None,
                "raw_file_sha256": None, "origin": "derived", "review_status": "unreviewed", "reviewed_by": None,
                "reviewed_at": None, "created_at": None, "notes": "derived by costdb.calc.loaded_labor_rate"}]
        res.derived_rows = derived
        return res


# ---------------------------------------------------------------- markup / margin
def markup_to_margin(m: Decimal) -> Decimal:
    """margin g = m / (1 + m)"""
    return m / (1 + m)


def margin_to_markup(g: Decimal) -> Decimal:
    """markup m = g / (1 - g)"""
    if g >= 1:
        raise ValueError("margin must be < 1")
    return g / (1 - g)


def apply_markup(base: RunResult, *, overhead_pct: Decimal, overhead_basis: str, contingency_pct: Decimal,
                 contingency_basis: str, profit_method: str, profit_value: Decimal, profit_basis: str,
                 run_at: Optional[str] = None, calc_version: str = CALC_VERSION) -> RunResult:
    """Show overhead, contingency and profit SEPARATELY on top of direct cost.

      overhead     = direct × oh
      contingency  = (direct + overhead) × ct
      cost         = direct + overhead + contingency
      profit_markup: price = cost × (1 + m)        profit_margin: price = cost / (1 - g)
    No default percentages exist: each must be passed with a stated basis."""
    for name, basis in (("overhead", overhead_basis), ("contingency", contingency_basis), ("profit", profit_basis)):
        if not basis or not basis.strip():
            raise ValueError(f"{name} percentage needs a stated basis (no universal default)")
    if base.run["status"] != "complete" or base.total is None:
        raise ValueError("cannot apply markup to an incomplete/failed run")
    if profit_method not in ("markup", "margin"):
        raise ValueError("profit_method must be 'markup' or 'margin'")
    direct = _d(base.total)
    overhead = direct * overhead_pct
    cont = (direct + overhead) * contingency_pct
    cost = direct + overhead + cont
    if profit_method == "markup":
        price = cost * (1 + profit_value)
        pformula = f"price = cost × (1 + markup {profit_value})"
    else:
        if profit_value >= 1:
            raise ValueError("margin must be < 1")
        price = cost / (1 - profit_value)
        pformula = f"price = cost / (1 − margin {profit_value})"
    profit = price - cost
    rows = [
        ("subtotal", "Direct cost", direct, f"direct cost from run {base.run['run_id']}", "derived"),
        ("overhead", f"Overhead ({overhead_pct}) — {overhead_basis}", overhead, f"{direct} × {overhead_pct}", "assumed"),
        ("contingency", f"Contingency ({contingency_pct}) — {contingency_basis}", cont,
         f"({direct} + {q10(overhead)}) × {contingency_pct}", "assumed"),
        ("subtotal", "Cost incl. overhead and contingency", cost, "direct + overhead + contingency", "derived"),
        ("profit", f"Profit by {profit_method} {profit_value} — {profit_basis}", profit, pformula, "assumed"),
        ("subtotal", "Price", price, "cost + profit", "derived"),
    ]
    fp = hashlib.sha1(json.dumps([str(direct), str(overhead_pct), str(contingency_pct), profit_method, str(profit_value)]).encode()).hexdigest()
    run_id = make_id("RUN", "markup", base.run["run_id"], fp, calc_version, length=12)
    lines = [{"run_id": run_id, "line_no": i, "line_kind": k, "component_ref": None, "description": d, "quantity": None,
              "quantity_unit_id": None, "unit_cost": None, "extended_cost": q10(v), "formula": f,
              "inputs": [{"table": "calculation_runs", "id": base.run["run_id"], "field": "direct_cost_total",
                          "value": str(direct), "origin": "derived"}] if i == 1 else [], "origin_summary": o, "warnings": []}
             for i, (k, d, v, f, o) in enumerate(rows, 1)]
    run = {"run_id": run_id, "run_at": run_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "calc_version": calc_version, "target_type": "markup", "target_id": base.run["run_id"], "target_version": None,
           "mode": "with_assumptions", "parameters": {"overhead_pct": str(overhead_pct), "overhead_basis": overhead_basis,
                                                      "contingency_pct": str(contingency_pct),
                                                      "contingency_basis": contingency_basis, "profit_method": profit_method,
                                                      "profit_value": str(profit_value), "profit_basis": profit_basis},
           "status": "complete", "has_assumptions": True, "result_unit_id": base.run["result_unit_id"],
           "material_cost": None, "labor_cost": None, "equipment_cost": None, "other_direct_cost": None,
           "direct_cost_total": q6(price), "missing_inputs": [], "warnings": ["MARKUP_PERCENTAGES_ARE_POLICY_INPUTS"],
           "code_ref": None, "origin": "derived", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
           "notes": f"price shown separately from direct cost; direct={q6(direct)} overhead={q6(overhead)} "
                    f"contingency={q6(cont)} profit={q6(profit)}"}
    return RunResult(run=run, lines=lines, children=[base])
