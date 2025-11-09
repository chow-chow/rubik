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

from .linker import ProfessorGroupsLinker
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

        self.study_plans_dir = self.data_dir / "study_plans"
        self.courses_dir = self.data_dir / "courses"
        self.groups_dir = self.data_dir / "groups"
        self.study_plans_dir.mkdir(exist_ok=True)
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
        """Save programs index."""
        data = [asdict(program) for program in programs]
        filepath = self.data_dir / "programs.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(programs)} programs")
        return success

    def save_courses(self, study_plan_code: str, courses: List[Course]) -> bool:
        """Save courses for a specific study plan."""
        data = [asdict(course) for course in courses]
        data.sort(key=lambda x: x["code"])

        filepath = self.courses_dir / f"{study_plan_code}.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(
                f"Saved {len(courses)} courses for study plan {study_plan_code}"
            )
        return success

    def save_courses_index(self, all_courses: Dict[str, Course]) -> bool:
        """Save global courses index for search."""
        filepath = self.data_dir / "courses_index.json"

        existing_courses = {}
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    for course in existing_data:
                        existing_courses[course["code"]] = course
            except Exception as e:
                logger.warning(f"Could not load existing courses index: {e}")

        data = []
        for course in all_courses.values():
            course_dict = asdict(course)

            if course.code in existing_courses:
                existing = existing_courses[course.code]
                if "has_lab" in existing:
                    course_dict["has_lab"] = existing["has_lab"]
                if "lab" in existing:
                    course_dict["lab"] = existing["lab"]

            data.append(course_dict)

        data.sort(key=lambda x: x["code"])

        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(data)} courses to index")
        return success

    def save_groups(
        self,
        course_code: str,
        groups: List[Group],
        professor_ratings: Dict[int, Dict] = None,
    ) -> bool:
        """Save groups for a course."""

        data = []
        linker = ProfessorGroupsLinker()
        linker.professors = (
            list(professor_ratings.values()) if professor_ratings else []
        )
        linker._build_indexes()

        for group in groups:
            group_dict = asdict(group)

            if professor_ratings and group.professor:
                match = linker._match_professor(group.professor)
                if match:
                    group_dict["professor_id"] = match.get("id")
                    group_dict["first_name"] = match.get("first_name")
                    group_dict["last_name"] = match.get("last_name")
                    group_dict["rating"] = match.get("rating")
                    group_dict["num_ratings"] = match.get("num_ratings")

            data.append(group_dict)

        filepath = self.groups_dir / f"{course_code}.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(groups)} groups for course {course_code}")
        return success

    def save_study_plans(self, program_code: str, study_plans: List[StudyPlan]) -> bool:
        """Save study plans for a specific program."""
        data = [asdict(plan) for plan in study_plans]
        filepath = self.study_plans_dir / f"{program_code}.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(
                f"Saved {len(study_plans)} study plans for program {program_code}"
            )
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
        """Save professor ratings index."""
        sorted_profs = sorted(
            professors, key=lambda p: (p.rating, p.num_ratings), reverse=True
        )
        data = [asdict(p) for p in sorted_profs]
        filepath = self.data_dir / "professor_ratings_index.json"
        success = self._save_json(data, filepath)
        if success:
            logger.info(f"Saved {len(professors)} professors to index")
        return success

    def load_professor_ratings(self) -> Dict[int, Dict]:
        """Load professor ratings as dict keyed by professor_id."""
        filepath = self.data_dir / "professor_ratings_index.json"
        if not filepath.exists():
            logger.warning("Professor ratings index not found")
            return {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                professors = json.load(f)
                return {p["id"]: p for p in professors}
        except Exception as e:
            logger.error(f"Failed to load professor ratings: {e}")
            return {}

    def get_all_course_codes(self) -> set:
        """Get all unique course codes from courses_index.json, including labs."""
        codes = set()
        filepath = self.data_dir / "courses_index.json"

        if not filepath.exists():
            return codes

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                courses = json.load(f)

            for course in courses:
                if "code" in course:
                    codes.add(course["code"])
                if course.get("has_lab") and course.get("lab"):
                    lab_code = course["lab"].get("code")
                    if lab_code:
                        codes.add(lab_code)
        except Exception as e:
            logger.warning(f"Error reading courses_index.json: {e}")

        return codes

    def save_lab_associations(self, lab_data: List[Dict]) -> bool:
        """Update courses_index.json and all courses/*.json with lab associations."""

        def update_course_list(courses_list):
            """Helper to update a list of course dicts with lab data."""
            for course in courses_list:
                course["has_lab"] = False
                course["lab"] = None

            associations = 0
            for course in courses_list:
                course_code = course["code"]
                for lab in lab_data:
                    try:
                        expected_base = f"{int(lab['code']) - 5000:04d}"
                        if expected_base == course_code:
                            course["has_lab"] = True
                            course["lab"] = {
                                "code": lab["code"],
                                "name": lab["name"],
                            }
                            associations += 1
                            break
                    except (ValueError, TypeError):
                        continue
            return associations

        try:
            total_associations = 0

            index_path = self.data_dir / "courses_index.json"
            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as f:
                    index_courses = json.load(f)

                associations = update_course_list(index_courses)
                self._save_json(index_courses, index_path)
                total_associations += associations
                logger.info(
                    f"Updated courses_index.json: {associations} lab associations"
                )

            if self.courses_dir.exists():
                for course_file in self.courses_dir.glob("*.json"):
                    try:
                        with open(course_file, "r", encoding="utf-8") as f:
                            plan_courses = json.load(f)

                        associations = update_course_list(plan_courses)
                        self._save_json(plan_courses, course_file)
                        if associations > 0:
                            logger.debug(
                                f"Updated {course_file.name}: {associations} lab associations"
                            )
                        total_associations += associations
                    except Exception as e:
                        logger.warning(f"Error updating {course_file.name}: {e}")

            logger.info(
                f"Total lab associations across all files: {total_associations}"
            )
            return total_associations > 0

        except Exception as e:
            logger.error(f"Error processing lab associations: {e}")
            return False

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
