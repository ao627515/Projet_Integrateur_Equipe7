"""Métriques diagnostiques du jeu d'évaluation (BM25 et accord inter-annotateurs)."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np

from src.common.text import tokenize


def evaluate_bm25(
    items: list[dict[str, Any]],
    corpus: dict[int, dict[str, Any]],
    top_k: int = 5,
    workers: int = 4,
    max_workers: int = 8,
) -> dict[str, Any]:
    """Évalue BM25Okapi en parallèle sur les questions dans_le_champ (Succès@k & Rappel@k)."""
    from rank_bm25 import BM25Okapi

    art_nums = sorted(corpus.keys())
    safe_workers = max(1, min(workers, os.cpu_count() or 1, max_workers))
    with ThreadPoolExecutor(max_workers=safe_workers) as ex:
        corpus_terms = list(ex.map(lambda n: tokenize(corpus[n]["texte"], remove_stop=False), art_nums))
    bm25 = BM25Okapi(corpus_terms)

    def score_item(it: dict[str, Any]) -> tuple[float, float]:
        q_terms = tokenize(it["question"], remove_stop=False)
        scores = bm25.get_scores(q_terms)
        top_idx = np.argsort(scores)[-top_k:][::-1]
        top_set = {art_nums[int(i)] for i in top_idx}
        ap = it["article_principal"]
        ri = {ap} | set(it.get("articles_complementaires") or [])
        return (1.0 if ap in top_set else 0.0), (len(ri & top_set) / max(1, len(ri)))

    in_scope = [it for it in items if it.get("statut_champ") == "dans_le_champ"]
    non_soutenu = [it for it in in_scope if it.get("registre") != "soutenu"]

    def eval_subset(sub: list[dict[str, Any]]) -> dict[str, float]:
        if not sub:
            return {"n": 0, "succes_at_5": 0.0, "rappel_at_5": 0.0}
        with ThreadPoolExecutor(max_workers=safe_workers) as ex:
            pairs = list(ex.map(score_item, sub))
        s5 = sum(p[0] for p in pairs)
        r5 = sum(p[1] for p in pairs)
        return {
            "n": len(sub),
            "succes_at_5": round(100.0 * s5 / len(sub), 2),
            "rappel_at_5": round(100.0 * r5 / len(sub), 2),
        }

    return {
        "all_dans_le_champ": eval_subset(in_scope),
        "non_soutenu_dans_le_champ": eval_subset(non_soutenu),
    }


def compute_agreement(items_a: list[dict[str, Any]], items_b: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcule l'accord sur l'article principal et le Jaccard moyen sur R_i entre deux annotateurs."""
    map_b = {it["id"]: it for it in items_b}
    principal_matches = 0
    jaccards: list[float] = []
    disagreements = []
    n = 0
    for a in items_a:
        if a["id"] not in map_b:
            continue
        b = map_b[a["id"]]
        n += 1
        ap_a, ap_b = a.get("article_principal"), b.get("article_principal")
        if ap_a == ap_b:
            principal_matches += 1
        ra = ({ap_a} if ap_a else set()) | set(a.get("articles_complementaires") or [])
        rb = ({ap_b} if ap_b else set()) | set(b.get("articles_complementaires") or [])
        jac = 1.0 if (not ra and not rb) else len(ra & rb) / max(1, len(ra | rb))
        jaccards.append(jac)
        if ap_a != ap_b or jac < 1.0:
            disagreements.append({"id": a["id"], "A": sorted(ra), "B": sorted(rb), "jaccard": round(jac, 3)})
    return {
        "n_compared": n,
        "principal_agreement_pct": round(100.0 * principal_matches / max(1, n), 2),
        "mean_jaccard": round(sum(jaccards) / max(1, len(jaccards)), 3),
        "disagreements_count": len(disagreements),
        "disagreements_sample": disagreements[:15],
    }
