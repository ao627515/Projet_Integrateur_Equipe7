# Assistant de consultation du Code du travail burkinabè

## Objet du produit
Nous concevons et évaluons un assistant d'aide à la consultation de la **loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso** (441 articles), à destination des gérants de PME, responsables RH, salariés et délégués du personnel :
1. **Recherche d'articles pertinents** (comparaison entre la baseline lexicale **BM25**, classement par correspondance de mots, des plongements sémantiques et une approche hybride) ;
2. **Détection et refus hors champ** par seuil de confiance ;
3. **Synthèse explicative sourcée** accompagnée de l'extrait officiel exact et d'un avertissement documentaire.

## Contributeurs
- **COMPAORE Alexis Awossonoyi** : Chef de projet et référent éthique *(suppléant Données & Qualité)*
- **TAPSOBA Faridatou** : Responsable données et qualité *(suppléante Chef de projet)*
- **OUEDRAOGO Abdoul Aziz** : Responsable modélisation et intégration *(suppléant Éthique & Déploiement)*

## Structure du dépôt 

```text
Projet_Integrateur_Equipe7/
├── README.md                 # Présentation, installation et suivi des documents
├── pyproject.toml            # Dépendances Python (uv)
├── .gitignore                # Exclusions (.venv/, .env, données brutes lourdes, modèles, secrets)
├── .env.example              # Modèle de configuration pour l'API LLM
├── data/
│   ├── raw/                  # Données brutes officielles (jamais modifiées)
│   ├── overrides_articles.json # Correctifs vérifiés sur images de pages PDF
│   └── processed/            # Corpus structuré (441 articles CSV/JSON), jeu d'évaluation et splits validation/test
├── scripts/                  # Scripts CLI : extraction OCR (extract_code_pdf_ocr.py) et QA/split (qa_and_split_dataset.py)
├── notebooks/                # Exploration , baseline BM25 , comparaisons
├── src/                      # Code Python réutilisable (ingestion, retrieval, generation, evaluation, app)
├── models/                   # Configurations / index légers
├── reports/                  # Figures, graphiques et tableaux de résultats
├── docs/                     # Plan de projet , protocole d'évaluation, journal de bord, comptes rendus
└── tests/                    # Tests automatisés (test_corpus_quality.py : intégrité 1..441, métriques, citations)
```

## Documentation clé
- [docs/protocole_evaluation.md](docs/protocole_evaluation.md) : métriques (`Succès@5`, `Rappel@5`, matrice 6 cas), découpage `Validation` / `Test`, bootstrap apparié 95 %, seuils de refus/doute et grille de fidélité LLM.
- [docs/consignes_etiquetage.md](docs/consignes_etiquetage.md) : règles d'étiquetage multi-articles, frontière `dans_le_champ` / `hors_champ` / `doute`, renvois externes, traçabilité `origine` et schéma JSON à 26 champs.
- [docs/architecture_pipeline.md](docs/architecture_pipeline.md) : choix de `RapidOCR`, alternatives/contreparties et guide d'extension modulaire (remplacement d'OCR ou d'étape sans casser le reste).
- [docs/methode_exploration_donnees.md](docs/methode_exploration_donnees.md) : grille d'exploration textuelle, contrôle qualité post-OCR et critères de conformité légale.
- [notebooks/01_exploration.ipynb](notebooks/01_exploration.ipynb) et [reports/rapport_exploration.md](reports/rapport_exploration.md) : exploration exécutable des 441 articles et 270 questions, audit avant/après nettoyage et conséquences pour le RAG.

## Sources et licences des données

- **Corpus juridique :** *Loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso* (**441 articles**), promulguée par **décret n° 2026-0613/PF du 25 mai 2026** et publiée au **Journal Officiel Spécial N°23 du 29 mai 2026** (Assemblée législative du Peuple / Présidence du Faso). Texte législatif officiel public burkinabè, librement réutilisable.
- **Fichiers bruts locaux (`data/raw/`, conservés intacts) :**
  - `LOI_2026_decret_2026_0613 pf_promulguant_loi_n°013-2026_alp_code_travail_Burkina_Faso_cp.pdf` (127 pages, scan officiel du Journal Officiel) ;
  - `decret_no2026-0613_code_du_travail_new.pdf` (128 pages, copie scannée avec couche OCR préalable auditée et corrigée via `src/ingestion/parser.py` et 30 correctifs visuels dans `data/overrides_articles.json`).
- **Jeu d'évaluation (`data/processed/jeu_evaluation_270.json`) :** 270 questions originales (206 formulées à l'aveugle de manière anonyme et 64 en interne) relues juridiquement sans conservation de données personnelles.
- **Outils d'extraction, d'analyse et licences :** `RapidOCR` (licence Apache-2.0), `PyMuPDF`, `spaCy`, `nltk` (`SnowballStemmer`), `scikit-learn`, `matplotlib` et `seaborn` ; aucune donnée personnelle ni clé API stockée sur le dépôt.


## Installation (environnement Python)

```bash
# Par défaut (CPU : Windows, Linux, macOS) :
uv sync

# Optionnel (PC équipé d'un GPU NVIDIA CUDA) :
uv sync --group gpu --config-file uv.gpu.toml

cp .env.example .env   # puis renseigner LLM_API_KEY en local
```

## Utilisation des scripts (`scripts/`)

Toutes les commandes ci-dessous s'exécutent depuis le dossier `Projet_Integrateur_Equipe7/` (auto-détection GPU CUDA avec repli automatique sur CPU).

### 1. Extraction PDF & OCR local (`scripts/extract_code_pdf_ocr.py`)

Extrait les 441 articles depuis les deux PDF officiels placés dans `data/raw/`, applique les correctifs vérifiés (`data/overrides_articles.json`) et exporte `data/processed/code_travail_2026_articles_verifies.{json,csv}` :

```bash
# Extraction OCR complète des deux PDF (auto GPU CUDA ou CPU parallèle)
uv run python scripts/extract_code_pdf_ocr.py --run-adobe-ocr --run-scan-ocr

# Forcer l'exécution CPU (ou --force pour recalculer le cache OCR)
uv run python scripts/extract_code_pdf_ocr.py --run-adobe-ocr --run-scan-ocr --device cpu

# Exporter des pages isolées en PNG pour contrôle visuel (sans écraser le corpus)
uv run python scripts/extract_code_pdf_ocr.py --render-pages 5,55,127 --render-source adobe --render-only
```

### 2. Contrôle qualité & split 70/30 (`scripts/qa_and_split_dataset.py`)

Vérifie le schéma, les quotas (`270` questions, `aveugle` vs `equipe`, multi-articles), les fuites lexicales, les doublons TF-IDF, les PII, le benchmark BM25, l'accord inter-annotateurs et le découpage stratifié groupé par `famille_id` (`random_state = 42`) :

```bash
# Audit complet + export CSV juriste + simulation du split 70/30 (sans gel)
uv run python scripts/qa_and_split_dataset.py \
  --input data/processed/jeu_evaluation_270.json \
  --corpus data/processed/code_travail_2026_articles_verifies.json \
  --mode full --run-bm25 --dry-run-split \
  --export-jurist-csv data/processed/revue_juriste_270.csv \
  --report reports/rapport_qa.md

# Gel définitif de validation.json (189) et test.json (81)
uv run python scripts/qa_and_split_dataset.py \
  --input data/processed/jeu_evaluation_270.json \
  --corpus data/processed/code_travail_2026_articles_verifies.json \
  --mode full --split --out-dir data/processed \
  --report reports/rapport_qa_split.md
```

## Règles Git
- Aucun travail direct sur `main` : toute tâche passe par une branche dédiée et une **Pull Request relue** par au moins un autre membre.
- Aucune donnée personnelle ni clé d'API ne doit être commitée sur ce dépôt.
- `data/raw/` n'est jamais modifié manuellement : toute préparation passe par un script dans `src/ingestion/` écrivant vers `data/processed/`.
