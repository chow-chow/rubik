"""
Parser for course groups/sections.
"""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from ..models import Group
from .base import BaseParser
from .utils import remove_academic_title

logger = logging.getLogger(__name__)


class GroupsParser(BaseParser):
    """Parser for course groups."""

    DAYS_MAP = {"Lun": 1, "Mar": 2, "Mie": 3, "Jue": 4, "Vie": 5, "Sab": 6, "Dom": 7}

    def parse(self, soup: BeautifulSoup, course_code: str) -> List[Group]:
        """Extract course groups."""
        groups = []
        seen = set()

        tables = soup.select("table.table-horarios-custom")

        for table in tables:
            for tbody in table.select("tbody"):
                group = self._parse_group(tbody, course_code)
                if group:
                    key = f"{group.code}-{group.group}"
                    if key not in seen:
                        groups.append(group)
                        seen.add(key)

        logger.debug(f"Parsed {len(groups)} groups for {course_code}")
        return groups

    def _parse_group(self, tbody, course_code: str) -> Optional[Group]:
        """Parse single group."""
        rows = tbody.select("tr")
        if not rows:
            return None

        try:
            first_row = rows[0]
            cells = first_row.find_all(["td", "th"])

            if len(cells) < 5:
                return None

            code = self.safe_get_text(cells[0])
            group_num = self.safe_get_text(cells[1])
            professor_raw = self.safe_get_text(cells[2])

            professor = re.sub(r"\s*\(.*?\)", "", professor_raw)
            professor = professor.replace("\n", " ").strip()
            professor = remove_academic_title(professor)

            if int(code) != int(course_code):
                return None

            group = Group(code=code, group=group_num, professor=professor, schedules=[])

            for row_idx, row in enumerate(rows):
                schedule = self._parse_schedule(row, row_idx)
                if schedule:
                    group.schedules.append(schedule)

            return group if group.schedules else None

        except Exception as e:
            logger.error(f"Error parsing group: {e}")
            return None

    def _parse_schedule(self, row, row_idx: int) -> Optional[Dict]:
        """Parse schedule from row."""
        cells = row.find_all(["td", "th"])

        start_idx = (
            4
            if row_idx == 0
            else (
                0
                if len(cells) > 0 and self._is_time(self.safe_get_text(cells[0]))
                else 1
            )
        )

        if len(cells) <= start_idx + 2:
            return None

        try:
            time = self.safe_get_text(cells[start_idx]).replace(" a ", "-").strip()
            day_str = self.safe_get_text(cells[start_idx + 1])
            classroom = self.safe_get_text(cells[start_idx + 2])

            days = [
                self.DAYS_MAP[d.strip()]
                for d in day_str.split(",")
                if d.strip() in self.DAYS_MAP
            ]

            if time and days:
                return {"time": time, "days": days, "classroom": classroom}
        except Exception:
            pass

        return None

    def _is_time(self, text: str) -> bool:
        """Check if text is time format."""
        return bool(re.match(r"\d{1,2}:\d{2}\s*a\s*\d{1,2}:\d{2}", text.strip()))
