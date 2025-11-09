"""
Parser for study plan courses.
Extracts course organization by section (required, elective, elective_humanities).
"""

import logging
from typing import Dict, List

from bs4 import BeautifulSoup

from .base import BaseParser

logger = logging.getLogger(__name__)


class StudyPlanCoursesParser(BaseParser):
    """Parser for study plan course structure."""

    def parse(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """
        Extract courses organized by section from study plan page.

        Returns:
            Dict with keys: 'required', 'elective', 'elective_humanities'
        """
        sections = {"required": [], "elective": [], "elective_humanities": []}

        try:
            current_section = None

            for element in soup.find_all(["h5", "table"]):
                if element.name == "h5" and element.get("align") == "center":
                    current_section = self.safe_get_text(element)
                elif element.name == "table" and current_section:
                    section_type = self._get_section_type(current_section)
                    if section_type:
                        codes = self._parse_course_codes(element)
                        sections[section_type].extend(codes)

            for key in sections:
                seen = set()
                sections[key] = [
                    x for x in sections[key] if not (x in seen or seen.add(x))
                ]

            logger.debug(
                f"Parsed courses: {len(sections['required'])} required, "
                f"{len(sections['elective'])} elective, "
                f"{len(sections['elective_humanities'])} humanities"
            )

        except Exception as e:
            logger.error(f"Error parsing study plan courses: {e}")

        return sections

    def _parse_course_codes(self, table) -> List[str]:
        """Extract course codes from table."""
        codes = []
        rows = self.safe_find_all(table, "tr")

        for row in rows:
            cells = self.safe_find_all(row, "td")
            if len(cells) < 4 or "CellIco" not in cells[0].get("class", []):
                continue

            input_tag = self.safe_find(cells[0], "input")
            if not input_tag or "value" not in input_tag.attrs:
                continue

            code = input_tag["value"]
            codes.append(code)

        return codes

    def _get_section_type(self, section: str) -> str:
        """Determine section type from header text."""
        s = section.lower().strip()

        if "obligatoria" in s:
            return "required"
        elif "humanidades" in s:
            return "elective_humanities"
        else:
            return "elective"
