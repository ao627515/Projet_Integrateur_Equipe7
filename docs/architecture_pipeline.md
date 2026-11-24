# Architecture modulaire : Ingestion OCR et Contrôle Qualité / Split

Ce document présente les choix techniques retenus pour les deux pipelines de préparation des données de la **loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso** (441 articles, promulguée par décret n° 2026-0613/PF du 25 mai 2026, publiée au Journal Officiel Spécial N°23 du 29 mai 2026) :
1. l'extraction PDF et **OCR** (reconnaissance optique de caractères) locale (`src/ingestion/`, interface en ligne de commande `scripts/extract_code_pdf_ocr.py`) ;
2. le contrôle qualité et le découpage `Validation` / `Test` (`src/evaluation/qa/`, interface en ligne de commande `scripts/qa_and_split_dataset.py`).

---

## 1. Choix du moteur OCR : pourquoi `RapidOCR` (`latin_PP-OCRv5_rec_mobile`)

Nous avons retenu **`RapidOCR`** (`rapidocr>=3.10.0`, exécuté sur **ONNX Runtime**, un moteur d'inférence léger multiplateforme) configuré avec `LangRec.LATIN` et `OCRVersion.PPOCRV5` (`latin_PP-OCRv5_rec_mobile.onnx`, ~7,5 Mo) pour quatre raisons techniques concrètes :

1. **Zéro dépendance système externe :** s'installe directement via `uv sync` sur Windows, Linux et macOS sans installer manuellement de binaire OS (`tesseract.exe`, `paddlepaddle` ou packs de langues).
2. **Qualité sur le français juridique scanné :** le modèle de reconnaissance latin (`PP-OCRv5`) gère nativement les espaces inter-mots (y compris sur les en-têtes en majuscules grasses `TITRE` / `CHAPITRE`) et les diacritiques français (`é, è, ê, à, ç, œ`), contrairement au modèle chinois/anglais par défaut (`ch_PP-OCRv4`) qui collait les majuscules.
3. **Portabilité CPU par défaut et accélération GPU CUDA optionnelle :** le même code s'exécute en parallèle sur processeur standard (`ProcessPoolExecutor` borné) et accélère automatiquement via **CUDA** (calcul sur carte graphique NVIDIA, `CUDAExecutionProvider`, `~2 min 20` pour 255 pages à 200 DPI) sur un poste équipé.
4. **Reproductibilité et souveraineté :** traitement 100 % local et déterministe, sans envoi de documents ni coût ou latence réseau.

---

## 2. Alternatives envisageables et contreparties acceptées

| Alternative | Contreparties principales | Quand l'envisager |
| :--- | :--- | :--- |
| **Tesseract OCR (`pytesseract` + `fra`)** | Exige l'installation d'un binaire système externe et des données `fra.traineddata` ; pas d'accélération GPU CUDA ; plus sensible aux scans légèrement inclinés ou bruités. | Poste serveur Linux déjà muni de `tesseract-ocr` système où l'on veut une empreinte Python minimale. |
| **PaddleOCR natif** | Impose le framework `paddlepaddle` complet (installation plus lourde et parfois délicate sous Windows / Python récent). Note : `RapidOCR` exécute déjà les modèles `PP-OCR` convertis en ONNX. | Besoin d'accéder à des modèles expérimentaux Paddle non encore convertis au format ONNX. |
| **DocTR / EasyOCR / Surya** | Exigent **PyTorch** (+2 Go avec support CUDA), consomment davantage de RAM/VRAM et sont nettement plus lents sur des postes CPU sans GPU. | Mise en page multi-colonnes très complexe ou tableaux imbriqués nécessitant un modèle vision-document complet. |
| **OCR Cloud / Modèles Vision distants** | Coût par page, dépendance réseau, limites de débit/taille de fichiers et risque de reformulation involontaire des chiffres ou numéros d'articles. | Relecture ponctuelle d'une poignée de pages isolées très dégradées (gérée ici via `--render-pages` + `data/overrides_articles.json`). |

---

## 3. Architecture découplée (principes SOLID) et remplacement d'une brique

Chaque étape du pipeline est isolée derrière un contrat simple (`Protocol`) et assemblée par **injection de dépendances** (transmission des composants en paramètre plutôt que création en dur, via `IngestionPipeline` et `DatasetQAPipeline`), avec une base partagée dans `src/common/` (`io.py`, `text.py`). Remplacer une brique n'affecte pas l'intégrité des autres étapes.

### A. Changer ou ajouter un moteur OCR sans toucher au parser, au comparateur ni aux exports

1. **Implémenter le contrat `PageExtractor`** défini dans `src/ingestion/ocr_engine.py` :
   ```python
   from pathlib import Path
   from typing import Any
   from src.ingestion.config import ExtractionConfig
   from src.ingestion.ocr_engine import register_extractor

   class CustomOcrExtractor:
       profile_tag = "custom_ocr_v1"  # Invalide automatiquement le cache si modifié

       def __init__(self, config: ExtractionConfig) -> None:
           self.config = config

       def extract(self, pdf_path: Path, cache_path: Path) -> list[dict[str, Any]]:
           # Retourne une liste de dicts :
           # {"source_pdf": pdf_path.name, "page": 1, "mode": self.profile_tag, "char_count": ..., "image_count": ..., "text": "..."}
           ...

   register_extractor("custom", CustomOcrExtractor)
   ```
2. **Sélectionner le moteur sans modifier le pipeline :**
   - par CLI : `uv run python scripts/extract_code_pdf_ocr.py --run-adobe-ocr --run-scan-ocr --ocr-engine custom` ;
   - ou par injection directe en code / test : `IngestionPipeline(config, adobe_extractor=..., scan_extractor=...)`.
3. `PageCache` génère un cache distinct (`extraction_pdf_adobe_<moteur>.jsonl`) et vérifie `pdf_sha256`, `dpi` et `profile_tag` sans aucune modification de `parser.py`, `comparator.py`, `exporters.py` ou `pipeline.py`.

### B. Autres briques interchangeables
- **Parser (`src/ingestion/parser.py`) :** injectable via `IngestionPipeline(config, parser=...)` tant qu'il expose `.parse(pages) -> list[dict]`.
- **Contrôles qualité (`src/evaluation/qa/checks.py`) :** tout nouveau contrôle implémente `QualityCheck.run(items, corpus, config) -> CheckResult` et peut être passé à `DatasetQAPipeline(config, checks=[...])`.
- **Découpage (`src/evaluation/qa/splitter.py`) :** injectable via `DatasetQAPipeline(config, splitter=...)` pour changer la stratégie de stratification sans toucher aux contrôles QA ni aux exports.
