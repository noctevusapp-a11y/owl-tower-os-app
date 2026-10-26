# Network access needed to collect real data

**Situation (tested 2026-10-24):** the cloud environment this pilot was built in refused every connection to the 79 hosts named in the source register (`data/raw_agent_returns/host_reachability_2026-10-24.tsv`); the proxy status endpoint recorded the refusals as `connect_rejected` (policy denial). Only package registries and GitHub's API were reachable. Therefore **no primary document could be downloaded**, every source record is search-summary level and nothing is `validated`.

**How to fix (pick one):**
1. In the environment's *Network access* settings choose a broader access level, or add the hosts below under *Allowed domains* (steps: <https://code.claude.com/docs/en/cloud-environments#network-access>); or
2. run the connectors on a machine with normal internet access (the office PC): `pip install requests openpyxl pdfplumber pypdfium2 pillow` then see `pipeline/connectors/README.md`.

Tiers are in order of value for the pilot. Tier 1 alone unlocks labor wages, employer burden and index series — the parts of a cost that *can* be sourced from open government data.

## Tier 1 — labor, burden, indices (unblocks 11 trades × LA + payroll items)

| host | why | register ids |
|---|---|---|
| `download.bls.gov`, `www.bls.gov`, `api.bls.gov` | OEWS wage files (May 2025 is the newest), OEWS/PPI/ECI/ECEC series via API v2 (free key) | SRC-BLS-OEWS-MAY2025, SRC-BLS-OE-FLATFILES, SRC-BLS-API-V2, SRC-BLS-PPI, SRC-BLS-ECEC, SRC-BLS-ECI |
| `edd.ca.gov`, `labormarketinfo.edd.ca.gov`, `data.edd.ca.gov` | California payroll tax rates (UI, ETT); county/metro OEWS wages | SRC-EDD-PAYROLL-RATES-2026, SRC-EDD-OEWS-LMI |
| `www.irs.gov`, `www.eitc.irs.gov` | Publication 15 (FICA, FUTA) | SRC-IRS-PUB15-2026 |
| `www.dir.ca.gov`, `dir.ca.gov` | prevailing wage determinations (PDF, issued Feb 22 / Aug 22) — **public-works context only** | SRC-DIR-PWD-GENERAL-2026-2, SRC-DIR-PWD-FAQ-RULES |
| `sam.gov`, `www.dol.gov` | Davis-Bacon wage determinations — public-works context only | SRC-SAM-DBA-WAGE-DETS, SRC-DOL-DBA-FACTSHEET-66D |
| `www.wcirb.com`, `www.insurance.ca.gov` | workers' comp classifications and advisory pure premiums (advisory only; your premium comes from your insurer) | SRC-WCIRB-CLASS-USRP, SRC-CDI-WC-ADVISORY-2026-09 |
| `labor.nv.gov`, `www.azag.gov` | Nevada prevailing wage regions; Arizona context | SRC-NVLC-PWD-2025-26, SRC-AZAG-OPINION-I23-004 |

## Tier 2 — equipment, productivity, bid benchmarks

| host | why |
|---|---|
| `dot.ca.gov` (and `ppmoe.dot.ca.gov`, `sv08data.dot.ca.gov`, `ctps.dot.ca.gov`) | Caltrans Labor Surcharge and Equipment Rental Rates; Contract Cost Data; terms of use |
| `www.publications.usace.army.mil`, `www.nww.usace.army.mil` | USACE EP 1110-1-8 equipment ownership & operating expense schedule (free PDFs) |
| `apps.dtic.mil`, `www.marines.mil`, `www.wbdg.org`, `everyspec.com` | NAVFAC P-405 / TM 3-34.41 / older government production handbooks — check the document for labor-hour tables before relying on it |
| `www.fhwa.dot.gov`, `library.ctr.utexas.edu`, `www.txdot.gov`, `www.oregon.gov` | production-rate guidance; DOT average bid unit prices (benchmarks only) |
| `azdot.gov`, `apps.azdot.gov`, `cnsads.azdot.gov`, `www.dot.nv.gov`, `appss.nevadadot.com` | ADOT / NDOT bid tabulations |
| `dpw.lacounty.gov`, `torranceca.gov`, `cityofgardena.org`, `res.sbcounty.gov`, `pfm.sbcounty.gov`, `fpcprojects.sandi.net` | Southern California bid tabulations (benchmarks, not cost) |

## Tier 3 — manufacturer documentation (coverage, yield, packaging, specs)

`jm.com`, `www.dunnedwards.com`, `www.quikrete.com`, `assemblies-tools.usg.com`, `www.wwpa.org`, `www.nist.gov`, `sweets.construction.com`, `www.ahrinet.org` (AHRI directory: free CSV export limited to 250 records).

## Tier 4 — retailers and distributors: **terms review first, no automated access**

`www.homedepot.com`, `www.lowes.com`, `www.grainger.com`, `www.ferguson.com`, `www.sherwin-williams.com`, `www.sunbeltrentals.com`, `www.unitedrentals.com`.
Allowing the hosts does **not** make scraping acceptable: snippet-level evidence says Lowe's, Ferguson and Sherwin-Williams prohibit robots/scraping, and Home Depot/Grainger terms were not found. Use **manual capture** (`templates/price_capture_template.csv`) or an account-based/licensed feed the company itself opens. A person must read each site's current Terms of Use and robots.txt and record the result in `sources.reuse_status`.

## Do not whitelist for data (reasons)

`fred.stlouisfed.org` (terms bar storing FRED content — use bls.gov directly; series IDs only), `ieee-dataport.org`, `omnicost.com`, `www.epi.org`, `geniuslink.com`, `uppromote.com`, `scws-warrior-training.yolasite.com` (secondary or unrelated hosts that appeared in search results).
