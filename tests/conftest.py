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

@pytest.fixture
def db_conn(tmp_path: Path):
    """Base SQLite temporaire avec le schéma §10.2 (jamais data/runtime/) ; fermée après le test."""
    from src.storage.db import init_db

    conn = init_db(tmp_path / "test_capstone.db")
    yield conn
    conn.close()


@pytest.fixture
def small_paysim_csv(tmp_path: Path) -> Path:
    """CSV inventé de 200 lignes, sans hasard, conforme au contrat (pour scripts/build_demo_cases.py).

    1 ligne sur 10 a isFraud = 1 : le découpage stratifié trouve une fraude dans chaque partie.
    Les identifiants inventés (C + 7 chiffres) servent à vérifier qu'ils ne sortent jamais.
    """
    types = ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]
    rows = []
    for i in range(200):
        amount = 100.0 + 37.5 * i
        old_orig = 0.0 if i % 7 == 0 else amount * (1 + (i % 3))
        new_orig = 0.0 if i % 4 == 0 else max(old_orig - amount, 0.0)
        old_dest = 0.0 if i % 5 == 0 else 1000.0 + i
        new_dest = 0.0 if i % 5 == 0 else old_dest + amount
        rows.append([
            1 + i % 50, types[i % 5], amount, f"C{1000000 + i}",
            old_orig, new_orig, f"C{2000000 + i}", old_dest, new_dest,
            1 if i % 10 == 0 else 0, 0,
        ])
    path = tmp_path / "paysim_small.csv"
    pd.DataFrame(rows, columns=_COLUMNS).to_csv(path, index=False)
    return path
