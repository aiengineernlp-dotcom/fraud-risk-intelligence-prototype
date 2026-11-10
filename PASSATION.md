# PASSATION — fraud-risk-intelligence-prototype

> The handover note at the project's bedside. Any agent or chat that arrives reads it first; any agent or chat that leaves updates it.
> §1 to §7: rewritten at each departure. §8: one line added, never erased.
> No secret, no real data, no internal information.

## 1. OÙ ON EN EST
- Phase : Phase 1 – J2 données · mode de build : guidé
- Tâche ou séance en cours : J2, séance 1 — n° 09 `src/data/schema.py` ☑ (Temps 1 ✅, Temps 2 ✅ le 2026-11-07) ; prochain : libérer le disque (≥ 8 Go), puis `Donnees_et_Modeles.md` (partie données), puis n° 10 `src/data/load_paysim.py`
- Arrêtée exactement à : n° 09 terminé, pas encore commité (commit en fin de séance)
- Branche / pull request : `main`, rien d'ouvert ; non commités : `src/data/schema.py` (nouveau), `PASSATION.md` (modifié)
- Décisions de référence : `Architecture_Projet.md` v1.1 §4 (D-04, D-08, D-12, D-14, D-15), dans le dossier du projet (`00_ritual/`, hors dépôt) ; points ouverts : I04 (fiche PaySim, en partie) et I05 (mémoire) au J2 ; I08, I09, I10 au J3
- FAIT (2026-11-09) : étape a — état reconstitué en lecture seule : HEAD = origin/main = `6f6c050` (`vj1-cadrage-frozen`), index vide, aucun `.lock` ; non commités : `src/data/schema.py` (SHA-256 `2d9c90bf…` = Journal) et `PASSATION.md` ; PaySim intact (SHA-256 `16910f90…`, ignoré par `.gitignore:19`) ; disque : 5,9 Go libres (vue de la session, à confirmer par `df -h .` sur le Mac) — sous les 8 Go
- FAIT (2026-11-10) : rattrapage — collages du 2026-11-07 faits et vérifiés : §6 de `Donnees_et_Modeles.md`, I28-I29-I30, 2 entrées d'`AMELIORATION_SYSTEME.md` (replacées), case 🟡 du Build_Control (replacée ligne 135), statut J2 à jour, 2 lignes au Journal ; ancien chat lu en lecture seule par le navigateur intégré (compte tensoratech), reprise dans le compte aiengineernlp
- FAIT (2026-11-10) : étape b — 4 documents de défense ajoutés aux DOCUMENTS DE BUILD et au STATUT DES JALONS (Rapport_Technique J3→J6, décision A ; Script_Demo J5 ; Support_Presentation et Declaration_Contribution_IA J6) ; `verif_workspace.py` v2.17.2 (lancé depuis `09_SYSTEME/`, hors copie) `--projet` → 16 ✅ / 0 ❌, C18 ✅ ; pas de liste `--sensibles` pour l'instant (décision d'Erman)
- FAIT (2026-11-10) : étape c, disque (Q-01) — suppression complète : BioGPT-large, whisper/large-v3.pt, codex-runtimes, cache uv, cache Comet, acp-agents (PyCharm fermé) → 19+ Go libres (cible ≥ 8 Go ✅)
- FAIT (2026-11-10) : étape c, décisions — I31 ✅, I32 (×2, 🔵 Hypothèse) ✅, I33 ✅ collés dans Points_A_Trancher_INTERNE ; liste sensibles : fichier existant `99_PRIVE/MOTS_SENSIBLES_C10.txt` retenu (A) ; ajout de `ermanw` et `Tony-237` : en attente de réponse d'Erman

## 2. FAIT — AVEC PREUVE
- [x] J1 : fichiers 01 à 08 — preuve : commit du tag `vj1-cadrage-frozen`, empreintes SHA-256 dans le journal de build
- [x] Handoff du J2 (2026-11-04) — preuve : `git describe` → `vj1-cadrage-frozen`, `git status` vide, `load_config` OK, `pytest --co -q` sans erreur
- [x] PaySim dans `data/raw/PS_20174392719_1491204439457_log.csv` (471 Mo) — preuve : `ls -lh`, SHA-256 `16910f90…e4eea6b`, `git status` vide (fichier ignoré)
- [x] n° 09 `src/data/schema.py`, Temps 1 — preuve : vraie copie (1 000 lignes) acceptée ; colonne manquante, colonne en trop, cible = 2, montant négatif : refusés (2026-11-06)
- [x] n° 09 `src/data/schema.py`, Temps 2 — preuve : 7 questions validées le 2026-11-07, tracées dans le journal de build ; SHA-256 `2d9c90bf…`

## 3. RESTE À FAIRE — dans l'ordre, la prochaine en premier
- [ ] Libérer de nouveau de la place sur le disque (voir §6, Q-01) — critère de fin : `df -h .` montre au moins 8 Go libres
- [ ] `Donnees_et_Modeles.md`, partie données (document de build, hors dépôt) — critère de fin : rempli avant le n° 10
- [x] n° 10 `src/data/load_paysim.py`, Temps 1 ✅ (2026-11-10 : Shape (6 362 620, 11), schéma validé, Python 3.13.9) ; en cours : Temps 2
- [ ] n° 11 `tests/conftest.py`, n° 12 `tests/test_data_schema.py` — critère de fin : `pytest` vert
- [ ] n° 13 `src/data/eda.py`, n° 14 `notebooks/01_eda.ipynb` → figures fig01 à fig06 — critère de fin : 6 PNG dans `artifacts/figures/`
- [ ] n° 15 `data/README.md` (fiche du jeu de données) — critère de fin : sections R044 à R055 remplies depuis la copie téléchargée
- [ ] Freeze du J2 (tag `vj2-donnees-frozen`)

## 4. VÉRIFIÉ / SUPPOSÉ
- Vérifié : la copie PaySim a les 11 colonnes de l'énoncé, dans l'ordre ; `type` a exactement 5 valeurs ; `isFraud` et `isFlaggedFraud` valent seulement 0 ou 1 ; aucune case vide ; aucun nombre négatif — comment : lecture complète du CSV en ligne de commande, 2026-11-06 (les comptes eux-mêmes seront calculés et prouvés par `eda.py`, n° 13)
- Vérifié : la clé n'apparaît jamais dans l'affichage de la configuration ni dans les journaux — comment : essai avec une fausse clé, 2026-11-04
- Supposé : la mémoire suffit pour charger PaySim en entier — risque si c'est faux : J2 bloqué ; repli prévu : sous-échantillon stratifié pour développer (I05)
- Supposé : `torch` s'importe et s'entraîne correctement sur cette machine — risque si c'est faux : J3 (MLP) bloqué ; à tester au début du J3

## 5. ÉCHECS — NE PAS REFAIRE · INCIDENTS
- Incident : 2026-11-04 disque plein → installation faite avec `pip install --no-cache-dir`
- Incident : 2026-11-04 `.venv` créé en Python 3.13 au lieu de 3.11 → 3.13 gardé (I22)
- Échec : `conda deactivate` avant de créer le `.venv` → ne pas le refaire ; vérifier `python3 --version` avant `python3 -m venv`
- Échec : 2026-11-06 `schema.py` collé dans `data/` (données) au lieu de `src/data/` (code) → `No module named 'src.data.schema'` ; corrigé par `mv` ; vérifier le chemin exact avant de coller
- Incident : `data/schema.py` ajouté à l'index git (`git add`) avant d'être déplacé → `git status` montre `AD data/schema.py` → à nettoyer avec `git restore --staged data/schema.py` avant le commit de fin de séance
- Attention : un terminal ouvert dans un environnement conda (`pre_learn_1`) n'est pas le `.venv` ; toujours `source .venv/bin/activate` puis `python --version` (attendu : 3.13.9) avant une preuve

## 6. QUESTIONS ET PROPOSITIONS POUR LE FONDATEUR
- Q-01 Le disque est de nouveau presque plein (1,4 Go libres le 2026-11-06 au soir, après 16 Go le 2026-11-04) — libérer au moins 8 Go avant le n° 10 — bloquante : oui (pour le n° 10)
- Q-02 Recopier mot pour mot la licence, l'URL et le titre de la page Kaggle de PaySim (R044, R046) — bloquante : non (nécessaire avant le n° 15)
- Q-03 Date exacte de la remise (week-end du 14-15 nov.) — bloquante : non (nécessaire pour recaler le planning des jalons)

## 7. PROCHAINE SÉANCE — LA TÂCHE DU PROCHAIN (même format dans les deux modes — v2.14.0)
- Tâche : Phase 1 – J2 données — libérer le disque (≥ 8 Go), puis `Donnees_et_Modeles.md` (partie données), puis n° 10 `src/data/load_paysim.py`
- Critère de fin : `tests/test_data_schema.py` vert sur un petit jeu synthétique ; Temps 2 ✅ de chaque fichier
- Fichiers autorisés : `src/data/schema.py`, `src/data/load_paysim.py`, `tests/conftest.py`, `tests/test_data_schema.py`, `src/data/eda.py`, `notebooks/01_eda.ipynb`, `data/README.md` ; générés : `artifacts/figures/fig01_class_balance.png` à `fig06_correlation_heatmap.png`
- À lire d'abord : ce fichier ; `Architecture_Projet.md` v1.1 §8 (n° 09 à 15) ; `Matrice_Conformite.md` R040 à R075
- Préalables : `.venv` activé ; au moins 8 Go libres avant le n° 10

## 8. JOURNAL DES PASSAGES — ajout seul
| Date | Qui (outil, modèle si connu) | Mode | Ce qui a été fait | Commit / pull request | Statut laissé |
|---|---|---|---|---|---|
| 2026-11-04 | Claude (chat « Capstone · M3 · J1 session 1 ») | guidé | J1 : fichiers 01 à 08, Temps 1 et Temps 2 ✅, Freeze | commit du tag `vj1-cadrage-frozen` | validé par le fondateur le 2026-11-04 |
| 2026-11-06 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : Handoff, préalables (disque, PaySim), ouverture courte ✅ | — (pas encore de commit J2) | en cours |
| 2026-11-06 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : n° 09 posé, Temps 1 ✅ ; Temps 2 posé, en attente des réponses | — (commit en fin de séance) | en cours |
| 2026-11-07 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : propositions v2.15.6 appliquées ; n° 09 Temps 2 ✅ | — (commit en fin de séance) | en cours |
| 2026-11-10 | Claude (chat « Capstone · M5 · Phase 1 – J2 données ») | guidé | J2 (suite) : lecture fichiers contexte tensoratech ✅ ; DTYPES ajouté dans schema.py ; n° 10 load_paysim.py posé, Temps 1 ✅ (6 362 620 × 11, schéma validé) | — (commit en fin de séance) | en cours |
