"""
Couche SoC    : Couche 1 — Data (chargement des données brutes)
Responsabilité : Charger le fichier brut PaySim et valider son schéma.
Ne fait jamais : Transformation, filtrage, prétraitement, feature engineering.
Référence      : 03_Architecture_Globale_ML.md §2 ; Donnees_et_Modeles.md §1
"""
# load_paysim.py — n° 10
# Utilisé par : eda.py (n° 11, n° 13), split.py (n° 16).

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.schema import DTYPES, validate_frame

_DEFAULT_PATH = Path("data/raw/PS_20174392719_1491204439457_log.csv")


def load_raw(path: str | Path | None = None) -> pd.DataFrame:
    """Charge le CSV brut PaySim et valide son schéma.

    Parameters
    ----------
    path : str, Path ou None
        Chemin vers le fichier CSV.
        Si None, utilise le chemin par défaut ``data/raw/PS_..._log.csv``.

    Returns
    -------
    pd.DataFrame
        DataFrame brut (6 362 620 lignes × 11 colonnes, *provisoire*).

    Raises
    ------
    FileNotFoundError
        Si le fichier est introuvable au chemin donné.
    SchemaError
        Si le schéma du fichier ne correspond pas au contrat (schema.py).
    """
    csv_path = Path(path) if path is not None else _DEFAULT_PATH

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Fichier PaySim introuvable : {csv_path}\n"
            "Vérifier que data/raw/ contient le CSV et que le chemin est correct."
        )

    df = pd.read_csv(csv_path, dtype=DTYPES)
    validate_frame(df)   # lève SchemaError si KO
    return df