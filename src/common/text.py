"""Normalisation et découpage lexical français partagés."""

from __future__ import annotations

import re

EXTRA_FRENCH_STOPWORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "cette", "cet", "dans", "de", "des", "du",
    "elle", "en", "est", "et", "eu", "il", "ils", "je", "la", "le", "les", "leur",
    "lui", "ma", "mais", "me", "meme", "mes", "moi", "mon", "ne", "nos", "notre",
    "nous", "on", "ou", "par", "pas", "pour", "qu", "que", "quel", "quelle", "quels",
    "quelles", "qui", "sa", "sans", "se", "ses", "si", "son", "sont", "sur", "ta",
    "te", "tes", "toi", "ton", "tu", "un", "une", "vos", "votre", "vous", "y",
    "d", "l", "m", "n", "s", "t", "c", "j", "ai", "as", "ont", "etre", "avoir",
    "fait", "faire", "peut", "peux", "plus", "tout", "tous", "toute", "toutes",
    "comme", "dont", "afin", "alors", "ainsi", "apres", "avant", "bien", "chez",
    "depuis", "donc", "encore", "entre", "ici", "jusqu", "lors", "moins", "ni",
    "non", "oui", "peu", "quand", "rien", "soit", "sous", "tres", "trop", "vers",
    "estce", "ca", "cest", "sil", "sils", "jai", "svp", "cmt",
}


def load_french_stopwords() -> set[str]:
    """Charge les stopwords français (fusionne nltk/spacy si installés avec la liste locale)."""
    words = set(EXTRA_FRENCH_STOPWORDS)
    try:
        from nltk.corpus import stopwords as nltk_sw

        for w in nltk_sw.words("french"):
            words.add(w.lower())
    except Exception:
        pass
    try:
        from spacy.lang.fr.stop_words import STOP_WORDS as spacy_sw

        for w in spacy_sw:
            words.add(w.lower())
    except Exception:
        pass
    return words


FRENCH_STOPWORDS = load_french_stopwords()


def strip_french_accents(text: str) -> str:
    """Normalise en minuscules et retire les diacritiques français courants."""
    text = text.lower()
    return (
        text.replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
        .replace("à", "a").replace("â", "a").replace("ä", "a")
        .replace("î", "i").replace("ï", "i")
        .replace("ô", "o").replace("ö", "o")
        .replace("ù", "u").replace("û", "u").replace("ü", "u")
        .replace("ç", "c").replace("œ", "oe")
    )


def normalize_for_diff(text: str) -> str:
    """Normalise un texte pour la comparaison de similarité entre deux extractions."""
    cleaned = re.sub(r"[^a-z0-9\s]", " ", strip_french_accents(text))
    return re.sub(r"\s+", " ", cleaned).strip()


def tokenize(text: str, remove_stop: bool = True, min_len: int = 3) -> list[str]:
    """Découpe un texte français en termes alphanumériques normalisés."""
    terms = re.findall(r"[a-z0-9]+", strip_french_accents(text))
    if remove_stop:
        return [t for t in terms if len(t) >= min_len and t not in FRENCH_STOPWORDS]
    return terms


def ngrams(terms: list[str], n: int) -> set[tuple[str, ...]]:
    """Construit l'ensemble des n-grammes contigus d'une séquence de termes."""
    if len(terms) < n:
        return set()
    return {tuple(terms[i : i + n]) for i in range(len(terms) - n + 1)}
