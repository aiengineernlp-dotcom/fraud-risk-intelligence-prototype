# PASSATION — fraud-risk-intelligence-prototype

> The handover note at the project's bedside. Any agent or chat that arrives reads it first; any agent or chat that leaves updates it.
> §1 to §7: rewritten at each departure. §8: one line added, never erased.
> No secret, no real data, no internal information.

## 1. OÙ ON EN EST
- Phase : Phase 1 – J3 Modèles **FROZEN** (tag `vj3-modeles-frozen`) · prochaine : Phase 1 – J4 Agent et LLM, **vibe coding contrôlé** (AS-15 : J3 non gelé le 2026-11-11 à 24 h)
- Arrêtée exactement à : gel du J3 (2026-11-12) ; J4 pas commencé
- Branche / pull request : `main` ; rien d'ouvert
- Décisions J3 à ne pas rediscuter : découpage stratifié 70/15/15, graine 42 dans `configs/settings.yaml` (I34) ; 12 variables, `newbalance…` retirées après VIF, `hour_of_day` au lieu de `step` (I36) ; modèle final Random Forest, choisi sur la PR-AUC de validation (I09) ; seuil 0,5492 pour 300 cas/jour, marge 0,05 (I08) ; permutation seule (I10) ; seuil et métadonnées seulement dans `model_metadata.json` (I20)
- Ouvert : 8 Temps 2 🟡 à reformuler avant l'oral (I39) ; `risk_band_bounds: null` → fixées au J4 (n° 40)

## 2. FAIT — AVEC PREUVE
- [x] J1, J2 FROZEN — tags `vj1-cadrage-frozen`, `vj2-donnees-frozen` (poussés)
- [x] J3 : n° 16 à 28 posés, Temps 1 ✅ ; n° 06 et n° 07 modifiés au J3 (porte G2 : sections `split`, `routing`) — empreintes SHA-256 dans `Journal_Build.md`
- [x] Tests : 40 passed (`.venv/bin/python -m pytest -q`, 2026-11-12)
- [x] Entraînement complet `python -m src.train` (2026-11-11, 3 min 56) — test, une seule fois : PR-AUC 0,908, rappel 0,863, précision 0,776, seuil 0,5492 (`artifacts/metrics/test_results.json`) ; fig07 à fig10 générées
- [x] `Donnees_et_Modeles.md` §4–§12 et `Preparation_Questions.md` (hors dépôt) remplis

## 3. RESTE À FAIRE — dans l'ordre, la prochaine en premier
- [ ] J4 : mise en place du vibe coding contrôlé (`02_BUILD/03_VIBE_CODING_CONTROLE.md` §2 : `main` protégée, accès de l'agent limité au dépôt, `AGENTS.md`, `docs/specs/`, CI qui lance les tests)
- [ ] J4 : n° 32 à 65 (agent, outils, validateur, LLM, orchestrateur), une pull request par petite tâche, Temps 2 dans le chat J4 avant chaque fusion
- [ ] J5 : n° 66 à 72 (+ corriger les manques C2 du J2 : `data/README.md` R049, R055, R064, R082 ; notebook R061–R074, chemin absolu `os.chdir`)
- [ ] J6 : README final, rapport, déclaration IA, présentation, vidéo
- [ ] Avant l'oral : les 8 🟡 (I39) et la simulation de défense

## 4. VÉRIFIÉ / SUPPOSÉ
- Vérifié : même graine → mêmes lignes (deux jours de suite) ; test ouvert une seule fois dans `train.py` (`X_test` n'existe qu'à l'étape 5)
- Vérifié : `torch 2.8.0` fonctionne dans le `.venv` — mais `requirements.txt` fixe `torch==2.15.0` : écart à corriger (installation chez l'enseignant)
- Supposé : `ruff` absent du `.venv` (formatage non lancé au gel)

## 5. ÉCHECS — NE PAS REFAIRE · INCIDENTS
- Le shell réactive conda (`(base)`, `(pre_learn_1)`) et `python` est un alias de `python3` → toujours lancer `.venv/bin/python …` (pytest compris : `.venv/bin/python -m pytest`)
- PyCharm utilise l'interpréteur `pre_learn_1 [3.11]` → le pointer sur `.venv/bin/python`
- `np.array_equal` sur une Random Forest parallèle échoue (ordre des additions) → `assert_allclose(atol=1e-12)`
- Wrapper PyTorch refusé par `Pipeline` sans `fit` → `fit` factice + `__sklearn_is_fitted__`
- Fichiers collés mais non sauvegardés (⌘S) : vérifier sur la machine avant le Temps 1
- Sous la pression du temps, réponses complétées par l'assistant validées ✅ → AS-17 : 🟡, jamais ✅

## 6. QUESTIONS ET PROPOSITIONS POUR LE FONDATEUR
- Q-01 Date et heure exactes de la remise (week-end du 14-15 nov.) — bloquante pour le plan J4–J6
- Q-02 Message à l'enseignant : travail seul accepté ? allègement possible (R177 : seulement par écrit) ?
- Q-03 `ermanw` et `Tony-237` à ajouter dans `99_PRIVE/MOTS_SENSIBLES_C10.txt`

## 7. PROCHAINE SÉANCE — LA TÂCHE DU PROCHAIN
- Tâche : Phase 1 – J4 Agent et LLM, nouveau chat (message dans `01_sessions/Prochain_message.md`) — Handoff (J3 FROZEN, 40 tests verts), ouverture courte, puis mise en place du vibe coding contrôlé
- Critère de fin : n° 32 à 65 fusionnés par pull request, Temps 2 de chaque pull request ✅, tests verts en CI, Freeze J4 (tag `vj4-agent-frozen`)
- Fichiers autorisés : n° 32 à 65 du registre (`Architecture_Projet.md` §8) ; `AGENTS.md`, `docs/specs/`, `.github/workflows/` (mise en place)
- À lire d'abord : ce fichier ; `02_BUILD/03_VIBE_CODING_CONTROLE.md` ; `Architecture_Projet.md` §3 (flux), §3bis (états), §8 (n° 32 à 65)
- Préalables : `.venv/bin/python -m pytest -q` → 40 passed

## 8. JOURNAL DES PASSAGES — ajout seul
| Date | Qui (outil, modèle si connu) | Mode | Ce qui a été fait | Commit / pull request | Statut laissé |
|---|---|---|---|---|---|
| 2026-11-04 | Claude (chat « Capstone · M3 · J1 session 1 ») | guidé | J1 : fichiers 01 à 08, Temps 1 et Temps 2 ✅, Freeze | commit `6f6c050`, tag `vj1-cadrage-frozen` | validé par le fondateur le 2026-11-04 |
| 2026-11-06 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : Handoff, préalables (disque, PaySim), ouverture courte ✅ | — | en cours |
| 2026-11-06 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : n° 09 posé, Temps 1 ✅ ; Temps 2 posé, en attente des réponses | — | en cours |
| 2026-11-07 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | J2 : propositions v2.15.6 appliquées ; n° 09 Temps 2 ✅ | — | en cours |
| 2026-11-10 | Claude (chat « Capstone · M5 · Phase 1 – J2 données ») | guidé | J2 (suite) : n° 10 load_paysim.py ✅ ; n° 11 conftest.py ✅ ; n° 12 test_data_schema.py ✅ ; n° 13 eda.py ✅ ; n° 14 01_eda.ipynb ✅ ; n° 15 data/README.md ✅ ; Freeze J2 | commit `364b660`, tag `vj2-donnees-frozen` | J2 FROZEN — J3 à démarrer dans nouveau chat M5 |
| 2026-11-10 | Claude (chat « Capstone · M4 · Phase 1 – J2 données ») | guidé | Fin J2 : AS-07/AS-08/AS-09 dans AMELIORATION_SYSTEME.md ; message de reprise M5 produit ; PASSATION mise à jour | — | prêt à fermer |
| 2026-11-10 | Claude (chat « Capstone · M4 · Phase 1 – J3 modèles ») | guidé | J3 : Handoff ✅, tag vj2 poussé, ouverture courte ✅ | — | en cours |
| 2026-11-12 | Claude (chat « Capstone · M4 · Phase 1 – J3 modèles ») | guidé | J3 : n° 16–28, n° 06–07 (G2), entraînement complet, 40 tests ; gel avec 8 Temps 2 🟡 (I39) | tag `vj3-modeles-frozen` | J3 FROZEN — J4 dans un nouveau chat |
