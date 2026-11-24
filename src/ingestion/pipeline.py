"""Orchestrateur du pipeline d'ingestion PDF/OCR (injection de dépendances)."""

from __future__ import annotations

import json
from typing import Any

from src.common.io import atomic_write_text, process_lock, save_jsonl_atomic
from src.ingestion.comparator import (
    apply_manual_overrides,
    compare_extractions,
    detect_anomalies,
    merge_extractions,
)
from src.ingestion.config import ExtractionConfig
from src.ingestion.exporters import (
    build_structure_summary,
    export_structured,
    render_comparison_report,
    render_pages_as_png,
)
from src.ingestion.ocr_engine import PageExtractor, create_extractor
from src.ingestion.parser import CodeTravailParser


class IngestionPipeline:
    """Orchestre extraction, parsing, fusion, overrides et exports structurés."""

    def __init__(
        self,
        config: ExtractionConfig,
        adobe_extractor: PageExtractor | None = None,
        scan_extractor: PageExtractor | None = None,
        parser: CodeTravailParser | None = None,
    ) -> None:
        self.config = config
        self.adobe_extractor: PageExtractor = adobe_extractor or create_extractor(
            config.ocr_engine if config.run_adobe_ocr else "embedded", config
        )
        self.scan_extractor: PageExtractor = scan_extractor or create_extractor(config.ocr_engine, config)
        self.parser = parser or CodeTravailParser(
            min_num=config.min_article_num,
            max_num=config.max_article_num,
            max_jump=config.max_article_jump,
        )

    def run(self) -> int:
        cfg = self.config
        scratch = cfg.scratch_dir
        scratch.mkdir(parents=True, exist_ok=True)

        # Garde-fou anti-écrasement : rendu PNG seul si le corpus existe déjà
        if cfg.render_pages and (
            cfg.render_only
            or (not cfg.run_adobe_ocr and not cfg.run_scan_ocr and (scratch / "corpus_verifie.jsonl").exists())
        ):
            pnums = [int(x.strip()) for x in cfg.render_pages.split(",") if x.strip().isdigit()]
            src = cfg.pdf_adobe if cfg.render_source == "adobe" else cfg.pdf_scan
            saved = render_pages_as_png(src, pnums, scratch / "page_images", dpi=cfg.png_render_dpi)
            print(
                f"[RENDER-ONLY] {len(saved)} page(s) rendue(s) dans {scratch / 'page_images'} "
                "(corpus existant préservé sans modification)",
                flush=True,
            )
            return 0

        try:
            lock_ctx = process_lock(scratch / ".extract_code_pdf_ocr.lock")
            lock_ctx.__enter__()
        except RuntimeError as exc:
            print(f"[LOCK-BLOCKED] {exc}", flush=True)
            return 2

        try:
            adobe_cache = (
                scratch / f"extraction_pdf_adobe_{cfg.ocr_engine}.jsonl"
                if cfg.run_adobe_ocr
                else scratch / "extraction_pdf_adobe.jsonl"
            )
            pages_adobe = self.adobe_extractor.extract(cfg.pdf_adobe, adobe_cache)
            arts_adobe = self.parser.parse(pages_adobe)
            anom_adobe = detect_anomalies(arts_adobe, min_text_len=cfg.min_article_text_len)

            divergences: list[dict[str, Any]] = []
            anom_scan: dict[str, Any] | None = None
            pages_scan: list[dict[str, Any]] = []
            arts_merged = list(arts_adobe)

            if cfg.run_scan_ocr:
                pages_scan = self.scan_extractor.extract(cfg.pdf_scan, scratch / "extraction_pdf_scan.jsonl")
                arts_scan = self.parser.parse(pages_scan)
                anom_scan = detect_anomalies(arts_scan, min_text_len=cfg.min_article_text_len)
                divergences = compare_extractions(
                    arts_adobe, arts_scan, similarity_threshold=cfg.diff_similarity_threshold
                )
                arts_merged = merge_extractions(arts_adobe, arts_scan, anom_adobe)

            n_overrides = apply_manual_overrides(arts_merged, cfg.overrides_path)
            if n_overrides:
                print(
                    f"[OVERRIDES] {n_overrides} correction(s) vérifiée(s) sur PNG appliquée(s) depuis {cfg.overrides_path}",
                    flush=True,
                )

            save_jsonl_atomic(scratch / "corpus_verifie.jsonl", arts_merged)
            struct = build_structure_summary(arts_merged)
            atomic_write_text(scratch / "structure_code.json", json.dumps(struct, ensure_ascii=False, indent=2))
            export_structured(
                arts_merged,
                cfg.out_dir / "code_travail_2026_articles_verifies.json",
                cfg.out_dir / "code_travail_2026_articles_verifies.csv",
            )

            if cfg.render_pages:
                pnums = [int(x.strip()) for x in cfg.render_pages.split(",") if x.strip().isdigit()]
                src = cfg.pdf_adobe if cfg.render_source == "adobe" else cfg.pdf_scan
                saved = render_pages_as_png(src, pnums, scratch / "page_images", dpi=cfg.png_render_dpi)
                print(f"[PNG] {len(saved)} pages rendues dans {scratch / 'page_images'}", flush=True)

            report_md = render_comparison_report(
                pdf_adobe_name=cfg.pdf_adobe.name,
                nb_pages_adobe=len(pages_adobe),
                anom_adobe=anom_adobe,
                n_overrides=n_overrides,
                pdf_scan_name=cfg.pdf_scan.name if cfg.run_scan_ocr else None,
                nb_pages_scan=len(pages_scan),
                anom_scan=anom_scan,
                divergences=divergences,
                max_suspects=cfg.report_max_suspects,
                max_divergences=cfg.report_max_divergences,
            )
            atomic_write_text(scratch / "rapport_comparaison_pdfs.md", report_md)
            print(f"[OK] Rapport écrit -> {scratch / 'rapport_comparaison_pdfs.md'}", flush=True)
            print(
                f"[SYNTHESE] Corpus final: {len(arts_merged)} art. (overrides={n_overrides}) | "
                f"JO brut: {anom_adobe['total_articles']} art., manquants={anom_adobe['missing_numeros']}",
                flush=True,
            )
            if anom_scan is not None:
                print(
                    f"[SYNTHESE] Scan: {anom_scan['total_articles']} art., "
                    f"manquants={len(anom_scan['missing_numeros'])}, "
                    f"divergences={len(divergences)}",
                    flush=True,
                )
            return 0
        finally:
            lock_ctx.__exit__(None, None, None)
