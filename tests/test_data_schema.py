"""
Couche SoC    : Transverse — Tests
Responsabilité : Vérifier le contrat de load_paysim.py et schema.py.
Ne fait jamais : Charger le vrai fichier PaySim ; tester la logique métier.
Référence      : Architecture_Projet.md v1.1 §8 (n° 12) ; Matrice_Conformite.md R051–R053
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data.load_paysim import load_raw
from src.data.schema import COLUMNS, SchemaError, validate_frame


# ---------------------------------------------------------------------------
# Chemin heureux
# ---------------------------------------------------------------------------

def test_load_raw_valid(valid_paysim_csv: Path) -> None:
    """load_raw() accepte un CSV conforme et retourne un DataFrame."""
    df = load_raw(valid_paysim_csv)
    assert isinstance(df, pd.DataFrame)


def test_load_raw_shape(valid_paysim_csv: Path) -> None:
    """Le DataFrame synthétique a exactement 5 lignes et 11 colonnes."""
    df = load_raw(valid_paysim_csv)
    assert df.shape == (5, 11)


def test_load_raw_columns(valid_paysim_csv: Path) -> None:
    """Les colonnes sont présentes dans le bon ordre."""
    df = load_raw(valid_paysim_csv)
    expected = [spec.name for spec in COLUMNS]
    assert list(df.columns) == expected


# ---------------------------------------------------------------------------
# Chemins d'erreur
# ---------------------------------------------------------------------------

def test_load_raw_invalid(invalid_paysim_csv: Path) -> None:
    """load_raw() lève SchemaError si une colonne du contrat est absente."""
    with pytest.raises(SchemaError):
        load_raw(invalid_paysim_csv)


def test_load_raw_not_found() -> None:
    """load_raw() lève FileNotFoundError si le fichier est introuvable."""
    with pytest.raises(FileNotFoundError):
        load_raw("fichier_qui_nexiste_pas.csv")


def test_validate_frame_target(valid_paysim_csv: Path) -> None:
    """validate_frame lève SchemaError si la cible contient un NaN."""
    df = load_raw(valid_paysim_csv)
    df_bad = df.copy()
    df_bad.loc[0, "isFraud"] = np.nan
    # Forcer le dtype en float pour accepter NaN
    df_bad["isFraud"] = df_bad["isFraud"].astype(float)
    with pytest.raises(SchemaError):
        validate_frame(df_bad)