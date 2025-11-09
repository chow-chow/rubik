"""
Data storage management.

Handles saving scraped data to JSON files with atomic writes.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .models import (
    Course,
    Group,
    Professor,
    Program,
    ScraperMetadata,
    ScraperResult,
    StudyPlan,
)

logger = logging.getLogger(__name__)


class DataStorage:
    """Manages data persistence to JSON files."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize storage manager.

        Args:
            data_dir: Directory for data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.courses_dir = self.data_dir / "courses"
        self.groups_dir = self.data_dir / "groups"
        self.courses_dir.mkdir(exist_ok=True)
        self.groups_dir.mkdir(exist_ok=True)

        self.metadata_file = self.data_dir / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> ScraperMetadata:
        """Load metadata from file or create new."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return ScraperMetadata(**data)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")

        return ScraperMetadata.create_empty()

    def _save_json(self, data: Any, filepath: Path) -> bool:
        """
        Save data to JSON file atomically.

        Args:
            data: Data to save
            filepath: Target file path

        Returns:
            True if successful
        """
        try:
            temp_file = filepath.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(filepath)
            logger.debug(f"Saved: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return False

    def save_programs(self, programs: List[Program]) -> bool:
        """Save programs index, preserving existing fields."""
        filepath = self.data_dir / "programs.json"

        existing_programs = {}
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    for program in existing_data:
                        existing_programs[program["code"]] = program
            except Exception as e:
                logger.warning(f"Could not load existing programs: {e}")

        data = []
        for program in programs:
            program_dict = asdict(program)

            if program.code in existing_programs:
                existing = existing_programs[program.code]
                if "total_courses" in existing:
                    program_dict["total_courses"] = existing["total_courses"]

            data.append(program_dict)

        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(programs)} programs")
        return success

    def save_courses(self, program_code: str, courses: List[Course]) -> bool:
        """Save courses for a program, preserving existing fields"""
        filepath = self.courses_dir / f"{program_code}.json"

        existing_courses = {}
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    for course in existing_data:
                        existing_courses[course["code"]] = course
            except Exception as e:
                logger.warning(
                    f"Could not load existing courses for {program_code}: {e}"
                )

        data = []
        for course in courses:
            course_dict = asdict(course)

            if course.code in existing_courses:
                existing = existing_courses[course.code]
                if "total_groups" in existing:
                    course_dict["total_groups"] = existing["total_groups"]
                if "has_lab" in existing:
                    course_dict["has_lab"] = existing["has_lab"]
                if "lab" in existing:
                    course_dict["lab"] = existing["lab"]

            data.append(course_dict)

        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(courses)} courses for program {program_code}")
        return success

    def save_groups(self, course_code: str, groups: List[Group]) -> bool:
        """Save groups for a course."""
        data = [asdict(g) for g in groups]
        filepath = self.groups_dir / f"{course_code}.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(groups)} groups for course {course_code}")
        return success

    def save_study_plans(self, study_plans: List[StudyPlan]) -> bool:
        """Save study plans index."""
        data = [asdict(plan) for plan in study_plans]
        filepath = self.data_dir / "study_plans.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(study_plans)} study plans")
        return success

    def load_study_plans(self) -> List[Dict]:
        """Load study plans from file."""
        filepath = self.data_dir / "study_plans.json"
        if not filepath.exists():
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load study plans: {e}")
            return []

    def load_programs(self) -> List[Dict]:
        """Load programs from file."""
        filepath = self.data_dir / "programs.json"
        if not filepath.exists():
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load programs: {e}")
            return []

    def save_professors(self, professors: List[Professor]) -> bool:
        """Save professor ratings."""
        sorted_profs = sorted(
            professors, key=lambda p: (p.rating, p.num_ratings), reverse=True
        )
        data = [asdict(p) for p in sorted_profs]
        filepath = self.data_dir / "professor_ratings.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(professors)} professors")
        return success

    def get_all_course_codes(self) -> set:
        """Get all unique course codes from saved data, including labs."""
        codes = set()
        for file in self.courses_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    courses = json.load(f)
                for course in courses:
                    if "code" in course:
                        codes.add(course["code"])
                    # Also add lab codes
                    if course.get("has_lab") and course.get("lab"):
                        lab_code = course["lab"].get("code")
                        if lab_code:
                            codes.add(lab_code)
            except Exception as e:
                logger.warning(f"Error reading {file}: {e}")
        return codes

    def update_program_total_courses(
        self, program_code: str, total_courses: int
    ) -> bool:
        """
        Update total_courses field for a program in programs.json.

        Args:
            program_code: Program identifier
            total_courses: Number of courses

        Returns:
            True if successful
        """
        programs_file = self.data_dir / "programs.json"

        if not programs_file.exists():
            logger.warning("programs.json not found")
            return False

        try:
            with open(programs_file, "r", encoding="utf-8") as f:
                programs = json.load(f)

            updated = False
            for program in programs:
                if program.get("code") == program_code:
                    program["total_courses"] = total_courses
                    updated = True
                    logger.debug(
                        f"Updated total_courses={total_courses} for program {program_code}"
                    )
                    break

            if not updated:
                logger.warning(f"Program {program_code} not found in programs.json")
                return False

            return self._save_json(programs, programs_file)

        except Exception as e:
            logger.error(
                f"Error updating total_courses for program {program_code}: {e}"
            )
            return False

    def update_course_group_count(self, course_code: str, total_groups: int) -> None:
        """Update total_groups for a course or lab across all program files."""
        for file in self.courses_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    courses = json.load(f)

                updated = False
                for course in courses:
                    if course.get("code") == course_code:
                        course["total_groups"] = total_groups
                        updated = True
                    elif (
                        course.get("has_lab")
                        and course.get("lab")
                        and course["lab"].get("code") == course_code
                    ):
                        course["lab"]["total_groups"] = total_groups
                        updated = True

                if updated:
                    self._save_json(courses, file)

            except Exception as e:
                logger.warning(f"Error updating {file}: {e}")

    def save_lab_associations(self, lab_data: List[Dict]) -> bool:
        """
        Update courses with lab associations.

        Args:
            lab_data: List of lab course dictionaries

        Returns:
            True if successful
        """
        associations = 0
        for file in self.courses_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    courses = json.load(f)

                updated = False
                for course in courses:
                    course_code = course["code"]
                    for lab in lab_data:
                        try:
                            expected_base = f"{int(lab['code']) - 5000:04d}"
                            if expected_base == course_code:
                                course["has_lab"] = True
                                course["lab"] = {
                                    "code": lab["code"],
                                    "name": lab["name"],
                                    "total_groups": 0,
                                }
                                associations += 1
                                updated = True
                                break
                        except (ValueError, TypeError):
                            continue

                if updated:
                    self._save_json(courses, file)

            except Exception as e:
                logger.warning(f"Error processing {file}: {e}")

        logger.info(f"Created {associations} lab associations")
        return associations > 0

    def update_metadata(self, result: ScraperResult) -> None:
        """Update metadata after scraper execution."""
        self.metadata.timestamp = result.timestamp
        self.metadata.scrapers[result.scraper_name] = {
            "status": result.status,
            "last_run": result.timestamp,
            "execution_time": result.execution_time,
            "items_processed": result.items_processed,
        }
        self._save_json(asdict(self.metadata), self.metadata_file)
