"""Orchestrateur du contrôle qualité et du split 70/30 (injection de dépendances)."""

from __future__ import annotations

import json
from typing import Any

from src.common.io import atomic_write_text
from src.evaluation.qa.checks import (
    DuplicateCheck,
    LexicalLeakageCheck,
    PiiCheck,
    QualityCheck,
    QuotaCheck,
    SchemaAndIntegrityCheck,
    detect_torch_cuda,
    load_corpus,
)
from src.evaluation.qa.config import QAConfig
from src.evaluation.qa.exporters import export_jurist_csv, render_qa_report
from src.evaluation.qa.metrics import compute_agreement, evaluate_bm25
from src.evaluation.qa.splitter import StratifiedGroupSplitter


class DatasetQAPipeline:
    """Enchaîne les contrôles qualité, métriques diagnostiques, export juriste et split 70/30."""

    def __init__(
        self,
        config: QAConfig,
        checks: list[QualityCheck] | None = None,
        splitter: StratifiedGroupSplitter | None = None,
    ) -> None:
        self.config = config
        self._custom_checks = checks
        self.splitter = splitter or StratifiedGroupSplitter(
            test_ratio=config.test_ratio,
            random_state=config.random_state,
        )

    def run(self) -> int:
        cfg = self.config
        use_cuda, dev_label = detect_torch_cuda(cfg.device)
        print(f"[QA-INIT] Device={dev_label} | Workers={cfg.workers} | Mode={cfg.mode}", flush=True)

        items: list[dict[str, Any]] = json.loads(cfg.input_path.read_text(encoding="utf-8"))
        corpus = load_corpus(cfg.corpus_path)

        checks: list[QualityCheck] = self._custom_checks or [
            SchemaAndIntegrityCheck(),
            PiiCheck(),
            QuotaCheck(),
            LexicalLeakageCheck(),
            DuplicateCheck(use_cuda=use_cuda),
        ]

        errors: list[str] = []
        warnings: list[str] = []
        details: dict[str, Any] = {}
        for chk in checks:
            res = chk.run(items, corpus, cfg)
            errors.extend(res.errors)
            warnings.extend(res.warnings)
            details.update(res.details)

        bm25_res = (
            evaluate_bm25(items, corpus, top_k=cfg.bm25_top_k, workers=cfg.workers, max_workers=cfg.max_workers)
            if cfg.run_bm25
            else None
        )

        agree_res = None
        if cfg.annotator_b_path and cfg.annotator_b_path.exists():
            items_b = json.loads(cfg.annotator_b_path.read_text(encoding="utf-8"))
            agree_res = compute_agreement(items, items_b)

        if cfg.export_jurist_csv:
            export_jurist_csv(items, cfg.export_jurist_csv)
            print(f"[CSV] Export juriste écrit -> {cfg.export_jurist_csv}", flush=True)

        split_summary = None
        if cfg.split or cfg.dry_run_split:
            split_summary, split_errors = self.splitter.execute(
                items,
                freeze=cfg.split,
                out_dir=cfg.out_dir,
                existing_errors=errors,
            )
            errors.extend(split_errors)

        leaks = details.get("leaks", [])
        dups = details.get("dups", [])
        quota_details = {
            "strata_counts": details.get("strata_counts", {}),
            "origine_counts": details.get("origine_counts", {}),
            "registre_counts": details.get("registre_counts", {}),
            "multi_count": details.get("multi_count", 0),
            "in_scope_count": details.get("in_scope_count", 0),
        }

        report_md = render_qa_report(
            mode=cfg.mode,
            n_items=len(items),
            dev_label=dev_label,
            quota_details=quota_details,
            leaks=leaks,
            dups=dups,
            errors=errors,
            bm25_res=bm25_res,
            agree_res=agree_res,
            split_summary=split_summary,
            random_state=cfg.random_state,
        )
        atomic_write_text(cfg.report_path, report_md)
        print(f"[QA] Rapport écrit -> {cfg.report_path} | Erreurs={len(errors)} | Fuites={len(leaks)}", flush=True)
        if bm25_res:
            print(f"[BM25] {bm25_res}", flush=True)
        if split_summary:
            print(f"[SPLIT-CHECK] {split_summary}", flush=True)
        return 1 if errors else 0
