"""Gestion du cache d'extraction par page (.jsonl + .meta.json avec SHA-256/DPI/profil)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.common.io import atomic_write_text, load_jsonl, save_jsonl_atomic, sha256_file


class PageCache:
    """Cache incrémental atomique invalidé automatiquement si le PDF, le DPI ou le profil OCR change."""

    def __init__(self, jsonl_path: Path, pdf_path: Path, dpi: int, ocr_profile: str) -> None:
        self.jsonl_path = jsonl_path
        self.meta_path = jsonl_path.with_suffix(".meta.json")
        self.pdf_path = pdf_path
        self.dpi = dpi
        self.ocr_profile = ocr_profile
        self.pdf_sha = sha256_file(pdf_path)

    def load_valid_pages(self, force: bool = False) -> dict[int, dict[str, Any]]:
        """Retourne les pages déjà extraites sans erreur si le cache correspond au PDF/DPI/profil."""
        if force or not self.jsonl_path.exists() or not self.meta_path.exists():
            return {}
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        if (
            meta.get("pdf_sha256") != self.pdf_sha
            or meta.get("dpi") != self.dpi
            or meta.get("ocr_profile") != self.ocr_profile
        ):
            print(
                f"[CACHE-INVALID] PDF/DPI/modèle OCR modifié (cache dpi={meta.get('dpi')}, "
                f"profile={meta.get('ocr_profile')} vs {self.ocr_profile}) -> recalcul OCR pour {self.pdf_path.name}",
                flush=True,
            )
            return {}
        return {r["page"]: r for r in load_jsonl(self.jsonl_path) if not r.get("error")}

    def write_meta(self) -> None:
        atomic_write_text(
            self.meta_path,
            json.dumps(
                {
                    "pdf_name": self.pdf_path.name,
                    "pdf_sha256": self.pdf_sha,
                    "dpi": self.dpi,
                    "ocr_profile": self.ocr_profile,
                },
                indent=2,
            ),
        )

    def save_pages(self, results: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
        ordered = [results[k] for k in sorted(results)]
        save_jsonl_atomic(self.jsonl_path, ordered)
        return ordered
