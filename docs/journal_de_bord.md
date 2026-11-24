# Journal de bord : Assistant Code du travail burkinabè

Ce journal consigne l'avancement technique, les décisions prises à l'issue des contrôles qualité et les évolutions actées par rapport au plan initial ([docs/plan_projet.md](plan_projet.md)), sans modifier ce dernier.

---

## Journal des sessions (19/11 au 24/11/2026)

| Date | Activités réalisées | Décisions et résultats vérifiés | Référents |
| :--- | :--- | :--- | :--- |
| **19/11 – 22/11** | Initialisation technique, structuration du dépôt et rédaction de la documentation de référence (`README.md`, `docs/plan_projet.md`, `docs/protocole_evaluation.md`, `docs/architecture_pipeline.md`). | Premier commit poussé sur GitHub, tableau Kanban activé, `≥ 1` Pull Request relue fusionnée par chacun des `3` contributeurs ; `.gitignore` configuré hors `.env` et `scratch/`. | OUEDRAOGO A. Aziz, COMPAORE Alexis, Tous |
| **23/11** | Extraction locale PDF + **OCR** (reconnaissance optique de caractères) via `RapidOCR` sur les deux PDF officiels (`127` et `128` pages) avec `scripts/extract_code_pdf_ocr.py`, et rédaction de `docs/consignes_etiquetage.md`. | Rejet de la couche OCR préalable bruitée (`96` articles avec `U+FFFD`) ; production de `441` articles (`1..441`) dans `data/processed/code_travail_2026_articles_verifies.{json,csv}` avec `6` premiers correctifs visuels dans `data/overrides_articles.json`. | TAPSOBA Faridatou |
| **24/11 (matin)** | Constitution, contrôle qualité et gel du découpage stratifié groupé `70/30` sur `data/processed/jeu_evaluation_270.json` (`270` questions validées, `206 aveugle` / `64 equipe`) via `scripts/qa_and_split_dataset.py`. | `0` erreur, `0` fuite lexicale, `0` PII ; `validation.json` (`189` fiches, `sha256=b6bc2935e429557e3bd0df3f8888b4bf108916b81b09d31b9cafa3ea2ca9d775`) et `test.json` (`81` fiches verrouillées, `sha256=8eb33c71a1651a2f966826550712082030298c178e51cd1d548edfea304c28f2`) gelés sans fuite de `famille_id` (`reports/rapport_qa_split.md`). | TAPSOBA Faridatou, COMPAORE Alexis |
| **24/11 (après-midi)** | Exploration complète dans `notebooks/01_exploration.ipynb` (articles, questions, croisement), audit qualité sur 6 dimensions et nettoyage correctif à la source. | Découverte de `61` articles avec anomalies post-OCR résiduelles ; correction via `src/ingestion/parser.py` (tampons marginaux, en-têtes `Section` multi-lignes, `CHAPITRE 5`) et passage de `6` à `30` entrées vérifiées sur PNG dans `data/overrides_articles.json`. Régénération (`61 -> 0` anomalie), ajout de `tests/test_corpus_quality.py` (`5/5` tests OK) et mise à jour de `reports/rapport_exploration.md`. | Tous (3 contributeurs) |

---

## Évolutions par rapport au plan initial (`docs/plan_projet.md`)

1. **Sorties conservées dans le notebook d'exploration (`notebooks/01_exploration.ipynb`) :**
   - *Plan initial :* `docs/plan_projet_synthese.md` indiquait de vider les sorties des notebooks avant commit.
   - *Décision retenue :* nous conservons les sorties et les `13` graphiques intégrés dans `notebooks/01_exploration.ipynb` afin que le diagnostic reste directement lisible sur GitHub, tout en maintenant les fichiers PNG exportés à jour dans `reports/figures/`.
2. **Avancement des risques `R1` et `R2` :**
   - **Risque `R1` (jeu d'évaluation) :** le statut *« attente juriste »* noté dans `docs/plan_projet.md` est levé (`270/270` fiches validées) ; `scripts/qa_and_split_dataset.py --mode full --split` a gelé `validation.json` (`189`) et `test.json` (`81`) avec `Erreurs=0`, `Fuites=0` et `0` fuite de `famille_id` (`reports/rapport_qa_split.md`).
   - **Risque `R2` (qualité OCR du corpus) :** l'audit exploratoire a complété le contrôle initial (`441/441` présents) en éliminant `61` défauts résiduels de découpage et de marge (`17` débuts tronqués, `23` fins sans ponctuation, `20` caractères parasites, `4` mots collés), verrouillés par `tests/test_corpus_quality.py` (`5/5` tests passés).

---

## Rétrospective de la semaine et prochaines actions

- **Ce qui a bien fonctionné :** la séparation entre données brutes immuables (`data/raw/`), cache OCR reproductible et correctifs explicites (`data/overrides_articles.json`) a permis de corriger et régénérer les `441` articles en quelques secondes sans ré-exécuter l'OCR sur les `255` pages.
- **Actions immédiates :**
  1. Implémenter la baseline lexicale **BM25** (`src/retrieval/bm25.py`) et les scripts d'évaluation (`Succès@5`, `Rappel@5`, matrice 6 cas, bootstrap apparié 95 %) en travaillant uniquement sur `data/processed/validation.json` (`189` questions).
  2. Maintenir `data/processed/test.json` (`81` questions) strictement verrouillé jusqu'à l'évaluation finale du modèle hybride.
