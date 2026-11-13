"""
SoC layer      : 3 — Logic Engine
Responsibility : Turn a fraud score into exactly one risk band ("low", "medium" or "high") with the
                 band bounds RECEIVED AS A PARAMETER; refuse missing or badly ordered bounds and any
                 score outside [0, 1] (RiskBandError)
Never does     : Read the configuration or model_metadata.json (score_transaction passes the bounds
                 from model_metadata.json, D-12 / I20); hold a bound value in the code; call the LLM;
                 import Streamlit
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 40), D-12;
                 Features_Complet.md D07; Points_A_Trancher I20, I46, I47
"""

from __future__ import annotations

import math
from typing import Any

BAND_LOW = "low"
BAND_MEDIUM = "medium"
BAND_HIGH = "high"

# The only two keys of `risk_band_bounds` in model_metadata.json (I46).
BOUND_KEYS = ("medium", "high")


class RiskBandError(ValueError):
    """Raised when the band bounds or the score cannot give a trustworthy band."""


def _is_real_number(value: Any) -> bool:
    """True for an int or a float that is not a bool and not NaN.
    (bool is a subclass of int in Python: True would otherwise pass as 1.)"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return not math.isnan(value)


def check_bounds(bounds: Any) -> tuple[float, float]:
    """Check the bounds and return them as (medium, high).

    Expected: a dict with exactly the keys "medium" and "high", two real numbers,
    and 0 < medium < high < 1. Anything else is refused with RiskBandError."""
    if bounds is None:
        raise RiskBandError(
            "Risk band bounds are missing (risk_band_bounds is empty in model_metadata.json — "
            "run `python -m scripts.set_risk_band_bounds`)"
        )
    if not isinstance(bounds, dict) or set(bounds) != set(BOUND_KEYS):
        raise RiskBandError('Risk band bounds must be a dict with exactly the keys "medium" and "high"')
    medium, high = bounds["medium"], bounds["high"]
    if not (_is_real_number(medium) and _is_real_number(high)):
        raise RiskBandError("Risk band bounds must be numbers (not bool, not NaN)")
    # Strict order: equal bounds would leave the medium band empty.
    if not 0 < medium < high < 1:
        raise RiskBandError(f"Risk band bounds must satisfy 0 < medium < high < 1, got {medium}, {high}")
    return float(medium), float(high)


def risk_band(score: Any, bounds: Any) -> str:
    """Return the band of `score`:
    low if score < medium; medium if medium <= score < high; high if score >= high.
    A score equal to a bound goes to the upper band (medium bound = decision threshold, I46)."""
    medium, high = check_bounds(bounds)
    if not _is_real_number(score) or not 0 <= score <= 1:
        raise RiskBandError(f"Score must be a number between 0 and 1, got {score!r}")
    if score < medium:
        return BAND_LOW
    if score < high:
        return BAND_MEDIUM
    return BAND_HIGH
