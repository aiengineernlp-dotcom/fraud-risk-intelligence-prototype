"""
SoC layer      : Tests
Responsibility : Prove the model chain on a small synthetic set: valid scores, models beat the baseline,
                 final model = best validation PR-AUC, counts add up, MLP wrapper and history behave,
                 save -> reload gives the same scores, bad metadata is refused
Never does     : Load the real PaySim CSV or write into artifacts/ (pytest's tmp_path only)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 28); D-12, D-13; Points_A_Trancher I09,
                 I37, I38; Matrice_Conformite.md R103
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.schema import TARGET_COLUMN, TRANSACTION_TYPES
from src.data.split import stratified_split
from src.features.build_features import MODEL_INPUT_COLUMNS, split_xy
from src.models import evaluate as ev
from src.models.model_io import ModelIOError, load_model, save_model
from src.models.train_classical import train_classical
from src.models.train_mlp import train_mlp

SEED = 42


def _raw(n_rows: int = 3000, seed: int = 0) -> pd.DataFrame:
    """Synthetic PaySim-like frame where fraud is learnable: frauds (TRANSFER / CASH_OUT only)
    move the whole balance and leave the sender at zero."""
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


@pytest.fixture(scope="module")
def trained():
    """Train every candidate ONCE for the whole file."""
    parts = stratified_split(_raw(), val_size=0.2, test_size=0.2, seed=SEED)
    X_train, y_train = split_xy(parts.train)
    X_val, y_val = split_xy(parts.validation)
    candidates = train_classical(X_train, y_train, X_val, y_val, seed=SEED, train_rows=10_000)
    mlp, history = train_mlp(X_train, y_train, X_val, y_val, seed=SEED, train_rows=10_000)
    return candidates + [mlp], history, X_val, y_val


def test_four_candidates_give_valid_scores(trained) -> None:
    candidates, _, X_val, _ = trained
    assert [c.name for c in candidates] == [
        "baseline_prior", "logistic_regression", "random_forest", "mlp"]
    for candidate in candidates:
        scores = ev.fraud_scores(candidate, X_val)
        assert scores.shape == (len(X_val),)
        assert ((scores >= 0) & (scores <= 1)).all()


def test_real_models_beat_the_baseline(trained) -> None:
    candidates, _, _, y_val = trained
    by_name = {c.name: c.val_pr_auc for c in candidates}
    assert by_name["baseline_prior"] == pytest.approx(y_val.mean(), abs=0.02)  # chance = fraud rate
    for name in ("logistic_regression", "random_forest", "mlp"):
        assert by_name[name] > 2 * by_name["baseline_prior"]


def test_final_model_is_best_validation_pr_auc(trained) -> None:
    candidates, _, X_val, y_val = trained
    table = ev.compare_candidates(candidates, X_val, y_val)
    assert ev.select_final(table) == table.loc[table["pr_auc"].idxmax(), "model"]


def test_confusion_counts_add_up(trained) -> None:
    candidates, _, X_val, y_val = trained
    counts = ev.metrics_at_threshold(y_val, ev.fraud_scores(candidates[2], X_val), 0.5)
    assert counts["tp"] + counts["fp"] + counts["fn"] + counts["tn"] == len(y_val)
    assert counts["tp"] + counts["fn"] == int(y_val.sum())


def test_mlp_history_and_wrapper(trained) -> None:
    candidates, history, _, _ = trained
    assert len(history.train_loss) == len(history.val_pr_auc)
    assert 1 <= history.best_epoch <= len(history.val_pr_auc)
    wrapper = candidates[3].pipeline.named_steps["model"]
    assert not hasattr(wrapper, "predict")  # decisions only through the metadata threshold
    with pytest.raises(NotImplementedError):
        wrapper.fit(None)


def _metadata(threshold: float = 0.5) -> dict:
    return {"model_name": "random_forest", "threshold": threshold, "split": {"seed": SEED},
            "model_input_columns": list(MODEL_INPUT_COLUMNS)}


def test_save_then_reload_gives_same_scores(trained, tmp_path) -> None:
    candidates, _, X_val, _ = trained
    forest = candidates[2]
    save_model(forest.pipeline, _metadata(), tmp_path / "p.joblib", tmp_path / "m.json")
    pipeline, metadata = load_model(tmp_path / "p.joblib", tmp_path / "m.json")
    # Same model: equal up to float rounding (parallel trees sum their votes in varying order)
    np.testing.assert_allclose(
        forest.pipeline.predict_proba(X_val), pipeline.predict_proba(X_val), rtol=0, atol=1e-12
    )
    assert metadata["model_name"] == "random_forest" and "saved_at" in metadata


@pytest.mark.parametrize("metadata, message", [
    (_metadata(threshold=1.5), "threshold"),
    ({"model_name": "x", "threshold": 0.5}, "missing"),
])
def test_bad_metadata_is_refused(trained, tmp_path, metadata: dict, message: str) -> None:
    with pytest.raises(ModelIOError, match=message):
        save_model(trained[0][2].pipeline, metadata, tmp_path / "p.joblib", tmp_path / "m.json")