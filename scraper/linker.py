"""
Professor-Groups linker.
"""

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .parsers.utils import remove_academic_title

logger = logging.getLogger(__name__)


class ProfessorGroupsLinker:
    """Links professors with their groups"""

    CONNECTORS = {"DE", "DEL", "LA", "LAS", "LOS", "Y"}

    def __init__(self, data_dir: str = "data"):
        """Initialize linker with data directory."""
        self.data_dir = Path(data_dir)
        self.professors = []
        self.professor_by_normalized = {}
        self.professor_by_tokens = defaultdict(list)

    def link(self) -> Tuple[int, int, int]:
        """
        Link professors with groups.

        Returns:
            Tuple of (matched_professors, total_groups, unmatched_groups)
        """
        logger.info("Starting professor-groups linking")

        self._load_professors()

        self._build_indexes()

        matched_count, total_groups, unmatched = self._process_groups()

        logger.info(
            f"Linking completed: {matched_count}/{total_groups} groups matched "
            f"({unmatched} unmatched)"
        )

        return matched_count, total_groups, unmatched

    def _load_professors(self) -> None:
        """Load professor ratings."""
        filepath = self.data_dir / "professor_ratings.json"
        if not filepath.exists():
            logger.warning("professor_ratings.json not found")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.professors = json.load(f)
            logger.info(f"Loaded {len(self.professors)} professors")
        except Exception as e:
            logger.error(f"Error loading professors: {e}")

    def _build_indexes(self) -> None:
        """Build lookup indexes for fast matching."""
        for prof in self.professors:
            full_name = prof.get("full_name", "")
            normalized = self._normalize_name(full_name)

            self.professor_by_normalized[normalized] = prof

            tokens = self._get_tokens(normalized)
            token_key = " ".join(sorted(tokens))
            self.professor_by_tokens[token_key].append(prof)

        logger.info(f"Built indexes for {len(self.professors)} professors")

    def _normalize_name(self, name: str) -> str:
        """Normalize name for matching."""
        if not name:
            return ""
        name = remove_academic_title(name)
        name = name.upper().strip()
        name = re.sub(r"[^A-ZÑ\s]", "", name)
        words = name.split()
        words = [w for w in words if w and w not in self.CONNECTORS]
        return " ".join(words)

    def _get_tokens(self, normalized_name: str) -> Set[str]:
        """Get set of tokens from normalized name."""
        return set(normalized_name.split()) if normalized_name else set()

    def _process_groups(self) -> Tuple[int, int, int]:
        """Process all groups and link with professors."""
        groups_dir = self.data_dir / "groups"
        if not groups_dir.exists():
            logger.warning("groups directory not found")
            return 0, 0, 0

        logger.info("Extracting unique professor names...")
        unique_professors = set()
        all_groups_data = {}

        for file in groups_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    groups = json.load(f)
                    all_groups_data[file] = groups

                    for group in groups:
                        professor_name = group.get("professor", "")
                        if professor_name:
                            unique_professors.add(professor_name)
            except Exception as e:
                logger.warning(f"Error reading {file}: {e}")

        logger.info(f"Found {len(unique_professors)} unique professor names")

        logger.info("Matching professor names...")
        professor_matches = {}
        for professor_name in unique_professors:
            match = self._match_professor(professor_name)
            professor_matches[professor_name] = match

        logger.info("Applying matches to groups...")
        matched_count = 0
        total_groups = 0
        unmatched = 0

        for file, groups in all_groups_data.items():
            try:
                updated = False
                for group in groups:
                    total_groups += 1
                    professor_name = group.get("professor", "")

                    if not professor_name:
                        continue

                    match = professor_matches.get(professor_name)

                    if match:
                        group["professor_id"] = match["id"]
                        matched_count += 1
                        updated = True
                    else:
                        group["professor_id"] = None
                        unmatched += 1

                if updated:
                    with open(file, "w", encoding="utf-8") as f:
                        json.dump(groups, f, indent=2, ensure_ascii=False)

            except Exception as e:
                logger.warning(f"Error processing {file}: {e}")

        return matched_count, total_groups, unmatched

    def _match_professor(self, professor_name: str) -> Optional[Dict]:
        """
        Match professor name with rating entry.

        Uses multiple strategies in order of confidence.
        """
        normalized = self._normalize_name(professor_name)
        if not normalized:
            return None

        if normalized in self.professor_by_normalized:
            return self.professor_by_normalized[normalized]

        group_tokens = self._get_tokens(normalized)
        if not group_tokens:
            return None

        matches = []
        for token_key, profs in self.professor_by_tokens.items():
            rating_tokens = set(token_key.split())

            if rating_tokens.issubset(group_tokens):
                matches.extend(profs)

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            logger.warning(
                f"Multiple matches for '{normalized}': "
                f"{[p.get('full_name') for p in matches]}"
            )
            matches.sort(
                key=lambda p: len(self._get_tokens(p.get("full_name", ""))),
                reverse=True,
            )
            logger.info(f"Selected match: {matches[0].get('full_name')}")
            return matches[0]

        for prof in self.professors:
            rating_tokens = self._get_tokens(prof.get("full_name", ""))
            if group_tokens.issubset(rating_tokens):
                return prof

        return None


def link_professors_groups(data_dir: str = "data") -> bool:
    """
    Link professors with groups.

    Args:
        data_dir: Data directory path

    Returns:
        True if successful
    """
    try:
        linker = ProfessorGroupsLinker(data_dir)
        matched, total, unmatched = linker.link()

        if total > 0:
            match_rate = (matched / total) * 100
            logger.info(
                f"Match rate: {match_rate:.1f}% ({matched}/{total}), "
                f"Unmatched: {unmatched}"
            )

        return True
    except Exception as e:
        logger.error(f"Error linking professors and groups: {e}")
        return False
