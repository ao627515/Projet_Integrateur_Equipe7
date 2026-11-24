"""Contrôles qualité modulaires du jeu d'évaluation (SOLID / Protocol QualityCheck)."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from src.common.io import register_nvidia_dll_dirs
from src.common.text import ngrams, tokenize
from src.evaluation.qa.config import QAConfig, REQUIRED_ITEM_KEYS

PII_PATTERNS = [
    re.compile(r"\b[\w.\-+]+@[\w\-]+\.[\w.\-]+\b"),
    re.compile(r"(?:\+?226[\s\-]?)?(?:\d{2}[\s\-]?){4}\b"),
]


@dataclass
class CheckResult:
    """Résultat normalisé d'un contrôle qualité individuel."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class QualityCheck(Protocol):
    """Contrat minimal de tout contrôle qualité exécutable sur le jeu de données."""

    def run(self, items: list[dict[str, Any]], corpus: dict[int, dict[str, Any]], config: QAConfig) -> CheckResult:
        ...


def load_corpus(path: Path) -> dict[int, dict[str, Any]]:
    """Charge le corpus vérifié (.jsonl ou .json) indexé par numéro d'article."""
    corpus: dict[int, dict[str, Any]] = {}
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    a = json.loads(line)
                    corpus[int(a["numero"])] = a
    else:
        for a in json.loads(path.read_text(encoding="utf-8")):
            corpus[int(a["numero"])] = a
    return corpus


def detect_torch_cuda(requested: str = "auto") -> tuple[bool, str]:
    """Détecte PyTorch CUDA en toute sécurité avec repli CPU."""
    if requested == "cpu":
        return False, "cpu (forcé)"
    try:
        register_nvidia_dll_dirs()
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            t = torch.ones((2, 2), device="cuda")
            _ = (t @ t).cpu()
            return True, f"cuda ({gpu_name})"
    except Exception as exc:
        if requested == "cuda":
            print(f"[WARN] CUDA demandé mais indisponible ({exc}) -> repli CPU", flush=True)
    return False, "cpu"


class SchemaAndIntegrityCheck:
    """Vérifie la présence des 26 champs requis et l'existence de tous les articles dans le corpus."""

    def run(self, items: list[dict[str, Any]], corpus: dict[int, dict[str, Any]], config: QAConfig) -> CheckResult:
        errors: list[str] = []
        for it in items:
            missing = REQUIRED_ITEM_KEYS - set(it.keys())
            if missing:
                errors.append(f"{it.get('id')}: champs manquants {sorted(missing)}")
            if it.get("origine") not in {"aveugle", "equipe"}:
                errors.append(f"{it.get('id')}: origine invalide ({it.get('origine')})")
            if it.get("statut_champ") == "dans_le_champ":
                ap = it.get("article_principal")
                ac = it.get("articles_complementaires") or []
                if ap not in corpus:
                    errors.append(f"{it['id']}: article_principal {ap} absent du corpus")
                if ap in ac:
                    errors.append(f"{it['id']}: article_principal présent dans articles_complementaires")
                if len(set(ac)) != len(ac):
                    errors.append(f"{it['id']}: doublons dans articles_complementaires")
                if 1 + len(ac) > config.max_ri_articles:
                    errors.append(f"{it['id']}: |R_i| > {config.max_ri_articles} ({1 + len(ac)})")
                for c in ac:
                    if c not in corpus:
                        errors.append(f"{it['id']}: article complémentaire {c} absent du corpus")
        return CheckResult(errors=errors)


class PiiCheck:
    """Détecte toute donnée personnelle (adresse e-mail ou numéro de téléphone) dans les questions."""

    def run(self, items: list[dict[str, Any]], corpus: dict[int, dict[str, Any]], config: QAConfig) -> CheckResult:
        _ = (corpus, config)
        pii_hits = []
        for it in items:
            q = it.get("question", "")
            if any(pat.search(q) for pat in PII_PATTERNS):
                pii_hits.append(it["id"])
        errors = [f"PII détectées dans : {pii_hits}"] if pii_hits else []
        return CheckResult(errors=errors, details={"pii_hits": pii_hits})


class QuotaCheck:
    """Vérifie les effectifs par strate, origine, multi-articles et plafond des formes (mode full)."""

    def run(self, items: list[dict[str, Any]], corpus: dict[int, dict[str, Any]], config: QAConfig) -> CheckResult:
        _ = corpus
        strata_counts = Counter(it["strate"] for it in items)
        origine_counts = Counter(it.get("origine") for it in items)
        in_scope = [it for it in items if it["statut_champ"] == "dans_le_champ"]
        multi_count = sum(1 for it in in_scope if len(it.get("articles_complementaires") or []) >= 1)
        forme_counts = Counter(it["forme"] for it in items)
        registre_counts = Counter(it["registre"] for it in items)

        errors: list[str] = []
        if config.mode == "full":
            if len(items) != config.total_dataset_target:
                errors.append(f"Volume total = {len(items)} (attendu {config.total_dataset_target})")
            for st, (tot, _, _) in config.expected_full_strata.items():
                if strata_counts[st] != tot:
                    errors.append(f"Strate {st}: {strata_counts[st]} (attendu {tot})")
            for orig, exp_cnt in config.expected_origine_counts.items():
                if origine_counts[orig] != exp_cnt:
                    errors.append(f"Origine {orig}: {origine_counts[orig]} (attendu {exp_cnt})")
            if origine_counts.get("aveugle", 0) / max(1, len(items)) < config.min_aveugle_ratio:
                errors.append(
                    f"Part aveugle insuffisante ({origine_counts.get('aveugle', 0)}/{len(items)} < {config.min_aveugle_ratio:.0%})"
                )
            if multi_count < config.min_multi_articles:
                errors.append(f"Multi-articles = {multi_count}/200 (plancher bloquant {config.min_multi_articles})")
            for fm, cnt in forme_counts.items():
                if cnt / max(1, len(items)) > config.max_forme_ratio:
                    errors.append(f"Forme {fm} dépasse {int(config.max_forme_ratio * 100)} % ({cnt}/{len(items)})")

        return CheckResult(
            errors=errors,
            details={
                "strata_counts": dict(strata_counts),
                "origine_counts": dict(origine_counts),
                "registre_counts": dict(registre_counts),
                "multi_count": multi_count,
                "in_scope_count": len(in_scope),
            },
        )


class LexicalLeakageCheck:
    """Vérification anti-fuite lexicale parallélisée (0 trigramme rare, <=30% / <=40% mots pleins)."""

    def run(self, items: list[dict[str, Any]], corpus: dict[int, dict[str, Any]], config: QAConfig) -> CheckResult:
        def _eval_one(it: dict[str, Any]) -> dict[str, Any] | None:
            if it.get("statut_champ") != "dans_le_champ":
                return None
            ri = [it["article_principal"]] + list(it.get("articles_complementaires") or [])
            ri_text = " ".join(corpus[n]["texte"] for n in ri if n in corpus)
            q_terms = tokenize(it["question"], remove_stop=True, min_len=config.min_token_len)
            r_terms = tokenize(ri_text, remove_stop=True, min_len=config.min_token_len)
            r_set = set(r_terms)
            overlap = sum(1 for t in set(q_terms) if t in r_set) / max(1, len(set(q_terms)))
            shared_trigrams = ngrams(q_terms, config.leakage_ngram_n) & ngrams(r_terms, config.leakage_ngram_n)

            max_overlap = config.max_overlap_soutenu if it.get("registre") == "soutenu" else config.max_overlap_pop_courant
            if overlap > max_overlap or shared_trigrams:
                return {
                    "id": it["id"],
                    "registre": it.get("registre"),
                    "overlap": round(overlap, 3),
                    "limit": max_overlap,
                    "shared_trigrams": [" ".join(tg) for tg in sorted(shared_trigrams)],
                }
            return None

        safe_workers = max(1, min(config.workers, os.cpu_count() or 1, config.max_workers))
        with ThreadPoolExecutor(max_workers=safe_workers) as ex:
            leaks = [r for r in ex.map(_eval_one, items) if r is not None]

        warnings = [f"Fuite lexicale sur {len(leaks)} question(s) : {[x['id'] for x in leaks[:10]]}"] if leaks else []
        return CheckResult(warnings=warnings, details={"leaks": leaks})


class DuplicateCheck:
    """Détecte les quasi-doublons par similarité cosinus TF-IDF (CUDA si disponible, sinon CPU)."""

    def __init__(self, use_cuda: bool = False) -> None:
        self.use_cuda = use_cuda

    def run(self, items: list[dict[str, Any]], corpus: dict[int, dict[str, Any]], config: QAConfig) -> CheckResult:
        _ = corpus
        if len(items) < 2:
            return CheckResult(details={"dups": []})

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        safe_workers = max(1, min(config.workers, os.cpu_count() or 1, config.max_workers))
        with ThreadPoolExecutor(max_workers=safe_workers) as ex:
            docs_str = list(
                ex.map(lambda it: " ".join(tokenize(it["question"], remove_stop=True, min_len=config.min_token_len)), items)
            )

        vec = TfidfVectorizer(lowercase=False, token_pattern=r"\S+")
        tfidf_sparse = vec.fit_transform(docs_str)

        if self.use_cuda:
            import torch

            mat = tfidf_sparse.toarray().astype(np.float32)
            with torch.no_grad():
                t_mat = torch.from_numpy(mat).to("cuda")
                sim_matrix = (t_mat @ t_mat.T).cpu().numpy()
                del t_mat
                torch.cuda.empty_cache()
        else:
            sim_matrix = cosine_similarity(tfidf_sparse)

        n_docs = len(items)
        dups = []
        for i in range(n_docs):
            for j in range(i + 1, n_docs):
                sim = float(sim_matrix[i, j])
                same_fam = items[i].get("famille_id") is not None and items[i].get("famille_id") == items[j].get("famille_id")
                limit = config.dup_sim_limit_same_famille if same_fam else config.dup_sim_limit_other
                if sim > limit:
                    dups.append(
                        {
                            "id_1": items[i]["id"],
                            "id_2": items[j]["id"],
                            "similarity": round(sim, 3),
                            "same_famille": same_fam,
                            "limit": limit,
                        }
                    )
        errors = [f"Doublons détectés ({len(dups)} paires) : {dups[:5]}"] if dups else []
        return CheckResult(errors=errors, details={"dups": dups})
