"""Découpage stratifié sur `(strate, origine)` et groupé par `famille_id` (Validation 70 % / Test 30 %)."""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.common.io import atomic_write_text, sha256_file


class StratifiedGroupSplitter:
    """Exécute et gèle le découpage déterministe 70/30 avec garde-fou de validation juriste."""

    def __init__(self, test_ratio: float = 0.30, random_state: int = 42) -> None:
        self.test_ratio = test_ratio
        self.random_state = random_state

    def split(self, items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Sépare les items sans jamais couper un groupe `famille_id` entre Validation et Test."""
        rng = random.Random(self.random_state)
        by_stratum: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for it in items:
            by_stratum[(it["strate"], it.get("origine", "aveugle"))].append(it)

        val_items: list[dict[str, Any]] = []
        test_items: list[dict[str, Any]] = []

        for (_, _), s_items in sorted(by_stratum.items()):
            target_test = round(len(s_items) * self.test_ratio)
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for it in s_items:
                gkey = f"FAM::{it['famille_id']}" if it.get("famille_id") else f"ID::{it['id']}"
                groups[gkey].append(it)

            group_list = list(groups.values())
            rng.shuffle(group_list)
            multi = [g for g in group_list if len(g) > 1]
            single = [g for g in group_list if len(g) == 1]

            cur_test: list[dict[str, Any]] = []
            cur_val: list[dict[str, Any]] = []
            for g in multi + single:
                if len(cur_test) + len(g) <= target_test:
                    cur_test.extend(g)
                else:
                    cur_val.extend(g)

            val_items.extend(cur_val)
            test_items.extend(cur_test)

        return val_items, test_items

    def execute(
        self,
        items: list[dict[str, Any]],
        freeze: bool,
        out_dir: Path,
        existing_errors: list[str],
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """Simule ou gèle les fichiers `validation.json` et `test.json` avec vérification anti-fuite."""
        new_errors: list[str] = []
        not_valid = [it["id"] for it in items if it.get("statut_relecture_juriste") != "valide"]
        if freeze and not_valid:
            new_errors.append(
                f"Split gelé BLOQUÉ : {len(not_valid)} items n'ont pas statut_relecture_juriste == 'valide'"
            )
            return None, new_errors

        val_items, test_items = self.split(items)
        val_fams = {it["famille_id"] for it in val_items if it.get("famille_id")}
        test_fams = {it["famille_id"] for it in test_items if it.get("famille_id")}
        leaked_fams = val_fams & test_fams
        if leaked_fams:
            new_errors.append(f"FUITE famille_id entre Validation et Test : {leaked_fams}")

        summary: dict[str, Any] = {
            "validation_total": len(val_items),
            "test_total": len(test_items),
            "validation_strata": dict(Counter(it["strate"] for it in val_items)),
            "test_strata": dict(Counter(it["strate"] for it in test_items)),
            "validation_origines": dict(Counter(it.get("origine") for it in val_items)),
            "test_origines": dict(Counter(it.get("origine") for it in test_items)),
            "leaked_familles": sorted(leaked_fams),
        }

        if freeze and not existing_errors and not new_errors:
            val_path = out_dir / "validation.json"
            test_path = out_dir / "test.json"
            atomic_write_text(val_path, json.dumps(val_items, ensure_ascii=False, indent=2))
            atomic_write_text(test_path, json.dumps(test_items, ensure_ascii=False, indent=2))
            summary["validation_sha256"] = sha256_file(val_path)
            summary["test_sha256"] = sha256_file(test_path)
            print(
                f"[SPLIT] Gelé -> validation.json ({len(val_items)}, sha256={summary['validation_sha256'][:12]}) "
                f"& test.json ({len(test_items)}, sha256={summary['test_sha256'][:12]})",
                flush=True,
            )
        return summary, new_errors
