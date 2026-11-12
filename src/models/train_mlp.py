"""
SoC layer      : Training (ML)
Responsibility : Train a small PyTorch MLP on the preprocessed train part (weighted loss for the
                 0.13 % fraud rate, early stopping on validation PR-AUC, fixed seeds) and wrap it with
                 predict_proba so it plugs into the same pipeline as the classical models
Never does     : Touch the test part (R103); choose the threshold (n° 24); write files, except the
                 network weights through save_mlp_state (called by train.py)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 22), D-13; Points_A_Trancher I38, I05;
                 Matrice_Conformite.md R097, R103
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from torch import nn

from src.features.build_features import build_preprocessor
from src.models.train_classical import TRAIN_SAMPLE_ROWS, Candidate, sample_train

# --- Network and training settings (I38) ---------------------------------------
HIDDEN = (32, 16)
DROPOUT = 0.1
LEARNING_RATE = 1e-3
BATCH_SIZE = 2048
MAX_EPOCHS = 50  # I38 revised: at 20 the best epoch was the last one (still improving)
PATIENCE = 5     # epochs without a better validation PR-AUC before stopping

def _network(n_inputs: int) -> nn.Sequential:
    layers: list[nn.Module] = []
    width = n_inputs
    for hidden in HIDDEN:
        layers += [nn.Linear(width, hidden), nn.ReLU(), nn.Dropout(DROPOUT)]
        width = hidden
    layers.append(nn.Linear(width, 1))  # one logit: the fraud score before the sigmoid
    return nn.Sequential(*layers)


class TorchMLPClassifier(BaseEstimator, ClassifierMixin):
    """A fitted network seen as a scikit-learn model: model_io.py and the agent only need
    predict_proba. No predict(): decisions use the threshold from model_metadata.json."""

    def __init__(self, network: nn.Module | None = None) -> None:
        self.network = network

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> TorchMLPClassifier:
        """Required by scikit-learn to accept this object as a model. Not used: the network is
        trained by train_mlp(), because early stopping needs the validation part."""
        raise NotImplementedError("Train the network with train_mlp(); this wrapper only scores")

    def __sklearn_is_fitted__(self) -> bool:
        return self.network is not None

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self.network.eval()
        with torch.no_grad():
            logits = self.network(torch.as_tensor(np.asarray(X, dtype=np.float32))).squeeze(1)
        fraud = torch.sigmoid(logits).numpy()
        return np.column_stack([1.0 - fraud, fraud])


@dataclass(frozen=True)
class MLPHistory:
    train_loss: list[float]   # one value per epoch (learning curve)
    val_pr_auc: list[float]   # one value per epoch (early-stopping signal)
    best_epoch: int


def train_mlp(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    *,
    seed: int,
    train_rows: int = TRAIN_SAMPLE_ROWS,
) -> tuple[Candidate, MLPHistory]:
    """Fit the preprocessor on train, train the network epoch by epoch, keep the epoch with the
    best validation PR-AUC, stop after PATIENCE epochs without progress."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    X_fit, y_fit = sample_train(X_train, y_train, train_rows, seed)
    preprocessor = build_preprocessor().fit(X_fit)  # fit on train only (R097)
    Z_fit = torch.as_tensor(preprocessor.transform(X_fit), dtype=torch.float32)
    target = torch.tensor(y_fit.to_numpy(), dtype=torch.float32)  # a copy: writable, no warning
    Z_val = preprocessor.transform(X_val)

    network = _network(Z_fit.shape[1])
    n_frauds = float(target.sum())
    pos_weight = torch.tensor((len(target) - n_frauds) / n_frauds)  # ~775: one fraud ~ 775 rows
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(network.parameters(), lr=LEARNING_RATE)
    generator = torch.Generator().manual_seed(seed)

    train_loss: list[float] = []
    val_scores: list[float] = []
    best_score, best_state, best_epoch, waited = -1.0, None, 0, 0
    for epoch in range(1, MAX_EPOCHS + 1):
        network.train()
        total = 0.0
        order = torch.randperm(len(target), generator=generator)
        for start in range(0, len(order), BATCH_SIZE):
            batch = order[start:start + BATCH_SIZE]
            optimizer.zero_grad()
            loss = loss_fn(network(Z_fit[batch]).squeeze(1), target[batch])
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch)
        train_loss.append(total / len(target))

        scores = TorchMLPClassifier(network).predict_proba(Z_val)[:, 1]
        score = float(average_precision_score(y_val, scores))
        val_scores.append(score)
        if score > best_score:
            best_score, best_state, best_epoch, waited = score, copy.deepcopy(
                network.state_dict()), epoch, 0
        else:
            waited += 1
            if waited >= PATIENCE:
                break  # early stopping

    network.load_state_dict(best_state)
    pipeline = Pipeline([("features", preprocessor), ("model", TorchMLPClassifier(network))])
    params = {"hidden": list(HIDDEN), "dropout": DROPOUT, "best_epoch": best_epoch}
    return Candidate("mlp", pipeline, params, best_score), MLPHistory(
        train_loss, val_scores, best_epoch)


def save_mlp_state(candidate: Candidate, path: Path) -> None:
    """Write the network weights (artifacts/models/mlp_state.pt), called by train.py."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(candidate.pipeline.named_steps["model"].network.state_dict(), path)