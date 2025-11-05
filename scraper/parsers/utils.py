"""
Shared utilities.
"""

import re
from typing import Set

ACADEMIC_TITLES: Set[str] = {
    "DR",
    "DR.",
    "DRA",
    "DRA.",
    "DOC",
    "DOC.",
    "M.C.",
    "MC",
    "M.C",
    "MC.",
    "M.C.Q.",
    "MCQ",
    "MCQ.",
    "M.C.Q",
    "MC.Q",
    "M.CQ",
    "M.I.",
    "MI",
    "M.I",
    "MI.",
    "M.A.",
    "MA",
    "MA.",
    "M.A",
    "M.E.",
    "ME",
    "ME.",
    "M.E",
    "MTRO",
    "MTRO.",
    "MTRA",
    "MTRA.",
    "M.SC.",
    "MSC",
    "M.SC",
    "MSC.",
    "ING",
    "ING.",
    "LIC",
    "LIC.",
    "ARQ",
    "ARQ.",
    "PROF",
    "PROF.",
    "C.P.",
    "CP",
    "CP.",
    "C.P",
    "L.C.C.",
    "LCC",
    "LCC.",
    "L.C.C",
    "L.CC",
    "LC.C",
    "L.A.",
    "LA",
    "LA.",
    "L.A",
    "C.D.",
    "CD",
    "CD.",
    "C.D",
    "Q.F.B.",
    "QFB",
    "QFB.",
    "Q.F.B",
    "Q.FB",
    "QF.B",
    "M.D.",
    "MD",
    "MD.",
    "M.D",
    "PH.D.",
    "PHD",
    "PHD.",
    "PH.D",
    "PH.D",
    "P.H.D.",
}


def remove_academic_title(name: str) -> str:
    """
    Remove academic title from professor name.

    Handles various formats:
    - With/without dots: M.C. vs MC
    - With/without trailing dot: M.C.Q vs M.C.Q.
    - Missing dots: M.C.Q vs MCQ or MC.Q

    Args:
        name: Professor name potentially with academic title

    Returns:
        Cleaned name without academic title

    Examples:
        >>> remove_academic_title("M.C.Q. JUAN PEREZ")
        "JUAN PEREZ"
        >>> remove_academic_title("MCQ JUAN PEREZ")
        "JUAN PEREZ"
        >>> remove_academic_title("ING MARIA LOPEZ")
        "MARIA LOPEZ"
    """
    if not name:
        return ""

    name = name.strip()
    name_upper = name.upper()

    for title in sorted(ACADEMIC_TITLES, key=len, reverse=True):
        if name_upper.startswith(title):
            if len(name) == len(title) or name[len(title)].isspace():
                return name[len(title) :].lstrip(". ")

    return name.strip()


def normalize_name_for_matching(name: str) -> str:
    """
    Normalize professor name for matching purposes.
    Removes accents, titles, and extra whitespace.

    Args:
        name: Professor name to normalize

    Returns:
        Normalized name in uppercase without accents or titles
    """
    ACCENT_MAP = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "á": "A",
        "é": "E",
        "í": "I",
        "ó": "O",
        "ú": "U",
        "ü": "U",
        "Ü": "U",
    }

    if not name:
        return ""

    name = re.sub(r"\s*\(.*?\)", "", name)

    name = name.replace("\n", " ").strip()

    name = remove_academic_title(name)

    name = name.upper().strip()

    normalized = "".join([ACCENT_MAP.get(c, c) for c in name])

    normalized = re.sub(r"[^A-ZÑ\s]", "", normalized).strip()

    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized
