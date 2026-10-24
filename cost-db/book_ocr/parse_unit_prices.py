#!/usr/bin/env python3
"""Parse the unit-price pages of the OCR'd 2022 cost book into rows, using THREE independent readings of every number and the
table's own arithmetic to settle doubtful cells:

  T  tesseract word boxes (ocr/pNNNN.tsv)            digits + punctuation as recognised
  I  the scan's own text layer (ia/pNNNN.json)       a second OCR engine's reading
  G  geometry of the cell on the page image          number of digit glyphs and the position of the decimal point / commas
                                                     (OCR engines drop a leading point far more often than they misread a digit)

  python3 -I parse_unit_prices.py <book_dir> <out_dir> <first_pdf_page> <last_pdf_page> [--crews crews_2022_totals.csv]

<book_dir> holds parts/ (the PDF parts, named rsmeans_partNN_pAAAA-BBBB.pdf), ocr/ and ia/.
Per page: header row -> column centres -> every row is a section title, a division header or a data line.
Per data line: line number, description (with its indentation for the hierarchy), crew, daily output, labor-hours, unit,
material, labor, equipment, total, total incl. O&P. For each numeric cell the candidate values of the three readings are
combined and the combination that satisfies  total = material + labor + equipment  and  output x labor-hours = crew
labor-hours per day (a multiple of 8, or the crew's known value)  is kept. What no combination settles stays None and is
flagged. Nothing is typed in by hand.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

import numpy as np
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cellgeom import analyse  # noqa: E402

HEADERS = ("Crew", "Output", "Hours", "Unit", "Material", "Labor", "Equipment", "Total", "Incl")
COLS = ["crew", "output", "hours", "unit", "material", "labor", "equipment", "total", "total_op"]
NUM_COLS = ("output", "hours", "material", "labor", "equipment", "total", "total_op")
MONEY = ("material", "labor", "equipment", "total", "total_op")
LINE_RE = re.compile(r"^\d{4}$")
VALID_DIVS = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "21", "22", "23", "25", "26", "27", "28",
              "31", "32", "33", "34", "35", "41", "44", "46", "48"}
REF_RE = re.compile(r"^R\d{6}-\d{2}")
JUNK_RE = re.compile(r"^[|:;.,'‘’`\"~=_\-—–*°)(\]\[}{!]+$")
OCR_DIGIT_FIX = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "|": "1", "S": "5", "B": "8", "Z": "2", "D": "0", "G": "6"})
TRADES = {"skwk", "clab", "asbe", "boil", "bric", "brhe", "carp", "cefi", "elec", "elev", "eqhv", "eqmd", "eqlt", "eqol", "eqmm", "glaz", "lath",
          "marb", "mill", "mstz", "pord", "psst", "pape", "pile", "plas", "plah", "plum", "rodm", "rofc", "rots", "rohe", "shee", "spri", "stpi",
          "ston", "sswk", "tilf", "tilh", "trlt", "trhv", "sswl", "wrck", "swk", "clam", "pile", "bric", "carp"}
UNIT_TABLE = {"SF": "S.F.", "SY": "S.Y.", "LF": "L.F.", "CF": "C.F.", "CY": "C.Y.", "EA": "Ea.", "JOB": "Job", "HR": "Hr.", "DAY": "Day",
              "WEEK": "Week", "WK": "Week", "MONTH": "Month", "MO": "Month", "TON": "Ton", "LB": "Lb.", "GAL": "Gal.", "MSF": "M.S.F.", "MLF": "M.L.F.",
              "CLF": "C.L.F.", "CSF": "C.S.F.", "SQ": "Sq.", "M": "M", "%": "%", "SET": "Set", "PR": "Pr.", "OPNG": "Opng.", "FLIGHT": "Flight",
              "FLT": "Flight", "RISER": "Riser", "PAIR": "Pair", "MILE": "Mile", "MI": "Mile", "VLF": "V.L.F.", "MBF": "M.B.F.", "PC": "Pc.", "PT": "Pt.",
              "QT": "Qt.", "CWT": "Cwt.", "CORD": "Cord", "BAG": "Bag", "ROLL": "Roll", "KIT": "Kit", "CASE": "Case", "SHEET": "Sheet", "BOX": "Box",
              "TOTAL": "Total", "INCH": "Inch", "IN": "Inch", "SFCA": "SFCA", "BF": "B.F.", "STORY": "Story", "ROOM": "Room", "FLOOR": "Floor",
              "ACRE": "Acre", "LOAD": "Load", "TRIP": "Trip", "UNIT": "Unit", "HOUR": "Hr.", "SYST": "System", "SYSTEM": "System", "OUTLET": "Outlet",
              "FIXT": "Fixt.", "GALLON": "Gal.", "YEAR": "Year", "YR": "Year", "PERSON": "Person", "KW": "kW", "HP": "H.P.", "LBS": "Lb.", "TONS": "Ton",
              "EACH": "Ea.", "VERT": "V.L.F.", "SQFT": "S.F.", "LNFT": "L.F.", "CUYD": "C.Y.", "DRUM": "Drum", "CAN": "Can", "BUNDLE": "Bundle",
              "BDL": "Bundle", "CARTON": "Carton", "PKG": "Pkg.", "SPAN": "Span", "SEAT": "Seat", "COURT": "Court", "LANE": "Lane", "BED": "Bed",
              "STALL": "Stall", "DOOR": "Door", "LEAF": "Leaf", "WINDOW": "Window", "VEHICLE": "Vehicle", "BAY": "Bay", "SPACE": "Space",
              "SE": "S.F.", "SR": "S.F.", "LE": "L.F.", "CE": "C.F.", "EO": "Ea.", "FA": "Ea.", "SYS": "System", "CSY": "C.S.Y."}


# ----------------------------------------------------------------------------------------------- loading
def load_tess(path: Path) -> tuple[int, int, list[dict]]:
    words, w, h = [], 0, 0
    with path.open(encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["level"] == "1":
                w, h = int(r["width"]), int(r["height"])
            if r["level"] != "5" or not r["text"].strip():
                continue
            x0, y0, ww, hh = int(r["left"]), int(r["top"]), int(r["width"]), int(r["height"])
            t = r["text"].strip()
            if JUNK_RE.fullmatch(t) or hh > 110 or ww < 3:      # column leaders, stray punctuation, vertical rules (titles are up to ~80 px tall)
                continue
            words.append({"x0": x0, "x1": x0 + ww, "y0": y0, "y1": y0 + hh, "t": t, "conf": float(r["conf"]), "src": "T"})
    return w, h, words


def load_ia(path: Path, w: int, h: int) -> list[dict]:
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for r in d["words"]:
        t = r["t"].strip()
        if t and not JUNK_RE.fullmatch(t) and (r["y1"] - r["y0"]) * h <= 110:
            out.append({"x0": int(r["x0"] * w), "x1": int(r["x1"] * w), "y0": int(r["y0"] * h), "y1": int(r["y1"] * h), "t": t, "conf": None, "src": "I"})
    return out


def rows_of(words: list[dict], tol: int) -> list[list[dict]]:
    """Cluster words into text rows: a word joins the current row when its vertical extent overlaps the row's by at least
    40% of its own height (or its centre is within `tol` px) - bold section titles are taller than the table text."""
    ws = sorted(words, key=lambda z: ((z["y0"] + z["y1"]) / 2, z["x0"]))
    rows: list[list[dict]] = []
    for z in ws:
        yc = (z["y0"] + z["y1"]) / 2
        if rows:
            r = rows[-1]
            ry0, ry1, ryc = r[-1]["_ry0"], r[-1]["_ry1"], r[-1]["_yc"]
            overlap = min(z["y1"], ry1) - max(z["y0"], ry0)
            if abs(yc - ryc) <= tol or overlap >= 0.4 * (z["y1"] - z["y0"]):
                n = len(r)
                z["_yc"] = (ryc * n + yc) / (n + 1)
                z["_ry0"] = (ry0 * n + z["y0"]) / (n + 1)
                z["_ry1"] = (ry1 * n + z["y1"]) / (n + 1)
                for t in r:
                    t["_yc"], t["_ry0"], t["_ry1"] = z["_yc"], z["_ry0"], z["_ry1"]
                r.append(z)
                continue
        z["_yc"], z["_ry0"], z["_ry1"] = yc, z["y0"], z["y1"]
        rows.append([z])
    for r in rows:
        r.sort(key=lambda z: z["x0"])
    return rows


class Parts:
    """pdf page -> rendered gray image (numpy), rendered on demand, one page cached."""

    def __init__(self, parts_dir: Path):
        self.map = {}
        for p in sorted(parts_dir.glob("*.pdf")):
            m = re.search(r"_p(\d{4})-(\d{4})\.pdf$", p.name)
            if m:
                self.map[(int(m.group(1)), int(m.group(2)))] = p
        self._doc = None
        self._doc_path = None
        self._cache: dict[int, np.ndarray] = {}

    def image(self, pdf_page: int, dpi: int = 360) -> Optional[np.ndarray]:
        if pdf_page in self._cache:
            return self._cache[pdf_page]
        for (a, b), path in self.map.items():
            if a <= pdf_page <= b:
                if self._doc_path != path:
                    self._doc = pymupdf.open(path)
                    self._doc_path = path
                pix = self._doc[pdf_page - a].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()
                self._cache = {pdf_page: img}
                return img
        return None


# ----------------------------------------------------------------------------------------------- header / columns
def find_header(rows: list[list[dict]]) -> Optional[dict]:
    best = None
    for i, r in enumerate(rows):
        toks = {}
        for z in r:
            t = z["t"].strip(".,:;|=~-_'\"")
            for hname in HEADERS:
                if t.lower().startswith(hname.lower()) and len(t) <= len(hname) + 3:
                    toks.setdefault(hname, (z["x0"] + z["x1"]) / 2)
        if len(toks) >= 5 and "Material" in toks and "Labor" in toks:
            if best is None or len(toks) > len(best[1]):
                best = (i, toks)
    if best is None:
        return None
    i, c = best
    c = dict(c)
    if "Equipment" not in c and "Labor" in c and "Total" in c:
        c["Equipment"] = (c["Labor"] + c["Total"]) / 2
    if "Total" not in c and "Equipment" in c and "Labor" in c:
        c["Total"] = c["Equipment"] + (c["Equipment"] - c["Labor"])
    if "Incl" not in c and "Total" in c and "Equipment" in c:
        c["Incl"] = c["Total"] + (c["Total"] - c["Equipment"]) * 1.0
    if "Unit" not in c and "Hours" in c and "Material" in c:
        c["Unit"] = (c["Hours"] + c["Material"]) / 2
    if "Hours" not in c and "Output" in c and "Unit" in c:
        c["Hours"] = (c["Output"] + c["Unit"]) / 2
    if "Output" not in c and "Crew" in c and "Hours" in c:
        c["Output"] = (c["Crew"] + c["Hours"]) / 2
    if "Crew" not in c and "Output" in c and "Hours" in c:
        c["Crew"] = c["Output"] - (c["Hours"] - c["Output"]) * 1.3
    need = ("Crew", "Output", "Hours", "Unit", "Material", "Labor", "Equipment", "Total", "Incl")
    if any(k not in c for k in need):
        return None
    order = [c[k] for k in need]
    if order != sorted(order):
        return None
    bounds = {}
    for j, k in enumerate(COLS):
        left = (order[j - 1] + order[j]) / 2 if j else order[0] - 95
        right = (order[j] + order[j + 1]) / 2 if j + 1 < len(order) else 10 ** 6
        bounds[k] = (left, right)
    return {"row": i, "centres": c, "bounds": bounds, "desc_end": order[0] - 95, "y": rows[i][0]["_yc"]}


def col_of(xc: float, bounds: dict) -> Optional[str]:
    for k, (l, r) in bounds.items():
        if l <= xc < r:
            return k
    return None


# ----------------------------------------------------------------------------------------------- numbers
def digits_of(t: str) -> str:
    return re.sub(r"[^0-9]", "", t.translate(OCR_DIGIT_FIX))


def clean_num(t: str) -> str:
    t = t.strip().strip("|:;'\"`‘’“”~=_-—–*°)(]}{[!").replace(" ", "")
    if not t:
        return ""
    s = re.sub(r"[^0-9.,]", "", t.translate(OCR_DIGIT_FIX))
    return s.strip(",")


def candidates(raw: str, kind: str) -> list[tuple[Decimal, str]]:
    """Possible values of one OCR token: (value, how). 'as_read' = the token had the point where it is; 'point_restored' = a
    plausible place for a point the OCR dropped."""
    s = clean_num(raw)
    if not s or not re.search(r"\d", s):
        return []
    out: list[tuple[Decimal, str]] = []
    try:
        if "." in s:
            whole, frac = s.rsplit(".", 1)
            whole = whole.replace(",", "")
            if not re.fullmatch(r"\d*", whole) or not re.fullmatch(r"\d+", frac):
                return []
            out.append((Decimal((whole or "0") + "." + frac), "as_read"))
        else:
            s2 = s.replace(",", "")
            if not re.fullmatch(r"\d+", s2):
                return []
            n = Decimal(s2)
            if kind == "hours":
                if len(s2) >= 3:
                    out.append((Decimal((s2[:-3] or "0") + "." + s2[-3:]), "point_restored"))
                else:
                    out.append((n, "as_read"))
            elif kind == "output":
                out.append((n, "as_read"))
                if len(s2) >= 3:
                    out.append((Decimal(s2[:-2] + "." + s2[-2:]), "point_restored"))
            else:
                out.append((n, "as_read"))
                if len(s2) >= 3:
                    out.append((Decimal(s2[:-2] + "." + s2[-2:]), "point_restored"))
                elif len(s2) == 2:
                    out.append((Decimal("0." + s2), "point_restored"))
    except Exception:
        return []
    seen: dict[Decimal, str] = {}
    for v, how in out:
        seen.setdefault(v, how)
    return list(seen.items())


def rstep(v: Decimal) -> Decimal:
    """Rounding step of a printed unit cost (the book rounds every cost above $5; steps inferred from the data)."""
    v = abs(v)
    if v <= 5:
        return Decimal("0.01")
    if v <= 20:
        return Decimal("0.05")
    if v <= 100:
        return Decimal("0.50")
    if v <= 300:
        return Decimal("1")
    if v <= 1000:
        return Decimal("5")
    if v <= 10000:
        return Decimal("25")
    if v <= 50000:
        return Decimal("100")
    return Decimal("500")


def book_round(v: Decimal) -> Decimal:
    st = rstep(v)
    return (v / st).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * st


# ----------------------------------------------------------------------------------------------- settle one row
WEIGHT = {("G", "as_read"): 3.0, ("T", "as_read"): 1.0, ("I", "as_read"): 1.0, ("T", "point_restored"): 0.25, ("I", "point_restored"): 0.25}


def weights(cands: list[tuple[Decimal, str, str]]) -> dict[Decimal, float]:
    w: dict[Decimal, float] = {}
    for v, how, src in cands:
        w[v] = w.get(v, 0.0) + WEIGHT.get((src, how), 0.0)
    return w


def settle(cands: dict[str, list], crew: Optional[dict]) -> tuple[dict, dict, list[str]]:
    flags: list[str] = []
    vals: dict[str, Optional[Decimal]] = {k: None for k in NUM_COLS}
    conf: dict[str, Optional[float]] = {k: None for k in NUM_COLS}
    W = {k: weights(cands[k]) for k in NUM_COLS}

    def opts(k):
        return sorted(W[k]) if W[k] else [None]

    # ---- money: the printed total is the exact sum of the printed components
    best, best_score, ties = None, None, 0
    for m in opts("material"):
        for l in opts("labor"):
            for e in opts("equipment"):
                for t in opts("total"):
                    parts = [x for x in (m, l, e) if x is not None]
                    if t is None or not parts or abs(sum(parts) - t) > Decimal("0.011"):
                        continue
                    score = sum(W[k].get(v, 0.0) for k, v in (("material", m), ("labor", l), ("equipment", e), ("total", t)) if v is not None)
                    if best_score is None or score > best_score + 1e-9:
                        best, best_score, ties = (m, l, e, t), score, 0
                    elif abs(score - best_score) <= 1e-9 and (m, l, e, t) != best:
                        ties += 1
    if best and ties == 0:
        vals["material"], vals["labor"], vals["equipment"], vals["total"] = best
        for k, v in zip(("material", "labor", "equipment", "total"), best):
            conf[k] = W[k].get(v) if v is not None else None
    else:
        if best:
            flags.append("MONEY_AMBIGUOUS")
        strong = {}
        for k in ("material", "labor", "equipment", "total"):
            good = sorted(((w, v) for v, w in W[k].items() if w >= 2.0), reverse=True)
            strong[k] = good[0][1] if good and (len(good) == 1 or good[0][0] > good[1][0]) else None
        derived = None
        if not best:
            # one cell printed but unreadable (candidates, none strong) while the others are strong: the sum defines it.
            # Cells with no reading at all are taken as blank; when two or more cells are in doubt nothing is derived.
            unresolved = [k for k in ("material", "labor", "equipment", "total") if W[k] and strong[k] is None]
            # only a cell that was printed but could not be read is derived; a cell no reading saw is taken as blank, except the
            # total, which the book prints whenever a component exists
            free = unresolved[0] if len(unresolved) == 1 else ("total" if not unresolved and not W["total"] else None)
            if free:
                others = {k: strong[k] for k in ("material", "labor", "equipment", "total") if k != free}
                if free == "total":
                    parts = [v for v in others.values() if v is not None]
                    val = sum(parts) if parts else None
                elif others["total"] is not None:
                    val = others["total"] - sum(v for k, v in others.items() if k != "total" and v is not None)
                    if val < 0:
                        val = None
                    elif val == 0:
                        val = Decimal(0)
                    elif val > 5 and val != book_round(val):
                        val = None                             # a printed component above $5 is always on the rounding grid
                else:
                    val = None
                if val is not None:
                    derived = (free, None if val == 0 else val, others)
        if derived not in (None, "ambiguous"):
            free, val, others = derived
            for k, v in others.items():
                vals[k], conf[k] = v, W[k].get(v)
            vals[free], conf[free] = val, None
            flags.append(f"{free.upper()}_DERIVED_FROM_SUM")
        else:
            if not best and any(W[k] for k in ("material", "labor", "equipment", "total")):
                flags.append("MONEY_UNSETTLED")
            for k in ("material", "labor", "equipment", "total"):
                vals[k] = strong[k]
                conf[k] = W[k].get(vals[k]) if vals[k] is not None else None
    # ---- output x hours = crew labor-hours per day
    lh_known = Decimal(str(crew["labor_hours_per_day"])) if crew and crew.get("labor_hours_per_day") else None
    best, best_score, ties = None, None, 0
    for o in opts("output"):
        for h in opts("hours"):
            if o is None or h is None or o <= 0 or h <= 0:
                continue
            prod = o * h
            if lh_known is not None:
                ok = abs(prod - lh_known) <= max(Decimal("0.02"), o * Decimal("0.0006") + Decimal("0.05"))
            else:
                k8 = (prod / 8).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                ok = 1 <= k8 <= 60 and abs(prod - 8 * k8) <= max(Decimal("0.02"), o * Decimal("0.0006") + Decimal("0.06"))
            if not ok:
                continue
            score = W["output"].get(o, 0.0) + W["hours"].get(h, 0.0)
            if best_score is None or score > best_score + 1e-9:
                best, best_score, ties = (o, h), score, 0
            elif abs(score - best_score) <= 1e-9 and (o, h) != best:
                ties += 1
    if best and ties == 0:
        vals["output"], vals["hours"] = best
        conf["output"], conf["hours"] = W["output"].get(best[0]), W["hours"].get(best[1])
    else:
        if best:
            flags.append("OUTPUT_HOURS_AMBIGUOUS")
        strong = {}
        for k in ("output", "hours"):
            good = sorted(((w, v) for v, w in W[k].items() if w >= 2.0), reverse=True)
            strong[k] = good[0][1] if good and (len(good) == 1 or good[0][0] > good[1][0]) else None
        done = False
        if not best and lh_known is not None:
            # labor-hours = crew labor-hours / daily output by definition: one strong value defines the other
            if strong["output"] and strong["output"] > 0:
                vals["output"], conf["output"] = strong["output"], W["output"].get(strong["output"])
                vals["hours"] = (lh_known / strong["output"]).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                flags.append("HOURS_DERIVED_FROM_CREW")
                done = True
            elif strong["hours"] and strong["hours"] > 0:
                vals["hours"], conf["hours"] = strong["hours"], W["hours"].get(strong["hours"])
                o = lh_known / strong["hours"]
                vals["output"] = o.quantize(Decimal("1")) if abs(o - o.quantize(Decimal("1"))) < Decimal("0.02") * o else o.quantize(Decimal("0.01"))
                flags.append("OUTPUT_DERIVED_FROM_CREW")
                done = True
        if not done:
            if not best and (W["output"] or W["hours"]):
                flags.append("OUTPUT_HOURS_UNSETTLED")
            for k in ("output", "hours"):
                vals[k] = strong[k]
                conf[k] = W[k].get(vals[k]) if vals[k] is not None else None
    # ---- crew arithmetic checks on the settled values
    if crew and vals["labor"] is not None and crew.get("bare_labor_daily") is not None and vals["labor"] > 0:
        daily = Decimal(str(crew["bare_labor_daily"]))
        ok = vals["output"] is not None and abs(book_round(daily / vals["output"]) - vals["labor"]) <= rstep(vals["labor"])
        if not ok:
            # the printed labor cost is crew daily cost / output: find the output reading (any source) that reproduces it
            alts = [o for o in opts("output") if o and o > 0 and abs(book_round(daily / o) - vals["labor"]) <= rstep(vals["labor"])]
            if len(alts) == 1 and (lh_known is None or vals["hours"] is None or abs(alts[0] * vals["hours"] - lh_known) <= Decimal("0.1")):
                vals["output"], conf["output"] = alts[0], W["output"].get(alts[0])
                if lh_known is not None:
                    vals["hours"] = (lh_known / alts[0]).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                flags.append("OUTPUT_FROM_LABOR_CHECK")
                flags[:] = [f for f in flags if f not in ("OUTPUT_HOURS_UNSETTLED", "OUTPUT_HOURS_AMBIGUOUS", "HOURS_DERIVED_FROM_CREW")]
            else:
                flags.append("LABOR_CREW_MISMATCH")
    # the crew says whether an equipment cost exists at all; with labor confirmed, a total that does not add up pins the material
    if crew and crew.get("bare_labor_daily") is not None and vals["labor"] is not None and vals["output"] and vals["total"] is not None \
            and "LABOR_CREW_MISMATCH" not in flags and (crew.get("bare_equip_daily") or 0) == 0 and conf.get("total", 0) and conf["total"] >= 2.0:
        m = vals["total"] - vals["labor"]
        if vals["equipment"] is not None or (vals["material"] is not None and vals["material"] != m) or (vals["material"] is None and m > 0):
            if m >= 0 and (m <= 5 or m == book_round(m)):
                vals["material"], conf["material"], vals["equipment"], conf["equipment"] = (m if m > 0 else None), None, None, None
                flags[:] = [f for f in flags if f not in ("MONEY_UNSETTLED", "MONEY_AMBIGUOUS", "EQUIPMENT_DERIVED_FROM_SUM", "MATERIAL_DERIVED_FROM_SUM")]
                flags.append("MATERIAL_DERIVED_FROM_CREW_SUM")
    if crew and vals["output"] and vals["equipment"] is not None and crew.get("bare_equip_daily") is not None:
        exp = book_round(Decimal(str(crew["bare_equip_daily"])) / vals["output"])
        if abs(exp - vals["equipment"]) > rstep(exp):
            flags.append("EQUIP_CREW_MISMATCH")
    # ---- total incl O&P: often cut by the scan edge on right-hand pages; keep a strong reading only, plausibility-checked
    good = sorted(((w, v) for v, w in W["total_op"].items()), reverse=True)
    if good and good[0][0] >= 2.0 and (len(good) == 1 or good[0][0] > good[1][0]):
        vals["total_op"], conf["total_op"] = good[0][1], good[0][0]
    if vals["total_op"] is not None and vals["total"] is not None and not (vals["total"] <= vals["total_op"] <= vals["total"] * Decimal("2.2")):
        vals["total_op"] = None
        conf["total_op"] = None
        flags.append("TOTAL_OP_IMPLAUSIBLE")
    return vals, conf, flags


# ----------------------------------------------------------------------------------------------- crews / units
def normalise_crew(s: str, known: set[str]) -> Optional[str]:
    if not s:
        return None
    t = re.sub(r"[^A-Za-z0-9.\-\]|‘’'!]", "", s)
    if not t:
        return None
    # "1 Lath" is often read as "]loth", "Tloth", "1Cop": a confusable prefix stands for the count, the rest for the trade
    m = re.match(r"^([\]|‘’'!lIT]|\d|\.5|1\.5|\d\.\d)?([A-Za-z]{3,5})$", t)
    if m:
        trade = m.group(2).lower()
        pre = m.group(1) or ""
        qty = pre if re.fullmatch(r"\d|\.5|1\.5|\d\.\d", pre) else ("1" if pre or trade in TRADES else None)
        if trade in TRADES and qty:
            return f"{qty} {trade[0].upper() + trade[1:]}"
        close = sorted({tr for tr in TRADES if _lev(tr, trade) <= 1})
        if len(close) != 1 and re.fullmatch(r"\d|\.5|1\.5|\d\.\d", pre):
            close = sorted({tr for tr in TRADES if _lev(tr, trade) <= 2})       # a printed count makes a looser match safe
        if len(close) == 1 and qty:
            return f"{qty} {close[0][0].upper() + close[0][1:]}"
    m = re.match(r"^([A-Za-z])-?(\d{1,2})([A-Za-z]?)$", t)
    if m:
        cid = f"{m.group(1).upper()}-{int(m.group(2))}{m.group(3).upper()}"
        if not known or cid in known:
            return cid
    # fuzzy against the known crew list (e.g. 'lloth' -> '1 Lath', 'C14A' -> 'C-14A')
    if known:
        key = t.lower().replace("-", "")
        cand = [c for c in known if _close(key, c.lower().replace(" ", "").replace("-", ""))]
        if len(cand) == 1:
            return cand[0]
    return None


def _lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _close(a: str, b: str) -> bool:
    if len(a) != len(b) or not a:
        return False
    confus = {("l", "1"), ("1", "l"), ("i", "1"), ("1", "i"), ("o", "a"), ("a", "o"), ("o", "0"), ("0", "o"), ("c", "e"), ("e", "c"), ("t", "l"), ("l", "t"),
              ("i", "l"), ("l", "i"), ("h", "b"), ("b", "h"), ("u", "o"), ("o", "u"), ("s", "5"), ("5", "s"), ("q", "g"), ("g", "q"), ("1", "l")}
    d = sum(1 for x, y in zip(a, b) if x != y and (x, y) not in confus)
    e = sum(1 for x, y in zip(a, b) if x != y)
    return d == 0 and e <= 2 or (d <= 1 and e <= 1)


def normalise_unit(s: str) -> Optional[str]:
    if not s:
        return None
    t = re.sub(r"[^A-Za-z%.]", "", s).upper()
    if not t:
        return None
    if t in UNIT_TABLE:
        return UNIT_TABLE[t]
    t2 = t.replace(".", "")
    if t2 in UNIT_TABLE:
        return UNIT_TABLE[t2]
    return None


# ----------------------------------------------------------------------------------------------- page
MERGED_OH = re.compile(r"^(\d{1,4})[.,]?(\d{3})[.:]?$")


def cell_tokens(row: list[dict], bounds: dict, desc_end: float) -> dict:
    cells: dict[str, list[dict]] = {k: [] for k in bounds}
    desc = []
    for z in row:
        xc = (z["x0"] + z["x1"]) / 2
        if z["x1"] <= desc_end + 20 and xc < desc_end:
            desc.append(z)
            continue
        k = col_of(xc, bounds)
        if k in ("output", "hours") and z["x0"] < bounds["output"][1] - 10 and z["x1"] > bounds["hours"][0] + 10:
            # one OCR token spanning the Daily Output and Labor-Hours columns ("500.016", "313.026"): split it
            m = MERGED_OH.fullmatch(z["t"].replace(" ", ""))
            if m:
                cut = bounds["output"][1]
                cells["output"].append({**z, "t": m.group(1), "x1": int(cut) - 8})
                cells["hours"].append({**z, "t": "." + m.group(2), "x0": int(cut) + 8})
                continue
        if k:
            cells[k].append(z)
    return {"desc": desc, "cells": cells}


def numeric_candidates(kind: str, toks_t: list[dict], toks_i: list[dict], img: Optional[np.ndarray], page_w: int) -> list[tuple[Decimal, str, str]]:
    out: list[tuple[Decimal, str, str]] = []
    raw_t = "".join(z["t"] for z in toks_t)
    raw_i = "".join(z["t"] for z in toks_i)
    for v, how in candidates(raw_t, kind):
        out.append((v, how, "T"))
    for v, how in candidates(raw_i, kind):
        out.append((v, how, "I"))
    # geometric reading on the OCR box (tesseract's, else the text layer's)
    box_src = toks_t if toks_t else toks_i
    if img is not None and box_src:
        x0 = min(z["x0"] for z in box_src)
        x1 = max(z["x1"] for z in box_src)
        y0 = min(z["y0"] for z in box_src)
        y1 = max(z["y1"] for z in box_src)
        if x1 < page_w - 12:                                   # a box touching the page edge is cut: no geometric reading
            g = analyse(img, x0, x1, y0, y1)
            if g is not None and len(g.points) <= 1:
                # the geometry fixes the POINT of each OCR digit string; it does not decide between different digit strings
                for d in sorted({digits_of(raw_t), digits_of(raw_i)}):
                    if d:
                        s = g.apply(d)
                        if s is not None:
                            try:
                                out.append((Decimal(s), "as_read", "G"))
                            except Exception:
                                pass
    return out


def parse_page(pdf_page: int, book: Path, parts: Parts, crews: dict) -> dict:
    w, h, tw = load_tess(book / "ocr" / f"p{pdf_page:04d}.tsv")
    iw = load_ia(book / "ia" / f"p{pdf_page:04d}.json", w, h)
    trows = rows_of(tw, tol=16)
    irows = rows_of(iw, tol=16)
    hdr = find_header(trows)
    out = {"pdf_page": pdf_page, "book_page": pdf_page - 14, "header_found": hdr is not None, "lines": [], "sections": [], "divisions": []}
    if hdr is None:
        return out
    img = parts.image(pdf_page)
    if img is not None and img.shape[1] != w:
        img = None                                             # OCR was run at another size; no geometry then
    bounds, desc_end = hdr["bounds"], hdr["desc_end"]
    irow_by_y = [(r[0]["_yc"], r) for r in irows]
    known = set(crews)

    def ia_row_near(yc):
        best = min(irow_by_y, key=lambda p: abs(p[0] - yc), default=None)
        return best[1] if best and abs(best[0] - yc) <= 18 else []

    def division(txt):
        m3 = re.match(r"^(\d{2})\s?(\d{2})\s?(\d{2})(?![.,\d])\s*(.*)$", txt)
        m2 = re.match(r"^(\d{2})\s?(\d{2})(?![.,\d])\s*(.*)$", txt)
        if m3 and not re.match(r"^\d{2} \d{2} \d{2}[.,]\d{2}", txt):
            return ("div3", f"{m3.group(1)} {m3.group(2)} {m3.group(3)}", m3.group(4).strip(" -—–~_=|"))
        if m2 and len(m2.group(3).strip()) > 2:
            return ("div2", f"{m2.group(1)} {m2.group(2)}", m2.group(3).strip(" -—–~_=|"))
        return None

    section = None
    div2 = div3 = None
    last_unit = None
    last_crew = None
    last_line: Optional[int] = None

    SEC_RE = re.compile(r"^(\d{1,2})\s*(\d{2})\s*(\d{2})\s*[.,]\s*(\d{2})(?!\d)")

    def section_from(tokens_row: list[dict]) -> Optional[dict]:
        if not tokens_row or tokens_row[0]["x0"] > 230:
            return None
        joined = " ".join(z["t"] for z in tokens_row[:6])
        m = SEC_RE.match(joined)
        if not m:
            return None
        first = m.group(1)
        uncertain = len(first) == 1 or tokens_row[0]["x0"] < 60 or first not in VALID_DIVS
        if uncertain and div2 and div2[0][3:5] == m.group(2) and div2[0][:2] in VALID_DIVS:
            first = div2[0][:2]                                # the division digit at the page edge is cut or misread; the running division says what it is
        elif len(first) == 1:
            first = "0" + first                                # placeholder: fixed in the merge step from neighbouring pages
        # title = the words after the id, inside the description area
        consumed = 0
        acc = ""
        for i, z in enumerate(tokens_row):
            acc = (acc + " " + z["t"]).strip()
            if re.sub(r"\s", "", acc) == re.sub(r"\s", "", m.group(0)) or len(re.sub(r"\D", "", acc)) >= 8:
                consumed = i + 1
                break
        title = " ".join(z["t"] for z in tokens_row[consumed:] if z["x1"] < desc_end and re.search(r"[A-Za-z]", z["t"]))
        return {"section_id": f"{first} {m.group(2)} {m.group(3)}.{m.group(4)}", "title": title.strip(" -—–=~_.|"), "div2": div2, "div3": div3,
                "pdf_page": pdf_page, "division_uncertain": uncertain, "division_raw": m.group(1)}

    for r in trows:
        txt = " ".join(z["t"] for z in r)
        if r is trows[hdr["row"]]:
            sec = section_from(r)
            if sec:
                section = sec
                out["sections"].append(sec)
            continue
        if r[0]["_yc"] < hdr["y"]:
            dv = division(txt)
            if dv:
                if dv[0] == "div3":
                    div3 = dv[1:]
                else:
                    div2 = dv[1:]
                out["divisions"].append(dv)
            continue
        if r[0]["x0"] > desc_end * 0.25:
            continue
        sec = section_from(r)
        if sec:
            section = sec
            out["sections"].append(sec)
            last_unit = last_crew = last_line = None
            continue
        first = r[0]["t"]
        partial = False
        ir = ia_row_near(r[0]["_yc"])
        ia_first = ir[0]["t"] if ir and ir[0]["x0"] < 230 and re.fullmatch(r"\d{3,4}", ir[0]["t"]) else None
        body = r[1:]
        if LINE_RE.fullmatch(first) and r[0]["x0"] < 230:
            line_no = first
            if ia_first and ia_first != first and len(ia_first) == 4 and last_line is not None:
                # the two readings differ: keep the one that continues the numbering
                if not (int(first) > last_line) and int(ia_first) > last_line:
                    line_no = ia_first
        elif re.fullmatch(r"\d{3}", first) and r[0]["x0"] < 60:
            line_no, partial = first, True                     # left edge of the page cut off: thousands digit missing
        elif r[0]["x0"] >= 60 and ia_first and (not (ir[0]["x0"] < 60) or len(ia_first) == 4):
            line_no, partial, body = ia_first, len(ia_first) == 3, r   # tesseract missed the number, the text layer has it
        elif r[0]["x0"] >= 150 and not division(txt) \
                and any(col_of((z["x0"] + z["x1"]) / 2, bounds) in ("material", "labor", "total") and re.search(r"\d", z["t"]) for z in r) \
                and any(re.search(r"[A-Za-z]", z["t"]) for z in r if z["x1"] < desc_end):
            line_no, body = None, r                            # a priced row whose number no reading caught
        else:
            dv = division(txt)
            if dv:
                if dv[0] == "div3":
                    div3 = dv[1:]
                else:
                    div2 = dv[1:]
                out["divisions"].append(dv)
            continue
        if line_no is not None and not partial:
            if last_line is not None and int(line_no) <= last_line:
                order_flag = "LINE_ORDER"
            else:
                order_flag = None
            last_line = int(line_no)
        else:
            order_flag = None
        ct = cell_tokens(body, bounds, desc_end)
        ci = cell_tokens([z for z in ir if not (re.fullmatch(r"\d{3,4}", z["t"]) and z["x0"] <= r[0]["x1"] + 5)], bounds, desc_end)
        desc_toks = [z for z in ct["desc"] if not JUNK_RE.fullmatch(z["t"])]
        ref = [z["t"] for z in desc_toks if REF_RE.match(z["t"])]
        desc_toks = [z for z in desc_toks if not REF_RE.match(z["t"])]
        desc_t = " ".join(z["t"] for z in desc_toks)
        desc_i = " ".join(z["t"] for z in ci["desc"] if not REF_RE.match(z["t"]) and not JUNK_RE.fullmatch(z["t"]))
        indent = desc_toks[0]["x0"] if desc_toks else (ci["desc"][0]["x0"] if ci["desc"] else None)
        crew_raw = " ".join(z["t"] for z in ct["cells"]["crew"]).strip(" |:;.,'‘’`\"~=_")
        crew_raw_i = " ".join(z["t"] for z in ci["cells"]["crew"]).strip(" |:;.,'‘’`\"~=_")
        unit_raw = " ".join(z["t"] for z in ct["cells"]["unit"]).strip(" |:;,'‘’`\"~=_")
        unit_raw_i = " ".join(z["t"] for z in ci["cells"]["unit"]).strip(" |:;,'‘’`\"~=_")
        cands = {k: numeric_candidates(k, ct["cells"][k], ci["cells"][k], img, w) for k in NUM_COLS}
        crew_id = normalise_crew(crew_raw, known) or normalise_crew(crew_raw_i, known)
        crew_src = "printed" if crew_id else None
        if crew_id is None and (cands["hours"] or cands["output"]) and last_crew:
            crew_id, crew_src = last_crew, "carried"
        crew_row = crews.get(crew_id) if crew_id else None
        vals, confs, flags = settle(cands, crew_row)
        unit = normalise_unit(unit_raw) or normalise_unit(unit_raw_i)
        if unit:
            last_unit, unit_src = unit, "printed"
        elif last_unit:
            unit, unit_src = last_unit, "carried"
        else:
            unit_src = None
        if crew_src == "printed":
            last_crew = crew_id
        if crew_id and crews and crew_row is None:
            flags.append("CREW_UNKNOWN")
        if partial:
            flags.append("LINE_NUMBER_PARTIAL")
        if line_no is None:
            flags.append("LINE_NUMBER_MISSING")
        if order_flag:
            flags.append(order_flag)
        out["lines"].append({
            "line": line_no, "line_partial": partial, "section_id": section["section_id"] if section else None, "pdf_page": pdf_page,
            "book_page": pdf_page - 14, "description": desc_t, "description_alt": desc_i if desc_i != desc_t else None, "indent_px": indent,
            "ref_note": ref[0] if ref else None, "crew": crew_id, "crew_source": crew_src, "crew_raw": crew_raw or crew_raw_i or None,
            "unit": unit, "unit_source": unit_src, "unit_raw": unit_raw or unit_raw_i or None,
            **{k: (str(vals[k]) if vals[k] is not None else None) for k in NUM_COLS},
            "conf": {k: confs[k] for k in NUM_COLS if confs[k] is not None},
            "raw": {k: [(str(v), how, src) for v, how, src in cands[k]] for k in NUM_COLS if cands[k]},
            "flags": flags})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("book_dir")
    ap.add_argument("out_dir")
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("--crews", default=None)
    a = ap.parse_args()
    book = Path(a.book_dir)
    crews = {}
    if a.crews and Path(a.crews).exists():
        with open(a.crews, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                crews[r["crew_id"]] = {k: (float(v) if v not in ("", None) else None) for k, v in r.items()
                                       if k not in ("crew_id", "notes", "checks_ok", "page_pdf")}
    parts = Parts(book / "parts")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n_lines = n_pages = 0
    for p in range(a.first, a.last + 1):
        if not (book / "ocr" / f"p{p:04d}.tsv").exists():
            continue
        res = parse_page(p, book, parts, crews)
        (out / f"p{p:04d}.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        if res["header_found"]:
            n_pages += 1
            n_lines += len(res["lines"])
        if p % 50 == 0:
            print(f"  page {p}: {n_pages} table pages, {n_lines} lines so far", flush=True)
    print(f"pages with a unit-price header: {n_pages}; lines: {n_lines}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
