"""Tests de qualité post-OCR et de cohérence sur le corpus vérifié du Code du travail."""

from __future__ import annotations

import csv
import json
import re
import unittest
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "data/processed/code_travail_2026_articles_verifies.json"
CSV_PATH = PROJECT_ROOT / "data/processed/code_travail_2026_articles_verifies.csv"
QUESTIONS_PATH = PROJECT_ROOT / "data/processed/jeu_evaluation_270.json"

STANDARD_CHARS_RE = re.compile(
    r"[a-zA-ZÀ-ÿœŒ0-9\s\.,;:!\?'\x22\u2019\u2018\u2014\u2022«»\(\)\[\]\-–/%°\*]"
)
GLUED_CAPS_RE = re.compile(
    r"[a-zàâäéèêëîïôöùûüç][A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ][a-zàâäéèêëîïôöùûüç]+"
)


class CorpusQualityTests(unittest.TestCase):
    """Garantit l'absence de régression OCR, de troncature ou d'écart CSV/JSON."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.articles = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
            cls.csv_rows = list(csv.DictReader(f))
        cls.by_num = {a["numero"]: a for a in cls.articles}

    def test_completeness_and_continuity(self) -> None:
        self.assertEqual(len(self.articles), 441)
        self.assertEqual(sorted(self.by_num.keys()), list(range(1, 442)))
        for art in self.articles:
            for k, v in art.items():
                self.assertNotIn(v, (None, "", []), f"Champ vide {k} sur Art. {art['numero']}")

    def test_csv_matches_json(self) -> None:
        self.assertEqual(len(self.csv_rows), len(self.articles))
        csv_by_num = {int(r["numero"]): r for r in self.csv_rows}
        self.assertEqual(sorted(csv_by_num.keys()), sorted(self.by_num.keys()))
        for n, art in self.by_num.items():
            self.assertEqual(
                csv_by_num[n]["texte"].replace("\r\n", "\n"),
                art["texte"].replace("\r\n", "\n"),
                f"Écart CSV/JSON sur Art. {n}",
            )

    def test_unicode_and_typographic_cleanliness(self) -> None:
        for art in self.articles:
            n = art["numero"]
            txt = art["texte"].strip()
            self.assertNotIn("\ufffd", txt, f"U+FFFD sur Art. {n}")
            self.assertFalse(
                any(unicodedata.category(c)[0] == "C" and c not in "\n\t" for c in txt),
                f"Caractère de contrôle sur Art. {n}",
            )
            self.assertEqual(unicodedata.normalize("NFKC", txt), txt, f"Écart NFKC sur Art. {n}")
            self.assertFalse(txt[0].islower(), f"Début en minuscule sur Art. {n}: {txt[:40]}")
            self.assertTrue(
                txt.endswith((".", ";", ":", "?", "!", "»", ")")),
                f"Fin sans ponctuation sur Art. {n}: {txt[-40:]}",
            )
            self.assertEqual(STANDARD_CHARS_RE.sub("", txt), "", f"Caractères hors norme sur Art. {n}")
            self.assertEqual(GLUED_CAPS_RE.findall(txt), [], f"Mot collé sur Art. {n}")
            long_words = [w for w in re.findall(r"[a-zA-ZÀ-ÿ]+", txt) if len(w) > 22]
            self.assertEqual(long_words, [], f"Mot > 22 lettres sur Art. {n}: {long_words}")

    def test_main_pdf_page_sequence_continuous(self) -> None:
        main_src = "decret_no2026-0613_code_du_travail_new.pdf"
        pages = {
            int(d)
            for a in self.articles
            if a["source_pdf"] == main_src
            for p in a["pages_pdf"]
            for d in re.findall(r"\d+", str(p))
        }
        self.assertEqual(min(pages), 5)
        self.assertEqual(max(pages), 128)
        self.assertEqual(sorted(set(range(5, 129)) - pages), [])

    def test_questions_reference_valid_articles(self) -> None:
        questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(questions), 270)
        for q in questions:
            if q["statut_champ"] == "dans_le_champ":
                self.assertIn(q["article_principal"], self.by_num, f"Principal invalide {q['id']}")
                for comp in q["articles_complementaires"]:
                    self.assertIn(comp, self.by_num, f"Complémentaire invalide {q['id']}")


if __name__ == "__main__":
    unittest.main()
