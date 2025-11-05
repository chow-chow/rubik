"""
Parser for professor ratings.
"""

import json
import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .base import BaseParser
from .utils import remove_academic_title

logger = logging.getLogger(__name__)


class ProfessorRatingsParser(BaseParser):
    """Parser for professor ratings."""

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
    }

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract professors from JavaScript dataset."""
        try:
            dataset = self._extract_dataset(soup)
            if not dataset:
                return []

            logger.info(f"Extracted {len(dataset)} raw entries")

            processed = []
            for entry in dataset:
                prof = self._process_entry(entry)
                if prof:
                    processed.append(prof)

            logger.info(f"Processed {len(processed)} valid professors")
            return processed

        except Exception as e:
            logger.error(f"Error parsing professors: {e}")
            return []

    def _extract_dataset(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract dataset from JavaScript."""
        scripts = self.safe_find_all(soup, "script")

        for script in scripts:
            if not script.string or "var dataSet" not in script.string:
                continue

            match = re.search(r"var dataSet\s*=\s*(\[.*?\]);", script.string, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        return []

    def _process_entry(self, entry: Dict) -> Optional[Dict]:
        """Process single professor entry."""
        try:
            prof_id = str(entry.get("i", "")).strip()
            first = str(entry.get("n", "")).strip()
            last = str(entry.get("a", "")).strip()

            num_ratings = int(entry.get("m", 0))
            rating = float(entry.get("c", 0.0))

            if not prof_id or not (first or last):
                return None

            full = f"{first} {last}".strip()
            normalized = self._normalize_name(full)

            if not normalized:
                return None

            return {
                "id": prof_id,
                "full_name": normalized,
                "first_name": first,
                "last_name": last,
                "num_ratings": num_ratings,
                "rating": rating,
            }
        except Exception:
            return None

    def _normalize_name(self, name: str) -> str:
        """Normalize professor name."""
        if not name:
            return ""
        name = remove_academic_title(name)
        name = name.upper().strip()
        normalized = "".join([self.ACCENT_MAP.get(c, c) for c in name])
        normalized = re.sub(r"[^A-ZÑ\s]", "", normalized).strip()
        return re.sub(r"\s+", " ", normalized).strip()

    def consolidate(self, professors: List[Dict]) -> List[Dict]:
        """Consolidate duplicate professors."""
        initial = len(professors)

        filtered = [p for p in professors if p.get("num_ratings", 0) > 1]

        groups = defaultdict(list)
        for prof in filtered:
            name = prof.get("full_name", "")
            if name:
                groups[name].append(prof)

        consolidated = []
        for name, entries in groups.items():
            if len(entries) == 1:
                consolidated.append(entries[0])
            else:
                merged = self._merge(entries)
                consolidated.append(merged)

        logger.info(f"Consolidated: {initial} → {len(consolidated)} professors")
        return consolidated

    def _merge(self, entries: List[Dict]) -> Dict:
        """Merge duplicate professors using weighted average."""
        main = max(entries, key=lambda x: x.get("num_ratings", 0))

        total_ratings = 0
        weighted_sum = 0

        for entry in entries:
            n = entry.get("num_ratings", 0)
            r = entry.get("rating", 0.0)
            total_ratings += n
            weighted_sum += r * n

        avg_rating = (
            round(weighted_sum / total_ratings, 2) if total_ratings > 0 else 0.0
        )

        return {
            "id": main.get("id", 0),
            "full_name": main.get("full_name", ""),
            "first_name": main.get("first_name", ""),
            "last_name": main.get("last_name", ""),
            "num_ratings": total_ratings,
            "rating": avg_rating,
        }
