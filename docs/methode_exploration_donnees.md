# Spécification technique : Exploration, audit qualité et conformité des données

**Corpus évalué :** Loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso (**441 articles**, promulguée par décret n° 2026-0613/PF du **25 mai 2026**, publiée au Journal Officiel Spécial N°23 du **29 mai 2026**).  
**Périmètre :** ce document fixe la méthode d'exploration textuelle, de contrôle qualité post-OCR, de diagnostic pour la recherche d'information et de conformité légale appliquée à nos données avant toute modélisation.

---

## 1. Principes méthodologiques (cycle NLP et recherche d'information)

Pour notre assistant **RAG** (génération augmentée par recherche documentaire), cette phase sépare strictement trois activités :
1. **Exploration textuelle (EDA) :** observer ce que contiennent les données (échantillons réels, longueurs, vocabulaire, couverture des thèmes, renvois juridiques) sans a priori.
2. **Évaluation de la qualité textuelle :** traquer les défauts cachés après extraction **OCR** (reconnaissance optique de caractères), les troncatures, le bruit de marge, les doublons ou les biais lexicaux.
3. **Tests exploratoires de prétraitement :** mesurer l'effet de choix techniques simples (mots vides français, accents, nombres en lettres) sur la représentation du texte avant d'indexer ou d'entraîner un modèle.

Les étapes suivantes (calcul de paramètres sur le jeu d'entraînement ou de validation, entraînement **BM25**, modèles vectoriels, calibration des seuils de refus et déploiement) restent hors de cette phase et ne doivent jamais toucher au jeu `Test`.

---

## 2. Livrables techniques retenus pour notre produit

| Livrable | Rôle dans le dépôt | Contenu attendu |
| :--- | :--- | :--- |
| **Données brutes intactes (`data/raw/`)** | Source officielle immuable | Les deux PDF officiels (`127` et `128` pages), jamais modifiés à la main, documentés et cités dans `README.md` (producteur, dates officielles, statut public). |
| **Pipeline déterministe (`src/` → `data/processed/`)** | Reproductibilité | `src/ingestion/` (`scripts/extract_code_pdf_ocr.py`) avec `data/overrides_articles.json` et `tests/test_corpus_quality.py` ; `src/evaluation/qa/` (`scripts/qa_and_split_dataset.py`). |
| **Notebook exploratoire (`notebooks/01_exploration.ipynb`)** | Diagnostic exécutable | Exploration en 3 parties (corpus des 441 articles, jeu d'évaluation de 270 questions, croisement articles × questions : `spaCy`, `SnowballStemmer`, contrôle post-OCR, TF-IDF et projection `t-SNE`) + export des graphiques dans `reports/figures/`. |
| **Journal de nettoyage** | Traçabilité des décisions | Tableau `Étape | Défaut constaté | Décision | Éléments concernés` justifiant chaque correction ou conservation d'article atypique. |
| **Rapport de synthèse (`reports/rapport_exploration.md`, 5 pages max)** | Décision données vers méthode | Bilan structuré (rappel, fiche de données, dictionnaire, 6 dimensions qualité, journal avant/après, 4 figures principales commentées, conséquences pour le RAG, conformité). |

---

## 3. Adaptation aux deux jeux de données du projet

### 3.1 Données couvertes
1. **Corpus juridique (`data/processed/code_travail_2026_articles_verifies.{json,csv}`) :** 441 articles × 7 colonnes (`numero`, `titre`, `chapitre`, `section`, `texte`, `source_pdf`, `pages_pdf`).
2. **Jeu d'évaluation (`data/processed/jeu_evaluation_270.json`) :** jeu validé de **270 questions** × 26 champs (`200` dans le champ, `50` hors champ, `20` en zone de doute ; construit au-dessus du plancher minimal initial d'environ `180` questions), prêt pour le découpage unique `70 % Validation (189) / 30 % Test (81)` groupé par `famille_id`.

### 3.2 Grille d'analyse spécifique au NLP juridique
- **Longueur et valeurs atypiques (règle IQR) :** mesurer la moyenne, la médiane, les quartiles et les articles longs au-delà de $Q_3 + 1{,}5 \times \text{IQR}$ pour dimensionner le découpage documentaire (*chunking*) sans jamais supprimer d'article authentique.
- **Écart de vocabulaire (`spaCy` français et `SnowballStemmer`) :** comparer les mots et bigrammes fréquents du Code avec ceux des questions `aveugle` après retrait des **507 mots vides français `spaCy`** (`spacy.lang.fr.stop_words.STOP_WORDS`), et mesurer l'effet de la suppression des accents et du *stemming* français sur le recouvrement lexical.
- **Qualité post-OCR :** vérifier la continuité `1..441`, `0` caractère `U+FFFD`, l'absence de caractères parasites, de mots collés, de débuts tronqués (minuscule initiale), de fins sans ponctuation (paraphes ou tampons marginaux), et l'absence de quasi-doublons par similarité **TF-IDF cosinus** (`scikit-learn`).
- **Phénomènes juridiques :** quantifier les nombres écrits en toutes lettres face aux chiffres, les renvois internes (`article X`, `alinéa`) et les renvois externes (`convention collective`, `décret`, `arrêté`, `voie réglementaire`).

---

## 4. Cadre légal et liste de contrôle de conformité

Le texte de loi est un document officiel public burkinabè librement réutilisable (y compris pour un usage commercial). Pour la protection des données personnelles, le cadre burkinabè inclut la Convention de Malabo, la loi n° 001-2021/AN, la loi révisée adoptée le **3 août 2026** et la loi organique **n° 038-2026/ALP** créant l'**ARCOD** (en remplacement de la CIL et du CSC).

| Critère de conformité | Exigence produit |
| :--- | :--- |
| **Licence et sources** | Statut public de la loi n° 013-2026/ALP et licences des bibliothèques (`RapidOCR` Apache-2.0) documentés et cités dans `README.md` et le rapport. |
| **Minimisation et consentement** | 0 donnée personnelle dans le corpus et les 270 questions ; accord écrit avec la juriste ; consentement préalable et anonymat pour les ≥ 10 testeurs externes. |
| **Sécurité et transferts** | `.env`, `scratch/` et dossiers privés exclus par `.gitignore` ; avertissement anti-saisie de données personnelles avant appel API distante ; mode dégradé 100 % local sans LLM. |
| **Durée de conservation** | Zéro stockage des requêtes en production ; aucune donnée nominative conservée après synthèse anonyme de l'essai utilisateurs. |

---

## 5. Critères d'acceptation technique de cette phase

1. **Documentation :** fiche de données à 6 rubriques (*Provenance, Composition, Collecte, Prétraitement, Droits, Limites*) et dictionnaire complet pour les deux jeux.
2. **Qualité et nettoyage :** défauts diagnostiqués selon les 6 dimensions (*Complétude, Validité, Exactitude, Cohérence, Unicité, Actualité*), `data/raw/` intact, journal complet.
3. **Exploration et diagnostic :** 4 figures principales commentées dans le rapport (issues des 13 graphiques du notebook) éclairant longueur, couverture des 10 Titres, multi-articles et écart lexical / renvois externes.
4. **Retour données vers méthode :** décisions concrètes tirées des constats réels (y compris correctifs OCR à appliquer si des anomalies résiduelles apparaissent).
5. **Reproductibilité et concision :** notebook exécuté sans erreur de bout en bout, scripts déterministes et rapport synthétique tenant en 5 pages maximum.
