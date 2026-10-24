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
        "review_status": review, "reviewed_by": "tests", "reviewed_at": RUN_AT if review == "validated" else None, "registered_at": AS_OF, "notes": None})


def add_product(db: Database, pid: str, mat_key: str, content_qty, content_unit: str, brand: str, mpn: str, source: str = SRC):
    m = pilot.MATS[mat_key]
    return db.add("products", {
        "product_id": pid, "category_id": m["cat"], "name": f"TEST {m['desc']}", "brand": brand, "manufacturer": brand, "mpn": mpn,
        "description": None, "spec_attributes": m["attrs"], "spec_key": m["spec_key"], "standards": [],
        "sale_unit_label": m["sale"], "content_qty": D(str(content_qty)), "content_unit_id": content_unit, "content_note": None,
        "source_id": source, "source_locator": "synthetic", "evidence_excerpt": "synthetic", "origin": "observed",
        "review_status": "validated", "reviewed_by": "tests", "reviewed_at": RUN_AT, "created_at": None, "notes": None})


def _rev(review: str) -> dict:
    return {"reviewed_by": "tests", "reviewed_at": RUN_AT} if review == "validated" else {"reviewed_by": None, "reviewed_at": None}


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
        "origin": "observed", "review_status": review, **_rev(review), "created_at": None, "notes": None})


def add_labor_actual(db: Database, rid: str, trade: str, total, region: str = REGION, review: str = "validated"):
    return db.add("labor_rates", {
        "labor_rate_id": rid, "rate_type": "company_actual", "trade_code": trade, "classification_raw": "TEST " + trade,
        "soc_code": None, "statistic": "actual", "region_id": region, "base_wage_hr": D(str(total)), "fringe_hr": None,
        "fringe_breakdown": None, "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None,
        "total_hr": D(str(total)), "includes_fringe": True, "includes_payroll_taxes": True, "includes_workers_comp": True,
        "wage_basis": "straight_time", "project_type": "n/a", "use_context": "employer_internal", "apprentice": False,
        "determination_ref": None, "effective_from": date(2026, 1, 1), "effective_to": None, "retrieved_at": RUN_AT,
        "derived_from": None, "calc_run_id": None, "source_id": SRC, "source_locator": "synthetic", "evidence_excerpt": "synthetic",
        "raw_file_sha256": None, "origin": "observed", "review_status": review, **_rev(review),
        "created_at": None, "notes": None})


def set_crew(db: Database, crew_id: str, shift, members: list[tuple]):
    """members: (kind, code, qty, is_operator). Turns the real placeholder crew into an observed synthetic crew."""
    for c in db["crews"]:
        if c["crew_id"] == crew_id:
            c.update({"origin": "observed", "shift_hours": D(str(shift)), "source_id": SRC, "source_locator": "synthetic",
                      "review_status": "validated", **_rev("validated")})
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
                      "review_status": review, **_rev(review),
                      "person_hours_per_unit_derived": D(str(crew_size)) * D(str(shift)) / D(str(daily_output))})


def set_waste(db: Database, work_item_id: str, mapping: dict[str, tuple], origin: str = "observed"):
    """mapping: spec_key-or-description-substring -> (waste, basis)."""
    for c in db["work_item_components"]:
        if c["work_item_id"] != work_item_id or c["component_kind"] not in ("material", "other_direct"):
            continue
        for needle, (w, basis) in mapping.items():
            if needle in (c["product_spec_key"] or "") or needle in c["description"]:
                c["waste_factor"] = D(str(w)); c["waste_origin"] = origin; c["waste_basis"] = basis


def validate_definitions(db: Database) -> None:
    """Test fixture: mark every (real) work-item/assembly definition as reviewed so that strict runs can complete."""
    for t in ("work_items", "assemblies"):
        for r in db[t]:
            r.update({"review_status": "validated", "valid_from": date(2026, 1, 1), **_rev("validated")})


def priced_drywall_db() -> Database:
    """Real definitions + synthetic inputs sufficient to price WI-DRY-001 in strict mode.

    Hand calculation (per SF of board):
      board : 1 SF x (1+0.10) x ($12.80 / 32 SF = $0.40/SF)                     = 0.44
      screws: 0.875 EA x (1+0.05) x ($5.00 / 500 EA = $0.01/EA)                 = 0.0091875
      labor : crew (2 x $40 + 1 x $30) x 8 h = $880 per shift / 1600 SF         = 0.55
      total                                                                       = 0.9991875 (stored 0.999188)
    """
    db = real_db()
    validate_definitions(db)
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
                allow_synthetic=True, accept_retail_proxy=True, run_at=RUN_AT)
    base.update(kw)
    return RunParams(**base)


def clone(db: Database) -> Database:
    return copy.deepcopy(db)


# ----------------------------------------------------------------------------------------------- more builders
def add_equipment_rate(db: Database, rid: str, etype: str, *, rate_hr=None, rate_day=None, ownership=None, operating=None, fuel_cost=None,
                       fuel_included=True, operator_included=False, region: str = REGION, review: str = "validated",
                       min_rental=None, delivery=None, effective_from: date = date(2026, 1, 1)):
    return db.add("equipment_rates", {
        "equipment_rate_id": rid, "equipment_type_code": etype, "description_raw": "TEST", "make_model_raw": None, "capacity_raw": None,
        "rate_basis": "rental_market", "ownership_cost_hr": D(str(ownership)) if ownership is not None else None,
        "operating_cost_hr": D(str(operating)) if operating is not None else None, "fuel_cost_hr": D(str(fuel_cost)) if fuel_cost is not None else None,
        "rental_rate_hr": D(str(rate_hr)) if rate_hr is not None else None, "rental_rate_day": D(str(rate_day)) if rate_day is not None else None,
        "rental_rate_week": None, "rental_rate_month": None, "min_rental_period": min_rental,
        "delivery_pickup_cost": D(str(delivery)) if delivery is not None else None, "fuel_included": fuel_included,
        "operator_included": operator_included, "region_id": region, "effective_from": effective_from, "effective_to": None,
        "retrieved_at": RUN_AT, "source_id": SRC, "source_locator": "synthetic", "evidence_excerpt": "synthetic", "raw_file_sha256": None,
        "origin": "observed", "review_status": review, **_rev(review), "created_at": None, "notes": None})


def add_stat_wage(db: Database, rid: str, trade: str, base, *, region: str = "REG-MD-31084", statistic: str = "mean", apprentice: bool = False,
                  wage_basis: str = "straight_time", effective_from: date = date(2026, 5, 1), classification: str = "TEST", review: str = "validated"):
    return db.add("labor_rates", {
        "labor_rate_id": rid, "rate_type": "stat_wage", "trade_code": trade, "classification_raw": classification, "soc_code": None,
        "statistic": statistic, "region_id": region, "base_wage_hr": D(str(base)), "fringe_hr": None, "fringe_breakdown": None,
        "payroll_tax_hr": None, "workers_comp_hr": None, "other_employer_cost_hr": None, "total_hr": None, "includes_fringe": False,
        "includes_payroll_taxes": False, "includes_workers_comp": False, "wage_basis": wage_basis, "project_type": "n/a",
        "use_context": "statistical_reference", "apprentice": apprentice, "determination_ref": None, "effective_from": effective_from,
        "effective_to": None, "retrieved_at": RUN_AT, "derived_from": None, "calc_run_id": None, "source_id": SRC, "source_locator": "synthetic",
        "evidence_excerpt": "synthetic", "raw_file_sha256": None, "origin": "observed", "review_status": review, **_rev(review),
        "created_at": None, "notes": None})


def add_pw_rate(db: Database, rid: str, trade: str, base, fringe, *, payroll_tax=None, workers_comp=None, other=None, total=None,
                inc_pt: bool = False, inc_wc: bool = False, region: str = REGION, project_type: str = "building",
                rate_type: str = "prevailing_wage", effective_from: date = date(2026, 8, 22), review: str = "validated"):
    return db.add("labor_rates", {
        "labor_rate_id": rid, "rate_type": rate_type, "trade_code": trade, "classification_raw": "TEST", "soc_code": None,
        "statistic": "determined", "region_id": region, "base_wage_hr": D(str(base)), "fringe_hr": D(str(fringe)), "fringe_breakdown": None,
        "payroll_tax_hr": D(str(payroll_tax)) if payroll_tax is not None else None,
        "workers_comp_hr": D(str(workers_comp)) if workers_comp is not None else None,
        "other_employer_cost_hr": D(str(other)) if other is not None else None, "total_hr": D(str(total)) if total is not None else None,
        "includes_fringe": True, "includes_payroll_taxes": inc_pt, "includes_workers_comp": inc_wc, "wage_basis": "straight_time",
        "project_type": project_type, "use_context": "public_works_only", "apprentice": False, "determination_ref": "TEST-DET",
        "effective_from": effective_from, "effective_to": date(2027, 2, 21), "retrieved_at": RUN_AT, "derived_from": None, "calc_run_id": None,
        "source_id": SRC, "source_locator": "synthetic", "evidence_excerpt": "synthetic", "raw_file_sha256": None, "origin": "observed",
        "review_status": review, **_rev(review), "created_at": None, "notes": None})


def add_burden(db: Database, bid: str, btype: str, basis: str, rate, cap=None, trade=None, region: str = "REG-US",
               effective_from: date = date(2026, 1, 1), effective_to=date(2026, 12, 31), review: str = "validated", class_code=None):
    return db.add("burden_rates", {
        "burden_id": bid, "burden_type": btype, "basis": basis, "rate": D(str(rate)), "wage_cap_annual": D(str(cap)) if cap else None,
        "class_code": class_code, "trade_code": trade, "region_id": region, "effective_from": effective_from, "effective_to": effective_to,
        "retrieved_at": RUN_AT, "source_id": SRC, "source_locator": "synthetic", "evidence_excerpt": "synthetic", "origin": "observed",
        "review_status": review, **_rev(review), "created_at": None, "notes": None})


def add_all_burdens(db: Database, with_ett: bool = True) -> None:
    add_burden(db, "TEST-BRD-BEN", "employer_benefits", "pct_of_wages", "0.25")
    add_burden(db, "TEST-BRD-SS", "fica_social_security", "pct_of_wages", "0.062", "200000")
    add_burden(db, "TEST-BRD-MED", "fica_medicare", "pct_of_wages", "0.0145")
    add_burden(db, "TEST-BRD-FUTA", "futa", "pct_of_wages", "0.006", "7000")
    add_burden(db, "TEST-BRD-UI", "state_ui", "pct_of_wages", "0.034", "7000")
    if with_ett:
        add_burden(db, "TEST-BRD-ETT", "state_ett", "pct_of_wages", "0.001", "7000")
    add_burden(db, "TEST-BRD-WC", "workers_comp", "per_100_payroll", "8.00")


def add_assumption(db: Database, aid: str, atype: str, ref: str, value, unit=None, *, proposed_by: str = "tests",
                   approved_by="second reviewer", status: str = "approved", expires_on=date(2027, 1, 1), review_status: str = "unreviewed",
                   value_text=None):
    return db.add("assumptions", {
        "assumption_id": aid, "assumption_type": atype, "applies_to_ref": ref, "value_numeric": D(str(value)) if value is not None else None,
        "value_text": value_text, "unit_id": unit, "rationale": "synthetic", "proposed_by": proposed_by, "proposed_at": None,
        "approved_by": approved_by, "approved_at": "2026-10-24T00:00:00+00:00" if approved_by else None, "status": status,
        "expires_on": expires_on, "origin": "assumed", "review_status": review_status, "notes": None})


def add_factor(db: Database, fid: str, ftype: str, applies_to: str, value, *, condition=None, qty_min=None, qty_max=None, valid_from=None,
               valid_to=None, origin: str = "observed", review: str = "validated", source: str = SRC, from_region=None, to_region=None,
               index_id=None):
    return db.add("adjustment_factors", {
        "factor_id": fid, "factor_type": ftype, "applies_to": applies_to, "from_region_id": from_region, "to_region_id": to_region,
        "factor_value": D(str(value)), "qty_min": D(str(qty_min)) if qty_min is not None else None,
        "qty_max": D(str(qty_max)) if qty_max is not None else None, "condition_desc": condition, "valid_from": valid_from, "valid_to": valid_to,
        "index_id": index_id, "derivation_formula": "synthetic", "input_refs": [], "source_id": source,
        "assumption_basis": "synthetic" if origin == "assumed" else None, "calc_run_id": None, "origin": origin, "review_status": review,
        **_rev(review), "created_at": None, "notes": None})


def add_index(db: Database, index_id: str, values: dict, *, applies_to: str = "material", review: str = "validated",
              frequency: str = "monthly", vintage: date = date(2026, 10, 20)):
    db.add("indices", {"index_id": index_id, "publisher": "TEST", "series_code": index_id, "name": "synthetic", "base_period": None,
                       "frequency": frequency, "seasonal_adjustment": None, "geography": None, "applies_to": applies_to, "source_id": SRC,
                       "origin": "observed", "review_status": review, **_rev(review), "notes": None})
    for per, val in values.items():
        db.add("index_values", {"index_id": index_id, "period_start": per, "vintage_date": vintage, "value": D(str(val)), "value_status": "final",
                                "retrieved_at": f"{vintage.isoformat()}T00:00:00+00:00", "source_locator": "synthetic", "raw_file_sha256": None,
                                "origin": "observed", "review_status": review, **_rev(review), "notes": None})


def add_consumption(db: Database, cid: str, pid: str, application: str, coverage, coverage_unit: str, per_unit: str = "GAL_US", *,
                    per_qty=1, coats=1, film=None, substrate=None, method=None, conditions=None, review: str = "validated"):
    return db.add("product_consumption", {
        "consumption_id": cid, "product_id": pid, "application": application, "coverage_qty": D(str(coverage)), "coverage_unit_id": coverage_unit,
        "per_qty": D(str(per_qty)), "per_unit_id": per_unit, "film_thickness": film, "coats": D(str(coats)), "substrate_condition": substrate,
        "application_method": method, "conditions": conditions, "source_id": SRC, "source_locator": "synthetic", "evidence_excerpt": "synthetic",
        "retrieved_at": RUN_AT, "origin": "observed", "review_status": review, **_rev(review), "created_at": None, "notes": None})


PNT = "WI-PNT-001"          # real definition: prime new gypsum board, 1 coat PVA primer (unit SF; coverage-based material quantity)


def paint_db() -> Database:
    """Real painting definition + synthetic inputs. Two primer products of the SAME spec line:
         A: $100 per 5 GAL_US = $20/gal, covers 400 SF/gal  ->  0.05 $/SF
         B: $200 per 5 GAL_US = $40/gal, covers 200 SF/gal  ->  0.20 $/SF     (median of the two paired costs = 0.125)
       labor: 2 painters x $40 x 8 h / 2000 SF = 0.32 $/SF."""
    db = real_db()
    validate_definitions(db)
    add_source(db)
    add_product(db, "TEST-PRD-PA", "prm_pva_5", 5, "GAL_US", "A", "A-1")
    add_product(db, "TEST-PRD-PB", "prm_pva_5", 5, "GAL_US", "B", "B-1")
    add_obs(db, "TEST-OBS-PA", "TEST-PRD-PA", "100", 5, "GAL_US")
    add_obs(db, "TEST-OBS-PB", "TEST-PRD-PB", "200", 5, "GAL_US")
    add_consumption(db, "TEST-CON-A", "TEST-PRD-PA", "new_drywall_primer", 400, "SF")
    add_consumption(db, "TEST-CON-B", "TEST-PRD-PB", "new_drywall_primer", 200, "SF")
    add_labor_actual(db, "TEST-LRT-PNT", "TR-PNT", 40)
    set_crew(db, "CRW-PNT", 8, [("labor", "TR-PNT", 2, False)])
    set_productivity(db, PNT, 2, 8, 2000)
    set_waste(db, PNT, {"CAT-PNT-PRM": (0.0, "TEST fixture")})
    return db


def assembly_db() -> Database:
    """priced_drywall_db + synthetic material-only work item TEST-WI-9 ($2.00 each) + assembly TEST-ASM-1 = 2 x WI-DRY-001 + 3 x TEST-WI-9."""
    db = priced_drywall_db()
    db.add("work_items", {"work_item_id": "TEST-WI-9", "version": 1, "name": "TEST widget install", "category_id": "CAT-FRM",
                          "spec_attributes": {"widget": "synthetic"}, "output_unit_id": "EA", "description": "synthetic",
                          "included_scope": ["widget_material"], "excluded_scope": [], "conditions": None, "status": "defined",
                          "valid_from": AS_OF, "supersedes_version": None, "definition_basis": "synthetic", "origin": "assumed",
                          "review_status": "validated", **_rev("validated"), "created_at": None, "notes": None})
    m = pilot.MATS["hurricane_tie"]
    add_product(db, "TEST-PRD-WIDGET", "hurricane_tie", 1, "EA", "TESTBRAND-W", "TW-1")
    add_obs(db, "TEST-OBS-WIDGET", "TEST-PRD-WIDGET", "2.00", 1, "EA")
    db.add("work_item_components", {"component_id": "TEST-WIC-9", "work_item_id": "TEST-WI-9", "work_item_version": 1, "line_no": 1,
                                    "component_kind": "material", "description": "widget", "product_spec_key": m["spec_key"], "product_id": None,
                                    "qty_mode": "fixed", "qty_per_unit": D("1"), "qty_unit_id": "EA", "qty_formula": "1 per EA",
                                    "qty_origin": "derived", "waste_factor": D("0"), "waste_origin": "observed", "waste_basis": "TEST",
                                    "crew_id": None, "productivity_id": None, "consumption_application": None, "coats_applied": None,
                                    "cost_tags": ["widget"], "is_optional": False, "notes": None})
    db.add("assemblies", {"assembly_id": "TEST-ASM-1", "version": 1, "name": "TEST assembly", "category_id": "CAT-FRM",
                          "spec_attributes": {"synthetic": True}, "output_unit_id": "SF", "description": "synthetic",
                          "included_scope": [], "excluded_scope": [], "conditions": None, "status": "defined", "valid_from": AS_OF,
                          "supersedes_version": None, "definition_basis": "synthetic", "origin": "assumed", "review_status": "validated",
                          **_rev("validated"), "created_at": None, "notes": None})
    for i, (wid, qty, unit) in enumerate((("WI-DRY-001", "2", "SF"), ("TEST-WI-9", "3", "EA")), 1):
        db.add("assembly_components", {"assembly_component_id": f"TEST-ASC-{i}", "assembly_id": "TEST-ASM-1", "assembly_version": 1,
                                       "line_no": i, "work_item_id": wid, "work_item_version": 1, "qty_per_assembly_unit": D(qty),
                                       "qty_unit_id": unit, "qty_formula": "synthetic", "qty_origin": "derived", "cost_tags": [], "notes": None})
    return db
