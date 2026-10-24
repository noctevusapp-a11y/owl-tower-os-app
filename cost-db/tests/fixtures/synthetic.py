"""SYNTHETIC TEST FIXTURES — NOT MARKET DATA.

Every number here is deliberately round and invented so that expected results can be computed by hand.
All ids start with TEST- and the sources carry verification_method='synthetic_test_fixture'; the validator rejects
any of these in production data and the data/ CSVs are scanned for them by tests/test_data_gates.py.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from costdb.store import Database  # noqa: E402

_spec = importlib.util.spec_from_file_location("gen_pilot_definitions", ROOT / "pipeline" / "scripts" / "gen_pilot_definitions.py")
pilot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pilot)       # builds MATS/WORK_ITEMS in memory; main() is not executed

AS_OF = date(2026, 10, 24)
RUN_AT = "2026-10-24T00:00:00+00:00"
REGION = "REG-CA-037"
SRC = "TEST-SRC-SYN"
WI = "WI-DRY-001"          # real definition: hang 1/2 in regular gypsum board on wood studs, walls (unit SF)


def real_db() -> Database:
    return Database.load_csv_dir()


def _blank(db: Database, table: str, **kw) -> dict:
    return db.add(table, kw)


def add_source(db: Database, sid: str = SRC, method: str = "synthetic_test_fixture", review: str = "validated",
               reuse: str = "open_license") -> None:
    db.add("sources", {
        "source_id": sid, "title": "SYNTHETIC TEST FIXTURE - not market data", "owner": "Owl Tower tests", "source_kind": "internal",
        "url": None, "data_url": None, "data_provided": "invented round numbers", "geography": None, "period_covered": None,
        "edition": None, "access_format": None, "requires_registration": None, "requires_payment": None, "access_notes": None,
        "reuse_status": reuse, "reuse_terms": None, "reuse_terms_url": None, "limitations": "synthetic", "update_frequency": None,
        "quality_tier": "A", "reachability_from_build_env": "not_tested", "reachability_checked_at": None,
        "verification_method": method, "evidence_quote": "synthetic", "evidence_url": None, "origin": "observed",
        "review_status": review, "reviewed_by": "tests", "reviewed_at": None, "registered_at": AS_OF, "notes": None})


def add_product(db: Database, pid: str, mat_key: str, content_qty, content_unit: str, brand: str, mpn: str, source: str = SRC):
    m = pilot.MATS[mat_key]
    return db.add("products", {
        "product_id": pid, "category_id": m["cat"], "name": f"TEST {m['desc']}", "brand": brand, "manufacturer": brand, "mpn": mpn,
        "description": None, "spec_attributes": m["attrs"], "spec_key": m["spec_key"], "standards": [],
        "sale_unit_label": m["sale"], "content_qty": D(str(content_qty)), "content_unit_id": content_unit, "content_note": None,
        "source_id": source, "source_locator": "synthetic", "evidence_excerpt": "synthetic", "origin": "observed",
        "review_status": "validated", "reviewed_by": "tests", "reviewed_at": None, "created_at": None, "notes": None})


def add_obs(db: Database, oid: str, pid: str, price, qty, unit: str, region: str = REGION, observed: date = date(2026, 9, 1),
            channel: str = "retail_public", review: str = "validated", promo: bool = False, source: str = SRC):
    return db.add("price_observations", {
        "observation_id": oid, "product_id": pid, "source_id": source, "retailer_sku": "T-" + oid[-4:], "store_ref": "TEST STORE",
        "zip": "90245", "region_id": region, "observed_at": observed, "retrieved_at": f"{observed.isoformat()}T12:00:00+00:00",
        "price_amount": D(str(price)), "currency": "USD", "original_price_text": f"${price}", "price_channel": channel,
        "is_contractor_cost": False, "sold_as_label": "pack", "pack_content_qty": D(str(qty)), "pack_content_unit_id": unit,
        "availability": "in_stock", "delivery_included": False, "sales_tax_included": False, "promo_flag": promo,
        "qty_limit_text": None, "qty_tier_min": None, "url": None, "source_locator": "synthetic",
        "evidence_excerpt": f"${price}", "raw_file_sha256": None, "capture_method": "manual_browser", "captured_by": "tests",
        "origin": "observed", "review_status": review, "reviewed_by": None, "reviewed_at": None, "created_at": None, "notes": None})


def add_labor_actual(db: Database, rid: str, trade: str, total, region: str = REGION, review: str = "validated"):
    return db.add("labor_rates", {
        "labor_rate_id": rid, "rate_type": "company_actual", "trade_code": trade, "classification_raw": "TEST " + trade,
        "soc_code": None, "statistic": "actual", "region_id": region, "base_wage_hr": D(str(total)), "fringe_hr": None,
        "fringe_breakdown": None, "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None,
        "total_hr": D(str(total)), "includes_fringe": True, "includes_payroll_taxes": True, "includes_workers_comp": True,
        "wage_basis": "straight_time", "project_type": "n/a", "use_context": "employer_internal", "apprentice": False,
        "determination_ref": None, "effective_from": date(2026, 1, 1), "effective_to": None, "retrieved_at": RUN_AT,
        "derived_from": None, "calc_run_id": None, "source_id": SRC, "source_locator": "synthetic", "evidence_excerpt": "synthetic",
        "raw_file_sha256": None, "origin": "observed", "review_status": review, "reviewed_by": None, "reviewed_at": None,
        "created_at": None, "notes": None})


def set_crew(db: Database, crew_id: str, shift, members: list[tuple]):
    """members: (kind, code, qty, is_operator). Turns the real placeholder crew into an observed synthetic crew."""
    for c in db["crews"]:
        if c["crew_id"] == crew_id:
            c.update({"origin": "observed", "shift_hours": D(str(shift)), "source_id": SRC, "source_locator": "synthetic"})
    db.tables["crew_members"] = [m for m in db["crew_members"] if m["crew_id"] != crew_id]
    for i, (kind, code, qty, op) in enumerate(members, 1):
        db.add("crew_members", {"crew_member_id": f"TEST-CMB-{crew_id[-6:]}{i}", "crew_id": crew_id, "member_kind": kind,
                                "trade_code": code if kind == "labor" else None,
                                "equipment_type_code": code if kind == "equipment" else None, "labor_rate_id": None,
                                "equipment_rate_id": None, "quantity": D(str(qty)), "hours_per_shift": None,
                                "is_operator": op, "notes": None})


def set_productivity(db: Database, work_item_id: str, crew_size, shift, daily_output, unit: str = "SF", review: str = "validated"):
    for p in db["productivity_observations"]:
        if p["work_item_id"] == work_item_id:
            p.update({"origin": "observed", "source_id": SRC, "source_doc": "SYNTHETIC", "source_edition": "n/a",
                      "source_page": "0", "source_table": "t", "source_context": "synthetic test", "evidence_excerpt": "synthetic",
                      "retrieved_at": RUN_AT, "crew_size": D(str(crew_size)), "shift_hours": D(str(shift)),
                      "daily_output": D(str(daily_output)), "output_unit_id": unit, "missing_reason": None,
                      "review_status": review,
                      "person_hours_per_unit_derived": D(str(crew_size)) * D(str(shift)) / D(str(daily_output))})


def set_waste(db: Database, work_item_id: str, mapping: dict[str, tuple], origin: str = "observed"):
    """mapping: spec_key-or-description-substring -> (waste, basis)."""
    for c in db["work_item_components"]:
        if c["work_item_id"] != work_item_id or c["component_kind"] not in ("material", "other_direct"):
            continue
        for needle, (w, basis) in mapping.items():
            if needle in (c["product_spec_key"] or "") or needle in c["description"]:
                c["waste_factor"] = D(str(w)); c["waste_origin"] = origin; c["waste_basis"] = basis


def priced_drywall_db() -> Database:
    """Real definitions + synthetic inputs sufficient to price WI-DRY-001 in strict mode.

    Hand calculation (per SF of board):
      board : 1 SF x (1+0.10) x ($12.80 / 32 SF = $0.40/SF)                     = 0.44
      screws: 0.75 EA x (1+0.05) x ($5.00 / 500 EA = $0.01/EA)                  = 0.007875
      labor : crew (2 x $40 + 1 x $30) x 8 h = $880 per shift / 1600 SF         = 0.55
      total                                                                       = 0.997875
    """
    db = real_db()
    add_source(db)
    add_product(db, "TEST-PRD-BOARDA", "gyp_half_reg_4x8", 32, "SF", "TESTBRAND-A", "TB-A-1")
    add_product(db, "TEST-PRD-SCREW", "ds_coarse_125", 500, "EA", "TESTBRAND-S", "TS-1")
    add_obs(db, "TEST-OBS-BOARDA", "TEST-PRD-BOARDA", "12.80", 32, "SF")
    add_obs(db, "TEST-OBS-SCREW", "TEST-PRD-SCREW", "5.00", 500, "EA")
    add_labor_actual(db, "TEST-LRT-DRYW", "TR-DRYW", 40)
    add_labor_actual(db, "TEST-LRT-LAB", "TR-LAB", 30)
    set_crew(db, "CRW-DRY-HANG", 8, [("labor", "TR-DRYW", 2, False), ("labor", "TR-LAB", 1, False)])
    set_productivity(db, WI, 3, 8, 1600)
    set_waste(db, WI, {"CAT-DRY-BRD": (0.10, "TEST fixture"), "CAT-FRM-FAS": (0.05, "TEST fixture")})
    return db


def params(**kw):
    from costdb.calc import RunParams
    base = dict(region_id=REGION, as_of=AS_OF, mode="strict", min_review="validated", labor_basis="company_actual",
                allow_synthetic=True, run_at=RUN_AT)
    base.update(kw)
    return RunParams(**base)


def clone(db: Database) -> Database:
    return copy.deepcopy(db)
