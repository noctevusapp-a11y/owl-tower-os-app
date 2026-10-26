# Crews - Standard (PDF pages 763-799, book pages 749-785) and trade-rate table (PDF page 963): parse report

Date: 2026-10-24. Scripts: `/tmp/claude-0/book/scripts_crews/`. Working files: `/tmp/claude-0/book/work/`.

## Results

| file | content | rows | pass all checks |
|---|---|---|---|
| `derived/trade_rates_2022.csv` | labor trade rates, inside back cover | 45 trades (Skwk, Helpers, Foreman inside/outside, Clab, Asbe ... Wrck) | 45 / 45 |
| `derived/crews_2022.csv` | one row per crew member line | 2,543 (1,523 labor, 1,020 equipment) | 3 rows with an empty cell |
| `derived/crews_2022_totals.csv` | one row per crew | 583 crews, 583 distinct ids (A-1 ... A-13, B-1 ... B-95, C, D, E, F, G, H, J, K, L, M, Q, R series and W-41E) | 568 / 583 (`checks_ok=true`) |

Series counts: A 45, B 335, C 65, D 14, E 27, F 5, G 8, H 3, J 8, K 2, L 14, M 3, Q 26, R 24, W 1.

Checks stored per crew (`checks_ok` is true only when every one holds): labor daily = hr x 8 x qty (bare and O&P),
L.H. = 8 x sum(labor qty), sum of member dailies = daily total (bare and O&P, tolerance 0.006 + 0.005 per member because the
printed dailies are rounded to the cent and the total is the rounded exact sum), and the six cost-per-labor-hour figures
(labor, equipment, total; bare and O&P) = the corresponding daily sum / L.H. (tolerance 0.011).
Trade-rate checks: daily = 8 x hourly, F = B + C + D + E, G = A x F (allowing the 0.05 rounding of G and the 0.1 % rounding of F),
H = A + G, I = 8 x H. Columns C (18.5 %) and E (10 %) are printed once with an arrow and carried down every row, as on the page.

## Unresolved cells (left empty, note in the `notes` column)

Member rows (`crews_2022.csv`):

- B-15 (p772) member 4: quantity (no source read the count; the row is otherwise complete).
- B-37I (p779) member 7: bare_daily (readings 54.02 / 4.02 / 94.02; the sum needs 61.43, none compatible).
- E-8 (p792) member 10: bare_daily (readings 98758.26 / $8758.26 / 88758.26 disagree in the leading digit and the totals of this crew are also unreadable).

Crew totals (`crews_2022_totals.csv`):

- A-10B (p764): bare and O&P daily totals and the total $/LH (the totals row is unreadable in every reading).
- B-10T (p768): O&P labor $/LH (readings $8268 / 69953, expected 82.53).
- B-34H (p776): bare and O&P labor $/LH (not read); its member sum is also short of the printed total (a row lost between stray OCR lines).
- B-90D (p786): bare/O&P totals and total $/LH (totals row unreadable).
- E-5 (p792): O&P daily total (readings 9656.87 / 9656.88 both fit the sum within rounding).
- E-8 (p792): all four totals cells.
- R-6 (p798): O&P daily total (readings $9588.20 do not fit the member sum 9369.35; one member O&P daily is probably misread).

## Crews that fail at least one check (15)

A-10B, B-10T, B-15, B-34H, B-34U, B-37I, B-37K, B-69A, B-81, B-90D, C-17C, E-5, E-8, R-6, W-41E. Each carries the failed
check names and the raw readings in its `notes`. Typical causes: an equipment daily read with one wrong digit where two cells of
the same kind could absorb the correction (B-34U, B-37K, B-81), a per-LH figure read with a lost digit (B-69A, W-41E), a quantity
of .375 that the parser could not confirm (C-17C), totals rows that no reading could resolve (A-10B, B-90D, E-8).

## Values that were settled by the identities rather than by a clean reading

- 49 member rows carry a cell chosen among disagreeing OCR readings by the identities (note "via ..."); 2 of them are single-digit
  corrections where the sum and the per-LH figure both contradicted an agreed reading (B-82C member 8 O&P daily, B-82D member 2 O&P daily).
- 12 cells had no OCR reading at all and were filled only because two independent printed identities agree on them (note "no OCR reading"):
  the L.H. figure of A-3G, A-10B, B-25B, B-34A, B-39, B-62A, B-64, B-90D, E-8, E-13, E-19 (= 8 x sum of labor quantities, confirmed by
  total $/LH x L.H. where the total was read) and the bare daily total of A-1H (sum of dailies = 444.40 and 55.55 $/LH x 8 agree).
  On B-25B the left edge of the scan is cut, so the leading counts of two equipment rows and the L.H. figure are physically missing;
  the counts come from the item rates seen in other crews (see below).
- Lost leading decimal points in quantities (".5 Laborer" read as "5") are restored by the labor identity daily = hr x 8 x qty;
  for equipment lines the daily rate of the same item in other crews decides (e.g. ".5 Crawler Loader, 3 C.Y." 590.46 vs 1180.92 at qty 1).
- 11 crew ids were settled by looking at the header crop on the page image (contact sheets `work/ids_sheet*.png`): the O/Q suffix that
  every OCR prints as "0" (A-3Q, B-10O, B-10Q, B-11Q, B-12O, B-12Q, B-34Q), B-13I, B-81A, H-2, Q-4. Their notes say "confirmed by eye".
- 4 crews had a header or totals row that no page-level reading found; they were read from a row crop (note "read from a row crop").
- Descriptions are the OCR reading whose words are most confirmed by the other readings; they keep the book's abbreviations and are not
  spell-checked. "2-50' Air Hoses, 1.5\"" style rows are stored as quantity 2 with description "-50' Air Hoses, 1.5\"".

## Method

1. Readings. Three readings per page were merged word by word: `ocr/pNNNN.tsv` (book OCR, 360 dpi), `ia/pNNNN.json` (the scan's text
   layer) and T400 = tesseract 5 (psm 6) run on each crew column cropped from a 400 dpi pymupdf render (`scripts_crews/render_ocr.py`).
   Recto and verso pages are shifted by ~0.055 of the page width, so each page's column positions are calibrated from the position of the
   "Costs" header words in the text layer (`work/page_offsets.json`). Vertical offsets of the text layer are aligned to T400 per page.
2. Structure. Words are grouped into rows (T400 rows anchor the other sources; the row y is the median of its words); numeric tokens are
   assigned to the six right-aligned columns (Hr, Daily, Hr, Daily, bare $/LH, O&P $/LH) by their right edge; a row is a header
   ("Crew X-NN"), a member (leading count + description), a totals row ("N L.H., Daily Totals", or $-amounts without an hourly rate), or a
   column header. Stray OCR lines closer than 0.0095 page heights to a real row are dropped (noted). A member row after a totals row starts a
   new crew whose header is read from a row crop.
3. Cells. Every cell keeps all its readings; a value is accepted directly when two readings agree (a lost decimal point counts as agreement
   at the digit level); otherwise the identities choose between the candidates, and a value is only ever taken from the identities when it is
   compatible with at least one reading (same digits, one substituted digit, or one dropped digit) or, for the 12 cells above, when two
   independent printed identities agree.
4. Fallbacks. A crew that still fails gets a fourth reading (TROW): each of its rows is located by its ink profile in the 400 dpi render,
   upscaled 2x (3x if empty) and read with tesseract psm 7; cells still empty get a fifth reading (TCELL) from the single cell crop with a
   digit whitelist. The remaining doubtful crews were inspected by eye on crops of the page image (B-25B, B-57, B-82C and the crew-id sheets).
5. Cross-crew equipment check: the daily amount of an equipment line is quantity x the item's daily rate, and the rate is constant across the
   book; the mode of daily/qty per description (fuzzy on the words, exact on the numbers) validates or restores the equipment quantities.
6. Labor hourly rates were checked against `trade_rates_2022.csv` (base rates, +0.50 inside foreman, +2.00 outside foreman) as a
   tie-breaker, never as an override: the printed rates in the crews match the table (e.g. Clab 45.60/67.90, Carp 56.30/83.80,
   Labor Foreman (outside) 47.60/70.85, Carpenter Foreman (inside) 56.80/84.55).

Scripts: `render_ocr.py` (renders, crops, OCR), `parse_trade_rates.py`, `parse_crews.py` (everything above; `--debug` prints the merged rows),
`apply_eye_ids.py` (applies the by-eye id table to the outputs), `contact_sheet.py`, `summarize.py`, `common.py`. Nothing under
`/home/user/owl-tower-os-app` was touched.
