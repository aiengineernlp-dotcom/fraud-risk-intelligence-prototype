data/README.md
══════════════════════════════════════════════════════
 Couche SoC : Documentation — Contrat de données J2
 Rôle       : Fiche du jeu de données PaySim
 Consomme   : schema.py (n°09), load_paysim.py (n°10)
 Ne fait    : aucune transformation, aucun code
══════════════════════════════════════════════════════

[Flux]
  schema.py ──► data/README.md (documente REQUIRED_COLUMNS + DTYPES)
  load_paysim.py ──► data/README.md (documente le chemin attendu)
  01_eda.ipynb ──► data/README.md (documente les 3 décisions J3)

# Données — fraud-risk-intelligence-prototype

**Référence** : `Matrice_Conformite.md` R001–R010 ; `Donnees_et_Modeles.md` §1  
**Mise à jour** : 2026-11-10 (J2 — Phase 1 Données)

---

## Jeu de données : PaySim

| Champ | Valeur |
|-------|--------|
| Nom du fichier | `PS_20174392719_1491204399457_log.csv` |
| Emplacement | `data/raw/` |
| Taille | ~470 Mo |
| Lignes | 6 362 620 |
| Colonnes | 11 |
| Source | Kaggle — PaySim Synthetic Financial Dataset |
| Licence | CC BY-SA 4.0 |

---

## Colonnes et types (contrat `schema.py`)

| Colonne | Type pandas | Description |
|---------|-------------|-------------|
| `step` | `int64` | Unité de temps (1 step = 1 heure) |
| `type` | `object` | Type de transaction (PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN) |
| `amount` | `float64` | Montant de la transaction |
| `nameOrig` | `object` | Identifiant du compte émetteur |
| `oldbalanceOrg` | `float64` | Solde émetteur avant transaction |
| `newbalanceOrig` | `float64` | Solde émetteur après transaction |
| `nameDest` | `object` | Identifiant du compte destinataire |
| `oldbalanceDest` | `float64` | Solde destinataire avant transaction |
| `newbalanceDest` | `float64` | Solde destinataire après transaction |
| `isFraud` | `int64` | Cible : 1 = fraude, 0 = normal |
| `isFlaggedFraud` | `int64` | Flag interne PaySim (non utilisé comme cible) |

---

## Statistiques clés (EDA J2)

- **Taux de fraude** : ~0,13 % (8 213 fraudes / 6 362 620 transactions)
- **Types frauduleux** : TRANSFER (0,77 %) et CASH_OUT (0,18 %) uniquement
- **Colinéarité** : corrélation 1,00 entre `oldbalanceOrg` et `newbalanceOrig`
- **Valeurs nulles** : aucune

---

## Décisions J3 issues de l'EDA

1. **Métriques** : PR-AUC et F1 (accuracy inutile sur classes déséquilibrées)
2. **VIF** : analyser la colinéarité `oldbalanceOrg`/`newbalanceOrig` après split
3. **Feature** : envisager `is_risky_type` (TRANSFER ou CASH_OUT = 1)

---

## Règles d'utilisation

- Le fichier CSV brut ne doit **jamais** être modifié.
- Tout accès passe par `load_raw()` (`src/data/load_paysim.py`).
- Le fichier CSV est exclu du dépôt git (`.gitignore`).