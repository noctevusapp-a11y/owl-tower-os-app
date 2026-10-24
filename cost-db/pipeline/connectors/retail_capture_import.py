#!/usr/bin/env python3
"""Import price observations from a capture CSV (templates/price_capture_template.csv).

This is the COMPLIANT route for retailer prices: a person (or a licensed feed / official API / public price list)
records exactly what a listing shows; this importer validates and normalises it. It never fetches websites.

Row rules (a row failing any rule is rejected with its reasons and nothing is written for it):
  * source must exist in the source register; if its reuse_status is 'prohibited' or 'restricted_no_automated_access'
    the capture_method must be 'manual_browser' (a human looked at the page) and a warning is raised
  * product identity: manufacturer+MPN (or brand+name+pack) -> stable product_id; re-seeing a known MPN must agree
    on spec_key and pack content, otherwise the row is rejected (different SKU configuration)
  * spec_attributes must contain every attribute the category requires; spec_key is computed, never typed by hand
  * the price text shown must appear in the evidence excerpt (the excerpt has to support the number)
  * units must exist (TON/GAL are always qualified, e.g. TON_SHORT, GAL_US); pack content > 0
  * observed date not in the future; retrieved_at not earlier than the observed date
  * observations are append-only: an identical observation id is skipped, never overwritten

Usage:
  python3 -I pipeline/connectors/retail_capture_import.py capture.csv [--zip-map zip_region_map.csv] [--write]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from costdb.ids import SpecError, make_id, spec_key  # noqa: E402
from costdb.store import Database  # noqa: E402
from costdb.units import Units  # noqa: E402

REQUIRED = ["retailer_source_id", "product_name", "category_id", "spec_attributes_json", "sale_unit_label",
            "pack_content_qty", "pack_content_unit_id", "price_amount", "price_channel", "observed_date",
            "retrieved_at", "evidence_excerpt", "capture_method", "captured_by"]
TEMPLATE_COLUMNS = ["target_id", "retailer_source_id", "retailer_sku", "manufacturer", "brand", "mpn", "product_name",
                    "category_id", "spec_attributes_json", "standards", "sale_unit_label", "pack_content_qty",
                    "pack_content_unit_id", "content_note", "price_amount", "currency", "original_price_text",
                    "price_channel", "is_contractor_cost", "observed_date", "retrieved_at", "zip", "store_ref",
                    "region_id", "availability", "delivery_included", "sales_tax_included", "promo_flag",
                    "qty_limit_text", "qty_tier_min", "url", "evidence_excerpt", "capture_method", "captured_by", "notes"]
CHANNELS = {"retail_public", "retail_promo", "pro_account_quote", "distributor_quote", "manufacturer_msrp",
            "public_price_list", "supplier_quote"}
METHODS = {"manual_browser", "licensed_feed", "official_api", "public_price_list", "supplier_quote_document"}
AVAIL = {"in_stock", "limited", "out_of_stock", "special_order", "unknown"}


@dataclass
class ImportReport:
    accepted_products: list[str] = field(default_factory=list)
    accepted_observations: list[str] = field(default_factory=list)
    skipped_duplicates: list[str] = field(default_factory=list)
    rejected: list[tuple[int, list[str]]] = field(default_factory=list)
    warnings: list[tuple[int, str]] = field(default_factory=list)

    def summary(self) -> str:
        return (f"products+={len(self.accepted_products)} observations+={len(self.accepted_observations)} "
                f"duplicates_skipped={len(self.skipped_duplicates)} rejected_rows={len(self.rejected)} warnings={len(self.warnings)}")


def _b(v: str) -> Optional[bool]:
    v = (v or "").strip().lower()
    if v == "":
        return None
    if v in ("true", "yes", "1"):
        return True
    if v in ("false", "no", "0"):
        return False
    raise ValueError(f"bad boolean {v!r}")


def _dec(v: str, name: str) -> Decimal:
    try:
        return Decimal(v.strip().replace(",", ""))
    except InvalidOperation as e:
        raise ValueError(f"{name}: not a number {v!r}") from e


def import_capture(rows: list[dict], db: Database, today: Optional[date] = None,
                   zip_map: Optional[dict[str, str]] = None) -> ImportReport:
    today = today or date.today()
    zip_map = zip_map or {}
    units = Units(db["units"])
    cats = db.index("categories", "category_id")
    sources = db.index("sources", "source_id")
    regions = db.index("regions", "region_id")
    products = db.index("products", "product_id")
    existing_obs = {o["observation_id"] for o in db["price_observations"]}
    mpn_index = {(p["manufacturer"].lower(), p["mpn"].lower()): p for p in db["products"] if p.get("mpn") and p.get("manufacturer")}
    rep = ImportReport()

    for n, raw in enumerate(rows, start=2):  # row 1 is the header
        errs: list[str] = []
        g = {k: (raw.get(k) or "").strip() for k in TEMPLATE_COLUMNS}
        for k in REQUIRED:
            if not g[k]:
                errs.append(f"missing required field '{k}'")
        if not (g["retailer_sku"] or g["mpn"]):
            errs.append("need retailer_sku or mpn")
        if not (g["zip"] or g["store_ref"] or g["region_id"]):
            errs.append("need zip, store_ref or region_id (where the price applies)")
        if errs:
            rep.rejected.append((n, errs)); continue
        try:
            src = sources.get(g["retailer_source_id"])
            if src is None:
                errs.append(f"unknown source {g['retailer_source_id']} (register it first)")
            if g["price_channel"] not in CHANNELS:
                errs.append(f"price_channel must be one of {sorted(CHANNELS)}")
            if g["capture_method"] not in METHODS:
                errs.append(f"capture_method must be one of {sorted(METHODS)}")
            cat = cats.get(g["category_id"])
            req = (cat or {}).get("required_product_attributes") or []
            if not req:
                errs.append(f"category {g['category_id']} is unknown or not a leaf category")
            attrs = json.loads(g["spec_attributes_json"])
            if not isinstance(attrs, dict):
                errs.append("spec_attributes_json must be a JSON object")
            qty = _dec(g["pack_content_qty"], "pack_content_qty")
            price = _dec(g["price_amount"], "price_amount")
            if qty <= 0:
                errs.append("pack_content_qty must be > 0")
            if price < 0:
                errs.append("price_amount must be >= 0")
            if g["pack_content_unit_id"] not in units:
                errs.append(f"unknown unit {g['pack_content_unit_id']} (use TON_SHORT/GAL_US etc.)")
            observed = date.fromisoformat(g["observed_date"])
            retrieved = datetime.fromisoformat(g["retrieved_at"].replace("Z", "+00:00"))
            if observed > today:
                errs.append("observed_date is in the future")
            if retrieved.date() < observed:
                errs.append("retrieved_at is earlier than observed_date")
            shown = g["original_price_text"] or f"{price:.2f}"
            if shown not in g["evidence_excerpt"] and f"{price:.2f}" not in g["evidence_excerpt"]:
                errs.append("the price shown does not appear in evidence_excerpt (excerpt must support the number)")
            currency = (g["currency"] or "USD").upper()
            if currency != "USD":
                errs.append("only USD is supported")
            avail = g["availability"] or "unknown"
            if avail not in AVAIL:
                errs.append(f"availability must be one of {sorted(AVAIL)}")
            contractor = _b(g["is_contractor_cost"]) or False
            if contractor and g["price_channel"] not in ("pro_account_quote", "distributor_quote", "supplier_quote"):
                errs.append("is_contractor_cost=true requires a quote channel; retail prices are not contractor cost")
            region_id = g["region_id"] or (zip_map.get(g["zip"]) if g["zip"] else None) or None
            if region_id and region_id not in regions:
                errs.append(f"unknown region_id {region_id}")
            if g["zip"] and not re.fullmatch(r"\d{5}", g["zip"]):
                errs.append("zip must be 5 digits")
            if src and src["reuse_status"] == "restricted_no_storage":
                errs.append(f"source terms are 'restricted_no_storage': values from {src['source_id']} must not be stored")
            if src and src["reuse_status"] in ("prohibited", "restricted_no_automated_access"):
                if g["capture_method"] != "manual_browser":
                    errs.append(f"source terms are '{src['reuse_status']}': only capture_method=manual_browser is acceptable")
                else:
                    rep.warnings.append((n, f"source {src['source_id']} is '{src['reuse_status']}': confirm that recording this "
                                            f"price manually for internal estimating is within the site's terms"))
            elif src and src["reuse_status"] == "unknown_needs_check":
                rep.warnings.append((n, f"source {src['source_id']} terms are unverified: read them before capturing at scale"))
            if cat and req and isinstance(attrs, dict):
                try:
                    key = spec_key(g["category_id"], attrs, req)
                except SpecError as e:
                    errs.append(str(e)); key = None
            else:
                key = None
            if errs:
                rep.rejected.append((n, errs)); continue

            # ---- product identity
            standards = [s.strip() for s in g["standards"].split(";") if s.strip()]
            if g["manufacturer"] and g["mpn"]:
                existing = mpn_index.get((g["manufacturer"].lower(), g["mpn"].lower()))
                pid = existing["product_id"] if existing else make_id("PRD", g["manufacturer"], g["mpn"])
            else:
                existing = None
                pid = make_id("PRD", g["brand"], g["product_name"], g["pack_content_qty"], g["pack_content_unit_id"])
            if pid in products:
                existing = products[pid]
            if existing:
                if existing["spec_key"] != key or Decimal(existing["content_qty"]) != qty or existing["content_unit_id"] != g["pack_content_unit_id"]:
                    rep.rejected.append((n, [f"product {pid} already exists with a different spec_key/pack: this listing is a different "
                                             f"configuration (existing: {existing['spec_key']}, {existing['content_qty']} {existing['content_unit_id']})"]))
                    continue
            else:
                prod = db.add("products", {
                    "product_id": pid, "category_id": g["category_id"], "name": g["product_name"], "brand": g["brand"] or None,
                    "manufacturer": g["manufacturer"] or None, "mpn": g["mpn"] or None, "description": None,
                    "spec_attributes": attrs, "spec_key": key, "standards": standards, "sale_unit_label": g["sale_unit_label"],
                    "content_qty": qty, "content_unit_id": g["pack_content_unit_id"], "content_note": g["content_note"] or None,
                    "source_id": g["retailer_source_id"], "source_locator": g["url"] or None, "evidence_excerpt": g["evidence_excerpt"],
                    "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
                    "created_at": None, "notes": None})
                products[pid] = prod
                if g["manufacturer"] and g["mpn"]:
                    mpn_index[(g["manufacturer"].lower(), g["mpn"].lower())] = prod
                rep.accepted_products.append(pid)

            oid = make_id("OBS", pid, g["retailer_source_id"], g["retailer_sku"], g["store_ref"], g["zip"], g["observed_date"],
                          g["price_channel"], g["qty_tier_min"])
            if oid in existing_obs:
                rep.skipped_duplicates.append(oid); continue
            existing_obs.add(oid)
            db.add("price_observations", {
                "observation_id": oid, "product_id": pid, "source_id": g["retailer_source_id"],
                "retailer_sku": g["retailer_sku"] or None, "store_ref": g["store_ref"] or None, "zip": g["zip"] or None,
                "region_id": region_id, "observed_at": observed, "retrieved_at": retrieved.isoformat(), "price_amount": price,
                "currency": currency, "original_price_text": g["original_price_text"] or None, "price_channel": g["price_channel"],
                "is_contractor_cost": contractor, "sold_as_label": g["sale_unit_label"], "pack_content_qty": qty,
                "pack_content_unit_id": g["pack_content_unit_id"], "availability": avail,
                "delivery_included": _b(g["delivery_included"]), "sales_tax_included": _b(g["sales_tax_included"]),
                "promo_flag": _b(g["promo_flag"]) or False, "qty_limit_text": g["qty_limit_text"] or None,
                "qty_tier_min": _dec(g["qty_tier_min"], "qty_tier_min") if g["qty_tier_min"] else None,
                "url": g["url"] or None, "source_locator": g["url"] or None, "evidence_excerpt": g["evidence_excerpt"],
                "raw_file_sha256": None, "capture_method": g["capture_method"], "captured_by": g["captured_by"],
                "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
                "created_at": None, "notes": g["notes"] or None})
            rep.accepted_observations.append(oid)
        except (ValueError, json.JSONDecodeError) as e:
            rep.rejected.append((n, [f"parse error: {e}"]))
    return rep


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__); return 2
    path = Path(argv[0])
    zip_map: dict[str, str] = {}
    if "--zip-map" in argv:
        with open(argv[argv.index("--zip-map") + 1], newline="", encoding="utf-8") as fh:
            zip_map = {r["zip"]: r["region_id"] for r in csv.DictReader(fh)}
    db = Database.load_csv_dir()
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rep = import_capture(rows, db, zip_map=zip_map)
    print(rep.summary())
    for n, e in rep.rejected:
        print(f"  REJECTED row {n}: " + "; ".join(e))
    for n, w in rep.warnings:
        print(f"  warning row {n}: {w}")
    if "--write" in argv and (rep.accepted_observations or rep.accepted_products):
        from costdb.store import format_value
        import csv as _csv
        for t in ("products", "price_observations"):
            use = [c for c in db.meta[t] if not c.generated]
            with open(ROOT / "data" / "csv" / f"{t}.csv", "w", newline="", encoding="utf-8") as fh:
                w = _csv.writer(fh, lineterminator="\n")
                w.writerow([c.name for c in use])
                for r in db[t]:
                    w.writerow([format_value(c, r.get(c.name)) for c in use])
        print("written to data/csv/products.csv and price_observations.csv")
    return 0 if not rep.rejected else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
