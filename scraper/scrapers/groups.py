"""
Groups scraper - fetches course groups/sections data.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ..config import get_config
from ..models import ScraperResult, ScraperStatus
from ..parsers import GroupsParser

logger = logging.getLogger(__name__)


def scrape_groups(http_client, storage) -> ScraperResult:
    """
    Scrape course groups for all courses.

    Args:
        http_client: HTTPClient instance
        storage: DataStorage instance

    Returns:
        ScraperResult with execution details
    """
    start_time = time.time()
    config = get_config()

    try:
        logger.info("Starting groups scraper")

        course_codes = storage.get_all_course_codes()

        if not course_codes:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["No courses found. Run 'courses' scraper first."],
                start_time=start_time,
            )

        professor_ratings = storage.load_professor_ratings()
        logger.info(f"Loaded {len(professor_ratings)} professor ratings")

        logger.info(f"Processing {len(course_codes)} courses")

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            results = list(
                executor.map(
                    lambda code: _process_course(
                        code, http_client, storage, config, professor_ratings
                    ),
                    course_codes,
                )
            )

        total_groups = sum(r for r in results if r is not None)

        execution_time = time.time() - start_time
        logger.info(
            f"Groups scraper completed: {total_groups} groups in {execution_time:.2f}s"
        )

        return _create_result(
            status=ScraperStatus.SUCCESS,
            items=total_groups,
            errors=[],
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Error in groups scraper: {e}", exc_info=True)
        return _create_result(
            status=ScraperStatus.FAILED,
            items=0,
            errors=[str(e)],
            execution_time=time.time() - start_time,
        )


def _process_course(
    course_code: str, http_client, storage, config, professor_ratings: dict
) -> int:
    """Process groups for a single course with embedded professor data."""
    try:
        logger.info(f"Processing groups for course {course_code}")

        url = config.GROUPS_URL.format(course_code)
        soup = http_client.get(url)

        if not soup:
            logger.warning(f"Failed to fetch groups for {course_code}")
            return 0

        parser = GroupsParser()
        groups = parser.parse(soup, course_code)

        if not groups:
            logger.debug(f"No groups found for {course_code}")
            return 0

        storage.save_groups(course_code, groups, professor_ratings)

        logger.info(f"Saved {len(groups)} groups for {course_code}")
        return len(groups)

    except Exception as e:
        logger.error(f"Error processing groups for {course_code}: {e}")
        return 0


def _create_result(
    status: ScraperStatus, items: int, errors: list, execution_time: float
) -> ScraperResult:
    """Create scraper result."""
    return ScraperResult(
        scraper_name="groups",
        status=status.value,
        items_processed=items,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )
