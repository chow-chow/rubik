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

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            results = list(
                executor.map(
                    lambda p: _process_program(p, http_client, storage, config),
                    programs,
                )
            )

        total_courses = sum(r for r in results if r is not None)

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
            status=ScraperStatus.FAILED, items=0, errors=[str(e)], execution_time=time.time() - start_time
        )


def _process_program(program: dict, http_client, storage, config) -> int:
    """Process courses for a single program."""
    from ..parsers import StudyPlansParser

    code = program["code"]
    name = program["name"]

    try:
        logger.info(f"Processing courses for {code}: {name}")

        plans_url = config.STUDY_PLANS_URL.format(code)
        soup = http_client.get(plans_url)

        if not soup:
            logger.warning(f"Failed to fetch study plans for {code}")
            return 0

        plans_parser = StudyPlansParser()
        study_plans = plans_parser.parse(soup, code)

        if not study_plans:
            logger.warning(f"No study plans found for {code}")
            return 0

        all_courses = {}
        courses_parser = CoursesParser()

        for plan in study_plans:
            try:
                courses_url = config.COURSES_URL.format(plan.code)
                courses_soup = http_client.get(courses_url)

                if courses_soup:
                    plan_courses = courses_parser.parse(courses_soup)
                    all_courses.update(plan_courses)
                    logger.debug(
                        f"Found {len(plan_courses)} courses in plan {plan.code}"
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch courses for plan {plan.code}: {e}")
                continue

        if not all_courses:
            logger.warning(f"No courses found for {code}")
            return 0

        courses = list(all_courses.values())

        storage.save_courses(code, courses)

        storage.update_program_total_courses(code, len(courses))

        logger.info(f"Saved {len(courses)} courses for {code}")
        return len(courses)

    except Exception as e:
        logger.error(f"Error processing courses for {code}: {e}")
        return 0


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
