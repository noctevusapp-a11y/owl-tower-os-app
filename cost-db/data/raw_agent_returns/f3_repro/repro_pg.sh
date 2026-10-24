#!/bin/bash
# Usage: PGHOST=... PGPORT=... PGUSER=... bash repro_pg.sh   (needs a scratch server; creates database f3_repro)
R=/home/user/owl-tower-os-app/cost-db
psql -q -d postgres -c "DROP DATABASE IF EXISTS f3_repro" -c "CREATE DATABASE f3_repro" 2>&1 | grep -v NOTICE
psql -q -v ON_ERROR_STOP=1 -d f3_repro -f $R/schema/001_schema.sql -f $R/schema/003_comments.sql
PYTHONPATH=$R/pipeline python3 -B -c "
from pathlib import Path
from costdb import pg
print(pg.copy_script(Path('$R/data/csv')))" | psql -q -v ON_ERROR_STOP=1 -d f3_repro
psql -d f3_repro <<'SQL'
\set ON_ERROR_STOP off
\echo '=== setup: one product (from a real capture target) and sources'
insert into costdb.sources (source_id,title,owner,source_kind,verification_method,reuse_status) values
 ('SRC-XSNIP','t','o','other','search_snippet_only','open_license'),
 ('SRC-XFETCH','t','o','other','fetched_primary','open_license'),
 ('SRC-XPROH','t','o','other','search_snippet_only','prohibited');
insert into costdb.products (product_id,category_id,name,spec_attributes,spec_key,sale_unit_label,content_qty,content_unit_id,source_id)
 select 'PRD-X1', category_id, 'x', spec_attributes, spec_key, 'sheet', 32, 'SF', 'SRC-XSNIP' from costdb.capture_targets
 where spec_key like 'CAT-DRY-BRD%' limit 1;
\echo '=== F3-01 pg_temp shadow table defeats the validated-needs-fetch gate and the review log'
\echo '--- control (rejected):'
insert into costdb.price_observations (observation_id,product_id,source_id,zip,region_id,observed_at,retrieved_at,price_amount,price_channel,sold_as_label,pack_content_qty,pack_content_unit_id,evidence_excerpt,capture_method,captured_by,review_status,reviewed_by,reviewed_at)
 values ('OBS-C1','PRD-X1','SRC-XSNIP','90245','REG-CA-037','2026-10-01','2026-10-01T12:00:00Z',12.8,'retail_public','sheet',32,'SF','12.80','manual_browser','me','validated','rev',now());
\echo '--- attack (accepted):'
create temp table sources (source_id text, reuse_status text, verification_method text);
insert into sources values ('SRC-XSNIP','open_license','fetched_primary'), ('SRC-XPROH','open_license','fetched_primary');
insert into costdb.price_observations (observation_id,product_id,source_id,zip,region_id,observed_at,retrieved_at,price_amount,price_channel,sold_as_label,pack_content_qty,pack_content_unit_id,evidence_excerpt,capture_method,captured_by,review_status,reviewed_by,reviewed_at)
 values ('OBS-A1','PRD-X1','SRC-XSNIP','90245','REG-CA-037','2026-10-01','2026-10-01T12:00:00Z',12.8,'retail_public','sheet',32,'SF','12.80','manual_browser','me','validated','rev',now());
insert into costdb.price_observations (observation_id,product_id,source_id,zip,region_id,observed_at,retrieved_at,price_amount,price_channel,sold_as_label,pack_content_qty,pack_content_unit_id,evidence_excerpt,capture_method,captured_by)
 values ('OBS-A2','PRD-X1','SRC-XPROH','90245','REG-CA-037','2026-10-01','2026-10-01T12:00:00Z',12.8,'retail_public','sheet',32,'SF','12.80','manual_browser','me');
select o.observation_id, o.review_status, s.reuse_status, s.verification_method from costdb.price_observations o join costdb.sources s using (source_id) where observation_id in ('OBS-A1','OBS-A2');
drop table pg_temp.sources;
create temp table review_events (event_id serial, record_table text, record_id text, old_status text, new_status text, changed_by text, changed_at timestamptz, db_user text);
update costdb.price_observations set review_status='flagged' where observation_id='OBS-A1';
select count(*) as events_in_real_log_for_OBS_A1 from costdb.review_events where record_id='OBS-A1';
\echo '=== F3-03 sources / indices are mutable and unlogged: one UPDATE opens the gate'
update costdb.sources set verification_method='fetched_primary' where source_id='SRC-XSNIP';
insert into costdb.price_observations (observation_id,product_id,source_id,zip,region_id,observed_at,retrieved_at,price_amount,price_channel,sold_as_label,pack_content_qty,pack_content_unit_id,evidence_excerpt,capture_method,captured_by,review_status,reviewed_by,reviewed_at)
 values ('OBS-A3','PRD-X1','SRC-XSNIP','90245','REG-CA-037','2026-10-02','2026-10-02T12:00:00Z',12.8,'retail_public','sheet',32,'SF','12.80','manual_browser','me','validated','rev',now());
update costdb.sources set verification_method='search_snippet_only' where source_id='SRC-XSNIP';
select o.observation_id, o.review_status, s.verification_method as source_now from costdb.price_observations o join costdb.sources s using (source_id) where observation_id='OBS-A3';
update costdb.sources set reuse_status='open_license' where source_id='SRC-XPROH';   -- a prohibited source silently becomes usable
insert into costdb.price_observations (observation_id,product_id,source_id,zip,region_id,observed_at,retrieved_at,price_amount,price_channel,sold_as_label,pack_content_qty,pack_content_unit_id,evidence_excerpt,capture_method,captured_by) values ('OBS-A5','PRD-X1','SRC-XPROH','90245','REG-CA-037','2026-10-03','2026-10-03T12:00:00Z',12.8,'retail_public','sheet',32,'SF','12.80','manual_browser','me');
update costdb.sources set reuse_status='prohibited' where source_id='SRC-XPROH';   -- flipped back: the stored value now sits under a prohibited source
select o.observation_id, s.reuse_status as source_now from costdb.price_observations o join costdb.sources s using (source_id) where observation_id='OBS-A5';
\echo '=== F3-02 crews are outside the source gate: validated from a never-fetched, prohibited source'
insert into costdb.crews (crew_id,name,shift_hours,source_id,source_locator,origin,review_status,reviewed_by,reviewed_at) values ('CRW-X1','x',8,'SRC-XSNIP','p.1','observed','validated','me',now());
select crew_id, review_status from costdb.crews where crew_id='CRW-X1';
\echo '=== F3-22 reference tables and assumption approval fields are unprotected / unlogged'
update costdb.categories set required_product_attributes='["x"]' where category_id='CAT-DRY-BRD';
update costdb.indices set applies_to='all';
update costdb.regions set parent_region_id=null where region_id='REG-CA-037';
\echo '=== F3-23 DB-vs-Python numeric scale: price 12.98765 stored as'
insert into costdb.price_observations (observation_id,product_id,source_id,zip,region_id,observed_at,retrieved_at,price_amount,price_channel,sold_as_label,pack_content_qty,pack_content_unit_id,evidence_excerpt,capture_method,captured_by) values ('OBS-A4','PRD-X1','SRC-XFETCH','90245','REG-CA-037','2026-10-02','2026-10-02T12:00:00Z',12.98765,'retail_public','sheet',32,'SF','12.98765','manual_browser','me') returning price_amount;
SQL
