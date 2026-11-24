# Plan de projet : Assistant Code du travail burkinabè

**Produit :** Assistant de recherche et d'explication sur la **loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso** (441 articles, promulguée par décret n° 2026-0613/PF du 25 mai 2026, publiée au Journal Officiel Spécial N°23 du 29 mai 2026)  
**Dépôt Git (public) :** `https://github.com/ao627515/Projet_Integrateur_Equipe7`  
**Document associé :** `protocole_evaluation.md`

---

## 1. Synthèse du périmètre produit

Notre application accompagne les gérants de PME, responsables RH, salariés et délégués du personnel sur PC et smartphone dans la consultation du Code du travail burkinabè (441 articles, décrets d'application prévus en extension). Elle éclaire la règle applicable (CDD, essai, préavis, télétravail, licenciement) et signale les situations nécessitant l'avis d'un juriste ou de l'inspecteur du travail.

Notre architecture **RAG** (génération augmentée par recherche documentaire) enchaîne trois étapes :
1. recherche des 5 articles les plus pertinents (en combinant **BM25**, recherche lexicale par mots-clés, et **embeddings**, vecteurs sémantiques capturant le sens) ;
2. filtrage du hors champ et de la zone de doute par trois seuils (`τ_score`, `τ_haut`, `τ_marge`) réglés exclusivement sur le jeu de validation (70 % du jeu d'évaluation) ;
3. rédaction de la réponse par un **LLM** (modèle de langage) encadré par un prompt système versionné (`temperature ≤ 0,1`).

**Critères de succès mesurables :**
- Sur un jeu stratifié ciblant **270 questions** (**200 dans le champ + 50 hors champ + 20 doute**, seuil minimal d'environ 180 questions dont 150 dans le champ et 30 hors champ ; cible choisie pour obtenir 81 questions en `Test` et couvrir les 4 strates tout en restant compatible avec une validation juridique à 100 %, `206 aveugle = 76,3 % ≥ 75 %` et `64 equipe = 23,7 %`, `15 %` `renvoi_externe`, `≥ 38 %` / `40 %` cible multi-articles, double annotation sur 30 % stratifié = 81 fiches), le découpage unique **70 % Validation (189) / 30 % Test (81)** stratifié sur `(strate, origine)` et **groupé par `famille_id`** (sans séparer les paraphrases d'un même besoin juridique) est gelé uniquement après validation juridique à 100 %, avec `Test` verrouillé jusqu'à la mesure finale.
- **Recherche :** dépasser la référence **BM25** d'au moins **+10 points** sur `Succès@5` (présence de l'article principal dans le top-5) et/ou `Rappel@5` (part moyenne des articles attendus retrouvés dans le top-5), validé par un test statistique **bootstrap apparié à 95 %** ($B = 10\,000$ rééchantillonnages, borne basse > 0), **sans régression sur `Rappel@5`**, avec suivi par matrice à 6 cas `Succès@5 × Rappel@5` (seuils `0,40` et `0,80`).
- **Refus et doute :** rejeter ≥ 80 % du hors champ (≤ 10 % de faux refus légitimes) et suivre la demande de clarification sur les `6` questions `doute` de `Test`.
- **Fidélité des réponses :** auditer manuellement **≥ 30 réponses** stratifiées sur `Test` (dont ≥ 5 renvois externes : ≥ 85 % fidèles, **0 % d'erreur numérique visé / ≤ 5 % toléré**, 0 % citation inventée, ≥ 90 % respect du prompt système).
- **Essai utilisateurs :** valider avec **≥ 10 testeurs** (3 questions chacun, temps de réponse < 10 s, ≥ 80 % d'avis positifs).

---

## 2. Contributeurs, rôles et suppléance

| Contributeur | Rôle principal | Rôle de suppléance | Responsabilités clés |
| :--- | :--- | :--- | :--- |
| **COMPAORE Alexis Awossonoyi** | Chef de projet et référent éthique | Suppléant Données et qualité | Planning, coordination, relation avec la juriste (`SOULAMA Grace Hope`), collecte à l'aveugle, conformité éthique |
| **TAPSOBA Faridatou** | Responsable données et qualité | Suppléante Chef de projet | Corpus (`data/raw/` vers `data/processed/`), contrôle OCR `1..441`, consignes d'étiquetage, reproductibilité |
| **OUEDRAOGO Abdoul Aziz** | Responsable modélisation et intégration | Suppléant Éthique et déploiement | Dépôt Git et Kanban, pipelines BM25/sémantique/hybride/RAG, protocole et scripts d'évaluation (bootstrap), interface web |

Un rôle définit une responsabilité principale sans cloisonnement : chaque contributeur développe, rédige, relit et maîtrise l'ensemble du système.

---

## 3. Méthode, rituels de suivi et outils

- **Démarche combinée :** cycle data **CRISP-DM** (itérations préparatoires sur les données et la modélisation, avec une **tranche verticale** rapide livrant une première chaîne complète avec BM25 avant d'itérer) et organisation **Scrum/Kanban** par cycles hebdomadaires.
- **Rituels :**
  - **Planification hebdomadaire :** point fixe le **jeudi** (30 min) et point hebdomadaire le **lundi à 22h00** (45 min max, présentiel, Google Meet ou WhatsApp vocal), avec répartition des tâches et vote à la majorité (le chef de projet tranche en cas d'égalité).
  - **Points de synchronisation :** **2 à 3 fois par semaine, 10 minutes** (vocal WhatsApp accepté) pour lever les blocages et suivre les risques élevés.
  - **Revue et rétrospective :** revue à chaque étape hebdomadaire ; rétrospective de **10 minutes en fin de semaine**, consignée à tour de rôle dans `docs/journal_de_bord.md`.
- **Outils partagés :** GitHub (**dépôt public**), tableau Kanban (**GitHub Projects** : `À faire`, `En cours`, `En relecture`, `Terminé`), WhatsApp / Google Meet, Google Drive / Colab.
- **Règles de fonctionnement :** préavis de **36 h** avant échéance en cas de retard, délai de réponse de **24 h en semaine et 12 h le week-end** (pour soutenir le rythme des cycles intensifs du week-end, WhatsApp restant réservé à l'urgent), relecture croisée obligatoire de chaque Pull Request et document. Le suivi repose sur l'historique Git, le journal de bord, la présence aux points et la revue entre pairs.

---

## 4. Planning (19/11 au 22/12/2026), tâches bloquantes et marges

### 4.1 Feuille de route semaine par semaine

| Période | Phase | Objectifs du cycle | Étape et échéance |
| :--- | :--- | :--- | :--- |
| **19/11 au 24/11/2026** | Organisation, compréhension et préparation des données | Plan de projet, dépôt Git public structuré, Kanban et ≥ 1 PR relue par contributeur ; extraction OCR locale des 2 PDF officiels (`1..441` dans `data/processed/code_travail_2026_articles_verifies.json` et `.csv`), exploration du corpus ; consignes d'étiquetage, constitution du jeu de **270 questions** (`200+50+20 doute`, `206 aveugle / 64 equipe`) et calendrier de relecture juridique. | **Phase 1 : Architecture et données** *(24/11/2026)* |
| **26/11 au 01/12/2026** | Préparation, modélisation initiale et évaluation | Découpage unique stratifié groupé par `famille_id` 70/30 (`Validation` 189 / `Test` 81 sur `strate × origine`, `random_state=42`, gelé après validation juriste à 100 %, `Test` verrouillé) ; baseline **BM25** et tranche verticale complète ; mise en place du protocole d'évaluation sur `Validation` (`Succès@5`, `Rappel@5`, matrice 6 cas, séparation `aveugle` vs `equipe`, bootstrap apparié 95 %, calibration `τ_score`/`τ_haut`/`τ_marge`, audit manuel du prompt système sur `Validation`). | **Phase 2 : Baseline et évaluation** *(01/12/2026)* |
| **03/12 au 08/12/2026** | Modélisation itérative et déploiement | Embeddings et **hybride (BM25 + sémantique)** réglés sur `Validation`, puis évaluation finale unique sur `Test` verrouillé (≥ +10 pts vs BM25 sans régression `Rappel@5`, refus sur similarité cosinus : ≥ 80 % hors champ, ≤ 10 % faux refus ; audit manuel de **≥ 30 réponses** stratifiées dont ≥ 5 renvois externes) ; application web légère (PC et smartphone), mode dégradé local sans LLM ; **essai utilisateurs** (≥ 10 testeurs, 3 questions, chronométrage outil vs PDF). | **Phase 3 : Modèle hybride et prototype** *(08/12/2026)* |
| **10/12 au 15/12/2026** | Évaluation finale et documentation | Bilan du critère métier, documentation finale, audit de reproductibilité (`uv sync`, tests verts) et audit éthique. | **Phase 4 : Documentation finale** *(15/12/2026)* |
| **16/12 au 22/12/2026** | Clôture | Démonstration en direct du produit par les 3 contributeurs. | **Démonstration produit** |

### 4.2 Tâches bloquantes (priorité haute)

1. **Initialisation propre du dépôt public :** premier push sans contact personnel ni clé API, ajout des collaborateurs, activation du Kanban et fusion d'une première PR relue par chacun.
2. **Production du corpus structuré vérifié (`1..441`) dans `data/processed/code_travail_2026_articles_verifies.json` et `.csv` :** extrait des deux PDF officiels (`127` et `128` pages, promulgation confirmée au **25 mai 2026** sur le décret n° 2026-0613/PF) via `scripts/extract_code_pdf_ocr.py`, indispensable pour l'exploration et le lancement de BM25.
3. **Jeu de 270 questions, consignes d'étiquetage et relecture juridique :** le jeu stratifié (`200 dans_le_champ + 50 hors_champ + 20 doute`, `206 aveugle / 64 equipe`, `15 %` `renvoi_externe`, `≥ 38 %` multi-articles, double annotation sur 81 fiches) exporté dans `data/processed/revue_juriste_270.csv` et relu par `SOULAMA Grace Hope` conditionne le gel du découpage `189 / 81` et la validité de l'évaluation du 01/12.

### 4.3 Marges et gestion de la cadence

- **Réserve de ~20 % du temps :** chaque semaine conserve une marge pour absorber les coupures d'électricité ou d'Internet, les corrections OCR et les allers-retours entre données et modélisation.
- **Parallélisation et durée bornée (*timebox*) :** nous menons en parallèle la préparation des données et le développement, et bornons toute expérimentation (choix d'embeddings, réglage de seuils) à **1 à 2 jours maximum**.

---

## 5. Plan d'exécution des deux premières semaines (19/11 au 01/12/2026)

| Semaine | ID | Tâche (courte, vérifiable, bornée) | Responsable | Échéance | Critère de vérification |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **S1** | **T1** | Pousser la structure du dépôt (`README.md`, `.gitignore`, `docs/protocole_evaluation.md`, `docs/plan_projet.md`) sur le dépôt public GitHub et créer le Kanban. | OUEDRAOGO A. Aziz | 22/11 | Premier push sur `main`, collaborateurs ajoutés, Kanban actif avec colonnes. |
| **S1** | **T2** | Acter la date de promulgation confirmée (**25 mai 2026**, décret n° 2026-0613/PF), harmoniser la documentation (périmètre 441 articles, délai 12 h week-end), valider les règles internes et organiser la collecte à l'aveugle et le calendrier par lots avec `SOULAMA Grace Hope`. | COMPAORE Alexis | 23/11 | Dates sourcées ; règles validées ; calendrier par lots confirmé avec `SOULAMA Grace Hope`. |
| **S1** | **T3** | Fusionner au moins 1 branche + Pull Request relue par contributeur (`docs/protocole-eval`, `docs/consignes-etiquetage`, `docs/protocole-utilisateurs`). | Tous (3 membres) | 23/11 | ≥ 1 commit par contributeur visible dans l'historique via PR relue. |
| **S1** | **T4** | Extraire et vérifier les 441 articles depuis les 2 PDF officiels (`scripts/extract_code_pdf_ocr.py`) vers `data/processed/code_travail_2026_articles_verifies.json` et `.csv`, contrôler `1..441` + délais critiques, rédiger `docs/consignes_etiquetage.md` et explorer le corpus. | TAPSOBA Faridatou | 24/11 | 441 articles validés sans trou (0 caractère `U+FFFD`), consignes relues, notebook `01_exploration.ipynb` prêt. |
| **S2** | **T5** | Finaliser le jeu de **270 questions** (`data/processed/jeu_evaluation_270.json`, `200+50+20 doute`, `206 aveugle / 64 equipe`, double annotation 81 fiches, contrôle via `scripts/qa_and_split_dataset.py`), faire valider les 270 lignes (`revue_juriste_270.csv`) par la juriste puis geler le découpage stratifié groupé par `famille_id` 70/30 (`validation.json` et `test.json`, `random_state=42`). | TAPSOBA Faridatou et COMPAORE Alexis | 27/11 | 100 % `statut_relecture_juriste == "valide"` ; `validation.json` (189) et `test.json` (81, verrouillé, 0 fuite `famille_id`) gelés avec SHA-256. |
| **S2** | **T6** | Implémenter la baseline **BM25** (`src/retrieval/bm25.py`), le notebook `02_modele_reference.ipynb` et la tranche verticale complète (*timebox 1,5 jour*). | OUEDRAOGO A. Aziz | 28/11 | Pipeline exécutable de bout en bout (question, top-5 BM25, réponse). |
| **S2** | **T7** | Implémenter `src/evaluation/` (`Succès@5`, `Rappel@5`, matrice 6 cas aux seuils `0,40` et `0,80`, séparation `aveugle`/`equipe`, bootstrap apparié 95 % avec $B=10\,000$) et calibrer les seuils `τ_score`, `τ_haut`, `τ_marge` sur `Validation` uniquement. | OUEDRAOGO A. Aziz | 29/11 | Script d'évaluation vert ; seuils calibrés sur `Validation` (≥ 80 % refus hors champ, ≤ 10 % faux refus, clarification `doute` ; `Test` non touché). |
| **S2** | **T8** | Implémenter le prompt système (`src/generation/prompts.py`, `temperature ≤ 0,1`), auditer manuellement la fidélité sur `Validation` (grille 5 critères : fidélité, nombres exacts, citations valides, renvoi externe, respect du prompt) et produire le rapport d'évaluation S2 (l'audit final ≥ 30 réponses sur `Test` étant exécuté en S3 après gel du modèle hybride). | Tous (3 membres) | 01/12 | Prompt validé sur `Validation` (double relecture sur ≥ 10 réponses), rapport d'évaluation S2 produit. |

---

## 6. Registre des risques

Échelle : **P (Probabilité)** de `1` (peu probable) à `3` (probable) ; **I (Impact)** de `1` (gênant) à `3` (bloquant) ; **Crit. = P × I** (`6 ou 9` = Élevé avec action immédiate et suivi à chaque synchronisation ; `3 ou 4` = Moyen avec suivi hebdomadaire ; `1 ou 2` = Faible revu en rétrospective). Si un risque élevé se réalise, le chef de projet déclenche immédiatement le plan de repli et prévient les contributeurs.

| N° | Risque | Catégorie | P (1-3) | I (1-3) | Crit. | Stratégie et action | Resp. | Statut |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **R1** | Jeu de test trop petit, biaisé ou mono-article faussant la comparaison à BM25 | Données / Évaluation | 3 | 3 | **9** | **Réduire :** jeu de **270 questions** (`200+50+20 doute`, `206 aveugle / 64 equipe`, ≥ 38 % multi-articles, 0 fuite lexicale, double annotation 81 fiches), découpage 70/30 stratifié groupé par `famille_id`, `Succès@5` + `Rappel@5` + matrice 6 cas séparés (`aveugle`/`equipe`) + bootstrap apparié 95 % ($B=10\,000$). | Chef de projet et Modélisation | **Sous contrôle (attente juriste)** |
| **R2** | Erreurs d'OCR sur les 2 PDF officiels (127-128 p. : chiffres, délais, montants, numéros d'articles) | Données | 2 | 3 | **6** | **Réduire :** `data/raw/` jamais modifié ; extraction déterministe via `scripts/extract_code_pdf_ocr.py`, contrôle `1..441` (0 `U+FFFD`), correctifs visuels persistants (`data/overrides_articles.json`) dans `data/processed/code_travail_2026_articles_verifies.json`. | Resp. données | **Maîtrisé (441/441 vérifiés)** |
| **R3** | Inventions, erreurs numériques ou non-respect du prompt système par le LLM | Technique | 2 | 3 | **6** | **Réduire :** prompt système strict (`temperature ≤ 0,1`), contrôle automatique des citations (0 % inventée), audit manuel sur ≥ 30 réponses (≥ 85 % fidèles, 0 % erreur numérique visé / ≤ 5 % toléré, `Respect du prompt` ≥ 90 %, renvoi externe vérifié), affichage prioritaire du texte officiel brut. | Resp. modélisation | **Planifié** |
| **R4** | Exposition de données personnelles ou clés API sur le **dépôt GitHub public** | Éthique et juridique | 2 | 3 | **6** | **Éviter :** séparation stricte entre les dossiers privés locaux et le dépôt public (zéro contact personnel, `.env` ignoré dans `.gitignore`), zéro stockage des requêtes utilisateurs. | Référent éthique | **Sous contrôle** |
| **R5** | Cadence serrée ou retard de la relecture juridique élargie | Planning | 3 | 2 | **6** | **Réduire :** calendrier par lots avec `SOULAMA Grace Hope`, parallélisation des tâches, préavis 36 h, réserve de 20 % par semaine. | Chef de projet | **Ouvert (action immédiate)** |
| **R6** | Indisponibilité de l'API LLM, quota dépassé ou coupures réseau/électricité (latence > 10 s) | Infrastructure | 2 | 2 | **4** | **Réduire :** push quotidien sur GitHub, **mode dégradé local sans LLM** (moteur hybride BM25 + embeddings 100 % local affichant directement les top-5 articles officiels). | Resp. intégration | **Planifié** |
| **R7** | Le modèle hybride ne dépasse pas BM25 de +10 points sur le sous-ensemble `aveugle` | Technique | 2 | 2 | **4** | **Accepter / Réduire :** tester plusieurs embeddings et pondérations sur `Validation` (*timebox 1,5 jour*) ; si l'écart reste < 10 pts, analyser et documenter les causes. | Resp. modélisation | **Surveillance** |

---

## 7. Dépôt Git, architecture et règles de travail

### 7.1 Dépôt public et séparation des espaces

- **Adresse du dépôt public :** `https://github.com/ao627515/Projet_Integrateur_Equipe7` (tous les contributeurs disposent des droits collaborateurs).
- **Séparation propre :** le dépôt public ne contient que le code, les données structurées publiques et la documentation propre ; les notes privées et documents contenant des coordonnées personnelles restent strictement en local et ignorés par Git.
- **Critères d'initialisation :** arborescence standardisée, `README.md` et `.gitignore` (`uv`, `.env`, `scratch/`, fichiers volumineux) poussés, tableau Kanban actif sur GitHub Projects, et **au moins une branche + Pull Request relue par chacun des 3 contributeurs**.

### 7.2 Structure du dépôt

```text
.
├── README.md                 # Présentation, installation (uv sync), liens consignes et protocole
├── pyproject.toml            # Dépendances Python et métadonnées (avec uv.lock)
├── .gitignore                # Exclusion .venv/, .uv/, __pycache__/, .env, scratch/, données brutes/modèles lourds
├── .env.example              # Modèle de configuration API (clé LLM jamais commitée)
├── data/
│   ├── raw/                  # Données brutes officielles (2 PDF officiels, 127-128 p.) - jamais modifiées
│   ├── overrides_articles.json # Correctifs visuels persistants vérifiés sur pages PDF
│   └── processed/            # code_travail_2026_articles_verifies.json/.csv, jeu_evaluation_270.json, revue_juriste_270.csv, validation.json (189), test.json (81)
├── scripts/                  # Scripts CLI déterministes : extract_code_pdf_ocr.py, qa_and_split_dataset.py
├── notebooks/                # Notebooks numérotés (01_exploration.ipynb, 02_modele_reference.ipynb) - 1 auteur/notebook
├── src/                      # Code Python réutilisable (.py) : common/, ingestion/, retrieval/, generation/, evaluation/, app/
├── models/                   # Configurations / index locaux légers (hors binaires lourds)
├── reports/                  # Figures, graphiques et tableaux d'évaluation
├── docs/                     # plan_projet.md, plan_projet_synthese.md, protocole_evaluation.md, consignes_etiquetage.md, architecture_pipeline.md, journal_de_bord.md, comptes_rendus/
└── tests/                    # Tests automatisés (intégrité 1..441, métriques, citations)
```

### 7.3 Règles Git et documents de suivi (`docs/`)

1. **Jamais de travail direct sur `main` :** chaque tâche du Kanban donne lieu à une branche dédiée (`git switch -c <type>/<tache>`) fusionnée via une **Pull Request relue par au moins un autre contributeur**.
2. **Synchronisation et petits commits :** exécuter `git pull` avant de travailler ; commits fréquents avec message clair (`feat(...)`, `fix(...)`, `docs(...)`, `test(...)`, `chore(...)`). **Aucun code échangé par WhatsApp.**
3. **Hygiène notebooks et confidentialité :** un notebook correspond à un auteur ; effacer les sorties avant de commiter et déplacer le code réutilisable dans `src/`. Ne jamais commiter de clés API, fichiers volumineux ni données personnelles sur le dépôt public.
4. **Suivi léger dans `docs/` :** `docs/journal_de_bord.md` (à chaque session de travail), `docs/comptes_rendus/` (à chaque réunion) et `README.md` (mis à jour à chaque étape majeure).
