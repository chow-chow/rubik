"""
Courses scraper - fetches course data for all programs.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from ..config import get_config
from ..models import ScraperResult, ScraperStatus
from ..parsers import CoursesParser

logger = logging.getLogger(__name__)


def scrape_courses(http_client, storage) -> ScraperResult:
    """
    Scrape courses for all programs.

    Args:
        http_client: HTTPClient instance
        storage: DataStorage instance

    Returns:
        ScraperResult with execution details
    """
    start_time = time.time()
    config = get_config()

    try:
        logger.info("Starting courses scraper")

        programs_file = Path(storage.data_dir) / "programs.json"
        if not programs_file.exists():
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["Programs file not found. Run 'programs' scraper first."],
                execution_time=time.time() - start_time,
            )

        with open(programs_file, "r") as f:
            programs = json.load(f)

        logger.info(f"Processing {len(programs)} programs")

        all_unique_courses = {}

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            results = list(
                executor.map(
                    lambda p: _process_program(p, http_client, config, storage),
                    programs,
                )
            )

        for course_dict in results:
            if course_dict:
                all_unique_courses.update(course_dict)

        if all_unique_courses:
            storage.save_courses_index(all_unique_courses)

        total_courses = len(all_unique_courses)

        execution_time = time.time() - start_time
        logger.info(
            f"Courses scraper completed: {total_courses} courses in {execution_time:.2f}s"
        )

        return _create_result(
            status=ScraperStatus.SUCCESS,
            items=total_courses,
            errors=[],
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Error in courses scraper: {e}", exc_info=True)
        return _create_result(
            status=ScraperStatus.FAILED,
            items=0,
            errors=[str(e)],
            execution_time=time.time() - start_time,
        )


def _process_program(program: dict, http_client, config, storage) -> dict:
    """Process courses for a single program, save per study plan, and return unique courses."""
    from ..parsers import StudyPlansParser

    code = program["code"]
    name = program["name"]

    try:
        logger.info(f"Processing courses for {code}: {name}")

        plans_url = config.STUDY_PLANS_URL.format(code)
        soup = http_client.get(plans_url)

        if not soup:
            logger.warning(f"Failed to fetch study plans for {code}")
            return {}

        plans_parser = StudyPlansParser()
        study_plans = plans_parser.parse(soup, code)

        if not study_plans:
            logger.warning(f"No study plans found for {code}")
            return {}

        all_unique_courses = {}
        courses_parser = CoursesParser()

        for plan in study_plans:
            try:
                courses_url = config.COURSES_URL.format(plan.code)
                courses_soup = http_client.get(courses_url)

                if courses_soup:
                    plan_courses = courses_parser.parse(courses_soup)

                    courses_list = list(plan_courses.values())
                    storage.save_courses(plan.code, courses_list)

                    all_unique_courses.update(plan_courses)

                    logger.debug(
                        f"Saved {len(plan_courses)} courses for plan {plan.code}"
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch courses for plan {plan.code}: {e}")
                continue

        if all_unique_courses:
            logger.info(
                f"Collected {len(all_unique_courses)} unique courses for {code}"
            )

        return all_unique_courses

    except Exception as e:
        logger.error(f"Error processing courses for {code}: {e}")
        return {}


def _create_result(
    status: ScraperStatus, items: int, errors: list, execution_time: float
) -> ScraperResult:
    """Create scraper result."""
    return ScraperResult(
        scraper_name="courses",
        status=status.value,
        items_processed=items,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )
