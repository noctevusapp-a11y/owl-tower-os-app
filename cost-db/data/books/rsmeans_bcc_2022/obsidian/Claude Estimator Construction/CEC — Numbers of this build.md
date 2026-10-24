---
title: CEC — Numbers of this build
type: reference
tags: [estimating, status]
source: Claude Estimator Construction
build: 2026-10-24
---
# Numbers of this build

* 692 table pages (all unit-price table pages of the scan; 41 with an unreadable header read through the neighbouring page's column anchors), 1473 sections, 29629 printed lines; **24117 priced lines**: **11378 verified**, 3285 machine_read (not verified), 9454 flagged (not verified), 949 percentage-add lines, 4563 description-only lines.
* 22252 lines carry a derived Los Angeles 2026-Q02 value (11045 of them on verified lines).
* Crews: 583 (incl. 0 single-trade crews built from the trade-rate table); trades: 45.
* **verified** means: every printed money cell carries evidence weight ≥ 4 for one value (the geometric reading of digits and decimal point, 3, plus at least one of the three OCR readings: 360-dpi tesseract, the scan's text layer, 600-dpi tesseract) or is computed by the book's arithmetic; output/hours confirmed by two readings or the crew rule; no check open; money columns tied; section id known. An unreadable crew cell is filled only when exactly one crew of the crew table satisfies the line's labor-hours, daily labor cost, equipment presence and O&P at once (`CREW_FROM_ARITHMETIC`). The spot-check results (rows read by eye against the page image) are in `extraction_report.md`, section 3. No tolerance is attached to any number: a number is verified or it is not.

| division | verified | machine_read | flagged |
|---|---|---|---|
| 01 General Requirements | 265 | 44 | 122 |
| 02 Existing Conditions | 382 | 115 | 250 |
| 03 Concrete | 817 | 253 | 476 |
| 04 Masonry | 389 | 112 | 305 |
| 05 Metals | 703 | 364 | 551 |
| 06 Wood, Plastics & Composites | 1114 | 245 | 689 |
| 07 Thermal & Moisture Protection | 346 | 193 | 671 |
| 08 Openings | 803 | 206 | 787 |
| 09 Finishes | 837 | 452 | 614 |
| 10 Specialties | 626 | 99 | 306 |
| 11 Equipment | 573 | 98 | 360 |
| 12 Furnishings | 285 | 37 | 180 |
| 13 Special Construction | 328 | 96 | 242 |
| 14 Conveying Equipment | 122 | 25 | 111 |
| 21 Fire Suppression | 61 | 3 | 20 |
| 22 Plumbing | 441 | 93 | 346 |
| 23 Heating, Ventilating & Air Conditioning | 468 | 110 | 409 |
| 26 Electrical | 964 | 116 | 290 |
| 27 Communications | 17 | 26 | 23 |
| 28 Electronic Safety & Security | 100 | 12 | 32 |
| 31 Earthwork | 611 | 278 | 499 |
| 32 Exterior Improvements | 426 | 119 | 290 |
| 33 Utilities | 541 | 162 | 350 |
| 34 Transportation | 60 | 5 | 38 |
| 35 Waterway & Marine Construction | 7 | 3 | 6 |
| 41 Material Processing & Handling Equipment | 37 | 0 | 19 |
| 44 Pollution Control Equipment | 53 | 14 | 35 |
| 46 Water & Wastewater Equipment | 0 | 5 | 7 |
| 48 Electrical Power Generation | 2 | 0 | 6 |

Back to [[Claude Estimator Construction]].
