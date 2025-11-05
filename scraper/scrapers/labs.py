"""
Labs scraper - fetches laboratory course associations.
"""

import logging
import time
from datetime import datetime

from ..config import get_config
from ..models import ScraperResult, ScraperStatus
from ..parsers import LabsParser

logger = logging.getLogger(__name__)


def scrape_labs(http_client, storage) -> ScraperResult:
    """
    Scrape laboratory course associations.

    Args:
        http_client: HTTPClient instance
        storage: DataStorage instance

    Returns:
        ScraperResult with execution details
    """
    start_time = time.time()
    config = get_config()

    try:
        logger.info("Starting labs scraper")

        soup = http_client.get(config.LABS_JS_URL)
        if not soup:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["Failed to fetch labs JavaScript file"],
                start_time=start_time,
            )

        parser = LabsParser()
        labs = parser.parse(soup)

        if not labs:
            return _create_result(
                status=ScraperStatus.FAILED,
                items=0,
                errors=["No lab courses found"],
                start_time=start_time,
            )

        logger.info(f"Found {len(labs)} lab courses")

        storage.save_lab_associations(labs)

        execution_time = time.time() - start_time
        logger.info(
            f"Labs scraper completed: {len(labs)} labs in {execution_time:.2f}s"
        )

        return _create_result(
            status=ScraperStatus.SUCCESS,
            items=len(labs),
            errors=[],
            start_time=start_time,
        )

    except Exception as e:
        logger.error(f"Error in labs scraper: {e}", exc_info=True)
        return _create_result(
            status=ScraperStatus.FAILED, items=0, errors=[str(e)], start_time=start_time
        )


def _create_result(
    status: ScraperStatus, items: int, errors: list, start_time: float
) -> ScraperResult:
    """Create scraper result."""
    return ScraperResult(
        scraper_name="labs",
        status=status.value,
        items_processed=items,
        execution_time=time.time() - start_time,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )
