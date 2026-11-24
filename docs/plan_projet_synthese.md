# Plan de projet condensé : Assistant Code du travail burkinabè

**Produit :** assistant de recherche et d'explication sur la **loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso** (441 articles, promulguée par décret n° 2026-0613/PF du 25 mai 2026, Journal Officiel Spécial N°23 du 29 mai 2026).  
**Dépôt public :** `https://github.com/ao627515/Projet_Integrateur_Equipe7` | **Protocole :** `protocole_evaluation.md`.

## 1. Périmètre produit et critères de succès

Notre outil aide gérants de PME, responsables RH, salariés et délégués du personnel (PC et smartphone) à consulter les 441 articles du Code du travail (décrets prévus en extension). Il éclaire la règle applicable (CDD, essai, préavis, télétravail, licenciement) et oriente vers un juriste ou un inspecteur du travail si nécessaire. Il enchaîne : **(1)** recherche des 5 articles les plus pertinents, **(2)** filtrage du hors champ et du doute par trois seuils (`τ_score`, `τ_haut`, `τ_marge`, calculés sur la similarité sémantique pour l'hybride) réglés exclusivement sur le jeu de validation, **(3)** synthèse **RAG** (génération augmentée par recherche) par **LLM** (modèle de langage) encadré par un prompt système strict (`src/generation/prompts.py`, température ≤ 0,1).

Notre objectif est un jeu d'évaluation de **270 questions** (**200 dans le champ + 50 hors champ + 20 doute** ; seuil minimal d'environ 180 questions, soit 150 dans le champ et 30 hors champ, la cible de 270 assurant 81 questions de `Test` pour des intervalles bootstrap fiables et la couverture des 4 strates), dont **`206` à l'aveugle (`76,3 % ≥ 75 %`)**, **`64` `equipe` (`23,7 %`)**, **`30` à renvoi externe (`15 %` du champ)**, **≥ 38 % (`40 %` cible) multi-articles** et une **double annotation sur 30 % stratifié (`81` fiches)**. Le découpage unique **70 % Validation (189) / 30 % Test (81)** stratifié sur `(strate, origine)` et **groupé par `famille_id`** (`random_state = 42`, sans séparer les paraphrases d'un même besoin juridique) est gelé uniquement après validation juridique à 100 % (`Test` reste verrouillé). Les résultats distinguent `aveugle` (principal) et `equipe` (secondaire) :

- **Recherche :** battre **BM25** *(recherche lexicale par mots-clés)* de **≥ +10 pts** en `Succès@5` *(article principal dans le top-5)* et/ou `Rappel@5` *(part moyenne des articles pertinents trouvés)*, validé par **bootstrap apparié 95 %** *(10 000 tirages aléatoires avec remise, borne basse > 0)*, **sans régression sur `Rappel@5`**, avec suivi par **matrice 6 cas `Succès@5 × Rappel@5`** (seuils `0,40` et `0,80`).
- **Refus et doute :** rejeter **≥ 80 %** du hors champ (`15` questions de `Test`) avec **≤ 10 %** de faux refus légitimes, et suivre le taux de clarification pertinente sur les `6` questions `doute` de `Test`.
- **Fidélité LLM :** audit manuel sur **≥ 30 réponses** de `Test` (dont ≥ 5 renvois externes, double relecture ≥ 10) : **≥ 85 %** fidèles, **0 % d'erreur numérique visé** *(≤ 5 % toléré)*, **0 % citation inventée**, **≥ 90 %** respect du prompt.
- **Essai utilisateurs :** **≥ 10 testeurs** (3 questions), réponse **< 10 s** (comparée aux PDF) et **≥ 80 %** d'avis positifs.

## 2. Contributeurs, rôles et organisation

| Contributeur | Rôle principal | Suppléance | Responsabilités clés |
| :--- | :--- | :--- | :--- |
| **COMPAORE Alexis Awossonoyi** | Chef de projet et éthique | Données et qualité | Planning, coordination, relation juriste (`SOULAMA Grace Hope`), collecte à l'aveugle, conformité |
| **TAPSOBA Faridatou** | Données et qualité | Chef de projet | Corpus (`data/raw/` vers `data/processed/`), contrôle OCR `1..441`, consignes d'étiquetage, reproductibilité |
| **OUEDRAOGO Abdoul Aziz** | Modélisation et intégration | Éthique et déploiement | Dépôt Git et Kanban, pipelines BM25 / sémantique / hybride / RAG, évaluation, prototype web |

Un rôle définit une responsabilité principale sans cloisonnement : chacun code, rédige, relit et maîtrise tout le système.

- **Méthode et rituels :** cycle data **CRISP-DM** avec **tranche verticale** rapide *(chaîne complète dès BM25 avant d'itérer)* et cycles hebdomadaires sur Kanban **GitHub Projects** (`À faire`, `En cours`, `En relecture`, `Terminé`). Planification le jeudi (30 min), point fixe le lundi à 22 h (45 min, Meet/WhatsApp vocal), 2 à 3 synchros de 10 min par semaine et rétrospective hebdomadaire dans `docs/journal_de_bord.md`.
- **Règles internes :** décisions à la majorité (le chef de projet tranche), préavis **36 h** en cas de retard, réponse sous **24 h en semaine / 12 h le week-end** *(disponibilité accrue pour les phases intensives du week-end ; WhatsApp pour l'urgent)*, relecture croisée obligatoire et suivi via Git, journal de bord, présence et revue entre pairs.

## 3. Planning (19/11 au 22/12/2026), tâches bloquantes et marges

| Période | Phase | Objectifs du cycle | Échéance |
| :--- | :--- | :--- | :---: |
| **19/11 au 24/11** | Organisation et données | Dépôt public + Kanban + 1 PR/contributeur ; extraction OCR des 2 PDF officiels (`1..441` dans `data/processed/code_travail_2026_articles_verifies.json`/`.csv`), exploration, consignes, jeu de **270 q.** (`206 aveugle / 64 equipe`) et calendrier juriste. | 24/11 |
| **26/11 au 01/12** | Modélisation et évaluation | Découpage 70/30 stratifié groupé par `famille_id` (`189 / 81`, gelé après validation juriste 100 %, `Test` verrouillé) ; baseline **BM25** + tranche verticale ; métriques (`Succès@5`, `Rappel@5`, matrice 6 cas, bootstrap 95 %), réglage des seuils et audit du prompt sur `Validation`. | 01/12 |
| **03/12 au 08/12** | Modélisation itérative et déploiement | **Embeddings** *(sens)* + **hybride** réglés sur `Validation`, puis évaluation finale sur `Test` (audit ≥ 30 réponses) ; application web PC/smartphone, mode dégradé local sans LLM et **essai utilisateurs** (≥ 10 testeurs). | 08/12 |
| **10/12 au 15/12** | Évaluation finale | Bilan métier, documentation finale, audit reproductibilité (`uv sync`, tests verts) et éthique. | 15/12 |
| **16/12 au 22/12** | Clôture | Démonstration en direct du produit par les 3 contributeurs. | 16-22/12 |

**Tâches bloquantes :** **(1)** dépôt public propre (zéro contact ni clé API, Kanban actif, 1 PR relue par contributeur) ; **(2)** corpus vérifié `1..441` (promulgation confirmée au **25 mai 2026**, décret n° 2026-0613/PF) ; **(3)** validation par `SOULAMA Grace Hope` des 270 questions (`revue_juriste_270.csv`) avant gel du découpage `189 / 81`. **Marges :** ~20 % par semaine (coupures réseau/électricité, OCR, retours CRISP-DM) et expérimentations bornées (*timebox*) à 1,5 à 2 jours max.

## 4. Plan d'action des deux premières semaines (19/11 au 01/12/2026)

| ID | Tâche (courte, vérifiable, bornée) | Resp. | Éch. | Critère de vérification |
| :---: | :--- | :--- | :---: | :--- |
| **T1** | Pousser arborescence, `README.md`, `.gitignore`, `docs/plan_projet.md` et `docs/protocole_evaluation.md` ; créer Kanban. | OUEDRAOGO | 22/11 | Push sur `main`, collaborateurs et Kanban actifs |
| **T2** | Acter la date de promulgation (**25 mai 2026**), harmoniser la documentation (441 art., délai 12 h), valider les règles internes, confirmer le calendrier par lots juriste. | COMPAORE | 23/11 | Dates sourcées, règles signées, calendrier juriste confirmé |
| **T3** | Fusionner ≥ 1 branche + Pull Request relue par contributeur. | Tous | 23/11 | ≥ 1 commit par contributeur via PR relue |
| **T4** | Extraire les 441 articles depuis les 2 PDF (`scripts/extract_code_pdf_ocr.py`) vers `code_travail_2026_articles_verifies.json`/`.csv`, vérifier `1..441`, rédiger consignes, explorer. | TAPSOBA | 24/11 | 441 articles sans trou (0 `U+FFFD`), consignes relues, `01_exploration.ipynb` prêt |
| **T5** | Finaliser le jeu étiqueté (**270 q.** : `200+50+20 doute`, `206 aveugle / 64 equipe`, double annotation 81 fiches, contrôle `scripts/qa_and_split_dataset.py`), valider avec la juriste (`revue_juriste_270.csv`), geler découpage 70/30 groupé. | TAPSOBA, COMPAORE | 27/11 | 100 % `valide` juriste ; `validation.json` (189) et `test.json` (81, 0 fuite `famille_id`) gelés |
| **T6** | Implémenter **BM25** (`src/retrieval/bm25.py`), `02_modele_reference.ipynb` et la tranche verticale (*timebox 1,5 j*). | OUEDRAOGO | 28/11 | Pipeline exécutable de bout en bout (question, top-5, réponse) |
| **T7** | Implémenter `src/evaluation/` (`Succès@5`, `Rappel@5`, matrice 6 cas, `aveugle`/`equipe`, bootstrap 10 000) et calibrer `τ_score`/`τ_haut`/`τ_marge` sur `Validation`. | OUEDRAOGO | 29/11 | Script vert ; seuils calibrés sur `Validation` (≥ 80 % / ≤ 10 % / `doute` ; `Test` intact) |
| **T8** | Intégrer le prompt (`src/generation/prompts.py`, température ≤ 0,1), auditer sur `Validation` (grille 5 critères, double relecture ≥ 10), rapport S2. | Tous | 01/12 | Prompt validé sur `Validation`, rapport S2 produit (audit `Test` en S3) |

## 5. Registre des risques

`P` et `I` de 1 à 3 (`Crit. = P × I`). **Élevé (6 ou 9) :** action immédiate, suivi à chaque synchro et plan de repli déclenché par le chef de projet ; **Moyen (3 ou 4) :** suivi hebdomadaire ; **Faible (1 ou 2) :** rétrospective.

| N° | Risque | Catégorie | P | I | Crit. | Stratégie et action | Resp. | Statut |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **R1** | Jeu de test petit, biaisé ou mono-article | Données / Éval. | 3 | 3 | **9** | **Réduire :** jeu **270 q.** (`206 aveugle / 64 equipe`, ≥ 38 % multi-articles, double annotation 81), découpage 70/30 groupé `famille_id`, matrice 6 cas, bootstrap 95 %. | COMPAORE, OUEDRAOGO | Sous contrôle |
| **R2** | Erreurs OCR sur chiffres, délais et articles | Données | 2 | 3 | **6** | **Réduire :** `data/raw/` intact, `scripts/extract_code_pdf_ocr.py`, contrôle `1..441` (0 `U+FFFD`), `data/overrides_articles.json`. | TAPSOBA | Maîtrisé |
| **R3** | Inventions, erreurs numériques ou écart au prompt | Technique | 2 | 3 | **6** | **Réduire :** prompt strict (temp. ≤ 0,1), contrôle citations (0 % inventée), audit ≥ 30 rép. (≥ 85 % fidèles, 0 % err. num. visé / ≤ 5 % toléré, ≥ 90 % prompt), texte officiel brut prioritaire. | OUEDRAOGO | Planifié |
| **R4** | Fuite de contacts ou clés API sur dépôt public | Éthique / Jurid. | 2 | 3 | **6** | **Éviter :** fichiers privés locaux ignorés par Git, `.env` dans `.gitignore`, zéro stockage des requêtes. | COMPAORE | Sous contrôle |
| **R5** | Cadence serrée ou retard relecture juridique | Planning | 3 | 2 | **6** | **Réduire :** calendrier par lots, parallélisation, préavis 36 h, marge 20 %. | COMPAORE | Ouvert |
| **R6** | Panne d'API LLM ou coupure réseau/électricité | Infra. | 2 | 2 | **4** | **Réduire :** push quotidien GitHub, **mode dégradé local sans LLM** (top-5 articles officiels). | OUEDRAOGO | Planifié |
| **R7** | Hybride sans gain +10 pts sur BM25 (`aveugle`) | Technique | 2 | 2 | **4** | **Accepter / Réduire :** tester embeddings et poids sur `Validation` (*1,5 j*) ; sinon analyser les causes. | OUEDRAOGO | Surveillance |

## 6. Dépôt Git, architecture et règles de travail

- **Architecture :** racine (`README.md`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example`) ; `data/raw/` *(2 PDF officiels 127-128 p. intacts)*, `data/overrides_articles.json` et `data/processed/` *(`code_travail_2026_articles_verifies.json`/`.csv`, `jeu_evaluation_270.json`, `revue_juriste_270.csv`, `validation.json` [189], `test.json` [81])* ; `scripts/` *(`extract_code_pdf_ocr.py`, `qa_and_split_dataset.py`)* ; `notebooks/` *(1 auteur/notebook, sorties effacées)* ; `src/` *(`common/`, `ingestion/`, `retrieval/`, `generation/`, `evaluation/`, `app/`)* ; `models/` ; `reports/` ; `tests/` ; `docs/` *(`plan_projet.md`, `plan_projet_synthese.md`, `protocole_evaluation.md`, `consignes_etiquetage.md`, `architecture_pipeline.md`, `journal_de_bord.md` à chaque session, `comptes_rendus/` à chaque réunion, `README.md` à chaque étape)*. Les dossiers de travail privés restent locaux et exclus de Git.
- **Règles Git :** jamais sur `main` ; une branche dédiée par tâche fusionnée via **Pull Request relue par ≥ 1 contributeur**, après `git pull` et commits courts (`feat`, `fix`, `docs`, `test`, `chore`). **Aucun code par WhatsApp** ; aucune clé API, donnée personnelle ni fichier volumineux versionné.
