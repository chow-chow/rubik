"""
Professors scraper - fetches professor ratings.
"""

import logging
import time
from datetime import datetime

from ..config import get_config
from ..models import Professor, ScraperResult, ScraperStatus
from ..parsers import ProfessorRatingsParser

logger = logging.getLogger(__name__)


def scrape_professors(http_client, storage) -> ScraperResult:
    """
    Scrape professor ratings.

    Args:
        http_client: HTTPClient instance
        storage: DataStorage instance

    Returns:
        ScraperResult with execution details
    """
    start_time = time.time()
    config = get_config()

    try:
        logger.info("Starting professors scraper")

        soup = http_client.get(config.PROFESSORS_URL)
        if not soup:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["Failed to fetch professors page"],
                start_time=start_time,
            )

        parser = ProfessorRatingsParser()
        raw_professors = parser.parse(soup)

        if not raw_professors:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["No professors found"],
                start_time=start_time,
            )

        logger.info(f"Found {len(raw_professors)} raw professor entries")

        consolidated = parser.consolidate(raw_professors)

        professors = [
            Professor(
                id=int(p["id"]),
                full_name=p["full_name"],
                first_name=p["first_name"],
                last_name=p["last_name"],
                num_ratings=p["num_ratings"],
                rating=p["rating"],
            )
            for p in consolidated
        ]

        storage.save_professors(professors)

        execution_time = time.time() - start_time
        logger.info(
            f"Professors scraper completed: {len(professors)} professors in {execution_time:.2f}s"
        )

        return _create_result(
            status=ScraperStatus.SUCCESS,
            items=len(professors),
            errors=[],
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Error in professors scraper: {e}", exc_info=True)
        return _create_result(
            status=ScraperStatus.FAILED, items=0, errors=[str(e)], execution_time=time.time() - start_time
        )


def _create_result(
    status: ScraperStatus, items: int, errors: list, execution_time: float
) -> ScraperResult:
    """Create scraper result."""
    return ScraperResult(
        scraper_name="professors",
        status=status.value,
        items_processed=items,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )
