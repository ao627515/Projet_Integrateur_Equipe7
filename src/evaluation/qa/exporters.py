"""Exports de relecture juridique (CSV atomique) et rapport Markdown de contrôle qualité."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def export_jurist_csv(items: list[dict[str, Any]], out_csv: Path) -> None:
    """Exporte de manière atomique le tableau de relecture juridique UTF-8 BOM."""
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id", "origine", "strate", "persona", "registre", "forme", "type_question", "famille_id",
        "comportement_attendu", "question", "article_principal", "articles_complementaires",
        "source_pdf", "pages_pdf", "nombres_cles", "reponse_reference",
        "statut_relecture_juriste", "commentaire_juriste",
    ]
    fd, tmp_name = tempfile.mkstemp(prefix=out_csv.name + ".", suffix=".tmp", dir=str(out_csv.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for it in items:
                w.writerow(
                    {
                        "id": it["id"],
                        "origine": it.get("origine", "aveugle"),
                        "strate": it["strate"],
                        "persona": it["persona"],
                        "registre": it["registre"],
                        "forme": it["forme"],
                        "type_question": it["type_question"],
                        "famille_id": it.get("famille_id") or "",
                        "comportement_attendu": it["comportement_attendu"],
                        "question": it["question"],
                        "article_principal": it.get("article_principal") or "",
                        "articles_complementaires": json.dumps(it.get("articles_complementaires") or []),
                        "source_pdf": it.get("source_pdf") or "",
                        "pages_pdf": "; ".join(it.get("pages_pdf") or []),
                        "nombres_cles": "; ".join(it.get("nombres_cles") or []),
                        "reponse_reference": it["reponse_reference"],
                        "statut_relecture_juriste": it["statut_relecture_juriste"],
                        "commentaire_juriste": "",
                    }
                )
        os.replace(tmp_name, out_csv)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def render_qa_report(
    mode: str,
    n_items: int,
    dev_label: str,
    quota_details: dict[str, Any],
    leaks: list[dict[str, Any]],
    dups: list[dict[str, Any]],
    errors: list[str],
    bm25_res: dict[str, Any] | None = None,
    agree_res: dict[str, Any] | None = None,
    split_summary: dict[str, Any] | None = None,
    random_state: int = 42,
) -> str:
    """Construit le rapport Markdown de synthèse qualité."""
    report_lines = [
        f"# Rapport de contrôle qualité (`mode={mode}`, `n={n_items}`, `device={dev_label}`)",
        "",
        f"- **Strates :** `{quota_details['strata_counts']}`",
        f"- **Origines :** `{quota_details['origine_counts']}`",
        f"- **Registres :** `{quota_details['registre_counts']}`",
        f"- **Multi-articles (`dans_le_champ`) :** `{quota_details['multi_count']}/{quota_details['in_scope_count']}`",
        f"- **Fuites lexicales :** `{len(leaks)}`",
        f"- **Doublons :** `{len(dups)}`",
        f"- **Erreurs bloquantes :** `{len(errors)}`",
        "",
    ]
    if bm25_res:
        report_lines.append(f"- **Benchmark BM25 :** `{json.dumps(bm25_res, ensure_ascii=False)}`")
    if agree_res:
        report_lines.append(
            f"- **Accord inter-annotateurs (A vs B) :** principal=`{agree_res['principal_agreement_pct']}%`, "
            f"Jaccard=`{agree_res['mean_jaccard']}` (n={agree_res['n_compared']})"
        )
    if split_summary:
        report_lines.append(
            f"- **Split 70/30 (`random_state={random_state}`) :** `{json.dumps(split_summary, ensure_ascii=False)}`"
        )
    if leaks:
        report_lines.append("\n## Détail fuites lexicales")
        for lk in leaks:
            report_lines.append(
                f"- `{lk['id']}` ({lk['registre']}): overlap={lk['overlap']} (max {lk['limit']}), trigrammes={lk['shared_trigrams']}"
            )
    if errors:
        report_lines.append("\n## Erreurs bloquantes")
        for e in errors:
            report_lines.append(f"- {e}")
    return "\n".join(report_lines)
