"""Exports structurés (JSON, CSV atomique, structure, PNG isolés et rapport Markdown)."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import pymupdf as fitz

from src.common.io import atomic_write_text


def export_structured(articles: list[dict[str, Any]], out_json: Path, out_csv: Path) -> None:
    """Écrit de manière atomique le corpus structuré en JSON et en CSV UTF-8 BOM."""
    atomic_write_text(out_json, json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["numero", "titre", "chapitre", "section", "source_pdf", "pages_pdf", "texte"]
    fd, tmp_name = tempfile.mkstemp(prefix=out_csv.name + ".", suffix=".tmp", dir=str(out_csv.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for a in articles:
                row = dict(a)
                row["pages_pdf"] = "; ".join(a["pages_pdf"])
                writer.writerow(row)
        os.replace(tmp_name, out_csv)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def build_structure_summary(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Synthétise la hiérarchie Titres -> Chapitres et les plages de numéros d'articles."""
    titres: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for a in articles:
        titres[a["titre"]][a["chapitre"]].append(a["numero"])
    summary = []
    for t, chaps in titres.items():
        all_nums = [n for lst in chaps.values() for n in lst]
        summary.append(
            {
                "titre": t,
                "nb_articles": len(all_nums),
                "min_article": min(all_nums),
                "max_article": max(all_nums),
                "chapitres": [
                    {
                        "chapitre": c,
                        "nb_articles": len(lst),
                        "min_article": min(lst),
                        "max_article": max(lst),
                    }
                    for c, lst in chaps.items()
                ],
            }
        )
    return {"total_articles": len(articles), "titres": summary}


def render_pages_as_png(pdf_path: Path, page_nums: list[int], out_dir: Path, dpi: int = 150) -> list[Path]:
    """Exporte des pages isolées en PNG compressé pour contrôle visuel ciblé."""
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    saved = []
    for pnum in sorted(set(page_nums)):
        if 1 <= pnum <= len(doc):
            pix = doc[pnum - 1].get_pixmap(dpi=dpi)
            out_file = out_dir / f"{pdf_path.stem[:30]}_p{pnum:03d}.png"
            pix.save(str(out_file))
            saved.append(out_file)
    doc.close()
    return saved


def render_comparison_report(
    pdf_adobe_name: str,
    nb_pages_adobe: int,
    anom_adobe: dict[str, Any],
    n_overrides: int,
    pdf_scan_name: str | None = None,
    nb_pages_scan: int = 0,
    anom_scan: dict[str, Any] | None = None,
    divergences: list[dict[str, Any]] | None = None,
    max_suspects: int = 50,
    max_divergences: int = 80,
) -> str:
    """Construit le rapport Markdown de contrôle d'extraction et de comparaison."""
    lines = [
        "# Rapport d'extraction locale PDF & Comparaison — Code du travail 2026",
        "",
        f"- **PDF Journal Officiel (JO Spécial n° 23, 29 mai 2026) :** `{pdf_adobe_name}` ({nb_pages_adobe} pages)",
        f"  - Articles parsés : **{anom_adobe['total_articles']}** (min={anom_adobe['min_numero']}, max={anom_adobe['max_numero']})",
        f"  - Numéros manquants : `{anom_adobe['missing_numeros']}`",
        f"  - Doublons : `{anom_adobe['duplicate_numeros']}`",
        f"  - Articles suspects à vérifier sur image : **{anom_adobe['suspect_count']}**",
        f"  - Corrections PNG réappliquées (`overrides`) : **{n_overrides}**",
        "",
    ]
    if anom_scan is not None and pdf_scan_name is not None:
        lines += [
            f"- **PDF Scanné pur (Décret + Loi signée) :** `{pdf_scan_name}` ({nb_pages_scan} pages)",
            f"  - Articles parsés : **{anom_scan['total_articles']}** (min={anom_scan['min_numero']}, max={anom_scan['max_numero']})",
            f"  - Numéros manquants : `{anom_scan['missing_numeros']}`",
            f"  - Doublons : `{anom_scan['duplicate_numeros']}`",
            f"  - Divergences détectées entre les 2 PDF : **{len(divergences or [])}**",
            "",
        ]
    if anom_adobe["suspect_articles"]:
        lines.append("## Articles suspects (PDF JO) à vérifier sur image")
        for s in anom_adobe["suspect_articles"][:max_suspects]:
            lines.append(f"- **Art. {s['numero']}** ({', '.join(s['pages_pdf'])}) — `{', '.join(s['reasons'])}` : {s['extrait']}")
    if divergences:
        lines.append("\n## Divergences PDF JO vs PDF Scanné (OCR local)")
        for d in divergences[:max_divergences]:
            lines.append(f"- **Art. {d['numero']}** — `{d['type']}` (sim={d['similarity']}) | JO={d['pages_a']} | Scan={d['pages_b']}")
    return "\n".join(lines)
