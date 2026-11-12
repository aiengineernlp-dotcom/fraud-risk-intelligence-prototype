> COPIE en lecture seule — source : [DOSSIER_PROJET]/00_ritual/Features_Complet.md, version du 2026-10-20. Ne pas modifier ici : une correction se propose au §6 de PASSATION.md.

# FEATURES COMPLET — Capstone_Project_1

> Ressources utilisées : `Document_Maitre.md` v1.0, `Matrice_Conformite.md` v1.0, `Banque_Questions.md` v1.0 (tous validés le 2026-10-19) ;
> énoncé `Capstone_Project_1_Project_Brief.docx` (18 octobre 2026) ; gabarit `10_Template_Features_Complet.md` v1 · système v2.3.4
> · Contrôle indépendant : aucun · Date : 2026-10-19
>
> Version : **v1.0** — **VALIDÉ par Erman le 2026-10-20** · Version précédente : v0.1 (même contenu, statut EN COURS)
> Confidentialité : **Document INTERNE** — jamais rendu (langue de travail : français ; les noms techniques restent en anglais)

> Rôle : document [2] du rituel — « ce qu'on construit ». Source de vérité pour **les fonctionnalités**.
> Au palier Noté, chaque fonctionnalité P1 renvoie aux exigences de l'énoncé (`Matrice_Conformite.md`, IDs R) : elle dit *quoi construire* ;
> la matrice dit *quelle preuve rendre*. Une exigence de la matrice sans fonctionnalité ici = un trou à signaler.

---

## 1. LISTE DES FONCTIONNALITÉS

**Lecture des colonnes**
- **ID** : lettre du module + numéro (`A01`, `B03`…). Repris par le Test_Plan et le registre des fichiers d'`Architecture_Projet.md`.
- **Priorité P1 / P2** : **P1** = Phase 1, la remise du 2026-11-06. **P2** = plus tard (Phase 2, après la note) : on ne la construit pas par anticipation. « P1 (opt.) » = encouragée mais non exigée par l'énoncé ; à sacrifier en premier si le planning glisse.
- **Palier produit** : au palier Noté, ce sont les **jalons** de `Matrice_Conformite.md` §6 : J1 Cadrage · J2 Données · J3 Modèles · J4 Agent et LLM · J5 Application et tests · J6 Remise.
- **Objectif métier servi** : renvoi à `Document_Maitre.md` (DM §… / indicateur §7 / principe §8), puis aux exigences de l'énoncé (R…).
- **Rôle** : rôles de `Document_Maitre.md` §4 — **Relecteur** (enquêteur), **Évaluateur** (enseignant), **Constructeur** (Erman), **Responsable** (responsable des opérations, fictif).
- **Config** : ✅ si c'est réglable par configuration (fichier de configuration ou variable d'environnement), sans toucher au code.
- **Critère d'acceptation** : une phrase vérifiable, reprise mot pour mot par le Test_Plan.

### A. DONNÉES ET EDA
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| A01 | Instructions d'obtention de PaySim ; données brutes jamais versionnées | P1 | J2 | DM §8.1 ; R040, R043, R321, R326 | Non | Constructeur, Évaluateur | ✅ (chemin des données) | Le README explique comment obtenir le fichier, et `git ls-files` ne liste aucun fichier de données brutes. |
| A02 | Fiche du jeu de données (source exacte, date, licence copiée, comptes calculés, cible, ≥ 5 limites) | P1 | J2 | DM §7 ; R044–R050 | Non | Constructeur | — | `data/README.md` contient les 6 rubriques de §3.4, avec des comptes produits par le code et au moins 5 limites. |
| A03 | Chargement et validation du schéma (colonnes requises, types) | P1 | J2 | R080, R061, R062 | Non | Constructeur | — | Une fonction refuse un fichier auquel il manque une colonne requise ou qui a un type incorrect, et un test le prouve. |
| A04 | Dictionnaire de données (nom, type, sens, rôle, manquants, utilisé ou non, risque de fuite ou d'équité) | P1 | J2 | R051, R055 | Non | Constructeur | — | Le dictionnaire couvre 100 % des colonnes du fichier téléchargé, avec les 7 attributs de §4.4. |
| A05 | Contrôles de qualité : valeurs manquantes, doublons (définition + compte + décision), valeurs aberrantes | P1 | J2 | R063, R064, R072, R081, R082 | Non | Constructeur | — | Chaque contrôle a un compte et une décision écrite. |
| A06 | Les 12 investigations EDA de §5.1 | P1 | J2 | R061–R072 | Non | Constructeur, Responsable | — | Le notebook EDA contient une sortie pour chacune des 12 investigations. |
| A07 | ≥ 6 graphiques annotés (ce que montre le graphique, l'implication pour Northstar, la décision qu'il éclaire), générés par le code | P1 | J2 | DM §7 ; R073, R074 | Non | Responsable, Évaluateur | — | `artifacts/figures/` contient au moins 6 graphiques, chacun avec ses 3 phrases dans le notebook et le rapport. |
| A08 | Constats de l'EDA → décisions (colonnes exclues, variables créées, découpage) | P1 | J2 | R060, R071 | Non | Constructeur | — | Une liste « constat → décision » existe ; chaque décision est reprise dans B. |
| A09 | Contrôle du dépôt : aucun champ qui ressemble à une donnée personnelle | P1 | J5 | R241, R042 | K | Constructeur | — | Un test échoue si un fichier versionné contient un motif de donnée sensible (liste écrite dans le test). |

### B. PRÉTRAITEMENT ET VARIABLES
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| B01 | Séparation X / y ; `isFraud` et `isFlaggedFraud` exclus des variables du modèle principal ; identifiants exclus sauf justification | P1 | J3 | DM §8.5 ; R053, R095 | Non | Constructeur | ✅ (listes de colonnes) | Un test prouve que ni `isFraud` ni `isFlaggedFraud` n'est dans X. |
| B02 | Découpage stratifié train / validation / test, proportions et graine fixées | P1 | J3 | R102, R103 | Non | Constructeur | ✅ (proportions, graine) | Deux exécutions avec la même graine donnent les mêmes index ; graine et proportions figurent dans le README et le rapport. |
| B03 | Pipeline reproductible (ColumnTransformer) : encodage de `type`, mise à l'échelle seulement pour les modèles qui en ont besoin | P1 | J3 | R091, R092, R094, R099, R100 | Non | Constructeur | — | Le même objet pipeline sert à l'entraînement, à l'évaluation et à l'application. |
| B04 | Ajustement du prétraitement sur l'entraînement uniquement | P1 | J3 | R097 | B03 | Constructeur | — | Le code montre un seul `fit` du prétraitement, sur les données d'entraînement, et la ligne est citée dans le rapport. |
| B05 | Variables dérivées justifiées (ex. variations de solde), chacune avec sa justification et son contrôle de fuite | P1 | J3 | R093 | Non | Constructeur | ✅ (activation) | Chaque variable dérivée a une ligne « justification + fuite vérifiée » dans la documentation des données. |
| B06 | Traitement du déséquilibre (poids de classes ou rééchantillonnage) **dans l'entraînement seulement** | P1 | J3 | R101, R123 | Non | Constructeur | ✅ (stratégie) | Un test montre que la taille et la répartition des jeux de validation et de test ne changent pas. |
| B07 | Documentation de chaque transformation | P1 | J3 | R098 | Non | Constructeur | — | Chaque étape du pipeline a une ligne dans `data/README.md`. |
| B08 | Expérience en plus : découpage temporel (premiers steps → derniers steps), comparé au découpage aléatoire | P1 (opt.) | J3 | R104 ; DM Q14 | Non | Constructeur | ✅ (step de coupure) | Le tableau comparatif contient une ligne « découpage temporel », discutée dans le rapport. |

### C. ML CLASSIQUE
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| C01 | Baseline (classe majoritaire ou règle simple) | P1 | J3 | R111 | Non | Constructeur | — | La baseline apparaît dans le tableau comparatif avec toutes les métriques de D01. |
| C02 | Régression logistique dans un pipeline | P1 | J3 | R110, R112 | Non | Constructeur | ✅ (hyperparamètres) | Elle est entraînée par une commande documentée et figure dans le tableau. |
| C03 | Random Forest dans un pipeline | P1 | J3 | R110, R113 | Non | Constructeur | ✅ (hyperparamètres) | Idem C02. |
| C04 | Gradient Boosting ou XGBoost | P1 (opt.) | J3 | R114 ; DM Q15 | Non | Constructeur | ✅ | S'il est fait, il figure dans le tableau ; sinon, la raison est écrite. |
| C05 | Réglage des hyperparamètres sur train et validation uniquement | P1 | J3 | R122, R103 | Non | Constructeur | ✅ (grille) | Aucun appel d'évaluation sur le test avant D04 (preuve : code + journal). |
| C06 | Choix du modèle final sur la validation, justifié | P1 | J3 | R124 | Non | Constructeur | ✅ (modèle retenu) | Le rapport cite les chiffres de validation qui justifient le choix. |
| C07 | Pipeline sauvegardé (prétraitement + modèle), avec nom, version et date d'entraînement | P1 | J3 | R126, R285 | Non | Constructeur | ✅ (chemin, version) | `artifacts/` contient le pipeline ; un test le recharge et obtient les mêmes scores. |
| C08 | Commande d'entraînement documentée | P1 | J3 | R125 | Non | Évaluateur | — | La commande du README produit le pipeline et les métriques sur un environnement propre. |

### D. ÉVALUATION, SEUIL ET EXPLICABILITÉ
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| D01 | Jeu complet de métriques adaptées au déséquilibre : matrice de confusion **en comptes**, precision, recall, F1, ROC-AUC, PR-AUC ou average precision | P1 | J3 | DM §7 ; R140–R144 | Non | Responsable | — | Chaque modèle a les 8 valeurs dans le tableau ; chacune a une phrase en langage métier. |
| D02 | Tableau comparatif (baseline, modèles classiques, MLP) avec les paramètres documentés | P1 | J3 | R127, R175 | D01 | Responsable, Évaluateur | — | Un seul tableau, généré par le code, mêmes découpages pour tous. |
| D03 | Choix du seuil sur la validation, lié à un objectif opérationnel (ex. capacité de revue), avec le compromis precision / recall sur des seuils candidats | P1 | J3 | R148–R150 | Non | Responsable | ✅ (objectif, seuil) | Une courbe ou un tableau des seuils candidats existe, et le seuil retenu est écrit dans la configuration. |
| D04 | Évaluation finale sur le test, **une seule fois**, au seuil choisi | P1 | J3 | R151 | Non | Constructeur | — | `Journal_Build.md` note une seule exécution sur le test, et ses chiffres sont ceux du rapport. |
| D05 | Analyse d'erreurs : faux positifs et faux négatifs groupés (type, tranche de montant…), avec leurs causes probables | P1 | J3 | R152, R244 | Non | Responsable | — | Un tableau des erreurs par groupe, avec une explication par groupe. |
| D06 | Explicabilité (coefficients, importance par permutation ou SHAP), sans affirmation de causalité | P1 | J3 | R153, R154 | Non | Responsable | — | Un graphique d'explication + une phrase « décrit ce que le modèle utilise, pas ce qui cause la fraude ». |
| D07 | Bandes de risque (low / medium / high) dérivées du score et du seuil | P1 | J4 | R182, R284 | Non | Relecteur | ✅ (bornes) | Toute valeur de score donne exactement une bande, et un test couvre les bornes. |
| D08 | Discussion honnête des limites (synthétique → réel, raccourcis des soldes) | P1 | J6 | R054, R155, R249 | Non | Évaluateur | — | La section « Limitations » du rapport traite au moins ces deux points. |

### E. DEEP LEARNING
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| E01 | Petit MLP (PyTorch ou TensorFlow/Keras), mêmes entrées et mêmes règles anti-fuite que B | P1 | J3 | R170–R172 | B03 | Constructeur | ✅ (architecture) | Le MLP utilise les sorties du pipeline B03, sans prétraitement séparé. |
| E02 | Sortie binaire, perte, optimiseur, gestion du déséquilibre expliquée | P1 | J3 | R173 | Non | Constructeur | ✅ | Le rapport nomme la perte, l'optimiseur et la méthode de déséquilibre choisis. |
| E03 | Suivi sur la validation (arrêt précoce), courbes d'apprentissage enregistrées, graines fixées | P1 | J3 | R174 | Non | Constructeur | ✅ (patience, graine) | Les courbes sont dans `artifacts/figures/`, et deux exécutions donnent le même résultat à la tolérance près. |
| E04 | Même évaluation que les autres modèles (découpages, métriques, procédure de seuil), résultat rapporté honnêtement | P1 | J3 | R175, R176 | D02 | Responsable | — | Le MLP a sa ligne dans le tableau D02, même s'il est moins bon. |

### F. LLM — ASSISTANT DE RÉSUMÉ D'ENQUÊTE
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| F01 | Client LLM derrière une interface remplaçable (hébergé ou local — choix dans `Architecture_Projet.md`), avec délai maximal | P1 | J4 | DM §9, Q10 ; R198, R203 | Non | Constructeur | ✅ (fournisseur, modèle, délai) | Changer de fournisseur ne touche qu'un fichier de configuration et une implémentation. |
| F02 | Faux client LLM pour les tests (réponses écrites à l'avance : valide, mal formée, avec allégation, avec mauvais score…) | P1 | J4 | R203, R301 | Non | Constructeur | — | Toute la suite de tests passe sans réseau. |
| F03 | Gabarit de prompt versionné : instructions système fixes, section de données séparée | P1 | J4 | R183, R186 | Non | Constructeur | ✅ (version du gabarit) | La version du gabarit est enregistrée dans chaque événement d'audit de rédaction. |
| F04 | Contexte minimal : ID du cas, score officiel et bande, variables vérifiées, preuves approuvées, version du modèle | P1 | J4 | R181, R185 | Non | Constructeur | ✅ (liste de champs) | Le prompt ne contient aucun champ hors de la liste autorisée (test). |
| F05 | Notes de cas traitées comme des données non fiables (protection contre l'injection de prompt) | P1 | J4 | R184, R196, R242 | K03 | Constructeur | — | Une note piégée ne change ni le score, ni la structure, ni l'issue de la validation (test). |
| F06 | Sortie JSON structurée (les 10 champs de §10.2, extensible) | P1 | J4 | R182, R187 | Non | Relecteur | — | Le brouillon contient les 10 champs, sinon il est rejeté par H01. |
| F07 | Preuves insuffisantes → incertitude écrite + recommandation de revue humaine | P1 | J4 | R197 | Non | Relecteur | — | Un cas sans preuve produit au moins une incertitude et une étape de revue recommandée. |
| F08 | Mesure de la latence et du coût par cas, documentés | P1 | J4 | R199–R202 | Non | Évaluateur | — | Le rapport donne la latence typique, le coût par cas (ou « 0 en local ») et ce qui se passe en cas de délai dépassé. |

### G. WORKFLOW AGENTIQUE ET OUTILS
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| G01 | Machine à états explicite : 11 états, transitions de §11.3 | P1 | J4 | R018, R215, R216 | Non | Constructeur | — | Chaque transition autorisée est codée et testée. |
| G02 | Refus des transitions invalides (ex. RECEIVED → VALIDATED) | P1 | J4 | R218 | G01 | Constructeur | — | Un test vérifie le refus et l'événement d'audit associé. |
| G03 | Orchestrateur écrit à la main ; le LLM n'est qu'une étape ; ordre : réception → validation de l'entrée → score → preuves → brouillon → validation → revue humaine → audit et statut final | P1 | J4 | R210–R214 | Non | Constructeur | — | Un cas normal traverse les états dans cet ordre, et l'audit en garde la trace. |
| G04 | Outil `score_transaction()` : charge le pipeline sauvegardé et renvoie score, seuil, bande et version du modèle | P1 | J4 | R219, R221 ; DM §8.3 | C07 | Constructeur | — | L'outil est appelé par l'orchestrateur (pas seulement documenté) et testé (arguments valides et invalides). |
| G05 | Outil `retrieve_case_evidence()` : preuves synthétiques approuvées depuis un stockage local, avec ID de source, ou résultat vide explicite | P1 | J4 | R222, R217 | Non | Constructeur | — | Un ID inconnu renvoie un résultat vide explicite, sans exception non gérée (test). |
| G06 | Outil `validate_investigation_json()` appelé par le workflow | P1 | J4 | R223 | H01 | Constructeur | — | Voir H01. |
| G07 | Outil `write_audit_event()` | P1 | J4 | R224 | I01 | Constructeur | — | Voir I01. |
| G08 | Stockage local de preuves synthétiques approuvées (généré, versionné, sans données personnelles) | P1 | J4 | R181, R222 | Non | Constructeur | ✅ (chemin) | Chaque preuve a un ID de source unique ; le stockage est reproductible par un script. |
| G09 | Délais maximaux et nouvelles tentatives **limitées** pour chaque outil et pour le LLM ; états FAILED et VALIDATION_REJECTED, avec leur cause | P1 | J4 | R211, R229, R247 | Non | Constructeur | ✅ (délais, nombre d'essais) | Quand les essais sont épuisés, le cas passe à l'état d'échec nommé, avec la cause dans l'audit et à l'écran. |
| G10 | Idempotence : clé = ID du cas + étape, ce qui empêche les appels en double | P1 | J4 | R230, R307 | Non | Constructeur | — | Soumettre deux fois la même étape ne crée ni un deuxième score ni un deuxième brouillon (test). |
| G11 | Tout cas VALIDATED passe en HUMAN_REVIEW ; politique de routage écrite (priorité, preuve manquante, rejet, panne) | P1 | J4 | R231–R233 | Non | Relecteur | ✅ (règles de priorité) | La file de revue montre la priorité calculée selon la politique écrite. |
| G12 | Aucun outil ne peut faire une action financière (outils en lecture seule ou à portée limitée) | P1 | J4 | DM §8.1 ; R002, R005, R247 | K04 | Constructeur | — | Un test vérifie qu'aucun outil enregistré n'offre une action de paiement, de blocage ou de gel. |

### H. VALIDATION INDÉPENDANTE ET GARDE-FOUS
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| H01 | Validateur déterministe, séparé du LLM : JSON lisible + schéma + champs requis | P1 | J4 | DM §8.3 ; R191, R187 | Non | Constructeur | — | Un JSON mal formé ou incomplet est rejeté, avec une raison précise. |
| H02 | Contrôle de la valeur de `risk_level` (low / medium / high) | P1 | J4 | R305 | H01 | Constructeur | — | Une étiquette invalide est rejetée (test). |
| H03 | Contrôle du score : `model_score` et `model_version` égaux à la sortie officielle de G04 | P1 | J4 | R193 | Non | Constructeur | ✅ (tolérance) | Un score modifié est détecté et rejeté (test). |
| H04 | Contrôle des références : chaque `source_id` appartient aux preuves fournies | P1 | J4 | R188, R190 | Non | Constructeur | — | Un ID de preuve inventé est rejeté (test). |
| H05 | Contrôle des formulations interdites ou affirmatives (liste « Avoid » de §12.2 + mots d'affirmation définitive) | P1 | J4 | R194, R251 | Non | Constructeur | ✅ (liste de termes) | Le texte « This customer committed fraud. » est rejeté ou signalé (test). |
| H06 | Nouvelle tentative limitée de rédaction après un rejet, puis VALIDATION_REJECTED : aucun résumé n'est montré comme fiable, le relecteur ne voit que les données structurées | P1 | J4 | R215, R233 | G09 | Relecteur | ✅ (essais) | Après N rejets, le cas est VALIDATION_REJECTED, et l'écran ne montre pas le brouillon comme fiable. |

### I. JOURNAL D'AUDIT
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| I01 | Événement d'audit structuré pour chaque changement d'état, chaque appel d'outil et chaque décision du relecteur (ID du cas, état, acteur, action, résultat, horodatage) | P1 | J4 | DM §8.4 ; R019, R248 | Non | Constructeur | — | Un cas de bout en bout produit un événement par étape, sans trou (test). |
| I02 | Export de l'audit en CSV et / ou JSON | P1 | J5 | R292 | Non | Relecteur, Évaluateur | — | Un bouton exporte un fichier lisible par un tableur, avec le même nombre de lignes qu'à l'écran. |
| I03 | Aucun secret dans les logs et l'audit | P1 | J5 | R306, R246 | K | Constructeur | — | Un test vérifie que la clé d'API n'apparaît dans aucun log. |
| I04 | L'audit reste local, il n'est pas versionné | P1 | J4 | DM §13 | Non | Constructeur | ✅ (chemin) | Le fichier d'audit figure dans `.gitignore`. |

### J. APPLICATION ET REVUE HUMAINE
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| J01 | Application Streamlit ou Gradio (choix dans `Architecture_Projet.md`), lancée par une commande, sans notebook | P1 | J5 | DM §7 ; R021, R280, R281 | Non | Relecteur, Évaluateur | — | La commande du README ouvre l'app et un cas va de la réception jusqu'à la revue. |
| J02 | Bandeau visible : prototype pédagogique, données synthétiques, « le score et le résumé ne prouvent rien » | P1 | J5 | R004, R006, R294 | Non | Relecteur | — | Le bandeau est visible sur chaque écran. |
| J03 | Éléments 1 à 4 : choix du cas / saisie de l'ID ; variables vérifiées ; score + bande + seuil ; modèle, version et date d'entraînement | P1 | J5 | R282–R285 | Non | Relecteur | — | Les 4 éléments sont visibles pour un cas normal. |
| J04 | Éléments 5 à 9 : preuves avec ID de source ; brouillon marqué « AI draft for human review » ; références reliées à la liste des preuves ; incertitudes jamais cachées ; statut du validateur avec ses raisons | P1 | J5 | R286–R290 | Non | Relecteur | — | Les 5 éléments sont visibles ; en cas de rejet, les raisons s'affichent. |
| J05 | Élément 10 : décision du relecteur (clôturer, escalader, plus d'informations) + commentaire facultatif, enregistrée | P1 | J5 | R291, R019 | I01 | Relecteur | — | Chaque décision crée un événement d'audit et fait passer le cas à l'état final correspondant (test). |
| J06 | Élément 11 : piste d'audit visible et exportable | P1 | J5 | R292 | I02 | Relecteur | — | Voir I02. |
| J07 | Élément 12 : messages d'erreur clairs (entrée invalide, panne d'outil, échec de validation) | P1 | J5 | R293 | Non | Relecteur | — | Chacun des 3 cas affiche un message lisible, sans trace technique brute. |
| J08 | File de revue triée par priorité (politique G11) | P1 | J5 | R231 | G11 | Relecteur | — | Les cas prioritaires apparaissent en premier. |
| J09 | Soumissions en double gérées (ou documentées) côté app | P1 | J5 | R307 | G10 | Relecteur | — | Un double clic ne crée pas deux cas (test ou documentation). |

### K. TESTS, SÉCURITÉ ET REPRODUCTIBILITÉ
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| K01 | Suite pytest : ≥ 15 tests, dont ≥ 5 sur le workflow agent / LLM / validation ; déterministes, hors ligne | P1 | J5 | DM §7, §8.7 ; R300, R301 | Non | Évaluateur | — | `pytest` passe hors ligne : au moins 15 tests réussis, dont au moins 5 marqués « validation workflow ». |
| K02 | Couverture des 26 exemples de tests de §14 (Recommandé) | P1 | J5 | R302–R307 | K01 | Constructeur | — | Chaque exemple est couvert par un test ou porte une note « non couvert, raison ». |
| K03 | Test d'injection de prompt avec une note piégée | P1 | J5 | R242, R306 | F05 | Constructeur | — | Voir F05. |
| K04 | Test « aucune action financière possible » | P1 | J5 | R306 | G12 | Constructeur | — | Voir G12. |
| K05 | Secrets en variables d'environnement, `.env` ignoré par git, `.env.example` sans valeurs | P1 | J1 | R246 | Non | Constructeur | ✅ | `.env.example` existe sans valeurs, et `.env` figure dans `.gitignore` dès le premier commit. |
| K06 | Preuves de tests : résumé (exécutés / réussis / échoués), sortie mal formée rejetée, entrée d'audit d'une panne d'outil | P1 | J5 | R308 | Non | Évaluateur | — | `reports/test_evidence/` contient le résumé et au moins ces deux preuves d'échec. |
| K07 | README complet (les 6 rubriques de §16.1) testé sur un environnement propre | P1 | J6 | R324–R329, R357 | Non | Évaluateur | — | Un environnement neuf suit le README jusqu'à l'app et aux tests, sans aide. |
| K08 | Plan de suivi de la dérive du modèle (quoi suivre, quand réentraîner) — plan seulement | P1 | J5 | R245 | Non | Responsable | — | La section du rapport existe. |
| K09 | Registre des risques (les 15 de §12 + ceux propres au design) | P1 | J5 | R240–R252 | `Risk_Register.md` | Constructeur | — | Les 15 risques de l'énoncé y figurent, chacun avec son contrôle. |

### L. LIVRABLES RENDUS
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| L01 | Dépôt `capstone-project-1` structuré comme au §16 (adaptable) | P1 | J1 | R320–R323 | Non | Évaluateur | — | L'arborescence du dépôt correspond à `Architecture_Projet.md` §7. |
| L02 | Documentation des données (livrable B) | P1 | J2 | Livrable B | A02, A04, B07 | Évaluateur | — | Les 5 contenus minimum sont présents. |
| L03 | Rapport technique (livrable C) : 23 sections, 2 500 à 4 000 mots, en anglais | P1 | J6 | R350, R351 | Non | Évaluateur | — | Les 23 sections sont présentes, le nombre de mots est dans la fourchette, et chaque chiffre a passé Q08. |
| L04 | Diagramme d'architecture (≥ 9 composants), conforme au design réel | P1 | J4 | R225 | `Architecture_Projet.md` | Évaluateur | — | Le diagramme contient les 9 composants de §11.5. |
| L05 | Présentation (livrable D) : 10 à 14 diapositives, 14 contenus | P1 | J6 | R352, R353 | Non | Évaluateur | — | Le nombre de diapositives et les contenus sont conformes. |
| L06 | Vidéo de démonstration (livrable E) : 6 à 10 min, 6 éléments montrés et commentés | P1 | J6 | R354, R355 | Non | Évaluateur | — | La minute de chacun des 6 éléments est notée dans la matrice. |
| L07 | Déclaration de contribution, d'originalité et d'usage de l'IA (livrable H), réalisée seul | P1 | J6 | R341–R346 | Non | Évaluateur | — | Une page qui dit le travail fait seul, les sources, l'usage de l'IA et les bibliothèques. |
| L08 | Dossier de défense : soutenance et questions-réponses (livrable F), simulation faite | P1 | J6 | R356, R347 ; Banque §4 | Non | Constructeur | — | Les 73 questions du §1 de la banque sont ✅, et la simulation de défense est faite. |
| L09 | Posts LinkedIn préparés, publiés **après** la note | P1 | J6 | DM §8.10 | Non | Constructeur | — | Aucun post publié avant la note. |

### M. PHASE 2 — APRÈS LA NOTE
| ID | Fonctionnalité | Priorité | Palier produit | Objectif métier servi | Couverte par une autre feature ? | Rôle | Config | Critère d'acceptation |
|---|---|---|---|---|---|---|---|---|
| M01 | Transformation en produit Tensoratech (porte A, idéation, puis palier Standard ou Client) | P2 | Au-delà de J6 — non défini | DM §14 | Non | Constructeur | — | Non défini — sera fixé au changement de palier. |

## 2. HORS SCOPE — PHASE 1
Ce qui pourrait sembler inclus mais ne l'est pas :
- Connexion à un vrai système de paiement, ou toute action financière (G12 l'interdit par test)
- Données réelles ou personnelles, jeux de données alternatifs (Credit Card, AMLSim) sans accord écrit de l'enseignant
- Utilisation d'`isFlaggedFraud` comme variable du modèle principal (comparaison séparée seulement, si elle est faite et justifiée)
- Affirmation « prêt pour la production »
- Authentification, plusieurs utilisateurs, rôles d'accès *(proposé par Claude, accepté avec le Document maître v1.0)*
- Déploiement en ligne : l'app tourne en local *(idem)*
- Flux en temps réel, analyse de graphe ou anti-blanchiment *(idem)*
- Réentraînement automatique : seulement le plan de suivi de la dérive, K08 *(idem)*
- Tout ce qui sert le produit futur (M01)

## 3. RÉPARTITION PAR PHASE
| Phase | Fonctionnalités (IDs) | Nombre |
|---|---|---|
| Phase 1 — Capstone noté (remise 2026-11-06) | A01–A09 · B01–B08 · C01–C08 · D01–D08 · E01–E04 · F01–F08 · G01–G12 · H01–H06 · I01–I04 · J01–J09 · K01–K09 · L01–L09 | 94 (dont 2 « P1 (opt.) » : B08, C04) |
| Phase 2 — Produit Tensoratech (après la note) | M01 | 1 |

Répartition des 94 P1 par jalon :

| Jalon | Fonctionnalités | Nombre |
|---|---|---|
| J1 | K05, L01 | 2 |
| J2 | A01–A08, L02 | 9 |
| J3 | B01–B08, C01–C08, D01–D06, E01–E04 | 26 |
| J4 | D07, F01–F08, G01–G12, H01–H06, I01, I04, L04 | 30 |
| J5 | A09, I02, I03, J01–J09, K01–K04, K06, K08, K09 | 19 |
| J6 | D08, K07, L03, L05–L09 | 8 |

⚠️ **J4 porte 30 fonctionnalités en 3 jours (28 au 30 octobre)** : c'est le jalon le plus chargé, et celui du critère le plus lourd (C6, 16 points). Ce risque va dans `Risk_Register.md` ; la question du découpage revient dans `Architecture_Projet.md` (ordre des couches).

## 4. HISTORIQUE — DÉCISIONS PRISES EN RÉDIGEANT
| Ref | Point | Décision |
|---|---|---|
| F-1 | Les « Example tests » de §14 sont-ils des fonctionnalités ? | Non : regroupés en K02 (couverture), conformément au statut « Recommandé » validé dans la matrice v1.0 — 2026-10-19 |
| F-2 | Les 4 outils suggérés (§11.4) : tous les 4, ou seulement les 2 minimum ? | Les 4 sont en P1 (G04–G07) : ils sont déjà nécessaires au workflow (score, preuves, validation, audit) ; le minimum de 2 est donc dépassé sans travail en plus — proposition, à confirmer par la validation de ce document |
| F-3 | Stockage des preuves synthétiques : l'énoncé dit « approved local store » sans le définir | G08 : un stockage local généré par un script ; la forme (fichiers ou base) se décide dans `Architecture_Projet.md` |
| F-4 | Seuil de score « proche du seuil » pour la revue prioritaire (G11) | Ouvert — la valeur se fixe après D03 (J3) ; à noter dans `Points_A_Trancher_INTERNE` |
| F-5 | Les livrables (rapport, présentation, vidéo) sont-ils des fonctionnalités ? | Oui, module L : au palier Noté, ce qui est rendu est noté au même titre que le code (C10) |

---

## VALIDATION
| Rôle | Nom | Date |
|---|---|---|
| Préparé par | Tensoratech (Claude, chat M2) | 2026-10-19 |
| Validé par (v1.0) | Erman | 2026-10-20 |

---

## ÉCARTS AVEC LE GABARIT v1
- **Sections ajoutées (validées par le fondateur)** : aucune section. Ajouts dans des sections existantes : la phrase de rôle en tête (lien fonctionnalité ↔ matrice au palier Noté) ; la valeur « P1 (opt.) » ; le tableau par jalon et l'alerte J4 en §3.
- **Sections marquées « ne s'applique pas »** : aucune.
- **Questions « ne dit pas encore » tranchées** : « Les phases au-delà du dernier palier défini doivent-elles recevoir un palier avant leur propre CDC ? » → au palier Noté, il n'y a pas de CDC ; la Phase 2 reçoit ses paliers seulement au changement de palier (`Document_Maitre.md` §10), d'où « Au-delà de J6 — non défini ».
- **Ce qui reste ambigu dans le gabarit** :
  - (a) la colonne « Palier produit » suppose des paliers Standard / Client ; au palier Noté, on y met les jalons ;
  - (b) le gabarit ne prévoit pas de lien avec la matrice : je l'ai mis dans la colonne « Objectif métier servi » (IDs R) ;
  - (c) P1 / P2 ne distingue pas « exigé » et « encouragé par la source », d'où « P1 (opt.) ».
