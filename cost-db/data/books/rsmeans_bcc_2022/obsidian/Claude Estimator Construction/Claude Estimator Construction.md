---
title: Claude Estimator Construction
type: reference
tags: [moc, estimating, cost-data]
source: Claude Estimator Construction
build: 2026-10-24
aliases: [CEC, Cost table]
---

# Claude Estimator Construction — Map of Content

The company's book-derived unit-cost reference, read by machine from the 2022 cost book and brought to Los Angeles at the latest BLS month. Built and checked by Claude; the extraction method and the limits are in [[CEC — Method and limits]].

## Use
* [[CEC — How to price a line]] — the rule, with a worked example
* [[CEC — Numbers of this build]] — counts by division, what is verified
* `book_lines_la_latest.xlsx` (in this folder) — the table itself; `COLUMNS.md` — the columns

## Reference data
* [[CEC — Factors 2022 to latest]] — BLS/EIA factors with sources
* [[CEC — Los Angeles City Cost Index 2022]]
* [[CEC — Trade rates 2022]]
* [[CEC — Method and limits]]

## Where it lives
* Repository `owl-tower-os-app`, branch `claude/construction-cost-database-sv4dab`, folder `cost-db/data/books/rsmeans_bcc_2022/`.
* Skill: the same reference is attached to the **bid-estimating** skill as `references/claude-estimator-construction.md`.
