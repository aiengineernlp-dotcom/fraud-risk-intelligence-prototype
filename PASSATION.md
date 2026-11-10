# PASSATION — fraud-risk-intelligence-prototype

> The handover note at the project's bedside. Any agent or chat that arrives reads it first; any agent or chat that leaves updates it.
> §1 to §7: rewritten at each departure. §8: one line added, never erased.
> No secret, no real data, no internal information.

## 1. OÙ ON EN EST
- Phase : Phase 1 – J3 Modèles · mode de build : guidé
- Tâche ou séance en cours : J3, séance 1 — ouverture courte (§0bis) puis n° 16 `src/data/split.py`
- Arrêtée exactement à : J2 FROZEN (commit `364b660`, tag `vj2-donnees-frozen`) ; J3 pas encore commencé
- Branche / pull request : `main`, rien d'ouvert ; git status propre
- Décisions héritées du J2 à ne pas rediscuter : PR-AUC et F1 comme métriques principales ; analyse VIF avant feature engineering ; feature `is_risky_type` (TRANSFER+CASH_OUT uniquement) ; `isFlaggedFraud` gardé dans le schéma pour détecter la fuite de cible, jamais utilisé comme feature ; `artifacts/models/` ignoré de git, `metrics/` et `figures/` versionnés (D-15)
- Supposé à tester au début du J3 : `torch` s'importe et s'entraîne correctement sur cette machine — risque si faux : J3 MLP bloqué

## 2. FAIT — AVEC PREUVE
- [x] J1 : fichiers 01 à 08 — preuve : commit `6f6c050`, tag `vj1-cadrage-frozen`, empreintes SHA-256 dans Journal_Build.md
- [x] Handoff du J2 (2026-11-04) — preuve : `git describe` → `vj1-cadrage-frozen`, `git status` vide, `load_config` OK, `pytest --co -q` sans erreur
- [x] PaySim dans `data/raw/PS_20174392719_1491204439457_log.csv` (471 Mo) — preuve : SHA-256 `16910f90…e4eea6b`, ignoré par `.gitignore`
- [x] n° 09 `src/data/schema.py` Temps 1 + Temps 2 ✅ — preuve : SHA-256 `2d9c90bf…`, 7 questions validées 2026-11-07
- [x] n° 10 `src/data/load_paysim.py` Temps 1 + Temps 2 ✅ — preuve : Shape (6 362 620, 11), schéma validé, Python 3.13.9
- [x] n° 11 `tests/conftest.py` Temps 1 + Temps 2 ✅
- [x] n° 12 `tests/test_data_schema.py` Temps 1 + Temps 2 ✅ — preuve : pytest vert
- [x] n° 13 `src/data/eda.py` Temps 1 + Temps 2 ✅ — preuve : 6 PNG dans `artifacts/figures/`
- [x] n° 14 `notebooks/01_eda.ipynb` Temps 1 + Temps 2 ✅ — preuve : nbconvert exécuté, 6 figures affichées
- [x] n° 15 `data/README.md` Temps 1 + Temps 2 ✅ — preuve : fiche PaySim complète, déplacée de `src/data/`
- [x] Freeze J2 — preuve : commit `364b660`, tag `vj2-donnees-frozen`, poussés

## 3. RESTE À FAIRE — dans l'ordre, la prochaine en premier
- [ ] Ouverture courte J3 (§0bis) — vue d'ensemble des fichiers n°16 à 28
- [ ] n° 16 `src/data/split.py` — stratified train/val/test split
- [ ] n° 17 `tests/test_split.py`
- [ ] n° 18 `src/features/build_features.py` — VIF + is_risky_type
- [ ] n° 19 `tests/test_features.py`
- [ ] n° 20 `src/models/model_io.py`
- [ ] n° 21 `src/models/train_classical.py`
- [ ] n° 22 `src/models/train_mlp.py`
- [ ] n° 23 `src/models/evaluate.py`
- [ ] n° 24 `src/models/threshold.py`
- [ ] n° 25 `tests/test_threshold.py`
- [ ] n° 26 `src/models/explain.py`
- [ ] n° 27 `src/train.py`
- [ ] n° 28 `tests/test_models.py`
- [ ] `Donnees_et_Modeles.md` partie modèles ; `Rapport_Technique.md` sections données + modèles
- [ ] Freeze J3 (tag `vj3-modeles-frozen`)

## 4. VÉRIFIÉ / SUPPOSÉ
- Vérifié : PaySim — 11 colonnes, 6 362 620 lignes, taux de fraude ~0,13 %, TRANSFER+CASH_OUT seulement pour fraude, corrélation 1,00 oldbalanceOrg/newbalanceOrig, aucun null
- Vérifié : la clé n'apparaît jamais dans les journaux — essai avec fausse clé, 2026-11-04
- Supposé : la mémoire suffit pour charger PaySim en entier (I05 : sous-échantillon stratifié en repli)
- Supposé : `torch` s'importe et s'entraîne correctement sur cette machine — à tester au début du J3

## 5. ÉCHECS — NE PAS REFAIRE · INCIDENTS
- Incident : 2026-11-04 disque plein → `pip install --no-cache-dir`
- Incident : 2026-11-04 `.venv` créé en Python 3.13 au lieu de 3.11 → 3.13 gardé (I22)
- Échec : `conda deactivate` avant de créer le `.venv` → vérifier `python3 --version` avant `python3 -m venv`
- Échec : `schema.py` collé dans `data/` au lieu de `src/data/` → vérifier le chemin exact avant de coller
- Incident : notebook `01_eda.ipynb` corrompu par PyCharm (JSON stocké comme code) → toujours exécuter avec `jupyter nbconvert --to notebook --execute`, jamais Run dans PyCharm
- Incident : contexte Claude compressé avant la fin du J2 → J3 a failli démarrer dans le même chat ; détecté par Erman ; règle AS-07 ajoutée
- Attention : un terminal ouvert en conda (`pre_learn_1`) n'est pas le `.venv` ; toujours `source .venv/bin/activate` puis `python --version` (attendu : 3.13.9)

## 6. QUESTIONS ET PROPOSITIONS POUR LE FONDATEUR
- Q-01 Date exacte de la remise (week-end du 14-15 nov.) — bloquante : non (nécessaire pour recaler le planning)
- Q-02 Décision vibe coding J4 (I32, 🔵 Hypothèse) — à trancher au Freeze J3
- Q-03 `ermanw` et `Tony-237` à ajouter dans `99_PRIVE/MOTS_SENSIBLES_C10.txt` — en attente réponse Erman

## 7. PROCHAINE SÉANCE — LA TÂCHE DU PROCHAIN (même format dans les deux modes — v2.14.0)
- Tâche : Phase 1 – J3 Modèles — ouverture courte (§0bis), puis n° 16 `src/data/split.py`
- Critère de fin : tous les fichiers n°16 à 28 livrés, Temps 2 ✅, pytest vert, Freeze J3
- Fichiers autorisés : `src/data/split.py`, `tests/test_split.py`, `src/features/build_features.py`, `tests/test_features.py`, `src/models/model_io.py`, `src/models/train_classical.py`, `src/models/train_mlp.py`, `src/models/evaluate.py`, `src/models/threshold.py`, `tests/test_threshold.py`, `src/models/explain.py`, `src/train.py`, `tests/test_models.py` ; générés : `artifacts/models/` (3 fichiers), `artifacts/metrics/` (4 fichiers)
- À lire d'abord : ce fichier ; `Build_Control.md` (J3) ; `Architecture_Projet.md` v1.1 §8 (n°16 à 28) ; `Matrice_Conformite.md` R076 et suivants ; `Donnees_et_Modeles.md` (décisions J3)
- Préalables : `.venv` activé ; pytest J2 100 % vert avant tout nouveau fichier

## 8. JOURNAL DES PASSAGES — ajout seul
| Date | Qui (outil, modèle si connu) | Mode | Ce qui a été fait | Commit / pull request | Statut laissé |
|---|---|---|---|---|---|
| 2026-11-04 | Claude (chat « Capstone · M3 · J1 session 1 ») | guidé | J1 : fichiers 01 à 08, Temps 1 et Temps 2 ✅, Freeze | commit `6f6c050`, tag `vj1-cadrage-frozen` | validé par le fondateur le 2026-11-04 |
| 2026-11-06 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : Handoff, préalables (disque, PaySim), ouverture courte ✅ | — | en cours |
| 2026-11-06 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : n° 09 posé, Temps 1 ✅ ; Temps 2 posé, en attente des réponses | — | en cours |
| 2026-11-07 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : propositions v2.15.6 appliquées ; n° 09 Temps 2 ✅ | — | en cours |
| 2026-11-10 | Claude (chat « Capstone · M5 · Phase 1 – J2 données ») | guidé | J2 (suite) : n° 10 load_paysim.py ✅ ; n° 11 conftest.py ✅ ; n° 12 test_data_schema.py ✅ ; n° 13 eda.py ✅ ; n° 14 01_eda.ipynb ✅ ; n° 15 data/README.md ✅ ; Freeze J2 | commit `364b660`, tag `vj2-donnees-frozen` | J2 FROZEN — J3 à démarrer dans nouveau chat M5 |
| 2026-11-10 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | Fin J2 : AS-07/AS-08/AS-09 dans AMELIORATION_SYSTEME.md ; message de reprise M5 produit ; PASSATION mise à jour | — | prêt à fermer |
