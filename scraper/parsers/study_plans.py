"""
Parser for study plans.
"""

import logging
from typing import List

from bs4 import BeautifulSoup

from ..models import StudyPlan
from .base import BaseParser

logger = logging.getLogger(__name__)


class StudyPlansParser(BaseParser):
    """Parser for study plans."""

    def parse(self, soup: BeautifulSoup, program_code: str) -> List[StudyPlan]:
        """Extract study plans for a program."""
        try:
            table = self.safe_find(soup, "table", class_="TblBlk")
            if not table:
                return []

            raw_plans = []
            rows = self.safe_find_all(table, "tr")[1:]

            for row in rows:
                cells = self.safe_find_all(row, "td")
                if len(cells) < 10:
                    continue

                try:
                    plan = StudyPlan(
                        code=self.safe_get_text(cells[1]),
                        name=self.safe_get_text(cells[2]).split("-")[-1].strip(),
                        release_year=int(self.safe_get_text(cells[4])),
                        duration=int(self.safe_get_text(cells[5]).split()[0]),
                    )
                    raw_plans.append(plan)
                except (ValueError, IndexError):
                    continue

            if not raw_plans:
                return []

            max_year = max(p.release_year for p in raw_plans)
            latest = [p for p in raw_plans if p.release_year == max_year]

            logger.debug(
                f"Filtered {len(raw_plans)} to {len(latest)} latest plans for program {program_code}"
            )
            return latest

        except Exception as e:
            logger.error(f"Error parsing study plans for {program_code}: {e}")
            return []
