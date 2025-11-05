"""
Parser for academic programs.
"""

import logging
from typing import Dict, List

from bs4 import BeautifulSoup

from .base import BaseParser

logger = logging.getLogger(__name__)


class ProgramsParser(BaseParser):
    """Parser for degree programs."""

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract programs from index page."""
        programs = []

        try:
            table = self.safe_find(soup, "table", class_="TblBlk")
            if not table:
                return programs

            rows = self.safe_find_all(table, "tr")[1:]

            for row in rows:
                cells = self.safe_find_all(row, "td")
                if len(cells) < 2:
                    continue

                code_input = self.safe_find(cells[0], "input", {"name": "crr"})
                if not code_input:
                    continue

                code = code_input.get("value")
                name = self.safe_get_text(cells[1])

                if code and code not in ("116", "120"):
                    programs.append({"code": code, "name": name})

            logger.info(f"Parsed {len(programs)} programs")

        except Exception as e:
            logger.error(f"Error parsing programs: {e}")

        return programs
