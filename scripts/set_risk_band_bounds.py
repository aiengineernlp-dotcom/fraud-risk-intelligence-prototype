"""
SoC layer      : Training (ML) — one-off script, run by the founder
Responsibility : Write the risk band bounds (I46) into model_metadata.json, without retraining (I47):
                 medium bound = `threshold` of the metadata (300 cases/day);
                 high bound   = `threshold` of the 200 cases/day row of threshold_analysis.csv
                 (validation set); check that the 300 row has exactly the metadata threshold
Never does     : Retrain; open the test set; invent a value; touch any other metadata key
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 40bis), D-12;
                 Features_Complet.md D07; Points_A_Trancher I20, I46, I47
Run            : .venv/bin/python -m scripts.set_risk_band_bounds
"""

from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from src.config import load_config
from src.models.risk_bands import check_bounds  # dependency noted in PASSATION.md §6 (Q2)

# Same file name as src/train.py writes in paths.metrics_dir.
THRESHOLD_ANALYSIS_FILE = "threshold_analysis.csv"

# Decision I46: high bound = threshold for 200 cases/day; the 300 cases/day row must match the
# metadata threshold (I08). Capacities from the founder's decision, not tunable settings.
HIGH_BOUND_CAPACITY = 200
THRESHOLD_CAPACITY = 300


class BoundsSourceError(Exception):
    """Raised when the metadata or the threshold analysis cannot give trustworthy bounds."""


def _row_threshold(rows: list[dict[str, str]], capacity: int) -> float:
    """Return the `threshold` of the single row with `capacity_per_day == capacity`."""
    matches = [row for row in rows if int(row["capacity_per_day"]) == capacity]
    if len(matches) != 1:
        raise BoundsSourceError(
            f"{THRESHOLD_ANALYSIS_FILE}: expected exactly one row with capacity_per_day == {capacity}, "
            f"found {len(matches)}"
        )
    return float(matches[0]["threshold"])


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.is_file():
        raise BoundsSourceError(f"Missing file: {csv_path} — run `python -m src.train` first")
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"capacity_per_day", "threshold"} <= set(rows[0]):
        raise BoundsSourceError(f"{csv_path}: needs the columns capacity_per_day and threshold")
    return rows


def _write_json_atomically(path: Path, data: dict[str, Any]) -> None:
    """Write to a temporary file in the same folder, then replace: a crash never leaves a
    half-written model_metadata.json. Same format as model_io.py (indent 2, sorted keys)."""
    handle, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as tmp:
            tmp.write(json.dumps(data, indent=2, sort_keys=True))
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def set_risk_band_bounds(metadata_path: Path, csv_path: Path) -> tuple[Any, dict[str, float]]:
    """Compute the bounds, write them into `metadata_path`, return (old value, new value)."""
    if not metadata_path.is_file():
        raise BoundsSourceError(f"Missing file: {metadata_path} — run `python -m src.train` first")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    # Q3: read `threshold` straight from the JSON (model_io.load_model would also load the pipeline).
    threshold = metadata.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise BoundsSourceError(f"{metadata_path}: `threshold` is missing or not a number")

    rows = _read_rows(csv_path)
    # Q1: strict equality — both values come from the same training run, written at full precision.
    threshold_row = _row_threshold(rows, THRESHOLD_CAPACITY)
    if threshold_row != threshold:
        raise BoundsSourceError(
            f"Inconsistent files: threshold {threshold} in {metadata_path.name} but "
            f"{threshold_row} for {THRESHOLD_CAPACITY} cases/day in {csv_path.name}"
        )
    new_bounds = {"medium": float(threshold), "high": _row_threshold(rows, HIGH_BOUND_CAPACITY)}
    check_bounds(new_bounds)  # Q2: same rule as the agent (0 < medium < high < 1)

    # Q4: bounds already set -> rewrite them; the caller shows old and new values.
    old_bounds = metadata.get("risk_band_bounds")
    metadata["risk_band_bounds"] = new_bounds
    _write_json_atomically(metadata_path, metadata)
    return old_bounds, new_bounds


def main() -> int:
    paths = load_config().paths
    try:
        old, new = set_risk_band_bounds(paths.model_metadata, paths.metrics_dir / THRESHOLD_ANALYSIS_FILE)
    except (BoundsSourceError, ValueError) as error:  # RiskBandError is a ValueError
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    print(f"risk_band_bounds written to {paths.model_metadata}")
    print(f"  old: {old}")
    print(f"  new: {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
