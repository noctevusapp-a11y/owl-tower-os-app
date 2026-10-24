---
title: CEC — Numbers of this build
type: reference
tags: [estimating, status]
source: Claude Estimator Construction
build: 2026-10-24
---
# Numbers of this build

* 692 table pages (all unit-price table pages of the scan; 41 with an unreadable header read through the neighbouring page's column anchors), 1473 sections, 29629 printed lines; **24117 priced lines**: **11745 verified**, 3394 machine_read (not verified), 8978 flagged (not verified), 949 percentage-add lines, 4563 description-only lines.
* 23064 lines carry a derived Los Angeles 2026-Q02 value (11411 of them on verified lines).
* Crews: 961 (incl. 378 single-trade crews built from the trade-rate table); trades: 45.
* **verified** means: every printed money cell carries evidence weight ≥ 4 for one value (the geometric reading of digits and decimal point, 3, plus at least one of the three OCR readings: 360-dpi tesseract, the scan's text layer, 600-dpi tesseract) or is computed by the book's arithmetic; output/hours confirmed by two readings or the crew rule; no check open; money columns tied; section id known. An unreadable crew cell is filled only when exactly one crew of the crew table satisfies the line's labor-hours, daily labor cost, equipment presence and O&P at once (`CREW_FROM_ARITHMETIC`). The spot-check results (rows read by eye against the page image) are in `extraction_report.md`, section 3. No tolerance is attached to any number: a number is verified or it is not.

| division | verified | machine_read | flagged |
|---|---|---|---|
| 01 General Requirements | 265 | 44 | 122 |
| 02 Existing Conditions | 388 | 120 | 255 |
| 03 Concrete | 857 | 257 | 511 |
| 04 Masonry | 399 | 124 | 322 |
| 05 Metals | 723 | 379 | 581 |
| 06 Wood, Plastics & Composites | 1129 | 245 | 695 |
| 07 Thermal & Moisture Protection | 375 | 209 | 711 |
| 08 Openings | 820 | 218 | 810 |
| 09 Finishes | 851 | 461 | 626 |
| 10 Specialties | 628 | 99 | 307 |
| 11 Equipment | 582 | 98 | 361 |
| 12 Furnishings | 291 | 38 | 182 |
| 13 Special Construction | 338 | 100 | 265 |
| 14 Conveying Equipment | 128 | 26 | 112 |
| 21 Fire Suppression | 66 | 3 | 20 |
| 22 Plumbing | 519 | 102 | 402 |
| 23 Heating, Ventilating & Air Conditioning | 519 | 123 | 459 |
| 26 Electrical | 964 | 116 | 290 |
| 27 Communications | 17 | 26 | 23 |
| 28 Electronic Safety & Security | 100 | 12 | 32 |
| 31 Earthwork | 638 | 283 | 508 |
| 32 Exterior Improvements | 432 | 119 | 291 |
| 33 Utilities | 541 | 162 | 350 |
| 34 Transportation | 76 | 8 | 55 |
| 35 Waterway & Marine Construction | 7 | 3 | 6 |
| 41 Material Processing & Handling Equipment | 37 | 0 | 22 |
| 44 Pollution Control Equipment | 53 | 14 | 35 |
| 46 Water & Wastewater Equipment | 0 | 5 | 7 |
| 48 Electrical Power Generation | 2 | 0 | 6 |

Back to [[Claude Estimator Construction]].
