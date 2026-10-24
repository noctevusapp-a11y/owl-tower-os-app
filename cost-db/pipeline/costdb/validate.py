"""Independent validation rules (the 'agent F' checks) + the strict promotion gate.

Every rule returns Issue records that map 1:1 to the validation_issues table. Rules are written to FAIL LOUDLY on
contradictions; missing data is NOT an issue (it is a backlog item) unless a record claims to have it.

Promotion gate (promote_validated): an OBSERVED record may become review_status='validated' only if
  1. it has no open error-level issue,
  2. its source was actually fetched (verification_method == 'fetched_primary'), and
  3. its evidence fields are present.
Search-snippet evidence therefore can never reach 'validated'.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable, Optional

from .calc import Engine, RunParams, median
from .enums import NO_DATA_USE
from .ids import SpecError, spec_key
from .store import Database
from .units import Units, UnitError

D = Decimal
GLOBAL_EXCLUDED_TOKENS = {"mobilization", "daily_cleanup_and_protection", "supervision_and_general_conditions",
                          "sales_tax_and_delivery", "permits_and_inspections", "overhead_and_profit"}
OBSERVED_TABLES = ("price_observations", "labor_rates", "equipment_rates", "productivity_observations",
                   "burden_rates", "index_values", "product_consumption", "bid_benchmarks", "products")
# Tables whose rows carry a source_id column directly; index_values inherit the source of their series (indices.source_id).
SOURCE_TABLES = tuple(t for t in OBSERVED_TABLES if t != "index_values") + ("indices",)
# Fields a row must show before it may be promoted to 'validated' (per table).
EVIDENCE_FIELDS = {"price_observations": ("evidence_excerpt",), "labor_rates": ("evidence_excerpt",), "equipment_rates": ("evidence_excerpt",),
                   "burden_rates": ("evidence_excerpt",), "productivity_observations": ("evidence_excerpt", "source_page"),
                   "product_consumption": ("evidence_excerpt", "source_locator"), "products": ("evidence_excerpt", "source_locator"),
                   "bid_benchmarks": ("evidence_excerpt", "source_locator"), "index_values": ("source_locator",)}

# Screening thresholds. They never change a calculation; they decide which warnings the validator raises. Each one states its basis;
# pass Validator(policy={...}) to change them (the value actually used is written into the issue details).
DEFAULT_POLICY: dict[str, tuple[Any, str]] = {
    "price_stale_days": (365, "screening threshold: a price older than one year is flagged for re-capture; not a quality statement"),
    "rate_stale_days": (800, "screening threshold: wage determinations/surveys are published about yearly; ~2 years + margin"),
    "price_outlier_ratio": (3, "screening threshold: a product price beyond 3x or below 1/3 of the median of >=3 comparable products is flagged for a human look"),
    "productivity_recon_tol": (Decimal("0.01"), "reported person-hours per unit must reproduce crew x shift / daily output within 1% (rounding of a printed table)"),
    "loaded_sum_tol": (Decimal("0.0002"), "four-decimal rounding of component rates"),
}


@dataclass
class Issue:
    record_table: str
    record_id: str
    rule_code: str
    severity: str          # error | warning | info
    message: str
    details: dict = field(default_factory=dict)

    def as_row(self, detected_by: str = "costdb.validate") -> dict:
        return {"detected_at": None, "detected_by": detected_by, "record_table": self.record_table,
                "record_id": self.record_id, "rule_code": self.rule_code, "severity": self.severity,
                "message": self.message, "details": self.details, "status": "open", "resolution_note": None,
                "resolved_at": None}


def _parse_ts(x: Any) -> Optional[datetime]:
    """Aware UTC datetime, or None when the text has no time zone / cannot be read (a naive time is never guessed)."""
    if x is None or x == "":
        return None
    try:
        dt = x if isinstance(x, datetime) else datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    except ValueError:
        return None
    return None if dt.tzinfo is None else dt.astimezone(timezone.utc)


def pk_of(table: str, row: dict) -> str:
    keys = {"work_items": ("work_item_id", "version"), "assemblies": ("assembly_id", "version"),
            "index_values": ("index_id", "period_start", "vintage_date"), "calculation_run_lines": ("run_id", "line_no")}
    if table in keys:
        return "|".join(str(row[k]) for k in keys[table])
    meta_first = {"units": "unit_id", "regions": "region_id", "categories": "category_id", "trades": "trade_code",
                  "equipment_types": "equipment_type_code", "sources": "source_id", "products": "product_id",
                  "product_consumption": "consumption_id", "price_observations": "observation_id",
                  "calculation_runs": "run_id", "labor_rates": "labor_rate_id", "burden_rates": "burden_id",
                  "equipment_rates": "equipment_rate_id", "crews": "crew_id", "crew_members": "crew_member_id",
                  "work_item_components": "component_id", "productivity_observations": "productivity_id",
                  "assembly_components": "assembly_component_id", "indices": "index_id", "adjustment_factors": "factor_id",
                  "assumptions": "assumption_id", "capture_targets": "target_id", "bid_benchmarks": "benchmark_id"}
    return str(row[meta_first[table]])


class Validator:
    def __init__(self, db: Database, today: Optional[date] = None, production: bool = True, policy: Optional[dict] = None):
        self.db = db
        self.today = today or date.today()
        self.production = production
        self.policy = {k: v[0] for k, v in DEFAULT_POLICY.items()}
        self.policy.update(policy or {})
        self.units = Units(db["units"])
        self.issues: list[Issue] = []
        self.sources = db.index("sources", "source_id")
        self.products = db.index("products", "product_id")
        self.categories = db.index("categories", "category_id")

    # ------------------------------------------------------------------ plumbing
    def add(self, table: str, row_or_id: Any, code: str, sev: str, msg: str, **details):
        rid = row_or_id if isinstance(row_or_id, str) else pk_of(table, row_or_id)
        self.issues.append(Issue(table, rid, code, sev, msg, details))

    def run(self) -> list[Issue]:
        for fn in (self.check_foreign_keys, self.check_sources, self.check_products, self.check_observations,
                   self.check_labor, self.check_equipment_and_crews, self.check_productivity, self.check_work_items,
                   self.check_assemblies, self.check_assumptions, self.check_calculation_runs):
            fn()
        return self.issues

    # ---------------------------------------------------------------- foreign keys
    def check_foreign_keys(self):
        pk_cache: dict[tuple[str, str], set] = {}
        for table, cols in self.db.meta.items():
            for c in cols:
                if not c.references:
                    continue
                rt, rc = c.references
                key = (rt, rc)
                if key not in pk_cache:
                    pk_cache[key] = {r[rc] for r in self.db[rt]}
                for r in self.db[table]:
                    v = r.get(c.name)
                    if v is not None and v not in pk_cache[key]:
                        self.add(table, r if table not in ("calculation_run_lines",) else r, "FK_BROKEN", "error",
                                 f"{table}.{c.name}={v!r} not found in {rt}.{rc}")
        wis = {(r["work_item_id"], r["version"]) for r in self.db["work_items"]}
        asm = {(r["assembly_id"], r["version"]) for r in self.db["assemblies"]}
        for r in self.db["work_item_components"]:
            if (r["work_item_id"], r["work_item_version"]) not in wis:
                self.add("work_item_components", r, "FK_BROKEN", "error", "work item version not found")
        for r in self.db["assembly_components"]:
            if (r["assembly_id"], r["assembly_version"]) not in asm:
                self.add("assembly_components", r, "FK_BROKEN", "error", "assembly version not found")
            if (r["work_item_id"], r["work_item_version"]) not in wis:
                self.add("assembly_components", r, "ASM_WI_MISSING", "error",
                         f"work item {r['work_item_id']} v{r['work_item_version']} not found")
        for t in self.db.meta:
            seen = set()
            for r in self.db[t]:
                k = pk_of(t, r) if t not in ("validation_issues",) else None
                if k is None:
                    continue
                if k in seen:
                    self.add(t, k, "ID_DUPLICATE", "error", "duplicate primary key")
                seen.add(k)

    # ---------------------------------------------------------------------- sources
    def _source(self, row) -> Optional[dict]:
        return self.sources.get(row.get("source_id"))

    def check_sources(self):
        for s in self.db["sources"]:
            if not s.get("evidence_quote"):
                self.add("sources", s, "SRC_NO_EVIDENCE", "warning", "source has no evidence quote")
            if s["reuse_status"] in NO_DATA_USE and s["review_status"] == "validated":
                self.add("sources", s, "SRC_PROHIBITED_VALIDATED", "error",
                         f"a source whose terms are '{s['reuse_status']}' cannot be 'validated' for data use")
            if s["verification_method"] == "synthetic_test_fixture" and self.production:
                self.add("sources", s, "SRC_SYNTHETIC_IN_PRODUCTION", "error", "synthetic test fixture present in production data")
            if s["review_status"] == "validated" and s["verification_method"] not in ("fetched_primary", "synthetic_test_fixture"):
                self.add("sources", s, "SRC_VALIDATED_WITHOUT_FETCH", "error",
                         "source marked validated although its primary document was never fetched")
        for t in SOURCE_TABLES:
            for r in self.db[t]:
                sid = r.get("source_id")
                if not sid or sid not in self.sources:
                    continue
                src = self.sources[sid]
                if src["reuse_status"] in NO_DATA_USE:
                    self.add(t, r, "SRC_PROHIBITED_IN_USE", "error", f"record uses source {sid} whose terms are '{src['reuse_status']}'")
                if src["verification_method"] == "synthetic_test_fixture" and self.production:
                    self.add(t, r, "SRC_SYNTHETIC_IN_PRODUCTION", "error", f"record uses synthetic fixture source {sid}")
                if r.get("review_status") == "validated" and src["verification_method"] not in ("fetched_primary", "synthetic_test_fixture"):
                    self.add(t, r, "VALIDATED_FROM_SNIPPET", "error",
                             "record is 'validated' but its source was only seen in search snippets")
        series = self.db.index("indices", "index_id")
        for r in self.db["index_values"]:
            ser = series.get(r["index_id"])
            src = self.sources.get(ser["source_id"]) if ser else None
            if src is None:
                continue
            if src["reuse_status"] in NO_DATA_USE:
                self.add("index_values", r, "SRC_PROHIBITED_IN_USE", "error", f"index value of series {r['index_id']} whose source {src['source_id']} is '{src['reuse_status']}'")
            if r.get("review_status") == "validated" and src["verification_method"] not in ("fetched_primary", "synthetic_test_fixture"):
                self.add("index_values", r, "VALIDATED_FROM_SNIPPET", "error", "index value is 'validated' but its series source was only seen in search snippets")
        for t in self.db.meta:
            for r in self.db[t]:
                if r.get("review_status") == "validated" and "reviewed_by" in r and not (r.get("reviewed_by") and r.get("reviewed_at")):
                    self.add(t, r, "VALIDATED_WITHOUT_REVIEWER", "error", "validated record without a reviewer and review time")

    # --------------------------------------------------------------------- products
    def check_products(self):
        for p in self.db["products"]:
            cat = self.categories.get(p["category_id"])
            req = (cat or {}).get("required_product_attributes") or []
            if not req:
                self.add("products", p, "PRD_CATEGORY_NOT_LEAF", "error", "category defines no required attributes; use a leaf category")
                continue
            try:
                key = spec_key(p["category_id"], p["spec_attributes"] or {}, req)
            except SpecError as e:
                self.add("products", p, "PRD_ATTR_MISSING", "error", str(e))
                continue
            if key != p["spec_key"]:
                self.add("products", p, "PRD_SPEC_KEY_MISMATCH", "error", "stored spec_key differs from recomputed key",
                         stored=p["spec_key"], recomputed=key)
            if p["content_unit_id"] not in self.units:
                self.add("products", p, "UNIT_UNKNOWN", "error", f"unknown content unit {p['content_unit_id']}")
        seen: dict[tuple, str] = {}
        for p in self.db["products"]:
            if p.get("mpn") and p.get("manufacturer"):
                k = (p["manufacturer"].lower(), p["mpn"].lower())
                if k in seen:
                    self.add("products", p, "PRD_DUP_MPN", "error", f"duplicate manufacturer+MPN with {seen[k]}")
                seen[k] = p["product_id"]
            if not p.get("mpn") and not p.get("brand"):
                self.add("products", p, "PRD_NO_IDENTITY", "warning", "no MPN and no brand: cannot be re-identified")

    # ----------------------------------------------------------------- observations
    def check_observations(self):
        by_spec_region: dict[tuple, list[tuple[dict, Decimal]]] = defaultdict(list)
        dupes: dict[tuple, str] = {}
        for o in self.db["price_observations"]:
            p = self.products.get(o["product_id"])
            if p is None:
                continue
            if o["pack_content_unit_id"] != p["content_unit_id"] or Decimal(o["pack_content_qty"]) != Decimal(p["content_qty"]):
                self.add("price_observations", o, "OBS_PACK_MISMATCH", "error",
                         "observation pack content differs from the product's pack (different SKU?)",
                         obs=f"{o['pack_content_qty']} {o['pack_content_unit_id']}", product=f"{p['content_qty']} {p['content_unit_id']}")
            if o["observed_at"] > self.today:
                self.add("price_observations", o, "OBS_FUTURE_DATE", "error", "observed_at is in the future")
            rts = _parse_ts(o["retrieved_at"])
            if rts is None:
                self.add("price_observations", o, "OBS_NAIVE_TIMESTAMP", "error", "retrieved_at has no time zone (or is unreadable): it would be read in the server time zone")
            elif rts < datetime(o["observed_at"].year, o["observed_at"].month, o["observed_at"].day, tzinfo=timezone.utc) - timedelta(days=1):
                self.add("price_observations", o, "OBS_RETRIEVED_BEFORE_OBSERVED", "error", "retrieved_at precedes observed_at")
            if (self.today - o["observed_at"]).days > self.policy["price_stale_days"]:
                self.add("price_observations", o, "OBS_STALE", "warning", f"{(self.today - o['observed_at']).days} days old",
                         threshold_days=self.policy["price_stale_days"], basis=DEFAULT_POLICY["price_stale_days"][1])
            if o["price_amount"] == 0:
                self.add("price_observations", o, "OBS_PRICE_ZERO", "warning", "zero price")
            if o["is_contractor_cost"] and o["price_channel"] in ("retail_public", "retail_promo", "manufacturer_msrp"):
                self.add("price_observations", o, "OBS_RETAIL_AS_CONTRACTOR", "error", "retail/MSRP price marked as contractor cost")
            if o.get("region_id") is None:
                self.add("price_observations", o, "OBS_NO_REGION", "warning", "no region_id: cannot be used by the engine (map ZIP to county first)")
            if o.get("sales_tax_included") is None or o.get("delivery_included") is None:
                self.add("price_observations", o, "OBS_TAX_DELIVERY_UNKNOWN", "info", "tax/delivery inclusion not recorded")
            k = (o["product_id"], o["source_id"], o.get("store_ref"), o.get("zip"), o["observed_at"], str(o["price_amount"]), o["price_channel"])
            if k in dupes:
                self.add("price_observations", o, "OBS_DUP", "warning", f"same product/store/day/price as {dupes[k]}")
            dupes[k] = o["observation_id"]
            if not o["promo_flag"] and o["price_channel"] != "manufacturer_msrp":
                by_spec_region[(p["spec_key"], o.get("region_id"))].append((o, Decimal(o["price_amount"]) / Decimal(o["pack_content_qty"])))
        for (key, reg), items in by_spec_region.items():
            latest: dict[str, tuple[dict, Decimal]] = {}
            for o, unit_price in items:
                cur = latest.get(o["product_id"])
                if cur is None or o["observed_at"] > cur[0]["observed_at"]:
                    latest[o["product_id"]] = (o, unit_price)
            if len(latest) >= 3:
                med = median([v[1] for v in latest.values()])
                for o, up in latest.values():
                    ratio = D(str(self.policy["price_outlier_ratio"]))
                    if med > 0 and (up > med * ratio or up < med / ratio):
                        self.add("price_observations", o, "OBS_OUTLIER", "warning",
                                 f"unit price {up} is >{ratio}x or <1/{ratio} of the median {med} for spec {key}", ratio=str(ratio),
                                 basis=DEFAULT_POLICY["price_outlier_ratio"][1])

    # ------------------------------------------------------------------------ labor
    def check_labor(self):
        rates = self.db.index("labor_rates", "labor_rate_id")
        tol = D(str(self.policy["loaded_sum_tol"]))
        for r in self.db["labor_rates"]:
            if r["rate_type"] in ("prevailing_wage", "federal_wage_determination") and r["use_context"] != "public_works_only":
                self.add("labor_rates", r, "LAB_PW_SCOPE", "error", "prevailing/federal rate must be public_works_only")
            if r["rate_type"] == "stat_wage" and r["includes_fringe"]:
                self.add("labor_rates", r, "LAB_STAT_INCLUDES_FRINGE", "error", "statistical wage cannot include fringe")
            if r["effective_to"] and r["effective_to"] < r["effective_from"]:
                self.add("labor_rates", r, "LAB_PERIOD", "error", "effective_to before effective_from")
            if (self.today - r["effective_from"]).days > self.policy["rate_stale_days"] and r["origin"] == "observed":
                self.add("labor_rates", r, "LAB_STALE", "warning", f"rate period starts {(self.today - r['effective_from']).days} days ago",
                         threshold_days=self.policy["rate_stale_days"], basis=DEFAULT_POLICY["rate_stale_days"][1])
            if r["origin"] == "observed" and not r["includes_overhead"] and not r["includes_profit"] and r["total_hr"] is not None \
                    and r["includes_fringe"] and r["includes_payroll_taxes"] and r["includes_workers_comp"] and r["rate_type"] != "company_actual":
                parts = sum((D(r[k] or 0) for k in ("base_wage_hr", "fringe_hr", "payroll_tax_hr", "workers_comp_hr", "other_employer_cost_hr")), D(0))
                if all(r[k] is not None for k in ("fringe_hr", "payroll_tax_hr", "workers_comp_hr")) and abs(parts - D(r["total_hr"])) > tol:
                    self.add("labor_rates", r, "LAB_TOTAL_MISMATCH", "error", "fully loaded source rate: total_hr differs from the sum of its components",
                             parts=str(parts), total=str(r["total_hr"]))
            if r["rate_type"] == "loaded_employer_cost":
                parts = sum((D(r[k] or 0) for k in ("base_wage_hr", "fringe_hr", "payroll_tax_hr", "workers_comp_hr", "other_employer_cost_hr")), D(0))
                if r["total_hr"] is None or abs(parts - D(r["total_hr"])) > tol:
                    self.add("labor_rates", r, "LAB_LOADED_SUM", "error", "loaded total does not equal the sum of its components",
                             parts=str(parts), total=str(r["total_hr"]))
                for sid in r["derived_from"] or []:
                    src = rates.get(sid)
                    if not src:
                        continue
                    if src["includes_fringe"] and D(r["fringe_hr"] or 0) != D(src["fringe_hr"] or 0):
                        self.add("labor_rates", r, "LAB_DOUBLE_FRINGE", "error",
                                 "source rate already includes fringe but the loaded rate carries a different fringe amount",
                                 source_fringe=str(src["fringe_hr"]), loaded_fringe=str(r["fringe_hr"]))
                    if src["includes_payroll_taxes"] and D(r["payroll_tax_hr"] or 0) != D(src["payroll_tax_hr"] or 0):
                        self.add("labor_rates", r, "LAB_DOUBLE_PAYROLL_TAX", "error", "payroll taxes added on top of a rate that includes them")
                    if src["includes_workers_comp"] and D(r["workers_comp_hr"] or 0) != D(src["workers_comp_hr"] or 0):
                        self.add("labor_rates", r, "LAB_DOUBLE_WC", "error", "workers' comp added on top of a rate that includes it")
        for b in self.db["burden_rates"]:
            if b["basis"] == "pct_of_wages" and b["rate"] is not None and Decimal(b["rate"]) > 1:
                self.add("burden_rates", b, "BRD_PCT_GT_1", "error",
                         f"pct_of_wages rate {b['rate']} > 1: store percentages as fractions (0.062 = 6.2%)")

    # ----------------------------------------------------------- equipment & crews
    def check_equipment_and_crews(self):
        for e in self.db["equipment_rates"]:
            if e["fuel_cost_hr"] is not None and e["operating_cost_hr"] is not None and e["fuel_included"]:
                self.add("equipment_rates", e, "EQP_FUEL_DOUBLE", "warning",
                         "fuel_cost_hr and operating_cost_hr both present while fuel_included=true: fuel may be counted twice")
        erates = self.db.index("equipment_rates", "equipment_rate_id")
        members = defaultdict(list)
        for m in self.db["crew_members"]:
            members[m["crew_id"]].append(m)
        eq_by_type: dict[str, list[dict]] = defaultdict(list)
        for e in self.db["equipment_rates"]:
            eq_by_type[e["equipment_type_code"]].append(e)
        for cid, ms in members.items():
            has_operator = any(m["member_kind"] == "labor" and (m["is_operator"] or m["trade_code"] == "TR-OPR") for m in ms)
            for m in ms:
                if m["member_kind"] != "equipment":
                    continue
                pinned = erates.get(m["equipment_rate_id"]) if m["equipment_rate_id"] else None
                if has_operator and pinned and pinned["operator_included"]:
                    self.add("crew_members", m, "CREW_OPERATOR_DOUBLE", "error",
                             "operator is listed as crew labor AND included in the pinned equipment rate")
                elif has_operator and not pinned and any(e["operator_included"] for e in eq_by_type[m["equipment_type_code"]]):
                    self.add("crew_members", m, "CREW_OPERATOR_AMBIGUOUS", "warning",
                             "some rates for this equipment include an operator; engine will refuse those for this crew")
        prods = self.db.index("productivity_observations", "productivity_id")
        for p in self.db["productivity_observations"]:
            if p["origin"] != "observed" or not p["crew_id"] or p["crew_size"] is None:
                continue
            size = sum(D(m["quantity"]) for m in members.get(p["crew_id"], []) if m["member_kind"] == "labor")
            if size and size != D(p["crew_size"]):
                self.add("productivity_observations", p, "CREW_SIZE_MISMATCH", "error",
                         f"norm observed for crew size {p['crew_size']} but crew {p['crew_id']} has {size}")

    # ----------------------------------------------------------------- productivity
    def check_productivity(self):
        for p in self.db["productivity_observations"]:
            if p["output_unit_id"] not in self.units:
                self.add("productivity_observations", p, "UNIT_UNKNOWN", "error", f"unknown unit {p['output_unit_id']}")
            if p["origin"] == "observed" and p["person_hours_per_unit_reported"] is not None \
                    and p["crew_size"] is not None and p["shift_hours"] is not None and p["daily_output"] is not None:
                derived = D(p["crew_size"]) * D(p["shift_hours"]) / D(p["daily_output"])
                rep = D(p["person_hours_per_unit_reported"])
                tol = D(str(self.policy["productivity_recon_tol"]))
                if abs(derived - rep) / rep > tol:
                    self.add("productivity_observations", p, "PROD_RECON", "error",
                             f"reported person-hours/unit differs from crew x shift / daily output by more than {tol * 100}%",
                             reported=str(rep), derived=str(derived), basis=DEFAULT_POLICY["productivity_recon_tol"][1])

    # ------------------------------------------------------------------- work items
    def check_work_items(self):
        comps_by = defaultdict(list)
        for c in self.db["work_item_components"]:
            comps_by[(c["work_item_id"], c["work_item_version"])].append(c)
        specs = defaultdict(list)
        for p in self.db["products"]:
            specs[p["spec_key"]].append(p)
        prods = self.db.index("productivity_observations", "productivity_id")
        for w in self.db["work_items"]:
            key = (w["work_item_id"], w["version"])
            if not w["spec_attributes"]:
                self.add("work_items", w, "WI_SPEC_EMPTY", "error", "work item has no measurable spec")
            if w["output_unit_id"] not in self.units:
                self.add("work_items", w, "UNIT_UNKNOWN", "error", f"unknown output unit {w['output_unit_id']}")
            bad = GLOBAL_EXCLUDED_TOKENS & set(w["included_scope"] or [])
            if bad:
                self.add("work_items", w, "WI_GLOBAL_SCOPE_INCLUDED", "error",
                         f"shared activities must be excluded, not included: {sorted(bad)}")
            missing_excl = GLOBAL_EXCLUDED_TOKENS - set(w["excluded_scope"] or [])
            if missing_excl:
                self.add("work_items", w, "WI_GLOBAL_SCOPE_NOT_EXCLUDED", "warning", f"not excluded explicitly: {sorted(missing_excl)}")
            for name, vals in (("included_scope", w["included_scope"]), ("excluded_scope", w["excluded_scope"])):
                dup = sorted({t for t in vals or [] if (vals or []).count(t) > 1})
                if dup:
                    self.add("work_items", w, "WI_SCOPE_DUPLICATE_TOKEN", "warning", f"duplicate token(s) in {name}: {dup}")
            both = sorted(set(w["included_scope"] or []) & set(w["excluded_scope"] or []))
            if both:
                self.add("work_items", w, "WI_SCOPE_CONTRADICTION", "error", f"scope token(s) both included and excluded: {both}")
            cs = comps_by.get(key, [])
            if not any(c["component_kind"] == "labor" for c in cs):
                self.add("work_items", w, "WI_NO_LABOR", "warning", "no labor component")
            tag_owner: dict[str, str] = {}
            mspecs = (w["spec_attributes"] or {}).get("material_specs")
            by_line = {m.get("line"): m for m in mspecs or []} if isinstance(mspecs, list) else {}
            used_lines = set()
            for c in cs:
                for t in c["cost_tags"] or []:
                    if t in tag_owner and tag_owner[t] != c["component_id"]:
                        self.add("work_item_components", c, "WI_DUP_TAG", "error", f"cost tag '{t}' also on {tag_owner[t]}: double-counting suspicion")
                    tag_owner.setdefault(t, c["component_id"])
                if c["qty_unit_id"] and c["qty_unit_id"] not in self.units:
                    self.add("work_item_components", c, "UNIT_UNKNOWN", "error", f"unknown unit {c['qty_unit_id']}")
                if c["component_kind"] in ("material", "other_direct") and c["product_spec_key"] and c["qty_unit_id"]:
                    for p in specs.get(c["product_spec_key"], []):
                        if not self.units.compatible(c["qty_unit_id"], p["content_unit_id"]) and c["qty_mode"] == "fixed":
                            self.add("work_item_components", c, "WI_UNIT_MISMATCH", "error",
                                     f"component unit {c['qty_unit_id']} cannot be converted from product content unit {p['content_unit_id']}")
                if c["productivity_id"]:
                    pr = prods.get(c["productivity_id"])
                    if pr and pr["output_unit_id"] in self.units and not self.units.compatible(pr["output_unit_id"], w["output_unit_id"]):
                        self.add("work_item_components", c, "WI_PRODUCTIVITY_UNIT", "error",
                                 f"productivity unit {pr['output_unit_id']} incompatible with work item unit {w['output_unit_id']}")
                if c["waste_factor"] is not None and not c["waste_basis"]:
                    self.add("work_item_components", c, "WI_WASTE_NO_BASIS", "error", "waste factor without a stated basis")
                if c.get("consumption_selector"):
                    badk = [k for k in c["consumption_selector"] if k not in ("film_thickness", "substrate_condition", "application_method", "conditions")]
                    if badk or c["qty_mode"] != "from_product_consumption":
                        self.add("work_item_components", c, "WI_SELECTOR_INVALID", "error", "consumption_selector has unknown keys or the component is not coverage based", keys=badk)
                if c["component_kind"] == "equipment" and c.get("crew_id"):
                    types = {m["equipment_type_code"] for m in self.db["crew_members"] if m["crew_id"] == c["crew_id"] and m["member_kind"] == "equipment"}
                    if types and c["equipment_type_code"] not in types:
                        self.add("work_item_components", c, "WI_EQUIPMENT_NOT_IN_CREW", "error",
                                 f"equipment component {c['equipment_type_code']} is not a member of crew {c['crew_id']}")
                # the measurable spec of the work item must say what the component prices
                if c["component_kind"] in ("material", "other_direct") and c["product_spec_key"] and isinstance(mspecs, list):
                    entry = by_line.get(c["line_no"])
                    used_lines.add(c["line_no"])
                    if entry is None:
                        self.add("work_item_components", c, "WI_SPEC_COMPONENT_MISMATCH", "error", "work item spec_attributes.material_specs has no entry for this component line")
                    elif entry.get("spec_key") != c["product_spec_key"]:
                        self.add("work_item_components", c, "WI_SPEC_COMPONENT_MISMATCH", "error",
                                 "component prices a different spec line than the work item's stated specification",
                                 component=c["product_spec_key"], work_item_spec=entry.get("spec_key"))
                    else:
                        cat = self.categories.get(c["product_spec_key"].split("|")[0])
                        try:
                            again = spec_key(cat["category_id"], entry.get("attributes") or {}, cat["required_product_attributes"]) if cat else None
                        except SpecError:
                            again = None
                        if again != entry["spec_key"]:
                            self.add("work_item_components", c, "WI_SPEC_ATTRS_MISMATCH", "error",
                                     "material_specs attributes do not reproduce the stated spec_key", recomputed=again, stated=entry["spec_key"])
            if mspecs is not None and not isinstance(mspecs, list):
                self.add("work_items", w, "WI_SPEC_COMPONENT_MISMATCH", "error", "material_specs must be a list")
            for ln in sorted(set(by_line) - used_lines):
                self.add("work_items", w, "WI_SPEC_ORPHAN", "error", f"material_specs line {ln} matches no material component")
            if isinstance(mspecs, list) is False and any(c["component_kind"] in ("material", "other_direct") and c["product_spec_key"] for c in cs) \
                    and self.production:
                self.add("work_items", w, "WI_SPEC_COMPONENT_MISMATCH", "error", "priced material components but no material_specs in the work item spec")

    # -------------------------------------------------------------------- assemblies
    def check_assemblies(self):
        wis = self.db.index("work_items", "work_item_id", "version")
        comps = defaultdict(list)
        for c in self.db["assembly_components"]:
            comps[(c["assembly_id"], c["assembly_version"])].append(c)
        for a in self.db["assemblies"]:
            if not a["spec_attributes"]:
                self.add("assemblies", a, "ASM_SPEC_EMPTY", "error", "assembly has no measurable spec (no generic averaged assemblies)")
            owner: dict[str, str] = {}
            tag_owner: dict[str, str] = {}
            child_included: set[str] = set()
            child_excluded: set[str] = set()
            cs = comps.get((a["assembly_id"], a["version"]), [])
            for c in cs:
                for t in c["cost_tags"] or []:
                    if t in tag_owner and tag_owner[t] != c["assembly_component_id"]:
                        self.add("assembly_components", c, "ASM_DUP_TAG", "error", f"cost tag '{t}' also on {tag_owner[t]}: double-counting suspicion")
                    tag_owner.setdefault(t, c["assembly_component_id"])
                wi = wis.get((c["work_item_id"], c["work_item_version"]))
                if not wi:
                    continue
                child_included |= set(wi["included_scope"] or [])
                child_excluded |= set(wi["excluded_scope"] or [])
                if not self.units.compatible(c["qty_unit_id"], wi["output_unit_id"]):
                    self.add("assembly_components", c, "ASM_UNIT_MISMATCH", "error",
                             f"component unit {c['qty_unit_id']} vs work item unit {wi['output_unit_id']}")
                for t in wi["included_scope"] or []:
                    if t in owner and owner[t] != wi["work_item_id"]:
                        self.add("assemblies", a, "ASM_SCOPE_OVERLAP", "error",
                                 f"scope '{t}' included by both {owner[t]} and {wi['work_item_id']}: double counting")
                    owner.setdefault(t, wi["work_item_id"])
            if not cs:
                self.add("assemblies", a, "ASM_EMPTY", "error", "assembly has no components")
                continue
            # inclusions / exclusions must be derived from what the children really price
            inc, exc = set(a["included_scope"] or []), set(a["excluded_scope"] or [])
            if not inc:
                self.add("assemblies", a, "ASM_NO_INCLUSIONS", "error", "assembly states no inclusions (included_scope is empty)")
            stray = sorted(inc - child_included)
            if stray:
                self.add("assemblies", a, "ASM_INCLUDED_NOT_PRICED", "error", f"assembly claims to include {stray} but no child work item prices it")
            surfaced = sorted((child_excluded - child_included) - exc)
            if surfaced:
                self.add("assemblies", a, "ASM_CHILD_EXCLUSION_NOT_SURFACED", "error",
                         f"exclusions of child work items are missing from the assembly's excluded_scope: {surfaced}")
            clash = sorted(inc & exc)
            if clash:
                self.add("assemblies", a, "ASM_SCOPE_CONTRADICTION", "error", f"scope token(s) both included and excluded: {clash}")
            # the assembly's stated composition must be its components
            stated = (a["spec_attributes"] or {}).get("work_items")
            actual = sorted((c["work_item_id"], c["work_item_version"], D(str(c["qty_per_assembly_unit"]))) for c in cs)
            if isinstance(stated, list):
                try:
                    claim = sorted((x["work_item_id"], x["version"], D(str(x["qty_per_assembly_unit"]))) for x in stated)
                except (KeyError, TypeError):
                    claim = None
                if claim != actual:
                    self.add("assemblies", a, "ASM_SPEC_CHILD_MISMATCH", "error", "assembly spec_attributes.work_items differs from its component rows",
                             stated=[list(map(str, t)) for t in claim or []], actual=[list(map(str, t)) for t in actual])
            elif self.production:
                self.add("assemblies", a, "ASM_SPEC_CHILD_MISMATCH", "error", "assembly spec_attributes lists no work_items to compare with its components")

    # ------------------------------------------------------------------ assumptions
    def check_assumptions(self):
        approved: dict[str, list[dict]] = defaultdict(list)
        for a in self.db["assumptions"]:
            if a["status"] == "approved":
                approved[a["applies_to_ref"]].append(a)
                if not a.get("expires_on"):
                    self.add("assumptions", a, "ASU_NO_EXPIRY", "error", "approved assumption without an expiry date")
                if a.get("approved_by") and a["approved_by"].strip().lower() == a["proposed_by"].strip().lower():
                    self.add("assumptions", a, "ASU_SELF_APPROVED", "error", "assumption approved by its proposer")
        for ref, rows in approved.items():
            if len(rows) > 1:
                self.add("assumptions", rows[1], "ASU_DUPLICATE_APPROVED", "error", f"{len(rows)} approved assumptions for '{ref}'")

    # -------------------------------------------------------------- calculation runs
    def check_calculation_runs(self, engine: Optional[Engine] = None):
        lines = defaultdict(list)
        for ln in self.db["calculation_run_lines"]:
            lines[ln["run_id"]].append(ln)
        asu = self.db.index("assumptions", "assumption_id")
        pk_sets: dict[str, set] = {}

        def exists(tbl: str, rid: str) -> bool:
            if tbl not in pk_sets:
                pk_sets[tbl] = {pk_of(tbl, x) for x in self.db[tbl]}
            return rid in pk_sets[tbl]
        for r in self.db["calculation_runs"]:
            params = r.get("parameters") or {}
            if r["status"] == "complete" and r["missing_inputs"]:
                self.add("calculation_runs", r, "CALC_COMPLETE_HAS_MISSING", "error", "complete run lists missing inputs")
            if r["mode"] == "strict" and r["has_assumptions"]:
                self.add("calculation_runs", r, "CALC_STRICT_ASSUMED", "error", "strict run used assumptions")
            if r["price_basis"] == "retail_proxy" and r["target_type"] != "markup" and not params.get("accept_retail_proxy"):
                self.add("calculation_runs", r, "CALC_RETAIL_WITHOUT_OPT_IN", "error", "run rests on retail prices but accept_retail_proxy was not set")
            if r["target_type"] != "markup" and params.get("min_review") and r["input_review_floor"] != params["min_review"]:
                self.add("calculation_runs", r, "CALC_REVIEW_FLOOR_MISMATCH", "error", "input_review_floor differs from the run parameter min_review")
            ls = lines.get(r["run_id"], [])
            if r["status"] == "complete" and r["target_type"] != "markup":
                total = sum((D(str(ln["extended_cost"])) for ln in ls if ln["line_kind"] in ("material", "labor", "equipment", "other_direct", "assembly_component")
                             and ln["extended_cost"] is not None), D(0))
                if r["direct_cost_total"] is None or abs(total - D(str(r["direct_cost_total"]))) > D("0.0005"):
                    self.add("calculation_runs", r, "CALC_TOTAL_NOT_LINE_SUM", "error", "stored total differs from the sum of its lines",
                             total=str(total), stored=str(r["direct_cost_total"]))
            for ln in ls:
                if not ln["formula"]:
                    self.add("calculation_run_lines", ln, "CALC_LINE_NO_FORMULA", "error", "line without formula")
                for inp in ln["inputs"] or []:
                    tbl, rid = inp.get("table"), inp.get("id")
                    if tbl in self.db.tables and tbl != "assumptions":
                        try:
                            ok = exists(tbl, rid)
                        except KeyError:
                            ok = True
                        if not ok:
                            self.add("calculation_run_lines", ln, "CALC_INPUT_NOT_FOUND", "error", f"input {tbl}:{rid} does not exist")
                    if tbl == "assumptions":
                        a = asu.get(rid)
                        if a is None:
                            self.add("calculation_run_lines", ln, "CALC_INPUT_NOT_FOUND", "error", f"input assumptions:{rid} does not exist")
                        elif a["status"] != "approved" and r["status"] == "complete":
                            self.add("calculation_run_lines", ln, "CALC_ASSUMPTION_NOT_APPROVED", "error", f"complete run uses assumption {rid} with status {a['status']}")
                    if inp.get("review_status") in ("flagged", "rejected"):
                        self.add("calculation_run_lines", ln, "CALC_INPUT_FLAGGED", "error", f"uses {inp.get('review_status')} input {tbl}:{rid}")
            if r["status"] == "complete" and engine is not None and r["target_type"] in ("unit_cost", "assembly"):
                p = RunParams.from_canonical(params, run_at=r["run_at"])
                res = (engine.unit_cost if r["target_type"] == "unit_cost" else engine.assembly_cost)(r["target_id"], r["target_version"], p)
                if res.total != r["direct_cost_total"]:
                    self.add("calculation_runs", r, "CALC_NOT_REPRODUCIBLE", "error",
                             "recomputation gives a different total", stored=str(r["direct_cost_total"]), recomputed=str(res.total))
                elif res.run["run_id"] != r["run_id"]:
                    self.add("calculation_runs", r, "CALC_RUN_ID_CHANGED", "warning", "recomputation gives the same total but a different run_id (inputs or code changed)")


def validate(db: Database, today: Optional[date] = None, production: bool = True, engine: Optional[Engine] = None,
             policy: Optional[dict] = None) -> list[Issue]:
    v = Validator(db, today, production, policy)
    v.run()
    if engine is not None:
        v.check_calculation_runs(engine)
    return v.issues


def promote_validated(db: Database, issues: list[Issue], reviewer: str, when: str) -> dict[str, int]:
    """Strict promotion of OBSERVED records to review_status='validated'. Returns counts per table.

    A row is promoted only if (1) it has no error-level issue, (2) its source was really fetched (fetched_primary - a search
    snippet can never be promoted) and its terms allow data use, (3) every evidence field required for its table is filled.
    index_values inherit the source of their series. Every promotion is logged in review_events."""
    sources = db.index("sources", "source_id")
    series = db.index("indices", "index_id")
    bad = {(i.record_table, i.record_id) for i in issues if i.severity == "error"}
    promoted: dict[str, int] = defaultdict(int)
    for t in OBSERVED_TABLES:
        for r in db[t]:
            if r.get("review_status") != "unreviewed" or r.get("origin") != "observed":
                continue
            rid = pk_of(t, r)
            if (t, rid) in bad:
                continue
            sid = r.get("source_id") or (series.get(r.get("index_id"), {}) or {}).get("source_id")
            src = sources.get(sid)
            if not src or src["verification_method"] != "fetched_primary" or src["reuse_status"] in NO_DATA_USE:
                continue
            if any(not r.get(f) for f in EVIDENCE_FIELDS.get(t, ())):
                continue
            r["review_status"] = "validated"
            r["reviewed_by"] = reviewer
            r["reviewed_at"] = when
            db.add("review_events", {"record_table": t, "record_id": rid, "old_status": "unreviewed", "new_status": "validated",
                                     "changed_by": reviewer, "changed_at": when, "db_user": "costdb.promote_validated"})
            promoted[t] += 1
    return dict(promoted)
