#!/usr/bin/env python3
"""Reproducible worked examples -> examples/worked_examples.md

Sections 1-6 use SYNTHETIC, deliberately round inputs from tests/fixtures/synthetic.py (they exist only so the formulas can be
followed by hand). Section 7 runs the engine on the REAL data and shows what it refuses to compute.

Run:  python3 examples/run_examples.py
"""
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "pipeline"))
from costdb.calc import Engine, apply_markup, margin_to_markup, markup_to_margin  # noqa: E402
from tests.fixtures import synthetic as S  # noqa: E402
from tests.test_calc import LaborRateTest  # noqa: E402

out = []


def w(*lines):
    out.extend(lines)


def table(res, title):
    w(f"**{title}** — status `{res.status}`, unit `{res.run['result_unit_id']}`", "", "| # | kind | description | quantity (incl. waste; labor = person-hours) | unit | unit cost | per unit of result | origin |", "|---|---|---|---|---|---|---|---|")
    for ln in res.lines:
        q = f"{ln['quantity']:.6f}".rstrip("0").rstrip(".") if ln["quantity"] is not None else "—"
        uc = f"{ln['unit_cost']:.6f}".rstrip("0").rstrip(".") if ln["unit_cost"] is not None else "—"
        ec = f"{ln['extended_cost']:.6f}" if ln["extended_cost"] is not None else "—"
        w(f"| {ln['line_no']} | {ln['line_kind']} | {ln['description']} | {q} | {ln['quantity_unit_id'] or ''} | {uc} | {ec} | {ln['origin_summary']} |")
    w("")


w("# Worked examples", "",
  "> **SYNTHETIC INPUTS — NOT MARKET DATA.** Sections 1–6b use invented round numbers (a $12.80 sheet, a $40/h crew rate ...) so every figure can be "
  "checked by hand. They show the *method*, not Los Angeles prices. They live in `tests/fixtures/` and can never enter `data/` (tests and the validator reject them). "
  "Section 7 uses the real data and shows what the engine refuses to compute without sourced inputs.", "",
  "Regenerate: `python3 examples/run_examples.py`.", "")

# ---------------------------------------------------------------- 1
db = S.priced_drywall_db()
eng = Engine(db)
res = eng.unit_cost(S.WI, 1, S.params())
w("## 1. Unit cost — hang 1/2 in regular gypsum board on wood studs (`WI-DRY-001`, per SF)", "",
  "Real work-item definition; synthetic prices, waste factors and labor data.", "",
  "| input | synthetic value |", "|---|---|",
  "| board pack | 4x8 sheet = 32 SF at $12.80 → $0.40/SF; waste 10 % |",
  "| screws | box of 500 at $5.00 → $0.01 each; 0.875 screws/SF (from geometry: 4 fastener lines × 7 screws per 4x8 sheet, screw at both ends, 28 ÷ 32 SF); waste 5 % |",
  "| crew | 2 × drywall installer at $40/h + 1 laborer at $30/h, 8 h shift |",
  "| norm | 1,600 SF per crew-day |",
  "| run options | strict mode; `accept_retail_proxy=True` (the synthetic prices are labelled retail; retail is never used unless asked for); company labor rate |", "")
table(res, "Result")
w("Hand check:", "",
  "```", "board   = 1 SF × (1 + 0.10) × (12.80 / 32)          = 0.44",
  "screws  = 0.875 EA × (1 + 0.05) × (5.00 / 500)        = 0.0091875",
  "labor   = (2×40 + 1×30) × 8 h / 1600 SF = 880 / 1600  = 0.55",
  "total                                                  = 0.9991875 per SF (stored rounded to 6 decimals: 0.999188)",
  "person-hours per SF = 3 × 8 / 1600 = 0.015;  crew-hours per SF = 8 / 1600 = 0.005", "```", "",
  f"Engine: `direct_cost_total = {res.run['direct_cost_total']}`  · run id `{res.run['run_id']}` (deterministic) · warnings: {', '.join(res.run['warnings'])}", "",
  f"Run basis recorded on the run: `price_basis = {res.run['price_basis']}`, `input_review_floor = {res.run['input_review_floor']}`.",
  "The retail-price warning is deliberate: this is not a contractor purchase price.", "")

# ---------------------------------------------------------------- 2
base = res
base.run["direct_cost_total"] = D("100.000000")
kw = dict(overhead_pct=D("0.10"), overhead_basis="example only", contingency_pct=D("0.05"), contingency_basis="example only",
          profit_basis="example only", run_at=S.RUN_AT)
a = apply_markup(base, profit_method="markup", profit_value=D("0.10"), **kw)
b = apply_markup(base, profit_method="margin", profit_value=D("0.10"), **kw)
w("## 2. Overhead, contingency, profit — markup versus margin", "",
  "With a direct cost of $100.00 (round number for the example), overhead 10 % of direct, contingency 5 % of (direct + overhead). The price goes to "
  "`price_total`; `direct_cost_total` keeps the direct cost, and percentages outside 0–1 (e.g. `10` meaning 10 %) are refused:", "",
  "| step | markup 10 % | margin 10 % |", "|---|---|---|")
for la, lb in zip(a.lines, b.lines):
    label = "Profit" if la["line_kind"] == "profit" else la["description"].split(" — ")[0]
    w(f"| {label} | {la['extended_cost']:.2f} | {lb['extended_cost']:.2f} |")
w("", "```", "markup m = 10 %:  price = cost × (1 + m)  = 115.50 × 1.10   = 127.05", "margin g = 10 %:  price = cost / (1 − g)  = 115.50 / 0.90   = 128.33",
  f"a 25 % markup is a {markup_to_margin(D('0.25'))*100:.0f} % margin;  a 20 % margin needs a {margin_to_markup(D('0.20'))*100:.0f} % markup", "```", "",
  "Each percentage must be passed with a stated basis; there are no defaults.", "")

# ---------------------------------------------------------------- 3
t = LaborRateTest(); t.setUp(); t.stat_rate(); t.all_burdens()
lr = Engine(t.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="stat_loaded", annual_paid_hours=D("2080")))
w("## 3. Loaded labor rate from layered inputs (statistical wage + burdens)", "",
  "Synthetic: wage $30.00/h (metro-division level, used for the county and flagged), benefits 25 % of wages, Social Security 6.2 % (cap $200,000), Medicare 1.45 %, "
  "FUTA 0.6 % / CA UI 3.4 % / ETT 0.1 % each on the first $7,000, workers' comp $8.00 per $100 payroll, 2,080 paid hours per year.", "",
  "| component | $/paid hour |", "|---|---|")
for ln in lr.lines:
    w(f"| {ln['description']} | {ln['unit_cost']:.4f} |")
w(f"| **loaded total** | **{lr.run['labor_cost']:.4f}** |", "",
  "Note the capped items: UI = 0.034 × 7,000 / 2,080 = $0.1144/h — a cap makes the hourly cost tiny, it is **not** 3.4 % of wages. "
  f"Warnings: {', '.join(lr.run['warnings'])}.", "")

# ---------------------------------------------------------------- 4
t2 = LaborRateTest(); t2.setUp()
r_priv = Engine(t2.db).loaded_labor_rate("TR-DRYW", S.params(labor_basis="prevailing_loaded", project_type="private"))
w("## 4. Prevailing wage is not applied to private projects", "",
  f"Requesting `labor_basis='prevailing_loaded'` with `project_type='private'` → status `{r_priv.status}`, code `{r_priv.run['missing_inputs'][0]['code']}`: "
  f"*{r_priv.run['missing_inputs'][0]['reason']}*", "",
  "For a public-works run the determination already contains fringe, so the engine adds payroll taxes and workers' comp but **not** employer benefits again "
  "(see `tests/test_calc.py::test_prevailing_wage_does_not_add_benefits_twice`).", "")

# ---------------------------------------------------------------- 5
db5 = S.priced_drywall_db()
o = next(x for x in db5["price_observations"] if x["observation_id"] == "TEST-OBS-BOARDA")
o["observed_at"] = date(2025, 6, 1); o["retrieved_at"] = "2025-06-02T00:00:00+00:00"
r_no = Engine(db5).unit_cost(S.WI, 1, S.params(max_price_age_days=365))
db5.add("indices", {"index_id": "TEST-IDX-1", "publisher": "TEST", "series_code": "T1", "name": "synthetic", "base_period": None, "frequency": "monthly",
                    "seasonal_adjustment": None, "geography": None, "applies_to": "material", "source_id": S.SRC, "origin": "observed",
                    "review_status": "validated", "reviewed_by": "tests", "reviewed_at": S.RUN_AT, "notes": None})
for per, val in ((date(2025, 6, 1), "200"), (date(2026, 9, 1), "205"), (date(2026, 10, 1), "210")):
    db5.add("index_values", {"index_id": "TEST-IDX-1", "period_start": per, "vintage_date": date(2026, 10, 20), "value": D(val), "value_status": "final",
                             "retrieved_at": "2026-10-20T00:00:00+00:00", "source_locator": "synthetic", "raw_file_sha256": None, "origin": "observed",
                             "review_status": "validated", "reviewed_by": "tests", "reviewed_at": S.RUN_AT, "notes": None})
r_idx = Engine(db5).unit_cost(S.WI, 1, S.params(time_index_id="TEST-IDX-1"))
mat = [ln for ln in r_idx.lines if ln["line_kind"] == "material"][0]
adj = mat["inputs"][-1]["adjustments"]["time_index"]
w("## 5. Bringing an old price forward with an index", "",
  f"The same board price observed 2025-06-01 is {(date(2026,10,24)-date(2025,6,1)).days} days old. With an explicit age limit of 365 days and no index the run is "
  f"`{r_no.status}` (`{r_no.run['missing_inputs'][0]['code']}`); without any limit the price would be used unadjusted and flagged `PRICE_NOT_TIME_ADJUSTED`. "
  "With a synthetic monthly index series (200 in 2025-06, 205 in 2026-09, 210 in 2026-10) the engine adjusts EVERY price whose month differs from the as-of month, "
  "stores both dates, the series, both index values and the formula on the line (if the as-of month is not yet published it falls back to the latest published period "
  "and says so with `INDEX_LATEST_PUBLISHED_PERIOD_USED`). The series must apply to the same cost kind (a labor index cannot adjust a material price):", "",
  "```", f"price_to = price_from × index_to / index_from = 0.40 × {adj['index_to']} / {adj['index_from']} = {0.40*210/200:.2f} per SF",
  f"line = 1 SF × (1 + 0.10) × 0.42 = {mat['extended_cost']:.6f}", "```", "",
  "The index is an input to a conversion, never a price in itself; a regional factor is never applied to an already-local price.", "")

# ---------------------------------------------------------------- 6
asm = S.assembly_db()
ra = Engine(asm).assembly_cost("TEST-ASM-1", 1, S.params())
w("## 6. Assembly from versioned unit costs", "",
  "Synthetic assembly = 2.0 SF of `WI-DRY-001` + 3 EA of a synthetic $2.00 widget work item, per SF.", "")
table(ra, "Result")
w("```", f"2 × 0.999188 + 3 × 2.00 = {2*D('0.999188')+3*D('2.00')}", "```", "",
  "A second work item that claims the same included-scope token as the first turns the run into `failed / SCOPE_OVERLAP` (double counting), "
  "see `tests/test_calc.py::test_scope_overlap_is_a_double_counting_failure`. Each child is priced for its OWN quantity "
  "(assembly quantity × quantity per assembly unit), so quantity tiers and quantity factors are chosen on the right number.", "")

# ---------------------------------------------------------------- 6b
pdb = S.paint_db()
rp = Engine(pdb).unit_cost(S.PNT, 1, S.params())
pl = [ln for ln in rp.lines if ln["line_kind"] == "material"][0]
w("## 6b. Coverage-based material: each spread rate is paired with ITS OWN product's price", "",
  "`WI-PNT-001` — prime new gypsum board, one coat of PVA primer. The quantity of primer comes from the manufacturer's spread rate, not from a typed number. "
  "Synthetic: product A $100 per 5 US gal ($20/gal) covers 400 SF/gal; product B $200 per 5 US gal ($40/gal) covers 200 SF/gal; both are the same spec line.", "",
  "```", "A: 1/400 gal/SF × $20 = 0.05 $/SF", "B: 1/200 gal/SF × $40 = 0.20 $/SF", "line = median of the two paired costs = 0.125 $/SF", "```", "",
  f"Engine: material line `extended_cost = {pl['extended_cost']}`, `quantity = {pl['quantity']}` (none: the two products consume different quantities), "
  f"warnings {pl['warnings']}. A coverage given in SY (or any other area unit) is converted to the work item's SF; several coverage rows that differ in film thickness "
  "need a `consumption_selector`, otherwise the run is incomplete (`CONSUMPTION_AMBIGUOUS`).", "")

# ---------------------------------------------------------------- 7
real = Engine(S.real_db())
rr = real.assembly_cost("ASM-WALL-001", 1, S.params(allow_synthetic=False, labor_basis="stat_loaded", region_id="REG-CA-037"))
import collections
cnt = collections.Counter(m["code"] for m in rr.run["missing_inputs"])
w("## 7. The real pilot data: what the engine refuses to compute", "",
  "`ASM-WALL-001` — interior partition, 2x4 wood studs @16 in, 1/2 in regular gypsum each side, Level 4, primer + 2 eggshell coats each side (per SF of wall), "
  "Los Angeles County, strict mode, real data (no synthetic input).", "",
  f"Status: **`{rr.status}`**, total: **{rr.run['direct_cost_total']}** (none is stored). Missing inputs reported: **{len(rr.run['missing_inputs'])}**", "",
  "| code | count |", "|---|---|")
for k, v in cnt.most_common():
    w(f"| {k} | {v} |")
w("", "First items:", "")
for m in rr.run["missing_inputs"][:6]:
    w(f"- `{m['component_ref']}` **{m['code']}** — {m['needed']}: {m['reason']}")
w("", "Each gap names what to capture; closing the gaps (prices, waste factors, crew and norm, manufacturer coverage) turns the run `complete` without any code change.", "")

(ROOT / "examples" / "worked_examples.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote examples/worked_examples.md")
