# Price-update factors, 2022-01 → latest published (2026--09)

Generated 2026-10-24 06:28Z by `pipeline/scripts/price_update_factors.py` from the raw fetch in `data/raw_sources/bls_eia_2026-10-24/` (BLS API v1 response and EIA spreadsheets exactly as downloaded on 2026-10-24; `fetch_log.txt` holds the commands and SHA-256 of every file; `titles/series_titles.txt` holds the official series titles).

**What a factor is.** `factor = index(latest) / index(base)`. It rescales a cost that was valid in the base month to the latest month for the thing the series measures. It is not a price, it is national (except the Los Angeles CPI and the California diesel price) and it says nothing about one supplier's quote. Apply at most one factor per cost component; never a material factor on a labor cost, never two factors on the same number, never a factor on a quote you already have for today.

**How to apply to a unit cost from a 2022 book (national, bare costs as of January 2022):**

* material cost × the commodity series that fits the item (steel, lumber, concrete, gypsum, paint, nonferrous metals); `WPUIP2300001` (inputs to construction, goods) when none fits;
* labor cost × `CIU2012300000000I` (total compensation) when the book figure includes employer-paid benefits, else `CIU2022300000000I` (wages);
* equipment cost: the ownership/rental part × `WPU114`, the fuel part × diesel (`WPU057303` producer price, or the EIA retail series);
* then the location adjustment for Los Angeles from the book's own city cost index (material and installation separately) — not the CPI;
* the CPI rows are reference only: consumer prices are not construction costs.

The latest monthly PPI points are **preliminary** (BLS revises up to four months after first publication); ECI is quarterly, latest 2026-Q2.

| series id | series | fits | base | base value | latest | latest value | **factor** | latest point |
|---|---|---|---|---|---|---|---|---|
| `WPU1022` | Primary nonferrous metals (PPI) | copper/aluminum content of wire, pipe, flashing: upper bound (raw metal, not finished product) | 2022-M01 | 275.728 | 2026-M09 | 566.010 | **2.0528** | preliminary |
| `WPU1025` | Nonferrous mill shapes (PPI) | aluminum/copper products: sheet, extrusions, tube, wire rod | 2022-M01 | 282.544 | 2026-M09 | 401.472 | **1.4209** | preliminary |
| `WPU1017` | Steel mill products (PPI) | rebar, structural steel, studs, decking | 2022-M01 | 441.497 | 2026-M09 | 388.580 | **0.8801** | preliminary |
| `WPU0811` | Softwood lumber (PPI) | framing lumber | 2022-M01 | 480.643 | 2026-M09 | 288.562 | **0.6004** | preliminary |
| `WPU081` | Lumber (PPI) | lumber, all | 2022-M01 | 404.213 | 2026-M09 | 282.340 | **0.6985** | preliminary |
| `WPU133` | Concrete products (PPI) | precast, block, pipe | 2022-M01 | 309.141 | 2026-M09 | 410.255 | **1.3271** | preliminary |
| `WPU1332` | Concrete pipe (PPI) | concrete pipe | 2022-M01 | 285.898 | 2026-M09 | 399.708 | **1.3981** | preliminary |
| `WPU1333` | Ready-mix concrete (PPI) | ready-mix concrete | 2022-M01 | 309.607 | 2026-M09 | 395.319 | **1.2768** | preliminary |
| `WPU137` | Gypsum products (PPI) | drywall, plaster | 2022-M01 | 417.482 | 2026-M09 | 488.936 | **1.1712** | preliminary |
| `WPU0622` | Paint materials (PPI) | paint and coatings | 2022-M01 | 295.024 | 2026-M09 | 350.371 | **1.1876** | preliminary |
| `WPU114` | General purpose machinery and equipment (PPI) | equipment ownership/rental component (not fuel) | 2022-M01 | 286.277 | 2026-M09 | 382.178 | **1.3350** | preliminary |
| `WPU0573` | Light fuel oils (PPI) | reference | 2022-M01 | 342.535 | 2026-M09 | 636.707 | **1.8588** | preliminary |
| `WPU057303` | No. 2 diesel fuel (PPI) | equipment fuel component (producer price) | 2022-M01 | 365.449 | 2026-M09 | 675.626 | **1.8488** | preliminary |
| `WPUIP2300001` | Inputs to construction industries, goods (PPI) | material cost, default when no commodity series fits | 2022-M01 | 301.473 | 2026-M09 | 365.374 | **1.2120** | preliminary |
| `CIU2012300000000I` | ECI total compensation, private construction (NSA, current dollar) | labor cost incl. benefits | 2022-Q01 | 146.1 | 2026-Q02 | 171.203 | **1.1718** | final |
| `CIU2022300000000I` | ECI wages and salaries, private construction (NSA, current dollar) | bare wages | 2022-Q01 | 147.2 | 2026-Q02 | 174.584 | **1.1860** | final |
| `CUUR0000SA0` | CPI-U all items, U.S. city average (NSA) | reference only: consumer prices, not construction | 2022-M01 | 281.148 | 2026-M09 | 336.940 | **1.1984** | final |
| `CUURS49ASA0` | CPI-U all items, Los Angeles-Long Beach-Anaheim (NSA) | reference only | 2022-M01 | 301.209 | 2026-M09 | 358.725 | **1.1910** | final |
| `eia_diesel_us_monthly.xls` | EIA U.S. No. 2 diesel retail price, $/gal, monthly | equipment fuel component (retail, national) | 2022-01 | 3.724 | 2026-09 | 6.291 | **1.6893** | as published (EIA monthly average) |
| `eia_diesel_california_monthly.xls` | EIA California No. 2 diesel retail price, $/gal, monthly | equipment fuel component (retail, California) | 2022-01 | 4.803 | 2026-09 | 8.058 | **1.6777** | as published (EIA monthly average) |

CSV: `data/derived/price_update_factors_2022-01_2026-09.csv`.
