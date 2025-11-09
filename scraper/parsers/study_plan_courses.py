"""
Parser for study plan courses.
Extracts course organization by section (required, elective, elective_humanities).
"""

import logging
import re
from typing import Dict, List

from bs4 import BeautifulSoup

from .base import BaseParser

logger = logging.getLogger(__name__)


class StudyPlanCoursesParser(BaseParser):
    """Parser for study plan course structure."""

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract courses with metadata from study plan page.

        Returns:
            List of dicts with keys: 'code', 'semester' (optional), 'type'
        """
        courses = []

        try:
            current_section = None

            for element in soup.find_all(["h5", "table"]):
                if element.name == "h5" and element.get("align") == "center":
                    current_section = self.safe_get_text(element)
                elif element.name == "table" and current_section:
                    section_type = self._get_section_type(current_section)
                    if section_type:
                        course_objects = self._parse_course_objects(
                            element, section_type
                        )
                        courses.extend(course_objects)

            seen = set()
            unique_courses = []
            for course in courses:
                if course["code"] not in seen:
                    seen.add(course["code"])
                    unique_courses.append(course)

            logger.debug(f"Parsed {len(unique_courses)} courses")

        except Exception as e:
            logger.error(f"Error parsing study plan courses: {e}")

        return unique_courses

    def _parse_course_objects(self, table, section_type: str) -> List[Dict]:
        """Extract course objects with metadata from table."""
        courses = []
        rows = self.safe_find_all(table, "tr")
        current_semester = None

        for row in rows:
            cells = self.safe_find_all(row, "td")

            if not cells:
                continue

            if len(cells) == 1 and "CellSpa" in cells[0].get("class", []):
                semester_text = self.safe_get_text(cells[0]).strip().upper()
                current_semester = self._parse_semester_text(semester_text)
                continue

            if len(cells) >= 4 and "CellIco" in cells[0].get("class", []):
                input_tag = self.safe_find(cells[0], "input")
                if not input_tag or "value" not in input_tag.attrs:
                    continue

                code = input_tag["value"]
                course_obj = {"code": code, "type": section_type}

                if current_semester is not None:
                    course_obj["semester"] = current_semester

                courses.append(course_obj)

        return courses

    def _parse_semester_text(self, text: str) -> int:
        """Convert semester text to number (e.g., 'PRIMER SEMESTRE' -> 1)."""
        text = text.upper().strip()

        if "CUALQUIER" in text:
            return None

        semester_map = {
            "PRIMER": 1,
            "PRIMERO": 1,
            "SEGUNDO": 2,
            "TERCER": 3,
            "TERCERO": 3,
            "CUARTO": 4,
            "QUINTO": 5,
            "SEXTO": 6,
            "SEPTIMO": 7,
            "SÉPTIMO": 7,
            "OCTAVO": 8,
            "NOVENO": 9,
            "DECIMO": 10,
            "DÉCIMO": 10,
            "UNDECIMO": 11,
            "UNDÉCIMO": 11,
            "DUODECIMO": 12,
            "DUODÉCIMO": 12,
        }

        for word, number in semester_map.items():
            if word in text:
                return number

        match = re.search(r"\d+", text)
        if match:
            return int(match.group())

        return None

    def _get_section_type(self, section: str) -> str:
        """Determine section type from header text."""
        s = section.lower().strip()

        if "obligatoria" in s:
            return "required"
        elif "humanidades" in s:
            return "elective_humanities"
        else:
            return "elective"
