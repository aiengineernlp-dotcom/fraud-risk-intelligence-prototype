# PASSATION — fraud-risk-intelligence-prototype

> The handover note at the project's bedside. Any agent or chat that arrives reads it first; any agent or chat that leaves updates it.
> §1 to §7: rewritten at each departure. §8: one line added, never erased.
> No secret, no real data, no internal information.

## 1. OÙ ON EN EST
- Phase : Phase 1 – J4 Agent et LLM, **vibe coding contrôlé** (AS-15 ; I35, I39) — agent de code : Claude Code, en local ; Temps 2 de chaque pull request dans le chat « Capstone · M4 · Phase 1 – J4 agent et LLM »
- Arrêtée exactement à : PR 2 (D07) **fusionnée** (pull request #3, merge `0f1846c`) ; bornes des bandes écrites par le fondateur dans le vrai `model_metadata.json` (local) ; PR 3 🔒 (n° 33, 34, 35, 70) **en cours** sur `tache/G10-stockage-audit` — plan validé (GO 2026-11-13, décisions au §6) ; n° 36 à 39 et 44 à 65 à faire
- Branche / pull request : `tache/G10-stockage-audit` (depuis `main` à `b745cf1`) ; pas encore de pull request (PR #2 et #3 fusionnées)
- Décisions J3 à ne pas rediscuter : découpage stratifié 70/15/15, graine 42 dans `configs/settings.yaml` (I34) ; 12 variables (I36) ; Random Forest choisie sur la PR-AUC de validation (I09) ; seuil 0,5492 pour 300 cas/jour, marge 0,05 (I08) ; permutation seule (I10) ; seuil et métadonnées seulement dans `model_metadata.json` (I20)
- Décisions J4 : `main` protégée par garde-fous locaux + CI (compte GitHub Free, I40) ; `CLAUDE.md` = `@AGENTS.md` (I41) ; points de contrôle : J4 gelé ven. 13 nov. 23 h 00, J5 gelé sam. 14 nov. 15 h 00, J6 prêt sam. 14 nov. 23 h 59 ; remise dim. 15 nov. 10 h 45 (I42)
- Ouvert : Temps 2 🟡 à reformuler avant l'oral : 8 du J3 + B162 (ouverture J4) + B163 à B166 (PR 1)

## 2. FAIT — AVEC PREUVE
- [x] J1, J2, J3 FROZEN — tags `vj1-cadrage-frozen`, `vj2-donnees-frozen`, `vj3-modeles-frozen` (poussés ; `git ls-remote` → `600f8884…`, 2026-11-12)
- [x] Handoff J4 : `.venv/bin/python -m pytest -q` → 40 passed in 14.21s (2026-11-12, 13 h 45) ; `torch.__version__` → 2.15.0
- [x] Branche par défaut GitHub passée de `developpement` à `main` (2026-11-12, `HEAD branch: main`)
- [x] Mise en place vérifiée (T08) : hook, interdictions chargées (`/permissions`), bypass refusé, mode `accept edits`, CI verte, `protected-paths` rouge sur PR d'essai — preuves dans `01_sessions/Build_Control.md`, section VIBE CODING CONTRÔLÉ (2026-11-12, 16 h 48)
- [x] PR 1 — G01, G02 : `src/agent/domain.py` (n° 32), `src/agent/state_machine.py` (n° 42), `tests/test_state_machine.py` (n° 43) — commit `9401da5` ; `.venv/bin/python -m pytest -q` → 58 passed in 28.65s (2026-11-12 ; 40 anciens + 18 nouveaux, dont `test_valid_path`, `test_invalid_transition_rejected`, `test_terminal_states_are_final` et les 13 transitions autorisées une par une)
- [x] PR 1 — décision I45 (Q-06) : FAILED ajouté aux transitions de VALIDATED et HUMAN_REVIEW (15 transitions autorisées) ; `.venv/bin/python -m pytest -q` → 60 passed in 8.50s (2026-11-12)
- [x] PR 1 fusionnée : pull request #2, CI `tests` ✅ + `protected-paths` ✅, Temps 2 fait (B163 à B166, 🟡), merge `157e689` (2026-11-12)
- [x] PR 2 — D07 : `src/models/risk_bands.py` (n° 40 : `RiskBandError(ValueError)`, `check_bounds`, `risk_band`), `scripts/set_risk_band_bounds.py` (n° 40bis), `tests/test_risk_bands.py` (n° 41, 41 tests dont `math.nextafter` sous chaque borne) — commit `7309ce3` ; `.venv/bin/python -m pytest -q` → 101 passed in 7.52s (2026-11-13 ; 60 anciens + 41 nouveaux)
- [x] PR 2 fusionnée : pull request #3, merge `0f1846c` ; `scripts.set_risk_band_bounds` lancé par le fondateur (2026-11-13, §7 de la passation précédente)
- [x] PR 2 — essai du script sur des **copies** de `model_metadata.json` et `threshold_analysis.csv` (dossier temporaire hors dépôt) → `(None, {'medium': 0.5492405919533623, 'high': 0.8516238554349536})` = valeurs I46 ; autres clés identiques (2026-11-13). Aucun fichier de `artifacts/` modifié

## 3. RESTE À FAIRE — dans l'ordre, la prochaine en premier
- [ ] PR 3 🔒 — n° 33 `db.py`, n° 34 `case_repository.py`, n° 35 `audit_repository.py`, n° 70 `test_review_and_audit.py` (commencé) — en cours sur `tache/G10-stockage-audit`
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
- Vérifié : aucun `CLAUDE.md` au-dessus du dépôt ni dans `~/.claude/` ; Claude Code **2.1.322** (`claude --version`, 2026-11-12, 16 h 23 ; mis à jour seul depuis 2.1.220) — lit `AGENTS.md`, aussi par l'import de `CLAUDE.md`
- Supposé : `ruff` absent du `.venv` (formatage non lancé)
- Vérifié : la PR 1 ne modifie aucun fichier de `.github/protected_paths.txt` (seulement 3 fichiers nouveaux + `PASSATION.md`)
- Vérifié : CI verte sur la PR 1 (pull request #2 : `tests` ✅ 1 min, `protected-paths` ✅ 5 s)
- Supposé : les champs proposés pour `ScoreResult`, `EvidenceItem`, `ReviewDecision` suffiront aux PR suivantes (non détaillés dans `docs/specs/`) ; `AuditEvent` suit champ pour champ la table `audit_events` (§10.2), sans `event_id` (attribué par la base)
- Vérifié : la PR 2 ne modifie aucun fichier de `.github/protected_paths.txt` (3 fichiers nouveaux + `PASSATION.md`) ; `scripts` s'importe comme paquet d'espace de noms (sans `__init__.py`, D-14)
- Supposé : CI verte sur la PR 2 (pas encore poussée) ; `score_transaction` (n° 45, PR 5) passera `metadata["risk_band_bounds"]` à `risk_band` — `model_io.py` (gelé) ne vérifie pas ce champ, c'est `check_bounds` qui refuse `None`
- Vérifié : les interdictions de `.claude/settings.json` sont chargées (`/permissions` → Deny, 50 règles, 2026-11-12) ; mode par défaut `accept edits` (I44) — à relire sur la ligne d'état à chaque session (la PR 1 a d'abord tourné en « auto mode »)

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
- Q-05 (PR 1) G02 demande un test du refus **et de l'événement d'audit** ; l'audit n'existe pas encore → PR 1 teste seulement le refus. À couvrir avec l'orchestrateur (PR 10, action `invalid_transition`). Le §3bis et G02 restent tels quels ; décision du fondateur sur le report
- Q-06 (PR 1) — **tranchée : I45** — FAILED atteignable depuis tous les états non finaux (énoncé §11.3 « Any step → FAILED ») ; `Architecture_Projet.md` §3bis v1.2 ; VALIDATED → FAILED et HUMAN_REVIEW → FAILED ajoutées dans `state_machine.py` (15 transitions). Copie de `docs/specs/` (encore v1.1) mise à jour sur `main` par le fondateur après la fusion
- Q-07 (PR 1) Tests de la machine à états non marqués `validation_workflow` (ce ne sont pas des tests du flux de validation du brouillon) — choix validé au plan
- Q-08 (PR 2, Q2 du plan) — **Réponse du fondateur (2026-11-13) : gardée** ; dépendance ajoutée au registre (`Architecture_Projet.md` §8, n° 40bis).  Dépendance : `scripts/set_risk_band_bounds.py` (n° 40bis, couche Entraînement) importe `check_bounds` de `src/models/risk_bands.py` (n° 40, couche 3), pour appliquer la même règle (0 < medium < high < 1) que l'agent. Le registre §8 ne liste pas cette dépendance pour le n° 40bis → à ajouter dans `docs/specs/Architecture_Projet.md` par le fondateur s'il la garde
- Q-09 (PR 2) — **Réponse : d'accord** (décisions, pas réglages).  Les capacités 200 et 300 sont des constantes nommées dans le script (`HIGH_BOUND_CAPACITY`, `THRESHOLD_CAPACITY`), issues des décisions I46 et I08, et pas des réglages : `configs/settings.yaml` a `review_capacity_per_day` (300), que le script n'utilise pas. Le script refuse si la ligne 300 ne porte pas le seuil des métadonnées. À confirmer
- Q-10 (PR 2) — **Réponse : d'accord.**  Le script lève `BoundsSourceError` (nouvelle exception, non nommée dans le plan) pour les fichiers absents ou incohérents, et `RiskBandError` (de `check_bounds`) pour les bornes mal ordonnées ; `main()` les affiche sur stderr et rend 1
- Décisions PR 3 (GO du fondateur, 2026-11-13) : 11 états **en dur** dans le SQL de `db.py` + test paramétré sur `CaseState` (pas de dépendance `db.py` → `domain.py`, registre §8 respecté) ; `CHECK` sur `step` (`score`, `evidence`, `draft`, `validation`, §10.2) ; (a) 2 déclencheurs refusant `UPDATE` / `DELETE` sur `audit_events` ; (b) clé de `details` ressemblant à un secret → `SecretInAuditError` (morceaux `secret`, `password`, `passwd`, `token`, `apikey` ; `api` suivi de `key` ; clé exactement `key` ; découpage sur `_` et `-`, minuscules, dictionnaires imbriqués) ; (c) résultat d'étape existant rendu tel quel avec `created=False` (D-07) ; (d) ISO 8601 UTC avec décalage, horodatage d'audit non UTC refusé, ordre par `event_id` ; (e) `create_case` refuse `isFraud` / `isFlaggedFraud` dans la transaction
- Q-11 (PR 3, risque 2) Schéma non migré : `CREATE TABLE IF NOT EXISTS` ne modifie pas une base existante. Si le schéma change plus tard, un `data/runtime/capstone.db` déjà créé garde l'ancien schéma sans erreur. Aucune base n'existe aujourd'hui. À décider : supprimer la base locale (fondateur) à chaque changement de schéma, ou une vérification de version
- Q-12 (PR 3, risque 7) Threads de Streamlit : `sqlite3` refuse par défaut d'utiliser une connexion dans un autre thread que celui qui l'a ouverte (`check_same_thread`). Non traité dans la PR 3 (les dépôts reçoivent la connexion de l'appelant). À trancher à la PR 10 (orchestrateur) ou au J5 : une connexion par appel, ou `check_same_thread=False` avec verrou
- Q-04 `.claude/settings.local.json` (créé par Claude Code) à ignorer dans `.gitignore` (fichier gelé n° 01 : porte G2, décision du fondateur)

## 7. PROCHAINE SÉANCE — LA TÂCHE DU PROCHAIN
- Fait par le fondateur : PR 2 fusionnée (pull request #3, `0f1846c`) ; `scripts.set_risk_band_bounds` lancé : `risk_band_bounds` = {medium 0,5492405919533623, high 0,8516238554349536} dans `artifacts/models/model_metadata.json` (local) ; Q-08 à Q-10 répondues (§6).
- Tâche : PR 3 🔒 **zone sensible** (base de données, schéma, journal d'audit) — **plan et GO obligatoires, même pour une petite correction**. Fichiers (registre `docs/specs/Architecture_Projet.md` §8) :
  - n° 33 `src/storage/db.py` (couche 1) : ouvrir une base SQLite à un **chemin reçu en paramètre** (jamais lu dans `config.py` par ce fichier ; l'appelant donne `paths.runtime_db`) ; créer les 3 tables **exactement** comme `docs/specs/Architecture_Projet.md` §10.2 (`cases`, `step_results`, `audit_events`), avec les contraintes écrites (clés primaires, clés étrangères **activées**, `state` parmi les 11 valeurs de `CaseState`, `reviewer_decision` parmi les 3 issues, `attempts` ≥ 1) ; création idempotente (relancer ne casse rien) ; aucune logique métier.
  - n° 34 `src/storage/case_repository.py` (couche 2) : créer un cas **une seule fois** (même `case_id` deux fois → refus nommé, D-07) ; lire un cas ; enregistrer le nouvel état **déjà décidé** par l'appelant (ce fichier ne décide jamais d'une transition : c'est `state_machine.py` + l'orchestrateur) ; enregistrer et lire un résultat d'étape par clé d'idempotence `"{case_id}:{step}"` (une étape déjà enregistrée n'est pas réécrite : D-07, G10). SQL seulement ici, requêtes paramétrées (`?`), jamais de chaîne formatée.
  - n° 35 `src/audit/audit_repository.py` (couche 2) : **ajouter** un événement (`AuditEvent` de `src/agent/domain.py`, champs = §10.2) et rendre son `event_id` ; lire les événements d'un cas dans l'ordre ; **aucune fonction de modification ni de suppression** ; `details` sérialisé en JSON.
  - Tests : **n° 70 `tests/test_review_and_audit.py`, commencé maintenant** (le registre le désigne comme test des n° 33 et 35 ; il sera complété au J5) — base temporaire (`tmp_path`), jamais `data/runtime/`.
- À proposer dans le plan (décision du fondateur) : (a) un déclencheur SQLite qui **refuse** `UPDATE` / `DELETE` sur `audit_events` (en plus de l'absence de fonction) ; (b) que faire si `details` contient une clé qui ressemble à un secret (`key`, `token`, `secret`, `password`) ; (c) comportement exact quand un résultat d'étape existe déjà (rendre l'existant ou lever une erreur) ; (d) forme des horodatages (ISO 8601 UTC).
- Critère de fin : tests verts — création des tables, contraintes refusant un état inconnu et un `attempts` à 0, double création d'un cas refusée, clé d'idempotence respectée, ajout et lecture ordonnée de l'audit, aucune modification possible de l'audit ; les 101 tests existants toujours verts ; CI verte ; branche `tache/G10-stockage-audit` poussée ; `PASSATION.md` à jour dans la branche.
- Fichiers autorisés : n° 33, 34, 35, 70 (+ `tests/conftest.py` si une fixture de base temporaire est utile, + `PASSATION.md`). Interdit : `.github/protected_paths.txt` (dont `configs/settings.yaml`, `src/config.py`) ; `data/runtime/` ; tout appel réseau.
- À lire d'abord : `AGENTS.md` ; ce fichier ; `docs/specs/Architecture_Projet.md` §1.2, §5, §8 (n° 33, 34, 35, 70), §10 ; `src/agent/domain.py` (`CaseState`, `AuditEvent`, `REVIEWER_OUTCOMES`) ; `src/agent/state_machine.py`.
- Préalables : `main` à jour ; `.venv/bin/python -m pytest -q` → 101 passed.

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
| 2026-11-12 | Claude Code (Opus 5.5) | vibe coding contrôlé | PR 1 — G01, G02 : n° 32 `domain.py`, n° 42 `state_machine.py`, n° 43 `test_state_machine.py` ; 58 passed ; Q-05 à Q-07 | branche `tache/G01-machine-etats`, commit `9401da5` | À VÉRIFIER |
| 2026-11-12 | Claude Code (Opus 5.5) | vibe coding contrôlé | PR 1 — décision I45 : FAILED depuis VALIDATED et HUMAN_REVIEW (n° 42, 43) ; 60 passed ; Q-06 tranchée | branche `tache/G01-machine-etats` | À VÉRIFIER |
| 2026-11-12 | Claude (chat « Capstone · M4 · Phase 1 – J4 agent et LLM ») | vibe coding contrôlé | PR 1 : Temps 2 (B163–B166 🟡), décision I45 (Q-06), fusion #2 ; §1, §2, §4 mis à jour (T08 prouvé, version de Claude Code) | merge `157e689` | À VÉRIFIER — fondateur |
| 2026-11-12 | Claude (chat « Capstone · M4 · Phase 1 – J4 agent et LLM ») | vibe coding contrôlé | Fin de la séance 1 : PR 2 décidée (I46, I47), ACK + plan validés, pas commencée ; AS-33 à AS-35 ; gabarits de messages | — | À VÉRIFIER — reprise séance 2 (2026-11-13, matin) |
| 2026-11-13 | Claude Code (Opus 5.5) | vibe coding contrôlé | PR 2 — D07 : n° 40 `risk_bands.py`, n° 40bis `set_risk_band_bounds.py`, n° 41 `test_risk_bands.py` (plan Q1–Q4) ; 101 passed ; script essayé sur copies → valeurs I46 ; Q-08 à Q-10 | branche `tache/D07-bandes-risque`, commit `7309ce3` | À VÉRIFIER |
| 2026-11-13 | Claude (chat « Capstone · M4 · Phase 1 – J4 agent et LLM ») | vibe coding contrôlé | PR 2 : Temps 2 (B167 🟡), Q-08 à Q-10 répondues, fusion #3, bornes écrites ; §7 = PR 3 🔒 | merge `0f1846c` | À VÉRIFIER — fondateur |
