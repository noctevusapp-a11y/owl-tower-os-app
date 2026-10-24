"""Owl Tower cost database toolkit: ids, units, schema metadata, storage, calculation, validation."""

__version__ = "0.1.0"
CALC_VERSION = f"costdb-calc/{__version__}"

# Timestamp stamped on generated rows (created_at). Fixed per build so CSV output is reproducible.
import os as _os
BUILD_TS = _os.environ.get("OWL_BUILD_TS", "2026-10-24T00:00:00+00:00")
