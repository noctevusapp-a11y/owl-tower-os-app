"""Geometric reading of a numeric table cell: where are the digits, the decimal point and the thousands commas?

OCR engines drop a leading decimal point (".40" -> "40") far more often than they misread a digit. The point is still on the
page: a small blob at the baseline, left of or between the tall digit glyphs. This module finds the glyphs of a cell by ink
projection on the page image and reports (number_of_tall_glyphs, positions of points, positions of commas). Combined with the
digit string from OCR this fixes the magnitude without guessing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Glyphs:
    tall: list[tuple[int, int]]          # (x0, x1) of digit-sized glyph runs, left to right
    points: list[int]                    # index in `tall` AFTER which a decimal point sits (0 = before the first digit)
    commas: list[int]                    # same for commas
    digit_height: float
    note: str = ""

    def apply(self, digits: str) -> Optional[str]:
        """Insert the point into a digit-only string; None when the glyph count does not match the digits."""
        if len(digits) != len(self.tall) or len(self.points) > 1:
            return None
        if not self.points:
            return digits
        k = self.points[0]
        return (digits[:k] or "0") + "." + digits[k:] if k < len(digits) else None


def _ink_mask(crop: np.ndarray) -> np.ndarray:
    bg = float(np.percentile(crop, 85))
    fg = float(np.percentile(crop, 5))
    if bg - fg < 40:                      # blank cell
        return np.zeros_like(crop, dtype=bool)
    thr = fg + (bg - fg) * 0.55
    return crop < thr


def analyse(page: np.ndarray, x0: int, x1: int, y0: int, y1: int, margin_left: int = 22) -> Optional[Glyphs]:
    """page: 2-D uint8 gray image (row-major). The box (x0..x1, y0..y1) is the OCR word box of the number; the margin to the
    left catches a dropped leading point. Returns None when nothing readable is there."""
    h, w = page.shape
    X0, X1 = max(0, x0 - margin_left), min(w, x1 + 4)
    Y0, Y1 = max(0, y0 - 3), min(h, y1 + 6)
    if X1 - X0 < 4 or Y1 - Y0 < 6:
        return None
    crop = page[Y0:Y1, X0:X1]
    ink = _ink_mask(crop)
    if not ink.any():
        return None
    cols = ink.any(axis=0)
    runs = []
    x = 0
    while x < len(cols):
        if cols[x]:
            s = x
            while x < len(cols) and cols[x]:
                x += 1
            ys = np.where(ink[:, s:x].any(axis=1))[0]
            runs.append((s, x, int(ys.min()), int(ys.max())))
        else:
            x += 1
    if not runs:
        return None
    heights = [r[3] - r[2] + 1 for r in runs]
    # digit glyphs: the wide tall runs (a '1' is about a quarter of the digit height wide; leaders '|' and brackets are thinner
    # and usually taller than the digits because they cross the baseline)
    digit_like = [(r, hh) for r, hh in zip(runs, heights) if hh >= 14 and (r[1] - r[0]) >= 6]
    if not digit_like:
        return None
    dh = float(np.median([hh for r, hh in digit_like]))
    base = float(np.median([r[3] for r, hh in digit_like]))                     # baseline = bottom of the digits
    tall = [(r[0], r[1]) for r, hh in zip(runs, heights)
            if 0.72 * dh <= hh <= 1.18 * dh and 0.2 * dh <= (r[1] - r[0]) <= 1.3 * dh and r[3] <= base + 0.15 * dh]
    if not tall:
        return None
    points, commas = [], []
    for r, hh in zip(runs, heights):
        wdt = r[1] - r[0]
        if hh <= 0.3 * dh and wdt <= 0.3 * dh and hh >= 2 and wdt >= 2:
            near = any(abs(r[0] - t[1]) <= 0.6 * dh or abs(t[0] - r[1]) <= 0.6 * dh for t in tall)
            if not near or r[2] < base - 0.45 * dh:           # far from the digits, or too high (dash, apostrophe, noise)
                continue
            k = sum(1 for t in tall if t[1] <= r[0])          # digits to the left of the blob
            if k == len(tall):                                 # a trailing blob is punctuation of the line, never a decimal point
                continue
            if r[3] > base + 0.1 * dh + 1:
                commas.append(k)
            else:
                points.append(k)
    return Glyphs(tall=tall, points=points, commas=commas, digit_height=dh)
