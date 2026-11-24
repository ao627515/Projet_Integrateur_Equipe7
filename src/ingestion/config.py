"""Configuration typée du pipeline d'extraction PDF et OCR local."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionConfig:
    """Paramètres d'exécution de l'extraction PDF, OCR, parsing et comparaison."""

    pdf_adobe: Path = Path("data/raw/decret_no2026-0613_code_du_travail_new.pdf")
    pdf_scan: Path = Path(
        "data/raw/LOI_2026_decret_2026_0613 pf_promulguant_loi_n°013-2026_alp_code_travail_Burkina_Faso_cp.pdf"
    )
    scratch_dir: Path = Path("scratch")
    out_dir: Path = Path("data/processed")
    overrides_path: Path = Path("data/overrides_articles.json")

    run_adobe_ocr: bool = False
    run_scan_ocr: bool = False
    ocr_engine: str = "rapidocr"      # Nom enregistré dans le registre d'extracteurs
    device: str = "auto"  # "auto" | "cuda" | "cpu"
    dpi: int = 200
    ocr_profile_tag: str = "rapidocr_latin_ppocrv5"
    png_render_dpi: int = 150
    max_ocr_pages: int | None = None
    workers: int = 4
    gpu_render_threads: int = 2
    max_inflight_gpu_pages: int = 4
    gc_every_n_pages: int = 20
    checkpoint_every_n_pages: int = 5
    ocr_retries_per_page: int = 2
    force: bool = False

    min_article_num: int = 1
    max_article_num: int = 450
    max_article_jump: int = 10
    min_article_text_len: int = 15
    diff_similarity_threshold: float = 0.90
    report_max_suspects: int = 50
    report_max_divergences: int = 80

    render_pages: str = ""
    render_source: str = "adobe"  # "adobe" | "scan"
    render_only: bool = False
