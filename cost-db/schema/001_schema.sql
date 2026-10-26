-- =====================================================================
-- Owl Tower Construction Group — independent construction cost database
-- Schema 001: tables, constraints, history protection, views
-- Target: PostgreSQL 14+ / Supabase (tested on PostgreSQL 16)
--
-- Design rules enforced here (see docs/methodology.md):
--   * every record has a stable id, a source (or an explicit "no source" origin) and a status
--   * origin       : observed / derived / assumed / missing        (where did the value come from)
--   * review_status: unreviewed / validated / flagged / rejected   (what the independent check said)
--   * observed measurements are append-only (history is never overwritten)
--   * expert assumptions live in their own table, never inside observed tables
--   * calculated results are only stored together with their inputs, formulas and calc version
--
-- Everything lives in schema "costdb". On Supabase, add "costdb" to the exposed
-- schemas (Settings -> API) if you want PostgREST access, and enable RLS per your policy.
-- =====================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS costdb;
SET LOCAL search_path = costdb, public;

-- ---------------------------------------------------------------------
-- Domains
-- ---------------------------------------------------------------------
CREATE DOMAIN id_t AS text
  CHECK (VALUE ~ '^(TEST-)?[A-Z][A-Z0-9]{1,5}-[A-Za-z0-9._-]{1,80}$');
COMMENT ON DOMAIN id_t IS 'Stable record id: PREFIX-body, e.g. SRC-BLS-OEWS-MAY2024, PRD-3fa9c01b2d. Test fixtures are prefixed TEST-.';

CREATE DOMAIN origin_t AS text
  CHECK (VALUE IN ('observed','derived','assumed','missing'));
CREATE DOMAIN review_status_t AS text
  CHECK (VALUE IN ('unreviewed','validated','flagged','rejected'));
CREATE DOMAIN severity_t AS text
  CHECK (VALUE IN ('error','warning','info'));
CREATE DOMAIN currency_t AS char(3)
  CHECK (VALUE ~ '^[A-Z]{3}$');
CREATE DOMAIN cost_component_t AS text
  CHECK (VALUE IN ('material','labor','equipment','other_direct'));

-- ---------------------------------------------------------------------
-- Append-only guard: observed history must never be rewritten.
-- Only review fields and notes may change on a protected table.
-- ---------------------------------------------------------------------
CREATE FUNCTION forbid_history_rewrite() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  -- review fields stay editable; GENERATED columns are excluded because in a BEFORE trigger NEW does not yet hold
  -- their recomputed value (they cannot change independently of the protected columns anyway)
  mutable text[] := ARRAY['review_status','reviewed_by','reviewed_at','notes','price_per_content_unit','person_hours_per_unit_derived'];
BEGIN
  mutable := mutable || TG_ARGV;     -- a trigger may name extra mutable columns (e.g. 'status' on versioned definitions)
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION '% is append-only: DELETE is forbidden (supersede or flag the record instead)', TG_TABLE_NAME;
  END IF;
  IF (to_jsonb(OLD) - mutable) IS DISTINCT FROM (to_jsonb(NEW) - mutable) THEN
    RAISE EXCEPTION '% is append-only: only review_status/reviewed_by/reviewed_at/notes (and explicitly listed status columns) may be updated; insert a new row or version instead', TG_TABLE_NAME;
  END IF;
  RETURN NEW;
END $$;

-- TRUNCATE would bypass the row triggers: refuse it on every protected table (drop the schema to reset a scratch database).
CREATE FUNCTION forbid_truncate() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is protected: TRUNCATE is forbidden', TG_TABLE_NAME;
END $$;

-- Reference tables that must never change after load (unit definitions).
CREATE FUNCTION forbid_any_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is immutable reference data: % is forbidden', TG_TABLE_NAME, TG_OP;
END $$;

-- Every change of review_status is logged (who/when/old/new); the log itself is append-only.
CREATE TABLE review_events (
  event_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  record_table text NOT NULL,
  record_id    text NOT NULL,
  old_status   text NOT NULL,
  new_status   text NOT NULL,
  changed_by   text,
  changed_at   timestamptz NOT NULL DEFAULT now(),
  db_user      text NOT NULL DEFAULT session_user
);
CREATE INDEX review_events_record_idx ON review_events (record_table, record_id);

CREATE FUNCTION log_review_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE rid text; i int;
BEGIN
  -- a change of status AND a change of the recorded reviewer (status unchanged) are both history
  IF NEW.review_status IS DISTINCT FROM OLD.review_status OR (to_jsonb(NEW) ->> 'reviewed_by') IS DISTINCT FROM (to_jsonb(OLD) ->> 'reviewed_by') THEN
    rid := to_jsonb(NEW) ->> TG_ARGV[0];
    FOR i IN 1 .. TG_NARGS - 1 LOOP
      rid := rid || '|' || (to_jsonb(NEW) ->> TG_ARGV[i]);
    END LOOP;
    INSERT INTO review_events (record_table, record_id, old_status, new_status, changed_by, changed_at)
    VALUES (TG_TABLE_NAME, rid, OLD.review_status, NEW.review_status, to_jsonb(NEW) ->> 'reviewed_by',
            COALESCE((to_jsonb(NEW) ->> 'reviewed_at')::timestamptz, now()));
  END IF;
  RETURN NEW;
END $$;

-- Row-level change log for reference and approval data that stay editable (source register, region hierarchy, categories, trades,
-- equipment types, assumption approvals): who/when and the complete old and new row. Append-only. (Protection against mistakes: the
-- table owner/superuser can always disable triggers.)
CREATE TABLE change_log (
  event_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  table_name   text NOT NULL,
  record_id    text NOT NULL,
  op           text NOT NULL CHECK (op IN ('UPDATE','DELETE')),
  old_row      jsonb NOT NULL,
  new_row      jsonb,
  changed_at   timestamptz NOT NULL DEFAULT now(),
  db_user      text NOT NULL DEFAULT session_user
);
CREATE INDEX change_log_record_idx ON change_log (table_name, record_id);

CREATE FUNCTION log_row_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND to_jsonb(OLD) = to_jsonb(NEW) THEN RETURN NEW; END IF;
  INSERT INTO change_log (table_name, record_id, op, old_row, new_row)
  VALUES (TG_TABLE_NAME, to_jsonb(OLD) ->> TG_ARGV[0], TG_OP, to_jsonb(OLD), CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(NEW) END);
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$;

-- A source may not be downgraded (no longer fetched) or turned into one whose terms bar data use while rows depend on it:
-- otherwise "flip the source up, validate, flip it back" would leave validated rows resting on an unfetched source.
CREATE FUNCTION guard_source_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE t text; n bigint; downgrade boolean; restricted boolean;
BEGIN
  downgrade := OLD.verification_method = 'fetched_primary' AND NEW.verification_method <> 'fetched_primary';
  restricted := NEW.reuse_status IN ('prohibited','restricted_no_storage','licence_required')
                AND OLD.reuse_status NOT IN ('prohibited','restricted_no_storage','licence_required');
  IF downgrade OR restricted THEN
    FOREACH t IN ARRAY ARRAY['products','product_consumption','price_observations','labor_rates','burden_rates','equipment_rates',
                             'productivity_observations','bid_benchmarks','crews','adjustment_factors','indices'] LOOP
      EXECUTE format('SELECT count(*) FROM %I WHERE source_id = $1 AND (review_status = ''validated'' OR $2)', t) INTO n USING OLD.source_id, restricted;
      IF n > 0 THEN
        RAISE EXCEPTION 'source %: cannot be % while % row(s) of % depend on it - flag or supersede them first', OLD.source_id,
          CASE WHEN downgrade THEN 'downgraded from fetched_primary' ELSE 'restricted' END, n, t;
      END IF;
    END LOOP;
    SELECT count(*) INTO n FROM index_values v JOIN indices i USING (index_id) WHERE i.source_id = OLD.source_id AND (v.review_status = 'validated' OR restricted);
    IF n > 0 THEN
      RAISE EXCEPTION 'source %: cannot be changed while % index value(s) depend on it - flag or supersede them first', OLD.source_id, n;
    END IF;
  END IF;
  RETURN NEW;
END $$;

-- A record may only be 'validated' when its source was really fetched, and observed data may never come from a source whose
-- terms bar using/storing the values. (Synthetic test fixtures are exempt and are rejected from production data elsewhere.)
CREATE FUNCTION check_source_usable() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE sid text; rs text; vm text; j jsonb := to_jsonb(NEW);
BEGIN
  sid := j ->> 'source_id';
  IF sid IS NULL THEN RETURN NEW; END IF;
  SELECT reuse_status, verification_method INTO rs, vm FROM sources WHERE source_id = sid;
  IF rs IS NULL THEN RETURN NEW; END IF;     -- the foreign key reports unknown sources
  IF (j ->> 'origin') = 'observed' AND rs IN ('prohibited','restricted_no_storage','licence_required') THEN
    RAISE EXCEPTION '%: source % has reuse_status % - observed values must not be stored from it', TG_TABLE_NAME, sid, rs;
  END IF;
  IF (j ->> 'review_status') = 'validated' AND vm NOT IN ('fetched_primary','synthetic_test_fixture') THEN
    RAISE EXCEPTION '%: cannot be validated - source % was never fetched (verification_method=%)', TG_TABLE_NAME, sid, vm;
  END IF;
  RETURN NEW;
END $$;

-- index_values have no source column of their own: they inherit the terms and fetch status of their series' source.
CREATE FUNCTION check_index_value_source() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE rs text; vm text;
BEGIN
  SELECT s.reuse_status, s.verification_method INTO rs, vm FROM indices i JOIN sources s ON s.source_id = i.source_id WHERE i.index_id = NEW.index_id;
  IF rs IS NULL THEN RETURN NEW; END IF;
  IF rs IN ('prohibited','restricted_no_storage','licence_required') THEN
    RAISE EXCEPTION 'index_values: series % has a source with reuse_status % - values must not be stored from it', NEW.index_id, rs;
  END IF;
  IF NEW.review_status = 'validated' AND vm NOT IN ('fetched_primary','synthetic_test_fixture') THEN
    RAISE EXCEPTION 'index_values: cannot be validated - the series source was never fetched (verification_method=%)', vm;
  END IF;
  RETURN NEW;
END $$;

-- ---------------------------------------------------------------------
-- Reference: units
-- ---------------------------------------------------------------------
CREATE TABLE units (
  unit_id          text PRIMARY KEY,
  base_code        text NOT NULL,
  qualifier        text,
  name             text NOT NULL,
  dimension        text NOT NULL CHECK (dimension IN ('count','length','area','volume','mass','time','cooling_capacity')),
  base_unit_id     text NOT NULL,
  to_base_num      bigint,
  to_base_den      bigint,
  factor_formula   text,
  definition       text NOT NULL,
  is_fixed_conversion boolean NOT NULL,
  CONSTRAINT units_factor_chk CHECK (
    (is_fixed_conversion AND to_base_num > 0 AND to_base_den > 0)
    OR (NOT is_fixed_conversion AND to_base_num IS NULL AND to_base_den IS NULL)),
  -- NULL-safe: a bare TON or GAL (qualifier NULL) must fail these checks, not slip through as "unknown"
  CONSTRAINT units_qualifier_chk CHECK (
    (base_code IN ('TON','GAL') AND qualifier IS NOT NULL AND qualifier IN ('short','long','metric','refrigeration','us_liquid','imperial'))
    OR (base_code NOT IN ('TON','GAL') AND qualifier IS NULL)),
  CONSTRAINT units_qualifier_match_chk CHECK (
    (base_code <> 'TON' OR (qualifier IS NOT NULL AND qualifier IN ('short','long','metric','refrigeration')))
    AND (base_code <> 'GAL' OR (qualifier IS NOT NULL AND qualifier IN ('us_liquid','imperial'))))
);

-- every unit must convert to a unit of the same dimension, and base units must exist
ALTER TABLE units ADD CONSTRAINT units_base_fk FOREIGN KEY (base_unit_id) REFERENCES units(unit_id) DEFERRABLE INITIALLY DEFERRED;

-- a unit's base unit must be of the same dimension and must be its own base (checked at commit)
CREATE FUNCTION check_unit_base() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE d text; b text;
BEGIN
  SELECT dimension, base_unit_id INTO d, b FROM units WHERE unit_id = NEW.base_unit_id;
  IF d IS DISTINCT FROM NEW.dimension OR b IS DISTINCT FROM NEW.base_unit_id THEN
    RAISE EXCEPTION 'unit %: base unit % must have dimension % and be its own base', NEW.unit_id, NEW.base_unit_id, NEW.dimension;
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER units_base_dimension AFTER INSERT ON units DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_unit_base();
CREATE TRIGGER units_immutable BEFORE UPDATE OR DELETE ON units FOR EACH ROW EXECUTE FUNCTION forbid_any_change();
CREATE TRIGGER units_no_truncate BEFORE TRUNCATE ON units FOR EACH STATEMENT EXECUTE FUNCTION forbid_truncate();

-- ---------------------------------------------------------------------
-- Reference: regions
-- ---------------------------------------------------------------------
CREATE TABLE regions (
  region_id          id_t PRIMARY KEY,
  level              text NOT NULL CHECK (level IN ('country','state','msa','metro_division','county','zip3','zip','custom')),
  name               text NOT NULL,
  parent_region_id   id_t REFERENCES regions(region_id),
  state_code         char(2),
  fips_code          text,
  cbsa_code          text,
  origin             origin_t NOT NULL,
  assumption_basis   text,
  review_status      review_status_t NOT NULL DEFAULT 'unreviewed',
  notes              text,
  CONSTRAINT regions_origin_basis_chk CHECK (origin <> 'assumed' OR assumption_basis IS NOT NULL)
);

-- ---------------------------------------------------------------------
-- Reference: categories (OWN codes; no CSI/RSMeans identifiers)
-- ---------------------------------------------------------------------
CREATE TABLE categories (
  category_id        id_t PRIMARY KEY,
  name               text NOT NULL,
  parent_category_id id_t REFERENCES categories(category_id),
  description        text,
  pilot              boolean NOT NULL DEFAULT false,
  required_product_attributes jsonb NOT NULL DEFAULT '[]'::jsonb,
  external_refs      jsonb NOT NULL DEFAULT '{}'::jsonb,
  notes              text,
  CONSTRAINT categories_attr_array_chk CHECK (jsonb_typeof(required_product_attributes) = 'array')
);

-- Canonical spec_key in SQL: must stay identical to costdb.ids.spec_key (tests compare both for every spec line).
CREATE FUNCTION norm_attr(v jsonb) RETURNS text LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE raw text; t text;
BEGIN
  CASE jsonb_typeof(v)
    WHEN 'number'  THEN RETURN trim_scale((v #>> '{}')::numeric)::text;
    WHEN 'boolean' THEN RETURN v #>> '{}';
    WHEN 'string'  THEN
      raw := v #>> '{}';
      -- attribute text is plain ASCII (write 1/2 in, not a vulgar-fraction character): lower-casing and whitespace rules then agree
      -- exactly with costdb.ids.norm_attr_value in Python. Only space, tab, LF, CR, FF, VT count as whitespace.
      IF raw ~ '[^\x20-\x7E\x09-\x0D]' THEN
        RAISE EXCEPTION 'attribute value % contains non-ASCII or control characters', quote_literal(raw);
      END IF;
      t := btrim(raw, E' \t\n\r\f' || chr(11));       -- (E'' strings have no \v escape)
      IF t ~ '^-?[0-9]+(\.[0-9]+)?$' THEN RETURN trim_scale(t::numeric)::text; END IF;
      RETURN translate(regexp_replace(t, '[ \t\n\r\f\v]+', ' ', 'g'), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz');   -- locale-proof lower()
    ELSE RETURN NULL;
  END CASE;
END $$;

CREATE FUNCTION compute_spec_key(cat text, attrs jsonb) RETURNS text LANGUAGE plpgsql STABLE AS $$
DECLARE req jsonb; nm text; parts text[] := '{}'; val text;
BEGIN
  SELECT required_product_attributes INTO req FROM categories WHERE category_id = cat;
  IF req IS NULL OR jsonb_array_length(req) = 0 THEN
    RAISE EXCEPTION 'category % is not a leaf category (it defines no required product attributes)', cat;
  END IF;
  FOR nm IN SELECT e.n FROM jsonb_array_elements_text(req) AS e(n) ORDER BY e.n COLLATE "C" LOOP
    val := CASE WHEN attrs -> nm IS NULL THEN NULL ELSE norm_attr(attrs -> nm) END;
    IF val IS NULL OR val = '' OR val IN ('unspecified','unknown','n/a','tbd') THEN
      RAISE EXCEPTION 'category %: required attribute % is missing - equivalence is never guessed', cat, nm;
    END IF;
    parts := parts || (nm || '=' || val);
  END LOOP;
  RETURN cat || '|' || array_to_string(parts, '|');
END $$;

-- ---------------------------------------------------------------------
-- Reference: trades and equipment types (OWN codes; SOC mapping is for BLS joins only)
-- ---------------------------------------------------------------------
CREATE TABLE trades (
  trade_code       id_t PRIMARY KEY,
  name             text NOT NULL,
  soc_code         text,
  soc_status       text NOT NULL DEFAULT 'pending_verification' CHECK (soc_status IN ('verified_against_bls','pending_verification','not_applicable')),
  description      text,
  origin           origin_t NOT NULL DEFAULT 'assumed' CHECK (origin IN ('observed','assumed')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  notes            text
);

CREATE TABLE equipment_types (
  equipment_type_code id_t PRIMARY KEY,
  name             text NOT NULL,
  description      text,
  typically_needs_operator boolean,
  origin           origin_t NOT NULL DEFAULT 'assumed' CHECK (origin IN ('observed','assumed')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  notes            text
);

-- ---------------------------------------------------------------------
-- sources
-- ---------------------------------------------------------------------
CREATE TABLE sources (
  source_id        id_t PRIMARY KEY,
  title            text NOT NULL,
  owner            text NOT NULL,
  source_kind      text NOT NULL CHECK (source_kind IN
                    ('government_dataset','government_publication','government_bid_data','manufacturer_doc',
                     'retailer_catalog','distributor_catalog','index_publisher','standard_or_code','internal','other')),
  url              text,
  data_url         text,
  data_provided    text,
  geography        text,
  period_covered   text,
  edition          text,
  access_format    text,
  requires_registration boolean,
  requires_payment boolean,
  access_notes     text,
  reuse_status     text NOT NULL DEFAULT 'unknown_needs_check' CHECK (reuse_status IN
                    ('public_domain','open_license','permitted_with_attribution',
                     'restricted_no_automated_access','restricted_no_storage','licence_required',
                     'prohibited','unknown_needs_check')),
  reuse_terms      text,
  reuse_terms_url  text,
  limitations      text,
  update_frequency text,
  quality_tier     text NOT NULL DEFAULT 'X' CHECK (quality_tier IN ('A','B','C','D','E','X')),
  reachability_from_build_env text NOT NULL DEFAULT 'not_tested' CHECK (reachability_from_build_env IN
                    ('reachable','blocked_by_network_policy','not_tested')),
  reachability_checked_at date,
  verification_method text NOT NULL CHECK (verification_method IN
                    ('fetched_primary','search_snippet_only','prior_knowledge_unverified','synthetic_test_fixture')),
  evidence_quote   text,
  evidence_url     text,
  origin           origin_t NOT NULL DEFAULT 'observed',
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  registered_at    date NOT NULL DEFAULT current_date,
  notes            text,
  CONSTRAINT sources_synthetic_chk CHECK (verification_method <> 'synthetic_test_fixture' OR source_id LIKE 'TEST-%'),
  CONSTRAINT sources_validated_fetch_chk CHECK (review_status <> 'validated' OR verification_method IN ('fetched_primary','synthetic_test_fixture')),
  CONSTRAINT sources_validated_terms_chk CHECK (review_status <> 'validated' OR reuse_status NOT IN ('prohibited','restricted_no_storage','licence_required')),
  CONSTRAINT sources_fetched_evidence_chk CHECK (verification_method <> 'fetched_primary' OR (evidence_url IS NOT NULL AND evidence_quote IS NOT NULL))
);

-- ---------------------------------------------------------------------
-- products  (one row per manufacturer part; retailer SKUs live on observations)
-- ---------------------------------------------------------------------
CREATE TABLE products (
  product_id       id_t PRIMARY KEY,
  category_id      id_t NOT NULL REFERENCES categories(category_id),
  name             text NOT NULL,
  brand            text,
  manufacturer     text,
  mpn              text,
  description      text,
  spec_attributes  jsonb NOT NULL DEFAULT '{}'::jsonb,
  spec_key         text NOT NULL,
  standards        text[] NOT NULL DEFAULT '{}',
  sale_unit_label  text NOT NULL,
  content_qty      numeric(18,6) NOT NULL CHECK (content_qty > 0),
  content_unit_id  text NOT NULL REFERENCES units(unit_id),
  content_note     text,
  source_id        id_t NOT NULL REFERENCES sources(source_id),
  source_locator   text,
  evidence_excerpt text,
  origin           origin_t NOT NULL DEFAULT 'observed' CHECK (origin IN ('observed','assumed')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT products_attr_obj_chk CHECK (jsonb_typeof(spec_attributes) = 'object')
);
CREATE UNIQUE INDEX products_mfr_mpn_uq ON products (lower(manufacturer), lower(mpn)) WHERE mpn IS NOT NULL AND manufacturer IS NOT NULL;
CREATE INDEX products_spec_key_idx ON products (spec_key);
CREATE INDEX products_category_idx ON products (category_id);

-- spec_key must be the canonical key of the attributes (leaf category, all required attributes present)
CREATE FUNCTION products_spec_integrity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.spec_key IS DISTINCT FROM compute_spec_key(NEW.category_id, NEW.spec_attributes) THEN
    RAISE EXCEPTION 'product %: spec_key % does not match the canonical key of its attributes (%)', NEW.product_id, NEW.spec_key,
      compute_spec_key(NEW.category_id, NEW.spec_attributes);
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER products_spec_integrity_trg BEFORE INSERT OR UPDATE ON products
  FOR EACH ROW EXECUTE FUNCTION products_spec_integrity();

-- ---------------------------------------------------------------------
-- product_consumption  (manufacturer coverage/yield WITH film thickness, coats, conditions)
-- ---------------------------------------------------------------------
CREATE TABLE product_consumption (
  consumption_id   id_t PRIMARY KEY,
  product_id       id_t NOT NULL REFERENCES products(product_id),
  application      text NOT NULL,
  coverage_qty     numeric(18,6),
  coverage_unit_id text REFERENCES units(unit_id),
  per_qty          numeric(18,6) NOT NULL DEFAULT 1 CHECK (per_qty > 0),
  per_unit_id      text REFERENCES units(unit_id),
  film_thickness   text,
  coats            numeric(4,1),
  substrate_condition text,
  application_method text,
  conditions       text,
  source_id        id_t REFERENCES sources(source_id),
  source_locator   text,
  evidence_excerpt text,
  retrieved_at     timestamptz,
  origin           origin_t NOT NULL DEFAULT 'observed' CHECK (origin IN ('observed','missing')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT pc_observed_chk CHECK (origin <> 'observed' OR
    (source_id IS NOT NULL AND coverage_qty IS NOT NULL AND coverage_unit_id IS NOT NULL AND per_unit_id IS NOT NULL
     AND source_locator IS NOT NULL AND coats IS NOT NULL)),
  CONSTRAINT pc_missing_chk CHECK (origin <> 'missing' OR coverage_qty IS NULL),
  CONSTRAINT pc_positive_chk CHECK ((coverage_qty IS NULL OR coverage_qty > 0) AND (coats IS NULL OR coats > 0)),
  CONSTRAINT pc_units_chk CHECK (origin <> 'observed' OR coverage_unit_id <> per_unit_id)
);
CREATE TRIGGER pc_append_only BEFORE UPDATE OR DELETE ON product_consumption
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- price_observations  (append-only price history)
-- ---------------------------------------------------------------------
CREATE TABLE price_observations (
  observation_id   id_t PRIMARY KEY,
  product_id       id_t NOT NULL REFERENCES products(product_id),
  source_id        id_t NOT NULL REFERENCES sources(source_id),
  retailer_sku     text,
  store_ref        text,
  zip              char(5) CHECK (zip ~ '^[0-9]{5}$'),
  region_id        id_t REFERENCES regions(region_id),
  observed_at      date NOT NULL,
  retrieved_at     timestamptz NOT NULL,
  price_amount     numeric(14,4) NOT NULL CHECK (price_amount > 0),
  currency         currency_t NOT NULL DEFAULT 'USD',
  original_price_text text,
  price_channel    text NOT NULL CHECK (price_channel IN
                    ('retail_public','retail_promo','pro_account_quote','distributor_quote',
                     'manufacturer_msrp','public_price_list','supplier_quote')),
  is_contractor_cost boolean NOT NULL DEFAULT false,
  sold_as_label    text NOT NULL,
  pack_content_qty numeric(18,6) NOT NULL CHECK (pack_content_qty > 0),
  pack_content_unit_id text NOT NULL REFERENCES units(unit_id),
  price_per_content_unit numeric(18,8) GENERATED ALWAYS AS (price_amount / NULLIF(pack_content_qty, 0)) STORED,
  availability     text NOT NULL DEFAULT 'unknown' CHECK (availability IN
                    ('in_stock','limited','out_of_stock','special_order','unknown')),
  delivery_included boolean,
  sales_tax_included boolean,
  promo_flag       boolean NOT NULL DEFAULT false,
  qty_limit_text   text,
  qty_tier_min     numeric(18,6),
  url              text,
  source_locator   text,
  evidence_excerpt text NOT NULL,
  raw_file_sha256  text,
  capture_method   text NOT NULL CHECK (capture_method IN
                    ('manual_browser','licensed_feed','official_api','public_price_list','supplier_quote_document')),
  captured_by      text NOT NULL CHECK (length(trim(captured_by)) > 0),
  origin           origin_t NOT NULL DEFAULT 'observed' CHECK (origin = 'observed'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT po_dates_chk CHECK (retrieved_at >= (observed_at::timestamp AT TIME ZONE 'UTC') - interval '1 day'),
  CONSTRAINT po_promo_chk CHECK (price_channel <> 'retail_promo' OR promo_flag),
  CONSTRAINT po_contractor_chk CHECK (NOT is_contractor_cost OR price_channel IN ('pro_account_quote','distributor_quote','supplier_quote')),
  CONSTRAINT po_location_chk CHECK (zip IS NOT NULL OR store_ref IS NOT NULL OR region_id IS NOT NULL)
);
CREATE INDEX po_product_date_idx ON price_observations (product_id, observed_at DESC);
CREATE INDEX po_region_idx ON price_observations (region_id);

-- the observation's pack must be the product's pack (a different pack size is a different SKU)
CREATE FUNCTION po_pack_integrity() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE q numeric; u text;
BEGIN
  SELECT content_qty, content_unit_id INTO q, u FROM products WHERE product_id = NEW.product_id;
  IF q IS DISTINCT FROM NEW.pack_content_qty OR u IS DISTINCT FROM NEW.pack_content_unit_id THEN
    RAISE EXCEPTION 'observation %: pack % % differs from the product pack % % (different SKU?)', NEW.observation_id,
      NEW.pack_content_qty, NEW.pack_content_unit_id, q, u;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER po_pack_integrity_trg BEFORE INSERT ON price_observations
  FOR EACH ROW EXECUTE FUNCTION po_pack_integrity();
CREATE TRIGGER po_append_only BEFORE UPDATE OR DELETE ON price_observations
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- calculation_runs / calculation_run_lines   (created early: derived rows reference them)
-- ---------------------------------------------------------------------
CREATE TABLE calculation_runs (
  run_id           id_t PRIMARY KEY,
  run_at           timestamptz NOT NULL DEFAULT now(),
  calc_version     text NOT NULL,
  target_type      text NOT NULL CHECK (target_type IN ('unit_cost','assembly','labor_loaded','index_adjustment','markup')),
  target_id        text NOT NULL,
  target_version   integer,
  mode             text NOT NULL CHECK (mode IN ('strict','with_assumptions')),
  parameters       jsonb NOT NULL DEFAULT '{}'::jsonb,
  status           text NOT NULL CHECK (status IN ('complete','incomplete','failed')),
  has_assumptions  boolean NOT NULL DEFAULT false,
  result_unit_id   text REFERENCES units(unit_id),
  material_cost    numeric(18,6),
  labor_cost       numeric(18,6),
  equipment_cost   numeric(18,6),
  other_direct_cost numeric(18,6),
  direct_cost_total numeric(18,6),
  missing_inputs   jsonb NOT NULL DEFAULT '[]'::jsonb,
  warnings         jsonb NOT NULL DEFAULT '[]'::jsonb,
  code_ref         text,
  price_basis      text NOT NULL DEFAULT 'none' CHECK (price_basis IN ('none','contractor_quote','public_list','retail_proxy','assumed','mixed')),
  input_review_floor text NOT NULL DEFAULT 'validated' CHECK (input_review_floor IN ('validated','unreviewed')),
  price_total      numeric(18,6),
  origin           origin_t NOT NULL DEFAULT 'derived' CHECK (origin = 'derived'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  notes            text,
  CONSTRAINT cr_complete_chk CHECK (status <> 'complete' OR (direct_cost_total IS NOT NULL AND jsonb_array_length(missing_inputs) = 0)),
  CONSTRAINT cr_strict_chk CHECK (NOT (mode = 'strict' AND has_assumptions)),
  CONSTRAINT cr_markup_chk CHECK ((target_type = 'markup') = (price_total IS NOT NULL)),
  CONSTRAINT cr_floor_chk CHECK (NOT (mode = 'strict' AND input_review_floor = 'unreviewed' AND status = 'complete' AND review_status = 'validated'))
);
CREATE INDEX cr_target_idx ON calculation_runs (target_type, target_id, run_at DESC);

CREATE TABLE calculation_run_lines (
  run_id           id_t NOT NULL REFERENCES calculation_runs(run_id),
  line_no          integer NOT NULL,
  line_kind        text NOT NULL CHECK (line_kind IN ('material','labor','equipment','other_direct','overhead','contingency','profit','adjustment','subtotal','assembly_component')),
  component_ref    text,
  description      text NOT NULL,
  quantity         numeric(24,10),
  quantity_unit_id text REFERENCES units(unit_id),
  quantity_kind    text NOT NULL DEFAULT 'none' CHECK (quantity_kind IN ('material_qty','person_hours','crew_hours','equipment_hours','work_item_qty','none')),
  unit_cost        numeric(24,10),
  extended_cost    numeric(24,10),
  formula          text NOT NULL,
  inputs           jsonb NOT NULL DEFAULT '[]'::jsonb,
  origin_summary   text NOT NULL CHECK (origin_summary IN ('observed','derived','assumed','mixed','missing')),
  warnings         jsonb NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (run_id, line_no)
);

-- a 'complete' run must have lines and its total must equal the sum of its cost lines (checked at commit: insert run and lines in ONE transaction)
CREATE FUNCTION check_complete_run() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE n int; s numeric;
BEGIN
  IF NEW.status = 'complete' THEN
    SELECT count(*), COALESCE(sum(extended_cost) FILTER (WHERE line_kind IN ('material','labor','equipment','other_direct','assembly_component')), 0)
      INTO n, s FROM calculation_run_lines WHERE run_id = NEW.run_id;
    IF n = 0 THEN
      RAISE EXCEPTION 'complete run % has no lines', NEW.run_id;
    END IF;
    IF NEW.target_type <> 'markup' AND abs(s - NEW.direct_cost_total) > 0.0005 THEN
      RAISE EXCEPTION 'complete run %: total % differs from the sum of its lines %', NEW.run_id, NEW.direct_cost_total, s;
    END IF;
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER cr_complete_integrity AFTER INSERT ON calculation_runs DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_complete_run();

-- ---------------------------------------------------------------------
-- labor_rates
-- ---------------------------------------------------------------------
CREATE TABLE labor_rates (
  labor_rate_id    id_t PRIMARY KEY,
  rate_type        text NOT NULL CHECK (rate_type IN
                    ('stat_wage','prevailing_wage','federal_wage_determination',
                     'employer_compensation_index','loaded_employer_cost','company_actual')),
  trade_code       id_t NOT NULL REFERENCES trades(trade_code),
  classification_raw text NOT NULL,
  soc_code         text,
  statistic        text CHECK (statistic IN ('mean','median','p10','p25','p75','p90','determined','actual','n/a')),
  region_id        id_t NOT NULL REFERENCES regions(region_id),
  base_wage_hr     numeric(12,4) CHECK (base_wage_hr >= 0),
  fringe_hr        numeric(12,4) CHECK (fringe_hr >= 0),
  fringe_breakdown jsonb,
  payroll_tax_hr   numeric(12,4) CHECK (payroll_tax_hr >= 0),
  workers_comp_hr  numeric(12,4) CHECK (workers_comp_hr >= 0),
  other_employer_cost_hr numeric(12,4) CHECK (other_employer_cost_hr >= 0),
  total_hr         numeric(12,4) CHECK (total_hr >= 0),
  includes_fringe  boolean NOT NULL,
  includes_payroll_taxes boolean NOT NULL,
  includes_workers_comp boolean NOT NULL,
  includes_overhead boolean NOT NULL DEFAULT false,
  includes_profit  boolean NOT NULL DEFAULT false,
  wage_basis       text NOT NULL DEFAULT 'straight_time' CHECK (wage_basis IN ('straight_time','overtime_1_5x','overtime_2x','n/a')),
  project_type     text NOT NULL DEFAULT 'n/a' CHECK (project_type IN ('building','residential','heavy','highway','n/a')),
  use_context      text NOT NULL CHECK (use_context IN ('public_works_only','statistical_reference','employer_internal')),
  apprentice       boolean NOT NULL DEFAULT false,
  determination_ref text,
  effective_from   date NOT NULL,
  effective_to     date,
  retrieved_at     timestamptz,
  derived_from     text[],
  calc_run_id      id_t REFERENCES calculation_runs(run_id),
  source_id        id_t REFERENCES sources(source_id),
  source_locator   text,
  evidence_excerpt text,
  raw_file_sha256  text,
  origin           origin_t NOT NULL,
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT lr_origin_chk CHECK (origin IN ('observed','derived','missing')),
  CONSTRAINT lr_observed_chk CHECK (origin <> 'observed' OR
    (source_id IS NOT NULL AND source_locator IS NOT NULL AND evidence_excerpt IS NOT NULL AND retrieved_at IS NOT NULL
     AND base_wage_hr IS NOT NULL)),
  CONSTRAINT lr_derived_chk CHECK (origin <> 'derived' OR
    (calc_run_id IS NOT NULL AND derived_from IS NOT NULL AND array_length(derived_from,1) >= 1 AND total_hr IS NOT NULL)),
  CONSTRAINT lr_missing_chk CHECK (origin <> 'missing' OR (base_wage_hr IS NULL AND total_hr IS NULL)),
  CONSTRAINT lr_loaded_derived_chk CHECK (rate_type <> 'loaded_employer_cost' OR origin = 'derived'),
  CONSTRAINT lr_pw_scope_chk CHECK (rate_type NOT IN ('prevailing_wage','federal_wage_determination') OR use_context = 'public_works_only'),
  CONSTRAINT lr_stat_scope_chk CHECK (rate_type <> 'stat_wage' OR (use_context = 'statistical_reference' AND includes_fringe = false)),
  CONSTRAINT lr_period_chk CHECK (effective_to IS NULL OR effective_to >= effective_from),
  CONSTRAINT lr_ovh_profit_chk CHECK (NOT (includes_overhead OR includes_profit) OR rate_type = 'company_actual'),
  CONSTRAINT lr_stat_burden_chk CHECK (rate_type <> 'stat_wage' OR (NOT includes_payroll_taxes AND NOT includes_workers_comp)),
  CONSTRAINT lr_total_chk CHECK (total_hr IS NULL OR NOT (includes_fringe AND includes_payroll_taxes AND includes_workers_comp)
    OR base_wage_hr IS NULL OR fringe_hr IS NULL OR payroll_tax_hr IS NULL OR workers_comp_hr IS NULL
    OR abs(total_hr - (base_wage_hr + fringe_hr + payroll_tax_hr + workers_comp_hr + COALESCE(other_employer_cost_hr, 0))) <= 0.0005)
);
CREATE INDEX lr_trade_region_idx ON labor_rates (trade_code, region_id, effective_from DESC);
CREATE TRIGGER lr_append_only BEFORE UPDATE OR DELETE ON labor_rates
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- burden_rates  (employer percentage / per-hour items, kept apart from wages)
-- ---------------------------------------------------------------------
CREATE TABLE burden_rates (
  burden_id        id_t PRIMARY KEY,
  burden_type      text NOT NULL CHECK (burden_type IN
                    ('fica_social_security','fica_medicare','futa','state_ui','state_ett','workers_comp',
                     'employer_benefits','general_liability','other')),
  basis            text NOT NULL CHECK (basis IN ('pct_of_wages','per_hour','per_100_payroll')),
  rate             numeric(14,6) NOT NULL CHECK (rate >= 0),
  wage_cap_annual  numeric(14,2),
  class_code       text,
  trade_code       id_t REFERENCES trades(trade_code),
  region_id        id_t REFERENCES regions(region_id),
  effective_from   date NOT NULL,
  effective_to     date,
  retrieved_at     timestamptz,
  source_id        id_t REFERENCES sources(source_id),
  source_locator   text,
  evidence_excerpt text,
  origin           origin_t NOT NULL CHECK (origin IN ('observed','missing')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT br_observed_chk CHECK (origin <> 'observed' OR (source_id IS NOT NULL AND source_locator IS NOT NULL AND evidence_excerpt IS NOT NULL)),
  CONSTRAINT br_period_chk CHECK (effective_to IS NULL OR effective_to >= effective_from),
  CONSTRAINT br_cap_chk CHECK (wage_cap_annual IS NULL OR (basis <> 'per_hour' AND wage_cap_annual > 0))
);
CREATE TRIGGER br_append_only BEFORE UPDATE OR DELETE ON burden_rates
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- equipment_rates
-- ---------------------------------------------------------------------
CREATE TABLE equipment_rates (
  equipment_rate_id id_t PRIMARY KEY,
  equipment_type_code id_t NOT NULL REFERENCES equipment_types(equipment_type_code),
  description_raw  text NOT NULL,
  make_model_raw   text,
  capacity_raw     text,
  rate_basis       text NOT NULL CHECK (rate_basis IN ('rental_market','owned_cost_schedule','dot_schedule','usace_schedule')),
  ownership_cost_hr numeric(12,4) CHECK (ownership_cost_hr >= 0),
  operating_cost_hr numeric(12,4) CHECK (operating_cost_hr >= 0),
  fuel_cost_hr     numeric(12,4) CHECK (fuel_cost_hr >= 0),
  rental_rate_hr   numeric(12,4) CHECK (rental_rate_hr >= 0),
  rental_rate_day  numeric(12,4) CHECK (rental_rate_day >= 0),
  rental_rate_week numeric(12,4) CHECK (rental_rate_week >= 0),
  rental_rate_month numeric(12,4) CHECK (rental_rate_month >= 0),
  min_rental_period text,
  delivery_pickup_cost numeric(12,4) CHECK (delivery_pickup_cost >= 0),
  fuel_included    boolean,
  operator_included boolean NOT NULL,
  region_id        id_t NOT NULL REFERENCES regions(region_id),
  effective_from   date NOT NULL,
  effective_to     date,
  retrieved_at     timestamptz,
  source_id        id_t REFERENCES sources(source_id),
  source_locator   text,
  evidence_excerpt text,
  raw_file_sha256  text,
  origin           origin_t NOT NULL CHECK (origin IN ('observed','missing')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT er_observed_chk CHECK (origin <> 'observed' OR
    (source_id IS NOT NULL AND source_locator IS NOT NULL AND evidence_excerpt IS NOT NULL AND retrieved_at IS NOT NULL
     AND (rental_rate_hr IS NOT NULL OR rental_rate_day IS NOT NULL OR rental_rate_week IS NOT NULL
          OR rental_rate_month IS NOT NULL OR ownership_cost_hr IS NOT NULL OR operating_cost_hr IS NOT NULL))),
  CONSTRAINT er_period_chk CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE INDEX er_type_region_idx ON equipment_rates (equipment_type_code, region_id, effective_from DESC);
CREATE TRIGGER er_append_only BEFORE UPDATE OR DELETE ON equipment_rates
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- crews / crew_members  (composition only; rates are resolved at calc time)
-- ---------------------------------------------------------------------
CREATE TABLE crews (
  crew_id          id_t PRIMARY KEY,
  name             text NOT NULL,
  description      text,
  category_id      id_t REFERENCES categories(category_id),
  shift_hours      numeric(5,2) CHECK (shift_hours > 0 AND shift_hours <= 24),
  source_id        id_t REFERENCES sources(source_id),
  source_locator   text,
  assumption_basis text,
  origin           origin_t NOT NULL CHECK (origin IN ('observed','assumed','missing')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT crews_observed_chk CHECK (origin <> 'observed' OR (source_id IS NOT NULL AND source_locator IS NOT NULL)),
  CONSTRAINT crews_assumed_chk CHECK (origin <> 'assumed' OR assumption_basis IS NOT NULL),
  CONSTRAINT crews_shift_chk CHECK (origin = 'missing' OR shift_hours IS NOT NULL)
);

CREATE TABLE crew_members (
  crew_member_id   id_t PRIMARY KEY,
  crew_id          id_t NOT NULL REFERENCES crews(crew_id),
  member_kind      text NOT NULL CHECK (member_kind IN ('labor','equipment')),
  trade_code       id_t REFERENCES trades(trade_code),
  equipment_type_code id_t REFERENCES equipment_types(equipment_type_code),
  labor_rate_id    id_t REFERENCES labor_rates(labor_rate_id),
  equipment_rate_id id_t REFERENCES equipment_rates(equipment_rate_id),
  quantity         numeric(8,3) NOT NULL CHECK (quantity > 0),
  hours_per_shift  numeric(5,2) CHECK (hours_per_shift > 0),
  is_operator      boolean NOT NULL DEFAULT false,
  notes            text,
  CONSTRAINT cm_kind_chk CHECK (
    (member_kind = 'labor' AND trade_code IS NOT NULL AND equipment_type_code IS NULL AND equipment_rate_id IS NULL)
    OR (member_kind = 'equipment' AND equipment_type_code IS NOT NULL AND trade_code IS NULL AND labor_rate_id IS NULL AND NOT is_operator))
);
CREATE INDEX cm_crew_idx ON crew_members (crew_id);

-- ---------------------------------------------------------------------
-- work_items (versioned unit-cost operations) — definition tables
-- ---------------------------------------------------------------------
CREATE TABLE work_items (
  work_item_id     id_t NOT NULL,
  version          integer NOT NULL CHECK (version >= 1),
  name             text NOT NULL,
  category_id      id_t NOT NULL REFERENCES categories(category_id),
  spec_attributes  jsonb NOT NULL DEFAULT '{}'::jsonb,
  output_unit_id   text NOT NULL REFERENCES units(unit_id),
  description      text NOT NULL,
  included_scope   text[] NOT NULL DEFAULT '{}',
  excluded_scope   text[] NOT NULL DEFAULT '{}',
  conditions       text,
  status           text NOT NULL DEFAULT 'defined' CHECK (status IN ('defined','priced_incomplete','priced_with_assumptions','priced_verified','retired')),
  valid_from       date NOT NULL,
  supersedes_version integer,
  definition_basis text NOT NULL,
  origin           origin_t NOT NULL DEFAULT 'assumed' CHECK (origin IN ('observed','assumed')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  PRIMARY KEY (work_item_id, version),
  CONSTRAINT wi_spec_obj_chk CHECK (jsonb_typeof(spec_attributes) = 'object')
);

CREATE TABLE work_item_components (
  component_id     id_t PRIMARY KEY,
  work_item_id     id_t NOT NULL,
  work_item_version integer NOT NULL,
  line_no          integer NOT NULL,
  component_kind   cost_component_t NOT NULL,
  description      text NOT NULL,
  product_spec_key text,
  product_id       id_t REFERENCES products(product_id),
  qty_mode         text NOT NULL DEFAULT 'fixed' CHECK (qty_mode IN ('fixed','from_product_consumption','from_productivity')),
  equipment_type_code id_t REFERENCES equipment_types(equipment_type_code),
  qty_per_unit     numeric(24,10) CHECK (qty_per_unit >= 0),
  qty_unit_id      text REFERENCES units(unit_id),
  qty_formula      text,
  qty_origin       origin_t NOT NULL CHECK (qty_origin IN ('derived','observed','missing')),
  waste_factor     numeric(8,5) CHECK (waste_factor >= 0 AND waste_factor < 1),
  waste_origin     origin_t CHECK (waste_origin IN ('observed','derived')),
  waste_basis      text,
  crew_id          id_t REFERENCES crews(crew_id),
  productivity_id  id_t,
  consumption_application text,
  consumption_selector jsonb CHECK (consumption_selector IS NULL OR jsonb_typeof(consumption_selector) = 'object'),
  coats_applied    numeric(4,1) CHECK (coats_applied > 0),
  cost_tags        text[] NOT NULL DEFAULT '{}',
  is_optional      boolean NOT NULL DEFAULT false,
  notes            text,
  UNIQUE (work_item_id, work_item_version, line_no),
  FOREIGN KEY (work_item_id, work_item_version) REFERENCES work_items(work_item_id, version),
  CONSTRAINT wic_material_chk CHECK (component_kind <> 'material' OR product_spec_key IS NOT NULL OR product_id IS NOT NULL),
  CONSTRAINT wic_labor_chk CHECK (component_kind NOT IN ('labor','equipment') OR (crew_id IS NOT NULL AND productivity_id IS NOT NULL)),
  CONSTRAINT wic_equipment_chk CHECK ((component_kind = 'equipment') = (equipment_type_code IS NOT NULL)),
  CONSTRAINT wic_fixed_chk CHECK (qty_mode <> 'fixed' OR qty_origin = 'missing' OR (qty_per_unit IS NOT NULL AND qty_unit_id IS NOT NULL AND qty_formula IS NOT NULL)),
  CONSTRAINT wic_waste_chk CHECK (waste_factor IS NULL OR (waste_origin IN ('observed','derived') AND waste_basis IS NOT NULL)),
  CONSTRAINT wic_consumption_chk CHECK (qty_mode <> 'from_product_consumption' OR (consumption_application IS NOT NULL AND coats_applied IS NOT NULL AND product_spec_key IS NOT NULL))
);

-- ---------------------------------------------------------------------
-- productivity_observations
-- ---------------------------------------------------------------------
CREATE TABLE productivity_observations (
  productivity_id  id_t PRIMARY KEY,
  work_item_id     id_t,
  operation_text   text NOT NULL,
  category_id      id_t REFERENCES categories(category_id),
  output_unit_id   text NOT NULL REFERENCES units(unit_id),
  crew_id          id_t REFERENCES crews(crew_id),
  crew_description_raw text,
  crew_size        numeric(8,3) CHECK (crew_size > 0),
  shift_hours      numeric(5,2) CHECK (shift_hours > 0),
  daily_output     numeric(18,6) CHECK (daily_output > 0),
  person_hours_per_unit_reported numeric(18,8) CHECK (person_hours_per_unit_reported > 0),
  person_hours_per_unit_derived numeric(18,8)
    GENERATED ALWAYS AS (crew_size * shift_hours / NULLIF(daily_output, 0)) STORED,
  conditions       text,
  included_operations text,
  excluded_operations text,
  source_id        id_t REFERENCES sources(source_id),
  source_doc       text,
  source_edition   text,
  source_page      text,
  source_table     text,
  source_context   text,
  evidence_excerpt text,
  retrieved_at     timestamptz,
  raw_file_sha256  text,
  missing_reason   text,
  origin           origin_t NOT NULL CHECK (origin IN ('observed','missing')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT prod_observed_chk CHECK (origin <> 'observed' OR
    (source_id IS NOT NULL AND source_doc IS NOT NULL AND source_edition IS NOT NULL AND source_page IS NOT NULL
     AND source_context IS NOT NULL AND evidence_excerpt IS NOT NULL AND retrieved_at IS NOT NULL
     AND (person_hours_per_unit_reported IS NOT NULL OR (crew_size IS NOT NULL AND shift_hours IS NOT NULL AND daily_output IS NOT NULL)))),
  CONSTRAINT prod_missing_chk CHECK (origin <> 'missing' OR
    (crew_size IS NULL AND shift_hours IS NULL AND daily_output IS NULL AND person_hours_per_unit_reported IS NULL AND missing_reason IS NOT NULL))
);
CREATE INDEX prod_work_item_idx ON productivity_observations (work_item_id);
CREATE TRIGGER prod_append_only BEFORE UPDATE OR DELETE ON productivity_observations
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

ALTER TABLE work_item_components
  ADD CONSTRAINT wic_productivity_fk FOREIGN KEY (productivity_id) REFERENCES productivity_observations(productivity_id);

-- ---------------------------------------------------------------------
-- assemblies
-- ---------------------------------------------------------------------
CREATE TABLE assemblies (
  assembly_id      id_t NOT NULL,
  version          integer NOT NULL CHECK (version >= 1),
  name             text NOT NULL,
  category_id      id_t NOT NULL REFERENCES categories(category_id),
  spec_attributes  jsonb NOT NULL,
  output_unit_id   text NOT NULL REFERENCES units(unit_id),
  description      text NOT NULL,
  included_scope   text[] NOT NULL DEFAULT '{}',
  excluded_scope   text[] NOT NULL DEFAULT '{}',
  conditions       text,
  status           text NOT NULL DEFAULT 'defined' CHECK (status IN ('defined','priced_incomplete','priced_with_assumptions','priced_verified','retired')),
  valid_from       date NOT NULL,
  supersedes_version integer,
  definition_basis text NOT NULL,
  origin           origin_t NOT NULL DEFAULT 'assumed' CHECK (origin IN ('observed','assumed')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  PRIMARY KEY (assembly_id, version),
  CONSTRAINT asm_spec_obj_chk CHECK (jsonb_typeof(spec_attributes) = 'object' AND spec_attributes <> '{}'::jsonb)
);

CREATE TABLE assembly_components (
  assembly_component_id id_t PRIMARY KEY,
  assembly_id      id_t NOT NULL,
  assembly_version integer NOT NULL,
  line_no          integer NOT NULL,
  work_item_id     id_t NOT NULL,
  work_item_version integer NOT NULL,
  qty_per_assembly_unit numeric(24,10) NOT NULL CHECK (qty_per_assembly_unit > 0),
  qty_unit_id      text NOT NULL REFERENCES units(unit_id),
  qty_formula      text NOT NULL,
  qty_origin       origin_t NOT NULL CHECK (qty_origin IN ('derived','observed')),
  cost_tags        text[] NOT NULL DEFAULT '{}',
  notes            text,
  UNIQUE (assembly_id, assembly_version, line_no),
  FOREIGN KEY (assembly_id, assembly_version) REFERENCES assemblies(assembly_id, version),
  FOREIGN KEY (work_item_id, work_item_version) REFERENCES work_items(work_item_id, version)
);

-- ---------------------------------------------------------------------
-- bid_benchmarks  (public-contract bid prices: benchmarks only, NEVER a cost input)
-- ---------------------------------------------------------------------
CREATE TABLE bid_benchmarks (
  benchmark_id     id_t PRIMARY KEY,
  source_id        id_t NOT NULL REFERENCES sources(source_id),
  agency           text NOT NULL,
  contract_ref     text,
  item_code_source text,
  item_description text NOT NULL,
  category_id      id_t REFERENCES categories(category_id),
  quantity         numeric(18,4) CHECK (quantity > 0),
  quantity_unit_id text REFERENCES units(unit_id),
  unit_price       numeric(18,6) NOT NULL CHECK (unit_price >= 0),
  unit_price_unit_id text NOT NULL REFERENCES units(unit_id),
  price_statistic  text NOT NULL CHECK (price_statistic IN ('single_bid','low_bid','awarded','average_of_n','median_of_n')),
  sample_size      integer CHECK (sample_size > 0),
  bid_date         date,
  period_end       date,
  region_id        id_t REFERENCES regions(region_id),
  scope_note       text NOT NULL,
  price_nature     text NOT NULL DEFAULT 'bid_price_not_cost' CHECK (price_nature = 'bid_price_not_cost'),
  source_locator   text NOT NULL,
  evidence_excerpt text NOT NULL,
  retrieved_at     timestamptz NOT NULL,
  origin           origin_t NOT NULL DEFAULT 'observed' CHECK (origin = 'observed'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text
);
CREATE TRIGGER bb_append_only BEFORE UPDATE OR DELETE ON bid_benchmarks
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- indices / index_values  (time adjustment inputs; NOT product prices)
-- ---------------------------------------------------------------------
CREATE TABLE indices (
  index_id         id_t PRIMARY KEY,
  publisher        text NOT NULL,
  series_code      text NOT NULL,
  name             text NOT NULL,
  base_period      text,
  frequency        text NOT NULL CHECK (frequency IN ('monthly','quarterly','annual','other')),
  seasonal_adjustment text,
  geography        text,
  applies_to       text NOT NULL CHECK (applies_to IN ('material','labor','equipment','all')),
  source_id        id_t NOT NULL REFERENCES sources(source_id),
  origin           origin_t NOT NULL DEFAULT 'observed' CHECK (origin = 'observed'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  notes            text,
  UNIQUE (publisher, series_code)
);

CREATE TABLE index_values (
  index_id         id_t NOT NULL REFERENCES indices(index_id),
  period_start     date NOT NULL,
  vintage_date     date NOT NULL,
  value            numeric(18,6) NOT NULL CHECK (value > 0),
  value_status     text NOT NULL DEFAULT 'final' CHECK (value_status IN ('preliminary','final','revised')),
  retrieved_at     timestamptz NOT NULL,
  source_locator   text NOT NULL,
  raw_file_sha256  text,
  origin           origin_t NOT NULL DEFAULT 'observed' CHECK (origin = 'observed'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  notes            text,
  PRIMARY KEY (index_id, period_start, vintage_date)
);
CREATE TRIGGER iv_append_only BEFORE UPDATE OR DELETE ON index_values
  FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- ---------------------------------------------------------------------
-- adjustment_factors  (region / time / quantity / condition factors; applies to ONE cost component)
-- ---------------------------------------------------------------------
CREATE TABLE adjustment_factors (
  factor_id        id_t PRIMARY KEY,
  factor_type      text NOT NULL CHECK (factor_type IN ('region','time_index','quantity','conditions','productivity_condition')),
  applies_to       cost_component_t NOT NULL,
  from_region_id   id_t REFERENCES regions(region_id),
  to_region_id     id_t REFERENCES regions(region_id),
  factor_value     numeric(14,8) NOT NULL CHECK (factor_value > 0),
  qty_min          numeric(18,6),
  qty_max          numeric(18,6),
  condition_desc   text,
  valid_from       date,
  valid_to         date,
  index_id         id_t REFERENCES indices(index_id),
  derivation_formula text NOT NULL,
  input_refs       jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_id        id_t REFERENCES sources(source_id),
  assumption_basis text,
  calc_run_id      id_t REFERENCES calculation_runs(run_id),
  origin           origin_t NOT NULL CHECK (origin IN ('observed','derived','assumed')),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  notes            text,
  CONSTRAINT af_observed_chk CHECK (origin <> 'observed' OR source_id IS NOT NULL),
  CONSTRAINT af_derived_chk CHECK (origin <> 'derived' OR (calc_run_id IS NOT NULL AND jsonb_array_length(input_refs) >= 1)),
  CONSTRAINT af_assumed_chk CHECK (origin <> 'assumed' OR assumption_basis IS NOT NULL),
  CONSTRAINT af_region_chk CHECK (factor_type <> 'region' OR (from_region_id IS NOT NULL AND to_region_id IS NOT NULL)),
  CONSTRAINT af_time_chk CHECK (factor_type <> 'time_index' OR index_id IS NOT NULL),
  CONSTRAINT af_qty_chk CHECK (factor_type <> 'quantity' OR (qty_min IS NOT NULL OR qty_max IS NOT NULL)),
  CONSTRAINT af_region_distinct_chk CHECK (factor_type <> 'region' OR from_region_id <> to_region_id),
  CONSTRAINT af_period_chk CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);

-- a time factor may only use an index series that applies to the same cost component
CREATE FUNCTION af_index_integrity() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE a text;
BEGIN
  IF NEW.index_id IS NOT NULL THEN
    SELECT applies_to INTO a FROM indices WHERE index_id = NEW.index_id;
    IF a IS DISTINCT FROM 'all' AND a IS DISTINCT FROM (CASE WHEN NEW.applies_to = 'other_direct' THEN 'material' ELSE NEW.applies_to END) THEN
      RAISE EXCEPTION 'factor %: index % applies to % but the factor applies to %', NEW.factor_id, NEW.index_id, a, NEW.applies_to;
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER af_index_integrity_trg BEFORE INSERT ON adjustment_factors
  FOR EACH ROW EXECUTE FUNCTION af_index_integrity();

-- ---------------------------------------------------------------------
-- assumptions  (expert proposals — stored apart from observed data)
-- ---------------------------------------------------------------------
CREATE TABLE assumptions (
  assumption_id    id_t PRIMARY KEY,
  assumption_type  text NOT NULL CHECK (assumption_type IN
                    ('productivity','waste','crew_composition','material_price','labor_rate','equipment_rate','factor','other')),
  applies_to_ref   text NOT NULL,
  value_numeric    numeric(24,10),
  value_text       text,
  unit_id          text REFERENCES units(unit_id),
  rationale        text NOT NULL,
  proposed_by      text NOT NULL,
  proposed_at      timestamptz NOT NULL DEFAULT now(),
  approved_by      text,
  approved_at      timestamptz,
  status           text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','approved','rejected','superseded')),
  expires_on       date,
  origin           origin_t NOT NULL DEFAULT 'assumed' CHECK (origin = 'assumed'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  notes            text,
  CONSTRAINT as_value_chk CHECK (value_numeric IS NOT NULL OR (assumption_type = 'crew_composition' AND value_text IS NOT NULL)),
  CONSTRAINT as_approval_chk CHECK (status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL AND expires_on IS NOT NULL)),
  CONSTRAINT as_four_eyes_chk CHECK (approved_by IS NULL OR lower(btrim(approved_by)) <> lower(btrim(proposed_by))),
  CONSTRAINT as_range_chk CHECK (value_numeric IS NULL OR
    (assumption_type = 'waste' AND value_numeric >= 0 AND value_numeric < 1)
    OR (assumption_type IN ('productivity','material_price','labor_rate','equipment_rate','factor') AND value_numeric > 0)
    OR assumption_type IN ('crew_composition','other'))
);

-- an assumption's content is immutable; only its approval workflow fields change
CREATE FUNCTION forbid_assumption_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE mutable text[] := ARRAY['status','approved_by','approved_at','expires_on','review_status','notes'];
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'assumptions are never deleted (mark them rejected or superseded)'; END IF;
  IF (to_jsonb(OLD) - mutable) IS DISTINCT FROM (to_jsonb(NEW) - mutable) THEN
    RAISE EXCEPTION 'assumption content is immutable; propose a new assumption and supersede the old one';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER as_immutable BEFORE UPDATE OR DELETE ON assumptions FOR EACH ROW EXECUTE FUNCTION forbid_assumption_rewrite();

-- ---------------------------------------------------------------------
-- capture_targets  (work queue of data still to be collected)
-- ---------------------------------------------------------------------
CREATE TABLE capture_targets (
  target_id        id_t PRIMARY KEY,
  target_kind      text NOT NULL CHECK (target_kind IN ('material','labor','equipment','productivity','index','burden','other')),
  category_id      id_t REFERENCES categories(category_id),
  description      text NOT NULL,
  spec_attributes  jsonb NOT NULL DEFAULT '{}'::jsonb,
  spec_key         text,
  preferred_sale_unit text,
  pilot_priority   integer NOT NULL DEFAULT 2 CHECK (pilot_priority IN (1,2,3)),
  required_by      text,
  recommended_source_ids text[] NOT NULL DEFAULT '{}',
  status           text NOT NULL DEFAULT 'open' CHECK (status IN ('open','in_progress','captured','blocked')),
  blocked_reason   text,
  origin           origin_t NOT NULL DEFAULT 'assumed' CHECK (origin = 'assumed'),
  review_status    review_status_t NOT NULL DEFAULT 'unreviewed',
  notes            text
);

-- ---------------------------------------------------------------------
-- validation_issues
-- ---------------------------------------------------------------------
CREATE TABLE validation_issues (
  issue_id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  detected_at      timestamptz NOT NULL DEFAULT now(),
  detected_by      text NOT NULL,
  record_table     text NOT NULL,
  record_id        text NOT NULL,
  rule_code        text NOT NULL,
  severity         severity_t NOT NULL,
  message          text NOT NULL,
  details          jsonb NOT NULL DEFAULT '{}'::jsonb,
  status           text NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved','waived')),
  resolution_note  text,
  resolved_at      timestamptz,
  CONSTRAINT vi_resolved_chk CHECK (status = 'open' OR resolution_note IS NOT NULL),
  CONSTRAINT vi_waive_chk CHECK (status <> 'waived' OR severity <> 'error')
);
CREATE INDEX vi_record_idx ON validation_issues (record_table, record_id);
CREATE INDEX vi_open_idx ON validation_issues (status, severity);

-- ---------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------
-- All same-dimension unit conversions, derived from the exact rationals in units.
CREATE VIEW v_unit_conversions AS
SELECT f.unit_id AS from_unit_id, t.unit_id AS to_unit_id,
       (f.to_base_num::numeric * t.to_base_den) / (f.to_base_den::numeric * t.to_base_num) AS factor,
       f.dimension
FROM units f JOIN units t ON f.dimension = t.dimension AND f.base_unit_id = t.base_unit_id
WHERE f.is_fixed_conversion AND t.is_fixed_conversion;

-- Price history with normalization (nothing is hidden or averaged).
CREATE VIEW v_price_history AS
SELECT o.observation_id, o.product_id, p.spec_key, p.name, o.observed_at, o.retrieved_at, o.zip, o.store_ref, o.region_id,
       o.price_amount, o.currency, o.sold_as_label, o.pack_content_qty, o.pack_content_unit_id,
       o.price_per_content_unit, o.price_channel, o.is_contractor_cost, o.availability,
       o.delivery_included, o.sales_tax_included, o.promo_flag, o.review_status, o.source_id
FROM price_observations o JOIN products p USING (product_id);

-- Latest VALIDATED, non-promo observation per product+region (a convenience; the calc engine applies its own policy).
CREATE VIEW v_price_latest_validated AS
SELECT DISTINCT ON (product_id, COALESCE(region_id, zip, store_ref)) *
FROM v_price_history
WHERE review_status = 'validated' AND NOT promo_flag
ORDER BY product_id, COALESCE(region_id, zip, store_ref), observed_at DESC, retrieved_at DESC;

-- Confidence is DESCRIBED, never scored: source tier, data age, and spec match.
CREATE VIEW v_price_confidence_facets AS
SELECT o.observation_id, s.quality_tier AS source_quality_tier, s.reuse_status,
       (current_date - o.observed_at) AS age_days,
       o.review_status, o.price_channel, o.is_contractor_cost,
       CASE WHEN p.spec_key IS NOT NULL AND p.spec_attributes <> '{}'::jsonb THEN 'spec_attributes_recorded' ELSE 'spec_unspecified' END AS spec_facet
FROM price_observations o JOIN products p USING (product_id) JOIN sources s ON s.source_id = o.source_id;

CREATE VIEW v_open_issue_summary AS
SELECT record_table, rule_code, severity, count(*) AS open_count
FROM validation_issues WHERE status = 'open' GROUP BY 1,2,3;

-- ---------------------------------------------------------------------
-- Protection wiring (needs every table to exist)
-- ---------------------------------------------------------------------
DO $$
DECLARE t text;
BEGIN
  -- append-only: observed history, calculation records, products, versioned definitions, factors, crews
  FOREACH t IN ARRAY ARRAY['products','calculation_runs','calculation_run_lines','work_item_components','assembly_components',
                           'adjustment_factors','crews','crew_members','indices','change_log'] LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite()', t || '_append_only', t);
  END LOOP;
  -- versioned definitions: content frozen, only the derived status label may move
  FOREACH t IN ARRAY ARRAY['work_items','assemblies'] LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite(''status'')', t || '_append_only', t);
  END LOOP;
  -- TRUNCATE guard on everything protected
  FOREACH t IN ARRAY ARRAY['products','product_consumption','price_observations','calculation_runs','calculation_run_lines','labor_rates',
                           'burden_rates','equipment_rates','crews','crew_members','work_items','work_item_components','productivity_observations',
                           'assemblies','assembly_components','bid_benchmarks','index_values','adjustment_factors','assumptions','review_events','change_log'] LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON %I FOR EACH STATEMENT EXECUTE FUNCTION forbid_truncate()', t || '_no_truncate', t);
  END LOOP;
  -- review log (single-column and composite keys) and its own protection
  FOREACH t IN ARRAY ARRAY['sources','products','product_consumption','price_observations','labor_rates','burden_rates','equipment_rates',
                           'crews','productivity_observations','bid_benchmarks','indices','adjustment_factors','calculation_runs'] LOOP
    EXECUTE format('CREATE TRIGGER %I AFTER UPDATE OF review_status, reviewed_by, reviewed_at ON %I FOR EACH ROW EXECUTE FUNCTION log_review_change(%L)',
                   t || '_review_log', t, (SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey)
                                           WHERE i.indrelid = t::regclass AND i.indisprimary ORDER BY a.attnum LIMIT 1));
  END LOOP;
  CREATE TRIGGER work_items_review_log AFTER UPDATE OF review_status, reviewed_by, reviewed_at ON work_items FOR EACH ROW EXECUTE FUNCTION log_review_change('work_item_id','version');
  CREATE TRIGGER assemblies_review_log AFTER UPDATE OF review_status, reviewed_by, reviewed_at ON assemblies FOR EACH ROW EXECUTE FUNCTION log_review_change('assembly_id','version');
  CREATE TRIGGER index_values_review_log AFTER UPDATE OF review_status, reviewed_by, reviewed_at ON index_values FOR EACH ROW EXECUTE FUNCTION log_review_change('index_id','period_start','vintage_date');
  -- 'validated' needs a named reviewer and a timestamp
  FOREACH t IN ARRAY ARRAY['sources','products','product_consumption','price_observations','calculation_runs','labor_rates','burden_rates',
                           'equipment_rates','crews','work_items','productivity_observations','assemblies','bid_benchmarks','indices',
                           'index_values','adjustment_factors'] LOOP
    EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I CHECK (review_status <> ''validated'' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))',
                   t, t || '_validated_reviewer_chk');
  END LOOP;
  CREATE TRIGGER index_values_source_gate BEFORE INSERT OR UPDATE ON index_values FOR EACH ROW EXECUTE FUNCTION check_index_value_source();
  CREATE TRIGGER sources_guard BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION guard_source_change();
  -- editable reference / approval data: every change is logged with the complete old and new row
  CREATE TRIGGER sources_change_log AFTER UPDATE OR DELETE ON sources FOR EACH ROW EXECUTE FUNCTION log_row_change('source_id');
  CREATE TRIGGER regions_change_log AFTER UPDATE OR DELETE ON regions FOR EACH ROW EXECUTE FUNCTION log_row_change('region_id');
  CREATE TRIGGER categories_change_log AFTER UPDATE OR DELETE ON categories FOR EACH ROW EXECUTE FUNCTION log_row_change('category_id');
  CREATE TRIGGER trades_change_log AFTER UPDATE OR DELETE ON trades FOR EACH ROW EXECUTE FUNCTION log_row_change('trade_code');
  CREATE TRIGGER equipment_types_change_log AFTER UPDATE OR DELETE ON equipment_types FOR EACH ROW EXECUTE FUNCTION log_row_change('equipment_type_code');
  CREATE TRIGGER assumptions_change_log AFTER UPDATE OR DELETE ON assumptions FOR EACH ROW EXECUTE FUNCTION log_row_change('assumption_id');
  -- source terms / fetch status gate
  FOREACH t IN ARRAY ARRAY['products','product_consumption','price_observations','labor_rates','burden_rates','equipment_rates',
                           'productivity_observations','bid_benchmarks','indices','adjustment_factors','crews'] LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE INSERT OR UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION check_source_usable()', t || '_source_gate', t);
  END LOOP;
END $$;

CREATE TRIGGER review_events_append_only BEFORE UPDATE OR DELETE ON review_events FOR EACH ROW EXECUTE FUNCTION forbid_history_rewrite();

-- Trigger/check functions read tables by bare name: pin their search_path so they work from any session. pg_temp is listed LAST on
-- purpose: PostgreSQL searches it first unless it is named, and a session could otherwise shadow sources/review_events with a temp table.
DO $$
DECLARE f record;
BEGIN
  FOR f IN SELECT p.oid::regprocedure AS sig FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
           WHERE n.nspname = 'costdb' AND p.prokind = 'f' AND p.prolang = (SELECT oid FROM pg_language WHERE lanname = 'plpgsql') LOOP
    EXECUTE format('ALTER FUNCTION %s SET search_path = pg_catalog, costdb, pg_temp', f.sig);
  END LOOP;
END $$;

COMMIT;
