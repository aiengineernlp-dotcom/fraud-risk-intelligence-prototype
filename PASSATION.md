# PASSATION — fraud-risk-intelligence-prototype

> The handover note at the project's bedside. Any agent or chat that arrives reads it first; any agent or chat that leaves updates it.
> §1 to §7: rewritten at each departure. §8: one line added, never erased.
> No secret, no real data, no internal information.

## 1. OÙ ON EN EST
- Phase : Phase 1 – J4 Agent et LLM, **vibe coding contrôlé** (AS-15 ; I35, I39) — agent de code : Claude Code, en local ; Temps 2 de chaque pull request dans le chat « Capstone · M4 · Phase 1 – J4 agent et LLM »
- Arrêtée exactement à : mise en place posée sur `main` (`AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `.github/`, `docs/specs/`) ; aucune tâche J4 commencée ; n° 32 à 65 tous à faire
- Branche / pull request : `main` ; rien d'ouvert
- Décisions J3 à ne pas rediscuter : découpage stratifié 70/15/15, graine 42 dans `configs/settings.yaml` (I34) ; 12 variables (I36) ; Random Forest choisie sur la PR-AUC de validation (I09) ; seuil 0,5492 pour 300 cas/jour, marge 0,05 (I08) ; permutation seule (I10) ; seuil et métadonnées seulement dans `model_metadata.json` (I20)
- Décisions J4 : `main` protégée par garde-fous locaux + CI (compte GitHub Free, I40) ; `CLAUDE.md` = `@AGENTS.md` (I41) ; points de contrôle : J4 gelé ven. 13 nov. 23 h 00, J5 gelé sam. 14 nov. 15 h 00, J6 prêt sam. 14 nov. 23 h 59 ; remise dim. 15 nov. 10 h 45 (I42)
- Ouvert : `risk_band_bounds: null` → bornes à décider par le fondateur avant le n° 40 ; 8 Temps 2 🟡 du J3 + B162 (ouverture J4) à reformuler avant l'oral

## 2. FAIT — AVEC PREUVE
- [x] J1, J2, J3 FROZEN — tags `vj1-cadrage-frozen`, `vj2-donnees-frozen`, `vj3-modeles-frozen` (poussés ; `git ls-remote` → `600f8884…`, 2026-11-12)
- [x] Handoff J4 : `.venv/bin/python -m pytest -q` → 40 passed in 14.21s (2026-11-12, 13 h 45) ; `torch.__version__` → 2.15.0
- [x] Branche par défaut GitHub passée de `developpement` à `main` (2026-11-12, `HEAD branch: main`)
- [ ] Mise en place vérifiée (T08) : en cours — voir `01_sessions/Build_Control.md`, section VIBE CODING CONTRÔLÉ

## 3. RESTE À FAIRE — dans l'ordre, la prochaine en premier
- [ ] PR 1 — G01, G02 : n° 32 `src/agent/domain.py`, n° 42 `src/agent/state_machine.py`, n° 43 `tests/test_state_machine.py`
- [ ] PR 2 — D07 : n° 40 `src/models/risk_bands.py`, n° 41 (après la décision du fondateur sur les bornes)
- [ ] PR 3 🔒 — n° 33 `db.py`, n° 34 `case_repository.py`, n° 35 `audit_repository.py`
- [ ] PR 4 — G08 : n° 36, 37, 38, 39
- [ ] PR 5 — G04, G05, G07 : n° 44 à 47, n° 48 (+ petit pipeline de test dans `tests/conftest.py`)
- [ ] PR 6 — H01–H04 : n° 49 à 53
- [ ] PR 7 🔒 — F01, F02 : n° 55 à 58, n° 59
- [ ] PR 8 — F03–F05 : n° 60, 61
- [ ] PR 9 — G09, G11 : n° 62 `retry.py`, n° 54 `routing_policy.py`
- [ ] PR 10 — G03, G10 : n° 63 `orchestrator.py`, n° 64
- [ ] PR 11 — I02 : n° 65 `audit_export.py`
- [ ] Freeze J4 (tag `vj4-agent-frozen`) ; puis J5 (n° 66 à 72 + manques C2 du J2) ; J6 (rapport, présentation, vidéo)

## 4. VÉRIFIÉ / SUPPOSÉ
- Vérifié : `torch 2.15.0` installé dans le `.venv` = `requirements.txt` (2026-11-12). L'écart « 2.8.0 installé » annoncé au J3 était faux.
- Vérifié : aucun `CLAUDE.md` au-dessus du dépôt ni dans `~/.claude/` ; Claude Code 2.1.220 (lit `AGENTS.md` par l'import de `CLAUDE.md`)
- Supposé : `ruff` absent du `.venv` (formatage non lancé)
- Supposé : les règles `deny` de `.claude/settings.json` sont appliquées par Claude Code 2.1.220 — à prouver par l'essai T08

## 5. ÉCHECS — NE PAS REFAIRE · INCIDENTS
- Le shell réactive conda (`(base)`, `(pre_learn_1)`) et `python` est un alias de `python3` → toujours lancer `.venv/bin/python …` (pytest compris : `.venv/bin/python -m pytest`)
- PyCharm utilise l'interpréteur `pre_learn_1 [3.11]` → le pointer sur `.venv/bin/python`
- `np.array_equal` sur une Random Forest parallèle échoue (ordre des additions) → `assert_allclose(atol=1e-12)`
- Wrapper PyTorch refusé par `Pipeline` sans `fit` → `fit` factice + `__sklearn_is_fitted__`
- Fichiers collés mais non sauvegardés (⌘S) : vérifier sur la machine avant le Temps 1
- Sous la pression du temps, réponses complétées par l'assistant validées ✅ → AS-17 : 🟡, jamais ✅
- Le modèle entraîné (`artifacts/models/`) n'est pas versionné : la CI ne l'a pas → un test qui charge le vrai modèle échoue en CI

## 6. QUESTIONS ET PROPOSITIONS POUR LE FONDATEUR
- Q-01 Date de remise : FERMÉE — dim. 15 nov. 2026, 10 h 45 (I42)
- Q-02 Message à l'enseignant : travail seul accepté ? allègement possible (R177 : seulement par écrit) ?
- Q-03 Deux identifiants locaux à ajouter dans `99_PRIVE/MOTS_SENSIBLES_C10.txt` (liste hors dépôt)
- Q-04 `.claude/settings.local.json` (créé par Claude Code) à ignorer dans `.gitignore` (fichier gelé n° 01 : porte G2, décision du fondateur)

## 7. PROCHAINE SÉANCE — LA TÂCHE DU PROCHAIN
- Tâche : PR 1 — G01, G02 (`docs/specs/Features_Complet.md`) : n° 32 `src/agent/domain.py` (types partagés : `CaseState`, `ScoreResult`, `EvidenceItem`, `ReviewDecision`, `AuditEvent`, dataclasses figées) ; n° 42 `src/agent/state_machine.py` (états, transitions autorisées, refus des transitions invalides par `InvalidTransitionError`) ; n° 43 `tests/test_state_machine.py`
- Critère de fin : `test_valid_path`, `test_invalid_transition_rejected` (ex. RECEIVED → VALIDATED refusée), `test_terminal_states_are_final` verts ; les 40 tests existants toujours verts ; CI verte ; branche `tache/G01-machine-etats` poussée ; `PASSATION.md` à jour dans la branche
- Fichiers autorisés : n° 32, 42, 43 seulement. Interdit : base, LLM, audit (ils viennent après) ; tout fichier de `.github/protected_paths.txt`
- À lire d'abord : `AGENTS.md` ; ce fichier ; `docs/specs/Architecture_Projet.md` §1.2, §3bis (machine à états et tableau des transitions), §5, §8 (lignes n° 32, 42, 43) ; `docs/specs/Features_Complet.md` G01, G02
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
| 2026-11-12 | Claude (chat « Capstone · M4 · Phase 1 – J4 agent et LLM ») | vibe coding contrôlé (mise en place) | J4 : Handoff ✅ (40 passed), ouverture courte (B162 🟡), mise en place T01–T07 posée : `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, CI, `docs/specs/` | commit de mise en place (fondateur) | À VÉRIFIER — essais T08 à faire |
