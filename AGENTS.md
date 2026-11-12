# AGENTS.md — fraud-risk-intelligence-prototype (Capstone_Project_1)

> Règles pour tout agent de code qui travaille sur ce dépôt, quel que soit l'outil.
> Écrit par le fondateur (Erman). Tu ne modifies jamais ce fichier.
> Mode : vibe coding contrôlé, Phase 1 – J4 Agent et LLM (n° 32 à 65 du registre). Palier : Noté (capstone évalué).

## 0. TA PLACE
Tu reprends un travail commencé par d'autres agents que tu ne connais pas et à qui tu ne parleras jamais.
Tout ce que tu dois savoir est dans ce dépôt ; tout ce que tu fais doit y être écrit avant que tu partes.
Le seul lien entre vous est `PASSATION.md`. Le fondateur décide ; toi, tu proposes et tu exécutes.
Le fondateur doit pouvoir **expliquer et défendre** chaque ligne que tu écris devant un jury : écris du code simple,
lisible, commenté là où une décision est prise, jamais « malin ».

## 1. À L'ARRIVÉE — dans cet ordre
1. Lis ce fichier en entier.
2. Lis `PASSATION.md` : les §1 à §7 en entier, et les 3 dernières lignes du journal (§8).
3. Lis les fichiers que le §7 de `PASSATION.md` te donne (souvent dans `docs/specs/`).
4. Réponds **uniquement** par l'ACK du §2, puis attends « GO ».
Si tu ne peux pas lire un fichier, dis lequel. N'invente jamais son contenu.

**Si `PASSATION.md` n'est pas à jour** (des commits plus récents que la dernière ligne du journal, ou une étape « en cours »
sans suite — le précédent a pu être coupé par ses crédits) : ne devine pas. Reconstruis à partir des preuves — dernier
`PASSATION.md`, `git log` et `git diff` depuis, branche, pull request, CI — en mettant en tête du §1
« RECONSTRUIT par [toi] le [date] — à valider » ; tout ce que tu n'as pas vérifié va en « supposé », ce qui était en cours
repart comme non fait. Puis ton ACK, et attends que le fondateur valide la reconstruction.

## 2. L'ACK — 4 lignes, rien d'autre
1. Ma mission : [la tâche du §7 de PASSATION.md, avec son critère de fin, avec tes mots]
2. État actuel : [une phrase, citée du §1 de PASSATION.md]
3. Ce qui n'est pas clair ou se contredit : [… ou « aucune », avec la raison]
4. Preuve de lecture et capacités : [une ligne du §3 ou du §4 de PASSATION.md, recopiée mot pour mot] — lire le dépôt : oui/non ·
   écrire dans une branche : oui/non · lancer les tests : oui/non · ouvrir une pull request : oui/non

## 3. PENDANT LE TRAVAIL
- **Plan d'abord** : fichiers touchés (avec leur n° du registre, `docs/specs/Architecture_Projet.md` §8), risques, tests prévus,
  **zones sensibles touchées : oui ou non, lesquelles — y compris indirectement**, et un diagramme Mermaid si des parties
  interagissent. Tu n'écris rien avant le « GO » sur le plan.
- **Une tâche, une branche** `tache/[ID]-[nom-court]` (ID de `docs/specs/Features_Complet.md`, ex. `tache/G01-machine-etats`),
  créée depuis `main` à jour. Une pull request vers `main`. Jamais de commit sur `main`.
- **Rien hors du périmètre** de la tâche. Une autre idée → §6 de `PASSATION.md` (PROPOSÉ).
- **« Fait » exige une preuve** : un test vert, un commit. Sinon c'est « supposé » (§4 de `PASSATION.md`).
- **Tu n'inventes jamais** : ce que tu ne sais pas, tu l'écris « INCONNU » ou en question (§6). Aucune valeur de décision
  inventée (seuil, bornes, délais, nombre d'essais) : elles viennent de `configs/settings.yaml` ou de
  `artifacts/models/model_metadata.json`, ou d'une décision du fondateur.
- **Contradiction** entre la demande, `docs/specs/` et le code → tu t'arrêtes et tu le signales. Tu ne répares pas en silence.
- **Tu ne refais pas** ce qui est dans « ÉCHECS — NE PAS REFAIRE » (§5 de `PASSATION.md`).
- **Zones sensibles** — plan et GO, toujours : base de données et son schéma (`src/storage/db.py`, les repositories),
  journal d'audit (ajout seulement, jamais de modification ni de suppression d'un événement), clé et appels du LLM
  (`.env`, `src/agent/llm/`), suppression de données, tout outil qui pourrait agir sur de l'argent (interdit : G12).
- **Secrets et données réelles** : jamais dans le code, jamais dans un commit, jamais dans tes messages. Tu ne lis pas `.env`.
- `docs/specs/` est en **lecture seule** : une correction à y faire → §6 de `PASSATION.md`.
- **Mets `PASSATION.md` à jour après chaque sous-étape, et commite-le** dans ta branche, pas seulement à la fin.

### Règles propres à ce projet
- **Couches** (`docs/specs/Architecture_Projet.md` §1.2 et §5) : chaque fichier respecte ce que sa couche « ne fait jamais ».
  Le LLM ne calcule jamais le score, la bande ni la validité ; l'orchestrateur ne valide pas lui-même, il appelle le validateur.
- **Le seuil** vient seulement de `model_metadata.json`, lu par `src/models/model_io.py` (décision I20) ; jamais de 0,5 en dur.
- **Aucune étiquette** (`isFraud`, `isFlaggedFraud`) dans les cas de démo, le prompt ou une sortie de l'agent.
- **Tests hors ligne** : aucun appel réseau, aucun vrai LLM ; le faux client (n° 56) sert aux tests. Le modèle entraîné
  (`artifacts/models/`) n'est **pas** dans le dépôt : les tests qui scorent utilisent un petit pipeline ajusté dans
  `tests/conftest.py`.
- **Marqueur** `validation_workflow` sur les tests du flux de validation (au moins 5 exigés par l'énoncé §14).
- **En-tête** de chaque fichier Python, comme les fichiers existants : SoC layer, Responsibility, Never does, Reference.
- **Fichiers protégés** (gelés au J1–J3, ou qui jugent ton travail) : liste dans `.github/protected_paths.txt`.
  Une pull request qui en modifie un est rouge en CI. S'il faut en changer un (ex. `configs/settings.yaml`), tu le proposes
  au §6 de `PASSATION.md` : c'est le fondateur qui le fait.

## 4. AU DÉPART — avant de rendre la main
1. Réécris les §1 à §7 de `PASSATION.md` (où on en est exactement, fait avec preuve, reste à faire, vérifié / supposé,
   échecs et incidents, questions et propositions, mission du prochain agent).
2. Ajoute **une** ligne au journal (§8). Tu ne modifies et n'effaces jamais les lignes existantes.
3. Commite dans ta branche ; pousse la branche (le fondateur approuve la commande) ; le fondateur ouvre la pull request.
4. Statut laissé : « À VÉRIFIER » — jamais « validé » : seul le fondateur valide.
5. Compte rendu dans la conversation : fichiers modifiés, tests lancés et leur résultat, nom de la branche.

## 5. CE QUE TU NE FAIS JAMAIS
Envoyer sur `main` · fusionner · déployer · toucher aux secrets ou à `.env` · utiliser `gh` ·
marquer une tâche « validée » · modifier ce fichier, `CLAUDE.md`, `.claude/`, une décision ou une copie de `docs/specs/` ·
effacer ou réécrire une ligne du journal de `PASSATION.md` · modifier la CI (`.github/`) · supprimer, désactiver ou
affaiblir un test existant (s'il te semble faux, dis-le au §6 de `PASSATION.md`) · contourner un contrôle
(`--no-verify`, `--force`, `reset --hard`).

## 6. COMMANDES DU PROJET
- Installer : `python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt`
- Lancer : `.venv/bin/python -m src.train` (entraînement complet, ~4 min, données PaySim dans `data/raw/` — non requis au J4)
- Tests : `.venv/bin/python -m pytest -q` (toujours `.venv/bin/python`, jamais `python` ni `pytest` seuls : voir §5 de `PASSATION.md`)
- Vérifications de style : aucune (`ruff` n'est pas installé)
