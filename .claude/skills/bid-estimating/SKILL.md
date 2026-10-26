---
name: bid-estimating
description: Use this skill when the user prepares bids, proposals, takeoffs, cost estimates, or pricing for construction projects. Covers quantitative takeoff methods, unit pricing, labor productivity rates, overhead and profit (OH&P) markup calibration, subcontractor bid solicitation, bid-day protocols, proposal structure, exclusions language, contingency calculation, and bid-to-award ratio tracking. Includes frameworks for residential remodel, custom new construction, commercial TI, and mandatory retrofit estimating. Tuned for Owl Tower Construction Group, Inc. (CSLB #1108551).
license: Owl Tower Construction Group, Inc. — internal use
---

# Bid & Estimating Skill for California General Contractors

## Когда использовать этот скилл

Активируй когда пользователь:
- Готовит bid или proposal для нового project
- Делает takeoff (quantity survey) с plans или from existing
- Solicit-ит subcontractor quotes
- Калибрует unit costs для specific scope
- Решает overhead markup и profit для bid
- Готовит exclusions list для proposal
- Rebid-ит job после loss или scope change
- Анализирует win/loss patterns на прошлых bids
- Составляет estimating system для scaling

## Контекст компании

- **Company:** Owl Tower Construction Group, Inc.
- **CSLB License:** #1108551 (Class B)
- **Revenue baseline:** $3.4M annual, targeting $7M Year 1 growth, $50M+ long-term
- **Mix:** residential remodels (PV, Westside), commercial TI, custom fabrication
- **Estimating pain point at current size:** ad-hoc estimating, inconsistent markups, proposals without defensive exclusions — common at $3M scale, fatal at $10M+
- **Critical need:** systematize estimating BEFORE scaling headcount (otherwise scale multiplies inefficiency)

## Правило #1 — каждый bid проходит через эту последовательность

Никогда не давать price без выполнения этих шагов:

1. **Qualify the opportunity** — worth bidding?
2. **Understand scope** — plans, specs, site visit, client goals
3. **Takeoff** — quantities measured (not guessed)
4. **Unit pricing applied** — labor + material + equipment per line item
5. **Sub solicitation** — minimum 3 quotes per subcontracted scope
6. **General conditions / GCs** — project-duration overhead
7. **Contingency** — based on risk / unknowns
8. **Markup** — company overhead + profit
9. **Sanity check** — total against similar projects, gut check against market
10. **Exclusions / assumptions** — what's NOT included, clearly stated
11. **Review** — second set of eyes before sending

## Bid/No-Bid Decision — Qualify Before Investing Time

Estimating takes 20-80 hours per bid. Don't bid everything. Qualify using this framework:

### GO indicators:
- **Repeat client** or strong referral
- **Scope matches** Owl Tower's sweet spot (residential remodel $250K-$2M, commercial TI $200K-$1M)
- **Realistic budget** disclosed or probable
- **Clean specs** (stamped drawings, clear scope)
- **Reasonable schedule** (not impossible)
- **Payment terms** standard (10% retention, pay-when-paid modified)
- **No red flags** on client (see `client-vetting` skill)

### NO-BID indicators:
- **Price shopping** — client getting 10 bids, lowest wins
- **Budget way below market** — "we have $100K for full kitchen and 2 baths"
- **Client history** — lawsuits, slow pay, prior contractor terminations (check public records)
- **Scope undefined** — "we know what we want, just bid it"
- **Schedule unrealistic** — "we need it done in 30 days" (typical 120 days scope)
- **Design incomplete** — stamped drawings missing for permit-required work
- **Public works** — prevailing wage requirements if not set up for it
- **Geography** — too far (travel time kills margin)

### Qualify conversation — ask early:
1. "What's your budget range?" (если they refuse, 50/50 it's a fishing expedition)
2. "How many contractors are you getting bids from?" (3-4 OK, 10+ = race to bottom)
3. "What's your target start date?" (see if realistic)
4. "Are plans fully designed and permitted?"
5. "Have you worked with a GC before?" (newbies = high drama potential)
6. "What's most important: price, speed, or quality?" (all three = unrealistic expectations)

### If unqualified — professionally decline:
"Based on your requirements, we don't think we'd be the right fit for this project. We focus on [X type of work] and typically work in [Y budget range]. I'd be happy to refer you to [contractor in appropriate category]."

## Takeoff Methodology

**Takeoff** = measuring quantities from plans (or existing conditions) that become basis для pricing.

### Types of takeoff:
- **Linear** (LF) — baseboards, trim, rebar, piping
- **Area** (SF) — flooring, drywall, roofing, painting
- **Volume** (CY) — concrete, excavation, topsoil
- **Count** (EA) — windows, doors, fixtures, outlets
- **Weight** (LBS/TONS) — structural steel, rebar

### Tools:
- **PlanSwift, Bluebeam, STACK, Esticom** — digital takeoff software
- **Measuring wheel, tape** — field takeoff
- **Scaled paper drawings** + **engineer scale** — old-school, still valid

### Accuracy tolerance:
- **Concept estimate** — ±30% (based on sf x $/sf rule of thumb)
- **Schematic** — ±20% (rough takeoff)
- **Design Development** — ±10% (detailed takeoff, known specs)
- **Construction Documents (CDs)** — ±5% (final quantity takeoff, priced)

### Waste factors (add to takeoff):
- Drywall: 5-10%
- Flooring (tile): 10-15%
- Wood flooring: 5-10%
- Paint: 10-15% + 1 extra gallon per room
- Lumber framing: 10-15% (depends on pattern complexity)
- Concrete: 5% (slabs), 10% (complex forms)
- Rebar: 10%
- Roofing: 10-15%

### Common takeoff errors (costs you margin):
- Forgot corner wraps / returns on trim
- Missed L-shaped room hidden in plan
- Ceiling area same as floor (assumed, but vaulted = more)
- Wall area = perimeter × height (but minus openings — don't forget to subtract)
- Tall walls = two people needed → scaffolding / lift rental

## Unit Pricing Framework

**Unit cost** = cost per unit of measure for a specific task.

Example: Install drywall
- Material: $12 per 4×8 sheet (0.375 sf/$ unit cost for material)
- Labor: Hang drywall at 400 sf per person-day, $350 loaded labor/day = $0.875/sf labor
- Plus tape/mud material ~$0.30/sf, taping labor $0.90/sf
- **Total installed drywall ~$2.50-3.00/sf** (hang + tape, smooth finish)

### Owl Tower cost table (Claude Estimator Construction) — обязательный reference layer

Перед тем как ставить unit price по памяти или "по рынку", открой `references/claude-estimator-construction.md`
(полная таблица: репозиторий `owl-tower-os-app`, `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.xlsx`).
Это машинно считанная копия справочного экземпляра книги 2022 года (national bare costs) с пересчётом
каждой строки в **Los Angeles, последний месяц BLS** (компонент × City Cost Index LA × индекс BLS по компоненту).

Правило применения:
1. Найди строку по `cost_code` (`OT-<section>-<line>`) или по описанию; проверь единицу измерения.
2. `status = verified` — можно использовать как reference (каждое число подтверждено всеми тремя чтениями или арифметикой
   книги, колонки сверены). `machine_read` и `flagged` — не verified: сначала открой страницу книги (`book_page`) и прочитай
   строку сам; не используй их «с допуском» — погрешности к числам не приписываются. `percent_add` — это надбавка в %, не цена.
3. Для текущего бюджета бери колонки `*_la_latest`; для "что говорит книга" — `*_2022`.
4. Замени тем, что лучше: котировка поставщика → material; свои бригады и выработка (`labor_hours` × loaded rate) → labor;
   аренда → equipment. Таблица — ориентир, не котировка; сверху добавляй tax, delivery, GCs, contingency, OH&P компании.
5. Никогда не применяй второй региональный или временной коэффициент: он уже внутри `*_la_latest`.

### Build your own unit cost library — critical для scaling.

Track на каждый past job actual costs per unit. After 10 jobs, you have reliable internal data. Industry sources (RS Means, Craftsman) — starting point but regional variance significant.

### Labor rates — understand loaded cost:

Carpenter pay rate: $35/hour
+ Employer FICA, Medicare, SUI, FUI: ~10% = $38.50/hr
+ Workers' Comp (construction class ~15-20%): $42-46/hr
+ General liability allocation (~5%): $44-48/hr
+ Health insurance, vacation, sick pay (~15-20%): $50-55/hr
+ Non-productive time (travel, cleanup, meetings ~15%): $58-64/hr
+ Equipment usage, small tools, truck: $63-70/hr
+ Supervisory overhead allocation: $70-80/hr

**Loaded labor rate = ~2-2.3× base pay rate.** Without understanding this, you'll lose money every day.

### Material markup:
- Most materials: 10-15% markup on cost (Owl Tower handling, storage, delivery)
- Large items (cabinets, appliances): 10-15%
- High-volume materials (lumber, concrete): 5-10% или sometimes pass-through
- Specialty items: 15-25% (rare, risky to stock)
- **Be transparent в proposal** — clients resent finding markup "hidden"

### Sub markup:
- **5-10% standard** on sub costs
- Covers Owl Tower coordination time, insurance burden, warranty backstop
- **Some owners negotiate pure pass-through** — if so, charge separately для PM time
- **Don't undercut** — sub markup is real cost, not extra profit

## Subcontractor Bid Solicitation

### Timing:
- Start sub solicitation 2-3 weeks before bid due (complex projects 4+)
- Simple scopes — 1 week OK
- Give subs 5-10 days minimum для their estimate

### Scope packages to subs:
- Include relevant drawings (not all 100 sheets — just what applies to their scope)
- Written scope (2-3 pages typical)
- Schedule requirements
- Special requirements (prevailing wage, bonding, etc.)
- Bid format required (lump sum vs unit price)
- Due date + time
- Owl Tower contact info

### Best practices:
- Use **ITB (Invitation to Bid)** format — consistent
- Minimum 3 quotes per scope
- Pre-qualified subs preferred (see `sub-prequal` skill)
- **Never share other sub's pricing** — destroys trust, creates collusion risk
- **Bid leveling** — compare subs on same scope basis, not apples to oranges

### Common sub bid issues:
- Incomplete scope (sub misses something — risk of scope gap)
- Exclusions to watch (permits, overtime, hoisting, hazmat)
- Unit pricing vs lump sum clarity
- Labor burden assumptions
- Material escalation clauses (common 2022-2024 due to inflation)

### Bid leveling exercise:
Build spreadsheet with each sub's bid broken down to apples-apples. Typical columns:
- Scope item
- Sub A price
- Sub B price
- Sub C price
- Low bid
- Spread (low vs high)
- Notes (what drives difference)

High spread (>30%) = one sub missed scope. Clarify before relying on low.

## General Conditions (GCs) / Project Overhead

GCs = project-specific overhead (labor, equipment, services) that don't fit in direct trade costs. Typical items:

### Personnel:
- Project Manager (% time allocated to this project)
- Superintendent (full-time or % time)
- Laborer / cleanup
- Safety coordinator (if on-staff)

### Temporary facilities:
- Site trailer rental ($200-800/month)
- Portable restroom ($150-300/month)
- Temporary power ($500-2,000 setup)
- Temporary water
- Temporary fence
- Dumpster (per pickup, varies by size)

### Communication/tech:
- CompanyCam / BuilderTrend / project software subscription (allocated)
- Phone, internet
- Printing, postage

### Safety:
- PPE for laborers (allocated)
- First aid supplies
- Safety training (project-specific)

### Small tools / consumables:
- Nails, fasteners, blades, tape, etc.
- Allocated per job (typically 1-3% of labor cost)

### Insurance specific:
- Project-specific insurance (builders risk, performance bond) if required

### Permits & fees:
- Building permit (owner usually pays, but Owl Tower fronts sometimes)
- Plan check
- Grading / development impact fees
- Special inspections / deputy inspector fees (owner sometimes pays)
- Utility connection fees

### GCs calculation:
- **Duration-based:** many items are monthly (trailer, portapotty) × project duration
- **Event-based:** some are per-occurrence (move-in, cleanup, final)
- **% of direct cost:** typically 8-15% of direct cost on smaller projects; 5-10% on larger

## Contingency — The Buffer You Hope to Not Use

**Contingency** = buffer for unknowns разных types:

### Types of contingency:
1. **Design contingency** — drawings may have gaps; design errors discovered during construction
2. **Estimating contingency** — prices may drift from estimate by bid day
3. **Construction contingency** — unforeseen site conditions, changed conditions
4. **Schedule contingency** — weather, supply chain, labor disruption

### Typical values:
- **New construction, clear drawings, known site:** 3-5%
- **Residential remodel, existing building unknowns:** 10-20%
- **Commercial TI, existing building:** 8-15%
- **Demolition-heavy:** higher — lots of unknowns
- **Complete CDs with known subs:** lower — less risk

### How to present contingency:
- **Internal cushion** — add to bid price, don't show to client
- **Allowance line item** — transparent "allowance for unforeseen conditions, reconciled at close"
- **Change order basis** — no allowance in bid, changes via formal CO (riskier для you)

### Hybrid approach (recommended):
- Small internal cushion (2-3%) for real unknowns
- Explicit allowance items for specific expected-unknowns (e.g., "rotted subfloor replacement up to 200 sf allowance")
- Clear CO process для scope additions

## Overhead & Profit (OH&P) Markup

### Company overhead:
Fixed costs to run Owl Tower regardless of any specific job:
- Office rent ($X/mo Torrance)
- Admin salaries (Evgeniy, bookkeeper, admin)
- Insurance (policies not allocated to job)
- Vehicles / fleet
- Marketing
- Software subscriptions
- Utilities, accounting, legal

**Annual overhead** ÷ **annual revenue** = overhead percentage.

Example: $680K annual overhead on $3.4M revenue = 20% overhead rate.

Every job must carry its share of that 20% OR company loses money.

### Profit:
What Owl Tower keeps AFTER covering all costs и overhead.

Typical profit targets:
- **Net profit 5-10%** typical GC industry
- **Net profit 10-15%** achievable для quality GC with good project mix
- **Net profit 15-20%** rare, only sustained с premium positioning + efficiency

### Markup application:

**Method 1: Simple markup on direct cost**
- Direct cost (labor + material + sub + GCs): $500K
- Markup 25% (covers 20% overhead + 5% profit): $125K
- **Bid: $625K**

**Method 2: Overhead as % of revenue, separate profit**
- Direct: $500K
- Overhead at 20% of total bid: divide $500K by 0.75 (since overhead + profit = 25%): = $667K subtotal
- Add profit 10%: **Bid $733K**

**Method 2 is mathematically more accurate.** Simple markup undercalculates on higher-overhead jobs.

### Competitive adjustments:
- Market rates — если competitors bid 15% markup, you can't always hit 25%
- Some jobs you bid tighter для strategic reasons (entry client, portfolio project)
- Some jobs you bid higher because you don't really want them (but would do if client desperate)

## Exclusions & Assumptions — CYA Language

**Exclusions** = what is NOT in your bid. Critical для protecting margin.

### Standard Owl Tower exclusions:
1. Permit fees (unless specifically included)
2. Testing & special inspection fees
3. Bonds (performance, payment) unless specified
4. Hazardous material abatement (unless specifically scoped with allowance)
5. Site survey
6. Geotechnical report
7. Existing utility locate beyond Blue Stakes/811
8. Overtime or accelerated schedule not in base
9. Work beyond normal 7am-5pm weekdays
10. Storage of owner-provided materials
11. Unknown conditions behind walls, under floors, in attics
12. Mold, lead, asbestos remediation
13. Pre-existing code violations (non-compliant existing work being kept)
14. Design changes after contract
15. Items not specifically shown on drawings or described in specs
16. Owner-provided items installation (unless labor included)
17. Utility hookup fees
18. Dewatering beyond minor pumping
19. Tree removal (unless specified)
20. Extraordinary site protection (beyond normal)

### Assumptions (what your bid assumes to be true):
- Plans provided are complete and accurate
- Site is accessible during normal work hours
- Utilities at site to supports construction needs
- Owner will provide decisions on selections per schedule
- No work stoppage due to owner delay
- Permits issued within standard timeframe after submittal
- Materials available at current market prices
- No prevailing wage requirement (if not public work)
- Normal weather for the season

### Strong exclusion language:
"This proposal excludes all items not specifically listed in the Scope of Work. Owner acknowledges that items not explicitly included are to be provided by Owner, a separate contractor, or subject to separate Change Order. In the event of discrepancy between plans and specifications and this Scope of Work, the Scope of Work governs pricing."

## Proposal Structure

### Sections (in order):
1. **Cover page** — Owl Tower brand, project name, client, date
2. **Introduction** — brief thank-you, project understanding
3. **Scope of Work** — detailed description of what's included
4. **Pricing** — lump sum or unit price, clearly stated
5. **Exclusions** — what's NOT included
6. **Assumptions**
7. **Schedule** — estimated duration + milestones
8. **Payment Terms** — schedule of values, progress billing, retention
9. **Warranty** — 1 year standard, extended where applicable
10. **Validity period** — proposal valid for 30 days
11. **Qualifications / credentials** — CSLB license, insurance, years in business, relevant projects
12. **Signatures** — acceptance block
13. **Exhibits** — plan pages, spec sheets, alternate pricing if applicable

### Tone:
- Professional but not cold
- Confident but not cocky
- Specific but not overwhelming

### Format:
- Owl Tower branded (yellow #F5C400 accents on black #1A1A1A, Courier New font)
- PDF delivery preferred
- Max 10 pages for most bids (supplemental technical docs as exhibits)

## Bid Day Protocols

### Timing (for formal bid submission):
- **Day before:** finalize all sub quotes, pricing
- **Morning of:** assemble final numbers, second review
- **2 hours before:** print, sign, seal (if required)
- **1 hour before:** check in at bid location (if in-person)
- **Bid opening:** attend if public bid, record competitors

### Last-minute adjustments:
- Common: sub bids come in last-minute, need recalculation
- Have someone dedicated к math — can't do this alone on complex bid
- **Double check total before submitting** — most costly bid errors happen in final hour

### After loss:
- Request bid tabulation (public work) — see winning bid and yours
- Analyze: where did we miss? Scope gap? Markup too high? Labor rate assumption?
- Update unit cost library based on learnings
- Don't chase to match low bid — might have been bid error

### After win:
- Celebrate briefly
- Immediately start pre-construction mobilization
- Schedule client kickoff меeting within 1 week
- Convert estimate into **production budget** — different document, used during project to track actual vs estimated

## Tracking Bid-to-Award Ratio

Key performance metric. Industry typical:
- **Public bid (open competition):** 10-15% win rate
- **Invited bid (3-5 contractors):** 25-40% win rate
- **Negotiated / relationship:** 60-80% win rate
- **Design-build:** 50-75% win rate

If winning every bid — pricing too low. If winning <5% — pricing too high OR wrong market.

### Track in spreadsheet / CRM:
- Date bid
- Client
- Project type
- Value
- Status (pending, won, lost, no decision)
- Reason won/lost
- Competitors
- Learnings

Analyze quarterly. Adjust strategy based on data.

## Common Bid Mistakes

1. **Overly optimistic labor productivity** — "we can do that in 2 days" when 4 realistic
2. **Missing scope** — scope gap = change order rejection → margin loss
3. **Sub bid used без review** — sub missed scope, GC carries the gap
4. **Material escalation ignored** — lumber / steel / copper pricing volatile 2022-2024
5. **General conditions undercalculated** — duration longer than estimated, GCs blow out
6. **Site conditions assumed** — unforeseen excavation, demo, access issues
7. **Permit timing assumed** — bid assumed 30-day permit, actual 90 days = GC extension
8. **Weather / seasonal adjustments missed** — rainy season in CA, summer heat productivity drops
9. **Markup set by rule of thumb, not actual overhead rate** — undercharging на lower-volume years
10. **Not including ALL exclusions** — client expects and demands item not in scope

## Estimating Team Structure (Scaling Roadmap)

**Current ($3.4M):** Owner (Evgeniy) или superintendent does estimating — single-threaded, bottleneck

**$5-10M:** dedicated estimator (1 person, all scopes)

**$10-25M:** estimating lead + 1-2 estimators specialized (residential / commercial)

**$25M+:** estimating department with specialty estimators (civil, structural, MEP, finishes), chief estimator, integration with project management software

### Software progression:
- **$0-5M:** Excel templates, PlanSwift or Bluebeam for takeoff
- **$5-15M:** Dedicated estimating software (ProEst, STACK, Sage Estimating)
- **$15M+:** Integrated with project management / accounting (Procore, BuilderTrend full suite, Viewpoint)

## Ссылки / standards

- **RS Means** — industry cost data (annual publication)
- **Craftsman Book Company** — detailed unit cost databases
- **National Association of Home Builders (NAHB)** — residential costing
- **AGC (Associated General Contractors)** — industry benchmarks
- **California Department of Industrial Relations** — prevailing wage determinations
- **CA Business & Professions Code §7159** — Home Improvement Contract requirements (Owl Tower contracts must comply)
- **Cal. Civil Code §7151** — Service + Repair Contract requirements (under $750 scope)

## Шаблоны (папка templates/)

- `bid-no-bid-qualification-form.md`
- `proposal-master-template.md` (Owl Tower branded, full-form)
- `proposal-short-form.md` (repair / small scope)
- `scope-of-work-template.md`
- `exclusions-assumptions-master-list.md`
- `invitation-to-bid-sub.md`
- `sub-bid-leveling-template.xlsx (or .md)`
- `general-conditions-worksheet.md`
- `unit-cost-library-template.xlsx`
- `bid-tracking-log.xlsx`
- `schedule-of-values-template.xlsx`

## Референсы (папка references/)

- `labor-productivity-rates-residential.md`
- `labor-productivity-rates-commercial.md`
- `loaded-labor-rate-calculation.md`
- `markup-calculation-examples.md`
- `contingency-guidelines-by-project-type.md`
- `common-bid-errors-to-avoid.md`
- `owl-tower-unit-cost-library.md` (internal — populated over time)
- `claude-estimator-construction.md` — book-derived unit costs, LA latest-month (Claude Estimator Construction; data in `cost-db/data/books/rsmeans_bcc_2022/`)

## Важное правило

Estimating — fundamentally risk management. Too high = no work. Too low = work that loses money. Winning bids should generate profit, not just revenue. Invest in estimating system accuracy — it compounds with every job. At $3M scale, estimating errors are painful; at $50M scale, they're fatal. Build the system now before scale forces it.
