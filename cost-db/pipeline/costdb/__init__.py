"""Owl Tower cost database toolkit: ids, units, schema metadata, storage, calculation, validation."""
import hashlib as _hashlib
import os as _os
from pathlib import Path as _Path

__version__ = "0.2.0"


def _code_fingerprint() -> str:
    """Short hash of the files that decide calculation results, so a fixed bug changes every run id."""
    h = _hashlib.sha1()
    for name in ("calc.py", "units.py", "ids.py", "enums.py"):
        h.update((_Path(__file__).parent / name).read_bytes())
    return h.hexdigest()[:8]


CALC_VERSION = f"costdb-calc/{__version__}+{_code_fingerprint()}"

# Timestamp stamped on generated rows (created_at). Fixed per build so CSV output is reproducible.
BUILD_TS = _os.environ.get("OWL_BUILD_TS", "2026-10-24T00:00:00+00:00")
