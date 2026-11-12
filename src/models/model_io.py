"""
SoC layer      : 2 — Model access (the only door to the saved model, for training and for the agent)
Responsibility : Save the fitted pipeline (joblib) with its metadata (JSON: threshold, split,
                 model inputs); reload both and check them before anyone scores a transaction
Never does     : Train, evaluate or choose the threshold; load a file this project did not write
                 (loading a .joblib runs code: never open an untrusted one)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 20), D-12, D-13; Points_A_Trancher I20
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

# What the agent (J4) and the report need to trust a saved model.
REQUIRED_METADATA_KEYS = ("model_name", "threshold", "split", "model_input_columns", "saved_at")


class ModelIOError(Exception):
    """Raised when the saved model is missing, incomplete or unusable."""


def save_model(
    pipeline: Pipeline,
    metadata: dict[str, Any],
    pipeline_path: Path,
    metadata_path: Path,
) -> dict[str, Any]:
    """Check the metadata, then write the pipeline and its metadata side by side.
    Returns the metadata actually written (with the UTC save time added)."""
    written = {**metadata, "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _check_metadata(written)
    pipeline_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, pipeline_path)
    metadata_path.write_text(
        json.dumps(written, indent=2, sort_keys=True, default=_to_builtin), encoding="utf-8"
    )
    return written


def load_model(pipeline_path: Path, metadata_path: Path) -> tuple[Pipeline, dict[str, Any]]:
    """Reload the pipeline and its metadata; refuse anything missing, incomplete or unusable."""
    for path in (pipeline_path, metadata_path):
        if not path.is_file():
            raise ModelIOError(f"Missing model file: {path} — run `python -m src.train` first")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    _check_metadata(metadata)
    pipeline = joblib.load(pipeline_path)  # our own artifact only (see header)
    if not hasattr(pipeline, "predict_proba"):
        raise ModelIOError("The saved model cannot give fraud probabilities (no predict_proba)")
    return pipeline, metadata


def _check_metadata(metadata: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_METADATA_KEYS if key not in metadata]
    if missing:
        raise ModelIOError(f"Model metadata is missing: {', '.join(missing)}")
    threshold = metadata["threshold"]
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) \
            or not 0 < threshold < 1:
        raise ModelIOError("Model metadata: threshold must be a number strictly between 0 and 1")


def _to_builtin(value: Any) -> Any:
    """Let json write numpy numbers (np.float64, np.int64) as plain Python numbers."""
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Not JSON serialisable: {type(value).__name__}")