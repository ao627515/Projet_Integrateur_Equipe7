#!/usr/bin/env python3
"""Point d'entrée CLI du contrôle qualité déterministe et du split stratifié groupé 70/30."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.qa.config import QAConfig
from src.evaluation.qa.pipeline import DatasetQAPipeline


def build_parser() -> argparse.ArgumentParser:
    defaults = QAConfig()
    parser = argparse.ArgumentParser(
        description="Contrôle qualité déterministe du jeu d'évaluation et split stratifié groupé 70/30"
    )
    parser.add_argument("--input", type=Path, required=True, help="Jeu de données JSON à auditer")
    parser.add_argument("--corpus", type=Path, required=True, help="Corpus extrait (jsonl ou json)")
    parser.add_argument("--mode", choices=["pilot", "full"], default=defaults.mode)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default=defaults.device)
    parser.add_argument("--workers", type=int, default=defaults.workers, help=f"Nb threads borné (max {defaults.max_workers})")
    parser.add_argument("--annotator-b", type=Path, default=None, help="Annotations indépendantes (annotateur B) pour calcul d'accord")
    parser.add_argument("--run-bm25", action="store_true")
    parser.add_argument("--export-jurist-csv", type=Path, default=None)
    parser.add_argument("--split", action="store_true", help="Exécuter le split 70/30 (exige 100 %% validé juriste)")
    parser.add_argument("--dry-run-split", action="store_true", help="Simuler le split sans exiger validation juriste")
    parser.add_argument("--out-dir", type=Path, default=defaults.out_dir)
    parser.add_argument("--report", type=Path, default=defaults.report_path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = QAConfig(
        input_path=args.input,
        corpus_path=args.corpus,
        out_dir=args.out_dir,
        report_path=args.report,
        annotator_b_path=args.annotator_b,
        export_jurist_csv=args.export_jurist_csv,
        mode=args.mode,
        device=args.device,
        workers=args.workers,
        run_bm25=args.run_bm25,
        split=args.split,
        dry_run_split=args.dry_run_split,
    )
    return DatasetQAPipeline(config).run()


if __name__ == "__main__":
    sys.exit(main())
