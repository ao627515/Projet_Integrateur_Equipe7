"""Configuration typée du contrôle qualité et du découpage Validation / Test."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_EXPECTED_FULL_STRATA: dict[str, tuple[int, int, int]] = {
    "dans_le_champ__sans_renvoi": (170, 119, 51),
    "dans_le_champ__renvoi": (30, 21, 9),
    "hors_champ": (50, 35, 15),
    "doute": (20, 14, 6),
}

DEFAULT_EXPECTED_ORIGINE_COUNTS: dict[str, int] = {
    "aveugle": 206,
    "equipe": 64,
}

REQUIRED_ITEM_KEYS: frozenset[str] = frozenset(
    {
        "id", "question", "origine", "statut_champ", "renvoi_externe", "strate",
        "persona", "registre", "forme", "type_question", "famille_id", "difficulte",
        "comportement_attendu", "theme_titre", "source_pdf", "pages_pdf",
        "article_principal", "articles_complementaires", "roles_articles_complementaires",
        "nombres_cles", "points_cles", "variantes_acceptables", "conditions_exceptions",
        "erreurs_frequentes", "reponse_reference", "statut_relecture_juriste",
    }
)


@dataclass(frozen=True)
class QAConfig:
    """Paramètres d'audit qualité, quotas, seuils et split 70/30."""

    input_path: Path = Path("data/processed/jeu_evaluation_270.json")
    corpus_path: Path = Path("data/processed/code_travail_2026_articles_verifies.json")
    out_dir: Path = Path("data/processed")
    report_path: Path = Path("scratch/rapport_qa.md")
    annotator_b_path: Path | None = None
    export_jurist_csv: Path | None = None

    mode: str = "pilot"  # "pilot" | "full"
    device: str = "auto"  # "auto" | "cuda" | "cpu"
    workers: int = 4
    max_workers: int = 8
    run_bm25: bool = False
    split: bool = False
    dry_run_split: bool = False

    total_dataset_target: int = 270
    expected_full_strata: dict[str, tuple[int, int, int]] = field(
        default_factory=lambda: dict(DEFAULT_EXPECTED_FULL_STRATA)
    )
    expected_origine_counts: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_EXPECTED_ORIGINE_COUNTS)
    )
    min_multi_articles: int = 76
    min_aveugle_ratio: float = 0.75
    max_forme_ratio: float = 0.25
    max_ri_articles: int = 5

    min_token_len: int = 3
    leakage_ngram_n: int = 3
    max_overlap_pop_courant: float = 0.30
    max_overlap_soutenu: float = 0.40
    dup_sim_limit_other: float = 0.75
    dup_sim_limit_same_famille: float = 0.85
    bm25_top_k: int = 5

    test_ratio: float = 0.30
    random_state: int = 42
