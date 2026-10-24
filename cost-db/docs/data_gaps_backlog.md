# Data-gap backlog

Generated at build time from open `capture_targets`, the missing inputs reported by the strict calculation runs, and the gaps listed by the research agents. Priority 1 = blocks a pilot unit cost.

## A. Blockers that are not data tasks (do these first)

| # | action | why |
|---|---|---|
| A1 | **Open outbound network access** for the build environment to the hosts in `docs/network_allowlist.md` (or run the connectors on a machine with normal internet access). | Every primary source host was refused by the sandbox network policy on 2026-10-24; no primary document could be fetched, so nothing can be `validated`. |
| A2 | Register a free **BLS API v2 key** (store as `BLS_API_KEY`; do not commit). | Index series and OEWS time series need the v2 limits (500 queries/day). Terms: cite source and access date. |
| A3 | A person reads the **live Terms of Use / robots.txt** of Home Depot, Lowe's, Grainger, Ferguson, Sherwin-Williams and Dunn-Edwards before any price capture; record the outcome in `sources.reuse_status`. | Retailer terms were only seen as search snippets. Sources registered as `prohibited` (Lowe's, Ferguson snippets) are **refused by the importer whatever the capture method** until their live terms are read and the status is corrected; `restricted_no_automated_access` sources (Home Depot, Grainger, Sherwin-Williams) accept manual capture only. No scraping is implemented. |
| A4 | Decide who captures retail prices **by hand** (office staff with a browser) and use `templates/price_capture_template.csv`. | The only compliant route for retailers without a licensed feed. |
| A5 | Confirm whether the company will obtain **contractor (pro-account / supplier) quotes**; they are a separate price channel and the only valid contractor-cost evidence. | Retail prices must never be presented as contractor purchase cost. |
| A7 | Name a **reviewer for the 25 work-item and 10 assembly definitions** (scope, specification, quantities, exclusions) and record the review. | Strict runs refuse unreviewed definitions (`DEFINITION_NOT_REVIEWED`); the definitions were written by the system and have not been checked by a person. |
| A6 | Provide company-specific burden inputs: **workers' comp rate by class, experience mod, UI rate notice, benefit costs**, and (optionally) actual payroll rates by trade. | These are company-specific and cannot be found in public sources. |

## B. Open capture targets

| kind | priority 1 | priority 2 | priority 3 |
|---|---|---|---|
| material | 44 | 85 | 0 |
| labor | 11 | 0 | 11 |
| burden | 4 | 0 | 0 |
| equipment | 0 | 3 | 0 |
| productivity | 25 | 0 | 0 |
| index | 0 | 2 | 0 |
| other | 6 | 0 | 0 |

The full list with required attributes, recommended sources and the work items that need each line is `data/csv/capture_targets.csv`. Priority-1 material lines (needed by a pilot work item):

| target | category | description | needed by |
|---|---|---|---|
| `TGT-4f5c1d4a364c` | CAT-CON-ACC | Concrete curing compound, 5 gal pail | WI-CON-005 |
| `TGT-655102d19aca` | CAT-CON-ACC | J anchor bolt 1/2 in x 10 in with nut and washer | WI-CON-004 |
| `TGT-ee81be4fe0bc` | CAT-CON-ACC | Under-slab vapor retarder 10 mil, roll | WI-CON-001, WI-CON-002 |
| `TGT-105e40e0b8e7` | CAT-CON-RMX | Ready-mix concrete 4000 psi, 3/4 in agg, 4 in slump, Type II | WI-CON-001, WI-CON-002, WI-CON-003 |
| `TGT-4ca6cc4b6b90` | CAT-DRY-BRD | Gypsum board 1/2 in x 4x8, regular core, tapered edge | WI-DRY-001, WI-DRY-004 |
| `TGT-2635e2f22a7b` | CAT-DRY-BRD | Gypsum board 5/8 in x 4x12, Type X, tapered edge | WI-DRY-003 |
| `TGT-663e340e01fa` | CAT-DRY-BRD | Gypsum board 5/8 in x 4x8, Type X, tapered edge | WI-DRY-002 |
| `TGT-a3505dde6938` | CAT-DRY-BRD | Moisture-/mold-resistant gypsum board 1/2 in x 4x8 | WI-DRY-006 |
| `TGT-39a316a35700` | CAT-DRY-JNT | All-purpose pre-mixed joint compound, 4.5 gal, standard weight | WI-DRY-005 |
| `TGT-38410aaa3499` | CAT-DRY-TAP | Paper joint tape 2-1/16 in x 500 ft | WI-DRY-005 |
| `TGT-6afc9cdfa68d` | CAT-FRM-CON | Face-mount joist hanger for 2x10, 18 ga, G90 | WI-FRM-003 |
| `TGT-f99ac6a783c2` | CAT-FRM-FAS | 16d sinker nail 3-1/4 in x 0.148 in | WI-FRM-001, WI-FRM-002, WI-FRM-003, WI-FRM-006 |
| `TGT-e28cc147c0a3` | CAT-FRM-FAS | 8d common nail 2-1/2 in x 0.131 in | WI-FRM-004 |
| `TGT-7db82d16e102` | CAT-FRM-FAS | Drywall screw #6 x 1-1/4 in, coarse thread (wood) | WI-DRY-001, WI-DRY-004, WI-DRY-006 |
| `TGT-2788451b64a6` | CAT-FRM-FAS | Drywall screw #6 x 1-1/4 in, fine thread (steel) | WI-DRY-003 |
| `TGT-5bd9b54db14b` | CAT-FRM-FAS | Drywall screw #6 x 1-5/8 in, coarse thread (wood) | WI-DRY-002 |
| `TGT-c323b11f55fb` | CAT-FRM-FAS | Self-drilling pan-head screw #8 x 1/2 in (steel framing) | WI-FRM-005 |
| `TGT-0d9e3a651164` | CAT-FRM-LBR | 2x10x12 ft DF-L #2 and better, kiln-dried | WI-FRM-003 |
| `TGT-6b2fcbbb82ff` | CAT-FRM-LBR | 2x4 precut stud 92-5/8 in, DF-L, stud grade, kiln-dried | WI-FRM-001 |
| `TGT-00370a17ce1d` | CAT-FRM-LBR | 2x4x8 ft DF-L #2 and better, kiln-dried | WI-FRM-001, WI-FRM-006 |
| `TGT-afead3566766` | CAT-FRM-LBR | 2x6 precut stud 92-5/8 in, DF-L, stud grade, kiln-dried | WI-FRM-002 |
| `TGT-0cd345afeb14` | CAT-FRM-LBR | 2x6x8 ft DF-L #2 and better, kiln-dried | WI-FRM-002 |
| `TGT-d8dc0c5d4620` | CAT-FRM-LGS | Steel stud 3-5/8 in x 1-5/8 in, 18 mil (25 ga), 10 ft, nonstructural | WI-FRM-005 |
| `TGT-c340df14b641` | CAT-FRM-LGS | Steel track 3-5/8 in x 1-1/4 in, 18 mil (25 ga), 10 ft, nonstructural | WI-FRM-005 |
| `TGT-6ce1e9aecc4d` | CAT-FRM-SHT | Plywood sheathing 15/32 in 4x8, Exposure 1, CD, span rating 32/16 | WI-FRM-004 |
| `TGT-86e62f9f6c20` | CAT-HVC-ACC | Condenser pad 36x36x3 in, composite | WI-HVC-001 |
| `TGT-ffcb5fa76f33` | CAT-HVC-CTL | AC disconnect 60 A, 240 V, non-fused pull-out | WI-HVC-001 |
| `TGT-5abf0cc43cda` | CAT-HVC-CTL | AC whip 60 A, 6 ft flexible conduit | WI-HVC-001 |
| `TGT-e477e9ae79d9` | CAT-HVC-CTL | Programmable thermostat 24 V, 1H/1C | WI-HVC-002 |
| `TGT-6a2ddce68198` | CAT-HVC-DUC | Insulated flexible duct 8 in, R-6, 25 ft | WI-HVC-003 |
| `TGT-ad332e71457c` | CAT-HVC-EQP | AC condenser 3 ton, 14.3 SEER2, R-454B | WI-HVC-001 |
| `TGT-8ed6c4019092` | CAT-HVC-EQP | Cased evaporator coil 3 ton, R-454B | WI-HVC-002 |
| `TGT-6c66e5825bf1` | CAT-HVC-EQP | Gas furnace 80,000 Btu/h input, 80% AFUE, upflow | WI-HVC-002 |
| `TGT-09a8f134e17b` | CAT-HVC-REF | Copper line set 3/8 x 7/8 in, 25 ft, insulated | WI-HVC-001 |
| `TGT-bc4f44a7d23d` | CAT-INS-BAT | Fiberglass batt R-13, 3-1/2 in, 15 in wide, kraft-faced (2x4) | WI-INS-001 |
| `TGT-535779a26c69` | CAT-PNT-PNT | Interior acrylic latex wall paint, eggshell, 5 gal | WI-PNT-002 |
| `TGT-c0288adb6a7b` | CAT-PNT-PNT | Interior ceiling paint, flat, 5 gal | WI-PNT-003 |
| `TGT-8a15322181ad` | CAT-PNT-PRM | PVA drywall primer, 5 gal | WI-PNT-001 |
| `TGT-391785a94ecb` | CAT-PNT-SUP | Paintable siliconized acrylic latex caulk, 10.1 fl oz | WI-PNT-004 |
| `TGT-b560789b1cc9` | CAT-REB-ACC | Bar support chair 3 in height, plastic | WI-CON-002 |
| `TGT-da8d06894974` | CAT-REB-ACC | Bar/mesh support chair 2 in height, plastic | WI-CON-001 |
| `TGT-dc4559501487` | CAT-REB-ACC | Rebar tie wire, 16 gauge annealed, coil | WI-CON-002 |
| `TGT-f28b1cdfad95` | CAT-REB-BAR | Rebar #4 Grade 60, 20 ft | WI-CON-002, WI-CON-003 |
| `TGT-773b50a29f87` | CAT-REB-BAR | Welded wire reinforcement 6x6-W1.4xW1.4, 5x10 ft sheet | WI-CON-001 |

## C. Missing inputs reported by strict calculation runs

Aggregated over all 25 work-item runs (LA County, as of the build date). Every run is `incomplete` and carries no total.

| code | occurrences | distinct inputs | how to fill |
|---|---|---|---|
| WASTE_MISSING | 55 | 48 | Source a waste/loss factor for the line with a stated basis, or add an approved assumption. |
| PRICE_MISSING | 55 | 44 | Capture ≥1 real SKU matching the spec line (templates/price_capture_template.csv) in the target region. |
| CREW_MISSING | 29 | 11 | Extract a crew composition (trades, quantities, shift) from a documented norm source. |
| PRODUCTIVITY_MISSING | 29 | 25 | Extract a labor norm (document, edition, page, crew, daily output, conditions). |
| DEFINITION_NOT_REVIEWED | 25 | 25 | A person other than the author checks the work item's scope, specification and quantities and records the review (review_events); until then strict runs cannot complete. |
| CONSUMPTION_MISSING | 5 | 5 | Extract manufacturer coverage with film thickness, coats and conditions; bind to a SKU. |
| QUANTITY_MISSING | 2 | 2 | Derive the quantity from geometry or manufacturer data. |

## D. Gaps reported by the research agents (search-summary level)

### Agent A1

- No official OEWS detailed-occupation wage for any construction trade in the Los Angeles-Long Beach-Glendale metropolitan division (or Riverside-San Bernardino-Ontario, Phoenix, Las Vegas) was retrievable: the search tool never returned the XLSX/table content. Needed: fetch the May 2025 MSA/MD XLSX from bls.gov (blocked in this sandbox) and read the actual rows for SOC 47-2031 etc.
- Exact May 2025 OEWS data-file names and URLs (national/state/metro ZIP or XLSX), the column header list and the CBSA codes for the four metros: not confirmed; prior-knowledge guesses are flagged. Need the bls.gov/oes/tables.htm page or a directory listing.
- Whether the May 2025 OEWS tables publish the Los Angeles-Long Beach-Glendale metropolitan division separately from the MSA: not confirmed.
- Official BLS statement of the exact OEWS benefit-exclusion wording and the OEWS FAQ page text were not read; only the search-tool summary of the technical notes was seen.
- Full OEWS series-ID layout and datatype codes: only field-width fragments seen; need oe.txt and oe.datatype. No OEWS series ID is reported.
- ECEC: no construction-industry series ID seen; BLS's own construction table values (as opposed to EPI's reproduction) not seen; latest ECEC quarter as of Oct 2026 unknown (Dec 2025 was the one seen); regional (West) ECEC availability not established.
- ECI regional/metro cuts (West region, Los Angeles) and a trade-specific cut were not searched beyond the national construction series.
- PPI: gypsum (WPU137 vs other), asphalt roofing, paint, copper wire/pipe and 'inputs to construction industries' IDs came only via search-tool summaries of AGC tables; the BLS PPI series lookup should be used to validate each ID, title and base period. WPUID611 not confirmed.
- FRED numeric rate limits and the exact FRED legal statement about BLS data were not seen; legal review needed before any storage of FRED-sourced data.
- California DIR: current 2026-2 (and 2026-1) Southern California determination rate tables were not retrieved for any craft; effective dates, predetermined increases and the exact 2026 carpenter, laborer, electrician, plumber, painter, drywall, operating engineer rates are unknown. The meaning of the numeric components of the determination number (e.g. 23-31-2) is not documented in snippets. DIR terms of use for republication were not found. No API/bulk download found; need to confirm by reading the DIR PWD index page and the OPRL pages.
- Whether DIR travel-and-subsistence (zones/per diem) is published as numbers anywhere in the determinations or in separate zone pages was not established.
- SAM.gov: no official API documentation for wage determinations found (open.gsa.gov / api.sam.gov); current Los Angeles County DBA general decision numbers, revisions and the Arizona and Nevada county decisions were not retrieved; the Los Angeles court-hosted copy has an inconsistent identifier (CA20200022 in title vs CA20240022 in summary).
- Arizona: no official statute text or state agency page confirming whether a state prevailing-wage regime exists; conflicting contractor claims about A.R.S. 34-321.
- Nevada: the October 1, 2026 successor determinations (Clark County and other regions) and the labor.nv.gov landing page were not seen; the Northern Nevada and other region names/URL patterns beyond those listed are not confirmed.
- EDD OEWS: Excel file URLs and column layout not seen; current vintage (page may have moved beyond the aged-to-Q1-2025 version); no terms of use found; other EDD labor-market series (e.g. Employment Projections) not searched.
- FUTA from IRS primary source (Form 940 instructions) and California's FUTA credit-reduction status for 2026 not checked; EDD's own statement of new-employer UI rate not found; EDD explicit statement that SDI is employee-paid not read (inferred from 'withholding rate' wording).
- WCIRB: California class-code descriptions for drywall, painting, concrete, HVAC, roofing, glazing, sheet metal, insulation and rebar were not confirmed from WCIRB pages; class-level advisory pure premium rates for 9/1/2026 were not seen; WCIRB free-vs-paid access boundaries (e.g. rating data, experience rating worksheet) not established.
- Nothing was searched for Arizona/Nevada employer-burden items (state UI/workers comp: Nevada and Arizona SUI rates, NCCI states) or for local/other benefit contribution rates (union trust fund rates, apprenticeship) outside the DIR determinations.

### Agent A2

- Caltrans EQRR: actual rate values, current labor surcharge percentage, definitive effective dates of book_26_27_intv2 vs book_26_27 vs book_26v3, whether rates vary by district/region, and whether the operator is excluded - requires opening the PDF/CSV (dot.ca.gov is blocked from this sandbox; a different environment or a human download is needed). The CSV URL was not seen.
- Caltrans Contract Cost Data: official conditions-of-use text (sv08data help/terms) and any sanctioned bulk export or data request process; whether the Office of Engineer still publishes an annual Cost Data book. Needs reading the live conditions page or a written request to Caltrans.
- Caltrans global 'Conditions of Use' (dot.ca.gov footer link) text and any statement covering datasets and rate books.
- Caltrans Standard Specifications 2024 Section 9-1.04 (force-account equipment, labor surcharge and markup) and Construction Manual text not retrieved; markups were seen only in training slides.
- USACE EP 1110-1-8: which regional volume covers California, Arizona and Nevada (must be read from the pamphlet's region map in the front matter, e.g., EP 1110-1-8_RV1-12.pdf), the latest edition year (2021 or later vs Nov 2016), operator inclusion/exclusion, fuel price basis, regional adjustment factors, and reuse terms (no distribution/copyright statement seen).
- NAVFAC P-405: actual table contents (trades, units, crew compositions, daily outputs), the NAVFAC-hosted original, and the distribution statement. Needs download and read.
- Joint TM 3-34.41 / NTRP 4-04.2.3 / MCRP 3-40D.12 (2021): whether it includes labor-hour or crew-production tables by trade - needs reading the PDF.
- No free, current, trade-level labor-hour or crew-output source (framing, drywall, painting, concrete placing/finishing, rebar, demolition, HVAC, electrical rough-in, plumbing) was confirmed; likely requires licensed commercial data, contractor-supplied history, or Owl Tower's own job-cost records.
- ADOT and NDOT equipment rental rate schedules or force-account rates were not found; ADOT/NDOT standard specifications (force-account sections, Blue Book adoption) need a direct check. ADOT and NDOT average-unit-price reports not found (only bid tabs/E2C2).
- City of Los Angeles BOE, LA Metro, LAUSD and Riverside County: no current bid-result pages or datasets located; LA County Public Works bid-results index/landing page and archive depth also not located.
- Open-data portals (data.lacity.org, LA County, San Diego, Riverside) were not found to host construction bid line-item datasets; a targeted portal search would be needed.
- Rental companies: actual website-use / automated-access clauses for Sunbelt, United Rentals (Section 3) and Home Depot, and whether any publish usable public rate sheets; needs reading the live terms and robots.txt (no scraping done).
- Open installed-cost datasets: no insulation dataset, no LBNL installed-cost dataset for HVAC found; TECH Clean California data license, period, format, geographic granularity unknown; NYSERDA and Consumer Reports/Rewiring America datasets' license/availability unconfirmed.
- IEEE DataPort SlabCalc 26-metro record license not shown; whether the 26 metros include Los Angeles not shown.

### Agent A3

- Live clause text for homedepot.com Terms of Use, Grainger Terms of Access, Ferguson terms landing page, Dunn-Edwards terms, and the full Sherwin-Williams terms could not be read (network blocked; search returns only summaries). A human must open the live pages and record verbatim clauses, effective dates and any robots.txt (Grainger, Ferguson, Sherwin-Williams, Dunn-Edwards robots.txt were not found).
- Home Depot and Lowe's affiliate programs: actual feed terms, field list (does it include price, store-level availability, SKU/model), permitted uses, and whether an internal cost database is a permitted use are unknown; network for Lowe's conflicts (Impact vs Rakuten). Needs a human to read the live affiliate directory entry; no account is to be opened by the project.
- Grainger official API/developer portal: documentation, fees and account prerequisites not found; Punch-Out and ERP integration require an existing Grainger account and rep contact. No Home Depot API/catalog-feed documentation found beyond punch-out via procurement platforms. Ferguson and Dunn-Edwards official data routes not searched.
- No standalone SKU price book found from cooperative purchasing (Sourcewell contracts are discount schedules). OMNIA Partners, BuyBoard, TIPS and state contracts for Arizona (State Procurement Office) and Nevada were not searched. Sourcewell 091422-WWG expiry (2026-11-08 vs 2027-11-08) must be confirmed.
- GSA: no building-materials/HVAC/paint schedule price list identified; GSA open-data portal, catalog.gsa.gov help pages and any bulk export and reuse terms not verified. California DGS: only recycled exterior paint found; Cal eProcure pricing access and reuse terms unverified; no HVAC or general materials statewide contract found.
- BLS/FRED: BLS copyright/reuse page and FRED terms not seen; BLS API data endpoint URL not seen; series IDs for softwood lumber, gypsum products, steel mill products, copper/PVC pipe and related PPIs were not retrieved (only ready-mix concrete FRED IDs and PCUBCON/PCUBHWY). No regional (Los Angeles) material price dataset with open terms found.
- Classification: CSI full EULA text (MasterFormat, UniFormat, OmniClass) and current post-2026 platform terms not retrieved; UNSPSC commercial-use answer not retrieved; HS/Schedule B, SOC and CPV license terms were not searched (prior knowledge, unverified: HS codes are WCO-licensed but Census Schedule B and USITC HTS are US government publications; CPV is an EU Publications Office vocabulary). NAICS public-domain status not explicitly stated.
- Manufacturer documentation not searched or not found: CertainTeed and Georgia-Pacific gypsum, standard 1/2 in. and 5/8 in. Type X weights/fire ratings, joint compound product data sheets (finish levels), screws/fasteners (box counts, per-sq-ft usage), Behr/Kelly-Moore/Sherwin-Williams product data sheets (spread rate, DFT, VOC), Sakrete yield, ready-mix specs (ACI 318/ASTM C94 are paid standards), CRSI rebar tables, SMACNA free duct references, HVAC manufacturer submittals (Carrier, Trane, Goodman/Daikin, Lennox), Owens Corning/CertainTeed insulation charts, and non-fiberglass insulation R-values.
- Dunn-Edwards EVERSHIELD/VINYLASTIC/SPARTASHIELD spread rates and the conformance table contents were not visible in snippets.
- Document-level reuse/copyright terms for all manufacturer PDFs (USG, National Gypsum, QUIKRETE, Dunn-Edwards, Johns Manville) are unknown; plan is to record cited factual specs only, not republish documents.
- AHRI Directory public terms of use text not seen; commercial subscription cost not stated.
