"""Détection d'anomalies, comparaison entre les deux PDF, fusion et application des correctifs PNG."""

from __future__ import annotations

import difflib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from src.common.text import normalize_for_diff

NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_SUSPECT_CHAR_RE = re.compile(r"[_|~]{2,}|[^\w\s.,;:!?()'\"°%€\-–—/«»’àâäéèêëïîôöùûüçÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ]")


def detect_anomalies(articles: list[dict[str, Any]], min_text_len: int = 15) -> dict[str, Any]:
    """Vérifie la continuité 1..N, l'absence de doublons et les artefacts OCR dans les textes."""
    nums = [a["numero"] for a in articles]
    counts = Counter(nums)
    duplicates = sorted([n for n, c in counts.items() if c > 1])
    max_n = max(nums) if nums else 0
    missing = [n for n in range(1, max_n + 1) if n not in counts]

    suspect_articles = []
    for a in articles:
        reasons = []
        txt = a["texte"]
        if "\ufffd" in txt:
            reasons.append("caractere_U+FFFD")
        if re.search(r"CHAPITRE\s*\d+", txt, re.IGNORECASE):
            reasons.append("chapitre_fusionne_dans_texte")
        if re.search(r"TITRE\s*[IVX]+", txt):
            reasons.append("titre_fusionne_dans_texte")
        if len(txt) < min_text_len:
            reasons.append("texte_trop_court")
        if _SUSPECT_CHAR_RE.search(txt):
            reasons.append("caracteres_ocr_suspects")
        if reasons:
            suspect_articles.append(
                {
                    "numero": a["numero"],
                    "pages_pdf": a["pages_pdf"],
                    "reasons": reasons,
                    "extrait": txt[:140],
                }
            )

    return {
        "total_articles": len(articles),
        "min_numero": min(nums) if nums else None,
        "max_numero": max_n,
        "missing_numeros": missing,
        "duplicate_numeros": duplicates,
        "suspect_count": len(suspect_articles),
        "suspect_articles": suspect_articles,
    }


def compare_extractions(
    arts_a: list[dict[str, Any]],
    arts_b: list[dict[str, Any]],
    similarity_threshold: float = 0.90,
) -> list[dict[str, Any]]:
    """Compare article par article deux extractions issues des deux PDF officiels."""
    map_a = {a["numero"]: a for a in arts_a}
    map_b = {a["numero"]: a for a in arts_b}
    divergences = []
    for n in sorted(set(map_a) | set(map_b)):
        a = map_a.get(n)
        b = map_b.get(n)
        if not a or not b:
            divergences.append(
                {
                    "numero": n,
                    "type": "article_manquant_un_pdf",
                    "pages_a": a["pages_pdf"] if a else [],
                    "pages_b": b["pages_pdf"] if b else [],
                    "similarity": 0.0,
                }
            )
            continue
        sim = difflib.SequenceMatcher(None, normalize_for_diff(a["texte"]), normalize_for_diff(b["texte"])).ratio()
        nums_a = NUMBER_RE.findall(a["texte"])
        nums_b = NUMBER_RE.findall(b["texte"])
        if sim < similarity_threshold or nums_a != nums_b:
            divergences.append(
                {
                    "numero": n,
                    "type": "divergence_chiffres" if nums_a != nums_b else "divergence_texte",
                    "similarity": round(sim, 3),
                    "pages_a": a["pages_pdf"],
                    "pages_b": b["pages_pdf"],
                    "nums_a": nums_a,
                    "nums_b": nums_b,
                }
            )
    return divergences


def merge_extractions(
    arts_primary: list[dict[str, Any]],
    arts_fallback: list[dict[str, Any]],
    anom_primary: dict[str, Any],
) -> list[dict[str, Any]]:
    """Injecte depuis le PDF de secours les articles manquants ou corrompus de la source principale."""
    fallback_map = {a["numero"]: a for a in arts_fallback}
    merged_map = {a["numero"]: a for a in arts_primary}
    suspect_nums = {s["numero"] for s in anom_primary["suspect_articles"] if "@" in s["extrait"]}
    for n in sorted(set(anom_primary["missing_numeros"]) | suspect_nums):
        if n in fallback_map:
            injected = dict(fallback_map[n])
            if (n - 1) in merged_map and injected["titre"].replace(" ", "") == merged_map[n - 1]["titre"].replace(" ", ""):
                injected["titre"] = merged_map[n - 1]["titre"]
                injected["chapitre"] = merged_map[n - 1]["chapitre"]
            merged_map[n] = injected
    return [merged_map[k] for k in sorted(merged_map)]


def apply_manual_overrides(articles: list[dict[str, Any]], overrides_path: Path) -> int:
    """Réapplique les corrections vérifiées sur image PNG (empêche tout écrasement lors des relances)."""
    if not overrides_path.exists():
        return 0
    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    by_num = {int(o["numero"]): o for o in overrides}
    applied = 0
    for a in articles:
        ov = by_num.get(int(a["numero"]))
        if ov and "texte" in ov:
            a["texte"] = ov["texte"]
            applied += 1
    return applied
