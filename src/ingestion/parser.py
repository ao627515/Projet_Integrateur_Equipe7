"""Parsing structurel et normalisation typographique des 441 articles du Code du travail."""

from __future__ import annotations

import re
from typing import Any

HEADER_NOISE_RE = re.compile(
    r"^(?:"
    r"\d{1,3}|"
    r"29\s*mai\s*2026|"
    r"JOURNAL\s*OFFICIEL.*|"
    r"SPECIAL\s*N°?\s*23.*|"
    r"B7/21/2826.*|"
    r"87/21/2826.*|"
    r"IMPRIMERIE DU JOURNAL OFFICIEL.*|"
    r"01\s*Bp\s*3924.*|"
    r"Dépôt\s*Légal.*|"
    r"(?:[FBELTbfelt]u|lu|tu)\s*la\s*M(?:or[lti]|er[li])|"
    r"4\.0\s+travail\s+luts\s+Mori|"
    r"BURKINA\s*FASO?|BURKIHA|EASG|Laputre|"
    r"\.?8P|>\s*104|•"
    r")$",
    re.IGNORECASE,
)

_INLINE_STAMP_RE = re.compile(
    r"(?:\b(?:[FBELTbfelt]u|lu|tu)\s*la\s*M(?:or[lti]|er[li])\b|"
    r"\b4\.0\s+travail\s+luts\s+Mori\b|"
    r"\bBURKINA\s*FAS\b|\bBURKIHA\b|\bEASG\b|\bLaputre\b|"
    r"\.\.8P\b|>\s*104|\s*•$|\s+4\.0$)"
)

_ART_HEADING_RE = re.compile(
    r"^[:.\-\s]*(?:Article|Artiche|Articie)[\s.]*(premier|1er|[\dZzOoIi][\s\dZzOoIi]{0,4})\s*[_\s]*[:：.\-–]?\s*(.*)$",
    re.IGNORECASE,
)


class CodeTravailParser:
    """Reconstruit les articles ordonnés et leurs titres/chapitres/sections depuis les pages extraites."""

    def __init__(self, min_num: int = 1, max_num: int = 450, max_jump: int = 10) -> None:
        self.min_num = min_num
        self.max_num = max_num
        self.max_jump = max_jump

    def _parse_article_num(self, raw_num: str) -> int | None:
        s = raw_num.strip().lower().replace(" ", "")
        if s in ("premier", "1er"):
            return 1
        s = s.translate(str.maketrans({"z": "7", "o": "0", "l": "1", "i": "1"}))
        if s.isdigit():
            val = int(s)
            if self.min_num <= val <= self.max_num:
                return val
        return None

    @staticmethod
    def normalize_heading(kind: str, raw: str) -> str:
        """Normalise les en-têtes TITRE / CHAPITRE / Section (espaces propres et coquilles OCR)."""
        s = raw.replace("’", "'").replace("：", ":").replace("E'T", "ET").rstrip(" _").strip()
        if kind == "TITRE":
            s = re.sub(r"^TITRE\s*([IVX]+)\s*:\s*", r"TITRE \1 : ", s, flags=re.IGNORECASE)
        elif kind == "CHAPITRE":
            s = re.sub(r"^CHAPITRE\s*([IVX\dOS]+)\s*:\s*", r"CHAPITRE \1 : ", s, flags=re.IGNORECASE)
            s = re.sub(r"^CHAPITRE\s+1O\s*:", "CHAPITRE 10 :", s)
            s = re.sub(r"^CHAPITRE\s+S\s*:", "CHAPITRE 5 :", s)
            s = s.replace("TRAVAHL", "TRAVAIL")
        elif kind == "SECTION":
            s = re.sub(r"^Section\s*([IVX\d]+)\s*:\s*", r"Section \1 : ", s, flags=re.IGNORECASE)
            s = (
                s.replace("Télétrayail", "Télétravail")
                .replace("d'établissem ent", "d'établissement")
                .replace("Iours chômés", "Jours chômés")
                .replace("Margues", "Marques")
                .replace("trayail", "travail")
            )
        return re.sub(r"\s+", " ", s).strip()

    @staticmethod
    def clean_article_text(text: str) -> str:
        """Nettoie les artefacts typographiques et tampons marginaux OCR sans altérer le sens juridique."""
        txt = (
            text.replace("’", "'")
            .replace("‘", "'")
            .replace("：", ":")
            .replace("exéqutée", "exécutée")
            .replace("ę", "e")
            .replace("ě", "e")
            .replace("_", " ")
            .replace("consuItatif", "consultatif")
            .replace("circonscriptionadministrative", "circonscription administrative")
            .replace("estHéclaré", "est déclaré")
            .replace("depreuve", "de preuve")
        )
        txt = re.sub(r"(?<=[A-Za-zÀ-ÿ])\$(?=[A-Za-zÀ-ÿ\s.,;:])", "s", txt)
        txt = _INLINE_STAMP_RE.sub("", txt)
        txt = re.sub(r"^[_\s:]+", "", txt)
        txt = re.sub(r"\s+([,.;])", r"\1", txt)
        txt = re.sub(r"([,;:])([A-Za-zÀ-ÖØ-öø-ÿ])", r"\1 \2", txt)
        txt = re.sub(r"(\d+\))([A-Za-zÀ-ÖØ-öø-ÿ])", r"\1 \2", txt)
        return re.sub(r"\s+", " ", txt).strip()

    def parse(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse séquentiellement les pages à partir de TITRE I et retourne les articles structurés."""
        articles: list[dict[str, Any]] = []
        cur_titre = "Non spécifié"
        cur_chapitre = "Non spécifié"
        cur_section = "Sans section"
        cur_art: dict[str, Any] | None = None
        pending_heading: str | None = None
        in_code = False

        def flush() -> None:
            nonlocal cur_art
            if cur_art is not None:
                txt = self.clean_article_text(cur_art["texte"])
                if cur_art["numero"] == 441:
                    txt = re.split(r"Ainsi\s*fait\s*et\s*d[ée]lib[ée]r[ée]", txt, flags=re.IGNORECASE)[0].strip()
                cur_art["texte"] = txt
                articles.append(cur_art)
                cur_art = None

        for p in pages:
            page_label = f"p. {p['page']}"
            source_pdf = p["source_pdf"]
            for raw_line in p["text"].splitlines():
                line = raw_line.strip()
                if not line or HEADER_NOISE_RE.match(line):
                    continue

                if re.match(r"^TITRE\s*[IVX]+\s*[:：]", line):
                    in_code = True
                    flush()
                    cur_titre = self.normalize_heading("TITRE", line)
                    cur_chapitre = "Non spécifié"
                    cur_section = "Sans section"
                    pending_heading = "TITRE"
                    continue

                if not in_code:
                    continue

                if re.match(r"^CHAPITRE\s*[IVX\dOS]+\s*[:：]", line):
                    flush()
                    cur_chapitre = self.normalize_heading("CHAPITRE", line)
                    cur_section = "Sans section"
                    pending_heading = "CHAPITRE"
                    continue
                if re.match(r"^Section\s*[IVX\d]+\s*[:：]?", line, re.IGNORECASE):
                    flush()
                    cur_section = self.normalize_heading("SECTION", line)
                    pending_heading = "SECTION"
                    continue

                m = _ART_HEADING_RE.match(line)
                if m:
                    num = self._parse_article_num(m.group(1))
                    last_num = cur_art["numero"] if cur_art else (articles[-1]["numero"] if articles else 0)
                    if num is not None and (last_num == 0 or last_num < num <= last_num + self.max_jump):
                        flush()
                        pending_heading = None
                        cur_art = {
                            "numero": num,
                            "titre": cur_titre,
                            "chapitre": cur_chapitre,
                            "section": cur_section,
                            "texte": m.group(2).strip(),
                            "source_pdf": source_pdf,
                            "pages_pdf": [page_label],
                        }
                        continue

                if cur_art is None and pending_heading is not None:
                    if pending_heading == "SECTION":
                        cur_section = self.normalize_heading("SECTION", f"{cur_section} {line}")
                    elif pending_heading == "CHAPITRE":
                        cur_chapitre = self.normalize_heading("CHAPITRE", f"{cur_chapitre} {line}")
                    elif pending_heading == "TITRE":
                        cur_titre = self.normalize_heading("TITRE", f"{cur_titre} {line}")
                    continue

                if cur_art is not None:
                    cur_art["texte"] += " " + line
                    if page_label not in cur_art["pages_pdf"]:
                        cur_art["pages_pdf"].append(page_label)

        flush()
        return articles
