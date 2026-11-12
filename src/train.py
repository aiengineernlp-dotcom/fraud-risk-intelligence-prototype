"""
SoC layer      : Training (ML) — entry point: python -m src.train
Responsibility : Run the whole J3 chain in order with one command: load -> split -> candidates ->
                 final model and threshold on validation -> explanation on validation -> ONE test
                 evaluation -> metrics, figures, saved model with its metadata
Never does     : Hold a setting (all values come from configs/settings.yaml); open the test part
                 before the final model and threshold are fixed (R103); decide anything for the agent
Reference      : Architecture_Projet.md v1.1 — section 7, section 8 (n° 27); D-12, D-13;
                 Points_A_Trancher I08, I09, I10, I34–I38; Matrice_Conformite.md R103, R182–R186
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import load_config
from src.data.load_paysim import load_raw
from src.data.split import stratified_split
from src.features.build_features import EXCLUDED_COLUMNS, MODEL_INPUT_COLUMNS, split_xy
from src.logging_setup import setup_logging
from src.models import evaluate as ev
from src.models.explain import error_table, permutation_table, plot_importance
from src.models.model_io import save_model
from src.models.threshold import choose_threshold, daily_volume, threshold_table
from src.models.train_classical import TRAIN_SAMPLE_ROWS, train_classical
from src.models.train_mlp import save_mlp_state, train_mlp


def main() -> dict[str, Any]:
    config = load_config()
    log = setup_logging(config)
    paths, split_cfg = config.paths, config.split

    # 1. Data and split (seed and shares from settings.yaml, I34)
    log.info("Loading PaySim")
    frame = load_raw()
    per_day = daily_volume(frame)
    parts = stratified_split(frame, val_size=split_cfg.val_size,
                             test_size=split_cfg.test_size, seed=split_cfg.seed)
    X_train, y_train = split_xy(parts.train)
    X_val, y_val = split_xy(parts.validation)

    # 2. Candidates, all fitted on train only (n° 21, n° 22)
    log.info("Training classical candidates")
    candidates = train_classical(X_train, y_train, X_val, y_val, seed=split_cfg.seed)
    log.info("Training the MLP")
    mlp, history = train_mlp(X_train, y_train, X_val, y_val, seed=split_cfg.seed)
    candidates.append(mlp)

    # 3. Final model and threshold, chosen on VALIDATION (I09, I08)
    table = ev.compare_candidates(candidates, X_val, y_val)
    final = next(c for c in candidates if c.name == ev.select_final(table))
    val_scores = ev.fraud_scores(final, X_val)
    choice = choose_threshold(y_val, val_scores, capacity_per_day=config.review_capacity_per_day,
                              transactions_per_day=per_day)
    trade_off = threshold_table(y_val, val_scores, transactions_per_day=per_day)
    log.info("Final model %s, threshold %.4f", final.name, choice.threshold)

    # 4. Explanation, on validation (I10)
    importance = permutation_table(final, X_val, y_val, seed=split_cfg.seed)
    errors = error_table(final, X_val, y_val, choice.threshold)

    # 5. The ONE look at the test part (R103): everything above is now fixed
    X_test, y_test = split_xy(parts.test)
    test_results = ev.evaluate_on_test(final, X_test, y_test, choice.threshold)
    log.info("Test: PR-AUC %.4f, recall %.4f, precision %.4f",
             test_results["pr_auc"], test_results["recall"], test_results["precision"])

    # 6. Metrics (artifacts/metrics/, versioned) and figures (artifacts/figures/, versioned)
    paths.metrics_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(paths.metrics_dir / "comparison_table.csv", index=False)
    trade_off.to_csv(paths.metrics_dir / "threshold_analysis.csv", index=False)
    errors.to_csv(paths.metrics_dir / "error_analysis.csv", index=False)
    _write_json(paths.metrics_dir / "test_results.json", test_results)
    ev.plot_precision_recall(candidates, X_val, y_val,
                             paths.figures_dir / "fig07_precision_recall_threshold.png",
                             final.name, choice.threshold)
    ev.plot_confusion(test_results, paths.figures_dir / "fig08_confusion_matrix.png")
    plot_importance(importance, paths.figures_dir / "fig09_permutation_importance.png")
    ev.plot_learning_curve(history, paths.figures_dir / "fig10_mlp_learning_curves.png")

    # 7. Saved model and its metadata (artifacts/models/, not versioned, D-15)
    metadata = {
        "model_name": final.name,
        "params": final.params,
        "threshold": choice.threshold,
        "split": {"strategy": "stratified", "seed": split_cfg.seed,
                  "val_size": split_cfg.val_size, "test_size": split_cfg.test_size},
        "train_rows": TRAIN_SAMPLE_ROWS,
        "model_input_columns": list(MODEL_INPUT_COLUMNS),
        "excluded_columns": list(EXCLUDED_COLUMNS),
        "objective": {"review_capacity_per_day": config.review_capacity_per_day,
                      "transactions_per_day": round(per_day),
                      "alert_share": choice.alert_share,
                      "near_threshold_margin": config.near_threshold_margin},
        "validation_at_threshold": choice.validation,
        "risk_band_bounds": None,  # fixed at J4 (risk_bands.py, n° 40)
    }
    written = save_model(final.pipeline, metadata, paths.model_pipeline, paths.model_metadata)
    save_mlp_state(mlp, paths.mlp_state)
    log.info("Saved %s and its metadata", final.name)
    return {"metadata": written, "test_results": test_results}


def _write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(json.dumps(content, indent=2, sort_keys=True,
                               default=lambda value: value.item()), encoding="utf-8")


if __name__ == "__main__":
    main()