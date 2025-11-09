"""
Parser for study plans.
"""

import logging
import re
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
                logger.debug(f"Row has {len(cells)} cells")
                if len(cells) < 10:
                    logger.debug(f"Skipping row with only {len(cells)} cells")
                    continue

                try:
                    code = self.safe_get_text(cells[1])
                    name = self.safe_get_text(cells[2]).strip()
                    release_year = int(self.safe_get_text(cells[4]))
                    required_credits = int(self.safe_get_text(cells[6]))
                    elective_credits = int(self.safe_get_text(cells[7]))
                    credit_limit_text = self.safe_get_text(cells[8])

                    logger.debug(
                        f"Parsing plan: code={code}, name={name}, year={release_year}, "
                        f"req={required_credits}, elec={elective_credits}, limit={credit_limit_text}"
                    )

                    credit_limit = self._extract_credit_limit(credit_limit_text)

                    plan = StudyPlan(
                        code=code,
                        name=name,
                        release_year=release_year,
                        required_credits=required_credits,
                        elective_credits=elective_credits,
                        credit_limit_per_period=credit_limit,
                    )
                    raw_plans.append(plan)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping invalid row: {e}")
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

    def _extract_credit_limit(self, text: str) -> int:
        """Extract numeric credit limit from text."""
        if not text or text.strip() == "":
            return None

        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1))
        return None
