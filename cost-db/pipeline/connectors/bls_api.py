#!/usr/bin/env python3
"""BLS Public Data API v2 client + parser (index series: PPI, ECI, OEWS time series ...).

UNTESTED AGAINST THE LIVE API from the build sandbox (bls.gov is blocked by its network policy). The request and
response layouts below follow the public BLS API documentation as recalled by the author; the parser is covered by a
format fixture only (tests/fixtures/bls_api_format_fixture.json). First live run must be reviewed by a person.

Terms to respect (per research agent A1, search-snippet level — re-verify at bls.gov):
  * v2 needs a free registration key; limits: 500 queries/day, 50 series/query, 20 years/query
  * v1 (no key): 25 queries/day, 25 series/query, 10 years/query; request rate limit 50 requests / 10 s
  * the Terms of Service ask users to cite the source and access date
The key is read from the environment variable BLS_API_KEY and is never logged or stored.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Optional

ENDPOINT = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
LIMITS = {"v2": {"series": 50, "years": 20, "queries": 500}, "v1": {"series": 25, "years": 10, "queries": 25}}


class BlsError(RuntimeError):
    pass


def build_payload(series_ids: list[str], start_year: int, end_year: int, key: Optional[str] = None) -> dict:
    lim = LIMITS["v2" if key else "v1"]
    if len(series_ids) > lim["series"]:
        raise BlsError(f"{len(series_ids)} series exceeds the {lim['series']}-series limit; split into batches")
    if end_year - start_year + 1 > lim["years"]:
        raise BlsError(f"{end_year - start_year + 1} years exceeds the {lim['years']}-year limit; split the range")
    if not all(re.fullmatch(r"[A-Za-z0-9]{6,32}", s) for s in series_ids):
        raise BlsError("series ids must be alphanumeric BLS identifiers")
    payload = {"seriesid": series_ids, "startyear": str(start_year), "endyear": str(end_year)}
    if key:
        payload["registrationkey"] = key
        payload["catalog"] = False
    return payload


def batches(series_ids: list[str], start_year: int, end_year: int, key: Optional[str]) -> Iterable[tuple[list[str], int, int]]:
    lim = LIMITS["v2" if key else "v1"]
    for i in range(0, len(series_ids), lim["series"]):
        chunk = series_ids[i:i + lim["series"]]
        y = start_year
        while y <= end_year:
            yield chunk, y, min(end_year, y + lim["years"] - 1)
            y += lim["years"]


def fetch(series_ids: list[str], start_year: int, end_year: int, raw_dir: Path, session=None, pause_s: float = 0.25) -> list[Path]:
    """POST each batch, store the raw JSON (hash-named) and return the file paths. Requires network access to api.bls.gov."""
    import requests  # imported lazily so parsing works without the dependency
    key = os.environ.get("BLS_API_KEY") or None
    sess = session or requests.Session()
    sess.headers["User-Agent"] = "OwlTowerCostDB/0.1 (contact: noctevusapp@gmail.com)"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for chunk, y0, y1 in batches(series_ids, start_year, end_year, key):
        payload = build_payload(chunk, y0, y1, key)
        for attempt in range(4):
            resp = sess.post(ENDPOINT, json=payload, timeout=60)
            if resp.status_code == 200:
                break
            time.sleep(2 ** attempt)
        else:
            raise BlsError(f"HTTP {resp.status_code} from BLS after retries")
        body = resp.content
        data = json.loads(body)
        if data.get("status") != "REQUEST_SUCCEEDED":
            raise BlsError(f"BLS status {data.get('status')}: {data.get('message')}")
        digest = hashlib.sha256(body).hexdigest()
        p = raw_dir / f"bls_{digest[:16]}.json"
        p.write_bytes(body)
        out.append(p)
        time.sleep(pause_s)
    return out


@dataclass
class Point:
    series_id: str
    year: int
    period: str
    period_name: str
    value: Optional[Decimal]
    footnote_codes: tuple[str, ...]
    latest: bool


def parse_response(data: dict) -> list[Point]:
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise BlsError(f"unsuccessful response: {data.get('status')} {data.get('message')}")
    pts: list[Point] = []
    for s in data["Results"]["series"]:
        for d in s["data"]:
            try:
                v: Optional[Decimal] = Decimal(d["value"])
            except (InvalidOperation, KeyError):
                v = None   # '-' means no data for the period
            codes = tuple(f.get("code", "") for f in d.get("footnotes", []) if f and f.get("code"))
            pts.append(Point(s["seriesID"], int(d["year"]), d["period"], d.get("periodName", ""), v, codes, d.get("latest") == "true"))
    return pts


def period_start(year: int, period: str) -> Optional[date]:
    m = re.fullmatch(r"([MQA])(\d{2})", period)
    if not m:
        return None
    kind, n = m.group(1), int(m.group(2))
    if kind == "M":
        return date(year, n, 1) if 1 <= n <= 12 else None     # M13 = annual average -> skipped
    if kind == "Q":
        return date(year, 3 * (n - 1) + 1, 1) if 1 <= n <= 4 else None
    return date(year, 1, 1) if n == 1 else None


def to_index_values(points: list[Point], index_id_by_series: dict[str, str], vintage: date, retrieved_at: str,
                    locator: str, sha256: Optional[str]) -> list[dict]:
    """Rows for index_values. Footnote code 'P' means preliminary. Missing values are skipped, never invented."""
    rows = []
    for p in points:
        idx = index_id_by_series.get(p.series_id)
        start = period_start(p.year, p.period)
        if idx is None or start is None or p.value is None:
            continue
        rows.append({"index_id": idx, "period_start": start, "vintage_date": vintage, "value": p.value,
                     "value_status": "preliminary" if "P" in p.footnote_codes else "final", "retrieved_at": retrieved_at,
                     "source_locator": f"{locator} series {p.series_id} {p.year} {p.period}", "raw_file_sha256": sha256,
                     "origin": "observed", "review_status": "unreviewed", "reviewed_by": None, "reviewed_at": None,
                     "notes": "BLS API; cite source and access date per BLS terms"})
    return rows


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
