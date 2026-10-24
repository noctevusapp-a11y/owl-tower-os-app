# Connectors

Run these on a machine that can reach the source hosts (see `docs/network_allowlist.md`). Every connector writes **new rows with `review_status = unreviewed`**; nothing is promoted automatically unless the source was really fetched (`costdb.validate.promote_validated`).

| connector | purpose | state | how it was tested |
|---|---|---|---|
| `retail_capture_import.py` | validate and normalise **manually captured** retail/supplier prices (`templates/price_capture_template.csv`) into `products` + `price_observations` | implemented | 11 unit tests on synthetic rows: unit qualification, spec completeness, evidence-supports-price, prohibited-source rules, dedupe, append-only |
| `bls_api.py` | BLS Public Data API v2 client (limits, batching, raw-JSON hashing) and parser to `index_values` | implemented, **never run against the live API** | parser tested on a *format fixture* with invented values; request layout follows BLS documentation as recalled — the first live run must be reviewed by a person |
| `oews_flatfile.py` | parse a BLS OEWS table (CSV/XLSX) into `labor_rates` (`stat_wage`, mean/median, benefits excluded) | implemented, **never run on a real OEWS file** | tested on a synthetic CSV: suppressed (`*`) and top-coded (`#`) wages are not stored; missing columns fail loudly rather than guess a layout |
| `pdf_tables.py` | extract tables + trailing notes from text-layer PDFs (DIR determinations, DOT/Army manuals); render sampled cells as highlighted page images; warn when the text layer jumps right-to-left | implemented | tested on a generated PDF; **real manuals have not been processed** |
| DIR prevailing-wage PDFs → `labor_rates` (`prevailing_wage`, fringe breakdown) | needs `pdf_tables.py` + a per-document column map | **not implemented** — table layout unseen | — |
| SAM.gov / DOL wage determinations | no documented API was found (agent A1); documents are text/PDF | **not implemented** | — |
| Caltrans equipment rates / contract cost data, USACE EP 1110-1-8 | rate-book PDFs or CSV (a CSV is said to exist, URL not seen) | **not implemented** — formats unseen | — |
| Retailer/distributor scraping | — | **deliberately not implemented**: terms prohibit or are unverified; no CAPTCHA/login/paywall bypass, no accounts on the company's behalf | — |

## Typical run (real data, once network access exists)

```bash
export BLS_API_KEY=...            # free key, never commit
python3 - <<'PY'
# 1. fetch OEWS file by hand/browser or with your own downloader; then:
# 2. parse -> labor_rates rows (statistical wages), append, rebuild
PY
python3 -I pipeline/scripts/build.py
```

After a source is genuinely fetched, record it: set `sources.verification_method = 'fetched_primary'`, `reachability_from_build_env = 'reachable'`, and store the file's SHA-256 in each record's `raw_file_sha256`. Only then can the promotion gate validate records from it.
