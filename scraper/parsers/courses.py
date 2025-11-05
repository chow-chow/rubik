"""
Parser for courses.
"""

import logging
from typing import Dict

from bs4 import BeautifulSoup

from ..models import Course, SectionType
from .base import BaseParser

logger = logging.getLogger(__name__)


class CoursesParser(BaseParser):
    """Parser for courses."""

    def parse(self, soup: BeautifulSoup) -> Dict[str, Course]:
        """Extract courses from study plan page."""
        courses = {}

        try:
            current_section = None

            for element in soup.find_all(["h5", "table"]):
                if element.name == "h5" and element.get("align") == "center":
                    current_section = self.safe_get_text(element)
                elif element.name == "table" and current_section:
                    self._parse_table(element, current_section, courses)

            logger.info(f"Found {len(courses)} courses")

        except Exception as e:
            logger.error(f"Error parsing courses: {e}")

        return courses

    def _parse_table(self, table, section: str, courses: Dict):
        """Parse courses from table."""
        rows = self.safe_find_all(table, "tr")

        for row in rows:
            cells = self.safe_find_all(row, "td")
            if len(cells) < 4 or "CellIco" not in cells[0].get("class", []):
                continue

            input_tag = self.safe_find(cells[0], "input")
            if not input_tag or "value" not in input_tag.attrs:
                continue

            code = input_tag["value"]
            name = self.safe_get_text(cells[1])
            credits_text = self.safe_get_text(cells[2])

            if code not in courses:
                try:
                    credits = int(credits_text) if credits_text else None
                except ValueError:
                    credits = None

                section_type = self._get_section_type(section)
                courses[code] = Course(
                    code=code, name=name, credits=credits, section=section_type
                )

    def _get_section_type(self, section: str) -> SectionType:
        """Determine section type."""
        s = section.lower().strip()

        if "obligatoria" in s:
            return SectionType.CORE
        elif "humanidades" in s:
            return SectionType.HUMANITIES
        else:
            return SectionType.ELECTIVE
