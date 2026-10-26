---
title: CEC — Factors 2022 to latest
type: reference
tags: [indices, bls]
source: Claude Estimator Construction
build: 2026-10-24
---
# Factors (BLS/EIA, January 2022 → latest)

| series | fits | factor |
|---|---|---|
| `WPU1022` Primary nonferrous metals (PPI) | copper/aluminum content of wire, pipe, flashing: upper bound (raw metal, not finished product) | **2.0528** |
| `WPU1025` Nonferrous mill shapes (PPI) | aluminum/copper products: sheet, extrusions, tube, wire rod | **1.4209** |
| `WPU1017` Steel mill products (PPI) | rebar, structural steel, studs, decking | **0.8801** |
| `WPU0811` Softwood lumber (PPI) | framing lumber | **0.6004** |
| `WPU081` Lumber (PPI) | lumber, all | **0.6985** |
| `WPU133` Concrete products (PPI) | precast, block, pipe | **1.3271** |
| `WPU1332` Concrete pipe (PPI) | concrete pipe | **1.3981** |
| `WPU1333` Ready-mix concrete (PPI) | ready-mix concrete | **1.2768** |
| `WPU137` Gypsum products (PPI) | drywall, plaster | **1.1712** |
| `WPU0622` Paint materials (PPI) | paint and coatings | **1.1876** |
| `WPU114` General purpose machinery and equipment (PPI) | equipment ownership/rental component (not fuel) | **1.3350** |
| `WPU0573` Light fuel oils (PPI) | reference | **1.8588** |
| `WPU057303` No. 2 diesel fuel (PPI) | equipment fuel component (producer price) | **1.8488** |
| `WPUIP2300001` Inputs to construction industries, goods (PPI) | material cost, default when no commodity series fits | **1.2120** |
| `CIU2012300000000I` ECI total compensation, private construction (NSA, current dollar) | labor cost incl. benefits | **1.1718** |
| `CIU2022300000000I` ECI wages and salaries, private construction (NSA, current dollar) | bare wages | **1.1860** |
| `CUUR0000SA0` CPI-U all items, U.S. city average (NSA) | reference only: consumer prices, not construction | **1.1984** |
| `CUURS49ASA0` CPI-U all items, Los Angeles-Long Beach-Anaheim (NSA) | reference only | **1.1910** |
| `eia_diesel_us_monthly.xls` EIA U.S. No. 2 diesel retail price, $/gal, monthly | equipment fuel component (retail, national) | **1.6893** |
| `eia_diesel_california_monthly.xls` EIA California No. 2 diesel retail price, $/gal, monthly | equipment fuel component (retail, California) | **1.6777** |

Back to [[Claude Estimator Construction]].
