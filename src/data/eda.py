"""
Couche SoC    : Couche 1 — Data (analyse exploratoire)
Responsabilité : Produire les 6 figures EDA du J2 à partir du DataFrame brut PaySim.
Ne fait jamais : Modifier les données ; entraîner un modèle ; afficher les figures
                 à l'écran (savefig uniquement) ; accéder directement au CSV.
Référence      : Architecture_Projet.md v1.1 §8 (n° 13) ; Matrice_Conformite.md R056–R075 ;
                 03_Architecture_Globale_ML.md §4 (chaque figure = ce qu'elle montre +
                 ce que ça veut dire + la décision qu'elle entraîne)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.load_paysim import load_raw
from src.data.schema import TARGET_COLUMN

# Répertoire de sortie par défaut
_DEFAULT_OUTPUT = Path("artifacts/figures")

# Palette accessible daltonisme (colorblind-safe)
_COLOR_OK = "#2196F3"      # bleu — transactions normales
_COLOR_FRAUD = "#F44336"   # rouge — fraudes


def plot_class_balance(df: pd.DataFrame, output_dir: Path) -> Path:
    """Fig 01 — Déséquilibre des classes.

    Montre : proportion fraudes vs non-fraudes.
    Signification métier : le modèle verra ~0,13 % de fraudes → accuracy inutile,
                           PR-AUC et F1 sont les métriques cibles.
    Décision : utiliser class_weight='balanced' ou suréchantillonnage dans le pipeline.
    """
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    labels = ["Non-fraude (0)", "Fraude (1)"]
    colors = [_COLOR_OK, _COLOR_FRAUD]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, counts.values, color=colors, edgecolor="white", linewidth=0.8)
    ax.bar_label(bars, fmt="{:,.0f}", padding=4, fontsize=9)
    ax.set_title("Fig 01 — Déséquilibre des classes", fontsize=11, fontweight="bold")
    ax.set_ylabel("Nombre de transactions")
    ax.set_xlabel("")
    pct = counts[1] / counts.sum() * 100
    ax.text(0.98, 0.95, f"Fraudes : {pct:.2f} %",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF9C4", edgecolor="#F9A825"))
    fig.tight_layout()
    out = output_dir / "fig01_class_balance.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_transaction_types(df: pd.DataFrame, output_dir: Path) -> Path:
    """Fig 02 — Volume par type de transaction.

    Montre : répartition des 5 types (CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER).
    Signification métier : TRANSFER et CASH_OUT concentrent presque toutes les fraudes.
    Décision : `type` sera une variable catégorielle encodée dans le pipeline.
    """
    counts = df["type"].value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(counts.index, counts.values, color=_COLOR_OK,
                   edgecolor="white", linewidth=0.8)
    ax.bar_label(bars, fmt="{:,.0f}", padding=4, fontsize=9)
    ax.set_title("Fig 02 — Volume par type de transaction", fontsize=11, fontweight="bold")
    ax.set_xlabel("Nombre de transactions")
    fig.tight_layout()
    out = output_dir / "fig02_transaction_types.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_amount_distribution(df: pd.DataFrame, output_dir: Path) -> Path:
    """Fig 03 — Distribution des montants (échelle log).

    Montre : distribution très asymétrique des montants (longue queue à droite).
    Signification métier : la plupart des transactions sont petites ;
                           les fraudes tendent à concentrer des montants élevés.
    Décision : appliquer log1p(amount) dans le pipeline de prétraitement.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Brut
    axes[0].hist(df["amount"], bins=100, color=_COLOR_OK, edgecolor="none", alpha=0.8)
    axes[0].set_title("Montant brut", fontsize=10)
    axes[0].set_xlabel("amount")
    axes[0].set_ylabel("Fréquence")

    # Log1p
    axes[1].hist(np.log1p(df["amount"]), bins=100, color=_COLOR_OK,
                 edgecolor="none", alpha=0.8)
    axes[1].set_title("log1p(amount)", fontsize=10)
    axes[1].set_xlabel("log1p(amount)")

    fig.suptitle("Fig 03 — Distribution des montants", fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = output_dir / "fig03_amount_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_fraud_by_type(df: pd.DataFrame, output_dir: Path) -> Path:
    """Fig 04 — Taux de fraude par type de transaction.

    Montre : seuls TRANSFER et CASH_OUT contiennent des fraudes.
    Signification métier : les autres types (CASH_IN, DEBIT, PAYMENT) ne fraudent jamais.
    Décision : feature engineering possible — variable binaire `is_risky_type`.
    """
    fraud_rate = (
        df.groupby("type")[TARGET_COLUMN]
        .mean()
        .mul(100)
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [_COLOR_FRAUD if v > 0 else _COLOR_OK for v in fraud_rate.values]
    bars = ax.barh(fraud_rate.index, fraud_rate.values, color=colors,
                   edgecolor="white", linewidth=0.8)
    ax.bar_label(bars, fmt="{:.2f} %", padding=4, fontsize=9)
    ax.set_title("Fig 04 — Taux de fraude par type de transaction",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Taux de fraude (%)")
    fig.tight_layout()
    out = output_dir / "fig04_fraud_by_type.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_balance_errors(df: pd.DataFrame, output_dir: Path) -> Path:
    """Fig 05 — Erreurs de solde (indicateur de fraude simulateur).

    Montre : dans les transactions frauduleuses, le solde après ne diminue pas
             comme attendu (le simulateur laisse une trace).
    Signification métier : delta_orig = oldbalanceOrg - newbalanceOrig - amount
                           devrait être ≈ 0 ; un écart signal une anomalie.
    Décision : créer les features `error_balance_orig` et `error_balance_dest` au J3.
    """
    df2 = df.copy()
    df2["error_orig"] = df2["oldbalanceOrg"] - df2["newbalanceOrig"] - df2["amount"]
    df2["error_dest"] = df2["oldbalanceDest"] - df2["newbalanceDest"] + df2["amount"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, col, label in zip(
        axes,
        ["error_orig", "error_dest"],
        ["Erreur solde origine", "Erreur solde destination"],
    ):
        for val, color, lbl in [(0, _COLOR_OK, "Non-fraude"), (1, _COLOR_FRAUD, "Fraude")]:
            subset = df2[df2[TARGET_COLUMN] == val][col]
            ax.hist(np.log1p(subset.abs()), bins=80, alpha=0.6,
                    color=color, label=lbl, edgecolor="none")
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("log1p(|erreur|)")
        ax.set_ylabel("Fréquence")
        ax.legend(fontsize=8)

    fig.suptitle("Fig 05 — Erreurs de solde par classe", fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = output_dir / "fig05_balance_errors.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: Path) -> Path:
    """Fig 06 — Heatmap de corrélation des variables numériques.

    Montre : corrélations entre les 7 variables numériques + cible.
    Signification métier : oldbalanceOrg et newbalanceOrig sont très corrélées →
                           risque de redondance ; à surveiller au J3.
    Décision : pas de suppression automatique ici — l'analyse des VIF se fera au J3.
    """
    num_cols = [
        "step", "amount", "oldbalanceOrg", "newbalanceOrig",
        "oldbalanceDest", "newbalanceDest", TARGET_COLUMN,
    ]
    corr = df[num_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_xticks(range(len(num_cols)))
    ax.set_yticks(range(len(num_cols)))
    ax.set_xticklabels(num_cols, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(num_cols, fontsize=8)

    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}",
                    ha="center", va="center", fontsize=7,
                    color="white" if abs(corr.values[i, j]) > 0.6 else "black")

    ax.set_title("Fig 06 — Heatmap de corrélation", fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = output_dir / "fig06_correlation_heatmap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def run_eda(df: pd.DataFrame, output_dir: Path | None = None) -> list[Path]:
    """Lance les 6 analyses EDA et sauvegarde les figures.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame brut retourné par load_raw().
    output_dir : Path ou None
        Dossier de sortie. Par défaut : artifacts/figures/.

    Returns
    -------
    list[Path]
        Chemins des 6 fichiers PNG produits.
    """
    out = Path(output_dir) if output_dir is not None else _DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)

    figures = [
        plot_class_balance(df, out),
        plot_transaction_types(df, out),
        plot_amount_distribution(df, out),
        plot_fraud_by_type(df, out),
        plot_balance_errors(df, out),
        plot_correlation_heatmap(df, out),
    ]

    print(f"EDA terminée — {len(figures)} figures sauvegardées dans {out}/")
    for p in figures:
        print(f"  ✅ {p.name}")
    return figures