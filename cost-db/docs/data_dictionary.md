# Data dictionary

Generated from `pipeline/costdb/dictionary.py` and `schema/001_schema.sql` — do not edit by hand. Every column of every table is described here and as a PostgreSQL `COMMENT` (`schema/003_comments.sql`).

## Conventions

- **IDs**: `PREFIX-body` (`SRC-`, `PRD-`, `OBS-`, `LRT-`, `RUN-`, ...). Natural-key ids are deterministic hashes, so re-importing never duplicates. Test fixtures use `TEST-` and are rejected from production data.
- **origin** (where a value came from): `observed` / `derived` / `assumed` / `missing`. **review_status** (independent check): `unreviewed` / `validated` / `flagged` / `rejected`. The two are independent.
- **Dates**: price *observation* date, rate *effective period* and *retrieval* timestamp are always separate fields.
- **Units**: only ids from `units`. `TON` and `GAL` exist only qualified (`TON_SHORT`, `TON_LONG`, `TON_METRIC`, `TON_REFRIG`, `GAL_US`, `GAL_IMP`). Conversion factors are exact integer ratios.
- **Money**: USD, `numeric` (never float). Percentages are fractions (`0.062` = 6.2%) except `per_100_payroll` rates.
- **CSV interchange** (`data/csv/*.csv`): header row, empty field = NULL, booleans `true/false`, arrays as PostgreSQL literals `{a,b}`, jsonb as JSON text. Generated columns are not in the CSV.
- **Append-only** tables (triggers forbid UPDATE of data fields and any DELETE): `price_observations`, `labor_rates`, `equipment_rates`, `productivity_observations`, `burden_rates`, `index_values`, `product_consumption`, `bid_benchmarks`. Only `review_status`, `reviewed_by`, `reviewed_at`, `notes` may change.

## Tables

### `units`

Unit catalogue with exact rational conversion factors. TON and GAL exist only in qualified forms (TON_SHORT, TON_REFRIG, GAL_US ...).

| column | type | description |
|---|---|---|
| `unit_id` | text | Stable unit code; the only unit identifier used elsewhere (e.g. SF, SY, TON_SHORT, GAL_US). |
| `base_code` | text | Generic code (EA, LF, SF, SY, CF, CY, LB, TON, GAL, HR, DAY). |
| `qualifier` | text | Required for TON (short/long/metric/refrigeration) and GAL (us_liquid/imperial). |
| `name` | text | Human-readable unit name. |
| `dimension` | text | Physical dimension; only units of one dimension and base convert to each other. |
| `base_unit_id` | text | Unit this unit converts to (same dimension). |
| `to_base_num` | bigint | Numerator of the exact factor to the base unit (NULL when not fixed, e.g. DAY). |
| `to_base_den` | bigint | Denominator of the exact factor to the base unit. |
| `factor_formula` | text | Conversion formula in words/symbols, kept for audit. |
| `definition` | text | Precise definition of the unit and cautions. |
| `is_fixed_conversion` | boolean | False for units whose size depends on context (DAY = crew shift length). |

### `regions`

Geography tree: country > state > CBSA > metro division > county (ZIP optional). Identifiers still need verification against official delineations.

| column | type | description |
|---|---|---|
| `region_id` | id_t | Geography the value applies to (regions.region_id). |
| `level` | text | Geographic level of the row. |
| `name` | text | Region name. |
| `parent_region_id` | id_t → `regions.region_id` | Containing region; used to find rates published for a larger area. |
| `state_code` | char(2) | Two-letter state. |
| `fips_code` | text | Census FIPS code (state or county). |
| `cbsa_code` | text | OMB CBSA / metropolitan-division code. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `assumption_basis` | text | Why the identifier is trusted although not yet verified (required when origin=assumed). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `categories`

Own classification codes (no CSI/RSMeans identifiers). Leaf categories define which attributes make two products equivalent.

| column | type | description |
|---|---|---|
| `category_id` | id_t | Stable own category code (CAT-...). |
| `name` | text | Category name. |
| `parent_category_id` | id_t → `categories.category_id` | Parent category. |
| `description` | text | Optional description. |
| `pilot` | boolean | True for categories in the first pilot (framing/drywall, concrete, painting, HVAC). |
| `required_product_attributes` | jsonb | JSON array of attribute names that DEFINE material equivalence in this category. Products must carry all of them. |
| `external_refs` | jsonb | JSON for optional external classifier references (empty until licences are checked). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `trades`

Trades with SOC code mapping for joins to BLS data. Own codes.

| column | type | description |
|---|---|---|
| `trade_code` | id_t | Stable own trade code (TR-...). |
| `name` | text | Trade name. |
| `soc_code` | text | BLS Standard Occupational Classification code (to be verified). |
| `soc_status` | text | verified_against_bls / pending_verification / not_applicable. |
| `description` | text | Optional description. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `equipment_types`

Equipment type codes (own). Rates attach to these codes.

| column | type | description |
|---|---|---|
| `equipment_type_code` | id_t | Stable own equipment code (EQ-...). |
| `name` | text | Equipment name. |
| `description` | text | Optional description. |
| `typically_needs_operator` | boolean | Planning hint: usually operated by a dedicated operator. Does not replace the operator_included flag on rates. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `sources`

Source register: every dataset, document or page the database relies on, with access, terms and verification status.

| column | type | description |
|---|---|---|
| `source_id` | id_t | Stable source id (SRC-OWNER-DATASET[-PERIOD]). |
| `title` | text | Document/dataset title. |
| `owner` | text | Publishing organisation. |
| `source_kind` | text | government_dataset / government_publication / government_bid_data / manufacturer_doc / retailer_catalog / distributor_catalog / index_publisher / standard_or_code / internal / other. |
| `url` | text | Landing page. |
| `data_url` | text | Direct file or API endpoint, if known. |
| `data_provided` | text | What data the source holds. |
| `geography` | text | Geographic coverage. |
| `period_covered` | text | Time coverage / reference period. |
| `edition` | text | Edition or vintage. |
| `access_format` | text | API / CSV / XLSX / PDF / HTML / ZIP / mixed / unknown. |
| `requires_registration` | boolean | True when a (free) registration or key is needed. |
| `requires_payment` | boolean | True when access costs money (such sources are not used). |
| `access_notes` | text | How to obtain the data and obstacles met. |
| `reuse_status` | text | public_domain / open_license / permitted_with_attribution / restricted_no_automated_access (manual capture only) / restricted_no_storage (values must not be stored, e.g. FRED) / licence_required (licence needed for derivative use, e.g. CSI classifiers) / prohibited / unknown_needs_check. |
| `reuse_terms` | text | Terms of reuse as found (quote or paraphrase). |
| `reuse_terms_url` | text | Where the terms are published. |
| `limitations` | text | Known limits of the source. |
| `update_frequency` | text | How often the source is updated. |
| `quality_tier` | text | Source quality class: A official statistical/administrative dataset with method; B official publication/schedule; C manufacturer documentation; D retailer/distributor listing; E secondary/aggregator; X unclassified. |
| `reachability_from_build_env` | text | Whether the build environment could connect (reachable / blocked_by_network_policy / not_tested). |
| `reachability_checked_at` | date | Date of the connectivity test. |
| `verification_method` | text | fetched_primary (document actually read) / search_snippet_only / prior_knowledge_unverified / synthetic_test_fixture. Only fetched_primary can lead to validated data. |
| `evidence_quote` | text | Text from the search result or page supporting this register entry. |
| `evidence_url` | text | URL of the evidence. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `registered_at` | date | Date the source was entered in the register. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `products`

Purchasable products (manufacturer part). Equivalence between products is decided ONLY by spec_key.

| column | type | description |
|---|---|---|
| `product_id` | id_t | Stable product id (PRD-...), derived from manufacturer+MPN. |
| `category_id` | id_t → `categories.category_id` | Leaf category. |
| `name` | text | Exact product name as listed. |
| `brand` | text | Brand. |
| `manufacturer` | text | Manufacturer. |
| `mpn` | text | Manufacturer part number. |
| `description` | text | Optional longer description. |
| `spec_attributes` | jsonb | JSON of specification attributes (thickness, grade, gauge, fire rating, voltage, capacity ...). |
| `spec_key` | text | Canonical equivalence key computed from the category's required attributes; equal keys = interchangeable for costing. |
| `standards` | text[] | Applicable standards named by the manufacturer (e.g. ASTM C1396). |
| `sale_unit_label` | text | How it is sold (each, box, pail, roll ...). |
| `content_qty` | numeric(18,6) | Quantity of normalised units contained in ONE sale unit (e.g. 32 for a 4x8 sheet in SF). |
| `content_unit_id` | text → `units.unit_id` | Unit of content_qty. |
| `content_note` | text | Clarification of the pack content, e.g. count stated on the package. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `product_consumption`

Manufacturer coverage/yield rates with film thickness, coats and conditions. Never mixed with prices.

| column | type | description |
|---|---|---|
| `consumption_id` | id_t | Stable id. |
| `product_id` | id_t → `products.product_id` | Product the rate belongs to. |
| `application` | text | Application name matched by work_item_components.consumption_application. |
| `coverage_qty` | numeric(18,6) | Coverage achieved per per_qty of product. |
| `coverage_unit_id` | text → `units.unit_id` | Unit of coverage (e.g. SF). |
| `per_qty` | numeric(18,6) | Product quantity the coverage refers to. |
| `per_unit_id` | text → `units.unit_id` | Unit of per_qty (e.g. GAL_US). |
| `film_thickness` | text | Stated film/dry thickness or layer depth. |
| `coats` | numeric(4,1) | Number of coats the stated coverage refers to (1 for per-coat rates). |
| `substrate_condition` | text | Substrate the rate assumes (porous, primed ...). |
| `application_method` | text | Roller, spray, trowel ... |
| `conditions` | text | Other conditions of the rate. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `price_observations`

Append-only price history. Every observation keeps source, store/ZIP, dates, pack, inclusions and capture method.

| column | type | description |
|---|---|---|
| `observation_id` | id_t | Stable id from product+source+SKU+store+ZIP+date+channel. |
| `product_id` | id_t → `products.product_id` | Product observed. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `retailer_sku` | text | Retailer's own SKU. |
| `store_ref` | text | Store name/number. |
| `zip` | char(5) | ZIP code where the price applies. |
| `region_id` | id_t → `regions.region_id` | Geography the value applies to (regions.region_id). |
| `observed_at` | date | Date the price was seen. |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `price_amount` | numeric(14,4) | Price of ONE sale unit (pack) in the original currency. |
| `currency` | currency_t | ISO currency (USD). |
| `original_price_text` | text | Price exactly as displayed. |
| `price_channel` | text | retail_public / retail_promo / pro_account_quote / distributor_quote / manufacturer_msrp / public_price_list / supplier_quote. |
| `is_contractor_cost` | boolean | True only for contractor quote channels; retail prices are never contractor purchase cost. |
| `sold_as_label` | text | Sale unit as listed. |
| `pack_content_qty` | numeric(18,6) | Normalised content of the pack on the listing (snapshot). |
| `pack_content_unit_id` | text → `units.unit_id` | Unit of pack_content_qty. |
| `price_per_content_unit` | numeric(18,8) (generated) | GENERATED: price_amount / pack_content_qty (price per normalised unit). |
| `availability` | text | in_stock / limited / out_of_stock / special_order / unknown. |
| `delivery_included` | boolean | Whether delivery is included in the price (NULL = not recorded). |
| `sales_tax_included` | boolean | Whether sales tax is included (NULL = not recorded). |
| `promo_flag` | boolean | True for promotional/limited-time prices (excluded from costing by default). |
| `qty_limit_text` | text | Purchase-limit text of the listing. |
| `qty_tier_min` | numeric(18,6) | Minimum quantity for which this price applies. |
| `url` | text | Listing URL. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `raw_file_sha256` | text | SHA-256 of the raw downloaded file the value was read from (NULL while only search-snippet evidence exists). |
| `capture_method` | text | manual_browser / licensed_feed / official_api / public_price_list / supplier_quote_document - how the price was obtained. |
| `captured_by` | text | Person or system that captured it. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `calculation_runs`

One row per calculation: target, parameters, status, subtotals and the exact calc version. Incomplete runs store NO total.

| column | type | description |
|---|---|---|
| `run_id` | id_t | Deterministic id: same data + parameters + calc version give the same id. |
| `run_at` | timestamptz | Timestamp of the run. |
| `calc_version` | text | Version of the calculation code. |
| `target_type` | text | unit_cost / assembly / labor_loaded / index_adjustment / markup. |
| `target_id` | text | Work item, assembly, trade or base run that was calculated. |
| `target_version` | integer | Version of the target definition. |
| `mode` | text | strict (observed/derived validated inputs only) or with_assumptions (approved assumptions may fill gaps). |
| `parameters` | jsonb | JSON of all run parameters (region, as-of date, policies, conditions). |
| `status` | text | complete / incomplete (inputs missing) / failed (logical conflict such as double counting). |
| `has_assumptions` | boolean | True if any input came from the assumptions table. |
| `result_unit_id` | text → `units.unit_id` | Unit of the result (per this unit). |
| `material_cost` | numeric(18,6) | Material subtotal per result unit. |
| `labor_cost` | numeric(18,6) | Labor subtotal per result unit. |
| `equipment_cost` | numeric(18,6) | Equipment subtotal per result unit. |
| `other_direct_cost` | numeric(18,6) | Other direct subtotal per result unit. |
| `direct_cost_total` | numeric(18,6) | Total direct cost per result unit (price for markup runs). NULL unless status=complete. |
| `missing_inputs` | jsonb | JSON list of unresolved inputs with reason and how to fill them. |
| `warnings` | jsonb | JSON list of warnings (e.g. RETAIL_PRICE_NOT_CONTRACTOR_COST). |
| `code_ref` | text | Repository revision of the calculation code. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `calculation_run_lines`

Cost lines of a run: quantity, unit, unit cost, formula text and exact input record ids.

| column | type | description |
|---|---|---|
| `run_id` | id_t → `calculation_runs.run_id` | Run the line belongs to. |
| `line_no` | integer | Line order. |
| `line_kind` | text | material / labor / equipment / other_direct / overhead / contingency / profit / adjustment / subtotal / assembly_component. |
| `component_ref` | text | Component/crew/trade the line came from. |
| `description` | text | Line description. |
| `quantity` | numeric(24,10) | Quantity per result unit (person-hours or crew-hours for labor/equipment lines). |
| `quantity_unit_id` | text → `units.unit_id` | Unit of quantity. |
| `unit_cost` | numeric(24,10) | Cost per quantity unit. |
| `extended_cost` | numeric(24,10) | Cost per result unit (quantity incl. waste x unit cost). |
| `formula` | text | Readable formula with the numbers used. |
| `inputs` | jsonb | JSON list of input records {table,id,field,value,unit,origin,review_status,...}. |
| `origin_summary` | text | observed / derived / assumed / mixed / missing. |
| `warnings` | jsonb | JSON list of line-level warnings. |

### `labor_rates`

Labor rates in separate layers: statistical wages, prevailing/federal determinations, company actuals, and derived loaded employer cost.

| column | type | description |
|---|---|---|
| `labor_rate_id` | id_t | Stable id. |
| `rate_type` | text | stat_wage / prevailing_wage / federal_wage_determination / employer_compensation_index / loaded_employer_cost / company_actual. |
| `trade_code` | id_t → `trades.trade_code` | Trade (trades.trade_code). |
| `classification_raw` | text | Classification text exactly as in the source. |
| `soc_code` | text | SOC code for statistical wages. |
| `statistic` | text | mean / median / p10 / p25 / p75 / p90 / determined / actual / n/a. |
| `region_id` | id_t → `regions.region_id` | Geography the value applies to (regions.region_id). |
| `base_wage_hr` | numeric(12,4) | Hourly base wage (excludes fringe unless stated). |
| `fringe_hr` | numeric(12,4) | Hourly fringe benefits as stated by the source. |
| `fringe_breakdown` | jsonb | JSON breakdown of fringe items (health, pension, vacation, training ...). |
| `payroll_tax_hr` | numeric(12,4) | Employer payroll taxes per hour (loaded rates only). |
| `workers_comp_hr` | numeric(12,4) | Workers' compensation per hour (loaded rates only). |
| `other_employer_cost_hr` | numeric(12,4) | Other documented employer cost per hour. |
| `total_hr` | numeric(12,4) | Total hourly cost as defined by rate_type (loaded: sum of components). |
| `includes_fringe` | boolean | True if fringe benefits are already inside the rate (never add them again). |
| `includes_payroll_taxes` | boolean | True if payroll taxes are already inside the rate. |
| `includes_workers_comp` | boolean | True if workers' comp is already inside the rate. |
| `wage_basis` | text | straight_time / overtime_1_5x / overtime_2x / n/a. |
| `project_type` | text | building / residential / heavy / highway / n/a (determination classes). |
| `use_context` | text | public_works_only (prevailing/federal) / statistical_reference / employer_internal. Public-works rates are not applied to private projects. |
| `apprentice` | boolean | True for apprentice classifications. |
| `determination_ref` | text | Determination number (e.g. DIR / DBA). |
| `effective_from` | date | First day the rate/period is in force. |
| `effective_to` | date | Last day the rate/period is in force (NULL = open ended / unknown). |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `derived_from` | text[] | IDs of the records a derived loaded rate was built from. |
| `calc_run_id` | id_t → `calculation_runs.run_id` | Calculation run that produced a derived rate. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `raw_file_sha256` | text | SHA-256 of the raw downloaded file the value was read from (NULL while only search-snippet evidence exists). |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `burden_rates`

Employer burden items (payroll taxes, benefits, workers' comp ...), kept apart from wages.

| column | type | description |
|---|---|---|
| `burden_id` | id_t | Stable id. |
| `burden_type` | text | fica_social_security / fica_medicare / futa / state_ui / state_ett / workers_comp / employer_benefits / general_liability / other. |
| `basis` | text | pct_of_wages (fraction, 0.062 = 6.2%) / per_hour / per_100_payroll. |
| `rate` | numeric(14,6) | Rate in the stated basis. |
| `wage_cap_annual` | numeric(14,2) | Annual wage cap per employee (the hourly equivalent is computed with annual paid hours). |
| `class_code` | text | Classification code (e.g. workers' comp class). |
| `trade_code` | id_t → `trades.trade_code` | Trade the rate is specific to (NULL = all). |
| `region_id` | id_t → `regions.region_id` | Geography (state/country level usually). |
| `effective_from` | date | First day the rate/period is in force. |
| `effective_to` | date | Last day the rate/period is in force (NULL = open ended / unknown). |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `equipment_rates`

Equipment rates with explicit treatment of operator, fuel, delivery and minimum rental. Delivery/mobilization are never part of hourly unit-cost rates.

| column | type | description |
|---|---|---|
| `equipment_rate_id` | id_t | Stable id. |
| `equipment_type_code` | id_t → `equipment_types.equipment_type_code` | Equipment type. |
| `description_raw` | text | Description as in the source. |
| `make_model_raw` | text | Make/model as in the source. |
| `capacity_raw` | text | Size/capacity as in the source. |
| `rate_basis` | text | rental_market / owned_cost_schedule / dot_schedule / usace_schedule. |
| `ownership_cost_hr` | numeric(12,4) | Ownership cost per hour. |
| `operating_cost_hr` | numeric(12,4) | Operating cost per hour (fuel/lube/repairs, excluding operator). |
| `fuel_cost_hr` | numeric(12,4) | Fuel cost per hour if listed separately. |
| `rental_rate_hr` | numeric(12,4) | Rental rate per hour. |
| `rental_rate_day` | numeric(12,4) | Rental rate per day. |
| `rental_rate_week` | numeric(12,4) | Rental rate per week. |
| `rental_rate_month` | numeric(12,4) | Rental rate per month. |
| `min_rental_period` | text | Minimum rental period text. |
| `delivery_pickup_cost` | numeric(12,4) | Delivery and pickup cost (a separate cost, not in unit-cost rates). |
| `fuel_included` | boolean | Whether fuel is included in the rate. |
| `operator_included` | boolean | Whether the operator is included (never count the operator again in labor). |
| `region_id` | id_t → `regions.region_id` | Geography the value applies to (regions.region_id). |
| `effective_from` | date | First day the rate/period is in force. |
| `effective_to` | date | Last day the rate/period is in force (NULL = open ended / unknown). |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `raw_file_sha256` | text | SHA-256 of the raw downloaded file the value was read from (NULL while only search-snippet evidence exists). |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `crews`

Crew composition templates. Rates are resolved at calculation time, not stored here. origin=missing means composition not yet sourced.

| column | type | description |
|---|---|---|
| `crew_id` | id_t | Stable crew id. |
| `name` | text | Crew name. |
| `description` | text | Intended trades and scope. |
| `category_id` | id_t → `categories.category_id` | Category the crew works in. |
| `shift_hours` | numeric(5,2) | Productive shift length in hours (NULL while the crew is missing). |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `assumption_basis` | text | Basis when origin=assumed. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `crew_members`

Crew members: labor by trade or equipment by type, with quantity and hours per shift.

| column | type | description |
|---|---|---|
| `crew_member_id` | id_t | Stable id. |
| `crew_id` | id_t → `crews.crew_id` | Crew. |
| `member_kind` | text | labor / equipment. |
| `trade_code` | id_t → `trades.trade_code` | Trade for labor members. |
| `equipment_type_code` | id_t → `equipment_types.equipment_type_code` | Equipment type for equipment members. |
| `labor_rate_id` | id_t → `labor_rates.labor_rate_id` | Optional pinned labor rate (overrides resolution). |
| `equipment_rate_id` | id_t → `equipment_rates.equipment_rate_id` | Optional pinned equipment rate. |
| `quantity` | numeric(8,3) | Persons (labor) or units (equipment). |
| `hours_per_shift` | numeric(5,2) | Hours this member works per shift (default: crew shift). |
| `is_operator` | boolean | True if this labor member operates a piece of crew equipment (prevents double counting with operator-inclusive rates). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `productivity_observations`

Labor norms: crew, shift, daily output, person-hours per unit, conditions, inclusions, and the exact document/edition/page. origin=missing when not found.

| column | type | description |
|---|---|---|
| `productivity_id` | id_t | Stable id. |
| `work_item_id` | id_t | Work item the norm maps to (when mapped). |
| `operation_text` | text | Operation as worded in the source. |
| `category_id` | id_t → `categories.category_id` | Category. |
| `output_unit_id` | text → `units.unit_id` | Unit of daily_output. |
| `crew_id` | id_t → `crews.crew_id` | Crew record (if modelled). |
| `crew_description_raw` | text | Crew as described in the source. |
| `crew_size` | numeric(8,3) | Persons in the crew. |
| `shift_hours` | numeric(5,2) | Productive hours per shift. |
| `daily_output` | numeric(18,6) | Output per crew per shift in output_unit_id. |
| `person_hours_per_unit_reported` | numeric(18,8) | Person-hours per unit as printed in the source. |
| `person_hours_per_unit_derived` | numeric(18,8) (generated) | GENERATED: crew_size x shift_hours / daily_output. |
| `conditions` | text | Conditions of the norm. |
| `included_operations` | text | Operations the norm includes. |
| `excluded_operations` | text | Operations the norm excludes. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `source_doc` | text | Document title. |
| `source_edition` | text | Edition / year. |
| `source_page` | text | Page. |
| `source_table` | text | Table or section. |
| `source_context` | text | Surrounding context (heading, footnote). |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `raw_file_sha256` | text | SHA-256 of the raw downloaded file the value was read from (NULL while only search-snippet evidence exists). |
| `missing_reason` | text | Why the norm is missing (required when origin=missing). |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `work_items`

Unit-cost operations: a specific operation with measurable spec, output unit and explicit scope. Versioned.

| column | type | description |
|---|---|---|
| `work_item_id` | id_t | Stable work item code. |
| `version` | integer | Version number; assemblies reference an exact version. |
| `name` | text | Operation name. |
| `category_id` | id_t → `categories.category_id` | Category. |
| `spec_attributes` | jsonb | JSON measurable specification (sizes, spacing, layers, thickness ...). |
| `output_unit_id` | text → `units.unit_id` | Unit of the result (what one unit of work measures). |
| `description` | text | What is done. |
| `included_scope` | text[] | Scope tokens this item covers (used to detect double counting in assemblies). |
| `excluded_scope` | text[] | Scope tokens explicitly NOT covered (mobilization, cleanup, overhead ... are excluded everywhere). |
| `conditions` | text | Working conditions the cost applies to. |
| `status` | text | defined / priced_incomplete / priced_with_assumptions / priced_verified / retired. |
| `valid_from` | date | Date this version takes effect. |
| `supersedes_version` | integer | Earlier version replaced by this one. |
| `definition_basis` | text | How the definition was authored; geometry-derived, not copied from a commercial book. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `work_item_components`

Material, labor, equipment and other direct components of a work item, with quantity per unit and formula.

| column | type | description |
|---|---|---|
| `component_id` | id_t | Stable id. |
| `work_item_id` | id_t | Work item. |
| `work_item_version` | integer | Work item version. |
| `line_no` | integer | Line order. |
| `component_kind` | cost_component_t | material / labor / equipment / other_direct. |
| `description` | text | Component description. |
| `product_spec_key` | text | Material equivalence key whose observations may price this line. |
| `product_id` | id_t → `products.product_id` | Optional pinned product. |
| `qty_mode` | text | fixed / from_product_consumption (manufacturer coverage) / from_productivity (crew norm). |
| `qty_per_unit` | numeric(24,10) | Quantity per ONE unit of work-item output, before waste. |
| `qty_unit_id` | text → `units.unit_id` | Unit of qty_per_unit. |
| `qty_formula` | text | Derivation of the quantity from the spec geometry. |
| `qty_origin` | origin_t | derived (from spec geometry) / observed / missing. Assumed quantities live in the assumptions table. |
| `waste_factor` | numeric(8,5) | Fraction added for waste: purchased = qty x (1 + waste_factor). NULL = not yet sourced. |
| `waste_origin` | origin_t | observed / derived. Assumed waste lives in the assumptions table. |
| `waste_basis` | text | Source or reasoning of the waste factor (mandatory when set). |
| `crew_id` | id_t → `crews.crew_id` | Crew for labor/equipment lines. |
| `productivity_id` | id_t | Productivity record for labor/equipment lines. |
| `consumption_application` | text | Application name to look up in product_consumption. |
| `coats_applied` | numeric(4,1) | Number of coats applied by this component (coverage-based lines). |
| `cost_tags` | text[] | Tags for detecting duplicated cost within a work item. |
| `is_optional` | boolean | Optional component flag. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `assemblies`

Assemblies: a measurable construction spec composed of exact work-item versions. No generic 'average' assemblies.

| column | type | description |
|---|---|---|
| `assembly_id` | id_t | Stable assembly code. |
| `version` | integer | Version number. |
| `name` | text | Assembly name. |
| `category_id` | id_t → `categories.category_id` | Category. |
| `spec_attributes` | jsonb | JSON measurable specification (non-empty). |
| `output_unit_id` | text → `units.unit_id` | Unit of the assembly result. |
| `description` | text | Description. |
| `included_scope` | text[] | Scope tokens. |
| `excluded_scope` | text[] | Explicit exclusions. |
| `conditions` | text | Conditions. |
| `status` | text | defined / priced_incomplete / priced_with_assumptions / priced_verified / retired. |
| `valid_from` | date | Effective date. |
| `supersedes_version` | integer | Replaced version. |
| `definition_basis` | text | How the definition was authored. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `assembly_components`

Work items inside an assembly with quantity per assembly unit and the derivation.

| column | type | description |
|---|---|---|
| `assembly_component_id` | id_t | Stable id. |
| `assembly_id` | id_t | Assembly. |
| `assembly_version` | integer | Assembly version. |
| `line_no` | integer | Order. |
| `work_item_id` | id_t | Work item. |
| `work_item_version` | integer | Exact work-item version used. |
| `qty_per_assembly_unit` | numeric(24,10) | Work-item units per ONE assembly unit. |
| `qty_unit_id` | text → `units.unit_id` | Unit (must convert to the work item's output unit). |
| `qty_formula` | text | Derivation of the quantity. |
| `qty_origin` | origin_t | derived / observed. |
| `cost_tags` | text[] | Tags for duplicate detection. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `bid_benchmarks`

Public-contract bid prices stored as benchmarks only. A bid price is not cost and is never an input to calculations.

| column | type | description |
|---|---|---|
| `benchmark_id` | id_t | Stable id. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `agency` | text | Awarding/publishing agency. |
| `contract_ref` | text | Contract or bid reference. |
| `item_code_source` | text | Agency's own item code. |
| `item_description` | text | Item as described by the agency. |
| `category_id` | id_t → `categories.category_id` | Own category. |
| `quantity` | numeric(18,4) | Contract quantity. |
| `quantity_unit_id` | text → `units.unit_id` | Unit of quantity. |
| `unit_price` | numeric(18,6) | Bid unit price. |
| `unit_price_unit_id` | text → `units.unit_id` | Unit the price is per. |
| `price_statistic` | text | single_bid / low_bid / awarded / average_of_n / median_of_n. |
| `sample_size` | integer | Number of bids/contracts behind the figure. |
| `bid_date` | date | Bid opening date. |
| `period_end` | date | End of the averaging period (for averages). |
| `region_id` | id_t → `regions.region_id` | Geography the value applies to (regions.region_id). |
| `scope_note` | text | What the price covers (furnish+install, mobilization, traffic control ...). |
| `price_nature` | text | Always 'bid_price_not_cost'. |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `evidence_excerpt` | text | Verbatim text or JSON excerpt from the source that supports the stored value. |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `indices`

Price/cost index series definitions (time adjustment inputs; not product prices).

| column | type | description |
|---|---|---|
| `index_id` | id_t | Stable id. |
| `publisher` | text | Publisher (BLS ...). |
| `series_code` | text | Series identifier. |
| `name` | text | Series name. |
| `base_period` | text | Index base period. |
| `frequency` | text | monthly / quarterly / annual / other. |
| `seasonal_adjustment` | text | Seasonal adjustment status. |
| `geography` | text | Geography of the series. |
| `applies_to` | text | material / labor / equipment / all. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `index_values`

Index values with vintage so revisions never overwrite earlier values.

| column | type | description |
|---|---|---|
| `index_id` | id_t → `indices.index_id` | Series. |
| `period_start` | date | First day of the index period. |
| `vintage_date` | date | Date this value was current (revisions add rows). |
| `value` | numeric(18,6) | Index value. |
| `value_status` | text | preliminary / final / revised. |
| `retrieved_at` | timestamptz | When WE obtained the data (distinct from the observation date or the rate's effective period). |
| `source_locator` | text | Where inside the source the value sits: page / table / row / URL fragment. |
| `raw_file_sha256` | text | SHA-256 of the raw downloaded file the value was read from (NULL while only search-snippet evidence exists). |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `adjustment_factors`

Multiplicative factors for region, time, quantity and conditions; each applies to ONE cost component and is never applied twice.

| column | type | description |
|---|---|---|
| `factor_id` | id_t | Stable id. |
| `factor_type` | text | region / time_index / quantity / conditions / productivity_condition. |
| `applies_to` | cost_component_t | Cost component the factor applies to (material / labor / equipment / other_direct). |
| `from_region_id` | id_t → `regions.region_id` | Region the base price comes from (region factors). |
| `to_region_id` | id_t → `regions.region_id` | Target region (region factors). |
| `factor_value` | numeric(14,8) | Multiplier (> 0). |
| `qty_min` | numeric(18,6) | Lower quantity bound (quantity factors). |
| `qty_max` | numeric(18,6) | Upper quantity bound (exclusive). |
| `condition_desc` | text | Condition tag (conditions factors), matched against RunParams.conditions. |
| `valid_from` | date | Start of validity. |
| `valid_to` | date | End of validity. |
| `index_id` | id_t → `indices.index_id` | Index series (time factors). |
| `derivation_formula` | text | How the factor was obtained. |
| `input_refs` | jsonb | JSON list of input records for derived factors. |
| `source_id` | id_t → `sources.source_id` | Source-register entry (sources.source_id) the value comes from. |
| `assumption_basis` | text | Basis for assumed factors. |
| `calc_run_id` | id_t → `calculation_runs.run_id` | Run that derived the factor. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `reviewed_by` | text | Person or agent that set review_status. |
| `reviewed_at` | timestamptz | When review_status was set. |
| `created_at` | timestamptz | When the row was created (build timestamp for generated rows). |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `assumptions`

Expert assumptions, stored apart from observed data. Used only in with_assumptions mode and only when approved.

| column | type | description |
|---|---|---|
| `assumption_id` | id_t | Stable id. |
| `assumption_type` | text | productivity / waste / crew_composition / material_price / labor_rate / equipment_rate / factor / other. |
| `applies_to_ref` | text | What the assumption fills: waste:<component_id>, quantity:<component_id>, price:<spec_key>, productivity:<component_id>, labor_rate:<trade>:<region>, equipment_rate:<type>:<region>, burden:<type>:<trade>. |
| `value_numeric` | numeric(24,10) | Numeric value. |
| `value_text` | text | Text value. |
| `unit_id` | text → `units.unit_id` | Unit of the value. |
| `rationale` | text | Why this value is proposed. |
| `proposed_by` | text | Proposer. |
| `proposed_at` | timestamptz | When proposed. |
| `approved_by` | text | Approver (required for status=approved). |
| `approved_at` | timestamptz | When approved. |
| `status` | text | proposed / approved / rejected / superseded. |
| `expires_on` | date | Date after which the assumption must not be used. |
| `origin` | origin_t | Where the value came from: observed (read from a source), derived (computed by a recorded calculation), assumed (expert assumption), missing (looked for and not found; value fields stay NULL). |
| `review_status` | review_status_t | Independent-check result: unreviewed / validated / flagged / rejected. Only 'validated' records feed verified calculations; flagged and rejected are never used. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `capture_targets`

Work queue: data still to be collected (material specs, labor, equipment, norms, indices ...).

| column | type | description |
|---|---|---|
| `target_id` | id_t | Stable id. |
| `target_kind` | text | material / labor / equipment / productivity / index / burden / other. |
| `category_id` | id_t → `categories.category_id` | Category. |
| `description` | text | What to capture. |
| `spec_attributes` | jsonb | JSON of required attributes. |
| `spec_key` | text | Spec key a captured product must match (materials). |
| `preferred_sale_unit` | text | Preferred sale unit. |
| `pilot_priority` | integer | 1 needed by a pilot work item, 2 useful, 3 later. |
| `required_by` | text | Work items / uses that need it. |
| `recommended_source_ids` | text[] | Source-register ids suggested for this target. |
| `status` | text | open / in_progress / captured / blocked. |
| `blocked_reason` | text | Why it is blocked. |
| `notes` | text | Free-text remarks. Never holds data that calculations depend on. |

### `validation_issues`

Findings of the independent validation, one row per violation.

| column | type | description |
|---|---|---|
| `issue_id` | bigint (generated) | Sequence id. |
| `detected_at` | timestamptz | When detected. |
| `detected_by` | text | Rule engine or agent. |
| `record_table` | text | Table of the offending record. |
| `record_id` | text | Primary key of the record. |
| `rule_code` | text | Stable rule code. |
| `severity` | severity_t | error / warning / info. |
| `message` | text | Explanation. |
| `details` | jsonb | JSON details. |
| `status` | text | open / resolved / waived. |
| `resolution_note` | text | Required when not open. |
| `resolved_at` | timestamptz | When resolved. |
