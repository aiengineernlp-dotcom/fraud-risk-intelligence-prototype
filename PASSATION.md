# PASSATION — fraud-risk-intelligence-prototype

> The handover note at the project's bedside. Any agent or chat that arrives reads it first; any agent or chat that leaves updates it.
> §1 to §7: rewritten at each departure. §8: one line added, never erased.
> No secret, no real data, no internal information.

## 1. OÙ ON EN EST
- Phase : Phase 1 – J1 cadrage · mode de build : guidé
- Tâche ou séance en cours : J1, séance 1 — **terminée** ; J1 gelé (tag `vj1-cadrage-frozen`)
- Arrêtée exactement à : les 8 fichiers de configuration (registre n° 01 à 08) sont commités et vérifiés ; aucun fichier du J2 n'existe encore
- Branche / pull request : `main`, rien d'ouvert
- Décisions de référence : `Architecture_Projet.md` v1.1 §4 (D-04, D-08, D-12, D-14, D-15), dans le dossier du projet (`00_ritual/`, hors dépôt) ; points ouverts : I04 et I05 (J2), I08, I09, I10 (J3)

## 2. FAIT — AVEC PREUVE
- [x] `.gitignore`, `.env.example`, `requirements.txt`, `pyproject.toml`, `README.md` (§2 rempli), `configs/settings.yaml`, `src/config.py`, `src/logging_setup.py` — preuve : commit du tag `vj1-cadrage-frozen`, empreintes SHA-256 dans le journal de build
- [x] Environnement installé — preuve : `pip install -r requirements.txt` sans erreur (Python 3.13.9, 2026-11-04)
- [x] Configuration chargée — preuve : `load_config()` → provider `fake`, outils 2 nouvelles tentatives / 5 s, LLM 2 / 30 s ; journalisation active
- [x] `pytest --co -q` sans erreur (aucun test encore : les premiers arrivent au J2) ; `git status` ne montre ni `.venv/` ni `.env`

## 3. RESTE À FAIRE — dans l'ordre, la prochaine en premier
- [ ] J2 — ouverture courte (où le J2 se place, ce qu'il reçoit du J1, ce qu'il prépare pour le J3) — critère de fin : Temps 2 Q04 validé
- [ ] Déplacer la copie PaySim locale dans `data/raw/` (ignoré par git) — critère de fin : `ls data/raw/` montre le CSV, `git status` ne le montre pas
- [ ] n° 09 `src/data/schema.py`, n° 10 `src/data/load_paysim.py`, n° 11 `tests/conftest.py`, n° 12 `tests/test_data_schema.py` — critère de fin : `pytest` vert
- [ ] n° 13 `src/data/eda.py`, n° 14 `notebooks/01_eda.ipynb` → figures fig01 à fig06 — critère de fin : 6 PNG dans `artifacts/figures/`
- [ ] n° 15 `data/README.md` (fiche du jeu de données) — critère de fin : sections R044 à R055 remplies depuis la copie téléchargée
- [ ] Freeze du J2 (tag `vj2-donnees-frozen`)

## 4. VÉRIFIÉ / SUPPOSÉ
- Vérifié : toutes les versions de `requirements.txt` existent pour Python 3.11 et 3.13 sur macOS arm64 — comment : PyPI, 2026-11-04 ; installation réelle en 3.13.9
- Vérifié : la clé n'apparaît jamais dans l'affichage de la configuration ni dans les journaux (message, arguments, traceback) — comment : essai avec une fausse clé, 2026-11-04
- Supposé : la mémoire et le disque suffisent pour charger PaySim en entier — risque si c'est faux : J2 bloqué ; repli prévu : sous-échantillon stratifié pour développer (I05)
- Supposé : `torch` s'importe et s'entraîne correctement sur cette machine — risque si c'est faux : J3 (MLP) bloqué ; à tester au début du J3

## 5. ÉCHECS — NE PAS REFAIRE · INCIDENTS
- Incident : 2026-11-04 disque plein (60 Mo libres) → installation impossible → place libérée (3,9 Go) → installation faite avec `pip install --no-cache-dir`
- Incident : 2026-11-04 `.venv` créé en Python 3.13 au lieu de 3.11 → versions vérifiées pour les deux → 3.13 gardé (en-tête de `requirements.txt` et README mis à jour)
- Échec : `conda deactivate` avant de créer le `.venv` → change de Python sans le dire → ne pas le refaire ; vérifier `python3 --version` avant `python3 -m venv`

## 6. QUESTIONS ET PROPOSITIONS POUR LE FONDATEUR
- Q-01 Libérer au moins 8 Go avant le J2 (CSV de 471 Mo chargé en mémoire, figures, puis modèles au J3) — bloquante : oui
- Q-02 Recopier mot pour mot la licence affichée sur la page Kaggle de PaySim (R046) — bloquante : non (nécessaire avant le n° 15)

## 7. PROCHAINE SÉANCE — LA TÂCHE DU PROCHAIN (même format dans les deux modes — v2.14.0)
- Tâche : Phase 1 – J2 données — ouverture courte, puis n° 09 `src/data/schema.py` (colonnes requises, types, valeurs valides de la cible)
- Critère de fin : `tests/test_data_schema.py` vert sur un petit jeu synthétique ; Temps 2 ✅ de chaque fichier
- Fichiers autorisés : `src/data/schema.py`, `src/data/load_paysim.py`, `tests/conftest.py`, `tests/test_data_schema.py`, `src/data/eda.py`, `notebooks/01_eda.ipynb`, `data/README.md` ; générés : `artifacts/figures/fig01_class_balance.png` à `fig06_correlation_heatmap.png`
- À lire d'abord : ce fichier ; `Architecture_Projet.md` v1.1 §8 (n° 09 à 15) ; `Matrice_Conformite.md` R040 à R075
- Préalables : J1 FROZEN (`vj1-cadrage-frozen`) ; au moins 8 Go libres ; copie PaySim déplacée dans `data/raw/`

## 8. JOURNAL DES PASSAGES — ajout seul
| Date | Qui (outil, modèle si connu) | Mode | Ce qui a été fait | Commit / pull request | Statut laissé |
|---|---|---|---|---|---|
| 2026-11-04 | Claude (chat « Capstone · M3 · J1 session 1 ») | guidé | J1 : fichiers 01 à 08, Temps 1 et Temps 2 ✅, Freeze | commit du tag `vj1-cadrage-frozen` | validé par le fondateur le 2026-11-04 |