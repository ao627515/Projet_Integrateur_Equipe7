#!/usr/bin/env python3
"""Point d'entrée CLI d'extraction locale PDF + OCR pour le Code du travail 2026."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.config import ExtractionConfig
from src.ingestion.ocr_engine import available_extractors
from src.ingestion.pipeline import IngestionPipeline


def build_parser() -> argparse.ArgumentParser:
    defaults = ExtractionConfig()
    parser = argparse.ArgumentParser(
        description="Extraction locale PDF + OCR (CUDA/CPU) et comparaison des sources officielles du Code du travail 2026"
    )
    parser.add_argument("--pdf-adobe", type=Path, default=defaults.pdf_adobe)
    parser.add_argument("--pdf-scan", type=Path, default=defaults.pdf_scan)
    parser.add_argument("--scratch-dir", type=Path, default=defaults.scratch_dir)
    parser.add_argument("--out-dir", type=Path, default=defaults.out_dir)
    parser.add_argument("--overrides", type=Path, default=defaults.overrides_path, help="Patchs vérifiés sur image PNG")
    parser.add_argument("--run-adobe-ocr", action="store_true", help="Appliquer l'OCR local sur les images du PDF JO")
    parser.add_argument("--run-scan-ocr", action="store_true", help="Appliquer l'OCR local sur le PDF scanné pur")
    parser.add_argument(
        "--ocr-engine",
        choices=available_extractors(),
        default=defaults.ocr_engine,
        help="Moteur d'extraction OCR enregistré",
    )
    parser.add_argument("--dpi", type=int, default=defaults.dpi, help="Résolution OCR en DPI (invalide le cache si modifié)")
    parser.add_argument("--max-ocr-pages", type=int, default=None, help="Limiter le nb de pages OCR (test)")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default=defaults.device)
    parser.add_argument("--workers", type=int, default=defaults.workers, help="Nb max workers CPU (borné)")
    parser.add_argument("--render-pages", type=str, default="", help="Pages à exporter en PNG, ex: 1,2,35,127")
    parser.add_argument("--render-source", choices=["adobe", "scan"], default=defaults.render_source)
    parser.add_argument("--render-only", action="store_true", help="Rendre les PNG sans modifier le corpus ni les exports")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = ExtractionConfig(
        pdf_adobe=args.pdf_adobe,
        pdf_scan=args.pdf_scan,
        scratch_dir=args.scratch_dir,
        out_dir=args.out_dir,
        overrides_path=args.overrides,
        run_adobe_ocr=args.run_adobe_ocr,
        run_scan_ocr=args.run_scan_ocr,
        ocr_engine=args.ocr_engine,
        device=args.device,
        dpi=args.dpi,
        max_ocr_pages=args.max_ocr_pages,
        workers=args.workers,
        render_pages=args.render_pages,
        render_source=args.render_source,
        render_only=args.render_only,
        force=args.force,
    )
    return IngestionPipeline(config).run()


if __name__ == "__main__":
    sys.exit(main())
