"""
Couche SoC    : Transverse — Infrastructure de test
Responsabilité : Fournir les fixtures pytest partagées entre tous les tests du projet.
Ne fait jamais : Tester une logique métier ; charger le vrai fichier PaySim.
Référence      : Architecture_Projet.md v1.1 §8 (n° 11)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

# Colonnes du contrat PaySim (ordre du CSV, brief §4.1)
_COLUMNS = [
    "step", "type", "amount", "nameOrig",
    "oldbalanceOrg", "newbalanceOrig",
    "nameDest", "oldbalanceDest", "newbalanceDest",
    "isFraud", "isFlaggedFraud",
]

_ROWS = [
    [1, "PAYMENT",  9839.64, "C1231006815", 170136.0, 160296.36, "M1979787155", 0.0,      0.0,      0, 0],
    [1, "PAYMENT",  1864.28, "C1666544295",  21249.0,  19384.72, "M2044282225", 0.0,      0.0,      0, 0],
    [1, "TRANSFER", 181.0,   "C1305486145",    181.0,      0.0,  "C553264065",  0.0,      0.0,      1, 0],
    [1, "CASH_OUT", 181.0,   "C840083671",     181.0,      0.0,  "C38997010",   21182.0,  0.0,      1, 0],
    [1, "PAYMENT",  11668.14,"C2048537720", 41554.0,  29885.86,  "M1230701703", 0.0,      0.0,      0, 0],
]


@pytest.fixture
def valid_paysim_csv(tmp_path: Path) -> Path:
    """CSV synthétique conforme au contrat (5 lignes, 11 colonnes)."""
    df = pd.DataFrame(_ROWS, columns=_COLUMNS)
    path = tmp_path / "paysim_valid.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def invalid_paysim_csv(tmp_path: Path) -> Path:
    """CSV synthétique sans la colonne isFraud (contrat violé)."""
    cols_without_target = [c for c in _COLUMNS if c != "isFraud"]
    df = pd.DataFrame(
        [[row[i] for i, c in enumerate(_COLUMNS) if c != "isFraud"] for row in _ROWS],
        columns=cols_without_target,
    )
    path = tmp_path / "paysim_invalid.csv"
    df.to_csv(path, index=False)
    return path