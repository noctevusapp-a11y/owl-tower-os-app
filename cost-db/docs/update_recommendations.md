# Update recommendations

Different data go stale at different speeds and need different re-checks. Cadences marked *(register)* come from what research agents found in search results (re-verify at the source); the rest are the project's recommendation.

| data type | what changes | recommended refresh | trigger for an extra refresh | owner / route |
|---|---|---|---|---|
| **Material prices** (retail, supplier quotes) | prices move weekly; promotions distort | pilot categories: **monthly** capture of each spec line; lumber/steel/copper-driven lines (framing, rebar, duct) **every 2 weeks** while volatile; always store a new observation, never overwrite | tariff/commodity news; a price outside ±3× the median (`OBS_OUTLIER`); new SKU numbering | estimator/office staff via `price_capture_template.csv`; supplier quotes via company accounts |
| **Contractor (pro/supplier) quotes** | negotiated; volume dependent | per project and at least **quarterly** for the 20 most-used lines | quote expiry; volume tier change | purchasing |
| **Statistical wages (BLS OEWS)** | one reference period (May) per year | **annually** — newest is May 2025, published 2026-05-15 *(register)*; check each spring | new release | connector `oews_flatfile.py` |
| **Prevailing wage (CA DIR)** | general determinations issued **twice a year** (Feb 22 / Aug 22) *(register)*, effective after a short lag; predetermined increases mid-period | **semiannually** plus when a notice of correction is published | DIR notices; project bid date | public-works pricing only; PDF extraction with page-image spot check |
| **Federal wage determinations (SAM.gov)** | project-specific and general; modifications | per public-works bid | modification notices | public-works pricing only |
| **Employer burden** | FICA wage base and rates each January; CA UI/ETT annually; workers' comp rates each policy period, experience mod each year | **annually in January**; workers' comp at policy renewal | insurer notice; EDD rate notice | accounting/insurance broker (company-specific values) |
| **Benefits ratio (ECEC) / company benefits** | quarterly (ECEC); company costs when plans renew | **semiannually**; at plan renewal | plan change | HR / accounting |
| **Price indices (BLS PPI, ECI)** | PPI monthly, ECI quarterly *(register)*; PPI values are revised for several months | **monthly** pull with vintage date; re-pull the previous 4 months for revisions | — | connector `bls_api.py` (needs free API key) |
| **Equipment rates** | Caltrans/USACE schedules annual or per edition *(register)*; rental rates change with market and fuel | schedules **annually**; rental quotes **quarterly** | fuel price shock; new edition | `equipment_rates` observations with operator/fuel flags |
| **Productivity norms** | rarely; printed manuals are years old | review at **every new edition**, and **annually** compare with the company's own timesheets (`company_actual`) | method change; own data deviates > 15 % from the norm | estimator; keep edition and page |
| **Manufacturer coverage/yield** | changes with formulation | **annually**, and when a SKU changes or a data sheet revision appears | new product line; VOC regulation change | `product_consumption` |
| **Bid benchmarks** | per lettings | **quarterly** | large new contract | `bid_benchmarks` (never a cost input) |
| **Region/trade/classification codes** | CBSA delineations and SOC revisions are rare | **annually** check; on SOC/NAICS revision | OMB bulletin | `regions`, `trades` |
| **Source terms and reachability** | websites change terms and block automation | **annual** review; before any new bulk capture | site redesign; blocked access | person reads Terms of Use + robots.txt; update `sources.reuse_status` |
| **Waste factors, crews, assumptions** | company practice | **annually** and after each completed project (actual vs estimate) | variance > 10 % on a project | project manager; approve in `assumptions` |
| **Work-item and assembly definitions** | scope, specification, quantities change with practice and code | review **before first use** (strict runs refuse unreviewed definitions) and **annually**; new content = new version (definitions are frozen in the database) | spec or code change; a project variance traced to a definition | estimator who did not write it; record in `review_events` |


**Process rules for every refresh:** (1) capture into new rows; (2) record `observed_at`, `retrieved_at`, effective period, source locator and evidence; (3) run `pipeline/scripts/build.py`; (4) review `validation_issues` and the coverage matrix; (5) only then promote — and only records whose source was actually fetched can be promoted.
