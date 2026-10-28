# F&B equipment - published web prices (Hollywood Comedy Club, 6263 Hollywood Blvd)

Companion to `equipment_web_prices.csv` (98 rows, one per row of `equipment.csv`). Prices were collected on 2026-10-28 from public US foodservice-dealer and manufacturer product pages so that Owl Tower Construction Group can carry documented numbers until dealer quotes arrive. Nothing here is a quote.

## 1. What the numbers are and are not

- **Freight, sales tax, uncrating, installation, final connections, start-up and warranty registration are NOT included in any price.** The dealer pages price the bare unit, FOB their warehouse or the factory; several pages add a freight line ($50-$100 at BakedECO) or a packing fee ($15 at ACityDiscount for FE-95). Options and accessories (casters, quick-disconnect hoses, stacking kits, boosters, faucets, soda manifolds, shelf posts) are not included unless the page bundles them.
- `price_usd` is exactly the figure the cited page shows for the exact model string (or the exact cut-sheet variant, named in `matched_model`); nothing was estimated, averaged or extrapolated. Where a page shows a crossed-out list price next to the selling price, the selling price is carried and the list price is in `notes`.
- `price_kind`: `dealer_price` = a US dealer's published selling price; `msrp` = the manufacturer's own published price (only FE-22 Big Dipper, carried per the rule that a manufacturer price wins over dealers when both exist - the dealer prices are in `notes`); `variant` = only a close variant is published (FE-75 / FE-104 Everpure).
- One source per row; where a second source differs it is in `notes`. Dealers were taken in this order where they carried the exact model: WebstaurantStore, KaTom, RestaurantSupply.com, CKitchen, Central Restaurant Products, ACityDiscount, then other US dealers (GoFoodservice, Kitchen Restock, Chefbuyer, Culinary Depot, Amechef, The Restaurant Warehouse, Fresh Water Systems).
- **How the pages were read.** The session's network policy refused direct HTTPS connections to every dealer and manufacturer host (403 on CONNECT for webstaurantstore.com, katom.com, restaurantsupply.com, acitydiscount.com, ckitchen.com, centralrestaurant.com, culinarydepotinc.com, gofoodservice.com, chefsnj.com, big-dipper.com, media.htpg.com, perlick.com and others), so no product page could be loaded in full. Each price, model string and crossed-out list price was taken from the search engine's indexed text of the cited product URL (the `url` column), which quotes the page's price block. That index can lag the live page by days to weeks, and dealer prices change often - the cited URL is the thing to open before the number is relied on. Two pages carried stale 'manufacturer price increase' banners (FE-69 Jan 1 2026, FE-98 Feb 16 2026), which suggests the index predates those increases.
- `date_checked` is the date the search was run (2026-10-28), not the date the dealer last changed the page.

## 2. Counts

| status | rows |
|---|---|
| priced at the exact model or exact cut-sheet variant (`dealer_price` / `msrp`) | 50 |
| priced at a close variant (`variant`) | 2 |
| quote required (custom stainless, walk-in, hoods/fans/fire, Russell A2L refrigeration, placeholder models, no manufacturer, no price published) | 30 |
| owner-furnished / existing / vendor-furnished - skipped | 16 |
| total | 98 |

Sum of `extended_usd` over the 52 priced rows: **$142,546.45** (equipment only, before freight, tax, options and installation).

## 3. Extended totals by category (grouping as in `equipment_notes.md` section 3)

| category | rows priced | sum of extended_usd | quote required (item nos.) | owner / existing / vendor (item nos.) |
|---|---|---|---|---|
| Cooking (11 44 00) | 10 | 53,380.48 | 40 | 46 |
| Refrigeration, self-contained (11 41 00 part) | 10 | 32,043.50 | - | - |
| Walk-ins and remote refrigeration (11 41 00 part) | 0 | 0.00 | 7, 8, 9.1, 9.2, 11, 12 | - |
| Shelving / storage (11 41 00 part) | 3 | 3,036.19 | 1, 10, 13, 36 | - |
| Hoods, fans, fire system (23 38 13 / 21 23 00) | 0 | 0.00 | 55, 56.1, 56.2, 57, 58, 97 | - |
| Dish / scullery / sinks / faucets (11 48 00) | 13 | 20,434.51 | 94, 100, 101 | - |
| Prep tables, work counters, slicer, mixer, processor (11 42 00) | 4 | 6,664.78 | 16, 33, 34, 38, 39, 41 | 6, 17 |
| Bar (11 46 00) | 8 | 18,961.33 | 61, 84, 103 | 64, 80, 81, 82, 83 |
| Ice (11 47 00) | 4 | 8,025.66 | - | 73, 74, 76, 77 |
| Other | 0 | 0.00 | 102 | 2, 14, 68, 68.1 |
| **total** | **52** | **$142,546.45** | | |

Two lines move the Cooking total materially and are flagged in the CSV: FE-27 Ovention S1200 is priced as ONE oven ($17,730.89) although K2.0 says DOUBLE STACK (two decks, two circuits) - if the consultant confirms two ovens (query 10) add $17,730.89 plus the stacking kit; FE-98 CMA 180-C is the no-booster machine ($10,992.00) while K0.0 note U calls for a 180 F booster (CMA-180CB about $11,306.00, query 9).

## 4. Largest priced lines

| item | description | matched model | qty | unit price | extended |
|---|---|---|---|---|---|
| FE-27 | CONVEYOR OVEN (VENTLE[SS]) (description clipped on K2.0) | Ovention SHUTTLE S1200 | 1 | $17,730.89 | $17,730.89 |
| FE-28 | HEATED CABINET | Cres Cor H135WSUA11 | 3 | $4,418.00 | $13,254.00 |
| FE-98 | DISHMACHINE | CMA Dishmachines 180-C | 1 | $10,992.00 | $10,992.00 |
| FE-65 | ICE BIN (underbar ice chest with cold plate) | Perlick TSD30IC10 | 3 | $2,763.75 | $8,291.25 |
| FE-47 | 6 O.B. RANGE W/CONV. OV[EN] (description clipped on K2.0) | Imperial IR-6-C | 1 | $6,611.00 | $6,611.00 |
| FE-78 | SLIDING DOOR REFRIGERA[TOR] (description clipped on K2.0) | Atosa MCF8727GR | 2 | $2,934.00 | $5,868.00 |
| FE-54 | FRY DUMP (crisp 'n hold) | Carter-Hoffmann CNH18 | 1 | $5,096.85 | $5,096.85 |
| FE-22 | GREASE INTERCEPTOR (automatic, point source) | Big Dipper W-350-IS | 1 | $4,344.00 | $4,344.00 |
| FE-105 | ICE MACHINE (2nd level service) | Hoshizaki KM-520MAJ | 1 | $4,280.00 | $4,280.00 |
| FE-25 | REFRIGERATED PIZZA TAB[LE] (description clipped on K2.0) | Atosa MPF8202GR | 1 | $3,792.00 | $3,792.00 |
| FE-50 | REFRIGERATED STAND (chef base, 72 in) | Atosa MGF8453GR | 1 | $3,304.00 | $3,304.00 |
| FE-37 | REFRIGERATED TABLE (sandwich/salad, 3 door) | Atosa MSF8304GR | 1 | $3,140.00 | $3,140.00 |

## 5. Largest unpriced (quote required) items

- FE-7 / FE-11 walk-in cooler + freezer box (Arctic Q228534, combined box 13'-3" x 7'-8" with freezer floor, doors, lights, accessories) - refrigeration/walk-in contractor quote.
- FE-8, FE-9.1, FE-9.2, FE-12 Russell R-454A evaporator coils and outdoor condensing units with A2L leak detection, valves, controls - refrigeration contractor quote (nothing published for the A2L models; the Russell March 2025 price book that search results quote covers the older RL6A series only).
- FE-56.1, FE-56.2, FE-97 CaptiveAire hoods (18'-3" Type I in two sections + 3'-6" Type II), FE-57 exhaust/MUA fan lot (models not in the K package), FE-55 fire suppression system - hood / mechanical / fire contractor quotes.
- 12 custom stainless lines (FE-16, 33, 34, 38, 39, 41, 58, 61, 84, 94, 100, 101) - fabricator quote; no dimensions on the K-sheets.
- FE-40 Wells TMPT hot food well - no dealer publishes a price for this model; FE-102 RDH132WUT-HHS - no manufacturer; FE-103 2nd-level soda system - no make/model; FE-1, FE-10, FE-13, FE-36 Metro shelving placeholders (per-shelf prices for the cut-sheet shelves are in `notes`, but posts and unit counts are undefined).

## 6. Rows where the web model differs from the K2.0 schedule string

| item | K2.0 model | model priced on the web | why |
|---|---|---|---|
| FE-45 | RATIONAL R295-CL | Rational art. 1900.1150US (Rational's sell sheet pairs the R295-CL name with this part) | cut sheet shows R295-CLX = 1900.1158US (10 gpm / 108,000 gal vs 5 gpm / 60,000 gal); RestaurantSupply $1,596.43 for the CLX kit - query 7 |
| FE-51 | ATOSA ATTG-36 | ATTG-36 NG | dealer sells the gas type as a suffix; NG assumed from K2.0 gas schedule |
| FE-52 | ATOSA ATFS-40 | ATFS-40 NG | cut sheet names the Energy Star ATFS-40ES-NG; Keg Outlet lists ATFS-40ES at the same $1,068.00 |
| FE-53 | TRUE TWT-27F-HC | TWT-27F-HC right-hinge (KaTom 598-TWT27F) | hinge side is an order option, same price for LH |
| FE-63 | PERLICK TSF18DS | TSF18DS-TR (cut-sheet variant with trash chute) | no dealer lists TSF18DS without -TR; TS18DS is the shallower TS series - query 7 |
| FE-67 | PERLICK TSD21 | TSD21 (embossed top) | cut sheet shows TSF21DB (pitched top, full depth) at RestaurantSupply $1,104.95; a dealer notes TSF21DB replaces TSD21 - query 7 |
| FE-75 / FE-104 | EVERPURE EV9329-52 | EV977132 High Flow CSR Twin-7CLM+ (dealer lists EV9329-52 as alternate part no.) - `variant` | K2.0 part is the chloramine 7CLM twin, superseded; cut sheet shows EV9329-72 High Flow CSR Twin 7FC (CKitchen $1,093.68) - query 7 |
| FE-105 | HOSHIZAKI KM-520MAJ | KM-520MAJ (US 115 V) | cut sheet in the book is the KM-520MAJ-E 220-240 V export model - priced the US unit as scheduled |
| FE-28 | CRESCOR H-135-WSUA-11 | H135WSUA11 (same model, dealer spelling) | WebstaurantStore carries only the Dutch-door H-135-WUA-11 at $4,248.00 |
| FE-35 | HATCO GRAH-48D3 | GRAH-48D3 (voltage chosen at order) | WebstaurantStore's 208 V / 2,200 W toggle configuration (413GAH48D3TB) is the same $767.25 |
| FE-22 | BIG DIPPER W-350-IS | W-350-IS | priced at the manufacturer's page ($4,344.00) per the MSRP rule; WebstaurantStore $3,589.00 |
| FE-1 / FE-36 | METRO MQ21XXQ / 14XXFG (placeholders) | not priced; cut-sheet shelves MQ2148G $92.00 and 1436FG $86.00 per shelf noted | posts and unit counts undefined |

## 7. Other flags carried in the CSV notes

- FE-29 GSW WT-PB3060: ACityDiscount shows $575.64 on the canonical URL and $473.34 on a second URL for the same SKU 76673 - confirm; RestaurantSupply $1,028.35.
- FE-62 Perlick TS90LIC (KaTom) and FE-18 Robot Coupe CL50E (KaTom) pages carry 'call for details / log in for your price' beside the published price.
- FE-65 / FE-69 Perlick pages state 2-3 week lead times; FE-35 WebstaurantStore 208 V configuration out of stock; FE-78 Top Jet shows the MCF8727GR as out of stock / discontinued (other dealers list it).
- FE-66 Perlick TSF4SGB is the housing only; soda manifold, gun and drip cup are by the soda vendor (items 80/81).
- FE-19 mop sink, FE-31/93 hand sinks, FE-88 three-compartment sink: faucets are separate lines (FE-20, FE-90, FE-91); hand-sink faucets for 31/93 are not scheduled at all.
- Atosa and Perlick dealer prices vary 15-30% between dealers on the same day (MAP vs list); the `notes` column lists the second and third dealer prices seen so the spread is visible.
