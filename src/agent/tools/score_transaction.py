"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool score_transaction: load the saved pipeline and its metadata ONCE
                 (load_scoring_model, through model_io.py), then give the official ScoreResult of a
                 checked case: score, threshold and band bounds read from model_metadata.json (I20),
                 band from risk_bands.py, model version "{model_name}@{saved_at}"
Never does     : Call the LLM; rebuild the model variables by hand (the saved pipeline holds the
                 "derive" step, D-12); hard-code a threshold or a bound; read isFraud or
                 isFlaggedFraud; keep a hidden global cache; retry (retry.py, n° 62); write anything;
                 any financial action
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 1), section 5, section 8 (n° 45), D-12;
                 Features_Complet.md G04, G12, D07; brief §11.4; PASSATION.md §6, decisions PR 5 (i), (ii), (c)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.agent.domain import ScoreResult
from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.data.case_input import CaseInput
from src.models.model_io import ModelIOError, load_model
from src.models.risk_bands import RiskBandError, check_bounds, risk_band

# What this tool may change (G12 test): nothing, it only reads the model.
TOOL_EFFECT = "read_only"


@dataclass(frozen=True)
class ScoringModel:
    """The saved model, loaded once and passed to every call (decision (c): no global cache).

    Every number here comes from model_metadata.json; nothing is chosen in this file.
    """

    pipeline: Any  # fitted sklearn Pipeline: raw transaction columns in, probabilities out
    threshold: float
    risk_band_bounds: dict[str, float]  # {"medium": ..., "high": ...}, already checked
    model_version: str


def load_scoring_model(pipeline_path: Path, metadata_path: Path) -> ScoringModel:
    """Load the pipeline and its metadata, and check the band bounds now, not at the first case.

    Raises ToolUnavailableError: missing or unusable model, or missing / wrong band bounds.
    """
    try:
        pipeline, metadata = load_model(Path(pipeline_path), Path(metadata_path))
    except (ModelIOError, OSError, ValueError) as error:
        # ValueError also covers an unreadable JSON file (json.JSONDecodeError).
        raise ToolUnavailableError(f"Scoring model unavailable: {error}") from error

    try:
        # None (bounds never written) is refused here, with the reminder of the script to run.
        medium, high = check_bounds(metadata.get("risk_band_bounds"))
    except RiskBandError as error:
        raise ToolUnavailableError(str(error)) from error

    return ScoringModel(
        pipeline=pipeline,
        threshold=float(metadata["threshold"]),  # checked 0 < threshold < 1 by model_io
        risk_band_bounds={"medium": medium, "high": high},
        # Founder decision (i): same version string as scripts/build_demo_cases.py.
        model_version=f"{metadata['model_name']}@{metadata['saved_at']}",
    )


def score_transaction(model: ScoringModel, case_input: CaseInput) -> ScoreResult:
    """Score one checked case. One attempt only (decision (a)).

    Raises ToolInputError (wrong arguments) or ToolUnavailableError (the model failed or gave
    a score outside [0, 1]).
    """
    if not isinstance(model, ScoringModel):
        raise ToolInputError("score_transaction needs a ScoringModel (see load_scoring_model)")
    if not isinstance(case_input, CaseInput):
        raise ToolInputError("score_transaction needs a CaseInput checked by parse_case_input")

    # One row with the 7 raw transaction columns only: no label, no identifier, no case note.
    # The pipeline derives its own variables (decision (ii), D-12).
    features = pd.DataFrame([case_input.transaction()])
    try:
        score = float(model.pipeline.predict_proba(features)[0, 1])
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        raise ToolUnavailableError(f"The model could not score {case_input.case_id}") from error

    try:
        band = risk_band(score, model.risk_band_bounds)
    except RiskBandError as error:
        # A score outside [0, 1] or NaN: the model is not trustworthy, not the input.
        raise ToolUnavailableError(f"Untrustworthy score for {case_input.case_id}: {error}") from error

    return ScoreResult(
        score=score,
        threshold=model.threshold,
        risk_band=band,
        model_version=model.model_version,
    )
