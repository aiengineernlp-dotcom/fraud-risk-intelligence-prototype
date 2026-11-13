"""
SoC layer      : Tests
Responsibility : Prove that risk_bands.py gives exactly one band per score, with the exact bounds
                 going to the upper band, and refuses missing / badly ordered bounds and scores
                 outside [0, 1]; prove that scripts/set_risk_band_bounds.py writes the I46 bounds
                 and refuses inconsistent files — on temporary files only
Never does     : Read or write a real file of artifacts/; train a model; call the LLM
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 40, 40bis, 41);
                 Features_Complet.md D07; Points_A_Trancher I46, I47
"""

from __future__ import annotations

import csv
import json
import math

import pytest

from scripts.set_risk_band_bounds import BoundsSourceError, set_risk_band_bounds
from src.models.risk_bands import RiskBandError, check_bounds, risk_band

# Test values: the I46 bounds (copied by hand from threshold_analysis.csv, lines 200 and 300).
MEDIUM = 0.5492405919533623
HIGH = 0.8516238554349536
BOUNDS = {"medium": MEDIUM, "high": HIGH}


# ---------- risk_bands.py (n° 40) ----------

@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "low"),
        (0.3, "low"),
        (math.nextafter(MEDIUM, 0.0), "low"),     # just below the medium bound
        (MEDIUM, "medium"),                        # exact medium bound -> medium
        (0.7, "medium"),
        (math.nextafter(HIGH, 0.0), "medium"),    # just below the high bound
        (HIGH, "high"),                            # exact high bound -> high
        (0.95, "high"),
        (1.0, "high"),
    ],
)
def test_each_score_gets_its_band(score, expected):
    assert risk_band(score, BOUNDS) == expected


def test_integer_scores_accepted():
    assert risk_band(0, BOUNDS) == "low"
    assert risk_band(1, BOUNDS) == "high"


def test_check_bounds_returns_medium_and_high():
    assert check_bounds(BOUNDS) == (MEDIUM, HIGH)


def test_missing_bounds_refused():
    with pytest.raises(RiskBandError, match="missing"):
        risk_band(0.5, None)


@pytest.mark.parametrize(
    "bounds",
    [
        {"medium": 0.9, "high": 0.5},     # reversed
        {"medium": 0.5, "high": 0.5},     # equal: empty medium band
        {"medium": 0.0, "high": 0.5},     # medium must be > 0
        {"medium": 0.5, "high": 1.0},     # high must be < 1
        {"medium": -0.1, "high": 0.5},
    ],
)
def test_badly_ordered_bounds_refused(bounds):
    with pytest.raises(RiskBandError, match="0 < medium < high < 1"):
        check_bounds(bounds)


@pytest.mark.parametrize(
    "bounds",
    [
        {"medium": MEDIUM},                                # key missing
        {"medium": MEDIUM, "high": HIGH, "extra": 0.9},   # key too many
        [MEDIUM, HIGH],                                    # not a dict
        {"medium": True, "high": HIGH},                    # bool is not a number
        {"medium": "0.5", "high": HIGH},                   # text is not a number
        {"medium": float("nan"), "high": HIGH},            # NaN
    ],
)
def test_malformed_bounds_refused(bounds):
    with pytest.raises(RiskBandError):
        check_bounds(bounds)


@pytest.mark.parametrize(
    "score",
    [-0.01, math.nextafter(0.0, -1.0), math.nextafter(1.0, 2.0), 1.5, float("nan"), True, "0.5", None],
)
def test_score_outside_0_1_refused(score):
    with pytest.raises(RiskBandError, match="Score"):
        risk_band(score, BOUNDS)


def test_risk_band_error_is_a_value_error():
    assert issubclass(RiskBandError, ValueError)


# ---------- scripts/set_risk_band_bounds.py (n° 40bis) ----------

CSV_COLUMNS = ["capacity_per_day", "alert_share", "alerts", "threshold", "tp"]


def _write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for capacity, threshold in rows:
            writer.writerow({"capacity_per_day": capacity, "alert_share": 0.001, "alerts": 1,
                             "threshold": repr(threshold), "tp": 1})


@pytest.fixture
def files(tmp_path):
    """A temporary model_metadata.json and threshold_analysis.csv shaped like the real ones."""
    metadata_path = tmp_path / "model_metadata.json"
    metadata = {"model_name": "random_forest", "threshold": MEDIUM, "risk_band_bounds": None,
                "split": {"seed": 42}, "validation_at_threshold": {"tp": 1082}}
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    csv_path = tmp_path / "threshold_analysis.csv"
    _write_csv(csv_path, [(100, 0.9948075001239073), (200, HIGH), (300, MEDIUM), (500, 0.42)])
    return metadata_path, csv_path, metadata


def test_script_writes_the_i46_bounds(files):
    metadata_path, csv_path, before = files
    old, new = set_risk_band_bounds(metadata_path, csv_path)
    assert old is None
    assert new == BOUNDS
    after = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert after["risk_band_bounds"] == BOUNDS
    # No other key touched.
    assert {k: v for k, v in after.items() if k != "risk_band_bounds"} == \
        {k: v for k, v in before.items() if k != "risk_band_bounds"}
    # Same format as model_io.py, no temporary file left behind.
    assert metadata_path.read_text(encoding="utf-8") == json.dumps(after, indent=2, sort_keys=True)
    assert sorted(p.name for p in metadata_path.parent.iterdir()) == \
        ["model_metadata.json", "threshold_analysis.csv"]


def test_script_rewrites_existing_bounds_and_returns_old_value(files):
    metadata_path, csv_path, _ = files
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    data["risk_band_bounds"] = {"medium": 0.3, "high": 0.6}
    metadata_path.write_text(json.dumps(data), encoding="utf-8")
    old, new = set_risk_band_bounds(metadata_path, csv_path)
    assert old == {"medium": 0.3, "high": 0.6}
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["risk_band_bounds"] == new == BOUNDS


def test_script_refuses_inconsistent_threshold(files):
    metadata_path, csv_path, _ = files
    _write_csv(csv_path, [(200, HIGH), (300, math.nextafter(MEDIUM, 1.0))])  # off by one ulp
    original = metadata_path.read_text(encoding="utf-8")
    with pytest.raises(BoundsSourceError, match="Inconsistent"):
        set_risk_band_bounds(metadata_path, csv_path)
    assert metadata_path.read_text(encoding="utf-8") == original  # nothing written


@pytest.mark.parametrize(
    "rows",
    [
        [(300, MEDIUM)],                          # no 200 row
        [(200, HIGH)],                            # no 300 row
        [(200, HIGH), (200, 0.8), (300, MEDIUM)],  # two 200 rows
    ],
)
def test_script_needs_exactly_one_200_and_one_300_row(files, rows):
    metadata_path, csv_path, _ = files
    _write_csv(csv_path, rows)
    with pytest.raises(BoundsSourceError, match="exactly one row"):
        set_risk_band_bounds(metadata_path, csv_path)


def test_script_refuses_bounds_in_wrong_order(files):
    metadata_path, csv_path, _ = files
    _write_csv(csv_path, [(200, 0.4), (300, MEDIUM)])  # high bound below the threshold
    with pytest.raises(RiskBandError):
        set_risk_band_bounds(metadata_path, csv_path)


def test_script_refuses_missing_files(tmp_path):
    with pytest.raises(BoundsSourceError, match="Missing file"):
        set_risk_band_bounds(tmp_path / "absent.json", tmp_path / "absent.csv")


def test_script_refuses_metadata_without_threshold(files):
    metadata_path, csv_path, _ = files
    metadata_path.write_text(json.dumps({"model_name": "random_forest"}), encoding="utf-8")
    with pytest.raises(BoundsSourceError, match="threshold"):
        set_risk_band_bounds(metadata_path, csv_path)
