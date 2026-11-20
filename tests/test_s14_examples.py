"""
SoC layer      : Tests
Responsibility : Cover the examples of brief §14 (R302, R303) that no existing test covered: the
                 target holds only valid values, the written rule for missing feature values, and
                 metrics computed on held-out (test) rows only
Never does     : Load the real PaySim CSV or the trained model; write outside pytest's tmp_path;
               open a network connection; modify a frozen module (the frozen test files of J2/J3
               are protected, so these tests live in this new file)
Reference      : Architecture_Projet.md v1.5 — section 8 (this file is outside the register, Q-51:
                 number to be given by the founder in v1.6); Features_Complet.md K02;
                 Matrice_Conformite.md R302, R303; data/README.md §4 (R081)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.data.schema import TARGET_COLUMN, TRANSACTION_TYPES, SchemaError, validate_frame
from src.data.split import stratified_split
from src.features.build_features import build_preprocessor, split_xy
from src.models import evaluate as ev
from src.models.train_classical import Candidate

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "configs" / "settings.yaml"
# Seed and shares of the split come from settings.yaml (I34), never written here.
SPLIT = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))["split"]
# Invented for this test only (like the 0.3 of tests/conftest.py): the counts checked below add
# up whatever the threshold is.
TEST_THRESHOLD = 0.3


def _raw(n_rows: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Invented PaySim-like frame (same shape as tests/test_models.py): frauds move the whole
    balance of a TRANSFER or CASH_OUT. No real row, no real identifier."""
    rng = np.random.default_rng(seed)
    types = rng.choice(sorted(TRANSACTION_TYPES), n_rows)
    old_orig = rng.uniform(100, 20_000, n_rows)
    fraud = (np.isin(types, ["TRANSFER", "CASH_OUT"]) & (rng.random(n_rows) < 0.25)).astype(int)
    amount = np.where(fraud == 1, old_orig, rng.uniform(10, 5_000, n_rows))
    return pd.DataFrame({
        "step": rng.integers(1, 744, n_rows),
        "type": types,
        "amount": amount,
        "nameOrig": [f"C{i}" for i in range(n_rows)],
        "oldbalanceOrg": old_orig,
        "newbalanceOrig": np.where(fraud == 1, 0.0, np.maximum(old_orig - amount, 0)),
        "nameDest": [f"M{i}" for i in range(n_rows)],
        "oldbalanceDest": rng.uniform(0, 20_000, n_rows),
        "newbalanceDest": rng.uniform(0, 20_000, n_rows),
        TARGET_COLUMN: fraud,
        "isFlaggedFraud": 0,
    })


# --- R302 "Target has valid values." ----------------------------------------------------------
def test_invented_frame_passes_the_contract():
    """Guard: the frame used below is valid, so a refusal can only come from the changed value."""
    validate_frame(_raw(n_rows=50))


@pytest.mark.parametrize("bad_value", [2, -1])
def test_target_value_outside_zero_one_refused(bad_value):
    """isFraud may only be 0 or 1 (schema.BINARY_VALUES); any other value refuses the frame.
    The existing test_validate_frame_target covers a missing target only."""
    frame = _raw(n_rows=50)
    frame.loc[0, TARGET_COLUMN] = bad_value
    with pytest.raises(SchemaError, match=TARGET_COLUMN):
        validate_frame(frame)


# --- R302 "Missing data is handled." ------------------------------------------------------------
def test_missing_feature_value_is_not_refused_at_load():
    """Pins the written rule (data/README.md §4, R081): a missing TARGET refuses the frame
    (test_validate_frame_target), a missing FEATURE value is not refused at load time.
    No imputation exists because PaySim has 0 missing values (nb02 R063)."""
    frame = _raw(n_rows=50)
    frame["amount"] = frame["amount"].astype(float)
    frame.loc[0, "amount"] = np.nan
    validate_frame(frame)  # no SchemaError
    frame.loc[0, TARGET_COLUMN] = np.nan
    frame[TARGET_COLUMN] = frame[TARGET_COLUMN].astype(float)
    with pytest.raises(SchemaError, match="missing values in the target"):
        validate_frame(frame)


# --- R303 "Metrics are calculated on held-out data." ----------------------------------------
def test_test_metrics_use_only_held_out_rows():
    """The model is fitted on the train part only; evaluate_on_test scores exactly the test part,
    whose rows were never seen in train or validation."""
    parts = stratified_split(_raw(), val_size=SPLIT["val_size"], test_size=SPLIT["test_size"],
                             seed=SPLIT["seed"])
    # Held out: no test row is in train or validation.
    assert set(parts.test.index).isdisjoint(parts.train.index)
    assert set(parts.test.index).isdisjoint(parts.validation.index)

    X_train, y_train = split_xy(parts.train)
    X_test, y_test = split_xy(parts.test)
    pipeline = Pipeline([("prep", build_preprocessor()),
                         ("model", LogisticRegression(max_iter=1000))]).fit(X_train, y_train)
    candidate = Candidate(name="logistic_regression", pipeline=pipeline, params={}, val_pr_auc=0.0)

    result = ev.evaluate_on_test(candidate, X_test, y_test, TEST_THRESHOLD)
    assert result["rows"] == len(parts.test) != len(parts.train)
    assert result["frauds"] == int(y_test.sum())
    assert result["tp"] + result["fp"] + result["fn"] + result["tn"] == len(parts.test)
    assert result["tp"] + result["fn"] == int(y_test.sum())
    # The ranking metric is the one of the test scores, not of any other part.
    test_scores = ev.fraud_scores(candidate, X_test)
    assert result["pr_auc"] == pytest.approx(ev.ranking_metrics(y_test, test_scores)["pr_auc"])
