"""Shared enumerations. ONE definition used by the engine, validator, importer and tests (a status handled in one place
only is how restricted sources slipped through before the independent review)."""

# Values from a source with one of these reuse statuses must never be stored or used as a calculation input.
NO_DATA_USE = ("prohibited", "restricted_no_storage", "licence_required")
# Manual capture only: a person records what a listing shows; no automated retrieval.
MANUAL_ONLY = ("restricted_no_automated_access",)

MODES = ("strict", "with_assumptions")
MIN_REVIEWS = ("validated", "unreviewed")
PRICE_POLICIES = ("median_of_latest_per_product", "latest")
LABOR_BASES = ("stat_loaded", "prevailing_loaded", "company_actual")
LABOR_STATISTICS = ("mean", "median", "p10", "p25", "p75", "p90")
WAGE_REGIMES = ("state", "federal")
WAGE_CLASSES = ("building", "residential", "heavy", "highway", "n/a")
PROJECT_TYPES = ("private", "public_works")
BURDEN_BASES = ("base_wage", "wage_plus_fringe")
EQUIPMENT_BASES = ("hourly", "rental_day")

RETAIL_CHANNELS = ("retail_public", "retail_promo")
CONTRACTOR_CHANNELS = ("pro_account_quote", "distributor_quote", "supplier_quote")
LIST_CHANNELS = ("public_price_list",)
DEFAULT_CHANNELS = LIST_CHANNELS + CONTRACTOR_CHANNELS          # retail is an explicit opt-in (accept_retail_proxy)
ALL_CHANNELS = ("retail_public", "retail_promo", "pro_account_quote", "distributor_quote", "manufacturer_msrp",
                "public_price_list", "supplier_quote")

# Payroll-tax burdens that every run needs; state-specific ones are added by region (see calc._payroll_types).
BASE_PAYROLL_TYPES = ("fica_social_security", "fica_medicare", "futa", "state_ui")
STATE_PAYROLL_EXTRA = {"CA": ("state_ett",)}
# Rows of these burden types are NEVER added to labor cost silently (they usually belong to overhead): they are flagged.
FLAGGED_ONLY_BURDENS = ("general_liability", "other")
