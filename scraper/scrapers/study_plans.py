"""
Study plans scraper - fetches complete study plan data with course organization.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ..config import get_config
from ..models import ScraperResult, ScraperStatus, StudyPlan
from ..parsers import StudyPlanCoursesParser, StudyPlansParser

logger = logging.getLogger(__name__)


def scrape_study_plans(http_client, storage) -> ScraperResult:
    """
    Scrape all study plans with their course organization.

    Args:
        http_client: HTTPClient instance
        storage: DataStorage instance

    Returns:
        ScraperResult with execution details
    """
    start_time = time.time()
    config = get_config()

    try:
        logger.info("Starting study plans scraper")

        programs = storage.load_programs()
        if not programs:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["No programs found. Run programs scraper first."],
                execution_time=time.time() - start_time,
            )

        all_plans = []

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            results = list(
                executor.map(
                    lambda p: _process_program_plans(p, http_client, config), programs
                )
            )

        for plans in results:
            if plans:
                all_plans.extend(plans)

        if all_plans:
            storage.save_study_plans(all_plans)

        execution_time = time.time() - start_time
        status = ScraperStatus.SUCCESS if all_plans else ScraperStatus.FAILED

        logger.info(
            f"Study plans scraper completed: {len(all_plans)} plans in {execution_time:.2f}s"
        )

        return _create_result(
            status=status, items=len(all_plans), errors=[], execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"Error in study plans scraper: {e}", exc_info=True)
        return _create_result(
            status=ScraperStatus.FAILED, items=0, errors=[str(e)], execution_time=time.time() - start_time
        )


def _process_program_plans(program: dict, http_client, config) -> list:
    """Process all study plans for a program."""
    code = program["code"]

    try:
        logger.info(f"Processing study plans for program {code}")

        plans_url = config.STUDY_PLANS_URL.format(code)
        soup = http_client.get(plans_url)

        if not soup:
            logger.warning(f"Failed to fetch study plans page for {code}")
            return []

        parser = StudyPlansParser()
        plans = parser.parse(soup, code)

        if not plans:
            logger.warning(f"No study plans found for {code}")
            return []

        completed_plans = []
        courses_parser = StudyPlanCoursesParser()

        for plan in plans:
            try:
                courses_url = config.COURSES_URL.format(plan.code)
                courses_soup = http_client.get(courses_url)

                if not courses_soup:
                    logger.warning(f"Failed to fetch courses for plan {plan.code}")
                    continue

                courses_by_section = courses_parser.parse(courses_soup)
                plan.courses = courses_by_section

                completed_plans.append(plan)
                logger.debug(f"Completed plan {plan.code}: {plan.name}")

            except Exception as e:
                logger.error(f"Error processing plan {plan.code}: {e}")
                continue

        return completed_plans

    except Exception as e:
        logger.error(f"Error processing program {code}: {e}")
        return []


def _create_result(
    status: ScraperStatus, items: int, errors: list, execution_time: float
) -> ScraperResult:
    """Create scraper result."""
    return ScraperResult(
        scraper_name="study_plans",
        status=status.value,
        items_processed=items,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )
